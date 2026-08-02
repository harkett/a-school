r"""Preuve — /api/ocr et /api/transcribe ne sont plus ouvertes a tout le monde.

Ces deux routes DEPENSENT DE L'ARGENT a chaque appel : la dictee passe l'audio a Groq Whisper
(cle_env_dictee), l'OCR passe l'image a Groq Vision (cle_env_ocr) — et sur un PDF scanne, c'est
un appel modele PAR PAGE, jusqu'a 15 pour une seule requete.

Elles ne lisaient AUCUN cookie et n'avaient AUCUN plafond. N'importe qui, sans compte, pouvait
les appeler en boucle et vider les cles payantes du proprietaire. C'etaient les deux seules
routes couteuses dans ce cas ; toutes les autres lisent deja aschool_access. Aucun test ne les
couvrait — c'est ce qui l'a laisse passer.

Ce qui est tenu ici :

  1. Sans cookie, les deux repondent 401 — pas 200, et surtout pas un appel modele.
  2. Un prof connecte les utilise normalement : la dictee et le scan marchent toujours.
  3. Le plafond se declenche vraiment au-dela du seuil, et le message est HUMAIN (RÈGLE 23) :
     jamais « Rate limit exceeded », et sous la cle `detail` que les ecrans lisent.
  4. Le plafond se compte PAR COMPTE, pas par adresse. C'est le choix du 02/08/2026, et ce
     test est ce qui l'empeche d'etre defait sans s'en apercevoir : deux profs derriere la
     MEME adresse — un etablissement entier sort sur une seule adresse publique — ne se
     bloquent pas l'un l'autre.

Lancer : docker compose exec backend python -m pytest tests/test_dictee_ocr_authentifiees.py -q
"""
import pytest
from fastapi.testclient import TestClient

# engine / SessionLocal rediriges vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod
import backend.securite.comptes as comptes
import backend.dictee.ocr as ocrmod
import backend.dictee.transcribe as dicteemod
from backend.core.limiter import PLAFOND_DICTEE, PLAFOND_OCR, limiter
from backend.core.models_db import User
from backend.main import app

EMAIL_PROF = "marie@college.fr"
EMAIL_AUTRE = "paul@college.fr"

IMAGE = ("page.png", b"\x89PNG\r\n\x1a\n fausse image", "image/png")
AUDIO = ("dictee.webm", b"faux audio", "audio/webm")


def _seuil(plafond: str) -> int:
    """Nombre d'appels autorises, lu depuis la constante (« 30/hour » -> 30). Zero seuil en dur :
    changer la valeur dans limiter.py ne doit pas rendre ce test faux en silence."""
    return int(plafond.split("/")[0])


@pytest.fixture(autouse=True)
def _compteurs_a_zero():
    """Les compteurs slowapi vivent en memoire du process : sans remise a zero, un test
    heriterait du plafond deja consomme par le precedent."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(autouse=True)
def _aucun_appel_paye(monkeypatch):
    """Rien ne sort vers Groq. On remplace les deux portes payantes ET la resolution des cles,
    pour que le test ne depende ni du reseau ni du .env — et surtout pour que se tromper de
    protection ne coute pas d'argent pendant la suite."""
    monkeypatch.setattr(ocrmod, "get_cle_api", lambda db, nom: "cle-de-test")
    monkeypatch.setattr(ocrmod, "get_ocr_model", lambda db: "modele-de-test")
    monkeypatch.setattr(ocrmod, "get_max_tokens", lambda db, quoi: 512)
    monkeypatch.setattr(ocrmod, "transcribe_image", lambda *a, **k: "texte lu sur l'image")

    monkeypatch.setattr(dicteemod, "get_cle_api", lambda db, nom: "cle-de-test")
    monkeypatch.setattr(dicteemod, "transcribe_audio", lambda *a, **k: "texte dicte")


def _prof(email=EMAIL_PROF):
    db = dbmod.SessionLocal()
    db.add(User(email=email, password_hash="x", is_verified=True, prenom="Marie"))
    db.commit()
    db.close()
    return email


def _client_connecte(email):
    c = TestClient(app)
    c.cookies.set("aschool_access", comptes.create_access_token(email))
    return c


# ── 1. Sans cookie : la porte est fermee ───────────────────────────────────

@pytest.mark.parametrize("route, fichier", [("/api/ocr", IMAGE), ("/api/transcribe", AUDIO)])
def test_sans_cookie_la_route_repond_401(route, fichier):
    """Le coeur du trou : ces deux routes repondaient 200 — et facturaient — a un inconnu."""
    r = TestClient(app).post(route, files={"file": fichier})
    assert r.status_code == 401, f"{route} repond {r.status_code} sans cookie : elle est ouverte"


@pytest.mark.parametrize("route, fichier", [("/api/ocr", IMAGE), ("/api/transcribe", AUDIO)])
def test_un_jeton_qui_ne_designe_aucun_compte_ne_passe_pas(route, fichier):
    """Un jeton bien signe pour un compte SUPPRIME reste valide 15 minutes. Sur une route qui
    depense de l'argent, ces 15 minutes se paient — d'ou get_current_user, qui verifie que le
    compte existe encore, plutot que la simple lecture du jeton."""
    c = TestClient(app)
    c.cookies.set("aschool_access", comptes.create_access_token("fantome@college.fr"))
    r = c.post(route, files={"file": fichier})
    assert r.status_code == 401, f"{route} accepte un jeton sans compte derriere"


# ── 2. Le prof connecte travaille normalement ──────────────────────────────

def test_le_prof_connecte_lit_toujours_une_image():
    r = _client_connecte(_prof()).post("/api/ocr", files={"file": IMAGE})
    assert r.status_code == 200, r.text
    assert r.json()["texte"] == "texte lu sur l'image"


def test_le_prof_connecte_dicte_toujours():
    r = _client_connecte(_prof()).post("/api/transcribe", files={"file": AUDIO})
    assert r.status_code == 200, r.text
    assert r.json()["text"] == "texte dicte"


def test_les_garde_fous_deja_la_n_ont_pas_bouge():
    """La correction ne devait rien retirer : audio vide -> 400, type de fichier inconnu -> 400.
    Ces deux controles vivent APRÈS l'authentification et devaient continuer de s'appliquer."""
    c = _client_connecte(_prof())
    assert c.post("/api/transcribe", files={"file": ("v.webm", b"", "audio/webm")}).status_code == 400
    assert c.post("/api/ocr", files={"file": ("x.zip", b"pas une image", "application/zip")}).status_code == 400


# ── 3. Le plafond se declenche, et il parle francais ───────────────────────

def test_le_plafond_se_declenche_au_dela_du_seuil():
    c = _client_connecte(_prof())
    seuil = _seuil(PLAFOND_OCR)

    for i in range(seuil):
        r = c.post("/api/ocr", files={"file": IMAGE})
        assert r.status_code == 200, f"appel {i + 1}/{seuil} refuse avant le seuil : {r.text}"

    refuse = c.post("/api/ocr", files={"file": IMAGE})
    assert refuse.status_code == 429, "route payante NON plafonnee — une cle peut etre videe"


def test_le_message_du_plafond_est_humain_et_sous_la_cle_detail():
    c = _client_connecte(_prof())
    for _ in range(_seuil(PLAFOND_OCR) + 1):
        refuse = c.post("/api/ocr", files={"file": IMAGE})
    assert refuse.status_code == 429

    corps = refuse.json()
    # Les ecrans lisent TOUS `detail` — la cle `error` de slowapi y donnait « Erreur 429 ».
    assert "detail" in corps, f"cle `detail` absente du 429 : {corps}"
    assert "Trop de demandes" in corps["detail"]
    assert "Rate limit" not in corps["detail"]
    assert "429" not in corps["detail"]


# ── 4. La cle du plafond : le COMPTE, pas l'adresse ────────────────────────

def test_un_prof_qui_sature_son_plafond_ne_bloque_pas_son_collegue():
    """LE test du choix du 02/08/2026.

    Compte par adresse, un etablissement entier partage un seul plafond : le premier qui
    s'emballe prive tous les autres de dictee et de scan pour une heure. Les deux clients
    ci-dessous sortent de la MEME adresse (meme process de test) et ne different que par leur
    compte. Si ce test tombe, c'est que la cle est redevenue l'adresse."""
    marie = _client_connecte(_prof(EMAIL_PROF))
    paul = _client_connecte(_prof(EMAIL_AUTRE))

    for _ in range(_seuil(PLAFOND_OCR) + 1):
        marie.post("/api/ocr", files={"file": IMAGE})
    assert marie.post("/api/ocr", files={"file": IMAGE}).status_code == 429

    r = paul.post("/api/ocr", files={"file": IMAGE})
    assert r.status_code == 200, "le plafond est compte par adresse : un prof en bloque un autre"


def test_les_deux_routes_ont_chacune_leur_compteur():
    """Saturer le scan ne doit pas couper la dictee : ce sont deux depenses distinctes, avec
    deux plafonds distincts (PLAFOND_OCR et PLAFOND_DICTEE)."""
    c = _client_connecte(_prof())
    for _ in range(_seuil(PLAFOND_OCR) + 1):
        c.post("/api/ocr", files={"file": IMAGE})
    assert c.post("/api/ocr", files={"file": IMAGE}).status_code == 429

    assert _seuil(PLAFOND_DICTEE) > 0
    assert c.post("/api/transcribe", files={"file": AUDIO}).status_code == 200
