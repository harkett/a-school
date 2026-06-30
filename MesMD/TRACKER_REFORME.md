# Tracker éphémère — Réforme moteur LLM + RAG

> Liste de pilotage (pour Harketti). ✅ fait · ☐ à faire · ⏸️ parqué. Détail : demander.

## Phase 0 — Audit
- [x] Audit complet (6 blocs + décision archi RAG)

## Phase 1 — Nettoyage moteur LLM
- [x] Tout passe par generate(), gate maths retirée, Groq texte mort supprimé

## Phase 2 — Refonte RAG
- [x] Moteur générique + une fiche par référentiel (CIEL)

## Phase 3 — Qualité du différenciateur
- [x] Overlap, déduplication, seuil de score, métadonnées — base CIEL 236 chunks

## Phase 4 — Administrable
- [x] 4.1.a — modèle texte administrable
- [x] 4.1.b — écriture admin du modèle (combo fermée)
- [x] 4.1.c — max_tokens administrable
- [x] 4.1.d — température administrable (globale ; optimiseur reste à 0)
- [x] Interface admin qui lit/écrit les réglages
- [x] Validation des valeurs (modale bloquante)
- [x] Réglages rechargeables à chaud
- [x] Prompts administrables en base (5 outils ; repères obligatoires protégés ; retour au défaut)

## Phase 5 — Robustesse / dette
- [x] Régulation de concurrence sur les appels LLM (sémaphore partagé, limite env, attente bornée)
- [x] Unifier les migrations (plus d'ALTER inline)
- [x] Décider : rester SQLite ou migrer PostgreSQL — TRANCHÉ 25/06 : rester SQLite (YAGNI). **RENVERSÉ le 27/06 : moteur cible = PostgreSQL** — éléments nouveaux : (1) le Niveau 2 = modifs de tables, pénibles sous SQLite (cf. migration 010 = reconstruction de 7 tables) ; (2) base quasi vide → migrer coûte le moins maintenant. Migration moteur **faite en local** (Pas 1-11, cf. `AUDIT-EN-BASE-VS-EN-DUR.md`) ; reste la **bascule prod** (Pas 13). Doctrine durable mise à jour dans CLAUDE.md.
- [x] Code d'erreur 429 distinct (surcharge / rate limit → « réessayez », sur tous les outils + OCR + dictée)
- [x] Robustesse de l'indexation RAG (chaque lot protégé + vérif d'intégrité ; jamais de base à moitié construite en silence)

## Phase 6 — Cosmétique / différé
- [x] Retirer le 'Français'/'4e' en dur — au-delà des 3 endroits : exemples en dur des 4 outils supprimés (bouton → « pas d'exemple disponible pour le moment »), défauts App.jsx retirés (matière/niveau = profil), table ABREV admin retirée. Commit 593073d.
- [ ] CRUD matières via l'admin
- [x] P4.8 — alignement des cartes — déjà fait antérieurement (confirmé par Harketti le 25/06). Cette case était restée [ ] à tort ; réouverture erronée annulée (modif App.jsx revertie). Leçon : vérifier l'état réel, pas se fier à une case périmée.
- [x] P4.9 — confirmation inline qui RESTE (toast écarté) : enregistrer un prompt → encadré rouge « Prompt modifié » (= personnalisé, ≠ défaut) ; revenir au défaut → encadré vert « Prompt remis au défaut ».
- [x] Cleanup préfixe RAG mort (_build_rag_prefix)
- [x] Sortir ChromaDB du git (rebuild au déploiement) — *(ChromaDB **totalement éradiqué** le 29/06 → pgvector)*
- [x] Aide : expliquer que l'exemple varie, l'ancrage reste — fait 25/06. Tip « Créer une activité » (Aide.jsx) : « Tester un exemple » génère un extrait ancré sur le référentiel officiel du niveau → change à chaque clic mais reste fidèle au programme ; niveau sans référentiel = message + texte perso. Doublons du tip (Aide 301/693/731, App.jsx 845, dont Optimiseur/Ambiguïtés « en préparation ») laissés en l'état.
- [x] Étude : annexes de référentiels (ex. E6 BTS CIEL) — fait 25/06. CONCLUSION : RAG inchangé (PDF déjà ingéré en entier, filtrage option correct). Annexes scindées en enseignable (II/III → ancrent les activités de formation) vs évaluation/organisation (IV dont E6, V, VI → méta pour le RAG formation). E6 = évaluation pure → ne sert pas l'ancrage d'activités ; débouché = futur pilier « Mes évaluations » (TABLEAU item 46). Rien à changer côté RAG.

## Rappels transverses
- [x] Rectifier la doc d'archi : base réelle = SQLite — vérifié 25/06 (rien à corriger *alors*). **Caduc depuis le 27/06** : moteur cible = PostgreSQL (cf. ligne Phase 5 ci-dessus). **Migration moteur faite en local (Pas 1-11)** : la base locale est désormais **PostgreSQL** (`database.py` refuse SQLite) ; reste la **bascule prod** (Pas 13). La doc d'archi reflètera PostgreSQL une fois la prod basculée.
- [x] Groq conservé seulement pour Whisper / OCR

> Le bloc « Backlog écran Résultat généré » a été déplacé dans le réservoir du
> [TABLEAU-DE-BORD.md](TABLEAU-DE-BORD.md) → items **47** (éditer les réponses) et
> **48** (texte source éditable après génération). Le 25/06.
