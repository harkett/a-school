r"""Preuve de raccordement — la vie d'une session : reprise, sortie, mot de passe repris.

CE QUI N'ÉTAIT PAS TENU. Quatre routes d'écriture de `auth.py` n'avaient aucun test le
10/08/2026 : `refresh` (la reprise silencieuse qui garde le prof connecté), `logout`,
`logout-inactivite` et `reset-password`. Ce sont les quatre gestes qui décident si quelqu'un
entre ou sort — les moins visibles et les plus fâcheux à casser : un `refresh` en panne
déconnecte tout le monde au bout d'un quart d'heure, sans erreur nulle part.

CE QUE LE TEST PROUVE, en chaîne réelle :
  1. `refresh` échange un jeton valide contre un NOUVEAU couple, et REVOQUE l'ancien — un jeton
     rejoué une seconde fois est refusé (c'est la rotation qui protège d'un vol de cookie) ;
  2. sans cookie, `refresh` rend 401 et n'écrit rien ;
  3. `logout` révoque vraiment le jeton en base — le rejouer ensuite échoue ;
  4. `logout-inactivite` journalise la sortie (`connexion_logs`, action `inactivite_logout`) ;
  5. `reset-password` change le mot de passe ET révoque toutes les sessions ouvertes, refuse un
     lien invalide, un mot de passe trop court et deux saisies qui divergent.

Lancer : docker compose exec backend python -m pytest tests/test_auth_session_et_reprise.py -q
"""
import backend.core.database as dbmod
from backend.core.models_db import ConnexionLog, RefreshToken, User
from backend.main import app
from backend.securite import comptes
from fastapi.testclient import TestClient

EMAIL = "prof.session@exemple.fr"
MDP = "MotDePasse!1"


def _prof():
    """Un compte vérifié, prêt à ouvrir une session. Rendu avec un refresh valide."""
    db = dbmod.SessionLocal()
    try:
        db.query(User).filter(User.email == EMAIL).delete()
        db.add(User(email=EMAIL, password_hash=comptes._hash_password(MDP),
                    is_verified=True, is_active=True, failed_attempts=0))
        db.commit()
        return comptes.create_refresh_token(db, EMAIL)
    finally:
        db.close()


def _jetons_vivants() -> int:
    db = dbmod.SessionLocal()
    try:
        uid = db.query(User.id).filter(User.email == EMAIL).scalar()
        return (db.query(RefreshToken)
                  .filter(RefreshToken.user_id == uid, RefreshToken.revoked == False)   # noqa: E712
                  .count())
    finally:
        db.close()


def test_refresh_tourne_le_jeton_et_refuse_le_rejeu():
    refresh = _prof()
    c = TestClient(app)
    c.cookies.set("aschool_refresh", refresh)

    r = c.post("/api/auth/refresh")
    assert r.status_code == 200, r.text
    # On lit l'en-tête de la réponse et non le bocal à cookies du client : après rotation il en
    # contient deux du même nom (l'ancien et le neuf), et `cookies.get` lève alors CookieConflict.
    poses = [v for k, v in r.headers.items() if k.lower() == "set-cookie" and "aschool_refresh=" in v]
    assert poses, "La reprise doit reposer le cookie de rafraîchissement."
    neuf = poses[-1].split("aschool_refresh=", 1)[1].split(";", 1)[0]
    assert neuf and neuf != refresh, (
        "La reprise doit rendre un NOUVEAU jeton : sans rotation, un cookie volé sert indéfiniment."
    )

    # le premier jeton a été révoqué par la rotation : le rejouer ne doit plus rien ouvrir
    rejeu = TestClient(app)
    rejeu.cookies.set("aschool_refresh", refresh)
    assert rejeu.post("/api/auth/refresh").status_code == 401


def test_refresh_sans_cookie_refuse():
    assert TestClient(app).post("/api/auth/refresh").status_code == 401


def test_logout_revoque_le_jeton_en_base():
    refresh = _prof()
    assert _jetons_vivants() == 1
    c = TestClient(app)
    c.cookies.set("aschool_refresh", refresh)

    assert c.post("/api/auth/logout").status_code == 200
    assert _jetons_vivants() == 0, "Sortir doit révoquer : le jeton est encore valable en base."


def test_logout_inactivite_journalise_la_sortie():
    _prof()
    db = dbmod.SessionLocal()
    try:
        acces = comptes.create_access_token(EMAIL)
    finally:
        db.close()
    c = TestClient(app)
    c.cookies.set("aschool_access", acces)

    assert c.post("/api/auth/logout-inactivite").status_code == 200
    db = dbmod.SessionLocal()
    try:
        n = (db.query(ConnexionLog)
               .filter(ConnexionLog.email == EMAIL, ConnexionLog.action == "inactivite_logout")
               .count())
    finally:
        db.close()
    assert n == 1, "La sortie pour inactivité doit laisser une trace : sinon elle est invisible."


def test_reset_password_change_le_mot_de_passe_et_ferme_les_sessions():
    _prof()
    db = dbmod.SessionLocal()
    try:
        jeton = comptes.generate_email_token(db, EMAIL, "reset_password")
    finally:
        db.close()
    assert _jetons_vivants() == 1

    c = TestClient(app)
    r = c.post("/api/auth/reset-password",
               json={"token": jeton, "password": "NouveauMdp!9", "password_confirm": "NouveauMdp!9"})
    assert r.status_code == 200, r.text

    db = dbmod.SessionLocal()
    try:
        u = db.query(User).filter(User.email == EMAIL).first()
        assert comptes._verify_password("NouveauMdp!9", u.password_hash)
        assert not comptes._verify_password(MDP, u.password_hash)
    finally:
        db.close()
    assert _jetons_vivants() == 0, (
        "Reprendre son mot de passe doit fermer les sessions ouvertes : c'est le geste qu'on fait "
        "quand on croit son compte compromis."
    )


def test_reset_password_refuse_ce_qui_doit_l_etre():
    _prof()
    db = dbmod.SessionLocal()
    try:
        jeton = comptes.generate_email_token(db, EMAIL, "reset_password")
    finally:
        db.close()
    c = TestClient(app)

    refus = [
        ({"token": jeton, "password": "abc", "password_confirm": "abc"}, "trop court"),
        ({"token": jeton, "password": "NouveauMdp!9", "password_confirm": "AutreChose!9"}, "divergent"),
        ({"token": "jeton-bidon", "password": "NouveauMdp!9", "password_confirm": "NouveauMdp!9"}, "lien invalide"),
    ]
    for corps, quoi in refus:
        assert c.post("/api/auth/reset-password", json=corps).status_code == 400, quoi

    db = dbmod.SessionLocal()
    try:
        u = db.query(User).filter(User.email == EMAIL).first()
        assert comptes._verify_password(MDP, u.password_hash), (
            "Refusé, donc le mot de passe d'origine doit tenir."
        )
    finally:
        db.close()
