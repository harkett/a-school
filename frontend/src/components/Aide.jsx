import { useState } from 'react'

const IconBook = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
  </svg>
)

const IconSliders = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/>
    <line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/>
    <line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/>
    <line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>
  </svg>
)

const IconBulb = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/>
    <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>
  </svg>
)

const IconAlert = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
)

const ChevronDown = ({ open }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2"
    style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.25s ease', flexShrink: 0 }}>
    <polyline points="6 9 12 15 18 9"/>
  </svg>
)

const sections = [
  {
    id: 'comment',
    titre: 'Comment utiliser A-SCHOOL',
    Icon: IconBook,
    contenu: (
      <ol className="flex flex-col gap-3 text-sm text-gray-600">
        <li className="flex gap-3">
          <span className="font-semibold shrink-0" style={{ color: 'var(--bleu)' }}>1.</span>
          <span><strong>Collez un texte source</strong> dans la zone de texte principale — un extrait de manuel, un document élève, un article.</span>
        </li>
        <li className="flex gap-3">
          <span className="font-semibold shrink-0" style={{ color: 'var(--bleu)' }}>2.</span>
          <span><strong>Choisissez les paramètres</strong> : niveau scolaire, type d'activité, nombre de questions.</span>
        </li>
        <li className="flex gap-3">
          <span className="font-semibold shrink-0" style={{ color: 'var(--bleu)' }}>3.</span>
          <span><strong>Cliquez sur "Générer"</strong> — A-SCHOOL produit l'activité en quelques secondes.</span>
        </li>
      </ol>
    ),
  },
  {
    id: 'champs',
    titre: 'Les champs expliqués',
    Icon: IconSliders,
    contenu: (
      <dl className="flex flex-col gap-4 text-sm text-gray-600">
        <div>
          <dt className="font-semibold text-gray-700">Niveau</dt>
          <dd className="mt-0.5">Le niveau scolaire de vos élèves, de la 6e à la Terminale. Influence le vocabulaire et la complexité de l'activité générée.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Type d'activité</dt>
          <dd className="mt-0.5">Le genre d'exercice à produire (compréhension, vocabulaire, résumé…). Chaque type génère un format différent.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Nombre de questions</dt>
          <dd className="mt-0.5">Le nombre d'items dans l'activité. Disponible selon le type choisi.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Avec correction</dt>
          <dd className="mt-0.5">Si activé, A-SCHOOL ajoute la correction complète sous l'activité — pratique pour préparer votre cours.</dd>
        </div>
      </dl>
    ),
  },
  {
    id: 'conseils',
    titre: 'Conseils pour un bon texte source',
    Icon: IconBulb,
    contenu: (
      <ul className="flex flex-col gap-2 text-sm text-gray-600">
        <li className="flex gap-2"><span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span><span><strong>200 à 1 000 mots</strong> — en dessous le résultat manque de matière, au-dessus il peut perdre en précision.</span></li>
        <li className="flex gap-2"><span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span><span><strong>Texte structuré</strong> — préférez des paragraphes rédigés à des listes ou des tableaux.</span></li>
        <li className="flex gap-2"><span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span><span><strong>Langue française</strong> — A-SCHOOL est optimisé pour les textes en français.</span></li>
        <li className="flex gap-2"><span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span><span><strong>Sujet cohérent</strong> — un extrait avec un thème clair donne de meilleurs résultats qu'un assemblage de fragments.</span></li>
      </ul>
    ),
  },
  {
    id: 'problemes',
    titre: 'Problèmes fréquents',
    Icon: IconAlert,
    contenu: (
      <dl className="flex flex-col gap-4 text-sm text-gray-600">
        <div>
          <dt className="font-semibold text-gray-700">Le bouton "Générer" ne fait rien</dt>
          <dd className="mt-0.5">Vérifiez que la zone de texte source n'est pas vide. Le bouton est grisé tant que le texte manque.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Le résultat ne correspond pas à mes attentes</dt>
          <dd className="mt-0.5">Essayez un autre type d'activité, ajustez le niveau, ou utilisez un texte source plus clair et mieux structuré. Le bouton "Régénérer" relance une nouvelle génération avec les mêmes paramètres.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Erreur lors de la génération</dt>
          <dd className="mt-0.5">Vérifiez votre connexion internet. Si le problème persiste, contactez <a href="mailto:harketti@afia.fr" className="underline hover:text-gray-800">harketti@afia.fr</a>.</dd>
        </div>
      </dl>
    ),
  },
]

export default function Aide() {
  const [open, setOpen] = useState('comment')

  return (
    <div className="flex flex-col gap-3 max-w-2xl">
      <h2 className="text-base font-semibold text-gray-800 mb-1">Aide</h2>
      {sections.map(s => {
        const isOpen = open === s.id
        return (
          <div
            key={s.id}
            className="bg-white rounded-lg border overflow-hidden shadow-sm"
            style={{
              borderColor: isOpen ? 'var(--bleu)' : '#e5e7eb',
              borderLeftWidth: isOpen ? '3px' : '1px',
              transition: 'border-color 0.2s ease',
            }}
          >
            <button
              onClick={() => setOpen(isOpen ? null : s.id)}
              title={isOpen ? 'Réduire cette section' : 'Développer cette section'}
              className="w-full flex items-center gap-3 px-5 py-4 text-sm font-medium hover:bg-gray-50 transition-colors"
              style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', color: isOpen ? 'var(--bleu)' : '#1f2937' }}
            >
              <span style={{ color: isOpen ? 'var(--bleu)' : '#6b7280', transition: 'color 0.2s ease' }}>
                <s.Icon />
              </span>
              <span className="flex-1">{s.titre}</span>
              <span style={{ color: isOpen ? 'var(--bleu)' : '#9ca3af', transition: 'color 0.2s ease' }}>
                <ChevronDown open={isOpen} />
              </span>
            </button>
            <div
              style={{
                display: 'grid',
                gridTemplateRows: isOpen ? '1fr' : '0fr',
                transition: 'grid-template-rows 0.25s ease',
              }}
            >
              <div style={{ overflow: 'hidden' }}>
                <div className="px-5 pb-5 border-t border-gray-100 pt-4">
                  {s.contenu}
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
