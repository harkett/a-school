import { useState } from 'react'
import Feedback from './Feedback'
import Notation from './Notation'
import { APP_VERSION } from '../version'

const MATIERES = ['Français', 'Histoire-Géographie', 'Mathématiques', 'Physique-Chimie', 'SVT', 'SES', 'NSI', 'Philosophie', 'Langues Vivantes (LV)', 'Technologie', 'Arts', 'EPS']

export default function APropos({ email, matiere }) {
  const [showFeedback, setShowFeedback] = useState(false)
  const [showNotation, setShowNotation] = useState(false)
  const [showFiche, setShowFiche] = useState(false)

  return (
    <div className="max-w-lg">
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">

        {/* Bloc 1 — Identité */}
        <div className="px-8 py-7 border-b border-gray-100">
          <div className="flex items-center gap-5">
            <img src="/Logo_aSchool.png" alt="aSchool" style={{ width: 100, height: 'auto', flexShrink: 0 }} />
            <div>
              <span className="text-xs font-medium text-gray-400 border border-gray-200 rounded px-2 py-0.5">
                v{APP_VERSION}
              </span>
              <p className="text-sm text-gray-500 mt-2">
                Générateur d'activités pédagogiques pour enseignants
              </p>
            </div>
          </div>
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
            onClick={() => setShowFiche(true)}
            title={`Voir la fiche de présentation aSchool pour ${matiere}`}
            style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 8, cursor: 'pointer', padding: '10px 16px', textAlign: 'left', width: '100%' }}
          >
            <div className="text-sm font-medium" style={{ color: '#1d4ed8' }}>
              Ma fiche aSchool — {matiere}
            </div>
            <div className="text-xs mt-0.5" style={{ color: '#3b82f6' }}>
              Document de présentation à imprimer ou partager à vos collègues
            </div>
          </button>
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

      {showFiche && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 500, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={e => { if (e.target === e.currentTarget) setShowFiche(false) }}
        >
          <div style={{ background: '#fff', borderRadius: 10, width: '90vw', maxWidth: 860, height: '90vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 16px 48px rgba(0,0,0,0.25)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: '#1e293b' }}>
                Fiche aSchool — {matiere}
              </span>
              <div style={{ display: 'flex', gap: 8 }}>
                <a
                  href={`/api/fiches/${encodeURIComponent(matiere)}`}
                  download={`aSchool_${matiere}.html`}
                  title="Télécharger la fiche (HTML imprimable)"
                  style={{ padding: '6px 14px', borderRadius: 6, border: '1px solid #bfdbfe', background: '#eff6ff', color: '#1d4ed8', fontSize: 12, fontWeight: 600, textDecoration: 'none' }}
                >
                  Télécharger
                </a>
                <button
                  onClick={() => setShowFiche(false)}
                  title="Fermer"
                  style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#64748b', fontSize: 18, lineHeight: 1, cursor: 'pointer' }}
                >
                  ×
                </button>
              </div>
            </div>
            <iframe
              src={`/api/fiches/${encodeURIComponent(matiere)}`}
              title={`Fiche aSchool ${matiere}`}
              style={{ flex: 1, border: 'none', width: '100%' }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
