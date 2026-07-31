import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'
import { demanderConfirmation } from '../confirmDialog'
import SplitPane from '../components/SplitPane.jsx'

// Écran « Prompts » — sorti de Système → Génération LLM (31/07) : un prompt n'est pas de la
// plomberie (clés, modèles, délais) mais le texte qui décide de ce que le prof reçoit.
//
// UN SEUL fichier commun pour les trois sous-options (Prof / Admin / Autres) : elles montrent la
// même chose sur un jeu de prompts différent. La `categorie` arrive en prop depuis la route, qui
// pose aussi un `key` : changer de sous-option REMONTE le composant, donc chaque vue a bien SON
// état (rien de la vue précédente ne traîne).
//
// Deux colonnes, comme les pages listes de « Mes contenus » : la liste à gauche, le détail du
// prompt choisi à droite, la liste reste visible pendant qu'on travaille. Habillage admin, pas
// celui du prof. Le bouton « Cacher le détail » est permanent (règle maison).
const CATEGORIES = {
  prof: {
    titre: 'Prompts — Prof',
    intro: 'Les textes qui servent à l\'enseignant : séances et séquences, propositions, tons de rédaction, correction et contrôle qualité.',
  },
  admin: {
    titre: 'Prompts — Admin',
    intro: 'Les textes du traitement d\'un référentiel au dépôt du PDF : découpe en unités, analyse amont, détection du couple, des matières et des types d\'activité.',
  },
  autres: {
    titre: 'Prompts — Autres',
    intro: 'Le filet : ce qui ne sert ni au prof ni à l\'admin. Aujourd\'hui, des restes de l\'ancien monde démoli — plus aucun outil ne les demande. Ils sont rangés ici en attendant une décision.',
  },
}

export default function AdminPrompts({ categorie }) {
  // Prompts des outils (administrables en base). Liste depuis le backend ; un éditeur par prompt.
  const [prompts, setPrompts] = useState([])      // [{ key, label, placeholders, categorie, current, default, is_default }]
  const [promptKey, setPromptKey] = useState('')  // '' = rien de choisi (on ne présélectionne pas)
  const [promptText, setPromptText] = useState('')
  const [savingPrompt, setSavingPrompt] = useState(false)
  const [messagePrompt, setMessagePrompt] = useState(null)
  const [detailCache, setDetailCache] = useState(false)

  const meta = CATEGORIES[categorie] || CATEGORIES.autres

  useEffect(() => { loadPrompts() }, [])

  // Recharge la liste des prompts et réaffiche le texte courant de l'outil sélectionné
  // (réutilisé après Enregistrer / Revenir au défaut pour refléter l'état réel de la base).
  async function loadPrompts(selectKey) {
    try {
      const r = await fetch('/api/admin/prompts', { credentials: 'include' })
      const data = await r.json()
      const list = data.prompts || []
      setPrompts(list)
      const cle = selectKey || promptKey
      const actif = list.find(p => p.key === cle)
      setPromptKey(actif ? cle : '')
      setPromptText(actif ? actif.current : '')
    } catch { /* chargement best-effort : en cas d'échec réseau, on laisse la liste en l'état */ }
  }

  // Seuls les prompts de CETTE sous-option. La catégorie vient du registre serveur (llm_prompts).
  const liste = prompts.filter(p => p.categorie === categorie)

  // Prompt sélectionné + repères obligatoires manquants (miroir du garde-fou backend).
  // Un repère absent = injection cassée (matière/niveau/contenu non insérés) -> on refuse.
  const promptActif = liste.find(p => p.key === promptKey)
  const reperesManquants = promptActif
    ? promptActif.placeholders.filter(ph => !promptText.includes('{' + ph + '}'))
    : []
  const promptInvalide = !promptActif || promptText.trim() === '' || reperesManquants.length > 0
  const promptModifie = promptActif && promptText !== promptActif.current

  function choisirPrompt(key) {
    setPromptKey(key)
    const actif = liste.find(p => p.key === key)
    setPromptText(actif ? actif.current : '')
    setMessagePrompt(null)
    setDetailCache(false)   // cliquer une ligne veut dire « montre-moi le détail »
  }

  async function savePrompt() {
    // Incohérence -> modale bloquante (jamais inline) ; bouton déjà désactivé. Le 400 backend
    // reste un filet (accolades mal équilibrées que le front ne détecte pas).
    if (promptInvalide) {
      showError(
        promptText.trim() === ''
          ? 'Le prompt ne peut pas être vide.'
          : `Repère(s) obligatoire(s) manquant(s) : ${reperesManquants.map(p => '{' + p + '}').join(', ')}. ` +
            `Remettez-les tels quels dans le texte avant d'enregistrer : sans eux, la matière, le niveau ou ` +
            `le contenu de l'enseignant ne seraient pas injectés dans la demande envoyée à l'IA.`
      )
      return
    }
    setSavingPrompt(true)
    setMessagePrompt(null)
    try {
      const res = await fetchWithTimeout('/api/admin/prompts', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ key: promptKey, text: promptText }),
      }, TIMEOUT_STD)
      const data = await res.json().catch(() => ({}))
      if (res.ok) {
        setMessagePrompt({ type: 'warn', text: 'Prompt modifié.' })
        await loadPrompts(promptKey)
      } else {
        showError(data.detail || 'Erreur lors de l\'enregistrement du prompt.')
      }
    } catch {
      showError('Erreur réseau — vérifiez que le backend tourne.')
    } finally {
      setSavingPrompt(false)
    }
  }

  async function resetPrompt() {
    if (!promptActif) return
    if (!await demanderConfirmation({
      titre: `Revenir au prompt par défaut pour « ${promptActif.label} » ?`,
      message: 'Votre version personnalisée sera définitivement supprimée.',
      confirmLabel: 'Revenir au défaut',
      danger: true,
    })) return
    setSavingPrompt(true)
    setMessagePrompt(null)
    try {
      const res = await fetchWithTimeout(`/api/admin/prompts/${promptKey}`, {
        method: 'DELETE',
        credentials: 'include',
      }, TIMEOUT_STD)
      const data = await res.json().catch(() => ({}))
      if (res.ok) {
        setMessagePrompt({ type: 'ok', text: 'Prompt remis au défaut.' })
        await loadPrompts(promptKey)
      } else {
        showError(data.detail || 'Erreur lors du retour au défaut.')
      }
    } catch {
      showError('Erreur réseau — vérifiez que le backend tourne.')
    } finally {
      setSavingPrompt(false)
    }
  }

  // ── Colonne gauche : la liste. Une ligne = un prompt, avec son étiquette d'état. ──
  const colonneListe = (
    <div className="bg-white rounded-lg border border-gray-200" style={{ overflow: 'hidden' }}>
      {liste.length === 0 && (
        <p className="text-sm text-gray-400" style={{ padding: '24px 16px', textAlign: 'center' }}>
          Aucun prompt dans cette catégorie.
        </p>
      )}
      {liste.map(p => {
        const active = p.key === promptKey
        return (
          <button
            key={p.key}
            onClick={() => choisirPrompt(p.key)}
            title={p.label}
            style={{
              display: 'block', width: '100%', textAlign: 'left',
              padding: '10px 14px', cursor: 'pointer',
              border: 'none', borderBottom: '1px solid #f1f5f9',
              borderLeft: active ? '3px solid #A63045' : '3px solid transparent',
              background: active ? '#fdf2f4' : 'white',
            }}
          >
            <span style={{
              display: 'flex', alignItems: 'baseline', gap: 8, fontSize: 13,
              color: active ? '#A63045' : '#374151', fontWeight: active ? 600 : 400,
            }}>
              <span style={{ flex: 1, minWidth: 0 }}>{p.label}</span>
              {!p.is_default && (
                <span style={{
                  flexShrink: 0, fontSize: 10, padding: '1px 7px', borderRadius: 5,
                  background: '#eff6ff', color: '#1558C0', border: '1px solid #bfdbfe',
                }}>
                  Personnalisé
                </span>
              )}
            </span>
            <span style={{
              display: 'block', marginTop: 3, fontSize: 11, color: '#94a3b8',
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
            }}>
              {p.key}
            </span>
          </button>
        )
      })}
    </div>
  )

  // ── Colonne droite : le détail du prompt choisi (ce qui existait dans l'onglet). Les repères
  //    {…} obligatoires DOIVENT rester (sinon matière/niveau/contenu non injectés) -> bord rouge
  //    + modale + bouton off. Le 400 backend reste un filet (accolades). « Revenir au défaut »
  //    efface vraiment la surcharge en base. Le catalogue d'activités N'EST PAS ici. ──
  const colonneDetail = !promptActif ? (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <p className="text-sm text-gray-500">Choisissez un prompt dans la liste pour l'ouvrir ici.</p>
      <p className="text-xs text-gray-400 mt-2">
        Les repères <code>{'{…}'}</code> entre accolades sont remplacés à l'exécution (matière, niveau,
        contenu de l'enseignant…) : ils sont obligatoires et doivent rester tels quels. Toute
        modification est prise en compte immédiatement, sans redémarrage.
      </p>
    </div>
  ) : (
    <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">
      <div>
        <h3 className="text-sm font-semibold text-gray-700">{promptActif.label}</h3>
        <p className="text-xs text-gray-400 mt-1" style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
          {promptActif.key}
        </p>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs font-medium text-gray-600">Repères obligatoires :</span>
        {promptActif.placeholders.length === 0 && (
          <span className="text-xs text-gray-400">aucun pour ce prompt</span>
        )}
        {promptActif.placeholders.map(ph => {
          const manquant = reperesManquants.includes(ph)
          return (
            <code
              key={ph}
              title={manquant ? 'Repère manquant — à remettre dans le texte' : 'Présent dans le texte'}
              style={{
                fontSize: 12, padding: '2px 7px', borderRadius: 5,
                background: manquant ? '#fef2f2' : '#f0fdf4',
                color: manquant ? '#dc2626' : '#166534',
                border: `1px solid ${manquant ? '#fecaca' : '#bbf7d0'}`,
              }}
            >
              {'{' + ph + '}'}
            </code>
          )
        })}
        <span style={{
          marginLeft: 'auto', fontSize: 11, padding: '2px 8px', borderRadius: 5,
          background: promptActif.is_default ? '#f3f4f6' : '#eff6ff',
          color: promptActif.is_default ? '#6b7280' : '#1558C0',
          border: `1px solid ${promptActif.is_default ? '#e5e7eb' : '#bfdbfe'}`,
        }}>
          {promptActif.is_default ? 'Par défaut' : 'Personnalisé'}
        </span>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Prompt</label>
        <textarea
          value={promptText}
          onChange={e => setPromptText(e.target.value)}
          rows={18}
          spellCheck={false}
          className="w-full border rounded px-3 py-2"
          style={{
            borderColor: promptInvalide ? '#dc2626' : '#d1d5db',
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
            fontSize: 12, lineHeight: 1.5, resize: 'vertical',
          }}
        />
        <p className="text-xs text-gray-400 mt-1">
          Dans un exemple JSON, doublez les accolades : <code>{'{{ }}'}</code> — sinon le repère
          serait interprété et le prompt refusé.
        </p>
      </div>

      <div className="flex items-center gap-3 pt-1 flex-wrap">
        <button
          onClick={savePrompt}
          disabled={savingPrompt || promptInvalide || !promptModifie}
          title="Enregistrer ce prompt"
          style={{
            background: '#1F6EEB', color: 'white', border: 'none',
            borderRadius: 7, padding: '8px 20px', fontSize: 13, fontWeight: 500,
            cursor: (savingPrompt || promptInvalide || !promptModifie) ? 'not-allowed' : 'pointer',
            opacity: (savingPrompt || promptInvalide || !promptModifie) ? 0.6 : 1,
          }}
        >
          {savingPrompt ? 'Enregistrement…' : 'Enregistrer le prompt'}
        </button>
        <button
          onClick={resetPrompt}
          disabled={savingPrompt || promptActif.is_default}
          title="Supprimer la version personnalisée et revenir au prompt par défaut"
          style={{
            background: 'white', color: '#6b7280', border: '1px solid #e5e7eb',
            borderRadius: 7, padding: '8px 20px', fontSize: 13, fontWeight: 500,
            cursor: (savingPrompt || promptActif.is_default) ? 'not-allowed' : 'pointer',
            opacity: (savingPrompt || promptActif.is_default) ? 0.6 : 1,
          }}
        >
          Revenir au défaut
        </button>
        {messagePrompt && (
          <div style={{
            background: messagePrompt.type === 'warn' ? '#fef2f2' : '#f0fdf4',
            border: `1px solid ${messagePrompt.type === 'warn' ? '#fecaca' : '#bbf7d0'}`,
            color: messagePrompt.type === 'warn' ? '#dc2626' : '#166534',
            borderRadius: 8, padding: '10px 14px', fontSize: 13,
          }}>
            {messagePrompt.text}
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className="flex flex-col gap-4">

      {/* En-tête : titre + compteur à gauche ; « Cacher le détail » tout à droite, au-dessus de
          la liste — permanent sur les pages listes (règle maison, il ne se retire jamais). */}
      <div className="flex items-start gap-3" style={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <h2 className="text-sm font-semibold text-gray-700 mb-1">
            {meta.titre}
            {liste.length > 0 && (
              <span style={{
                marginLeft: 8, fontSize: 11, fontWeight: 600, padding: '1px 8px', borderRadius: 99,
                background: '#f3f4f6', color: '#6b7280', border: '1px solid #e5e7eb',
              }}>
                {liste.length} prompt{liste.length > 1 ? 's' : ''}
              </span>
            )}
          </h2>
          <p className="text-xs text-gray-400">{meta.intro}</p>
        </div>
        <button
          onClick={() => setDetailCache(c => !c)}
          title={detailCache
            ? 'Réafficher la colonne de détail à droite'
            : 'Cacher la colonne de détail — la liste prend toute la largeur'}
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

      {/* Deux colonnes redimensionnables : liste à gauche | détail à droite. Détail caché :
          la liste prend toute la largeur (le même SplitPane que les pages listes du prof). */}
      {detailCache
        ? <div className="split-pane"><div className="split-col split-col-flex">{colonneListe}</div></div>
        : <SplitPane
            storageKey={`admin-prompts-${categorie}-split-v1`}
            defautGauche={38}
            gauche={colonneListe}
            droite={colonneDetail}
          />}
    </div>
  )
}
