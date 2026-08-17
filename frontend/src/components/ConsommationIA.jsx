import { useEffect, useRef, useState } from 'react'
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
// UN RÉSUMÉ, PAS UN ÉCRAN. Deux choses restent visibles en permanence : le total, et qui a été
// payé. Les ACTIONS — il y en a une vingtaine — se replient dans un menu déroulant : étalées en
// colonnes, elles faisaient de la cartouche l'écran qu'elle résume. On les ouvre quand on
// cherche où part l'argent, on les referme aussitôt.
//
// CE QUI RESTE VISIBLE SE LIT DE HAUT EN BAS : le titre, puis le montant, puis le nombre
// d'appels. C'est la forme des tuiles de facturation d'Azure et de Google Cloud, et elle vaut
// pour la même raison — on compare des montants côte à côte, sans lire une seule étiquette.
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

  // Les actions les plus chères en tête. Trier par MONTANT et non par volume : la cartouche
  // répond à « où part l'argent », pas à « qui écrit le plus ».
  const actions = [...(data?.par_outil || [])].sort((a, b) => (b.cout_usd || 0) - (a.cout_usd || 0))

  return (
    <div style={{
      background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10,
      padding: '14px 18px 13px', marginBottom: 18,
    }}>

      {/* ── L'en-tête : le titre, la fenêtre, et le menu des actions juste dessous ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 12,
                    flexWrap: 'wrap' }}>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#0f766e',
                       flexShrink: 0, marginTop: 7 }} />
        <span style={{ fontSize: 13, fontWeight: 800, letterSpacing: '0.05em',
                       textTransform: 'uppercase', color: '#0f766e' }}>
          Consommation IA
        </span>

        {/* LE TOTAL SUR LA LIGNE DU TITRE. Il occupait une colonne à lui seul sous l'en-tête,
            et c'était une colonne de plus pour un seul chiffre : le montant EST le sujet de la
            cartouche, il se lit donc dans son titre, pas en dessous.

            AU MILIEU, et pas collé au titre : deux marges automatiques, une de chaque côté,
            partagent l'espace libre à parts égales. Contre le titre, le montant se lisait
            comme la suite du mot « consommation » plutôt que comme un chiffre à lui. */}
        {!isLoading && data && (
          <span style={{ marginLeft: 'auto', display: 'inline-flex', alignItems: 'baseline',
                         gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 20, fontWeight: 800, letterSpacing: '-0.02em',
                           color: data.cout_usd ? '#A63045' : '#166534' }}>
              {usd(data.cout_usd)}
            </span>
            <span style={{ fontSize: 11.5, color: '#94a3b8' }}>
              {periode.phrase} · {nb(data.appels)} appel{data.appels > 1 ? 's' : ''}
            </span>
            {/* Un modèle sans tarif ne rend pas le total faux, il le rend INCOMPLET — et un
                montant incomplet lu comme une facture est pire qu'un montant absent. */}
            {data.cout_partiel && (
              <span style={{ fontSize: 10.5, color: '#b45309' }}
                    title="Un ou plusieurs modèles n'ont pas de tarif renseigné dans Admin › IA › Fournisseurs">
                au moins — tarif manquant
              </span>
            )}
          </span>
        )}

        <div style={{ marginLeft: 'auto', display: 'flex', flexDirection: 'column',
                      alignItems: 'flex-end', gap: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
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

          {/* Le menu des actions, sous la fenêtre qu'il suit : changer de période change ce
              qu'il contient, la place le dit sans qu'une phrase soit nécessaire. */}
          <ComboActions actions={actions} />
        </div>
      </div>

      {isLoading && <div style={{ fontSize: 12.5, color: '#94a3b8' }}>Lecture de la consommation…</div>}

      {!isLoading && !data && (
        <div style={{ fontSize: 12.5, color: '#94a3b8' }}>Consommation indisponible.</div>
      )}

      {!isLoading && data && (
        <Bande
          titre="Par fournisseur"
          vide="Aucun appel sur la période."
          colonnes={fournisseurs.map(f => ({
            cle: f.cle, titre: f.libelle, montant: f.cout_usd, appels: f.appels,
            partiel: f.cout_partiel,
            aide: `${f.libelle} — ${nb(f.appels)} appel(s), ${nb(f.tokens_entree)} jetons envoyés`,
          }))}
        />
      )}
    </div>
  )
}


// LE MENU DES ACTIONS — fermé, il tient sur une ligne ; ouvert, il donne TOUT.
//
// Rien n'est tronqué ici, et c'est la raison d'être du menu : une liste repliée peut être
// complète, une bande de colonnes ne le peut pas. Le « + 12 autres » qui masquait le reste
// disparaît avec elle.
//
// Un menu écrit à la main plutôt qu'un <select> natif : le natif ne sait afficher qu'une chaîne
// par ligne, donc le montant se collerait au libellé au lieu de s'aligner à droite — et c'est
// justement la colonne qu'on vient lire.
function ComboActions({ actions }) {
  const [ouvert, setOuvert] = useState(false)
  const boite = useRef(null)

  // Un menu se ferme au clic dehors ET à Échap. Sans ça, il reste ouvert par-dessus la page
  // pendant qu'on essaie de lire ce qu'il recouvre.
  useEffect(() => {
    if (!ouvert) return
    const dehors = e => { if (boite.current && !boite.current.contains(e.target)) setOuvert(false) }
    const echap = e => { if (e.key === 'Escape') setOuvert(false) }
    document.addEventListener('mousedown', dehors)
    document.addEventListener('keydown', echap)
    return () => {
      document.removeEventListener('mousedown', dehors)
      document.removeEventListener('keydown', echap)
    }
  }, [ouvert])

  const vide = actions.length === 0
  // La part de la plus chère sert d'échelle aux barres : elles comparent les actions entre
  // elles, pas au total — sinon toutes seraient des traits invisibles sauf la première.
  const plusCher = actions.reduce((m, a) => Math.max(m, a.cout_usd || 0), 0)

  return (
    <div ref={boite} style={{ position: 'relative' }}>
      <button
        type="button"
        onClick={() => setOuvert(o => !o)}
        disabled={vide}
        title={vide ? 'Aucun appel sur la période'
                    : 'Voir ce que chaque action a coûté sur la période'}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 8, minWidth: 210,
          border: '1px solid #e2e8f0', borderRadius: 7, background: '#fff',
          padding: '4px 10px', fontFamily: 'inherit', fontSize: 11.5, color: '#64748b',
          cursor: vide ? 'not-allowed' : 'pointer',
        }}
      >
        <span style={{ fontWeight: 600 }}>Par action</span>
        <span style={{ color: '#cbd5e1' }}>
          {vide ? 'aucune' : `${actions.length} action${actions.length > 1 ? 's' : ''}`}
        </span>
        <svg style={{ marginLeft: 'auto', transform: ouvert ? 'rotate(180deg)' : 'none',
                      transition: 'transform 0.12s' }}
             width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {ouvert && !vide && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 4px)', right: 0, zIndex: 30,
          width: 340, maxHeight: 300, overflowY: 'auto',
          background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8,
          boxShadow: '0 10px 26px rgba(15,23,42,0.13)', padding: '6px 0',
        }}>
          {actions.map(a => (
            // UNE ACTION PAR LIGNE : ce qu'elle est, ce qu'elle a coûté, et la barre qui la
            // situe face à la plus chère. Le nombre d'appels en dessous répond à la question
            // suivante — cher parce que souvent, ou cher parce que long ?
            <div key={a.cle || 'non-precise'}
                 style={{ padding: '6px 12px' }}
                 title={`${nb(a.tokens_entree)} jetons envoyés, ${nb(a.tokens_sortie)} produits`}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
                <span style={{ flex: 1, minWidth: 0, fontSize: 12, color: '#334155',
                               overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {a.libelle}
                </span>
                <span style={{ fontSize: 12.5, fontWeight: 700, whiteSpace: 'nowrap',
                               color: a.cout_usd ? '#1e293b' : '#166534' }}>
                  {usd(a.cout_usd)}{a.cout_partiel && <span style={{ color: '#b45309' }}> +</span>}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 3 }}>
                <div style={{ flex: 1, height: 3, borderRadius: 2, background: '#f1f5f9' }}>
                  <div style={{
                    width: `${plusCher ? Math.round(100 * (a.cout_usd || 0) / plusCher) : 0}%`,
                    height: '100%', borderRadius: 2, background: '#0f766e',
                  }} />
                </div>
                <span style={{ fontSize: 10.5, color: '#cbd5e1', whiteSpace: 'nowrap' }}>
                  {nb(a.appels)} appel{a.appels > 1 ? 's' : ''}
                </span>
              </div>
            </div>
          ))}
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
