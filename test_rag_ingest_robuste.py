r"""Preuve de raccordement — Phase 5 : filet de sécurité sur la construction de la base RAG.

Ce que le test PROUVE (le filet agit vraiment, pas « le code existe ») :
  1. Un lot qui échoue -> arrêt NET avec message clair (quel lot, quelle cause), jamais un
     retour silencieux qui laisserait croire que la base est complète.
  2. Base incomplète (moins de morceaux rangés qu'attendu) -> détectée et refusée, même si
     aucun lot n'a levé d'erreur.
  3. Cas nominal : tout est rangé -> renvoie le compte.

Client ChromaDB et embeddings MOQUÉS (aucun modèle lourd chargé, aucune vraie base touchée).

Lancer : .\.venv\Scripts\python.exe -m pytest test_rag_ingest_robuste.py -q
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from unittest.mock import MagicMock, patch

import pytest

import backend.rag.ingest_referentiel as ing


def _chunks(n):
    return [{"text": f"morceau {i}", "meta": {"option": "A", "page": 1}} for i in range(n)]


def _fake_client(col):
    client = MagicMock()
    client.list_collections.return_value = []      # collection absente -> pas de delete
    client.create_collection.return_value = col
    return client


def test_lot_echoue_arret_clair():
    col = MagicMock()
    col.add.side_effect = [None, Exception("boom embeddings")]  # 1er lot OK, 2e plante
    with patch.object(ing, "get_client", return_value=_fake_client(col)), \
         patch.object(ing, "get_embedding_function", return_value=MagicMock()):
        with pytest.raises(RuntimeError, match="Indexation interrompue"):
            ing.ingest(_chunks(70))                 # 70 morceaux -> 2 lots (BATCH=64)


def test_base_incomplete_detectee():
    col = MagicMock()
    col.add.return_value = None                     # aucun lot ne plante...
    col.count.return_value = 10                     # ...mais il manque des morceaux
    with patch.object(ing, "get_client", return_value=_fake_client(col)), \
         patch.object(ing, "get_embedding_function", return_value=MagicMock()):
        with pytest.raises(RuntimeError, match="incomplète"):
            ing.ingest(_chunks(70))


def test_cas_nominal_renvoie_le_compte():
    col = MagicMock()
    col.add.return_value = None
    col.count.return_value = 70                      # tout est bien rangé
    with patch.object(ing, "get_client", return_value=_fake_client(col)), \
         patch.object(ing, "get_embedding_function", return_value=MagicMock()):
        assert ing.ingest(_chunks(70)) == 70
