// Page « Base de données → Démos » — PANCARTE honnête : le chantier « mode démo »
// (une base de démonstration par cycle, fabriquée par l'admin, remise à zéro à la sortie)
// est conçu mais rien n'est codé. Cette page tient la place de la sous-option du menu
// pour qu'aucun clic ne tombe dans le vide ; elle sera remplacée par le vrai écran.
export default function AdminBaseDemos() {
  return (
    <div className="flex flex-col gap-6">
      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
        <div>
          <h2 className="text-base font-semibold text-gray-800">Bases de démonstration</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Les bases de démonstration que vous fabriquerez pour faire essayer la plateforme.
          </p>
        </div>
        <p style={{ fontSize: 13, color: '#64748b', margin: 0, lineHeight: 1.6, maxWidth: 560 }}>
          Cet écran est en préparation : rien n'est branché pour l'instant. Il accueillera la
          fabrication et la remise à zéro des bases de démonstration.
        </p>
      </div>
    </div>
  )
}
