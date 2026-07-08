r"""Preuve — les matières HORS catalogue (ex. BTS CIEL) ont un repli générique d'activités.

Ce que le test PROUVE :
  1. `/api/activites/<matière CIEL>` → 200 + liste NON VIDE (plus de 404, plus de mur
     « Sélectionnez un type », plus de crash `activites.find`).
  2. INVARIANT (dispatch vivant `.get(matiere, GENERIC)`) : une matière QUI A son propre
     catalogue garde SES clés — le repli générique ne déborde pas dessus. Prouvé sur une
     matière dédiée injectée, car le catalogue réel est vide en attendant le RAG.
  3. Le prompt générique se construit (texte + niveau, framing neutre — pas « français »),
     donc la génération marchera de bout en bout pour un prof BTS CIEL.

Lancer : .\.venv\Scripts\python.exe -m pytest test_activites_ciel.py -q
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from unittest.mock import patch

import backend.contenu.activites as activites_mod
from backend.main import app
from src.prompts import build_prompt
from fastapi.testclient import TestClient

client = TestClient(app)


def test_matiere_ciel_hors_catalogue_repli_generique():
    r = client.get("/api/activites/Réseaux")
    assert r.status_code == 200, r.text          # plus de 404
    data = r.json()
    assert isinstance(data, list) and len(data) > 0
    keys = {a["key"] for a in data}
    assert "gen_comprehension" in keys


def test_repli_ne_deborde_pas_sur_une_matiere_du_catalogue():
    # INVARIANT sur le dispatch vivant `.get(matiere, GENERIC)` : une matière QUI A son propre
    # catalogue garde SES clés ; le repli générique ne déborde pas dessus. Le catalogue réel est
    # vide (contenu à venir du RAG) → on injecte une matière dédiée fictive le temps du test.
    catalogue_fictif = {
        "MatièreFictive": {"Type dédié": {"key": "dedie_test", "sous_types": [], "params": ["nb"]}},
    }
    with patch.object(activites_mod, "ACTIVITES_PAR_MATIERE", catalogue_fictif):
        keys = {a["key"] for a in client.get("/api/activites/MatièreFictive").json()}
        assert "dedie_test" in keys             # la matière garde SA clé dédiée
        assert "gen_comprehension" not in keys  # le repli générique ne déborde PAS dessus
        keys_absente = {a["key"] for a in client.get("/api/activites/MatièreInconnue").json()}
        assert "gen_comprehension" in keys_absente  # une matière absente retombe sur le repli


def test_prompt_generique_se_construit_et_est_neutre():
    p = build_prompt("gen_comprehension", "Un réseau informatique d'entreprise à sécuriser.",
                     nb=5, niveau="BTS CIEL option A")
    assert "Un réseau informatique" in p          # le texte source est dedans
    assert "BTS CIEL option A" in p               # le niveau est dedans
    assert "professeur de français" not in p.lower()  # framing neutre, pas Français
