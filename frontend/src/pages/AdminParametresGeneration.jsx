import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'

export default function AdminParametresGeneration() {
  const [onglet, setOnglet] = useState('modele')
  const [aiModel, setAiModel] = useState('')
  const [supportedModels, setSupportedModels] = useState([])
  const [saving, setSaving]   = useState(false)
  const [message, setMessage] = useState(null) // { type: 'ok', text }

  // max_tokens (Phase 4.1.c) — défaut global + 3 surcharges + bornes.
  const [tokens, setTokens] = useState({ default: '', ambiguites: '', sequence: '', optimiseur: '' })
  const [bounds, setBounds] = useState({ min: 256, max: 8000 })
  const [savingTokens, setSavingTokens] = useState(false)
  const [messageTokens, setMessageTokens] = useState(null)

  useEffect(() => {
    fetch('/api/admin/ai-models', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setAiModel(data.current || '')
        setSupportedModels(data.supported || [])
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
  }, [])

  async function saveModel() {
    setSaving(true)
    setMessage(null)
    try {
      const res = await fetchWithTimeout('/api/admin/ai-model', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ model: aiModel }),
      }, TIMEOUT_STD)
      const data = await res.json().catch(() => ({}))
      if (res.ok) setMessage({ type: 'ok', text: 'Modèle enregistré.' })
      else showError(data.detail || 'Erreur lors de l\'enregistrement du modèle.')
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

  const tabStyle = active => ({
    padding: '7px 18px', borderRadius: 6, fontSize: 13, fontWeight: active ? 600 : 400,
    cursor: 'pointer', border: 'none',
    background: active ? 'var(--bleu)' : 'white',
    color: active ? 'white' : '#6b7280',
    boxShadow: active ? 'none' : 'inset 0 0 0 1px #e5e7eb',
  })

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
    <div style={{ maxWidth: 640 }} className="flex flex-col gap-6">

      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-1">Génération LLM</h2>
        <p className="text-xs text-gray-400">
          Réglages du moteur de génération des activités.
        </p>
      </div>

      {/* Onglets */}
      <div className="flex gap-2">
        <button style={tabStyle(onglet === 'modele')} onClick={() => setOnglet('modele')}>
          Modèle
        </button>
        <button style={tabStyle(onglet === 'tokens')} onClick={() => setOnglet('tokens')}>
          Longueur (tokens)
        </button>
      </div>

      {/* Onglet Modèle — liste déroulante fermée (Option 3) : l'admin choisit le modèle
          dans la liste blanche fournie par le backend. Invalidité impossible à la source ;
          le 400 backend reste un filet. */}
      {onglet === 'modele' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Modèle de génération
            </label>
            <select
              value={aiModel}
              onChange={e => setAiModel(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            >
              {supportedModels.length === 0 && <option value="">Chargement…</option>}
              {supportedModels.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">
              Modèle d'IA utilisé pour générer les activités. Pris en compte immédiatement, sans redémarrage.
            </p>
          </div>

          <div className="flex flex-col gap-3 pt-1">
            <button
              onClick={saveModel}
              disabled={saving || !aiModel}
              title="Enregistrer le modèle de génération"
              style={{
                background: '#1F6EEB', color: 'white', border: 'none',
                borderRadius: 7, padding: '8px 20px', fontSize: 13, fontWeight: 500,
                alignSelf: 'flex-start',
                cursor: (saving || !aiModel) ? 'not-allowed' : 'pointer',
                opacity: (saving || !aiModel) ? 0.6 : 1,
              }}
            >
              {saving ? 'Enregistrement…' : 'Enregistrer le modèle'}
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

    </div>
  )
}
