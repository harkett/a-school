"""Preuve de raccordement — Slice 2a (endpoint /api/exemple-referentiel, génération ancrée).

Ce que le test PROUVE (Groq MOCKÉ — déterministe, pas « le code existe ») :
  1. Couple SUPPORTÉ (Réseaux × BTS CIEL option A) : le prompt envoyé au LLM CONTIENT
     les chunks CIEL option A que retrieve() remonte POUR CE COUPLE + le niveau →
     l'exemple est ancré sur le bon couple, pas inventé.
  2. Couple SANS référentiel (Français × 4e) : {available:false}, AUCUN appel LLM,
     AUCUN texte fabriqué (règle d'or).
  3. Sans cookie d'auth : 401.

Lancer : .\.venv\Scripts\python.exe -m pytest test_exemple_referentiel.py -q
"""
import os
import sys

# Windows : torch + chromadb → deux runtimes OpenMP. Sans ces garde-fous, l'embedding
# de la requête sous pytest plante en « access violation ». Posés AVANT tout import torch.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# --- BDD SQLite EN MÉMOIRE avant d'importer l'app (la vraie data/aschool.db n'est jamais ouverte) ---
import backend.database as dbmod
_mem = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
dbmod.engine = _mem
dbmod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_mem)

from backend import models_db
models_db.Base.metadata.create_all(bind=_mem)

from backend.main import app
from backend.auth import create_access_token
from backend.rag import retrieve
from backend.routers.exemple_referentiel import _resolve_collection
from fastapi.testclient import TestClient

assert "memory" in str(dbmod.engine.url), "SECURITE: engine non redirigé vers la mémoire"

NIVEAU_CIEL = "BTS CIEL option A"
TOKEN = create_access_token("prof.test@aschool.fr")


def _authed():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def test_couple_supporte_prompt_est_ancre_sur_le_bon_couple():
    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return "TEXTE SOURCE EXEMPLE (généré)"

    with patch("backend.routers.exemple_referentiel.generate", side_effect=fake_generate) as mock_gen:
        r = _authed().post("/api/exemple-referentiel",
                           json={"matiere": "Réseaux", "niveau": NIVEAU_CIEL})

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["available"] is True
    assert data["texte"] == "TEXTE SOURCE EXEMPLE (généré)"
    assert mock_gen.call_count == 1  # le LLM a bien été appelé une fois

    prompt = captured["prompt"]
    # Le couple est dans le prompt…
    assert NIVEAU_CIEL in prompt
    assert "Réseaux" in prompt
    # …et le prompt contient EXACTEMENT les chunks CIEL option A remontés pour ce couple.
    collection, filters = _resolve_collection(NIVEAU_CIEL)
    chunks = retrieve(collection, "Réseaux", filters=filters, top_k=4)
    assert chunks, "retrieve() ne remonte rien pour le couple"
    for c in chunks:
        assert c["source"] == "REF-BTS-CIEL-2023"      # bien du CIEL, pas du maths cycle 4
        assert c["text"][:60] in prompt                # le matériel du couple est injecté


def test_couple_sans_referentiel_ne_fabrique_rien():
    with patch("backend.routers.exemple_referentiel.generate") as mock_gen:
        r = _authed().post("/api/exemple-referentiel",
                           json={"matiere": "Français", "niveau": "4e"})

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["available"] is False
    assert data["texte"] is None
    assert mock_gen.call_count == 0  # AUCUN appel LLM, AUCUN texte fabriqué (règle d'or)


def test_exige_authentification():
    r = TestClient(app).post("/api/exemple-referentiel",
                             json={"matiere": "Réseaux", "niveau": NIVEAU_CIEL})
    assert r.status_code == 401
