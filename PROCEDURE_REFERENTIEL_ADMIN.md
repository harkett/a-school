# Procédure Admin — Déposer un référentiel

**Légende :** case cochée = **prouvé en vrai** (exécuté et vérifié cette session). Case vide = code présent mais pas prouvé bout-en-bout, ou pas construit.
Écran : `frontend/src/pages/AdminReferentiels.jsx` · Moteur : `backend/pedagogie/referentiels_admin.py` · Base de test : `aschool_creche_miroir`.

---

## Ce qui marche, prouvé en vrai (jusqu'à la validation du PDF)

- [x] **1. Choisir le couple (cycle + niveau)** — l'écran dit tout de suite si ce couple a déjà un référentiel (nom du PDF, source, matières reliées).
  GET `/admin/referentiels/etat`

- [x] **2. Fournir le PDF** — par dépôt (choisir le fichier) ou par lien (URL). Aperçu de contrôle : nb de pages + 25 premières lignes.
  POST `/admin/referentiels/preparer-depot` · POST `/admin/referentiels/preparer-lien` — testé HTTP 200.

- [x] **2 bis. Garde-fou : plafond de pages au dépôt** — réglage EN BASE `depot_max_pages` (défaut 150). Un PDF trop long est refusé tout de suite, avant tout traitement.
  Testé : BO 967 p. → refus net (« Document trop long : 967 pages. Veuillez déposer un document de 150 pages maximum. ») ; BTS 88 p. → accepté.
  *Corrigé cette session : avant, un gros PDF figeait l'écran puis affichait un faux « échec réseau » alors que l'enregistrement aboutissait quand même côté serveur.*

- [x] **3. Test — la famille (l'IA classe le PDF)** — match d'une famille existante, ou proposition d'une nouvelle à créer, ou on jette.
  POST `/admin/referentiels/detecter-famille` (+ `/familles`, `/abandonner`) — testé 200, l'IA répond.

- [x] **4. Test — le couple (IA) + place de la famille** — n°1 : le couple visé par le PDF colle-t-il au couple déclaré ; n°2 : le (famille + niveau) a-t-il sa place (`famille_couples`). « Valider » ne s'affiche que si les deux passent ; sinon forçage avec motif tracé.
  POST `/admin/referentiels/verifier-depot` — testé : `correspond=true`, famille `existe=true`.

- [x] **5. Valider le document** — range le PDF en `REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf` et écrit la ligne `referentiels` (couple, famille, source, forçage).
  POST `/admin/referentiels/valider` — testé **0,37 s**.
  *Corrigé cette session : `valider` n'extrait plus le texte complet du PDF (travail lourd ~177 s sur un gros doc, et le fichier produit n'était relu par personne). Le découpage/ingestion ré-extrait déjà du PDF quand c'est nécessaire.*

---

## Ce qui a du code mais n'est PAS prouvé bout-en-bout

Les endpoints existent et l'écran les appelle, mais rien n'a été prouvé jusqu'au bout cette session — et surtout **la chaîne se termine dans le vide** (voir plus bas : 0 chunk).

- [ ] **6. Renseigner les matières du couple** — cocher / ajouter, renommer, retirer.
  POST `/admin/referentiels/matieres` (+ `/matiere`, `/retirer-matiere`).

- [ ] **7. Prompt de découpe (généré par l'IA, validé par l'admin)** — la découpe refuse de tourner tant que le prompt n'est pas validé.
  `/admin/referentiels/prompt-decoupe/generer|regenerer|valider|decouper`.

- [ ] **8. Règle de découpe — valider/rejeter le statut.**
  POST `/admin/referentiels/regle-decoupe/valider|rejeter`.

- [ ] **9. Aperçu du découpage + arbitrage des cas ambigus** — voir les unités et tranches d'âge (lecture seule), trancher les cas flous ou demander l'avis d'un pro par mail.
  GET `/admin/referentiels/apercu-decoupage` · `/arbitrage-flou`.

---

## Le vrai reste à faire (pas un geste admin aujourd'hui)

- [ ] **Vectoriser & ingérer** — la seule brique qui écrit les chunks vectorisés (BGE-M3 → `referentiel_chunks`) est `ingest_pgvector`, appelée **uniquement en ligne de commande**. Aucun bouton admin.
  Prouvé cette session : **0 chunk** dans la base → **aucun couple n'est réellement « traité / disponible »** au prof.
  `backend/rag/pgvector_store.py:134`

- [ ] **Calibrer le seuil** — `referentiels.score_min` existe en base (défaut 0.30), mais aucun endpoint ne le mesure, ne le calibre ni ne l'édite.
  `backend/core/models_db.py:420`

- [ ] **Activer (niveau « traité »)** — aucun bouton « activer ». La disponibilité au prof (`refDisponible`) est dérivée : le niveau devient sélectionnable dès qu'au moins 1 chunk existe. Donc ça dépend de l'ingestion ci-dessus.
  `backend/pedagogie/programmes.py:42`

- [ ] **Fournir le PDF par recherche web** — onglet affiché à l'écran, mais pas branché (« bientôt disponible »).
