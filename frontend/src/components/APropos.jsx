import { useState } from 'react'
import Feedback from './Feedback'
import Notation from './Notation'
import { APP_VERSION } from '../version'

const MATIERES = ['Français', 'Histoire-Géographie', 'Mathématiques', 'Physique-Chimie', 'SVT', 'SES', 'NSI', 'Philosophie', 'Langues Vivantes (LV)', 'Technologie', 'Arts', 'EPS']

export default function APropos({ email }) {
  const [showFeedback, setShowFeedback] = useState(false)
  const [showNotation, setShowNotation] = useState(false)

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
              v{APP_VERSION}
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
                <td className="py-2.5 text-gray-700 font-medium">{APP_VERSION}</td>
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

        {/* Bloc 3 — Matières */}
        <div className="px-8 py-5 border-b border-gray-100">
          <div className="text-xs text-gray-400 mb-3">Matières disponibles ({MATIERES.length})</div>
          <div className="flex flex-wrap gap-1.5">
            {MATIERES.map(m => (
              <span key={m} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 99, background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0' }}>
                {m}
              </span>
            ))}
          </div>
        </div>

        {/* Bloc 4 — Actions */}
        <div className="px-8 py-5 border-b border-gray-100 flex flex-col gap-3">
          <button
            onClick={() => setShowNotation(true)}
            title="Donnez une note à A-SCHOOL"
            style={{ background: 'none', border: '1px solid #e5e7eb', borderRadius: 8, cursor: 'pointer', padding: '10px 16px', textAlign: 'left', width: '100%' }}
          >
            <div className="text-sm font-medium text-gray-700">Notez A-SCHOOL</div>
            <div className="text-xs text-gray-400 mt-0.5">Donnez votre avis sur la plateforme — 30 secondes</div>
          </button>
          <button
            onClick={() => setShowFeedback(true)}
            title="Signaler un problème ou suggérer une amélioration"
            style={{ background: 'none', border: '1px solid #e5e7eb', borderRadius: 8, cursor: 'pointer', padding: '10px 16px', textAlign: 'left', width: '100%' }}
          >
            <div className="text-sm font-medium text-gray-700">Envoyer un feedback</div>
            <div className="text-xs text-gray-400 mt-0.5">Signaler un problème ou suggérer une amélioration</div>
          </button>
        </div>

        {/* Bloc 5 — Copyright */}
        <div className="px-8 py-4">
          <p className="text-xs text-gray-400">© 2026 AFIA — Tous droits réservés</p>
        </div>

      </div>

      {showFeedback && <Feedback onClose={() => setShowFeedback(false)} />}
      {showNotation && <Notation onClose={() => setShowNotation(false)} />}
    </div>
  )
}
