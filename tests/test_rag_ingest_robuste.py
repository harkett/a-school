r"""Preuve de raccordement — filet de sécurité sur la construction de la base RAG (pgvector).

Ce que le test PROUVE (le filet agit vraiment, pas « le code existe ») — les deux garde-fous
d'intégrité d'ingest_pgvector, TOUJOURS présents dans le code actuel :
  1. Embeddings en nombre != chunks -> arrêt NET AVANT toute écriture
     (backend/rag/pgvector_store.py : `if len(vecs) != len(chunks): raise "Embeddings ..."`).
  2. Base incomplète (moins de morceaux rangés qu'attendu) -> détectée et refusée
     (`if n != len(chunks): raise "Incomplet ..."`), même si aucune écriture n'a levé d'erreur.
  3. Cas nominal : tout est rangé -> renvoie le rapport avec le bon compte.

AGNOSTIQUE AU RÉFÉRENTIEL : la fiche, le PDF, les embeddings ET la session PostgreSQL sont
MOQUÉS (aucun modèle lourd, aucune vraie base, aucun référentiel réel — ni BTS ni crèche).
On n'exerce que les garde-fous génériques, insensibles à la vie/mort d'une fiche.

Note d'historique : ces tests patchaient l'ANCIENNE API mono-fiche (`pg.fiche`,
`build_chunks_from_pdf`), disparue au passage socle+fiche. Réécrits ici sur l'API actuelle
(`get_fiche` local + `extract_pages` + `build_chunks`), en gardant la même couverture.

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_rag_ingest_robuste.py -q
"""
import os
import sys

# Windows : garde-fous OpenMP AVANT tout import susceptible de charger torch (via .embeddings).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from unittest.mock import MagicMock, patch

import pytest

import backend.rag.pgvector_store as pg


def _chunks(n):
    return [{"text": f"morceau {i}", "page": 1, "meta": {"option": "A"}} for i in range(n)]


def _fake_fiche():
    """Fiche factice AGNOSTIQUE. `spec` sans `filtrer_chunks` → `getattr(fiche, "filtrer_chunks",
    None)` renvoie None dans ingest_pgvector : aucun filtre par niveau appliqué (on ne teste que
    les garde-fous). extract_pages renvoie une page bidon (build_chunks est de toute façon moqué)."""
    f = MagicMock(spec=["extract_pages", "MAX_CHARS", "MIN_CHARS", "OVERLAP_CHARS",
                        "section_boundary", "chunk_metadata", "dedup_key"])
    f.extract_pages.return_value = [(1, "texte")]
    return f


def _fake_path():
    """PDF factice : .exists() True (passe le garde « PDF introuvable ») + .name pour le rapport."""
    p = MagicMock()
    p.exists.return_value = True
    p.name = "referentiel.pdf"
    return p


def _fake_db(count_en_base=None, par_option=None):
    """Session moquée : la résolution du référentiel renvoie un ref (id=1) ; db.scalar() -> le
    compte d'intégrité en base ; db.execute().all() -> l'agrégat par option (cas nominal)."""
    db = MagicMock()
    ref = MagicMock()
    ref.id = 1
    db.execute.return_value.scalar_one_or_none.return_value = ref      # résolution du référentiel
    db.execute.return_value.all.return_value = list((par_option or {}).items())  # agrégat par option
    db.scalar.return_value = count_en_base                             # vérif d'intégrité (n en base)
    return db


def test_embeddings_decales_arret_clair():
    # 3 chunks mais 2 vecteurs -> garde-fou : on s'arrête avant toute écriture.
    with patch.object(pg, "get_fiche", return_value=_fake_fiche()), \
         patch.object(pg, "_pdf_path_for", return_value=_fake_path()), \
         patch.object(pg, "SessionLocal", return_value=_fake_db()), \
         patch.object(pg, "build_chunks", return_value=_chunks(3)), \
         patch.object(pg, "embed_texts", return_value=[[0.0], [0.0]]):
        with pytest.raises(RuntimeError, match="Embeddings 2 != chunks 3"):
            pg.ingest_pgvector("collection-factice")


def test_base_incomplete_detectee():
    # 3 chunks insérés mais le compte en base renvoie 1 -> garde-fou « Incomplet ».
    with patch.object(pg, "get_fiche", return_value=_fake_fiche()), \
         patch.object(pg, "_pdf_path_for", return_value=_fake_path()), \
         patch.object(pg, "SessionLocal", return_value=_fake_db(count_en_base=1)), \
         patch.object(pg, "build_chunks", return_value=_chunks(3)), \
         patch.object(pg, "embed_texts", return_value=[[0.0]] * 3), \
         patch.object(pg, "_sauvegarder_chunks_avant_purge", return_value="(sauvegarde simulée)"):
        with pytest.raises(RuntimeError, match="Incomplet"):
            pg.ingest_pgvector("collection-factice")


def test_cas_nominal_renvoie_le_rapport():
    # Tout est rangé (compte == nb de chunks) -> rapport renvoyé avec le bon total.
    db = _fake_db(count_en_base=3, par_option={"A": 3})
    with patch.object(pg, "get_fiche", return_value=_fake_fiche()), \
         patch.object(pg, "_pdf_path_for", return_value=_fake_path()), \
         patch.object(pg, "SessionLocal", return_value=db), \
         patch.object(pg, "build_chunks", return_value=_chunks(3)), \
         patch.object(pg, "embed_texts", return_value=[[0.0]] * 3), \
         patch.object(pg, "_sauvegarder_chunks_avant_purge", return_value="(sauvegarde simulée)"):
        rapport = pg.ingest_pgvector("collection-factice")
    assert rapport["inseres_en_base"] == 3
    assert rapport["par_option_en_base"] == {"A": 3}
