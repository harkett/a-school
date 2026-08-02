"""Preuve — /auth/me dit si le profil ENREGISTRE tient toujours debout (`profil_coherent`).

L'ecran lisait deja ce champ (App.jsx : `user.profil_coherent === false`) et le serveur ne
l'envoyait JAMAIS. Il valait donc `undefined`, `undefined === false` est faux, et cette moitie
du garde-fou ne s'est pas executee une seule fois — seul `!user.subject` fonctionnait.

CE QUI PASSAIT A TRAVERS : un prof dont la matiere a cesse d'etre au programme de son niveau
(referentiel remplace, matiere retiree, niveau renomme) gardait un profil qui ne veut plus rien
dire, sans jamais etre ramene sur « Mon profil ». C'est exactement le cas que ce garde-fou etait
cense couvrir.

Ce fichier FIGE la valeur du champ dans les trois cas, parce qu'ils ne se valent pas :

  coherent    -> True   : la matiere du profil est au programme du niveau du profil.
  incoherent  -> False  : elle ne l'est plus. C'est CE cas qui ramene le prof sur son profil.
  profil vide -> None   : la question ne se pose pas encore. Ni True (mensonge), ni False (qui
                          enverrait reparer un profil qui n'existe pas). `null === false` vaut
                          faux en JavaScript : l'ecran se comporte comme avant, un profil vide
                          part par `!user.subject`.

Le champ est calcule sur le couple DU PROFIL (subject_id / niveau_id), jamais sur le couple de
travail : c'est le profil qui est en cause, et `couple_ajuste` couvre deja l'autre cas.

Lancer : docker compose exec backend python -m pytest tests/test_auth_me_profil_coherent.py -q
"""
from fastapi.testclient import TestClient

# engine / SessionLocal rediriges vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod
from backend.core.models_db import Cycle, Matiere, Niveau, Referentiel, User
from backend.main import app
from backend.securite.comptes import create_access_token

EMAIL = "prof.coherence@aschool.fr"


def _client(email=EMAIL):
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(email))
    return c


def _semer():
    """Un niveau PC-6e dont le referentiel nomme PC-Fr, et PC-HG qui appartient au referentiel
    d'un AUTRE niveau — donc hors du programme de PC-6e. C'est la situation exacte que produit
    un remplacement de referentiel : la matiere existe encore, mais plus a ce niveau-la."""
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom="PC-College", ordre=91)
        db.add(cy); db.flush()
        n6 = Niveau(cycle_id=cy.id, nom="PC-6e", ordre=1)
        n5 = Niveau(cycle_id=cy.id, nom="PC-5e", ordre=2)
        db.add_all([n6, n5]); db.flush()
        ref6 = Referentiel(niveau_id=n6.id, nom_fixe="pc_6e", collection="pc_6e")
        ref5 = Referentiel(niveau_id=n5.id, nom_fixe="pc_5e", collection="pc_5e")
        db.add_all([ref6, ref5]); db.flush()
        mfr = Matiere(referentiel_id=ref6.id, nom="PC-Fr", ordre=911, validee=True)
        mhg = Matiere(referentiel_id=ref5.id, nom="PC-HG", ordre=912, validee=True)
        db.add_all([mfr, mhg]); db.flush()
        db.add(User(email=EMAIL, password_hash="x", is_verified=True))
        db.commit()
        return {"n6": n6.id, "fr": mfr.id, "hg": mhg.id}


def _poser_profil(subject_id, niveau_id):
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        u.subject_id, u.niveau_id = subject_id, niveau_id
        db.commit()


def _me():
    r = _client().get("/api/auth/me")
    assert r.status_code == 200, r.text
    return r.json()


def test_le_champ_est_reellement_dans_la_reponse():
    """Le coeur du trou : le champ n'existait pas cote serveur. Sa PRESENCE se teste a part de
    sa valeur — un `.get()` qui rend None ne dirait pas la difference entre « absent » et
    « null », or c'est precisement la confusion qui a laisse passer le defaut pendant des mois."""
    _semer()
    assert "profil_coherent" in _me(), (
        "/auth/me n'envoie pas profil_coherent : l'ecran lit un champ inexistant")


def test_profil_coherent_vrai_quand_la_matiere_est_au_programme():
    ids = _semer()
    _poser_profil(ids["fr"], ids["n6"])

    corps = _me()
    assert corps["profil_coherent"] is True
    assert corps["subject"] == "PC-Fr" and corps["niveau"] == "PC-6e"


def test_profil_coherent_faux_quand_la_matiere_n_est_plus_au_programme():
    """LE cas qui ne se declenchait jamais. La matiere existe toujours en base, mais elle
    appartient au referentiel d'un autre niveau : elle n'est plus au programme de celui du prof."""
    ids = _semer()
    _poser_profil(ids["hg"], ids["n6"])

    corps = _me()
    assert corps["profil_coherent"] is False, (
        "un profil devenu hors programme est annonce coherent : le prof n'est jamais ramene "
        "sur « Mon profil »")
    # L'ecran teste `=== false` : la valeur doit etre le booleen, pas une chaine ni un 0.
    assert corps["profil_coherent"] is not None


def test_profil_vide_rend_null_et_ne_declenche_pas_ce_chemin():
    """Un profil vide n'est pas « incoherent », il est absent. Il part deja par `!user.subject`.
    `null` le dit ; `false` enverrait le prof reparer quelque chose qui n'existe pas."""
    _semer()   # aucun profil pose

    corps = _me()
    assert corps["profil_coherent"] is None
    assert corps["subject"] is None and corps["niveau"] is None


def test_un_niveau_sans_matiere_posee_rend_null_aussi():
    """Demi-profil : le niveau est choisi, la matiere pas encore. La question « cette matiere
    est-elle au programme » n'a pas d'objet — on ne repond pas False a une question qu'on ne
    peut pas poser."""
    ids = _semer()
    _poser_profil(None, ids["n6"])

    assert _me()["profil_coherent"] is None


def test_le_champ_suit_le_profil_et_non_le_couple_de_travail():
    """Le couple de TRAVAIL peut differer du profil sans que le profil soit en cause — c'est
    `couple_ajuste` qui porte ce cas. Un prof au profil sain qui travaille ailleurs ne doit pas
    etre renvoye sur « Mon profil »."""
    ids = _semer()
    _poser_profil(ids["fr"], ids["n6"])
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        u.travail_matiere_id, u.travail_niveau_id = ids["hg"], ids["n6"]
        db.commit()

    corps = _me()
    assert corps["profil_coherent"] is True, "le champ a suivi le couple de travail, pas le profil"
    assert corps["couple_ajuste"] is True   # l'ecart, lui, est bien signale — par l'autre champ
