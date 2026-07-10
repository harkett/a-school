r"""Preuve — pas 1 du chantier TRACKER 67 : la brique d'ANALYSE AMONT par l'IA, isolée.

On prouve la PLOMBERIE, jamais la sortie du modèle : `generate()` est MOQUÉ (aucun appel réel).
- `formater_unites` / `parser_reponse` : fonctions pures (ni IA ni base) → testées seules.
- `analyser_unites` : bâtit le bon prompt (contient les unités), passe les bons réglages
  (JSON déterministe, température 0), parse le JSON, et laisse remonter les pannes.
La brique n'est PAS branchée sur le découpage/ingestion (pas 1) : `_age_est_flou` vit encore.

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_analyse_amont.py -q
"""
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import pytest

import backend.core.database as dbmod
import backend.rag.analyse_amont as aamod
from backend.core.llm_prompts import PROMPTS
from src.generator import LLMRateLimitError

UNITES = [
    {"titre": "Créer ses propres livres", "texte": "Âge : dès ~2 ans\nMatériel : papier, crayons."},
    {"titre": "Comptine du matin", "texte": "Âge : 0-1 an\nChanter en portant l'enfant."},
]

REPONSE_JSON = (
    '{"regle": "classement par tranche d\'age",'
    ' "unites": ['
    '{"index": 0, "classe": [], "doute": true, "raison": "age imprecis"},'
    '{"index": 1, "classe": ["0-1"], "doute": false, "raison": ""}]}'
)


# ── Fonctions pures ───────────────────────────────────────────────────────────

def test_formater_unites_numerote_et_garde_titre_et_texte():
    out = aamod.formater_unites(UNITES)
    assert "[0] Créer ses propres livres" in out
    assert "dès ~2 ans" in out
    assert "[1] Comptine du matin" in out
    # ordre préservé : l'unité 0 avant l'unité 1
    assert out.index("[0]") < out.index("[1]")


def test_formater_unites_titre_optionnel():
    out = aamod.formater_unites([{"texte": "juste du texte"}])
    assert out.startswith("[0]")
    assert "juste du texte" in out


def test_parser_reponse_direct():
    assert aamod.parser_reponse(REPONSE_JSON)["regle"].startswith("classement")


def test_parser_reponse_dans_un_bloc_markdown():
    raw = "Voici le résultat :\n```json\n" + REPONSE_JSON + "\n```\nMerci."
    assert len(aamod.parser_reponse(raw)["unites"]) == 2


def test_parser_reponse_illisible_leve():
    with pytest.raises(ValueError):
        aamod.parser_reponse("désolé, pas de JSON ici")


# ── analyser_unites : generate() MOQUÉ ────────────────────────────────────────

def _mock_generate(monkeypatch, retour):
    """Remplace generate() dans le module (là où il est importé) et capture ses arguments."""
    capture = {}

    def fake(prompt, **kwargs):
        capture["prompt"] = prompt
        capture["kwargs"] = kwargs
        if isinstance(retour, Exception):
            raise retour
        return retour

    monkeypatch.setattr(aamod, "generate", fake)
    return capture


def test_analyser_unites_batit_le_prompt_et_parse(monkeypatch):
    capture = _mock_generate(monkeypatch, REPONSE_JSON)
    db = dbmod.SessionLocal()
    try:
        data = aamod.analyser_unites(UNITES, db=db)
    finally:
        db.close()
    # parse OK : la règle + le verdict par unité remontent
    assert data["regle"].startswith("classement")
    assert data["unites"][0]["doute"] is True and data["unites"][0]["raison"] == "age imprecis"
    assert data["unites"][1]["classe"] == ["0-1"] and data["unites"][1]["doute"] is False
    # le prompt envoyé contient bien les unités
    assert "dès ~2 ans" in capture["prompt"]
    assert "Comptine du matin" in capture["prompt"]
    # réglages : JSON déterministe
    assert capture["kwargs"]["json_mode"] is True
    assert capture["kwargs"]["temperature"] == 0
    assert capture["kwargs"]["provider"] and capture["kwargs"]["model"]


def test_analyser_unites_json_illisible_leve(monkeypatch):
    _mock_generate(monkeypatch, "le modèle a répondu en prose, pas de JSON")
    db = dbmod.SessionLocal()
    try:
        with pytest.raises(ValueError):
            aamod.analyser_unites(UNITES, db=db)
    finally:
        db.close()


def test_analyser_unites_rate_limit_remonte(monkeypatch):
    _mock_generate(monkeypatch, LLMRateLimitError("surchargé"))
    db = dbmod.SessionLocal()
    try:
        with pytest.raises(LLMRateLimitError):
            aamod.analyser_unites(UNITES, db=db)
    finally:
        db.close()


# ── Le prompt par défaut survit à .format() (garde-fou accolades JSON doublées) ─

def test_prompt_defaut_analyse_amont_formatable():
    tpl = PROMPTS["analyse_amont"]["default"]
    rendu = tpl.format(unites="[0] exemple\ntexte")
    assert "[0] exemple" in rendu
    assert '"regle"' in rendu   # l'exemple JSON a survécu (accolades doublées)
