// Page « Base de données → Démos » — le PILOTAGE des bases de démonstration, jamais leur contenu.
//
// Une démonstration vit dans une base PostgreSQL À PART (ciela_demo, cielb_demo…) : un référentiel
// déjà fabriqué, un compte de démonstration, du contenu d'exemple. Cet écran ne l'ouvre JAMAIS —
// il tient sa FICHE, dans la base réelle. D'où deux conséquences visibles ici :
//   · les compteurs se SAISISSENT et ne se calculent pas (les recompter voudrait dire se
//     connecter à l'autre base, ce que le serveur ne fait pas) ;
//   · « Retirer » retire la fiche de la liste, pas la base — elle survit et se détruit à la main.
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'
import GuideDemos from '../components/GuideDemos.jsx'

// Les cinq statuts, du vide au livrable. Le mot affiché est celui qu'on prononce ; la valeur
// stockée reste celle de la base (`a_faire`…), jamais traduite en dur ailleurs.
const STATUTS = {
  a_faire:  { label: 'À faire',   bg: '#f1f5f9', color: '#475569', border: '#cbd5e1' },
  en_cours: { label: 'En cours',  bg: '#fffbeb', color: '#92400e', border: '#fde68a' },
  fait:     { label: 'Fabriquée', bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe' },
  teste:    { label: 'Testée',    bg: '#f5f3ff', color: '#6d28d9', border: '#ddd6fe' },
  valide:   { label: 'Validée',   bg: '#ecfdf5', color: '#065f46', border: '#a7f3d0' },
}

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
  referentiel_id: '', nom_base: '', url: '', statut: 'a_faire',
  nb_activites: 0, nb_sequences: 0, nb_seances: 0,
  date_generation: '', date_dernier_test: '', defauts_connus: '', notes: '',
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
      statut: edition.statut,
      nb_activites: Number(edition.nb_activites) || 0,
      nb_sequences: Number(edition.nb_sequences) || 0,
      nb_seances: Number(edition.nb_seances) || 0,
      // <input type="date"> rend « 2026-08-07 » ; le serveur attend un instant. Midi évite qu'un
      // décalage de fuseau ne recule la date d'un jour à l'affichage.
      date_generation: edition.date_generation ? edition.date_generation + 'T12:00:00' : null,
      date_dernier_test: edition.date_dernier_test ? edition.date_dernier_test + 'T12:00:00' : null,
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
      statut: d.statut,
      nb_activites: d.nb_activites,
      nb_sequences: d.nb_sequences,
      nb_seances: d.nb_seances,
      date_generation: pourInput(d.date_generation),
      date_dernier_test: pourInput(d.date_dernier_test),
      defauts_connus: d.defauts_connus || '',
      notes: d.notes || '',
    })
  }

  const libres = (data && data.referentiels_libres) || []

  return (
    <div className="flex flex-col gap-6">
      {guide && <GuideDemos onFermer={() => setGuide(false)} />}
      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-gray-800">Bases de démonstration</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Une base par niveau, livrée avec le produit : l’enseignant qui découvre y explore
              sans toucher au réel. Cet écran tient leur fiche — les données, elles, vivent dans
              leur propre base.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            <button
              type="button"
              style={btnNeutre(false)}
              onClick={() => setGuide(true)}
              title="Ce qu’est une démonstration, ce que cet écran pilote, et ce que le prof en voit"
            >
              <IconAide />Comment ça marche
            </button>
            <button
              type="button"
              style={btnAjouter(busy || !!edition || libres.length === 0)}
              disabled={busy || !!edition || libres.length === 0}
              onClick={() => setEdition({ id: 'nouveau', ...VIDE })}
              title={libres.length === 0
                ? 'Tous les référentiels ont déjà leur démonstration'
                : 'Déclarer une démonstration pour un référentiel qui n’en a pas encore'}
            >
              + Déclarer une démonstration
            </button>
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
                  <th style={{ padding: '6px 8px', fontWeight: 600 }}>Niveau</th>
                  <th style={{ padding: '6px 8px', fontWeight: 600 }}>Base</th>
                  <th style={{ padding: '6px 8px', fontWeight: 600 }}
                      title="L'instance branchée sur cette base — sans elle, le prof ne peut pas s'y rendre">
                    Adresse
                  </th>
                  <th style={{ padding: '6px 8px', fontWeight: 600 }}>Statut</th>
                  <th style={{ padding: '6px 8px', fontWeight: 600, textAlign: 'right' }}
                      title="Compteurs figés à la fabrication — cet écran ne peut pas les recompter">
                    Act. / Séq. / Séa.
                  </th>
                  <th style={{ padding: '6px 8px', fontWeight: 600 }}>Fabriquée</th>
                  <th style={{ padding: '6px 8px', fontWeight: 600 }}>Testée</th>
                  <th style={{ padding: '6px 8px', fontWeight: 600 }} />
                </tr>
              </thead>
              <tbody>
                {data.demos.map(d => (
                  edition && edition.id === d.id
                    ? <LigneEdition key={d.id} edition={edition} setEdition={setEdition}
                                    statuts={data.statuts} libres={libres} demo={d}
                                    busy={busy} onValider={enregistrer}
                                    onAnnuler={() => setEdition(null)} />
                    : <LigneLecture key={d.id} d={d} busy={busy} bloque={!!edition}
                                    onModifier={() => ouvrirModification(d)}
                                    onRetirer={() => retirer(d)} />
                ))}
                {edition && edition.id === 'nouveau' && (
                  <LigneEdition edition={edition} setEdition={setEdition}
                                statuts={data.statuts} libres={libres} demo={null}
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
  const s = STATUTS[d.statut] || STATUTS.a_faire
  return (
    <>
      <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
        <td style={{ padding: '8px', color: '#0f172a', fontWeight: 600 }}>
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
        <td style={{ padding: '8px' }}>
          <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999,
                         fontSize: 11.5, fontWeight: 600,
                         background: s.bg, color: s.color, border: '1px solid ' + s.border }}>
            {s.label}
          </span>
        </td>
        <td style={{ padding: '8px', textAlign: 'right', color: '#334155' }}>
          {d.nb_activites} / {d.nb_sequences} / {d.nb_seances}
        </td>
        <td style={{ padding: '8px', color: '#64748b' }}>{jour(d.date_generation)}</td>
        <td style={{ padding: '8px', color: '#64748b' }}>{jour(d.date_dernier_test)}</td>
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
      {(d.defauts_connus || d.notes) && (
        <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
          <td colSpan={8} style={{ padding: '0 8px 10px 8px' }}>
            {d.defauts_connus && (
              <div style={{ fontSize: 12, color: '#92400e', background: '#fffbeb',
                            border: '1px solid #fde68a', borderRadius: 6, padding: '6px 8px',
                            marginBottom: d.notes ? 6 : 0 }}>
                <strong>Défauts connus :</strong> {d.defauts_connus}
              </div>
            )}
            {d.notes && <div style={{ fontSize: 12, color: '#475569' }}>{d.notes}</div>}
          </td>
        </tr>
      )}
    </>
  )
}

function LigneEdition({ edition, setEdition, statuts, libres, demo, busy, onValider, onAnnuler }) {
  const set = (k, v) => setEdition(e => ({ ...e, [k]: v }))
  const nouveau = edition.id === 'nouveau'
  // En modification, le référentiel de la ligne ne figure pas dans « libres » (il est pris — par
  // elle). On le rajoute en tête, sinon le menu s'ouvrirait sur un choix vide.
  const choix = nouveau
    ? libres
    : [{ id: demo.referentiel_id, cycle: demo.cycle, niveau: demo.niveau }, ...libres]
  const pret = String(edition.referentiel_id) !== '' && edition.nom_base.trim() !== ''

  return (
    <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e5e7eb' }}>
      <td colSpan={8} style={{ padding: '10px 8px' }}>
        <div style={{ display: 'grid', gap: 8,
                      gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }}>
          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Niveau
            <select style={champ} value={edition.referentiel_id} disabled={busy}
                    onChange={e => set('referentiel_id', e.target.value)}
                    title="Le référentiel que cette démonstration fait découvrir">
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
          </label>

          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Adresse de l’instance
            <input style={champ} value={edition.url} disabled={busy}
                   onChange={e => set('url', e.target.value)}
                   placeholder="https://demo-ciela.aschool.fr"
                   title="L’application branchée sur cette base — c’est là que le menu prof enverra l’enseignant" />
          </label>

          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Statut
            <select style={champ} value={edition.statut} disabled={busy}
                    onChange={e => set('statut', e.target.value)}
                    title="Où en est cette démonstration">
              {statuts.map(s => (
                <option key={s} value={s}>{(STATUTS[s] || {}).label || s}</option>
              ))}
            </select>
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

          <label style={{ fontSize: 11.5, color: '#64748b' }}>
            Testée le
            <input style={champ} type="date" value={edition.date_dernier_test} disabled={busy}
                   onChange={e => set('date_dernier_test', e.target.value)}
                   title="Date du dernier parcours de vérification" />
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
