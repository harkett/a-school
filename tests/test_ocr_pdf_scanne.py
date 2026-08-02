r"""Preuve — le bouton PDF lit AUSSI les PDF scannés (sans couche texte), via l'OCR image.

Avant : un PDF scanné était REJETÉ (422 « utilisez plutôt le bouton Image / Scan »). Maintenant
l'endpoint /ocr rend chaque page en image (pypdfium2) et la passe dans la MÊME OCR que le bouton
« Image / Scan » (transcribe_image, mockée ici : ni Groq, ni réseau, ni base réelle).

Ce que ces tests PROUVENT :
  1. PDF scanné (image sans texte) → OCR page par page, texte recollé ;
  2. PDF numérique (couche texte ≥ 50 car.) → extraction directe, AUCUNE OCR ;
  3. PDF scanné trop long → message HUMAIN (RÈGLE 23), aucune OCR lancée.

Lancer : docker compose exec backend python -m pytest tests/test_ocr_pdf_scanne.py -q
"""
import io
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

# engine / SessionLocal rediriges vers PostgreSQL (aschool_test) par conftest.py
import backend.core.database as dbmod
import backend.dictee.ocr as ocr_mod
import backend.securite.comptes as comptes
from backend.core.limiter import limiter
from backend.core.models_db import User
from backend.main import app

EMAIL_PROF = "prof.scan@college.fr"


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


# Ces tests appelaient la fonction ocr() DIRECTEMENT, avec un faux UploadFile. Ils sautaient
# donc la route, et avec elle l'authentification et le plafond ajoutes le 02/08/2026 — ils ne
# voyaient meme pas que la route etait ouverte a tout le monde. Ils passent desormais par HTTP,
# comme l'ecran : meme chemin, memes gardes, meme preuve de cablage.
def _client_connecte():
    db = dbmod.SessionLocal()
    db.add(User(email=EMAIL_PROF, password_hash="x", is_verified=True, prenom="Marie"))
    db.commit()
    db.close()
    limiter.reset()          # les compteurs vivent en memoire du process, entre les tests aussi
    c = TestClient(app)
    c.cookies.set("aschool_access", comptes.create_access_token(EMAIL_PROF))
    return c


def _envoyer(client, data: bytes):
    return client.post("/api/ocr", files={"file": ("doc.pdf", data, "application/pdf")})


def _mocks_base():
    """Patche la résolution EN BASE (clé/modèle/max_tokens) — ni base réelle, ni secret."""
    return (
        patch.object(ocr_mod, "get_cle_api", return_value="cle"),
        patch.object(ocr_mod, "get_ocr_model", return_value="modele-ocr"),
        patch.object(ocr_mod, "get_max_tokens", return_value=500),
    )


def test_pdf_scanne_passe_par_l_ocr_page_par_page():
    client = _client_connecte()
    data = _pdf_scanne(nb_pages=2)
    m_cle, m_mod, m_max = _mocks_base()
    with patch.object(ocr_mod, "transcribe_image", return_value="PAGE-OCR") as m_tr, m_cle, m_mod, m_max:
        reponse = _envoyer(client, data)
    assert reponse.status_code == 200, reponse.text
    res = reponse.json()
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

    client = _client_connecte()
    with patch("pdfplumber.open", return_value=_Doc()), \
         patch.object(ocr_mod, "transcribe_image") as m_tr:
        reponse = _envoyer(client, b"%PDF-fake")
    assert reponse.status_code == 200, reponse.text
    assert "Contenu numérique" in reponse.json()["texte"]
    m_tr.assert_not_called()                          # couche texte → jamais d'OCR


def test_pdf_scanne_trop_long_message_humain():
    client = _client_connecte()
    data = _pdf_scanne(nb_pages=ocr_mod._PDF_OCR_MAX_PAGES + 1)
    m_cle, m_mod, m_max = _mocks_base()
    with patch.object(ocr_mod, "transcribe_image") as m_tr, m_cle, m_mod, m_max:
        reponse = _envoyer(client, data)
    assert reponse.status_code == 422
    assert "plusieurs fois" in reponse.json()["detail"]  # message humain, actionnable — jamais technique
    m_tr.assert_not_called()                            # plafond franchi → aucune OCR lancée
