import { useEffect, useRef, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD, MSG_TIMEOUT } from '../utils/api.js'
import { useActionsEcran } from '../components/actionsEcran.jsx'
import FenetreRecette from '../components/FenetreRecette.jsx'

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

// ── LA RECETTE, EN LECTURE ────────────────────────────────────────────────────────────────────
// UNE MODALE EST MODALE. Voile sombre, l'écran de dessous ne se clique plus, le focus entre dans
// la fenêtre et n'en sort pas, Échap et la croix ferment. Une fenêtre posée par-dessus un écran
// resté vivant laisse supprimer une tâche pendant qu'on lit sa recette : c'est la règle de base
// des fenêtres, elle ne se discute pas.
function FenetreDeLaRecette({ tache, onFermer }) {
  const fermerRef = useRef(null)
  const carteRef = useRef(null)

  // Le focus entre dans la fenêtre à l'ouverture, et Échap la ferme.
  useEffect(() => {
    fermerRef.current?.focus()
    const onKey = e => {
      if (e.key === 'Escape') { onFermer(); return }
      // LE FOCUS NE SORT PAS. Sans ce piège, la tabulation repart dans la liste derrière le
      // voile : on donne le focus à des boutons qu'on ne peut plus cliquer.
      if (e.key !== 'Tab') return
      const cibles = carteRef.current?.querySelectorAll('button, [href], textarea, [tabindex]:not([tabindex="-1"])')
      if (!cibles?.length) return
      const premier = cibles[0]
      const dernier = cibles[cibles.length - 1]
      if (e.shiftKey && document.activeElement === premier) { e.preventDefault(); dernier.focus() }
      else if (!e.shiftKey && document.activeElement === dernier) { e.preventDefault(); premier.focus() }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onFermer])

  return (
    <div
      role="dialog"
      aria-modal="true"
      onMouseDown={e => { if (e.target === e.currentTarget) onFermer() }}
      style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.55)',
               backdropFilter: 'blur(2px)', zIndex: 2200, display: 'flex',
               alignItems: 'center', justifyContent: 'center', padding: 16 }}
    >
      <div ref={carteRef} style={{ background: '#fff', borderRadius: 12, width: '100%',
                                   maxWidth: 660, maxHeight: '82vh', display: 'flex',
                                   flexDirection: 'column', overflow: 'hidden',
                                   boxShadow: '0 24px 70px rgba(0,0,0,0.34)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '13px 16px',
                      borderBottom: '1px solid #e2e8f0' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--bleu)"
               strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <path d="M9 11l3 3L22 4" />
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
          </svg>
          <span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a', flex: 1, minWidth: 0,
                         overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            Recette — {tache.titre}
          </span>
        </div>

        <div style={{ padding: '16px 20px', overflowY: 'auto', flex: 1, fontSize: 13,
                      lineHeight: 1.7, whiteSpace: 'pre-wrap',
                      color: tache.recette ? '#334155' : '#9ca3af',
                      fontStyle: tache.recette ? 'normal' : 'italic' }}>
          {tache.recette
            || 'Aucune recette écrite pour cette tâche. Tant qu’elle manque, cocher ne prouve rien.'}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '12px 16px',
                      borderTop: '1px solid #e2e8f0', background: '#f8fafc' }}>
          <button ref={fermerRef} type="button" onClick={onFermer} title="Fermer cette fenêtre"
                  style={BTN_VALIDER}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            Fermer
          </button>
        </div>
      </div>
    </div>
  )
}

// ── LE MESSAGE POUR LA SESSION ────────────────────────────────────────────────────────────────
// Une note du carnet finit toujours de la même façon : on ouvre une session neuve, et on lui
// redit à la main ce qui est écrit là. Recopier, c'est perdre le détail — celui qui contient
// justement la spécification. Le bouton met la note entière dans le presse-papiers.
//
// LE TITRE SEUL EN PREMIÈRE LIGNE, puis le détail : c'est la forme d'une demande, pas d'une
// fiche. Une session qui reçoit ça n'a rien à décoder.
// LE TITRE ET LE TEXTE, RIEN DE PLUS. La recette et l'encart script sont DANS le détail depuis
// qu'ils sont posés à la création de la note : les rajouter ici les enverrait en double, et une
// session qui reçoit deux fois la même consigne cherche ce qui les distingue.
function messagePourLaSession(tache) {
  const detail = (tache.detail || '').trim()
  return detail ? `${tache.titre}\n\n${detail}` : tache.titre
}

// LE PRESSE-PAPIERS, AVEC SON REPLI. `navigator.clipboard` n'existe qu'en contexte sécurisé
// (https, ou localhost) : l'application ouverte par l'adresse IP de la machine ne l'a pas, et le
// bouton n'y ferait rien du tout. Le vieux `execCommand('copy')` sur un champ caché, lui, marche
// partout — il est là pour ce cas-là, pas par habitude.
async function copier(texte) {
  try {
    await navigator.clipboard.writeText(texte)
    return true
  } catch { /* contexte non sécurisé, ou permission refusée */ }
  try {
    const champ = document.createElement('textarea')
    champ.value = texte
    champ.style.position = 'fixed'
    champ.style.opacity = '0'
    document.body.appendChild(champ)
    champ.select()
    const fait = document.execCommand('copy')
    document.body.removeChild(champ)
    return fait
  } catch {
    return false
  }
}

export default function AdminTachesAFaire() {
  const [taches, setTaches] = useState(null)
  const [erreur, setErreur] = useState('')
  const [occupe, setOccupe] = useState(false)
  const [form, setForm]     = useState(null)   // { id | null, titre, detail } — une seule ouverte
  const [cherche, setCherche] = useState('')
  // La note dont la recette tourne. Une seule à la fois : le lanceur refuse les passages
  // parallèles, et deux fenêtres ouvertes montreraient le même passage sous deux noms.
  const [recette, setRecette] = useState(null)

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

  // COCHER NE COCHE PAS — ça lance la recette, et c'est elle qui décide.
  //
  // « Fait » était une déclaration : on cochait, et rien ne disait si le travail tenait debout.
  // Une note ne tombe donc plus que sur une recette verte. Le geste est le même — un clic sur la
  // case —, mais ce qui suit est une fenêtre qui parcourt l'application et rend un verdict.
  //
  // DÉCOCHER RESTE DIRECT. Remettre une note à faire, c'est RETIRER une affirmation, pas en
  // ajouter une : rien à prouver, donc rien à lancer. C'est aussi la seule sortie quand une
  // recette rate pour une raison qui n'a rien à voir avec la note.
  function basculer(t) {
    if (!t.fait) { setRecette(t); return Promise.resolve(true) }
    return envoyer(`/api/admin/taches-a-faire/${t.id}`, 'PUT',
                   { titre: t.titre, detail: t.detail, fait: false })
  }

  async function supprimer(t) {
    if (!window.confirm(`Supprimer définitivement « ${t.titre} » ?`)) return
    await envoyer(`/api/admin/taches-a-faire/${t.id}`, 'DELETE', null)
  }

  useActionsEcran(
    taches && !form ? (
      <button
        onClick={() => setForm({ id: null, ...VIDE })}
        title={'Inscrire une tâche à faire : son titre, et en détail ce qu’il faut faire. '
             + 'Elle ne se coche pas à la main — quand elle sera finie, cocher lancera la recette, '
             + 'et la case ne tombera que si tout passe.'}
        style={BTN_AJOUTER}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             strokeWidth="2.5" strokeLinecap="round">
          <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        Ajouter une nouvelle tâche
      </button>
    ) : null,
    [!!taches, !!form],
  )

  if (erreur && !taches) return <p style={{ fontSize: 13, color: '#dc2626' }}>{erreur}</p>
  if (!taches) return <p style={{ fontSize: 13, color: '#9ca3af' }}>Chargement…</p>

  // ── L'ÉCRAN DE CRÉATION PREND TOUTE LA PLACE ────────────────────────────────────────────
  // Le formulaire s'insérait entre la recherche et les listes, qui restaient affichées dessous :
  // on créait une tâche avec, sous les yeux, une barre de recherche dont on n'avait que faire et
  // trente lignes qu'on ne lisait pas. Écrire, c'est écrire — la liste attend son tour.
  //
  // AUCUNE DATE ICI. Celle qui compte est l'heure du clic sur « Valider », posée par la base.
  // L'afficher avant, c'est afficher une valeur qui n'est pas encore vraie.
  if (form) {
    const nouvelle = form.id === null
    return (
      // L'ÉCRAN OCCUPE LA PLACE, ET SUIT LA FENÊTRE. Une largeur figée laissait la moitié droite
      // vide sur un grand écran, et le champ « Détail » gardait ses quatre lignes au milieu d'un
      // blanc de trois cents pixels.
      <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
        {erreur && <p style={{ fontSize: 13, color: '#dc2626', marginBottom: 12 }}>{erreur}</p>}

        {/* LE TITRE ET LES DEUX GESTES SUR LA MÊME LIGNE, les boutons à droite. On lit de gauche
            à droite : le nom de l'écran d'abord, ce qu'on peut en faire au bout du regard. En bas
            de page, ils descendaient avec le champ « Détail » et sortaient de vue dès que la
            fenêtre rétrécissait. */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '0 0 16px' }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0f172a', margin: 0, flex: 1,
                       minWidth: 0 }}>
            {nouvelle ? 'Nouvelle tâche' : 'Modifier la tâche'}
          </h3>
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <button
              onClick={enregistrer}
              disabled={occupe || !form.titre.trim()}
              title={form.titre.trim() ? 'Enregistrer cette tâche' : 'Le titre est obligatoire'}
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
              title="Abandonner cette tâche"
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
          placeholder="Le contexte, la décision prise, ce qui reste à trancher…"
          // LA HAUTEUR SUIT LA FENÊTRE, en fraction de l'écran et non en pixels : la zone de
          // saisie garde la même proportion sur un portable et sur un grand écran, et se réduit
          // quand on rétrécit la fenêtre au lieu de pousser les boutons hors de vue.
          style={{ ...CHAMP, height: 'calc(100vh - 300px)', minHeight: 200, resize: 'vertical' }}
        />
      </div>
    )
  }

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
          placeholder="Rechercher dans les tâches — titre et détail"
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

      <Bloc titre="À faire" lignes={aFaire} vide={motif ? 'Aucune tâche ne correspond.' : 'Rien en attente.'}
            basculer={basculer} supprimer={supprimer} occupe={occupe} marquee={charger}
            modifier={t => setForm({ id: t.id, titre: t.titre, detail: t.detail || '', fait: t.fait })} />

      <Bloc titre="Faites" lignes={faites} vide={motif ? 'Aucune tâche ne correspond.' : 'Aucune tâche terminée.'} faites
            basculer={basculer} supprimer={supprimer} occupe={occupe} marquee={charger}
            modifier={t => setForm({ id: t.id, titre: t.titre, detail: t.detail || '', fait: t.fait })} />

      {/* LA RECETTE. Elle s'ouvre sur le clic dans la case, elle décide, et elle recharge le
          carnet en se fermant — la note a changé de bloc, ou elle a gagné sa mention. */}
      {recette && (
        <FenetreRecette
          tacheId={recette.id}
          titre={recette.titre}
          onFini={() => { setRecette(null); charger() }}
        />
      )}
    </div>
  )
}

// LA MENTION DE RECETTE — ce que la ligne dit de son dernier passage.
//
// DEUX MENTIONS, PAS TROIS. « Recette faite » sur une note du bas : c'est la preuve que la case
// a été gagnée et pas cochée. « À refaire » sur une note du haut : on a essayé, ça a lâché.
//
// ET RIEN SUR LES AUTRES. Une note jamais testée ne porte aucune marque — dans « À faire »,
// aucune ne l'a été : une mention « recette à faire » serait sur toutes les lignes et ne
// distinguerait donc rien. Le silence dit « pas encore essayé ».
function Mention({ tache }) {
  // CE QUI EST PARTI CHEZ UNE SESSION passe devant le reste : c'est l'état du moment, alors que
  // le verdict de recette parle du passage précédent.
  if (tache.dev_en_cours && !tache.fait) {
    return (
      <span
        title="Le texte de cette tâche a été copié et confié à une session. La mention partira quand la tâche sera cochée."
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 5, flexShrink: 0,
          padding: '2px 9px', borderRadius: 999, fontSize: 11, fontWeight: 600,
          color: '#9a3412', background: '#fff7ed', border: '1px solid #fed7aa',
        }}
      >
        <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#ea580c' }} />
        Développement en cours
      </span>
    )
  }
  const etat = tache.recette_etat
  if (!etat) return null
  const vert = etat === 'verte'
  return (
    <span
      title={vert
        ? 'La recette est passée : cette tâche a été vérifiée, pas seulement cochée'
        : 'La recette a échoué — ouvrez le détail pour voir ce qui a lâché'}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 5, flexShrink: 0,
        padding: '2px 9px', borderRadius: 999, fontSize: 11, fontWeight: 600,
        color: vert ? '#166534' : '#991b1b',
        background: vert ? '#f0fdf4' : '#fef2f2',
        border: `1px solid ${vert ? '#bbf7d0' : '#fecaca'}`,
      }}
    >
      <span style={{ width: 6, height: 6, borderRadius: '50%',
                     background: vert ? '#16a34a' : '#dc2626' }} />
      {vert ? 'Recette faite' : 'Recette à refaire'}
    </span>
  )
}

// LES DEUX TITRES SONT TOUJOURS AFFICHÉS, même sur une zone vide : masquer une zone sans note
// laisse croire que la rubrique n'existe pas — on ne cherche pas ce qu'on n'a jamais vu.
//
// UNE LIGNE = UN TITRE (18/08/2026). Chaque note dépliait tout : son texte complet sur plusieurs
// lignes, sa date, ses deux boutons — trente notes faisaient une page qu'on ne parcourait plus.
// La liste ne porte donc que le titre et sa case à cocher ; « Détail » ouvre le reste, et c'est
// là que Modifier et Supprimer attendent — deux gestes qui portent sur une note qu'on vient de
// relire, jamais sur une ligne survolée au passage.
function Bloc({ titre, lignes, vide, faites, basculer, supprimer, modifier, occupe, marquee }) {
  // Une seule note ouverte à la fois : la liste reste une liste.
  const [ouverte, setOuverte] = useState(null)
  // La note qu'on vient de copier. Un presse-papiers ne se voit pas : sans cette confirmation de
  // deux secondes, on ne sait pas si le clic a pris et on recopie deux fois pour être sûr.
  const [copiee, setCopiee] = useState(null)
  // La note dont on lit l'épreuve. L'administrateur l'ouvre pour savoir ce qui sera vérifié ;
  // c'est le dev qui l'écrit et la met à jour, jamais cet écran.
  const [recetteLue, setRecetteLue] = useState(null)

  async function copierLaNote(t) {
    if (!(await copier(messagePourLaSession(t)))) return
    setCopiee(t.id)
    setTimeout(() => setCopiee(c => (c === t.id ? null : c)), 2000)
    // COPIER, C'EST DONNER. Le texte part chez une session : la ligne le dit désormais, et ne
    // le dira plus le jour où la note sera cochée.
    await fetch(`/api/admin/taches-a-faire/${t.id}/en-developpement`,
                { method: 'POST', credentials: 'include' }).catch(() => {})
    marquee?.(t.id)
  }

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
          {lignes.map(t => {
            const ouvert = ouverte === t.id
            return (
            <div key={t.id} style={{
              border: '1px solid #e5e7eb', borderRadius: 10,
              background: faites ? '#f8fafc' : '#fff',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px' }}>
                {/* SANS RECETTE, LA CASE NE SE COCHE PAS. Cocher, c'est lancer l'épreuve ; une
                    note qui n'en a pas n'aurait rien à faire vérifier, et la case tomberait sur
                    une déclaration — exactement ce que ce carnet ne veut plus. Décocher reste
                    possible : retirer une affirmation ne demande aucune preuve. */}
                <input
                  type="checkbox"
                  checked={t.fait}
                  disabled={occupe || (!t.fait && !t.recette)}
                  onChange={() => basculer(t)}
                  title={t.fait
                    ? 'Remettre à faire'
                    : (t.recette
                        ? 'Marquer comme faite — la recette de cette tâche va être lancée'
                        : 'Cette tâche n’a pas encore de recette : rien à vérifier, donc rien à cocher')}
                  style={{ cursor: (occupe || (!t.fait && !t.recette)) ? 'not-allowed' : 'pointer',
                           width: 16, height: 16, flexShrink: 0 }}
                />
                {/* Le titre seul, sur UNE ligne : coupé par des points de suspension plutôt que
                    replié sur trois lignes — la liste garde sa hauteur, le détail dira tout. */}
                <div style={{
                  flex: 1, minWidth: 0,
                  fontSize: 13, fontWeight: 600,
                  color: faites ? '#94a3b8' : '#1e293b',
                  textDecoration: faites ? 'line-through' : 'none',
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>
                  {/* LE NUMÉRO DE LA NOTE, devant son titre. C'est par lui qu'on la désigne
                      quand on en parle ailleurs — dans une session, dans un message. */}
                  <span style={{ color: '#94a3b8', fontWeight: 600, marginRight: 6 }}>{t.id}</span>
                  {t.titre}
                </div>
                {/* LA DATE, en petit et en gris — celle qui compte pour le bloc où l'on est :
                    quand la note a été prise tant qu'elle est à faire, quand elle a été terminée
                    une fois qu'elle l'est. Le détail garde les trois, celle-ci est là pour le
                    coup d'œil : voir d'un balayage ce qui traîne depuis trois semaines. */}
                <span style={{ fontSize: 11, color: '#94a3b8', flexShrink: 0,
                               fontVariantNumeric: 'tabular-nums' }}>
                  {faites ? jour(t.fait_at) : jour(t.created_at)}
                </span>
                <Mention tache={t} />
                {/* COPIER LA NOTE — sur la ligne, pas dans le détail : le geste sert à passer la
                    tâche à une session neuve, on le fait en parcourant la liste, sans déplier. */}
                <button
                  onClick={() => copierLaNote(t)}
                  title="Copier le message pour la session — le titre et le détail de cette tâche, prêts à coller dans une session neuve"
                  style={{ ...BTN_NEUTRE, flexShrink: 0,
                           ...(copiee === t.id ? { color: '#166534', borderColor: '#bbf7d0',
                                                   background: '#f0fdf4' } : null) }}
                >
                  {copiee === t.id ? (
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                         strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 6 9 17l-5-5" />
                    </svg>
                  ) : (
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                    </svg>
                  )}
                  {copiee === t.id ? 'Copié' : 'Copier'}
                </button>
                {/* L'ÉPREUVE DE CETTE TÂCHE — ce que la recette vérifiera, en clair. Sans elle,
                    cocher lançait une suite de scénarios qui n'avaient rien à voir avec la note. */}
                <button
                  onClick={() => setRecetteLue(t)}
                  title={t.recette
                    ? 'Voir la recette de cette tâche — les gestes qui seront vérifiés'
                    : 'Cette tâche n’a pas encore de recette'}
                  style={{ ...BTN_NEUTRE, flexShrink: 0,
                           ...(t.recette ? null : { color: '#9ca3af' }) }}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                       strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 11l3 3L22 4" />
                    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                  </svg>
                  Recette
                </button>
                <button
                  onClick={() => setOuverte(ouvert ? null : t.id)}
                  title={ouvert ? 'Replier cette tâche' : 'Voir le détail de cette tâche, la modifier ou la supprimer'}
                  style={{ ...BTN_NEUTRE, flexShrink: 0 }}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                       strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                       style={{ transform: ouvert ? 'rotate(180deg)' : 'none', transition: 'transform .15s' }}>
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                  Détail
                </button>
              </div>

              {ouvert && (
                <div style={{ borderTop: '1px solid #f1f5f9', padding: '10px 12px 12px' }}>
                  {/* LES DEUX GESTES EN HAUT À DROITE, sous « Copier » et « Détail » : la même
                      place, la même règle que l'écran de modification. */}
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6,
                                marginBottom: 10 }}>
                    <button
                      onClick={() => modifier(t)}
                      disabled={occupe}
                      title="Modifier cette tâche"
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
                      title="Supprimer définitivement cette tâche"
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
                  {/* Le texte de la note, en entier. Une note sans détail le dit : un blanc
                      laisserait croire que le dépliage a raté. */}
                  <div style={{ fontSize: 12, color: t.detail ? '#374151' : '#9ca3af',
                                whiteSpace: 'pre-wrap', fontStyle: t.detail ? 'normal' : 'italic' }}>
                    {t.detail || 'Aucun détail pour cette tâche.'}
                  </div>
                  {/* CE QUI A LÂCHÉ, gardé sous la note. Une mention « recette à refaire » sans
                      motif oblige à relancer trois minutes pour réapprendre ce qu'on savait. */}
                  {t.recette_etat === 'ratee' && t.recette_detail && (
                    <div style={{ marginTop: 10, padding: '9px 11px', borderRadius: 8,
                                  background: '#fef2f2', border: '1px solid #fecaca',
                                  fontSize: 12, color: '#7f1d1d', lineHeight: 1.6 }}>
                      <strong style={{ color: '#dc2626' }}>Dernière recette</strong> — {t.recette_detail}
                    </div>
                  )}
                  <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 8 }}>
                    Notée le {jour(t.created_at)}
                    {t.fait_at ? ` · faite le ${jour(t.fait_at)}` : ''}
                    {t.recette_at ? ` · recette le ${jour(t.recette_at)}` : ''}
                  </div>
                </div>
              )}
            </div>
            )
          })}
        </div>
      )}

      {/* LA RECETTE, EN LECTURE. Dans la coquille de la maison, comme toutes les fenêtres —
          déplaçable, étirable, fermée par sa croix. On lit ce qui sera vérifié ; on ne l'écrit
          pas ici. */}
      {recetteLue && (
        <FenetreDeLaRecette tache={recetteLue} onFermer={() => setRecetteLue(null)} />
      )}
    </div>
  )
}
