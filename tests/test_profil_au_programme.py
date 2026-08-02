"""Preuve — PATCH /user/profile porte le contrôle métier SERVEUR (paire au programme).

Ce que ces tests PROUVENT (base aschool_test via conftest.py — JAMAIS SQLite) :
  1. Une matière ABSENTE du programme du niveau (le référentiel du niveau ne la nomme pas) est
     refusée en 400 humain et RIEN n'est écrit — le front seul ne suffit plus (trou du 30/07).
  2. Une matière au programme s'écrit par clés (subject_id / niveau_id), comme avant.
  3. Une matière SANS niveau est refusée en 400 humain : depuis que la matière appartient au
     référentiel d'un niveau, elle ne se range nulle part sans lui. On le dit au prof plutôt
     que d'enregistrer un profil dont la matière serait silencieusement perdue.

Même règle et même message que PUT /user/couple-travail (couple_est_au_programme).

Lancer : docker compose exec backend python -m pytest tests/test_profil_au_programme.py -q
"""


import backend.core.database as dbmod
from backend.securite.comptes import create_access_token
from backend.core.models_db import Cycle, Matiere, Niveau, Referentiel, User
from backend.main import app
from fastapi.testclient import TestClient

EMAIL = "prof.programme@aschool.fr"


def _client():
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(EMAIL))
    return c


def _semer():
    """Cycle + niveau PP-6e, son référentiel qui nomme PP-Fr (retenue par l'admin), et PP-HG
    qui appartient au référentiel d'un AUTRE niveau — donc hors du programme de PP-6e.
    + le prof sans profil."""
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom="PP-College", ordre=90)
        db.add(cy); db.flush()
        n6 = Niveau(cycle_id=cy.id, nom="PP-6e", ordre=1)
        n5 = Niveau(cycle_id=cy.id, nom="PP-5e", ordre=2)
        db.add_all([n6, n5]); db.flush()
        ref6 = Referentiel(niveau_id=n6.id, nom_fixe="pp_6e", collection="pp_6e")
        ref5 = Referentiel(niveau_id=n5.id, nom_fixe="pp_5e", collection="pp_5e")
        db.add_all([ref6, ref5]); db.flush()
        mfr = Matiere(referentiel_id=ref6.id, nom="PP-Fr", ordre=901, validee=True)
        mhg = Matiere(referentiel_id=ref5.id, nom="PP-HG", ordre=902, validee=True)
        db.add_all([mfr, mhg]); db.flush()
        db.add(User(email=EMAIL, password_hash="x", is_verified=True))
        db.commit()
        return mfr.id, n6.id


def test_paire_hors_programme_400_et_rien_ecrit():
    _semer()
    r = _client().patch("/api/user/profile", json={"prenom": "Ana", "subject": "PP-HG", "niveau": "PP-6e"})
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Cette matière n'est pas enseignée à ce niveau dans les programmes. Choisissez une matière proposée pour ce niveau."
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        assert u.subject_id is None and u.niveau_id is None and u.prenom is None


def test_paire_au_programme_ecrite_par_cles():
    mfr_id, n6_id = _semer()
    r = _client().patch("/api/user/profile", json={"subject": "PP-Fr", "niveau": "PP-6e"})
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        assert u.subject_id == mfr_id and u.niveau_id == n6_id


def test_matiere_sans_niveau_refusee_et_rien_ecrit():
    """Une matière n'existe que dans le référentiel d'un niveau : sans niveau, elle ne se range
    nulle part. Refus explicite plutôt qu'un enregistrement qui perdrait la matière en silence."""
    _semer()
    r = _client().patch("/api/user/profile", json={"subject": "PP-Fr", "niveau": ""})
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Choisissez d'abord votre niveau : les matières proposées dépendent de son programme."
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        assert u.subject_id is None and u.niveau_id is None
