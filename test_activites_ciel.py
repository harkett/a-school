"""Preuve — les matières HORS catalogue (ex. BTS CIEL) ont un repli générique d'activités.

Ce que le test PROUVE :
  1. `/api/activites/<matière CIEL>` → 200 + liste NON VIDE (plus de 404, plus de mur
     « Sélectionnez un type », plus de crash `activites.find`).
  2. Une matière standard garde ses activités PROPRES (le repli ne déborde pas dessus).
  3. Le prompt générique se construit (texte + niveau, framing neutre — pas « français »),
     donc la génération marchera de bout en bout pour un prof BTS CIEL.

Lancer : .\.venv\Scripts\python.exe -m pytest test_activites_ciel.py -q
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.database as dbmod
_mem = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
dbmod.engine = _mem
dbmod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_mem)

from backend import models_db
models_db.Base.metadata.create_all(bind=_mem)

from backend.main import app
from src.prompts import build_prompt
from fastapi.testclient import TestClient

assert "memory" in str(dbmod.engine.url), "SECURITE: engine non redirigé vers la mémoire"

client = TestClient(app)


def test_matiere_ciel_hors_catalogue_repli_generique():
    r = client.get("/api/activites/Réseaux")
    assert r.status_code == 200, r.text          # plus de 404
    data = r.json()
    assert isinstance(data, list) and len(data) > 0
    keys = {a["key"] for a in data}
    assert "gen_comprehension" in keys


def test_matiere_du_catalogue_garde_ses_activites():
    r = client.get("/api/activites/Français")
    assert r.status_code == 200
    keys = {a["key"] for a in r.json()}
    assert "comprehension" in keys          # clé propre Français
    assert "gen_comprehension" not in keys  # le repli ne déborde pas sur les 12 matières


def test_prompt_generique_se_construit_et_est_neutre():
    p = build_prompt("gen_comprehension", "Un réseau informatique d'entreprise à sécuriser.",
                     nb=5, niveau="BTS CIEL option A")
    assert "Un réseau informatique" in p          # le texte source est dedans
    assert "BTS CIEL option A" in p               # le niveau est dedans
    assert "professeur de français" not in p.lower()  # framing neutre, pas Français
