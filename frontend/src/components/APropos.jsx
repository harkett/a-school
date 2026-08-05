import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import Feedback from './Feedback'
import Notation from './Notation'
import { APP_VERSION } from '../version'
import { fetchWithTimeout, lireReponse, messagePourEcran, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'

// Puces « niveau » de l'onglet Programmes : disponible = gras + point bordeaux ; à venir = gris estompé.
const chipDispo = {
  display: 'inline-flex', alignItems: 'center', gap: 6,
  fontSize: 12, fontWeight: 600, padding: '3px 10px', borderRadius: 99,
  background: '#fff', color: '#1e293b', border: '1px solid #e2e8f0',
}
const chipAvenir = {
  display: 'inline-flex', alignItems: 'center', gap: 6,
  fontSize: 12, fontWeight: 400, padding: '3px 10px', borderRadius: 99,
  background: '#f8fafc', color: '#b4bac3', border: '1px solid #f1f5f9',
}

export default function APropos({ email }) {
  const [showFeedback, setShowFeedback] = useState(false)
  const [showNotation, setShowNotation] = useState(false)
  const [onglet, setOnglet] = useState('apropos')   // onglet actif : 'apropos' | 'programmes'

  // Arbre des programmes (get, zéro copie) : cycles → niveaux, chacun avec refDisponible (DÉRIVÉ
  // en base = référentiel réellement ingéré). C'est LUI qui décide gras (disponible) / gris (à venir).
  // Lecture ratée : l'onglet ne reste pas figé sur « Chargement… » — message en boîte de
  // dialogue et bouton « Réessayer » (motif de l'Accueil).
  const { data: programmes = null, isError: chargementRate, error, refetch } = useQuery({
    queryKey: ['programmes', 'couverture'],
    queryFn: async () => await lireReponse(await fetchWithTimeout(
      '/api/programmes/couverture', { credentials: 'include' }, TIMEOUT_STD)),
  })
  useEffect(() => { if (error) showError(messagePourEcran(error)) }, [error])
  const charger = () => refetch()

  const cycles = programmes?.cycles || []
  const totalNiv = cycles.reduce((s, b) => s + b.niveaux.length, 0)
  const dispoNiv = cycles.reduce((s, b) => s + b.niveaux.filter(n => n.refDisponible).length, 0)

  const onglets = [
    { id: 'apropos', label: 'À propos', title: 'Informations sur aSchool' },
    { id: 'programmes', label: 'Programmes couverts', title: 'Les programmes déjà intégrés à aSchool' },
  ]

  return (
    <div className="w-full flex flex-col gap-4">
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">

        {/* Barre d'onglets : l'onglet actif est souligné en bordeaux (cohérent avec toute l'appli). */}
        <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb' }}>
          {onglets.map(t => {
            const actif = onglet === t.id
            return (
              <button
                key={t.id}
                onClick={() => setOnglet(t.id)}
                title={t.title}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  padding: '14px 22px', fontSize: 13,
                  fontWeight: actif ? 600 : 500,
                  color: actif ? 'var(--bordeaux)' : '#64748b',
                  borderBottom: actif ? '2px solid var(--bordeaux)' : '2px solid transparent',
                  marginBottom: -1,
                  transition: 'color 0.15s',
                }}
              >
                {t.label}
              </button>
            )
          })}
        </div>

        {/* ─────────── Onglet « À propos » ─────────── */}
        {onglet === 'apropos' && (
          <>
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
                    <td className="py-2.5 text-gray-700 font-medium">{import.meta.env.DEV ? 'Développement' : 'Production'}</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-gray-400">Compte connecté</td>
                    <td className="py-2.5 text-gray-700 font-medium" style={{ wordBreak: 'break-all' }}>{email}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Bloc 3 — Actions */}
            <div className="px-8 py-5 border-b border-gray-100 flex flex-col gap-3">
              <button
                onClick={() => setShowNotation(true)}
                title="Donnez une note à aSchool"
                style={{ background: 'none', border: '1px solid #e5e7eb', borderRadius: 8, cursor: 'pointer', padding: '10px 16px', textAlign: 'left', width: '100%' }}
              >
                <div className="text-sm font-medium text-gray-700">Notez aSchool</div>
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

            {/* Bloc 4 — Copyright */}
            <div className="px-8 py-4">
              <p className="text-xs text-gray-400">© 2026 AFIA — Tous droits réservés</p>
            </div>
          </>
        )}

        {/* ─────────── Onglet « Programmes couverts » ─────────── */}
        {/* Groupés par cycle ; niveau EN GRAS = programme disponible dans aSchool aujourd'hui,
            EN GRIS = à venir. Légende en bas. Donnée = get, zéro copie. Pleine largeur : les
            puces s'étalent sur toute la fenêtre. */}
        {onglet === 'programmes' && (
          <div className="px-8 py-6">
            <div className="flex items-baseline justify-between gap-3 mb-1">
              <h3 className="text-sm font-semibold text-gray-800">Programmes couverts</h3>
              {programmes && (
                <span className="text-xs text-gray-400">{dispoNiv} niveau{dispoNiv > 1 ? 'x' : ''} sur {totalNiv} disponible{dispoNiv > 1 ? 's' : ''}</span>
              )}
            </div>
            <p className="text-xs text-gray-400 mb-4">Les niveaux dont le programme officiel est déjà intégré à aSchool.</p>

            {!programmes && chargementRate ? (
              <button type="button" onClick={charger} className="btn-primary"
                title="Recharger la liste des programmes couverts">
                Réessayer
              </button>
            ) : !programmes ? (
              <p className="text-sm text-gray-400">Chargement…</p>
            ) : cycles.length === 0 ? (
              <p className="text-sm text-gray-400">Aucun programme pour le moment.</p>
            ) : (
              <>
                {cycles.map(bloc => (
                  <div key={bloc.cycle} style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
                      {bloc.cycle}
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {bloc.niveaux.map(n => (
                        <span
                          key={n.id}
                          style={n.refDisponible ? chipDispo : chipAvenir}
                          title={n.refDisponible ? `${n.nom} — disponible dans aSchool` : `${n.nom} — à venir`}
                        >
                          <span style={{ width: 5, height: 5, borderRadius: '50%', background: n.refDisponible ? 'var(--bordeaux)' : '#cbd5e1', flexShrink: 0 }} />
                          {n.nom}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}

                {/* Légende */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginTop: 6, paddingTop: 12, borderTop: '1px solid #f1f5f9', fontSize: 11, color: '#94a3b8' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--bordeaux)', flexShrink: 0 }} />
                    <strong style={{ color: '#475569', fontWeight: 600 }}>En gras</strong> : disponible aujourd'hui
                  </span>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#cbd5e1', flexShrink: 0 }} />
                    En gris : à venir
                  </span>
                </div>
              </>
            )}
          </div>
        )}

      </div>

      {showFeedback && <Feedback onClose={() => setShowFeedback(false)} />}
      {showNotation && <Notation onClose={() => setShowNotation(false)} />}
    </div>
  )
}
