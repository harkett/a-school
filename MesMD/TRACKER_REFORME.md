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
- [ ] 4.1.e — bascule fournisseur — ⏸️ parqué (→ TRACKER_FOURNISSEURS_IA.md)
- [x] Interface admin qui lit/écrit les réglages
- [x] Validation des valeurs (modale bloquante)
- [x] Réglages rechargeables à chaud
- [ ] Prompts administrables en base

## Phase 5 — Robustesse / dette
- [ ] Régulation de concurrence sur les appels LLM
- [x] Unifier les migrations (plus d'ALTER inline)
- [ ] Décider : rester SQLite ou migrer PostgreSQL
- [ ] Code d'erreur 429 distinct (400/401/500/502 déjà là)
- [ ] Robustesse de l'indexation RAG (filet autour de col.add)

## Phase 6 — Cosmétique / différé
- [ ] Retirer le défaut 'Français' en dur (3 endroits frontend)
- [ ] CRUD matières via l'admin
- [ ] P4.8 — alignement des cartes
- [ ] P4.9 — toast à la réinitialisation des paramètres
- [x] Cleanup préfixe RAG mort (_build_rag_prefix)
- [x] Sortir ChromaDB du git (rebuild au déploiement)
- [ ] Aide : expliquer que l'exemple varie, l'ancrage reste
- [ ] Étude : annexes de référentiels (ex. E6 BTS CIEL)

## Rappels transverses
- [ ] Bascule Claude : vérifier température / mode JSON Opus dans l'adaptateur
- [ ] Rebrancher l'adaptateur Anthropic via claude -p à la bascule
- [ ] Rectifier la doc d'archi : base réelle = SQLite
- [x] Groq conservé seulement pour Whisper / OCR

## Backlog écran "Résultat généré" (réservoir, à déplacer plus tard)
- [ ] Éditer les réponses du résultat généré (crayon sur les réponses, pas le texte source)
- [ ] Texte source éditable après génération (résultat = photo, MAJ au clic "Régénérer")
