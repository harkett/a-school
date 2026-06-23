"""Preuve de raccordement — Slice 1 du Chantier B (référentiel BTS CIEL → RAG).

Ce que le test PROUVE (pas « le code existe » — la chaîne réelle donne le bon résultat) :
  1. La collection `bts_ciel_optionA` existe et est peuplée depuis le PDF officiel.
  2. NON NÉGOCIABLE : chaque chunk porte le bon `niveau` dès l'ingestion
     (jamais un corpus sans niveau qui mélangerait plusieurs référentiels).
  3. La fonction générique `retrieve()` remonte bien du CIEL pour une requête du
     domaine (réseaux / cybersécurité) → le raccordement ingestion ↔ retrieve marche.

Prérequis : la collection a été construite —
    .\.venv\Scripts\python.exe -m backend.rag.ingest_referentiel
Lancer :
    .\.venv\Scripts\python.exe -m pytest test_rag_ciel.py -q
"""
import os
import sys

# Windows : torch (sentence-transformers) et chromadb embarquent chacun libiomp5md.dll.
# Sans ces garde-fous, l'embedding de la requête sous pytest plante en « access
# violation » (deux runtimes OpenMP chargés). Posés AVANT tout import de torch.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from backend.rag.client import get_client
from backend.rag import retrieve

COLLECTION = "bts_ciel_optionA"
NIVEAU = "BTS CIEL option A"
SOURCE_CIEL = "REF-BTS-CIEL-2023"


def _metadatas(name):
    col = get_client().get_collection(name=name)
    return col.get(include=["metadatas"])["metadatas"]


def test_collection_existe_et_peuplee():
    col = get_client().get_collection(name=COLLECTION)
    # le référentiel fait 88 p. → bien plus que quelques chunks
    assert col.count() > 50


def test_niveau_pose_sur_chaque_chunk():
    metas = _metadatas(COLLECTION)
    assert metas, "collection vide — l'ingestion n'a pas tourné ?"
    # Non négociable : le niveau est posé DÈS l'ingestion, sur TOUS les chunks.
    assert all(m.get("niveau") == NIVEAU for m in metas)
    # L'option est taguée (A = option A + commun, B = sections spécifiques option B).
    assert all(m.get("option") in ("A", "B") for m in metas)
    # Le détecteur a bien trouvé les deux : sinon le découpage A/B est cassé.
    options = {m["option"] for m in metas}
    assert options == {"A", "B"}


def test_metadata_exactement_quatre_cles():
    # Verrou Phase 3 point 4 : la fiche ne pose QUE ces 4 clés de métadonnée.
    # `label`/`cycle` ont été retirés (écrits jamais lus). Échoue tant que la
    # collection n'a pas été ré-ingérée — c'est voulu (cohérence code ↔ base).
    metas = _metadatas(COLLECTION)
    assert metas, "collection vide — l'ingestion n'a pas tourné ?"
    attendu = {"source", "niveau", "option", "page"}
    assert all(set(m.keys()) == attendu for m in metas), \
        f"clés méta inattendues : {sorted({k for m in metas for k in m.keys()} - attendu)}"


def test_retrieve_generique_remonte_du_ciel():
    # La chaîne complète : question domaine → retrieve() → chunks du référentiel CIEL.
    chunks = retrieve(
        COLLECTION,
        "Installer, exploiter et sécuriser un réseau informatique ; cybersécurité",
        top_k=4,
    )
    assert chunks, "retrieve() ne remonte rien"
    assert all(c["source"] == SOURCE_CIEL for c in chunks)
    assert chunks[0]["score"] is not None
