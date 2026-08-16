// Page « Base de données → Démos » — le PILOTAGE des bases de démonstration, jamais leur contenu.
//
// Une démonstration vit dans une base PostgreSQL À PART (ciela_demo, cielb_demo…) : un référentiel
// déjà fabriqué, un compte de démonstration, du contenu d'exemple. Cet écran ne l'ouvre JAMAIS —
// il tient sa FICHE, dans la base réelle. D'où deux conséquences visibles ici :
//   · les compteurs se SAISISSENT et ne se calculent pas (les recompter voudrait dire se
//     connecter à l'autre base, ce que le serveur ne fait pas) ;
//   · « Retirer » retire la fiche de la liste, pas la base — elle survit et se détruit à la main.
import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchWithTimeout, TIMEOUT_STD, TIMEOUT_XLONG } from '../utils/api.js'
import GuideDemos from '../components/GuideDemos.jsx'
import { useActionsEcran } from '../components/actionsEcran.jsx'
import Attente from '../components/Attente.jsx'
import { showError } from '../errorDialog.js'
import { demanderConfirmation } from '../confirmDialog.js'

// LE STATUT A DISPARU (16/08/2026). Cinq mots — À faire, En cours, Fabriquée, Testée, Validée —
// dont deux seulement agissaient, et au même endroit : ouvrir l'entrée « Démonstration » du menu
// prof. Une démonstration pas prête n'a pas d'adresse, et cette absence la tenait déjà fermée. La
// règle tient en une phrase : une démonstration est visitable dès qu'elle a une adresse. La
// colonne « Adresse » de ce tableau la dit déjà, en toutes lettres.

// Norme maison : même hauteur pour tous, curseur interdit quand c'est grisé, une couleur par geste
// (valider bleu, annuler rouge, ajouter vert), et une bulle d'aide sur chacun — posée à l'appel.
const btn = (fond, bord, texte) => (off) => ({
  display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
  height: 32, padding: '0 12px', borderRadius: 6, fontSize: 12.5, fontWeight: 600,
  border: '1px solid ' + (off ? '#e5e7eb' : bord),
  background: off ? '#f8fafc' : fond,
  color: off ? '#94a3b8' : texte,
  cursor: off ? 'not-allowed' : 'pointer',
})
const btnValider = btn('#2563eb', '#1d4ed8', '#fff')
const btnAnnuler = btn('#fff', '#fecaca', '#b91c1c')
const btnAjouter = btn('#16a34a', '#15803d', '#fff')
const btnNeutre  = btn('#fff', '#cbd5e1', '#334155')
const btnVisiter = btn('#7c3aed', '#6d28d9', '#fff')

const IconVisiter = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
    <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
  </svg>
)

const IconAide = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
  </svg>
)

const champ = {
  height: 32, padding: '0 8px', borderRadius: 6, border: '1px solid #cbd5e1',
  fontSize: 12.5, color: '#0f172a', background: '#fff', width: '100%', boxSizing: 'border-box',
}

const VIDE = {
  referentiel_id: '', nom_base: '', url: '',
  nb_activites: 0, nb_sequences: 0, nb_seances: 0,
  date_generation: '', defauts_connus: '', notes: '',
}

// « 2026-08-07T10:17:00 » → « 07/08/2026 ». Une date absente s'écrit « — », jamais « Invalid Date ».
function jour(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString('fr-FR')
}

// L'inverse, pour <input type="date"> qui n'accepte que « 2026-08-07 ».
function pourInput(iso) {
  return iso ? String(iso).slice(0, 10) : ''
}

const CLE_DEMOS = ['admin', 'demos']

export default function AdminBaseDemos() {
  const queryClient = useQueryClient()
  const [busy, setBusy]       = useState(false)
  const [edition, setEdition] = useState(null)   // { id: number | 'nouveau', ...champs }
  // Erreur d'ÉCRITURE seulement (enregistrer / retirer) : celle de la lecture vient de useQuery.
  const [erreurEcriture, setErreurEcriture] = useState('')
  // « Comment ça marche » : replié par défaut, il n'encombre que celui qui l'ouvre.
  const [guide, setGuide] = useState(false)

  // La lecture passe par react-query, comme les autres écrans de l'admin (AdminAlertes,
  // AdminContenu…). Elle y a gagné une correction et pas seulement une mise au motif : le
  // chargement se faisait dans un `useEffect` qui modifiait l'état de l'écran avant même le
  // premier appel, ce que React signale comme un affichage refait pour rien
  // (`set-state-in-effect`). Ici, plus d'effet du tout — et le rechargement après une écriture
  // devient une invalidation de la clé, pas un second appel écrit à la main.
  const { data, error } = useQuery({
    queryKey: CLE_DEMOS,
    queryFn: async () => {
      const r = await fetchWithTimeout('/api/admin/demos', { credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) throw new Error('Impossible de lire la liste des démonstrations.')
      return r.json()
    },
  })
  const erreur = erreurEcriture || (error ? error.message : '')
  const recharger = () => queryClient.invalidateQueries({ queryKey: CLE_DEMOS })

  async function enregistrer() {
    setBusy(true); setErreurEcriture('')
    const nouveau = edition.id === 'nouveau'
    const corps = {
      referentiel_id: Number(edition.referentiel_id),
      nom_base: edition.nom_base,
      url: edition.url.trim() || null,
      nb_activites: Number(edition.nb_activites) || 0,
      nb_sequences: Number(edition.nb_sequences) || 0,
      nb_seances: Number(edition.nb_seances) || 0,
      // <input type="date"> rend « 2026-08-07 » ; le serveur attend un instant. Midi évite qu'un
      // décalage de fuseau ne recule la date d'un jour à l'affichage.
      date_generation: edition.date_generation ? edition.date_generation + 'T12:00:00' : null,
      defauts_connus: edition.defauts_connus || null,
      notes: edition.notes || null,
    }
    try {
      const r = await fetchWithTimeout(
        nouveau ? '/api/admin/demos' : '/api/admin/demos/' + edition.id,
        {
          method: nouveau ? 'POST' : 'PUT',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(corps),
        }, TIMEOUT_STD)
      if (!r.ok) {
        const d = await r.json().catch(() => ({}))
        throw new Error(d.detail || "L'enregistrement a échoué.")
      }
      setEdition(null)
      await recharger()
    } catch (e) {
      setErreurEcriture(e.message || "L'enregistrement a échoué.")
    } finally {
      setBusy(false)
    }
  }

  async function retirer(d) {
    const ok = window.confirm(
      'Retirer « ' + d.nom_base + ' » de cette liste ?\n\n'
      + "La base PostgreSQL, elle, n'est pas touchée : elle continue d'exister sur le serveur."
    )
    if (!ok) return
    setBusy(true); setErreurEcriture('')
    try {
      const r = await fetchWithTimeout('/api/admin/demos/' + d.id,
        { method: 'DELETE', credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) throw new Error()
      await recharger()
    } catch {
      setErreurEcriture('Le retrait a échoué.')
    } finally {
      setBusy(false)
    }
  }

  function ouvrirModification(d) {
    setEdition({
      id: d.id,
      referentiel_id: d.referentiel_id,
      nom_base: d.nom_base,
      url: d.url || '',
      nb_activites: d.nb_activites,
      nb_sequences: d.nb_sequences,
      nb_seances: d.nb_seances,
      date_generation: pourInput(d.date_generation),
      defauts_connus: d.defauts_connus || '',
      notes: d.notes || '',
    })
  }

  const libres = (data && data.referentiels_libres) || []

  // LES TROIS BOUTONS VIVENT DANS LA BARRE FIXE DU HAUT, en face du titre de l'écran. Ils
  // occupaient le coin droit de la carte, où ils débordaient dès que la fenêtre rétrécissait —
  // et ils y répétaient une place que l'administration réserve déjà aux actions d'un écran.
  useActionsEcran(
    <>
      <button
        type="button"
        style={btnNeutre(false)}
        onClick={() => setGuide(true)}
        title="Ce qu’est une démonstration, ce que cet écran pilote, et ce que le prof en voit"
      >
        <IconAide />Comment ça marche
      </button>
      {/* IMPORTER UNE FICHE VENUE D'AILLEURS. Une démonstration se déclare sur le poste où on la
          fabrique ; un déploiement ne porte pas les fiches saisies. Sans ce bouton, il fallait
          retaper la fiche en production — et le 16/08/2026 personne ne l'avait fait : la
          démonstration du Collège tournait sans qu'aucun professeur la voie. */}
      <ImporterDemo onImporte={recharger} />
      <button
        type="button"
        style={btnAjouter(busy || !!edition || libres.length === 0)}
        disabled={busy || !!edition || libres.length === 0}
        onClick={() => setEdition({ id: 'nouveau', ...VIDE })}
        title={libres.length === 0
          ? 'Tous les référentiels ont déjà leur démonstration'
          : 'Déclarer une démonstration pour un référentiel qui n’en a pas encore'}
      >
        + Déclarer
      </button>
    </>,
    [busy, edition, libres.length]
  )

  return (
    <div className="flex flex-col gap-6">
      {guide && <GuideDemos onFermer={() => setGuide(false)} />}
      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
        <div>
          <div>
            <h2 className="text-base font-semibold text-gray-800">Bases de démonstration</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Une base par niveau, livrée avec le produit : l’enseignant qui découvre y explore
              sans toucher au réel. Cet écran tient leur fiche — les données, elles, vivent dans
              leur propre base.
            </p>
            <p className="text-xs text-gray-400 mt-1">
              <b>On n’entre jamais dans une démonstration par un compte de démonstration.</b> D’ici,
              « Visiter » vous y emmène avec votre identité d’administrateur ; l’enseignant, lui, y
              entre depuis son propre écran. Aucun identifiant ne circule.
            </p>
          </div>
        </div>


        {erreur && (
          <div style={{ fontSize: 12.5, color: '#b91c1c', background: '#fef2f2',
                        border: '1px solid #fecaca', borderRadius: 6, padding: '8px 10px' }}>
            {erreur}
          </div>
        )}

        {!data && !erreur && <div className="text-gray-400 text-sm">Lecture…</div>}

        {data && data.demos.length === 0 && (!edition || edition.id !== 'nouveau') && (
          <p style={{ fontSize: 13, color: '#64748b', margin: 0 }}>
            Aucune démonstration déclarée pour l’instant.
          </p>
        )}

        {data && (data.demos.length > 0 || (edition && edition.id === 'nouveau')) && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
              <thead>
                <tr style={{ textAlign: 'left', color: '#64748b', borderBottom: '1px solid #e5e7eb' }}>
                  <th style={{ padding: '6px 8px', fontWeight: 700, color: '#334155', whiteSpace: 'nowrap', minWidth: 190 }}>Niveau</th>
                  <th style={{ padding: '6px 8px', fontWeight: 700, color: '#334155' }}>Base</th>
                  <th style={{ padding: '6px 8px', fontWeight: 700, color: '#334155' }}
                      title="L'instance branchée sur cette base — sans elle, le prof ne peut pas s'y rendre">
                    Adresse
                  </th>
                  {/* LES COMPTEURS ONT QUITTÉ LA VUE D'ENSEMBLE (16/08/2026). Trois nombres
                      saisis à la main, qu'on ne compare à rien : ils allongeaient la ligne sans
                      jamais aider à choisir. La donnée reste, elle se lit dans « Modifier ».
                      LA COLONNE « TESTÉE » A DISPARU AVEC SA DONNÉE, le même jour : une date de
                      relecture que personne n'a jamais remplie, dernier vestige du suivi de
                      chantier parti avec les cinq statuts. */}
                  <th style={{ padding: '6px 8px', fontWeight: 700, color: '#334155' }}>Fabriquée</th>
                  <th style={{ padding: '6px 8px', fontWeight: 700, color: '#334155' }} />
                </tr>
              </thead>
              <tbody>
                {data.demos.map(d => (
                  edition && edition.id === d.id
                    ? <LigneEdition key={d.id} edition={edition} setEdition={setEdition}
                                    libres={libres} demo={d}
                                    busy={busy} onValider={enregistrer}
                                    onAnnuler={() => setEdition(null)} />
                    : <LigneLecture key={d.id} d={d} busy={busy} bloque={!!edition}
                                    onModifier={() => ouvrirModification(d)}
                                    onRetirer={() => retirer(d)} />
                ))}
                {edition && edition.id === 'nouveau' && (
                  <LigneEdition edition={edition} setEdition={setEdition}
                                libres={libres} demo={null}
                                busy={busy} onValider={enregistrer}
                                onAnnuler={() => setEdition(null)} />
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function LigneLecture({ d, busy, bloque, onModifier, onRetirer }) {
  return (
    <>
      <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
        {/* Sur une seule ligne, et large : « BTS · BTS CIEL Option A » se cassait en trois, et
            chaque ligne du tableau prenait trois fois sa hauteur pour rien. */}
        <td style={{ padding: '8px', color: '#0f172a', fontWeight: 600, whiteSpace: 'nowrap' }}>
          {[d.cycle, d.niveau].filter(Boolean).join(' · ')}
        </td>
        <td style={{ padding: '8px', fontFamily: 'ui-monospace, monospace', color: '#334155' }}>
          {d.nom_base}
        </td>
        <td style={{ padding: '8px' }}>
          {d.url
            ? <a href={d.url} target="_blank" rel="noreferrer" style={{ color: '#2563eb' }}
                 title="Ouvrir cette démonstration dans un nouvel onglet">{d.url}</a>
            : <span style={{ color: '#b45309' }}
                    title="Tant qu'aucune adresse n'est renseignée, l'entrée « Démonstration » du menu prof reste grisée">
                instance non montée
              </span>}
        </td>
        <td style={{ padding: '8px', color: '#64748b' }}>{jour(d.date_generation)}</td>
        <td style={{ padding: '8px', textAlign: 'right', whiteSpace: 'nowrap' }}>
          {/* VISITER — un vrai lien, pas un appel en JavaScript : la route répond par une
              redirection vers l'autre instance, et c'est le navigateur qui doit la suivre en
              emportant le cookie d'administration. Un fetch() suivrait la redirection lui-même
              et n'ouvrirait rien. Grisé tant qu'aucune adresse n'est renseignée. */}
          <a href={d.url ? `/api/admin/demos/${d.id}/aller` : undefined}
             target="_blank" rel="noreferrer"
             style={{ ...btnVisiter(!d.url), textDecoration: 'none' }}
             title={d.url
               ? "Ouvrir cette démonstration avec votre identité d'administrateur — quel que soit votre couple, et même si elle n'est pas encore déclarée testée"
               : "Renseignez d'abord l'adresse de l'instance"}>
            <IconVisiter /> Visiter
          </a>
          {' '}
          {/* EXPORTER — un vrai lien lui aussi : le serveur répond par un fichier à télécharger,
              c'est au navigateur de le recevoir. Un fetch() le garderait en mémoire sans jamais
              l'écrire sur le disque. */}
          <a href={`/api/admin/demos/${d.id}/exporter`}
             style={{ ...btnNeutre(false), textDecoration: 'none' }}
             title="Emporter cette fiche vers une autre installation — l'adresse ne part pas avec, elle décrit cette machine">
            Exporter
          </a>
          {' '}
          <button type="button" style={btnNeutre(busy || bloque)} disabled={busy || bloque}
                  onClick={onModifier}
                  title="Modifier la fiche de cette démonstration">Modifier</button>
          {' '}
          <button type="button" style={btnAnnuler(busy || bloque)} disabled={busy || bloque}
                  onClick={onRetirer}
                  title="Retirer cette fiche de la liste — la base PostgreSQL n’est pas touchée">
            Retirer
          </button>
        </td>
      </tr>
      {/* LES DÉFAUTS CONNUS ET LES NOTES NE S'AFFICHENT PLUS ICI (16/08/2026). Ce sont des notes
          de chantier — « le PDF est hors base », « 0 appel API, contenu rédigé directement » —
          écrites par qui montait la démonstration, pour un développeur. Elles doublaient la
          hauteur de chaque ligne. La donnée reste : elle se lit dans « Modifier ». */}
    </>
  )
}

function LigneEdition({ edition, setEdition, libres, demo, busy, onValider, onAnnuler }) {
  const set = (k, v) => setEdition(e => ({ ...e, [k]: v }))
  const nouveau = edition.id === 'nouveau'
  // Ce que le serveur a proposé au dernier choix de référentiel : sert uniquement à dire, sous
  // le champ, d'où viennent les compteurs. `null` tant qu'aucun choix n'a été fait.
  const [propose, setPropose] = useState(null)

  // AU CHOIX DU RÉFÉRENTIEL, l'écran va chercher ce qu'il peut renseigner seul : le nom de la
  // base, l'adresse, et les trois compteurs lus dans la base de démonstration elle-même.
  // Rien n'est imposé — tous les champs restent modifiables, et un échec de la requête laisse
  // simplement le formulaire tel qu'il était.
  async function choisirReferentiel(v) {
    set('referentiel_id', v)
    setPropose(null)
    if (!nouveau || v === '') return
    try {
      const r = await fetchWithTimeout('/api/admin/demos/proposition?referentiel_id=' + v,
                                       { credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) return
      const p = await r.json()
      setPropose(p)
      setEdition(e => ({
        ...e,
        nom_base: p.nom_base || e.nom_base,
        url: p.url || e.url,
        nb_sequences: p.nb_sequences,
        nb_seances: p.nb_seances,
        nb_activites: p.nb_activites,
      }))
    } catch {
      // Silence volontaire : la proposition est un confort, pas une étape. L'admin saisit.
    }
  }

  // En modification, le référentiel de la ligne ne figure pas dans « libres » (il est pris — par
  // elle). On le rajoute en tête, sinon le menu s'ouvrirait sur un choix vide.
  const choix = nouveau
    ? libres
    : [{ id: demo.referentiel_id, cycle: demo.cycle, niveau: demo.niveau }, ...libres]
  const pret = String(edition.referentiel_id) !== '' && edition.nom_base.trim() !== ''

  return (
    <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e5e7eb' }}>
      <td colSpan={6} style={{ padding: '10px 8px' }}>
        <div style={{ display: 'grid', gap: 8,
                      gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }}>
          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Niveau
            <select style={champ} value={edition.referentiel_id} disabled={busy}
                    onChange={e => choisirReferentiel(e.target.value)}
                    title="Le référentiel que cette démonstration fait découvrir — le choisir renseigne la base, l’adresse et les compteurs">
              <option value="">— choisir —</option>
              {choix.map(r => (
                <option key={r.id} value={r.id}>
                  {[r.cycle, r.niveau].filter(Boolean).join(' · ')}
                </option>
              ))}
            </select>
          </label>

          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Base PostgreSQL
            <input style={champ} value={edition.nom_base} disabled={busy}
                   onChange={e => set('nom_base', e.target.value)}
                   placeholder="ciela_demo"
                   title="Nom de la base qui contient les données — minuscules et soulignés, jamais de tiret" />
            {/* D'où viennent les compteurs affichés. Sans cette ligne, trois zéros passeraient
                pour un comptage réel alors que la base n'a pas encore été fabriquée. */}
            {propose && (
              <span style={{ fontSize: 11, color: propose.base_trouvee ? '#15803d' : '#92400e' }}>
                {propose.base_trouvee ? 'Base lue — compteurs à jour'
                  : propose.erreur ? 'Base injoignable (' + propose.erreur + ') — compteurs à saisir'
                  : 'Base pas encore fabriquée — compteurs à saisir'}
              </span>
            )}
          </label>

          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Adresse de l’instance
            <input style={champ} value={edition.url} disabled={busy}
                   onChange={e => set('url', e.target.value)}
                   placeholder="https://demo-ciela.aschool.fr"
                   title="L’application branchée sur cette base — c’est là que le menu prof enverra l’enseignant" />
          </label>

          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Activités
            <input style={champ} type="number" min="0" value={edition.nb_activites} disabled={busy}
                   onChange={e => set('nb_activites', e.target.value)}
                   title="Compteur figé — cet écran ne peut pas ouvrir la base pour recompter" />
          </label>

          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Séquences
            <input style={champ} type="number" min="0" value={edition.nb_sequences} disabled={busy}
                   onChange={e => set('nb_sequences', e.target.value)}
                   title="Compteur figé — cet écran ne peut pas ouvrir la base pour recompter" />
          </label>

          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Séances
            <input style={champ} type="number" min="0" value={edition.nb_seances} disabled={busy}
                   onChange={e => set('nb_seances', e.target.value)}
                   title="Compteur figé — cet écran ne peut pas ouvrir la base pour recompter" />
          </label>

          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Fabriquée le
            <input style={champ} type="date" value={edition.date_generation} disabled={busy}
                   onChange={e => set('date_generation', e.target.value)}
                   title="Date de fabrication de la base" />
          </label>

        </div>

        <div style={{ display: 'grid', gap: 8, marginTop: 8,
                      gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Défauts connus
            <textarea style={{ ...champ, height: 56, padding: '6px 8px', resize: 'vertical' }}
                      value={edition.defauts_connus} disabled={busy}
                      onChange={e => set('defauts_connus', e.target.value)}
                      title="Ce qu’on a déjà trouvé sur cette démonstration — pour ne pas le rechercher deux fois" />
          </label>
          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Notes
            <textarea style={{ ...champ, height: 56, padding: '6px 8px', resize: 'vertical' }}
                      value={edition.notes} disabled={busy}
                      onChange={e => set('notes', e.target.value)}
                      title="Tout ce qui mérite d’être retenu sur cette démonstration" />
          </label>
        </div>

        <div style={{ display: 'flex', gap: 8, marginTop: 10, justifyContent: 'flex-end' }}>
          <button type="button" style={btnAnnuler(busy)} disabled={busy} onClick={onAnnuler}
                  title="Abandonner la saisie sans rien enregistrer">Annuler</button>
          <button type="button" style={btnValider(busy || !pret)} disabled={busy || !pret}
                  onClick={onValider}
                  title={pret ? 'Enregistrer cette fiche'
                              : 'Choisissez un niveau et donnez le nom de la base'}>
            {busy ? 'Enregistrement…' : 'Valider'}
          </button>
        </div>
      </td>
    </tr>
  )
}


// IMPORTER LA FICHE D'UNE DÉMONSTRATION VENUE D'UNE AUTRE INSTALLATION.
//
// CE QU'ELLE APPORTE : le nom du compartiment de données, les compteurs, la date de fabrication,
// les défauts connus et les notes. Le rattachement se fait par le NOM du référentiel — s'il n'est
// pas là, l'import refuse en le disant, plutôt que de poser une fiche qui ne montrerait rien.
//
// L'ADRESSE NE VOYAGE PAS. Elle décrit une machine, et c'est elle qui ouvre la porte au
// professeur : importer « localhost » en production ouvrirait une entrée de menu vers le vide.
// On la renseigne à l'arrivée. Lors d'un remplacement, l'adresse déjà en place est conservée.
//
// DEUX CONFIRMATIONS POUR ÉCRASER, jamais une. Le serveur refuse d'abord ; l'écran demande alors
// si l'on remplace, puis fait confirmer une seconde fois. Écraser une fiche est sans retour.
function ImporterDemo({ onImporte }) {
  const [occupe, setOccupe] = useState(false)
  const champFichier = useRef(null)

  async function envoyer(fichier, remplacer) {
    const corps = new FormData()
    corps.append('fichier', fichier)
    corps.append('remplacer', remplacer ? 'true' : 'false')
    const r = await fetchWithTimeout('/api/admin/demos/importer',
                                     { method: 'POST', credentials: 'include', body: corps },
                                     TIMEOUT_XLONG)
    // UN REFUS EN AMONT NE PARLE PAS JSON : quand le serveur web écarte le fichier, il rend une
    // page HTML et `r.json()` échoue. Le code se dit en clair.
    if (r.status === 413) {
      throw new Error('Ce fichier est trop lourd pour être envoyé au serveur.\n\n'
                      + 'La limite se règle dans la configuration du serveur web.')
    }
    const d = await r.json().catch(() => ({}))
    return { ok: r.ok, corps: d }
  }

  async function importer(evenement) {
    const fichier = evenement.target.files?.[0]
    evenement.target.value = ''          // pour que le même fichier puisse être redéposé
    if (!fichier) return
    setOccupe(true)
    try {
      let { ok, corps } = await envoyer(fichier, false)

      // Le seul refus qui se rattrape : une fiche existe déjà pour ce référentiel.
      if (!ok && (corps.detail || '').includes('Confirmez le remplacement')) {
        const veut = await demanderConfirmation({
          titre: 'Une démonstration existe déjà',
          message: corps.detail.replace(' Confirmez le remplacement pour l’écraser — rien n’a été modifié.', '')
                   + '\n\nVoulez-vous la remplacer par celle du fichier ?',
          confirmLabel: 'Remplacer',
          danger: true,
        })
        if (!veut) return
        const sur = await demanderConfirmation({
          titre: 'Confirmer le remplacement',
          message: 'La fiche actuelle sera écrasée : compteurs, date de fabrication, défauts '
                   + 'connus et notes seront ceux du fichier.\n\nL’adresse déjà renseignée, elle, '
                   + 'est conservée — les professeurs gardent leur accès.\n\nCette opération est '
                   + 'sans retour.',
          confirmLabel: 'Oui, écraser',
          danger: true,
        })
        if (!sur) return
        ;({ ok, corps } = await envoyer(fichier, true))
      }

      if (!ok) throw new Error(corps.detail || 'Import impossible.')
      onImporte?.()
      showError(`« ${corps.etiquette || 'Démonstration'} » ${corps.remplacee ? 'remplacée' : 'installée'}.`
                + (corps.url ? '' : '\n\nRenseignez son adresse pour que les professeurs la voient.'),
                { titre: 'Import terminé', danger: false })
    } catch (e) {
      showError(e.message === 'timeout'
        ? 'Le serveur met trop de temps à répondre. Rien n’a été écrit.'
        : e.message)
    } finally {
      setOccupe(false)
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => champFichier.current?.click()}
        disabled={occupe}
        style={btnNeutre(occupe)}
        title="Installer la fiche d'une démonstration exportée depuis une autre installation"
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        Importer
      </button>
      <input ref={champFichier} type="file" accept=".json,application/json"
             onChange={importer} style={{ display: 'none' }} />
      {occupe && (
        <div style={{ marginLeft: 8 }}>
          <Attente texte="Installation…" compact />
        </div>
      )}
    </>
  )
}
