r"""Preuve — les matieres candidates d'un couple vivent EN BASE (table `matieres_candidates`),
plus dans un fichier matieres-candidates.json.

Avant : `_lire_candidates(cycle_nom, niveau_nom)` lisait un fichier
REFERENTIELS/<CYCLE>/<NIVEAU>/matieres-candidates.json (qui n'existe pour aucun couple).
Apres : table `matieres_candidates` (une ligne par niveau), lue par `_lire_candidates(db, niveau_id)`.
Regle « toute donnee metier en base ».

Ce que ce test PROUVE (base aschool_test) :
  1. Aucune ligne pour le niveau -> `_lire_candidates` renvoie [] (comportement identique a l'ancien
     fichier absent) ET `etat_couple` renvoie candidates: [].
  2. Une ligne en base (matieres = tableau JSON) -> `_lire_candidates` renvoie la liste, et
     `etat_couple` la sert telle quelle.

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_matieres_candidates_en_base.py -q
"""
import json
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod
from backend.core.models_db import Cycle, Niveau, MatiereCandidate
from backend.pedagogie.referentiels_admin import _lire_candidates, etat_couple

CYCLE = "Crèche"
NIVEAU = "Bébés (0-1 an)"


def _couple(candidates=None):
    """Crée cycle + niveau ; si candidates fourni, une ligne matieres_candidates. Renvoie (cycle_id, niveau_id)."""
    db = dbmod.SessionLocal()
    try:
        cy = Cycle(nom=CYCLE, ordre=1); db.add(cy); db.flush()
        niv = Niveau(cycle_id=cy.id, nom=NIVEAU, ordre=1); db.add(niv); db.flush()
        if candidates is not None:
            db.add(MatiereCandidate(niveau_id=niv.id, matieres=json.dumps(candidates, ensure_ascii=False)))
        db.commit()
        return cy.id, niv.id
    finally:
        db.close()


def test_aucune_ligne_renvoie_liste_vide():
    cycle_id, niveau_id = _couple(candidates=None)   # aucune candidate en base
    db = dbmod.SessionLocal()
    try:
        assert _lire_candidates(db, niveau_id) == []
        etat = etat_couple(cycle_id=cycle_id, niveau=NIVEAU, db=db)
        assert etat["candidates"] == []
    finally:
        db.close()


def test_candidates_lues_depuis_la_base():
    noms = ["Langage", "Éveil sensoriel", "Motricité"]
    cycle_id, niveau_id = _couple(candidates=noms)
    db = dbmod.SessionLocal()
    try:
        assert _lire_candidates(db, niveau_id) == noms          # vient de la table, pas d'un fichier
        etat = etat_couple(cycle_id=cycle_id, niveau=NIVEAU, db=db)
        assert etat["candidates"] == noms
    finally:
        db.close()
