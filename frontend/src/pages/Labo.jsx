// ── ÉCRAN LABO (brouillon, réutilisable) ────────────────────────────────────────────────
// Bac à sable : on met UNE fonctionnalité au point ici, isolément, avec les VRAIS get/put
// (aucune maquette, aucune donnée en dur — la base fait foi). Une fois qu'elle convient, elle
// DÉMÉNAGE dans la vraie page, et ce labo est vidé pour la tâche suivante.
//
// État : vide, en attente du prochain chantier.

export default function Labo() {
  return (
    <div>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">🧪 Labo</h2>
        <span className="text-xs text-gray-400">écran brouillon (réutilisable)</span>
      </div>
      <p className="text-xs text-gray-500 mb-6" style={{ maxWidth: 760, lineHeight: 1.6 }}>
        Cet écran est un <b>bac à sable</b> : on y construit une fonctionnalité <b>isolément</b>, avec les vrais
        <code> get</code>/<code>put</code> sur la base réelle (zéro donnée en dur). On l'affine tranquillement ici,
        puis — une fois validée — on la <b>déplace dans la vraie page</b>. Le labo est ensuite <b>vidé</b> pour la
        tâche suivante.
      </p>

      <div style={{ padding: '2.5rem', textAlign: 'center', color: '#94a3b8',
        background: 'white', borderRadius: 12, border: '1px dashed #cbd5e1' }}>
        Labo vide — en attente de la prochaine fonctionnalité à mettre au point.
      </div>
    </div>
  )
}
