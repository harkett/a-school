// Écran « Détecter les ambiguïtés ». Le prof COCHE les types à faire relire : l'IA ne cherche
// que ceux-là. Les critères ne sont plus écrits ici — ils sont LUS EN BASE (catalogue
// `ambiguite_criteres`, servi par /ambiguites/criteres), à la même source que celle sur
// laquelle le serveur refusera ou acceptera. La case « Autre » ouvre un champ libre : ce que
// le prof y écrit part au modèle comme un point de vigilance, jamais comme une consigne.
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_LONG, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog.js'
import AmbiguitesResultat, { TYPE_COLOR, DEFAULT_COLOR } from './AmbiguitesResultat.jsx'
import ApportTexte from './contenus/ApportTexte.jsx'
import JaugeAttente from './JaugeAttente.jsx'
import SplitPane from './SplitPane.jsx'
import ApercuHtmlModale from './ApercuHtmlModale.jsx'
import InfoGuide from './InfoGuide.jsx'
import { aideAmbiguites } from '../utils/aideAmbiguites.js'
import { documentDepuisHtml } from '../utils/apercuHtml.js'
import { IconAmbiguites, IconAnalyser, Spinner } from './icones.jsx'




// Le rapport, écrit EN PAGE pour l'aperçu mis en forme (bouton « HTML », comme l'activité).
// Il reprend les couleurs de l'écran — celles de TYPE_COLOR, lues à la même source — parce
// qu'elles portent du sens : le type d'ambiguïté se reconnaît à sa teinte, et la reformulation
// au vert de ce qui est prêt à recopier. `print-color-adjust` demande à l'imprimante de les
// garder : sans lui, la plupart des navigateurs suppriment les fonds pour épargner l'encre, et
// la feuille sortirait grise.
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
  const n = Array.isArray(resultat.ambiguites) ? resultat.ambiguites.length : 0
  const blocs = ["<h1>Rapport d'ambiguïtés</h1>"]

  // Le verdict, dans la couleur qu'il a à l'écran : vert s'il n'y a rien à corriger, ambre sinon.
  const v = n === 0
    ? { fond: '#f0fdf4', bord: '#86efac', texte: '#166534', titre: 'Énoncé clair' }
    : { fond: '#fffbeb', bord: '#fcd34d', texte: '#92400e',
        titre: `${n} ambiguïté${n > 1 ? 's' : ''} détectée${n > 1 ? 's' : ''}` }
  blocs.push(`<div style="background:${v.fond};border:1px solid ${v.bord};border-radius:6px;`
    + `padding:12px 16px;color:${v.texte};margin:14px 0;${COULEURS_A_L_IMPRESSION}">`
    + `<strong>${v.titre}</strong> — ${ech(resultat.verdict)}</div>`)

  ;(resultat.ambiguites || []).forEach((a, i) => {
    const c = TYPE_COLOR[a.type] || DEFAULT_COLOR
    blocs.push(`<div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;`
      + `margin:0 0 10px;page-break-inside:avoid;${COULEURS_A_L_IMPRESSION}">`
      + `<span style="display:inline-block;font-size:11px;font-weight:700;color:${c.text};`
      + `background:${c.bg};border:1px solid ${c.border};border-radius:12px;padding:2px 10px;`
      + `${COULEURS_A_L_IMPRESSION}">${i + 1}. ${ech(a.type)}</span>`
      + etiquette('Extrait problématique', '#94a3b8')
      + `<div style="font-style:italic;color:#374151;background:#fafafa;border-left:3px solid #e2e8f0;`
      + `padding:6px 10px;border-radius:3px;${COULEURS_A_L_IMPRESSION}">« ${ech(a.extrait)} »</div>`
      + etiquette("Risque pour l'élève", '#94a3b8')
      + `<div style="color:#374151">${ech(a.risque)}</div>`
      + etiquette('Reformulation corrigée', '#166534')
      + `<div style="color:#166534;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:5px;`
      + `padding:8px 10px;${COULEURS_A_L_IMPRESSION}">${ech(a.reformulation)}</div>`
      + `</div>`)
  })
  return blocs.join('')
}

function isTexteGibberish(t) {
  const words = t.trim().split(/\s+/).filter(w => w.length > 2)
  if (words.length < 2) return false
  const vowels = /[aeiouyàâäéèêëîïôöùûüæœAEIOUYÀÂÄÉÈÊËÎÏÔÖÙÛÜÆŒ]/
  let suspect = 0
  for (const word of words) {
    const alpha = word.replace(/[^a-zA-ZÀ-ÿ]/g, '')
    if (alpha.length > 8) {
      const vRatio = alpha.split('').filter(c => vowels.test(c)).length / alpha.length
      if (vRatio < 0.15) suspect++
    }
  }
  return suspect / words.length > 0.25
}

// Le seul code que l'écran connaisse : celui qui ouvre le champ de texte libre. Les libellés,
// l'ordre et le nombre de critères appartiennent à la base.
const CODE_CRITERE_LIBRE = 'autre'
const CRITERE_LIBRE_MAX = 200

// D'où vient le texte de la zone, quand il n'a pas été tapé au clavier — la rangée d'apport
// le signale, l'écran l'affiche (même principe que les écrans Séance et Séquence).
const SOURCES_TEXTE = {
  txt:    'Texte importé d\'un fichier',
  image:  'Texte extrait d\'une image',
  pdf:    'Texte extrait d\'un PDF',
  dictee: 'Texte issu de votre dictée',
  exemple: "Énoncé d'exemple écrit par aSchool",
}

export default function Ambiguites() {
  const [texte, setTexte]         = useState('')
  const [loading, setLoading]     = useState(false)

  const [alertDialog, setAlertDialog] = useState(null)
  const [origineTexte, setOrigineTexte] = useState(null)
  const [resultat, setResultat]   = useState(null)
  // Le rapport occupe la colonne de droite : on peut la replier pour rendre toute la
  // largeur au formulaire (même geste que « Cacher le détail » des pages listes).
  const [resultatCache, setResultatCache] = useState(false)
  // Aperçu mis en forme du rapport : chaîne = ouvert, null = fermé. Éphémère, jamais en base.
  const [apercu, setApercu] = useState(null)

  // ── Les critères : catalogue lu en base, aucune case pré-cochée (règle maison) ──
  const { data: criteres = [], error: criteresErreur } = useQuery({
    queryKey: ['ambiguites', 'criteres'],
    queryFn: async () => {
      const d = await lireReponse(await apiFetch('/api/ambiguites/criteres', { credentials: 'include' }, TIMEOUT_STD))
      return Array.isArray(d) ? d : []
    },
  })
  useEffect(() => { if (criteresErreur) showError(messagePourEcran(criteresErreur)) }, [criteresErreur])

  // « Propose-moi un exemple » — aSchool écrit À LA DEMANDE un énoncé de démonstration pour le
  // couple du prof, ancré sur son référentiel, avec de vrais défauts dedans. Un clic, un appel,
  // rien de rangé en base : un texte de démonstration n'a aucune raison d'être le même deux fois.
  // La mécanique commune (confirmation de remplacement, sablier + jauge, pastille d'origine) vit
  // dans ApportTexte ; ici seulement l'appel serveur.
  const proposerExemple = {
    label: 'Propose-moi un exemple',
    // La bulle du bouton se lit dans le catalogue, comme les « i » : une explication, une place.
    title: aideAmbiguites('exemple').court,
    jauge: "aSchool lit le programme officiel de votre niveau et écrit un énoncé d'exemple…",
    note: 'exemple',
    action: async () => {
      try {
        const res = await apiFetch('/api/ambiguites/exemple-genere', {
          method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}),
        }, TIMEOUT_LONG)
        const d = await lireReponse(res)
        if (d.available && d.texte) return d.texte
        // Pas de référentiel pour ce niveau, ou rien d'assez pertinent : on n'invente rien, on le dit.
        showError(d.message || "Pas d'exemple possible pour le moment pour votre niveau (programme officiel pas encore chargé).\n\nCollez votre propre énoncé dans la zone de texte.")
        return null
      } catch (err) {
        showError(`Écriture de l'exemple impossible.\n\n${messagePourEcran(err)}`)
        return null
      }
    },
  }

  const [coches, setCoches]         = useState([])
  const [critereLibre, setCritereLibre] = useState('')

  const autreCoche = coches.includes(CODE_CRITERE_LIBRE)
  const critereLibreManquant = autreCoche && !critereLibre.trim()
  // Le bouton reste gris tant que l'analyse n'a pas de quoi être lancée — et sa bulle d'aide
  // dit LEQUEL des trois motifs bloque, jamais un simple « indisponible ».
  const empeche =
    coches.length === 0      ? 'Cochez au moins un type d\'ambiguïté à rechercher.'
    : critereLibreManquant   ? 'Écrivez ce qu\'aSchool doit vérifier, ou décochez « Autre ».'
    : !texte.trim()          ? 'Collez un exercice ou un énoncé avant de lancer l\'analyse.'
    : null

  function basculerCritere(code) {
    setCoches(prev => prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code])
  }

  async function analyser() {
    if (!texte.trim()) {
      setAlertDialog('Collez un exercice ou un énoncé avant de lancer l\'analyse.')
      return
    }
    if (isTexteGibberish(texte)) {
      setAlertDialog('Le texte saisi ne ressemble pas à un énoncé pédagogique.\n\nCollez un vrai exercice, ou apportez-le depuis un fichier, une image, un PDF ou votre dictée.')
      return
    }
    setResultat(null)
    // Lancer l'analyse rouvre la colonne : sinon le rapport arriverait derrière un volet
    // fermé, et l'écran ne montrerait rien de ce qu'on vient de lui demander.
    setResultatCache(false)
    setLoading(true)
    try {
      const res = await apiFetch('/api/detect-ambiguites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        // Le couple se résout EN BASE côté serveur ; les critères, eux, sont ceux cochés ici
        // et re-validés là-bas sur la même table.
        body: JSON.stringify({
          texte: texte.trim(),
          criteres: coches,
          critere_libre: autreCoche ? critereLibre.trim() : null,
        }),
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
    setOrigineTexte(null)
    setCoches([])
    setCritereLibre('')
  }

  // ── COLONNE DE GAUCHE : tout ce que le professeur remplit — l'énoncé, d'où il vient, et
  // les types à faire chercher. Elle scrolle seule (classe .split-col). ──
  const colonneFormulaire = (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <p style={{ fontSize: '13px', color: '#64748b', margin: 0, lineHeight: 1.6 }}>
        Collez un exercice ou un énoncé. aSchool identifie les formulations ambiguës et vous propose des reformulations corrigées, prêtes à l'emploi.
      </p>

      {/* Zone de saisie */}
      <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'inline-flex', alignItems: 'center' }}>
            Votre exercice ou énoncé
            <InfoGuide {...aideAmbiguites('enonce')} />
          </label>

          {/* Cinq façons d'apporter l'énoncé, en plus du clavier. Le cinquième bouton écrit
              l'énoncé lui-même : c'est un énoncé VOLONTAIREMENT imparfait, écrit pour la
              démonstration — l'analyse a donc bien quelque chose à y trouver. */}
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
          placeholder="Collez ici votre exercice, vos questions ou votre consigne…"
          disabled={loading}
          style={{
            width: '100%', minHeight: '120px', padding: '10px 12px',
            fontSize: '13px', lineHeight: 1.6, color: '#1e293b',
            border: '1px solid #cbd5e1', borderRadius: '6px',
            resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box',
            background: loading ? '#f8fafc' : '#fff',
          }}
        />

        {/* Critères — ce que le prof demande de chercher. Rien n'est coché au départ. */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'inline-flex', alignItems: 'center' }}>
            Ce qu'aSchool doit chercher
            <InfoGuide {...aideAmbiguites('criteres')} />
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 20px' }}>
            {criteres.map(c => (
              <label
                key={c.code}
                title={c.description || 'Décrivez vous-même le point à vérifier'}
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

          {/* Le champ libre n'existe que si « Autre » est coché. */}
          {autreCoche && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '11.5px', color: '#64748b' }}>
              Votre point de vigilance
              <InfoGuide {...aideAmbiguites('autre')} />
            </span>
          )}
          {autreCoche && (
            <input
              type="text"
              value={critereLibre}
              onChange={e => setCritereLibre(e.target.value)}
              maxLength={CRITERE_LIBRE_MAX}
              disabled={loading}
              placeholder="Ex. : vérifie le vocabulaire inclusif"
              title="Ce point s'ajoute aux types cochés — aSchool le traite comme un point de vigilance"
              style={{
                width: '100%', padding: '8px 12px', fontSize: '13px', color: '#1e293b',
                border: `1px solid ${critereLibreManquant ? '#fca5a5' : '#cbd5e1'}`,
                borderRadius: '6px', boxSizing: 'border-box', fontFamily: 'inherit',
                background: loading ? '#f8fafc' : '#fff',
              }}
            />
          )}
        </div>

        {resultat && (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={reinitialiser}
              title="Effacer et analyser un nouvel énoncé"
              style={{ padding: '5px 12px', fontSize: '12px', background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '6px', cursor: 'pointer' }}
            >
              Nouvel énoncé
            </button>
          </div>
        )}
      </div>
    </div>
  )

  // ── COLONNE DE DROITE : le rapport, DANS SA MISE EN FORME D'ORIGINE (AmbiguitesResultat n'est
  // pas touché — il est seulement déplacé de dessous le formulaire à côté de lui). Avant
  // l'analyse, le cadre en pointillés dit où le résultat arrivera, comme l'écran Activité. ──
  const nbAmbiguites = resultat && Array.isArray(resultat.ambiguites) ? resultat.ambiguites.length : 0
  const colonneRapport = (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#1f2937', display: 'inline-flex', alignItems: 'center', gap: 7 }}>
          <IconAnalyser />
          Rapport d'analyse
          <InfoGuide {...aideAmbiguites(resultat ? 'sortie' : 'rapport')} />
        </h2>
        {resultat && (
          <span style={{ fontSize: 12, fontWeight: 600, borderRadius: 99, padding: '1px 10px',
            color: nbAmbiguites > 0 ? '#b45309' : '#166534',
            background: nbAmbiguites > 0 ? '#fef3c7' : '#dcfce7',
            border: `1px solid ${nbAmbiguites > 0 ? '#fcd34d' : '#86efac'}` }}>
            {nbAmbiguites === 0
              ? 'Aucune ambiguïté trouvée'
              : `${nbAmbiguites} ambiguïté${nbAmbiguites > 1 ? 's' : ''} trouvée${nbAmbiguites > 1 ? 's' : ''}`}
          </span>
        )}
        {/* La sortie mise en forme du rapport — le même geste que « HTML » de l'activité :
            on voit la page telle qu'elle s'imprime, sans quitter aSchool. */}
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
        <JaugeAttente libelle="aSchool relit votre énoncé à la recherche des ambiguïtés…" />
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

      {resultat && <AmbiguitesResultat resultat={resultat} />}
    </div>
  )


  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

      {/* Barre de titre fixe. Plus d'onglets : « Comment ça marche » est passé dans le bouton
          du header (registre `guidesParPage` d'App.jsx), l'écran n'a plus qu'une seule chose
          à montrer — le formulaire. */}
      <div style={{
        display: 'flex', alignItems: 'center',
        borderBottom: '2px solid #e2e8f0',
        background: '#fff', padding: '0 24px', gap: '4px', flexShrink: 0,
      }}>
        <span
          title="Analyser un énoncé ou exercice pour détecter les zones d'incompréhension"
          style={{ padding: '12px 16px', fontSize: '13px', fontWeight: 600, color: 'var(--bordeaux)', whiteSpace: 'nowrap',
                   display: 'inline-flex', alignItems: 'center', gap: 7 }}
        >
          <IconAmbiguites />
          Analyser un texte pour détecter les ambiguïtés
        </span>

        {/* Le volet ne se replie que s'il y a quelque chose dedans : avant l'analyse, un bouton
            « Cacher le rapport » désignerait un cadre vide. */}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
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
          title={empeche || 'Analyser l\'énoncé et détecter les types d\'ambiguïté cochés'}
        >
          {loading ? <Spinner /> : <IconAnalyser />}
          {loading ? 'Analyse en cours…' : 'Analyser l\'énoncé'}
        </button>
        </div>
      </div>

      {/* Deux colonnes redimensionnables, comme l'écran Activité : le formulaire à gauche, le
          rapport à droite. Poignée à tirer, largeur mémorisée, double-clic pour rééquilibrer.
          Rapport caché (bouton de la barre) : le formulaire prend toute la largeur. */}
      <div style={{ flex: 1, minHeight: 0 }}>
        {resultatCache
          ? <div className="split-pane"><div className="split-col split-col-flex">{colonneFormulaire}</div></div>
          : <SplitPane storageKey="ambiguites-split-v1" gauche={colonneFormulaire} droite={colonneRapport} />}
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
