r"""Preuve de raccordement — les quatre gestes de service de l'admin agissent VRAIMENT.

CE QUI N'ÉTAIT PAS TENU. Quatre routes d'écriture d'`admin.py` n'avaient aucun test le
10/08/2026 : marquer une alerte lue, fermer la session d'un prof, purger une catégorie de la
base, régler la coupure de silence du flux. Ce sont des gestes qui MODIFIENT l'état du service —
celui du milieu efface des lignes pour de bon.

CE QUE LE TEST PROUVE, en chaîne réelle :
  1. `POST /admin/alerts/{id}/read` marque lu EN BASE, avec qui et quand ; 404 sur une alerte
     inconnue ;
  2. `POST /admin/force-logout/{id}` désactive la session visée et laisse une trace d'audit ;
     404 sur une session inconnue ;
  3. `POST /admin/maintenance/purge/{categorie}` SUPPRIME vraiment les lignes visées, ne touche
     pas aux autres, et refuse une catégorie inconnue (400) ;
  4. `PUT /admin/stream-timeout` écrit la valeur en base, et refuse hors bornes SANS rien écrire ;
  5. sans cookie admin : 401 sur les quatre.

L'ENVOI DE MAIL de `force-logout` n'est pas éprouvé ici : la route l'entoure déjà d'un
`try/except` parce qu'un SMTP muet ne doit pas empêcher de fermer une session. C'est la fermeture
qui compte, et c'est elle qu'on vérifie.

Lancer : docker compose exec backend python -m pytest tests/test_admin_gestes_de_service.py -q
"""
from datetime import timedelta

from conftest import resemer_reglages

import backend.core.database as dbmod
from backend.core.horloge import maintenant_utc
from backend.core.models_db import AdminAlert, AdminAuditLog, EmailToken, Setting, User, UserSession
from backend.main import app
from backend.systeme.admin import STREAM_SILENCE_MAX, STREAM_SILENCE_MIN, _make_admin_token
from fastapi.testclient import TestClient


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _prof(email="prof.service@exemple.fr") -> int:
    db = dbmod.SessionLocal()
    try:
        u = User(email=email, password_hash="x", is_verified=True, is_active=True, failed_attempts=0)
        db.add(u)
        db.commit()
        return u.id
    finally:
        db.close()


def test_marquer_une_alerte_lue():
    db = dbmod.SessionLocal()
    try:
        a = AdminAlert(level="warning", title="Disque", message="85 %")
        db.add(a)
        db.commit()
        aid = a.id
    finally:
        db.close()

    assert _admin().post(f"/api/admin/alerts/{aid}/read").status_code == 200
    db = dbmod.SessionLocal()
    try:
        a = db.query(AdminAlert).filter(AdminAlert.id == aid).first()
        assert a.is_read and a.read_by and a.read_at is not None, (
            "Marquer lu doit dire QUI et QUAND : sans ça, l'alerte disparaît sans responsable."
        )
    finally:
        db.close()
    assert _admin().post("/api/admin/alerts/999999/read").status_code == 404


def test_fermer_la_session_d_un_prof():
    uid = _prof()
    db = dbmod.SessionLocal()
    try:
        s = UserSession(user_id=uid, session_key="cle-de-session-1234", is_active=True)
        db.add(s)
        db.commit()
        sid = s.id
    finally:
        db.close()

    r = _admin().post(f"/api/admin/force-logout/{sid}", json={"raison": "poste partagé"})
    assert r.status_code == 200, r.text
    db = dbmod.SessionLocal()
    try:
        assert db.query(UserSession).filter(UserSession.id == sid).first().is_active is False
        trace = db.query(AdminAuditLog).filter(AdminAuditLog.action == "FORCE_LOGOUT").first()
        assert trace is not None and "poste partagé" in (trace.details or ""), (
            "Fermer la session de quelqu'un se journalise, raison comprise."
        )
    finally:
        db.close()
    assert _admin().post("/api/admin/force-logout/999999", json={"raison": ""}).status_code == 404


def test_purger_une_categorie_supprime_vraiment():
    """`tokens_email_expires` : les liens périmés partent, les valides restent."""
    uid = _prof("prof.purge@exemple.fr")
    db = dbmod.SessionLocal()
    try:
        db.add_all([
            EmailToken(user_id=uid, email="prof.purge@exemple.fr", token="jeton-perime",
                       purpose="verify_email",
                       expires_at=maintenant_utc() - timedelta(days=2)),
            EmailToken(user_id=uid, email="prof.purge@exemple.fr", token="jeton-valide",
                       purpose="verify_email",
                       expires_at=maintenant_utc() + timedelta(days=2)),
        ])
        db.commit()
    finally:
        db.close()

    r = _admin().post("/api/admin/maintenance/purge/tokens_email_expires")
    assert r.status_code == 200, r.text
    db = dbmod.SessionLocal()
    try:
        restants = {t.token for t in db.query(EmailToken).all()}
    finally:
        db.close()
    assert restants == {"jeton-valide"}, (
        f"La purge doit effacer les périmés et EUX SEULS. Restants : {restants}"
    )
    assert _admin().post("/api/admin/maintenance/purge/categorie_inventee").status_code == 400


def test_regler_la_coupure_de_silence():
    resemer_reglages(sauf=("stream_silence_timeout",))
    c = _admin()

    assert c.put("/api/admin/stream-timeout", json={"timeout": 45}).status_code == 200
    db = dbmod.SessionLocal()
    try:
        assert db.query(Setting).filter(Setting.key == "stream_silence_timeout").first().value == "45"
    finally:
        db.close()

    for hors in (STREAM_SILENCE_MIN - 1, STREAM_SILENCE_MAX + 1):
        assert c.put("/api/admin/stream-timeout", json={"timeout": hors}).status_code == 400
    db = dbmod.SessionLocal()
    try:
        assert db.query(Setting).filter(Setting.key == "stream_silence_timeout").first().value == "45", (
            "Refusé, donc la valeur d'avant doit tenir."
        )
    finally:
        db.close()


def test_sans_cookie_admin_les_quatre_gestes_refusent():
    c = TestClient(app)
    appels = [
        ("post", "/api/admin/alerts/1/read", None),
        ("post", "/api/admin/force-logout/1", {"raison": ""}),
        ("post", "/api/admin/maintenance/purge/tokens_email_expires", None),
        ("put", "/api/admin/stream-timeout", {"timeout": 30}),
    ]
    for methode, chemin, corps in appels:
        r = getattr(c, methode)(chemin, json=corps) if corps is not None else getattr(c, methode)(chemin)
        assert r.status_code == 401, f"{methode.upper()} {chemin} rend {r.status_code}"
