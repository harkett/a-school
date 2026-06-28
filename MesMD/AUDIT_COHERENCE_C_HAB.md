# AUDIT DE COHÉRENCE — liste du chat (axes 1 / 2 / 4)

> Périmètre : `TRACKER.md` · `TABLEAU-DE-BORD.md` · `TRACKER_REFORME.md` · `TRACKER_FOURNISSEURS_IA.md`.
> Axes couverts : **1 interne · 2 croisé · 4 source unique**. L'axe **3 (vs code/git)**
> n'est PAS couvert ici (je ne lis pas le code) — marqué « à confirmer côté code (CC) ».
> Format : `doc · emplacement · ce qui est affirmé · réalité/conflit · gravité`.
> Barème CLAUDE.md non fourni → je m'appuie sur les règles écrites dans les docs eux-mêmes
> (statut au seul TRACKER, détail au TABLEAU).

---

## Cluster A — `TABLEAU` périmé en tête (axe 1 interne)

**A1** · TABLEAU l.6 · « Date 2026-06-11 · v3.3.0 · Focus : Consolidation du cœur avant
réouverture du push » · On est au 23/06 ; consolidation finie (P5.10/11 ✅ au TRACKER),
réforme menée jusqu'au 22/06. En-tête périmé de 12 j. · **moyenne**

**A2** · TABLEAU l.21-23 · « ▶️ Prochaine action … PREMIÈRE TÂCHE matin du 13/06 : TRAITER
LA CRÈCHE » · Contredit TRACKER l.4-6 (« en cours : rien ; prochaine : P4.8/P4.9 puis jalon
push »). La Crèche/Petite-Enfance est en HORIZON 4 conditionnel (TRACKER l.166). Ce pointeur
« lis ici en premier » envoie sur une fausse piste. · **élevée**

**A3** · TABLEAU l.25 · « Chantier actif = Consolidation… Prochain : P5.11, puis P3.5 » ·
P5.11, P3.5, P5.10 sont ✅ au TRACKER (l.61-64). Le « prochain » est déjà fait. · **élevée**

---

## Cluster B — statuts P3.x/P4.x/P5.x : `TABLEAU` contredit `TRACKER` (axes 2 + 4)

> Racine : TABLEAU l.15 dit « le statut ne vit qu'une fois, dans le TRACKER ; ce tableau n'a
> plus de colonne État ». Or la section AUDIT (l.322-340) porte encore des `[x]/[ ]` — qui
> aujourd'hui **contredisent** le TRACKER. Violation de source unique **et** divergence.

**B1** · TABLEAU l.333 vs TRACKER l.61 · TABLEAU : P5.11 `[ ]` à corriger · TRACKER : P5.11
✅ « réglé (sans objet) ». · **élevée**

**B2** · TABLEAU l.334 vs TRACKER l.62 · TABLEAU : P3.5 `[ ]` à corriger · TRACKER : P3.5
✅. · **élevée**

**B3** · TABLEAU l.335 vs TRACKER l.63 · TABLEAU : P4.7 `[ ]` SOUS-D · TRACKER : P4.7 ✅. ·
**élevée**

**B4 (structurel, axe 4)** · TABLEAU (AUDIT l.322-340, Prochaine action, ITEMS) · porte des
`[x]/[ ]/[~]` partout · alors que sa propre règle l.15 l'interdit. Tant que ces marqueurs
restent, le TABLEAU re-porte un statut qui dérive du TRACKER. · **moyenne-élevée**

---

## Cluster C — RAG / `/api/generate` : docs décrivent un mécanisme supprimé (axe 2 ; à confirmer code)

**C1** · TABLEAU l.312 · « Aujourd'hui `/api/generate` n'active le RAG que si `RAG_ENABLED=true`
ET matière∈{maths} ET niveau∈{5e,4e,3e} » · TRACKER_REFORME Phase 1 Tâche 1 (l.27-31) :
gate maths/cycle4 **retirée** de `generate.py` + flag `RAG_ENABLED` **retiré** du `.env`. →
TABLEAU décrit une branche supprimée. · **élevée** · *à confirmer côté code (CC)*

**C2** · TABLEAU l.314 · « Valeur de `RAG_ENABLED` dans le `.env` prod inconnue » · Même cause :
`RAG_ENABLED` retiré par la réforme. Tâche sans objet. · **moyenne** · *à confirmer code*

**C3** · TABLEAU l.350 (INFRA-RAG) · « Branchée sur `/api/generate` avec gates (matière/niveau/
feature flag) » · Branche retirée par réforme Phase 1. Description périmée. · **élevée** · *code*

**C4** · TRACKER l.223 (A10) · « corpus actuel cycle 4 en bloc, filtre niveau explicitement
désactivé (`generate.py:78`) ; métadonnée niveau absente aujourd'hui » · TRACKER_REFORME
Phase 2/3 (l.42-70) : ingestion re-jouable **avec métadonnée niveau** livrée et validée (base
CIEL 236 chunks, niveau posé, 55 tests verts). → A10 **sous-estime** un acquis majeur de la
réforme (au moins pour CIEL). C'est exactement le chevauchement pressenti. · **élevée** ·
*portée maths vs CIEL à confirmer côté code*

---

## Cluster D — hébergement ChromaDB : décision « prise » vs « en attente » (axe 2)

**D1** · TRACKER l.219-220 (A9) vs TRACKER_REFORME l.109 · A9 : « binaire-en-git vs rebuild =
EN ATTENTE D'ARBITRAGE » · REFORME Phase 6 : « Décision (c) du 21/06 » (sortir le store du git +
reconstruction au déploiement). → Un doc dit décidé, l'autre dit en attente. · **élevée**

**D2 (interne A9)** · TRACKER l.220 · A9 pose une **contrainte dure** : « maths n'a pas de PDF
source → ne peut pas être reconstruit, seule option sûre = binaire-en-git ». Or REFORME l.109
décision (c) = « reconstruction au déploiement ». La décision (c) semble **incompatible** avec
la contrainte maths d'A9. À réconcilier (la décision tient-elle malgré maths ?). · **élevée**

---

## Cluster E — pointeurs vers fiches périmées (axe 2 ; déjà partiellement connu)

**E1** · TABLEAU l.63 (item 39) + TRACKER l.110 (item 39) · pointent vers `D28` · `TRACKER_
FOURNISSEURS_IA` §11 signale `D28`/`TABLEAU #39` **périmés** (« tout passe par Groq via
`groq_client.py` » + `anthropic_client.py` parallèle = faux depuis Tâche 2 du 21/06). →
Le pointeur périmé subsiste dans deux docs, non annoté. · **moyenne**

---

## Cluster F — sous-tâche déclarée mais non suivie (axe 1)

**F1** · TRACKER_REFORME l.77 vs l.78-83 · le découpage Phase 4 déclare « 4.1.d température »,
mais **aucune ligne de statut** `[x]/[ ]/[⏸️]` n'existe pour 4.1.d (4.1.a/b/c ✅, 4.1.e ⏸️,
4.1.d nulle part). Risque d'oubli. À noter : `TRACKER_FOURNISSEURS` §6 dit « ordre 4.1.d/4.1.e
non figé » — or 4.1.e est suspendu, statut de 4.1.d à clarifier. · **moyenne**

---

## Ce qui paraît COHÉRENT (vérifié doc-vs-doc, rien à corriger)

- `TRACKER_FOURNISSEURS_IA` v0.4 (bandeau STATUT suspendu) ↔ `TRACKER_REFORME` l.83
  (« [⏸️] 4.1.e suspendu ») : **alignés**.
- `TABLEAU` item 45 (l.101, multi-fournisseurs failover/dashboard/routage) ↔ `FOURNISSEURS`
  §8 (cap épic #45) : **cohérents**.
- A8 (TRACKER l.217, catalogue CIEL repli A → B obligatoire, B non fait) : aucun doc ne
  prétend B fait ; la réforme ne touche pas le catalogue d'activités → **paraît à jour**
  (contrairement à A10). *À confirmer côté code par CC.*

---

## Synthèse (mon angle)

- Le **pilote** (`TRACKER`) est globalement le plus à jour ; c'est le **`TABLEAU`** qui porte
  le plus de périmé (clusters A, B, C) — en-tête, « Prochaine action », section AUDIT, et la
  description RAG d'avant-réforme.
- Le chevauchement le plus lourd que CC pressentait est **confirmé doc-vs-doc** : **A10** (et la
  branche RAG `/api/generate`) décrivent un état antérieur à la réforme Phase 1/2/3.
- Deux **vraies contradictions de décision** à trancher, pas juste du périmé : **D1/D2**
  (hébergement ChromaDB : décidé vs en attente, + contrainte maths).
- Beaucoup de divergences viennent d'une cause unique (cluster B4) : le `TABLEAU` continue de
  porter des statuts que sa propre règle réserve au `TRACKER`.

> Rien corrigé. Liste à superposer avec la tienne et celle de CC. Les écarts qu'on trouve tous
> les trois = sûrs ; les écarts uniques à un seul = les plus instructifs.
