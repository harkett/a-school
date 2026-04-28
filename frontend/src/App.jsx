import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import Footer from './components/Footer'
import TexteSource from './components/TexteSource'
import Parametres from './components/Parametres'
import ZoneResultat from './components/ZoneResultat'
import Aide from './components/Aide'
import APropos from './components/APropos'
import Feedback from './components/Feedback'
import MesActivites from './components/MesActivites'
import MonProfil from './components/MonProfil'
import Notation from './components/Notation'
import Login from './pages/Login'
import Signup from './pages/Signup'
import VerifyEmail from './pages/VerifyEmail'
import MentionsLegales from './pages/MentionsLegales'
import AdminLogin from './pages/AdminLogin'
import AdminLogs from './pages/AdminLogs'
import AdminActivites from './pages/AdminActivites'
import AdminFeedbacks from './pages/AdminFeedbacks'
import AdminProfils from './pages/AdminProfils'
import AdminLayout from './components/AdminLayout'
import './index.css'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#f0f4f8' }}>
        <span className="text-gray-400 text-sm">Chargement…</span>
      </div>
    )
  }
  return user ? children : <Navigate to="/login" replace />
}

function MainApp() {
  const { user, logout } = useAuth()
  const matiere = user?.subject || 'Français'

  const [page, setPage] = useState('accueil')
  const [showFeedback, setShowFeedback] = useState(false)
  const [showNotation, setShowNotation] = useState(false)
  const [activites, setActivites] = useState([])
  const [texte, setTexte] = useState('')
  const [resultat, setResultat] = useState(null)
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState(null)

  const [params, setParams] = useState({
    activite_key: '',
    niveau: user?.niveau || localStorage.getItem('aschool_niveau') || '4e',
    sous_type: null,
    nb: 5,
    avec_correction: false,
  })

  function setParamsWithSave(newParams) {
    if (newParams.niveau !== params.niveau) {
      localStorage.setItem('aschool_niveau', newParams.niveau)
    }
    setParams(newParams)
  }

  useEffect(() => {
    fetch(`/api/activites/${encodeURIComponent(matiere)}`)
      .then(r => r.json())
      .then(data => {
        setActivites(data)
        if (data.length > 0) {
          setParams(p => ({
            ...p,
            activite_key: data[0].key,
            sous_type: data[0].sous_types[0] || null,
            nb: data[0].params.includes('nb') ? 5 : null,
          }))
        }
      })
      .catch(() => setErreur('Impossible de charger les activités — vérifiez que le backend tourne.'))
  }, [matiere])

  async function generer() {
    if (!texte.trim()) {
      setErreur('Veuillez saisir un texte source.')
      return
    }
    setErreur(null)
    setResultat(null)
    setLoading(true)
    try {
      const body = { ...params, texte }
      if (!body.nb) delete body.nb
      if (!body.sous_type) delete body.sous_type

      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || `Erreur ${res.status}`)
      }
      const data = await res.json()
      setResultat(data.resultat)
      fetch('/api/mes-activites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          activite_key: params.activite_key,
          activite_label: activites.find(a => a.key === params.activite_key)?.label || params.activite_key,
          niveau: params.niveau,
          sous_type: params.sous_type || null,
          nb: params.nb || null,
          avec_correction: params.avec_correction,
          texte_source: texte,
          resultat: data.resultat,
        }),
      }).catch(() => {})
    } catch (e) {
      setErreur(`Erreur : ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  function chargerActivite(act) {
    setTexte(act.texte_source)
    setParamsWithSave({
      activite_key: act.activite_key,
      niveau: act.niveau,
      sous_type: act.sous_type || null,
      nb: act.nb || 5,
      avec_correction: act.avec_correction,
    })
    setResultat(act.resultat)
    setPage('accueil')
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header
        matiere={matiere}
        email={user?.email}
        onLogout={logout}
      />

      <div className="flex flex-1 min-h-0">
        <Sidebar page={page} onNavigate={setPage} onFeedback={() => setShowFeedback(true)} onNotation={() => setShowNotation(true)} />

        <main className="flex-1 p-6 flex flex-col gap-4 overflow-auto">
          {erreur && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm">
              {erreur}
            </div>
          )}

          {page === 'accueil' && (
            <>
              <TexteSource texte={texte} onChange={setTexte} />
              {activites.length > 0 && (
                <Parametres
                  activites={activites}
                  params={params}
                  onChange={setParamsWithSave}
                  onGenerer={generer}
                  loading={loading}
                  hasResultat={!!resultat}
                  canGenerer={!!texte.trim() && !!params.activite_key}
                  onFeedback={() => setShowFeedback(true)}
                />
              )}
              <ZoneResultat
                resultat={resultat}
                onRegenerer={generer}
                loading={loading}
                email={user?.email}
              />
            </>
          )}

          {page === 'mes-activites' && (
            <MesActivites onCharger={chargerActivite} />
          )}

          {page === 'mon-profil' && <MonProfil />}

          {page === 'historique' && (
            <div className="bg-white rounded border border-gray-200 p-8 text-center text-gray-400 text-sm">
              Historique — disponible en Phase 3 (base de données)
            </div>
          )}

          {page === 'aide' && <Aide />}

          {page === 'apropos' && <APropos email={user?.email} />}
        </main>
      </div>

      <Footer />
      {showFeedback && <Feedback onClose={() => setShowFeedback(false)} />}
      {showNotation && <Notation onClose={() => setShowNotation(false)} />}
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainApp />
              </ProtectedRoute>
            }
          />
          <Route path="/mentions-legales" element={<MentionsLegales />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<Navigate to="/admin/logs" replace />} />
            <Route path="logs" element={<AdminLogs />} />
            <Route path="activites"  element={<AdminActivites />} />
            <Route path="feedbacks"  element={<AdminFeedbacks />} />
            <Route path="profils"    element={<AdminProfils />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
