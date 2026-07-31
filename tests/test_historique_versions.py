"""L'historique des versions — la moitié LECTURE de la règle 0.

Les jalons empilaient des versions depuis le premier jour, mais rien ne les relisait ni ne
les restaurait, alors que deux écrans le promettent au prof (« L'ancienne version reste dans
l'historique »). Vérifié ici, pour les activités ET les séances :
  - auth : 401 sans cookie ;
  - la liste rend l'historique le plus récent en tête, marque la version COURANTE et donne
    de quoi reconnaître chaque version (jalon en français, extrait) sans charger le texte ;
  - la lecture d'une version rend son contenu complet ;
  - RESTAURER remet la version choisie en état courant ET l'empile comme nouvelle version
    (jalon 'restauration') : on n'écrase jamais, et ce qu'on quitte reste dans l'historique ;
  - cloisonnement : l'historique d'un autre prof est introuvable (404), et une version qui
    n'appartient pas au contenu visé aussi.

Lance avec : pytest (BDD jetable aschool_test via conftest.py — jamais la base dev).
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod  # noqa: E402  (redirigé vers aschool_test par conftest)

from backend.main import app  # noqa: E402
from backend.auth import create_access_token  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

EMAIL = "historique@local.test"
INTRUS = "intrus-historique@local.test"


def _client(email=EMAIL):
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(email))
    return c


def _prof(email=EMAIL):
    """Un prof avec un couple de travail complet (le POST le lit EN BASE)."""
    from _profil import user_couple
    from backend.core.models_db import User
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            db.add(user_couple(db, email=email, password_hash="x", is_verified=True,
                               subject="Français", niveau="6e"))
            db.commit()
            u = db.query(User).filter(User.email == email).first()
        return u.id


def _type_id():
    from backend.core.models_db import ActiviteType
    with dbmod.SessionLocal() as db:
        t = db.query(ActiviteType).filter(ActiviteType.label == "Compréhension").first()
        if not t:
            t = ActiviteType(label="Compréhension")
            db.add(t)
            db.commit()
            db.refresh(t)
        return t.id


def _activite_a_trois_jalons():
    """Une activité et son historique : v1 (naissance), v2, v3 — comme trois générations."""
    _prof()
    corps = {
        "activite_type_id": _type_id(), "activite_label": "Compréhension",
        "sous_type": None, "nb": 5, "avec_correction": True,
        "objet": "Le récit d'aventure", "ton": "academique",
        "texte_source": "Un texte source.", "resultat": "# Activité v1",
    }
    aid = _client().post("/api/contenus/activites", json=corps).json()["id"]
    _client().put(f"/api/contenus/activites/{aid}",
                  json={**corps, "ton": "operationnel", "resultat": "# Activité v2"})
    _client().put(f"/api/contenus/activites/{aid}",
                  json={**corps, "ton": "academique", "resultat": "# Activité v3"})
    return aid


def test_auth_obligatoire():
    assert TestClient(app).get("/api/contenus/activites/1/versions").status_code == 401


def test_liste_versions_activite_plus_recente_en_tete():
    aid = _activite_a_trois_jalons()
    r = _client().get(f"/api/contenus/activites/{aid}/versions")
    assert r.status_code == 200, r.text
    versions = r.json()["versions"]
    assert [v["extrait"] for v in versions] == ["# Activité v3", "# Activité v2", "# Activité v1"]
    # La plus récente EST l'état courant : l'écran ne propose pas de restaurer l'affiché.
    assert [v["courante"] for v in versions] == [True, False, False]
    assert versions[0]["jalon"] == "generation"
    assert versions[0]["jalon_label"] == "Génération"      # français à l'écran, code en base
    assert versions[0]["ton"] == "academique"
    assert versions[0]["created_at"]
    assert "resultat" not in versions[0]                    # liste légère


def test_lire_une_version_rend_le_contenu_complet():
    aid = _activite_a_trois_jalons()
    versions = _client().get(f"/api/contenus/activites/{aid}/versions").json()["versions"]
    vid = versions[-1]["id"]                                 # la plus ancienne : v1
    r = _client().get(f"/api/contenus/activites/{aid}/versions/{vid}")
    assert r.status_code == 200, r.text
    assert r.json()["resultat"] == "# Activité v1"


def test_restaurer_activite_nempile_sans_jamais_ecraser():
    """« Revenir en arrière » = restaurer une version, qui devient elle-même une version."""
    from backend.core.models_db import Activite, ActiviteVersion
    aid = _activite_a_trois_jalons()
    versions = _client().get(f"/api/contenus/activites/{aid}/versions").json()["versions"]
    v1 = versions[-1]["id"]

    r = _client().post(f"/api/contenus/activites/{aid}/versions/{v1}/restaurer")
    assert r.status_code == 200, r.text
    assert r.json()["resultat"] == "# Activité v1"

    with dbmod.SessionLocal() as db:
        a = db.query(Activite).filter(Activite.id == aid).one()
        assert a.resultat == "# Activité v1"                 # l'état courant a bien reculé
        assert a.ton == "academique"
        empilees = (db.query(ActiviteVersion)
                    .filter(ActiviteVersion.activite_id == aid)
                    .order_by(ActiviteVersion.id).all())
        # v1, v2, v3 TOUJOURS là (rien d'écrasé) + la restauration en 4e.
        assert [v.resultat for v in empilees] == [
            "# Activité v1", "# Activité v2", "# Activité v3", "# Activité v1"]
        assert empilees[-1].jalon == "restauration"

    # On peut revenir en arrière d'un retour en arrière : v3 est toujours restaurable.
    v3 = next(v["id"] for v in
              _client().get(f"/api/contenus/activites/{aid}/versions").json()["versions"]
              if v["extrait"] == "# Activité v3")
    assert _client().post(
        f"/api/contenus/activites/{aid}/versions/{v3}/restaurer").json()["resultat"] == "# Activité v3"


def test_cloisonnement_activite():
    aid = _activite_a_trois_jalons()
    vid = _client().get(f"/api/contenus/activites/{aid}/versions").json()["versions"][0]["id"]
    _prof(INTRUS)
    autre = _client(INTRUS)
    assert autre.get(f"/api/contenus/activites/{aid}/versions").status_code == 404
    assert autre.get(f"/api/contenus/activites/{aid}/versions/{vid}").status_code == 404
    assert autre.post(f"/api/contenus/activites/{aid}/versions/{vid}/restaurer").status_code == 404


def test_version_d_une_autre_activite_refusee():
    """Une version existe, mais pas SUR cette activité-là : 404, on ne restaure rien."""
    a1 = _activite_a_trois_jalons()
    a2 = _activite_a_trois_jalons()
    vid_a1 = _client().get(f"/api/contenus/activites/{a1}/versions").json()["versions"][0]["id"]
    assert _client().get(f"/api/contenus/activites/{a2}/versions/{vid_a1}").status_code == 404
    assert _client().post(
        f"/api/contenus/activites/{a2}/versions/{vid_a1}/restaurer").status_code == 404


def _seance_a_deux_jalons():
    from backend.core.models_db import Seance, SeanceVersion
    uid = _prof()
    with dbmod.SessionLocal() as db:
        s = Seance(user_id=uid, titre="Séance test", matiere="Français", niveau="6e",
                   style="academique", resultat="# Séance v2")
        db.add(s)
        db.flush()
        db.add(SeanceVersion(seance_id=s.id, jalon="generation",
                             style="operationnel", resultat="# Séance v1"))
        db.add(SeanceVersion(seance_id=s.id, jalon="generation",
                             style="academique", resultat="# Séance v2"))
        db.commit()
        return s.id


def test_historique_seance_lecture_et_restauration():
    from backend.core.models_db import Seance, SeanceVersion
    sid = _seance_a_deux_jalons()
    versions = _client().get(f"/api/contenus/seances/{sid}/versions").json()["versions"]
    assert [v["extrait"] for v in versions] == ["# Séance v2", "# Séance v1"]
    assert versions[0]["courante"] is True
    assert versions[0]["style"] == "academique"

    v1 = versions[-1]["id"]
    assert _client().get(f"/api/contenus/seances/{sid}/versions/{v1}").json()["resultat"] == "# Séance v1"
    r = _client().post(f"/api/contenus/seances/{sid}/versions/{v1}/restaurer")
    assert r.status_code == 200, r.text

    with dbmod.SessionLocal() as db:
        s = db.query(Seance).filter(Seance.id == sid).one()
        assert s.resultat == "# Séance v1"
        assert s.style == "operationnel"                     # le style suit la version restaurée
        empilees = (db.query(SeanceVersion)
                    .filter(SeanceVersion.seance_id == sid)
                    .order_by(SeanceVersion.id).all())
        assert [v.resultat for v in empilees] == ["# Séance v1", "# Séance v2", "# Séance v1"]
        assert empilees[-1].jalon == "restauration"


def test_cloisonnement_seance():
    sid = _seance_a_deux_jalons()
    _prof(INTRUS)
    assert _client(INTRUS).get(f"/api/contenus/seances/{sid}/versions").status_code == 404
