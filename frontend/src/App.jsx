import { useState, useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
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
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import MentionsLegales from './pages/MentionsLegales'
import AdminLogin from './pages/AdminLogin'
import AdminLogs from './pages/AdminLogs'
import AdminActivites from './pages/AdminActivites'
import AdminFeedbacks from './pages/AdminFeedbacks'
import AdminProfils from './pages/AdminProfils'
import AdminParametres from './pages/AdminParametres'
import AdminSessions from './pages/AdminSessions'
import AdminServeur from './pages/AdminServeur'
import AdminAudit from './pages/AdminAudit'
import AdminAlertes from './pages/AdminAlertes'
import AdminTentatives from './pages/AdminTentatives'
import AdminCompte from './pages/AdminCompte'
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

const TIPS = [
  {
    texte: 'Si votre navigateur propose de traduire cette page, choisissez « Ne jamais traduire ce site ». La traduction automatique perturbe la génération des activités.',
    lien: { label: 'Pourquoi ?' },
    modal: {
      titre: 'Pourquoi ne pas traduire la page ?',
      lignes: [
        'La traduction automatique modifie le texte source et les consignes — A-SCHOOL reçoit alors des mots incorrects et génère des activités incohérentes ou vides.',
        'La page A-SCHOOL est entièrement en français : la traduction n\'apporte rien et perturbe tout.',
        '— Chrome : clic droit sur la page → « Traduire en français » → choisissez « Ne jamais traduire ce site ».',
        '— Edge : cliquez sur l\'icône de traduction dans la barre d\'adresse → « Ne jamais traduire ce site ».',
      ],
    },
  },
  {
    texte: 'A-SCHOOL apprend votre style : plus vous sauvegardez d\'activités du même type, plus il s\'adapte à votre façon d\'enseigner.',
    lien: { label: 'En savoir plus' },
    modal: {
      titre: 'Comment A-SCHOOL apprend votre style ?',
      lignes: [
        'À chaque sauvegarde, A-SCHOOL conserve votre activité comme exemple.',
        'À partir de la 3ème sauvegarde d\'un même type, il s\'en inspire automatiquement pour adapter le ton, la formulation des questions et le niveau de langue.',
        'Cela fonctionne par type d\'activité : vos exemples de QCM n\'influencent pas vos résumés, et inversement.',
        'Plus vous sauvegardez, plus les activités générées vous ressemblent.',
      ],
    },
  },
  { texte: 'Cliquez sur « Ajuster pour cette activité » pour changer la matière ou le niveau ponctuellement, sans modifier votre profil.' },
  { texte: 'Votre niveau par défaut est mémorisé d\'une session à l\'autre — vous n\'avez pas à le resélectionner à chaque connexion.' },
  { texte: 'L\'option « Avec correction » génère automatiquement un corrigé sous l\'activité.' },
  { texte: 'Depuis « Mes activités », rechargez une activité précédente et régénérez-la avec un nouveau texte source.' },
  { texte: 'Complétez votre profil (matière, niveau par défaut) pour que A-SCHOOL s\'adapte à votre contexte dès la connexion.' },
  { texte: 'La précision « Mélange » demande à A-SCHOOL de combiner tous les types disponibles pour cette activité. Le détail des types combinés s\'affiche sous le sélecteur.' },
  { texte: 'Pour retrouver un texte dont vous avez un souvenir vague, consultez Gallica (gallica.bnf.fr) ou Wikisource, puis copiez-collez le texte dans A-SCHOOL.' },
  { texte: 'Problème de connexion persistant malgré un identifiant correct ? Supprimez les cookies du site : dans Edge ou Chrome, appuyez sur F12, allez dans l\'onglet Application, puis Cookies, et supprimez tous les cookies de cette page.' },
]

const INACTIVITY_MS = 2 * 60 * 60 * 1000
const WARNING_SECS  = 300

function MainApp() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const matiere = user?.subject || 'Français'
  const matiereLabel = matiere === 'Langues Vivantes (LV)' && user?.langue_lv
    ? `LV - ${user.langue_lv}`
    : matiere

  const [page, setPage] = useState('accueil')
  const [showFeedback, setShowFeedback] = useState(false)
  const [showNotation, setShowNotation] = useState(false)
  const [activites, setActivites] = useState([])
  const [texte, setTexte] = useState('')
  const [resultat, setResultat] = useState(null)
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState(null)
  const [sessionMatiere, setSessionMatiere] = useState(matiere)
  const [toast, setToast] = useState(null)
  const [tipIndex, setTipIndex] = useState(
    () => parseInt(localStorage.getItem('aschool_tip_index') || '0') % TIPS.length
  )
  const [tipModal, setTipModal] = useState(null)
  const [inactivityWarning, setInactivityWarning] = useState(false)
  const [countdown, setCountdown] = useState(WARNING_SECS)
  const timerRef  = useRef(null)
  const cdRef     = useRef(null)
  const warningRef = useRef(false)

  useEffect(() => {
    function arm() {
      clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => {
        warningRef.current = true
        setInactivityWarning(true)
        let secs = WARNING_SECS
        setCountdown(secs)
        cdRef.current = setInterval(() => {
          secs -= 1
          setCountdown(secs)
          if (secs <= 0) {
            clearInterval(cdRef.current)
            fetch('/api/auth/logout-inactivite', { method: 'POST', credentials: 'include' }).catch(() => {})
            navigate('/login?raison=inactivite')
            logout()
          }
        }, 1000)
      }, INACTIVITY_MS)
    }
    function onActivity() { if (!warningRef.current) arm() }
    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart']
    events.forEach(e => window.addEventListener(e, onActivity, { passive: true }))
    arm()
    return () => {
      events.forEach(e => window.removeEventListener(e, onActivity))
      clearTimeout(timerRef.current)
      clearInterval(cdRef.current)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function stayConnected() {
    clearInterval(cdRef.current)
    warningRef.current = false
    setInactivityWarning(false)
    setCountdown(WARNING_SECS)
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      warningRef.current = true
      setInactivityWarning(true)
      let secs = WARNING_SECS
      setCountdown(secs)
      cdRef.current = setInterval(() => {
        secs -= 1
        setCountdown(secs)
        if (secs <= 0) {
          clearInterval(cdRef.current)
          navigate('/login?raison=inactivite')
          logout()
        }
      }, 1000)
    }, INACTIVITY_MS)
  }

  useEffect(() => {
    if (!user) return
    const id = setInterval(async () => {
      try {
        const r = await fetch('/api/heartbeat', { method: 'POST', credentials: 'include' })
        if (r.status === 401) {
          const data = await r.json().catch(() => ({}))
          if (data.detail === 'Session déconnectée.') {
            navigate('/login?raison=force_deconnexion')
            logout()
          }
        }
      } catch {}
    }, 60000)
    return () => clearInterval(id)
  }, [user]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 6000)
    return () => clearTimeout(t)
  }, [toast])

  function goTip(dir) {
    setTipIndex(i => {
      const next = (i + dir + TIPS.length) % TIPS.length
      localStorage.setItem('aschool_tip_index', String(next))
      return next
    })
  }

  useEffect(() => {
    setSessionMatiere(matiere)
  }, [matiere])

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
    fetch(`/api/activites/${encodeURIComponent(sessionMatiere)}`)
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
  }, [sessionMatiere])

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
      if (sessionMatiere === 'Langues Vivantes (LV)' && user?.langue_lv) {
        body.langue_lv = user.langue_lv
      }

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

      const countKey = `aschool_style_count_${params.activite_key}`
      const newCount = (parseInt(localStorage.getItem(countKey) || '0')) + 1
      localStorage.setItem(countKey, String(newCount))
      if (newCount === 3) {
        setToast('A-SCHOOL reconnaît maintenant votre façon de travailler sur ce type d\'activité.')
      }

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
        matiere={matiereLabel}
        email={user?.email}
        prenom={user?.prenom}
        nom={user?.nom}
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
              <div style={{
                background: '#f5f3ff',
                border: '1px solid #c4b5fd',
                borderRadius: '6px',
                padding: '7px 12px',
                fontSize: '12.5px',
                color: '#5b21b6',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
              }}>
                <span style={{ fontWeight: 700, whiteSpace: 'nowrap', flexShrink: 0, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: '#7c3aed' }}>
                  Truc &amp; astuce
                </span>
                <span style={{ color: '#a78bfa', fontSize: '11px', whiteSpace: 'nowrap', flexShrink: 0 }}>
                  {tipIndex + 1} / {TIPS.length}
                </span>
                <span style={{ flex: 1 }}>
                  {TIPS[tipIndex].texte}
                  {TIPS[tipIndex].lien && (
                    <>{' '}<button onClick={() => setTipModal(TIPS[tipIndex].modal)} style={{ background: 'none', border: 'none', padding: 0, color: '#5b21b6', textDecoration: 'underline', cursor: 'pointer', fontSize: '12.5px' }}>{TIPS[tipIndex].lien.label}</button></>
                  )}
                </span>
                <div style={{ display: 'flex', gap: '4px', flexShrink: 0 }}>
                  <button onClick={() => goTip(-1)} title="Conseil précédent" style={{ background: 'none', border: '1px solid #c4b5fd', borderRadius: '4px', padding: '4px 8px', cursor: 'pointer', color: '#5b21b6', display: 'flex', alignItems: 'center' }}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
                  </button>
                  <button onClick={() => goTip(1)} title="Conseil suivant" style={{ background: 'none', border: '1px solid #c4b5fd', borderRadius: '4px', padding: '4px 8px', cursor: 'pointer', color: '#5b21b6', display: 'flex', alignItems: 'center' }}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                  </button>
                </div>
              </div>

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
                  sessionMatiere={sessionMatiere}
                  onMatiereChange={setSessionMatiere}
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

          {page === 'mon-profil' && <MonProfil onNavigate={setPage} />}

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

      {tipModal && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 600 }}
          onClick={e => { if (e.target === e.currentTarget) setTipModal(null) }}
        >
          <div style={{ background: '#fff', borderRadius: '10px', padding: '24px', width: '420px', maxWidth: '92vw', boxShadow: '0 8px 32px rgba(0,0,0,0.18)', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
              <div style={{ fontSize: '14px', fontWeight: 700, color: '#3b0764' }}>{tipModal.titre}</div>
              <button onClick={() => setTipModal(null)} title="Fermer" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9ca3af', fontSize: '18px', lineHeight: 1, flexShrink: 0, padding: '0 2px' }}>×</button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {tipModal.lignes.map((l, i) => (
                <p key={i} style={{ fontSize: '13px', color: '#374151', lineHeight: 1.6, margin: 0 }}>{l}</p>
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setTipModal(null)} title="Fermer cette explication" style={{ padding: '7px 20px', fontSize: '13px', borderRadius: '6px', border: 'none', background: '#5b21b6', color: '#fff', cursor: 'pointer', fontWeight: 600 }}>
                Compris
              </button>
            </div>
          </div>
        </div>
      )}

      {inactivityWarning && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: '#fff', borderRadius: '12px', padding: '32px 28px', maxWidth: '380px', width: '90%', textAlign: 'center', boxShadow: '0 8px 32px rgba(0,0,0,0.2)' }}>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#1e293b', marginBottom: '10px' }}>Session inactive</div>
            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '24px', lineHeight: 1.6 }}>
              Vous allez être déconnecté dans{' '}
              <strong style={{ color: countdown <= 30 ? '#dc2626' : '#1e293b' }}>
                {countdown} seconde{countdown > 1 ? 's' : ''}
              </strong>{' '}
              en raison d'inactivité.
            </p>
            <button
              onClick={stayConnected}
              style={{ background: 'var(--bleu)', color: '#fff', border: 'none', borderRadius: '8px', padding: '10px 28px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}
            >
              Rester connecté
            </button>
          </div>
        </div>
      )}

      {toast && (
        <div style={{
          position: 'fixed',
          bottom: '28px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: '#1e40af',
          color: '#fff',
          padding: '12px 20px',
          borderRadius: '8px',
          fontSize: '14px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.18)',
          zIndex: 1000,
          maxWidth: '480px',
          textAlign: 'center',
          lineHeight: '1.5',
        }}>
          {toast}
        </div>
      )}
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
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
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
            <Route index element={<Navigate to="/admin/serveur" replace />} />
            <Route path="serveur"    element={<AdminServeur />} />
            <Route path="sessions"   element={<AdminSessions />} />
            <Route path="logs"       element={<AdminLogs />} />
            <Route path="activites"  element={<AdminActivites />} />
            <Route path="feedbacks"  element={<AdminFeedbacks />} />
            <Route path="profils"    element={<AdminProfils />} />
            <Route path="audit"       element={<AdminAudit />} />
            <Route path="tentatives" element={<AdminTentatives />} />
            <Route path="alertes"    element={<AdminAlertes />} />
            <Route path="compte"     element={<AdminCompte />} />
            <Route path="parametres" element={<AdminParametres />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
