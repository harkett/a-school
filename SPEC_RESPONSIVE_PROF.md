# SPEC — Refonte responsive du côté prof (aSchool)

> **Statut : v1 validée par l'utilisateur le 23/07/2026.**
> Ce document est la référence du chantier. On le suit étape par étape ; on ne
> détaille un lot qu'au moment de l'attaquer. Toute modification de cette spec
> passe par l'arbitrage de l'utilisateur.

## 1. But

Rendre tout le côté prof d'aSchool réellement responsive : l'affichage s'adapte
en continu à la taille de l'écran (téléphone, tablette, ordinateur, rotation
comprise), par le standard CSS mobile-first — plus aucune détection de largeur
en JavaScript. Le côté admin n'est PAS concerné.

**Périmètre : côté prof uniquement. L'admin (`Admin*.jsx`) fera l'objet d'un
chantier responsive séparé, plus tard, selon la même méthode (Tailwind
mobile-first) — il n'est pas touché ici.**

## 2. État des lieux (vérifié en dur le 23/07/2026)

| Fait | Preuve |
|---|---|
| React 19.2.5 + Vite 8.0.10 | `frontend/package.json` |
| Tailwind CSS ^4.2.4 + plugin `@tailwindcss/vite` déjà installés et committés | `frontend/package.json` lignes 21 et 29 ; plugin déclaré dans `frontend/vite.config.js` (version committée) ; `@import "tailwindcss"` en ligne 1 de `frontend/src/index.css` |
| Compatibilité officielle plugin ↔ Vite 8 | package `@tailwindcss/vite` v4.3.3 : `"vite": "^5.2.0 \|\| ^6 \|\| ^7 \|\| ^8"` (dépôt officiel tailwindlabs/tailwindcss) |
| Tailwind déjà utilisé pour des styles fixes dans 18 fichiers côté prof | comptage `className=` avec utilitaires |
| 0 préfixe responsive (`sm:`/`md:`/`lg:`) dans tout le code | comptage grep = 0 |
| 1 818 blocs `style={{…}}` inline dans `frontend/src` (dont ~976 côté prof) | comptage grep |
| 10 fichiers utilisent `window.innerWidth` pour la mise en page | comptage grep |
| Balise viewport présente | `frontend/index.html` ligne 7 |

Conclusion : le socle technique existe déjà. Le chantier est la CONVERSION des
écrans, pas l'installation d'un outil.

## 3. Standard technique (la règle du chantier)

- **Mobile-first** (doctrine officielle Tailwind, tailwindcss.com/docs/responsive-design) :
  les classes SANS préfixe s'appliquent dès 0 px — le téléphone est le défaut ;
  les préfixes élargissent vers les grands écrans.
- **3 paliers retenus**, sur les points de rupture officiels de Tailwind :
  | Palier | Préfixe | Largeur |
  |---|---|---|
  | Téléphone (défaut) | aucun | < 768 px |
  | Tablette | `md:` | ≥ 768 px |
  | Ordinateur | `lg:` | ≥ 1024 px |
  (`sm:` 640 px et `xl:` 1280 px autorisés ponctuellement si un écran le justifie.)
- **Interdits** dans tout écran converti :
  - `window.innerWidth` / `matchMedia` pour la mise en page ;
  - styles inline `style={{…}}` pour tout ce qui touche à la disposition,
    aux dimensions ou aux espacements ;
  - largeurs fixes en px sur les conteneurs (utiliser les classes `max-w-*`,
    les grilles et le flux).
- **Toléré** : style inline pour une valeur réellement dynamique issue des
  données (ex. une couleur calculée en base).

## 4. Définition de « écran terminé » (porte de sortie de chaque écran)

1. Zéro `style={{…}}` de mise en page et zéro `window.innerWidth` dans le fichier.
2. Vérifié sur 3 largeurs : **375 px** (téléphone), **768 px** (tablette),
   **1280 px** (ordinateur) — et rotation portrait/paysage.
3. Aucun défilement horizontal parasite à aucune taille.
4. Sur grand écran, l'aspect reste fidèle à l'existant : on rend responsive,
   on ne redessine pas.
5. Testé par le dev, PUIS testé par l'utilisateur, avant de passer à l'écran
   suivant.

## 5. Ordre de conversion (par lots — un commit proposé par lot)

| Lot | Contenu | Fichiers (frontend/src) |
|---|---|---|
| 0 — La charpente | structure générale dans laquelle tout vit | `App.jsx`, `components/Header.jsx`, `components/Sidebar.jsx`, `components/Footer.jsx` |
| 1 — Le cœur d'usage | flux de génération d'activité | `components/Accueil.jsx`, `components/Consigne.jsx`, `components/TexteSource.jsx`, `components/ZoneResultat.jsx` |
| 2 — Mes contenus | | `components/MesActivites.jsx`, `components/MesSequences.jsx`, `components/SequenceForm.jsx`, `components/MesStats.jsx` |
| 3 — Réseau et profil | | `components/MonReseau.jsx`, `components/MonReseauSequences.jsx`, `components/MonProfil.jsx`, `components/Parametres.jsx`, `components/Feedback.jsx`, `pages/MesFeedbacks.jsx` |
| 4 — Écrans d'entrée | **habillage uniquement — zéro modification de la logique de connexion (règle 15) ; lot ouvert sur ordre explicite de l'utilisateur** | `pages/Login.jsx`, `pages/Signup.jsx`, `pages/ForgotPassword.jsx`, `pages/ResetPassword.jsx`, `pages/VerifyEmail.jsx` |
| 5 — Annexes | | `components/Aide.jsx`, `components/Ambiguites.jsx`, `components/Optimiseur.jsx`, `components/Notation.jsx`, `components/APropos.jsx`, `pages/MentionsLegales.jsx`, bannières (`IOSInstallBanner`, `OfflineBanner`, `UpdateBanner`) |

## 6. Organisation (identique au chantier déploiement)

- Les **devs exécutent**, lot par lot.
- Le **contrôleur vérifie chaque lot** : comptages (zéro style inline de mise en
  page restant, zéro `window.innerWidth`, préfixes responsive présents) +
  relecture du diff complet.
- L'**utilisateur teste et arbitre** ; le commit du lot part sur son ok.
- On ne commence pas un lot tant que le précédent n'est pas clos.
- L'admin n'est pas touché. Le chantier s'ouvre APRÈS la fin du déploiement en
  cours.

## 7. Charge estimée (mesurée, pas devinée)

~30 écrans et composants, ~9 400 lignes, ~976 blocs de style à convertir côté
prof. 4 gros morceaux : `Aide.jsx` (1 341 lignes), `App.jsx` (1 114),
`MesActivites.jsx` (558), `TexteSource.jsx` (546). Pas de difficulté technique
(conversion mécanique d'un motif connu, socle en place) ; c'est un chantier de
volume, en plusieurs sessions, écran par écran, site utilisable en permanence.
