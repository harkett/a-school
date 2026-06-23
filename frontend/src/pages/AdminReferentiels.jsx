// Page Référentiels — PLACEHOLDER (entrée de menu non orpheline).
// La vraie page (téléversement du PDF, table `referentiels`, indexation,
// recherche à grande échelle) est le chantier de construction suivant.
export default function AdminReferentiels() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-base font-semibold text-gray-800">Référentiels</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Les référentiels officiels (PDF) qui ancrent la génération sur le vrai programme.
          Vous téléversez le PDF, le système l'indexe.
        </p>
      </div>

      <div style={{
        padding: '32px 24px', borderRadius: 10, border: '1px dashed #cbd5e1',
        background: '#f8fafc', textAlign: 'center', color: '#64748b', fontSize: 13, lineHeight: 1.6,
      }}>
        Page en construction.<br />
        À venir : téléversement des PDF, indexation, mise à jour et recherche.
      </div>
    </div>
  )
}
