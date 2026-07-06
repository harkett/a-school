r"""Preuve de raccordement — référentiel BTS CIEL → RAG pgvector (remplace ChromaDB).

Ce que le test PROUVE (la chaîne réelle donne le bon résultat, pas « le code existe ») :
  1. La table referentiel_chunks est peuplée DEPUIS LE PDF officiel (ingest_pgvector).
  2. NON NÉGOCIABLE : chaque chunk porte le bon niveau (par jointure referentiel_id)
     et une option A/B — jamais un corpus qui mélangerait plusieurs référentiels.
  3. retrieve_pg() remonte bien du CIEL pour une requête du domaine (réseaux /
     cybersécurité) → le raccordement ingestion ↔ retrieve marche sur pgvector.

Base de test PostgreSQL dédiée (aschool_test via conftest.py) — JAMAIS SQLite, JAMAIS ChromaDB.
Le test sème le couple (Cycle→Niveau→Referentiel) puis lance la VRAIE ingestion
(PDF officiel + embeddings) : intégration lourde assumée (modèle torch chargé une fois).
Lancer : .\.venv\Scripts\python.exe -m pytest test_rag_ciel.py -q
"""
import os
import sys

# Windows : torch (sentence-transformers) embarque son runtime OpenMP (libiomp5md.dll).
# Sans ces garde-fous, l'embedding sous pytest plante en « access violation ».
# Posés AVANT tout import susceptible de charger torch.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from sqlalchemy import select, func

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod
from backend.core.models_db import Cycle, Niveau, Referentiel, ReferentielChunk
from backend.rag import retrieve_pg
from backend.rag.pgvector_store import ingest_pgvector

COLLECTION = "bts_ciel_option_a"
NIVEAU = "BTS CIEL option A"
SOURCE_CIEL = "REF-BTS-CIEL-2023"


def _seed_couple_ciel():
    """Sème Cycle→Niveau→Referentiel pour que ingest_pgvector/retrieve_pg trouvent le couple.
    Nettoyé par le TRUNCATE de conftest.py après le test."""
    db = dbmod.SessionLocal()
    try:
        cyc = Cycle(nom="Supérieur", ordre=6)
        db.add(cyc); db.flush()
        niv = Niveau(cycle_id=cyc.id, nom=NIVEAU, ordre=1, traite=True)
        db.add(niv); db.flush()
        db.add(Referentiel(niveau_id=niv.id, matiere_id=None, nom_fixe=NIVEAU,
                           collection=COLLECTION, filtres=None, source=SOURCE_CIEL))
        db.commit()
    finally:
        db.close()


def test_referentiel_ciel_bout_en_bout_sur_pgvector():
    # Un seul test : sème, lance la VRAIE ingestion (modèle chargé une fois), puis prouve tout.
    _seed_couple_ciel()
    rapport = ingest_pgvector()
    # 1. Peuplée depuis le PDF — 88 p. → bien plus que quelques chunks.
    assert rapport["inseres_en_base"] > 50, rapport

    db = dbmod.SessionLocal()
    try:
        n = db.scalar(select(func.count()).select_from(ReferentielChunk))
        assert n > 50

        # 2. Niveau (par jointure) + option A/B + embedding_model sur CHAQUE chunk.
        rows = db.execute(
            select(ReferentielChunk.option_ab, ReferentielChunk.embedding_model, Niveau.nom)
            .join(Referentiel, Referentiel.id == ReferentielChunk.referentiel_id)
            .join(Niveau, Niveau.id == Referentiel.niveau_id)
        ).all()
        assert rows, "aucun chunk en base — l'ingestion n'a pas tourné ?"
        assert all(niv == NIVEAU for _, _, niv in rows)         # niveau correct partout
        assert all(opt in ("A", "B") for opt, _, _ in rows)     # option taguée
        assert {opt for opt, _, _ in rows} == {"A", "B"}        # les deux présentes (découpage A/B)
        assert all(model for _, model, _ in rows)               # garde-fou embedding_model posé
    finally:
        db.close()

    # 3. La chaîne complète : question domaine → retrieve_pg → chunks du CIEL.
    chunks = retrieve_pg(
        COLLECTION,
        "Installer, exploiter et sécuriser un réseau informatique ; cybersécurité",
        top_k=4,
    )
    assert chunks, "retrieve_pg() ne remonte rien"
    assert all(c["source"] == SOURCE_CIEL for c in chunks)
    assert chunks[0]["score"] is not None
