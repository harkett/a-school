import { useState, useEffect, useLayoutEffect, useRef } from 'react'
import { showError, registerFeedbackOpener } from './errorDialog'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import Footer from './components/Footer'
import TexteSource from './components/TexteSource'
import Parametres from './components/Parametres'
import VisiteGuidee from './components/VisiteGuidee'
import FenetreGuide from './components/FenetreGuide'
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
import VerificationResultat from './components/VerificationResultat.jsx'
import InfoGuide from './components/InfoGuide.jsx'
import EtapeBadge from './components/EtapeBadge.jsx'
import { aideActivite } from './utils/aideActivite.js'
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
import AdminAnalytique from './pages/AdminAnalytique'
import AdminAnalytiqueGeneral from './pages/AdminAnalytiqueGeneral'
import AdminAnalytiqueOutils from './pages/AdminAnalytiqueOutils'
import AdminAnalytiqueCommunaute from './pages/AdminAnalytiqueCommunaute'
import MesFeedbacks from './pages/MesFeedbacks'
import MesStats from './components/MesStats'
import AdminProgrammes from './pages/AdminProgrammes'
import AdminLayout from './components/AdminLayout'
import OfflineBanner from './components/OfflineBanner'
import UpdateBanner from './components/UpdateBanner'
import ErrorDialog from './components/ErrorDialog'
import ConfirmDialog from './components/ConfirmDialog'
import { showConfirm } from './confirmDialog'
import IOSInstallBanner from './components/IOSInstallBanner'
import JaugeAttente from './components/JaugeAttente.jsx'
import FriseProgression from './components/FriseProgression.jsx'
import SplitPane from './components/SplitPane.jsx'
import { fetchWithTimeout, apiFetch, refreshSession, lireReponse, messagePourEcran, TIMEOUT_AUTH, TIMEOUT_STD, TIMEOUT_LONG } from './utils/api.js'
import { sauvegarderActivite } from './utils/activites.js'
import { estPageCreer, typeVierge } from './utils/activite.js'
import { libelleEcran } from './utils/ecrans.js'
import './index.css'

// Message UNIQUE de tout échec TECHNIQUE de génération (règle 23). « cliquez ici » ouvre le
// feedback existant (opts.feedback). Les échecs MÉTIER (référentiel absent, RAG vide, service
// très demandé) gardent leur propre message, renvoyé par le backend.
const MSG_ECHEC_GENERATION =
  'La génération de votre activité n\'a pas pu aboutir. Merci de réessayer.\n' +
  'Si le problème persiste, cliquez ici pour nous le signaler.'

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
  const matiere = user?.subject

  // Garde-fou : pas de matière = pas de couple → profil BLOQUANT (l'app force « Mon profil »
  // comme tout premier écran, et neutralise la navigation tant que le couple n'est pas enregistré).
  // Le prénom/nom, eux, ne bloquent PAS : simple rappel discret dans le header (profilNomIncomplet).
  // Profil à revoir = matière absente OU matière devenue incohérente avec le programme vivant
  // (profil_coherent renvoyé en direct par /auth/me, ex. après remplacement d'un référentiel).
  // Dans les deux cas on force « Mon profil » à la connexion, où la modale + le re-choix existent.
  const profilIncomplet = user && (!user.subject || user.profil_coherent === false)
  const profilNomIncomplet = user && (!user.prenom || !user.nom)

  const isMobile = window.innerWidth < 768
  const [page, setPage] = useState(profilIncomplet ? 'mon-profil' : 'accueil')
  const [prefillTheme, setPrefillTheme] = useState('')
  const [prefillSeq, setPrefillSeq] = useState(null)
  const [prefillAmbiguites, setPrefillAmbiguites] = useState('')
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackIncidentRef, setFeedbackIncidentRef] = useState(null)  // réf d'incident jointe au feedback (échec de génération) ; null = feedback ouvert manuellement
  const [showNotation, setShowNotation] = useState(false)
  const [activites, setActivites] = useState([])
  const [texte, setTexte] = useState('')
  const [objet, setObjet] = useState('')
  const [resultat, setResultat] = useState(null)
  const [tonActuel, setTonActuel] = useState(null)   // ton ayant produit le résultat affiché : 'academique'|'operationnel'|null (repris d'historique / avant tout choix). Suit le résultat ; base plus tard avec l'auto-save.
  const [loading, setLoading] = useState(false)
  const [verifResultat, setVerifResultat] = useState(null)  // rapport « Vérifier le résultat » : LU sur `resultat` (get), affiché non stocké — zéro copie
  const [verifLoading, setVerifLoading]   = useState(false)  // vérification en cours : sablier du bouton + jauge de la cartouche
  const [ameliorerLoading, setAmeliorerLoading] = useState(null)  // étape 6 « Améliorer » en cours : 'simplifier' | 'enrichir' | null (sablier du bouton + jauge de la cartouche)
  const [corrigerLoading, setCorrigerLoading] = useState(false)  // correction (bras armé de Vérifier) en cours : sablier du bouton + jauge de la cartouche
  const [analysesReplie, setAnalysesReplie] = useState(false)  // repli manuel de la cartouche « Analyse et amélioration du résultat » (affichage éphémère, jamais en base)
  const [genererReplie, setGenererReplie] = useState(false)  // repli manuel de la cartouche ③ « Générer l'activité » (affichage éphémère, jamais en base)
  const [valide, setValide] = useState(false)          // résultat VALIDÉ (écrit en base) : phase « activité enregistrée », boutons de gestion retirés
  const [repriseHistorique, setRepriseHistorique] = useState(false)  // résultat repris de l'historique = DÉJÀ en base : Valider/Annuler grisés (rien à enregistrer, rien à annuler), Régénérer/Changer votre demande restent actifs. Repasse à false dès qu'on régénère (nouveau brouillon).
  const [enValidation, setEnValidation] = useState(false)  // put /api/mes-activites en cours (anti double-clic sur Valider)
  const [entreeDeverrouillee, setEntreeDeverrouillee] = useState(false)  // « Changer votre demande » : rouvre la saisie (sinon verrouillée dès qu'un résultat est là)
  const [erreur, setErreur] = useState(null)
  const [cahierPresent, setCahierPresent] = useState(false)   // le prof a-t-il déposé un cahier des charges ? (get, zéro copie) — adapte les bulles d'aide de Créer
  // Couple de TRAVAIL — LU du get /auth/me, résolu EN BASE par le serveur (couple de travail
  // s'il est posé, sinon profil). Plus AUCUN état local : l'écran est une fenêtre sur la base
  // (décision du 25/07) — un F5 ou un autre appareil montrent exactement la même vérité.
  const sessionMatiere = user?.travail_matiere || ''
  // Libellé affiché (header, Accueil) = ce même couple de travail — jamais un mélange.
  const matiereLabel = sessionMatiere === 'Langues Vivantes (LV)' && user?.langue_lv
    ? `LV - ${user.langue_lv}`
    : sessionMatiere
  const [fewShotModal, setFewShotModal] = useState(false)  // « aSchool vous reconnaît » : modale au franchissement du seuil
  const [aideSection, setAideSection] = useState(null)     // section ciblée à l'ouverture de l'Aide (lien profond)
  const [guideActif, setGuideActif] = useState(false)      // visite guidée de l'écran Créer en cours
  const [fenetreGuide, setFenetreGuide] = useState(false)  // fenêtre déplaçable « Comment ça marche » ouverte
  const [selectedCard, setSelectedCard] = useState('sequence')
  const [inactivityWarning, setInactivityWarning] = useState(false)
  const [countdown, setCountdown] = useState(WARNING_SECS)
  const timerRef   = useRef(null)
  const cdRef      = useRef(null)
  const warningRef = useRef(false)
  const resultatRef = useRef(null)
  const texteSourceRef = useRef(null)   // pour ramener le prof sur la saisie quand il clique « Changer votre demande »

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

  const [params, setParams] = useState({
    activite_type_id: null,              // identité du type = son id (génération ET sauvegarde pointent par id)
    niveau: user?.travail_niveau || '',  // reflet du get /auth/me (couple de travail résolu EN BASE)
    sous_type: null,
    nb: 5,
    avec_correction: false,
  })

  // Le niveau vit EN BASE (users.niveau, sauvegardé par le profil) — jamais dupliqué en localStorage.
  function setParamsWithSave(newParams) {
    setParams(newParams)
  }

  function changerParams(newParams) {
    setParamsWithSave(newParams)
  }

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

  useEffect(() => {
    fetchWithTimeout(`/api/activites/${encodeURIComponent(sessionMatiere)}?niveau=${encodeURIComponent(params.niveau || '')}`, {}, TIMEOUT_STD)
      .then(r => r.json())
      .then(data => {
        const list = Array.isArray(data) ? data : []  // garde-fou : toujours un tableau (jamais .find sur autre chose)
        setActivites(list)
        // Règle appli : on ne PRÉSÉLECTIONNE jamais un combo. Le prof choisit lui-même son type
        // (placeholder gris « Choisissez un type d'activité »). On repart donc de « rien de choisi »,
        // ce qui efface aussi un choix devenu périmé quand la matière/le niveau change (le type
        // d'avant peut ne plus exister dans la nouvelle liste).
        setParams(p => ({ ...p, activite_type_id: null, sous_type: null, nb: null }))
      })
      .catch(() => showError('Impossible de charger les activités — vérifiez que le backend tourne.'))
  }, [sessionMatiere, params.niveau])

  // Cahier des charges du prof déposé ? get de l'état (même endpoint que MonProfil) — sert à
  // ADAPTER les bulles d'aide « i » de l'écran Créer (Texte source, Résultat) quand un cahier
  // existe. Zéro copie : lu à l'affichage, jamais stocké. Relu quand l'utilisateur change (login,
  // refreshUser après un dépôt), donc la bulle reste juste.
  useEffect(() => {
    if (!user) return
    apiFetch('/api/user/cahier', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => setCahierPresent(!!(d && d.present)))
      .catch(() => setCahierPresent(false))
  }, [user])

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

  // `ton` : 'academique' | 'operationnel', choisi par le bouton de génération cliqué (cartouche ③)
  // ou par « Changer votre ton » (bascule l'autre ton). Il part au serveur (couche de style) et est
  // mémorisé dans `tonActuel` pour que « Changer votre ton » sache proposer l'autre.
  async function generer(ton) {
    if (!params.activite_type_id) {
      showError('Sélectionnez un type d\'activité avant de générer.')
      return
    }
    // La zone texte est LA BASE DE TOUT : la demande de l'utilisateur (tapée, dictée, scannée)
    // mène la génération et ancre la recherche au programme. Elle est TOUJOURS exigée.
    if (!texte.trim()) {
      showError(
        'Saisissez un texte source avant de générer — collez un extrait, dictez ou importez un fichier.' +
        (!params.avec_correction ? '\n\nSaviez-vous que vous pouvez inclure un corrigé complet ? Cochez « Avec correction » dans les paramètres.' : '')
      )
      return
    }
    if (isTexteGibberish(texte)) {
      showError('Le texte saisi ne ressemble pas à un contenu pédagogique exploitable.\n\nCollez un extrait de cours ou d\'article, dictez à la voix, ou importez un fichier.')
      return
    }
    setErreur(null)
    setResultat(null)
    setTonActuel(ton || null)       // le résultat à venir sera dans CE ton (bascule « Changer votre ton » comprise)
    setVerifResultat(null)          // (ré)générer = nouvelle activité → l'ancienne vérification ne vaut plus
    setVerifLoading(false)
    setValide(false)
    setRepriseHistorique(false)     // (ré)générer = nouveau brouillon PAS en base → Valider/Annuler redeviennent actifs
    setEntreeDeverrouillee(false)   // nouvelle génération → la saisie repart verrouillée dès qu'un résultat arrive
    setLoading(true)
    try {
      const body = { ...params, texte }
      if (ton) body.ton = ton
      if (!body.nb) delete body.nb
      if (!body.sous_type) delete body.sous_type
      // Le couple (matière/niveau) et la langue LV ne partent PLUS de l'écran : le serveur
      // lit le couple de travail EN BASE au moment de générer (décision du 25/07).
      delete body.niveau

      // Génération EN STREAMING : PAS de fetchWithTimeout — son abort à 45 s coupait le flux en
      // plein travail (LE bug du 23/07). L'autorité de coupure est le serveur (silence lu en base).
      // On garde le réflexe 401 (renouvellement partagé + rejeu UNE fois), sans aucun délai dur.
      const opts = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body),
      }
      let res = await fetch('/api/generate', opts)
      if (res.status === 401 && await refreshSession()) {
        res = await fetch('/api/generate', opts)
      }

      // Échec AVANT le flux : le backend a répondu en JSON. Message MÉTIER (`detail`) tel quel ;
      // sinon (pas de detail, pas de flux) = échec technique → message unique + lien feedback.
      if (!res.ok || !res.body) {
        const err = await res.json().catch(() => ({}))
        if (err.detail) showError(err.detail)
        else showError(MSG_ECHEC_GENERATION, { feedback: true })
        return
      }

      // Lecture du flux SSE (événements delta / error / done) : on affiche au fil de l'eau.
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let tampon = '', complet = '', erreurFlux = false, termine = false, refIncident = null
      setResultat('')
      setTimeout(() => resultatRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        tampon += decoder.decode(value, { stream: true })
        let sep
        while ((sep = tampon.indexOf('\n\n')) >= 0) {
          const bloc = tampon.slice(0, sep)
          tampon = tampon.slice(sep + 2)
          const evt  = (bloc.split('\n').find(l => l.startsWith('event:')) || '').slice(6).trim()
          const data = (bloc.split('\n').find(l => l.startsWith('data:'))  || '').slice(5).trim()
          if (evt === 'delta') {
            try { complet += JSON.parse(data).text; setResultat(complet) } catch { /* bloc partiel ignoré */ }
          } else if (evt === 'error') {
            erreurFlux = true
            try { refIncident = JSON.parse(data).ref || null } catch { /* pas de réf (bloc partiel / ancien format) */ }
          } else if (evt === 'done') {
            termine = true
          }
        }
      }

      // Succès = UNIQUEMENT un flux terminé proprement (`done`), sans `error`, avec du texte. Ceinture
      // de sécurité : un flux qui meurt en route SANS `done` (serveur tombé, connexion coupée) ne doit
      // JAMAIS passer pour un succès → message unique.
      if (erreurFlux || !termine || !complet) {
        setResultat(null)
        showError(MSG_ECHEC_GENERATION, { feedback: true, ref: refIncident })
        return
      }

      // Succès : le résultat reste AFFICHÉ, c'est un BROUILLON de travail — NON enregistré. L'écriture
      // en base (put /api/mes-activites) n'est plus automatique « au coup par coup » : elle est
      // déclenchée par le bouton Valider (modèle brouillon → Valider/Annuler, décision du 25/07,
      // ta RÈGLE 4 : get pour lire/générer, put SEULEMENT sur action explicite du prof).
    } catch (e) {
      // Coupure réseau / flux interrompu côté navigateur → message unique (règle 23), détail en console.
      console.error('génération activité :', e)
      setResultat(null)
      showError(MSG_ECHEC_GENERATION, { feedback: true })
    } finally {
      setLoading(false)
    }
  }

  // Bouton UNIQUE Générer / Régénérer (barre du haut) : tant qu'il n'y a pas de résultat il
  // GÉNÈRE ; dès qu'un résultat est là il RÉGÉNÈRE (même action `generer`, fusion du 25/07).
  // AUCUNE confirmation : régénérer ne fait perdre AUCUNE donnée en base. En création pure, rien
  // n'est encore enregistré (le put n'a lieu qu'au Valider) ; en reprise d'historique, l'originale
  // reste intacte et régénérer produit une activité SÉPARÉE. Il n'y a donc rien à perdre — la
  // question du « vous perdez tout » ne se pose pas ici (décision du 25/07).
  function regenerer() {
    generer()
  }

  // Bouton « Vérifier » de la cartouche : LIT (get) le texte de l'activité affichée + le contexte de
  // la demande (type, précision, correction) et lance /api/verifier-resultat (5 axes en une passe).
  // La checklist s'affiche SUR PLACE dans la cartouche — on ne quitte pas l'écran, le résultat n'est
  // pas modifié. Couple (matière/niveau) = couple de travail (sessionMatiere + params.niveau).
  async function verifierResultat() {
    if (verifLoading || !resultat || !resultat.trim()) return
    setVerifResultat(null)
    setVerifLoading(true)
    try {
      const res = await apiFetch('/api/verifier-resultat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          texte: resultat.trim(),
          matiere: sessionMatiere,
          niveau: params.niveau,
          type_activite: activites.find(a => a.id === params.activite_type_id)?.label || '',
          precision: params.sous_type || '',
          correction: !!params.avec_correction,
        }),
      }, TIMEOUT_LONG)
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Erreur ${res.status}`)
      }
      setVerifResultat(await res.json())
    } catch {
      showError("La vérification du résultat n'a pas pu aboutir. Votre activité reste affichée — réessayez dans un instant.")
    } finally {
      setVerifLoading(false)
    }
  }

  // Correction — bras armé de « Vérifier » : reprend les axes au statut "probleme" trouvés par la
  // vérification et demande à aSchool de RÉÉCRIRE l'activité en réparant EXACTEMENT ces points
  // (/api/corriger-resultat). La version corrigée REMPLACE le résultat affiché et réinitialise la
  // vérification (elle ne colle plus à la nouvelle version). Empilement des versions = RÈGLE 0, pas
  // encore codé : en v1 on remplace l'affiché.
  async function corrigerResultat() {
    if (corrigerLoading || verifLoading || !!ameliorerLoading || loading || !resultat || !resultat.trim() || !verifResultat) return
    const problemes = (verifResultat.axes || [])
      .filter(a => a.statut === 'probleme')
      .map(a => ({ axe: a.axe || '', constat: a.constat || '', extrait: a.extrait || '' }))
    if (problemes.length === 0) return
    setCorrigerLoading(true)
    try {
      const res = await apiFetch('/api/corriger-resultat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          texte: resultat.trim(),
          problemes,
          matiere: sessionMatiere,
          niveau: params.niveau,
          type_activite: activites.find(a => a.id === params.activite_type_id)?.label || '',
          precision: params.sous_type || '',
        }),
      }, TIMEOUT_LONG)
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Erreur ${res.status}`)
      }
      const data = await res.json()
      if (data.texte && data.texte.trim()) {
        setResultat(data.texte)     // version corrigée à la place de l'ancienne
        setVerifResultat(null)      // elle ne colle plus à la nouvelle version → vérif vierge
      }
    } catch {
      showError("La correction n'a pas pu aboutir. Votre activité reste affichée — réessayez dans un instant.")
    } finally {
      setCorrigerLoading(false)
    }
  }

  // Étape 6 « Améliorer » (v1 : 'simplifier' | 'enrichir' ; Transformer reporté en v2). Réécrit
  // l'activité affichée via /api/ameliorer-resultat et REMPLACE le résultat par la nouvelle version
  // → l'ancienne vérification ne vaut plus (réinitialisée). L'empilement des versions (ne rien
  // perdre) relève du chantier persistance (RÈGLE 0), pas encore codé : en v1 on remplace l'affiché.
  async function ameliorer(intention) {
    if (ameliorerLoading || verifLoading || loading || !resultat || !resultat.trim()) return
    setAmeliorerLoading(intention)
    try {
      const res = await apiFetch('/api/ameliorer-resultat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          texte: resultat.trim(),
          intention,
          matiere: sessionMatiere,
          niveau: params.niveau,
          type_activite: activites.find(a => a.id === params.activite_type_id)?.label || '',
          precision: params.sous_type || '',
        }),
      }, TIMEOUT_LONG)
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Erreur ${res.status}`)
      }
      const data = await res.json()
      if (data.texte && data.texte.trim()) {
        setResultat(data.texte)     // nouvelle version affichée à la place de l'ancienne
        setVerifResultat(null)      // elle ne colle plus à la version d'avant → on repart d'une vérif vierge
      }
    } catch {
      showError("L'amélioration n'a pas pu aboutir. Votre activité reste affichée — réessayez dans un instant.")
    } finally {
      setAmeliorerLoading(null)
    }
  }

  // Valider = put : écrit l'activité AFFICHÉE en base (une ligne dans « Mes activités »), puis on
  // passe en phase VALIDÉE (résultat figé, boutons de gestion retirés — seuls les exports restent).
  // Anti double-clic via enValidation. Le couple (matière/niveau) est stampé PAR LE SERVEUR (couple
  // de travail lu en base au moment de la sauvegarde). La modale « aSchool vous reconnaît » suit le seuil.
  async function valider() {
    if (enValidation || valide || !resultat || repriseHistorique) return  // repriseHistorique = déjà en base : re-valider créerait un doublon (RÈGLE 4, unicité)
    setEnValidation(true)
    try {
      const res = await sauvegarderActivite({
        activite_type_id: params.activite_type_id,
        activite_label: activites.find(a => a.id === params.activite_type_id)?.label || '',
        sous_type: params.sous_type || null,
        nb: params.nb || null,
        avec_correction: params.avec_correction,
        objet: objet.trim() || null,
        texte_source: texte,
        resultat,
      })
      setValide(true)
      if (res?.few_shot_just_reached) setFewShotModal(true)
    } catch {
      showError("Enregistrement impossible pour le moment. Votre activité reste affichée — réessayez, ou exportez-la en attendant.")
    } finally {
      setEnValidation(false)
    }
  }

  // Annuler = RIEN en base : deux confirmations en cascade (vu l'importance de la tâche), puis retour
  // à zéro via nouvelleActivite (vide texte / objet / résultat, type au défaut). La 1re confirmation
  // est exactement le message de Régénérer, déclinée pour « annuler ».
  function annuler() {
    if (!window.confirm('Des informations ont été saisies. Si vous annulez, vous perdez tout.')) return
    if (!window.confirm('Tout sera effacé et vous repartez de zéro. Confirmez-vous ?')) return
    nouvelleActivite()
  }

  function chargerSequence(seq) {
    setPrefillSeq(seq)
    setPage('creer-sequence')
  }

  function chargerActivite(act) {
    setTexte(act.texte_source)
    setObjet(act.objet || '')
    setParamsWithSave({
      activite_type_id: act.activite_type_id ?? null,   // l'id du type est renvoyé par la liste sauvegardée
      niveau: act.niveau,
      sous_type: act.sous_type || null,
      nb: act.nb || 5,
      avec_correction: act.avec_correction,
    })
    setResultat(act.resultat)
    setTonActuel(act.ton || null) // ton d'origine si l'activité en base le porte (sinon inconnu → « Changer votre ton » masqué)
    setVerifResultat(null)        // activité reprise de l'historique → pas d'ancienne vérification à afficher
    setValide(false)              // pas la phase VALIDÉ (qui retire tous les boutons) : on garde Régénérer + Changer votre demande
    setRepriseHistorique(true)    // …mais l'activité est DÉJÀ en base → Valider/Annuler grisés
    setEntreeDeverrouillee(false)
    setPage('creer-activite')
  }

  // « Créer » ouvre TOUJOURS une activité vierge : on vide tout le contenu de la fois
  // précédente (texte, objet, résultat, type sélectionné → aucun choix) et on
  // revient sur l'onglet de saisie. Le bandeau « exemple » est effacé par TexteSource dès
  // que le texte se vide. Le couple niveau+matière n'est PAS touché (contexte du profil).
  // NB : « réutiliser depuis l'Historique » passe par chargerActivite() qui charge
  // volontairement — il garde son setPage direct et ne subit donc pas cette remise à zéro.
  function nouvelleActivite() {
    setTexte('')
    setObjet('')
    setResultat(null)
    setTonActuel(null)
    setVerifResultat(null)
    setValide(false)
    setRepriseHistorique(false)
    setEntreeDeverrouillee(false)
    setFenetreGuide(false)
    setParams(p => ({ ...p, ...typeVierge() }))
    setPage('creer-activite')
  }

  // « Changer votre demande » (encart du résultat) : rouvre la saisie (les 6 boutons + la zone
  // + l'Objet redeviennent actifs) et ramène le prof sur la carte Texte source pour qu'il édite.
  // En reprise d'historique : dès qu'on décide de changer la demande, on ne travaille plus sur
  // l'original « tel quel » → on quitte l'état « déjà en base » pour que Valider/Annuler
  // redeviennent actifs (on s'apprête à produire une version à soi).
  function changerDemande() {
    setEntreeDeverrouillee(true)
    setRepriseHistorique(false)
    setTimeout(() => texteSourceRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
  }

  // « Changer votre ton » (bandeau du haut) : reprend le MÊME texte et régénère dans l'AUTRE ton.
  // Bascule directe (deux tons seulement). Action machine = nouvelle version (RÈGLE 0). Ne change pas
  // le texte source ; le résultat courant est remplacé par la version dans l'autre ton.
  function changerTon() {
    if (!tonActuel) return
    generer(tonActuel === 'academique' ? 'operationnel' : 'academique')
  }

  // Libellé lisible d'un ton, pour les messages au prof.
  const libelleTon = t => (t === 'academique' ? 'académique' : 'opérationnel')

  // Confirmation PRO avant les deux reprises (bandeau du haut) : chacune fera PERDRE l'activité
  // affichée (elle n'est pas encore rangée toute seule) → on dit clairement CE QUI change et on
  // rappelle d'exporter d'abord. Le prof confirme à chaque clic ; sinon rien ne bouge.
  function demanderChangerTexte() {
    showConfirm({
      titre: 'Modifier votre texte source ?',
      message: "Vous allez rouvrir votre texte pour le modifier, puis générer une nouvelle activité. L'activité affichée actuellement sera alors remplacée.\n\nSi vous souhaitez la garder, exportez-la d'abord (Word, PDF ou .txt).",
      confirmLabel: 'Modifier le texte',
      onConfirm: changerDemande,
    })
  }
  function demanderChangerTon() {
    if (!tonActuel) return
    const autre = tonActuel === 'academique' ? 'operationnel' : 'academique'
    showConfirm({
      titre: 'Changer le ton de l’activité ?',
      message: `Vous allez régénérer cette activité en ton ${libelleTon(autre)}. L'activité affichée (ton ${libelleTon(tonActuel)}) sera remplacée.\n\nSi vous souhaitez la garder, exportez-la d'abord (Word, PDF ou .txt).`,
      confirmLabel: `Générer en ton ${libelleTon(autre)}`,
      onConfirm: changerTon,
    })
  }

  // Routeur de navigation : toute arrivée sur « Créer » repart d'une activité vierge ;
  // les autres pages naviguent normalement.
  function naviguer(p) {
    setAideSection(null)   // navigation normale (sidebar) -> l'Aide s'ouvre sur sa section par défaut
    if (estPageCreer(p)) nouvelleActivite()
    else setPage(p)
  }

  // Première visite de l'écran Créer : la visite guidée se lance toute seule. Le « déjà
  // vu » est lu EN BASE (get /auth/me → guide_creer_vu) — jamais un stockage navigateur :
  // un autre appareil sait aussi que le guide a été montré.
  useEffect(() => {
    if (page === 'creer-activite' && user && user.guide_creer_vu === false) setGuideActif(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, user?.guide_creer_vu])

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

  // Guidage de l'écran Créer (patron « stepper », décision du 25/07) : les cartouches
  // portent leurs numéros ①②③, l'état réel coche ce qui est fait, et le bouton Générer ne
  // s'allume que quand tout est prêt — plus aucun halo qui se promène.
  const pretAGenerer = !!texte.trim() && !!params.activite_type_id

  // Contexte emporté par un feedback : l'écran courant + le couple de travail (résolu en
  // base via /auth/me). Affiché en clair dans la fenêtre avant l'envoi — le prof n'a plus
  // à décrire où il se trouve.
  const contexteFeedback = `Écran ${libelleEcran(page)}`
    + (matiereLabel && user?.travail_niveau ? ` · ${matiereLabel} × ${user.travail_niveau}` : '')

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
        onOuvrirGuide={page === 'creer-activite' ? () => setFenetreGuide(true) : null}
      />

      <div className="flex flex-1 min-h-0" style={{ paddingTop: 65 }}>
        <Sidebar page={page} onNavigate={naviguer} onFeedback={() => ouvrirFeedback()} onNotation={() => setShowNotation(true)} />

        <main className={`flex-1 p-6 flex flex-col gap-4 ${['creer-activite', 'creer-sequence', 'optimiseur', 'ambiguites', 'consigne'].includes(page) ? 'overflow-hidden' : 'overflow-auto'}`}>
          {page === 'accueil' && (
            <Accueil
              user={user}
              matiereLabel={matiereLabel}
              niveau={user?.travail_niveau}
              onNavigate={naviguer}
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
                            <li><strong>Nombre de questions</strong> — disponible selon le type d'activité choisi</li>
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
                            <button onClick={() => naviguer('creer-activite')} title="Créer une activité pédagogique"
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
                                { label: 'Créer une séquence', desc: 'Objectif pédagogique → séquence structurée', action: () => setPage('creer-sequence') },
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
                          onClick={() => naviguer('creer-activite')}
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
                        <div
                          onClick={() => setPage('creer-sequence')}
                          style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: '8px', cursor: 'pointer' }}>
                          <span style={{ fontSize: '13px', fontWeight: 700, color: '#1e293b' }}>Créer une séquence</span>
                          <p style={{ fontSize: '12px', color: '#64748b', margin: 0, lineHeight: 1.5 }}>
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
                {/* L'ancien onglet « Comment ça marche » (copie de l'écran en prose, toujours
                    périmée) est remplacé par la visite guidée + la fenêtre déplaçable. */}
                <div style={{ padding: '10px 20px', fontSize: '13px', fontWeight: 700, color: 'var(--bordeaux)', borderBottom: '2px solid var(--bordeaux)', marginBottom: '-1px' }}>
                  {repriseHistorique
                    ? `Reprise : ${objet.trim() || activites.find(a => a.id === params.activite_type_id)?.label || "activité de l'historique"}`
                    : 'Nouvelle activité'}
                </div>
                {/* Frise de progression déplacée en pleine largeur SOUS cette barre (voir plus bas). */}
                {/* Bandeau titre — à droite, une fois la génération TERMINÉE : DEUX boutons bleus, les deux
                    axes de reprise. « Changer votre texte » (ex-« Changer votre demande ») rouvre la saisie
                    pour modifier le contenu. « Changer votre ton » reprend le même texte et régénère dans
                    l'AUTRE ton (masqué si le ton d'origine est inconnu, ex. reprise d'historique). */}
                <div style={{ marginLeft: 'auto', marginRight: 8, display: 'flex', alignItems: 'center', gap: 8, minWidth: 0, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                  {resultat && !loading && (
                    <div data-guide="reprise" style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                      <button
                        type="button"
                        className="btn-primary"
                        onClick={demanderChangerTexte}
                        title="Changer votre texte : rouvre votre texte source pour le modifier (réécrire, réimporter un document, redicter…), puis vous régénérez."
                        style={{ flexShrink: 0 }}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                        Changer votre texte
                      </button>
                      {tonActuel && (
                        <button
                          type="button"
                          className="btn-primary"
                          onClick={demanderChangerTon}
                          title={`Changer votre ton : reprend le même texte et régénère l'activité en ton ${tonActuel === 'academique' ? 'opérationnel (clair, phrases courtes)' : 'académique (formel, phrases longues)'}.`}
                          style={{ flexShrink: 0 }}
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                          Changer votre ton
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Frise de progression — parcours en 4 étapes libellées, pleine largeur, sous la barre du haut. */}
              <div style={{ padding: '14px 20px 12px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
                <FriseProgression
                  typeOk={!!params.activite_type_id}
                  texteOk={!!texte.trim()}
                  loading={loading}
                  resultat={resultat}
                />
              </div>

              <div className="creer-corps">
                {(() => {
                  // Colonne PILOTAGE (Paramètres + Texte source + Vérifier) : seule colonne tant
                  // qu'il n'y a pas de résultat ; passe à DROITE dès qu'un résultat existe.
                  const pilotage = (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                      {activites.length > 0 && (
                        <Parametres
                          activites={activites}
                          params={params}
                          onChange={changerParams}
                          onGenerer={generer}
                          loading={loading}
                          hasResultat={!!resultat}
                          canGenerer={!!texte.trim() && !!params.activite_type_id}
                          onFeedback={() => ouvrirFeedback()}
                          verrouille={(loading || !!resultat) && !entreeDeverrouillee}
                        />
                      )}
                      {/* Étape 2 — Texte source : apparaît dès qu'un type d'activité est choisi (étape 1 faite). */}
                      {params.activite_type_id && (
                        <div data-guide="texte" ref={texteSourceRef}>
                          {/* Verrouillée dès qu'une génération est lancée ou qu'un résultat est là (mode
                              « Régénérer tel quel ») ; « Changer votre demande » la rouvre (entreeDeverrouillee). */}
                          <TexteSource texte={texte} onChange={setTexte} objet={objet} onObjetChange={setObjet} matiere={sessionMatiere} niveau={params.niveau} activiteTypeId={params.activite_type_id} sousType={params.sous_type} verrouille={(loading || !!resultat) && !entreeDeverrouillee} cahierPresent={cahierPresent} loading={loading} hasResultat={!!resultat} />
                        </div>
                      )}
                      {/* Étape 3 — Générer l'activité : cartouche dédiée (badge + titre gras + « i » + chevron),
                          même habillage que les autres. Le bouton Générer, déplacé ici depuis la carte Texte
                          source, lance la génération. Apparaît dès qu'un type est choisi (étape 1 faite). */}
                      {params.activite_type_id && (
                        <section data-guide="generer" className="bg-white rounded border border-gray-200 p-4">
                          <div className="section-title" style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                            <EtapeBadge n={3} fait={!!resultat && !loading} />
                            <span style={{ display: 'inline-flex', alignItems: 'center', fontWeight: 700 }}>
                              Générer l'activité
                              <InfoGuide {...aideActivite('generer', { cahier: cahierPresent })} />
                            </span>
                            {/* Chevron plier/déplier — même pattern cerclé que les autres cartouches. */}
                            <button
                              type="button"
                              onClick={() => setGenererReplie(r => !r)}
                              title={genererReplie ? "Déplier" : "Replier"}
                              style={{ marginLeft: 6, width: 16, height: 16, borderRadius: '50%', border: '1px solid #cbd5e1', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ transition: 'transform 0.2s', transform: genererReplie ? 'rotate(-90deg)' : 'none' }}>
                                <polyline points="6 9 12 15 18 9"/>
                              </svg>
                            </button>
                          </div>
                          {!genererReplie && (
                            <div style={{ fontSize: 13, color: '#64748b', display: 'flex', flexDirection: 'column', gap: 10 }}>
                              {/* Bandeau bleu permanent retiré (28/07) : l'info « référentiel officiel (+ cahier
                                  des charges si déposé) » est désormais dans le « i » de cette cartouche
                                  (aideActivite 'generer' / variante cahier), lisible même carte repliée. */}
                              {/* DEUX boutons = DEUX tons : cliquer choisit le ton ET lance la génération, d'un
                                  seul geste. Aucun présélectionné (règle combos). Pendant la génération : un
                                  indicateur unique qui rappelle le ton en cours. Après : ligne verte + le ton. */}
                              {loading ? (
                                <span className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, opacity: 0.75, cursor: 'wait', alignSelf: 'flex-start' }}>
                                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/></svg>
                                  {tonActuel === 'academique' ? 'Génération en cours — ton académique…'
                                    : tonActuel === 'operationnel' ? 'Génération en cours — ton opérationnel…'
                                    : 'Génération en cours…'}
                                </span>
                              ) : (!resultat || entreeDeverrouillee) ? (
                                <>
                                  <span style={{ fontSize: 12.5, color: '#64748b' }}>Choisissez le ton — c'est lui qui lance la génération :</span>
                                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                                    <button
                                      type="button"
                                      className="btn-primary"
                                      onClick={() => generer('academique')}
                                      disabled={!pretAGenerer}
                                      title={pretAGenerer ? "Générer dans un ton académique : formel, phrases longues, style « documents officiels »." : "Écrivez d'abord votre demande dans la zone de texte"}
                                      style={{ display: 'inline-flex', alignItems: 'center', gap: 6, opacity: pretAGenerer ? 1 : 0.55, cursor: pretAGenerer ? 'pointer' : 'not-allowed' }}
                                    >
                                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                                      Générer — ton académique
                                    </button>
                                    <button
                                      type="button"
                                      className="btn-primary"
                                      onClick={() => generer('operationnel')}
                                      disabled={!pretAGenerer}
                                      title={pretAGenerer ? "Générer dans un ton opérationnel : clair, phrases courtes, consignes directes, style « prof en classe »." : "Écrivez d'abord votre demande dans la zone de texte"}
                                      style={{ display: 'inline-flex', alignItems: 'center', gap: 6, opacity: pretAGenerer ? 1 : 0.55, cursor: pretAGenerer ? 'pointer' : 'not-allowed' }}
                                    >
                                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                                      Générer — ton opérationnel
                                    </button>
                                  </div>
                                </>
                              ) : (
                                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: '#16a34a', fontWeight: 600 }}>
                                  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                                  Activité générée{tonActuel === 'academique' ? ' — ton académique' : tonActuel === 'operationnel' ? ' — ton opérationnel' : ''} — le résultat s'affiche à droite.
                                </span>
                              )}
                            </div>
                          )}
                        </section>
                      )}
                    </div>
                  )

                  // Colonne RÉSULTAT (à DROITE), présente EN PERMANENCE. Avant toute génération : un
                  // encart grisé « Ici s'affichera votre résultat ». Pendant : la jauge. Après :
                  // l'activité générée (ZoneResultat s'affiche d'elle-même dès qu'il y a un résultat).
                  const colonneResultat = (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                      {loading && (
                        <JaugeAttente libelle="aSchool lit le programme officiel et rédige votre activité…" />
                      )}
                      {!loading && !resultat ? (
                        <div style={{
                          border: '1px dashed #cbd5e1', borderRadius: 8, background: '#f8fafc',
                          color: '#94a3b8', fontSize: 14, textAlign: 'center', minHeight: 340,
                          display: 'flex', flexDirection: 'column', alignItems: 'center',
                          justifyContent: 'center', gap: 12, padding: '48px 24px',
                        }}>
                          <svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                            <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
                          </svg>
                          <span>Ici s'affichera votre résultat.</span>
                        </div>
                      ) : (
                        <div ref={resultatRef}>
                          <ZoneResultat
                            resultat={resultat}
                            loading={loading}
                            valide={valide}
                            email={user?.email}
                            onRegenerer={regenerer}
                            onChangerDemande={changerDemande}
                            cahierPresent={cahierPresent}
                          />
                        </div>
                      )}
                    </div>
                  )

                  // Deux colonnes redimensionnables, EN PERMANENCE : pilotage à gauche | résultat à
                  // droite. Poignée ajustable, largeur mémorisée ; sur écran étroit elles s'empilent
                  // (pilotage au-dessus). Cf. components/SplitPane.jsx.
                  return <SplitPane storageKey="creer-split-v2" gauche={pilotage} droite={colonneResultat} />
                })()}
              </div>

              {/* Visite guidée (bulles sur les vrais éléments) + fenêtre déplaçable « Comment
                  ça marche » — les deux lisent le catalogue unique utils/aideCreer.js. */}
              {guideActif && (
                <VisiteGuidee onFermer={fermerGuide} onOuvrirAide={ouvrirAideDepuisGuide} />
              )}
              {fenetreGuide && (
                <FenetreGuide
                  onFermer={() => setFenetreGuide(false)}
                  onRevoirGuide={() => { setFenetreGuide(false); setGuideActif(true) }}
                  onOuvrirAide={ouvrirAideDepuisGuide}
                />
              )}
            </div>
          )}

          {page === 'creer-sequence' && (
            <SequenceForm
              matiere={sessionMatiere}
              niveau={params.niveau}
              onNavigate={naviguer}
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
              onNavigate={naviguer}
              userName={`${user?.prenom || ''} ${user?.nom || ''}`.trim()}
            />
          )}

          {page === 'mes-sequences' && (
            <MesSequences
              onCharger={chargerSequence}
              sessionMatiere={sessionMatiere}
              sessionNiveau={params.niveau}
              onNavigate={naviguer}
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
              onNavigate={naviguer}
            />
          )}

          {page === 'ambiguites' && (
            <Ambiguites
              matiere={sessionMatiere}
              niveau={params.niveau}
              onNavigate={naviguer}
              onCreateSequence={(reformulation) => { setPrefillTheme(reformulation); setPage('creer-sequence') }}
              prefillTexte={prefillAmbiguites}
              onPrefillUsed={() => setPrefillAmbiguites('')}
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
              <button onClick={() => setPage('mes-outils')} title="Retour au menu Mes outils"
                style={{ fontSize: '12px', color: '#6366f1', background: 'none', border: '1px solid #c7d2fe', borderRadius: '5px', padding: '5px 14px', cursor: 'pointer' }}>
                ← Retour aux outils
              </button>
            </div>
          )}

          {page === 'bientot-disponible' && <BientotDisponible />}

          {page === 'mon-profil' && <MonProfil onNavigate={naviguer} />}


          {page === 'aide' && <Aide initialSection={aideSection} />}

          {page === 'mes-feedbacks' && <MesFeedbacks />}

          {page === 'mes-stats' && <MesStats user={user} />}

          {page === 'apropos' && <APropos email={user?.email} matiere={user?.subject} />}
        </main>
      </div>

      <Footer />
      {showFeedback && <Feedback onClose={() => setShowFeedback(false)} contexte={contexteFeedback} incidentRef={feedbackIncidentRef} />}
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


      {fewShotModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: '#fff', borderRadius: '12px', padding: '28px 24px', maxWidth: '420px', width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.2)' }}>
            <div style={{ fontWeight: 700, fontSize: '15px', color: '#1e293b', marginBottom: '10px' }}>
              aSchool reconnaît votre façon de travailler
            </div>
            <p style={{ fontSize: '13.5px', color: '#374151', lineHeight: 1.6, margin: '0 0 20px' }}>
              À partir de 3 activités de ce type d'activité enregistrées, aSchool s'inspire de vos exemples pour générer dans votre style — automatiquement, sans rien régler.
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setFewShotModal(false)}
                title="Fermer ce message"
                style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '9px 18px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
              >
                Fermer
              </button>
              <button
                onClick={() => { setAideSection('apprentissage'); setPage('aide'); setFewShotModal(false) }}
                title="Ouvrir l'aide : comment aSchool apprend votre style"
                style={{ background: 'var(--bleu)', color: '#fff', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
              >
                Plus de détails
              </button>
            </div>
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
            <Route path="programmes" element={<AdminProgrammes />} />
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
            <Route path="analytique">
              <Route index element={<Navigate to="/admin/analytique/general" replace />} />
              <Route path="general"    element={<AdminAnalytiqueGeneral />} />
              <Route path="activites"  element={<AdminAnalytique />} />
              <Route path="outils"     element={<AdminAnalytiqueOutils />} />
              <Route path="communaute" element={<AdminAnalytiqueCommunaute />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
