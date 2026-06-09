# aSchool — BOUSSOLE

> Vue d'ensemble. Détail dans chaque `Dxx.md` du dossier courant.
> Mise à jour : fin de chaque session.

**Date :** 2026-06-09 · **Version :** 3.2.9 · **Focus :** Consolidation du cœur (filet de tests) avant réouverture du push

---

## 🧭 Règle de pilotage — un seul pilote

**La BOUSSOLE est le seul document qui pilote.** Aucun autre document n'a le droit de « ré-ordonner la boussole ». Tout plan, diagnostic ou audit ponctuel est **absorbé** ici en chantier `Dxx` — jamais un pilote concurrent. Réservoir d'idées = [BACKLOG](../BACKLOG.md). Les anciens états vivent dans l'**historique git**, pas dans un doc de l'arbre de travail.

**Périmètre de lecture = `main` uniquement.** Le contenu des autres branches (ex. `wip/deepgram-streaming` = chantier Deepgram gelé) n'est jamais lu spontanément : c'est du git, lecture **sur demande explicite** seulement. Pas de commande git large (`git grep --all`, `git log --all`, checkout d'une autre branche) de ma propre initiative.

---

## ▶️ Prochaine action (ouvre une nouvelle session ? lis ici en premier)

**Chantier actif = Consolidation du cœur ([D16](D16.md)).** Filet de tests posé (Phase 1, 17/17 verts), on traite le suspect **tâche par tâche, sous filet**. **Fait :** auto-save durci (2.1), P3.4 (`/api/generate` → 400/502). **Prochain : P3.6**, puis P5.11, puis P3.5 (verdicts : [BACKLOG](../BACKLOG.md) § AUDIT). Objectif final : rouvrir le push proprement, **Deepgram restant hors push**.

**Rappel :** dictée stabilisée (31/05, [D15](D15.md)) ; Deepgram gelé sur `wip/deepgram-streaming`.

---

## Chantiers vivants — par ordre d'attaque

> Lit cette table de haut en bas. La première ligne = ce qu'on fait maintenant. Quand elle est close, elle disparaît et on attaque la suivante.

| Ordre | Item | État | Détail |
|---|---|---|---|
| 1 | 🎯 **Consolidation du cœur** (filet de tests + suspect sous filet) | Phase 1 close (filet 17/17) · Phase 2 en cours (P3.4 ✅, reste P3.6→P5.11→P3.5) · récupère l'ex-PLAN_REPRISE | [D16](D16.md) |
| 2 | **L37 Affinage séquence** (route à câbler) | Plumbing dormant · débloque D13 | [D07](D07.md) |
| 3 | 🎯 **PROD-BUSINESS — Activité 100% fonctionnel** | Tous angles (qualité + UX + pilotes + features) · dictée livrée (D15) | [D12](D12.md) |
| 4 | 🎯 **PROD-BUSINESS — Séquences 100% fonctionnel** | Tous angles · attend D07 cloturé | [D13](D13.md) |
| 5 | 🛠️ DOC — **Dégraissage BACKLOG.md** (630 → ~150-200 lignes) | Session dédiée · non bloquant business | [D11](D11.md) |

## Checklist avant modification

- [ ] Lire `FAIT ✅` du [BACKLOG](../BACKLOG.md) — la modif est peut-être déjà livrée
- [ ] Lire le fichier cible **complet**, pas le diff
- [ ] Vérifier que routes/paths/fonctions cités existent
- [ ] Confirmer avec l'équipe avant action destructive ou multi-fichiers

---

## Fiches livrées + commitées (à archiver dans BACKLOG FAIT lors du dégraissage D11)

D01 (L5 Analyseur de consignes) · D02 (Optimiseur inline) · D03 (INFRA-RAG DEV) · D04 (Groq fallback) · D05 (errorDialog + niveau header) — commités le 18/05/2026. · D08 (branding `MesAdmin/` finalisé, 44/44) — commité le 19/05 (`cba2642`).

---

[BACKLOG (42 items)](../BACKLOG.md) · [CLAUDE.md (règles)](../../CLAUDE.md)
