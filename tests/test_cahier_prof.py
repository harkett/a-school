"""Dépôt du cahier des charges du prof — POST /api/user/cahier (chantier « cahier dans la génération »).

Ce que ces tests PROUVENT (Étape 1 — la donnée) :
  1. Déposer un PDF FIGE son texte épuré en base (cahiers_prof.texte_epure), extrait par LA porte
     unique rag.extraction (mockée ici) — c'est CE texte que la génération lira ensuite (get, zéro copie).
  2. Re-déposer REMPLACE le texte épuré (1 cahier par prof) : pas de doublon, pas de texte périmé.
  3. PDF illisible (extraction qui échoue) → message HUMAIN, AUCUN texte écrit (pas de demi-état).
  4. GET /api/user/cahier reflète l'état ; sans cookie d'auth : 401.

BDD de test PostgreSQL dédiée (aschool_test via conftest.py). Extraction mockée (déterministe).

Lancer : docker compose exec backend python -m pytest tests/test_cahier_prof.py -q
"""
from unittest.mock import patch


import backend.core.database as dbmod
from backend.main import app
from backend.securite.comptes import create_access_token
from backend.core.models_db import CahierProf, User
from fastapi.testclient import TestClient

EMAIL = "prof.cahier@aschool.fr"
TOKEN = create_access_token(EMAIL)

# Passe les gardes du endpoint (%PDF + non vide) ; l'extraction est mockée, le contenu n'a pas
# besoin d'être un vrai PDF analysable.
PDF_MINIMAL = b"%PDF-1.4\n%fake cahier\n"


def _client_avec_prof():
    with dbmod.SessionLocal() as db:
        from _profil import user_couple
        db.add(user_couple(db, email=EMAIL, password_hash="x", is_verified=True,
                    subject="CA-Matiere", niveau="CA-Niv"))
        db.commit()
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def _cahier_en_base():
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        return db.query(CahierProf).filter(CahierProf.user_id == u.id).first()


def test_depot_fige_le_texte_epure_en_base():
    c = _client_avec_prof()
    with patch("backend.rag.extraction.extraire_texte", return_value="RÈGLES DE L'ÉCOLE (épuré)"):
        r = c.post("/api/user/cahier",
                   files={"file": ("Mon cahier.pdf", PDF_MINIMAL, "application/pdf")})
    assert r.status_code == 200, r.text
    assert r.json() == {"present": True, "fichier": "Mon cahier.pdf"}
    cahier = _cahier_en_base()
    assert cahier is not None
    assert cahier.texte_epure == "RÈGLES DE L'ÉCOLE (épuré)"   # figé en base, lu ensuite par la génération


def test_redepot_remplace_le_texte_epure():
    c = _client_avec_prof()
    with patch("backend.rag.extraction.extraire_texte", return_value="ANCIEN"):
        c.post("/api/user/cahier", files={"file": ("v1.pdf", PDF_MINIMAL, "application/pdf")})
    with patch("backend.rag.extraction.extraire_texte", return_value="NOUVEAU"):
        r = c.post("/api/user/cahier", files={"file": ("v2.pdf", PDF_MINIMAL, "application/pdf")})
    assert r.status_code == 200, r.text
    assert r.json()["fichier"] == "v2.pdf"
    assert _cahier_en_base().texte_epure == "NOUVEAU"   # remplacement, pas de texte périmé
    with dbmod.SessionLocal() as db:                    # toujours UN seul cahier (user_id unique)
        u = db.query(User).filter(User.email == EMAIL).first()
        assert db.query(CahierProf).filter(CahierProf.user_id == u.id).count() == 1


def test_pdf_illisible_message_humain_et_aucun_texte():
    c = _client_avec_prof()
    with patch("backend.rag.extraction.extraire_texte", side_effect=Exception("boom pdfplumber")):
        r = c.post("/api/user/cahier", files={"file": ("ko.pdf", PDF_MINIMAL, "application/pdf")})
    assert r.status_code == 400, r.text
    detail = r.json()["detail"]
    assert "PDF" in detail and "déposer" in detail   # message humain, actionnable (règle des 2 publics)
    assert _cahier_en_base() is None                  # aucun demi-état écrit en base


def test_get_reflete_l_etat_et_exige_l_auth():
    c = _client_avec_prof()
    assert c.get("/api/user/cahier").json() == {"present": False, "fichier": None}
    with patch("backend.rag.extraction.extraire_texte", return_value="X"):
        c.post("/api/user/cahier", files={"file": ("c.pdf", PDF_MINIMAL, "application/pdf")})
    assert c.get("/api/user/cahier").json() == {"present": True, "fichier": "c.pdf"}
    assert TestClient(app).get("/api/user/cahier").status_code == 401
