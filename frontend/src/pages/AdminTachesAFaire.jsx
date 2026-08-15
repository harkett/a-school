import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD, MSG_TIMEOUT } from '../utils/api.js'
import { useActionsEcran } from '../components/actionsEcran.jsx'

// LE CARNET DE L'ADMINISTRATEUR — les idées, notées avant d'être oubliées.
//
// POURQUOI CET ÉCRAN. Les professeurs ont « Mes feedbacks » pour faire remonter une remarque, et
// l'administrateur a l'écran qui les reçoit. Lui n'avait rien : une idée qui lui vient au milieu
// d'une autre tâche se disait, et se perdait.
//
// CE QUE CET ÉCRAN N'EST PAS. Le « Planificateur » exécute des travaux à l'heure dite. Ici rien
// ne s'exécute et rien n'est vérifié — c'est un carnet, il ne contient que ce qu'on y écrit.
//
// UNE NOTE COCHÉE DESCEND, ELLE NE DISPARAÎT PAS : c'est la trace de ce qui a été décidé, et
// parfois la preuve qu'on l'avait déjà tranché. Pour la faire disparaître, il y a « Supprimer »,
// et celui-là supprime vraiment.

const BTN = {
  display: 'inline-flex', alignItems: 'center', gap: 6, height: 30, padding: '0 12px',
  borderRadius: 7, fontSize: 12, fontWeight: 500, cursor: 'pointer', border: '1px solid transparent',
}
const BTN_AJOUTER = { ...BTN, background: '#16a34a', color: '#fff' }
const BTN_VALIDER = { ...BTN, background: '#1F6EEB', color: '#fff' }
const BTN_ANNULER = { ...BTN, background: '#dc2626', color: '#fff' }
const BTN_NEUTRE  = { ...BTN, background: '#fff', color: '#374151', borderColor: '#d1d5db' }
const grise = style => ({ ...style, opacity: 0.45, cursor: 'not-allowed' })

const CHAMP = {
  width: '100%', border: '1px solid #d1d5db', borderRadius: 7, padding: '7px 10px',
  fontSize: 13, outline: 'none', fontFamily: 'inherit',
}

const deuxChiffres = n => String(n).padStart(2, '0')

function jour(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${deuxChiffres(d.getDate())}/${deuxChiffres(d.getMonth() + 1)}/${d.getFullYear()}`
}

const VIDE = { titre: '', detail: '' }

export default function AdminTachesAFaire() {
  const [taches, setTaches] = useState(null)
  const [erreur, setErreur] = useState('')
  const [occupe, setOccupe] = useState(false)
  const [form, setForm]     = useState(null)   // { id | null, titre, detail } — une seule ouverte
  const [cherche, setCherche] = useState('')

  function charger() {
    return fetchWithTimeout('/api/admin/taches-a-faire', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error('Lecture du carnet impossible.'))))
      .then(d => setTaches(d.taches))
      .catch(e => setErreur(e.message === 'timeout' ? MSG_TIMEOUT : e.message))
  }

  useEffect(() => { charger() }, [])

  async function envoyer(url, methode, corps) {
    setOccupe(true)
    setErreur('')
    try {
      const res = await fetchWithTimeout(url, {
        method: methode,
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: corps ? JSON.stringify(corps) : undefined,
      }, TIMEOUT_STD)
      if (!res.ok) {
        let detail = 'Enregistrement impossible.'
        try { detail = (await res.json()).detail || detail } catch { /* corps illisible */ }
        throw new Error(detail)
      }
      await charger()
      return true
    } catch (e) {
      setErreur(e.message === 'timeout' ? MSG_TIMEOUT : e.message)
      return false
    } finally {
      setOccupe(false)
    }
  }

  async function enregistrer() {
    if (!form.titre.trim()) return
    const ok = form.id
      ? await envoyer(`/api/admin/taches-a-faire/${form.id}`, 'PUT',
                      { titre: form.titre, detail: form.detail, fait: form.fait })
      : await envoyer('/api/admin/taches-a-faire', 'POST',
                      { titre: form.titre, detail: form.detail })
    if (ok) setForm(null)
  }

  // Cocher passe par le MÊME enregistrement que la modification : une seule route, donc pas de
  // chemin discret par lequel une note pourrait changer d'état sans passer par les contrôles.
  function basculer(t) {
    return envoyer(`/api/admin/taches-a-faire/${t.id}`, 'PUT',
                   { titre: t.titre, detail: t.detail, fait: !t.fait })
  }

  async function supprimer(t) {
    if (!window.confirm(`Supprimer définitivement « ${t.titre} » ?`)) return
    await envoyer(`/api/admin/taches-a-faire/${t.id}`, 'DELETE', null)
  }

  useActionsEcran(
    taches ? (
      <button
        onClick={() => setForm({ id: null, ...VIDE })}
        disabled={!!form}
        title={form ? 'Terminez la note en cours' : 'Noter une idée ou un chantier à traiter'}
        style={form ? grise(BTN_AJOUTER) : BTN_AJOUTER}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             strokeWidth="2.5" strokeLinecap="round">
          <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        Ajouter une note
      </button>
    ) : null,
    [!!taches, !!form],
  )

  if (erreur && !taches) return <p style={{ fontSize: 13, color: '#dc2626' }}>{erreur}</p>
  if (!taches) return <p style={{ fontSize: 13, color: '#9ca3af' }}>Chargement…</p>

  // LA RECHERCHE PORTE SUR LE DÉTAIL AUTANT QUE SUR LE TITRE. Ce qu'on retrouve six mois plus
  // tard, ce n'est presque jamais le titre exact — c'est un mot du contexte : « SMTP », « alias »,
  // « Infomaniak ». Chercher dans le seul titre serait chercher dans la table des matières.
  const motif = cherche.trim().toLowerCase()
  const retenues = motif
    ? taches.filter(t => `${t.titre} ${t.detail || ''}`.toLowerCase().includes(motif))
    : taches
  const aFaire = retenues.filter(t => !t.fait)
  const faites = retenues.filter(t => t.fait)

  return (
    <div style={{ maxWidth: 900 }}>
      {erreur && (
        <p style={{ fontSize: 13, color: '#dc2626', marginBottom: 12 }}>{erreur}</p>
      )}

      {/* La recherche est au-dessus de tout : c'est le premier geste dès que le carnet dépasse
          une dizaine de notes. */}
      <div style={{ position: 'relative', marginBottom: 16 }}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#9ca3af"
             strokeWidth="2" strokeLinecap="round"
             style={{ position: 'absolute', left: 10, top: 9 }}>
          <circle cx="11" cy="11" r="7" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          value={cherche}
          onChange={e => setCherche(e.target.value)}
          placeholder="Rechercher dans les notes — titre et détail"
          style={{ ...CHAMP, paddingLeft: 32, paddingRight: cherche ? 32 : 10 }}
        />
        {cherche && (
          <button
            onClick={() => setCherche('')}
            title="Effacer la recherche"
            style={{ position: 'absolute', right: 8, top: 6, background: 'none', border: 'none',
                     cursor: 'pointer', color: '#9ca3af', fontSize: 16, lineHeight: 1, padding: 2 }}
          >
            ×
          </button>
        )}
      </div>

      {form && (
        <div style={{ border: '1px solid #bfdbfe', background: '#eff6ff', borderRadius: 10,
                      padding: 14, marginBottom: 16 }}>
          <label style={{ display: 'block', fontSize: 11, color: '#64748b', marginBottom: 4 }}>
            Titre
          </label>
          <input
            value={form.titre}
            onChange={e => setForm({ ...form, titre: e.target.value })}
            onKeyDown={e => e.key === 'Enter' && enregistrer()}
            placeholder="Ce qu'il faut faire, en une ligne"
            autoFocus
            maxLength={200}
            style={CHAMP}
          />
          <label style={{ display: 'block', fontSize: 11, color: '#64748b', margin: '10px 0 4px' }}>
            Détail <span style={{ color: '#9ca3af' }}>(facultatif)</span>
          </label>
          {/* LE POURQUOI, LES PIÈGES, CE QU'ON AVAIT DÉCIDÉ. C'est ce qui fait qu'une note
              relue dans six mois veut encore dire quelque chose. */}
          <textarea
            value={form.detail || ''}
            onChange={e => setForm({ ...form, detail: e.target.value })}
            rows={4}
            placeholder="Le contexte, la décision prise, ce qui reste à trancher…"
            style={{ ...CHAMP, resize: 'vertical' }}
          />
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button
              onClick={enregistrer}
              disabled={occupe || !form.titre.trim()}
              title={form.titre.trim() ? 'Enregistrer cette note' : 'Le titre est obligatoire'}
              style={(occupe || !form.titre.trim()) ? grise(BTN_VALIDER) : BTN_VALIDER}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Valider
            </button>
            <button
              onClick={() => setForm(null)}
              disabled={occupe}
              title="Abandonner cette note"
              style={occupe ? grise(BTN_ANNULER) : BTN_ANNULER}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   strokeWidth="2.5" strokeLinecap="round">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
              Annuler
            </button>
          </div>
        </div>
      )}

      <Bloc titre="À faire" lignes={aFaire} vide={motif ? 'Aucune note ne correspond.' : 'Rien en attente.'}
            basculer={basculer} supprimer={supprimer} occupe={occupe}
            modifier={t => setForm({ id: t.id, titre: t.titre, detail: t.detail || '', fait: t.fait })} />

      <Bloc titre="Faites" lignes={faites} vide={motif ? 'Aucune note ne correspond.' : 'Aucune note terminée.'} faites
            basculer={basculer} supprimer={supprimer} occupe={occupe}
            modifier={t => setForm({ id: t.id, titre: t.titre, detail: t.detail || '', fait: t.fait })} />
    </div>
  )
}

// LES DEUX TITRES SONT TOUJOURS AFFICHÉS, même sur une zone vide : masquer une zone sans note
// laisse croire que la rubrique n'existe pas — on ne cherche pas ce qu'on n'a jamais vu.
function Bloc({ titre, lignes, vide, faites, basculer, supprimer, modifier, occupe }) {
  return (
    <div style={{ marginBottom: 22 }}>
      <h3 style={{ fontSize: 15, fontWeight: 700, color: '#1e293b', marginBottom: 8 }}>
        {titre}
        <span style={{ marginLeft: 8, fontSize: 12, fontWeight: 400, color: '#94a3b8' }}>
          ({lignes.length})
        </span>
      </h3>
      {lignes.length === 0 ? (
        <p style={{ fontSize: 13, color: '#9ca3af' }}>{vide}</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {lignes.map(t => (
            <div key={t.id} style={{
              display: 'flex', alignItems: 'flex-start', gap: 10,
              border: '1px solid #e5e7eb', borderRadius: 10, padding: '10px 12px',
              background: faites ? '#f8fafc' : '#fff',
            }}>
              <input
                type="checkbox"
                checked={t.fait}
                disabled={occupe}
                onChange={() => basculer(t)}
                title={t.fait ? 'Remettre à faire' : 'Marquer comme faite'}
                style={{ marginTop: 3, cursor: occupe ? 'not-allowed' : 'pointer', width: 16, height: 16 }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: 13, fontWeight: 600,
                  color: faites ? '#94a3b8' : '#1e293b',
                  textDecoration: faites ? 'line-through' : 'none',
                }}>
                  {t.titre}
                </div>
                {t.detail && (
                  <div style={{ fontSize: 12, color: '#64748b', marginTop: 4, whiteSpace: 'pre-wrap' }}>
                    {t.detail}
                  </div>
                )}
                <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 6 }}>
                  Notée le {jour(t.created_at)}
                  {t.fait_at ? ` · faite le ${jour(t.fait_at)}` : ''}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  onClick={() => modifier(t)}
                  disabled={occupe}
                  title="Modifier cette note"
                  style={occupe ? grise(BTN_NEUTRE) : BTN_NEUTRE}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                       strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z" />
                  </svg>
                  Modifier
                </button>
                <button
                  onClick={() => supprimer(t)}
                  disabled={occupe}
                  title="Supprimer définitivement cette note"
                  style={occupe ? grise(BTN_ANNULER) : BTN_ANNULER}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                       strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                    <path d="M10 11v6M14 11v6" />
                  </svg>
                  Supprimer
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
