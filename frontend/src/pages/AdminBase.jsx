// Page « Base de données » (V1) — affiche sur quelle base l'app est RÉELLEMENT connectée.
// Vérité terrain : GET /api/admin/base -> current_database() côté serveur. Garde-fou pour
// ne jamais confondre la vraie base (aschool) avec un miroir de test.
import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

// Le miroir/test doit SAUTER aux yeux (ambre) ; la vraie base est sobre (vert).
const STYLES = {
  reelle: { label: 'Base RÉELLE',                bg: '#ecfdf5', border: '#a7f3d0', color: '#065f46',
            note: 'Tu travailles sur la vraie base de développement. Les écritures sont réelles.' },
  miroir: { label: 'Base de TEST — MIROIR',      bg: '#fffbeb', border: '#fde68a', color: '#92400e',
            note: 'Copie jetable de la vraie base. Tu peux tester sans risque — rien n’atteint la vraie base.' },
  test:   { label: 'Base de tests automatiques', bg: '#fffbeb', border: '#fde68a', color: '#92400e',
            note: 'Base des tests automatisés (remise à zéro à chaque run). Pas pour un usage manuel.' },
  autre:  { label: 'Base non reconnue',          bg: '#f1f5f9', border: '#cbd5e1', color: '#334155',
            note: 'Le nom de la base n’est pas reconnu (ni aschool, ni miroir, ni test).' },
}

export default function AdminBase() {
  const [info, setInfo] = useState(null)
  const [erreur, setErreur] = useState(false)

  useEffect(() => {
    fetchWithTimeout('/api/admin/base', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : Promise.reject()))
      .then(setInfo)
      .catch(() => setErreur(true))
  }, [])

  const s = info ? (STYLES[info.type] || STYLES.autre) : null

  return (
    <div className="flex flex-col gap-6" style={{ maxWidth: 720 }}>
      <div>
        <h2 className="text-base font-semibold text-gray-800">Base de données</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          La base de données sur laquelle l’application est réellement connectée en ce moment.
        </p>
      </div>

      {erreur && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 text-sm text-gray-500">
          Impossible de lire l’état de la base.
        </div>
      )}

      {!info && !erreur && <div className="text-gray-400 text-sm">Lecture…</div>}

      {info && s && (
        <div style={{ background: s.bg, border: `1px solid ${s.border}`, borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: s.color }}>{s.label}</div>
          <div style={{ fontSize: 13, color: s.color, marginTop: 6, lineHeight: 1.5 }}>{s.note}</div>
          <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13, color: '#334155' }}>
            <div>Nom : <strong>{info.base}</strong></div>
            <div>Serveur : <strong>{info.host}:{info.port}</strong></div>
          </div>
        </div>
      )}
    </div>
  )
}
