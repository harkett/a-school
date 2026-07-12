r"""Preuve — le modèle OCR n'est plus en dur dans src.

Avant : `body["model"] = "meta-llama/llama-4-scout-17b-16e-instruct"` était ÉCRIT EN DUR dans
transcribe_image (src/generator.py). C'était le seul vrai « en dur » métier hors fiche (audit 12/07).
Après : le modèle (et le max_tokens) viennent des PARAMÈTRES, résolus EN BASE par le backend
(get_ocr_model(db) / get_max_tokens(db, "ocr")) et passés à la fonction, qui reste pure.

Ce que ces tests PROUVENT :
  1. transcribe_image envoie à l'API le modèle et le max_tokens qu'on lui PASSE (pas une valeur en dur) ;
  2. un modèle vide -> erreur claire (jamais un appel API sans modèle) ;
  3. une clé vide -> erreur claire (comportement historique préservé).

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_ocr_model.py -q
"""
import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ROOT))   # racine projet -> `src` importable

import src.generator as gen
import backend.dictee.ocr as ocr_mod


def _fake_response():
    r = MagicMock()
    r.status_code = 200
    r.ok = True
    r.json.return_value = {"choices": [{"message": {"content": "TEXTE OCR"}}]}
    return r


def test_transcribe_image_utilise_le_modele_passe():
    """Le modèle ET le max_tokens envoyés à l'API sont ceux PASSÉS, pas une valeur en dur."""
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["body"] = json
        return _fake_response()

    with patch("requests.post", side_effect=fake_post):
        texte = gen.transcribe_image(
            b"\x89PNG_fake_bytes", "image/png",
            api_key="cle-test", model="modele-ocr-test-xyz", max_tokens=1234,
        )

    assert texte == "TEXTE OCR"
    assert captured["body"]["model"] == "modele-ocr-test-xyz"   # le modèle PASSÉ, pas un modèle en dur
    assert captured["body"]["max_tokens"] == 1234
    assert "meta-llama" not in captured["body"]["model"]        # plus aucune trace de l'ancien modèle en dur


def test_transcribe_image_refuse_modele_vide():
    """Modèle vide -> erreur claire (jamais un appel API sans modèle)."""
    with pytest.raises(RuntimeError):
        gen.transcribe_image(b"x", "image/png", api_key="cle-test", model="", max_tokens=100)


def test_transcribe_image_refuse_cle_vide():
    """Clé vide -> erreur claire (comportement historique préservé)."""
    with pytest.raises(RuntimeError):
        gen.transcribe_image(b"x", "image/png", api_key="", model="m", max_tokens=100)


def test_endpoint_ocr_passe_le_modele_de_la_base():
    """Câblage : l'endpoint /ocr passe à transcribe_image le modèle ET le max_tokens LUS EN BASE
    (get_ocr_model / get_max_tokens), jamais une valeur en dur. transcribe_image est mockée : ni
    Groq, ni base réelle — on prouve le BRANCHEMENT (la partie qu'un test prof aurait couverte)."""
    fake_file = MagicMock()
    fake_file.content_type = "image/png"
    fake_file.filename = "scan.png"

    async def _read():
        return b"\x89PNG_fake"
    fake_file.read = _read

    with patch.object(ocr_mod, "transcribe_image", return_value="TXT") as m_tr, \
         patch.object(ocr_mod, "get_cle_api", return_value="cle"), \
         patch.object(ocr_mod, "get_ocr_model", return_value="modele-base-xyz"), \
         patch.object(ocr_mod, "get_max_tokens", return_value=777):
        res = asyncio.run(ocr_mod.ocr(fake_file, db=MagicMock()))

    assert res == {"texte": "TXT"}
    _, kwargs = m_tr.call_args
    assert kwargs["model"] == "modele-base-xyz"   # modèle résolu EN BASE, passé par l'endpoint
    assert kwargs["max_tokens"] == 777            # max_tokens résolu EN BASE (get_max_tokens(db,"ocr"))
