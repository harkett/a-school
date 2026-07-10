r"""Preuve — pas 2 du chantier 67 (bout 1) : la brique de RACCORD `doutes_ia` de la fiche crèche.

On prouve le RACCORD, pas la sortie du modèle : la brique générique `analyser_unites` est MOQUÉE.
- `doutes_ia` refait une unité `{titre, texte}` par chunk (titre = 2e ligne), appelle la brique,
  et renvoie le verdict `doute` ALIGNÉ sur l'ordre des chunks.
- Garde-fou : une unité sans verdict de l'IA est comptée douteuse (True) — jamais un passage muet.
Le chemin en service (`apercu_unites`) n'est PAS touché ici (il utilise encore `_age_est_flou`).

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_doutes_ia_creche.py -q
"""
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.rag.analyse_amont as aamod
import backend.rag.referentiels.creche_0_3_ans as fiche

CHUNKS = [
    {"text": "Âge : 0-1 an\nComptine du matin\nChanter en portant l'enfant.", "meta": {"age": ["0-1"]}},
    {"text": "Âge : dès ~2 ans\nCréer ses propres livres\npapier, crayons.", "meta": {"age": []}},
]


def test_doutes_ia_aligne_sur_les_chunks(monkeypatch):
    capture = {}

    def fake(unites, *, db):
        capture["unites"] = unites
        return {"regle": "classement par âge", "unites": [
            {"index": 0, "classe": ["0-1"], "doute": False, "raison": ""},
            {"index": 1, "classe": [], "doute": True, "raison": "âge imprécis"},
        ]}

    monkeypatch.setattr(aamod, "analyser_unites", fake)
    out = fiche.doutes_ia(CHUNKS, db=None)

    # verdict aligné sur l'ordre des chunks
    assert out == [False, True]
    # la brique a bien reçu titre (2e ligne) + texte (le chunk entier)
    assert capture["unites"][0]["titre"] == "Comptine du matin"
    assert "Chanter" in capture["unites"][0]["texte"]
    assert capture["unites"][1]["titre"] == "Créer ses propres livres"


def test_doutes_ia_unite_sans_verdict_comptee_douteuse(monkeypatch):
    # l'IA n'a rendu un verdict que pour l'unité 0 -> l'unité 1 est comptée douteuse (garde-fou)
    monkeypatch.setattr(aamod, "analyser_unites",
                        lambda unites, *, db: {"regle": "x",
                                               "unites": [{"index": 0, "classe": [], "doute": False}]})
    out = fiche.doutes_ia(CHUNKS, db=None)
    assert out == [False, True]
