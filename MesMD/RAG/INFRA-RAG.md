# INFRA-RAG — Pile RAG mutualisée

> **Statut :** ✅ codé en mode DEV · ✅ branché à `/api/generate` (15/05/2026) · ✅ Test 4 canary validé · ❌ pas en prod
> **Effort restant :** ~1 session (hébergement prod chroma_db + opti cold start + branchement autres consommateurs)
> **Nature :** prérequis transverse · hors numérotation L · alimente tous les producteurs et consommateurs RAG
> **Liens :** [BACKLOG#infra-rag](../BACKLOG.md#infra-rag) · producteurs : [L36](../LEVIERS/L36.md) (corpus MEN) · futurs producteurs : L30, L04, L31, L34

---

## Objectif

Fournir une pile RAG unique (ChromaDB + sentence-transformers + retrieve) que chaque router de l'app peut appeler. **Une infra, plusieurs collections — pas un RAG par feature.**

La couche infrastructure est mutualisée ; seul change le corpus indexé, le prompt et les métadonnées selon le levier consommateur.

---

## Stack

- **ChromaDB persistant** — singleton dans [client.py](../../backend/rag/client.py)
- **sentence-transformers** `paraphrase-multilingual-MiniLM-L12-v2` — singleton dans [embeddings.py](../../backend/rag/embeddings.py)
- **Fonction générique** `retrieve(collection_name, question, filters, top_k)` — [retrieve.py](../../backend/rag/retrieve.py)

Usage côté router consommateur :

```python
from backend.rag import retrieve

chunks = retrieve(
    collection_name="corpus_programmes_men",
    question="Que doit-on enseigner sur les identités remarquables en 3e ?",
    filters={"programme": "2020", "niveau": "3e"},
    top_k=4,
)
for c in chunks:
    print(c["text"], c["source"], c["page"], c["score"])
```

---

## Volumétrie infra (constante, indépendante des corpus)

| Élément | Valeur |
|---|---|
| Modèle en RAM (chargé une fois au boot) | ~120 MB |
| Embedding d'une requête (CPU) | ~30 ms |
| Recherche vectorielle top-k | ~30 ms |
| Latence ressentie totale (avec Groq) | ~2-4 s |
| Empreinte disque ChromaDB | variable — voir agrégation par producteur (section ci-dessous, à remplir au fil des corpus indexés) |

**Goulot :** TPM Groq, jamais le VPS. Chaque requête RAG consomme ~7 000 tokens Groq (~4 000 de contexte + question + réponse).

### Empreinte disque agrégée par producteur (à remplir)

| Producteur | Collection | Docs indexés | Disque |
|---|---|---|---|
| L36 | `corpus_programmes_men` | 1/96 (Maths cycle 4 via POC) | ~3 MB actuels, ~70-80 MB cible |
| L30 | `corpus_inclusion_dys_fle` | 0 | — |
| L04 | `corpus_equite_laicite` | 0 | — |
| L31 | `corpus_communication_familles` | 0 | — |
| L34 | `corpus_creativite_pedagogique` | 0 | — |
| **Total prévisionnel à terme** | | ~150 docs | **~100-120 MB** |

---

## État actuel (15/05/2026 — fin de session test branchement)

| Composant | Statut |
|---|---|
| Code `client.py` / `embeddings.py` / `retrieve.py` | ✅ écrit, testé manuellement |
| DB ChromaDB peuplée | ✅ partiellement (1 collection : `maths_cycle4`, 699 docs) |
| Test manuel `_test_retrieve.py` | ✅ OK (question identités remarquables 3e) |
| Branchement à un router | ✅ `backend/routers/generate.py` avec gates + fallback + logs INFO |
| Feature flag | ✅ `RAG_ENABLED` + `RAG_PROGRAMME_DEFAULT` + `RAG_DEBUG_PROMPT` (retiré après tests) |
| Affichage chunks dans la réponse API | ✅ `GenerateResponse.chunks` (populé uniquement quand RAG actif) |
| Test canary diagnostic | ✅ outil `backend/rag/_canary_inject.py` (mode injection + `--remove`) — 15/05 |
| Wording préfixe RAG | ✅ renforcé 15/05 — bascule de "à utiliser comme référence" → "Tu DOIS ancrer..." avec demande citation explicite vocabulaire institutionnel |
| Logging applicatif (uvicorn) | ✅ `logging.basicConfig(INFO)` ajouté dans `backend/main.py` |
| Hébergement prod | ❌ non décidé |
| Pré-chargement modèle au boot (anti cold start ~38 s) | ❌ pas fait — opti à venir |

---

## POC isolé `rag_demo/` (héritage — à supprimer)

Démo standalone (UI Flask sur `:8765`, indexait Maths cycle 4) ayant servi à valider la stack. Le code productif a été migré dans [backend/rag/](../../backend/rag/). **À supprimer après premier branchement router validé.**

---

## Reste à faire

- [ ] Choisir hébergement prod du `chroma_db/` (`/var/www/aSchool/backend/rag/chroma_db/` ?)
- [x] ~~Premier branchement router~~ — fait 15/05 sur `/api/generate`
- [x] ~~Feature flag `RAG_ENABLED`~~ — fait
- [x] ~~Affichage chunks dans la réponse API~~ — fait (`GenerateResponse.chunks`)
- [ ] Pré-charger sentence-transformers au boot FastAPI (lifespan) — éviter le cold start ~38 s sur la 1ʳᵉ requête RAG après démarrage
- [ ] Brancher les autres consommateurs : L1 (séquences), L25 (cohérence curriculaire), L30, L04, L31, L34 (collections différentes)
- [ ] Supprimer `rag_demo/` après validation (toujours en place)
- [ ] Décider du devenir de `backend/rag/_canary_inject.py` — conservé pour l'instant comme outil de diagnostic réutilisable (futurs producteurs)

---

## Risques techniques

- **TPM Groq saturation** : si plusieurs profs utilisent le RAG simultanément, Groq sature avant le VPS (scénario qui a causé le 413 du 15/05 sur l'optimiseur de séquence). Prévoir fallback via `backend/groq_client.py` + feature flag.
- **Empreinte disque cumulée** : à 5 collections producteurs, ~100-120 MB cumulés. Reste largement sous la marge VPS (250 GB) mais à surveiller dans le backoffice admin.
- **Maintenance des singletons** : le client ChromaDB et le modèle d'embedding sont chargés une fois au boot FastAPI. Toute modification du modèle (changement de dimension par exemple) impose un re-index complet de toutes les collections.

---

## Position dans la décision d'architecture RAG

Voir [BACKLOG](../BACKLOG.md) section *« DÉCISION D'ARCHITECTURE — RAG »* :
- sous-section *« Pré-requis transverse — INFRA-RAG »* (cette fiche)
- section 1 *« Principe & infrastructure »* (règles transverses)
- section 3 *« Table active — Typologie pédagogique »* (qui consomme quoi)
