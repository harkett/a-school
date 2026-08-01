"""Une cle de signature vide n'est jamais un cas legitime.

CE QUE CE TEST PROUVE. `_admin_secret()` faisait `os.getenv("JWT_SECRET", "")` : un serveur
demarre sans ADMIN_JWT_SECRET ni JWT_SECRET signait ses jetons admin avec la CHAINE VIDE —
un secret que n'importe qui peut deviner — et personne n'en etait averti. Le trou etait
silencieux : tout fonctionnait, la connexion admin marchait, les jetons etaient juste
forgeables par le premier venu.

Desormais l'absence des deux secrets fait LEVER, et au demarrage (l'appel est au niveau
module, donc a l'import de backend.systeme.admin), pas au premier clic.

Lancer : docker exec a-school-backend-1 python -m pytest tests/test_secret_admin_obligatoire.py -q
"""
import pytest

from backend.systeme import admin


def test_sans_aucun_secret_ca_leve(monkeypatch):
    monkeypatch.delenv("ADMIN_JWT_SECRET", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="SÉCURITÉ"):
        admin._admin_secret()


def test_un_secret_blanc_ne_compte_pas(monkeypatch):
    """« » n'est pas un secret : des espaces passaient le `or` de l'ancien code."""
    monkeypatch.setenv("ADMIN_JWT_SECRET", "   ")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="SÉCURITÉ"):
        admin._admin_secret()


def test_jwt_secret_seul_suffit(monkeypatch):
    """Le repli reste : tant qu'ADMIN_JWT_SECRET n'est pas pose, JWT_SECRET fait l'affaire."""
    monkeypatch.delenv("ADMIN_JWT_SECRET", raising=False)
    monkeypatch.setenv("JWT_SECRET", "secret-de-prof")
    assert admin._admin_secret() == "secret-de-prof"


def test_admin_jwt_secret_prend_la_main(monkeypatch):
    monkeypatch.setenv("ADMIN_JWT_SECRET", "secret-admin-dedie")
    monkeypatch.setenv("JWT_SECRET", "secret-de-prof")
    assert admin._admin_secret() == "secret-admin-dedie"


def test_le_jeton_admin_n_est_pas_signe_avec_du_vide(monkeypatch):
    """La consequence concrete : un jeton forge avec la chaine vide ne doit plus etre accepte."""
    from jose import jwt
    from datetime import timedelta
    from backend.core.horloge import maintenant_utc
    monkeypatch.setenv("ADMIN_JWT_SECRET", "secret-admin-dedie")
    faux = jwt.encode(
        {"sub": "admin", "role": "admin", "exp": maintenant_utc() + timedelta(hours=1)},
        "", algorithm="HS256",
    )
    assert admin._verify_admin_token(faux) is False
