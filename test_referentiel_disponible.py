"""Preuve de raccordement — endpoint /api/referentiel-disponible (le drapeau du garde-fou).

Ce que le test PROUVE (base de test aschool_test via conftest.py — JAMAIS SQLite) :
  1. Couple SANS référentiel → {disponible: false}.
  2. Référentiel couvrant tout le niveau (matiere_id NULL) → {disponible: true}
     quelle que soit la matière demandée.
  3. Référentiel propre à une matière → true pour CETTE matière, false pour une autre.

Lancer : python -m pytest test_referentiel_disponible.py -q
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import pytest

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.database as dbmod
from backend.main import app
from backend.models_db import Cycle, Niveau, Matiere, Referentiel
from fastapi.testclient import TestClient

client = TestClient(app)


def _seed(avec_referentiel=None):
    """Crée un cycle + niveau + deux matières. avec_referentiel :
       None            -> aucun référentiel
       'niveau'        -> un référentiel couvrant tout le niveau (matiere_id NULL)
       'matiere'       -> un référentiel propre à la matière 'Dev affectif'
       Renvoie le nom du niveau. Nettoyé par le TRUNCATE de conftest.py."""
    db = dbmod.SessionLocal()
    try:
        cyc = Cycle(nom="Crèche", ordre=7)
        db.add(cyc); db.flush()
        niv = Niveau(cycle_id=cyc.id, nom="Bébés (0-1 an)", ordre=1, traite=False)
        db.add(niv); db.flush()
        m1 = Matiere(nom="Développement affectif", ordre=1, actif=True)
        m2 = Matiere(nom="Motricité fine", ordre=2, actif=True)
        db.add_all([m1, m2]); db.flush()
        if avec_referentiel == "niveau":
            db.add(Referentiel(niveau_id=niv.id, matiere_id=None,
                               nom_fixe="ref_niveau", collection="ref_niveau"))
        elif avec_referentiel == "matiere":
            db.add(Referentiel(niveau_id=niv.id, matiere_id=m1.id,
                               nom_fixe="ref_mat", collection="ref_mat"))
        db.commit()
        return "Bébés (0-1 an)"
    finally:
        db.close()


def test_sans_referentiel_disponible_false():
    niveau = _seed(avec_referentiel=None)
    r = client.get("/api/referentiel-disponible",
                   params={"niveau": niveau, "matiere": "Développement affectif"})
    assert r.status_code == 200, r.text
    assert r.json() == {"disponible": False}


def test_referentiel_niveau_entier_disponible_true():
    niveau = _seed(avec_referentiel="niveau")
    r = client.get("/api/referentiel-disponible",
                   params={"niveau": niveau, "matiere": "Motricité fine"})
    assert r.status_code == 200, r.text
    assert r.json() == {"disponible": True}


def test_referentiel_matiere_specifique_true_pour_la_bonne_matiere():
    niveau = _seed(avec_referentiel="matiere")
    r = client.get("/api/referentiel-disponible",
                   params={"niveau": niveau, "matiere": "Développement affectif"})
    assert r.status_code == 200, r.text
    assert r.json() == {"disponible": True}


def test_referentiel_matiere_specifique_false_pour_une_autre_matiere():
    niveau = _seed(avec_referentiel="matiere")
    r = client.get("/api/referentiel-disponible",
                   params={"niveau": niveau, "matiere": "Motricité fine"})
    assert r.status_code == 200, r.text
    assert r.json() == {"disponible": False}
