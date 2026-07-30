"""Couple de TRAVAIL EN BASE (décision du 25/07) — users.travail_matiere/travail_niveau.

Avant : le couple de travail ne vivait que dans la mémoire de la page (un F5 le remettait
au profil, la génération reposait sur une donnée absente de la base). Désormais :

Ce que ces tests PROUVENT :
  1. /auth/me : sans écart → couple résolu = PROFIL, couple_ajuste=false ; écart posé →
     couple résolu = TRAVAIL, couple_ajuste=true. Une seule règle (couple_de_travail).
  2. PUT /api/user/couple-travail : paire valide du programme → écrite en base ;
     paire HORS programme → 400 humain, RIEN écrit.
  3. PUT du propre couple de profil → efface l'écart (NULL) — on ne stocke jamais une
     copie du profil.
  4. DELETE (« Revenir à mon profil ») → écart effacé, /auth/me repasse au profil.
  5. LA PREUVE MAÎTRESSE : la génération utilise le couple de travail EN BASE — profil sur
     le niveau A, travail posé sur le niveau B → le RAG interroge la collection de B.

BDD de test PostgreSQL dédiée (aschool_test via conftest.py), RAG et LLM mockés.
"""
import os
import sys
from unittest.mock import patch

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod
from backend.main import app
from backend.auth import create_access_token
from fastapi.testclient import TestClient

EMAIL = "prof.ct@aschool.fr"
TOKEN = create_access_token(EMAIL)


def _client():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def _programme():
    """Deux niveaux d'un même cycle (CT-6e profil, CT-5e travail), chacun avec sa matière
    au programme (paires `matiere_niveaux`), + le prof (profil = CT-Fr × CT-6e) + un
    référentiel et un type SUR CT-5e (pour prouver que la génération suit le TRAVAIL).
    Renvoie (type_id_5e)."""
    from backend.core.models_db import (Cycle, Niveau, Matiere, MatiereNiveau, User,
                                        Referentiel, ActiviteType, ReferentielActiviteType)
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom="CT-College", ordre=80)
        db.add(cy); db.flush()
        n6 = Niveau(cycle_id=cy.id, nom="CT-6e", ordre=1)
        n5 = Niveau(cycle_id=cy.id, nom="CT-5e", ordre=2)
        db.add_all([n6, n5]); db.flush()
        mfr = Matiere(nom="CT-Fr", ordre=801)
        mhg = Matiere(nom="CT-HG", ordre=802)
        db.add_all([mfr, mhg]); db.flush()
        db.add_all([MatiereNiveau(matiere_id=mfr.id, niveau_id=n6.id),
                    MatiereNiveau(matiere_id=mfr.id, niveau_id=n5.id),
                    MatiereNiveau(matiere_id=mhg.id, niveau_id=n5.id)])
        db.add(User(email=EMAIL, password_hash="x", is_verified=True,
                    subject_id=mfr.id, niveau_id=n6.id))
        ref5 = Referentiel(niveau_id=n5.id, matiere_id=None, nom_fixe="ct_5e",
                           collection="ct_5e", filtres=None, fichier="doc.pdf",
                           texte_epure="TEXTE")
        db.add(ref5); db.flush()
        t = ActiviteType(label="CT-Type", ordre=1, actif=True, origine="systeme")
        db.add(t); db.flush()
        db.add(ReferentielActiviteType(referentiel_id=ref5.id, activite_type_id=t.id,
                                       actif=True, source="admin", ordre=1,
                                       prompt="Texte : {texte}\nNiveau {niveau}.\n{referentiel}"))
        db.commit()
        return t.id


def _travail_en_base():
    from backend.core.models_db import User
    from backend.core.resolution_couple import matiere_nom_de_id, niveau_nom_de_id
    with dbmod.SessionLocal() as db:
        u = db.query(User).filter(User.email == EMAIL).first()
        return matiere_nom_de_id(db, u.travail_matiere_id), niveau_nom_de_id(db, u.travail_niveau_id)


def test_me_resout_profil_puis_travail_et_couple_ajuste():
    _programme()
    c = _client()
    # Sans écart : le couple résolu EST le profil.
    me = c.get("/api/auth/me").json()
    assert (me["travail_matiere"], me["travail_niveau"]) == ("CT-Fr", "CT-6e")
    assert me["couple_ajuste"] is False
    # Écart posé : le couple résolu EST le travail.
    r = c.put("/api/user/couple-travail", json={"matiere": "CT-HG", "niveau": "CT-5e"})
    assert r.status_code == 200, r.text
    me = c.get("/api/auth/me").json()
    assert (me["travail_matiere"], me["travail_niveau"]) == ("CT-HG", "CT-5e")
    assert me["couple_ajuste"] is True
    assert _travail_en_base() == ("CT-HG", "CT-5e")   # la vérité est bien EN BASE


def test_put_hors_programme_400_humain_et_rien_ecrit():
    _programme()
    c = _client()
    # CT-HG n'est PAS au programme de CT-6e (paire absente de matiere_niveaux).
    r = c.put("/api/user/couple-travail", json={"matiere": "CT-HG", "niveau": "CT-6e"})
    assert r.status_code == 400, r.text
    assert "n'est pas enseignée à ce niveau" in r.json()["detail"]
    assert _travail_en_base() == (None, None)         # RIEN écrit


def test_put_du_couple_du_profil_efface_l_ecart():
    _programme()
    c = _client()
    c.put("/api/user/couple-travail", json={"matiere": "CT-HG", "niveau": "CT-5e"})
    # Revenir manuellement sur son propre profil = plus d'écart à stocker (NULL, pas une copie).
    r = c.put("/api/user/couple-travail", json={"matiere": "CT-Fr", "niveau": "CT-6e"})
    assert r.status_code == 200, r.text
    assert r.json()["couple_ajuste"] is False
    assert _travail_en_base() == (None, None)


def test_delete_revenir_au_profil():
    _programme()
    c = _client()
    c.put("/api/user/couple-travail", json={"matiere": "CT-HG", "niveau": "CT-5e"})
    r = c.delete("/api/user/couple-travail")
    assert r.status_code == 200, r.text
    assert _travail_en_base() == (None, None)
    me = c.get("/api/auth/me").json()
    assert (me["travail_matiere"], me["travail_niveau"]) == ("CT-Fr", "CT-6e")
    assert me["couple_ajuste"] is False


def test_generation_utilise_le_couple_de_travail_en_base():
    """Profil sur CT-6e, travail posé sur CT-5e : la génération DOIT chercher dans le
    référentiel de CT-5e — preuve que le couple généré = le couple de travail EN BASE."""
    tid = _programme()
    c = _client()
    assert c.put("/api/user/couple-travail",
                 json={"matiere": "CT-HG", "niveau": "CT-5e"}).status_code == 200
    capture = {}

    def _faux_rag(collection, query, filters=None, top_k=None):
        capture["collection"] = collection
        return [{"text": "Extrait officiel CT-5e.", "score": 0.9}]

    with patch("backend.contenu.activites.retrieve_pg", side_effect=_faux_rag), \
         patch("backend.contenu.activites.generate_stream", return_value=iter(["OK"])) as gen:
        r = c.post("/api/generate", json={"texte": "La ville au Moyen Âge.",
                                          "activite_type_id": tid})
    assert r.status_code == 200, r.text
    assert "event: done" in r.text
    assert capture["collection"] == "ct_5e"            # la collection du niveau de TRAVAIL
    assert "Niveau CT-5e." in gen.call_args.args[0]    # le prompt porte le niveau de TRAVAIL


# (test_sauvegarde_stampe_le_couple_du_serveur supprimé le 30/07 : POST /api/mes-activites
# a été démoli avec l'ancien monde ; le stampage serveur du couple reste prouvé sur
# /api/generate ci-dessus et par les écritures du monde neuf.)
