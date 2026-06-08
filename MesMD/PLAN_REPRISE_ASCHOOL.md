# aSchool — Plan de reprise (document de travail)

> Document de conseil et de suivi. Claude analyse et conseille ; l'équipe décide et exécute.
> **FAIT** = livré et vérifié. **DÉCIDÉ** = tranché par toi. **[DÉCISION]** = reste à trancher.
> Version 3 — 31/05/2026 (intègre la clôture du chantier dictée).

---

## 1. Objectif

Reprendre sur de bonnes bases : **consolider le cœur du produit, valider ce qui est suspect tâche par tâche, puis rouvrir le push proprement.** Pas relancer l'ingénierie — sécuriser l'existant.

---

## 2. Acquis depuis la reprise

### ✅ FAIT — Chantier dictée (clôturé)
- **Cause de la panne d'origine prouvée** (repro empirique, pas hypothèse) : la 400 venait d'un **nom de fichier sans extension** envoyé à Groq (le blob MediaRecorder arrivait nommé « blob »). Ni un problème de qualité Whisper, ni un format incompatible (webm est accepté).
- **Cœur dictée recâblé en Groq Whisper batch**, fonctionnel en local, avec le double garde-fou (nom de fichier à extension `.webm` + `model` présent) et son test.
- **UX d'enregistrement améliorée** : barre animée temps réel (preuve de vie), chronomètre, message qui pose la bonne attente, état « transcription en cours » à l'arrêt.
- **Deepgram conservé en amélioration future**, isolé sur la branche `wip/deepgram-streaming` (récupérable, hors `main`, non poussé). Ce n'est plus un os actif.

> **Méthode validée au passage** : vérifier à la source → prouver la cause par une repro → fix minimal → test. C'est la cadence à garder pour tout le reste.

---

## 3. Vue globale (état réel)

**Solide :** le cœur — générer activités et séquences — est codé, câblé, cohérent en local. Une version stable tourne en prod pour de vrais profs. La dictée est désormais réparée et fonctionnelle en local.

**Ce qui sépare encore « codé » de « solide pour rouvrir le push » :**

1. **Aucun filet de test sur le cœur.** Les 5 endpoints centraux (`generate`, `generate-sequence`, `detect-ambiguites`, `analyser-consigne`, `optimize-sequence`) n'ont aucun test. Règle CLAUDE.md n°8. *Aggravé depuis le chantier dictée :* les tests Deepgram (7/7) sont partis sur la branche `wip/deepgram-streaming` → `main` n'a quasiment plus de test hors dictée. Le filet devient la priorité n°1.

2. **L'audit Activité du 15/05 a 9 cases non traitées**, dont une grave : auto-save sans try/catch → perte silencieuse d'activités possible, en prod.

3. **Build-ahead posé avant le besoin :** RAG (1 corpus sur 96, DEV uniquement) et le code dormant L37.

**Angle mort réel (non vérifié) :** le comportement **runtime** du cœur activité + séquence. L'app a tourné (port 8001) et la dictée a été observée, mais le golden path activité/séquence n'a pas encore été parcouru pour transformer ton « ça ne tient pas la route » en faits précis.

---

## 4. Principe de méthode

- **Vue globale d'abord, on ne s'éparpille pas.** Un point à la fois, fini avant le suivant.
- **Un « os » se met de côté, étiqueté, pour le jour venu** — il ne bloque pas la reprise.
- ⚠️ **Ce plan ré-ordonne volontairement la BOUSSOLE** (figée le 18/05 en mode ingénierie). L'objectif est la **consolidation**, pas l'ingénierie.

---

## 5. Décisions actées + os restant

### Décidé / Fait
| Sujet | État |
|---|---|
| Dictée — cœur | ✅ Groq Whisper batch recâblé + UX, fonctionnel local |
| Dictée — Deepgram | ✅ Isolé sur branche `wip/deepgram-streaming` (amélioration future) |

### Os restant (étiqueté, à rouvrir le jour venu)
| Os | Pourquoi enfoui | Rouvrir quand |
|---|---|---|
| **L37 / D07** (code dormant non commité, peut-être obsolète) | Tant qu'il dort, il ne nuit pas. Le câbler maintenant = travailler par-dessus du flou. | Quand on visera « Séquences 100% » (D13) avec l'affinage. |

### Contrainte aval (push)
Le push déploie `main` **en bloc** (`prod.ps1`). Le paysage des commits a changé depuis le gel (Deepgram parti sur branche, dictée recâblée sur `main`) — le **nombre exact de commits d'avance est à re-vérifier** avant la Phase 4. Le principe tient : on ne pousse que du validé + testé, Deepgram reste hors push.

---

## 6. Chronologie pour sortir du bourbier

> On ne passe à la phase suivante que quand le **critère de sortie** est atteint.

### Phase 0 — Voir la réalité ✅ TERMINÉE (31/05)
**Méthode :** double piste — UI jugée par l'humain (prof), API exercée en automatique (HTTP in-process, BDD mémoire, user fictif, zéro pollution de la vraie base).

**Résultat — le golden path TIENT au runtime. Aucun symptôme bloquant.**

| Case | UI (humain) | API (auto) |
|---|---|---|
| Générer activité | ✅ | ✅ 200 · 1,3 s |
| Sauvegarder activité | ✅ | ✅ save→reload intact |
| Export activité | ✅ | — (front only) |
| Générer séquence | ✅ | ✅ 200 · 2,7 s |
| Optimiser séquence | ⚠️ acceptable mais à améliorer (qualité) | ✅ 200 · 6,3 s |
| Save+reload séquence | ✅ | ✅ intact |
| detect-ambiguités / analyser-consigne | — | ✅ 200 |

**Seul point relevé (non bloquant) :** la sortie de l'**optimiseur de séquence** est jugée « acceptable mais à améliorer » → item de **qualité** à parker (à migrer vers TRACKER backlog), PAS un bug. Hors périmètre de la consolidation immédiate.

**Nuance auto-save (risque grave audit 15/05) :** le chemin de save côté **API est solide** (save→reload intact). Le trou est côté **FRONT sur le chemin d'ERREUR** (App.jsx : auto-save sans try/catch → perte silencieuse *si l'appel échoue*). C'est un point de **code front** pour la Phase 2.1, pas un symptôme runtime du happy path.

**Critère de sortie : ATTEINT** — golden path confirmé au runtime. Le « suspect » se réduit à : (1) qualité optimiseur (non bloquant, parké) + (2) durcissement front de l'auto-save (Phase 2.1).

### Phase 1 — Poser le filet de test sur le cœur ✅ TERMINÉE (31/05)
**But :** ne plus valider à l'aveugle (n°8). `main` était quasi sans test depuis le départ de Deepgram.
**Décision périmètre : (b)** happy path + cas d'erreur (le danger est sur le chemin d'erreur — cf. auto-save).
**Livré :** `test_endpoints_coeur.py` — **14/14 verts**, Groq mocké (zéro réseau), BDD mémoire (zéro pollution) :
- happy path 200 + sortie cohérente sur les 5 endpoints ;
- 401 (sans cookie + token invalide) ;
- 400 (thème / durée / mode invalides, entrées vides) + 422 (champ requis manquant) ;
- résilience Groq : fallback 429/413/503, non-fallback → 502, épuisement → 429, propagation 502 côté endpoint.
**Critère de sortie : ATTEINT** — les 5 endpoints ont un test vert en local, cas d'erreur verrouillés.

### Phase 2 — Traiter le suspect du cœur, sous filet, tâche par tâche
**Quoi, par ordre de gravité :**
1. ✅ **2.1 — auto-save sans try/catch (perte silencieuse)** — FAIT (31/05, sous filet) : helper `frontend/src/utils/activites.js` (lève sur échec réseau OU statut HTTP non-ok) + **modal d'alerte** dans `App.jsx` au lieu du `.catch(()=>{})` silencieux. Test `node --test` 4/4 ; filet backend toujours vert (14 à cette date — cf. correction baseline ci-dessous) ; build OK. Payload **inchangé** (contrat éprouvé). Reste : **vérif manuelle 30 s** (devtools offline → modal attendu + activité qui reste affichée).
2. Symptômes runtime trouvés en Phase 0 — *aucun bloquant* (golden path tient).
3. ✅ **Triage des 8 cases fait (31/05)** — 4 corriger (ordre **P3.4 → P3.6 → P5.11 → P3.5**), 2 sous-D (P4.7, P5.10), 2 garder/défer (P4.8, P4.9). Verdicts détaillés : TRACKER § AUDIT. Reste : exécuter le TEMPS 2 (corrections une par une, sous filet).
   - ✅ **P3.4 — FAIT (08/06)** : `/api/generate` ne passait pas par `call_groq` → except fourre-tout 500. Durci en `ValueError → 400` (clé inconnue) / `RuntimeError`+`RequestException` → 502 (Groq down) ; happy path inchangé. + 3 tests.
   - **Correction baseline filet** : le baseline réel était **14** tests (vérifié `git show HEAD`), pas 17 comme indiqué plus haut et dans le commit `fe97eff`. P3.4 le porte à **14 → 17 verts**. Prochain : P3.6, puis P5.11, puis P3.5.
Chaque point : reproduire → corriger → test vert → validé. Verdict **par point** (garder / corriger / abandonner).
**Critère de sortie :** plus de symptôme bloquant sur le golden path activité + séquence (L1+L3) ; filet vert.

### Phase 3 — Geler proprement le build-ahead
- **RAG** : laisser en DEV / désactivé (`RAG_ENABLED=false`). Hébergement = décision reportée.
- **L37 / D07** : trancher le sort du code dormant **[DÉCISION]** — (a) commit WIP, (b) branche WIP, (c) suppression. Reco : ne pas câbler maintenant ; isoler (b) ou étiqueter (a).
**Critère de sortie :** plus de code dormant ambigu dans le périmètre de reprise.

### Phase 4 — Rouvrir le push
**Quoi :** une fois le cœur validé + testé, re-vérifier le nombre de commits d'avance, puis décider du franchissement, **Deepgram restant hors push**.
**[DÉCISION]** : tout valider en bloc puis push, ou isoler le sous-ensemble validé.
**Critère de sortie :** prod à jour avec uniquement du code validé + testé.

---

## 7. Ce que je ne sais pas (à dire franchement)

- ~~Le comportement runtime du cœur activité + séquence.~~ **Vérifié en Phase 0 (31/05) : le golden path tient.** Le « suspect » se réduit à la qualité de l'optimiseur (à améliorer, non bloquant) + le durcissement front de l'auto-save (Phase 2.1).
- **Le nombre exact de commits d'avance** après le chantier dictée — à re-vérifier dans git avant la Phase 4.
- **Le poids exact du streaming** pour tes profs (pour décider, un jour, de rouvrir Deepgram).

---

*Document de travail — à décortiquer en équipe. Claude conseille, l'équipe pilote.*
