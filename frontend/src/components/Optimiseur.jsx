import { useState, useRef } from 'react'
import { apiFetch, TIMEOUT_GROQ } from '../utils/api.js'
import { showError } from '../errorDialog.js'

const SCORE_STYLE = {
  'Bon':      { background: '#dcfce7', color: '#166534', border: '1px solid #86efac' },
  'Moyen':    { background: '#fef9c3', color: '#854d0e', border: '1px solid #fde047' },
  'À revoir': { background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5' },
}

const TYPE_COLOR = {
  'Rupture conceptuelle':       { bg: '#fef3c7', text: '#92400e', border: '#fde68a' },
  'Surcharge cognitive':        { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' },
  'Consigne ambiguë':           { bg: '#fce7f3', text: '#9d174d', border: '#f9a8d4' },
  'Activité inefficace':        { bg: '#f3e8ff', text: '#6b21a8', border: '#d8b4fe' },
  'Progression déséquilibrée':  { bg: '#e0f2fe', text: '#075985', border: '#7dd3fc' },
  'Ancrage mémoriel manquant':  { bg: '#f0fdf4', text: '#166534', border: '#86efac' },
}

const DEFAULT_COLOR = { bg: '#f1f5f9', text: '#334155', border: '#cbd5e1' }

function Spinner() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}>
      <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/>
    </svg>
  )
}

function IconOptimiser() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M12 2L2 7l10 5 10-5-10-5z"/>
      <path d="M2 17l10 5 10-5"/>
      <path d="M2 12l10 5 10-5"/>
    </svg>
  )
}

function IconCopy() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
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

function isSequenceGibberish(t) {
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

export default function Optimiseur({ defaultMatiere, defaultNiveau, onNavigate }) {
  const matiere = defaultMatiere
  const niveau  = defaultNiveau

  const [tab, setTab]             = useState('ameliorer')
  const [sequence, setSequence]   = useState('')
  const [loading, setLoading]     = useState(false)

  const [alertDialog, setAlertDialog] = useState(null)
  const [resultat, setResultat]   = useState(null)
  const [copied, setCopied]       = useState(false)
  const resultRef = useRef(null)

  async function optimiser() {
    if (!sequence.trim()) {
      setAlertDialog('Collez une séquence pédagogique avant de lancer l\'analyse.')
      return
    }
    if (isSequenceGibberish(sequence)) {
      setAlertDialog('Le texte saisi ne ressemble pas à une séquence pédagogique.\n\nCollez une vraie séquence ou cliquez sur "Tester un exemple".')
      return
    }
    setResultat(null)
    setLoading(true)
    try {
      const res = await apiFetch('/api/optimize-sequence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ sequence: sequence.trim(), matiere, niveau }),
      }, TIMEOUT_GROQ)
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

  function copier() {
    if (!resultat?.sequence_optimisee) return
    navigator.clipboard.writeText(resultat.sequence_optimisee).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  function reinitialiser() {
    setResultat(null)
    setSequence('')
  }

  const scoreKey = resultat?.score?.split(' — ')[0] || ''
  const scoreStyle = SCORE_STYLE[scoreKey] || { background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1' }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

      {/* Barre d'onglets fixe */}
      <div style={{
        display: 'flex', alignItems: 'center',
        borderBottom: '2px solid #e2e8f0',
        background: '#fff', padding: '0 24px', gap: '4px', flexShrink: 0,
      }}>
        {[
          { id: 'ameliorer', label: 'Améliorer une séquence', title: 'Coller et optimiser une séquence pédagogique existante' },
          { id: 'aide',      label: 'Comment ça marche',     title: 'Guide d\'utilisation de l\'optimiseur de séquences' },
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

        {tab === 'ameliorer' && (
          <button
            className="btn-primary"
            onClick={optimiser}
            disabled={loading}
            title="Analyser la séquence et générer une version optimisée"
            style={{ marginLeft: 'auto' }}
          >
            {loading ? <Spinner /> : <IconOptimiser />}
            {loading ? 'Analyse en cours…' : 'Optimiser la séquence'}
          </button>
        )}
      </div>

      {/* Contenu scrollable */}
      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

        {/* ——— Onglet principal ——— */}
        {tab === 'ameliorer' && (
          <>
            <p style={{ fontSize: '13px', color: '#64748b', margin: 0, lineHeight: 1.6 }}>
              Collez une séquence pédagogique existante. aSchool détecte les problèmes structurels et vous en restitue une version améliorée.
            </p>

            {/* Zone de saisie */}
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Votre séquence pédagogique
                </label>
                {!resultat && !sequence.trim() && (
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
                value={sequence}
                onChange={e => setSequence(e.target.value)}
                placeholder="Collez ici votre séquence — phases, activités, consignes, durées..."
                disabled={loading}
                style={{
                  width: '100%', minHeight: '180px', padding: '10px 12px',
                  fontSize: '13px', lineHeight: 1.6, color: '#1e293b',
                  border: '1px solid #cbd5e1', borderRadius: '6px',
                  resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box',
                  background: loading ? '#f8fafc' : '#fff',
                }}
              />

              {/* Matière · Niveau + lien profil */}
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#1e293b', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '6px 12px' }}>
                  {matiere} · {niveau}
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
                    title="Effacer et recommencer avec une nouvelle séquence"
                    style={{ padding: '5px 12px', fontSize: '12px', background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '6px', cursor: 'pointer' }}
                  >
                    Nouvelle séquence
                  </button>
                )}
              </div>
            </div>


            {/* Résultats */}
            {resultat && (
              <div ref={resultRef} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

                {resultat.avertissement && (
                  <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: '6px', padding: '10px 14px', fontSize: '13px', color: '#92400e', display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 700, flexShrink: 0 }}>Attention</span>
                    <span>{resultat.avertissement}</span>
                  </div>
                )}

                {/* Score */}
                <div>
                  <span style={{ ...scoreStyle, padding: '4px 14px', borderRadius: '20px', fontSize: '13px', fontWeight: 700 }}>
                    {resultat.score}
                  </span>
                </div>

                {/* Problèmes */}
                {resultat.problemes.length > 0 && (
                  <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px 18px' }}>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '10px' }}>
                      {resultat.problemes.length} problème{resultat.problemes.length > 1 ? 's' : ''} détecté{resultat.problemes.length > 1 ? 's' : ''}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {resultat.problemes.map((p, i) => {
                        const c = TYPE_COLOR[p.type] || DEFAULT_COLOR
                        return (
                          <div key={i} style={{ background: c.bg, border: `1px solid ${c.border}`, borderRadius: '6px', padding: '8px 12px', display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                            <span style={{ fontSize: '11px', fontWeight: 700, color: c.text, whiteSpace: 'nowrap', paddingTop: '1px', minWidth: '160px' }}>{p.type}</span>
                            <span style={{ fontSize: '13px', color: '#374151', lineHeight: 1.5 }}>{p.detail}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {resultat.problemes.length === 0 && (
                  <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '6px', padding: '10px 14px', fontSize: '13px', color: '#166534' }}>
                    Aucun problème détecté — votre séquence est déjà bien structurée.
                  </div>
                )}

                {/* Séquence optimisée */}
                <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px 18px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Séquence optimisée
                    </span>
                    <button
                      onClick={copier}
                      title="Copier la séquence optimisée dans le presse-papier"
                      style={{
                        display: 'flex', alignItems: 'center', gap: '5px',
                        padding: '5px 10px', fontSize: '12px',
                        background: copied ? '#dcfce7' : '#f1f5f9',
                        color: copied ? '#166534' : '#475569',
                        border: `1px solid ${copied ? '#86efac' : '#cbd5e1'}`,
                        borderRadius: '5px', cursor: 'pointer',
                      }}
                    >
                      <IconCopy />
                      {copied ? 'Copié' : 'Copier'}
                    </button>
                  </div>
                  <div style={{
                    fontSize: '13px', color: '#1e293b', lineHeight: 1.7,
                    whiteSpace: 'pre-wrap', fontFamily: 'inherit',
                    background: '#f8fafc', borderRadius: '6px',
                    padding: '12px 14px', border: '1px solid #f1f5f9',
                  }}>
                    {resultat.sequence_optimisee}
                  </div>
                </div>

              </div>
            )}
          </>
        )}

        {/* ——— Onglet aide ——— */}
        {tab === 'aide' && (
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '24px', flex: 1 }}>
            <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '13px', marginBottom: '16px' }}>Améliorer une séquence — comment ça marche</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>1. Collez votre séquence</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li>Collez une séquence existante — planning de cours, progression rédigée, fichier de préparation</li>
                  <li>Le bouton <strong>Tester un exemple</strong> (exemple ancré sur le programme) est en cours de préparation.</li>
                </ul>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>2. Lancez l'optimisation</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li>Cliquez sur <strong>Optimiser la séquence</strong> (en haut à droite)</li>
                  <li>aSchool examine la structure, la progression et la cohérence des activités</li>
                </ul>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>3. Récupérez le résultat</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li>Un score global : Bon · Moyen · À revoir</li>
                  <li>La liste des problèmes détectés avec leur description précise</li>
                  <li>La séquence réécrite avec toutes les corrections intégrées</li>
                </ul>
              </div>
              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>Types de problèmes détectés</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li><strong>Rupture conceptuelle</strong> — notion introduite sans prérequis</li>
                  <li><strong>Surcharge cognitive</strong> — trop de nouveaux concepts en une seule phase</li>
                  <li><strong>Consigne ambiguë</strong> — formulation que les élèves risquent de mal interpréter</li>
                  <li><strong>Activité inefficace</strong> — tâche sans objectif pédagogique clair</li>
                  <li><strong>Progression déséquilibrée</strong> — phases trop longues ou trop courtes</li>
                  <li><strong>Ancrage mémoriel manquant</strong> — pas de phase de consolidation ou de révision</li>
                </ul>
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
