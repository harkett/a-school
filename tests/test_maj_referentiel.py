"""Mettre à jour un référentiel DÉJÀ EN SERVICE — ce qui protège les profs, et ce qui a été retiré.

CE FICHIER A CHANGÉ DE SUJET LE 07/08/2026, et c'est le fond de l'affaire.

Il verrouillait jusque-là un mécanisme de « blocage » : pour supprimer le référentiel d'un niveau
sur lequel des profs travaillaient, le serveur détachait lui-même leur matière
(`users.subject_id` remis à NULL), mémorisait le nom perdu dans une table `profs_bloques_maj`, et
refusait toute génération tant que la ligne existait — jusqu'à ce qu'un admin vienne la lever à
la main, depuis un écran du Labo (lui-même supprimé le 10/08/2026).

Ce mécanisme contournait la garde que la base pose déjà : `fk_users_subject_id` est en NO ACTION,
une matière portée par un prof NE PEUT PAS être supprimée. Le code désarmait cette contrainte
pour reconstruire en Python une protection que PostgreSQL assurait gratuitement — sauf que la
sienne ne se levait pas toute seule. Une ligne posée le 03/08/2026 par une suppression qui n'a
jamais abouti a laissé un compte incapable de générer pendant quatre jours, devant un référentiel
intact et une matière parfaitement valide.

CE QUE CES TESTS VERROUILLENT MAINTENANT :
  1. la clé étrangère tient : la base refuse la suppression d'une matière portée par un prof ;
  2. la route de suppression refuse AVANT d'écrire, avec un message qui dit quoi faire — et il
     n'existe plus aucun paramètre qui contourne ce refus ;
  3. rien ne coupe la génération d'un prof dont le couple est valide : `/auth/me` ne rend plus
     ni `blocage` ni `profil_en_travaux`, et générer ne dépend que du couple ;
  4. la table `profs_bloques_maj` n'existe plus, ni en base ni dans le code.

Lancer : docker compose exec backend python -m pytest tests/test_maj_referentiel.py -q
"""
import pytest
import sqlalchemy as sa

import backend.core.database as dbmod
from backend.core.models_db import Matiere, Niveau, Referentiel, User
from backend.main import app
from backend.securite.comptes import create_access_token
from fastapi.testclient import TestClient


def admin_client():
    from backend.systeme.admin import _make_admin_token
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def prof_client(email):
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(email))
    return c


def _monde(niveau="MAJ-Niv", matiere="Mathématiques", email="maj.prof@test.fr"):
    """Un prof au travail sur un référentiel réel : niveau, référentiel, matière retenue, profil."""
    from _profil import matiere_id, niveau_id, user_couple
    with dbmod.SessionLocal() as db:
        mid = matiere_id(db, matiere, niveau)
        nid = niveau_id(db, niveau)
        u = db.query(User).filter(User.email == email).first()
        if u is None:
            u = user_couple(db, email=email, password_hash="x", is_verified=True,
                            prenom="Ada", nom="Lovelace", subject=matiere, niveau=niveau)
            db.add(u)
        db.commit()
        db.refresh(u)
        return {"user_id": u.id, "email": email, "niveau": niveau, "niveau_id": nid,
                "matiere": matiere, "matiere_id": mid,
                "cycle_id": db.get(Niveau, nid).cycle_id}


def _supprimer(m, **extra):
    """La suppression de l'écran EN SERVICE (Admin > Référentiels).

    Elle passait par le labo jusqu'au 10/08/2026, jour où le labo a été supprimé. Même contrat,
    même refus 409 avec le même message : le mécanisme de blocage n'y était déjà plus."""
    corps = {"cycle_id": m["cycle_id"], "niveau": m["niveau"]}
    corps.update(extra)
    return admin_client().post("/api/admin/referentiels/supprimer", json=corps)


# ── 1. La base tient d'elle-même ──────────────────────────────────────────────────────────────

def test_la_cle_etrangere_refuse_de_supprimer_une_matiere_portee_par_un_prof():
    """LE test de fond : sans une ligne de Python, PostgreSQL empêche déjà le dégât.

    C'est ce qui rendait le mécanisme de blocage inutile — il ne protégeait de rien que la base
    ne protégeait pas, il ne faisait que se donner le droit de passer outre."""
    m = _monde(email="fk.prof@test.fr")
    with dbmod.SessionLocal() as db:
        with pytest.raises(sa.exc.IntegrityError):
            db.execute(sa.text("DELETE FROM matieres WHERE id = :i"), {"i": m["matiere_id"]})
            db.commit()
        db.rollback()
    # Et la matière est toujours là, portée par son prof.
    with dbmod.SessionLocal() as db:
        assert db.get(Matiere, m["matiere_id"]) is not None
        assert db.get(User, m["user_id"]).subject_id == m["matiere_id"]


# ── 2. La route refuse, et rien ne la contourne ───────────────────────────────────────────────

def test_la_suppression_est_refusee_tant_qu_un_prof_est_rattache():
    m = _monde(email="refus.prof@test.fr")
    r = _supprimer(m)
    assert r.status_code == 409
    assert "professeur" in r.json()["detail"]
    assert "Changez d'abord leur matière" in r.json()["detail"]
    with dbmod.SessionLocal() as db:
        assert db.query(Referentiel).filter(Referentiel.niveau_id == m["niveau_id"]).first() is not None


def test_aucun_parametre_ne_contourne_plus_le_refus():
    """`bloquer_profs` était LE chemin qui détachait les profs pour passer outre. Il n'existe
    plus : l'envoyer ne change rien — le refus tombe pareil, et le prof garde sa matière."""
    m = _monde(email="assume.prof@test.fr")
    assert _supprimer(m, bloquer_profs=True).status_code == 409
    with dbmod.SessionLocal() as db:
        assert db.get(User, m["user_id"]).subject_id == m["matiere_id"]


def test_la_suppression_passe_quand_plus_personne_n_est_rattache():
    """La contrepartie : l'admin change la matière du prof, et la suppression n'est plus refusée.
    C'est le chemin normal, et le seul."""
    m = _monde(email="libre.prof@test.fr")
    with dbmod.SessionLocal() as db:
        u = db.get(User, m["user_id"])
        u.subject_id = None
        u.travail_matiere_id = None
        u.travail_niveau_id = None
        db.commit()
    r = _supprimer(m)
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True}
    with dbmod.SessionLocal() as db:
        assert db.query(Referentiel).filter(Referentiel.niveau_id == m["niveau_id"]).first() is None


# ── 3. Plus rien ne coupe la génération ───────────────────────────────────────────────────────

def test_auth_me_ne_rend_plus_ni_blocage_ni_profil_en_travaux():
    """Les deux champs portaient le mécanisme jusqu'à l'écran. Ils sont partis avec lui : un
    écran qui les lirait encore ferait un test sur `undefined`, pas un blocage fantôme."""
    m = _monde(email="me.prof@test.fr")
    d = prof_client(m["email"]).get("/api/auth/me").json()
    assert "blocage" not in d
    assert "profil_en_travaux" not in d
    assert d["subject"] == m["matiere"]
    assert d["niveau"] == m["niveau"]


def test_le_couple_de_travail_ne_refuse_jamais():
    """`couple_de_travail` portait le 409 « mise à jour en cours », porte unique de ses vingt
    appelants. Elle résout un couple, désormais, et ne juge plus le droit de travailler."""
    from backend.prof.profil import couple_de_travail
    m = _monde(email="couple.prof@test.fr")
    with dbmod.SessionLocal() as db:
        matiere, niveau, ajuste = couple_de_travail(db, db.get(User, m["user_id"]))
    assert (matiere, niveau, ajuste) == (m["matiere"], m["niveau"], False)


# ── 4. Il n'en reste rien ─────────────────────────────────────────────────────────────────────

def test_la_table_des_blocages_n_existe_plus():
    with dbmod.SessionLocal() as db:
        existe = db.execute(sa.text(
            "SELECT to_regclass('public.profs_bloques_maj') IS NOT NULL")).scalar()
    assert existe is False, (
        "La table `profs_bloques_maj` est de retour. Elle reconstruisait en Python une garde "
        "que `fk_users_subject_id` assure déjà, sans jamais se lever toute seule."
    )


def test_le_modele_et_les_routes_de_deblocage_ont_disparu():
    """Le module qui portait le déblocage (`referentiels_labo`) a disparu entier le 10/08/2026 :
    on vérifie donc qu'il ne revient pas, et non plus qu'il ne contient pas telle fonction."""
    import importlib
    import backend.core.models_db as modeles
    assert not hasattr(modeles, "ProfBloqueMaj")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("backend.pedagogie.referentiels_labo")
    chemins = {r.path for r in app.routes if hasattr(r, "path")}
    assert "/api/admin/labo/referentiels/debloquer" not in chemins
    assert "/api/admin/labo/referentiels/blocages" not in chemins
    assert "/api/user/maj-lue" not in chemins
