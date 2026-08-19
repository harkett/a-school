// Écran « Analyser une consigne ». Le jumeau de l'écran Ambiguïtés, à une différence de fond :
// ici les cinq axes NE SE COCHENT PAS. Un type d'ambiguïté décoché retire des cartes du rapport ;
// un axe décoché produirait une « consigne optimisée » qui laisse passer un défaut connu, sans que
// le professeur le sache. Les cinq axes sont les dimensions d'un même diagnostic — ils sont donc
// imposés, et seulement AFFICHÉS (utils/axesConsigne.js, leur source unique).
import { useState } from 'react'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_LONG } from '../utils/api.js'
import { showError } from '../errorDialog.js'
import { ech } from '../utils/echapperHtml.js'
import ApportTexte from './contenus/ApportTexte.jsx'
import JaugeAttente from './JaugeAttente.jsx'
import SplitPane from './SplitPane.jsx'
import ApercuHtmlModale from './ApercuHtmlModale.jsx'
import InfoGuide from './InfoGuide.jsx'
import { aideConsigne } from '../utils/aideConsigne.js'
import { AXES_CONSIGNE, couleurAxe } from '../utils/axesConsigne.js'
import { documentDepuisHtml } from '../utils/apercuHtml.js'
import { isTexteGibberish } from '../utils/texteGibberish.js'
import { IconAnalyser, IconConsigne, Spinner } from './icones.jsx'

const SEVERITE_COLOR = {
  'Élevée':  { bg: '#fee2e2', text: '#991b1b' },
  'Modérée': { bg: '#fef3c7', text: '#92400e' },
}

// D'où vient le texte de la zone, quand il n'a pas été tapé au clavier — la rangée d'apport le
// signale, l'écran l'affiche (même principe que les écrans Ambiguïtés, Séance et Séquence).
const SOURCES_TEXTE = {
  txt:    "Texte importé d'un fichier",
  image:  "Texte extrait d'une image",
  pdf:    'Texte extrait d\'un PDF',
  dictee: 'Texte issu de votre dictée',
  exemple: "Consigne d'exemple écrite par aSchool",
}

// Le rapport, écrit EN PAGE pour l'aperçu mis en forme (bouton « HTML », comme l'activité et
// l'écran Ambiguïtés). Il reprend les couleurs de l'écran — lues à la même source que les cartes
// — parce qu'elles portent du sens : l'axe se reconnaît à sa teinte, la consigne réécrite au cadre
// de ce qui est prêt à recopier. `print-color-adjust` demande à l'imprimante de les garder : sans
// lui, la plupart des navigateurs suppriment les fonds pour épargner l'encre, et la feuille
// sortirait grise.
//
// Tout ce qui vient du modèle est ÉCHAPPÉ (`ech`, utils/echapperHtml.js — une seule place pour
// les cinq écrans qui composent une page). Le nettoyage de sortie (DOMPurify, dans apercuHtml.js)
// reste le dernier filet, jamais le premier.

const COULEURS_A_L_IMPRESSION = '-webkit-print-color-adjust:exact;print-color-adjust:exact'

function etiquette(texte, couleur) {
  return `<div style="font-size:11px;font-weight:700;color:${couleur};text-transform:uppercase;`
       + `letter-spacing:.04em;margin:12px 0 4px">${texte}</div>`
}

function rapportEnHtml(resultat) {
  const n = Array.isArray(resultat.analyses) ? resultat.analyses.length : 0
  const blocs = ["<h1>Analyse de la consigne</h1>"]

  // Le verdict, dans la couleur qu'il a à l'écran : vert s'il n'y a rien à corriger, ambre sinon.
  const v = n === 0
    ? { fond: '#f0fdf4', bord: '#86efac', texte: '#166534', titre: 'Consigne claire' }
    : { fond: '#fffbeb', bord: '#fcd34d', texte: '#92400e',
        titre: `${n} point${n > 1 ? 's' : ''} à améliorer` }
  blocs.push(`<div style="background:${v.fond};border:1px solid ${v.bord};border-radius:6px;`
    + `padding:12px 16px;color:${v.texte};margin:14px 0;${COULEURS_A_L_IMPRESSION}">`
    + `<strong>${v.titre}</strong> — ${ech(resultat.verdict)}</div>`)

  ;(resultat.analyses || []).forEach((a, i) => {
    const c = couleurAxe(a.axe)
    const sc = SEVERITE_COLOR[a.severite] || SEVERITE_COLOR['Modérée']
    blocs.push(`<div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;`
      + `margin:0 0 10px;page-break-inside:avoid;${COULEURS_A_L_IMPRESSION}">`
      + `<span style="display:inline-block;font-size:11px;font-weight:700;color:${c.text};`
      + `background:${c.bg};border:1px solid ${c.border};border-radius:12px;padding:2px 10px;`
      + `${COULEURS_A_L_IMPRESSION}">${i + 1}. ${ech(a.axe)}</span>`
      + ` <span style="display:inline-block;font-size:10px;font-weight:700;color:${sc.text};`
      + `background:${sc.bg};border-radius:10px;padding:2px 8px;${COULEURS_A_L_IMPRESSION}">`
      + `${ech(a.severite)}</span>`
      + etiquette('Extrait problématique', '#94a3b8')
      + `<div style="font-style:italic;color:#374151;background:#fafafa;border-left:3px solid #e2e8f0;`
      + `padding:6px 10px;border-radius:3px;${COULEURS_A_L_IMPRESSION}">« ${ech(a.extrait)} »</div>`
      + etiquette('Problème identifié', '#94a3b8')
      + `<div style="color:#374151">${ech(a.probleme)}</div>`
      + etiquette('Suggestion', '#166534')
      + `<div style="color:#166534;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:5px;`
      + `padding:8px 10px;${COULEURS_A_L_IMPRESSION}">${ech(a.conseil)}</div>`
      + `</div>`)
  })

  // La consigne réécrite ferme le rapport : c'est ce que le prof vient chercher.
  blocs.push(`<div style="border:2px solid #6366f1;border-radius:8px;padding:14px 16px;`
    + `page-break-inside:avoid;${COULEURS_A_L_IMPRESSION}">`
    + etiquette('Consigne optimisée', '#6366f1')
    + `<div style="color:#1e293b;white-space:pre-wrap">${ech(resultat.version_optimisee)}</div>`
    + `</div>`)
  return blocs.join('')
}

export default function Consigne() {
  const [consigne, setConsigne]   = useState('')
  const [loading, setLoading]     = useState(false)

  const [alertDialog, setAlertDialog] = useState(null)
  const [origineTexte, setOrigineTexte] = useState(null)
  const [resultat, setResultat]   = useState(null)
  // Le rapport occupe la colonne de droite : on peut la replier pour rendre toute la largeur au
  // formulaire (même geste que « Cacher le détail » des pages listes).
  const [resultatCache, setResultatCache] = useState(false)
  // Aperçu mis en forme du rapport : chaîne = ouvert, null = fermé. Éphémère, jamais en base.
  const [apercu, setApercu] = useState(null)

  // « Propose-moi un exemple » — aSchool écrit À LA DEMANDE une consigne de démonstration pour le
  // couple du prof, ancrée sur son référentiel, avec de vrais défauts dedans. Un clic, un appel,
  // rien de rangé en base : une consigne de démonstration n'a aucune raison d'être la même deux
  // fois. La mécanique commune (confirmation de remplacement, sablier + jauge, pastille d'origine)
  // vit dans ApportTexte ; ici seulement l'appel serveur.
  const proposerExemple = {
    label: 'Propose-moi un exemple',
    // La bulle du bouton se lit dans le catalogue, comme les « i » : une explication, une place.
    title: aideConsigne('exemple').court,
    jauge: "aSchool lit le programme officiel de votre niveau et écrit une consigne d'exemple…",
    note: 'exemple',
    action: async () => {
      try {
        const res = await apiFetch('/api/consignes/exemple-genere', {
          method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}),
        }, TIMEOUT_LONG)
        const d = await lireReponse(res)
        if (d.available && d.texte) return d.texte
        // Pas de référentiel pour ce niveau, rien d'assez pertinent, ou le modèle lui-même a
        // refusé d'écrire faute d'extraits parlants : on n'invente rien, on le dit.
        showError(d.message || "Pas d'exemple possible pour le moment pour votre niveau (programme officiel pas encore chargé).\n\nCollez votre propre consigne dans la zone de texte.")
        return null
      } catch (err) {
        showError(`Écriture de la consigne d'exemple impossible.\n\n${messagePourEcran(err)}`)
        return null
      }
    },
  }

  // Le bouton reste gris tant que l'analyse n'a pas de quoi être lancée — et sa bulle d'aide dit
  // LEQUEL des trois motifs bloque, jamais un simple « indisponible ». Ces trois refus sortaient
  // en boîte de dialogue APRÈS le clic : le prof découvrait le motif une fois le geste fait.
  const empeche =
    !consigne.trim()                             ? 'Collez une consigne avant de lancer l\'analyse.'
    : consigne.trim().split(/\s+/).length < 3    ? 'La consigne est trop courte — collez une consigne complète.'
    : isTexteGibberish(consigne)                 ? 'Le texte saisi ne ressemble pas à une consigne pédagogique.'
    : null

  async function analyser() {
    if (empeche) {
      setAlertDialog(empeche)
      return
    }
    setResultat(null)
    // Lancer l'analyse rouvre la colonne : sinon le rapport arriverait derrière un volet fermé, et
    // l'écran ne montrerait rien de ce qu'on vient de lui demander.
    setResultatCache(false)
    setLoading(true)
    try {
      const res = await apiFetch('/api/analyser-consigne', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ consigne: consigne.trim() }),   // le couple se résout EN BASE côté serveur
      }, TIMEOUT_LONG)
      const data = await lireReponse(res)   // message humain, jamais un détail technique brut
      setResultat(data)
    } catch (e) {
      showError(messagePourEcran(e))
    } finally {
      setLoading(false)
    }
  }

  function reinitialiser() {
    setResultat(null)
    setConsigne('')
    setOrigineTexte(null)
  }

  // ── COLONNE DE GAUCHE : tout ce que le professeur remplit — la consigne, d'où elle vient, et
  // les cinq axes sur lesquels elle sera jugée. Elle scrolle seule (classe .split-col). ──
  const colonneFormulaire = (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <p style={{ fontSize: '13px', color: '#64748b', margin: 0, lineHeight: 1.6 }}>
        Collez une consigne isolée. aSchool analyse sa clarté, sa précision didactique et les risques d'incompréhension — puis propose une version optimisée.
      </p>

      {/* Zone de saisie */}
      <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'inline-flex', alignItems: 'center' }}>
            Votre consigne
            <InfoGuide {...aideConsigne('consigne')} />
          </label>

          {/* Cinq façons d'apporter la consigne, en plus du clavier. Le cinquième bouton l'écrit
              lui-même : une consigne VOLONTAIREMENT imparfaite, écrite pour la démonstration —
              l'analyse a donc bien quelque chose à y trouver. Il remplace le bouton « Tester un
              exemple », qui n'ouvrait qu'une boîte « pas d'exemple disponible » depuis le premier
              jour. */}
          <ApportTexte texte={consigne} onChange={setConsigne} onSourceNote={setOrigineTexte} proposer={proposerExemple} disabled={loading} />
        </div>

        {origineTexte && SOURCES_TEXTE[origineTexte] && (
          <span style={{ fontSize: '11.5px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#6366f1', flexShrink: 0 }} />
            {SOURCES_TEXTE[origineTexte]}
          </span>
        )}

        <textarea
          value={consigne}
          onChange={e => setConsigne(e.target.value)}
          placeholder="Collez ici une consigne à analyser — une seule consigne, pas un exercice entier…"
          disabled={loading}
          style={{
            width: '100%', minHeight: '100px', padding: '10px 12px',
            fontSize: '13px', lineHeight: 1.6, color: '#1e293b',
            border: '1px solid #cbd5e1', borderRadius: '6px',
            resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box',
            background: loading ? '#f8fafc' : '#fff',
          }}
        />

        {/* Les cinq axes — EN LECTURE SEULE, à la place qu'occupent les cases à cocher de l'écran
            Ambiguïtés. Le professeur doit savoir sur quoi sa consigne est jugée AVANT de cliquer :
            sinon le rapport arrive avec des étiquettes qu'il découvre. */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'inline-flex', alignItems: 'center' }}>
            Ce qu'aSchool examine
            <InfoGuide {...aideConsigne('axes')} />
          </label>
          <ul style={{ margin: 0, padding: '0 0 0 20px', listStyle: 'disc outside', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {AXES_CONSIGNE.map(a => (
              <li key={a.label} title={a.description} style={{ display: 'list-item', fontSize: '13px', lineHeight: 1.5, color: '#1e293b' }}>
                {a.label}
              </li>
            ))}
          </ul>
          <span style={{ fontSize: '11.5px', color: '#94a3b8' }}>
            Les cinq axes sont examinés à chaque analyse — ils ne se décochent pas.
          </span>
        </div>

        {resultat && (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={reinitialiser}
              title="Effacer et analyser une nouvelle consigne"
              style={{ padding: '5px 12px', fontSize: '12px', background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '6px', cursor: 'pointer' }}
            >
              Nouvelle consigne
            </button>
          </div>
        )}
      </div>
    </div>
  )

  // ── COLONNE DE DROITE : le rapport, DANS SA MISE EN FORME D'ORIGINE — il est seulement déplacé
  // de dessous le formulaire à côté de lui. Avant l'analyse, le cadre en pointillés dit où le
  // résultat arrivera, comme les écrans Activité et Ambiguïtés. ──
  const nbPoints = resultat && Array.isArray(resultat.analyses) ? resultat.analyses.length : 0
  const colonneRapport = (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#1f2937', display: 'inline-flex', alignItems: 'center', gap: 7 }}>
          <IconAnalyser />
          Rapport d'analyse
          <InfoGuide {...aideConsigne(resultat ? 'sortie' : 'rapport')} />
        </h2>
        {resultat && (
          <span style={{ fontSize: 12, fontWeight: 600, borderRadius: 99, padding: '1px 10px',
            color: nbPoints > 0 ? '#b45309' : '#166534',
            background: nbPoints > 0 ? '#fef3c7' : '#dcfce7',
            border: `1px solid ${nbPoints > 0 ? '#fcd34d' : '#86efac'}` }}>
            {nbPoints === 0
              ? 'Consigne claire'
              : `${nbPoints} point${nbPoints > 1 ? 's' : ''} à améliorer`}
          </span>
        )}
        {/* La sortie mise en forme du rapport — le même geste que « HTML » de l'activité : on voit
            la page telle qu'elle s'imprime, sans quitter aSchool. */}
        {resultat && (
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setApercu(documentDepuisHtml(rapportEnHtml(resultat)))}
            title="Voir le rapport mis en forme (aperçu, sans quitter aSchool)"
            style={{ marginLeft: 'auto' }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            HTML
          </button>
        )}
      </div>

      {/* Règle « sablier ET jauge » : l'appel IA montre la jauge, jamais un écran figé. */}
      {loading && (
        <JaugeAttente libelle="aSchool analyse votre consigne axe par axe…" />
      )}

      {!loading && !resultat && (
        <div style={{
          border: '1px dashed #cbd5e1', borderRadius: 8, background: '#f8fafc',
          color: '#94a3b8', fontSize: 14, textAlign: 'center', minHeight: 340,
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', gap: 12, padding: '48px 24px',
        }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          <span>Ici s'affichera votre rapport.</span>
        </div>
      )}

      {resultat && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

          {/* Verdict */}
          {nbPoints === 0 ? (
            <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#166534', lineHeight: 1.6 }}>
              <strong>Consigne claire</strong> — {resultat.verdict}
            </div>
          ) : (
            <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#92400e', lineHeight: 1.6 }}>
              <strong>{nbPoints} point{nbPoints > 1 ? 's' : ''} à améliorer</strong> — {resultat.verdict}
            </div>
          )}

          {/* Une carte par point à améliorer */}
          {nbPoints > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {resultat.analyses.map((a, i) => {
                const c = couleurAxe(a.axe)
                const sc = SEVERITE_COLOR[a.severite] || SEVERITE_COLOR['Modérée']
                return (
                  <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
                    {/* En-tête carte */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', borderBottom: '1px solid #f1f5f9', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: c.text, background: c.bg, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '2px 10px', whiteSpace: 'nowrap' }}>
                        {a.axe}
                      </span>
                      <span style={{ fontSize: '10px', fontWeight: 700, color: sc.text, background: sc.bg, borderRadius: '10px', padding: '2px 8px', whiteSpace: 'nowrap' }}>
                        {a.severite}
                      </span>
                    </div>
                    {/* Corps carte */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '12px 14px' }}>
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                          Extrait problématique
                        </div>
                        <div style={{ fontSize: '13px', color: '#374151', fontStyle: 'italic', background: '#fafafa', borderLeft: '3px solid #e2e8f0', padding: '6px 10px', borderRadius: '3px' }}>
                          « {a.extrait} »
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                          Problème identifié
                        </div>
                        <div style={{ fontSize: '13px', color: '#374151', lineHeight: 1.5 }}>{a.probleme}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: '#166534', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                          Suggestion
                        </div>
                        <div style={{ fontSize: '13px', color: '#166534', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '5px', padding: '8px 10px', lineHeight: 1.5 }}>
                          {a.conseil}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* Version optimisée — ce que le prof vient chercher */}
          <div style={{ background: '#fff', border: '2px solid #6366f1', borderRadius: '8px', padding: '16px 18px' }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#6366f1', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>
              Consigne optimisée
            </div>
            <div style={{ fontSize: '14px', color: '#1e293b', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
              {resultat.version_optimisee}
            </div>
          </div>

        </div>
      )}
    </div>
  )

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

      {/* Barre de titre fixe. Plus d'onglets : « Comment ça marche » est passé dans le bouton du
          header (registre `guidesParPage` d'App.jsx), l'écran n'a plus qu'une seule chose à
          montrer — le formulaire. */}
      <div style={{
        display: 'flex', alignItems: 'center',
        borderBottom: '2px solid #e2e8f0',
        background: '#fff', padding: '0 24px', gap: '4px', flexShrink: 0,
      }}>
        <span
          title="Analyser la qualité didactique d'une consigne isolée"
          style={{ padding: '12px 16px', fontSize: '13px', fontWeight: 600, color: 'var(--bordeaux)', whiteSpace: 'nowrap',
                   display: 'inline-flex', alignItems: 'center', gap: 7 }}
        >
          <IconConsigne />
          Analyser une consigne
        </span>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Le volet ne se replie que s'il y a quelque chose dedans : avant l'analyse, un bouton
              « Cacher le rapport » désignerait un cadre vide. */}
          {resultat && (
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setResultatCache(c => !c)}
              title={resultatCache
                ? 'Réafficher le rapport à droite'
                : 'Cacher le rapport — le formulaire prend toute la largeur'}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                {resultatCache
                  ? <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
                  : <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>}
              </svg>
              {resultatCache ? 'Afficher le rapport' : 'Cacher le rapport'}
            </button>
          )}

          <button
            className="btn-primary"
            onClick={analyser}
            disabled={loading || !!empeche}
            title={empeche || 'Analyser la qualité didactique de la consigne'}
          >
            {loading ? <Spinner /> : <IconAnalyser />}
            {loading ? 'Analyse en cours…' : 'Analyser la consigne'}
          </button>
        </div>
      </div>

      {/* Deux colonnes redimensionnables, comme les écrans Activité et Ambiguïtés : le formulaire à
          gauche, le rapport à droite. Poignée à tirer, largeur mémorisée, double-clic pour
          rééquilibrer. Rapport caché : le formulaire prend toute la largeur. */}
      <div style={{ flex: 1, minHeight: 0 }}>
        {resultatCache
          ? <div className="split-pane"><div className="split-col split-col-flex">{colonneFormulaire}</div></div>
          : <SplitPane storageKey="consigne-split-v1" gauche={colonneFormulaire} droite={colonneRapport} />}
      </div>

      {/* Aperçu mis en forme — composant partagé (même modale que l'activité). */}
      <ApercuHtmlModale corps={apercu} onFermer={() => setApercu(null)}
        titreImpression="Imprimer ce rapport mis en forme" />

      {/* Dialog validation */}
      {alertDialog && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={() => setAlertDialog(null)}
        >
          <div
            style={{ background: '#fff', borderRadius: '10px', padding: '24px 28px', maxWidth: '420px', width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}
            onClick={e => e.stopPropagation()}
          >
            <p style={{ fontSize: '13.5px', color: '#475569', margin: '0 0 20px', lineHeight: 1.6, whiteSpace: 'pre-line' }}>
              {alertDialog}
            </p>
            <button
              onClick={() => setAlertDialog(null)}
              style={{ background: 'var(--bordeaux)', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 20px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
            >
              OK
            </button>
          </div>
        </div>
      )}

    </div>
  )
}
