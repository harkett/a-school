import { Fragment, useEffect, useState } from 'react'
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
    // `cout` : le total de la ligne. Il était caché sur ces deux onglets alors que la donnée
    // arrivait déjà du serveur — l'admin voyait des tokens et devait deviner le montant.
    // `detail` : la ligne se déplie sur les appels qui la composent.
    entete: 'Tâche', cout: true, detail: 'outil' },
  { cle: 'jour',    label: 'Par jour',    champ: 'par_jour',
    quoi: 'L’évolution dans le temps, pour repérer une dérive avant la facture.',
    entete: 'Jour', cout: true, detail: 'jour' },
]

const nb = n => (n ?? 0).toLocaleString('fr-FR')

// La ligne « Non précisé » de l'onglet « Par tâche » regroupe les appels dont l'outil est vide :
// son détail se demande par ce mot réservé, que le serveur traduit en « outil IS NULL ». Sans lui,
// le bouton envoyait la chaîne « null » et le tableau répondait « aucun appel » — faux.
const SANS_OUTIL = '__sans_outil__'
const cleDetail = l => (l.cle == null || l.cle === '' ? SANS_OUTIL : String(l.cle))

// Un coût par appel se compte en centimes : 2 décimales afficheraient « 0,00 $ » sur une découpe
// à 30 centimes de dollar. On descend à 4 décimales tant que le total reste sous le dollar.
const usd = v => v == null ? '—' : `${v < 1 ? v.toFixed(4) : v.toFixed(2)} $`

export default function AdminIAStatistiques() {
  const [onglet, setOnglet]   = useState('modele')
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [erreur, setErreur]   = useState('')
  // LE DÉTAIL D'UNE LIGNE (une journée, ou une tâche). Une seule ouverte à la fois : deux lignes
  // dépliées côte à côte se lisent moins bien qu'une seule, et le tableau du dessus reste la vue
  // d'ensemble. `null` = rien d'ouvert. Changer d'onglet referme — la clé n'y voudrait plus rien.
  const [ligneOuverte, setLigneOuverte] = useState(null)
  const [detail, setDetail] = useState(null)   // { cle, lignes } | { cle, erreur }
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

  // Le détail vient du JOURNAL, la même table que les cumuls : l'écran n'invente aucune source,
  // il ouvre celle qui existe — sur une date (`jour`) ou sur une tâche (`outil`). Recliquer sur
  // la même ligne referme.
  function ouvrirDetail(cle) {
    if (ligneOuverte === cle) { setLigneOuverte(null); setDetail(null); return }
    setLigneOuverte(cle)
    setDetail(null)
    const url = `/api/admin/ia/journal?${courant.detail}=${encodeURIComponent(cle)}&limite=500`
    fetch(url, { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        if (!r.ok) throw new Error('lecture impossible')
        return r.json()
      })
      .then(d => { if (d) setDetail({ cle, lignes: d.lignes || [] }) })
      .catch(() => setDetail({ cle, erreur: 'Impossible de lire le détail de cette ligne.' }))
  }

  // Changer d'onglet ferme ce qui était ouvert : la clé d'une journée n'a aucun sens dans la
  // liste des tâches, et laisser le dépliage ouvert afficherait le détail d'une autre ligne.
  function changerOnglet(cle) {
    setOnglet(cle)
    setLigneOuverte(null)
    setDetail(null)
  }

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
          {/* CE QUE LA LISTE DE FOURNISSEURS A SAUVÉ.
              Une réponse obtenue chez le deuxième ou le troisième est une génération que la
              version précédente aurait perdue : le premier avait refusé, et il n'y avait personne
              derrière lui — le professeur voyait un échec et devait recliquer.

              La carte n'apparaît QUE s'il y en a. À zéro, elle ne dirait rien d'utile et prendrait
              la place d'un chiffre qui en dit : tout s'est bien passé du premier coup. */}
          {data.appels_rattrapes > 0 && (
            <Carte titre="Générations sauvées"
                   valeur={nb(data.appels_rattrapes)}
                   note="obtenues chez un autre fournisseur après un refus" />
          )}
        </div>
      )}

      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #e5e7eb' }}>
        {ONGLETS.map(o => {
          const actif = onglet === o.cle
          return (
            <button
              key={o.cle}
              onClick={() => changerOnglet(o.cle)}
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
                    title="Tokens × tarif du modèle (écran Fournisseurs). Estimation, pas une facture.">
                  Coût estimé
                </th>
              )}
              {courant.detail && <th style={{ width: 1 }} />}
            </tr>
          </thead>
          <tbody>
            {lignes.map((l, i) => (
              <Fragment key={i}>
              <tr style={{ borderBottom: '1px solid #f3f4f6' }}>
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
                      title={l.cout_usd == null
                        ? 'Tarif non renseigné pour ce modèle'
                        : (l.cout_partiel ? 'Total partiel : un des modèles de cette ligne n’a pas de tarif renseigné' : undefined)}>
                    {usd(l.cout_usd)}
                  </td>
                )}
                {/* LE DÉTAIL DE LA LIGNE. Le tableau du dessus dit COMBIEN ; celui-ci dit QUOI —
                    l'heure de chaque appel, son modèle, son origine, ce qu'il a coûté. */}
                {courant.detail && (
                  <td style={{ padding: '7px 8px', textAlign: 'right' }}>
                    <button
                      type="button"
                      onClick={() => ouvrirDetail(cleDetail(l))}
                      title={ligneOuverte === cleDetail(l)
                        ? 'Replier ce détail'
                        : (courant.cle === 'jour'
                            ? 'Voir les appels de cette journée, un par ligne'
                            : 'Voir les appels de cette tâche, un par ligne')}
                      style={{
                        display: 'inline-flex', alignItems: 'center', gap: 5, whiteSpace: 'nowrap',
                        background: 'none', border: '1px solid #d1d5db', borderRadius: 6,
                        padding: '3px 9px', fontSize: 11, fontWeight: 600, color: '#374151',
                        cursor: 'pointer',
                      }}
                    >
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                           strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                           style={{ transform: ligneOuverte === cleDetail(l) ? 'rotate(180deg)' : 'none', transition: 'transform .15s' }}>
                        <polyline points="6 9 12 15 18 9" />
                      </svg>
                      Détail
                    </button>
                  </td>
                )}
              </tr>
              {courant.detail && ligneOuverte === cleDetail(l) && (
                <tr>
                  <td colSpan={6} style={{ padding: 0, background: '#fafafa', borderBottom: '1px solid #f3f4f6' }}>
                    <DetailAppels etat={detail} cle={cleDetail(l)} />
                  </td>
                </tr>
              )}
              </Fragment>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

// Le détail d'UNE ligne — une journée ou une tâche : un appel par ligne, dans l'ordre du journal
// (le plus récent en haut). Les colonnes sont celles qui servent devant une facture ou un
// incident — l'heure, le modèle, qui a déclenché, ce qui est parti, ce qui est revenu, le prix,
// et comment ça s'est terminé. Un refus ou un rejeu du cache n'a pas de prix : la case reste
// vide, jamais à zéro.
function DetailAppels({ etat, cle }) {
  if (!etat || etat.cle !== cle) {
    return <p className="text-xs text-gray-400" style={{ padding: '12px 16px' }}>Chargement du détail…</p>
  }
  if (etat.erreur) {
    return <p className="text-xs" style={{ color: '#ef4444', padding: '12px 16px' }}>{etat.erreur}</p>
  }
  if (!etat.lignes.length) {
    return <p className="text-xs text-gray-400" style={{ padding: '12px 16px' }}>Aucun appel ici.</p>
  }
  const heure = q => (q ? new Date(q).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—')
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
      <thead>
        <tr style={{ color: '#6b7280', borderBottom: '1px solid #e5e7eb' }}>
          <th style={{ textAlign: 'left',  padding: '6px 8px', fontWeight: 600 }}>Heure</th>
          <th style={{ textAlign: 'left',  padding: '6px 8px', fontWeight: 600 }}>Modèle</th>
          <th style={{ textAlign: 'left',  padding: '6px 8px', fontWeight: 600 }}>Origine</th>
          <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 600 }}>Envoyés</th>
          <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 600 }}>Produits</th>
          <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 600 }}>Durée</th>
          <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 600 }}>Coût estimé</th>
          <th style={{ textAlign: 'left',  padding: '6px 8px', fontWeight: 600 }}>Résultat</th>
        </tr>
      </thead>
      <tbody>
        {etat.lignes.map(u => (
          <tr key={u.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
            <td style={{ padding: '6px 8px', color: '#374151' }}>{heure(u.quand)}</td>
            <td style={{ padding: '6px 8px', color: '#374151' }}>{u.modele || '—'}</td>
            <td style={{ padding: '6px 8px', color: u.outil ? '#374151' : '#9ca3af' }}>{u.origine}</td>
            <td style={{ padding: '6px 8px', textAlign: 'right', color: '#6b7280' }}>{nb(u.tokens_entree)}</td>
            <td style={{ padding: '6px 8px', textAlign: 'right', color: '#6b7280' }}>{nb(u.tokens_sortie)}</td>
            <td style={{ padding: '6px 8px', textAlign: 'right', color: '#6b7280' }}>
              {u.duree_ms == null ? '—' : `${(u.duree_ms / 1000).toFixed(1)} s`}
            </td>
            <td style={{ padding: '6px 8px', textAlign: 'right', color: u.cout_usd == null ? '#9ca3af' : '#374151' }}
                title={u.depuis_cache ? 'Rejeu du cache : rien ne part chez le fournisseur, rien n\u2019est payé.' : undefined}>
              {u.cout_usd == null ? '—' : usd(u.cout_usd)}
            </td>
            <td style={{ padding: '6px 8px', color: u.resultat === 'ok' ? '#6b7280' : '#b91c1c' }}
                title={u.code_http ? `Réponse du fournisseur : ${u.code_http}` : undefined}>
              {u.depuis_cache ? 'cache' : (u.resultat || '—')}
              {u.motif_arret === 'max_tokens' && ' · coupée'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
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
