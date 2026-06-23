# INFRA-RAG — Pile RAG mutualisée

> **Statut :** ✅ pile RAG codée et utilisée par l'exemple de référentiel (CIEL, BTS CIEL option A) · ❌ pas en prod
> **Effort restant :** hébergement prod chroma_db + opti cold start + branchement autres consommateurs
> **Nature :** prérequis transverse · hors numérotation L · alimente tous les producteurs et consommateurs RAG
> **Liens :** [TABLEAU DE BORD#infra-rag](../TABLEAU-DE-BORD.md#infra-rag) · producteur réalisé : référentiel CIEL (BTS CIEL option A, un référentiel par couple matière+niveau) · futurs producteurs : [D23](../BOUSSOLE/D23.md) (DYS/FLE), [D17](../BOUSSOLE/D17.md) (équité), [D19](../BOUSSOLE/D19.md) (communication), [D22](../BOUSSOLE/D22.md) (créativité)

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
    collection_name="bts_ciel_optionA",
    question="Installer et sécuriser un réseau informatique",
    filters={"option": "A"},
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
| Référentiel CIEL | `bts_ciel_optionA` | 236 chunks | ~3 MB |
| D23 | `corpus_inclusion_dys_fle` | 0 | — |
| D17 | `corpus_equite_laicite` | 0 | — |
| D19 | `corpus_communication_familles` | 0 | — |
| D22 | `corpus_creativite_pedagogique` | 0 | — |
| **Total prévisionnel à terme** | | ~150 docs | **~100-120 MB** |

---

## État actuel (15/05/2026 — fin de session test branchement)

| Composant | Statut |
|---|---|
| Code `client.py` / `embeddings.py` / `retrieve.py` | ✅ écrit, testé manuellement |
| DB ChromaDB peuplée | ✅ 1 collection : `bts_ciel_optionA`, 236 chunks |
| Test de raccordement | ✅ `test_rag_ciel.py` (niveau posé, retrieve remonte du CIEL) |
| Branchement à un router | ✅ `backend/routers/exemple_referentiel.py` (exemple de référentiel CIEL) |
| Feature flag | ❌ retiré — la réforme a supprimé tout gating RAG de `generate.py` |
| Affichage chunks dans la réponse API | ✅ `GenerateResponse.chunks` (populé uniquement quand RAG actif) |
| Test canary diagnostic | ✅ outil `backend/rag/_canary_inject.py` (mode injection + `--remove`) — 15/05 |
| Wording préfixe RAG | ✅ renforcé 15/05 — bascule de "à utiliser comme référence" → "Tu DOIS ancrer..." avec demande citation explicite vocabulaire institutionnel |
| Logging applicatif (uvicorn) | ✅ `logging.basicConfig(INFO)` ajouté dans `backend/main.py` |
| Hébergement prod | ❌ non décidé |
| Pré-chargement modèle au boot (anti cold start ~38 s) | ❌ pas fait — opti à venir |

---

## Reste à faire

- [ ] Choisir hébergement prod du `chroma_db/` (`/var/www/aSchool/backend/rag/chroma_db/` ?)
- [x] ~~Premier branchement router~~ — fait : `exemple_referentiel.py` (référentiel CIEL)
- [ ] Pré-charger sentence-transformers au boot FastAPI (lifespan) — éviter le cold start ~38 s sur la 1ʳᵉ requête RAG après démarrage
- [ ] Brancher les autres consommateurs : Cohérence curriculaire (D25), D23 (DYS/FLE), D17 (équité), D19 (communication), D22 (créativité) — collections différentes

---

## Risques techniques

- **TPM Groq saturation** : si plusieurs profs utilisent le RAG simultanément, Groq sature avant le VPS (scénario qui a causé le 413 du 15/05 sur l'optimiseur de séquence). Prévoir fallback via `backend/groq_client.py` + feature flag.
- **Empreinte disque cumulée** : à 5 collections producteurs, ~100-120 MB cumulés. Reste largement sous la marge VPS (250 GB) mais à surveiller dans le backoffice admin.
- **Maintenance des singletons** : le client ChromaDB et le modèle d'embedding sont chargés une fois au boot FastAPI. Toute modification du modèle (changement de dimension par exemple) impose un re-index complet de toutes les collections.

---

## Position dans la décision d'architecture RAG

Voir [TABLEAU DE BORD](../TABLEAU-DE-BORD.md) section *« DÉCISION D'ARCHITECTURE — RAG »* :
- sous-section *« Pré-requis transverse — INFRA-RAG »* (cette fiche)
- section 1 *« Principe & infrastructure »* (règles transverses)
- section 3 *« Table active — Typologie pédagogique »* (qui consomme quoi)
