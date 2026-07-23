import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'

export default function AdminParametresGeneration() {
  const [onglet, setOnglet] = useState('modele')
  const [aiModel, setAiModel] = useState('')
  const [supportedModels, setSupportedModels] = useState([])
  const [recommandeModel, setRecommandeModel] = useState('') // modèle marqué « recommandé » (affiché entre parenthèses)
  const [saving, setSaving]   = useState(false)
  const [message, setMessage] = useState(null) // { type: 'ok', text }

  // Fournisseur — la combo affiche TOUS les fournisseurs connus du moteur (champ `all` du backend,
  // LU EN BASE) ; les non-opérationnels sont grisés « pas encore disponible ». Source UNIQUE : la
  // base. Aucun repli en dur : `all` vide → message d'erreur clair, jamais de faux libellés.
  const [aiProvider, setAiProvider] = useState('')
  const [allProviders, setAllProviders] = useState([]) // [{ name, label, available }]
  const [providersLoaded, setProvidersLoaded] = useState(false) // distingue « en cours » de « vide »

  // max_tokens (Phase 4.1.c) — défaut global + 3 surcharges + bornes.
  const [tokens, setTokens] = useState({ default: '', ambiguites: '', sequence: '', optimiseur: '' })
  const [bounds, setBounds] = useState({ min: 256, max: 8000 })
  const [savingTokens, setSavingTokens] = useState(false)
  const [messageTokens, setMessageTokens] = useState(null)

  // Température (Phase 4.1.d) — GLOBALE. Vide = défaut du fournisseur (non réglée), sinon 0.0–2.0.
  const [temperature, setTemperature] = useState('')
  const [tempBounds, setTempBounds] = useState({ min: 0, max: 2 })
  const [savingTemp, setSavingTemp] = useState(false)
  const [messageTemp, setMessageTemp] = useState(null)

  // Coupure de SILENCE du flux de génération (streaming) — secondes, réglage admin en base.
  const [streamTimeout, setStreamTimeout] = useState('')
  const [streamBounds, setStreamBounds]   = useState({ min: 5, max: 300 })
  const [savingStream, setSavingStream]   = useState(false)
  const [messageStream, setMessageStream] = useState(null)

  // Prompts des outils (administrables en base). Liste depuis le backend ; un éditeur par prompt.
  const [prompts, setPrompts] = useState([])      // [{ key, label, placeholders, current, default, is_default }]
  const [promptKey, setPromptKey] = useState('')
  const [promptText, setPromptText] = useState('')
  const [savingPrompt, setSavingPrompt] = useState(false)
  const [messagePrompt, setMessagePrompt] = useState(null)

  useEffect(() => {
    fetch('/api/admin/ai-models', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setAiModel(data.current || '')
        setSupportedModels(data.supported || [])
        setRecommandeModel(data.recommande || '')
      })
      .catch(() => {})

    fetch('/api/admin/max-tokens', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setTokens({
          default: String(data.default ?? ''),
          ambiguites: String(data.overrides?.ambiguites ?? ''),
          sequence: String(data.overrides?.sequence ?? ''),
          optimiseur: String(data.overrides?.optimiseur ?? ''),
        })
        if (data.bounds) setBounds(data.bounds)
      })
      .catch(() => {})

    fetch('/api/admin/ai-providers', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setAiProvider(data.current || '')
        setAllProviders(data.all || [])
      })
      .catch(() => {})
      .finally(() => setProvidersLoaded(true))

    fetch('/api/admin/temperature', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setTemperature(data.temperature == null ? '' : String(data.temperature))
        if (data.bounds) setTempBounds(data.bounds)
      })
      .catch(() => {})

    fetch('/api/admin/stream-timeout', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setStreamTimeout(String(data.timeout ?? ''))
        if (data.bounds) setStreamBounds(data.bounds)
      })
      .catch(() => {})

    loadPrompts()
  }, [])

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
    } catch {}
  }

  // Fournisseur & modèle groupés : le modèle DÉPEND du fournisseur (l'endpoint filtre les
  // modèles par fournisseur). Changer de fournisseur recharge SES modèles (?fournisseur=)
  // et présélectionne le recommandé.
  async function onChangeFournisseur(code) {
    setAiProvider(code)
    setMessage(null)
    try {
      const res = await fetch(`/api/admin/ai-models?fournisseur=${encodeURIComponent(code)}`, { credentials: 'include' })
      const data = await res.json()
      const liste = data.supported || []
      setSupportedModels(liste)
      setRecommandeModel(data.recommande || '')
      setAiModel(data.recommande || liste[0]?.modele || '')  // présélectionne le recommandé (meilleur défaut)
    } catch {
      setSupportedModels([]); setRecommandeModel(''); setAiModel('')
    }
  }

  // Un seul enregistrement pour les deux : le fournisseur D'ABORD (le backend valide le
  // modèle contre le fournisseur ENREGISTRÉ), puis le modèle.
  async function saveFournisseurModele() {
    setSaving(true)
    setMessage(null)
    try {
      let res = await fetchWithTimeout('/api/admin/ai-provider', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
        body: JSON.stringify({ provider: aiProvider }),
      }, TIMEOUT_STD)
      let data = await res.json().catch(() => ({}))
      if (!res.ok) { showError(data.detail || 'Erreur lors de l\'enregistrement du fournisseur.'); return }

      res = await fetchWithTimeout('/api/admin/ai-model', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
        body: JSON.stringify({ model: aiModel }),
      }, TIMEOUT_STD)
      data = await res.json().catch(() => ({}))
      if (!res.ok) { showError(data.detail || 'Erreur lors de l\'enregistrement du modèle.'); return }

      setMessage({ type: 'ok', text: 'Fournisseur et modèle enregistrés.' })
    } catch {
      showError('Erreur réseau — vérifiez que le backend tourne.')
    } finally {
      setSaving(false)
    }
  }

  // Un champ est invalide s'il est vide, non entier, ou hors [min, max].
  const champInvalide = v => {
    const n = Number(v)
    return v === '' || !Number.isInteger(n) || n < bounds.min || n > bounds.max
  }
  const tokensInvalides =
    champInvalide(tokens.default) || champInvalide(tokens.ambiguites) ||
    champInvalide(tokens.sequence) || champInvalide(tokens.optimiseur)

  async function saveMaxTokens() {
    // Garde-fou principal : incohérence -> modale bloquante (jamais avertissement inline),
    // bouton déjà désactivé en plus. Le 400 backend reste un filet.
    if (tokensInvalides) {
      showError(
        `Chaque valeur doit être un nombre entier compris entre ${bounds.min} et ${bounds.max}. ` +
        `Corrigez les champs en rouge avant d'enregistrer : une valeur trop basse tronquerait ` +
        `les activités générées, une valeur trop haute gaspillerait le quota.`
      )
      return
    }
    setSavingTokens(true)
    setMessageTokens(null)
    try {
      const res = await fetchWithTimeout('/api/admin/max-tokens', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          default: Number(tokens.default),
          ambiguites: Number(tokens.ambiguites),
          sequence: Number(tokens.sequence),
          optimiseur: Number(tokens.optimiseur),
        }),
      }, TIMEOUT_STD)
      const data = await res.json().catch(() => ({}))
      if (res.ok) setMessageTokens({ type: 'ok', text: 'Réglages enregistrés.' })
      else showError(data.detail || 'Erreur lors de l\'enregistrement des réglages.')
    } catch {
      showError('Erreur réseau — vérifiez que le backend tourne.')
    } finally {
      setSavingTokens(false)
    }
  }

  // Température : vide = valide (= défaut fournisseur) ; sinon nombre dans [min, max].
  const tempInvalide = v => {
    if (v === '') return false
    const n = Number(v)
    return !Number.isFinite(n) || n < tempBounds.min || n > tempBounds.max
  }

  async function saveTemperature() {
    if (tempInvalide(temperature)) {
      showError(
        `La température doit être un nombre entre ${tempBounds.min} et ${tempBounds.max}, ` +
        `ou laissée vide pour utiliser le défaut du fournisseur. Rappel : une température élevée ` +
        `rend les générations moins fiables (réponses fausses, format cassé) — pour du pédagogique, restez bas à modéré.`
      )
      return
    }
    setSavingTemp(true)
    setMessageTemp(null)
    try {
      const res = await fetchWithTimeout('/api/admin/temperature', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ temperature: temperature === '' ? null : Number(temperature) }),
      }, TIMEOUT_STD)
      const data = await res.json().catch(() => ({}))
      if (res.ok) setMessageTemp({ type: 'ok', text: 'Température enregistrée.' })
      else showError(data.detail || 'Erreur lors de l\'enregistrement de la température.')
    } catch {
      showError('Erreur réseau — vérifiez que le backend tourne.')
    } finally {
      setSavingTemp(false)
    }
  }

  // Coupure de silence : entier dans [min, max]. Vide / non entier / hors bornes = invalide.
  const streamInvalide = v => {
    const n = Number(v)
    return v === '' || !Number.isInteger(n) || n < streamBounds.min || n > streamBounds.max
  }

  async function saveStreamTimeout() {
    if (streamInvalide(streamTimeout)) {
      showError(
        `Le délai doit être un nombre entier de secondes entre ${streamBounds.min} et ${streamBounds.max}. ` +
        `C'est la coupure de SILENCE du flux (temps sans nouveau texte avant d'abandonner), pas la durée ` +
        `totale d'une génération : le compteur se remet à zéro à chaque morceau reçu.`
      )
      return
    }
    setSavingStream(true)
    setMessageStream(null)
    try {
      const res = await fetchWithTimeout('/api/admin/stream-timeout', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ timeout: Number(streamTimeout) }),
      }, TIMEOUT_STD)
      const data = await res.json().catch(() => ({}))
      if (res.ok) setMessageStream({ type: 'ok', text: 'Coupure du flux enregistrée.' })
      else showError(data.detail || 'Erreur lors de l\'enregistrement de la coupure du flux.')
    } catch {
      showError('Erreur réseau — vérifiez que le backend tourne.')
    } finally {
      setSavingStream(false)
    }
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
    if (!window.confirm(
      `Revenir au prompt par défaut pour « ${promptActif.label} » ? ` +
      `Votre version personnalisée sera définitivement supprimée.`
    )) return
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

  const champTokens = (cle, label, aide) => (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      <input
        type="number"
        min={bounds.min}
        max={bounds.max}
        value={tokens[cle]}
        onChange={e => setTokens(t => ({ ...t, [cle]: e.target.value }))}
        className="w-full border rounded px-3 py-2 text-sm"
        style={{ borderColor: champInvalide(tokens[cle]) ? '#dc2626' : '#d1d5db' }}
      />
      <p className="text-xs text-gray-400 mt-1">{aide}</p>
    </div>
  )

  return (
    <div className="flex flex-col gap-6">

      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-1">Génération LLM</h2>
        <p className="text-xs text-gray-400">
          Réglages du moteur de génération des textes.
        </p>
      </div>

      {/* Maître-détail : liste verticale des sections à gauche, détail à droite (motif admin qui
          scale — jamais une rangée d'onglets en haut, ingérable quand le nombre de sections grandit). */}
      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>

        {/* ── Colonne gauche : liste verticale des sections ── */}
        <div style={{ width: 210, flexShrink: 0 }}>
          <div className="bg-white rounded-lg border border-gray-200" style={{ overflow: 'hidden' }}>
            {[
              ['modele', 'Fournisseur & modèle'],
              ['tokens', 'Longueur (tokens)'],
              ['temperature', 'Température'],
              ['stream', 'Coupure du flux'],
              ['prompts', 'Prompts'],
            ].map(([key, label]) => {
              const active = onglet === key
              return (
                <button
                  key={key}
                  onClick={() => setOnglet(key)}
                  title={label}
                  style={{
                    display: 'block', width: '100%', textAlign: 'left',
                    padding: '10px 14px', fontSize: 13, cursor: 'pointer',
                    border: 'none', borderBottom: '1px solid #f1f5f9',
                    borderLeft: active ? '3px solid #A63045' : '3px solid transparent',
                    background: active ? '#fdf2f4' : 'white',
                    color: active ? '#A63045' : '#374151',
                    fontWeight: active ? 600 : 400,
                  }}
                >
                  {label}
                </button>
              )
            })}
          </div>
        </div>

        {/* ── Colonne droite : détail de la section sélectionnée ── */}
        <div style={{ flex: 1, minWidth: 0 }} className="flex flex-col gap-6">

      {/* Section « Fournisseur & modèle » — REGROUPÉES car le modèle DÉPEND du fournisseur
          (l'endpoint /ai-models filtre par fournisseur). On choisit le fournisseur, ses modèles
          se rechargent dessous (?fournisseur=), un seul bouton enregistre les deux (fournisseur
          d'abord : le backend valide le modèle contre le fournisseur enregistré). */}
      {onglet === 'modele' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">
          {/* Fournisseur */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Fournisseur d'IA
            </label>
            <select
              value={aiProvider}
              onChange={e => onChangeFournisseur(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            >
              {!providersLoaded && <option value="">Chargement…</option>}
              {providersLoaded && allProviders.length === 0 &&
                <option value="">Aucun fournisseur en base — vérifiez la table ai_fournisseurs</option>}
              {allProviders.map(p => (
                <option key={p.name} value={p.name} disabled={!p.available}>
                  {p.label}{p.available ? '' : ' — pas encore disponible'}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">
              Service d'IA qui exécute la génération. Les fournisseurs grisés ne sont pas encore
              disponibles (leur clé n'est pas configurée).
            </p>
          </div>

          {/* Modèle du fournisseur sélectionné */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Modèle de génération
            </label>
            <select
              value={aiModel}
              onChange={e => setAiModel(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            >
              {supportedModels.length === 0 && <option value="">Aucun modèle pour ce fournisseur</option>}
              {supportedModels.map(m => (
                <option key={m.modele} value={m.modele}>{m.label}{m.modele === recommandeModel ? ' (recommandé)' : ''}</option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">
              Modèle utilisé pour générer les activités. Pris en compte immédiatement, sans redémarrage.
            </p>
          </div>

          <div className="flex flex-col gap-3 pt-1">
            <button
              onClick={saveFournisseurModele}
              disabled={saving || !aiProvider || !aiModel}
              title="Enregistrer le fournisseur et le modèle"
              style={{
                background: '#1F6EEB', color: 'white', border: 'none',
                borderRadius: 7, padding: '8px 20px', fontSize: 13, fontWeight: 500,
                alignSelf: 'flex-start',
                cursor: (saving || !aiProvider || !aiModel) ? 'not-allowed' : 'pointer',
                opacity: (saving || !aiProvider || !aiModel) ? 0.6 : 1,
              }}
            >
              {saving ? 'Enregistrement…' : 'Enregistrer'}
            </button>
            {message && (
              <div style={{
                background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534',
                borderRadius: 8, padding: '10px 14px', fontSize: 13,
              }}>
                {message.text}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Onglet Longueur (tokens) — HYBRIDE : 1 défaut global + 3 surcharges (pas 6 champs nus).
          Le défaut s'applique aux outils sans surcharge (activité, exemple, consigne).
          Saisie hors bornes -> bord rouge + modale bloquante + bouton désactivé (jamais inline). */}
      {onglet === 'tokens' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">
          <p className="text-xs text-gray-500">
            Longueur maximale de la réponse de l'IA, en tokens. Valeur entre {bounds.min} et {bounds.max}.
            Pris en compte immédiatement, sans redémarrage.
          </p>

          {champTokens('default', 'Défaut global',
            'S\'applique à tous les outils sans réglage propre : création d\'activité, exemple de référentiel, analyse de consigne. (valeur par défaut : 2048)')}
          {champTokens('ambiguites', 'Surcharge — Détecteur d\'ambiguïtés',
            'Sortie souvent plus longue : laisser au-dessus du défaut. (valeur par défaut : 3000)')}
          {champTokens('sequence', 'Surcharge — Générateur de séquences',
            'Une séquence complète demande davantage de longueur. (valeur par défaut : 4000)')}
          {champTokens('optimiseur', 'Surcharge — Optimiseur de séquences',
            'Le plus long des outils : la valeur la plus haute. (valeur par défaut : 6000)')}

          <div className="flex flex-col gap-3 pt-1">
            <button
              onClick={saveMaxTokens}
              disabled={savingTokens || tokensInvalides}
              title="Enregistrer les longueurs maximales"
              style={{
                background: '#1F6EEB', color: 'white', border: 'none',
                borderRadius: 7, padding: '8px 20px', fontSize: 13, fontWeight: 500,
                alignSelf: 'flex-start',
                cursor: (savingTokens || tokensInvalides) ? 'not-allowed' : 'pointer',
                opacity: (savingTokens || tokensInvalides) ? 0.6 : 1,
              }}
            >
              {savingTokens ? 'Enregistrement…' : 'Enregistrer les réglages'}
            </button>
            {messageTokens && (
              <div style={{
                background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534',
                borderRadius: 8, padding: '10px 14px', fontSize: 13,
              }}>
                {messageTokens.text}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Onglet Température (Phase 4.1.d) — GLOBALE. Vide = défaut du fournisseur, sinon 0.0–2.0.
          « Plus haut » N'EST PAS « mieux » : haute température = sorties moins fiables. L'optimiseur
          n'est PAS concerné (température 0 figée en dur). Hors bornes -> bord rouge + modale + bouton off. */}
      {onglet === 'temperature' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">
          <p className="text-xs text-gray-500">
            Contrôle la variabilité des générations, entre {tempBounds.min} (stable, répétable) et {tempBounds.max} (très varié).
            Pour des activités fiables, rester bas à modéré : une valeur élevée rend les réponses moins sûres (erreurs, format cassé).
            Laisser vide = défaut du fournisseur. Pris en compte immédiatement, sans redémarrage.
          </p>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Température (vide = défaut du fournisseur)
            </label>
            <input
              type="number"
              step="0.1"
              min={tempBounds.min}
              max={tempBounds.max}
              value={temperature}
              onChange={e => setTemperature(e.target.value)}
              placeholder="Défaut du fournisseur"
              className="w-full border rounded px-3 py-2 text-sm"
              style={{ borderColor: tempInvalide(temperature) ? '#dc2626' : '#d1d5db' }}
            />
            <p className="text-xs text-gray-400 mt-1">
              L'optimiseur de séquences n'est pas concerné : il reste à 0 pour une sortie fiable.
            </p>
          </div>

          <div className="flex flex-col gap-3 pt-1">
            <button
              onClick={saveTemperature}
              disabled={savingTemp || tempInvalide(temperature)}
              title="Enregistrer la température"
              style={{
                background: '#1F6EEB', color: 'white', border: 'none',
                borderRadius: 7, padding: '8px 20px', fontSize: 13, fontWeight: 500,
                alignSelf: 'flex-start',
                cursor: (savingTemp || tempInvalide(temperature)) ? 'not-allowed' : 'pointer',
                opacity: (savingTemp || tempInvalide(temperature)) ? 0.6 : 1,
              }}
            >
              {savingTemp ? 'Enregistrement…' : 'Enregistrer la température'}
            </button>
            {messageTemp && (
              <div style={{
                background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534',
                borderRadius: 8, padding: '10px 14px', fontSize: 13,
              }}>
                {messageTemp.text}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Onglet Coupure du flux — coupure de SILENCE du streaming de génération (secondes).
          Ce n'est PAS la durée totale : le compteur se réarme à chaque morceau reçu, seuls les
          silences anormaux coupent. Hors bornes -> bord rouge + modale + bouton off. */}
      {onglet === 'stream' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">
          <p className="text-xs text-gray-500">
            Coupure de <strong>silence</strong> du flux de génération : nombre de secondes sans nouveau
            texte avant d'abandonner. Ce n'est PAS la durée totale d'une génération — le compteur se
            remet à zéro à chaque morceau reçu, donc une génération qui progresse n'est jamais coupée.
            Entre {streamBounds.min} et {streamBounds.max} s. Pris en compte immédiatement, sans redémarrage.
          </p>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Coupure de silence (secondes)
            </label>
            <input
              type="number"
              min={streamBounds.min}
              max={streamBounds.max}
              value={streamTimeout}
              onChange={e => setStreamTimeout(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
              style={{ borderColor: streamInvalide(streamTimeout) ? '#dc2626' : '#d1d5db' }}
            />
            <p className="text-xs text-gray-400 mt-1">
              Défaut 30 s. Trop bas = des générations lentes mais normales seraient coupées à tort.
            </p>
          </div>

          <div className="flex flex-col gap-3 pt-1">
            <button
              onClick={saveStreamTimeout}
              disabled={savingStream || streamInvalide(streamTimeout)}
              title="Enregistrer la coupure du flux"
              style={{
                background: '#1F6EEB', color: 'white', border: 'none',
                borderRadius: 7, padding: '8px 20px', fontSize: 13, fontWeight: 500,
                alignSelf: 'flex-start',
                cursor: (savingStream || streamInvalide(streamTimeout)) ? 'not-allowed' : 'pointer',
                opacity: (savingStream || streamInvalide(streamTimeout)) ? 0.6 : 1,
              }}
            >
              {savingStream ? 'Enregistrement…' : 'Enregistrer la coupure'}
            </button>
            {messageStream && (
              <div style={{
                background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534',
                borderRadius: 8, padding: '10px 14px', fontSize: 13,
              }}>
                {messageStream.text}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Onglet Prompts — texte exact envoyé à l'IA pour chaque outil. L'admin édite ; les repères
          {…} obligatoires DOIVENT rester (sinon matière/niveau/contenu non injectés) -> bord rouge
          + modale + bouton off. Le 400 backend reste un filet (accolades). « Revenir au défaut »
          efface vraiment la surcharge en base. Le catalogue d'activités N'EST PAS ici. */}
      {onglet === 'prompts' && (
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
      )}

      </div>{/* fin colonne droite (détail) */}
      </div>{/* fin maître-détail */}
    </div>
  )
}
