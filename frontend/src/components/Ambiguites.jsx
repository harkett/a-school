import { useState, useRef, useEffect } from 'react'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_LONG } from '../utils/api.js'
import { showError } from '../errorDialog.js'
import AmbiguitesResultat from './AmbiguitesResultat.jsx'
import JaugeAttente from './JaugeAttente.jsx'

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

export default function Ambiguites({ matiere, niveau, onNavigate, onCreateSequence, prefillTexte, onPrefillUsed }) {
  const mat = matiere
  const niv = niveau

  const [tab, setTab]             = useState('analyser')
  const [texte, setTexte]         = useState(prefillTexte || '')

  useEffect(() => {
    if (prefillTexte) onPrefillUsed?.()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  const [loading, setLoading]     = useState(false)

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
    setResultat(null)
    setLoading(true)
    try {
      const res = await apiFetch('/api/detect-ambiguites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ texte: texte.trim() }),   // le couple se résout EN BASE côté serveur
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

            {/* Règle « sablier ET jauge » : l'appel IA montre la jauge, jamais un écran figé. */}
            {loading && (
              <JaugeAttente libelle="aSchool relit votre énoncé à la recherche des ambiguïtés…" />
            )}

            {/* Résultats — affichage partagé (verdict + cartes) avec la cartouche de Créer une activité */}
            {resultat && (
              <div ref={resultRef}>
                <AmbiguitesResultat
                  resultat={resultat}
                  onDemanderSequence={onCreateSequence ? (r) => setConfirmDialog({ reformulation: r }) : undefined}
                />
              </div>
            )}
          </>
        )}

        {/* ——— Onglet aide ——— */}
        {tab === 'aide' && (
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '24px', flex: 1 }}>
            <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '13px', marginBottom: '16px' }}>Détecter les ambiguïtés — comment ça marche</div>
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '12px 16px', marginBottom: '16px' }}>
              <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '6px' }}>À quoi ça sert</div>
              <p style={{ margin: 0, fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                Un énoncé mal formulé, et l'élève bute sur la consigne au lieu de l'exercice. Cet outil relit votre énoncé à la loupe : il repère chaque formulation qui prête à confusion et, pour chacune, vous montre l'<strong>extrait</strong> en cause, le <strong>type</strong> de piège, le <strong>risque concret pour l'élève</strong>, et une <strong>reformulation corrigée</strong> prête à copier — le tout précédé d'un <strong>verdict global</strong> sur la clarté. Et si une reformulation vous inspire, elle devient le <strong>thème d'une nouvelle séance</strong> en un clic.
              </p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>1. Collez votre énoncé</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                  <li>Collez un exercice, une série de questions ou une consigne</li>
                  <li>Le bouton <strong>Tester un exemple</strong> (exemple ancré sur le programme) est en cours de préparation.</li>
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

      {/* Dialog confirmation séance */}
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
              Créer une séance depuis cette reformulation
            </div>
            <p style={{ fontSize: '13.5px', color: '#475569', margin: '0 0 6px', lineHeight: 1.6 }}>
              Cette reformulation sera utilisée comme thème de votre nouvelle séance :
            </p>
            <div style={{ fontSize: '13px', color: '#166534', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '5px', padding: '8px 12px', marginBottom: '16px', lineHeight: 1.5 }}>
              {confirmDialog.reformulation}
            </div>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '0 0 6px', lineHeight: 1.5 }}>
              Vous basculerez dans le module <strong>Créer une séance</strong> avec ce thème déjà rempli.
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
                title="Naviguer vers Créer une séance avec ce thème pré-rempli"
              >
                Créer la séance
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
