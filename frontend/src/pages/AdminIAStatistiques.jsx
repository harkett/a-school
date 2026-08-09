import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

// IA › Statistiques — ce que l'IA a consommé, et ce que ça coûte.
//
// L'écran lit `usage_llm` : une ligne par appel LLM réussi, posée par `_journal_appel`. Les trois
// onglets regroupent LES MÊMES lignes sous trois angles — par modèle (ce que chacun consomme), par
// tâche (quel outil dépense), par période (la dérive avant la facture).
//
// LE COÛT EST UNE ESTIMATION, et l'écran le dit au lieu de le laisser croire : il vient des tarifs
// de `ai_modeles`, qui ne sont renseignés que pour les modèles dont la grille a été relevée. Un
// modèle sans tarif affiche ses tokens et un tiret — jamais un zéro, qui se lirait « gratuit ».

const ONGLETS = [
  { cle: 'modele',  label: 'Par modèle',  champ: 'par_modele',
    quoi: 'Ce que chaque modèle a consommé, et d’où venait l’appel : tokens envoyés, tokens produits, coût estimé.',
    entete: 'Modèle', cout: true, origine: true },
  { cle: 'tache',   label: 'Par tâche',   champ: 'par_outil',
    quoi: 'La même consommation, vue par usage : découpe d’un référentiel, rédaction d’une activité, détections…',
    entete: 'Tâche', cout: false },
  { cle: 'jour',    label: 'Par jour',    champ: 'par_jour',
    quoi: 'L’évolution dans le temps, pour repérer une dérive avant la facture.',
    entete: 'Jour', cout: false },
]

const nb = n => (n ?? 0).toLocaleString('fr-FR')

// Un coût par appel se compte en centimes : 2 décimales afficheraient « 0,00 $ » sur une découpe
// à 30 centimes de dollar. On descend à 4 décimales tant que le total reste sous le dollar.
const usd = v => v == null ? '—' : `${v < 1 ? v.toFixed(4) : v.toFixed(2)} $`

export default function AdminIAStatistiques() {
  const [onglet, setOnglet]   = useState('modele')
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [erreur, setErreur]   = useState('')
  const navigate = useNavigate()

  // Fenêtre d'observation : le DÉFAUT du serveur, sans réglage à l'écran. Le paramètre `jours`
  // existe côté API et reste utilisable, mais il n'a pas d'affichage tant qu'on n'a pas décidé
  // de sa forme — trois boutons n'en étaient pas une.
  // Aucun setState avant le fetch : `loading` vaut déjà true et `erreur` déjà '' au premier
  // rendu (leurs valeurs de départ). Les réécrire ici ne changeait rien à l'écran et forçait un
  // rendu complet de plus avant même que la lecture soit partie.
  useEffect(() => {
    fetch('/api/admin/ia/usage', { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        if (!r.ok) throw new Error('lecture impossible')
        return r.json()
      })
      .then(d => { if (d) setData(d) })
      .catch(() => setErreur('Impossible de lire la consommation.'))
      .finally(() => setLoading(false))
  }, [navigate])

  const courant = ONGLETS.find(o => o.cle === onglet)
  const lignes  = data?.[courant.champ] || []

  return (
    <div className="flex flex-col gap-4">

      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-1">Statistiques</h2>
        <p className="text-xs text-gray-400">
          Ce que l’IA consomme, et ce que ça coûte
          {data ? ` — sur les ${data.jours} derniers jours.` : '.'}
        </p>
      </div>

      {data && !erreur && (
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {/* Les rejeux du cache disque (dev) sont DANS le total et annoncés dessous : les retirer
              ferait disparaître le travail du cache, alors que c'est ce qu'on veut voir. La note
              n'apparaît que s'il y en a — en production, cette carte est celle d'avant. */}
          <Carte titre="Appels"          valeur={nb(data.appels)}
                 note={data.appels_cache ? `dont ${nb(data.appels_cache)} rejoué${data.appels_cache > 1 ? 's' : ''} par le cache (0 $)` : null} />
          {/* Les tokens relus dans le cache du fournisseur SONT dans ce total : ils ont bien été
              envoyés, ils ont simplement coûté 10 %. Anthropic les compte à part — s'ils étaient
              laissés dehors, un appel qui vient de lire un référentiel entier s'afficherait à
              quelques dizaines de tokens. */}
          <Carte titre="Tokens envoyés"  valeur={nb(data.tokens_entree)}
                 note={data.tokens_cache_lecture
                   ? `dont ${nb(data.tokens_cache_lecture)} relus en cache (payés 10 %)` : null} />
          <Carte titre="Tokens produits" valeur={nb(data.tokens_sortie)} />
          <Carte titre="Coût estimé"     valeur={usd(data.cout_usd)}
                 note={data.cout_partiel ? 'hors modèles sans tarif' : null} />
        </div>
      )}

      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #e5e7eb' }}>
        {ONGLETS.map(o => {
          const actif = onglet === o.cle
          return (
            <button
              key={o.cle}
              onClick={() => setOnglet(o.cle)}
              title={o.quoi}
              style={{
                padding: '7px 14px', fontSize: 12, fontWeight: actif ? 600 : 500,
                color: actif ? '#A63045' : '#6b7280', background: 'transparent',
                border: 'none', borderBottom: actif ? '2px solid #A63045' : '2px solid transparent',
                marginBottom: -1, cursor: 'pointer',
              }}
            >
              {o.label}
            </button>
          )
        })}
      </div>

      {loading && <p className="text-xs text-gray-400" style={{ padding: 20 }}>Chargement…</p>}

      {!loading && erreur && (
        <p className="text-xs" style={{ color: '#ef4444', padding: 20 }}>{erreur}</p>
      )}

      {/* Aucune ligne n'est PAS une erreur : c'est une installation qui n'a pas encore appelé l'IA
          sur la période. On le dit ainsi, plutôt qu'avec un tableau vide qu'on croirait cassé. */}
      {!loading && !erreur && lignes.length === 0 && (
        <div style={{
          border: '1px dashed #d1d5db', borderRadius: 10, padding: '28px 20px',
          textAlign: 'center', background: '#fafafa',
        }}>
          <p className="text-sm font-semibold text-gray-600 mb-2">Aucun appel sur la période</p>
          <p className="text-xs text-gray-500" style={{ maxWidth: 620, margin: '0 auto' }}>
            {courant.quoi}
          </p>
        </div>
      )}

      {!loading && !erreur && lignes.length > 0 && (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #e5e7eb', color: '#6b7280' }}>
              <th style={{ textAlign: 'left',  padding: '7px 8px', fontWeight: 600 }}>{courant.entete}</th>
              {/* D'où vient l'appel. Sans elle, le tableau disait ce qui avait été dépensé sans
                  jamais dire par qui — et c'est « par qui » qu'on veut savoir devant un montant. */}
              {courant.origine && (
                <th style={{ textAlign: 'left', padding: '7px 8px', fontWeight: 600 }}
                    title="L’outil du logiciel qui a déclenché l’appel (découpe d’un référentiel, rédaction d’une activité…).">
                  Origine
                </th>
              )}
              <th style={{ textAlign: 'right', padding: '7px 8px', fontWeight: 600 }}>Appels</th>
              <th style={{ textAlign: 'right', padding: '7px 8px', fontWeight: 600 }}>Tokens envoyés</th>
              <th style={{ textAlign: 'right', padding: '7px 8px', fontWeight: 600 }}>Tokens produits</th>
              {courant.cout && (
                <th style={{ textAlign: 'right', padding: '7px 8px', fontWeight: 600 }}
                    title="Tokens × tarif du modèle (table Fournisseurs & modèles). Estimation, pas une facture.">
                  Coût estimé
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {lignes.map((l, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                <td style={{ padding: '7px 8px', color: '#374151' }}>{l.libelle}</td>
                {/* Un appel dont l'outil n'est pas encore nommé garde sa ligne et le dit en gris :
                    l'effacer ferait disparaître une dépense bien réelle du tableau. */}
                {courant.origine && (
                  <td style={{ padding: '7px 8px', color: l.outil ? '#374151' : '#9ca3af' }}
                      title={l.outil || 'Cet appel ne transmet pas son outil : sa dépense est comptée, son origine est inconnue.'}>
                    {l.origine}
                    {l.appels_cache > 0 && (
                      <span style={{ color: '#6b7280', fontSize: 11 }}
                            title="Appels rejoués depuis le cache disque : rien n’a été envoyé, rien n’a été payé.">
                        {' '}· {nb(l.appels_cache)} en cache
                      </span>
                    )}
                  </td>
                )}
                <td style={{ padding: '7px 8px', textAlign: 'right', color: '#6b7280' }}>{nb(l.appels)}</td>
                <td style={{ padding: '7px 8px', textAlign: 'right', color: '#6b7280' }}>{nb(l.tokens_entree)}</td>
                <td style={{ padding: '7px 8px', textAlign: 'right', color: '#6b7280' }}>{nb(l.tokens_sortie)}</td>
                {courant.cout && (
                  <td style={{ padding: '7px 8px', textAlign: 'right', color: l.cout_usd == null ? '#9ca3af' : '#374151' }}
                      title={l.cout_usd == null ? 'Tarif non renseigné pour ce modèle' : undefined}>
                    {usd(l.cout_usd)}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

function Carte({ titre, valeur, note }) {
  return (
    <div style={{
      border: '1px solid #e5e7eb', borderRadius: 10, padding: '10px 16px',
      background: '#fff', minWidth: 130,
    }}>
      <p className="text-xs text-gray-400" style={{ marginBottom: 3 }}>{titre}</p>
      <p className="text-sm font-semibold text-gray-700">{valeur}</p>
      {note && <p className="text-xs text-gray-400" style={{ marginTop: 2, fontSize: 10 }}>{note}</p>}
    </div>
  )
}
