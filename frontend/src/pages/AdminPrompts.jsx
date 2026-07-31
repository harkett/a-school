import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'
import { demanderConfirmation } from '../confirmDialog'

// Page « Prompts » — sortie de Système → Génération LLM (31/07) : un prompt n'est pas de la
// plomberie (clés, modèles, délais) mais du contenu pédagogique — c'est le texte qui décide de
// ce que le prof reçoit. Sa place est à côté des référentiels et des types d'activité.
// Un composant par vue avec SON état : rien ici n'est partagé avec les réglages du moteur.
export default function AdminPrompts() {
  // Prompts des outils (administrables en base). Liste depuis le backend ; un éditeur par prompt.
  const [prompts, setPrompts] = useState([])      // [{ key, label, placeholders, current, default, is_default }]
  const [promptKey, setPromptKey] = useState('')
  const [promptText, setPromptText] = useState('')
  const [savingPrompt, setSavingPrompt] = useState(false)
  const [messagePrompt, setMessagePrompt] = useState(null)

  useEffect(() => { loadPrompts() }, [])

  // Recharge la liste des prompts et réaffiche le texte courant de l'outil sélectionné
  // (réutilisé après Enregistrer / Revenir au défaut pour refléter l'état réel de la base).
  async function loadPrompts(selectKey) {
    try {
      const r = await fetch('/api/admin/prompts', { credentials: 'include' })
      const data = await r.json()
      const list = data.prompts || []
      setPrompts(list)
      const cle = selectKey || promptKey || (list[0] ? list[0].key : '')
      const actif = list.find(p => p.key === cle)
      setPromptKey(cle)
      setPromptText(actif ? actif.current : '')
    } catch { /* chargement best-effort : en cas d'échec réseau, on laisse la liste en l'état */ }
  }

  // Prompt sélectionné + repères obligatoires manquants (miroir du garde-fou backend).
  // Un repère absent = injection cassée (matière/niveau/contenu non insérés) -> on refuse.
  const promptActif = prompts.find(p => p.key === promptKey)
  const reperesManquants = promptActif
    ? promptActif.placeholders.filter(ph => !promptText.includes('{' + ph + '}'))
    : []
  const promptInvalide = !promptActif || promptText.trim() === '' || reperesManquants.length > 0
  const promptModifie = promptActif && promptText !== promptActif.current

  function choisirPrompt(key) {
    setPromptKey(key)
    const actif = prompts.find(p => p.key === key)
    setPromptText(actif ? actif.current : '')
    setMessagePrompt(null)
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

  return (
    <div className="flex flex-col gap-6">

      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-1">Prompts</h2>
        <p className="text-xs text-gray-400">
          Les textes d'instruction envoyés à l'IA pour chaque outil — ce qui décide de ce que
          l'enseignant reçoit.
        </p>
      </div>

      {/* Texte exact envoyé à l'IA pour chaque outil. L'admin édite ; les repères {…} obligatoires
          DOIVENT rester (sinon matière/niveau/contenu non injectés) -> bord rouge + modale + bouton
          off. Le 400 backend reste un filet (accolades). « Revenir au défaut » efface vraiment la
          surcharge en base. Le catalogue d'activités N'EST PAS ici. */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">
        <p className="text-xs text-gray-500">
          Texte d'instruction envoyé à l'IA pour chaque outil. Les repères <code>{'{…}'}</code> entre
          accolades sont remplacés à l'exécution (matière, niveau, contenu de l'enseignant…) : ils sont
          obligatoires et doivent rester tels quels. Pris en compte immédiatement, sans redémarrage.
        </p>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Outil</label>
          <select
            value={promptKey}
            onChange={e => choisirPrompt(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          >
            {prompts.length === 0 && <option value="">Chargement…</option>}
            {prompts.map(p => (
              <option key={p.key} value={p.key}>{p.label}</option>
            ))}
          </select>
        </div>

        {promptActif && (
          <>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-medium text-gray-600">Repères obligatoires :</span>
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
          </>
        )}
      </div>
    </div>
  )
}
