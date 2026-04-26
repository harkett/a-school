import { useState } from 'react'
import Feedback from './Feedback'

export default function APropos({ email }) {
  const [showFeedback, setShowFeedback] = useState(false)

  return (
    <div className="max-w-lg">
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">

        {/* Bloc 1 — Identité */}
        <div className="px-8 py-7 border-b border-gray-100">
          <div className="flex items-baseline gap-2 mb-2">
            <span className="text-2xl font-bold tracking-tight">
              <span style={{ color: 'var(--bordeaux)' }}>A</span>
              <span style={{ color: 'var(--bleu)' }}>-SCHOOL</span>
            </span>
            <span className="text-xs font-medium text-gray-400 border border-gray-200 rounded px-2 py-0.5">
              v3.0-dev
            </span>
          </div>
          <p className="text-sm text-gray-500">
            Générateur d'activités pédagogiques pour enseignants
          </p>
        </div>

        {/* Bloc 2 — Informations */}
        <div className="px-8 py-5 border-b border-gray-100">
          <table className="w-full text-sm">
            <tbody>
              <tr className="border-b border-gray-50">
                <td className="py-2.5 text-gray-400 w-40">Version</td>
                <td className="py-2.5 text-gray-700 font-medium">3.0-dev</td>
              </tr>
              <tr className="border-b border-gray-50">
                <td className="py-2.5 text-gray-400">Environnement</td>
                <td className="py-2.5 text-gray-700 font-medium">Développement</td>
              </tr>
              <tr>
                <td className="py-2.5 text-gray-400">Compte connecté</td>
                <td className="py-2.5 text-gray-700 font-medium">{email}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Bloc 3 — Feedback */}
        <div className="px-8 py-5 border-b border-gray-100">
          <button
            onClick={() => setShowFeedback(true)}
            title="Envoyer un retour ou signaler un problème"
            className="text-sm text-gray-500 hover:text-gray-800 underline"
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
          >
            Envoyer un feedback
          </button>
        </div>

        {/* Bloc 4 — Copyright */}
        <div className="px-8 py-4">
          <p className="text-xs text-gray-400">© 2026 AFIA — Tous droits réservés</p>
        </div>

      </div>

      {showFeedback && <Feedback onClose={() => setShowFeedback(false)} />}
    </div>
  )
}
