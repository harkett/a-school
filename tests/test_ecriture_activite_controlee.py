"""L'écriture d'une activité est CONTRÔLÉE côté serveur — comme la génération.

POST et PUT /contenus/activites écrivaient `activite_type_id` et `activite_label` tels que
l'écran les envoyait, sans rien vérifier, alors que les contrôles existaient déjà à la
génération. Deux conséquences : on pouvait ranger en base une activité d'un type inconnu ou
pas prêt pour le couple, et le LIBELLÉ — qui alimente « Mes stats » — était celui que le
client voulait bien donner.

Vérifié ici :
  - les trois refus de la génération valent maintenant à l'écriture (type inconnu, type
    inactif, type non coché pour le couple), et RIEN n'est écrit dans ce cas ;
  - le libellé écrit est celui de la BASE, jamais celui du client — même s'il en envoie un
    autre, même s'il n'en envoie aucun ;
  - « Mes stats » compte donc le vrai libellé ;
  - une seule porte : c'est la fonction de la génération qui est appelée (une divergence
    entre les deux ferait tomber ce test).

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

EMAIL = "ecriture@local.test"


def _client():
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(EMAIL))
    return c


def _prof_et_type(label="Compréhension"):
    """Le prof (couple Français / 6e en base) + un type RÉELLEMENT prêt pour ce niveau."""
    from _profil import type_pret, user_couple
    from backend.core.models_db import User
    with dbmod.SessionLocal() as db:
        if not db.query(User).filter(User.email == EMAIL).first():
            db.add(user_couple(db, email=EMAIL, password_hash="x", is_verified=True,
                               subject="Français", niveau="6e"))
        tid = type_pret(db, "6e", label=label)
        db.commit()
        return tid


def _corps(tid, **surcharges):
    return {
        "activite_type_id": tid, "sous_type": None, "nb": 5, "avec_correction": False,
        "objet": "Le récit d'aventure", "ton": "academique",
        "texte_source": "Un texte source.", "resultat": "# Activité v1", **surcharges,
    }


def test_le_libelle_vient_de_la_base_pas_du_client():
    """Le client peut écrire ce qu'il veut : c'est `types_activite.label` qui est enregistré."""
    from backend.core.models_db import Activite
    tid = _prof_et_type()
    r = _client().post("/api/contenus/activites",
                       json=_corps(tid, activite_label="LIBELLÉ INVENTÉ PAR LE CLIENT"))
    assert r.status_code == 200, r.text
    aid = r.json()["id"]
    with dbmod.SessionLocal() as db:
        assert db.query(Activite).filter(Activite.id == aid).one().activite_label == "Compréhension"


def test_libelle_absent_du_corps_l_ecriture_marche_quand_meme():
    """L'écran n'envoie plus de libellé du tout : le serveur le sait, il le relit."""
    from backend.core.models_db import Activite
    tid = _prof_et_type()
    r = _client().post("/api/contenus/activites", json=_corps(tid))
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        a = db.query(Activite).filter(Activite.id == r.json()["id"]).one()
        assert a.activite_label == "Compréhension"


def test_le_put_relit_lui_aussi_le_libelle():
    from backend.core.models_db import Activite
    tid = _prof_et_type()
    aid = _client().post("/api/contenus/activites", json=_corps(tid)).json()["id"]
    r = _client().put(f"/api/contenus/activites/{aid}",
                      json=_corps(tid, resultat="# v2", activite_label="ENCORE UN INVENTÉ"))
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        assert db.query(Activite).filter(Activite.id == aid).one().activite_label == "Compréhension"


def test_type_inconnu_refuse_et_rien_ecrit():
    from backend.core.models_db import Activite
    _prof_et_type()
    avant = _nb_activites()
    r = _client().post("/api/contenus/activites", json=_corps(999999))
    assert r.status_code == 400
    assert r.json()["detail"] == "Type d'activité inconnu."   # le message de la génération
    assert _nb_activites() == avant


def test_type_desactive_au_catalogue_refuse():
    from backend.core.models_db import ActiviteType
    tid = _prof_et_type(label="Type à désactiver")
    with dbmod.SessionLocal() as db:
        db.query(ActiviteType).filter(ActiviteType.id == tid).one().actif = False
        db.commit()
    avant = _nb_activites()
    r = _client().post("/api/contenus/activites", json=_corps(tid))
    assert r.status_code == 400
    assert r.json()["detail"] == "Type d'activité inconnu."
    assert _nb_activites() == avant


def test_type_non_coche_pour_le_couple_refuse():
    """Le type existe et est actif, mais il n'est pas coché pour le référentiel du niveau :
    c'est exactement ce que la génération refuse déjà."""
    from backend.core.models_db import ActiviteType, ReferentielActiviteType
    _prof_et_type()
    with dbmod.SessionLocal() as db:
        orphelin = ActiviteType(label="Type non coché", ordre=9, actif=True, origine="systeme")
        db.add(orphelin)
        db.commit()
        tid = orphelin.id
        assert db.query(ReferentielActiviteType).filter(
            ReferentielActiviteType.activite_type_id == tid).count() == 0
    avant = _nb_activites()
    r = _client().post("/api/contenus/activites", json=_corps(tid))
    assert r.status_code == 400
    assert r.json()["detail"] == "Ce type d'activité n'est pas encore prêt pour ce niveau."
    assert _nb_activites() == avant


def test_mes_stats_compte_le_vrai_libelle():
    """Le libellé figé alimente « Mes stats » (type favori) : il doit venir de la base."""
    tid = _prof_et_type()
    for i in range(2):
        _client().post("/api/contenus/activites",
                       json=_corps(tid, resultat=f"# v{i}", activite_label="Faux libellé"))
    d = _client().get("/api/stats/perso").json()
    assert d["type_favori"] == "Compréhension"


def _nb_activites():
    from backend.core.models_db import Activite
    with dbmod.SessionLocal() as db:
        return db.query(Activite).count()
