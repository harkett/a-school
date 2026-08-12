// Écran « Équité d'une évaluation ». Le troisième frère d'Ambiguïtés et de Consigne, bâti sur le
// premier : le prof COCHE les biais à faire chercher, aSchool ne remonte que ceux-là. Les biais ne
// sont pas écrits ici — ils sont LUS EN BASE (catalogue `equite_criteres`, servi par
// /equite/criteres), à la même source que celle sur laquelle le serveur refusera ou acceptera.
//
// DEUX DIFFÉRENCES avec l'écran Ambiguïtés, et une seule est visible :
//   • une SECONDE zone de texte, le barème, facultative — trois des neuf biais ne se voient que
//     là (barème décalé, double peine, question qui verrouille). Sans elle, ils seraient cochés
//     pour rien ;
//   • pas de case « Autre » ni de champ libre : l'équité se juge sur des motifs connus, et un
//     motif écrit à la main ne serait vérifiable par rien.
//
// CE QUE CET ÉCRAN NE PROMET PAS : les biais du correcteur (effet de halo, écarts entre
// correcteurs, dérive de sévérité). Ils ne se voient pas dans un sujet collé. L'aide leur consacre
// une entrée entière (`correcteur` dans aideEquite.js) plutôt que de les passer sous silence.
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_LONG, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog.js'
import ApportTexte from './contenus/ApportTexte.jsx'
import JaugeAttente from './JaugeAttente.jsx'
import SplitPane from './SplitPane.jsx'
import ApercuHtmlModale from './ApercuHtmlModale.jsx'
import InfoGuide from './InfoGuide.jsx'
import { aideEquite } from '../utils/aideEquite.js'
import { documentDepuisHtml } from '../utils/apercuHtml.js'
import { isTexteGibberish } from '../utils/texteGibberish.js'
import { IconAnalyser, IconEquite, Spinner } from './icones.jsx'
import Aschool from './Aschool.jsx'

// La couleur d'un biais — l'écran l'affiche, et la sortie mise en forme la reprend telle quelle.
// Deux rendus, une seule palette, tous deux dans ce fichier : rien à exporter. Les clés sont les
// `label` du catalogue ; un biais renommé en base retombe sur la couleur neutre, il ne disparaît
// pas de l'écran.
const BIAIS_COLOR = {
  'Savoir non enseigné':     { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' },
  'Culture et milieu':       { bg: '#f3e8ff', text: '#6b21a8', border: '#d8b4fe' },
  'Stéréotype':              { bg: '#fce7f3', text: '#9d174d', border: '#f9a8d4' },
  'Poids de la lecture':     { bg: '#e0f2fe', text: '#075985', border: '#7dd3fc' },
  'Matériel supposé':        { bg: '#fef3c7', text: '#92400e', border: '#fde68a' },
  'Barème absent ou décalé': { bg: '#ffedd5', text: '#9a3412', border: '#fdba74' },
  'Double peine':            { bg: '#ede9fe', text: '#5b21b6', border: '#c4b5fd' },
  'Question qui verrouille': { bg: '#e0e7ff', text: '#3730a3', border: '#a5b4fc' },
  'Temps insuffisant':       { bg: '#ccfbf1', text: '#115e59', border: '#5eead4' },
}

const DEFAULT_COLOR = { bg: '#f1f5f9', text: '#334155', border: '#cbd5e1' }

const couleurBiais = (label) => BIAIS_COLOR[label] || DEFAULT_COLOR

// D'où vient le texte de la zone, quand il n'a pas été tapé au clavier — la rangée d'apport le
// signale, l'écran l'affiche (même principe que les écrans Ambiguïtés, Consigne et Séance).
const SOURCES_TEXTE = {
  txt:     "Texte importé d'un fichier",
  image:   "Texte extrait d'une image",
  pdf:     "Texte extrait d'un PDF",
  dictee:  'Texte issu de votre dictée',
  exemple: "Évaluation d'exemple écrite par aSchool",
}

// Le rapport, écrit EN PAGE pour l'aperçu mis en forme (bouton « HTML », comme ses deux frères).
// Il reprend les couleurs de l'écran — lues à la même source — parce qu'elles portent du sens : le
// biais se reconnaît à sa teinte, la correction au vert de ce qui est prêt à appliquer.
// `print-color-adjust` demande à l'imprimante de les garder : sans lui, la plupart des navigateurs
// suppriment les fonds pour épargner l'encre, et la feuille sortirait grise.
//
// Tout ce qui vient du modèle est ÉCHAPPÉ ici. Le nettoyage de sortie (DOMPurify, dans
// apercuHtml.js) reste le dernier filet, jamais le premier.
function ech(v) {
  return String(v ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const COULEURS_A_L_IMPRESSION = '-webkit-print-color-adjust:exact;print-color-adjust:exact'

function etiquette(texte, couleur) {
  return `<div style="font-size:11px;font-weight:700;color:${couleur};text-transform:uppercase;`
       + `letter-spacing:.04em;margin:12px 0 4px">${texte}</div>`
}

function rapportEnHtml(resultat) {
  const n = Array.isArray(resultat.biais) ? resultat.biais.length : 0
  const blocs = ["<h1>Analyse d'équité</h1>"]

  const v = n === 0
    ? { fond: '#f0fdf4', bord: '#86efac', texte: '#166534', titre: 'Aucun biais repéré' }
    : { fond: '#fffbeb', bord: '#fcd34d', texte: '#92400e',
        titre: `${n} biais repéré${n > 1 ? 's' : ''}` }
  blocs.push(`<div style="background:${v.fond};border:1px solid ${v.bord};border-radius:6px;`
    + `padding:12px 16px;color:${v.texte};margin:14px 0;${COULEURS_A_L_IMPRESSION}">`
    + `<strong>${v.titre}</strong> — ${ech(resultat.verdict)}</div>`)

  ;(resultat.biais || []).forEach((b, i) => {
    const c = couleurBiais(b.critere)
    blocs.push(`<div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;`
      + `margin:0 0 10px;page-break-inside:avoid;${COULEURS_A_L_IMPRESSION}">`
      + `<span style="display:inline-block;font-size:11px;font-weight:700;color:${c.text};`
      + `background:${c.bg};border:1px solid ${c.border};border-radius:12px;padding:2px 10px;`
      + `${COULEURS_A_L_IMPRESSION}">${i + 1}. ${ech(b.critere)}</span>`
      // Pas d'extrait : le biais porte sur l'ensemble (temps annoncé, barème absent). Le bloc
      // « Passage en cause » saute alors, plutôt que d'afficher des guillemets vides.
      + (b.extrait
          ? etiquette('Passage en cause', '#94a3b8')
            + `<div style="font-style:italic;color:#374151;background:#fafafa;`
            + `border-left:3px solid #e2e8f0;padding:6px 10px;border-radius:3px;`
            + `${COULEURS_A_L_IMPRESSION}">« ${ech(b.extrait)} »</div>`
          : '')
      + etiquette('Qui est pénalisé', '#94a3b8')
      + `<div style="color:#374151">${ech(b.consequence)}</div>`
      + etiquette('Correction', '#166534')
      + `<div style="color:#166534;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:5px;`
      + `padding:8px 10px;${COULEURS_A_L_IMPRESSION}">${ech(b.correction)}</div>`
      + `</div>`)
  })
  return blocs.join('')
}

export default function Equite() {
  const [texte, setTexte]         = useState('')
  const [bareme, setBareme]       = useState('')
  const [coches, setCoches]       = useState([])
  const [loading, setLoading]     = useState(false)

  const [alertDialog, setAlertDialog] = useState(null)
  const [origineTexte, setOrigineTexte] = useState(null)
  const [resultat, setResultat]   = useState(null)
  // Le rapport occupe la colonne de droite : on peut la replier pour rendre toute la largeur au
  // formulaire (même geste que « Cacher le détail » des pages listes).
  const [resultatCache, setResultatCache] = useState(false)
  // Aperçu mis en forme du rapport : chaîne = ouvert, null = fermé. Éphémère, jamais en base.
  const [apercu, setApercu] = useState(null)

  // ── Les biais : catalogue lu en base, aucune case pré-cochée (règle maison) ──
  const { data: criteres = [], error: criteresErreur } = useQuery({
    queryKey: ['equite', 'criteres'],
    queryFn: async () => {
      const d = await lireReponse(await apiFetch('/api/equite/criteres', { credentials: 'include' }, TIMEOUT_STD))
      return Array.isArray(d) ? d : []
    },
  })
  useEffect(() => { if (criteresErreur) showError(messagePourEcran(criteresErreur)) }, [criteresErreur])

  function basculerCritere(code) {
    setCoches(l => l.includes(code) ? l.filter(c => c !== code) : [...l, code])
  }

  // « Propose-moi un exemple » — aSchool écrit À LA DEMANDE une évaluation de démonstration pour
  // le couple du prof, ancrée sur son référentiel, avec de vrais défauts d'équité dedans. Un clic,
  // un appel, rien de rangé en base. La mécanique commune (confirmation de remplacement, sablier +
  // jauge, pastille d'origine) vit dans ApportTexte ; ici seulement l'appel serveur.
  const proposerExemple = {
    label: 'Propose-moi un exemple',
    // La bulle du bouton se lit dans le catalogue, comme les « i » : une explication, une place.
    title: aideEquite('exemple').court,
    jauge: "aSchool lit le programme officiel de votre niveau et écrit une évaluation d'exemple…",
    note: 'exemple',
    action: async () => {
      try {
        const res = await apiFetch('/api/equite/exemple-genere', {
          method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}),
        }, TIMEOUT_LONG)
        const d = await lireReponse(res)
        if (d.available && d.texte) return d.texte
        // Pas de référentiel pour ce niveau, rien d'assez pertinent, ou le modèle lui-même a
        // refusé d'écrire faute d'extraits parlants : on n'invente rien, on le dit.
        showError(d.message || "Pas d'exemple possible pour le moment pour votre niveau (programme officiel pas encore chargé).\n\nCollez votre propre évaluation dans la zone de texte.")
        return null
      } catch (err) {
        showError(`Écriture de l'évaluation d'exemple impossible.\n\n${messagePourEcran(err)}`)
        return null
      }
    },
  }

  // Le bouton reste gris tant que l'analyse n'a pas de quoi être lancée — et sa bulle d'aide dit
  // LEQUEL des motifs bloque, jamais un simple « indisponible ». Le barème n'y figure pas : il est
  // facultatif, et l'analyse tourne sans lui.
  const empeche =
    !texte.trim()                          ? "Collez une évaluation avant de lancer l'analyse."
    : texte.trim().split(/\s+/).length < 3  ? "L'évaluation est trop courte — collez le sujet complet."
    : isTexteGibberish(texte)               ? "Le texte saisi ne ressemble pas à une évaluation."
    : coches.length === 0                   ? 'Cochez au moins un biais à rechercher.'
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
      const res = await apiFetch('/api/detect-equite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        // Le couple se résout EN BASE côté serveur : il ne part pas d'ici.
        body: JSON.stringify({ texte: texte.trim(), bareme: bareme.trim() || null, criteres: coches }),
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
    setTexte('')
    setBareme('')
    setOrigineTexte(null)
  }

  // ── COLONNE DE GAUCHE : tout ce que le professeur remplit — l'évaluation, son barème, et les
  // biais à chercher. Elle scrolle seule (classe .split-col). ──
  const colonneFormulaire = (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <p style={{ fontSize: '13px', color: '#64748b', margin: 0, lineHeight: 1.6 }}>
        Collez une évaluation. <Aschool /> cherche ce qu'elle demande <em>en plus</em> de la compétence visée — et qui n'est pas également disponible à tous vos élèves.
      </p>

      {/* Zone de saisie */}
      <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'inline-flex', alignItems: 'center' }}>
            Votre évaluation
            <InfoGuide {...aideEquite('evaluation')} />
          </label>

          {/* Cinq façons d'apporter le sujet, en plus du clavier. Le cinquième bouton l'écrit
              lui-même : une évaluation VOLONTAIREMENT inéquitable, écrite pour la démonstration —
              l'analyse a donc bien quelque chose à y trouver. */}
          <ApportTexte texte={texte} onChange={setTexte} onSourceNote={setOrigineTexte} proposer={proposerExemple} disabled={loading} />
        </div>

        {origineTexte && SOURCES_TEXTE[origineTexte] && (
          <span style={{ fontSize: '11.5px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#6366f1', flexShrink: 0 }} />
            {SOURCES_TEXTE[origineTexte]}
          </span>
        )}

        <textarea
          value={texte}
          onChange={e => setTexte(e.target.value)}
          placeholder="Collez ici l'évaluation à relire — le sujet complet, questions et documents…"
          disabled={loading}
          style={{
            width: '100%', minHeight: '120px', padding: '10px 12px',
            fontSize: '13px', lineHeight: 1.6, color: '#1e293b',
            border: '1px solid #cbd5e1', borderRadius: '6px',
            resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box',
            background: loading ? '#f8fafc' : '#fff',
          }}
        />

        {/* Le barème — SÉPARÉ du sujet, et facultatif. Trois des neuf biais ne se voient que là ;
            collé au milieu de l'énoncé, il serait lu comme une question de plus. */}
        <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'inline-flex', alignItems: 'center' }}>
          Votre barème
          <span style={{ textTransform: 'none', fontWeight: 500, color: '#94a3b8', marginLeft: 6 }}>(facultatif)</span>
          <InfoGuide {...aideEquite('bareme')} />
        </label>
        <textarea
          value={bareme}
          onChange={e => setBareme(e.target.value)}
          placeholder="Points par question, critères de notation… Laissez vide si vous n'en avez pas."
          disabled={loading}
          style={{
            width: '100%', minHeight: '60px', padding: '10px 12px',
            fontSize: '13px', lineHeight: 1.6, color: '#1e293b',
            border: '1px solid #cbd5e1', borderRadius: '6px',
            resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box',
            background: loading ? '#f8fafc' : '#fff',
          }}
        />

        {/* Les biais — ce que le prof demande de chercher. Rien n'est coché au départ. */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {/* Le libellé tient dans UN SEUL <span>, et ce n'est pas cosmétique : le <label> est en
              `inline-flex`, donc chacun de ses enfants devient un bloc et les espaces qui les
              séparent disparaissent — « Ce qu'aSchooldoit chercher ». Regroupé, le texte redevient
              du texte, avec ses espaces. */}
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'inline-flex', alignItems: 'center' }}>
            <span>Ce qu'<Aschool /> doit chercher</span>
            <InfoGuide {...aideEquite('criteres')} />
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 20px' }}>
            {criteres.map(c => (
              <label
                key={c.code}
                title={c.description}
                style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: '#334155', cursor: loading ? 'not-allowed' : 'pointer' }}
              >
                <input
                  type="checkbox"
                  checked={coches.includes(c.code)}
                  onChange={() => basculerCritere(c.code)}
                  disabled={loading}
                  style={{ cursor: loading ? 'not-allowed' : 'pointer' }}
                />
                {c.label}
              </label>
            ))}
          </div>

          {/* La question que le prof se pose en lisant cette liste — « et l'effet de halo ? ». Elle
              a sa réponse dans l'aide ; ce lien évite qu'il conclue à un oubli. */}
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '11.5px', color: '#94a3b8' }}>
            Ces biais sont ceux du SUJET — pas ceux de la correction
            <InfoGuide {...aideEquite('correcteur')} />
          </span>
        </div>

      </div>
    </div>
  )

  // ── COLONNE DE DROITE : le rapport. Avant l'analyse, le cadre en pointillés dit où le résultat
  // arrivera, comme les écrans Ambiguïtés et Consigne. ──
  const nbBiais = resultat && Array.isArray(resultat.biais) ? resultat.biais.length : 0
  const colonneRapport = (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#1f2937', display: 'inline-flex', alignItems: 'center', gap: 7 }}>
          <IconAnalyser />
          Rapport d'équité
          <InfoGuide {...aideEquite(resultat ? 'sortie' : 'rapport')} />
        </h2>
        {resultat && (
          <span style={{ fontSize: 12, fontWeight: 600, borderRadius: 99, padding: '1px 10px',
            color: nbBiais > 0 ? '#b45309' : '#166534',
            background: nbBiais > 0 ? '#fef3c7' : '#dcfce7',
            border: `1px solid ${nbBiais > 0 ? '#fcd34d' : '#86efac'}` }}>
            {nbBiais === 0
              ? 'Aucun biais repéré'
              : `${nbBiais} biais repéré${nbBiais > 1 ? 's' : ''}`}
          </span>
        )}
        {/* La sortie mise en forme du rapport — le même geste que « HTML » de ses deux frères. */}
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
        <JaugeAttente libelle="aSchool relit votre évaluation biais par biais…" />
      )}

      {!loading && !resultat && (
        <div style={{
          border: '1px dashed #cbd5e1', borderRadius: 8, background: '#f8fafc',
          color: '#94a3b8', fontSize: 14, textAlign: 'center', minHeight: 340,
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', gap: 12, padding: '48px 24px',
        }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="4" x2="12" y2="21"/><line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="4" y1="7" x2="20" y2="7"/><circle cx="12" cy="4" r="1.4"/>
            <path d="M4 7 1.5 13a2.5 2.5 0 0 0 5 0z"/><path d="M20 7l-2.5 6a2.5 2.5 0 0 0 5 0z"/>
          </svg>
          <span>Ici s'affichera votre rapport.</span>
        </div>
      )}

      {resultat && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

          {/* Verdict. « Aucun biais repéré » ne dit pas « évaluation parfaite » : il dit que sur
              les biais COCHÉS, rien n'a été trouvé. La phrase le rappelle. */}
          {nbBiais === 0 ? (
            <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#166534', lineHeight: 1.6 }}>
              <strong>Aucun biais repéré</strong> — {resultat.verdict}
            </div>
          ) : (
            <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#92400e', lineHeight: 1.6 }}>
              <strong>{nbBiais} biais repéré{nbBiais > 1 ? 's' : ''}</strong> — {resultat.verdict}
            </div>
          )}

          {/* Une carte par biais */}
          {nbBiais > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {resultat.biais.map((b, i) => {
                const c = couleurBiais(b.critere)
                return (
                  <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
                    {/* En-tête carte */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', borderBottom: '1px solid #f1f5f9', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: c.text, background: c.bg, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '2px 10px', whiteSpace: 'nowrap' }}>
                        {b.critere}
                      </span>
                    </div>
                    {/* Corps carte */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '12px 14px' }}>
                      {/* Le passage en cause — absent quand le biais porte sur l'ensemble (temps
                          annoncé, barème absent) : le bloc saute plutôt que d'afficher du vide. */}
                      {b.extrait && (
                        <div>
                          <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                            Passage en cause
                          </div>
                          <div style={{ fontSize: '13px', color: '#374151', fontStyle: 'italic', background: '#fafafa', borderLeft: '3px solid #e2e8f0', padding: '6px 10px', borderRadius: '3px' }}>
                            « {b.extrait} »
                          </div>
                        </div>
                      )}
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                          Qui est pénalisé
                        </div>
                        <div style={{ fontSize: '13px', color: '#374151', lineHeight: 1.5 }}>{b.consequence}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: '#166534', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                          Correction
                        </div>
                        <div style={{ fontSize: '13px', color: '#166534', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '5px', padding: '8px 10px', lineHeight: 1.5 }}>
                          {b.correction}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

        </div>
      )}
    </div>
  )

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

      {/* Barre de titre fixe. Pas d'onglets : « Comment ça marche » vit dans le bouton du header
          (registre `guidesParPage` d'App.jsx), comme chez ses deux frères. */}
      <div style={{
        display: 'flex', alignItems: 'center',
        borderBottom: '2px solid #e2e8f0',
        background: '#fff', padding: '0 24px', gap: '4px', flexShrink: 0,
      }}>
        <span
          title="Repérer ce qui pénalise certains élèves pour une raison étrangère à ce qui est évalué"
          style={{ padding: '12px 16px', fontSize: '13px', fontWeight: 600, color: 'var(--bordeaux)', whiteSpace: 'nowrap',
                   display: 'inline-flex', alignItems: 'center', gap: 7 }}
        >
          <IconEquite />
          Équité d'une évaluation
        </span>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* « Nouvelle évaluation » vit ICI, dans la barre, et non plus sous le formulaire : les
              boutons d'un écran se cherchent à un seul endroit, alignés et de même hauteur. En bas
              de la colonne de gauche, il fallait faire défiler pour le retrouver. Comme les deux
              autres, il n'apparaît qu'une fois le rapport là — avant, il n'effacerait rien. */}
          {resultat && (
            <button
              type="button"
              className="btn-secondary"
              onClick={reinitialiser}
              title="Effacer l'évaluation, le barème et le rapport — repartir d'une page blanche"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 2v6h6"/>
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L3 8"/>
              </svg>
              Nouvelle évaluation
            </button>
          )}

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
            title={empeche || "Chercher les biais d'équité de cette évaluation"}
          >
            {loading ? <Spinner /> : <IconAnalyser />}
            {loading ? 'Analyse en cours…' : "Analyser l'évaluation"}
          </button>
        </div>
      </div>

      {/* Deux colonnes redimensionnables, comme ses deux frères : le formulaire à gauche, le
          rapport à droite. Poignée à tirer, largeur mémorisée, double-clic pour rééquilibrer.
          Rapport caché : le formulaire prend toute la largeur. */}
      <div style={{ flex: 1, minHeight: 0 }}>
        {resultatCache
          ? <div className="split-pane"><div className="split-col split-col-flex">{colonneFormulaire}</div></div>
          : <SplitPane storageKey="equite-split-v1" gauche={colonneFormulaire} droite={colonneRapport} />}
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
