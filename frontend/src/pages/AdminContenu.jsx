import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchWithTimeout, lireReponse, messagePourEcran, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'
import { demanderConfirmation } from '../confirmDialog'
import { lignesMatieres, nbAuProgramme, compterContenu, AU_PROGRAMME, DESACTIVEE, PROPOSEE } from '../utils/contenuMatieres.js'
import SplitPane from '../components/SplitPane.jsx'

// LA page « Programmes & contenu » : tout le contenu pédagogique dans UN SEUL tableau qui se
// déroule — cycle → niveau (le couple) → référentiel, matières, types d'activité (et leurs
// précisions) — ET les gestes du programme au même endroit : « + Cycle » / « + Niveau » dans
// l'arbre, les matières d'un niveau dans le niveau déplié. Source unique = la base : UNE seule
// lecture (GET /admin/contenu), et chaque écriture est suivie d'une RELECTURE complète
// (read-after-write, jamais de miroir local).
//
// LA GRILLE A DISPARU (chantier Matière). L'écran croisait un catalogue global de matières avec
// les niveaux : une case à cocher par intersection, une paire matière × niveau derrière chaque
// case, et un panneau « Matières » au-dessus pour gérer le catalogue. Une matière appartient
// désormais au RÉFÉRENTIEL d'un niveau : il n'y a plus de catalogue à croiser, plus de paire à
// cocher, et les matières d'un niveau s'affichent simplement dans ce niveau. Un niveau sans
// référentiel n'a pas de matière et le dit — c'est l'écran Référentiel qui reçoit son document.

// Badge d'origine d'un type — même vérité que sur l'écran Référentiel : le lien dit qui l'a
// posé (source), le catalogue dit d'où vient le type (origine).
function BadgeType({ source, origine }) {
  const b = source === 'ia'
    ? (origine === 'ia'
        ? { texte: 'IA', bg: '#f3e8ff', fg: '#7e22ce' }
        : { texte: 'SYSTÈME · IA', bg: '#e0f2fe', fg: '#0369a1' })
    : source === 'admin'
      ? { texte: 'ADMIN', bg: '#e0e7ff', fg: '#4338ca' }
      : { texte: 'SYSTÈME', bg: '#f1f5f9', fg: '#64748b' }
  return (
    <span style={{ marginLeft: 8, padding: '1px 7px', borderRadius: 4, fontSize: 10, fontWeight: 600, background: b.bg, color: b.fg, whiteSpace: 'nowrap' }}>
      {b.texte}
    </span>
  )
}

// Pastille d'état compacte (référentiel : PDF, épuré, découpe…).
function Etat({ ok, texte }) {
  return (
    <span style={{
      padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap',
      background: ok ? '#dcfce7' : '#f1f5f9', color: ok ? '#16a34a' : '#94a3b8',
    }}>{texte}</span>
  )
}

// L'allure d'une matière dit son état, avec les mêmes couleurs que l'écran Référentiel :
// vert = au programme, violet = proposée par la lecture du document, gris = désactivée.
const ALLURE_MATIERE = {
  [AU_PROGRAMME]: { bg: '#f0fdf4', bord: '#bbf7d0', fg: '#166534', mention: null },
  [DESACTIVEE]:   { bg: '#fff',    bord: '#e2e8f0', fg: '#94a3b8', mention: 'retirée' },
  [PROPOSEE]:     { bg: '#faf5ff', bord: '#e9d5ff', fg: '#7e22ce', mention: 'proposée' },
}

const CHEVRON = (ouvert) => (
  <span aria-hidden="true" style={{
    display: 'inline-block', width: 14, fontSize: 10, color: '#94a3b8',
    transform: ouvert ? 'rotate(90deg)' : 'none', transition: 'transform 0.12s',
  }}>▶</span>
)

// Styles partagés des petites rangées d'ajout (mêmes que l'ex-écran Programmes).
const CHAMP_AJOUT = { flex: 1, minWidth: 0, border: '1px solid #d1d5db', borderRadius: 6, padding: '6px 8px', fontSize: 12 }
const btnAjout = (busy) => ({
  whiteSpace: 'nowrap', fontSize: 12, fontWeight: 600, padding: '6px 10px', borderRadius: 6,
  border: '1px solid #cbd5e1', background: '#f8fafc', color: '#334155', cursor: busy ? 'wait' : 'pointer',
})

export default function AdminContenu() {
  const [busy, setBusy]       = useState(false)    // une écriture (et sa relecture) est en cours
  const [nivOuverts, setNivOuverts] = useState(() => new Set())      // niveaux dépliés
  const [typesOuverts, setTypesOuverts] = useState(() => new Set())  // `${niveauId}|${typeId}` → précisions dépliées
  // Le prompt des matières du cycle ouvert à droite — LU en base à la demande, jamais recopié :
  // { id, nom, prompt, valide }. null = colonne de droite au repos.
  const [promptCycle, setPromptCycle] = useState(null)
  const [promptLectureId, setPromptLectureId] = useState(0)   // cycle en cours de lecture
  const [detailCache, setDetailCache] = useState(false)
  const navigate = useNavigate()

  // Lecture COMPLÈTE en base, en UN appel : l'arbre porte le référentiel de chaque niveau, ses
  // matières avec leur état, et ses types. C'est react-query qui tient cette lecture — « en
  // cours », « en panne » et la relecture ne sont plus des états posés à la main : ils SONT le
  // get. Une panne (réseau, serveur) n'affiche JAMAIS le faux « Aucun cycle en base. » : erreur
  // en modale (règle maison), l'écran ne garde qu'un « Réessayer ».
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['admin-contenu'],
    queryFn: async () => {
      const rc = await fetchWithTimeout('/api/admin/contenu', { credentials: 'include' }, TIMEOUT_STD)
      if (rc.status === 401) { navigate('/admin/login'); return { cycles: [] } }
      return await lireReponse(rc)
    },
  })
  const cycles = data?.cycles || []
  const panne  = isError

  // L'erreur de lecture se dit en modale (règle maison) — react-query la porte, il ne l'affiche
  // pas. Chaque échec produit un nouvel objet d'erreur : une relecture ratée reparle.
  useEffect(() => { if (error) showError(messagePourEcran(error)) }, [error])

  async function recharger() { await refetch() }

  // Enveloppe commune des écritures : écrit, montre l'erreur en modale, puis RELIT la base
  // (read-after-write — succès OU échec, l'écran raconte toujours l'état réel des tables).
  async function ecrire(action) {
    setBusy(true)
    let ok = false
    try { await action(); ok = true }
    catch (err) { showError(messagePourEcran(err)) }
    finally {
      await recharger()
      setBusy(false)
    }
    return ok
  }

  function creerCycle(nom) {
    const n = (nom || '').trim()
    if (!n) { showError('Indiquez le nom du cycle.'); return Promise.resolve(false) }
    return ecrire(async () => {
      const r = await fetchWithTimeout('/api/admin/cycles', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nom: n }),
      }, TIMEOUT_STD)
      await lireReponse(r)
    })
  }

  function creerNiveau(cycle_id, nom) {
    const n = (nom || '').trim()
    if (!n) { showError('Indiquez le nom du niveau.'); return Promise.resolve(false) }
    return ecrire(async () => {
      const r = await fetchWithTimeout('/api/admin/niveaux', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id, nom: n }),
      }, TIMEOUT_STD)
      const d = await lireReponse(r)
      // Le niveau tout neuf s'ouvre : on voit tout de suite ce qui lui manque.
      setNivOuverts(prev => { const s = new Set(prev); s.add(d.id); return s })
    })
  }

  // Une matière naît DANS un référentiel : sans référentiel, pas de matière — et le champ
  // d'ajout n'existe alors même pas à l'écran.
  function creerMatiere(referentiel_id, nom) {
    const n = (nom || '').trim()
    if (!n) { showError('Indiquez le nom de la matière.'); return Promise.resolve(false) }
    return ecrire(async () => {
      const r = await fetchWithTimeout('/api/admin/matieres', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ referentiel_id, nom: n }),
      }, TIMEOUT_STD)
      await lireReponse(r)
    })
  }

  async function toggleMatiere(m, niveauNom) {
    if (m.actif && !await demanderConfirmation({
      titre: `Retirer « ${m.nom} » du programme de ${niveauNom} ?`,
      message: `Elle disparaîtra des menus des profs de ce niveau. Les autres niveaux ne sont pas touchés : leurs matières leur appartiennent, même si l'une d'elles porte le même nom.\n\nRéversible : rien n'est supprimé, la matière reste sur son référentiel avec son historique.`,
      confirmLabel: 'Retirer du programme',
    })) return false
    return ecrire(async () => {
      const r = await fetchWithTimeout('/api/admin/matieres/actif', {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ matiere_id: m.id, actif: !m.actif }),
      }, TIMEOUT_STD)
      await lireReponse(r)
    })
  }

  // « Cette matière porte une langue » — l'indicateur qui décide si le prof choisit une langue à
  // son profil, et si la génération l'injecte dans le prompt. Il vit sur la ligne matière, donc
  // il se règle ici, à côté d'elle : une matière et ses attributs sur un seul écran. Sans cette
  // case, aucune matière ne pourrait plus le porter — elles naissent toutes à « non ».
  function toggleLangue(m) {
    return ecrire(async () => {
      const r = await fetchWithTimeout('/api/admin/matieres/demande-langue', {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ matiere_id: m.id, demande_langue: !m.demande_langue }),
      }, TIMEOUT_STD)
      await lireReponse(r)
    })
  }

  // « Voir le prompt » d'un cycle → colonne de droite. Reclic sur le MÊME cycle = « Fermer ».
  // Lecture en base à chaque ouverture (get direct) : ce qui s'affiche est ce qui est en base au
  // moment du clic, même si le prompt vient d'être changé dans l'écran Prompts.
  async function voirPrompt(cycle) {
    if (promptCycle && promptCycle.id === cycle.id) { setPromptCycle(null); return }
    setPromptLectureId(cycle.id)
    try {
      const r = await fetchWithTimeout(`/api/admin/cycles/prompt-matieres?cycle_id=${cycle.id}`,
        { credentials: 'include' }, TIMEOUT_STD)
      const d = await lireReponse(r)
      setPromptCycle({ id: cycle.id, nom: cycle.nom, prompt: d.prompt || '', valide: !!d.valide })
      setDetailCache(false)   // demander à voir le prompt veut dire « montre-moi le détail »
    } catch (err) {
      showError(messagePourEcran(err))
    } finally {
      setPromptLectureId(0)
    }
  }

  function basculerNiveau(id) {
    setNivOuverts(prev => {
      const s = new Set(prev)
      if (s.has(id)) s.delete(id); else s.add(id)
      return s
    })
  }
  function basculerType(cle) {
    setTypesOuverts(prev => {
      const s = new Set(prev)
      if (s.has(cle)) s.delete(cle); else s.add(cle)
      return s
    })
  }

  if (isPending) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  // Panne de lecture : l'erreur est déjà passée en modale ; l'écran ne garde que « Réessayer ».
  if (panne) return (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <button
        type="button"
        onClick={() => refetch()}
        title="Relancer la lecture du contenu pédagogique"
        style={{ padding: '9px 24px', borderRadius: 8, border: '1px solid #cbd5e1',
                 background: '#fff', color: '#334155', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
      >
        Réessayer
      </button>
    </div>
  )

  // Comptages DÉRIVÉS de l'arbre lu (jamais stockés) — les matières comptées sont celles qui sont
  // vraiment au programme, sans dédoublonner par nom : deux référentiels ont chacun les leurs.
  const total = compterContenu(cycles)

  // ── Colonne gauche : l'arbre du contenu, tel qu'il a toujours été. ──
  const colonneArbre = (
    <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <tbody>
          {cycles.length === 0 && (
            <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
              <td colSpan={2} style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8', fontSize: 13 }}>
                Aucun cycle en base.
              </td>
            </tr>
          )}
          {cycles.map(cycle => (
            <CycleBloc
              key={cycle.id}
              cycle={cycle}
              busy={busy}
              nivOuverts={nivOuverts}
              typesOuverts={typesOuverts}
              basculerNiveau={basculerNiveau}
              basculerType={basculerType}
              onCreerNiveau={creerNiveau}
              onCreerMatiere={creerMatiere}
              onToggleMatiere={toggleMatiere}
              onToggleLangue={toggleLangue}
              promptOuvert={!!promptCycle && promptCycle.id === cycle.id}
              promptLecture={promptLectureId === cycle.id}
              onVoirPrompt={voirPrompt}
            />
          ))}
          <AjoutCycleRow busy={busy} onCreer={creerCycle} />
        </tbody>
      </table>
    </div>
  )

  // ── Colonne droite : le détail du cycle choisi — son prompt des matières, EN LECTURE SEULE.
  //    Il se modifie dans Prompts → Matières par cycle ; ici, c'est une fenêtre, pas un éditeur. ──
  const colonneDetail = !promptCycle ? (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <p className="text-sm text-gray-500">
        Cliquez « Voir le prompt » sur un cycle pour lire ici le texte qui lit les matières de ses
        référentiels.
      </p>
      <p className="text-xs text-gray-400 mt-2">
        Il est rangé sur le cycle et sert à tous ses référentiels. Il s'écrit et se corrige dans
        <b> Prompts → Matières par cycle</b> ; cet écran ne fait que le montrer.
      </p>
    </div>
  ) : (
    <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-4"
         style={{ height: '100%', minHeight: 320 }}>
      <div style={{ flexShrink: 0 }}>
        <h3 className="text-sm font-semibold text-gray-700">
          Prompt de lecture des matières — cycle « {promptCycle.nom} »
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11, fontWeight: 700,
            color: promptCycle.valide ? '#166534' : promptCycle.prompt.trim() ? '#b45309' : '#6b7280' }}>
            {promptCycle.valide ? '● relu et validé'
              : promptCycle.prompt.trim() ? '● écrit par l’IA, à relire'
              : '● pas encore écrit'}
          </span>
          <span style={{ fontSize: 11, color: '#94a3b8' }}>
            lecture seule — il se modifie dans Prompts → Matières par cycle
          </span>
        </div>
      </div>
      {promptCycle.prompt.trim() ? (
        <pre style={{
          flex: 1, minHeight: 0, margin: 0, overflow: 'auto', whiteSpace: 'pre-wrap',
          wordBreak: 'break-word', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
          fontSize: 12, lineHeight: 1.5, color: '#334155',
          background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: 10,
        }}>
          {promptCycle.prompt}
        </pre>
      ) : (
        <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>
          Ce cycle n’a pas encore de prompt : il sera écrit par l’IA au premier
          « Proposer les matières » d’un de ses référentiels.
        </p>
      )}
    </div>
  )

  return (
    <div className="flex flex-col gap-3" style={{ height: '100%' }}>
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">Programmes &amp; contenu</h2>
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-xs text-gray-400">
            {total.cycles} cycle{total.cycles > 1 ? 's' : ''} · {total.niveaux} niveau{total.niveaux > 1 ? 'x' : ''} · {total.matieres} matière{total.matieres > 1 ? 's' : ''} au programme
          </span>
          {/* Permanent sur les pages listes (règle maison) : il ne se retire jamais. */}
          <button
            type="button"
            onClick={() => setDetailCache(c => !c)}
            title={detailCache
              ? 'Réafficher la colonne de détail à droite'
              : 'Cacher la colonne de détail — l’arbre prend toute la largeur'}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6, flexShrink: 0,
              background: 'white', color: '#6b7280', border: '1px solid #e5e7eb',
              borderRadius: 7, padding: '7px 14px', fontSize: 12, fontWeight: 500, cursor: 'pointer',
            }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {detailCache
                ? <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
                : <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>}
            </svg>
            {detailCache ? 'Afficher le détail' : 'Cacher le détail'}
          </button>
        </div>
      </div>

      <p className="text-xs text-gray-500" style={{ maxWidth: 760, lineHeight: 1.5 }}>
        Tout le contenu pédagogique, lu en direct dans la base. Ajoutez cycles et niveaux
        directement dans l'arbre&nbsp;; dépliez un niveau pour voir et gérer <b>ses matières</b> —
        elles appartiennent à son référentiel, un niveau ne partage jamais les siennes avec un
        autre. Retirer une matière du programme la retire des menus des profs de ce niveau
        (réversible, rien n'est supprimé)&nbsp;; cochez <b>langue</b> sur celles qui en sont une,
        pour que leurs profs choisissent laquelle. Le dépôt du référentiel, lui, se fait sur l'écran
        <b> Référentiel</b> : c'est aussi là que se retiennent les matières qu'il propose.
      </p>

      {/* Deux colonnes redimensionnables, comme les pages listes : l'arbre à gauche, le détail à
          droite. Détail caché : l'arbre prend toute la largeur. */}
      <div className="admin-contenu-corps">
        {detailCache
          ? <div className="split-pane"><div className="split-col split-col-flex">{colonneArbre}</div></div>
          : <SplitPane
              storageKey="admin-contenu-split-v1"
              defautGauche={58}
              gauche={colonneArbre}
              droite={colonneDetail}
            />}
      </div>
    </div>
  )
}

// ── Rangée « + Cycle » en pied d'arbre — SA cartouche, SON état. ──
function AjoutCycleRow({ busy, onCreer }) {
  const [nom, setNom] = useState('')

  async function creer() {
    const ok = await onCreer(nom)
    if (ok) setNom('')
  }

  return (
    <tr>
      <td colSpan={2} style={{ padding: '10px 16px', background: '#f8fafc' }}>
        <div style={{ display: 'flex', gap: 6, maxWidth: 420 }}>
          <input
            style={CHAMP_AJOUT} value={nom} disabled={busy}
            placeholder="Nom du cycle…" title="Nom du nouveau cycle (ex. CAP)"
            onChange={e => setNom(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') creer() }}
          />
          <button type="button" style={btnAjout(busy)} onClick={creer} disabled={busy}
            title="Créer ce cycle (il apparaît dans l'arbre, prêt à recevoir ses niveaux)">+ Cycle</button>
        </div>
      </td>
    </tr>
  )
}

// ── Rangée « + Niveau » d'un cycle — SA cartouche, SON état. ──
function AjoutNiveauRow({ cycle, busy, onCreer }) {
  const [nom, setNom] = useState('')

  async function creer() {
    const ok = await onCreer(cycle.id, nom)
    if (ok) setNom('')
  }

  return (
    <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
      <td colSpan={2} style={{ padding: '6px 16px 10px 40px' }}>
        <div style={{ display: 'flex', gap: 6, maxWidth: 420 }}>
          <input
            style={CHAMP_AJOUT} value={nom} disabled={busy}
            placeholder={`Nom du niveau dans « ${cycle.nom} »…`}
            title="Nom du nouveau niveau de ce cycle (ex. CAP Cuisine)"
            onChange={e => setNom(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') creer() }}
          />
          <button type="button" style={btnAjout(busy)} onClick={creer} disabled={busy}
            title="Créer ce niveau dans ce cycle (il s'ouvre aussitôt, prêt à recevoir son référentiel)">+ Niveau</button>
        </div>
      </td>
    </tr>
  )
}

// ── Champ « + Matière » d'un niveau — SA cartouche, SON état. N'apparaît que si le niveau a un
// référentiel : la matière créée y entre, au programme d'emblée (l'admin qui la saisit la retient
// par ce geste même). ──
function AjoutMatiereRow({ referentielId, niveauNom, busy, onCreer }) {
  const [nom, setNom] = useState('')

  async function creer() {
    const ok = await onCreer(referentielId, nom)
    if (ok) setNom('')
  }

  return (
    <div style={{ display: 'flex', gap: 6, marginTop: 10, maxWidth: 420 }}>
      <input
        style={CHAMP_AJOUT} value={nom} disabled={busy}
        placeholder="Nom de la matière…"
        title={`Nom d'une matière à ajouter au programme de ${niveauNom}, tel qu'il figure dans son référentiel`}
        onChange={e => setNom(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') creer() }}
      />
      <button type="button" style={btnAjout(busy)} onClick={creer} disabled={busy}
        title="Ajouter cette matière au référentiel de ce niveau (au programme d'emblée)">+ Matière</button>
    </div>
  )
}

function CycleBloc({ cycle, busy, nivOuverts, typesOuverts, basculerNiveau, basculerType,
                     onCreerNiveau, onCreerMatiere, onToggleMatiere, onToggleLangue,
                     promptOuvert, promptLecture, onVoirPrompt }) {
  return (
    <>
      {/* ─ Ligne CYCLE ─ */}
      <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
        <td colSpan={2} style={{ padding: '10px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontWeight: 700, color: '#1e293b', fontSize: 13.5 }}>{cycle.nom}</span>
            <span style={{ fontSize: 11, color: '#94a3b8' }}>
              {cycle.niveaux.length} niveau{cycle.niveaux.length > 1 ? 'x' : ''}
            </span>
            {/* Le prompt des matières du cycle : il s'ouvre dans la COLONNE DE DROITE, comme le
                détail de toutes les pages listes. Le bouton dit le geste qu'il fait — « Voir »
                quand il est fermé, « Fermer » quand ce cycle est celui qui est affiché. */}
            <button
              type="button" onClick={() => onVoirPrompt(cycle)} disabled={promptLecture}
              title={promptOuvert
                ? 'Fermer le prompt des matières de ce cycle'
                : 'Voir, à droite, le prompt qui lit les matières des référentiels de ce cycle (lecture seule — il se règle dans Prompts → Matières par cycle)'}
              style={{
                marginLeft: 'auto', display: 'inline-flex', alignItems: 'center', gap: 6,
                whiteSpace: 'nowrap', fontSize: 12, fontWeight: 600, padding: '4px 10px',
                borderRadius: 6,
                background: promptOuvert ? '#eff6ff' : '#fff',
                color: promptOuvert ? '#1d4ed8' : '#334155',
                border: `1px solid ${promptOuvert ? '#bfdbfe' : '#cbd5e1'}`,
                cursor: promptLecture ? 'not-allowed' : 'pointer',
                opacity: promptLecture ? 0.6 : 1,
              }}
            >
              📝 {promptLecture ? 'Lecture…' : promptOuvert ? 'Fermer le prompt' : 'Voir le prompt'}
            </button>
          </div>
        </td>
      </tr>

      {cycle.niveaux.length === 0 && (
        <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
          <td colSpan={2} style={{ padding: '8px 16px 8px 40px', color: '#94a3b8', fontSize: 12.5 }}>
            Aucun niveau dans ce cycle.
          </td>
        </tr>
      )}

      {cycle.niveaux.map(niveau => (
        <NiveauBloc
          key={niveau.id}
          niveau={niveau}
          ref_={niveau.referentiel}
          ouvert={nivOuverts.has(niveau.id)}
          busy={busy}
          typesOuverts={typesOuverts}
          basculerNiveau={basculerNiveau}
          basculerType={basculerType}
          onCreerMatiere={onCreerMatiere}
          onToggleMatiere={onToggleMatiere}
          onToggleLangue={onToggleLangue}
        />
      ))}

      <AjoutNiveauRow cycle={cycle} busy={busy} onCreer={onCreerNiveau} />
    </>
  )
}

function NiveauBloc({ niveau, ref_, ouvert, busy, typesOuverts, basculerNiveau, basculerType,
                      onCreerMatiere, onToggleMatiere, onToggleLangue }) {
  // Les matières de CE niveau, telles que la base les rend, chacune avec son état.
  const matieres = lignesMatieres(niveau)
  const nbProgramme = nbAuProgramme(niveau)

  return (
    <>
      {/* ─ Ligne NIVEAU (cliquable) ─ */}
      <tr
        onClick={() => basculerNiveau(niveau.id)}
        style={{ borderBottom: '1px solid #f1f5f9', cursor: 'pointer', background: ouvert ? '#fcfdff' : 'white' }}
      >
        <td style={{ padding: '9px 16px 9px 28px', whiteSpace: 'nowrap' }}>
          {CHEVRON(ouvert)}
          <span style={{ fontWeight: 600, color: '#1e293b', marginLeft: 4 }}>{niveau.nom}</span>
        </td>
        <td style={{ padding: '9px 16px', textAlign: 'right' }}>
          {ref_ === null ? (
            <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, background: '#fef3c7', color: '#b45309', whiteSpace: 'nowrap' }}>
              vide — à remplir
            </span>
          ) : (
            <span style={{ display: 'inline-flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <Etat ok texte="PDF déposé" />
              <Etat ok={ref_.epure} texte={ref_.epure ? 'texte épuré' : 'épuré manquant'} />
              <Etat ok={ref_.decoupe_valide} texte={ref_.decoupe_valide ? 'découpe validée' : 'découpe en cours'} />
              <span style={{ fontSize: 11, color: '#64748b', alignSelf: 'center', whiteSpace: 'nowrap' }}>
                {ref_.nb_unites} unité{ref_.nb_unites > 1 ? 's' : ''} · {nbProgramme} matière{nbProgramme > 1 ? 's' : ''} · {niveau.types.length} type{niveau.types.length > 1 ? 's' : ''}
              </span>
            </span>
          )}
        </td>
      </tr>

      {/* ─ Détail du niveau (déplié) ─ */}
      {ouvert && (
        <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
          <td colSpan={2} style={{ padding: '4px 16px 14px 52px', background: '#fcfdff' }}>

            {/* Provenance du référentiel */}
            {ref_ !== null && (ref_.source || ref_.date_doc) && (
              <p style={{ margin: '8px 0 0', fontSize: 11.5, color: '#94a3b8' }}>
                {ref_.source ? <>Source : {ref_.source}</> : null}
                {ref_.source && ref_.date_doc ? ' · ' : null}
                {ref_.date_doc ? <>Document daté : {ref_.date_doc}</> : null}
              </p>
            )}

            {/* Matières du niveau : celles de SON référentiel, chacune avec son état. Aucune
                grille, aucun croisement — il n'y a plus de catalogue commun à croiser. */}
            <p style={{ margin: '12px 0 6px', fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Matières de ce niveau ({nbProgramme} au programme{matieres.length > nbProgramme ? ` · ${matieres.length - nbProgramme} de côté` : ''})
            </p>

            {niveau.referentiel_id == null ? (
              <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>
                Aucun référentiel déposé pour ce niveau : ses matières naissent du document, sur
                l'écran <b>Référentiel</b>. Tant qu'il n'a rien reçu, aucun prof ne peut choisir ce niveau.
              </p>
            ) : (
              <>
                {matieres.length === 0 ? (
                  <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>
                    Le référentiel est déposé mais aucune matière n'en a encore été retenue —
                    cela se fait sur l'écran <b>Référentiel</b>, ou en ajoutant la matière ici.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {matieres.map(m => {
                      const a = ALLURE_MATIERE[m.etat]
                      return (
                        <span
                          key={m.id}
                          title={m.etat === AU_PROGRAMME
                            ? `« ${m.nom} » est au programme de ${niveau.nom} : les profs de ce niveau la voient.`
                            : m.etat === DESACTIVEE
                              ? `« ${m.nom} » a été retirée du programme de ${niveau.nom} : elle reste en base, remettez-la quand vous voulez.`
                              : `« ${m.nom} » a été lue dans le document mais pas encore retenue : cela se fait sur l'écran Référentiel.`}
                          style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '3px 10px',
                                   borderRadius: 6, fontSize: 12, border: `1px solid ${a.bord}`,
                                   background: a.bg, color: a.fg }}
                        >
                          {m.nom}
                          {a.mention && <span style={{ fontSize: 10 }}>({a.mention})</span>}
                          {/* « Porte une langue » : c'est CE drapeau, et pas le libellé, qui fait
                              apparaître le choix de la langue au profil du prof et l'injecte dans
                              la génération. Une matière naît toujours à « non » — sans cette case,
                              plus aucune ne pourrait le porter. */}
                          {m.etat !== PROPOSEE && (
                            <label
                              title={m.demande_langue
                                ? `« ${m.nom} » porte une langue : ses profs choisissent laquelle à leur profil, et aSchool en tient compte à la génération. Décochez si ce n'est pas le cas.`
                                : `Cochez si « ${m.nom} » est une matière de langue (LV1, LV2, langue régionale…) : ses profs pourront alors choisir laquelle à leur profil.`}
                              style={{ display: 'inline-flex', alignItems: 'center', gap: 3, fontSize: 10,
                                       fontWeight: 600, color: m.demande_langue ? a.fg : '#94a3b8',
                                       cursor: busy ? 'wait' : 'pointer' }}
                            >
                              <input
                                type="checkbox"
                                checked={!!m.demande_langue}
                                disabled={busy}
                                onChange={() => onToggleLangue(m)}
                                style={{ width: 11, height: 11, cursor: busy ? 'wait' : 'pointer' }}
                              />
                              langue
                            </label>
                          )}
                          {m.etat !== PROPOSEE && (
                            <button
                              type="button"
                              disabled={busy}
                              onClick={() => onToggleMatiere(m, niveau.nom)}
                              title={m.actif
                                ? `Retirer « ${m.nom} » du programme de ${niveau.nom} (réversible)`
                                : `Remettre « ${m.nom} » au programme de ${niveau.nom} : elle réapparaît chez ses profs`}
                              style={{ border: 'none', background: 'none', padding: 0, fontSize: 11, fontWeight: 600,
                                       color: m.actif ? '#A63045' : '#16a34a', cursor: busy ? 'wait' : 'pointer' }}
                            >
                              {m.actif ? 'retirer' : 'remettre'}
                            </button>
                          )}
                        </span>
                      )
                    })}
                  </div>
                )}
                <AjoutMatiereRow
                  referentielId={niveau.referentiel_id}
                  niveauNom={niveau.nom}
                  busy={busy}
                  onCreer={onCreerMatiere}
                />
              </>
            )}

            {/* Types d'activité du couple */}
            <p style={{ margin: '14px 0 6px', fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Types d'activité ({niveau.types.length})
            </p>
            {ref_ === null ? (
              <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>Pas encore de référentiel : aucun type d'activité rattaché.</p>
            ) : niveau.types.length === 0 ? (
              <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>Aucun type d'activité rattaché à ce couple pour le moment.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {niveau.types.map(t => {
                  const cle = `${niveau.id}|${t.id}`
                  const tOuvert = typesOuverts.has(cle)
                  return (
                    <div key={t.id}>
                      <button
                        onClick={() => basculerType(cle)}
                        style={{
                          display: 'inline-flex', alignItems: 'center', cursor: 'pointer',
                          border: 'none', background: 'none', padding: '3px 0', fontSize: 12.5,
                          color: '#1e293b', textAlign: 'left',
                        }}
                      >
                        {CHEVRON(tOuvert)}
                        <span style={{ fontWeight: 500, marginLeft: 4 }}>{t.label}</span>
                        <BadgeType source={t.source} origine={t.origine} />
                        <span style={{ marginLeft: 8, fontSize: 11, color: '#94a3b8' }}>
                          {t.precisions.length} précision{t.precisions.length > 1 ? 's' : ''}
                        </span>
                      </button>
                      {tOuvert && (
                        t.precisions.length === 0 ? (
                          <p style={{ margin: '2px 0 4px 34px', fontSize: 12, color: '#94a3b8' }}>Aucune précision pour ce type d'activité sur ce couple.</p>
                        ) : (
                          <ul style={{ margin: '2px 0 4px 34px', padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 2 }}>
                            {t.precisions.map((p, i) => (
                              <li key={i} style={{ fontSize: 12, color: '#475569' }}>· {p}</li>
                            ))}
                          </ul>
                        )
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  )
}
