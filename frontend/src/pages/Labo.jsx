// ── LABO — écran bac à sable (réutilisable) ──────────────────────────────────────────────
// Vide entre deux tâches : on y met au point une fonctionnalité (avec les vrais get/put) avant
// de l'intégrer dans son écran définitif, puis on remet le labo à zéro. Fichier et route
// (/admin/labo) conservés ; le contenu ci-dessous est volontairement générique.
export default function Labo() {
  return (
    <div style={{ maxWidth: 760 }}>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">🧪 Labo</h2>
        <span className="text-xs text-gray-400">écran brouillon (réutilisable)</span>
      </div>
      <div style={{ background: 'white', borderRadius: 12, border: '1px solid #e2e8f0', padding: 24 }}>
        <p className="text-sm" style={{ color: '#64748b', lineHeight: 1.6 }}>
          Écran de travail vide. On y construit la prochaine fonctionnalité (vrais get/put sur la base),
          on l'affine ici, puis on l'intègre dans son écran définitif — et on revide le labo.
        </p>
      </div>
    </div>
  )
}
