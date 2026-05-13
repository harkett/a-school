import { useState, useRef } from 'react'
import { fetchWithTimeout, TIMEOUT_GROQ } from '../utils/api.js'

const EXEMPLES = {
  'Français': () => `Lisez le texte et répondez aux questions suivantes.

1. Analysez le personnage principal.
2. Que pensez-vous du style de l'auteur ?
3. Commentez la fin du texte en donnant votre avis.`,

  'Histoire-Géographie': () => `Étudiez le document et répondez.

1. Expliquez le contexte historique.
2. Montrez que cet événement est important.
3. Quelles sont les conséquences ?`,

  'Mathématiques': () => `Résolvez le problème suivant en montrant votre démarche.

On dispose d'une figure géométrique. Calculez sa surface. Justifiez votre réponse et vérifiez.`,

  'Physique-Chimie': () => `À partir de vos observations, répondez aux questions.

1. Décrivez ce qui se passe.
2. Expliquez le phénomène.
3. Concluez sur les résultats obtenus.`,

  'SVT': () => `Exploitez les documents et rédigez un texte structuré expliquant le mécanisme étudié. Vous utiliserez vos connaissances.`,

  'SES': () => `À l'aide du document et de vos connaissances, répondez à la question suivante.

Montrez que le marché peut présenter des dysfonctionnements. Illustrez avec des exemples.`,

  'NSI': () => `Écrire un algorithme qui résout le problème. Tester et expliquer votre solution.

Le programme doit être efficace. Vous justifierez vos choix.`,

  'Philosophie': () => `Traitez le sujet suivant en rédigeant un devoir complet.

"Peut-on tout dire ?" — Analysez la question et donnez votre point de vue argumenté.`,

  'Langues Vivantes (LV)': () => `Read the text and answer the following questions.

1. What is the text about? Explain.
2. Comment on the author's point of view.
3. Give your opinion on the topic using examples.`,

  'Technologie': () => `Étudiez l'objet technique et complétez le tableau. Expliquez son fonctionnement et proposez une amélioration possible.`,

  'Arts': () => `Réalisez une production plastique en vous inspirant du document. Vous expliquerez votre démarche et vos choix artistiques.`,

  'EPS': () => `Exécutez l'exercice proposé en respectant les critères. Évaluez votre performance et commentez vos résultats.`,
}

const TYPE_COLOR = {
  'Consigne vague':                  { bg: '#fef3c7', text: '#92400e', border: '#fde68a' },
  'Vocabulaire technique non défini': { bg: '#f3e8ff', text: '#6b21a8', border: '#d8b4fe' },
  'Double sens':                     { bg: '#fce7f3', text: '#9d174d', border: '#f9a8d4' },
  'Critères de réussite absents':    { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' },
  'Référence implicite':             { bg: '#e0f2fe', text: '#075985', border: '#7dd3fc' },
  'Consigne trop longue':            { bg: '#f0fdf4', text: '#166534', border: '#86efac' },
}

const DEFAULT_COLOR = { bg: '#f1f5f9', text: '#334155', border: '#cbd5e1' }

function Spinner() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}>
      <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/>
    </svg>
  )
}

function IconAnalyser() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      <line x1="11" y1="8" x2="11" y2="14"/>
      <line x1="8" y1="11" x2="14" y2="11"/>
    </svg>
  )
}

function IconExemple() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
      <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
    </svg>
  )
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

export default function Ambiguites({ matiere, niveau, onNavigate, onCreateSequence }) {
  const mat = matiere || 'Français'
  const niv = niveau  || '4e'

  const [tab, setTab]             = useState('analyser')
  const [texte, setTexte]         = useState('')
  const [loading, setLoading]     = useState(false)
  const [erreur, setErreur]       = useState(null)
  const [alertDialog, setAlertDialog] = useState(null)
  const [confirmDialog, setConfirmDialog] = useState(null)
  const [resultat, setResultat]   = useState(null)
  const resultRef = useRef(null)

  async function analyser() {
    if (!texte.trim()) {
      setAlertDialog('Collez un exercice ou un énoncé avant de lancer l\'analyse.')
      return
    }
    if (isTexteGibberish(texte)) {
      setAlertDialog('Le texte saisi ne ressemble pas à un énoncé pédagogique.\n\nCollez un vrai exercice ou cliquez sur "Tester un exemple".')
      return
    }
    setErreur(null)
    setResultat(null)
    setLoading(true)
    try {
      const res = await fetchWithTimeout('/api/detect-ambiguites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ texte: texte.trim(), matiere: mat, niveau: niv }),
      }, TIMEOUT_GROQ)
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || `Erreur ${res.status}`)
      }
      const data = await res.json()
      setResultat(data)
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
    } catch (e) {
      setErreur(`Erreur : ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  function reinitialiser() {
    setResultat(null)
    setErreur(null)
    setTexte('')
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

      {/* Barre d'onglets fixe */}
      <div style={{
        display: 'flex', alignItems: 'center',
        borderBottom: '2px solid #e2e8f0',
        background: '#fff', padding: '0 24px', gap: '4px', flexShrink: 0,
      }}>
        {[
          { id: 'analyser', label: 'Détecter les ambiguïtés', title: 'Analyser un énoncé ou exercice pour détecter les zones d\'incompréhension' },
          { id: 'aide',     label: 'Comment ça marche',       title: 'Guide d\'utilisation du détecteur d\'ambiguïtés' },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} title={t.title}
            style={{
              padding: '12px 16px', fontSize: '13px',
              fontWeight: tab === t.id ? 600 : 400,
              color: tab === t.id ? 'var(--bordeaux)' : '#6b7280',
              borderBottom: `2px solid ${tab === t.id ? 'var(--bordeaux)' : 'transparent'}`,
              background: 'none', border: 'none', borderRadius: 0,
              cursor: 'pointer', marginBottom: '-2px', whiteSpace: 'nowrap',
            }}>
            {t.label}
          </button>
        ))}

        {tab === 'analyser' && (
          <button
            className="btn-primary"
            onClick={analyser}
            disabled={loading}
            title="Analyser l'énoncé et détecter les ambiguïtés cognitives"
            style={{ marginLeft: 'auto' }}
          >
            {loading ? <Spinner /> : <IconAnalyser />}
            {loading ? 'Analyse en cours…' : 'Analyser l\'énoncé'}
          </button>
        )}
      </div>

      {/* Contenu scrollable */}
      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

        {/* ——— Onglet principal ——— */}
        {tab === 'analyser' && (
          <>
            <p style={{ fontSize: '13px', color: '#64748b', margin: 0, lineHeight: 1.6 }}>
              Collez un exercice ou un énoncé. aSchool identifie les formulations ambiguës et vous propose des reformulations corrigées, prêtes à l'emploi.
            </p>

            {/* Zone de saisie */}
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Votre exercice ou énoncé
                </label>
                {!resultat && !texte.trim() && (
                  <button
                    onClick={() => setTexte((EXEMPLES[mat] || EXEMPLES['Français'])())}
                    title="Pré-remplir avec un énoncé exemple adapté à votre matière — pour tester sans avoir d'exercice sous la main"
                    disabled={loading}
                    style={{ fontSize: '11px', color: '#6366f1', background: 'none', border: '1px solid #c7d2fe', borderRadius: '5px', padding: '3px 10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}
                  >
                    <IconExemple />
                    Tester un exemple
                  </button>
                )}
              </div>

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

              {/* Matière · Niveau */}
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#1e293b', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '6px 12px' }}>
                  {mat} · {niv}
                </span>
                <span style={{ fontSize: '11.5px', color: '#94a3b8' }}>
                  Pour changer →{' '}
                  <button
                    onClick={() => onNavigate?.('mon-profil')}
                    title="Aller dans Mon profil pour modifier la matière ou le niveau"
                    style={{ background: 'none', border: 'none', padding: 0, color: '#6366f1', cursor: 'pointer', fontSize: '11.5px', textDecoration: 'underline' }}
                  >
                    Mon profil
                  </button>
                </span>
                {resultat && (
                  <button
                    onClick={reinitialiser}
                    title="Effacer et analyser un nouvel énoncé"
                    style={{ padding: '5px 12px', fontSize: '12px', background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '6px', cursor: 'pointer' }}
                  >
                    Nouvel énoncé
                  </button>
                )}
              </div>
            </div>

            {/* Erreur API */}
            {erreur && (
              <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '10px 14px', fontSize: '13px', color: '#dc2626' }}>
                {erreur}
              </div>
            )}

            {/* Résultats */}
            {resultat && (
              <div ref={resultRef} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

                {/* Verdict */}
                {resultat.ambiguites.length === 0 ? (
                  <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#166534', lineHeight: 1.6 }}>
                    <strong>Énoncé clair</strong> — {resultat.verdict}
                  </div>
                ) : (
                  <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#92400e', lineHeight: 1.6 }}>
                    <strong>{resultat.ambiguites.length} ambiguïté{resultat.ambiguites.length > 1 ? 's' : ''} détectée{resultat.ambiguites.length > 1 ? 's' : ''}</strong> — {resultat.verdict}
                  </div>
                )}

                {/* Liste des ambiguïtés */}
                {resultat.ambiguites.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {resultat.ambiguites.map((a, i) => {
                      const c = TYPE_COLOR[a.type] || DEFAULT_COLOR
                      return (
                        <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
                          {/* En-tête carte */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', borderBottom: '1px solid #f1f5f9' }}>
                            <span style={{ fontSize: '11px', fontWeight: 700, color: c.text, background: c.bg, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '2px 10px', whiteSpace: 'nowrap' }}>
                              {a.type}
                            </span>
                          </div>
                          {/* Corps carte */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '12px 14px' }}>
                            {/* Extrait */}
                            <div>
                              <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                                Extrait problématique
                              </div>
                              <div style={{ fontSize: '13px', color: '#374151', fontStyle: 'italic', background: '#fafafa', borderLeft: '3px solid #e2e8f0', padding: '6px 10px', borderRadius: '3px' }}>
                                "{a.extrait}"
                              </div>
                            </div>
                            {/* Risque */}
                            <div>
                              <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                                Risque pour l'élève
                              </div>
                              <div style={{ fontSize: '13px', color: '#374151', lineHeight: 1.5 }}>{a.risque}</div>
                            </div>
                            {/* Reformulation */}
                            <div>
                              <div style={{ fontSize: '11px', fontWeight: 600, color: '#166534', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                                Reformulation corrigée
                              </div>
                              <div style={{ fontSize: '13px', color: '#166534', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '5px', padding: '8px 10px', lineHeight: 1.5 }}>
                                {a.reformulation}
                              </div>
                            </div>

                            {/* Bouton Créer une séquence */}
                            {onCreateSequence && (
                              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                                <button
                                  onClick={() => setConfirmDialog({ reformulation: a.reformulation })}
                                  title="Utiliser cette reformulation comme thème pour créer une séquence pédagogique"
                                  style={{ fontSize: '12px', color: '#6366f1', background: 'none', border: '1px solid #c7d2fe', borderRadius: '5px', padding: '5px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}
                                >
                                  Créer une séquence →
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* ——— Onglet aide ——— */}
        {tab === 'aide' && (
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '24px', flex: 1 }}>
            <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '13px', marginBottom: '16px' }}>Détecter les ambiguïtés — comment ça marche</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>1. Collez votre énoncé</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li>Collez un exercice, une série de questions ou une consigne</li>
                  <li><strong>Pas de texte sous la main ?</strong> Cliquez sur <strong>Tester un exemple</strong> (en haut à droite du texte source) pour pré-remplir avec un extrait adapté à votre matière.</li>
                </ul>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>2. Lancez l'analyse</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li>Cliquez sur <strong>Analyser l'énoncé</strong> (en haut à droite)</li>
                  <li>aSchool parcourt chaque formulation et identifie les zones à risque</li>
                </ul>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>3. Lisez le rapport</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li>Un verdict global sur la clarté de l'énoncé</li>
                  <li>Pour chaque ambiguïté : l'extrait exact et le risque pour l'élève</li>
                  <li>Une <strong>reformulation corrigée</strong> prête à copier dans votre exercice</li>
                </ul>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>Types d'ambiguïtés détectées</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li><strong>Consigne vague</strong> — "analysez", "commentez" sans critères précis</li>
                  <li><strong>Vocabulaire technique non défini</strong> — terme supposé connu</li>
                  <li><strong>Double sens</strong> — formulation interprétable de deux façons</li>
                  <li><strong>Critères de réussite absents</strong> — longueur, forme, nombre de points non précisés</li>
                  <li><strong>Référence implicite</strong> — "le texte", "le document" sans préciser lequel</li>
                  <li><strong>Consigne trop longue</strong> — plusieurs tâches non séparées</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Dialog confirmation séquence */}
      {confirmDialog && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={() => setConfirmDialog(null)}
        >
          <div
            style={{ background: '#fff', borderRadius: '10px', padding: '24px 28px', maxWidth: '460px', width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ fontWeight: 700, fontSize: '15px', marginBottom: '10px', color: '#1e293b' }}>
              Créer une séquence depuis cette reformulation
            </div>
            <p style={{ fontSize: '13.5px', color: '#475569', margin: '0 0 6px', lineHeight: 1.6 }}>
              Cette reformulation sera utilisée comme thème de votre nouvelle séquence :
            </p>
            <div style={{ fontSize: '13px', color: '#166534', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '5px', padding: '8px 12px', marginBottom: '16px', lineHeight: 1.5 }}>
              {confirmDialog.reformulation}
            </div>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '0 0 6px', lineHeight: 1.5 }}>
              Vous basculerez dans le module <strong>Créer une séquence</strong> avec ce thème déjà rempli.
            </p>
            <p style={{ fontSize: '13px', color: '#ef4444', margin: '0 0 20px', lineHeight: 1.5 }}>
              Vous quitterez cette page — l'analyse en cours sera perdue.
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setConfirmDialog(null)}
                style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '8px 18px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
              >
                Annuler
              </button>
              <button
                onClick={() => { setConfirmDialog(null); onCreateSequence(confirmDialog.reformulation) }}
                style={{ background: '#6366f1', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 18px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
                title="Naviguer vers Créer une séquence avec ce thème pré-rempli"
              >
                Créer la séquence
              </button>
            </div>
          </div>
        </div>
      )}

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
            <div style={{ fontWeight: 700, fontSize: '15px', marginBottom: '10px', color: '#1e293b' }}>
              Énoncé manquant
            </div>
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
