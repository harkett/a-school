import { useState } from 'react'

export default function AdminParametresGeneration() {
  const [onglet, setOnglet] = useState('modele')

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

      {/* Onglet Modèle — coquille : point d'atterrissage de la combo (4.1.b).
          N'appelle pas le backend tant que 4.1.b n'est pas posé. */}
      {onglet === 'modele' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-sm text-gray-400">
            Le réglage du modèle de génération arrivera ici.
          </p>
        </div>
      )}

    </div>
  )
}
