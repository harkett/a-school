r"""Preuve du LIEU D'UNE SESSION — d'où se connecte un professeur, en clair.

CE QUI A CHANGÉ. L'écran des sessions gardait l'adresse IP depuis toujours et n'en faisait rien :
personne ne lit « 83.228.245.163 ». Un même compte ouvert à Lille et à Marseille au même moment
est un compte partagé entre deux personnes, et rien ne permettait de le voir. La ville est
désormais résolue depuis l'adresse, écrite sur la ligne de la session, et affichée.

CE QUE CES TESTS PROTÈGENT :
  1. une adresse de réseau local n'est pas envoyée à un service extérieur — elle n'a pas de ville,
     personne au monde ne peut la situer, l'appel serait perdu ;
  2. le lieu est résolu UNE SEULE FOIS par session, jamais à chaque affichage : trente professeurs
     d'un même établissement partagent une adresse publique, et l'écran se recharge toutes les
     30 secondes ;
  3. un service tiers muet ou en panne laisse la case vide — il ne casse pas l'écran, qui sert
     d'abord à déconnecter quelqu'un en urgence ;
  4. aucune ville n'est inventée : sans réponse, la session reste sans lieu ;
  5. la distance entre deux sessions se mesure vraiment (c'est elle qui dira, plus tard, que deux
     connexions simultanées ne peuvent pas être la même personne).

Lancer : docker compose exec backend python -m pytest tests/test_localisation_sessions.py -q
"""
import backend.core.database as dbmod
import backend.systeme.localisation_ip as loc
from backend.core.models_db import User, UserSession
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _session(ip: str, cle: str) -> int:
    """Pose une session active pour un prof, avec l'adresse voulue."""
    db = dbmod.SessionLocal()
    try:
        user = db.query(User).first()
        if user is None:
            user = User(email="lieu@test.fr", password_hash="x", is_verified=True)
            db.add(user)
            db.commit()
        s = UserSession(user_id=user.id, session_key=cle, ip_address=ip, is_active=True)
        db.add(s)
        db.commit()
        return s.id
    finally:
        db.close()


def _relire(sid: int):
    db = dbmod.SessionLocal()
    try:
        return db.query(UserSession).filter(UserSession.id == sid).first()
    finally:
        db.close()


def test_une_adresse_locale_ne_sort_jamais_du_serveur(monkeypatch):
    """127.0.0.1, 192.168.x, 10.x : aucune ville derrière. Interroger un service pour ça, c'est
    payer une attente pour rien — et en développement, c'est TOUTES les sessions."""
    appels = []
    monkeypatch.setattr(loc.urllib.request, "urlopen",
                        lambda *a, **k: appels.append(True))
    for ip in ("127.0.0.1", "192.168.1.20", "10.0.0.5", "172.16.0.1"):
        lieu, lat, lon = loc.localiser(ip)
        assert lieu == loc.RESEAU_LOCAL
        assert (lat, lon) == (None, None)
    assert not appels, "une adresse privée ne doit déclencher AUCUN appel extérieur"


def test_un_service_muet_ne_laisse_aucune_ville_inventee(monkeypatch):
    """Sans réponse, la case reste vide. Une ville devinée serait pire que rien : on prendrait
    des décisions dessus — déconnecter un compte, alerter — sur une donnée fausse."""
    loc._cache.clear()

    def _panne(*a, **k):
        raise OSError("réseau coupé")

    monkeypatch.setattr(loc.urllib.request, "urlopen", _panne)
    assert loc.localiser("83.228.245.163") == (None, None, None)


def test_la_ville_est_resolue_une_seule_fois_puis_gardee(monkeypatch):
    """Trente professeurs d'un collège partagent une adresse publique, et l'écran se recharge
    toutes les 30 secondes. Sans ce cache, ce serait des centaines d'appels identiques par heure."""
    loc._cache.clear()
    appels = []

    class _Reponse:
        def read(self, _n=None):
            return (b'{"cityName":"Lyon","countryName":"France",'
                    b'"latitude":45.75,"longitude":4.85}')

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _faux(*a, **k):
        appels.append(True)
        return _Reponse()

    monkeypatch.setattr(loc.urllib.request, "urlopen", _faux)
    assert loc.localiser("83.228.245.163") == ("Lyon, France", 45.75, 4.85)
    assert loc.localiser("83.228.245.163") == ("Lyon, France", 45.75, 4.85)
    assert len(appels) == 1, "la deuxième demande doit venir du cache, pas du service"


def test_l_ecran_ecrit_le_lieu_sur_la_session_et_l_affiche(monkeypatch):
    """LE POINT QUI COMPTE. Le lieu est écrit sur la ligne : la session suivante n'a plus rien à
    demander à personne, et l'information survit au redémarrage du serveur."""
    loc._cache.clear()
    monkeypatch.setattr(loc, "localiser",
                        lambda ip: ("Marseille, France", 43.3, 5.4))
    sid = _session("83.228.245.163", "cle-lieu-ecrit")

    r = _admin().get("/api/admin/sessions")
    assert r.status_code == 200, r.text[:200]
    ligne = next((s for s in r.json() if s["id"] == sid), None)
    assert ligne is not None
    assert ligne["lieu"] == "Marseille, France", "l'écran doit montrer la ville, pas seulement l'IP"
    assert ligne["ip"] == "83.228.245.163", "l'adresse reste : c'est elle qui fait foi"

    s = _relire(sid)
    assert s.localisation == "Marseille, France"
    assert (s.latitude, s.longitude) == (43.3, 5.4), (
        "sans coordonnées, impossible de mesurer l'écart entre deux sessions du même compte"
    )


def test_un_service_en_panne_ne_casse_pas_l_ecran_des_sessions(monkeypatch):
    """Cet écran sert à déconnecter quelqu'un en urgence. Il doit s'ouvrir même si le service de
    localisation est mort — sans lui, l'administrateur perd son seul geste d'urgence."""
    monkeypatch.setattr(loc, "localiser", lambda ip: (None, None, None))
    sid = _session("83.228.245.164", "cle-lieu-panne")

    r = _admin().get("/api/admin/sessions")
    assert r.status_code == 200
    ligne = next((s for s in r.json() if s["id"] == sid), None)
    assert ligne is not None and ligne["lieu"] == "—"
    assert _relire(sid).localisation is None, "rien d'écrit : on réessaiera au prochain affichage"


def test_la_distance_entre_deux_villes_est_juste():
    """C'est ce calcul qui dira qu'un compte ouvert à Lille et à Marseille au même instant n'est
    pas la même personne. S'il est faux, l'alerte l'est aussi."""
    lille = (50.63, 3.06)
    marseille = (43.30, 5.37)
    d = loc.distance_km(*lille, *marseille)
    assert 750 < d < 850, f"Lille–Marseille fait environ 800 km à vol d'oiseau, calculé {d}"
    assert loc.distance_km(*lille, *lille) < 1
    assert loc.distance_km(None, 3.06, 43.3, 5.37) is None, (
        "une session sans coordonnées ne se compare à rien — surtout pas à zéro kilomètre"
    )
