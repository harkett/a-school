r"""Preuve — le bouton PDF lit AUSSI les PDF scannés (sans couche texte), via l'OCR image.

Avant : un PDF scanné était REJETÉ (422 « utilisez plutôt le bouton Image / Scan »). Maintenant
l'endpoint /ocr rend chaque page en image (pypdfium2) et la passe dans la MÊME OCR que le bouton
« Image / Scan » (transcribe_image, mockée ici : ni Groq, ni réseau, ni base réelle).

Ce que ces tests PROUVENT :
  1. PDF scanné (image sans texte) → OCR page par page, texte recollé ;
  2. PDF numérique (couche texte ≥ 50 car.) → extraction directe, AUCUNE OCR ;
  3. PDF scanné trop long → message HUMAIN (RÈGLE 23), aucune OCR lancée.

Lancer : python -m pytest tests/test_ocr_pdf_scanne.py -q
"""
import asyncio
import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from PIL import Image, ImageDraw


import backend.dictee.ocr as ocr_mod


def _pdf_scanne(nb_pages: int = 1) -> bytes:
    """PDF SANS couche texte : des images enregistrées en PDF (PIL). pdfplumber n'y lit aucun texte
    → déclenche le chemin OCR. Le contenu importe peu (transcribe_image est mockée)."""
    imgs = []
    for i in range(nb_pages):
        im = Image.new("RGB", (600, 300), "white")
        ImageDraw.Draw(im).text((20, 140), f"page {i + 1}", fill="black")
        imgs.append(im)
    buf = io.BytesIO()
    imgs[0].save(buf, format="PDF", save_all=True, append_images=imgs[1:])
    return buf.getvalue()


def _fake_pdf_file(data: bytes):
    f = MagicMock()
    f.content_type = "application/pdf"
    f.filename = "doc.pdf"

    async def _read():
        return data

    f.read = _read
    return f


def _mocks_base():
    """Patche la résolution EN BASE (clé/modèle/max_tokens) — ni base réelle, ni secret."""
    return (
        patch.object(ocr_mod, "get_cle_api", return_value="cle"),
        patch.object(ocr_mod, "get_ocr_model", return_value="modele-ocr"),
        patch.object(ocr_mod, "get_max_tokens", return_value=500),
    )


def test_pdf_scanne_passe_par_l_ocr_page_par_page():
    data = _pdf_scanne(nb_pages=2)
    m_cle, m_mod, m_max = _mocks_base()
    with patch.object(ocr_mod, "transcribe_image", return_value="PAGE-OCR") as m_tr, m_cle, m_mod, m_max:
        res = asyncio.run(ocr_mod.ocr(_fake_pdf_file(data), db=MagicMock()))
    assert res == {"texte": "PAGE-OCR\n\nPAGE-OCR"}   # une OCR par page, recollées
    assert m_tr.call_count == 2
    args, kwargs = m_tr.call_args
    assert args[1] == "image/png"                     # chaque page envoyée en image PNG
    assert kwargs["model"] == "modele-ocr"            # modèle résolu EN BASE, passé à l'OCR
    assert kwargs["max_tokens"] == 500


def test_pdf_numerique_extraction_directe_sans_ocr():
    """Couche texte présente (≥ 50 car.) → extraction pdfplumber directe, aucune OCR déclenchée."""
    class _Page:
        def extract_text(self):
            return "Contenu numérique lisible et suffisamment long pour dépasser le seuil. " * 2

    class _Doc:
        pages = [_Page()]

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with patch("pdfplumber.open", return_value=_Doc()), \
         patch.object(ocr_mod, "transcribe_image") as m_tr:
        res = asyncio.run(ocr_mod.ocr(_fake_pdf_file(b"%PDF-fake"), db=MagicMock()))
    assert "Contenu numérique" in res["texte"]
    m_tr.assert_not_called()                          # couche texte → jamais d'OCR


def test_pdf_scanne_trop_long_message_humain():
    data = _pdf_scanne(nb_pages=ocr_mod._PDF_OCR_MAX_PAGES + 1)
    m_cle, m_mod, m_max = _mocks_base()
    with patch.object(ocr_mod, "transcribe_image") as m_tr, m_cle, m_mod, m_max:
        with pytest.raises(HTTPException) as exc:
            asyncio.run(ocr_mod.ocr(_fake_pdf_file(data), db=MagicMock()))
    assert exc.value.status_code == 422
    assert "plusieurs fois" in exc.value.detail       # message humain, actionnable — jamais technique
    m_tr.assert_not_called()                          # plafond franchi → aucune OCR lancée
