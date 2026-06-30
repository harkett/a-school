"""Garde-fou « sauvegarde avant purge » des chunks RAG (caillou 7).

Verifie, SANS PostgreSQL (db factice -> aucune connexion), que
`_sauvegarder_chunks_avant_purge` :
- ecrit un dump JSONL horodate (*.bak-*) quand des chunks existent, avec le bon
  nombre de lignes et un contenu fidele (round-trip) ;
- ne cree aucun fichier quand il n'y a rien a ecraser (0 chunk).

La sauvegarde est appelee AVANT le delete dans `ingest_pgvector` : si elle echoue,
elle RAISE et le delete n'est jamais atteint (garde-fou structurel, visible dans
`ingest_pgvector`). Ce module se lance hors suite normale via
`pytest test_rag_backup.py --noconftest` (le conftest racine, lui, se connecte a
aschool_test ; ici on n'en a pas besoin).
"""
import datetime as _dt
import json

import pytest

from backend.rag import pgvector_store


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeDB:
    """db minimal : execute(...).all() renvoie les rows fournies, ignore le select."""

    def __init__(self, rows):
        self._rows = rows

    def execute(self, _stmt):
        return _FakeResult(self._rows)


def test_sauvegarde_ecrit_dump_horodate(tmp_path, monkeypatch):
    monkeypatch.setattr(pgvector_store, "BACKUP_DIR", tmp_path)
    rows = [
        # (chunk_index, option_ab, page, texte, embedding, embedding_model)
        (0, "A", 12, "Texte du chunk zero", [0.1, 0.2, 0.3], "mini-lm"),
        (1, "A", 13, "Texte du chunk un", [0.4, 0.5, 0.6], "mini-lm"),
        (2, "B", 14, "Texte du chunk deux", [0.7, 0.8, 0.9], "mini-lm"),
    ]
    res = pgvector_store._sauvegarder_chunks_avant_purge(_FakeDB(rows), rid=42)

    assert res["lignes"] == 3
    fichiers = list(tmp_path.glob("referentiel_chunks-*.bak-*.jsonl"))
    assert len(fichiers) == 1, "un seul dump horodate attendu"

    lignes = fichiers[0].read_text(encoding="utf-8").splitlines()
    assert len(lignes) == 3
    premier = json.loads(lignes[0])
    assert premier["referentiel_id"] == 42
    assert premier["chunk_index"] == 0
    assert premier["option_ab"] == "A"
    assert premier["page"] == 12
    assert premier["texte"] == "Texte du chunk zero"
    assert premier["embedding"] == [0.1, 0.2, 0.3]
    assert premier["embedding_model"] == "mini-lm"


def test_sauvegarde_zero_chunk_n_ecrit_rien(tmp_path, monkeypatch):
    monkeypatch.setattr(pgvector_store, "BACKUP_DIR", tmp_path)
    res = pgvector_store._sauvegarder_chunks_avant_purge(_FakeDB([]), rid=42)

    assert res["lignes"] == 0
    assert list(tmp_path.glob("*.bak-*")) == []


def test_sauvegarde_refuse_d_ecraser_un_bak_existant(tmp_path, monkeypatch):
    monkeypatch.setattr(pgvector_store, "BACKUP_DIR", tmp_path)

    # Horodatage fige -> les deux appels visent EXACTEMENT le meme nom de fichier,
    # ce qui simule une collision (meme microseconde).
    fixe = _dt.datetime(2026, 6, 30, 12, 0, 0, 0)

    class _FixedDatetime:
        @staticmethod
        def now():
            return fixe

    monkeypatch.setattr(pgvector_store, "datetime", _FixedDatetime)
    rows = [(0, "A", 1, "texte", [0.1, 0.2], "mini-lm")]

    # 1er backup : ecrit normalement.
    pgvector_store._sauvegarder_chunks_avant_purge(_FakeDB(rows), rid=1)
    # 2e backup au meme nom : REFUS (mode "x") -> ne doit jamais ecraser le 1er.
    with pytest.raises(FileExistsError):
        pgvector_store._sauvegarder_chunks_avant_purge(_FakeDB(rows), rid=1)

    # Le 1er backup est intact, un seul fichier existe.
    assert len(list(tmp_path.glob("*.bak-*"))) == 1
