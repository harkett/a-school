import { useState, useEffect, useLayoutEffect, useRef } from 'react'
import { showError, registerFeedbackOpener } from './errorDialog'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import Footer from './components/Footer'
import VisiteGuidee from './components/VisiteGuidee'
import FenetreGuide from './components/FenetreGuide'
import FenetreGuideSeance from './components/FenetreGuideSeance'
import FenetreGuideSequence from './components/FenetreGuideSequence'
import FenetreGuideContenusActivites from './components/FenetreGuideContenusActivites'
import FenetreGuideContenusSeances from './components/FenetreGuideContenusSeances'
import FenetreGuideContenusSequences from './components/FenetreGuideContenusSequences'
import Aide from './components/Aide'
import APropos from './components/APropos'
import Feedback from './components/Feedback'
import MesContenus from './components/MesContenus'
import SeanceEcran from './components/SeanceEcran'
import SequenceEcran from './components/SequenceEcran'
import ActiviteEcran from './components/ActiviteEcran'
import BientotDisponible from './components/BientotDisponible'
import Accueil from './components/Accueil'
import Ambiguites from './components/Ambiguites'
import Consigne from './components/Consigne'
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
import AdminFeedbacks from './pages/AdminFeedbacks'
import AdminProfils from './pages/AdminProfils'
import AdminParametresGeneration from './pages/AdminParametresGeneration'
import AdminPrompts from './pages/AdminPrompts'
import AdminParametresEmail from './pages/AdminParametresEmail'
import AdminParametres from './pages/AdminParametres'
import AdminSessions from './pages/AdminSessions'
import AdminServeur from './pages/AdminServeur'
import AdminAudit from './pages/AdminAudit'
import AdminAlertes from './pages/AdminAlertes'
import AdminTentatives from './pages/AdminTentatives'
import AdminCompte from './pages/AdminCompte'
import AdminCommunication from './pages/AdminCommunication'
import AdminAide from './pages/AdminAide'
import AdminReferentiels from './pages/AdminReferentiels'
import AdminMiseEnRoute from './pages/AdminMiseEnRoute'
import Labo from './pages/Labo'   // écran labo générique (bac à sable réutilisable)
import AdminReferentielsConsulter from './pages/AdminReferentielsConsulter'
import AdminContenu from './pages/AdminContenu'
import AdminMaintenance from './pages/AdminMaintenance'
import AdminBase from './pages/AdminBase'
import AdminBaseDemos from './pages/AdminBaseDemos'
import AdminAnalytique from './pages/AdminAnalytique'
import AdminAnalytiqueGeneral from './pages/AdminAnalytiqueGeneral'
import MesFeedbacks from './pages/MesFeedbacks'
import MesStats from './components/MesStats'
import AdminLayout from './components/AdminLayout'
import OfflineBanner from './components/OfflineBanner'
import UpdateBanner from './components/UpdateBanner'
import ErrorDialog from './components/ErrorDialog'
import ConfirmDialog from './components/ConfirmDialog'
import IOSInstallBanner from './components/IOSInstallBanner'
import DialogueAutreCouple from './components/contenus/DialogueAutreCouple.jsx'
import { correspondProfil } from './utils/activites.js'
import { fetchWithTimeout, apiFetch, lireReponse, messagePourEcran, TIMEOUT_AUTH, TIMEOUT_STD } from './utils/api.js'
import { libelleEcran } from './utils/ecrans.js'
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
  const { user, logout, refreshUser } = useAuth()
  const navigate = useNavigate()

  // Garde-fou : pas de matière = pas de couple → profil BLOQUANT (l'app force « Mon profil »
  // comme tout premier écran, et neutralise la navigation tant que le couple n'est pas enregistré).
  // Le prénom/nom, eux, ne bloquent PAS : simple rappel discret dans le header (profilNomIncomplet).
  // Profil à revoir = matière absente OU matière devenue incohérente avec le programme vivant
  // (profil_coherent renvoyé en direct par /auth/me, ex. après remplacement d'un référentiel).
  // Dans les deux cas on force « Mon profil » à la connexion, où la modale + le re-choix existent.
  const profilIncomplet = user && (!user.subject || user.profil_coherent === false)
  const profilNomIncomplet = user && (!user.prenom || !user.nom)

  const [page, setPage] = useState(profilIncomplet ? 'mon-profil' : 'accueil')
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackIncidentRef, setFeedbackIncidentRef] = useState(null)  // réf d'incident jointe au feedback (échec de génération) ; null = feedback ouvert manuellement
  const [showNotation, setShowNotation] = useState(false)
  // La machinerie de l'ancien écran Créer (texte/objet/resultat/ton/valider…) a été
  // démolie le 30/07 avec lui — la création vit dans les écrans de Mes contenus.
  // Couple de TRAVAIL — LU du get /auth/me, résolu EN BASE par le serveur (couple de travail
  // s'il est posé, sinon profil). Plus AUCUN état local : l'écran est une fenêtre sur la base
  // (décision du 25/07) — un F5 ou un autre appareil montrent exactement la même vérité.
  const sessionMatiere = user?.travail_matiere || ''
  // Libellé affiché (header, Accueil) = ce même couple de travail — jamais un mélange. Une
  // matière qui PORTE une langue affiche la langue du prof à côté de son nom : le drapeau vient
  // du serveur (matieres.demande_langue), l'écran ne reconnaît plus la matière à son libellé.
  const matiereLabel = user?.travail_demande_langue && user?.langue_lv
    ? `${sessionMatiere} - ${user.langue_lv}`
    : sessionMatiere
  // Contenu de l'Accueil qu'on refuse d'ouvrir parce qu'il n'est pas du couple de travail
  // (même garde-fou que « Reprendre » des pages listes) → dialogue partagé.
  const [contenuAutreCouple, setContenuAutreCouple] = useState(null)
  const [aideSection, setAideSection] = useState(null)     // section ciblée à l'ouverture de l'Aide (lien profond)
  const [guideActif, setGuideActif] = useState(false)      // visite guidée de l'écran Créer en cours
  const [fenetreGuide, setFenetreGuide] = useState(false)  // fenêtre déplaçable « Comment ça marche » ouverte
  const [inactivityWarning, setInactivityWarning] = useState(false)
  const [countdown, setCountdown] = useState(WARNING_SECS)
  const timerRef   = useRef(null)
  const cdRef      = useRef(null)
  const warningRef = useRef(false)

  // Ouvre le feedback ; `ref` = référence d'incident (échec de génération) jointe au message, ou
  // null pour un feedback ouvert manuellement (Sidebar / menu).
  const ouvrirFeedback = (ref = null) => { setFeedbackIncidentRef(ref); setShowFeedback(true) }
  // « cliquez ici » de la modale d'erreur ouvre le feedback existant et lui transmet la réf d'incident.
  // ErrorDialog est monté ailleurs dans l'arbre : on passe par ce canal enregistré.
  useEffect(() => { registerFeedbackOpener((ref) => { setFeedbackIncidentRef(ref || null); setShowFeedback(true) }) }, [])

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

  // Nettoyage ponctuel : les compteurs few-shot vivaient en localStorage (avant P4.7) ;
  // le backend fait foi désormais. On purge ces clés devenues mortes, au montage.
  useEffect(() => {
    Object.keys(localStorage)
      .filter(k => k.startsWith('aschool_style_count_'))
      .forEach(k => localStorage.removeItem(k))
    localStorage.removeItem('aschool_niveau')  // niveau vit en base désormais — on purge le vieux cache
  }, [])

  // Écran forcé : tant que le profil n'a pas de matière (couple absent), on ramène TOUJOURS
  // sur « Mon profil ». useLayoutEffect (avant peinture) → aucune autre page ne s'affiche, même
  // une fraction de seconde. Se relâche seul dès que la matière est enregistrée (profilIncomplet=false).
  useLayoutEffect(() => {
    if (profilIncomplet && page !== 'mon-profil') setPage('mon-profil')
  }, [profilIncomplet, page])

  // Le niveau vit EN BASE (users.niveau) : `params` n'en est que le reflet du get /auth/me,
  // jamais dupliqué en localStorage. Les autres champs de l'ancien écran Créer sont partis
  // avec lui le 30/07 — il ne reste que le niveau, seul champ lu.
  const [params, setParams] = useState({
    niveau: user?.travail_niveau || '',
  })

  // « Revenir à mon profil » = EFFACER l'écart en base (DELETE), puis relire /auth/me :
  // le header et l'écran suivent le même get — jamais une remise à zéro locale.
  async function revenirAuProfil() {
    try {
      const res = await apiFetch('/api/user/couple-travail', { method: 'DELETE' }, TIMEOUT_STD)
      await lireReponse(res)
      await refreshUser()
    } catch (err) {
      showError(messagePourEcran(err))
    }
  }

  // Valider de « Changer niveau et/ou matière » = PUT du couple de travail EN BASE, puis
  // relecture /auth/me. Renvoie false si le serveur refuse (la modale reste ouverte).
  async function validerCoupleTravail(m, n) {
    try {
      const res = await apiFetch('/api/user/couple-travail', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ matiere: m, niveau: n }),
      }, TIMEOUT_STD)
      await lireReponse(res)
      await refreshUser()
      return true
    } catch (err) {
      showError(messagePourEcran(err))
      return false
    }
  }

  // Resynchronise params.niveau quand le couple de travail change en base (PUT/DELETE
  // ci-dessus, ou sauvegarde du profil) — params reste un simple reflet du get.
  useEffect(() => {
    if (user?.travail_niveau && user.travail_niveau !== params.niveau) {
      setParams(p => ({ ...p, niveau: user.travail_niveau }))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.travail_niveau])
  // Écran Séance de MES CONTENUS (maquette 29/07) : la ligne cliquée dans la bibliothèque,
  // ou null pour un formulaire vierge (« + Créer → Une séance »). Additif — rien d'existant ne bouge.
  const [seanceOuverte, setSeanceOuverte] = useState(null)
  function ouvrirSeance(s) {
    setSeanceOuverte(s)
    setSequenceRetour(null)     // ouverture depuis une liste : pas de séquence d'origine
    setPage('seance')
  }
  // Écran Séquence de MES CONTENUS (étapes 3-5 du chantier, 30/07) : la ligne cliquée dans
  // la page Séquences (reprise complète), ou null pour un formulaire vierge.
  const [sequenceOuverte, setSequenceOuverte] = useState(null)
  function ouvrirSequence(s) {
    setSequenceOuverte(s)
    setPage('sequence')
  }
  // LA BOUCLE (demande utilisateur 30/07) : depuis l'écran Séquence, une séance du plan
  // s'ouvre pré-remplie ; « ← Retour à la séquence » ramène au cockpit — même circuit que
  // activité↔séance, un étage au-dessus. `sequenceRetour` = l'id de la séquence d'origine,
  // PRÉSERVÉ pendant le détour séance→activité→séance.
  const [sequenceRetour, setSequenceRetour] = useState(null)
  function ouvrirSeanceDepuisSequence(seanceRow, sequenceId) {
    setSeanceOuverte(seanceRow)
    setSequenceRetour(sequenceId)
    setPage('seance')
  }
  // Retour vers la séquence d'origine : RELUE depuis la base (règle 0 : tout y est déjà)
  // puis rouverte — badges « à générer / générée » à jour. Échec → la liste, jamais le vide.
  async function retournerALaSequence() {
    const id = sequenceRetour
    setSequenceRetour(null)
    if (!id) return
    try {
      const d = await lireReponse(await apiFetch('/api/mes-contenus', { credentials: 'include' }, TIMEOUT_STD))
      const row = (d.contenus || []).find(c => c.type === 'sequence' && c.id === id)
      if (row) { ouvrirSequence(row); return }
    } catch { /* relecture impossible : on retombe sur la liste */ }
    naviguer('contenus-sequences')
  }
  // Écran Activité du monde MES CONTENUS : ligne cliquée (reprise) ou null (création).
  const [activiteContenusOuverte, setActiviteContenusOuverte] = useState(null)
  // Séance PARENTE d'une création d'activité (bouton « Créer une activité ici » de l'écran
  // Séance) : l'activité naîtra rattachée à cette séance. Null = création libre.
  const [seancePourActivite, setSeancePourActivite] = useState(null)
  function ouvrirActiviteContenus(a) {
    setActiviteContenusOuverte(a)
    setSeancePourActivite(null)
    setPage('activite')
  }
  function creerActiviteDansSeance(seanceId) {
    setActiviteContenusOuverte(null)
    setSeancePourActivite(seanceId)
    setPage('activite')
  }
  // Retour vers la séance d'origine (création d'activité DEPUIS une séance) : la séance est
  // RELUE depuis la base (règle 0 : tout y est déjà) puis rouverte — cartouche ⑤ à jour.
  // Si la relecture échoue, on retombe sur la liste des séances, jamais dans le vide.
  async function retournerALaSeance() {
    const id = seancePourActivite
    if (!id) return
    try {
      const d = await lireReponse(await apiFetch('/api/mes-contenus', { credentials: 'include' }, TIMEOUT_STD))
      const row = (d.contenus || []).find(c => c.type === 'seance' && c.id === id)
      // Réouverture DIRECTE (pas ouvrirSeance) : le détour séance→activité→séance ne doit
      // pas effacer la séquence d'origine — la boucle séquence→séance→activités survit.
      if (row) { setSeanceOuverte(row); setPage('seance'); return }
    } catch { /* relecture impossible : on retombe sur la liste */ }
    naviguer('contenus-seances')
  }

  // Accueil « monde neuf » : rouvrir la dernière création — la ligne est RELUE depuis la
  // base (règle 0 : tout y est déjà) puis ouverte dans son écran Mes contenus ; relecture
  // impossible ou ligne disparue → la liste du type, jamais le vide.
  //
  // MÊME GARDE-FOU QUE LES PAGES LISTES (posé le 31/07) : la carte « dernière création » n'est
  // pas filtrée par le couple de travail — elle peut donc montrer une activité de 3e à un prof
  // qui travaille en 6e. Ce chemin ouvrait sans rien vérifier, là où « Reprendre » refuse et
  // explique. Depuis que le serveur contrôle le type à l'écriture, le prof allait jusqu'à
  // régénérer pour s'entendre répondre « pas prêt pour ce niveau » — en parlant de son niveau
  // COURANT pendant que sa carte affichait l'autre. On arrête le geste avant, avec le même mot.
  async function ouvrirContenuAccueil(type, id) {
    try {
      const d = await lireReponse(await apiFetch('/api/mes-contenus', { credentials: 'include' }, TIMEOUT_STD))
      const row = (d.contenus || []).find(c => c.type === type && c.id === id)
      if (row) {
        if (!correspondProfil(row, sessionMatiere, params.niveau)) {
          setContenuAutreCouple({ ...row, type })
          return
        }
        if (type === 'activite') ouvrirActiviteContenus(row)
        else ouvrirSeance(row)
        return
      }
    } catch { /* relecture impossible : on retombe sur la liste */ }
    naviguer(type === 'activite' ? 'contenus-activites' : 'contenus-seances')
  }

  // Routeur de navigation.
  function naviguer(p) {
    setAideSection(null)   // navigation normale (sidebar) -> l'Aide s'ouvre sur sa section par défaut
    setFenetreGuide(false) // la fenêtre « Comment ça marche » ne suit pas d'un écran à l'autre
    setPage(p)
  }

  // Fin de visite (Terminer, Passer ou Échap) : on note le « vu » EN BASE (put) puis on
  // relit /auth/me. Échec silencieux : au pire le guide se relancera, sans gravité.
  async function fermerGuide() {
    setGuideActif(false)
    if (user && user.guide_creer_vu === false) {
      try {
        const res = await apiFetch('/api/user/guide-creer-vu', { method: 'PUT' }, TIMEOUT_STD)
        await lireReponse(res)
        await refreshUser()
      } catch { /* rien à montrer au prof */ }
    }
  }

  // « En savoir plus » d'une bulle ou lien de la fenêtre : le centre d'aide s'ouvre sur la
  // fiche de l'écran Créer (le lien profond aideSection existe déjà).
  function ouvrirAideDepuisGuide() {
    fermerGuide()
    setFenetreGuide(false)
    setAideSection('comment')
    setPage('aide')
  }

  // Contexte emporté par un feedback : l'écran courant + le couple de travail (résolu en
  // base via /auth/me). Affiché en clair dans la fenêtre avant l'envoi — le prof n'a plus
  // à décrire où il se trouve.
  const contexteFeedback = `Écran ${libelleEcran(page)}`
    + (matiereLabel && user?.travail_niveau ? ` · ${matiereLabel} × ${user.travail_niveau}` : '')

  // « Comment ça marche » — LE registre unique page → fenêtre de guide (règle maison : un
  // guide par écran, tenu à jour avec l'écran). Le bouton du header ET le rendu de la
  // fenêtre (en bas de <main>) se branchent TOUS LES DEUX ici : une nouvelle page = UNE
  // entrée à ajouter, le bouton apparaît tout seul — fini la liste à part qu'on oubliait
  // à chaque écran créé (bug du 30/07 : les pages Mes contenus n'avaient pas le bouton).
  const guidesParPage = {
    // L'écran Activité de Mes contenus réutilise TEL QUEL le guide de l'ex-écran Créer.
    'activite': () => (
      <FenetreGuide
        onFermer={() => setFenetreGuide(false)}
        onRevoirGuide={() => { setFenetreGuide(false); setGuideActif(true) }}
        onOuvrirAide={ouvrirAideDepuisGuide}
      />
    ),
    'seance': () => (
      <FenetreGuideSeance onFermer={() => setFenetreGuide(false)} onOuvrirAide={ouvrirAideDepuisGuide} />
    ),
    'contenus-activites': () => (
      <FenetreGuideContenusActivites onFermer={() => setFenetreGuide(false)} onOuvrirAide={ouvrirAideDepuisGuide} />
    ),
    // Alias historique de la page Activités de Mes contenus (liens/retours existants).
    'mes-contenus': () => (
      <FenetreGuideContenusActivites onFermer={() => setFenetreGuide(false)} onOuvrirAide={ouvrirAideDepuisGuide} />
    ),
    'contenus-seances': () => (
      <FenetreGuideContenusSeances onFermer={() => setFenetreGuide(false)} onOuvrirAide={ouvrirAideDepuisGuide} />
    ),
    'sequence': () => (
      <FenetreGuideSequence onFermer={() => setFenetreGuide(false)} onOuvrirAide={ouvrirAideDepuisGuide} />
    ),
    'contenus-sequences': () => (
      <FenetreGuideContenusSequences onFermer={() => setFenetreGuide(false)} onOuvrirAide={ouvrirAideDepuisGuide} />
    ),
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">

      {/* Profil sans matière : le blocage se fait en amont — page initiale forcée à « mon-profil »
          + snap-back useLayoutEffect (voir profilIncomplet plus haut). Pas de modale ici. */}

      <Header
        matiere={matiereLabel}
        niveau={user?.travail_niveau}
        email={user?.email}
        prenom={user?.prenom}
        nom={user?.nom}
        profilNomIncomplet={profilNomIncomplet}
        onLogout={logout}
        onNavigate={naviguer}
        onFeedback={() => ouvrirFeedback()}
        sessionMatiere={sessionMatiere}
        coupleAjuste={!!user?.couple_ajuste}
        onValiderCouple={validerCoupleTravail}
        onRevenirProfil={revenirAuProfil}
        onOuvrirGuide={guidesParPage[page] ? () => setFenetreGuide(true) : null}
      />

      <div className="flex flex-1 min-h-0" style={{ paddingTop: 65 }}>
        <Sidebar page={page} onNavigate={naviguer} onFeedback={() => ouvrirFeedback()} onNotation={() => setShowNotation(true)} />

        <main className={`flex-1 p-6 flex flex-col gap-4 ${['ambiguites', 'consigne', 'activite', 'mes-contenus', 'seance', 'sequence', 'contenus-sequences', 'contenus-seances', 'contenus-activites'].includes(page) ? 'overflow-hidden' : 'overflow-auto'}`}>
          {page === 'accueil' && (
            <Accueil
              user={user}
              matiereLabel={matiereLabel}
              niveau={user?.travail_niveau}
              onNavigate={naviguer}
              onOuvrir={ouvrirContenuAccueil}
            />
          )}


          {/* Mes contenus — une page PAR TYPE (3 sous-options du menu). L'ancienne route
              mes-contenus reste un alias vers Activités (liens/retours existants). */}
          {page === 'contenus-sequences' && (
            <MesContenus
              type="sequence"
              onNavigate={naviguer}
              onOuvrirSeance={ouvrirSeance}
              onOuvrirActivite={ouvrirActiviteContenus}
              onOuvrirSequence={ouvrirSequence}
              email={user?.email}
              sessionMatiere={sessionMatiere}
              sessionNiveau={params.niveau}
            />
          )}
          {page === 'contenus-seances' && (
            <MesContenus
              type="seance"
              onNavigate={naviguer}
              onOuvrirSeance={ouvrirSeance}
              onOuvrirActivite={ouvrirActiviteContenus}
              email={user?.email}
              sessionMatiere={sessionMatiere}
              sessionNiveau={params.niveau}
            />
          )}
          {(page === 'contenus-activites' || page === 'mes-contenus') && (
            <MesContenus
              type="activite"
              onNavigate={naviguer}
              onOuvrirSeance={ouvrirSeance}
              onOuvrirActivite={ouvrirActiviteContenus}
              email={user?.email}
              sessionMatiere={sessionMatiere}
              sessionNiveau={params.niveau}
              userName={`${user?.prenom || ''} ${user?.nom || ''}`.trim()}
            />
          )}

          {page === 'activite' && (
            <>
              <ActiviteEcran
                key={activiteContenusOuverte?.id ?? 'nouvelle'}
                activite={activiteContenusOuverte}
                seanceParente={seancePourActivite}
                onRetourSeance={retournerALaSeance}
                matiere={sessionMatiere}
                niveau={params.niveau}
                email={user?.email}
                onNavigate={naviguer}
              />
              {/* « Comment ça marche » récupéré TEL QUEL de l'écran Créer une activité
                  (même fenêtre, même visite guidée — les ancres data-guide sont les mêmes
                  composants ; une ancre absente fait juste sauter son étape). */}
              {guideActif && (
                <VisiteGuidee onFermer={fermerGuide} onOuvrirAide={ouvrirAideDepuisGuide} />
              )}
            </>
          )}

          {page === 'seance' && (
            <>
              <SeanceEcran
                key={seanceOuverte?.id ?? 'nouvelle'}
                seance={seanceOuverte}
                matiere={sessionMatiere}
                niveau={params.niveau}
                onNavigate={naviguer}
                onCreerActivite={creerActiviteDansSeance}
                onOuvrirActivite={ouvrirActiviteContenus}
                onRetourSequence={sequenceRetour ? retournerALaSequence : null}
              />
            </>
          )}

          {page === 'sequence' && (
            <SequenceEcran
              key={sequenceOuverte?.id ?? 'nouvelle'}
              sequence={sequenceOuverte}
              matiere={sessionMatiere}
              niveau={params.niveau}
              onNavigate={naviguer}
              onOuvrirSeance={ouvrirSeanceDepuisSequence}
            />
          )}

          {/* La passerelle « créer une séance depuis une reformulation » visait l'ancien
              outil Séquence (démoli) — elle renaîtra sur la séance du monde neuf. */}
          {page === 'ambiguites' && (
            <Ambiguites
              matiere={sessionMatiere}
              niveau={params.niveau}
              onNavigate={naviguer}
            />
          )}

          {page === 'consigne' && (
            <Consigne
              matiere={sessionMatiere}
              niveau={params.niveau}
              onNavigate={naviguer}
            />
          )}

          {page === 'equite' && (
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center', textAlign: 'center' }}>
              <div style={{ fontSize: '15px', fontWeight: 700, color: '#1e293b' }}>Détecteur d'équité pédagogique</div>
              <p style={{ fontSize: '13px', color: '#64748b', margin: 0, maxWidth: '400px', lineHeight: 1.6 }}>
                Outil en cours de développement.
              </p>
              <button onClick={() => naviguer('accueil')} title="Revenir à l'accueil"
                style={{ fontSize: '12px', color: '#6366f1', background: 'none', border: '1px solid #c7d2fe', borderRadius: '5px', padding: '5px 14px', cursor: 'pointer' }}>
                ← Retour à l'accueil
              </button>
            </div>
          )}

          {page === 'bientot-disponible' && <BientotDisponible />}

          {page === 'mon-profil' && <MonProfil onNavigate={naviguer} />}


          {page === 'aide' && <Aide initialSection={aideSection} />}

          {page === 'mes-feedbacks' && <MesFeedbacks />}

          {page === 'mes-stats' && <MesStats user={user} />}

          {page === 'apropos' && <APropos email={user?.email} matiere={user?.subject} />}

          {/* « Comment ça marche » de la page courante — rendu UNE seule fois, piloté par le
              registre guidesParPage (fenêtre déplaçable FenetrePro, par-dessus l'écran).
              Une page absente du registre n'a pas de guide → le header cache son bouton. */}
          {fenetreGuide && guidesParPage[page] && guidesParPage[page]()}
        </main>
      </div>

      <Footer />
      {showFeedback && <Feedback onClose={() => setShowFeedback(false)} contexte={contexteFeedback} incidentRef={feedbackIncidentRef} />}
      {showNotation && <Notation onClose={() => setShowNotation(false)} />}

      {/* Contenu de l'Accueil hors couple de travail : LE MÊME dialogue que « Reprendre »
          des pages listes (un seul fichier, donc un seul mot pour la même situation). */}
      {contenuAutreCouple && (
        <DialogueAutreCouple
          contenu={contenuAutreCouple}
          type={contenuAutreCouple.type}
          sessionMatiere={sessionMatiere}
          sessionNiveau={params.niveau}
          onFermer={() => setContenuAutreCouple(null)}
        />
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


    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <UpdateBanner />
        <ErrorDialog />
        <ConfirmDialog />
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
            <Route path="mise-en-route" element={<AdminMiseEnRoute />} />
            <Route path="serveur"    element={<AdminServeur />} />
            <Route path="sessions"   element={<AdminSessions />} />
            <Route path="logs"       element={<AdminLogs />} />
            <Route path="feedbacks"  element={<AdminFeedbacks />} />
            <Route path="profils"    element={<AdminProfils />} />
            <Route path="referentiels" element={<AdminReferentiels />} />
            <Route path="labo" element={<Labo />} />{/* écran labo générique (bac à sable) */}
            <Route path="referentiels-consulter" element={<AdminReferentielsConsulter />} />
            <Route path="contenu" element={<AdminContenu />} />
            {/* Prompts — contenu pédagogique, pas plomberie : sorti de Système → Génération LLM.
                Trois sous-options : à qui sert le texte. Le `key` force le remontage en changeant
                de sous-option, donc chaque vue repart sur SON état (rien ne traîne d'avant). */}
            <Route path="prompts">
              <Route index element={<Navigate to="/admin/prompts/prof" replace />} />
              <Route path="prof"   element={<AdminPrompts key="prof"   categorie="prof" />} />
              <Route path="admin"  element={<AdminPrompts key="admin"  categorie="admin" />} />
              <Route path="autres" element={<AdminPrompts key="autres" categorie="autres" />} />
            </Route>
            <Route path="audit"       element={<AdminAudit />} />
            <Route path="tentatives" element={<AdminTentatives />} />
            <Route path="alertes"    element={<AdminAlertes />} />
            <Route path="compte"        element={<AdminCompte />} />
            <Route path="parametres">
              <Route index element={<Navigate to="/admin/parametres/generation" replace />} />
              <Route path="generation" element={<AdminParametresGeneration />} />
              <Route path="email"      element={<AdminParametresEmail />} />
              <Route path="general"    element={<AdminParametres />} />
            </Route>
            <Route path="communication" element={<AdminCommunication />} />
            <Route path="aide"          element={<AdminAide />} />
            <Route path="maintenance"   element={<AdminMaintenance />} />
            <Route path="base"          element={<AdminBase />} />
            <Route path="base/demos"    element={<AdminBaseDemos />} />
            <Route path="analytique">
              <Route index element={<Navigate to="/admin/analytique/general" replace />} />
              <Route path="general"    element={<AdminAnalytiqueGeneral />} />
              <Route path="activites"  element={<AdminAnalytique />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
