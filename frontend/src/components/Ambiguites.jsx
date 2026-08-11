// Écran « Détecter les ambiguïtés ». Le prof COCHE les types à faire relire : l'IA ne cherche
// que ceux-là. Les critères ne sont plus écrits ici — ils sont LUS EN BASE (catalogue
// `ambiguite_criteres`, servi par /ambiguites/criteres), à la même source que celle sur
// laquelle le serveur refusera ou acceptera. La case « Autre » ouvre un champ libre : ce que
// le prof y écrit part au modèle comme un point de vigilance, jamais comme une consigne.
import { useEffect, useState, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_LONG, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog.js'
import AmbiguitesResultat from './AmbiguitesResultat.jsx'
import ApportTexte from './contenus/ApportTexte.jsx'
import JaugeAttente from './JaugeAttente.jsx'
import { IconAnalyser, IconExemple, Spinner } from './icones.jsx'




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
}

export default function Ambiguites() {
  const [texte, setTexte]         = useState('')
  const [loading, setLoading]     = useState(false)

  const [alertDialog, setAlertDialog] = useState(null)
  const [origineTexte, setOrigineTexte] = useState(null)
  const [resultat, setResultat]   = useState(null)
  const resultRef = useRef(null)

  // ── Les critères : catalogue lu en base, aucune case pré-cochée (règle maison) ──
  const { data: criteres = [], error: criteresErreur } = useQuery({
    queryKey: ['ambiguites', 'criteres'],
    queryFn: async () => {
      const d = await lireReponse(await apiFetch('/api/ambiguites/criteres', { credentials: 'include' }, TIMEOUT_STD))
      return Array.isArray(d) ? d : []
    },
  })
  useEffect(() => { if (criteresErreur) showError(messagePourEcran(criteresErreur)) }, [criteresErreur])

  // L'énoncé d'exemple de SON couple, écrit d'avance par l'admin. Absent pour ce couple :
  // `disponible` est faux et le bouton ne s'affiche pas — pas de bouton qui répond « rien ».
  const { data: exemple } = useQuery({
    queryKey: ['ambiguites', 'exemple'],
    queryFn: async () => await lireReponse(
      await apiFetch('/api/ambiguites/exemple', { credentials: 'include' }, TIMEOUT_STD)),
  })

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
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
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
          style={{ padding: '12px 16px', fontSize: '13px', fontWeight: 600, color: 'var(--bordeaux)', whiteSpace: 'nowrap' }}
        >
          Détecter les ambiguïtés
        </span>

        <button
          className="btn-primary"
          onClick={analyser}
          disabled={loading || !!empeche}
          title={empeche || 'Analyser l\'énoncé et détecter les types d\'ambiguïté cochés'}
          style={{ marginLeft: 'auto' }}
        >
          {loading ? <Spinner /> : <IconAnalyser />}
          {loading ? 'Analyse en cours…' : 'Analyser l\'énoncé'}
        </button>
      </div>

      {/* Contenu scrollable */}
      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

        <p style={{ fontSize: '13px', color: '#64748b', margin: 0, lineHeight: 1.6 }}>
          Collez un exercice ou un énoncé. aSchool identifie les formulations ambiguës et vous propose des reformulations corrigées, prêtes à l'emploi.
        </p>

        {/* Zone de saisie */}
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Votre exercice ou énoncé
            </label>

            {/* Un énoncé de votre matière, déjà écrit, avec de vrais défauts dedans : de quoi
                voir ce que l'outil sait faire sans avoir à chercher un sujet. */}
            {exemple?.disponible && !texte.trim() && (
              <button
                onClick={() => { setTexte(exemple.texte); setOrigineTexte(null) }}
                disabled={loading}
                title="Charger un énoncé d'exemple de votre matière, prêt à analyser"
                style={{
                  fontSize: '11px', color: '#6366f1', background: 'none',
                  border: '1px solid #c7d2fe', borderRadius: '5px', padding: '3px 10px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', gap: '5px',
                }}
              >
                <IconExemple />
                Utiliser un exemple
              </button>
            )}
            {/* Quatre façons d'apporter l'énoncé, en plus du clavier. Pas de cinquième bouton
                « Propose-moi… » ici : un énoncé écrit par aSchool serait déjà propre, l'analyse
                n'aurait rien à y détecter. */}
            <ApportTexte texte={texte} onChange={setTexte} onSourceNote={setOrigineTexte} disabled={loading} />
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
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Ce qu'aSchool doit chercher
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

        {/* Règle « sablier ET jauge » : l'appel IA montre la jauge, jamais un écran figé. */}
        {loading && (
          <JaugeAttente libelle="aSchool relit votre énoncé à la recherche des ambiguïtés…" />
        )}

        {/* Résultats — verdict + cartes */}
        {resultat && (
          <div ref={resultRef}>
            <AmbiguitesResultat resultat={resultat} />
          </div>
        )}

      </div>

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
