# A-SCHOOL — faits du poste et décisions produit

Ce fichier garde **les faits du poste de travail** et **les décisions produit** : comment le
poste est fait, et ce que l'application doit faire.

Il ne contient aucune consigne de conduite. Le rappel permanent et son archive ont été
supprimés le 01/08/2026.

---

## 1. Faits du poste — Python et Node passent par Docker

*(ancienne RÈGLE 24)*

**Rien n'est installé nativement sur ce poste.** Ce n'est pas un obstacle, c'est la
configuration normale du projet : tout passe par les conteneurs.

| Besoin | Commande |
|---|---|
| Python (alembic, pytest, uvicorn) | `docker exec a-school-backend-1 …` |
| Node (npm, vite, build, tests front) | `docker exec a-school-frontend-1 …` |
| Suite de tests backend | `docker exec a-school-backend-1 python -m pytest -p no:warnings -q` |
| Suite de tests frontend | `docker exec a-school-frontend-1 sh -c "cd /app/frontend && npm test"` |
| Migration | `docker exec a-school-backend-1 alembic upgrade head` |

Le code du projet est **monté** dans les conteneurs (`.:/app`) et le back tourne en
`--reload` : une édition est prise en compte sans rebuild.

**Les bases :**

- `a-school-db-1` — base de développement `aschool_dev` ;
- `a-school-db_test-1` — base de test `aschool_test`, jetable, celle que `conftest.py` impose ;
- `a-school-adminer-1` — l'explorateur web des bases.

Avant de dire « je ne peux pas exécuter », lancer `docker ps` et passer par le bon conteneur.

**Le dépôt est en `c:\A-SCHOOL`.** L'ancien cartouche du hook annonçait `d:\A-SCHOOL` à trois
endroits et le hook lui-même se repliait sur `/d/A-SCHOOL` — ce chemin n'existe pas sur ce
poste. Corrigé le 31/07/2026.

---

## 2. Décision produit — l'activité générée : auto-save et historique

*(ancienne RÈGLE 0)*

Pour l'activité générée, **il n'y a plus de bouton « Valider »**. Rien n'attend en mémoire :
tout est écrit en base immédiatement, à chaque changement — génération, réparation,
amélioration, retouche à la main.

**Deux mécanismes qu'on ne confond jamais :**

1. **L'auto-save** sauvegarde l'**état courant** du document en continu. Fermer puis revenir
   rend l'état exact. Ce n'est **pas** une version à chaque frappe.
2. **Une version** est une photo restaurable, figée seulement **aux jalons** : chaque action
   machine (génération, correction, amélioration) et chaque **fin** de session d'édition
   manuelle. Des retouches d'affilée font **une** version, pas une par frappe.

**On n'écrase jamais une version.** L'historique s'empile : « revenir en arrière » veut dire
*restaurer* une version, et cette restauration devient elle-même une nouvelle version.

**L'export (Word / PDF / txt) n'est pas une version** : c'est la sortie — un changement de
statut, plus le fichier produit à partir de la version courante.

**Le statut « brouillon » :** tant qu'on travaille dessus, l'activité est un brouillon en base.
Dès qu'elle sort — devient une vraie activité rangée dans « Mes activités » — le statut
brouillon tombe. Le brouillon ne disparaît pas : il **devient** l'activité, même enregistrement,
zéro copie. Conséquence voulue : pas de pile de brouillons à gérer, ni suppression manuelle ni
nettoyage admin à coder.

Ce modèle vaut pour **l'activité générée**. Les autres écrans CRUD gardent le « Valider = put »
décrit ci-dessous tant qu'on ne les bascule pas explicitement.

**Tests qui le tiennent :** `tests/test_historique_versions.py` (8 tests — empilement sans
écrasement, restauration qui devient une version, cloisonnement entre profs) et
`tests/test_ecriture_activite_controlee.py` (7 tests — le libellé écrit vient de la base,
jamais du client).

---

## 3. Décision produit — le CRUD encadré et le principe d'écran

*(ancienne RÈGLE 4, supprimée du rappel le 31/07/2026 : c'est du métier de base, pas une
consigne de travail. Elle est descendue ici en entier, et le test
`tests/test_pas_de_nom_recopie.py` en tient la partie vérifiable.)*

La base de données est la **seule** source de vérité. Toute donnée métier vit en base, à un
seul endroit.

**CRUD = les quatre seules opérations possibles.** Chaque opération qui écrit ou efface passe
d'abord un contrôle métier, jamais automatique :

- **Create** — refus si la donnée existe déjà (unicité) ;
- **Update** — refus si la donnée est figée par son usage (motif « facture validée » : gelée
  par la loi, et plein de cas semblables) ; on vérifie d'abord en base qu'elle est libre ;
- **Delete** — refus si la donnée est encore référencée par une autre table (clé étrangère) ;
- **Read** — aucune contrainte, la lecture est toujours libre.

**Principe d'écran.** Un écran n'est qu'une fenêtre sur les tables : ses champs **sont** les
colonnes réelles (get pour afficher), ses boutons **sont** le CRUD. « Valider » = put, on écrit
en base. « Annuler » = rien, aucune écriture, on garde la valeur lue.

Ce principe ne change pas avec la complexité : un écran sur une table ou une page sur plusieurs
tables reliées par leurs clés étrangères, c'est le même geste — juste plusieurs get/put sur les
bonnes tables. Un cas complexe peut porter **plusieurs** boutons Valider (validation par étapes
qui se dépendent : tant qu'une étape n'est pas validée on ne passe pas à la suivante, par
exemple la création d'un référentiel). Chaque Valider reste un put.

---

## 4. Décision produit — le couple toujours affiché dans le header

*(ancienne RÈGLE 26)*

Le couple de travail (**Matière - Niveau**) est affiché en permanence dans le bandeau bleu du
haut, en blanc, juste **au-dessus** du bouton « Changer niveau et/ou matière »
(`frontend/src/components/Header.jsx`, colonne du couple), en face du « générateur d'activités
pédagogiques » de gauche, sur **tous** les écrans.

Le retirer, le déplacer ou le masquer est un bug bloquant, pas un détail — demandé quatre fois
par l'utilisateur.

**Test qui le tient :** `frontend/test/couple-toujours-dans-le-header.test.js` (4 tests). Il attrape la
suppression, le passage sous le bouton, la mise sous condition, et le démontage du Header dans
`App.jsx`. Il n'attrape **pas** un `display: none` : le front tourne sur `node --test`, sans
jsdom ni testing-library, donc aucun rendu de composant n'est possible.

---

## 5. La dette du projet, telle qu'elle est comptée

Deux tests portent l'état des lieux gelé au **31/07/2026**. Ils sont verts aujourd'hui et
rouges à la première violation nouvelle. **Aucune entrée ne s'ajoute sans décision de
l'utilisateur** — un ajout silencieux vaut suppression du test.

### `tests/test_pas_de_nom_recopie.py` — 10 dettes, 2 exceptions permanentes

Une colonne texte qui recopie le nom d'une donnée de référence au lieu de ranger son
identifiant.

**Dette** — `sequences.matiere` / `.niveau`, `seances.matiere` / `.niveau` / `.mode` / `.style`,
`seance_versions.style`, `activites.matiere` / `.niveau`, `users.langue_lv`.

**Exception permanente** — `incidents.matiere` et `incidents.niveau` : instantané figé de la
tentative, motif « facture validée ». Relire le référentiel donnerait le nom d'aujourd'hui et
falsifierait le journal.

### `tests/test_rien_en_dur_dans_le_code.py` — 6 dettes, 5 exceptions permanentes

Une donnée métier écrite dans le code au lieu de vivre en base.

**Dette** — `activites.py:_USER_PARAMS`, `mes_contenus.py:JALON_LABELS`,
`mes_contenus.py:PHASES_ESQUISSE`, `maintenance.py:CATEGORIES`, les deux tons de rédaction
(`activites.py:438`), les fournisseurs IA (`generator.py:94`, alors que la table
`ai_fournisseurs` existe).

**Exception permanente** — `feedback.py:ALLOWED_TYPES` (types MIME),
`transcribe.py:_ALLOWED_EXT` et `ocr.py:65` (extensions de fichier),
`analyse_amont.py:_SCHEMA_DECOUPE` (schéma JSON), `llm_prompts.py:PROMPTS` (registre semé par
migration, déjà gardé par `test_prompts_en_base.py`).

**Corriger une dette se conclut en baissant le compte dans le test.** Un troisième test dans
chaque fichier tombe si une entrée réparée traîne encore dans la liste : la dette reste
comptable.
