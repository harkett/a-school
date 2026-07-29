"""« Mes contenus » — la bibliothèque à plat (brique 1 du chantier playlist).

GET /api/mes-contenus mélange les trois niveaux (séquences, séances, activités) dans UNE
liste : type, état de rangement (parent ou null), compteurs par type. Les activités viennent
de la table EXISTANTE `activites_sauvegardees` (zéro copie) ; séquences et séances des tables
neuves du socle. Vérifié ici :
  - auth : 401 sans cookie ;
  - bibliothèque vide = liste vide + compteurs à zéro (pas d'erreur, pas de repli) ;
  - mélange des types + compteurs + parent (« Rangée dans ») + titre d'activité (objet
    prioritaire sur le label) ;
  - cloisonnement : les contenus d'un autre prof n'apparaissent jamais ;
  - SET NULL en base : supprimer une séquence rend ses séances « non rangées », ne les
    détruit pas.

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

EMAIL = "contenus@local.test"


def _client(email=EMAIL):
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(email))
    return c


def _uid(email=EMAIL):
    from backend.core.models_db import User
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            u = User(email=email, password_hash="x", is_verified=True)
            db.add(u)
            db.commit()
            db.refresh(u)
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


def test_auth_obligatoire():
    assert TestClient(app).get("/api/mes-contenus").status_code == 401


def test_bibliotheque_vide():
    _uid()
    r = _client().get("/api/mes-contenus")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["contenus"] == []
    assert d["compteurs"] == {"tout": 0, "sequences": 0, "seances": 0, "activites": 0}


def test_liste_melangee_compteurs_et_rangement():
    from backend.core.models_db import Seance, Sequence
    uid = _uid()
    with dbmod.SessionLocal() as db:
        seq = Sequence(user_id=uid, titre="Le récit d'aventure", matiere="Français", niveau="6e")
        db.add(seq)
        db.flush()
        seq_id = seq.id
        db.add(Seance(user_id=uid, sequence_id=seq_id, position=1,
                      titre="Séance 1 : Introduction", matiere="Français", niveau="6e",
                      resultat="# Séance\ncontenu"))
        db.add(Seance(user_id=uid, titre="Séance libre", matiere="Français", niveau="6e"))
        db.commit()

    d = _client().get("/api/mes-contenus").json()
    assert d["compteurs"] == {"tout": 3, "sequences": 1, "seances": 2, "activites": 0}

    par_type = {}
    for c in d["contenus"]:
        par_type.setdefault(c["type"], []).append(c)

    assert par_type["sequence"][0]["nb_seances"] == 1
    rangee = next(s for s in par_type["seance"] if s["titre"] == "Séance 1 : Introduction")
    libre = next(s for s in par_type["seance"] if s["titre"] == "Séance libre")
    assert rangee["parent"] == {"type": "sequence", "id": seq_id, "titre": "Le récit d'aventure"}
    assert libre["parent"] is None


def test_l_ancien_monde_n_apparait_jamais():
    """DÉCISION utilisateur (29/07) : Mes contenus est le futur REMPLAÇANT — il ne lit que
    ses tables neuves. L'ancien monde (`sequences_sauvegardees` ET `activites_sauvegardees`)
    n'apparaît JAMAIS dans la bibliothèque."""
    from backend.core.models_db import ActiviteSauvegardee, SequenceSauvegardee
    uid = _uid()
    tid = _type_id()
    with dbmod.SessionLocal() as db:
        db.add(SequenceSauvegardee(user_id=uid, matiere="SVT", niveau="3e",
                                   theme="Photosynthèse", duree=55, mode="standard",
                                   description_classe="", resultat="# Séance"))
        db.add(ActiviteSauvegardee(user_id=uid, activite_type_id=tid, activite_label="Compréhension",
                                   niveau="3e", matiere="SVT", objet="Vieille activité",
                                   avec_correction=False, texte_source="t", resultat="r"))
        db.commit()
    d = _client().get("/api/mes-contenus").json()
    assert d["compteurs"] == {"tout": 0, "sequences": 0, "seances": 0, "activites": 0}
    assert d["contenus"] == []


def test_cloisonnement_entre_profs():
    from backend.core.models_db import Sequence
    autre = _uid("voisin@local.test")
    with dbmod.SessionLocal() as db:
        db.add(Sequence(user_id=autre, titre="Séquence du voisin"))
        db.commit()
    _uid()
    d = _client().get("/api/mes-contenus").json()
    assert d["contenus"] == []
    assert d["compteurs"]["tout"] == 0


def test_supprimer_une_sequence_ne_detruit_pas_ses_seances():
    """FK ON DELETE SET NULL : la séance survit et redevient « non rangée »."""
    from backend.core.models_db import Seance, Sequence
    uid = _uid()
    with dbmod.SessionLocal() as db:
        seq = Sequence(user_id=uid, titre="À supprimer")
        db.add(seq)
        db.flush()
        seq_id = seq.id
        db.add(Seance(user_id=uid, sequence_id=seq_id, titre="Séance survivante"))
        db.commit()
    with dbmod.SessionLocal() as db:
        db.delete(db.get(Sequence, seq_id))
        db.commit()
    with dbmod.SessionLocal() as db:
        s = db.query(Seance).filter(Seance.titre == "Séance survivante").one()
        assert s.sequence_id is None

    d = _client().get("/api/mes-contenus").json()
    assert d["compteurs"] == {"tout": 1, "sequences": 0, "seances": 1, "activites": 0}
    assert d["contenus"][0]["parent"] is None
