"""Test de non-régression — dictée vocale (Groq Whisper batch).

Lance avec :  python test_transcribe.py   (ou via pytest si installé)

Garde-fou des DEUX causes historiques du 400 Groq sur /api/transcribe, vérifiées
de bout en bout à travers la vraie route FastAPI (aucun appel réseau — l'appel
HTTP sortant vers Groq est intercepté et inspecté) :

  1. NOM DE FICHIER À EXTENSION VALIDE — Groq détermine le format par l'extension
     du nom de fichier. Un blob nommé « blob » (sans extension) → 400. Le backend
     doit donc TOUJOURS transmettre un nom à extension acceptée, même si le client
     envoie un nom sans extension.
  2. PARAMÈTRE `model` PRÉSENT — requis par l'API, 400 sinon. Doit valoir
     whisper-large-v3 (modèle acté le 31/05/2026).
"""

import io
import sys

from fastapi.testclient import TestClient

import backend.groq_client as groq_client
from backend.main import app

# Extensions acceptées par l'endpoint Groq Whisper (doc officielle Speech-to-Text).
_ALLOWED_EXT = {"flac", "mp3", "mp4", "mpeg", "mpga", "m4a", "ogg", "opus", "wav", "webm"}


class _FakeResponse:
    ok = True
    status_code = 200

    @staticmethod
    def json():
        return {"text": "Bonjour, ceci est une dictee de test."}


def _install_groq_spy():
    """Remplace requests.post (dans groq_client) par un espion qui capture l'appel
    sortant vers Groq sans rien envoyer sur le réseau. Renvoie (captured, restore)."""
    captured = {}
    original_post = groq_client.requests.post

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["files"] = kwargs.get("files")
        captured["data"] = kwargs.get("data")
        return _FakeResponse()

    groq_client.requests.post = fake_post

    def restore():
        groq_client.requests.post = original_post

    return captured, restore


def _post_audio(client, filename, content_type):
    """POST un faux fichier audio sur /api/transcribe et renvoie la réponse."""
    files = {"file": (filename, io.BytesIO(b"\x1aE\xdf\xa3 fake audio bytes"), content_type)}
    return client.post("/api/transcribe", files=files)


def _assert_groq_call_valid(captured, contexte):
    """Vérifie les DEUX garde-fous sur l'appel capturé vers Groq."""
    # Garde-fou 1 : nom de fichier transmis à Groq avec extension valide.
    sent_filename = captured["files"]["file"][0]
    assert "." in sent_filename, f"[{contexte}] nom de fichier sans extension : {sent_filename!r}"
    ext = sent_filename.rsplit(".", 1)[-1].lower()
    assert ext in _ALLOWED_EXT, f"[{contexte}] extension {ext!r} hors liste Groq"

    # Garde-fou 2 : paramètre model présent et égal au modèle acté.
    model = captured["data"].get("model")
    assert model == "whisper-large-v3", f"[{contexte}] model attendu whisper-large-v3, reçu {model!r}"

    # Sécurité : on tape bien l'endpoint transcriptions.
    assert captured["url"].endswith("/audio/transcriptions"), f"[{contexte}] URL inattendue : {captured['url']}"


def test_transcribe_nom_avec_extension():
    """Cas nominal : le navigateur envoie « dictee.webm » → 200 + texte inséré."""
    client = TestClient(app)
    captured, restore = _install_groq_spy()
    try:
        res = _post_audio(client, "dictee.webm", "audio/webm")
        assert res.status_code == 200, f"status {res.status_code} : {res.text}"
        assert res.json()["text"] == "Bonjour, ceci est une dictee de test."
        _assert_groq_call_valid(captured, "nom .webm")
    finally:
        restore()


def test_transcribe_nom_sans_extension_force_une_extension():
    """RÉGRESSION CŒUR : même si le client envoie « blob » (sans extension), le
    backend doit FORCER une extension valide avant de transmettre à Groq."""
    client = TestClient(app)
    captured, restore = _install_groq_spy()
    try:
        res = _post_audio(client, "blob", "audio/webm")
        assert res.status_code == 200, f"status {res.status_code} : {res.text}"
        _assert_groq_call_valid(captured, "nom 'blob' sans extension")
    finally:
        restore()


def test_transcribe_fichier_vide_refuse():
    """Un fichier vide est refusé proprement (400) — pas de 502 Groq."""
    client = TestClient(app)
    files = {"file": ("vide.webm", io.BytesIO(b""), "audio/webm")}
    res = client.post("/api/transcribe", files=files)
    assert res.status_code == 400, f"status {res.status_code} : {res.text}"


def _run():
    tests = [
        test_transcribe_nom_avec_extension,
        test_transcribe_nom_sans_extension_force_une_extension,
        test_transcribe_fichier_vide_refuse,
    ]
    echecs = 0
    for t in tests:
        try:
            t()
            print(f"OK   — {t.__name__}")
        except AssertionError as e:
            echecs += 1
            print(f"FAIL — {t.__name__} : {e}")
        except Exception as e:
            echecs += 1
            print(f"ERR  — {t.__name__} : {type(e).__name__}: {e}")
    print(f"\n{len(tests) - echecs}/{len(tests)} tests passés.")
    return echecs


if __name__ == "__main__":
    sys.exit(1 if _run() else 0)
