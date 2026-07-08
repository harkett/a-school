r"""Preuve de raccordement — Slice 2a (endpoint /api/exemple-referentiel, génération ancrée).

Ce que le test PROUVE (Groq MOCKÉ — déterministe, pas « le code existe ») :
  1. Couple SUPPORTÉ (Langage × Bébés (0-1 an)) : le prompt envoyé au LLM CONTIENT
     les chunks que retrieve_pg() remonte POUR CE COUPLE + le niveau → ancré, pas inventé.
  2. Couple SANS référentiel (Français × 4e) : {available:false}, AUCUN appel LLM,
     AUCUN texte fabriqué (règle d'or).
  3. Sans cookie d'auth : 401.

Base de test PostgreSQL dédiée (aschool_test via conftest.py) — JAMAIS SQLite.
Lancer : python -m pytest test_exemple_referentiel.py -q
"""
import os
import sys

# Windows : torch embarque son runtime OpenMP. Sans ces garde-fous, l'embedding sous
# pytest plante en « access violation ». Posés AVANT tout import susceptible de charger torch.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from unittest.mock import patch

import pytest

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.main import app
from backend.auth import create_access_token
from backend.core.models_db import Cycle, Niveau, Referentiel
from backend.pedagogie.exemple_referentiel import AUCUN_EXTRAIT_PERTINENT
from fastapi.testclient import TestClient

NIVEAU_CRECHE = "Bébés (0-1 an)"
MATIERE = "Langage"
TOKEN = create_access_token("prof.test@aschool.fr")


def _authed():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


@pytest.fixture
def couple_creche():
    """Sème le couple Bébés (0-1 an) dans la base de test (aschool_test) pour que
    _resolve_collection (data-driven) le trouve. Nettoyé par le TRUNCATE de conftest.py."""
    db = dbmod.SessionLocal()
    try:
        cyc = Cycle(nom="Crèche", ordre=1)
        db.add(cyc); db.flush()
        niv = Niveau(cycle_id=cyc.id, nom=NIVEAU_CRECHE, ordre=1)
        db.add(niv); db.flush()
        db.add(Referentiel(niveau_id=niv.id, matiere_id=None, nom_fixe="Bébés (0-1 an)",
                           collection="bebes_0_1_an", filtres=None, source="dépôt manuel"))
        db.commit()
    finally:
        db.close()


def test_couple_supporte_prompt_est_ancre_sur_le_bon_couple(couple_creche):
    captured = {}
    # Chunks ancrés simulés (>= seuil crèche 0.30). On prouve la CHAÎNE : couple → chunks retenus →
    # injectés dans le prompt. PAS de chaîne de provenance figée (le endpoint ne lit ni source ni meta).
    chunks_ok = [
        {"text": "Jeu de coucou-caché pour développer la permanence de l'objet chez le bébé",
         "page": 3, "source": "dépôt manuel", "score": 0.61,
         "meta": {"source": "dépôt manuel", "option": "", "age": ["0-1"], "page": 3}},
        {"text": "Comptines et jeux de doigts pour éveiller le langage du tout-petit",
         "page": 5, "source": "dépôt manuel", "score": 0.48,
         "meta": {"source": "dépôt manuel", "option": "", "age": ["0-1"], "page": 5}},
    ]

    def fake_generate(prompt, **kwargs):  # **kwargs : accepte model= et futurs params
        captured["prompt"] = prompt
        return "TEXTE SOURCE EXEMPLE (généré)"

    with patch("backend.pedagogie.exemple_referentiel.retrieve_pg", return_value=chunks_ok), \
         patch("backend.pedagogie.exemple_referentiel.generate", side_effect=fake_generate) as mock_gen:
        r = _authed().post("/api/exemple-referentiel",
                           json={"matiere": MATIERE, "niveau": NIVEAU_CRECHE})

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["available"] is True
    assert data["texte"] == "TEXTE SOURCE EXEMPLE (généré)"
    assert mock_gen.call_count == 1

    prompt = captured["prompt"]
    assert NIVEAU_CRECHE in prompt        # le niveau est dans le prompt
    assert MATIERE in prompt              # la matière est dans le prompt
    for c in chunks_ok:                   # le matériel retenu (>= seuil) est injecté
        assert c["text"][:60] in prompt


def test_couple_sans_referentiel_ne_fabrique_rien():
    # Pas de fixture couple_creche → aucun référentiel en base → available=false, sans LLM.
    with patch("backend.pedagogie.exemple_referentiel.generate") as mock_gen:
        r = _authed().post("/api/exemple-referentiel",
                           json={"matiere": "Français", "niveau": "4e"})

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["available"] is False
    assert data["texte"] is None
    assert mock_gen.call_count == 0  # AUCUN appel LLM, AUCUN texte fabriqué (règle d'or)


def test_exige_authentification():
    r = TestClient(app).post("/api/exemple-referentiel",
                             json={"matiere": MATIERE, "niveau": NIVEAU_CRECHE})
    assert r.status_code == 401


def _chunk(text, score):
    return {"text": text, "page": 2, "source": "dépôt manuel", "score": score,
            "meta": {"option": "", "age": ["0-1"], "page": 2}}


def test_seuil_tout_sous_seuil_message_honnete_et_pas_de_generation(couple_creche):
    # Tous les chunks sous 0.30 (seuil crèche) → available=false, message C, generate JAMAIS appelé.
    faibles = [_chunk("bruit hors-sujet A", 0.15), _chunk("bruit hors-sujet B", 0.25)]
    with patch("backend.pedagogie.exemple_referentiel.retrieve_pg", return_value=faibles), \
         patch("backend.pedagogie.exemple_referentiel.generate") as mock_gen:
        r = _authed().post("/api/exemple-referentiel",
                           json={"matiere": MATIERE, "niveau": NIVEAU_CRECHE})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["available"] is False
    assert data["texte"] is None
    assert data["message"] == AUCUN_EXTRAIT_PERTINENT   # wording C exact
    assert mock_gen.call_count == 0                      # aucune activité sans ancrage


def test_seuil_filtre_les_chunks_faibles_avant_le_prompt(couple_creche):
    # Un chunk >= 0.30 (gardé) + un chunk < 0.30 (écarté) → génère avec le bon seulement.
    mixtes = [_chunk("VRAI CONTENU pertinent jeu d'eveil sensoriel", 0.55),
              _chunk("BRUIT administratif sous le seuil", 0.10)]
    captured = {}
    def fake_generate(prompt, **kwargs):
        captured["p"] = prompt
        return "EXEMPLE"
    with patch("backend.pedagogie.exemple_referentiel.retrieve_pg", return_value=mixtes), \
         patch("backend.pedagogie.exemple_referentiel.generate", side_effect=fake_generate) as mock_gen:
        r = _authed().post("/api/exemple-referentiel",
                           json={"matiere": MATIERE, "niveau": NIVEAU_CRECHE})
    assert r.status_code == 200, r.text
    assert r.json()["available"] is True
    assert mock_gen.call_count == 1
    assert "VRAI CONTENU pertinent jeu d'eveil" in captured["p"]       # gardé
    assert "BRUIT administratif sous le seuil" not in captured["p"]    # écarté
