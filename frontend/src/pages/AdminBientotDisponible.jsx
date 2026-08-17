import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'

// Écran « Tâches à faire → Bientôt disponible » (16/08/2026).
//
// CE QUE LE PROFESSEUR VOIT, ET CE QU'ON LUI PROMET. Les cartes de son écran « Bientôt
// disponible » vivent en base (table `features_votables`) : l'administrateur ne pouvait les
// lire qu'en ouvrant l'application de son côté. Elles sont ici, telles qu'il les lit, avec
// ce qu'elles ont récolté.
//
// LES DEUX CASES, ET LEUR LIEN. « Livrée » veut dire que la fonctionnalité existe : sa carte
// quitte l'écran du professeur, car on ne fait pas voter pour ce qui est fait. « Nouveauté »
// l'annonce dans son bandeau d'accueil — elle ne s'ouvre que sur une ligne livrée, et se
// recoche des mois plus tard quand la fonctionnalité est améliorée. Le serveur tient la même
// règle : décocher « livrée » retire « nouveauté ».
//
// Le TEXTE des cartes, lui, ne se modifie pas ici : une promesse faite aux professeurs se
// change par migration, comme elle a été posée.
export default function AdminBientotDisponible() {
  const qc = useQueryClient()

  const { data: features, isError } = useQuery({
    queryKey: ['admin', 'feature-votes'],
    queryFn: async () => {
      const r = await fetchWithTimeout('/api/admin/feature-votes', { credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) throw new Error('Liste illisible')
      return await r.json()
    },
  })

  async function basculer(f, champ) {
    const etat = { livree: f.livree, nouveaute: f.nouveaute, [champ]: !f[champ] }
    // Décocher « livrée » éteint « nouveauté » : la règle se voit avant même la réponse.
    if (!etat.livree) etat.nouveaute = false
    try {
      const r = await fetchWithTimeout(`/api/admin/feature-votes/${f.key}`, {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(etat),
      }, TIMEOUT_STD)
      if (!r.ok) throw new Error('enregistrement refusé par le serveur')
      await qc.invalidateQueries({ queryKey: ['admin', 'feature-votes'] })
      // L'encart « À traiter » du tableau de bord compte les fonctionnalités livrées non
      // annoncées : cocher ici en retire une, la liste doit suivre sans attendre son heure.
      await qc.invalidateQueries({ queryKey: ['admin', 'actions'] })
    } catch (e) {
      showError('La case n’a pas pu être enregistrée : ' + e.message)
    }
  }

  if (isError)   return <p className="text-red-600 text-sm">Impossible de charger les fonctionnalités annoncées.</p>
  if (!features) return <p className="text-gray-400 text-sm">Chargement…</p>

  // L'ordre d'affichage est celui du professeur (`ordre`), pas celui des votes : on lit ici la
  // page telle qu'elle se présente à lui. Le classement par popularité a déjà son écran.
  const liste     = [...features].sort((a, b) => (a.ordre ?? 0) - (b.ordre ?? 0))
  const attendues = liste.filter(f => f.actif && !f.livree).length
  const annoncees = liste.filter(f => f.livree && f.nouveaute).length
  const total     = liste.reduce((s, f) => s + f.count, 0)

  return (
    <div className="flex flex-col gap-4">

      <div style={{
        background: '#eff6ff', border: '1px solid #bfdbfe', borderLeft: '4px solid #3b82f6',
        borderRadius: 8, padding: '12px 16px',
      }}>
        <div style={{ fontSize: 11, color: '#3b82f6', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
          Ce que le professeur voit
        </div>
        <div style={{ fontSize: 22, fontWeight: 800, color: '#1e3a8a', lineHeight: 1.2, marginTop: 2 }}>
          {attendues} à venir · {annoncees} en nouveauté
        </div>
        <div className="text-xs" style={{ color: '#64748b', marginTop: 4 }}>
          Écran « Bientôt disponible » du professeur · {total} vote{total > 1 ? 's' : ''} au total.
          Cochez <b>Livrée</b> quand la fonctionnalité existe : sa carte quitte son écran.
          Cochez ensuite <b>Nouveauté</b> pour l’annoncer dans son bandeau d’accueil —
          une seule à la fois : la précédente se décoche d’elle-même.
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {liste.map(f => (
          <div key={f.key}
               className="bg-white rounded-xl border border-gray-200 px-5 py-4"
               style={{ opacity: (f.actif || f.livree) ? 1 : 0.55 }}>

            <div className="flex items-start justify-between gap-4" style={{ flexWrap: 'wrap' }}>

              <div style={{ flex: '1 1 380px', minWidth: 0 }}>
                <div className="flex items-center gap-2 mb-1" style={{ flexWrap: 'wrap' }}>
                  <span className="text-sm font-semibold text-gray-800">{f.label}</span>
                  <span style={etiquette('#f1f5f9', '#64748b', '#e2e8f0')}>{f.categorie}</span>
                  {f.livree && <span style={etiquette('#ecfdf5', '#065f46', '#a7f3d0')}>livrée</span>}
                  {f.livree && f.nouveaute && <span style={etiquette('#fffbeb', '#92400e', '#fde68a')}>en nouveauté</span>}
                  {/* Une carte retirée de l'écran prof garde ses votes : le dire, sinon le
                      chiffre d'à côté se lit comme un engouement actuel. */}
                  {!f.actif && !f.livree && <span style={etiquette('#fef2f2', '#b91c1c', '#fecaca')}>retirée de l’écran prof</span>}
                </div>
                <p className="text-xs text-gray-500" style={{ lineHeight: 1.55, margin: 0 }}>
                  {f.description}
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexShrink: 0 }}>
                <Case
                  label="Livrée"
                  aide="La fonctionnalité existe : sa carte quitte l’écran « Bientôt disponible » du professeur. Ses votes sont conservés."
                  coche={f.livree}
                  onChange={() => basculer(f, 'livree')}
                />
                <Case
                  label="Nouveauté"
                  aide={f.livree
                    ? 'Annonce la fonctionnalité dans le bandeau d’accueil du professeur — et décoche celle qui y était : on n’annonce qu’une chose à la fois. À recocher si elle est améliorée plus tard.'
                    : 'Cochez d’abord « Livrée » : on n’annonce en nouveauté que ce qui existe.'}
                  coche={f.nouveaute}
                  off={!f.livree}
                  onChange={() => basculer(f, 'nouveaute')}
                />
                <div style={{ textAlign: 'right', minWidth: 62 }}>
                  <div className="text-sm font-bold" style={{ color: f.count > 0 ? '#A63045' : '#94a3b8' }}>
                    {f.count}
                  </div>
                  <div style={{ fontSize: 10.5, color: '#94a3b8' }}>vote{f.count !== 1 ? 's' : ''}</div>
                </div>
              </div>

            </div>
          </div>
        ))}
      </div>

    </div>
  )
}

const etiquette = (fond, texte, bord) => ({
  fontSize: 10.5, padding: '1px 8px', borderRadius: 5, whiteSpace: 'nowrap',
  background: fond, color: texte, border: '1px solid ' + bord,
})

// Norme maison : une bulle d'aide sur chaque commande, et le curseur interdit quand elle est
// grisée — la case « Nouveauté » d'une ligne non livrée doit REFUSER le clic, pas l'ignorer.
function Case({ label, aide, coche, off = false, onChange }) {
  return (
    <label
      title={aide}
      style={{
        display: 'flex', alignItems: 'center', gap: 7,
        cursor: off ? 'not-allowed' : 'pointer',
        opacity: off ? 0.45 : 1, userSelect: 'none',
      }}
    >
      <input
        type="checkbox"
        checked={coche}
        disabled={off}
        onChange={onChange}
        style={{ width: 16, height: 16, cursor: off ? 'not-allowed' : 'pointer', accentColor: '#1F6EEB' }}
      />
      <span style={{ fontSize: 12.5, fontWeight: 600, color: off ? '#94a3b8' : '#334155' }}>{label}</span>
    </label>
  )
}
