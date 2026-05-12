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
import Bibliotheque from './components/Bibliotheque'
import BientotDisponible from './components/BientotDisponible'
import Accueil from './components/Accueil'
import SequenceForm from './components/SequenceForm'
import Optimiseur from './components/Optimiseur'
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
  const [formVisible, setFormVisible] = useState(false)
  const [seqFormVisible, setSeqFormVisible] = useState(false)
  const [selectedCard, setSelectedCard] = useState('activite')
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
    setPage('mes-outils')
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header
        matiere={matiereLabel}
        email={user?.email}
        prenom={user?.prenom}
        nom={user?.nom}
        onLogout={logout}
        onNavigate={setPage}
      />

      <div className="flex flex-1 min-h-0" style={{ paddingTop: 65 }}>
        <Sidebar page={page} onNavigate={setPage} onFeedback={() => setShowFeedback(true)} onNotation={() => setShowNotation(true)} />

        <main className="flex-1 p-6 flex flex-col gap-4 overflow-auto">
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
                            <li>Dictez à la voix grâce au micro intégré — A-SCHOOL transcrit automatiquement</li>
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
                          A-SCHOOL apprend votre style : à partir de la 3e sauvegarde d'un même type, il adapte automatiquement le ton et la formulation à votre façon d'enseigner — sans rien configurer.
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
                            <li><strong>Nombre de phases ou de séances</strong> — A-SCHOOL répartit les apprentissages</li>
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
                          <div style={S}>3. A-SCHOOL génère la séquence complète</div>
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
                          <div style={S}>2. A-SCHOOL analyse sur 6 critères</div>
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
                const tuto = TUTOS[selectedCard] || TUTOS.activite
                function selectCard(id) {
                  setSelectedCard(id)
                  if (id !== 'activite') setFormVisible(false)
                  if (id !== 'sequence') setSeqFormVisible(false)
                }
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Que voulez-vous faire ?
                    </div>
                    {isMobile ? (
                      /* Mobile — liste verticale, un outil par ligne */
                      (!formVisible && !seqFormVisible) && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {[
                            { id: 'activite',  label: 'Créer une activité',    desc: 'Texte source → activité prête à l\'emploi',       action: () => { setFormVisible(true); setSelectedCard('activite') } },
                            { id: 'sequence',  label: 'Créer une séquence',    desc: 'Objectif pédagogique → séquence structurée',      action: () => { setSeqFormVisible(true); setFormVisible(false); setSelectedCard('sequence') } },
                            { id: 'optimiseur',label: 'Améliorer une séquence',desc: 'Séquence existante → corrigée et optimisée',      action: () => setPage('optimiseur') },
                          ].map(tool => (
                            <button
                              key={tool.id}
                              onClick={tool.action}
                              title={tool.label}
                              style={{ width: '100%', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', cursor: 'pointer', textAlign: 'left' }}
                            >
                              <div>
                                <div style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b' }}>{tool.label}</div>
                                <div style={{ fontSize: '12px', color: '#64748b', marginTop: '3px' }}>{tool.desc}</div>
                              </div>
                              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--bordeaux)" strokeWidth="2.5" style={{ flexShrink: 0 }}><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                            </button>
                          ))}
                        </div>
                      )
                    ) : (
                    <div style={{ display: 'flex', gap: '10px' }}>

                      {/* Carte 1 — Créer une activité */}
                      <div
                        onClick={() => selectCard('activite')}
                        style={{ flex: 1, background: '#fff', border: `2px solid ${selectedCard === 'activite' ? 'var(--bordeaux)' : '#e2e8f0'}`, borderRadius: '8px', padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: '8px', cursor: 'pointer' }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '7px', flexWrap: 'wrap' }}>
                          <span style={{ fontSize: '13px', fontWeight: 700, color: selectedCard === 'activite' ? 'var(--bordeaux)' : '#1e293b' }}>Créer une activité</span>
                          {selectedCard === 'activite' && <span style={{ fontSize: '10px', background: 'var(--bordeaux)', color: '#fff', borderRadius: '4px', padding: '1px 7px', fontWeight: 600 }}>Vous y êtes</span>}
                        </div>
                        <p style={{ fontSize: '12px', color: '#64748b', margin: 0, lineHeight: 1.5 }}>
                          Un sujet ou un texte → une activité prête à l'emploi (résumé, analyse, exercice…)
                        </p>
                        <div className="flex justify-end" style={{ marginTop: 'auto' }}>
                          <button
                            className="btn-primary"
                            onClick={e => { e.stopPropagation(); setFormVisible(true); setSelectedCard('activite') }}
                            title="Commencer à créer une activité pédagogique"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                            Commencer
                          </button>
                        </div>
                      </div>

                      {/* Carte 2 — Créer une séquence */}
                      <div
                        onClick={() => selectCard('sequence')}
                        style={{ flex: 1, background: selectedCard === 'sequence' ? '#fff' : '#f8fafc', border: `${selectedCard === 'sequence' ? '2' : '1'}px solid ${selectedCard === 'sequence' ? 'var(--bordeaux)' : '#e2e8f0'}`, borderRadius: '8px', padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: '8px', opacity: selectedCard === 'sequence' ? 1 : 0.6, cursor: 'pointer' }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '7px', flexWrap: 'wrap' }}>
                          <span style={{ fontSize: '13px', fontWeight: 700, color: selectedCard === 'sequence' ? 'var(--bordeaux)' : '#475569' }}>Créer une séquence</span>
                          {selectedCard === 'sequence' && <span style={{ fontSize: '10px', background: 'var(--bordeaux)', color: '#fff', borderRadius: '4px', padding: '1px 7px', fontWeight: 600 }}>Vous y êtes</span>}
                        </div>
                        <p style={{ fontSize: '12px', color: selectedCard === 'sequence' ? '#64748b' : '#94a3b8', margin: 0, lineHeight: 1.5, flex: 1 }}>
                          Un objectif pédagogique → séquence complète structurée de A à Z
                        </p>
                        <div className="flex justify-end" style={{ marginTop: 'auto' }}>
                          <button
                            className="btn-primary"
                            onClick={e => { e.stopPropagation(); setSeqFormVisible(true); setFormVisible(false); setSelectedCard('sequence') }}
                            title="Commencer à créer une séquence pédagogique"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                            Commencer
                          </button>
                        </div>
                      </div>

                      {/* Carte 3 — Améliorer une séquence */}
                      <div
                        onClick={() => selectCard('optimiseur')}
                        style={{ flex: 1, background: '#fff', border: `${selectedCard === 'optimiseur' ? '2' : '1'}px solid ${selectedCard === 'optimiseur' ? 'var(--bordeaux)' : '#e2e8f0'}`, borderRadius: '8px', padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: '8px', cursor: 'pointer' }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '7px', flexWrap: 'wrap' }}>
                          <span style={{ fontSize: '13px', fontWeight: 700, color: selectedCard === 'optimiseur' ? 'var(--bordeaux)' : '#1e293b' }}>Améliorer une séquence</span>
                          {selectedCard === 'optimiseur' && <span style={{ fontSize: '10px', background: 'var(--bordeaux)', color: '#fff', borderRadius: '4px', padding: '1px 7px', fontWeight: 600 }}>Vous y êtes</span>}
                        </div>
                        <p style={{ fontSize: '12px', color: '#64748b', margin: 0, lineHeight: 1.5, flex: 1 }}>
                          Collez une séquence existante → A-SCHOOL la corrige et l'optimise
                        </p>
                        <div className="flex justify-end" style={{ marginTop: 'auto' }}>
                          <button
                            className="btn-primary"
                            onClick={e => { e.stopPropagation(); setPage('optimiseur') }}
                            title="Commencer à améliorer une séquence pédagogique existante"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                            Commencer
                          </button>
                        </div>
                      </div>

                    </div>
                    )}

                    {/* Tutoriel */}
                    {!formVisible && !seqFormVisible && (
                      <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '18px 20px' }}>
                        <div style={{ fontSize: '13px', fontWeight: 700, color: '#1e293b', marginBottom: '14px' }}>{tuto.titre}</div>
                        {tuto.contenu}
                      </div>
                    )}

                    {/* Formulaire séquence */}
                    {seqFormVisible && selectedCard === 'sequence' && (
                      <SequenceForm
                        matiere={sessionMatiere}
                        niveau={params.niveau}
                        onNavigate={setPage}
                      />
                    )}
                  </div>
                )
              })()}


              {formVisible && (
                <>
                  <TexteSource texte={texte} onChange={setTexte} objet={objet} onObjetChange={setObjet} />
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
            </>
          )}

          {page === 'mes-activites' && (
            <MesActivites
              onCharger={chargerActivite}
              sessionMatiere={sessionMatiere}
              sessionNiveau={params.niveau}
              onNavigate={setPage}
            />
          )}

          {page === 'bibliotheque' && (
            <Bibliotheque
              onCharger={chargerActivite}
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

          {page === 'bientot-disponible' && <BientotDisponible />}

          {page === 'mon-profil' && <MonProfil onNavigate={setPage} />}

          {page === 'historique' && (
            <div className="bg-white rounded border border-gray-200 p-8 text-center text-gray-400 text-sm">
              Historique — disponible en Phase 3 (base de données)
            </div>
          )}

          {page === 'aide' && <Aide />}

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
