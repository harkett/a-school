import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'

// LA CARTOUCHE « CONSOMMATION IA » — ce que la plateforme a dépensé, en un coup d'œil, en tête
// du tableau de bord (17/08/2026).
//
// POURQUOI ELLE EST LÀ ET PAS SEULEMENT DANS IA › STATISTIQUES. Une dépense qu'il faut aller
// chercher dans un écran dédié ne se regarde qu'une fois qu'on s'inquiète — c'est-à-dire trop
// tard. La facture d'un logiciel qui appelle un modèle à chaque geste de professeur est un
// indicateur de première page, au même rang que l'avancement.
//
// UN RÉSUMÉ, PAS UN ÉCRAN. Trois choses seulement, et rien d'autre : le total, qui a été payé,
// et pour quoi. Le détail (par modèle, par jour, tokens, cache, refus) reste à IA ›
// Statistiques, où le lien de la cartouche mène en un clic. Tout ce qui ne tient pas en une
// bande de colonnes n'a rien à faire ici.
//
// LES COLONNES SE LISENT DE HAUT EN BAS : le titre, puis le montant, puis le nombre d'appels.
// C'est la forme des tuiles de facturation d'Azure et de Google Cloud, et elle vaut pour la
// même raison — on compare des montants côte à côte, sans lire une seule étiquette de ligne.
//
// LA SOURCE EST CELLE DE L'ÉCRAN DÉTAILLÉ : `GET /api/admin/ia/usage?jours=N`. Aucun calcul
// n'est refait ici — deux façons de compter la même facture finiraient par donner deux montants,
// et c'est le genre d'écart qui décrédibilise les deux écrans d'un coup.

// Les trois fenêtres, dans l'ordre où on les consulte. `jours` est le paramètre déjà accepté par
// la route : rien à ajouter côté serveur pour changer de période.
const PERIODES = [
  { cle: 'jour',  label: 'Jour',  jours: 1,   phrase: "aujourd'hui" },
  { cle: 'mois',  label: 'Mois',  jours: 30,  phrase: 'sur 30 jours' },
  { cle: 'annee', label: 'Année', jours: 365, phrase: 'sur 12 mois' },
]

// Combien d'actions détaillées avant de replier le reste. Cinq colonnes tiennent sur une ligne
// d'écran ordinaire ; au-delà, la cartouche deviendrait l'écran qu'elle résume.
const ACTIONS_MONTREES = 5

const nb = n => (n ?? 0).toLocaleString('fr-FR')

// Un montant se lit à la précision qui compte : quelques centièmes de dollar sur une journée
// creuse, deux décimales dès qu'il y a une vraie facture. Zéro s'écrit « 0 $ » et pas « 0,0000 $ ».
const usd = v => {
  const x = v || 0
  if (x === 0) return '0 $'
  return `${x < 1 ? x.toFixed(3) : x.toFixed(2)} $`
}


export default function ConsommationIA() {
  const [periode, setPeriode] = useState(PERIODES[1])   // le mois : la fenêtre d'une facture

  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'ia', 'usage', periode.jours],
    queryFn: async () => {
      const r = await fetchWithTimeout(`/api/admin/ia/usage?jours=${periode.jours}`,
                                       { credentials: 'include' }, TIMEOUT_STD)
      return r.ok ? await r.json() : null
    },
    // La consommation d'hier ne change plus, celle du jour bouge lentement : cinq minutes de
    // fraîcheur suffisent, et le tableau de bord n'interroge pas la base à chaque retour d'onglet.
    staleTime: 5 * 60 * 1000,
  })

  const fournisseurs = data?.par_fournisseur || []
  const actions = data?.par_outil || []

  // Les actions les plus chères devant, le reste replié en une colonne. Trier par MONTANT et non
  // par volume : la cartouche répond à « où part l'argent », pas à « qui écrit le plus ».
  const parCout = [...actions].sort((a, b) => (b.cout_usd || 0) - (a.cout_usd || 0))
  const tete = parCout.slice(0, ACTIONS_MONTREES)
  const reste = parCout.slice(ACTIONS_MONTREES)
  const coutReste = reste.reduce((s, l) => s + (l.cout_usd || 0), 0)

  return (
    <div style={{
      background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10,
      padding: '14px 18px 13px', marginBottom: 18,
    }}>

      {/* ── L'en-tête : le titre, et le choix de la fenêtre ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
        <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#0f766e', flexShrink: 0 }} />
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em',
                       textTransform: 'uppercase', color: '#0f766e' }}>
          Consommation IA
        </span>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Les trois périodes en segments collés — un seul geste pour changer de fenêtre,
              sans liste à dérouler ni bouton à valider. */}
          <div style={{ display: 'inline-flex', border: '1px solid #e2e8f0', borderRadius: 7,
                        overflow: 'hidden' }}>
            {PERIODES.map(p => {
              const actif = p.cle === periode.cle
              return (
                <button
                  key={p.cle}
                  type="button"
                  onClick={() => setPeriode(p)}
                  title={`Ce qui a été dépensé ${p.phrase}`}
                  style={{
                    border: 'none', padding: '4px 11px', fontFamily: 'inherit', fontSize: 11.5,
                    fontWeight: actif ? 700 : 500, cursor: actif ? 'default' : 'pointer',
                    background: actif ? '#0f766e' : '#fff', color: actif ? '#fff' : '#64748b',
                  }}
                >
                  {p.label}
                </button>
              )
            })}
          </div>
          <Link to="/admin/ia/statistiques" title="Le détail : par modèle, par jour, tokens et cache"
                style={{ fontSize: 12, fontWeight: 600, color: '#1F6EEB', textDecoration: 'none',
                         whiteSpace: 'nowrap' }}>
            Détail →
          </Link>
        </div>
      </div>

      {isLoading && <div style={{ fontSize: 12.5, color: '#94a3b8' }}>Lecture de la consommation…</div>}

      {!isLoading && !data && (
        <div style={{ fontSize: 12.5, color: '#94a3b8' }}>Consommation indisponible.</div>
      )}

      {!isLoading && data && (
        <div style={{ display: 'flex', alignItems: 'stretch', gap: 20, flexWrap: 'wrap' }}>

          {/* ── LE TOTAL — la seule chose qu'on lit si on ne lit qu'une chose ── */}
          <div style={{ flex: '0 0 auto', paddingRight: 20, borderRight: '1px solid #f1f5f9',
                        minWidth: 130 }}>
            <div style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.02em',
                          color: data.cout_usd ? '#A63045' : '#166534' }}>
              {usd(data.cout_usd)}
            </div>
            <div style={{ fontSize: 11.5, color: '#94a3b8', marginTop: 2 }}>{periode.phrase}</div>
            <div style={{ fontSize: 11.5, color: '#64748b', marginTop: 6 }}>
              {nb(data.appels)} appel{data.appels > 1 ? 's' : ''}
            </div>
            {/* Un modèle sans tarif ne rend pas le total faux, il le rend INCOMPLET — et un
                montant incomplet lu comme une facture est pire qu'un montant absent. */}
            {data.cout_partiel && (
              <div style={{ fontSize: 10.5, color: '#b45309', marginTop: 4, lineHeight: 1.35 }}
                   title="Un ou plusieurs modèles n'ont pas de tarif renseigné dans Admin › IA › Fournisseurs">
                au moins — tarif manquant
              </div>
            )}
          </div>

          {/* ── LES DEUX BANDES : qui a été payé, et pour quoi ── */}
          <div style={{ flex: '1 1 420px', minWidth: 0, display: 'flex', flexDirection: 'column',
                        gap: 12 }}>
            <Bande
              titre="Par fournisseur"
              vide="Aucun appel sur la période."
              colonnes={fournisseurs.map(f => ({
                cle: f.cle, titre: f.libelle, montant: f.cout_usd, appels: f.appels,
                partiel: f.cout_partiel,
                // Le gratuit qui n'a rien coûté est une bonne nouvelle, pas un manque : il se
                // lit en vert, comme un appel qui n'a pas été payé.
                aide: `${f.libelle} — ${nb(f.appels)} appel(s), ${nb(f.tokens_entree)} jetons envoyés`,
              }))}
            />
            <Bande
              titre="Par action"
              vide="Aucun appel sur la période."
              colonnes={[
                ...tete.map(a => ({
                  cle: a.cle || 'non-precise', titre: a.libelle, montant: a.cout_usd,
                  appels: a.appels, partiel: a.cout_partiel,
                  aide: `${a.libelle} — ${nb(a.appels)} appel(s), ${nb(a.tokens_entree)} jetons envoyés`,
                })),
                // Le reste ne disparaît pas : il se replie. Une somme tronquée en silence ferait
                // un total de colonnes inférieur au total affiché à gauche, sans explication.
                ...(reste.length > 0 ? [{
                  cle: '__reste', titre: `${reste.length} autres`, montant: coutReste,
                  appels: reste.reduce((s, l) => s + (l.appels || 0), 0),
                  aide: reste.map(l => l.libelle).join(', '),
                }] : []),
              ]}
            />
          </div>
        </div>
      )}
    </div>
  )
}


// UNE BANDE DE COLONNES — un titre de bande, puis les colonnes titre / montant / appels.
//
// Les colonnes défilent horizontalement DANS LEUR BANDE si elles débordent : une cartouche de
// résumé ne doit jamais pousser la page vers la droite.
function Bande({ titre, colonnes, vide }) {
  return (
    <div>
      <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '0.05em',
                    textTransform: 'uppercase', color: '#cbd5e1', marginBottom: 6 }}>
        {titre}
      </div>
      {colonnes.length === 0 ? (
        <div style={{ fontSize: 12, color: '#cbd5e1' }}>{vide}</div>
      ) : (
        <div style={{ display: 'flex', gap: 22, overflowX: 'auto', paddingBottom: 2 }}>
          {colonnes.map(c => (
            <div key={c.cle} title={c.aide} style={{ minWidth: 92, flexShrink: 0 }}>
              <div style={{ fontSize: 11.5, color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden',
                            textOverflow: 'ellipsis', maxWidth: 150 }}>
                {c.titre}
              </div>
              <div style={{ fontSize: 15, fontWeight: 700, marginTop: 2,
                            color: c.montant ? '#1e293b' : '#166534' }}>
                {usd(c.montant)}{c.partiel && <span style={{ color: '#b45309' }}> +</span>}
              </div>
              <div style={{ fontSize: 10.5, color: '#cbd5e1', marginTop: 1 }}>
                {nb(c.appels)} appel{c.appels > 1 ? 's' : ''}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
