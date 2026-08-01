"""Supprimer et éditer dans le monde neuf — ce qui meurt, ce qui survit.

Aucun DELETE n'existait dans backend/contenu/ : une séance ratée restait à vie, et une
séquence, sans PUT, était figée pour toujours. Vérifié ici :
  - ce que la suppression emporte est COMPTÉ EN BASE avant de confirmer (l'écran annonce des
    nombres vrais, pas un texte générique) ;
  - supprimer une activité emporte son historique de versions (CASCADE) ;
  - supprimer une séance emporte son historique mais PAS ses activités : elles repassent en
    « non rangées » (SET NULL) ;
  - supprimer une séquence ne détruit pas ses séances, qui repassent en « non rangées » ;
  - cloisonnement : l'id d'un autre prof répond 404 (jamais 403, qui confirmerait l'existence)
    et RIEN n'est supprimé ;
  - le PUT d'une séquence corrige le formulaire SANS toucher au plan déjà généré.

Lance avec : pytest (BDD jetable aschool_test via conftest.py — jamais la base dev).
"""


import backend.core.database as dbmod  # noqa: E402  (redirigé vers aschool_test par conftest)

from backend.main import app  # noqa: E402
from backend.securite.comptes import create_access_token  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

EMAIL = "suppression@local.test"
INTRUS = "intrus-suppression@local.test"


def _client(email=EMAIL):
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(email))
    return c


def _prof(email=EMAIL):
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
    """Un type utilisable pour le niveau du prof (référentiel + liaison cochée) : depuis
    l'étape 8, l'écriture exige les mêmes contrôles que la génération."""
    from _profil import type_pret
    with dbmod.SessionLocal() as db:
        tid = type_pret(db, "6e")
        db.commit()
        return tid


def _activite(seance_id=None):
    """Une activité née par l'API (donc avec sa version de naissance)."""
    _prof()
    corps = {
        "activite_type_id": _type_id(), "activite_label": "Compréhension",
        "sous_type": None, "nb": 5, "avec_correction": False,
        "objet": "Le récit d'aventure", "ton": "academique",
        "texte_source": "src", "resultat": "# v1", "seance_id": seance_id,
    }
    return _client().post("/api/contenus/activites", json=corps).json()["id"]


def _sequence_avec_seances(nb=2):
    from backend.core.models_db import Seance, Sequence
    uid = _prof()
    with dbmod.SessionLocal() as db:
        seq = Sequence(user_id=uid, titre="Le récit d'aventure", matiere="Français", niveau="6e")
        db.add(seq)
        db.flush()
        for i in range(nb):
            db.add(Seance(user_id=uid, sequence_id=seq.id, position=i + 1,
                          titre=f"Séance {i + 1}", matiere="Français", niveau="6e"))
        db.commit()
        return seq.id


def _seance_seule():
    from backend.core.models_db import Seance, SeanceVersion
    uid = _prof()
    with dbmod.SessionLocal() as db:
        s = Seance(user_id=uid, titre="Séance libre", matiere="Français", niveau="6e",
                   resultat="# déroulé")
        db.add(s)
        db.flush()
        db.add(SeanceVersion(seance_id=s.id, jalon="generation", resultat="# déroulé"))
        db.commit()
        return s.id


def test_auth_obligatoire():
    assert TestClient(app).delete("/api/contenus/activites/1").status_code == 401


def test_supprimer_une_activite_emporte_son_historique():
    from backend.core.models_db import Activite, ActiviteVersion
    aid = _activite()
    # Un second jalon : l'historique compte 2 versions, la confirmation doit le dire.
    _client().put(f"/api/contenus/activites/{aid}", json={
        "activite_type_id": _type_id(), "activite_label": "Compréhension",
        "objet": "Le récit d'aventure", "avec_correction": False,
        "texte_source": "src", "resultat": "# v2"})

    impact = _client().get(f"/api/contenus/activites/{aid}/suppression").json()
    assert impact["versions"] == 2
    assert impact["titre"] == "Le récit d'aventure"

    assert _client().delete(f"/api/contenus/activites/{aid}").status_code == 200
    with dbmod.SessionLocal() as db:
        assert db.query(Activite).filter(Activite.id == aid).first() is None
        assert db.query(ActiviteVersion).filter(ActiviteVersion.activite_id == aid).count() == 0

    # L'historique n'est plus lisible, et la ligne a bien quitté Mes contenus.
    assert _client().get(f"/api/contenus/activites/{aid}/versions").status_code == 404
    ids = [c["id"] for c in _client().get("/api/mes-contenus").json()["contenus"]
           if c["type"] == "activite"]
    assert aid not in ids


def test_supprimer_une_seance_laisse_vivre_ses_activites():
    from backend.core.models_db import Activite, Seance, SeanceVersion
    sid = _seance_seule()
    aid = _activite(seance_id=sid)

    impact = _client().get(f"/api/contenus/seances/{sid}/suppression").json()
    assert impact["versions"] == 1
    assert impact["activites_liberees"] == 1        # ce qui SURVIT, annoncé aussi

    assert _client().delete(f"/api/contenus/seances/{sid}").status_code == 200
    with dbmod.SessionLocal() as db:
        assert db.query(Seance).filter(Seance.id == sid).first() is None
        assert db.query(SeanceVersion).filter(SeanceVersion.seance_id == sid).count() == 0
        a = db.query(Activite).filter(Activite.id == aid).one()
        assert a.seance_id is None                   # « non rangée », pas détruite

    ligne = next(c for c in _client().get("/api/mes-contenus").json()["contenus"]
                 if c["type"] == "activite" and c["id"] == aid)
    assert ligne["parent"] is None


def test_supprimer_une_sequence_laisse_vivre_ses_seances():
    from backend.core.models_db import Seance, Sequence
    seq_id = _sequence_avec_seances(nb=3)

    impact = _client().get(f"/api/contenus/sequences/{seq_id}/suppression").json()
    assert impact["seances_liberees"] == 3
    assert "versions" not in impact                  # une séquence n'a pas d'historique

    assert _client().delete(f"/api/contenus/sequences/{seq_id}").status_code == 200
    with dbmod.SessionLocal() as db:
        assert db.query(Sequence).filter(Sequence.id == seq_id).first() is None
        survivantes = db.query(Seance).filter(Seance.sequence_id.is_(None)).count()
        assert survivantes == 3

    d = _client().get("/api/mes-contenus").json()
    assert d["compteurs"]["seances"] == 3
    assert all(s["parent"] is None for s in d["contenus"] if s["type"] == "seance")


def test_cloisonnement_rien_n_est_supprime_pour_un_autre_prof():
    from backend.core.models_db import Activite, Seance, Sequence
    aid = _activite()
    sid = _seance_seule()
    seq_id = _sequence_avec_seances()
    _prof(INTRUS)
    autre = _client(INTRUS)

    for chemin in (f"/api/contenus/activites/{aid}", f"/api/contenus/seances/{sid}",
                   f"/api/contenus/sequences/{seq_id}"):
        assert autre.get(f"{chemin}/suppression").status_code == 404
        assert autre.delete(chemin).status_code == 404   # 404, pas 403

    with dbmod.SessionLocal() as db:
        assert db.query(Activite).filter(Activite.id == aid).first() is not None
        assert db.query(Seance).filter(Seance.id == sid).first() is not None
        assert db.query(Sequence).filter(Sequence.id == seq_id).first() is not None


def test_editer_une_sequence_sans_toucher_au_plan():
    from backend.core.models_db import Seance, Sequence
    seq_id = _sequence_avec_seances(nb=2)
    with dbmod.SessionLocal() as db:
        avant = [(s.id, s.titre, s.position) for s in
                 db.query(Seance).filter(Seance.sequence_id == seq_id)
                 .order_by(Seance.position).all()]

    r = _client().put(f"/api/contenus/sequences/{seq_id}", json={
        "objectif": "Le récit d'aventure — version corrigée",
        "contexte": "Classe de 27 élèves",
        "ampleur": "6 séances",
        "competences": ["Lire", "  ", "Écrire"],
    })
    assert r.status_code == 200, r.text

    with dbmod.SessionLocal() as db:
        seq = db.query(Sequence).filter(Sequence.id == seq_id).one()
        assert seq.titre == "Le récit d'aventure — version corrigée"
        assert seq.contexte == "Classe de 27 élèves"
        assert seq.ampleur == "6 séances"
        assert '"Lire"' in seq.competences and '"Écrire"' in seq.competences
        apres = [(s.id, s.titre, s.position) for s in
                 db.query(Seance).filter(Seance.sequence_id == seq_id)
                 .order_by(Seance.position).all()]
        assert apres == avant                        # le plan n'a pas bougé d'un iota


def test_editer_une_sequence_refus_objectif_vide_et_cloisonnement():
    from backend.core.models_db import Sequence
    seq_id = _sequence_avec_seances()
    corps = {"objectif": "   ", "contexte": "", "ampleur": "", "competences": []}
    assert _client().put(f"/api/contenus/sequences/{seq_id}", json=corps).status_code == 400

    _prof(INTRUS)
    assert _client(INTRUS).put(f"/api/contenus/sequences/{seq_id}", json={
        **corps, "objectif": "Détourné"}).status_code == 404
    with dbmod.SessionLocal() as db:
        assert db.query(Sequence).filter(Sequence.id == seq_id).one().titre == "Le récit d'aventure"
