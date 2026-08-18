import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { useNavigate, useLocation, Link, Outlet } from 'react-router-dom'
import { fetchWithTimeout, TIMEOUT_AUTH } from '../utils/api.js'
import { ActionsEcran } from './actionsEcran.jsx'
import FenetrePro from './FenetrePro.jsx'

const SEP = { separator: true }

// L'AIDE DU MENU NE PASSE PLUS PAR LA BULLE DU NAVIGATEUR (16/08/2026). L'attribut `title` fait
// trois choses qu'on ne veut pas : il attend une seconde, il s'affiche en police système minuscule,
// et il rend illisibles les explications longues — celle du Journal fait 538 caractères, étalés
// sur toute la largeur de l'écran ou tronqués selon le navigateur.
//
// Celle-ci s'ouvre TOUT DE SUITE, à droite de la barre, dans la police de l'application, sur une
// largeur fixe où le texte se lit en paragraphe. Elle suit le survol ET le focus clavier : depuis
// que les rubriques sont des boutons tabulables, la tabulation doit expliquer autant que la souris.
//
// `position: fixed` et non `absolute` : la barre de navigation défile (`overflow-y: auto`), une
// bulle posée dedans serait coupée par le bord. Elle est mesurée après rendu et remontée si elle
// dépasse du bas de l'écran — sans quoi l'aide des dernières entrées sortait de la fenêtre.
const BULLE_LARGEUR = 300
const BULLE_MARGE = 12

// LA BARRE SE REPLIE (16/08/2026). Elle prenait 220 pixels quoi qu'il arrive : sur un portable 13
// pouces ou une fenêtre en demi-écran, les écrans larges — Référentiel, Journal, Formations — se
// tassaient sur ce qui restait, sans aucun moyen de récupérer la place.
//
// Repliée, elle ne garde que les icônes. Les libellés ne sont pas perdus : la bulle d'aide, déjà
// posée sur chaque entrée, donne le nom en gras et l'explication dessous — il n'y avait rien de
// plus à écrire. Le choix est retenu d'une visite à l'autre : régler sa largeur à chaque
// ouverture de l'administration serait une corvée quotidienne.
const LARGEUR_OUVERTE = 220
const LARGEUR_REDUITE = 62
const CLE_MENU_REDUIT = 'aschool_admin_menu_reduit'

function BulleAide({ bulle, gauche }) {
  const ref = useRef(null)
  const [haut, setHaut] = useState(bulle.top)
  useLayoutEffect(() => {
    const hauteur = ref.current ? ref.current.offsetHeight : 0
    const plafond = window.innerHeight - hauteur - BULLE_MARGE
    setHaut(Math.max(BULLE_MARGE, Math.min(bulle.top, plafond)))
  }, [bulle])
  return (
    <div
      ref={ref}
      role="tooltip"
      style={{
        position: 'fixed', left: gauche + 8, top: haut, width: BULLE_LARGEUR, zIndex: 60,
        background: '#0f172a', color: '#e2e8f0', borderRadius: 10,
        border: '1px solid rgba(255,255,255,0.12)',
        boxShadow: '0 10px 30px rgba(15,23,42,0.35)',
        padding: '11px 13px', pointerEvents: 'none',
      }}
    >
      <div style={{ fontSize: 12.5, fontWeight: 700, color: '#fff', marginBottom: 5 }}>{bulle.titre}</div>
      <div style={{ fontSize: 12, lineHeight: 1.5, color: 'rgba(226,232,240,0.85)' }}>{bulle.texte}</div>
    </div>
  )
}

// Une sous-entrée est « active » sur l'égalité stricte de son URL — sauf si elle déclare un
// `prefix`, pour une entrée dont plusieurs adresses mènent au même écran. La règle vit ici, pas
// recopiée aux quatre endroits qui s'en servent.
const estActive = (sub, chemin) => (sub.prefix ? chemin.startsWith(sub.prefix) : chemin === sub.to)

// Menu rangé du général au détaillé, en TROIS BLOCS séparés par un trait : où l'on arrive
// (Tableau de bord), ce que l'on administre (les familles à déplier), ce qui est à soi
// (Tâches à faire, Mon compte, Aide).
// RÈGLE : un menu se range du général au détaillé — familles, puis options. Toute nouvelle
// page se loge SOUS une famille existante, jamais en entrée à plat de plus : une liste plate
// qui grandit d'une ligne par écran finit illisible, et c'est irréversible en pratique.
// « Formations » = l'arbre du contenu pédagogique ET les actions du programme officiel
// (fusion de l'ex-écran Programmes le 30/07 ; renommé « Formations » le 07/08/2026).
const NAV_ITEMS = [
  // — Tableau de bord (plomberie technique + état des fonctionnalités des deux côtés) —
  {
    to:    '/admin/mise-en-route',
    label: 'Tableau de bord',
    // Le TOTAL des gestes en attente, toutes sources confondues : l'entrée de tête porte ce que
    // l'encart « À traiter » de cet écran détaille. Elle s'éteint seule quand tout est traité.
    badgeKey: 'actions_total',
    aide:  'État de la plateforme : les 8 étapes de branchement technique, lues en direct dans la base, et l’avancement des fonctionnalités côté admin et côté prof — fait, en cours, à venir.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 11l3 3L22 4"/>
        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
      </svg>
    ),
  },
  SEP,
  // — Pédagogie — LE CONTENU, réuni sous une famille (16/08/2026). Ces écrans traînaient à plat
  //   en haut du menu, quatre entrées seules au-dessus de huit rubriques : rien ne disait pourquoi
  //   eux échappaient au rangement. Ils parlent pourtant du même sujet — le programme et ce qu'on
  //   en tire — et la règle du menu, écrite juste au-dessus, veut que toute page loge sous une
  //   famille. Seul « Tableau de bord » reste en tête : c'est l'écran d'arrivée, pas un sujet.
  //
  //   « Consulter » a été SUPPRIMÉ le même jour. Il montrait exactement ce que montre Référentiel
  //   — PDF, source, matières, prompt de découpe — mais sans bouton qui écrit. Deux portes vers un
  //   même contenu, dont une que l'administrateur ne se rappelait pas avoir demandée : l'écran,
  //   sa route et sa ligne au tableau de bord sont partis ensemble.
  {
    group:  true,
    label:  'Pédagogie',
    aide:   'Le contenu enseigné : le référentiel officiel qu’on dépose et découpe, puis le programme qui en découle, cycle par cycle et niveau par niveau.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
      </svg>
    ),
    items: [
      { to: '/admin/referentiels', label: 'Référentiel',
        aide: 'L’écran unique du référentiel : choisir un couple, puis créer / consulter / modifier / supprimer — tout en base (get pour afficher, put pour enregistrer).',
        resume: 'Le document officiel : dépôt, découpe et prompts.' },
      { to: '/admin/contenu', label: 'Formations',
        aide: 'Tout le contenu pédagogique en un seul tableau : chaque cycle déroule ses niveaux, chaque niveau montre son référentiel, ses matières et ses types d’activité. Le programme officiel se règle sur place : cocher les matières du niveau, ajouter cycles et niveaux, gérer le catalogue des matières. Désactivation, jamais de suppression.',
        resume: 'Le programme : cycles, niveaux, matières et types.' },
    ],
  },
  // — IA — tout ce qui touche au moteur, réuni (05/08/2026). Les trois morceaux vivaient à trois
  //   endroits sans rapport : « Prompts » en entrée de premier niveau, « Génération LLM » perdue
  //   dans Système, et rien du tout pour les fournisseurs. Un troisième fournisseur les a rendus
  //   indissociables — on choisit un modèle, on règle sa longueur, on écrit son prompt : c'est le
  //   même sujet, ce sont trois clics au même endroit.
  {
    group:  true,
    label:  'IA',
    // Pas de `prefix` de groupe ici : ses écrans ne partagent pas une racine d'URL (Prompts et
    // Génération gardent les leurs, aucun lien existant ne casse). L'activité du groupe se déduit
    // donc de ses entrées, une par une.
    aide:   'Le moteur d’intelligence artificielle : quels fournisseurs et modèles sont disponibles, lequel est en service, avec quels textes d’instruction et quelles longueurs de réponse.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="4" y="7" width="16" height="12" rx="2"/>
        <path d="M12 3v4"/>
        <circle cx="9" cy="13" r="1"/><circle cx="15" cy="13" r="1"/>
      </svg>
    ),
    items: [
      { to: '/admin/ia/fournisseurs', label: 'Fournisseurs',
        // `resume` : la phrase AFFICHÉE en haut de l'écran, à côté du titre. Courte par
        // obligation — elle partage une ligne avec le titre et les boutons. Le reste (`aide`) va
        // dans le « i » : ce qui est utile une fois n'a pas à occuper la place en permanence.
        resume: 'Les moteurs d’IA raccordés, et l’ordre dans lequel ils répondent.',
        aide: 'Le CATALOGUE : quels fournisseurs d’IA sont raccordés, quels modèles ils offrent, et les bornes de chacun (fenêtre, longueur de réponse). C’est ici qu’on ajoute — pas ici qu’on choisit.' },
      { to: '/admin/parametres/generation', label: 'Génération',
        aide: 'Le RÉGLAGE : quel fournisseur et quel modèle sont en service, et comment ils répondent — longueur, température, coupure du flux, re-tentatives. C’est ici qu’on choisit dans le catalogue.' },
      { to: '/admin/ia/statistiques', label: 'Statistiques',
        aide: 'Les TOTAUX : ce que l’IA a consommé, regroupé par modèle, par tâche et par jour. Pour la facture et les tendances — pas pour un appel précis.' },
      { to: '/admin/ia/journal', label: 'Journal',
        aide: 'Le DÉTAIL, appel par appel : la liste de toutes les demandes envoyées à l’IA, la plus récente en haut. Pour chacune : l’heure, la fonction du logiciel qui l’a demandée, le modèle qui a répondu, s’il est allé au bout ou s’il a été coupé en route, le temps qu’il a pris et ce que ça a coûté. C’est ici qu’on regarde quand une génération s’arrête au milieu ou quand un montant surprend. Le texte envoyé et la réponse n’y sont pas : le journal compte les appels, il ne conserve pas leur contenu.' },
    ],
  },
  // — Prompts — rubrique à part entière (16/08/2026). Les quatre familles de prompts étaient les
  //   ONGLETS d'une seule page, derrière l'entrée « Prompts » de la rubrique IA : depuis le menu,
  //   rien ne disait qu'il y en avait quatre — il fallait ouvrir l'écran pour l'apprendre, et y
  //   revenir pour changer de famille. Elles sont désormais quatre sous-entrées, visibles sans
  //   ouvrir. Les URL ne bougent pas : liens et favoris existants continuent de fonctionner.
  {
    group:  true,
    label:  'Prompts',
    // Les quatre sous-entrées partagent la racine `/admin/prompts` : le préfixe suffit à allumer
    // la rubrique, y compris sur les vieilles adresses (`/prompts/prof`) qui redirigent.
    prefix: '/admin/prompts',
    aide:   'Les textes d’instruction envoyés à l’IA, un par outil. Les repères {…} entre accolades sont obligatoires — sans eux, matière, niveau et contenu de l’enseignant ne sont pas injectés.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        <path d="M8 9h8"/><path d="M8 13h5"/>
      </svg>
    ),
    items: [
      { to: '/admin/prompts/referentiels', label: 'Référentiels',
        resume: 'Les prompts écrits à la main pour UN couple cycle-niveau.',
        aide: 'Les prompts qui appartiennent à un référentiel précis — matières, découpe, types d’activité, précisions. Un jeu par couple cycle-niveau : deux diplômes ne se lisent pas avec les mêmes repères.' },
      { to: '/admin/prompts/fonctionnalites', label: 'Fonctionnalités',
        resume: 'Les prompts des outils du prof, rangés par bouton.',
        aide: 'Les textes rangés par FONCTIONNALITÉ : le chemin du menu où le professeur trouve le bouton qui les déclenche (détecteur d’ambiguïtés, analyse de consigne…).' },
      { to: '/admin/prompts/referentiels-communs', label: 'Commun',
        resume: 'Les prompts valables pour TOUS les référentiels.',
        aide: 'Les textes du traitement d’un référentiel au dépôt du PDF — découpe en unités, analyse amont, détection du couple, des matières et des types d’activité. Les mêmes pour tous les référentiels.' },
      { to: '/admin/prompts/autres', label: 'Autres',
        resume: 'Le filet : ce qui ne sert aucun outil en propre.',
        aide: 'Ce qui ne se range nulle part ailleurs — par exemple la ligne qui colle le cahier des charges de l’établissement au bas des prompts de génération.' },
    ],
  },
  // — Profs — les ENSEIGNANTS eux-mêmes. Séparé de « Communication » le 07/08/2026 : gérer un
  // compte et écrire à un groupe ne sont pas le même geste, et les mélanger obligeait à ouvrir
  // une rubrique « et » pour atteindre l'un ou l'autre.
  {
    group:  true,
    label:  'Profs',
    aide:   'Les enseignants : profils, matière et niveau, activation, mot de passe.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
    items: [
      { to: '/admin/profils',       label: 'Profils profs', aide: 'Profils des enseignants — consulter et modifier matière, niveau, prénom et nom.' },
    ],
  },
  // — Communication — ce qui CIRCULE entre eux et nous, dans les deux sens : le mail qui part,
  // le retour qui arrive.
  {
    group:  true,
    label:  'Communication',
    aide:   'Les échanges avec les enseignants : mail groupé qui part, retours qui arrivent.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
    items: [
      { to: '/admin/communication', label: 'Mail groupé', aide: 'Envoyer un message à plusieurs profs en une fois — sélection par matière, filtre, cases à cocher.' },
      { to: '/admin/feedbacks',     label: 'Feedbacks',   aide: 'Retours et suggestions des utilisateurs — note moyenne, répartition, statuts.', badgeKey: 'feedbacks_nouveaux' },
    ],
  },
  // — Supervision —
  {
    group:  true,
    label:  'Supervision',
    aide:   'L\'état du système et la sécurité : sessions, serveur, alertes, journaux d\'accès, audit.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
    ),
    items: [
      { to: '/admin/sessions',   label: 'Sessions',   aide: 'Profs connectés en ce moment — navigateur, dernière activité, durée. Déconnexion forcée possible.' },
      { to: '/admin/serveur',    label: 'Serveur',    aide: 'Métriques VPS (CPU, RAM, disque), statistiques d\'activité et graphe des connexions.' },
      { to: '/admin/alertes',    label: 'Alertes',    aide: 'Alertes automatiques : CPU critique, disque plein, tentatives d\'intrusion. Vérification toutes les 5 min.', badgeKey: 'alertes_nonlues' },
      { to: '/admin/logs',       label: 'Connexions', aide: 'Journal des connexions utilisateurs — qui s\'est connecté, quand et depuis quelle adresse IP.' },
      { to: '/admin/tentatives', label: 'Tentatives', aide: 'Tentatives de connexion échouées — IP, identifiant tenté, statut bloqué ou non.' },
      { to: '/admin/audit',      label: 'Audit',      aide: 'Historique des actions sensibles effectuées par l\'administrateur (déconnexions forcées, suppressions…).' },
    ],
  },
  // — Analytique —
  {
    group:  true,
    label:  'Analytique',
    prefix: '/admin/analytique',
    aide:   'Statistiques et analyses de la plateforme.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10"/>
        <line x1="12" y1="20" x2="12" y2="4"/>
        <line x1="6"  y1="20" x2="6"  y2="14"/>
        <line x1="2"  y1="20" x2="22" y2="20"/>
      </svg>
    ),
    items: [
      { to: '/admin/analytique/general',    label: 'Vue générale',  aide: 'KPIs globaux des activités du monde neuf.' },
      { to: '/admin/analytique/activites',  label: 'Activités',     aide: 'Détail par prof, matière, niveau et type.' },
    ],
  },
  // — Base de données — rubrique à sous-options (même niveau que « Système ») : « Réel » =
  // l'écran garde-fou existant sur la base réellement branchée ; d'autres bases s'ajouteront ici.
  {
    group: true,
    label: 'Base de données',
    aide:  'Les bases de données de la plateforme.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3"/>
        <path d="M3 5v14a9 3 0 0 0 18 0V5"/>
        <path d="M3 12a9 3 0 0 0 18 0"/>
      </svg>
    ),
    items: [
      { to: '/admin/base',       label: 'Réelle', aide: 'Sur quelle base l\'application est réellement connectée (réelle « aschool » vs miroir de test) — garde-fou.' },
      // Cette bulle a annoncé « chantier à venir, rien n'est branché » jusqu'au 16/08/2026 —
      // longtemps après que l'écran fut livré et branché sur six routes. Une aide qui décrit un
      // état passé est pire que pas d'aide : elle détourne de l'écran qu'elle est censée ouvrir.
      { to: '/admin/base/demos', label: 'Démos',
        // PAS DE RÉSUMÉ ICI, et c'est délibéré : cet écran porte ses trois boutons dans la barre
        // du haut. Une phrase entre le titre et les boutons les repoussait hors du cadre sur une
        // fenêtre étroite. Le « i » suffit — il ouvre la même explication, en entier.
        aide: 'Les démonstrations : leur adresse et le référentiel qu’elles montrent. On en crée une, on modifie sa fiche, on la retire, et « Visiter » y emmène directement avec votre identité d’administrateur.' },
    ],
  },
  // — Système —
  {
    group:  true,
    label:  'Système',
    aide:   'Réglages de la plateforme et maintenance.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
      </svg>
    ),
    items: [
      // « Génération LLM » est partie sous IA (05/08/2026) : c'est le réglage du moteur, pas de la
      // plomberie système. Système ne garde que ce qui l'est vraiment.
      { to: '/admin/parametres/email',      label: 'Email',          aide: 'Email de bienvenue envoyé automatiquement à chaque nouvel inscrit.' },
      { to: '/admin/parametres/general',    label: 'Paramètres',     aide: 'Table des paramètres du projet (clé / valeur / description), en consultation.' },
      { to: '/admin/maintenance',           label: 'Maintenance',    aide: 'Nettoyage de la base de données — tokens expirés, sessions fermées, comptes fantômes, logs anciens.' },
      { to: '/admin/planificateur',         label: 'Planificateur',
        resume: 'Les travaux que l’application fait toute seule.',
        aide: 'Les tâches automatiques : ce que le serveur exécute sans personne devant l’écran — surveillance du matériel, veille des tarifs d’IA. Pour chacune : à quelle heure elle passe, quand elle est passée la dernière fois et ce qu’elle a trouvé, à qui part le courriel. L’heure, la cadence, le destinataire et la mise en pause se règlent ici, sans développeur ; « Exécuter maintenant » lance un passage tout de suite, par le même chemin que le déclenchement automatique.' },
    ],
  },
  SEP,
  // — Entrées simples (hors catégorie) —
  // Hors catégorie, comme « Mon compte » : ce carnet n'appartient à aucune rubrique de la
  // plateforme — c'est celui de l'administrateur, sur tous les sujets à la fois.
  // — Tâches à faire — deux listes, et elles ne se mélangent pas (16/08/2026) : ce qui reste à
  //   CODER, et ce qui est déjà PROMIS aux professeurs. La seconde n'existait nulle part côté
  //   administration — pour savoir ce que le prof lit dans « Bientôt disponible », il fallait
  //   ouvrir l'application de son côté.
  {
    group:  true,
    label:  'Tâches à faire',
    aide:   'Ce qui reste à faire, des deux côtés : le carnet du développement, et les fonctionnalités annoncées aux professeurs.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 11l2 2 4-4"/>
        <path d="M20 6v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9z"/>
      </svg>
    ),
    items: [
      { to: '/admin/taches-a-faire', label: 'Développement',
        resume: 'Les idées et les chantiers, notés avant d’être oubliés.',
        aide: 'Le carnet de l’administrateur : ce qu’on décide de faire un jour, avec le contexte qui va avec. Rien ne s’exécute ici — à ne pas confondre avec le « Planificateur », qui fait tourner les travaux automatiques du serveur. Une note se coche quand elle est faite : elle descend dans « Faites » et y reste, parce qu’une décision prise sert encore le jour où la question revient. Pour la faire disparaître pour de bon, « Supprimer ».' },
      // `badgeKey` : le compteur vient du CENTRE D'ACTIONS, pas d'un calcul refait ici — c'est
      // la même source que l'encart « À traiter » du tableau de bord (`GET /api/admin/actions`).
      { to: '/admin/bientot-disponible', label: 'Bientôt disponible', badgeKey: 'actions_bientot_disponible',
        resume: 'Ce qui est annoncé aux professeurs, et ce qu’ils en demandent.',
        aide: 'Les fonctionnalités annoncées dans l’écran « Bientôt disponible » du professeur : le titre et le texte qu’il lit, la famille dont elles relèvent, et le nombre de professeurs qui les ont demandées. En lecture seule — une promesse faite ne se réécrit pas d’un clic, elle se change par migration.' },
    ],
  },
  {
    to:    '/admin/compte',
    label: 'Mon compte',
    aide:  'Changer le mot de passe du compte administrateur.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
    ),
  },
  {
    to:    '/admin/aide',
    label: 'Aide',
    aide:  'Documentation complète du backoffice — fonctionnalités, astuces, comportements.',
    icon:  (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    ),
  },
]

export default function AdminLayout() {
  const [checked, setChecked] = useState(false)
  const [notifs, setNotifs]   = useState({
    feedbacks_nouveaux: 0, alertes_nonlues: 0,
    actions_total: 0, actions_bientot_disponible: 0,
  })
  const navigate  = useNavigate()
  const location  = useLocation()

  // Accordéon : la catégorie dépliée. Elle suit la page — pas seulement au premier affichage.
  const _activeGroup = NAV_ITEMS.find(
    it => it.group && (it.prefix ? location.pathname.startsWith(it.prefix) : it.items.some(s => estActive(s, location.pathname)))
  )
  const groupeDeLaPage = _activeGroup ? _activeGroup.label : null
  const [openGroup, setOpenGroup] = useState(groupeDeLaPage)

  // LE MENU SUIT LA PAGE, MÊME QUAND ON N'EST PAS PASSÉ PAR LUI. Le calcul ci-dessus ne servait
  // qu'au tout premier affichage : un écran atteint autrement — un lien posé dans une page, une
  // redirection — laissait le menu figé sur la rubrique d'avant. Aujourd'hui aucun lien du
  // back-office ne traverse deux rubriques, donc rien ne se voyait ; le premier qu'on posera le
  // ferait apparaître, et personne ne penserait à regarder ici.
  //
  // Replier une rubrique à la main ne change pas l'adresse : elle reste repliée jusqu'à ce qu'on
  // change de page. C'est l'accordéon qui obéit, pas l'inverse.
  //
  // L'ajustement se fait PENDANT LE RENDU, pas dans un effet : c'est le motif React pour un état
  // qui se recale sur ce qui l'entoure. Un effet redessinerait l'écran une seconde fois, menu
  // fermé d'abord, ouvert ensuite — un battement visible à chaque changement de page.
  const [pagePrecedente, setPagePrecedente] = useState(groupeDeLaPage)
  if (groupeDeLaPage && groupeDeLaPage !== pagePrecedente) {
    setPagePrecedente(groupeDeLaPage)
    setOpenGroup(groupeDeLaPage)
  }
  // Les boutons que la page affiche en haut à droite. `null` tant qu'aucune n'en pose.
  const [actionsEcran, setActionsEcran] = useState(null)

  // La barre repliée en colonne d'icônes. Le choix survit à la fermeture de l'onglet.
  const [reduit, setReduit] = useState(() => {
    try { return localStorage.getItem(CLE_MENU_REDUIT) === '1' } catch { return false }
  })
  useEffect(() => {
    try { localStorage.setItem(CLE_MENU_REDUIT, reduit ? '1' : '0') } catch { /* navigation privée */ }
  }, [reduit])
  const largeurBarre = reduit ? LARGEUR_REDUITE : LARGEUR_OUVERTE

  // L'aide survolée (ou reçue au clavier). `null` = aucune bulle ouverte.
  const [bulle, setBulle] = useState(null)
  const montrerAide = (e, titre, texte) => {
    if (!texte) return
    const rect = e.currentTarget.getBoundingClientRect()
    setBulle({ titre, texte, top: rect.top })
  }
  const cacherAide = () => setBulle(null)

  // showError() est un singleton (errorDialog.js) : son handler est enregistré dans le
  // shell prof, NON monté en admin. Sans ce réenregistrement, showError serait inactif
  // sur /admin/* — l'erreur de saisie échouerait en silence. On rebranche la modale ici.
  // PLUS D'ENREGISTREMENT ICI, et c'est le fond du sujet. `ErrorDialog` est montée à la racine
  // de l'application (App.jsx) et écoute déjà ce canal ; cette ligne le lui volait dès qu'on
  // entrait dans l'administration, au profit d'une boîte écrite à la main juste en dessous —
  // sans barre de titre, sans icône, sans croix, et bleue quoi qu'il arrive. Deux dessins pour
  // le même geste, dont un seul recevait les corrections. Constaté le 16/08/2026 : la règle
  // « rouge par défaut » posée dans `ErrorDialog` restait invisible côté administration.

  // LA SESSION SE VÉRIFIE AU MONTAGE — et SEUL un 401 déconnecte.
  //
  // Le `.catch(() => navigate('/admin/login'))` d'avant éjectait sur N'IMPORTE QUELLE erreur du
  // fetch, y compris celle que le navigateur lève quand il ANNULE une requête en vol. C'est
  // exactement ce qui se passe à chaque retour arrière : le composant se remonte, la
  // vérification part, la navigation l'annule, et l'administrateur se retrouve devant l'écran
  // de connexion alors que son cookie est parfaitement valide. Trouvé par la recette
  // (frontend/e2e/admin.spec.js), reproduit à tous les coups.
  //
  // Une coupure réseau n'est pas une déconnexion : dans ce cas l'écran monte quand même, et
  // c'est la première lecture de données qui dira ce qui ne va pas — avec son message à elle.
  useEffect(() => {
    const arret = new AbortController()
    fetch('/api/admin/check', { credentials: 'include', signal: arret.signal })
      .then(r => {
        if (r.status === 401) navigate('/admin/login')
        else setChecked(true)
      })
      .catch(() => { if (!arret.signal.aborted) setChecked(true) })
    return () => arret.abort()
  }, [navigate])

  useEffect(() => {
    if (!checked) return
    function fetchNotifs() {
      // Deux lectures, deux sujets : les compteurs d'activité d'un côté, les GESTES EN ATTENTE
      // de l'autre. Le centre d'actions est calculé à un seul endroit côté serveur — le menu ne
      // recompte rien, il affiche ce que l'encart « À traiter » affiche aussi.
      Promise.all([
        fetch('/api/admin/stats/overview', { credentials: 'include' }).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch('/api/admin/actions', { credentials: 'include' }).then(r => r.ok ? r.json() : null).catch(() => null),
      ]).then(([stats, actions]) => {
        setNotifs({
          feedbacks_nouveaux: stats?.feedbacks_nouveaux || 0,
          alertes_nonlues:    stats?.alertes_nonlues || 0,
          actions_total:      actions?.total || 0,
          actions_bientot_disponible: actions?.par_ecran?.['bientot-disponible'] || 0,
        })
      })
    }
    fetchNotifs()
    const id = setInterval(fetchNotifs, 60000)
    return () => clearInterval(id)
  }, [checked])

  async function logout() {
    await fetchWithTimeout('/api/admin/logout', { method: 'POST', credentials: 'include' }, TIMEOUT_AUTH)
    navigate('/admin/login')
  }

  // Badge rouge réutilisé : en-tête de catégorie (repliée) + sous-entrée.
  const badgeStyle = {
    padding: '1px 6px', borderRadius: 99, fontSize: 10,
    fontWeight: 700, background: '#fee2e2', color: '#dc2626',
    lineHeight: '16px', flexShrink: 0,
  }

  if (!checked) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#f0f4f8' }}>
      <span className="text-gray-400 text-sm">Chargement…</span>
    </div>
  )

  // Fil d'Ariane de la page courante (en-tête fixe) — déduit du menu.
  // L'ICÔNE VIENT DU MENU, elle n'est pas redessinée ici : c'est la même image que dans la barre
  // de gauche, donc l'œil retrouve d'un coup où il se trouve. Une icône propre à l'en-tête aurait
  // fini par diverger de celle du menu, et deux dessins pour un seul endroit désorientent.
  let crumbCat = null, crumbPage = '', crumbIcon = null, crumbAide = '', crumbResume = ''
  for (const it of NAV_ITEMS) {
    if (it.group) {
      const sub = it.items.find(s => estActive(s, location.pathname))
      if (sub) { crumbCat = it.label; crumbPage = sub.label; crumbIcon = it.icon; crumbAide = sub.aide; crumbResume = sub.resume; break }
    } else if (it.to && location.pathname === it.to) {
      crumbPage = it.label; crumbIcon = it.icon; crumbAide = it.aide; crumbResume = it.resume; break
    }
  }

  // La bulle du bouton de repli annonce ce qu'il VA faire, pas l'état où l'on est.
  const titreRepli = reduit ? 'Déplier le menu' : 'Replier le menu'
  const aideRepli = reduit
    ? 'Rendre au menu sa largeur normale, avec les intitulés écrits en toutes lettres.'
    : 'Réduire le menu à ses icônes pour laisser la place aux écrans larges — Référentiel, Journal, Formations. Les intitulés restent lisibles au survol, dans cette bulle.'

  return (
    <div style={{ height: '100vh', display: 'flex', overflow: 'hidden' }}>

      {/* Sidebar — figée, pleine hauteur, repliable en colonne d'icônes */}
      <aside style={{ width: largeurBarre, height: '100vh', background: '#1e293b',
                      display: 'flex', flexDirection: 'column', flexShrink: 0,
                      transition: 'width 0.18s ease' }}>

        {/* Logo — réduit à son initiale quand la barre est repliée, et le bouton passe dessous */}
        <div style={{ padding: reduit ? '16px 8px 14px' : '24px 20px 20px',
                      borderBottom: '1px solid rgba(255,255,255,0.08)',
                      display: 'flex', flexDirection: reduit ? 'column' : 'row',
                      alignItems: reduit ? 'center' : 'flex-start', gap: reduit ? 10 : 8 }}>
          <div style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'white', letterSpacing: '-0.3px', whiteSpace: 'nowrap' }}>
              <span style={{ color: '#e05a6e' }}>A</span>{!reduit && '-SCHOOL'}
            </div>
            {!reduit && (
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginTop: 2 }}>
                Administration
              </div>
            )}
          </div>
          {/* REPLIER / DÉPLIER. Le seul bouton de la barre qui ne mène nulle part : il ne change
              que la place qu'elle prend. Sa bulle dit ce qu'il fera, pas l'état où il est. */}
          <button
            type="button"
            onClick={() => { setReduit(v => !v); cacherAide() }}
            aria-label={titreRepli}
            className="admin-categorie"
            onMouseEnter={e => montrerAide(e, titreRepli, aideRepli)}
            onMouseLeave={cacherAide}
            onFocus={e => montrerAide(e, titreRepli, aideRepli)}
            onBlur={cacherAide}
            style={{
              flexShrink: 0, width: 26, height: 26, borderRadius: 7, padding: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'rgba(255,255,255,0.07)', border: 'none', cursor: 'pointer',
              color: 'rgba(255,255,255,0.55)', transition: 'color 0.15s, background 0.15s',
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"
                 style={{ transform: reduit ? 'rotate(180deg)' : 'none', transition: 'transform 0.18s' }}>
              <polyline points="15 18 9 12 15 6"/>
            </svg>
          </button>
        </div>

        {/* Nav items — défile à l'intérieur de la sidebar si le menu est long */}
        {/* La bulle est posée en coordonnées d'écran : si la barre défile sous la souris, elle
            resterait affichée en face du vide. On la ferme au défilement. */}
        <nav className="admin-nav" onScroll={cacherAide}
             style={{ flex: 1, padding: '12px 10px', overflowY: 'auto' }}>
          {NAV_ITEMS.map((item, i) => {
            if (item.separator) return (
              <div key={`sep-${i}`} style={{ height: 1, background: 'rgba(255,255,255,0.08)', margin: '6px 4px' }} />
            )

            if (item.group) {
              // « Active » = la catégorie contient la page courante (surbrillance).
              const isGroupActive = item.prefix
                ? location.pathname.startsWith(item.prefix)
                : item.items.some(s => estActive(s, location.pathname))
              // « Ouverte » = dépliée (accordéon), indépendant de l'active → on peut replier.
              const isOpen = openGroup === item.label
              // Badges des enfants remontés sur l'en-tête : visibles quand la catégorie est repliée.
              const groupBadge = item.items.reduce(
                (n, s) => n + (s.badgeKey && notifs[s.badgeKey] > 0 ? notifs[s.badgeKey] : 0), 0
              )
              return (
                <div key={`group-${i}`} style={{ marginBottom: 2 }}>
                  {/* En-tête de catégorie — plus grand/gras ; clic = bascule ouvrir / replier.
                      DÉPLIER N'EMMÈNE NULLE PART, et c'est une correction du 16/08/2026. Le clic
                      ouvrait la catégorie ET envoyait sur sa première sous-entrée : on regardait
                      Formations, on ouvrait « Système » par curiosité, et l'écran partait sur
                      Système → Email sans qu'on ait rien demandé. Le travail en cours disparaissait.
                      C'était voulu — pour que la surbrillance bleue suive la catégorie qu'on vient
                      d'ouvrir — mais un détail de couleur ne justifie pas de changer d'écran à la
                      place de l'utilisateur. On déplie pour REGARDER ; on ne bouge que si on
                      clique une sous-entrée. */}
                  {/* UN VRAI BOUTON, PAS UN BLOC CLIQUABLE. C'était un <div> : la tabulation le
                      sautait, et les cinq rubriques du menu étaient inatteignables sans souris —
                      donc leurs écrans aussi, puisqu'aucun autre chemin n'y mène quand la rubrique
                      est repliée. Un <button> prend le focus, répond à Entrée et à Espace, et
                      annonce son état (`aria-expanded`) aux lecteurs d'écran ; tout cela est offert
                      par la balise, il n'y a rien à écrire. Les styles remis à zéro (bordure, fond,
                      police, alignement) ne servent qu'à ce que le bouton garde EXACTEMENT
                      l'apparence du bloc qu'il remplace. */}
                  <button
                    type="button"
                    onClick={() => {
                      // BARRE REPLIÉE : on la rouvre d'abord. Déplier une rubrique dans une colonne
                      // de 62 pixels n'afficherait que des sous-entrées illisibles.
                      if (reduit) { setReduit(false); setOpenGroup(item.label); cacherAide(); return }
                      setOpenGroup(isOpen ? null : item.label)
                    }}
                    aria-expanded={reduit ? false : isOpen}
                    className="admin-categorie"
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      justifyContent: reduit ? 'center' : 'flex-start',
                      width: '100%', textAlign: 'left', font: 'inherit',
                      padding: reduit ? '11px 0' : '11px 12px', border: 'none', borderRadius: 8, marginTop: 4,
                      fontSize: 14, fontWeight: 600,
                      color: isGroupActive ? '#fff' : 'rgba(255,255,255,0.62)',
                      background: isGroupActive ? 'rgba(255,255,255,0.06)' : 'transparent',
                      // UN SEUL TRAIT DANS LA COLONNE, celui de la PAGE ouverte (16/08/2026).
                      // La rubrique n'en porte aucun : elle contient la page, elle n'est pas la
                      // page. Elle se signale par son texte blanc et son fond léger — deux traits
                      // bleus d'intensités voisines obligeaient l'œil à les comparer pour savoir
                      // lequel désignait l'écran, ce qui était la moitié du défaut d'origine.
                      borderLeft: '3px solid transparent',
                      cursor: 'pointer', userSelect: 'none', transition: 'color 0.15s',
                    }}
                    onMouseEnter={e => {
                      if (!isGroupActive) e.currentTarget.style.color = 'rgba(255,255,255,0.9)'
                      montrerAide(e, item.label, item.aide)
                    }}
                    onMouseLeave={e => {
                      if (!isGroupActive) e.currentTarget.style.color = 'rgba(255,255,255,0.62)'
                      cacherAide()
                    }}
                    onFocus={e => montrerAide(e, item.label, item.aide)}
                    onBlur={cacherAide}
                  >
                    <span style={{ opacity: isGroupActive ? 1 : 0.75, display: 'flex', position: 'relative' }}>
                      {item.icon}
                      {/* Repliée, la barre n'a plus de place pour un badge à droite : il se pose
                          en pastille sur l'icône, comme sur une application de téléphone. */}
                      {reduit && groupBadge > 0 && (
                        <span style={{ position: 'absolute', top: -5, right: -7, minWidth: 15, height: 15,
                                       borderRadius: 99, background: '#dc2626', color: '#fff',
                                       fontSize: 9.5, fontWeight: 700, lineHeight: '15px',
                                       textAlign: 'center', padding: '0 3px' }}>{groupBadge}</span>
                      )}
                    </span>
                    {!reduit && <span>{item.label}</span>}
                    <span style={{ marginLeft: 'auto', display: reduit ? 'none' : 'flex', alignItems: 'center', gap: 8 }}>
                      {!isOpen && groupBadge > 0 && <span style={badgeStyle}>{groupBadge}</span>}
                      <svg
                        width="15" height="15" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                        style={{ opacity: 0.6, transform: isOpen ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.18s' }}
                      >
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                    </span>
                  </button>

                  {/* Sous-entrées — plus petites, décalées sous un rail, liseré bordeaux quand
                      actives. Jamais affichées quand la barre est repliée : elles n'ont que des
                      mots à montrer, et il n'y a plus la place de les écrire. */}
                  {isOpen && !reduit && (
                    <div style={{ marginLeft: 18, borderLeft: '1px solid rgba(255,255,255,0.10)', marginTop: 2, marginBottom: 4 }}>
                      {item.items.map(sub => {
                        const isSubActive = estActive(sub, location.pathname)
                        const subBadge = sub.badgeKey && notifs[sub.badgeKey] > 0 ? notifs[sub.badgeKey] : null
                        return (
                          <Link
                            key={sub.to}
                            to={sub.to}
                            style={{
                              display: 'flex', alignItems: 'center', gap: 8,
                              padding: '7px 12px', marginLeft: -1,
                              // LE BORDEAUX N'EST PLUS UNE BALISE DE POSITION (16/08/2026). C'est
                              // la couleur de la marque — logo, icône d'en-tête, pied de page,
                              // trente-quatre fichiers. À servir aussi de « vous êtes ici », elle
                              // ne voulait plus rien dire nulle part. La page où l'on se trouve
                              // porte le bleu PLEIN, le seul repère de position du menu.
                              borderLeft: isSubActive ? '3px solid #3b82f6' : '3px solid transparent',
                              borderRadius: '0 6px 6px 0',
                              fontSize: 12, fontWeight: isSubActive ? 600 : 400,
                              color: isSubActive ? '#fff' : 'rgba(255,255,255,0.5)',
                              background: isSubActive ? 'rgba(59,130,246,0.16)' : 'transparent',
                              textDecoration: 'none', transition: 'all 0.15s',
                            }}
                            onMouseEnter={e => {
                              if (!isSubActive) e.currentTarget.style.color = 'rgba(255,255,255,0.85)'
                              montrerAide(e, sub.label, sub.aide)
                            }}
                            onMouseLeave={e => {
                              if (!isSubActive) e.currentTarget.style.color = 'rgba(255,255,255,0.5)'
                              cacherAide()
                            }}
                            onFocus={e => montrerAide(e, sub.label, sub.aide)}
                            onBlur={cacherAide}
                          >
                            <span>{sub.label}</span>
                            {subBadge && <span style={{ ...badgeStyle, marginLeft: 'auto' }}>{subBadge}</span>}
                          </Link>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            }

            const isActive = !item.external && location.pathname === item.to
            const style = {
              display:        'flex',
              alignItems:     'center',
              justifyContent: reduit ? 'center' : 'flex-start',
              gap:            10,
              padding:        reduit ? '9px 0' : '9px 12px',
              borderRadius:   8,
              marginBottom:   2,
              fontSize:       14,
              fontWeight:     isActive ? 600 : 500,
              color:          isActive ? 'white' : 'rgba(255,255,255,0.55)',
              // Une entrée simple est une PAGE, au même rang qu'une sous-entrée : même bleu
              // plein, même fond bleuté. Le gris d'avant en faisait un troisième code visuel.
              background:     isActive ? 'rgba(59,130,246,0.16)' : 'transparent',
              textDecoration: 'none',
              cursor:         'pointer',
              transition:     'all 0.15s',
              borderLeft:     isActive ? '3px solid #3b82f6' : '3px solid transparent',
            }

            const badge = item.badgeKey && notifs[item.badgeKey] > 0 ? notifs[item.badgeKey] : null

            const content = (
              <>
                <span style={{ opacity: isActive ? 1 : 0.7, display: 'flex', position: 'relative' }}>
                  {item.icon}
                  {reduit && badge && (
                    <span style={{ position: 'absolute', top: -5, right: -7, minWidth: 15, height: 15,
                                   borderRadius: 99, background: '#dc2626', color: '#fff',
                                   fontSize: 9.5, fontWeight: 700, lineHeight: '15px',
                                   textAlign: 'center', padding: '0 3px' }}>{badge}</span>
                  )}
                </span>
                {!reduit && <span>{item.label}</span>}
                {!reduit && badge && (
                  <span style={{
                    padding: '1px 6px', borderRadius: 99, fontSize: 10,
                    fontWeight: 700, background: '#fee2e2', color: '#dc2626',
                    lineHeight: '16px', flexShrink: 0,
                  }}>
                    {badge}
                  </span>
                )}
                {/* Le « ? » n'a plus d'aide propre : c'est la ligne entière qui l'ouvre, et la
                    bulle sort au même endroit qu'on survole le mot ou le rond. */}
                <span
                  aria-hidden="true"
                  style={{
                    display:      reduit ? 'none' : 'flex',
                    marginLeft:   'auto',
                    width:        16,
                    height:       16,
                    borderRadius: '50%',
                    background:   'rgba(255,255,255,0.12)',
                    color:        'rgba(255,255,255,0.5)',
                    fontSize:     10,
                    fontWeight:   700,
                    alignItems:   'center',
                    justifyContent: 'center',
                    cursor:       'help',
                    flexShrink:   0,
                  }}
                >
                  ?
                </span>
              </>
            )

            return item.external ? (
              <a
                key={item.to}
                href={item.to}
                target="afeedback"
                rel="noopener noreferrer"
                style={style}
                onMouseEnter={e => {
                  if (!isActive) e.currentTarget.style.color = 'rgba(255,255,255,0.85)'
                  montrerAide(e, item.label, item.aide)
                }}
                onMouseLeave={e => {
                  if (!isActive) e.currentTarget.style.color = 'rgba(255,255,255,0.55)'
                  cacherAide()
                }}
                onFocus={e => montrerAide(e, item.label, item.aide)}
                onBlur={cacherAide}
              >
                {content}
              </a>
            ) : (
              <Link
                key={item.to}
                to={item.to}
                style={style}
                onMouseEnter={e => {
                  if (!isActive) e.currentTarget.style.color = 'rgba(255,255,255,0.85)'
                  montrerAide(e, item.label, item.aide)
                }}
                onMouseLeave={e => {
                  if (!isActive) e.currentTarget.style.color = 'rgba(255,255,255,0.55)'
                  cacherAide()
                }}
                onFocus={e => montrerAide(e, item.label, item.aide)}
                onBlur={cacherAide}
              >
                {content}
              </Link>
            )
          })}
        </nav>

        {/* Bas de sidebar */}
        <div style={{ padding: '12px 10px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* L'APPLICATION S'OUVRE À CÔTÉ, ELLE NE REMPLACE PAS L'ADMINISTRATION (16/08/2026).
              Ce bouton chargeait l'application du prof dans le même onglet : l'administration
              disparaissait sans un mot, et il fallait refaire tout le chemin — connexion comprise —
              pour revenir à l'écran qu'on était en train de régler.
              Un nouvel onglet règle les deux problèmes à la fois : rien à confirmer, puisque rien
              n'est perdu, et le va-et-vient entre les deux côtés devient un clic d'onglet.
              La flèche « retour » a laissé la place à l'icône de l'ouverture externe : elle
              annonce ce qui va se passer avant qu'on clique. */}
          <a
            href="/"
            target="_blank"
            rel="noopener noreferrer"
            title="Ouvrir l'application aSchool dans un nouvel onglet — l'administration reste ouverte ici"
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              justifyContent: reduit ? 'center' : 'flex-start',
              padding: reduit ? '9px 0' : '9px 12px', borderRadius: 8,
              fontSize: 13, color: 'rgba(255,255,255,0.45)',
              background: 'none', border: 'none', cursor: 'pointer',
              textDecoration: 'none',
              textAlign: 'left', width: '100%', transition: 'color 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.color = 'rgba(255,255,255,0.8)'}
            onMouseLeave={e => e.currentTarget.style.color = 'rgba(255,255,255,0.45)'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/>
              <line x1="10" y1="14" x2="21" y2="3"/>
            </svg>
            {!reduit && 'aSchool'}
          </a>

          <button
            onClick={logout}
            title="Se déconnecter de l'administration"
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              justifyContent: reduit ? 'center' : 'flex-start',
              padding: reduit ? '9px 0' : '9px 12px', borderRadius: 8,
              fontSize: 13, color: 'rgba(255,255,255,0.45)',
              background: 'none', border: 'none', cursor: 'pointer',
              textAlign: 'left', width: '100%', transition: 'color 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.color = 'rgba(255,255,255,0.8)'}
            onMouseLeave={e => e.currentTarget.style.color = 'rgba(255,255,255,0.45)'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            {!reduit && 'Déconnexion'}
          </button>

          {/* LA VRAIE VERSION, ET ON PEUT LA LIRE. « v1.3 · 02/05/2026 » était écrit en dur :
              trois versions de retard, et une date figée au jour où quelqu'un l'a tapée. Elle
              vient maintenant de `package.json`, lue à la construction (`__APP_VERSION__`), et la
              date s'en va — un numéro suffit à dire ce qui tourne.
              Le gris à 20 % la rendait par ailleurs illisible : c'est la première chose qu'on
              demande quand on signale un défaut. */}
          {!reduit && (
            <div style={{ padding: '8px 12px 2px', fontSize: 11.5, color: 'rgba(255,255,255,0.45)',
                          letterSpacing: '0.3px', fontWeight: 600 }}>
              v{__APP_VERSION__}
            </div>
          )}
        </div>
      </aside>

      {/* L'aide de l'entrée survolée. Hors de la barre : elle déborde sur le contenu, ce qu'une
          bulle enfermée dans un conteneur qui défile ne peut pas faire. */}
      {bulle && <BulleAide bulle={bulle} gauche={largeurBarre} />}

      {/* Contenu principal — en-tête fixe + zone centrale qui défile + footer figé */}
      <main style={{ flex: 1, height: '100vh', background: '#f0f4f8', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* En-tête fixe — fil d'Ariane « catégorie › page » : où on est */}
        {/* Hauteur LIBRE, pas figée à 56 pixels : le texte d'explication doit tenir en entier.
            Une barre de hauteur fixe le coupait au milieu d'une phrase — une information à moitié
            lisible ne renseigne personne et oblige à survoler pour connaître la fin. */}
        <header style={{
          flexShrink: 0, minHeight: 56, borderBottom: '1px solid #e2e8f0', background: '#fff',
          display: 'flex', alignItems: 'center', gap: 8, padding: '8px 32px',
        }}>
          {/* L'icône de la rubrique, à la taille du titre : c'est elle qu'on voit en premier, le
              chemin écrit ne fait que confirmer. */}
          {crumbIcon && (
            <span style={{ display: 'inline-flex', color: '#A63045', transform: 'scale(1.25)', transformOrigin: 'center', marginRight: 4 }}>
              {crumbIcon}
            </span>
          )}
          {crumbCat && (
            <>
              <span style={{ fontSize: 13, color: '#94a3b8' }}>{crumbCat}</span>
              <span style={{ fontSize: 13, color: '#cbd5e1' }}>›</span>
            </>
          )}
          {/* LA PAGE EST UN TITRE, pas la fin d'une phrase : elle est écrite comme tel. La rubrique
              qui la précède reste petite et grise — elle situe, elle ne nomme pas. */}
          <span style={{ fontSize: 20, fontWeight: 700, color: '#0f172a', letterSpacing: '-0.3px', flexShrink: 0 }}>{crumbPage || 'Administration'}</span>
          {/* CE QUE FAIT LA PAGE, ÉCRIT EN CLAIR — entre son titre et ses boutons. C'est une
              information, pas une décoration : elle reste affichée en permanence, sur une barre
              qui ne défile pas. En infobulle, il fallait savoir qu'il y avait quelque chose à
              survoler pour la lire ; dans le contenu, elle disparaissait au premier défilement. */}
          {crumbResume && (
            <span style={{ fontSize: 12, color: '#64748b', lineHeight: 1.35 }}>{crumbResume}</span>
          )}
          {/* LE RESTE EST DANS LE « i ». L'explication complète est utile la première fois et
              encombrante les suivantes : elle se survole au lieu de tenir la ligne. */}
          {crumbAide && <AideEcran titre={crumbPage} texte={crumbAide} />}
          {/* LES ACTIONS DE LA PAGE, à droite de l'en-tête FIXE. Chaque écran y dépose ses
              boutons (voir `useActionsEcran`) : ils restent sous les yeux quand la page défile,
              alors qu'un bouton posé dans le contenu disparaît dès qu'on descend.

              Cette place était occupée par le moteur « en service ». Elle ne l'est plus : depuis
              que les appels descendent la LISTE des fournisseurs, il n'y a plus un moteur élu, et
              afficher `settings.ai_provider` désignait un fournisseur qui n'est pas celui qui
              répond. Un en-tête qui se trompe est pire qu'un en-tête muet. */}
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            {actionsEcran}
          </div>
        </header>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          {/* Toutes les pages admin exploitent toute la largeur (comme Référentiel et Type d'activité) :
              plus de plafond, une seule règle pour tout le back-office. */}
          <div style={{ padding: 32, width: '100%', margin: '0 auto' }}>
            <ActionsEcran.Provider value={setActionsEcran}>
              <Outlet />
            </ActionsEcran.Provider>
          </div>
        </div>

        {/* Footer */}
        <footer style={{
          borderTop: '1px solid #e2e8f0',
          padding: '12px 32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#f0f4f8',
          flexShrink: 0,
        }}>
          <span style={{ fontSize: 11, color: '#94a3b8' }}>
            <span style={{ color: '#A63045', fontWeight: 700 }}>A</span>-SCHOOL — Administration
          </span>

          {/* Légende des pastilles d'étape — seulement sur l'écran Référentiel, où elles servent.
              Placée dans le footer global pour qu'un lecteur extérieur comprenne les couleurs. */}
          {location.pathname === '/admin/referentiels' && (
            <span style={{ display: 'flex', flexWrap: 'wrap', gap: 14, fontSize: 11, color: '#94a3b8', alignItems: 'center' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 9, height: 9, borderRadius: '50%', background: '#16a34a' }} />fait / validé
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 9, height: 9, borderRadius: '50%', background: '#dc2626' }} />à faire
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 9, height: 9, borderRadius: '50%', background: '#facc15', border: '1px solid rgba(0,0,0,0.12)' }} />non vérifié
              </span>
            </span>
          )}

          <span style={{ fontSize: 11, color: '#94a3b8' }}>
            © {new Date().getFullYear()} AFIA — aschool.fr
          </span>
        </footer>
      </main>

      {/* Modale bloquante admin (showError) — overlay plein écran, impossible à ignorer */}
    </div>
  )
}


// L'AIDE DE L'ÉCRAN — le « i » derrière le titre.
//
// LA RÈGLE DE LA MAISON, ET PAS UNE AUTRE : un « i » se survole pour une phrase courte, et se
// CLIQUE pour ouvrir une vraie fenêtre — `FenetrePro`, la coquille unique : déplaçable par sa
// barre de titre, étirable par le coin, avec son ascenseur, sans voile qui bloque l'écran
// derrière. C'est ce que font déjà « Comment ça marche » et les guides des cartouches côté
// professeur. Un panneau écrit sur mesure ici serait une deuxième mécanique à maintenir, et une
// fenêtre qui ne se déplace pas cache justement ce qu'on est en train de lire.
function AideEcran({ titre, texte }) {
  const [ouvert, setOuvert] = useState(false)
  return (
    <>
      <button
        onClick={() => setOuvert(true)}
        title="À quoi sert cet écran ? Cliquez pour ouvrir l’aide."
        style={{
          width: 17, height: 17, borderRadius: '50%', cursor: 'pointer', padding: 0, flexShrink: 0,
          border: '1px solid ' + (ouvert ? '#A63045' : '#cbd5e1'),
          color: ouvert ? '#fff' : '#64748b', background: ouvert ? '#A63045' : '#f8fafc',
          fontSize: 11, fontWeight: 700, fontStyle: 'italic', lineHeight: '15px',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        }}
      >i</button>

      {/* Pas de hauteur imposée : ces aides font trois lignes pour certaines et vingt pour
          d'autres — la fenêtre s'ajuste au texte qu'elle porte. */}
      {ouvert && (
        <FenetrePro titre={`Aide — ${titre}`} onFermer={() => setOuvert(false)} largeur={520}>
          <div style={{ overflowY: 'auto', padding: '14px 16px', fontSize: 13, lineHeight: 1.55, color: '#334155' }}>
            {texte}
          </div>
        </FenetrePro>
      )}
    </>
  )
}
