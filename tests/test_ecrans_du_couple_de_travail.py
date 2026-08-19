"""Preuve de cloisonnement — un prof, deux couples, aucun débordement.

Un professeur peut enseigner deux couples matière/niveau sans rapport : BTS technique un jour,
Licence Ergothérapie deux jours plus tard. L'application le permet, c'est voulu. Ce qui ne l'est
pas : retrouver, en basculant de couple, les créations et les chiffres de l'autre.

Ce que ces tests PROUVENT (base aschool_test via conftest.py — JAMAIS SQLite) :
  1. `/api/dashboard` ne rend que les DERNIÈRES CRÉATIONS du couple de travail ;
  2. ses TOTAUX (séquences, séances, activités) ne comptent que ce couple ;
  3. ses compteurs d'ANALYSES ne comptent que les analyses lancées sur ce couple ;
  4. `/api/stats/perso` compte lui aussi par couple ;
  5. basculer le couple de travail change les deux écrans, sans rien réenregistrer.

Lancer : docker compose exec backend python -m pytest tests/test_ecrans_du_couple_de_travail.py -q
"""

import backend.core.database as dbmod  # noqa: E402  (redirigé vers aschool_test par conftest)

from backend.main import app  # noqa: E402
from backend.securite.comptes import create_access_token  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

EMAIL = "deux.couples@local.test"

# Deux mondes sans rapport, comme chez un vrai prof.
M_BTS, N_BTS = "Sciences et techniques industrielles", "BTS CIEL"
M_ERGO, N_ERGO = "Ergonomie", "Licence Ergothérapie"


def _client():
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(EMAIL))
    return c


def _prof_des_deux_mondes():
    """Le prof, ses deux couples en base, et des contenus de chaque côté.

    Le profil porte le couple BTS ; le couple de TRAVAIL est posé ensuite par `_travailler_sur`,
    exactement comme le fait « Changer niveau et/ou matière » à l'écran.
    """
    from _profil import matiere_id, niveau_id, type_pret
    from backend.core.models_db import Activite, Seance, Sequence, ToolUsageLog, User

    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        if not u:
            u = User(email=EMAIL, password_hash="x", is_verified=True)
            db.add(u)
        u.subject_id = matiere_id(db, M_BTS, N_BTS)
        u.niveau_id = niveau_id(db, N_BTS)
        # La matière d'ergothérapie doit exister DANS son référentiel pour être choisissable.
        matiere_id(db, M_ERGO, N_ERGO)
        # `activites.activite_type_id` est obligatoire : un type par niveau, comme en vrai.
        type_bts = type_pret(db, N_BTS)
        type_ergo = type_pret(db, N_ERGO)
        db.flush()

        # BTS : deux activités, une séance, une séquence, une analyse d'ambiguïtés.
        for i in (1, 2):
            db.add(Activite(user_id=u.id, matiere=M_BTS, niveau=N_BTS,
                            activite_type_id=type_bts, activite_label="Compréhension",
                            objet=f"BTS {i}", texte_source="t", resultat="r"))
        db.add(Seance(user_id=u.id, matiere=M_BTS, niveau=N_BTS, titre="Séance BTS"))
        db.add(Sequence(user_id=u.id, matiere=M_BTS, niveau=N_BTS, titre="Séquence BTS"))
        db.add(ToolUsageLog(user_id=u.id, tool="ambiguites", score_label="2",
                            matiere=M_BTS, niveau=N_BTS))

        # Ergothérapie : une seule activité, et rien d'autre.
        db.add(Activite(user_id=u.id, matiere=M_ERGO, niveau=N_ERGO,
                        activite_type_id=type_ergo, activite_label="Compréhension",
                        objet="Ergo 1", texte_source="t", resultat="r"))
        db.commit()
        return u.id


def _travailler_sur(matiere, niveau):
    """Poser le couple de TRAVAIL, comme le bandeau du haut le fait."""
    from _profil import matiere_id, niveau_id
    from backend.core.models_db import User
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        u.travail_matiere_id = matiere_id(db, matiere, niveau)
        u.travail_niveau_id = niveau_id(db, niveau)
        db.commit()


def test_les_dernieres_creations_sont_celles_du_couple():
    _prof_des_deux_mondes()
    _travailler_sur(M_ERGO, N_ERGO)

    d = _client().get("/api/dashboard").json()

    assert d["derniere_activite"]["titre"] == "Ergo 1"
    # Le BTS a une séance et une séquence : elles NE DOIVENT PAS remonter ici.
    assert d["derniere_seance"] is None
    assert d["derniere_sequence"] is None


def test_les_totaux_ne_comptent_que_le_couple():
    _prof_des_deux_mondes()
    _travailler_sur(M_ERGO, N_ERGO)

    d = _client().get("/api/dashboard").json()

    assert d["mes_activites"] == 1        # 3 sur le compte, 1 en ergothérapie
    assert d["mes_seances"] == 0
    assert d["mes_sequences"] == 0


def test_les_analyses_ne_comptent_que_le_couple():
    _prof_des_deux_mondes()

    _travailler_sur(M_ERGO, N_ERGO)
    assert _client().get("/api/dashboard").json()["mes_ambiguites"] == 0

    _travailler_sur(M_BTS, N_BTS)
    assert _client().get("/api/dashboard").json()["mes_ambiguites"] == 1


def test_mes_stats_comptent_par_couple():
    _prof_des_deux_mondes()

    _travailler_sur(M_ERGO, N_ERGO)
    ergo = _client().get("/api/stats/perso").json()
    assert (ergo["activites_total"], ergo["seances"], ergo["sequences"]) == (1, 0, 0)

    _travailler_sur(M_BTS, N_BTS)
    bts = _client().get("/api/stats/perso").json()
    assert (bts["activites_total"], bts["seances"], bts["sequences"]) == (2, 1, 1)


def test_basculer_de_couple_change_les_deux_ecrans():
    """Le geste réel du prof : il ne réenregistre rien, il change de couple et tout suit."""
    _prof_des_deux_mondes()

    _travailler_sur(M_BTS, N_BTS)
    c = _client()
    assert c.get("/api/dashboard").json()["derniere_activite"]["titre"] == "BTS 2"

    _travailler_sur(M_ERGO, N_ERGO)
    assert c.get("/api/dashboard").json()["derniere_activite"]["titre"] == "Ergo 1"
