"""Garde-fou « sauvegarde avant purge » des chunks RAG (caillou 7).

Verifie, SANS PostgreSQL (db factice -> aucune connexion), que
`_sauvegarder_chunks_avant_purge` :
- ecrit un dump JSONL horodate (*.bak-*) quand des chunks existent, avec le bon
  nombre de lignes et un contenu fidele (round-trip) ;
- ne cree aucun fichier quand il n'y a rien a ecraser (0 chunk).

La sauvegarde est appelee AVANT le delete dans `ingest_pgvector` : si elle echoue,
elle RAISE et le delete n'est jamais atteint (garde-fou structurel, visible dans
`ingest_pgvector`). Ce module se lance hors suite normale via
`pytest test_rag_sauvegarde_avant_purge.py --noconftest` (le conftest racine, lui, se connecte a
aschool_test ; ici on n'en a pas besoin).

Lancer : docker compose exec backend python -m pytest tests/test_rag_sauvegarde_avant_purge.py -q
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
        # (chunk_index, option_ab, annee, page, texte, embedding, embedding_model,
        #  document_id, portee, valide_du, valide_au)
        (0, "A", "4e", 12, "Texte du chunk zero", [0.1, 0.2, 0.3], "bge-m3",
         7, "matiere", _dt.date(2026, 8, 1), None),
        (1, "A", None, 13, "Texte du chunk un", [0.4, 0.5, 0.6], "bge-m3",
         7, "formation", _dt.date(2026, 8, 1), None),
        (2, "B", None, 14, "Texte du chunk deux", [0.7, 0.8, 0.9], "bge-m3",
         7, "matiere", _dt.date(2026, 8, 1), _dt.date(2026, 9, 1)),
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
    # L'ANNÉE EST DANS LE DUMP. Sans elle, une restauration rendrait toutes les unités communes
    # à tout le cycle : le marquage disparaîtrait en silence, et le prof recevrait de nouveau
    # le contenu des autres années.
    assert premier["annee"] == "4e"
    assert json.loads(lignes[1])["annee"] is None
    assert premier["page"] == 12
    assert premier["texte"] == "Texte du chunk zero"
    assert premier["embedding"] == [0.1, 0.2, 0.3]
    assert premier["embedding_model"] == "bge-m3"
    # LE DOCUMENT, LA PORTÉE ET LA PLAGE PARTENT AUSSI. Sans eux, une unité restaurée ne saurait
    # plus d'où elle vient ni ce qu'elle couvre — et la base la refuserait (NOT NULL).
    assert premier["document_id"] == 7
    assert premier["portee"] == "matiere"
    assert premier["valide_du"] == "2026-08-01"
    assert premier["valide_au"] is None
    assert json.loads(lignes[1])["portee"] == "formation"
    assert json.loads(lignes[2])["valide_au"] == "2026-09-01"


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
    rows = [(0, "A", None, 1, "texte", [0.1, 0.2], "bge-m3", 7, "matiere",
             _dt.date(2026, 8, 1), None)]

    # 1er backup : ecrit normalement.
    pgvector_store._sauvegarder_chunks_avant_purge(_FakeDB(rows), rid=1)
    # 2e backup au meme nom : REFUS (mode "x") -> ne doit jamais ecraser le 1er.
    with pytest.raises(FileExistsError):
        pgvector_store._sauvegarder_chunks_avant_purge(_FakeDB(rows), rid=1)

    # Le 1er backup est intact, un seul fichier existe.
    assert len(list(tmp_path.glob("*.bak-*"))) == 1
