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
import MesSequences from './components/MesSequences'
import MonReseau from './components/MonReseau'
import MonReseauSequences from './components/MonReseauSequences'
import BientotDisponible from './components/BientotDisponible'
import Accueil from './components/Accueil'
import SequenceForm from './components/SequenceForm'
import Optimiseur from './components/Optimiseur'
import Ambiguites from './components/Ambiguites'
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
import AdminCommunication from './pages/AdminCommunication'
import AdminAide from './pages/AdminAide'
import AdminMaintenance from './pages/AdminMaintenance'
import AdminAnalytique from './pages/AdminAnalytique'
import AdminAnalytiqueGeneral from './pages/AdminAnalytiqueGeneral'
import AdminAnalytiqueOutils from './pages/AdminAnalytiqueOutils'
import AdminAnalytiqueCommunaute from './pages/AdminAnalytiqueCommunaute'
import MesFeedbacks from './pages/MesFeedbacks'
import MesStats from './components/MesStats'
import AdminFiches from './pages/AdminFiches'
import AdminLayout from './components/AdminLayout'
import OfflineBanner from './components/OfflineBanner'
import UpdateBanner from './components/UpdateBanner'
import IOSInstallBanner from './components/IOSInstallBanner'
import { fetchWithTimeout, TIMEOUT_AUTH, TIMEOUT_STD, TIMEOUT_GROQ } from './utils/api.js'
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

const INACTIVITY_MS = 2 * 60 * 60 * 1000
const WARNING_SECS  = 300

function MainApp() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const matiere = user?.subject || 'Français'
  const matiereLabel = matiere === 'Langues Vivantes (LV)' && user?.langue_lv
    ? `LV - ${user.langue_lv}`
    : matiere

  const isMobile = window.innerWidth < 768
  const [page, setPage] = useState('accueil')
  const [prefillTheme, setPrefillTheme] = useState('')
  const [prefillSeq, setPrefillSeq] = useState(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [showNotation, setShowNotation] = useState(false)
  const [activites, setActivites] = useState([])
  const [texte, setTexte] = useState('')
  const [objet, setObjet] = useState('')
  const [resultat, setResultat] = useState(null)
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState(null)
  const [sessionMatiere, setSessionMatiere] = useState(matiere)
  const [toast, setToast] = useState(null)
  const [activiteTab, setActiviteTab] = useState('creer')
  const [alertDialog, setAlertDialog] = useState(null)
  const [selectedCard, setSelectedCard] = useState('sequence')
  const [inactivityWarning, setInactivityWarning] = useState(false)
  const [countdown, setCountdown] = useState(WARNING_SECS)
  const timerRef   = useRef(null)
  const cdRef      = useRef(null)
  const warningRef = useRef(false)
  const resultatRef = useRef(null)

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
        const r = await fetchWithTimeout('/api/heartbeat', { method: 'POST', credentials: 'include' }, TIMEOUT_AUTH)
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
    fetchWithTimeout(`/api/activites/${encodeURIComponent(sessionMatiere)}`, {}, TIMEOUT_STD)
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

  function isTexteGibberish(t) {
    const words = t.trim().split(/\s+/).filter(w => w.length > 2)
    if (words.length < 2) return false
    const vowels = /[aeiouyàâäéèêëîïôöùûüæœAEIOUYÀÂÄÉÈÊËÎÏÔÖÙÛÜÆŒ]/
    let suspect = 0
    for (const word of words) {
      const alpha = word.replace(/[^a-zA-ZÀ-ÿ]/g, '')
      if (alpha.length > 8) {
        const vRatio = alpha.split('').filter(c => vowels.test(c)).length / alpha.length
        if (vRatio < 0.15) suspect++
      }
    }
    return suspect / words.length > 0.25
  }

  async function generer() {
    if (!params.activite_key) {
      setAlertDialog('Sélectionnez un type d\'activité avant de générer.')
      return
    }
    if (!texte.trim()) {
      setAlertDialog(
        'Saisissez un texte source avant de générer — collez un extrait, dictez ou importez un fichier.' +
        (!params.avec_correction ? '\n\nSaviez-vous que vous pouvez inclure un corrigé complet ? Cochez « Avec correction » dans les paramètres.' : '')
      )
      return
    }
    if (isTexteGibberish(texte)) {
      setAlertDialog('Le texte saisi ne ressemble pas à un contenu pédagogique exploitable.\n\nCollez un extrait de cours ou d\'article, dictez à la voix, ou importez un fichier.')
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

      const res = await fetchWithTimeout('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body),
      }, TIMEOUT_GROQ)
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || `Erreur ${res.status}`)
      }
      const data = await res.json()
      setResultat(data.resultat)
      setTimeout(() => resultatRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)

      const countKey = `aschool_style_count_${params.activite_key}`
      const newCount = (parseInt(localStorage.getItem(countKey) || '0')) + 1
      localStorage.setItem(countKey, String(newCount))
      if (newCount === 3) {
        setToast('aSchool reconnaît maintenant votre façon de travailler sur ce type d\'activité.')
      }

      fetch('/api/mes-activites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          activite_key: params.activite_key,
          activite_label: activites.find(a => a.key === params.activite_key)?.label || params.activite_key,
          matiere: sessionMatiere,
          niveau: params.niveau,
          sous_type: params.sous_type || null,
          nb: params.nb || null,
          avec_correction: params.avec_correction,
          objet: objet.trim() || null,
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

  function chargerSequence(seq) {
    setPrefillSeq(seq)
    setPage('creer-sequence')
  }

  function chargerActivite(act) {
    setTexte(act.texte_source)
    setObjet(act.objet || '')
    setParamsWithSave({
      activite_key: act.activite_key,
      niveau: act.niveau,
      sous_type: act.sous_type || null,
      nb: act.nb || 5,
      avec_correction: act.avec_correction,
    })
    setResultat(act.resultat)
    setPage('creer-activite')
  }

  const profilIncomplet = user && (!user.prenom || !user.nom)

  return (
    <div className="flex flex-col h-screen overflow-hidden">

      {/* Blocage profil incomplet */}
      {profilIncomplet && page !== 'mon-profil' && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div style={{ background: '#fff', borderRadius: 12, padding: '32px 36px', maxWidth: 440, width: '100%', boxShadow: '0 16px 48px rgba(0,0,0,0.25)', textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 800, color: '#1e293b', marginBottom: 12 }}>Bienvenue sur aSchool !</div>
            <p style={{ fontSize: 14, color: '#374151', lineHeight: 1.7, marginBottom: 24 }}>
              Avant de commencer, veuillez compléter votre profil en renseignant votre <strong>prénom</strong> et votre <strong>nom</strong>.
            </p>
            <button
              onClick={() => setPage('mon-profil')}
              title="Compléter votre profil maintenant"
              className="btn-primary"
            >
              Compléter mon profil
            </button>
          </div>
        </div>
      )}

      <Header
        matiere={matiereLabel}
        email={user?.email}
        prenom={user?.prenom}
        nom={user?.nom}
        onLogout={logout}
        onNavigate={setPage}
        onFeedback={() => setShowFeedback(true)}
      />

      <div className="flex flex-1 min-h-0" style={{ paddingTop: 65 }}>
        <Sidebar page={page} onNavigate={setPage} onFeedback={() => setShowFeedback(true)} onNotation={() => setShowNotation(true)} />

        <main className={`flex-1 p-6 flex flex-col gap-4 ${['creer-activite', 'creer-sequence', 'optimiseur', 'ambiguites'].includes(page) ? 'overflow-hidden' : 'overflow-auto'}`}>
          {erreur && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm">
              {erreur}
            </div>
          )}

          {page === 'accueil' && (
            <Accueil
              user={user}
              matiereLabel={matiereLabel}
              niveau={params.niveau}
              onNavigate={setPage}
              onCharger={chargerActivite}
              onChargerSequence={chargerSequence}
            />
          )}

          {page === 'mes-outils' && (
            <>
              {/* Que voulez-vous faire ? */}
              {(() => {
                const S = { fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }
                const UL = { margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }
                const SUB = { marginTop: '4px', paddingLeft: '14px', display: 'flex', flexDirection: 'column', gap: '2px', listStyleType: 'circle', fontSize: '13px', color: '#374151', lineHeight: 1.6 }
                const HR = { border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }
                const TUTOS = {
                  activite: {
                    titre: 'Créer une activité — tout ce que vous pouvez faire',
                    contenu: (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        <div>
                          <div style={S}>1. Fournissez un texte source — 3 options</div>
                          <ul style={UL}>
                            <li>Collez directement un texte — extrait de manuel, article de presse, document élève</li>
                            <li>Dictez à la voix grâce au micro intégré — aSchool transcrit automatiquement</li>
                            <li>Scannez un document papier avec l'OCR — la photo est convertie en texte exploitable</li>
                          </ul>
                        </div>
                        <hr style={HR} />
                        <div>
                          <div style={S}>2. Configurez les paramètres</div>
                          <ul style={UL}>
                            <li>
                              <strong>Type d'activité</strong> — varie selon la matière :
                              <ul style={SUB}>
                                <li>Questions de compréhension</li>
                                <li>Analyse de texte / document</li>
                                <li>Résumé / synthèse</li>
                                <li>Production d'écrit</li>
                                <li>Fiche de révision</li>
                                <li>Exercices de vocabulaire</li>
                                <li style={{ color: '#94a3b8', fontStyle: 'italic' }}>et d'autres selon la matière…</li>
                              </ul>
                            </li>
                            <li><strong>Sous-type</strong> — précise la nature exacte (ex : inférence, lexique, mélange de types)</li>
                            <li><strong>Nombre de questions</strong> — disponible selon le type choisi</li>
                            <li><strong>Avec correction</strong> — génère le corrigé complet sous l'activité</li>
                          </ul>
                        </div>
                        <hr style={HR} />
                        <div>
                          <div style={S}>3. Exploitez le résultat</div>
                          <ul style={UL}>
                            <li>Cliquez sur "Générer" — activité prête en quelques secondes</li>
                            <li>Régénérez sans hésiter — chaque génération est différente</li>
                            <li>Sauvegardez dans "Mes activités" — rechargeable en un clic à tout moment</li>
                            <li>Partagez par email avec un collègue depuis le résultat</li>
                          </ul>
                        </div>
                        <hr style={HR} />
                        <p style={{ margin: 0, fontSize: '12px', color: '#64748b', background: '#f8fafc', borderRadius: '6px', padding: '8px 12px', lineHeight: 1.6, borderLeft: '3px solid #cbd5e1' }}>
                          aSchool apprend votre style : à partir de la 3e sauvegarde d'un même type, il adapte automatiquement le ton et la formulation à votre façon d'enseigner — sans rien configurer.
                        </p>
                      </div>
                    ),
                  },
                  sequence: {
                    titre: 'Créer une séquence — ce que la fonctionnalité fera',
                    contenu: (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        <div>
                          <div style={S}>1. Décrivez votre objectif pédagogique</div>
                          <ul style={UL}>
                            <li>Formulez ce que vos élèves doivent savoir ou savoir-faire à la fin de la séquence</li>
                            <li>Précisez le contexte : nombre de séances, durée totale, contraintes éventuelles</li>
                            <li>Vous pouvez dicter l'objectif à la voix ou le coller depuis un autre document</li>
                          </ul>
                        </div>
                        <hr style={HR} />
                        <div>
                          <div style={S}>2. Paramétrez la structure</div>
                          <ul style={UL}>
                            <li><strong>Nombre de phases ou de séances</strong> — aSchool répartit les apprentissages</li>
                            <li>
                              <strong>Types de phases à inclure</strong> :
                              <ul style={SUB}>
                                <li>Découverte / mise en situation</li>
                                <li>Structuration des connaissances</li>
                                <li>Entraînement / exercices</li>
                                <li>Synthèse / bilan</li>
                                <li>Évaluation finale</li>
                              </ul>
                            </li>
                            <li><strong>Avec ou sans corrigé enseignant</strong> pour chaque phase</li>
                          </ul>
                        </div>
                        <hr style={HR} />
                        <div>
                          <div style={S}>3. aSchool génère la séquence complète</div>
                          <ul style={UL}>
                            <li>Chaque phase est détaillée : nom, durée, objectif, consignes élèves, matériel</li>
                            <li>Progression garantie : pas de rupture conceptuelle, charge cognitive maîtrisée</li>
                            <li>Ancrage mémoriel intégré : synthèse, révision et bilan prévus dans la structure</li>
                            <li>Séquence exportable et partageable avec des collègues</li>
                          </ul>
                        </div>
                      </div>
                    ),
                  },
                  optimiseur: {
                    titre: 'Améliorer une séquence — comment ça fonctionne',
                    contenu: (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        <div>
                          <div style={S}>1. Soumettez votre séquence</div>
                          <ul style={UL}>
                            <li>Collez une séquence existante — planning de cours, progression rédigée, fichier de préparation</li>
                            <li>Un bouton "Tester sur un exemple" permet de découvrir la fonctionnalité sans séquence sous la main</li>
                          </ul>
                        </div>
                        <hr style={HR} />
                        <div>
                          <div style={S}>2. aSchool analyse sur 6 critères</div>
                          <ul style={UL}>
                            <li>Rupture conceptuelle — une phase suppose une notion non encore construite</li>
                            <li>Surcharge cognitive — trop de notions nouvelles sur un temps trop court</li>
                            <li>Consigne ambiguë — formulation pouvant être mal interprétée</li>
                            <li>Activité inefficace — exercice sans lien réel avec l'objectif déclaré</li>
                            <li>Progression déséquilibrée — phases trop courtes ou trop longues</li>
                            <li>Ancrage mémoriel manquant — pas de consolidation avant l'évaluation</li>
                          </ul>
                        </div>
                        <hr style={HR} />
                        <div>
                          <div style={S}>3. Récupérez le résultat</div>
                          <ul style={UL}>
                            <li>Un score global : Bon · Moyen · À revoir</li>
                            <li>La liste des problèmes détectés avec leur description précise</li>
                            <li>La séquence réécrite avec toutes les corrections intégrées</li>
                          </ul>
                        </div>
                      </div>
                    ),
                  },
                }
                const tuto = TUTOS[selectedCard] || TUTOS.sequence
                function selectCard(id) {
                  setSelectedCard(id)
                }
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Que voulez-vous faire ?
                    </div>
                    {isMobile ? (
                      /* Mobile — sections verticales */
                      (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>

                          {/* ACTIVITÉ */}
                          <div>
                            <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>Activité</div>
                            <button onClick={() => setPage('creer-activite')} title="Créer une activité pédagogique"
                              style={{ width: '100%', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', cursor: 'pointer', textAlign: 'left' }}>
                              <div>
                                <div style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b' }}>Créer une activité</div>
                                <div style={{ fontSize: '12px', color: '#64748b', marginTop: '3px' }}>Texte source → activité prête à l'emploi</div>
                              </div>
                              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--bordeaux)" strokeWidth="2.5" style={{ flexShrink: 0 }}><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                            </button>
                          </div>

                          {/* SÉQUENCE */}
                          <div>
                            <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>Séquence</div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                              {[
                                { label: 'Créer une séquence',    desc: 'Objectif pédagogique → séquence structurée',  action: () => setPage('creer-sequence') },
                                { label: 'Améliorer une séquence', desc: 'Séquence existante → corrigée et optimisée', action: () => setPage('optimiseur') },
                              ].map((t, i) => (
                                <button key={i} onClick={t.action} title={t.label}
                                  style={{ width: '100%', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', cursor: 'pointer', textAlign: 'left' }}>
                                  <div>
                                    <div style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b' }}>{t.label}</div>
                                    <div style={{ fontSize: '12px', color: '#64748b', marginTop: '3px' }}>{t.desc}</div>
                                  </div>
                                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--bordeaux)" strokeWidth="2.5" style={{ flexShrink: 0 }}><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                                </button>
                              ))}
                            </div>
                          </div>

                          {/* ANALYSER */}
                          <div>
                            <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>Analyser et diagnostiquer</div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                              {[
                                { label: 'Ambiguïtés cognitives', desc: 'Exercice ou énoncé → zones de risque + version corrigée', action: () => setPage('ambiguites') },
                                { label: 'Qualité des consignes', desc: 'Une consigne → analyse didactique + version optimisée',  action: () => setPage('consigne') },
                                { label: 'Équité pédagogique',    desc: 'Évaluation → 3 biais détectés + version corrigée',       action: () => setPage('equite') },
                              ].map((t, i) => (
                                <button key={i} onClick={t.action} title={t.label}
                                  style={{ width: '100%', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', cursor: 'pointer', textAlign: 'left' }}>
                                  <div>
                                    <div style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b' }}>{t.label}</div>
                                    <div style={{ fontSize: '12px', color: '#64748b', marginTop: '3px' }}>{t.desc}</div>
                                  </div>
                                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--bordeaux)" strokeWidth="2.5" style={{ flexShrink: 0 }}><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                                </button>
                              ))}
                            </div>
                          </div>

                        </div>
                      )
                    ) : (
                    /* Desktop — 3 sections */
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

                      {/* ── ACTIVITÉ ── */}
                      <div>
                        <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px' }}>Activité</div>
                        <div
                          onClick={() => setPage('creer-activite')}
                          style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: '8px', cursor: 'pointer' }}
                        >
                          <span style={{ fontSize: '13px', fontWeight: 700, color: '#1e293b' }}>Créer une activité</span>
                          <p style={{ fontSize: '12px', color: '#64748b', margin: 0, lineHeight: 1.5 }}>
                            Un texte, une dictée ou un scan → activité prête à distribuer
                          </p>
                        </div>
                      </div>

                      {/* ── SÉQUENCE ── */}
                      <div>
                        <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px' }}>Séquence</div>
                        <div style={{ display: 'flex', gap: '10px' }}>

                          {/* Créer une séquence */}
                          <div onClick={() => selectCard('sequence')}
                            style={{ flex: 1, background: '#fff', border: `${selectedCard === 'sequence' ? '2' : '1'}px solid ${selectedCard === 'sequence' ? 'var(--bordeaux)' : '#e2e8f0'}`, borderRadius: '8px', padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: '8px', cursor: 'pointer' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '7px', flexWrap: 'wrap' }}>
                              <span style={{ fontSize: '13px', fontWeight: 700, color: selectedCard === 'sequence' ? 'var(--bordeaux)' : '#1e293b' }}>Créer une séquence</span>
                              {selectedCard === 'sequence' && <span style={{ fontSize: '10px', background: 'var(--bordeaux)', color: '#fff', borderRadius: '4px', padding: '1px 7px', fontWeight: 600 }}>Vous y êtes</span>}
                            </div>
                            <p style={{ fontSize: '12px', color: '#64748b', margin: 0, lineHeight: 1.5, flex: 1 }}>
                              Un objectif pédagogique → séquence complète structurée de A à Z
                            </p>
                            <div className="flex justify-end" style={{ marginTop: 'auto' }}>
                              <button className="btn-primary"
                                onClick={e => { e.stopPropagation(); setPage('creer-sequence') }}
                                title="Commencer à créer une séquence pédagogique">
                                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                                Commencer
                              </button>
                            </div>
                          </div>

                          {/* Améliorer une séquence */}
                          <div onClick={() => selectCard('optimiseur')}
                            style={{ flex: 1, background: '#fff', border: `${selectedCard === 'optimiseur' ? '2' : '1'}px solid ${selectedCard === 'optimiseur' ? 'var(--bordeaux)' : '#e2e8f0'}`, borderRadius: '8px', padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: '8px', cursor: 'pointer' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '7px', flexWrap: 'wrap' }}>
                              <span style={{ fontSize: '13px', fontWeight: 700, color: selectedCard === 'optimiseur' ? 'var(--bordeaux)' : '#1e293b' }}>Améliorer une séquence</span>
                              {selectedCard === 'optimiseur' && <span style={{ fontSize: '10px', background: 'var(--bordeaux)', color: '#fff', borderRadius: '4px', padding: '1px 7px', fontWeight: 600 }}>Vous y êtes</span>}
                            </div>
                            <p style={{ fontSize: '12px', color: '#64748b', margin: 0, lineHeight: 1.5, flex: 1 }}>
                              Collez une séquence existante → aSchool la corrige et l'optimise
                            </p>
                            <div className="flex justify-end" style={{ marginTop: 'auto' }}>
                              <button className="btn-primary"
                                onClick={e => { e.stopPropagation(); setPage('optimiseur') }}
                                title="Commencer à améliorer une séquence pédagogique existante">
                                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                                Commencer
                              </button>
                            </div>
                          </div>

                        </div>
                      </div>

                      {/* ── ANALYSER ET DIAGNOSTIQUER ── */}
                      <div>
                        <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px' }}>Analyser et diagnostiquer</div>
                        <div style={{ display: 'flex', gap: '10px' }}>

                          {/* L2 — Ambiguïtés cognitives */}
                          <div onClick={() => setPage('ambiguites')}
                            style={{ flex: 1, background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: '8px', cursor: 'pointer' }}>
                            <span style={{ fontSize: '13px', fontWeight: 700, color: '#1e293b' }}>Ambiguïtés cognitives</span>
                            <p style={{ fontSize: '12px', color: '#64748b', margin: 0, lineHeight: 1.5, flex: 1 }}>
                              Exercice ou énoncé → zones de risque d'incompréhension + version corrigée
                            </p>
                            <div className="flex justify-end" style={{ marginTop: 'auto' }}>
                              <button className="btn-primary"
                                onClick={e => { e.stopPropagation(); setPage('ambiguites') }}
                                title="Analyser les zones d'ambiguïté cognitive d'un exercice ou énoncé">
                                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                                Analyser
                              </button>
                            </div>
                          </div>

                          {/* L5 — Qualité des consignes */}
                          <div onClick={() => setPage('consigne')}
                            style={{ flex: 1, background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: '8px', cursor: 'pointer' }}>
                            <span style={{ fontSize: '13px', fontWeight: 700, color: '#1e293b' }}>Qualité des consignes</span>
                            <p style={{ fontSize: '12px', color: '#64748b', margin: 0, lineHeight: 1.5, flex: 1 }}>
                              Une consigne isolée → analyse didactique + version optimisée
                            </p>
                            <div className="flex justify-end" style={{ marginTop: 'auto' }}>
                              <button className="btn-primary"
                                onClick={e => { e.stopPropagation(); setPage('consigne') }}
                                title="Analyser la qualité didactique d'une consigne">
                                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                                Analyser
                              </button>
                            </div>
                          </div>

                          {/* L6 — Équité pédagogique */}
                          <div onClick={() => setPage('equite')}
                            style={{ flex: 1, background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: '8px', cursor: 'pointer' }}>
                            <span style={{ fontSize: '13px', fontWeight: 700, color: '#1e293b' }}>Équité pédagogique</span>
                            <p style={{ fontSize: '12px', color: '#64748b', margin: 0, lineHeight: 1.5, flex: 1 }}>
                              Évaluation → 3 biais détectés (contenu, difficulté, émotionnel) + version corrigée
                            </p>
                            <div className="flex justify-end" style={{ marginTop: 'auto' }}>
                              <button className="btn-primary"
                                onClick={e => { e.stopPropagation(); setPage('equite') }}
                                title="Auditer l'équité pédagogique d'une évaluation">
                                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                                Auditer
                              </button>
                            </div>
                          </div>

                        </div>
                      </div>

                    </div>
                    )}

                    {/* Tutoriel — masqué sur mobile */}
                    {!isMobile && (
                      <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '18px 20px' }}>
                        <div style={{ fontSize: '13px', fontWeight: 700, color: '#1e293b', marginBottom: '14px' }}>{tuto.titre}</div>
                        {tuto.contenu}
                      </div>
                    )}

                  </div>
                )
              })()}


            </>
          )}

          {page === 'creer-activite' && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', flexShrink: 0, alignItems: 'center' }}>
                <button
                  onClick={() => setActiviteTab('creer')}
                  title="Formulaire de création d'activité"
                  style={{ padding: '10px 20px', fontSize: '13px', fontWeight: activiteTab === 'creer' ? 700 : 400, color: activiteTab === 'creer' ? 'var(--bordeaux)' : '#6b7280', border: 'none', background: 'none', cursor: 'pointer', borderBottom: activiteTab === 'creer' ? '2px solid var(--bordeaux)' : '2px solid transparent', marginBottom: '-1px' }}
                >
                  Nouvelle activité
                </button>
                <button
                  onClick={() => setActiviteTab('aide')}
                  title="Comment créer une activité — guide pas à pas"
                  style={{ padding: '10px 20px', fontSize: '13px', fontWeight: activiteTab === 'aide' ? 700 : 400, color: activiteTab === 'aide' ? 'var(--bordeaux)' : '#6b7280', border: 'none', background: 'none', cursor: 'pointer', borderBottom: activiteTab === 'aide' ? '2px solid var(--bordeaux)' : '2px solid transparent', marginBottom: '-1px' }}
                >
                  Comment ça marche
                </button>
                {activiteTab === 'creer' && (
                  <button
                    className="btn-primary"
                    onClick={generer}
                    disabled={loading}
                    title="Lancer la génération de l'activité avec aSchool"
                    style={{ marginLeft: 'auto', marginRight: 8 }}
                  >
                    {loading
                      ? <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/></svg>
                      : <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>}
                    {loading ? 'Génération en cours...' : 'Générer l\'activité'}
                  </button>
                )}
              </div>

              <div style={{ flex: 1, overflowY: 'auto', minHeight: 0, paddingTop: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
              {activiteTab === 'creer' && (
                <>
                  <TexteSource texte={texte} onChange={setTexte} objet={objet} onObjetChange={setObjet} matiere={sessionMatiere} />
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
                  <div ref={resultatRef}>
                    <ZoneResultat
                      resultat={resultat}
                      onRegenerer={generer}
                      loading={loading}
                      email={user?.email}
                    />
                  </div>
                </>
              )}

              {activiteTab === 'aide' && (
                <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '24px', flex: 1 }}>
                  <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '13px', marginBottom: '16px' }}>Créer une activité — tout ce que vous pouvez faire</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    <div>
                      <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>1. Fournissez un texte source — 3 options</div>
                      <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                        <li>Collez directement un texte — extrait de manuel, article de presse, document élève</li>
                        <li>Dictez à la voix grâce au micro intégré — aSchool transcrit automatiquement</li>
                        <li>Scannez un document papier avec l'OCR — la photo est convertie en texte exploitable</li>
                        <li><strong>Pas de texte sous la main ?</strong> Cliquez sur <strong>Tester un exemple</strong> (en haut à droite du texte source) pour pré-remplir avec un extrait adapté à votre matière.</li>
                      </ul>
                    </div>
                    <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
                    <div>
                      <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>2. Configurez les paramètres</div>
                      <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                        <li><strong>Type d'activité</strong> — varie selon la matière : questions de compréhension, analyse de texte, résumé, production d'écrit, fiche de révision…</li>
                        <li><strong>Sous-type</strong> — précise la nature exacte (ex : inférence, lexique, mélange de types)</li>
                        <li><strong>Nombre de questions</strong> — disponible selon le type choisi</li>
                        <li><strong>Avec correction</strong> — génère le corrigé complet sous l'activité</li>
                      </ul>
                    </div>
                    <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
                    <div>
                      <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '12px', marginBottom: '7px' }}>3. Exploitez le résultat</div>
                      <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                        <li>Cliquez sur "Générer" — activité prête en quelques secondes</li>
                        <li>Régénérez sans hésiter — chaque génération est différente</li>
                        <li>Sauvegardez dans "Mes activités" — rechargeable en un clic à tout moment</li>
                        <li>Partagez par email avec un collègue depuis le résultat</li>
                      </ul>
                    </div>
                    <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />
                    <p style={{ margin: 0, fontSize: '12px', color: '#64748b', background: '#f8fafc', borderRadius: '6px', padding: '8px 12px', lineHeight: 1.6, borderLeft: '3px solid #cbd5e1' }}>
                      aSchool apprend votre style : à partir de la 3e sauvegarde d'un même type, il adapte automatiquement le ton et la formulation à votre façon d'enseigner — sans rien configurer.
                    </p>
                  </div>
                </div>
              )}
              </div>
            </div>
          )}

          {page === 'creer-sequence' && (
            <SequenceForm
              matiere={sessionMatiere}
              niveau={params.niveau}
              onNavigate={setPage}
              prefillTheme={prefillTheme}
              onPrefillUsed={() => setPrefillTheme('')}
              prefillSeq={prefillSeq}
              onPrefillSeqUsed={() => setPrefillSeq(null)}
            />
          )}

          {page === 'mes-activites' && (
            <MesActivites
              onCharger={chargerActivite}
              sessionMatiere={sessionMatiere}
              sessionNiveau={params.niveau}
              onNavigate={setPage}
              userName={`${user?.prenom || ''} ${user?.nom || ''}`.trim()}
            />
          )}

          {page === 'mes-sequences' && (
            <MesSequences
              onCharger={chargerSequence}
              sessionMatiere={sessionMatiere}
              sessionNiveau={params.niveau}
              onNavigate={setPage}
              userName={`${user?.prenom || ''} ${user?.nom || ''}`.trim()}
            />
          )}

          {page === 'mon-reseau-activites' && (
            <MonReseau
              onCharger={chargerActivite}
              sessionMatiere={sessionMatiere}
              sessionNiveau={params.niveau}
            />
          )}

          {page === 'mon-reseau-sequences' && (
            <MonReseauSequences
              onCharger={chargerSequence}
              sessionMatiere={sessionMatiere}
              sessionNiveau={params.niveau}
            />
          )}

          {page === 'optimiseur' && (
            <Optimiseur
              defaultMatiere={sessionMatiere}
              defaultNiveau={params.niveau}
              onNavigate={setPage}
            />
          )}

          {page === 'ambiguites' && (
            <Ambiguites
              matiere={sessionMatiere}
              niveau={params.niveau}
              onNavigate={setPage}
              onCreateSequence={(reformulation) => { setPrefillTheme(reformulation); setPage('creer-sequence') }}
            />
          )}

          {page === 'consigne' && (
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center', textAlign: 'center' }}>
              <div style={{ fontSize: '15px', fontWeight: 700, color: '#1e293b' }}>Analyseur de qualité des consignes</div>
              <p style={{ fontSize: '13px', color: '#64748b', margin: 0, maxWidth: '400px', lineHeight: 1.6 }}>
                Outil en cours de développement.
              </p>
              <button onClick={() => setPage('mes-outils')} title="Retour au menu Mes outils"
                style={{ fontSize: '12px', color: '#6366f1', background: 'none', border: '1px solid #c7d2fe', borderRadius: '5px', padding: '5px 14px', cursor: 'pointer' }}>
                ← Retour aux outils
              </button>
            </div>
          )}

          {page === 'equite' && (
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center', textAlign: 'center' }}>
              <div style={{ fontSize: '15px', fontWeight: 700, color: '#1e293b' }}>Détecteur d'équité pédagogique</div>
              <p style={{ fontSize: '13px', color: '#64748b', margin: 0, maxWidth: '400px', lineHeight: 1.6 }}>
                Outil en cours de développement.
              </p>
              <button onClick={() => setPage('mes-outils')} title="Retour au menu Mes outils"
                style={{ fontSize: '12px', color: '#6366f1', background: 'none', border: '1px solid #c7d2fe', borderRadius: '5px', padding: '5px 14px', cursor: 'pointer' }}>
                ← Retour aux outils
              </button>
            </div>
          )}

          {page === 'bientot-disponible' && <BientotDisponible />}

          {page === 'mon-profil' && <MonProfil onNavigate={setPage} />}


          {page === 'aide' && <Aide />}

          {page === 'mes-feedbacks' && <MesFeedbacks />}

          {page === 'mes-stats' && <MesStats user={user} />}

          {page === 'apropos' && <APropos email={user?.email} matiere={user?.subject || 'Français'} />}
        </main>
      </div>

      <Footer />
      {showFeedback && <Feedback onClose={() => setShowFeedback(false)} />}
      {showNotation && <Notation onClose={() => setShowNotation(false)} />}

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

      {alertDialog && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: '#fff', borderRadius: '12px', padding: '28px 24px', maxWidth: '380px', width: '90%', textAlign: 'center', boxShadow: '0 8px 32px rgba(0,0,0,0.2)' }}>
            <div style={{ fontSize: '14px', color: '#1e293b', marginBottom: '20px', lineHeight: 1.6, whiteSpace: 'pre-line' }}>{alertDialog}</div>
            <button
              onClick={() => setAlertDialog(null)}
              title="Fermer ce message"
              style={{ background: 'var(--bleu)', color: '#fff', border: 'none', borderRadius: '8px', padding: '9px 28px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}
            >
              OK
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
        <UpdateBanner />
        <OfflineBanner />
        <IOSInstallBanner />
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
            <Route path="compte"        element={<AdminCompte />} />
            <Route path="parametres"    element={<AdminParametres />} />
            <Route path="communication" element={<AdminCommunication />} />
            <Route path="aide"          element={<AdminAide />} />
            <Route path="maintenance"   element={<AdminMaintenance />} />
            <Route path="analytique">
              <Route index element={<Navigate to="/admin/analytique/general" replace />} />
              <Route path="general"    element={<AdminAnalytiqueGeneral />} />
              <Route path="activites"  element={<AdminAnalytique />} />
              <Route path="outils"     element={<AdminAnalytiqueOutils />} />
              <Route path="communaute" element={<AdminAnalytiqueCommunaute />} />
            </Route>
            <Route path="fiches"       element={<AdminFiches />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
