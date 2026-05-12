# aSchool — Spécification PWA (Progressive Web App)

> **Rôle : document de conception et de planification de la version mobile de aSchool.**
>
> Ce document n'est pas du code — c'est un plan de travail à lire, annoter et valider avant de commencer le développement.
>
> Il part de l'existant (stack, code, composants) pour décrire précisément ce qu'il faut faire, dans quel ordre, avec quels outils, et pourquoi.
>
> **Rédigé le : 03/05/2026 — À valider avant de commencer le développement**

---

## Sommaire

1. [Pourquoi une PWA et pas une app native](#1-pourquoi-une-pwa-et-pas-une-app-native)
2. [Qu'est-ce qu'une PWA — les 3 piliers](#2-quest-ce-quune-pwa--les-3-piliers)
3. [État de l'existant — ce qui est déjà favorable](#3-état-de-lexistant--ce-qui-est-déjà-favorable)
4. [Ce qui manque — inventaire précis](#4-ce-qui-manque--inventaire-précis)
5. [Outils et technologies retenus](#5-outils-et-technologies-retenus)
6. [Analyse composant par composant](#6-analyse-composant-par-composant)
7. [Cas d'usage mobile spécifiques à aSchool](#7-cas-dusage-mobile-spécifiques-à-aSchool)
8. [Plan d'implémentation — 4 étapes](#8-plan-dimplémentation--4-étapes)
9. [Stratégie offline et gestion du cache](#9-stratégie-offline-et-gestion-du-cache)
10. [Contraintes et points d'attention](#10-contraintes-et-points-dattention)
11. [Checklist de validation finale](#11-checklist-de-validation-finale)
12. [Effort estimé et récapitulatif](#12-effort-estimé-et-récapitulatif)

---

## 1. Pourquoi une PWA et pas une app native

Une app native (iOS + Android) nécessite :
- Deux bases de code séparées (Swift/SwiftUI pour iOS, Kotlin/Jetpack pour Android) ou un framework hybride (React Native, Flutter)
- Un compte Apple Developer (99 $/an) et Google Play (25 $ une fois)
- Une review Apple (1 à 7 jours, peut être refusée) à chaque mise à jour
- Une commission de 30% sur les achats in-app
- Une compétence native (ou un prestataire) en plus du stack actuel

Une **PWA** utilise le code React déjà en place, s'installe depuis le navigateur, et est disponible sur iOS et Android sans passer par un store. Les mises à jour se déploient comme le reste du code — un `git push` suffit.

| Critère | App native | PWA |
|---|---|---|
| Bases de code | 2 (iOS + Android) | 1 (même code React) |
| Store requis | Oui (Apple + Google) | Non |
| Review Apple | Oui — délai + refus possibles | Non |
| Mise à jour | Via le store (délai) | Immédiate via déploiement VPS |
| Coût | 99 $/an + 25 $ + commission 30% | 0 € supplémentaire |
| Compétence requise | Native ou React Native | Vite plugin + CSS responsive |
| Accès caméra | Oui (natif) | Oui (API browser `getUserMedia`) |
| Accès micro | Oui (natif) | Oui (API browser `MediaRecorder`) |
| Notifications push | Oui | Oui (Web Push API) |
| Installation | Via store | "Ajouter à l'écran d'accueil" |
| Mode offline | Oui | Oui (Service Worker) |

**Conclusion : la PWA est le bon choix pour aSchool.** Elle couvre tous les cas d'usage mobile (OCR photo, dictée vocale, consultation des activités), sans coût ni dépendance externe, avec le code déjà écrit.

---

## 2. Qu'est-ce qu'une PWA — les 3 piliers

Une Progressive Web App repose sur trois piliers techniques. Les 3 sont nécessaires pour qu'un navigateur propose l'installation à l'utilisateur.

### Pilier 1 — Installable
L'application peut être ajoutée à l'écran d'accueil du téléphone, exactement comme une app native. Elle apparaît avec une icône, un nom, et s'ouvre sans la barre d'adresse du navigateur.

**Ce que ça nécessite :**
- Un fichier `manifest.json` déclarant le nom, les icônes, la couleur de thème, le mode d'affichage (`standalone`)
- Une icône en plusieurs tailles (au minimum 192×192 et 512×512 px)
- Le site servi en HTTPS (déjà le cas sur school.afia.fr avec Let's Encrypt)
- Un Service Worker enregistré

### Pilier 2 — Rapide (Shell Architecture)
L'interface de base (Header, Sidebar, structure) se charge instantanément depuis le cache, même avec une connexion lente. Seul le contenu dynamique (génération d'activité, appel à l'API Groq) nécessite internet.

**Ce que ça nécessite :**
- Un Service Worker qui met en cache les assets statiques (JS, CSS, icônes, polices)
- Une stratégie de cache définie par type de ressource

### Pilier 3 — Capable (Accès aux APIs du navigateur)
La PWA utilise les APIs natives du navigateur mobile : caméra (OCR), microphone (dictée vocale), vibration, partage natif.

**Ce que ça nécessite :**
- Ces APIs sont déjà utilisées dans l'app web — elles fonctionnent telles quelles sur mobile
- Aucun code supplémentaire pour ces fonctionnalités

---

## 3. État de l'existant — ce qui est déjà favorable

### Stack (extrait de `frontend/package.json`)

| Composant | Version | Note |
|---|---|---|
| React | 19.2.5 | Dernière version stable |
| Vite | 8.0.10 | Supporte `vite-plugin-pwa` nativement |
| Tailwind CSS | 4.2.4 | Via `@tailwindcss/vite` — breakpoints responsive disponibles |
| react-router-dom | 7.14.2 | SPA routing — compatible PWA |
| docx | 9.6.1 | Export Word côté client — fonctionne sur mobile |

### Infrastructure déjà en place

| Prérequis PWA | État |
|---|---|
| HTTPS obligatoire | ✅ Let's Encrypt sur school.afia.fr — expire 2026-07-15, renouvellement auto |
| SPA (Single Page Application) | ✅ React Router avec une seule entrée `index.html` |
| Proxy API configuré | ✅ Vite proxy `/api` → `localhost:8000` en dev, Nginx en prod |
| Tailwind CSS | ✅ Installé — breakpoints `sm:` `md:` `lg:` disponibles immédiatement |
| Dictée vocale (API microphone) | ✅ Déjà implémentée — fonctionnera sur mobile sans modification |
| OCR image (API fichier) | ✅ Déjà implémentée — la caméra mobile peut fournir une image |
| Authentification JWT httpOnly | ✅ Les cookies httpOnly fonctionnent sur mobile |
| Heartbeat (App.jsx) | ✅ `setInterval` 60s — fonctionne sur mobile |

### Architecture fichiers frontend (état 03/05/2026)

```
frontend/src/
├── App.jsx                    # Router principal + MainApp + logique heartbeat
├── main.jsx                   # Point d'entrée React
├── index.css                  # Variables CSS globales (--bleu, --bordeaux)
├── App.css                    # Styles globaux additionnels
├── context/
│   └── AuthContext.jsx        # État auth global (user, login, logout)
├── components/
│   ├── Header.jsx             # Barre du haut — logo + matière + email + déconnexion
│   ├── Sidebar.jsx            # Navigation latérale — déjà collapsible (48px/176px)
│   ├── Footer.jsx             # Pied de page
│   ├── TexteSource.jsx        # Zone saisie texte + boutons Fichier/Dicter
│   ├── Parametres.jsx         # Sélecteurs activité/niveau/précision + bouton Générer
│   ├── ZoneResultat.jsx       # Affichage résultat + boutons export
│   ├── MesActivites.jsx       # Liste des activités sauvegardées
│   ├── MonProfil.jsx          # Formulaire profil prof
│   ├── Feedback.jsx           # Modale feedback (catégorie + message)
│   ├── Notation.jsx           # Modale notation (étoiles + commentaire)
│   ├── Aide.jsx               # Page d'aide
│   ├── APropos.jsx            # Page À propos
│   ├── EyeIcon.jsx            # Composant SVG partagé (œil mot de passe)
│   └── AdminLayout.jsx        # Layout sidebar admin
└── pages/
    ├── Login.jsx / Signup.jsx / VerifyEmail.jsx
    ├── ForgotPassword.jsx / ResetPassword.jsx
    ├── MentionsLegales.jsx
    ├── AdminLogin.jsx
    └── Admin*.jsx (10 pages admin)
```

---

## 4. Ce qui manque — inventaire précis

### 4.1 — Fichiers PWA manquants

| Fichier | Rôle | Emplacement |
|---|---|---|
| `manifest.json` | Nom, icônes, couleurs, mode standalone | `frontend/public/manifest.json` |
| `sw.js` (généré) | Service worker — cache des assets | Généré automatiquement par vite-plugin-pwa |
| `registerSW.js` (généré) | Enregistrement du SW dans le navigateur | Généré automatiquement |
| Icônes PNG | 192×192 px et 512×512 px minimum | `frontend/public/icons/` |
| Méta tags PWA dans `index.html` | `theme-color`, `apple-mobile-web-app-*` | `frontend/index.html` |

### 4.2 — Composants à rendre responsive

**Aucun composant n'est actuellement adapté mobile.** Le layout principal (`App.jsx`) utilise `flex flex-row` (sidebar fixe + contenu) sans aucun breakpoint. Sur un écran de 390px (iPhone 14), la sidebar occupe 176px sur 390px disponibles — l'interface est inutilisable.

Liste des composants à modifier, classés par priorité :

| Composant | Problème mobile | Effort |
|---|---|---|
| `App.jsx` (layout global) | `flex flex-row` sans breakpoint — sidebar prend 45% de l'écran | Fort |
| `Sidebar.jsx` | Largeur fixe 176px — pas de mode drawer/overlay mobile | Fort |
| `Header.jsx` | Logo + slogan + matière + email + bouton déco sur une seule ligne — déborde sur mobile | Moyen |
| `Parametres.jsx` | Sélecteurs en ligne — OK en hauteur mais vérifier les dropdowns | Faible |
| `TexteSource.jsx` | Textarea + boutons — OK mobile mais ajuster la hauteur | Faible |
| `ZoneResultat.jsx` | Boutons export en ligne — risque de débordement | Faible |
| `MesActivites.jsx` | Liste de cartes — vérifier la lisibilité | Faible |
| `MonProfil.jsx` | Formulaire — OK mobile nativement | Très faible |
| `Feedback.jsx` / `Notation.jsx` | Modales `position: fixed` — OK sur mobile | Très faible |
| Pages auth (`Login.jsx`, `Signup.jsx`, etc.) | Formulaires centrés — généralement OK sur mobile | Très faible |
| Pages admin (`Admin*.jsx`) | Tableaux larges — difficiles sur mobile | Non prioritaire (admin sur desktop) |

### 4.3 — Configuration Vite manquante

Le fichier `vite.config.js` actuel ne déclare pas `vite-plugin-pwa`. À ajouter lors de l'implémentation.

---

## 5. Outils et technologies retenus

### outil principal — vite-plugin-pwa

**Pourquoi vite-plugin-pwa :**
- Plugin officiel pour Vite — intégration native avec le build system déjà en place
- Génère automatiquement le Service Worker via **Workbox** (bibliothèque Google, éprouvée)
- Génère et injecte le `manifest.json` dans le `index.html` au build
- Gère le cycle de vie du Service Worker (mise à jour, rechargement)
- Compatible avec React 19 et Vite 8

```bash
# Installation — une seule commande
npm install -D vite-plugin-pwa
```

**Ce que vite-plugin-pwa fait automatiquement :**
- Précache tous les assets statiques produits par le build (JS, CSS, images)
- Génère le `sw.js` avec les bonnes stratégies de cache selon la config
- Injecte le `<link rel="manifest">` dans le HTML de production
- Gère le prompt de mise à jour quand une nouvelle version est déployée

### Workbox (utilisé en coulisses par vite-plugin-pwa)

Workbox est la bibliothèque de référence pour les Service Workers, maintenue par Google. Elle gère les stratégies de cache :

| Stratégie | Description | Usage dans aSchool |
|---|---|---|
| `CacheFirst` | Sert depuis le cache, met à jour en arrière-plan | Assets statiques (JS, CSS, icônes) |
| `NetworkFirst` | Essaie le réseau, fallback cache | Appels API (liste des activités, profil) |
| `NetworkOnly` | Réseau obligatoire — pas de cache | Génération d'activité (Groq en temps réel) |
| `StaleWhileRevalidate` | Sert le cache ET met à jour en arrière-plan | Pages statiques internes |

### Tailwind CSS (déjà installé — version 4)

Les breakpoints Tailwind permettent le responsive sans aucune librairie supplémentaire :

| Breakpoint | Taille d'écran | Usage |
|---|---|---|
| *(aucun)* | < 640px | Mobile — styles de base |
| `sm:` | ≥ 640px | Petites tablettes |
| `md:` | ≥ 768px | Tablettes |
| `lg:` | ≥ 1024px | Desktop |

**Stratégie retenue : mobile-first.** On écrit les styles pour mobile en premier, on surcharge pour desktop avec `md:` et `lg:`.

### Outil de validation — Lighthouse (intégré dans Edge)

Lighthouse est l'outil officiel Google/Microsoft pour auditer une PWA. Il est accessible dans Edge (F12 → onglet Lighthouse → cocher PWA). Il donne un score et une checklist des critères manquants.

**Score Lighthouse PWA cible : 100/100**

---

## 6. Analyse composant par composant

### 6.1 — Layout global (`App.jsx`)

**Situation actuelle :**
```jsx
<div className="flex flex-col min-h-screen">
  <Header />
  <div className="flex flex-1 min-h-0">   {/* flex row — sidebar + main côte à côte */}
    <Sidebar />
    <main className="flex-1 p-6 ...">
      {/* contenu */}
    </main>
  </div>
  <Footer />
</div>
```

**Problème :** `flex flex-1 min-h-0` crée un layout en colonne horizontale (sidebar à gauche, contenu à droite) sans aucune condition responsive. Sur mobile, la sidebar prend 176px sur ~390px disponibles.

**Solution :**
```jsx
{/* Mobile : colonne (sidebar devient header drawer) */}
{/* Desktop : ligne (sidebar fixe + contenu) */}
<div className="flex flex-1 min-h-0 flex-col md:flex-row">
  <Sidebar ... />
  <main className="flex-1 p-4 md:p-6 ...">
```

**Changement central :** sur mobile, le layout devient une colonne. La Sidebar passe en mode drawer (overlay) et se cache par défaut. Un bouton hamburger dans le Header l'affiche/masque.

---

### 6.2 — Sidebar (`Sidebar.jsx`)

**Situation actuelle :**
La Sidebar a déjà un état `collapsed` (48px compressé / 176px ouvert) pour le desktop. Ce mécanisme existe mais ce n'est pas un drawer mobile — il est toujours visible et prend de l'espace.

**Problème mobile :** même en collapsed (48px), sur un écran de 390px la sidebar prend 12% de la largeur et n'est pas tapable facilement.

**Solution : drawer mobile**

Sur mobile (< 768px), la sidebar devient un panneau overlay qui :
- Est **masqué par défaut** (hors écran, `transform: translateX(-100%)`)
- S'affiche quand l'utilisateur tape le bouton hamburger dans le Header (`transform: translateX(0)`)
- Se ferme en tapant en dehors ou en naviguant vers une page
- Recouvre le contenu avec un fond semi-transparent (backdrop)

Sur desktop (≥ 768px), le comportement actuel (collapsed/expanded) est conservé tel quel.

**État à ajouter dans `App.jsx` (ou dans `Sidebar.jsx`) :**
```jsx
const [sidebarOpen, setSidebarOpen] = useState(false)
// Passer sidebarOpen + setSidebarOpen à Header et Sidebar
```

**Modifications dans `Sidebar.jsx` :**
```jsx
<aside className={`
  fixed inset-y-0 left-0 z-50 bg-white border-r border-gray-200 flex flex-col
  transform transition-transform duration-200
  md:relative md:transform-none md:z-auto
  ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
`} style={{ width: collapsed ? 48 : 176 }}>
```

**Backdrop mobile (à ajouter dans App.jsx) :**
```jsx
{sidebarOpen && (
  <div
    className="fixed inset-0 bg-black/40 z-40 md:hidden"
    onClick={() => setSidebarOpen(false)}
  />
)}
```

**Comportement navigation :** fermer le drawer après chaque navigation (appel `setSidebarOpen(false)` dans `onNavigate`).

---

### 6.3 — Header (`Header.jsx`)

**Situation actuelle :**
```jsx
<header className="flex items-center justify-between px-6 py-4">
  <div>Logo | Slogan</div>
  <div>| Matière | Email | [Bouton déco]</div>
</header>
```

**Problème mobile :** tout sur une ligne. Sur 390px, "aSchool | Générateur d'activités pédagogiques | Français | prof@ac-paris.fr | Se déconnecter" ne tient pas — overflow ou wrapping non géré.

**Solution : deux couches**

Sur mobile :
- Ligne gauche : **bouton hamburger** (ouvre la sidebar drawer) + logo **aSchool**
- Ligne droite : **matière** (important) + **bouton déco** (compact, icône seule)
- Le slogan et l'email disparaissent sur mobile (pas essentiels)

Sur desktop : comportement actuel conservé.

```jsx
<header className="flex items-center justify-between px-4 md:px-6 py-3 md:py-4">
  {/* Mobile gauche : hamburger + logo */}
  <div className="flex items-center gap-3">
    <button className="md:hidden" onClick={toggleSidebar}>
      <IconMenu />
    </button>
    <span className="font-bold text-xl">
      <span style={{ color: 'var(--bordeaux)' }}>A</span>-SCHOOL
    </span>
    {/* Slogan masqué sur mobile */}
    <span className="hidden md:inline text-white" style={{ opacity: 0.75 }}>
      | Générateur d'activités pédagogiques
    </span>
  </div>
  {/* Droite : infos utilisateur */}
  <div className="flex items-center gap-3 text-sm">
    <span className="font-semibold text-white">{matiere}</span>
    {/* Email masqué sur mobile */}
    <span className="hidden md:inline" style={{ color: 'rgba(255,255,255,0.6)' }}>{email}</span>
    {/* Bouton déco : texte masqué sur mobile, icône seule */}
    <button onClick={onLogout} title="Se déconnecter">
      <svg .../>
      <span className="hidden md:inline">Se déconnecter</span>
    </button>
  </div>
</header>
```

---

### 6.4 — Zone texte source (`TexteSource.jsx`)

**Situation actuelle :** textarea + boutons "Fichier .txt / scan JPG" et "Dicter".

**Sur mobile :** la textarea est nativement utilisable sur mobile. Le clavier virtuel s'ouvre automatiquement. Les boutons d'action doivent être suffisamment grands (minimum 44×44px recommandé par Apple HIG).

**Cas d'usage mobile fort :** le bouton "Fichier" sur mobile ouvre le sélecteur de fichiers du téléphone, qui inclut la **caméra**. Un prof peut photographier directement une page de manuel ou une photocopie — c'est l'OCR en action. Ce flux est déjà fonctionnel sur mobile, il faut juste s'assurer que le bouton est assez grand et accessible.

**Modifications légères :**
- Boutons `btn-action` : ajouter `min-h-[44px]` et `px-4` pour les rendre tapables
- Textarea : hauteur auto sur mobile (`min-h-[100px]` au lieu de `rows=8` fixe)

---

### 6.5 — Paramètres (`Parametres.jsx`)

**Situation actuelle :** sélecteurs HTML natifs (`<select>`) pour activité, niveau, sous-type, nombre de questions. Case à cocher pour la correction.

**Sur mobile :** les `<select>` natifs sont parfaitement adaptés au mobile — le navigateur ouvre une roue de sélection sur iOS, une liste sur Android. Aucune modification majeure requise.

**Modifications légères :**
- Vérifier que les labels et sélecteurs s'empilent proprement en colonne sur petit écran
- Bouton "Générer" : pleine largeur sur mobile (`w-full md:w-auto`)
- Modale "Ajuster pour cette activité" : vérifier la largeur sur mobile

---

### 6.6 — Zone résultat (`ZoneResultat.jsx`)

**Situation actuelle :** zone d'affichage du texte généré + boutons [.txt] [Word] [Fermer].

**Sur mobile :** le texte est scrollable. Les boutons risquent de déborder si mis en ligne.

**Modification :**
- Sur mobile, les boutons d'export s'empilent en colonne ou en grille 2×2
- Boutons pleine largeur sur mobile

---

### 6.7 — Mes activités (`MesActivites.jsx`)

**Situation actuelle :** liste de cartes d'activités sauvegardées.

**Sur mobile :** les cartes doivent passer en colonne unique et être suffisamment hautes pour être tapables. Le titre, la date, et le bouton "Recharger" doivent être lisibles à 390px.

---

### 6.8 — Modales (Feedback, Notation, tipModal dans App.jsx)

**Situation actuelle :** `position: fixed; inset: 0` avec un conteneur centré. La modale tipModal est `width: 420px, maxWidth: 92vw`.

**Sur mobile :** `maxWidth: 92vw` gère déjà le cas mobile correctement. Les modales sont généralement OK. Vérifier la hauteur sur petit écran (ne pas déborder vers le bas).

**Modification légère :** ajouter `max-height: 90vh; overflow-y: auto` sur le contenu des modales pour les écrans très petits.

---

### 6.9 — Pages auth (Login, Signup, ForgotPassword, ResetPassword, VerifyEmail)

**Situation actuelle :** formulaires centrés dans une card.

**Sur mobile :** les formulaires centrés sont généralement déjà bien adaptés. Vérifier que la card ne déborde pas horizontalement et que les inputs sont assez hauts (44px minimum).

**Modifications très légères :** `w-full max-w-md mx-auto px-4` — probablement déjà en place.

---

### 6.10 — Pages admin

**Situation actuelle :** tableaux avec nombreuses colonnes, sidebar admin fixe.

**Sur mobile :** non prioritaire. L'admin est une interface de gestion conçue pour le desktop. L'approche retenue est d'afficher un **message d'avertissement sur mobile** ("L'interface d'administration est optimisée pour un écran d'ordinateur") plutôt que de rendre tous les tableaux responsive — investissement disproportionné pour un usage qui n'existera pas.

---

## 7. Cas d'usage mobile spécifiques à aSchool

Ces cas d'usage sont des arguments forts pour la PWA et doivent être testés en priorité.

### Cas 1 — OCR photo directe (cas d'usage #1 mobile)

Un prof en salle des profs ou en classe prend une photo d'un manuel, d'une photocopie ou d'un document avec l'appareil photo de son téléphone. Il la soumet directement à aSchool pour générer une activité.

**Flux actuel :** le bouton "Fichier .txt / scan JPG" ouvre un `<input type="file">`. Sur mobile, cet input propose automatiquement la caméra comme source. L'OCR (route `/api/ocr`) fonctionne déjà.

**Ce qu'il faut vérifier :** que l'`<input>` accepte bien `capture="environment"` (caméra arrière par défaut) sur mobile, et que le bouton est assez grand pour être tapé avec le doigt.

**Valeur produit :** c'est le cas d'usage le plus différenciant sur mobile — impossible avec un chatbot généraliste.

### Cas 2 — Dictée vocale mobile

Un prof dicte le texte source à voix haute (extrait d'un livre qu'il a en main, ou résumé de son cours) pendant qu'il est debout.

**Flux actuel :** le bouton "Dicter" utilise l'API `SpeechRecognition` du navigateur. Sur mobile (Safari iOS, Chrome Android), cette API est disponible et utilise le micro du téléphone.

**Ce qu'il faut vérifier :** la compatibilité de l'API `SpeechRecognition` sur Safari iOS (elle y est disponible via `webkitSpeechRecognition`).

### Cas 3 — Consultation des activités sauvegardées

Un prof est en déplacement ou en salle des profs et veut retrouver une activité générée précédemment pour l'imprimer ou l'envoyer à un élève.

**Flux actuel :** "Mes activités" charge les activités depuis l'API (`/api/mes-activites`). Avec le mode offline, les activités récemment consultées seraient disponibles sans connexion.

### Cas 4 — Installation depuis l'accueil

Un prof visite school.afia.fr depuis son mobile. Le navigateur lui propose "Ajouter aSchool à l'écran d'accueil". Il accepte. L'app s'ouvre désormais comme une vraie app, sans barre d'adresse, avec l'icône aSchool sur son téléphone.

---

## 8. Plan d'implémentation — 4 étapes

### Étape 1 — Installabilité (1 journée)

**Objectif :** l'app peut être installée sur le téléphone depuis le navigateur.

**Tâches :**

1. Créer les icônes aSchool aux formats requis :
   - 192×192 px (PNG, fond bordeaux `#A63045` ou blanc avec logo)
   - 512×512 px (PNG — affiché dans le store et le splash screen)
   - `favicon.ico` (si pas déjà présent)
   - `apple-touch-icon.png` 180×180 px (iOS)

2. Installer `vite-plugin-pwa` :
   ```bash
   npm install -D vite-plugin-pwa
   ```

3. Configurer `vite.config.js` :
   ```js
   import { VitePWA } from 'vite-plugin-pwa'
   
   export default defineConfig({
     plugins: [
       react(),
       tailwindcss(),
       VitePWA({
         registerType: 'autoUpdate',
         manifest: {
           name: 'aSchool',
           short_name: 'aSchool',
           description: 'Générateur d\'activités pédagogiques',
           theme_color: '#1F6EEB',
           background_color: '#ffffff',
           display: 'standalone',
           start_url: '/',
           scope: '/',
           icons: [
             { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
             { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
           ],
         },
       }),
     ],
   })
   ```

4. Ajouter les méta tags dans `frontend/index.html` :
   ```html
   <meta name="theme-color" content="#1F6EEB">
   <meta name="apple-mobile-web-app-capable" content="yes">
   <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
   <meta name="apple-mobile-web-app-title" content="aSchool">
   <link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
   <link rel="manifest" href="/manifest.json">
   ```

5. Ajouter le `viewport` correct dans `index.html` (si pas déjà présent) :
   ```html
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   ```

**Résultat attendu :** sur Chrome Android et Safari iOS, le navigateur propose "Ajouter à l'écran d'accueil". L'app s'ouvre en mode standalone (sans barre d'adresse). Score Lighthouse PWA : ≥ 70/100.

**Validation :** tester avec Lighthouse dans Edge (F12 → Lighthouse → PWA).

---

### Étape 2 — Service Worker et cache (1 à 2 jours)

**Objectif :** l'interface de base se charge rapidement même hors connexion.

**Stratégie de cache par type de ressource :**

| Ressource | Stratégie | Justification |
|---|---|---|
| Assets statiques (JS, CSS, icônes) | `CacheFirst` | Changent uniquement au déploiement |
| API `/api/activites/{matiere}` | `NetworkFirst` (TTL 24h) | Peut changer, mais rarement |
| API `/api/auth/me` | `NetworkFirst` | Vérifier l'auth en ligne si possible |
| API `/api/generate` | `NetworkOnly` | Génération en temps réel, impossibe offline |
| API `/api/mes-activites` | `NetworkFirst` (TTL 1h) | Lisible offline, éditable online |
| Images OCR envoyées | `NetworkOnly` | Ne pas cacher |

**Configuration Workbox dans `vite.config.js` :**
```js
VitePWA({
  registerType: 'autoUpdate',
  workbox: {
    globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/school\.afia\.fr\/api\/activites\//,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'api-activites',
          expiration: { maxAgeSeconds: 86400 }, // 24h
        },
      },
      {
        urlPattern: /^https:\/\/school\.afia\.fr\/api\/mes-activites/,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'api-mes-activites',
          expiration: { maxAgeSeconds: 3600 }, // 1h
        },
      },
    ],
    navigateFallback: '/index.html',
  },
})
```

**Page offline :** créer `frontend/public/offline.html` — page simple affichée quand la navigation échoue et qu'il n'y a pas de cache. Message : "Vous semblez être hors connexion. Vos activités sauvegardées sont toujours accessibles."

**Résultat attendu :** après une première visite, l'interface charge instantanément. En cas de perte de connexion, l'app reste navigable (Mes activités, Aide, À propos). La génération d'activité affiche un message "Connexion internet requise" au lieu d'une erreur technique.

---

### Étape 3 — Interface responsive mobile (2 à 3 semaines)

**Objectif :** l'interface est utilisable sur un téléphone de 390px de large (iPhone 14, standard de référence).

**Ordre des modifications (du plus impactant au moins impactant) :**

#### 3.1 — Drawer mobile pour la Sidebar (priorité critique)

Ajouter un état `sidebarOpen` dans `App.jsx`, le passer à `Header` et `Sidebar`.

Modifier `Sidebar.jsx` :
- Sur mobile (< 768px) : position fixe overlay, caché par défaut, affiché quand `sidebarOpen = true`
- Sur desktop (≥ 768px) : comportement actuel (collapsed/expanded)
- Fermer automatiquement après chaque navigation (`onNavigate` appelle `setSidebarOpen(false)`)

Modifier `Header.jsx` :
- Bouton hamburger visible uniquement sur mobile (`md:hidden`)
- Logo aSchool toujours visible
- Slogan masqué sur mobile (`hidden md:inline`)
- Email masqué sur mobile (`hidden md:inline`)
- Bouton déco : icône seule sur mobile (`hidden md:inline` pour le texte)

Ajouter le backdrop dans `App.jsx` :
- Fond semi-transparent `rgba(0,0,0,0.4)` cliquable pour fermer le drawer

#### 3.2 — Layout principal (priorité critique)

Dans `App.jsx`, modifier :
```jsx
{/* Avant */}
<div className="flex flex-1 min-h-0">

{/* Après */}
<div className="flex flex-1 min-h-0 flex-col md:flex-row">
```

#### 3.3 — Paddings et espacements

Sur mobile, réduire les paddings :
```jsx
{/* Avant */}
<main className="flex-1 p-6 flex flex-col gap-4 overflow-auto">

{/* Après */}
<main className="flex-1 p-4 md:p-6 flex flex-col gap-3 md:gap-4 overflow-auto">
```

#### 3.4 — Composants secondaires (par ordre décroissant d'effort)

- `ZoneResultat.jsx` : boutons en colonne sur mobile, pleine largeur
- `TexteSource.jsx` : textarea hauteur flexible, boutons 44px minimum
- `Parametres.jsx` : bouton Générer pleine largeur sur mobile, vérifier l'empilement des sélecteurs
- `MesActivites.jsx` : cartes en colonne unique sur mobile
- `Feedback.jsx` / `Notation.jsx` : `max-height: 90vh; overflow-y: auto` sur le contenu
- `Login.jsx` / `Signup.jsx` / etc. : vérifier `padding: 16px` sur les côtés

#### 3.5 — Input OCR sur mobile

Dans `TexteSource.jsx`, modifier l'`<input type="file">` pour favoriser la caméra arrière sur mobile :
```jsx
<input
  type="file"
  accept=".txt,image/jpeg,image/png"
  capture="environment"  {/* caméra arrière par défaut sur mobile */}
/>
```

**Résultat attendu :** l'interface est utilisable sur iPhone 14 (390px) et sur Samsung Galaxy S21 (360px). Navigation par drawer, génération d'activité, OCR photo, dictée vocale — tous les flux principaux fonctionnent.

---

### Étape 4 — Optimisations et polish mobile (2 à 3 jours)

**Objectif :** expérience fluide, native-like.

#### 4.1 — Splash screen

iOS affiche un splash screen pendant le chargement de la PWA. Configurer via les méta tags dans `index.html` :
```html
<link rel="apple-touch-startup-image" href="/icons/splash-1125x2436.png" media="...">
```
Générer les images aux tailles requises par Apple (plusieurs résolutions selon le modèle d'iPhone).

Alternative plus simple : utiliser `background_color` dans le manifest — iOS affiche cette couleur pendant le chargement.

#### 4.2 — Touch et interactions

- Vérifier que tous les éléments interactifs font au moins 44×44px (recommandation Apple) — particulièrement les items de navigation de la Sidebar
- Ajouter `touch-action: manipulation` sur les boutons pour éviter le délai 300ms de double-tap sur iOS
- Vérifier qu'il n'y a pas de `hover:` qui se déclenche au tap sur mobile (peut créer un état visuel figé)

#### 4.3 — Gestion du clavier virtuel

Sur mobile, quand le clavier virtuel s'ouvre sur la textarea :
- Le `viewport` se rétrécit — vérifier que le bouton "Générer" reste accessible
- Utiliser `position: sticky` plutôt que `position: fixed` pour les éléments qui doivent rester visibles
- Sur iOS, `100vh` inclut le clavier — utiliser `min-height: 100svh` (small viewport height) à la place de `min-h-screen`

#### 4.4 — Prompt d'installation personnalisé

Par défaut, Chrome Android affiche son propre prompt "Ajouter à l'écran d'accueil". On peut intercepter l'événement `beforeinstallprompt` pour afficher son propre bouton d'installation au moment le plus approprié (ex : après la première génération réussie).

```jsx
// Dans App.jsx
useEffect(() => {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    setDeferredInstallPrompt(e) // stocker pour plus tard
  })
}, [])

// Afficher le bouton d'installation après la 1ère génération réussie
// setDeferredInstallPrompt.prompt() pour déclencher l'installation
```

#### 4.5 — Gestion de la mise à jour de l'app

Quand une nouvelle version est déployée, le Service Worker se met à jour en arrière-plan. Il faut notifier l'utilisateur et lui proposer de recharger :

```jsx
// Dans App.jsx ou un composant dédié
import { useRegisterSW } from 'virtual:pwa-register/react'

function UpdatePrompt() {
  const { needRefresh, updateServiceWorker } = useRegisterSW()
  if (!needRefresh[0]) return null
  return (
    <div className="fixed bottom-4 left-4 right-4 bg-blue-600 text-white p-3 rounded-lg flex items-center justify-between">
      <span>Une nouvelle version est disponible</span>
      <button onClick={() => updateServiceWorker(true)}>Mettre à jour</button>
    </div>
  )
}
```

---

## 9. Stratégie offline et gestion du cache

### Ce qui fonctionne offline après la PWA

| Fonctionnalité | Offline ? | Justification |
|---|---|---|
| Navigation dans l'interface | ✅ Oui | Assets statiques en cache |
| Voir "Mes activités" (cache 1h) | ✅ Oui | Mis en cache au dernier chargement |
| Consulter une activité sauvegardée | ✅ Oui | Contenu en cache |
| Voir l'Aide | ✅ Oui | Contenu statique |
| Voir À propos | ✅ Oui | Contenu statique |
| Générer une activité | ❌ Non | Requiert Groq (API externe) |
| Dicter / OCR | ❌ Non | Requiert backend + Groq |
| Se connecter / S'inscrire | ❌ Non | Requiert le backend |

### Message offline à afficher

Quand l'utilisateur tente de générer une activité sans connexion, afficher un message clair :

> "Connexion internet requise pour générer une activité. Vos activités sauvegardées restent accessibles depuis 'Mes activités'."

---

## 10. Contraintes et points d'attention

### iOS — Safari (contraintes spécifiques Apple)

| Contrainte | Détail |
|---|---|
| `webkitSpeechRecognition` | La dictée vocale nécessite `window.webkitSpeechRecognition` sur Safari iOS — à vérifier avec un fallback si indisponible |
| Cookies httpOnly | Fonctionnent correctement sur Safari iOS (même domaine, SameSite=Lax) |
| Service Worker | Supporté depuis iOS 11.3 — aucune restriction actuelle |
| Web Push | Supporté depuis iOS 16.4 — mais uniquement si l'app est installée (PWA à l'écran d'accueil) |
| `100vh` | Sur Safari iOS avec la barre du bas, `100vh` inclut les barres UI — utiliser `100svh` ou `100dvh` |
| `position: fixed` | Peut se comporter bizarrement avec le clavier virtuel — tester |

### Android — Chrome

| Contrainte | Détail |
|---|---|
| Prompt installation | Chrome propose automatiquement "Ajouter à l'écran d'accueil" si les critères PWA sont remplis |
| `SpeechRecognition` | Disponible nativement, sans préfixe `webkit` |
| Service Worker | Support complet depuis Chrome 40 |

### Serveur — Nginx (VPS school.afia.fr)

Le Service Worker doit être servi avec les bons en-têtes HTTP. Vérifier que Nginx renvoie :
```nginx
# Pour le service worker — ne pas mettre en cache le SW lui-même
location /sw.js {
    add_header Cache-Control "no-cache";
    add_header Service-Worker-Allowed "/";
}

# Pour le manifest
location /manifest.json {
    add_header Cache-Control "no-cache";
}
```

Sans ces en-têtes, le navigateur peut cacher une version obsolète du Service Worker et empêcher les mises à jour.

### Taille du build

Avec le Service Worker qui précache tous les assets, le premier chargement télécharge légèrement plus de données. Vérifier que le bundle JS reste raisonnable (< 500 Ko gzippé).

---

## 11. Checklist de validation finale

### Critères d'installation (Lighthouse)

- [ ] `manifest.json` présent et valide
- [ ] Icône 192×192 px présente
- [ ] Icône 512×512 px présente (purpose: any maskable)
- [ ] `theme_color` défini
- [ ] `display: standalone`
- [ ] `start_url` défini
- [ ] HTTPS actif (✅ déjà en place)
- [ ] Service Worker enregistré
- [ ] Service Worker intercepte les requêtes réseau
- [ ] `<meta name="viewport">` présent

### Tests fonctionnels sur mobile

- [ ] L'app s'installe depuis Chrome Android
- [ ] L'app s'installe depuis Safari iOS
- [ ] Le drawer sidebar s'ouvre et se ferme correctement
- [ ] La navigation dans le drawer ferme le drawer
- [ ] Le clavier virtuel n'empêche pas d'accéder au bouton Générer
- [ ] L'input fichier propose la caméra sur mobile
- [ ] La dictée vocale fonctionne sur Android (Chrome)
- [ ] La dictée vocale fonctionne sur iOS (Safari)
- [ ] "Mes activités" est accessible offline (après une connexion préalable)
- [ ] La page offline s'affiche quand on essaie de générer sans connexion
- [ ] Le prompt de mise à jour s'affiche quand une nouvelle version est déployée
- [ ] Les modales (Feedback, Notation) sont utilisables sur mobile
- [ ] Les pages auth (Login, Signup) sont lisibles sur 390px
- [ ] Le score Lighthouse PWA est ≥ 90/100

### Tests de régression desktop

- [ ] La sidebar desktop fonctionne toujours (collapsed/expanded)
- [ ] Le Header desktop affiche toutes les infos
- [ ] Le layout desktop est intact (sidebar à gauche, contenu à droite)
- [ ] Les pages admin fonctionnent (non modifiées)

---

## 12. Effort estimé et récapitulatif

| Étape | Tâches principales | Effort estimé |
|---|---|---|
| **Étape 1** — Installabilité | Icônes + manifest + vite-plugin-pwa + méta tags | 1 journée |
| **Étape 2** — Service Worker | Configuration Workbox + stratégies de cache + page offline | 1 à 2 jours |
| **Étape 3** — Responsive mobile | Drawer sidebar + Header mobile + layout + composants | 2 à 3 semaines |
| **Étape 4** — Polish mobile | Splash screen + touch + clavier + prompt installation + mise à jour SW | 2 à 3 jours |
| **Total** | | **3 à 4 semaines** |

### Décomposition de l'Étape 3 (le plus gros morceau)

| Composant | Effort |
|---|---|
| `App.jsx` — layout flex-col/flex-row + état sidebarOpen + backdrop | 0,5 jour |
| `Sidebar.jsx` — drawer mobile overlay | 1 jour |
| `Header.jsx` — hamburger + masquage slogan/email sur mobile | 0,5 jour |
| `TexteSource.jsx` — boutons 44px + capture=environment | 0,5 jour |
| `Parametres.jsx` — bouton Générer pleine largeur | 0,5 jour |
| `ZoneResultat.jsx` — boutons en colonne mobile | 0,5 jour |
| `MesActivites.jsx` — cartes colonne unique | 0,5 jour |
| Modales (Feedback, Notation, tipModal) | 0,5 jour |
| Pages auth — vérification responsive | 0,5 jour |
| Tests cross-device (iPhone + Android) | 2 à 3 jours |
| **Total Étape 3** | **7 à 8 jours ouvrés** |

### Conseil de timing

Ne pas démarrer l'Étape 3 avant d'avoir des retours des pilotes. Les profs utilisent l'outil principalement sur ordinateur de bureau (salle des profs, domicile). L'Étape 1 + Étape 2 peuvent être faites en 3 jours et rendent l'app "installable" — un premier niveau de PWA sans toucher à l'interface.

L'Étape 3 (responsive) est le vrai investissement. Elle a du sens une fois que l'usage desktop est validé et que les pilotes commencent à demander un accès mobile.

---

*aSchool — Spécification PWA — Rédigé le 03/05/2026*
*À annoter et valider avant de commencer le développement*
