import { useState, useEffect, useRef } from 'react'
import { showError, registerFeedbackOpener } from './errorDialog'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './context/contexteAuth.js'
import Header, { HAUTEUR_HEADER } from './components/Header'
import Sidebar from './components/Sidebar'
import Footer from './components/Footer'
import VisiteGuidee from './components/VisiteGuidee'
import FenetreGuide from './components/FenetreGuide'
import FenetreGuideAmbiguites from './components/FenetreGuideAmbiguites'
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
import Equite from './components/Equite.jsx'
import FenetreGuideConsigne from './components/FenetreGuideConsigne.jsx'
import FenetreGuideEquite from './components/FenetreGuideEquite.jsx'
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
import AdminIAFournisseurs from './pages/AdminIAFournisseurs'
import AdminIAStatistiques from './pages/AdminIAStatistiques'
import AdminIAJournal from './pages/AdminIAJournal'
import AdminPrompts from './pages/AdminPrompts'
import AdminPromptsReferentiels from './pages/AdminPromptsReferentiels'
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
import AdminReferentielsConsulter from './pages/AdminReferentielsConsulter'
import AdminContenu from './pages/AdminContenu'
import AdminMaintenance from './pages/AdminMaintenance'
import AdminPlanificateur from './pages/AdminPlanificateur'
import AdminTachesAFaire from './pages/AdminTachesAFaire'
import AdminBase from './pages/AdminBase'
import AdminBaseDemos from './pages/AdminBaseDemos'
import AdminAnalytique from './pages/AdminAnalytique'
import AdminAnalytiqueGeneral from './pages/AdminAnalytiqueGeneral'
import MesFeedbacks from './pages/MesFeedbacks'
import DemoEntree from './pages/DemoEntree'
import BandeauDemo from './components/BandeauDemo'
import FiligraneDemo from './components/FiligraneDemo'
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
  //
  // `=== false` et non `!user.profil_coherent` : le serveur renvoie NULL quand le profil est
  // vide (la question ne se pose pas encore), et un profil vide part déjà par `!user.subject`.
  // Un test de vérité simple confondrait « incohérent » et « pas encore rempli ».
  //
  // (Ce champ n'a longtemps jamais été envoyé par le serveur : il valait `undefined`, donc
  // cette moitié de la condition ne s'exécutait pas une seule fois. Rétabli le 02/08/2026.)
  //
  // (`profil_en_travaux` a disparu le 07/08/2026 avec le mécanisme de blocage : plus personne
  // ne détache la matière d'un prof, la base refuse de supprimer une matière qu'il porte.)
  const profilIncomplet = user && (!user.subject || user.profil_coherent === false)
  const profilNomIncomplet = user && (!user.prenom || !user.nom)

  // Écran forcé : tant que le profil n'a pas de matière (couple absent), l'écran affiché est
  // TOUJOURS « Mon profil ». Ce n'est pas une correction après coup (on posait autrefois
  // setPage('mon-profil') dans un useLayoutEffect, ce qui repeignait l'écran une fois de trop) :
  // `page` est simplement CALCULÉ — tant que profilIncomplet est vrai, il n'existe pas d'autre
  // page, donc aucune autre ne peut s'afficher, même une fraction de seconde. Le choix de
  // l'utilisateur dort dans `pageChoisie` et revient dès que la matière est enregistrée.
  const [pageChoisie, setPage] = useState(profilIncomplet ? 'mon-profil' : 'accueil')
  const page = profilIncomplet ? 'mon-profil' : pageChoisie
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
      } catch { /* battement raté (réseau, serveur) : le suivant reposera la question dans 60 s */ }
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

  // Le niveau vit EN BASE (users.niveau) : `params` n'en est que le reflet du get /auth/me,
  // jamais dupliqué en localStorage. Les autres champs de l'ancien écran Créer sont partis
  // avec lui le 30/07 — il ne reste que le niveau, seul champ lu.
  // Reflet veut dire CALCULÉ, comme `sessionMatiere` juste au-dessus : plus de copie locale à
  // resynchroniser après coup (PUT/DELETE du couple, sauvegarde du profil) — le get fait foi
  // au rendu même où il arrive.
  const params = { niveau: user?.travail_niveau || '' }

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
  // fiche de l'écran d'où l'on vient (le lien profond aideSection existe déjà).
  //
  // La fiche était CODÉE EN DUR sur celle de l'écran Créer : le lien « Ouvrir le centre d'aide »
  // des guides Ambiguïtés et Consignes y menait aussi, alors que ces deux écrans ont leur propre
  // fiche. Chaque guide dit maintenant la sienne ; sans argument, on retombe sur « Créer », qui
  // reste la bonne réponse pour les guides qui n'ont pas de fiche à eux.
  function ouvrirAideDepuisGuide(section = 'comment') {
    fermerGuide()
    setFenetreGuide(false)
    setAideSection(section)
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
    // Sorti de la barre d'onglets de l'écran Ambiguïtés : le guide vit dans le header comme
    // partout ailleurs, l'écran n'a plus qu'une seule chose à montrer.
    'ambiguites': () => (
      <FenetreGuideAmbiguites onFermer={() => setFenetreGuide(false)} onOuvrirAide={() => ouvrirAideDepuisGuide('ambiguites')} />
    ),
    // Sorti de la barre d'onglets de l'écran Consignes, comme celui des ambiguïtés : le guide
    // vit dans le header, l'écran n'a plus qu'une seule chose à montrer.
    'consigne': () => (
      <FenetreGuideConsigne onFermer={() => setFenetreGuide(false)} onOuvrirAide={() => ouvrirAideDepuisGuide('consignes')} />
    ),
    // Le troisième frère : même dispositif, dès le premier jour de l'écran — il n'a jamais eu
    // d'onglet « Comment ça marche » à démolir.
    'equite': () => (
      <FenetreGuideEquite onFermer={() => setFenetreGuide(false)} onOuvrirAide={() => ouvrirAideDepuisGuide('equite')} />
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

      {/* PREMIÈRE OUVERTURE : TOUT EST ÉTEINT SAUF LE PROFIL.
          `page` valait déjà « mon-profil » quoi qu'il arrive (voir plus haut) — mais l'en-tête et
          la barre de gauche restaient allumés et cliquables. Le prof cliquait, rien ne se passait,
          et rien ne lui disait pourquoi. Ils sont maintenant grisés et sourds au clic : il reste
          UN seul endroit vivant à l'écran, celui où on lui demande sa matière.
          `pointerEvents: none` plutôt qu'un voile posé par-dessus : un voile laisserait le clavier
          atteindre les boutons (Tab), et masquerait le contenu au lieu de le désactiver. */}
      <div style={profilIncomplet ? { opacity: 0.35, pointerEvents: 'none', filter: 'grayscale(1)' } : undefined}
           aria-hidden={profilIncomplet || undefined}>
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
      </div>

      <div className="flex flex-1 min-h-0" style={{ paddingTop: HAUTEUR_HEADER }}>
        <div style={profilIncomplet ? { opacity: 0.35, pointerEvents: 'none', filter: 'grayscale(1)' } : undefined}
             aria-hidden={profilIncomplet || undefined}>
          <Sidebar page={page} onNavigate={naviguer} onNotation={() => setShowNotation(true)} />
        </div>

        <main className={`flex-1 p-6 flex flex-col gap-4 ${['ambiguites', 'consigne', 'equite', 'activite', 'mes-contenus', 'seance', 'sequence', 'contenus-sequences', 'contenus-seances', 'contenus-activites'].includes(page) ? 'overflow-hidden' : 'overflow-auto'}`}>
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
              onNavigate={naviguer}
              onOuvrirSeance={ouvrirSeanceDepuisSequence}
            />
          )}

          {/* La passerelle « créer une séance depuis une reformulation » visait l'ancien
              outil Séquence (démoli) — elle renaîtra sur la séance du monde neuf. */}
          {page === 'ambiguites' && (
            <Ambiguites />
          )}

          {/* Le couple ne descend plus en props : le header le porte déjà, et le serveur le
              résout en base (`couple_de_travail`). L'écran affichait un encart « matière ·
              niveau » qui redisait le bandeau du haut — son jumeau Ambiguïtés ne l'affiche pas. */}
          {page === 'consigne' && (
            <Consigne />
          )}

          {/* L'écran existe (composant Equite + backend analyse/equite.py). Il remplace le bloc
              « Outil en cours de développement » écrit ici en dur, qui tenait la place depuis le
              premier jour. Comme ses deux frères, il ne reçoit pas le couple en props : le header
              le porte, et le serveur le résout en base. */}
          {page === 'equite' && (
            <Equite />
          )}

          {page === 'bientot-disponible' && <BientotDisponible />}

          {page === 'mon-profil' && <MonProfil onNavigate={naviguer} />}


          {page === 'aide' && <Aide initialSection={aideSection} />}


          {page === 'nouveau-retour' && <MesFeedbacks vue="envoyer" onNavigate={naviguer} />}

          {page === 'mes-feedbacks' && <MesFeedbacks vue="retours" onNavigate={naviguer} />}

          {page === 'mes-stats' && <MesStats user={user} />}

          {page === 'apropos' && <APropos email={user?.email} />}

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
        <BandeauDemo />
        <FiligraneDemo />
        <Routes>
          <Route path="/login" element={<Login />} />
          {/* Arrivée dans la démonstration : hors ProtectedRoute, puisque c'est elle qui ouvre
              la session. Sur une instance ordinaire, /api/demo/entrer répond 404. */}
          <Route path="/demo" element={<DemoEntree />} />
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
            <Route path="referentiels-consulter" element={<AdminReferentielsConsulter />} />
            <Route path="contenu" element={<AdminContenu />} />
            {/* Prompts — contenu pédagogique, pas plomberie : sorti de Système → Génération LLM.
                Quatre sous-entrées de menu (16/08/2026), une par famille de prompts. Le `key`
                force le remontage en changeant de famille, donc chaque vue repart sur SON état
                (rien ne traîne d'avant). L'index mène à la première entrée du menu. */}
            <Route path="prompts">
              <Route index element={<Navigate to="/admin/prompts/referentiels" replace />} />
              {/* « Prof » et « Admin » ont disparu le 12/08/2026 (rangement par fonctionnalité).
                  Leurs adresses restent debout et mènent au bon onglet : un favori ne casse pas. */}
              <Route path="prof"  element={<Navigate to="/admin/prompts/fonctionnalites" replace />} />
              <Route path="admin" element={<Navigate to="/admin/prompts/referentiels-communs" replace />} />
              <Route path="referentiels-communs" element={<AdminPrompts key="referentiels-communs" categorie="referentiels_communs" />} />
              {/* « Matières par cycle » et « Découpe par cycle » ont été retirés le 06/08/2026 :
                  ces deux prompts appartiennent au RÉFÉRENTIEL (un par couple cycle+niveau) et se
                  règlent sur l'écran Référentiel, dans la cartouche qui les utilise. */}
              <Route path="referentiels" element={<AdminPromptsReferentiels key="referentiels" />} />
              {/* Rangement par fonctionnalité : la cible du lien « ambiguïté » de la carte
                  d'un référentiel. */}
              <Route path="fonctionnalites" element={<AdminPrompts key="fonctionnalites" categorie="fonctionnalites" />} />
              <Route path="autres" element={<AdminPrompts key="autres" categorie="autres" />} />
            </Route>
            {/* IA — les deux écrans nés avec la rubrique (05/08/2026). Prompts et Génération gardent
                leurs URL d'origine : le menu a changé, pas les adresses, donc aucun lien ni favori
                existant ne casse. */}
            <Route path="ia">
              <Route index element={<Navigate to="/admin/ia/fournisseurs" replace />} />
              <Route path="fournisseurs" element={<AdminIAFournisseurs />} />
              <Route path="statistiques" element={<AdminIAStatistiques />} />
              {/* Le détail que les statistiques n'ont jamais montré : un appel par ligne. */}
              <Route path="journal" element={<AdminIAJournal />} />
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
            <Route path="planificateur" element={<AdminPlanificateur />} />
            <Route path="taches-a-faire" element={<AdminTachesAFaire />} />
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
