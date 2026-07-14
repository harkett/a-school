import { useState, useRef } from 'react'
import { apiFetch, TIMEOUT_LONG } from '../utils/api.js'
import { showError } from '../errorDialog.js'

const AXE_COLOR = {
  'Clarté linguistique':       { bg: '#fef3c7', text: '#92400e', border: '#fde68a' },
  'Précision didactique':      { bg: '#f3e8ff', text: '#6b21a8', border: '#d8b4fe' },
  'Ambiguïté conceptuelle':    { bg: '#fce7f3', text: '#9d174d', border: '#f9a8d4' },
  'Structure logique':         { bg: '#ffedd5', text: '#7c2d12', border: '#fdba74' },
  'Risque d\'erreurs typiques': { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' },
}
const DEFAULT_COLOR = { bg: '#f1f5f9', text: '#334155', border: '#cbd5e1' }

const SEVERITE_COLOR = {
  'Élevée':  { bg: '#fee2e2', text: '#991b1b' },
  'Modérée': { bg: '#fef3c7', text: '#92400e' },
}

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

function isConsigneGibberish(t) {
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

export default function Consigne({ matiere, niveau, onNavigate }) {
  const mat = matiere
  const niv = niveau

  const [tab, setTab]                 = useState('analyser')
  const [consigne, setConsigne]       = useState('')
  const [loading, setLoading]         = useState(false)

  const [alertDialog, setAlertDialog] = useState(null)
  const [resultat, setResultat]       = useState(null)
  const resultRef = useRef(null)

  async function analyser() {
    if (!consigne.trim()) {
      setAlertDialog('Collez une consigne avant de lancer l\'analyse.')
      return
    }
    if (consigne.trim().split(/\s+/).length < 3) {
      setAlertDialog('La consigne est trop courte. Collez une consigne complète.')
      return
    }
    if (isConsigneGibberish(consigne)) {
      setAlertDialog('Le texte saisi ne ressemble pas à une consigne pédagogique.\n\nCollez une vraie consigne ou cliquez sur "Tester un exemple".')
      return
    }
    setResultat(null)
    setLoading(true)
    try {
      const res = await apiFetch('/api/analyser-consigne', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ consigne: consigne.trim(), matiere: mat, niveau: niv }),
      }, TIMEOUT_LONG)
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || `Erreur ${res.status}`)
      }
      const data = await res.json()
      setResultat(data)
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
    } catch (e) {
      showError(`Erreur : ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  function reinitialiser() {
    setResultat(null)
    setConsigne('')
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
          { id: 'analyser', label: 'Analyser une consigne', title: 'Analyser la qualité didactique d\'une consigne' },
          { id: 'aide',     label: 'Comment ça marche',     title: 'Guide d\'utilisation de l\'analyseur de consignes' },
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
            title="Analyser la qualité didactique de la consigne"
            style={{ marginLeft: 'auto' }}
          >
            {loading ? <Spinner /> : <IconAnalyser />}
            {loading ? 'Analyse en cours…' : 'Analyser la consigne'}
          </button>
        )}
      </div>

      {/* Contenu scrollable */}
      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

        {/* ——— Onglet principal ——— */}
        {tab === 'analyser' && (
          <>
            <p style={{ fontSize: '13px', color: '#64748b', margin: 0, lineHeight: 1.6 }}>
              Collez une consigne isolée. aSchool analyse sa clarté, sa précision didactique et les risques d'incompréhension — puis propose une version optimisée.
            </p>

            {/* Zone de saisie */}
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Votre consigne
                </label>
                {!resultat && !consigne.trim() && (
                  <button
                    onClick={() => setAlertDialog('Pas d\'exemple disponible pour le moment.')}
                    title="Aucun exemple disponible pour le moment"
                    disabled={loading}
                    style={{ fontSize: '11px', color: '#6366f1', background: 'none', border: '1px solid #c7d2fe', borderRadius: '5px', padding: '3px 10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}
                  >
                    <IconExemple />
                    Tester un exemple
                  </button>
                )}
              </div>

              <textarea
                value={consigne}
                onChange={e => setConsigne(e.target.value)}
                placeholder="Collez ici une consigne à analyser — une seule consigne, pas un exercice entier…"
                disabled={loading}
                style={{
                  width: '100%', minHeight: '80px', padding: '10px 12px',
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
                    title="Effacer et analyser une nouvelle consigne"
                    style={{ padding: '5px 12px', fontSize: '12px', background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '6px', cursor: 'pointer' }}
                  >
                    Nouvelle consigne
                  </button>
                )}
              </div>
            </div>


            {/* Résultats */}
            {resultat && (
              <div ref={resultRef} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

                {/* Verdict */}
                {resultat.analyses.length === 0 ? (
                  <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#166534', lineHeight: 1.6 }}>
                    <strong>Consigne claire</strong> — {resultat.verdict}
                  </div>
                ) : (
                  <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#92400e', lineHeight: 1.6 }}>
                    <strong>{resultat.analyses.length} point{resultat.analyses.length > 1 ? 's' : ''} à améliorer</strong> — {resultat.verdict}
                  </div>
                )}

                {/* Axes d'analyse */}
                {resultat.analyses.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {resultat.analyses.map((a, i) => {
                      const c = AXE_COLOR[a.axe] || DEFAULT_COLOR
                      const sc = SEVERITE_COLOR[a.severite] || SEVERITE_COLOR['Modérée']
                      return (
                        <div key={i} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
                          {/* En-tête carte */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', borderBottom: '1px solid #f1f5f9' }}>
                            <span style={{ fontSize: '11px', fontWeight: 700, color: c.text, background: c.bg, border: `1px solid ${c.border}`, borderRadius: '12px', padding: '2px 10px', whiteSpace: 'nowrap' }}>
                              {a.axe}
                            </span>
                            <span style={{ fontSize: '10px', fontWeight: 700, color: sc.text, background: sc.bg, borderRadius: '10px', padding: '2px 8px', whiteSpace: 'nowrap' }}>
                              {a.severite}
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
                            {/* Problème */}
                            <div>
                              <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                                Problème identifié
                              </div>
                              <div style={{ fontSize: '13px', color: '#374151', lineHeight: 1.5 }}>{a.probleme}</div>
                            </div>
                            {/* Conseil */}
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

                {/* Version optimisée */}
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
          </>
        )}

        {/* ——— Onglet aide ——— */}
        {tab === 'aide' && (
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '24px', flex: 1 }}>
            <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '13px', marginBottom: '16px' }}>Analyser une consigne — comment ça marche</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>1. Collez une consigne isolée</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li>Une consigne = une instruction adressée à l'élève (pas un exercice entier)</li>
                  <li>Exemple : "Analysez le personnage en faisant référence au texte."</li>
                  <li>Le bouton <strong>Tester un exemple</strong> (exemple ancré sur le programme) est en cours de préparation.</li>
                </ul>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>2. Lancez l'analyse</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li>Cliquez sur <strong>Analyser la consigne</strong> (en haut à droite)</li>
                  <li>aSchool examine la consigne sur 5 axes didactiques</li>
                </ul>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>3. Lisez le rapport</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li>Un verdict global sur la qualité de la consigne</li>
                  <li>Pour chaque problème : l'extrait exact, le problème identifié, une suggestion concrète</li>
                  <li>Une <strong>consigne optimisée</strong> prête à copier, directement utilisable</li>
                </ul>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>5 axes analysés</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li><strong>Clarté linguistique</strong> — formulations floues, vagues ou trop longues</li>
                  <li><strong>Précision didactique</strong> — la consigne dit-elle exactement ce qu'elle doit évaluer ?</li>
                  <li><strong>Ambiguïté conceptuelle</strong> — mots à double sens ("analyser", "simplifier", "produit"…)</li>
                  <li><strong>Structure logique</strong> — étapes implicites, tâches multiples, sauts logiques</li>
                  <li><strong>Risque d'erreurs typiques</strong> — formulations qui provoquent des erreurs récurrentes</li>
                </ul>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
              <div style={{ background: '#f8fafc', borderRadius: '6px', padding: '10px 14px', borderLeft: '3px solid #cbd5e1' }}>
                <div style={{ fontSize: '12px', color: '#64748b', lineHeight: 1.6 }}>
                  <strong style={{ color: '#475569' }}>Différence avec le Détecteur d'ambiguïtés</strong><br/>
                  Le Détecteur d'ambiguïtés analyse un <em>exercice entier</em> (plusieurs questions). L'Analyseur de consignes se concentre sur <em>une seule consigne</em> : il va plus loin sur la précision didactique, la charge cognitive et la structure logique de l'instruction elle-même.
                </div>
              </div>
            </div>
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
