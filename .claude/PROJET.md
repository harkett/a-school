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

**Test qui le tient :** `frontend/src/couple-toujours-dans-le-header.test.js` (4 tests). Il attrape la
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

### `tests/test_rien_en_dur_dans_le_code.py` — 12 dettes, 5 exceptions permanentes

Une donnée métier écrite dans le code au lieu de vivre en base.

**Le compte est passé de 6 à 12 le 01/08/2026, sans qu'une seule dette nouvelle ait été
écrite.** Le filet lisait les fichiers en `utf-8` ; quatre fichiers du backend portent un BOM
(`admin.py`, `comptes.py`, `alerts.py`, `main.py`), `ast.parse` levait, et un `except: continue`
les sautait **en silence** — le plus gros fichier du projet n'était pas analysé. Le chiffre
d'avant était faux ; un fichier illisible fait désormais **tomber** le test.

**Dette** — `activites.py:_USER_PARAMS`, `mes_contenus.py:JALON_LABELS`,
`mes_contenus.py:PHASES_ESQUISSE`, `maintenance.py:CATEGORIES`, les deux tons de rédaction
(`activites.py:438`), les fournisseurs IA (`generator.py:94`, alors que la table
`ai_fournisseurs` existe) ; et les six révélées : `admin.py:SETTING_DEFAULTS` (le repli code du
projet, alors que la doctrine du même fichier l'interdit), `main.py:_cors_defaut`, les noms de
bases réelles (`admin.py:539`), les types de feedback (`comptes.py:313`),
`admin.py:_PARAM_ECRAN_DEDIE_EXACTS` et `_PREFIXES`.

**Exception permanente** — `feedback.py:ALLOWED_TYPES` (types MIME),
`transcribe.py:_ALLOWED_EXT` et `ocr.py:65` (extensions de fichier),
`analyse_amont.py:_SCHEMA_DECOUPE` (schéma JSON), `llm_prompts.py:PROMPTS` (registre semé par
migration, déjà gardé par `test_prompts_en_base.py`).

**Corriger une dette se conclut en baissant le compte dans le test.** Un troisième test dans
chaque fichier tombe si une entrée réparée traîne encore dans la liste : la dette reste
comptable.

---

## 6. Le mot de passe admin — le `.env` amorce, il n'ouvre pas pour toujours

Il y a deux mots de passe admin possibles : celui écrit en clair dans `.env`
(`ADMIN_PASSWORD`) et celui que l'administrateur choisit lui-même dans **Admin → Mon compte**,
rangé chiffré en base (ligne `admin_password_hash` de la table `settings`).

**La règle : tant qu'aucun mot de passe n'a été choisi, celui du `.env` ouvre ; dès qu'un
existe en base, LUI SEUL ouvre.**

Ce n'était pas le cas jusqu'au 01/08/2026. `/admin/change-password` appliquait déjà cette
règle, mais `/admin/login` faisait `password_ok = env_ok or db_ok` : l'ancien mot de passe du
`.env` continuait d'ouvrir la porte d'entrée après un changement. Le bouton « changer mon mot
de passe » ne fermait donc rien — et ce mot de passe-là voyage, il est en clair dans chaque
copie du dossier (`Scripts/je_pars.ps1` emporte le `.env`) et dans chaque sauvegarde.

**Test qui le tient :** `tests/test_admin_mot_de_passe_amorcage_seul.py` (5 tests). Il vérifie
les deux sens — le `.env` ouvre quand la base est vide, il est refusé quand elle ne l'est pas —
et que les deux routes disent la même chose.

### Secours — mot de passe admin oublié

Supprimer la ligne remet celui du `.env` en service, immédiatement, sans redémarrage :

```sql
DELETE FROM settings WHERE key = 'admin_password_hash';
```

Sur le poste : `docker exec a-school-db-1 psql -U aschool -d aschool_dev -c "DELETE FROM
settings WHERE key = 'admin_password_hash';"` (l'utilisateur de la base est `aschool`, pas
`postgres` — cf. `docker-compose.yml`). Le dernier test du fichier vérifie ce chemin —
ce n'est pas une promesse de documentation, c'est un chemin prouvé.

---

## 7. Le cœur de la génération — ce que la lecture du 01/08/2026 a trouvé

Quatre fichiers portaient la génération sans avoir jamais été relus : `referentiels_admin.py`,
`mes_contenus.py`, `activites.py`, `generator.py` (~3 800 lignes). Quatre défauts en sont sortis,
tous **silencieux** : la suite était verte sur les quatre, et aucune passe mécanique ne les
avait vus.

### Le prompt d'un couple×type est contrôlé À L'ÉCRITURE

C'était le **seul** prompt du produit qui ne l'était pas. Tous les autres passent par
`valider_prompt` (admin.py) ; celui-là, écrit par ✎ Prompt de l'écran Référentiels, n'exigeait
que « non vide ». Il finit pourtant dans `modele.format(...)` (`activites.py`, api_generate
étape 5), qui n'attrape que `KeyError`.

- Accolades cassées (un exemple JSON collé, une accolade seule) → `ValueError` non attrapée →
  **500 nu chez le prof**, sans message et sans incident enregistré : l'erreur survient AVANT le
  flux, donc hors du `try` qui crée les incidents.
- **`{texte}` oublié** → rien ne tombe. La génération marche, elle ignore simplement l'idée que
  l'enseignant a écrite. Le produit repose sur « la zone de texte mène » ; sans ce repère, elle
  ne mène plus rien.

Garde-fou : `activites.valider_prompt_couple`, appelé avant l'écriture.
**Test :** `tests/test_prompt_du_couple_valide_a_l_ecriture.py` (8 tests).

### Le couple d'une activité suit sa régénération

`PUT /contenus/activites/{id}` contrôlait le type contre le couple de travail ACTUEL mais
laissait `matiere`/`niveau` à leur valeur de naissance. Un prof qui changeait de couple puis
régénérait écrivait un type validé en 3e sur une ligne étiquetée 6e. Cette étiquette n'est pas
décorative : « Mes stats » compte par couple, et le few-shot « aSchool vous reconnaît » ne
compare qu'aux activités du **même** couple. La séance faisait déjà suivre le sien
(`_remplir_seance`) — les deux frères se comportent enfin pareil.
**Test :** `tests/test_couple_de_l_activite_suit_la_regeneration.py` (3 tests).

### Le catalogue des types ne peut plus doublonner un libellé

L'anti-doublon se fait par `label` (aucun unique en base : la règle ne tient que par le code) —
et le code la disait de deux façons. `ajouter_type_catalogue` cherchait sans filtrer sur
`actif`, la détection IA cherchait avec. Un type **désactivé** devenait invisible pour la
détection, qui en recréait un second du même nom. Reproduit : 2 lignes « Exercice de repérage ».
Les deux portes cherchent maintenant par libellé seul ; un type désactivé reste désactivé.
**Test :** `tests/test_catalogue_types_sans_doublon.py` (4 tests, comportement réel).

### Retirer une matière annonce le vrai nombre de profs

`retirer_matiere` ne comptait que `subject_id` ; la suppression du référentiel, vingt lignes
plus bas, comptait `subject_id` **et** `travail_matiere_id`. Un prof dont c'était le couple de
travail perdait sa matière sans figurer dans le nombre annoncé à l'admin.

### Reste ouvert (aucun code écrit)

- **`GET /mes-contenus` renvoie le `resultat` COMPLET** de chaque séance et de chaque activité —
  l'écran n'en affiche qu'un titre. Un prof à 200 contenus télécharge 200 documents entiers pour
  dessiner une liste.

---

## 8. Le champ `mode` du registre des prompts — « format » ou « replace »

*(02/08/2026 — suite directe de la section 7.)*

Trois prompts vivaient **hors** du registre `PROMPTS`, donc hors de tout : l'écran Prompts ne
les voyait pas, `valider_prompt` ne les gardait pas, et rien ne vérifiait qu'une base neuve les
contenait.

| Prompt | Ce qu'il fait | Sa porte, avant |
|---|---|---|
| `prompt_meta_decoupe` | l'IA **rédige** le prompt de découpe du document | deux routes qu'aucun écran n'appelle |
| `prompt_verif_decoupe` | l'IA **relit** ce prompt et le corrige | **aucune** — lu à chaque découpe, modifiable par rien |
| `prompt_gabarit_type` | il **fabrique** le prompt de chaque couple×type au coche | **aucune** — pas même une ligne en base, seulement un repli code |

Ils ne pouvaient pas y entrer tels quels, et c'est la raison du champ `mode` :

- **`format`** (défaut, absent = celui-ci) — le prompt part dans `str.format(**valeurs)`. Ses
  accolades sont du code : les repères obligatoires doivent être là **et** le texte entier doit
  se formater sans lever. Un exemple JSON s'y écrit accolades doublées.
- **`replace`** — le prompt part dans `str.replace("{repère}", valeur)`. Ses autres accolades
  sont du **texte**, et c'est même leur raison d'être : ces prompts **décrivent un autre
  prompt** (« ton prompt devra contenir `{texte}` », « impose la sortie `{"unites":[…]}` »).
  On vérifie la **présence** des repères, on n'appelle **jamais** `.format()`.

Deux raisons distinctes, et il vaut la peine de ne pas les confondre :

- `meta_decoupe` et `verif_decoupe` **cassent réellement `.format()`** — mesuré :
  `KeyError: 'texte'` et `KeyError: '"unites"'`. La règle « format » refuserait leur texte
  légitime.
- `gabarit_type`, lui, se formate très bien. Son mode vient de la **consommation** : au coche
  d'un type on ne remplit que `{label}` et `{niveau}` ; `{texte}` et `{referentiel}` doivent
  **survivre** jusqu'à la génération du prof. Un `.format()` global les mangerait.

**Le gabarit se règle enfin depuis l'écran Prompts**, et `valider_prompt` le tient à l'écriture.
En plus, `_generer_prompt_type` **relit ce qu'il produit** avec `valider_prompt_couple` : une
valeur posée directement en base (Adminer est là) fait tomber la faute chez l'**admin**, au
moment où il coche le type, pas chez le prof au milieu d'une génération.

**Migration :** `d4f8a2b6c9e3` — `ON CONFLICT DO NOTHING`, c'est une **adoption**, pas une
correction : les deux premières lignes existent déjà et un texte affiné par l'admin ne doit pas
être écrasé. Son `downgrade` ne retire que `prompt_gabarit_type`, la seule qu'elle crée. Jouée
dans les deux sens.

**Tests :** `tests/test_prompts_mode_replace.py` (11 tests) — dont la liste **gelée** des trois
prompts en mode replace : retirer le contrôle `.format()` d'un prompt se décide, ça ne se glisse
pas.
