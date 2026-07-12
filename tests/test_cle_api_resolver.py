r"""Preuve de raccordement — le résolveur de clé API par usage (get_cle_api).

Principe : le NOM de la variable d'environnement vit EN BASE (settings.cle_env_*),
la VALEUR (secret) reste dans le .env. get_cle_api lit le nom en base puis os.getenv.

Ce que le test PROUVE (jamais un vide silencieux — cap « aSchool n'invente rien ») :
  1. Nom présent en base + variable définie dans l'environnement -> renvoie la clé.
  2. Nom ABSENT de la base (migration non appliquée) -> HTTPException 500, message clair.
  3. Nom présent en base mais variable ABSENTE du .env -> HTTPException 500, message clair.

Aucune valeur de clé n'est écrite ni affichée : on utilise une fausse variable de test.

Lancer : .\.venv\Scripts\python.exe -m pytest test_cle_api_resolver.py -q
"""
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import pytest
from fastapi import HTTPException

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod
from backend.core.models_db import Setting
from backend.systeme.admin import get_cle_api


def _set_nom_en_base(cle_setting, nom_variable):
    db = dbmod.SessionLocal()
    db.query(Setting).filter(Setting.key == cle_setting).delete()
    db.add(Setting(key=cle_setting, value=nom_variable))
    db.commit()
    db.close()


def test_nom_en_base_et_variable_definie_renvoie_la_cle():
    _set_nom_en_base("cle_env_ocr", "CLE_TEST_BIDON_OCR")
    os.environ["CLE_TEST_BIDON_OCR"] = "valeur-factice-123"
    try:
        db = dbmod.SessionLocal()
        assert get_cle_api(db, "cle_env_ocr") == "valeur-factice-123"
        db.close()
    finally:
        os.environ.pop("CLE_TEST_BIDON_OCR", None)


def test_nom_absent_de_la_base_erreur_claire_500():
    # aucune ligne cle_env_ocr en base (aschool_test vidée entre tests)
    db = dbmod.SessionLocal()
    with pytest.raises(HTTPException) as exc:
        get_cle_api(db, "cle_env_ocr")
    db.close()
    assert exc.value.status_code == 500
    assert "cle_env_ocr" in exc.value.detail


def test_nom_en_base_mais_variable_absente_erreur_claire_500():
    _set_nom_en_base("cle_env_ocr", "VARIABLE_QUI_N_EXISTE_PAS_XYZ")
    os.environ.pop("VARIABLE_QUI_N_EXISTE_PAS_XYZ", None)
    db = dbmod.SessionLocal()
    with pytest.raises(HTTPException) as exc:
        get_cle_api(db, "cle_env_ocr")
    db.close()
    assert exc.value.status_code == 500
    assert "VARIABLE_QUI_N_EXISTE_PAS_XYZ" in exc.value.detail
