r"""Le couple écrit sur une activité est celui contre lequel son type vient d'être contrôlé.

CE QUE CE TEST PROUVE, et pourquoi il existe. `PUT /contenus/activites/{id}` (régénération)
contrôle le type contre le couple de travail ACTUEL du prof — `_controler_type_et_label(db,
niveau, ...)`, la même porte qu'à la génération. Mais il ne réécrivait PAS `activite.matiere`
et `activite.niveau` : la ligne gardait le couple de sa NAISSANCE.

Le prof qui change de couple (« Changer niveau et/ou matière ») puis régénère écrivait donc un
type valable en 3e sur une ligne étiquetée 6e. Et cette étiquette n'est pas décorative :
  - « Mes stats » compte les activités PAR couple (`Activite.matiere` / `.niveau`) ;
  - le few-shot « aSchool vous reconnaît » ne prend en exemple que les activités du MÊME type
    ET du MÊME couple (few_shot_du_prof, activites.py) — un couple faux fausse le style rendu.
Rien ne tombait : la génération marchait, elle comptait juste dans la mauvaise colonne.

La séance faisait DÉJÀ suivre son couple à chaque régénération (`_remplir_seance`). Les deux
frères se comportent maintenant pareil.

Lancer : docker compose exec backend python -m pytest tests/test_couple_de_l_activite_suit_la_regeneration.py -q
"""
# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.core.models_db import Activite, User
from backend.main import app
from backend.securite.comptes import create_access_token
from fastapi.testclient import TestClient

EMAIL = "bascule-couple@local.test"


def _client():
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(EMAIL))
    return c


def _prof_sur_6e():
    """Le prof, couple de PROFIL Français/6e, et le type « Compréhension » prêt des DEUX côtés.

    Deux types DISTINCTS, un par référentiel : depuis le 05/08/2026 un type appartient au document
    qui le nomme, donc « Compréhension » en 6e et « Compréhension » en 3e sont deux lignes — comme
    deux matières homonymes dans deux diplômes. Le test renvoie les deux ids : après la bascule de
    couple, c'est celui de la 3e que l'écran du prof enverrait."""
    from _profil import matiere_id, niveau_id, type_pret, user_couple
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        if u is None:
            u = user_couple(db, email=EMAIL, password_hash="x", is_verified=True,
                            subject="Français", niveau="6e")
            db.add(u)
            db.flush()
        # Le MÊME type est prêt des deux côtés : le test porte sur le couple écrit, pas sur un refus.
        tid = type_pret(db, "6e", label="Compréhension")
        tid_3e = type_pret(db, "3e", label="Compréhension")
        matiere_3e = matiere_id(db, "Français", "3e")
        niveau_3e = niveau_id(db, "3e")
        # On repart toujours du profil : les tests ne se marchent pas dessus.
        u.travail_matiere_id = None
        u.travail_niveau_id = None
        db.commit()
        return tid, u.id, matiere_3e, niveau_3e, tid_3e


def _corps(tid, resultat="# v1"):
    return {"activite_type_id": tid, "sous_type": None, "nb": 5, "avec_correction": False,
            "objet": "Le récit", "ton": "academique",
            "texte_source": "Une idée.", "resultat": resultat}


def _basculer_sur_3e(user_id, matiere_3e, niveau_3e):
    with dbmod.SessionLocal() as db:
        u = db.get(User, user_id)
        u.travail_matiere_id = matiere_3e
        u.travail_niveau_id = niveau_3e
        db.commit()


def test_a_la_naissance_le_couple_est_celui_du_moment():
    tid, _, _, _, _ = _prof_sur_6e()
    r = _client().post("/api/contenus/activites", json=_corps(tid))
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        a = db.get(Activite, r.json()["id"])
        assert (a.matiere, a.niveau) == ("Français", "6e")


def test_apres_un_changement_de_couple_la_regeneration_reetiquette_la_ligne():
    """LA régression à empêcher : la ligne ne doit pas rester en 6e alors que son type vient
    d'être validé contre la 3e."""
    tid, user_id, matiere_3e, niveau_3e, tid_3e = _prof_sur_6e()
    c = _client()
    aid = c.post("/api/contenus/activites", json=_corps(tid)).json()["id"]

    _basculer_sur_3e(user_id, matiere_3e, niveau_3e)

    # Le type de la 3e : le prof qui a basculé de couple voit les types de SON nouveau niveau.
    r = c.put(f"/api/contenus/activites/{aid}", json=_corps(tid_3e, resultat="# v2"))
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        a = db.get(Activite, aid)
        assert a.niveau == "3e", (
            "L'activité reste étiquetée 6e alors que son type a été contrôlé contre la 3e : "
            "« Mes stats » compte dans la mauvaise colonne et le few-shot compare au mauvais couple."
        )
        assert a.matiere == "Français"
        assert a.resultat == "# v2"


def test_la_seance_faisait_deja_suivre_son_couple():
    """Le frère de référence : si ce comportement changeait côté séance, les deux divergeraient
    de nouveau — et c'est de cette divergence qu'est né le défaut."""
    import inspect
    from backend.contenu import mes_contenus
    source = inspect.getsource(mes_contenus._remplir_seance)
    assert "seance.matiere" in source and "seance.niveau" in source
