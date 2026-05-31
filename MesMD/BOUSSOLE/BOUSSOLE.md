# aSchool — BOUSSOLE

> Vue d'ensemble. Détail dans chaque `Dxx.md` du dossier courant.
> Mise à jour : fin de chaque session.

**Date :** 2026-05-31 · **Version :** 3.2.9 · **Focus :** Dictée Groq batch stabilisée (Deepgram gelé)

---

## ▶️ Prochaine action (ouvre une nouvelle session ? lis ici en premier)

**Dictée vocale = stabilisée (31/05).** Retour à Groq Whisper batch + fix 400 + retour visuel temps réel (visualiseur de volume + chrono). Détail : [D15](D15.md). **Deepgram streaming = gelé**, isolé sur la branche `wip/deepgram-streaming` (amélioration future, rien perdu) → la Phase 3.2 / [D09](D09/D09.md) **n'est plus le focus**.

**Prochain chantier business** : reprendre [D12](D12.md) (Activité 100% fonctionnel) — la case « dictée » y est désormais cochée.

---

## Chantiers vivants — par ordre d'attaque

> Lit cette table de haut en bas. La première ligne = ce qu'on fait maintenant. Quand elle est close, elle disparaît et on attaque la suivante.

| Ordre | Item | État | Détail |
|---|---|---|---|
| 1 | **Dictée — Groq batch stabilisée** ✅ | Revert Deepgram→Groq batch + fix 400 + retour visuel (31/05) · Deepgram gelé sur `wip/deepgram-streaming` | [D15](D15.md) |
| 2 | **L37 Affinage séquence** (route à câbler) | Plumbing dormant · débloque D13 | [D07](D07.md) |
| 3 | 🎯 **PROD-BUSINESS — Activité 100% fonctionnel** | Tous angles (qualité + UX + pilotes + features) · attend D09 partiel pour case dictée | [D12](D12.md) |
| 4 | 🎯 **PROD-BUSINESS — Séquences 100% fonctionnel** | Tous angles · attend D07 cloturé | [D13](D13.md) |
| 5 | 🛠️ DOC — **Dégraissage TRACKER.md** (586 → ~150-200 lignes) | Session dédiée · non bloquant business | [D11](D11.md) |
| 6 | 🛠️ DOC — **Dégraissage duplications roadmap/pilotage Deepgram** | Session dédiée · non bloquant | [D10](D10.md) |

## Checklist avant modification

- [ ] Lire `FAIT ✅` du [TRACKER](../TRACKER.md) — la modif est peut-être déjà livrée
- [ ] Lire le fichier cible **complet**, pas le diff
- [ ] Vérifier que routes/paths/fonctions cités existent
- [ ] Confirmer avec l'équipe avant action destructive ou multi-fichiers

---

## Livré, à committer (fin de session 19/05)

- **D08** — Dette branding `school.afia.fr` → `aschool.fr` : 44/44 corrigées (24 le 18/05 déjà commitées + 20 `MesAdmin/` le 19/05 **à commit**). Voir [D08](D08.md). Commit ciblé : `chore(branding): finaliser MesAdmin/`.

## Fiches livrées + commitées (à archiver dans TRACKER FAIT lors du dégraissage D11)

D01 (L5 Analyseur de consignes) · D02 (Optimiseur inline) · D03 (INFRA-RAG DEV) · D04 (Groq fallback) · D05 (errorDialog + niveau header) — commités le 18/05/2026.

---

[TRACKER (39 items)](../TRACKER.md) · [CLAUDE.md (règles)](../../CLAUDE.md)
