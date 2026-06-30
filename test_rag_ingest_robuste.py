r"""Preuve de raccordement — filet de sécurité sur la construction de la base RAG (pgvector).

Ce que le test PROUVE (le filet agit vraiment, pas « le code existe ») — portage fidèle
des deux garde-fous d'ingest_pgvector, même couverture qu'avant ChromaDB :
  1. Embeddings en nombre != chunks -> arrêt NET (pgvector_store.py l.86-87), jamais une
     base remplie à partir d'un vecteur décalé.
  2. Base incomplète (moins de morceaux rangés qu'attendu) -> détectée et refusée
     (pgvector_store.py l.108-109), même si aucune écriture n'a levé d'erreur.
  3. Cas nominal : tout est rangé -> renvoie le rapport avec le bon compte.

PDF, embeddings ET session PostgreSQL MOQUÉS (aucun modèle lourd, aucune vraie base touchée).
Lancer : .\.venv\Scripts\python.exe -m pytest test_rag_ingest_robuste.py -q
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from unittest.mock import MagicMock, patch

import pytest

import backend.rag.pgvector_store as pg


def _chunks(n):
    return [{"text": f"morceau {i}", "page": 1, "meta": {"option": "A"}} for i in range(n)]


def _fake_pdf():
    """PDF factice : .exists() True (bypass le garde l.71) + .name pour le rapport."""
    p = MagicMock()
    p.exists.return_value = True
    p.name = "referentiel.pdf"
    return p


def _fake_db(rid, count_apres_insert, par_option=None):
    """Session moquée : db.scalar() -> [rid (resolve), count (vérif intégrité)] ;
    db.execute().all() -> agrégat par option (utilisé seulement au cas nominal)."""
    db = MagicMock()
    db.scalar.side_effect = [rid, count_apres_insert]
    db.execute.return_value.all.return_value = list((par_option or {}).items())
    return db


def test_embeddings_decales_arret_clair():
    # 3 chunks mais 2 vecteurs -> garde-fou l.86-87 : on s'arrête avant toute écriture.
    with patch.object(pg, "build_chunks_from_pdf", return_value=_chunks(3)), \
         patch.object(pg, "embed_texts", return_value=[[0.0], [0.0]]), \
         patch.object(pg.fiche, "PDF_PATH", _fake_pdf()):
        with pytest.raises(RuntimeError, match="Embeddings 2 != chunks 3"):
            pg.ingest_pgvector()


def test_base_incomplete_detectee():
    # 3 chunks insérés mais le compte en base renvoie 1 -> garde-fou l.108-109.
    db = _fake_db(rid=1, count_apres_insert=1)
    with patch.object(pg, "build_chunks_from_pdf", return_value=_chunks(3)), \
         patch.object(pg, "embed_texts", return_value=[[0.0]] * 3), \
         patch.object(pg, "SessionLocal", return_value=db), \
         patch.object(pg.fiche, "PDF_PATH", _fake_pdf()):
        with pytest.raises(RuntimeError, match="Incomplet"):
            pg.ingest_pgvector()


def test_cas_nominal_renvoie_le_rapport():
    # Tout est rangé (compte == nb de chunks) -> rapport renvoyé avec le bon total.
    db = _fake_db(rid=1, count_apres_insert=3, par_option={"A": 3})
    with patch.object(pg, "build_chunks_from_pdf", return_value=_chunks(3)), \
         patch.object(pg, "embed_texts", return_value=[[0.0]] * 3), \
         patch.object(pg, "SessionLocal", return_value=db), \
         patch.object(pg.fiche, "PDF_PATH", _fake_pdf()):
        rapport = pg.ingest_pgvector()
    assert rapport["inseres_en_base"] == 3
    assert rapport["par_option_en_base"] == {"A": 3}
