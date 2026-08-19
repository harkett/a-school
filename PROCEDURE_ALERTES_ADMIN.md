# Procédure — Nouveautés et centre d'actions de l'administration

**Écrite le 16/08/2026 par la session « interface prof », à destination de la session admin.**
Elle n'est pas un cahier des charges de plus : elle décrit un mécanisme dont **la moitié existe
déjà** en base et côté serveur. Ce qui manque est nommé au point 4.

---

## 1. Le principe, en une phrase

Le **développement** livre une fonctionnalité et le dit dans le code ; **l'administration ne
saisit rien** — elle constate, et prend la seule décision qui lui revient : *faut-il l'annoncer
aux professeurs, et laquelle mettre en avant ?*

C'est le fonctionnement des grandes plateformes : la note de version est publiée par la
livraison elle-même, et ce qui reste à décider par un humain arrive dans un **centre d'actions**
(Microsoft 365 Message Center / Action Center, Google Workspace) — une file d'éléments à
traiter, signalée par une pastille, qui s'éteint une fois le geste fait.

---

## 2. Ce qui existe déjà (à ne pas refaire)

| Élément | Où | État |
|---|---|---|
| Catalogue des fonctionnalités | table `features_votables` (code, label, description, categorie, icone, ordre, actif, livree, nouveaute, page) | en place |
| Écran prof « Bientôt disponible » | `frontend/src/components/BientotDisponible.jsx` — lit `/api/feature-votes` | en place |
| Écran admin « Bientôt disponible » | `frontend/src/pages/AdminBientotDisponible.jsx` — lecture seule + deux cases | en place |
| Cases **Livrée** / **Nouveauté** | `PATCH /api/admin/feature-votes/{code}` (`backend/communication/votes.py`) | en place |
| Règles tenues côté serveur | « nouveauté » impossible sans « livrée » ; **une seule nouveauté à la fois** (cocher éteint la précédente) | en place |
| Bandeau nouveauté du prof | `GET /api/nouveautes` | en place |
| Alertes admin | `create_alert(level, title, message, …)` dans `backend/supervision/alerts.py` | existe, **jamais appelé** pour les fonctionnalités |
| Carnet « Tâches à faire » | `frontend/src/pages/AdminTachesAFaire.jsx` | saisi **à la main**, rien ne s'y ajoute seul |

**Point important :** aucun écran ne permet de modifier le *texte* d'une carte (libellé,
description, catégorie, icône, ordre, `actif`). C'est **voulu** — le contenu vient du code, par
migration. L'admin reste en lecture seule dessus.

---

## 3. Le catalogue à jour (relevé du 16/08/2026)

L'écran prof annonçait comme « à venir » trois choses **déjà livrées**. Une migration a été
écrite pour corriger le catalogue : `alembic/versions/f4b1c8d3a7e9_bientot_disponible_dit_vrai.py`
(branchée sur `a4e7c2f9b135`). Elle est **prête, non appliquée** — à reprendre ou à rejouer.

Ce qu'elle fait :

- `analyser-consigne` → `actif = false` : l'écran Consignes est livré, on ne fait plus voter
  pour lui. **Désactivée, jamais supprimée** — des votes y sont rattachés (clé étrangère).
- `verifier-evaluation` → devient **« Évaluation corrigée automatiquement »**, catégorie
  Évaluation : son ancienne description était mot pour mot ce que fait l'écran Équité, livré.
  Ne reste que ce qui n'existe pas — la réécriture automatique.
- `app-mobile` → devient **« aSchool adapté au téléphone »** : l'application s'installe déjà
  (PWA, trois fiches d'aide) ; ce qui manque est l'adaptation des écrans au format mobile.
- `quiz-interactif` → passe en catégorie **Évaluation**.
- Trois cartes neuves, catégorie Évaluation : `eval-sujets`, `eval-grilles`, `eval-ccf` — les
  quatre entrées grisées du menu prof « Mes évals » deviennent enfin votables (le menu et cet
  écran disaient deux choses différentes).

Trois icônes ont été ajoutées côté écran pour ces cartes : `document`, `grille`, `diplome`
(`BientotDisponible.jsx`).

---

## 4. Ce qui reste à faire (le travail de la session admin)

### 4.1 — La livraison pose elle-même le drapeau

Convention à adopter : **la migration qui livre une fonctionnalité pose `livree = true`** sur sa
ligne du catalogue. C'est le développement qui sait qu'elle est livrée, pas l'administrateur.
Conséquence : la carte quitte l'écran prof le jour du déploiement, sans que personne ait à y
penser. L'admin garde la main pour décocher si besoin.

Il ne reste alors **qu'une seule décision humaine** : cocher « Nouveauté ».

### 4.2 — Le centre d'actions du tableau de bord admin

Un encart **« À traiter »**, placé **en tête de la page d'accueil de l'administration, juste sous
le bandeau « aSchool — état de la plateforme », pleine largeur**.

Pourquoi là et pas dans la zone libre en bas : la santé de la plateforme se *consulte*, une
action *s'impose*. Une alerte qu'il faut aller chercher en bas d'une colonne n'est pas une
alerte. C'est la place qu'elle occupe chez Microsoft et Google.

Règles :

1. **L'encart n'existe que s'il y a quelque chose.** Aucun cartouche « Aucune alerte » en
   permanence : on apprend à ne plus le voir, et il occupe la place pour rien. Zéro action →
   zéro encart, la page respire.
2. **Une ligne = une action + un lien.** Elle dit ce qui est attendu (« *Quiz interactif élèves*
   est livrée : l'annoncer aux professeurs ? ») et ouvre l'écran concerné en un clic.
3. **Elle disparaît dès que le geste est fait** — l'état se lit en base, il ne se marque pas à
   la main.
4. **Une seule source.** Un `GET /api/admin/actions` renvoie la liste ; l'encart l'affiche, la
   pastille du menu la compte. Deux calculs séparés divergeraient.

Première source d'actions à brancher : les fonctionnalités `livree = true` et
`nouveaute = false` — livrées, pas encore annoncées. D'autres viendront (référentiels,
démonstrations, feedbacks sans réponse) : prévoir la liste ouverte dès le départ, chaque source
donnant `titre`, `detail`, `page` et `code`.

### 4.3 — La pastille du menu

Sur l'entrée **« Bientôt disponible »** du menu admin, une pastille comptant les actions en
attente pour cet écran, et sur l'entrée de tête du menu, le total. Elle n'apparaît **que** s'il y
a au moins une action, et s'éteint seule.

### 4.4 — La trace (facultatif, mais cohérent avec l'existant)

`create_alert` existe et n'est pas utilisé ici : une fonctionnalité qui passe en `livree = true`
peut y écrire une ligne d'information. À faire seulement si l'encart du 4.2 lit la même source —
sinon on crée un second endroit à consulter, donc un endroit oublié.

---

## 5. Ce qu'il ne faut pas faire

- **Ne pas rendre le texte des cartes modifiable dans l'administration.** Le contenu vient du
  code, il se relit en revue, il se déploie. Un écran de saisie ferait diverger le catalogue de
  la réalité — c'est exactement ce qui a produit les trois cartes fausses relevées au point 3.
- **Ne pas supprimer une carte livrée** : `actif = false`. Les votes lui sont rattachés.
- **Ne pas annoncer plusieurs nouveautés à la fois.** La règle est déjà tenue côté serveur, ne
  pas l'assouplir côté écran : annoncer trois choses, c'est n'en annoncer aucune.
- **Ne pas remplir la zone libre du tableau de bord.** Une page professionnelle n'a pas besoin
  d'être pleine.
