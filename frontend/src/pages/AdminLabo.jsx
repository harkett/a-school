// Labo — écran d'ATTENTE.
//
// L'écran d'origine (pages/Labo.jsx, 76 Ko) a été débranché le 06/08/2026 : il faisait les mêmes
// gestes qu'Admin → Référentiels, et deux écrans sur le même geste finissent par diverger. Son
// entrée de menu et sa route reviennent ici, mais elles ouvrent cette page-là, pas l'ancienne —
// la place est tenue, le brouillon reste fermé.
//
// Son backend, lui, n'a jamais été démonté : `referentiels_labo` est toujours monté dans
// main.py, et ses routes répondent. C'est par là qu'une ligne de blocage a été posée sur un
// compte prof le 03/08/2026, sans que plus aucun écran ne permette de la lever.
export default function AdminLabo() {
  return (
    <div className="flex flex-col gap-6">
      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-3">
        <h2 className="text-base font-semibold text-gray-800">Labo</h2>
        <p className="text-sm text-gray-500 m-0">
          Écran en attente. Le laboratoire de mise au point des référentiels est fermé depuis le
          6 août 2026 : ce qu’il savait faire et qui manque à <strong>Admin → Référentiels</strong>
          {' '}doit d’abord y être porté.
        </p>
        <p className="text-sm text-gray-500 m-0">
          Le code de l’écran d’origine est conservé sur le disque
          (<code style={{ fontFamily: 'ui-monospace, monospace' }}>pages/Labo.jsx</code>), ainsi
          que son serveur
          (<code style={{ fontFamily: 'ui-monospace, monospace' }}>backend/pedagogie/referentiels_labo.py</code>).
          Rien n’a été supprimé.
        </p>
      </div>
    </div>
  )
}
