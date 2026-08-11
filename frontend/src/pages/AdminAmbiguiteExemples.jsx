// Page « Exemples → Ambiguïté » — les énoncés d'exemple de l'écran prof « Détecter les ambiguïtés ».
//
// Un exemple par couple, écrit d'avance et rangé en base. L'application ne le génère JAMAIS :
// l'écran donne le prompt rempli pour un couple, l'admin l'exécute chez lui, et recolle la
// réponse d'un bloc — le serveur la découpe sur les deux marqueurs du prompt. Zéro appel payé
// par l'application, et le prof retrouve le même énoncé à chaque fois.
//
// Deux colonnes, comme les autres écrans admin : la liste des couples à gauche, le détail du
// couple choisi à droite. La liste montre TOUS les couples, y compris ceux sans exemple — c'est
// elle qui dit le travail restant.
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'
import SplitPane from '../components/SplitPane.jsx'

// Norme maison : même hauteur pour tous, curseur interdit quand c'est grisé, une couleur par
// geste (valider bleu, annuler rouge, ajouter vert, IA violet), une bulle d'aide sur chacun.
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
const btnNeutre  = btn('#fff', '#cbd5e1', '#334155')
const btnIA      = btn('#7c3aed', '#6d28d9', '#fff')

const IconPrompt = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 17l6-6-6-6" /><path d="M12 19h8" />
  </svg>
)
const IconOk = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 6L9 17l-5-5" />
  </svg>
)
const IconAnnuler = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
  </svg>
)
const IconOeil = ({ barre }) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" /><circle cx="12" cy="12" r="3" />
    {barre && <line x1="3" y1="21" x2="21" y2="3" />}
  </svg>
)

const IconCrayon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" />
  </svg>
)

// Les deux champs d'un exemple, décrits UNE fois : l'écran les rend en boucle, il n'y a donc pas
// deux blocs jumeaux à tenir d'accord à la main.
const ZONES = [
  { cle: 'texte', titre: 'Exemple vu par le prof',
    aide: 'Le texte exact que le professeur reçoit en cliquant « Utiliser un exemple »',
    vide: "L'énoncé que le professeur recevra. Écrivez-le, ou collez ici la réponse entière de votre agent." },
  { cle: 'defauts', titre: 'Défauts glissés',
    aide: "Ce qui a été mis volontairement dans l'énoncé — le professeur ne le voit jamais",
    vide: "Une ligne par défaut. Cette liste ne sort pas de cet écran : elle sert à vérifier ce que l'outil retrouve." },
]

// L'état d'un exemple, tel qu'il se lit d'un coup d'œil. TROIS, et non deux : « désactivé » n'est
// ni écrit ni manquant — le texte existe, c'est le professeur qui ne le reçoit plus.
const etatDe = (l) => (!l.texte.trim() ? 'manquant' : l.actif ? 'écrit' : 'désactivé')

const COULEURS = {
  'écrit':      { fond: '#ecfdf5', texte: '#065f46', bord: '#a7f3d0' },
  'désactivé':  { fond: '#fffbeb', texte: '#92400e', bord: '#fde68a' },
  'manquant':   { fond: '#fef2f2', texte: '#b91c1c', bord: '#fecaca' },
}

const pastille = (etat) => ({
  flexShrink: 0, fontSize: 10, fontWeight: 700, padding: '1px 7px', borderRadius: 5,
  background: COULEURS[etat].fond,
  color: COULEURS[etat].texte,
  border: '1px solid ' + COULEURS[etat].bord,
})

export default function AdminAmbiguiteExemples() {
  const qc = useQueryClient()
  const [choisi, setChoisi] = useState(null)      // matiere_id de la ligne ouverte à droite
  // L'exemple s'écrit LÀ OÙ IL SE LIT. Il y avait avant deux zones pour le même texte : celle du
  // haut le montrait sans qu'on puisse y toucher, celle du bas était le seul endroit où agir —
  // et dès qu'on y collait quelque chose, le haut affichait un texte périmé à l'identique. Rien
  // ne disait lequel faisait foi.
  const [brouillon, setBrouillon] = useState(null)   // { texte, defauts } en cours d'édition
  // Chaque zone est VERROUILLÉE tant qu'on n'a pas dit qu'on voulait la changer. Sans ce cran,
  // un clic malheureux dans un texte de 900 caractères l'écrase sans que rien ne le signale.
  const [ouvertes, setOuvertes] = useState({ texte: false, defauts: false })
  const [prompt, setPrompt] = useState(null)      // { matiere, niveau, prompt } de la fenêtre
  const [busy, setBusy] = useState(false)
  const [recherche, setRecherche] = useState('')

  const { data: lignes = [], error } = useQuery({
    queryKey: ['admin', 'ambiguite-exemples'],
    queryFn: async () => await lireReponse(
      await apiFetch('/api/admin/ambiguite-exemples', { credentials: 'include' }, TIMEOUT_STD)),
  })
  if (error) showError(messagePourEcran(error))

  // On compte ce que le PROFESSEUR reçoit : un exemple éteint ne fait pas avancer le compte,
  // sinon le compteur annoncerait un travail que personne ne voit.
  const ecrits = lignes.filter(l => l.texte.trim() && l.actif).length

  // Le travail se fait référentiel par référentiel : le total seul ne dit pas lequel attaquer.
  // L'ordre des niveaux est celui du serveur — on ne le retrie pas ici.
  const groupes = []
  for (const l of lignes) {
    let g = groupes.find(x => x.niveau === l.niveau)
    if (!g) { g = { niveau: l.niveau, lignes: [] }; groupes.push(g) }
    g.lignes.push(l)
  }

  const q = recherche.trim().toLowerCase()
  const groupesVus = !q ? groupes : groupes
    .map(g => ({ ...g, lignes: g.lignes.filter(l => (l.matiere + ' ' + l.niveau).toLowerCase().includes(q)) }))
    .filter(g => g.lignes.length > 0)

  // La ligne ouverte est un CALCUL : un couple disparu de la liste n'est plus sélectionné.
  const ligneActive = lignes.find(l => l.matiere_id === choisi) || null

  function ouvrir(l) {
    setChoisi(l.matiere_id)
    setBrouillon({ texte: l.texte, defauts: l.defauts })
    setOuvertes({ texte: false, defauts: false })   // on ouvre pour lire, pas pour écrire
  }

  async function voirPrompt(l) {
    try {
      setPrompt(await lireReponse(await apiFetch(
        `/api/admin/ambiguite-exemples/${l.matiere_id}/prompt`, { credentials: 'include' }, TIMEOUT_STD)))
    } catch (e) { showError(messagePourEcran(e)) }
  }

  async function enregistrer(l) {
    if (!brouillon || !brouillon.texte.trim()) return
    setBusy(true)
    // Coller la réponse entière d'un agent DANS le champ de l'énoncé reste le geste le plus
    // naturel : quand le texte porte les marqueurs du prompt, le serveur le découpe lui-même et
    // range chaque bloc à sa place. Sinon, les deux champs partent tels qu'ils sont écrits.
    const brut = brouillon.texte.includes('=== ENONCE ===')
    const url = `/api/admin/ambiguite-exemples/${l.matiere_id}${brut ? '/coller' : ''}`
    try {
      const enregistre = await lireReponse(await apiFetch(url, {
        method: brut ? 'POST' : 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(brut ? { brut: brouillon.texte }
                                  : { texte: brouillon.texte, defauts: brouillon.defauts }),
      }, TIMEOUT_STD))
      setBrouillon({ texte: enregistre.texte, defauts: enregistre.defauts })
      setOuvertes({ texte: false, defauts: false })   // enregistré = reverrouillé
      qc.invalidateQueries({ queryKey: ['admin', 'ambiguite-exemples'] })
    } catch (e) { showError(messagePourEcran(e)) } finally { setBusy(false) }
  }

  // Éteindre plutôt que supprimer : le professeur cesse de voir l'exemple, et le texte reste sous
  // la main pour être corrigé. Supprimer faisait perdre ce qu'il fallait justement reprendre.
  // Aucune confirmation : rien n'est perdu, et le même bouton défait ce qu'il vient de faire.
  async function basculer(l) {
    setBusy(true)
    try {
      await lireReponse(await apiFetch(`/api/admin/ambiguite-exemples/${l.matiere_id}/actif`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ actif: !l.actif }),
      }, TIMEOUT_STD))
      qc.invalidateQueries({ queryKey: ['admin', 'ambiguite-exemples'] })
    } catch (e) { showError(messagePourEcran(e)) } finally { setBusy(false) }
  }

  // Changé = le brouillon ne dit plus la même chose que ce qui est en base. Calculé à la
  // demande : un drapeau « sale » gardé à côté finit toujours par mentir.
  const modifie = (cle) => !!(ligneActive && brouillon && brouillon[cle] !== ligneActive[cle])

  // ── Colonne gauche : le menu des couples, groupés par référentiel ──────────────────────
  const colonneListe = (
    <div className="bg-white rounded-lg border border-gray-200"
         style={{ overflow: 'hidden', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: 10, borderBottom: '1px solid #f1f5f9', flexShrink: 0 }}>
        <input
          type="search"
          value={recherche}
          onChange={e => setRecherche(e.target.value)}
          placeholder="Rechercher une matière…"
          title="Filtre la liste au fil de la frappe — cherche dans la matière et dans le niveau"
          className="w-full border border-gray-300 rounded text-sm"
          style={{ padding: '7px 10px' }}
        />
      </div>

      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
        {lignes.length === 0 && (
          <p className="text-sm text-gray-400" style={{ padding: '24px 16px', textAlign: 'center' }}>
            Aucun couple en base — déposez d'abord un référentiel.
          </p>
        )}
        {lignes.length > 0 && groupesVus.length === 0 && (
          <p className="text-sm text-gray-400" style={{ padding: '24px 16px', textAlign: 'center' }}>
            Aucune matière ne correspond à « {recherche.trim()} ».
          </p>
        )}

        {groupesVus.map(g => {
          const n = g.lignes.filter(l => l.texte.trim() && l.actif).length
          return (
            <div key={g.niveau}>
              <div style={{
                padding: '7px 14px', background: '#f8fafc',
                borderTop: '1px solid #e2e8f0', borderBottom: '1px solid #e2e8f0',
                fontSize: 12, fontWeight: 700, color: '#475569',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8,
                position: 'sticky', top: 0, zIndex: 1,
              }}>
                <span>{g.niveau}</span>
                <span style={{ fontWeight: 600, color: '#94a3b8', flexShrink: 0 }}>
                  {n}/{g.lignes.length}
                </span>
              </div>

              {g.lignes.map(l => {
                const active = l.matiere_id === choisi
                const etat = etatDe(l)
                return (
                  <button
                    key={l.matiere_id}
                    type="button"
                    onClick={() => ouvrir(l)}
                    title={`${l.matiere} · ${l.niveau}`}
                    style={{
                      display: 'block', width: '100%', textAlign: 'left',
                      padding: '10px 14px', cursor: 'pointer',
                      border: 'none', borderBottom: '1px solid #f1f5f9',
                      borderLeft: active ? '3px solid #A63045' : '3px solid transparent',
                      background: active ? '#fdf2f4' : 'white',
                    }}
                  >
                    <span style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                      {/* Le nom COMPLET, sur plusieurs lignes s'il le faut : les intitulés
                          officiels sont longs et deux matières d'un même BTS ne se
                          distinguent parfois que par leur fin. */}
                      <span style={{
                        flex: 1, minWidth: 0, fontSize: 13, lineHeight: 1.4,
                        color: active ? '#A63045' : '#374151', fontWeight: active ? 600 : 400,
                      }}>
                        {l.matiere}
                      </span>
                      <span style={pastille(etat)}>{etat}</span>
                    </span>
                    <span style={{ display: 'block', marginTop: 3, fontSize: 11, color: '#94a3b8' }}>
                      {l.niveau}
                    </span>
                  </button>
                )
              })}
            </div>
          )
        })}
      </div>
    </div>
  )

  // ── Colonne droite : le couple choisi ──────────────────────────────────────────────────
  const colonneDetail = !ligneActive ? (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <p className="text-sm text-gray-500">Choisissez une matière dans la liste pour l'ouvrir ici.</p>
      <p className="text-xs text-gray-400 mt-2">
        Vous y verrez l'exemple tel que le professeur le reçoit, et ce qui a été glissé dedans.
        « Modifier » déverrouille la zone à corriger ; le reste du référentiel se traite d'un coup
        depuis sa cartouche « Ambiguïtés », dans Référentiels.
      </p>
    </div>
  ) : (
    <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5"
         style={{ height: '100%', minHeight: 420 }}>
      <div style={{ flexShrink: 0, display: 'flex', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 className="text-sm font-semibold text-gray-700">{ligneActive.matiere}</h3>
          <p className="text-xs text-gray-400 mt-1">{ligneActive.niveau}</p>
        </div>
        <span style={pastille(etatDe(ligneActive))}>{etatDe(ligneActive)}</span>
      </div>

      <div className="flex items-center gap-2 flex-wrap" style={{ flexShrink: 0 }}>
        <button type="button" onClick={() => voirPrompt(ligneActive)} style={btnIA(false)}
          title="Le prompt qui ÉCRIT l'énoncé d'exemple de cette matière — il n'analyse rien. Prêt à copier, à exécuter hors de l'application">
          <IconPrompt />Le prompt
        </button>
        <button type="button" onClick={() => basculer(ligneActive)}
          disabled={busy || !ligneActive.texte.trim()}
          style={(ligneActive.actif ? btnAnnuler : btnValider)(busy || !ligneActive.texte.trim())}
          title={!ligneActive.texte.trim() ? 'Ce couple n\'a pas d\'exemple'
            : ligneActive.actif
              ? 'Retirer cet exemple de l\'écran du prof — le texte reste ici'
              : 'Le rendre à nouveau visible par le prof'}>
          <IconOeil barre={ligneActive.actif} />
          {ligneActive.actif ? 'Désactiver' : 'Réactiver'}
        </button>
      </div>

      {/* UNE seule place pour chaque chose : l'exemple s'écrit LÀ OÙ IL SE LIT. Il y avait avant
          une troisième zone, vide, en bas — le seul endroit où l'on pouvait agir, pendant que le
          haut continuait d'afficher l'ancien texte à l'identique. Rien ne disait lequel faisait
          foi. Chaque cadre porte donc son propre bouton : « Modifier » déverrouille, et il devient
          « Enregistrer » dès qu'on a changé quelque chose. */}
      <div className="grid gap-3" style={{ flex: 1, minHeight: 0, gridTemplateColumns: '1fr 1fr' }}>
        {ZONES.map(z => {
          const ouverte = ouvertes[z.cle]
          const change = modifie(z.cle)
          return (
            <div key={z.cle} className="flex flex-col" style={{ minHeight: 0 }}>
              <div className="flex items-center gap-2 mb-1" style={{ flexShrink: 0 }}>
                <div className="text-xs font-semibold text-gray-600" title={z.aide}>{z.titre}</div>
                <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                  {ouverte && (
                    <button type="button" style={btnAnnuler(busy)} disabled={busy}
                      title="Revenir au texte enregistré et refermer la zone"
                      onClick={() => {
                        setBrouillon(b => ({ ...b, [z.cle]: ligneActive[z.cle] }))
                        setOuvertes(o => ({ ...o, [z.cle]: false }))
                      }}>
                      <IconAnnuler />Annuler
                    </button>
                  )}
                  {!ouverte ? (
                    <button type="button" style={btnNeutre(false)}
                      title={`Déverrouiller « ${z.titre} » pour le corriger`}
                      onClick={() => setOuvertes(o => ({ ...o, [z.cle]: true }))}>
                      <IconCrayon />Modifier
                    </button>
                  ) : (
                    <button type="button" onClick={() => enregistrer(ligneActive)}
                      disabled={busy || !change || !(brouillon && brouillon.texte.trim())}
                      style={btnValider(busy || !change || !(brouillon && brouillon.texte.trim()))}
                      title={!(brouillon && brouillon.texte.trim()) ? 'L\'exemple ne peut pas être vide'
                        : !change ? 'Rien n\'a changé' : 'Enregistrer — c\'est ce que le professeur recevra'}>
                      <IconOk />{busy ? 'Enregistrement…' : 'Enregistrer'}
                    </button>
                  )}
                </div>
              </div>
              <textarea
                value={brouillon ? brouillon[z.cle] : ''}
                readOnly={!ouverte}
                onChange={e => setBrouillon(b => ({ ...b, [z.cle]: e.target.value }))}
                placeholder={z.vide}
                className="w-full text-xs border rounded p-2"
                style={{ flex: 1, minHeight: 220, fontFamily: 'inherit', lineHeight: 1.5, resize: 'none',
                         background: ouverte ? '#fff' : '#f8fafc',
                         borderColor: ouverte ? '#94a3b8' : '#e2e8f0',
                         color: ouverte ? '#1e293b' : '#475569',
                         cursor: ouverte ? 'text' : 'default' }}
              />
            </div>
          )
        })}
      </div>

      <p className="text-xs text-gray-400" style={{ flexShrink: 0, margin: 0 }}>
        Vous pouvez coller la réponse entière de votre agent dans l'exemple, marqueurs compris :
        le serveur sépare alors l'énoncé des défauts.
      </p>
    </div>
  )

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-800">Exemples d'énoncés — Détecter les ambiguïtés</h2>
        <p className="text-sm text-gray-500 mt-1">
          Chaque couple a son énoncé d'exemple : un vrai sujet de la matière, au niveau, avec des défauts
          glissés dedans. Le prof le charge d'un clic pour découvrir l'outil. L'application ne le génère
          jamais — vous exécutez le prompt de votre côté et vous recollez la réponse ici.
        </p>

        <div className="flex items-center gap-2 flex-wrap mt-3">
          <span
            title="Tous référentiels confondus"
            style={{
              fontSize: 12, fontWeight: 700, padding: '3px 10px', borderRadius: 6,
              background: ecrits === lignes.length && lignes.length > 0 ? '#ecfdf5' : '#f1f5f9',
              color: ecrits === lignes.length && lignes.length > 0 ? '#065f46' : '#475569',
              border: '1px solid ' + (ecrits === lignes.length && lignes.length > 0 ? '#a7f3d0' : '#e2e8f0'),
            }}
          >
            {ecrits} / {lignes.length} au total
          </span>
          {groupes.map(g => {
            const n = g.lignes.filter(l => l.texte.trim() && l.actif).length
            const complet = n === g.lignes.length
            return (
              <span
                key={g.niveau}
                title={`${g.niveau} — ${n} exemple(s) écrit(s) sur ${g.lignes.length} matière(s)`}
                style={{
                  fontSize: 11.5, padding: '3px 9px', borderRadius: 6,
                  background: complet ? '#ecfdf5' : '#fff',
                  color: complet ? '#065f46' : '#64748b',
                  border: '1px solid ' + (complet ? '#a7f3d0' : '#e2e8f0'),
                }}
              >
                {g.niveau} <b>{n}/{g.lignes.length}</b>
              </span>
            )
          })}
        </div>
      </div>

      <div className="admin-prompts-corps">
        <SplitPane
          storageKey="admin-exemples-ambiguites-split-v1"
          defautGauche={34}
          gauche={colonneListe}
          droite={colonneDetail}
        />
      </div>

      {/* Le prompt du couple, à sélectionner puis copier — même geste que les fenêtres de
          l'écran Référentiel. */}
      {prompt && (
        <div onClick={() => setPrompt(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
                   display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '80vh',
                     display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                          padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                Prompt — {prompt.matiere} · {prompt.niveau}
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
                <button type="button" style={btnNeutre(false)}
                  title="Sélectionner tout le texte de cette fenêtre — il ne reste plus qu'à le copier (Ctrl+C)"
                  onClick={() => {
                    const n = document.getElementById('zone-prompt-exemple')
                    if (!n) return
                    const r = document.createRange(); r.selectNodeContents(n)
                    const s = window.getSelection(); s.removeAllRanges(); s.addRange(r)
                  }}>
                  Sélectionner tout
                </button>
                <button type="button" onClick={() => setPrompt(null)} title="Fermer"
                  style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
              </span>
            </div>
            {/* À QUOI SERT CE TEXTE, avant de le lire : sans cette ligne, rien ne disait si on
                tenait le prompt qui analyse l'énoncé du professeur ou celui qui écrit ses
                exemples. */}
            <div style={{ fontSize: 12.5, lineHeight: 1.6, color: '#334155', background: '#f8fafc',
              borderBottom: '1px solid #e2e8f0', padding: '9px 14px' }}>
              Ce texte <strong>n'analyse rien</strong> : il écrit l'énoncé d'exemple de cette matière,
              celui que le professeur charge par « Utiliser un exemple ». Le prompt qui analyse son
              énoncé est un autre — Admin → IA → Prompts → Autres fonctionnalités.
            </div>
            <pre id="zone-prompt-exemple"
              style={{ flex: 1, overflow: 'auto', margin: 0, padding: 14, fontSize: 12,
                       color: '#334155', whiteSpace: 'pre-wrap', background: '#f8fafc' }}>
              {prompt.prompt}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
