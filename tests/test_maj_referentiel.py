"""Mettre à jour un référentiel DÉJÀ EN SERVICE — le chantier complet, vérifié.

Le besoin : l'Éducation nationale publie une nouvelle version d'un programme, l'admin doit
pouvoir supprimer le référentiel et refaire la procédure MÊME QUAND des profs travaillent
dessus. Impossible avant : refus 409, et de toute façon la clé étrangère `fk_users_subject_id`
(NO ACTION) faisait ÉCHOUER l'écriture — pas un refus poli.

Ce que ces tests verrouillent, dans l'ordre du chantier :
  1. le refus 409 reste la règle ; seul le geste assumé (`bloquer_profs`) le contourne ;
  2. le détachement vide les DEUX colonnes du couple de travail — n'en vider qu'une ferait
     retomber le prof, silencieusement, sur le couple de son profil (un autre niveau) ;
  3. les TROIS questions de /auth/me ont des réponses distinctes : peut-il générer (niveau du
     couple), doit-on lui demander son profil (niveau du profil), a-t-il à lire (état de la ligne) ;
  4. les quatre situations réelles : bloqué ; profil en travaux mais travaille ailleurs ;
     débloqué et rebranché ; matière disparue du nouveau document.

Lancer : docker compose exec backend python -m pytest tests/test_maj_referentiel.py -q
"""
from unittest.mock import patch

import backend.core.database as dbmod
import backend.pedagogie.referentiels_admin as refadm
from backend.core.models_db import Matiere, ProfBloqueMaj, Referentiel, User
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


def _monde(niveau="MAJ-Niv", matiere="Mathématiques", email="maj.prof@test.fr", ordre=60):
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
        cycle_id = db.query(Referentiel).filter(Referentiel.niveau_id == nid).first().niveau_id
        from backend.core.models_db import Niveau
        cycle_id = db.get(Niveau, nid).cycle_id
        return {"user_id": u.id, "email": email, "niveau": niveau, "niveau_id": nid,
                "matiere": matiere, "matiere_id": mid, "cycle_id": cycle_id}


def _supprimer(m, bloquer):
    return admin_client().post("/api/admin/referentiels/supprimer", json={
        "cycle_id": m["cycle_id"], "niveau": m["niveau"], "bloquer_profs": bloquer})


def _recreer_referentiel(m, matieres):
    """Ce que fait la procédure refaite : un NOUVEAU référentiel pour le même niveau, avec de
    NOUVEAUX identifiants de matières. C'est tout l'enjeu du rebranchement par le nom."""
    with dbmod.SessionLocal() as db:
        ref = Referentiel(niveau_id=m["niveau_id"], nom_fixe=f"maj_{m['niveau_id']}",
                          collection=f"maj_{m['niveau_id']}", fichier="nouveau.pdf",
                          texte_epure="NOUVEAU TEXTE")
        db.add(ref); db.commit(); db.refresh(ref)
        for i, nom in enumerate(matieres):
            db.add(Matiere(referentiel_id=ref.id, nom=nom, ordre=i, actif=True, validee=True))
        db.commit()


def test_le_refus_reste_la_regle_seul_le_geste_assume_le_contourne():
    """Point ferme : une suppression appelée autrement reste refusée. Le 409 ne disparaît pas,
    il est contourné par le drapeau que seule la seconde boîte de dialogue pose."""
    m = _monde(niveau="MAJ-N1", email="maj1@test.fr")
    r = _supprimer(m, bloquer=False)
    assert r.status_code == 409, r.text
    assert "professeur(s) travaillent" in r.json()["detail"]
    with dbmod.SessionLocal() as db:                       # rien n'a bougé
        assert db.query(Referentiel).filter(Referentiel.niveau_id == m["niveau_id"]).count() == 1
        assert db.query(ProfBloqueMaj).filter(ProfBloqueMaj.user_id == m["user_id"]).count() == 0

    with patch.object(refadm, "_avis_maj"):                # l'e-mail part après le commit
        r = _supprimer(m, bloquer=True)
    assert r.status_code == 200, r.text                    # AVANT : impossible, quoi qu'on fasse
    assert r.json()["profs_bloques"] == 1
    with dbmod.SessionLocal() as db:
        assert db.query(Referentiel).filter(Referentiel.niveau_id == m["niveau_id"]).count() == 0
        ligne = db.query(ProfBloqueMaj).filter(ProfBloqueMaj.user_id == m["user_id"]).one()
        assert ligne.etat == "bloque"
        assert ligne.matiere_nom == "Mathématiques"        # la MÉMOIRE, par le nom
        u = db.get(User, m["user_id"])
        assert u.subject_id is None                        # détachée : c'est ce qui rend la
        assert u.niveau_id == m["niveau_id"]               # suppression possible ; le niveau reste


def test_le_detachement_vide_les_deux_colonnes_du_couple_de_travail():
    """Le trou qu'on a failli creuser : `couple_de_travail` exige les DEUX clés. N'en vider
    qu'une la ferait retomber SILENCIEUSEMENT sur le couple du profil — un autre niveau, non
    bloqué, sur lequel le prof n'a jamais demandé à travailler."""
    from _profil import matiere_id, niveau_id
    m = _monde(niveau="MAJ-N2", email="maj2@test.fr")
    with dbmod.SessionLocal() as db:                       # son couple de TRAVAIL vise ce niveau
        u = db.get(User, m["user_id"])
        u.travail_matiere_id = matiere_id(db, "Mathématiques", "MAJ-N2")
        u.travail_niveau_id = niveau_id(db, "MAJ-N2")
        db.commit()
    with patch.object(refadm, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200
    with dbmod.SessionLocal() as db:
        u = db.get(User, m["user_id"])
        assert u.travail_matiere_id is None
        assert u.travail_niveau_id is None                 # LES DEUX, jamais une seule
        ligne = db.query(ProfBloqueMaj).filter(ProfBloqueMaj.user_id == m["user_id"]).one()
        assert ligne.travail_matiere_nom == "Mathématiques"
        assert ligne.travail_niveau_id == m["niveau_id"]   # mémorisé pour le rebranchement


def test_situation_1_prof_bloque_sur_son_couple():
    """Il ne peut plus générer, il lit le message, et on ne lui demande PAS de compléter son
    profil — c'est nous qui avons vidé sa matière."""
    m = _monde(niveau="MAJ-N3", email="maj3@test.fr")
    with patch.object(refadm, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200
    c = prof_client(m["email"])

    r = c.post("/api/detect-ambiguites", json={"texte": "Analysez le document."})
    assert r.status_code == 409, r.text
    assert "en cours de mise à jour" in r.json()["detail"]      # jamais une erreur technique
    assert "momentanément indisponible" in r.json()["detail"]

    me = c.get("/api/auth/me").json()
    assert me["blocage"]["type"] == "en_cours"
    assert "en cours de mise à jour" in me["blocage"]["message"]
    assert me["profil_en_travaux"] is True                      # → l'écran ne l'envoie pas au profil
    assert me["subject"] is None                                # sa matière est bien détachée


def test_situation_2_profil_en_travaux_mais_travaille_sur_un_niveau_intact():
    """Il travaille ailleurs, sur un niveau qu'on n'a pas touché : il GÉNÈRE normalement — le
    message « le programme de VOTRE niveau » serait faux pour lui. Et il ne doit surtout pas
    être envoyé sur « Mon profil » : sa matière de profil manque parce que NOUS l'avons ôtée."""
    from _profil import matiere_id, niveau_id
    m = _monde(niveau="MAJ-N4", email="maj4@test.fr")
    with dbmod.SessionLocal() as db:                            # couple de travail AILLEURS
        u = db.get(User, m["user_id"])
        u.travail_matiere_id = matiere_id(db, "Histoire", "MAJ-Intact")
        u.travail_niveau_id = niveau_id(db, "MAJ-Intact")
        db.commit()
    with patch.object(refadm, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200
    c = prof_client(m["email"])

    with patch("backend.analyse.ambiguites.generate",
               return_value='{"ambiguites": [], "verdict": "ok"}'):
        r = c.post("/api/detect-ambiguites", json={"texte": "Analysez le document."})
    assert r.status_code == 200, r.text                         # il travaille, et c'est juste

    me = c.get("/api/auth/me").json()
    assert me["blocage"] is None                                # aucun message : il n'est pas concerné
    assert me["profil_en_travaux"] is True                      # mais son profil est protégé
    assert me["subject"] is None                                # sans ça, « Mon profil » l'attrapait


def test_situation_3_debloque_et_rebranche():
    """La procédure refaite recrée les matières avec de NOUVEAUX identifiants. Le prof les
    retrouve sans rien faire — rebranchement par le NOM — et lit le second message quand il
    revient, pas au moment où l'admin clique."""
    m = _monde(niveau="MAJ-N5", email="maj5@test.fr")
    with patch.object(refadm, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200
    _recreer_referentiel(m, ["Mathématiques", "Français"])
    with patch.object(refadm, "_avis_maj"):
        r = admin_client().post("/api/admin/referentiels/debloquer",
                                json={"cycle_id": m["cycle_id"], "niveau": m["niveau"]})
    assert r.status_code == 200, r.text
    assert [p["email"] for p in r.json()["rebranches"]] == [m["email"]]
    assert r.json()["non_rebranches"] == []

    with dbmod.SessionLocal() as db:
        u = db.get(User, m["user_id"])
        assert u.subject_id is not None
        assert u.subject_id != m["matiere_id"]                  # NOUVEL identifiant
        assert db.get(Matiere, u.subject_id).nom == "Mathématiques"   # même matière, à ses yeux

    c = prof_client(m["email"])
    me = c.get("/api/auth/me").json()
    assert me["blocage"]["type"] == "rebranche"
    assert "de nouveau générer" in me["blocage"]["message"]
    assert "Mathématiques" in me["blocage"]["message"]
    assert me["profil_en_travaux"] is True                      # tant qu'il n'a pas lu
    with patch("backend.analyse.ambiguites.generate",
               return_value='{"ambiguites": [], "verdict": "ok"}'):
        assert c.post("/api/detect-ambiguites", json={"texte": "x"}).status_code == 200

    assert c.post("/api/user/maj-lue").json()["lues"] == 1      # accusé de réception
    me = c.get("/api/auth/me").json()
    assert me["blocage"] is None and me["profil_en_travaux"] is False


def test_situation_4_matiere_disparue_du_nouveau_document():
    """Le nouveau document ne nomme plus sa matière : on n'invente rien. Il est libéré, le
    message la NOMME et l'envoie à son profil, et l'admin lit la liste nominative."""
    m = _monde(niveau="MAJ-N6", email="maj6@test.fr")
    with patch.object(refadm, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200
    _recreer_referentiel(m, ["Sciences numériques"])            # plus de « Mathématiques »
    with patch.object(refadm, "_avis_maj"):
        r = admin_client().post("/api/admin/referentiels/debloquer",
                                json={"cycle_id": m["cycle_id"], "niveau": m["niveau"]})
    assert r.status_code == 200, r.text
    assert r.json()["rebranches"] == []
    assert [p["email"] for p in r.json()["non_rebranches"]] == [m["email"]]

    c = prof_client(m["email"])
    me = c.get("/api/auth/me").json()
    assert me["blocage"]["type"] == "matiere_disparue"
    assert "Mathématiques" in me["blocage"]["message"]          # elle est NOMMÉE
    assert "Mon profil" in me["blocage"]["message"]             # et il sait quoi faire
    with dbmod.SessionLocal() as db:
        assert db.get(User, m["user_id"]).subject_id is None    # rien d'inventé

    # L'admin garde la trace nominative après coup — pas seulement dans la boîte affichée au clic.
    b = admin_client().get(f"/api/admin/referentiels/blocages?cycle_id={m['cycle_id']}&niveau={m['niveau']}")
    assert b.json()["a_informer"] == 1 and b.json()["bloques"] == 0
    assert b.json()["profs"][0]["resultat"] == "matiere_disparue"
    assert b.json()["profs"][0]["matiere"] == "Mathématiques"


def test_les_lectures_de_contenus_survivent_au_blocage():
    """« Tout ce que vous avez créé est conservé » doit être VRAI : les lectures ne passent pas
    par la porte gardée, un prof bloqué consulte donc toujours son travail."""
    m = _monde(niveau="MAJ-N7", email="maj7@test.fr")
    with patch.object(refadm, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200
    c = prof_client(m["email"])
    assert c.get("/api/mes-contenus").status_code == 200
    assert c.get("/api/contenus/seances/formulaire").status_code == 200
