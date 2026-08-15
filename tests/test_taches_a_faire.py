r"""Preuve du CARNET DE L'ADMINISTRATEUR — une idée notée ne se perd plus.

CE QUI A CHANGÉ. Les professeurs ont « Mes feedbacks » pour faire remonter une remarque, et
l'administrateur a l'écran qui les reçoit. Lui n'avait rien : une idée qui lui venait au milieu
d'une autre tâche se disait, et se perdait. Le carnet vit dans `taches_a_faire`, écran
« Tâches à faire ».

CE QUE CES TESTS PROTÈGENT :
  1. une note sans titre est refusée — une ligne sans titre ne se retrouve jamais dans une liste ;
  2. cocher pose la DATE, décocher l'efface : sans ça, une note rouverte compterait pour faite ;
  3. l'ordre est « à faire » d'abord, jamais l'ordre d'insertion — le carnet se lit du haut ;
  4. « Supprimer » supprime vraiment la ligne, pas un drapeau caché ;
  5. sans cookie admin, aucune des quatre routes ne répond.

Lancer : docker compose exec backend python -m pytest tests/test_taches_a_faire.py -q
"""
import backend.core.database as dbmod
from backend.core.models_db import TacheAFaire
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _vider():
    db = dbmod.SessionLocal()
    try:
        db.query(TacheAFaire).delete()
        db.commit()
    finally:
        db.close()


def _lire(tid: int):
    db = dbmod.SessionLocal()
    try:
        return db.query(TacheAFaire).filter(TacheAFaire.id == tid).first()
    finally:
        db.close()


def test_une_note_sans_titre_est_refusee():
    """Un titre vide donne une ligne invisible dans la liste : l'idée serait « notée » et
    pourtant introuvable — pire que pas de carnet du tout."""
    _vider()
    r = _admin().post("/api/admin/taches-a-faire", json={"titre": "   ", "detail": "sans titre"})
    assert r.status_code == 400
    db = dbmod.SessionLocal()
    try:
        assert db.query(TacheAFaire).count() == 0, "refusé, donc rien n'est écrit"
    finally:
        db.close()


def test_noter_puis_relire_garde_le_detail():
    """Le détail est ce qui fait qu'une note relue dans six mois veut encore dire quelque chose."""
    _vider()
    c = _admin()
    r = c.post("/api/admin/taches-a-faire", json={
        "titre": "Alerter sur deux connexions éloignées",
        "detail": "Lille et Marseille au même moment : pas la même personne.",
    })
    assert r.status_code == 201, r.text[:200]
    tid = r.json()["id"]

    corps = c.get("/api/admin/taches-a-faire").json()
    ligne = next(t for t in corps["taches"] if t["id"] == tid)
    assert ligne["titre"] == "Alerter sur deux connexions éloignées"
    assert "Marseille" in ligne["detail"]
    assert ligne["fait"] is False and ligne["fait_at"] is None


def test_cocher_pose_la_date_et_decocher_l_efface():
    """LE POINT QUI COMPTE. Une note rouverte qui garde sa date de clôture passe pour terminée
    dans tout comptage — et elle disparaît du travail restant sans que personne l'ait décidé."""
    _vider()
    c = _admin()
    tid = c.post("/api/admin/taches-a-faire", json={"titre": "Une seule connexion par prof"}).json()["id"]

    c.put(f"/api/admin/taches-a-faire/{tid}",
          json={"titre": "Une seule connexion par prof", "detail": None, "fait": True})
    t = _lire(tid)
    assert t.fait is True and t.fait_at is not None

    c.put(f"/api/admin/taches-a-faire/{tid}",
          json={"titre": "Une seule connexion par prof", "detail": None, "fait": False})
    t = _lire(tid)
    assert t.fait is False
    assert t.fait_at is None, "une note remise à faire ne garde pas sa date de clôture"


def test_les_notes_a_faire_passent_devant_les_faites():
    """Le carnet se lit du haut. Une note faite il y a trois mois ne doit pas s'intercaler entre
    deux choses à traiter."""
    _vider()
    c = _admin()
    a = c.post("/api/admin/taches-a-faire", json={"titre": "Première, et faite"}).json()["id"]
    c.post("/api/admin/taches-a-faire", json={"titre": "Deuxième, à faire"})
    c.put(f"/api/admin/taches-a-faire/{a}", json={"titre": "Première, et faite", "fait": True})

    taches = c.get("/api/admin/taches-a-faire").json()["taches"]
    assert [t["fait"] for t in taches] == [False, True]


def test_supprimer_supprime_vraiment():
    """Pas de drapeau caché : la ligne quitte la base. Un carnet qu'on ne peut pas raturer se
    remplit de notes mortes, et plus personne ne le lit."""
    _vider()
    c = _admin()
    tid = c.post("/api/admin/taches-a-faire", json={"titre": "À jeter"}).json()["id"]

    assert c.delete(f"/api/admin/taches-a-faire/{tid}").status_code == 200
    assert _lire(tid) is None
    assert c.delete(f"/api/admin/taches-a-faire/{tid}").status_code == 404


def test_sans_cookie_admin_les_quatre_routes_refusent():
    """Le carnet dit ce qui n'est pas encore fait dans le produit : il ne s'ouvre à personne."""
    _vider()
    c = TestClient(app)
    assert c.get("/api/admin/taches-a-faire").status_code == 401
    assert c.post("/api/admin/taches-a-faire", json={"titre": "x"}).status_code == 401
    assert c.put("/api/admin/taches-a-faire/1", json={"titre": "x"}).status_code == 401
    assert c.delete("/api/admin/taches-a-faire/1").status_code == 401


def test_le_carnet_ne_se_confond_pas_avec_le_planificateur():
    """Deux tables, deux écrans, deux URL. Une note du carnet ne doit jamais apparaître dans les
    travaux que le serveur exécute tout seul — et l'inverse non plus."""
    _vider()
    c = _admin()
    c.post("/api/admin/taches-a-faire", json={"titre": "Note qui ne s'exécute pas"})
    planif = c.get("/api/admin/taches").json()
    titres = [t.get("libelle") for t in planif["taches"]]
    assert "Note qui ne s'exécute pas" not in titres
