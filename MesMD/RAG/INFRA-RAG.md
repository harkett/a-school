# INFRA-RAG — Pile RAG mutualisée

> **Statut :** ✅ pile RAG codée · le référentiel BTS CIEL (premier producteur) a été **retiré le 08/07/2026** (à régénérer via la procédure standard) · ❌ pas en prod
> **Effort restant :** moteur pgvector (PostgreSQL) en place + préchauffe modèle au boot faite ; reste le branchement des autres consommateurs
> **Nature :** prérequis transverse · hors numérotation L · alimente tous les producteurs et consommateurs RAG
> **Liens :** [TABLEAU DE BORD#infra-rag](../TABLEAU-DE-BORD.md#infra-rag) · producteur : un référentiel par couple matière+niveau (BTS CIEL retiré le 08/07, à régénérer) · futurs producteurs : [D23](../BOUSSOLE/D23.md) (DYS/FLE), [D17](../BOUSSOLE/D17.md) (équité), [D19](../BOUSSOLE/D19.md) (communication), [D22](../BOUSSOLE/D22.md) (créativité)

---

## Objectif

Fournir une pile RAG unique (PostgreSQL/pgvector + sentence-transformers + retrieve_pg) que chaque router de l'app peut appeler. **Une infra, plusieurs collections — pas un RAG par feature.**

La couche infrastructure est mutualisée ; seul change le corpus indexé, le prompt et les métadonnées selon le levier consommateur.

---

## Stack

- **PostgreSQL / pgvector** — table `referentiel_chunks` (colonne `embedding` `vector(1024)`) : ingestion + recherche cosinus dans [pgvector_store.py](../../backend/rag/pgvector_store.py)
- **sentence-transformers** `BAAI/bge-m3` (dim 1024) — singleton (voie directe `get_st_model`) dans [embeddings.py](../../backend/rag/embeddings.py)
- **Fonction générique** `retrieve_pg(collection_name, question, filters, top_k)` — [pgvector_store.py](../../backend/rag/pgvector_store.py)

Usage côté router consommateur :

```python
from backend.rag import retrieve_pg

chunks = retrieve_pg(
    collection_name="bebes_0_1_an",
    question="Activité d'éveil pour développer le langage chez un bébé",
    filters=None,
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
| Empreinte vecteurs en base (pgvector) | variable — voir agrégation par producteur (section ci-dessous, à remplir au fil des corpus indexés) |

**Goulot :** TPM Groq, jamais le VPS. Chaque requête RAG consomme ~7 000 tokens Groq (~4 000 de contexte + question + réponse).

### Empreinte disque agrégée par producteur (à remplir)

| Producteur | Collection | Docs indexés | Disque |
|---|---|---|---|
| Référentiel BTS CIEL | *(retiré le 08/07/2026)* | 0 — à régénérer | — |
| D23 | `corpus_inclusion_dys_fle` | 0 | — |
| D17 | `corpus_equite_laicite` | 0 | — |
| D19 | `corpus_communication_familles` | 0 | — |
| D22 | `corpus_creativite_pedagogique` | 0 | — |
| **Total prévisionnel à terme** | | ~150 docs | **~100-120 MB** |

---

## État actuel (15/05/2026 — fin de session test branchement)

| Composant | Statut |
|---|---|
| Code `pgvector_store.py` / `embeddings.py` | ✅ écrit + couvert par `test_rag_ingest_robuste.py` et `test_decoupage_creche.py` |
| Table `referentiel_chunks` peuplée | ⏳ collection BTS CIEL retirée le 08/07 (à régénérer via la procédure standard) |
| Test de raccordement | ✅ `test_exemple_referentiel.py` (reciblé crèche : couple → chunks ancrés) + `test_decoupage_creche.py` |
| Branchement à un router | ✅ `backend/pedagogie/exemple_referentiel.py` (endpoint « Tester un exemple », ancré sur le référentiel du couple) |
| Feature flag | ❌ retiré — la réforme a supprimé tout gating RAG de `generate.py` |
| Affichage chunks dans la réponse API | ✅ `GenerateResponse.chunks` (populé uniquement quand RAG actif) |
| Test canary diagnostic | ✅ outil `backend/rag/_canary_inject.py` (mode injection + `--remove`) — 15/05 |
| Wording préfixe RAG | ✅ renforcé 15/05 — bascule de "à utiliser comme référence" → "Tu DOIS ancrer..." avec demande citation explicite vocabulaire institutionnel |
| Logging applicatif (uvicorn) | ✅ `logging.basicConfig(INFO)` ajouté dans `backend/main.py` |
| Hébergement prod | ✅ PostgreSQL/pgvector — aucun fichier à héberger (vecteurs en base) |
| Pré-chargement modèle au boot (anti cold start ~38 s) | ✅ fait — préchauffe lifespan (`get_st_model`, `backend/main.py`) |

---

## Reste à faire

- [x] ~~Hébergement prod du `chroma_db/`~~ — sans objet : moteur **PostgreSQL/pgvector** (vecteurs en base, table `referentiel_chunks`), aucun dossier à héberger
- [x] ~~Premier branchement router~~ — fait : `exemple_referentiel.py` (endpoint « Tester un exemple »)
- [x] ~~Pré-charger sentence-transformers au boot FastAPI (lifespan)~~ — fait : préchauffe `get_st_model` dans le lifespan de `backend/main.py`
- [ ] Brancher les autres consommateurs : Cohérence curriculaire (D25), D23 (DYS/FLE), D17 (équité), D19 (communication), D22 (créativité) — collections différentes

---

## Risques techniques

- **TPM Groq saturation** : si plusieurs profs utilisent le RAG simultanément, Groq sature avant le VPS (scénario qui a causé le 413 du 15/05 sur l'optimiseur de séquence). Prévoir fallback via `backend/groq_client.py` + feature flag.
- **Empreinte disque cumulée** : à 5 collections producteurs, ~100-120 MB cumulés. Reste largement sous la marge VPS (250 GB) mais à surveiller dans le backoffice admin.
- **Maintenance du singleton modèle** : le modèle d'embedding est chargé une fois au boot FastAPI (préchauffe). Toute modification du modèle (changement de dimension par exemple) impose un re-index complet de `referentiel_chunks` (toutes collections).

---

## Position dans la décision d'architecture RAG

Voir [TABLEAU DE BORD](../TABLEAU-DE-BORD.md) section *« DÉCISION D'ARCHITECTURE — RAG »* :
- sous-section *« Pré-requis transverse — INFRA-RAG »* (cette fiche)
- section 1 *« Principe & infrastructure »* (règles transverses)
- section 3 *« Table active — Typologie pédagogique »* (qui consomme quoi)
