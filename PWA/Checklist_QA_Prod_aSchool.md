# Checklist QA Production PWA aSchool

## Objectif
Valider les points critiques avant mise en ligne afin d'éviter la majorité des incidents réels.
Passer sur **mobile physique** (pas émulateur DevTools) — iPhone ou Android réel.

---

## Comment utiliser cette checklist — scénario réel

**Durée : 25-35 minutes. 1 seul testeur. iPhone dans la main.**

1. Ouvrir ce fichier sur un écran, téléphone dans l'autre main.
2. Suivre les 10 points prioritaires dans l'ordre — ils couvrent 80% des risques réels.
3. Compléter les 21 points si le temps le permet.
4. Remplir la colonne "Testé le / Par" sur chaque ligne cochée.

**Ce que cette checklist attrape que les tests unitaires ne voient pas :**
le 404 sur refresh de sous-page, le Back button après logout, la bannière iOS absente, le second onglet resté connecté.

**Règle : un point rouge bloquant = pas de déploiement.**
Un point cosmétique (icône légèrement floue, couleur splash) = non bloquant, noter et continuer.

---

## Checklist (21 points — 35 sous-tests)

| # | Point | Statut | Testé le | Par |
|---|-------|--------|----------|-----|
| 1 | Connexion navigateur normal | ✅ OK | 12/05 | harkett |
| 2 | Connexion app installée (PWA) | 🔒 prod | aschool.fr | — |
| 3.1 | Déconnexion — Pas reconnecté après relance | ✅ OK | 12/05 | harkett |
| 3.2 | Déconnexion — Bouton Back après logout | ✅ OK | 12/05 | harkett |
| 3.3 | Déconnexion — Cross-tab (deux onglets) | ✅ OK | 12/05 | harkett |
| 4 | Installation Android | 🔒 prod | aschool.fr | — |
| 5.1 | iPhone — Bannière apparaît après 5s | 🔒 prod | aschool.fr | — |
| 5.2 | iPhone — Bouton ✕ ferme définitivement | 🔒 prod | aschool.fr | — |
| 5.3 | iPhone — Install Safari → écran d'accueil | 🔒 prod | aschool.fr | — |
| 6 | Icône propre | 🔒 prod | aschool.fr | — |
| 7 | Splash / thème couleur | 🔒 prod | aschool.fr | — |
| 8 | Refresh sur sous-page | ✅ OK | 12/05 | harkett |
| 9 | API après installation | ✅ OK | 12/05 | harkett |
| 10.1 | Hors ligne — Shell visible sans crash | ✅ OK | 12/05 | harkett |
| 10.2 | Hors ligne — OfflineBanner apparaît | ✅ OK | 12/05 | harkett |
| 10.3 | Hors ligne — Message d'erreur propre sur génération | ✅ OK | 12/05 | harkett |
| 11 | Réseau lent + message timeout | 🔒 prod | aschool.fr | — |
| 12.1 | Update — Déployer nouvelle build | ✅ OK | 12/05 | harkett |
| 12.2 | Update — Bannière "Nouvelle version" apparaît | ✅ OK | 12/05 | harkett |
| 12.3 | Update — Bouton Actualiser recharge sur nouvelle version | ✅ OK | 12/05 | harkett |
| 12.4 | Update — Aucune session bloquée sur ancienne version | ✅ OK | 12/05 | harkett |
| 13 | Responsive mobile réel | 🔒 prod | aschool.fr | — |
| 14 | Clavier mobile | 🔒 prod | aschool.fr | — |
| 15 | HTTPS strict | 🔒 prod | aschool.fr | — |
| 16.1 | Cross-tab — Deux onglets ouverts et connectés | ✅ OK | 12/05 | harkett |
| 16.2 | Cross-tab — Déconnexion onglet A | ✅ OK | 12/05 | harkett |
| 16.3 | Cross-tab — Onglet B redirige automatiquement | ✅ OK | 12/05 | harkett |
| 17 | Taille bundle | ✅ OK | 12/05 | claude |
| 18 | Cache clean logout | ✅ OK | 12/05 | claude |
| 19 | Comptes réels / rôles | ✅ OK | 12/05 | claude |
| 20.1 | Console — Aucune erreur rouge navigateur | ✅ OK | 12/05 | harkett |
| 20.2 | Logs Nginx — Aucun 5xx | 🔒 prod | aschool.fr | — |
| 21.1 | DevTools — SW "activated and running" | 🔒 prod | aschool.fr | — |
| 21.2 | DevTools — Manifest sans erreur, icônes résolues | 🔒 prod | aschool.fr | — |
| 21.3 | DevTools — /api/ absent du Cache Storage | 🔒 prod | aschool.fr | — |

---

## Guide de test

---

### 1 — Connexion navigateur normal

**Pourquoi faire ce test**
Valide les cookies httpOnly, l'auth backend et la persistance de session JWT.

**Comment faire ce test**
→ Ouvrir `localhost:5173` → se connecter → rafraîchir la page
Attendu : session toujours active après F5, pas de redirection vers /login

---

### 2 — Connexion app installée (PWA) 🔒 prod

**Pourquoi faire ce test**
Le mode standalone peut gérer différemment les cookies httpOnly selon le navigateur — une app installée n'est pas un onglet ordinaire.

**Comment faire ce test**
→ Ouvrir l'app depuis l'icône écran d'accueil → se connecter
Attendu : login fonctionnel en mode standalone, cookies transmis correctement

---

### 3.1 — Déconnexion — Pas reconnecté après relance

**Pourquoi faire ce test**
Vérifie qu'aucune session fantôme ne persiste après fermeture de l'onglet.

**Comment faire ce test**
→ Logout → fermer l'onglet → rouvrir `localhost:5173`
Attendu : /login s'affiche, pas le dashboard
Échec : l'app s'ouvre directement sur le dashboard sans redemander de mot de passe

### 3.2 — Déconnexion — Bouton Back après logout

**Pourquoi faire ce test**
Le bfcache (back-forward cache) du navigateur peut restaurer un snapshot figé de la page sans réinitialiser React, rendant les données utilisateur visibles même après logout.

**Comment faire ce test**
→ Logout → arriver sur /login → appuyer Back → puis Forward
Attendu : checkAuth() se relance → cookies absents → redirection vers /login, aucune donnée visible
Échec : le dashboard s'affiche avec les données du compte sans redirection
Note : atterrir sur une page extérieure à aSchool via Back (ex. onglet par défaut Edge) = comportement normal du navigateur, pas un bug

### 3.3 — Déconnexion — Cross-tab (deux onglets)

**Pourquoi faire ce test**
Sans listener storage, les onglets orphelins restent connectés indéfiniment après logout — un prof peut laisser un onglet oublié accessible.

**Comment faire ce test**
→ Ouvrir 2 onglets sur aSchool → se connecter dans les deux → logout dans l'onglet A → observer l'onglet B sans rien faire
Attendu : l'onglet B bascule automatiquement sur /login en moins de 2 secondes
Échec : l'onglet B reste sur le dashboard et permet de continuer à naviguer

---

### 4 — Installation Android 🔒 prod

**Pourquoi faire ce test**
Valide que le manifeste, le service worker, HTTPS et les icônes 192/512 sont correctement configurés pour déclencher l'installation native.

**Comment faire ce test**
→ Ouvrir aschool.fr sur Chrome Android → attendre la bannière d'installation native → installer → lancer depuis l'écran d'accueil
Attendu : app lancée en mode standalone, icône visible sur l'écran d'accueil

---

### 5.1 — iPhone — Bannière apparaît après 5s 🔒 prod

**Pourquoi faire ce test**
iOS n'a pas de popup install automatique — la bannière IOSInstallBanner est le seul vecteur d'installation sur iPhone.

**Comment faire ce test**
→ Ouvrir aschool.fr sur Safari iPhone → se connecter → attendre 5 secondes sur le dashboard
Attendu : bannière bordeaux "Installer aSchool sur iPhone" apparaît en haut de page

### 5.2 — iPhone — Bouton ✕ ferme définitivement 🔒 prod

**Pourquoi faire ce test**
Vérifie que localStorage mémorise le refus et ne ré-affiche pas la bannière à chaque visite.

**Comment faire ce test**
→ Cliquer ✕ sur la bannière → recharger la page → naviguer dans l'app
Attendu : la bannière ne réapparaît plus, même après reload ou navigation

### 5.3 — iPhone — Install Safari → écran d'accueil 🔒 prod

**Pourquoi faire ce test**
Valide le flux complet d'installation iOS via le menu Partager de Safari.

**Comment faire ce test**
→ Safari > icône Partager > "Sur l'écran d'accueil" → confirmer
Attendu : icône aSchool sur l'écran d'accueil, app lancée en plein écran sans barre Safari

---

### 6 — Icône propre 🔒 prod

**Pourquoi faire ce test**
Une icône floue ou coupée nuit à la crédibilité de l'app sur l'écran d'accueil — valide icon-192.png et icon-512.png.

**Comment faire ce test**
→ Vérifier l'icône sur l'écran d'accueil Android et iOS après installation
Attendu : image nette, pas de flou, pas de bords coupés

---

### 7 — Splash / thème couleur 🔒 prod

**Pourquoi faire ce test**
Valide theme_color (bordeaux), background_color (blanc) et la meta apple-mobile-web-app-capable — un mauvais splash casse l'impression "app native".

**Comment faire ce test**
→ Fermer l'app installée → la rouvrir depuis l'icône écran d'accueil
Attendu : fond blanc au démarrage, barre de statut bordeaux, pas d'écran blanc cassé

---

### 8 — Refresh sur sous-page

**Pourquoi faire ce test**
React Router gère les routes côté client — si le serveur ne renvoie pas index.html sur toutes les routes, un F5 produit une erreur 404.

**Comment faire ce test**
→ Naviguer vers `/mes-activites` ou `/profil` → appuyer F5 (ou pull-to-refresh mobile)
Attendu : la page se recharge correctement, pas de 404
Échec : erreur 404 ou écran blanc

---

### 9 — API après installation

**Pourquoi faire ce test**
Vérifie que le service worker ne met pas en cache /api/ — les données doivent toujours venir du serveur, jamais d'un cache périmé.

**Comment faire ce test**
→ Créer une activité → la sauvegarder → la retrouver dans Mes activités
Attendu : les appels /api/ passent, données enregistrées et récupérées correctement

---

### 10.1 — Hors ligne — Shell visible sans crash

**Pourquoi faire ce test**
Les profs utilisent l'app en salle sans wifi — l'interface doit rester lisible même sans connexion, pas d'écran blanc.

**Comment faire ce test**
→ DevTools > Network > Offline → recharger l'app
Attendu : l'interface s'affiche (shell), pas d'écran blanc ni d'erreur JavaScript

### 10.2 — Hors ligne — OfflineBanner apparaît

**Pourquoi faire ce test**
Sans message clair, l'utilisateur pense que l'app est cassée — la bannière bordeaux signale explicitement la perte de connexion.

**Comment faire ce test**
→ Même contexte que 10.1, observer le haut de page
Attendu : bannière bordeaux "Hors connexion" visible en haut de page

### 10.3 — Hors ligne — Message d'erreur propre sur génération

**Pourquoi faire ce test**
Une tentative de génération hors ligne doit produire un message lisible, pas un spinner infini ou un crash silencieux.

**Comment faire ce test**
→ Toujours en mode Offline → tenter de générer une activité
Attendu : message d'erreur lisible affiché, pas de spinner infini

---

### 11 — Réseau lent + message timeout

**Pourquoi faire ce test**
fetchWithTimeout est actif sur toutes les requêtes — vérifie que le message "Connexion lente" remonte bien dans l'UI au lieu de laisser l'utilisateur face à un spinner sans fin.

**Comment faire ce test**
→ DevTools > Network > Slow 3G → déclencher une génération → attendre
Attendu : le message "Connexion lente ou indisponible. Vérifiez votre réseau et réessayez." apparaît après le timeout

---

### 12.1 — Update — Déployer nouvelle build 🔒 prod

**Pourquoi faire ce test**
skipWaiting + clientsClaim sont actifs — le nouveau SW doit prendre la main immédiatement sans laisser de sessions bloquées sur l'ancienne version.

**Comment faire ce test**
→ Déployer une nouvelle version sur aschool.fr (bump de version suffisant)

### 12.2 — Update — Bannière "Nouvelle version" apparaît 🔒 prod

**Pourquoi faire ce test**
Vérifie que le composant UpdateBanner détecte bien le nouveau service worker disponible.

**Comment faire ce test**
→ Ouvrir l'app depuis une session existante sans recharger
Attendu : bannière "Nouvelle version disponible" apparaît en haut de page

### 12.3 — Update — Bouton Actualiser fonctionne 🔒 prod

**Pourquoi faire ce test**
Vérifie que updateServiceWorker(true) déclenche bien le rechargement et bascule sur la nouvelle version.

**Comment faire ce test**
→ Cliquer "Actualiser" sur la bannière UpdateBanner
Attendu : page rechargée sur la nouvelle version

### 12.4 — Update — Aucune session bloquée 🔒 prod

**Pourquoi faire ce test**
clientsClaim garantit que tous les onglets ouverts basculent sur le nouveau SW — pas seulement celui qui a cliqué Actualiser.

**Comment faire ce test**
→ Avoir 2 onglets ouverts lors du déploiement → vérifier que les deux passent sur la nouvelle version
Attendu : aucune session reste bloquée sur l'ancienne version

---

### 13 — Responsive mobile réel

**Pourquoi faire ce test**
Les vrais profs utilisent leur téléphone entre deux cours — l'émulateur DevTools ne reproduit pas les vrais comportements tactiles ni les vrais bugs d'affichage.

**Comment faire ce test**
→ Tester sur iPhone ou Android réel : login, dashboard, formulaire génération, Mes activités
Attendu : mise en page correcte à 390px, textes lisibles, boutons accessibles au pouce

---

### 14 — Clavier mobile

**Pourquoi faire ce test**
Le clavier mobile réduit la hauteur visible de l'écran — les boutons positionnés en bas à droite peuvent disparaître sous le clavier.

**Comment faire ce test**
→ Taper du texte dans les champs principaux sur iPhone ou Android → observer le bouton "Générer"
Attendu : le bouton reste visible quand le clavier est ouvert
Échec : le bouton disparaît sous le clavier

---

### 15 — HTTPS strict 🔒 prod

**Pourquoi faire ce test**
HTTPS est obligatoire pour PWA, cookies Secure et SameSite — sans lui, l'installation et l'auth ne fonctionnent pas.

**Comment faire ce test**
→ Ouvrir aschool.fr → vérifier le cadenas dans la barre d'adresse → F12 > Console
Attendu : cadenas vert, aucune alerte "mixed content" dans la console

---

### 16.1 — Cross-tab — Deux onglets ouverts et connectés

**Pourquoi faire ce test**
Reproduit le cas réel d'un prof qui laisse un onglet aSchool ouvert dans un autre espace de travail — il doit se déconnecter partout en même temps.

**Comment faire ce test**
→ Ouvrir 2 onglets Edge sur `localhost:5173` → se connecter avec le même compte dans les deux
Attendu : les deux onglets affichent le dashboard

### 16.2 — Cross-tab — Déconnexion onglet A

**Pourquoi faire ce test**
Vérifie que le signal localStorage est bien émis au moment du logout et déclenche la chaîne cross-tab.

**Comment faire ce test**
→ Dans l'onglet A → cliquer Déconnexion
Attendu : onglet A redirige vers /login

### 16.3 — Cross-tab — Onglet B redirige automatiquement

**Pourquoi faire ce test**
Vérifie que le listener storage de l'onglet B capte le signal et force la redirection sans aucune action manuelle.

**Comment faire ce test**
→ Observer l'onglet B sans rien faire après le logout de l'onglet A
Attendu : l'onglet B bascule automatiquement sur /login en moins de 2 secondes
Échec : l'onglet B reste connecté et navigable

---

### 17 — Taille bundle

**Pourquoi faire ce test**
Un bundle trop lourd pénalise le chargement initial sur 4G — les profs en déplacement doivent attendre moins de 3 secondes.

**Comment faire ce test**
→ DevTools > Lighthouse > lancer un audit PWA + Performance
Attendu : score PWA ≥ 90, bundle JS < 500 Ko gzippé (vérifier dans Network > JS)

---

### 18 — Cache clean logout

**Pourquoi faire ce test**
Vérifie que localStorage et sessionStorage sont bien vidés au logout — aucune donnée privée ne doit survivre à la déconnexion.

**Comment faire ce test**
→ Logout → DevTools > Network > Offline → rouvrir `localhost:5173`
Attendu : aucune donnée utilisateur visible, aucune page protégée accessible

---

### 19 — Comptes réels / rôles

**Pourquoi faire ce test**
Les permissions sont spécifiques par rôle — un bug peut exposer le backoffice admin à un enseignant ou bloquer un enseignant légitime.

**Comment faire ce test**
→ Tester avec un compte enseignant → vérifier accès dashboard et génération uniquement
→ Tester avec un compte admin → vérifier accès backoffice, pas d'accès enseignant
Attendu : chaque rôle voit uniquement ce qu'il doit voir, sans fuite entre rôles

---

### 20.1 — Console — Aucune erreur rouge navigateur

**Pourquoi faire ce test**
Détecte les erreurs silencieuses côté client — une erreur JavaScript ignorée en dev devient un bug bloquant en prod.

**Comment faire ce test**
→ F12 > Console → effectuer dans l'ordre : login, génération, save, logout
Attendu : aucune erreur rouge dans la console à aucune étape

### 20.2 — Logs Nginx — Aucun 5xx 🔒 prod

**Pourquoi faire ce test**
Détecte les crashs backend non affichés à l'utilisateur — un 502 silencieux passe inaperçu côté UI mais indique un problème serveur réel.

**Comment faire ce test**
→ Sur le VPS : `sudo tail -f /var/log/nginx/access.log` pendant les tests
Attendu : aucun code 500, 502, 503 après chaque action

---

### 21.1 — DevTools — SW "activated and running" 🔒 prod

**Pourquoi faire ce test**
Un SW en "waiting" signifie qu'une ancienne version bloque la mise à jour — l'app tourne sur du code obsolète sans que l'utilisateur le sache.

**Comment faire ce test**
→ F12 > Application > Service Workers
Attendu : statut "activated and running", aucun SW en "waiting"

### 21.2 — DevTools — Manifest sans erreur 🔒 prod

**Pourquoi faire ce test**
Une erreur manifest empêche l'installation et le splash screen — cause fréquente : icône manquante ou start_url incorrecte.

**Comment faire ce test**
→ F12 > Application > Manifest
Attendu : aucune erreur affichée, icônes résolues, start_url = `/`

### 21.3 — DevTools — /api/ absent du Cache Storage 🔒 prod

**Pourquoi faire ce test**
Si /api/ apparaît dans le cache, le SW retourne des réponses périmées — les données affichées ne viennent plus du serveur.

**Comment faire ce test**
→ F12 > Application > Cache Storage → parcourir tous les caches listés
Attendu : `/api/` n'apparaît dans aucun cache

---

## Priorité si seulement 10 minutes

1. Login app installée
2. Déconnexion — les 3 sous-tests
3. Refresh sous-page
4. Install Android
5. Install iPhone + bannière
6. API create/save
7. Offline + OfflineBanner
8. Update build + UpdateBanner
9. Multi-onglets cross-tab logout
10. DevTools Application (SW + manifest)

---

## Verdict

Si tous les points passent, le lancement est fortement sécurisé.
Un point rouge = bloquant si lié à auth, données, ou install. Cosmétique = non bloquant.
