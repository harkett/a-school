import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'

export default function AdminParametresGeneration() {
  const [onglet, setOnglet] = useState('modele')
  const [aiModel, setAiModel] = useState('')
  const [supportedModels, setSupportedModels] = useState([])
  const [saving, setSaving]   = useState(false)
  const [message, setMessage] = useState(null) // { type: 'ok', text }

  useEffect(() => {
    fetch('/api/admin/ai-models', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setAiModel(data.current || '')
        setSupportedModels(data.supported || [])
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

  const tabStyle = active => ({
    padding: '7px 18px', borderRadius: 6, fontSize: 13, fontWeight: active ? 600 : 400,
    cursor: 'pointer', border: 'none',
    background: active ? 'var(--bleu)' : 'white',
    color: active ? 'white' : '#6b7280',
    boxShadow: active ? 'none' : 'inset 0 0 0 1px #e5e7eb',
  })

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

    </div>
  )
}
