import { useState, useEffect, useRef } from 'react'

// Petit « i » d'aide posé DERRIÈRE un titre. Deux niveaux, deux gestes :
//  - SURVOL → une bulle COURTE (prop `court`) ;
//  - CLIC   → une carte COMPLÈTE (prop `long`), ÉPINGLÉE : elle reste ouverte jusqu'au ✕,
//             à un clic AILLEURS, ou à la touche Échap (on ne piège jamais le prof).
// Composant générique (titre / court / long) : réutilisable partout où un titre a besoin d'aide.
// Les textes viennent du catalogue (utils/aideProfil.js), jamais réécrits ici.
export default function InfoGuide({ titre, court, long }) {
  const [survol, setSurvol] = useState(false)
  const [ouvert, setOuvert] = useState(false)   // carte épinglée (au clic)
  const wrapRef = useRef(null)

  // Fermer la carte au clic AILLEURS et à Échap. Le listener n'existe que quand la carte est
  // ouverte (posé après le render qui l'ouvre → le clic d'ouverture ne la referme pas aussitôt).
  useEffect(() => {
    if (!ouvert) return
    const surClicDehors = e => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOuvert(false) }
    const surEchap = e => { if (e.key === 'Escape') setOuvert(false) }
    document.addEventListener('mousedown', surClicDehors)
    document.addEventListener('keydown', surEchap)
    return () => {
      document.removeEventListener('mousedown', surClicDehors)
      document.removeEventListener('keydown', surEchap)
    }
  }, [ouvert])

  return (
    <span ref={wrapRef} style={{ position: 'relative', display: 'inline-flex', verticalAlign: 'middle', marginLeft: 6 }}>
      <button
        type="button"
        aria-label={`Aide : ${titre}`}
        aria-expanded={ouvert}
        onMouseEnter={() => setSurvol(true)}
        onMouseLeave={() => setSurvol(false)}
        onClick={() => { setOuvert(o => !o); setSurvol(false) }}
        style={{
          width: 16, height: 16, borderRadius: '50%', border: '1px solid #cbd5e1',
          background: ouvert ? '#2563eb' : '#fff', color: ouvert ? '#fff' : '#64748b',
          fontSize: 11, fontWeight: 700, fontStyle: 'italic', lineHeight: 1,
          textTransform: 'none', fontFamily: 'Georgia, "Times New Roman", serif',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', padding: 0, flexShrink: 0,
        }}
      >
        i
      </button>

      {/* SURVOL → bulle courte (masquée dès que la carte est épinglée, pour ne pas se superposer). */}
      {survol && !ouvert && (
        <span role="tooltip" style={{
          position: 'absolute', top: 'calc(100% + 6px)', left: 0, zIndex: 40,
          background: '#1e293b', color: '#fff', fontSize: 12, fontWeight: 400,
          textTransform: 'none', letterSpacing: 0, lineHeight: 1.4,
          padding: '6px 9px', borderRadius: 6, width: 'max-content', maxWidth: 240,
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)', pointerEvents: 'none',
        }}>
          <span style={{ display: 'block' }}>{court}</span>
          {/* Indice d'usage : dit au prof qu'un clic ouvre la fiche complète (affiché seulement
              s'il y a une fiche `long` à ouvrir). Plus petit, italique, gris clair → discret. */}
          {long && (
            <span style={{ display: 'block', marginTop: 4, fontSize: 11, fontStyle: 'italic', color: '#cbd5e1' }}>
              Cliquez pour en savoir plus
            </span>
          )}
        </span>
      )}

      {/* CLIC → carte complète, épinglée. */}
      {ouvert && (
        <span style={{
          position: 'absolute', top: 'calc(100% + 6px)', left: 0, zIndex: 50,
          background: '#fff', color: '#374151', border: '1px solid #e2e8f0',
          borderRadius: 8, padding: '10px 12px', width: 300, maxWidth: '80vw',
          textTransform: 'none', letterSpacing: 0,
          boxShadow: '0 8px 24px rgba(0,0,0,0.16)', display: 'block',
        }}>
          <span style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 4 }}>
            <strong style={{ fontSize: 12.5, color: '#1e293b' }}>{titre}</strong>
            <button type="button" aria-label="Fermer l'aide" onClick={() => setOuvert(false)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8',
                       fontSize: 15, lineHeight: 1, padding: 0, flexShrink: 0 }}>
              ✕
            </button>
          </span>
          <span style={{ display: 'block', fontSize: 12.5, fontWeight: 400, lineHeight: 1.5, whiteSpace: 'pre-line' }}>{long}</span>
        </span>
      )}
    </span>
  )
}
