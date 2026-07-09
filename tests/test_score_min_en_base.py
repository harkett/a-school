r"""Preuve — le seuil de pertinence RAG vit EN BASE (`referentiels.score_min`), plus en dur.

Avant : `SCORE_MIN = 0.30` codé dans la fiche crèche, lu par `get_fiche(collection).SCORE_MIN`.
Après : colonne `referentiels.score_min`, lue par `_resolve_collection` et servie à la génération.
Règle « toute donnée métier en base ».

Ce que ce test PROUVE (base aschool_test) :
  1. `_resolve_collection` renvoie le seuil DE LA LIGNE `referentiels` (pas une constante).
  2. Une ligne créée sans seuil prend le défaut 0.30 (server_default) — la valeur historique préservée.

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_score_min_en_base.py -q
"""
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod
from backend.core.models_db import Cycle, Niveau, Referentiel
from backend.pedagogie.exemple_referentiel import _resolve_collection

NIVEAU = "Bébés (0-1 an)"
COLLECTION = "bebes_0_1_an"


def _couple(score_min=None):
    db = dbmod.SessionLocal()
    cy = Cycle(nom="Crèche", ordre=1); db.add(cy); db.flush()
    niv = Niveau(cycle_id=cy.id, nom=NIVEAU, ordre=1); db.add(niv); db.flush()
    kw = {} if score_min is None else {"score_min": score_min}
    db.add(Referentiel(niveau_id=niv.id, matiere_id=None, nom_fixe=COLLECTION,
                       collection=COLLECTION, filtres=None, fichier="referentiel.pdf", **kw))
    db.commit()
    db.close()


def test_resolve_collection_lit_le_seuil_en_base():
    _couple(score_min=0.55)                       # seuil explicite en base
    db = dbmod.SessionLocal()
    try:
        collection, filters, seuil = _resolve_collection(db, NIVEAU)
        assert collection == COLLECTION
        assert filters is None
        assert seuil == 0.55                      # vient de la ligne referentiels, pas d'une constante
    finally:
        db.close()


def test_score_min_defaut_030():
    _couple()                                     # aucun seuil fourni
    db = dbmod.SessionLocal()
    try:
        row = db.query(Referentiel).filter(Referentiel.collection == COLLECTION).first()
        assert row.score_min == 0.30              # server_default : valeur historique préservée
        _, _, seuil = _resolve_collection(db, NIVEAU)
        assert seuil == 0.30
    finally:
        db.close()
