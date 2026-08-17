import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FenetrePro from '../components/FenetrePro.jsx'

// IA › Journal — un appel par ligne, le plus récent en haut.
//
// POURQUOI CET ÉCRAN. « Statistiques » additionne (par modèle, par tâche, par jour) et répond
// « qu'a coûté la semaine ? ». Il ne répond pas « que s'est-il passé sur CET appel ? » — la
// question qu'on pose devant une génération qui s'arrête au milieu. La réponse est dans la même
// table `usage_llm`, ligne par ligne ; jusqu'ici elle n'était lisible que dans `docker logs`,
// c'est-à-dire hors de l'application.
//
// LE PROMPT ET LA RÉPONSE N'Y SONT PAS, et n'y seront pas : la table compte, elle ne relit pas.
// Un journal qui garderait le texte des profs serait un second entrepôt de données personnelles.

const nb = n => (n ?? 0).toLocaleString('fr-FR')
const usd = v => v == null ? '—' : `${v < 1 ? v.toFixed(4) : v.toFixed(2)} $`

const quand = iso => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

const duree = ms => ms == null ? '—' : ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`

// Le motif d'arrêt vient du fournisseur, dans SON vocabulaire (« end_turn », « length »,
// « max_tokens »…). L'admin n'a pas à le connaître : ce qui l'intéresse est de savoir si la
// réponse est complète ou tronquée — et la tronquée se voit en rouge.
const COUPE = ['max_tokens', 'length', 'MAX_TOKENS']

// Ce qu'est devenue la tentative prime sur le motif d'arrêt : un appel REFUSÉ n'a pas de motif,
// puisqu'il n'a rien produit. Sans ce cas, il s'affichait « — », c'est-à-dire comme un appel dont
// on ignore la fin — alors qu'on sait très bien ce qui s'est passé : le fournisseur a dit non.
const REFUS = {
  429: 'Quota atteint chez ce fournisseur.',
  402: 'Plus de crédit sur le compte.',
  401: 'Clé d’accès refusée.',
  403: 'Clé d’accès refusée.',
  400: 'Demande refusée par le fournisseur.',
}

const arret = (m, resultat, code) => {
  if (resultat === 'refus') {
    return {
      texte: 'Refusé', coupe: true,
      brut: (REFUS[code] || 'Le fournisseur a refusé l’appel.')
        + (code ? ` (code ${code})` : ' Aucune réponse reçue — délai dépassé ou connexion perdue.'),
    }
  }
  if (!m) return { texte: '—', coupe: false, brut: 'Le fournisseur n’a pas dit pourquoi il s’est arrêté.' }
  if (COUPE.includes(m)) {
    return {
      texte: 'Réponse coupée', coupe: true,
      brut: `Motif du fournisseur : ${m}. La réponse a atteint la longueur maximale autorisée et s’arrête au milieu.`,
    }
  }
  return { texte: 'Terminée', coupe: false, brut: `Motif du fournisseur : ${m}. Le modèle a fini de lui-même.` }
}

const LIMITE = 100

export default function AdminIAJournal() {
  const [data, setData]     = useState(null)
  const [page, setPage]     = useState(1)
  // '' = tous les fournisseurs. Le filtre part au serveur : filtrer les seules lignes de la page
  // affichée ne montrerait qu'une partie du journal, et les pages suivantes seraient fausses.
  const [fournisseur, setFournisseur] = useState('')
  const [erreur, setErreur] = useState('')
  // La ligne dont on regarde le détail. `null` = aucune fenêtre ouverte.
  const [detail, setDetail] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetch(`/api/admin/ia/journal?page=${page}&limite=${LIMITE}&fournisseur=${encodeURIComponent(fournisseur)}`,
      { credentials: 'include' })
      .then(r => {
        if (r.status === 401) { navigate('/admin/login'); return null }
        if (!r.ok) throw new Error('lecture impossible')
        return r.json()
      })
      .then(d => { if (d) { setData(d); setErreur('') } })
      .catch(() => setErreur('Impossible de lire le journal.'))
  }, [page, fournisseur, navigate])

  const lignes  = data?.lignes || []
  const total   = data?.total || 0
  const dernier = Math.max(1, Math.ceil(total / LIMITE))

  // « En cours » se DÉDUIT : les lignes affichées sont-elles bien celles qu'on demande ? Un état
  // `loading` posé dans l'effet serait un setState synchrone de plus par changement de page —
  // React le refuse désormais (règle `set-state-in-effect`), et il n'apportait rien de plus.
  const loading = !erreur && (data?.page !== page || data?.fournisseur !== fournisseur)

  // Changer de fournisseur remet à la page 1 : rester sur la page 7 d'un filtre qui n'en compte
  // que deux afficherait un tableau vide qu'on croirait cassé.
  const choisir = code => { setFournisseur(code); setPage(1) }

  return (
    <div className="flex flex-col gap-4">

      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-1">Journal</h2>
        <p className="text-xs text-gray-400">
          Chaque appel à l’IA, un par ligne, le plus récent en haut
          {data ? ` — ${nb(total)} appel${total > 1 ? 's' : ''} sur les ${data.jours} derniers jours.` : '.'}
        </p>
      </div>

      {/* La liste des fournisseurs vient du serveur, qui la tire des appels eux-mêmes : rien n'est
          écrit en dur ici, donc un fournisseur raccordé plus tard s'ajoute tout seul. */}
      {data?.fournisseurs?.length > 0 && (
        // `sticky` : la barre reste sous les yeux quand on descend dans le journal. Un total qui
        // disparaît au premier défilement oblige à remonter pour le relire.
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, position: 'sticky', top: 0, zIndex: 5,
          background: '#fff', padding: '6px 0', borderBottom: '1px solid #f3f4f6',
        }}>
          <label htmlFor="filtre-fournisseur" className="text-xs text-gray-500">Fournisseur</label>
          <select
            id="filtre-fournisseur"
            value={fournisseur}
            onChange={e => choisir(e.target.value)}
            title="N’afficher que les appels partis chez ce fournisseur. Le nombre entre parenthèses est le total de ses appels sur la période."
            style={{
              height: 30, padding: '0 8px', fontSize: 12, borderRadius: 7,
              border: '1px solid #e5e7eb', background: '#fff', color: '#374151', cursor: 'pointer',
            }}
          >
            <option value="">Tous ({nb(data.total_tous)})</option>
            {data.fournisseurs.map(f => (
              <option key={f.code} value={f.code}>{f.libelle} ({nb(f.appels)})</option>
            ))}
          </select>

          {/* Le coût de TOUT ce que le filtre retient, pas de la page affichée : un montant qui
              changerait en tournant les pages ne répondrait à aucune question. */}
          <span
            className="text-xs"
            style={{ marginLeft: 'auto', color: '#374151' }}
            title={data.cout_partiel
              ? 'Total des appels retenus par le filtre, toutes pages confondues. Incomplet : certains modèles n’ont pas de tarif renseigné. Estimation, pas une facture.'
              : 'Total des appels retenus par le filtre, toutes pages confondues. Tokens × tarif du modèle — estimation, pas une facture.'}
          >
            Coût total <strong style={{ fontWeight: 600 }}>{usd(data.cout_usd)}</strong>
            {data.cout_partiel && (
              <span style={{ color: '#9ca3af' }}> · hors modèles sans tarif</span>
            )}
          </span>
        </div>
      )}

      {loading && <p className="text-xs text-gray-400" style={{ padding: 20 }}>Chargement…</p>}

      {!loading && erreur && (
        <p className="text-xs" style={{ color: '#ef4444', padding: 20 }}>{erreur}</p>
      )}

      {/* Journal vide = installation qui n'a pas appelé l'IA sur la période. Ce n'est pas une
          panne, et un tableau vide se lirait comme telle. */}
      {!loading && !erreur && lignes.length === 0 && (
        <div style={{
          border: '1px dashed #d1d5db', borderRadius: 10, padding: '28px 20px',
          textAlign: 'center', background: '#fafafa',
        }}>
          <p className="text-sm font-semibold text-gray-600 mb-2">
            {fournisseur ? 'Aucun appel chez ce fournisseur sur la période' : 'Aucun appel sur la période'}
          </p>
          <p className="text-xs text-gray-500" style={{ maxWidth: 620, margin: '0 auto' }}>
            {fournisseur
              ? 'Choisissez « Tous » pour revoir l’ensemble des appels.'
              : 'Le journal se remplit tout seul, à chaque fois qu’une fonction du logiciel interroge l’IA.'}
          </p>
        </div>
      )}

      {!loading && !erreur && lignes.length > 0 && (
        <>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e5e7eb', color: '#6b7280' }}>
                  <th style={TH}  title="Date et heure de l’appel.">Quand</th>
                  <th style={TH}  title="L’outil du logiciel qui a déclenché l’appel (découpe d’un référentiel, rédaction d’une activité…).">Origine</th>
                  <th style={TH}  title="Le modèle qui a répondu. Survolez pour voir chez quel fournisseur il tourne.">Modèle</th>
                  <th style={TH}  title="Pourquoi le modèle s’est arrêté : il a fini de lui-même, ou il a été coupé à la longueur maximale.">Arrêt</th>
                  <th style={THD} title="Tout ce qui est parti chez le fournisseur, y compris ce qui a été relu dans son cache.">Envoyés</th>
                  <th style={THD} title="Ce que le modèle a écrit en réponse.">Produits</th>
                  <th style={THD} title="Temps qu’a pris l’appel, de l’envoi à la dernière ligne reçue.">Durée</th>
                  <th style={THD} title="Tokens × tarif du modèle (écran Fournisseurs). Estimation, pas une facture.">Coût</th>
                  {/* LE DÉTAIL DE L'APPEL. La base garde plus que ce que huit colonnes peuvent
                      montrer — le fournisseur qui a répondu, son rang dans la cascade, le code
                      qu'il a rendu, le cache. Élargir le tableau le rendrait illisible ; un « i »
                      par ligne le donne à la demande. */}
                  <th style={{ ...TH, width: 30 }} />
                </tr>
              </thead>
              <tbody>
                {lignes.map(l => {
                  const a = arret(l.motif_arret, l.resultat, l.code_http)
                  return (
                    <tr key={l.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                      <td style={{ ...TD, whiteSpace: 'nowrap' }}>{quand(l.quand)}</td>
                      <td style={{ ...TD, color: l.outil ? '#374151' : '#9ca3af' }}
                          title={l.outil || 'Cet appel ne transmet pas son outil : sa dépense est comptée, son origine est inconnue.'}>
                        {l.origine}
                        {/* Rejeu du cache disque : l'appel a bien eu lieu côté logiciel, mais rien
                            n'est parti chez le fournisseur. Le dire évite de chercher pourquoi
                            cette ligne ne coûte rien. */}
                        {l.depuis_cache && (
                          <span style={{ color: '#6b7280', fontSize: 11 }}
                                title="Réponse rejouée depuis le cache : rien n’a été envoyé, rien n’a été payé.">
                            {' '}· en cache
                          </span>
                        )}
                      </td>
                      <td style={TD} title={`Fournisseur : ${l.fournisseur}`}>{l.modele}</td>
                      <td style={{ ...TD, color: a.coupe ? '#ef4444' : '#6b7280' }} title={a.brut}>{a.texte}</td>
                      <td style={TDD} title={l.tokens_cache_lecture
                        ? `dont ${nb(l.tokens_cache_lecture)} relus dans le cache du fournisseur (payés 10 %)` : undefined}>
                        {nb(l.tokens_entree)}
                      </td>
                      <td style={TDD}>{nb(l.tokens_sortie)}</td>
                      <td style={TDD}>{duree(l.duree_ms)}</td>
                      <td style={{ ...TDD, color: l.cout_usd == null ? '#9ca3af' : '#374151' }}
                          title={l.resultat === 'refus' ? 'Appel refusé : rien n’a été produit, rien n’a été facturé.'
                            : l.depuis_cache ? 'Rejeu du cache : rien n’a été facturé.'
                            : l.cout_usd == null ? 'Tarif non renseigné pour ce modèle' : undefined}>
                        {usd(l.cout_usd)}
                      </td>
                      <td style={{ ...TD, padding: '4px 6px', textAlign: 'right' }}>
                        <button
                          type="button"
                          onClick={() => setDetail(l)}
                          title="Tout ce que la base garde de cet appel"
                          style={{
                            width: 17, height: 17, borderRadius: '50%', cursor: 'pointer', padding: 0,
                            border: '1px solid ' + (detail?.id === l.id ? '#A63045' : '#cbd5e1'),
                            color: detail?.id === l.id ? '#fff' : '#64748b',
                            background: detail?.id === l.id ? '#A63045' : '#f8fafc',
                            fontSize: 11, fontWeight: 700, fontStyle: 'italic', lineHeight: '15px',
                            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                          }}
                        >i</button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination : un journal grandit sans fin, et une page qui charge tout finit par ne
              plus s'ouvrir du tout. */}
          {dernier > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Fleche sens="prev" desactive={page <= 1} onClick={() => setPage(p => p - 1)} />
              <span className="text-xs text-gray-500">Page {page} sur {dernier}</span>
              <Fleche sens="next" desactive={page >= dernier} onClick={() => setPage(p => p + 1)} />
            </div>
          )}
        </>
      )}

      {detail && <DetailAppel ligne={detail} onFermer={() => setDetail(null)} />}
    </div>
  )
}


// LE DÉTAIL D'UN APPEL — tout ce que `usage_llm` garde de cette ligne, et rien de plus.
//
// POURQUOI UNE FENÊTRE ET PAS DES COLONNES. Huit colonnes tiennent à l'écran, quinze non : le
// tableau deviendrait illisible pour montrer, à chaque ligne, des champs qu'on ne regarde qu'une
// fois sur cinquante. La fenêtre est celle de la maison (`FenetrePro`) : déplaçable, sans voile
// qui bloque la page derrière — on peut comparer deux appels en la traînant à côté.
//
// LE TEXTE ENVOYÉ ET LA RÉPONSE N'Y SONT PAS, et n'y seront pas : la table compte les appels,
// elle ne conserve pas leur contenu. La fenêtre le dit, sinon on la croit incomplète.
function DetailAppel({ ligne, onFermer }) {
  const a = arret(ligne.motif_arret, ligne.resultat, ligne.code_http)
  const cache = (ligne.tokens_cache_ecriture || 0) + (ligne.tokens_cache_lecture || 0)

  const lignes = [
    ['Quand',        quand(ligne.quand)],
    ['Origine',      ligne.origine + (ligne.outil ? ` (${ligne.outil})` : '')],
    ['Fournisseur',  ligne.fournisseur],
    ['Modèle',       ligne.modele],
    // LE RANG DIT LA CASCADE : « 2ᵉ appelé » veut dire que le premier — le gratuit — a refusé.
    // C'est l'information qui explique pourquoi un appel censé être gratuit a coûté quelque chose.
    ['Rang d’appel', ligne.rang ? `${ligne.rang}${ligne.rang === 1 ? 'er' : 'e'} fournisseur essayé` : '—'],
    ['Résultat',     ligne.resultat === 'refus' ? 'Refusé par le fournisseur'
                     : ligne.resultat === 'coupe' ? 'Réponse coupée' : 'Abouti'],
    ['Code rendu',   ligne.code_http ? String(ligne.code_http) : '—'],
    ['Arrêt',        a.texte],
    ['Jetons envoyés', nb(ligne.tokens_entree)],
    ['dont cache',   cache ? `${nb(ligne.tokens_cache_lecture || 0)} relus · ${nb(ligne.tokens_cache_ecriture || 0)} écrits` : '—'],
    ['Jetons produits', nb(ligne.tokens_sortie)],
    ['Durée',        duree(ligne.duree_ms)],
    ['Coût',         ligne.depuis_cache ? 'Rejeu du cache — rien n’a été envoyé'
                     : ligne.resultat === 'refus' ? 'Aucun — rien n’a été produit'
                     : usd(ligne.cout_usd)],
  ]

  return (
    <FenetrePro titre="Détail de l’appel" onFermer={onFermer} largeur={430} hauteur="min(70vh, 520px)">
      <div style={{ overflowY: 'auto', padding: '12px 16px 16px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
          <tbody>
            {lignes.map(([cle, valeur]) => (
              <tr key={cle} style={{ borderBottom: '1px solid #f3f4f6' }}>
                <td style={{ padding: '7px 0', color: '#94a3b8', whiteSpace: 'nowrap', width: 132 }}>{cle}</td>
                <td style={{ padding: '7px 0', color: '#1e293b', fontWeight: 500 }}>{valeur}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <p style={{ margin: '12px 0 0', fontSize: 11.5, lineHeight: 1.5, color: '#64748b' }}>
          {a.brut}
        </p>
        <p style={{ margin: '10px 0 0', fontSize: 11, lineHeight: 1.5, color: '#94a3b8' }}>
          Le texte envoyé et la réponse reçue ne sont pas conservés : le journal compte les appels,
          il ne relit pas leur contenu.
        </p>
      </div>
    </FenetrePro>
  )
}

const TH  = { textAlign: 'left',  padding: '7px 8px', fontWeight: 600 }
const THD = { textAlign: 'right', padding: '7px 8px', fontWeight: 600 }
const TD  = { padding: '7px 8px', color: '#374151' }
const TDD = { padding: '7px 8px', textAlign: 'right', color: '#6b7280' }

function Fleche({ sens, desactive, onClick }) {
  const precedent = sens === 'prev'
  return (
    <button
      onClick={onClick}
      disabled={desactive}
      title={precedent ? 'Voir les appels plus récents' : 'Voir les appels plus anciens'}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 5, height: 30, padding: '0 12px',
        fontSize: 12, borderRadius: 7, border: '1px solid #e5e7eb', background: '#fff',
        color: desactive ? '#d1d5db' : '#374151',
        cursor: desactive ? 'not-allowed' : 'pointer',
      }}
    >
      {precedent && <Chevron gauche />}
      {precedent ? 'Précédent' : 'Suivant'}
      {!precedent && <Chevron />}
    </button>
  )
}

function Chevron({ gauche }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points={gauche ? '15 18 9 12 15 6' : '9 18 15 12 9 6'} />
    </svg>
  )
}
