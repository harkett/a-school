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

const IconTarget = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>
  </svg>
)

const IconUser = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)

const IconSparkle = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
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
    id: 'apprentissage',
    titre: 'A-SCHOOL apprend votre style',
    Icon: IconSparkle,
    contenu: (
      <div className="flex flex-col gap-4 text-sm text-gray-600">
        <p>
          Chaque activité que vous sauvegardez est un exemple que A-SCHOOL retient.
          À partir du <strong>3e exemple du même type</strong>, il reconnaît votre façon
          de travailler et génère un résultat dans votre style.
        </p>
        <p className="text-xs text-gray-400 italic">Rien à configurer — cela se fait automatiquement.</p>

        <div className="rounded-lg overflow-hidden border border-gray-200">
          <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide bg-gray-50">
            Exemple — Questions de compréhension (Français, 4e)
          </div>
          <div className="flex flex-col divide-y divide-gray-100">
            <div className="px-4 py-3">
              <div className="text-xs font-medium text-gray-400 mb-1">Avant — génération standard</div>
              <div className="text-gray-500 italic">
                "À partir du texte proposé, identifiez et expliquez le rôle du personnage principal
                dans la progression narrative, en vous appuyant sur des exemples précis tirés du document."
              </div>
            </div>
            <div className="px-4 py-3" style={{ background: '#eff6ff' }}>
              <div className="text-xs font-medium mb-1" style={{ color: 'var(--bleu)' }}>
                Après — adapté au style de ce professeur
              </div>
              <div className="text-gray-700">
                "1. Quel est le rôle du personnage principal ?<br />
                2. Comment évolue-t-il au fil du texte ?"
              </div>
            </div>
          </div>
        </div>

        <p className="text-xs text-gray-500">
          A-SCHOOL s'affine progressivement à chaque utilisation.
          Plus vous l'utilisez, moins vous corrigez.
        </p>
      </div>
    ),
  },
  {
    id: 'comment',
    titre: 'Comment utiliser A-SCHOOL',
    Icon: IconBook,
    contenu: (
      <ol className="flex flex-col gap-3 text-sm text-gray-600">
        <li className="flex gap-3">
          <span className="font-semibold shrink-0" style={{ color: 'var(--bleu)' }}>1.</span>
          <span><strong>Configurez votre profil</strong> (menu "Mon profil") — renseignez votre prénom, nom, matière et niveau habituel. Ces informations personnalisent l'interface à chaque connexion.</span>
        </li>
        <li className="flex gap-3">
          <span className="font-semibold shrink-0" style={{ color: 'var(--bleu)' }}>2.</span>
          <span><strong>Collez un texte source</strong> dans la zone principale — un extrait de manuel, un document élève, un article de presse.</span>
        </li>
        <li className="flex gap-3">
          <span className="font-semibold shrink-0" style={{ color: 'var(--bleu)' }}>3.</span>
          <span><strong>Choisissez les paramètres</strong> : niveau scolaire, type d'activité, nombre de questions, avec ou sans correction.</span>
        </li>
        <li className="flex gap-3">
          <span className="font-semibold shrink-0" style={{ color: 'var(--bleu)' }}>4.</span>
          <span><strong>Cliquez sur "Générer"</strong> — A-SCHOOL produit l'activité en quelques secondes.</span>
        </li>
        <li className="flex gap-3">
          <span className="font-semibold shrink-0" style={{ color: 'var(--bleu)' }}>5.</span>
          <span><strong>Retrouvez vos activités</strong> dans "Mes activités" — chaque génération est sauvegardée automatiquement et peut être rechargée en un clic.</span>
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
          <dt className="font-semibold text-gray-700">Matière</dt>
          <dd className="mt-0.5 flex flex-col gap-2">
            <span>A-SCHOOL propose 12 matières : Français, Histoire-Géographie, Mathématiques, Physique-Chimie, SVT, SES, NSI, Philosophie, Langues vivantes, Technologie, Arts et EPS.</span>
            <span><strong>Votre matière de profil</strong> est définie à l'inscription et modifiable via "Mon profil" — c'est votre identité par défaut, elle persiste d'une connexion à l'autre.</span>
            <span><strong>Le sélecteur de matière dans les paramètres</strong> vous permet de changer de matière pour la session en cours uniquement, sans toucher à votre profil. Utile si vous intervenez ponctuellement dans une autre discipline ou souhaitez tester des activités d'une autre matière.</span>
          </dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Niveau</dt>
          <dd className="mt-0.5">Le niveau scolaire de vos élèves, de la 6e à la Terminale. Influence le vocabulaire et la complexité de l'activité. Votre niveau habituel est mémorisé d'une session à l'autre. Le niveau Supérieur (BTS, prépa) est en cours de développement.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Type d'activité</dt>
          <dd className="mt-0.5">Le genre d'exercice à produire — varie selon la matière (compréhension, vocabulaire, résumé, exercices…). Chaque type génère un format différent.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Nombre de questions</dt>
          <dd className="mt-0.5">Le nombre d'items dans l'activité. Disponible selon le type choisi.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Avec correction</dt>
          <dd className="mt-0.5">Si activé, A-SCHOOL ajoute la correction complète sous l'activité — pratique pour préparer votre cours ou gagner du temps sur la correction.</dd>
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
        <li className="flex gap-2"><span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span><span><strong>Régénérez si nécessaire</strong> — le bouton "Régénérer" relance une nouvelle génération avec les mêmes paramètres, sans ressaisir le texte.</span></li>
      </ul>
    ),
  },
  {
    id: 'conseils-utilisation',
    titre: 'Conseils d\'utilisation',
    Icon: IconTarget,
    contenu: (
      <ul className="flex flex-col gap-3 text-sm text-gray-600">
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Choisissez le type d'activité selon votre objectif</strong> — "Questions de compréhension" pour vérifier la lecture, "Production d'écrit" pour entraîner à la rédaction, "Fiche de révision" pour synthétiser un chapitre.</span>
        </li>
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Précisez le sous-type</strong> — plus votre choix est ciblé (ex : "inférence" plutôt que "mélange"), plus le résultat est adapté à ce que vous cherchez.</span>
        </li>
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Sauvegardez les activités qui vous conviennent</strong> — chaque génération sauvegardée est un exemple que A-SCHOOL retient pour apprendre votre style (voir "A-SCHOOL apprend votre style").</span>
        </li>
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Activez "Avec correction"</strong> pour obtenir le corrigé en même temps que l'activité — gain de temps direct pour la préparation de cours.</span>
        </li>
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Relisez avant de distribuer</strong> — A-SCHOOL produit une base solide, mais un regard professionnel sur le résultat garantit la pertinence pédagogique.</span>
        </li>
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Utilisez l'historique</strong> — retrouvez une ancienne activité dans "Mes activités" et rechargez-la en un clic pour la réutiliser ou la faire évoluer.</span>
        </li>
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Régénérez sans hésiter</strong> — chaque génération est différente. Si le premier résultat ne correspond pas, une seconde tentative avec le même texte peut donner exactement ce que vous cherchez.</span>
        </li>
      </ul>
    ),
  },
  {
    id: 'espace',
    titre: 'Votre espace & retours',
    Icon: IconUser,
    contenu: (
      <dl className="flex flex-col gap-4 text-sm text-gray-600">
        <div>
          <dt className="font-semibold text-gray-700">Mon profil</dt>
          <dd className="mt-0.5">Modifiez votre prénom, nom, matière et niveau par défaut depuis le menu latéral. Ces données sont enregistrées sur votre compte et persistent d'une session à l'autre.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Mes activités</dt>
          <dd className="mt-0.5">Toutes vos générations sont sauvegardées automatiquement. Cliquez sur une activité pour recharger le texte source, les paramètres et le résultat en un clic.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Notez A-SCHOOL</dt>
          <dd className="mt-0.5">Donnez votre avis en 30 secondes — de 1 à 5 étoiles, avec un commentaire optionnel. Vos retours nous aident directement à améliorer la plateforme.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Envoyer un feedback</dt>
          <dd className="mt-0.5">Signalez un problème, proposez une amélioration ou posez une question. Si un type d'activité vous manque, c'est ici que vous pouvez le suggérer.</dd>
        </div>
      </dl>
    ),
  },
  {
    id: 'problemes',
    titre: 'Trucs et astuces',
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
          <dt className="font-semibold text-gray-700">Un type d'activité est absent ou incorrect</dt>
          <dd className="mt-0.5">Utilisez "Envoyer un feedback" dans le menu latéral pour le signaler. C'est directement intégré au développement de la plateforme.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Le niveau Supérieur affiche un message de développement</dt>
          <dd className="mt-0.5">Les activités pour le niveau Supérieur (BTS, prépa, licence) sont en cours de développement. Les autres niveaux (6e à Terminale) sont pleinement opérationnels.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">La traduction automatique perturbe les activités</dt>
          <dd className="mt-0.5">
            A-SCHOOL génère des activités en français. Si vous laissez votre navigateur traduire la page,
            les paramètres envoyés à la génération sont altérés — les activités produites seront incohérentes
            ou de mauvaise qualité.<br />
            <strong>Solution :</strong> lorsque Chrome ou Edge propose de traduire, cliquez sur{' '}
            <strong>« Plus »</strong> puis <strong>« Ne jamais traduire ce site »</strong>.
          </dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Erreur lors de la génération</dt>
          <dd className="mt-0.5">Vérifiez votre connexion internet. Si le problème persiste, contactez <a href="mailto:contact@aschool.fr" className="underline hover:text-gray-800">contact@aschool.fr</a>.</dd>
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
