import { Link, useLocation } from 'react-router-dom'

// Les cinq catégories de prompts, passées du MENU aux ONGLETS de la page (05/08/2026).
//
// Règle de répartition du backoffice : le menu de gauche porte la navigation — une entrée par
// écran — et la page porte ses options. Cinq entrées de menu pour un même écran encombraient la
// colonne sans rien apprendre : on ne navigue pas entre cinq écrans, on regarde le même sous cinq
// angles. Les URL, elles, ne changent pas : chaque catégorie garde la sienne, les liens et les
// favoris existants continuent de fonctionner.
//
// Composant partagé par AdminPrompts et AdminPromptsCycle : les deux rendent des catégories de la
// même liste, la barre doit être identique et le rester — une seule définition, pas deux copies
// qui divergeront.
const ONGLETS = [
  { to: '/admin/prompts/prof',     label: 'Prof' },
  { to: '/admin/prompts/admin',    label: 'Admin' },
  { to: '/admin/prompts/matieres', label: 'Matières par cycle' },
  { to: '/admin/prompts/decoupe',  label: 'Découpe (chunk) par cycle' },
  { to: '/admin/prompts/autres',   label: 'Autres' },
]

export default function OngletsPrompts() {
  const { pathname } = useLocation()
  return (
    <div style={{
      display: 'flex', gap: 4, flexWrap: 'wrap',
      borderBottom: '1px solid #e5e7eb', paddingBottom: 0, marginBottom: 4,
    }}>
      {ONGLETS.map(o => {
        const actif = pathname === o.to
        return (
          <Link
            key={o.to}
            to={o.to}
            style={{
              padding: '7px 14px', fontSize: 12,
              fontWeight: actif ? 600 : 500,
              color: actif ? '#A63045' : '#6b7280',
              // Le trait sous l'onglet actif prolonge la bordure du conteneur : l'onglet paraît
              // ouvert sur la page, au lieu de flotter au-dessus d'elle.
              borderBottom: actif ? '2px solid #A63045' : '2px solid transparent',
              marginBottom: -1,
              textDecoration: 'none', whiteSpace: 'nowrap', transition: 'color 0.15s',
            }}
            onMouseEnter={e => { if (!actif) e.currentTarget.style.color = '#374151' }}
            onMouseLeave={e => { if (!actif) e.currentTarget.style.color = '#6b7280' }}
          >
            {o.label}
          </Link>
        )
      })}
    </div>
  )
}
