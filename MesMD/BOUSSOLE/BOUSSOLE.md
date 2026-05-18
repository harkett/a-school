# aSchool — BOUSSOLE

> Vue d'ensemble. Détail dans chaque `Dxx.md` du dossier courant.
> Mise à jour : fin de chaque session.

**Date :** 2026-05-18 · **Version :** 3.2.9 · **Focus :** Deepgram Phase 3.2

---

## ▶️ Prochaine action (ouvre une nouvelle session ? lis ici en premier)

**Action immédiate : ligne 1 de "Chantiers vivants" ci-dessous = [D14](D14.md)** — commit accumulé en 7 groupes logiques. Une fois fait, D14 disparaît et la ligne 1 devient [D09](D09/D09.md) (runs vocaux Phase 3.2).

---

## Livré, à committer

| # | Date | Livraison | Détail |
|---|---|---|---|
| 1 | 14/05 | L5 Analyseur de consignes | [D01](D01.md) |
| 2 | 14/05 | Optimiseur inline + sidebar lean | [D02](D02.md) |
| 3 | 15/05 | INFRA-RAG branchée DEV | [D03](D03.md) |
| 4 | 15/05 | Groq fallback chain 413/503 | [D04](D04.md) |
| 5 | 14-15/05 | errorDialog modal + matière-niveau header | [D05](D05.md) |

## Chantiers vivants — par ordre d'attaque

> Lit cette table de haut en bas. La première ligne = ce qu'on fait maintenant. Quand elle est close, elle disparaît et on attaque la suivante.

| Ordre | Item | État | Détail |
|---|---|---|---|
| 1 | 📦 **Commit accumulé session 18/05** (7 groupes logiques) | Hygiène · doit passer avant D09 | [D14](D14.md) |
| 2 | **Chantier Deepgram Phase 3.2** | Phase 3.2 ouverte · runs vocaux R0→R6 · débloque dictée D12 + push v3.3.0 | [D09](D09/D09.md) |
| 3 | **L37 Affinage séquence** (route à câbler) | Plumbing dormant · débloque D13 | [D07](D07.md) |
| 4 | 🎯 **PROD-BUSINESS — Activité 100% fonctionnel** | Tous angles (qualité + UX + pilotes + features) · attend D09 partiel pour case dictée | [D12](D12.md) |
| 5 | 🎯 **PROD-BUSINESS — Séquences 100% fonctionnel** | Tous angles · attend D07 cloturé | [D13](D13.md) |
| 6 | **Branding MesAdmin** (~22 occurrences) | À traiter avant scale public (PLAN_LANCEMENT, DIFFUSION) | [D08](D08.md) |
| 7 | 🛠️ DOC — **Dégraissage TRACKER.md** (586 → ~150-200 lignes) | Session dédiée · non bloquant business | [D11](D11.md) |
| 8 | 🛠️ DOC — **Dégraissage duplications roadmap/pilotage Deepgram** | Session dédiée · non bloquant | [D10](D10.md) |

## Checklist avant modification

- [ ] Lire `FAIT ✅` du [TRACKER](../TRACKER.md) — la modif est peut-être déjà livrée
- [ ] Lire le fichier cible **complet**, pas le diff
- [ ] Vérifier que routes/paths/fonctions cités existent
- [ ] Confirmer avec l'équipe avant action destructive ou multi-fichiers

---

[TRACKER (39 items)](../TRACKER.md) · [CLAUDE.md (règles)](../../CLAUDE.md)
