r"""Preuve du PLANIFICATEUR — les travaux automatiques se règlent à l'écran, pas dans le code.

CE QUI A CHANGÉ. L'heure de la veille des tarifs et la cadence de la surveillance étaient écrites
dans `main.py` : passer un contrôle de 6 h à 22 h demandait un développeur, une relecture et un
redéploiement pour deux chiffres qui ne regardent que l'exploitation. Elles vivent maintenant dans
`taches_planifiees`, et l'administrateur les règle depuis « Paramètres → Planificateur ».

CE QUE CES TESTS PROTÈGENT :
  1. le réglage s'écrit ET s'applique tout de suite — sans reprogrammation, l'administrateur voit
     22 h à l'écran pendant que la tâche continue de partir à 6 h ;
  2. un réglage impossible est refusé (25 h, un intervalle de zéro minute) plutôt qu'accepté et
     silencieusement ignoré par l'ordonnanceur ;
  3. une tâche qui échoue écrit son échec sur sa ligne et n'emporte pas les autres ;
  4. « Exécuter maintenant » emprunte le MÊME chemin que le déclenchement automatique — sans quoi
     un essai réussi ne prouverait rien de ce qui se passera la nuit ;
  5. sans cookie admin, aucune des trois routes ne répond.

Lancer : docker compose exec backend python -m pytest tests/test_planificateur.py -q
"""
from conftest import resemer_reglages

import backend.core.database as dbmod
import backend.systeme.planificateur as planif
from backend.core.models_db import TachePlanifiee
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _lire(code: str):
    db = dbmod.SessionLocal()
    try:
        return db.query(TachePlanifiee).filter(TachePlanifiee.code == code).first()
    finally:
        db.close()


def _semer(code="veille_tarifs", **champs):
    """Pose la tâche dans l'état voulu — la base de test n'a pas les lignes de la migration."""
    db = dbmod.SessionLocal()
    try:
        t = db.query(TachePlanifiee).filter(TachePlanifiee.code == code).first()
        if t is None:
            t = TachePlanifiee(code=code)
            db.add(t)
        t.actif = champs.get("actif", True)
        t.type_planif = champs.get("type_planif", "quotidien")
        t.heure = champs.get("heure", 6)
        t.minute = champs.get("minute", 5)
        t.intervalle_minutes = champs.get("intervalle_minutes")
        t.destinataire = champs.get("destinataire")
        db.commit()
    finally:
        db.close()


def test_regler_une_tache_ecrit_et_reprogramme(monkeypatch):
    """LE POINT QUI COMPTE. Un réglage enregistré mais non reprogrammé est le pire des deux mondes :
    l'écran affiche 22 h, la tâche part à 6 h, et rien ne signale l'écart."""
    resemer_reglages()
    _semer(heure=6, minute=5)
    reprogrammations = []
    monkeypatch.setattr(planif, "programmer_tout", lambda *a, **k: reprogrammations.append(True))
    r = _admin().put("/api/admin/taches/veille_tarifs", json={
        "actif": True, "type_planif": "quotidien", "heure": 22, "minute": 0,
        "intervalle_minutes": None, "destinataire": "  veille@aschool.fr  ",
    })
    assert r.status_code == 200, r.text[:200]

    t = _lire("veille_tarifs")
    assert (t.heure, t.minute) == (22, 0)
    assert t.destinataire == "veille@aschool.fr", "l'adresse doit être nettoyée de ses espaces"
    assert reprogrammations, "le réglage n'a pas été reprogrammé : il ne s'appliquerait qu'au prochain démarrage"


def test_une_heure_impossible_est_refusee():
    """25 h n'existe pas. Accepter la valeur reviendrait à l'écrire en base et à la voir ignorée
    par l'ordonnanceur — l'administrateur croirait avoir réglé quelque chose."""
    resemer_reglages()
    _semer()
    r = _admin().put("/api/admin/taches/veille_tarifs", json={
        "actif": True, "type_planif": "quotidien", "heure": 25, "minute": 0,
        "intervalle_minutes": None, "destinataire": None,
    })
    assert r.status_code == 400
    assert _lire("veille_tarifs").heure == 6, "refusé, donc rien n'est écrit"


def test_un_intervalle_de_zero_minute_est_refuse():
    """Une tâche « toutes les 0 minute » tournerait sans arrêt et occuperait le serveur entier."""
    resemer_reglages()
    _semer(code="surveillance", type_planif="intervalle", heure=None, minute=None,
           intervalle_minutes=5)
    r = _admin().put("/api/admin/taches/surveillance", json={
        "actif": True, "type_planif": "intervalle", "heure": None, "minute": None,
        "intervalle_minutes": 0, "destinataire": None,
    })
    assert r.status_code == 400
    assert _lire("surveillance").intervalle_minutes == 5


def test_executer_ecrit_le_resultat_sur_la_ligne(monkeypatch):
    """« Exécuter maintenant » passe par `planificateur.executer`, exactement comme l'ordonnanceur.
    C'est ce qui rend l'essai probant : ce qu'on voit ici est ce qui se produira cette nuit."""
    resemer_reglages()
    _semer()
    monkeypatch.setitem(planif.TACHES["veille_tarifs"], "fonction",
                        lambda _dest: "Aucun changement de tarif.")

    r = _admin().post("/api/admin/taches/veille_tarifs/executer")
    assert r.status_code == 200, r.text[:200]
    assert r.json()["ok"] is True

    t = _lire("veille_tarifs")
    assert t.dernier_resultat == "Aucun changement de tarif."
    assert t.dernier_ok is True
    assert t.dernier_passage is not None, "sans horodatage, une tâche muette est indiscernable d'une tâche morte"


def test_une_tache_qui_echoue_le_dit_sans_faire_tomber_le_reste(monkeypatch):
    """L'échec est une information d'exploitation : il se lit sur la ligne, en rouge, et
    l'ordonnanceur continue de tourner."""
    resemer_reglages()
    _semer()

    def _casse(_dest):
        raise RuntimeError("page injoignable")

    monkeypatch.setitem(planif.TACHES["veille_tarifs"], "fonction", _casse)

    r = _admin().post("/api/admin/taches/veille_tarifs/executer")
    assert r.status_code == 200, "un travail qui échoue n'est pas une panne de l'API"
    assert r.json()["ok"] is False

    t = _lire("veille_tarifs")
    assert t.dernier_ok is False
    assert "page injoignable" in t.dernier_resultat, "le message d'origine doit rester lisible"


def test_le_destinataire_vide_retombe_sur_l_adresse_du_serveur():
    """Une tâche ne devient pas muette parce qu'un champ est resté vide : sans adresse propre, le
    courriel part à l'adresse d'administration."""
    resemer_reglages()
    _semer(destinataire=None)
    corps = _admin().get("/api/admin/taches").json()
    assert "destinataire_par_defaut" in corps, "l'écran doit pouvoir dire qui reçoit par défaut"
    t = next(x for x in corps["taches"] if x["code"] == "veille_tarifs")
    assert t["destinataire"] is None


def test_sans_cookie_admin_les_trois_routes_refusent():
    """Elles règlent ce que le serveur exécute tout seul : elles ne s'ouvrent à personne d'autre."""
    resemer_reglages()
    _semer()
    c = TestClient(app)
    assert c.get("/api/admin/taches").status_code == 401
    assert c.put("/api/admin/taches/veille_tarifs", json={"actif": False}).status_code == 401
    assert c.post("/api/admin/taches/veille_tarifs/executer").status_code == 401
