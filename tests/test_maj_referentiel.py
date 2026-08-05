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

Le back visé est celui du LABO (backend/pedagogie/referentiels_labo.py), sur ses propres
routes /api/admin/labo/… — l'écran historique n'est plus concerné.

Lancer : docker compose exec backend python -m pytest tests/test_maj_referentiel.py -q
"""
from unittest.mock import patch

import backend.core.database as dbmod
import backend.pedagogie.referentiels_labo as reflabo
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
    return admin_client().post("/api/admin/labo/referentiels/supprimer", json={
        "cycle_id": m["cycle_id"], "niveau": m["niveau"], "bloquer_profs": bloquer})


def _propose(m, nom):
    """L'identifiant que l'écran propose d'office pour une matière attendue : celle du nouveau
    référentiel qui porte le MÊME nom."""
    q = f"cycle_id={m['cycle_id']}&niveau={m['niveau']}"
    etat = admin_client().get(f"/api/admin/labo/referentiels/correspondances?{q}").json()
    return next(a["propose"] for a in etat["attendues"] if a["nom"] == nom)


def _recreer_referentiel(m, matieres, validee=True):
    """Ce que fait la procédure refaite : un NOUVEAU référentiel pour le même niveau, avec de
    NOUVEAUX identifiants de matières. C'est tout l'enjeu du remplacement par le nom.
    `validee=False` = les matières sont PROPOSÉES par la détection, l'admin ne les a pas encore
    cochées — un profil ne peut pas les porter."""
    with dbmod.SessionLocal() as db:
        ref = Referentiel(niveau_id=m["niveau_id"], nom_fixe=f"maj_{m['niveau_id']}",
                          collection=f"maj_{m['niveau_id']}", fichier="nouveau.pdf",
                          texte_epure="NOUVEAU TEXTE")
        db.add(ref); db.commit(); db.refresh(ref)
        for i, nom in enumerate(matieres):
            db.add(Matiere(referentiel_id=ref.id, nom=nom, ordre=i, actif=True, validee=validee))
        db.commit()


def _valider_matieres(m):
    """L'admin coche les matières du nouveau document."""
    with dbmod.SessionLocal() as db:
        rid = db.query(Referentiel.id).filter(Referentiel.niveau_id == m["niveau_id"]).scalar()
        db.query(Matiere).filter(Matiere.referentiel_id == rid).update({"validee": True})
        db.commit()


def _debloquer(m, correspondances):
    with patch.object(reflabo, "_avis_maj"):
        return admin_client().post("/api/admin/labo/referentiels/debloquer", json={
            "cycle_id": m["cycle_id"], "niveau": m["niveau"], "correspondances": correspondances})


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

    with patch.object(reflabo, "_avis_maj"):                # l'e-mail part après le commit
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
    with patch.object(reflabo, "_avis_maj"):
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
    with patch.object(reflabo, "_avis_maj"):
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
    with patch.object(reflabo, "_avis_maj"):
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
    """La procédure refaite recrée les matières avec de NOUVEAUX identifiants. Le nouveau document
    porte le MÊME nom : la correspondance est proposée d'office, l'admin n'a qu'à la valider. Le
    prof retrouve sa matière sans rien faire, et lit le second message quand il revient, pas au
    moment où l'admin clique."""
    m = _monde(niveau="MAJ-N5", email="maj5@test.fr")
    with patch.object(reflabo, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200
    _recreer_referentiel(m, ["Mathématiques", "Français"])
    with patch.object(reflabo, "_avis_maj"):
        r = admin_client().post("/api/admin/labo/referentiels/debloquer",
                                json={"cycle_id": m["cycle_id"], "niveau": m["niveau"],
                                      "correspondances": {"Mathématiques": _propose(m, "Mathématiques")}})
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


def test_situation_4_la_matiere_est_remplacee_pas_perdue():
    """Le nouveau document ne porte plus le même nom : la matière n'a pas disparu, elle a été
    RENOMMÉE. L'admin désigne celle qui prend sa place, le prof est rebranché dessus, et son
    message nomme l'ancienne ET la nouvelle — sans les deux, il découvrirait une autre matière à
    son profil sans savoir pourquoi."""
    m = _monde(niveau="MAJ-N6", email="maj6@test.fr")
    with patch.object(reflabo, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200
    _recreer_referentiel(m, ["Sciences numériques"])            # « Mathématiques » a été renommée

    # Ce que l'écran affiche pour trancher : la matière attendue, et ce que le document propose.
    q = f"cycle_id={m['cycle_id']}&niveau={m['niveau']}"
    etat = admin_client().get(f"/api/admin/labo/referentiels/correspondances?{q}").json()
    assert etat["prete"] is True
    assert etat["attendues"] == [{"nom": "Mathématiques", "profs": 1,
                                  "propose": None,            # aucun même nom : rien d'évident
                                  "peut_disparaitre": False}]  # un prof l'attend : elle ne peut pas
    cible = etat["matieres"][0]["id"]

    with patch.object(reflabo, "_avis_maj"):
        r = admin_client().post("/api/admin/labo/referentiels/debloquer",
                                json={"cycle_id": m["cycle_id"], "niveau": m["niveau"],
                                      "correspondances": {"Mathématiques": cible}})
    assert r.status_code == 200, r.text
    assert r.json()["rebranches"] == [] and r.json()["non_rebranches"] == []
    assert r.json()["remplaces"] == [{"prenom": "Ada", "nom": "Lovelace", "email": m["email"],
                                      "avant": "Mathématiques", "apres": "Sciences numériques"}]

    with dbmod.SessionLocal() as db:
        u = db.get(User, m["user_id"])
        assert db.get(Matiere, u.subject_id).nom == "Sciences numériques"   # rebranché, pas perdu

    c = prof_client(m["email"])
    me = c.get("/api/auth/me").json()
    assert me["blocage"]["type"] == "remplace"
    assert "Mathématiques" in me["blocage"]["message"]          # l'ancienne est nommée…
    assert "Sciences numériques" in me["blocage"]["message"]    # …et la nouvelle aussi

    # L'admin garde la trace nominative après coup — pas seulement dans la boîte affichée au clic.
    b = admin_client().get(f"/api/admin/labo/referentiels/blocages?{q}")
    assert b.json()["a_informer"] == 1 and b.json()["bloques"] == 0
    assert b.json()["profs"][0]["resultat"] == "remplace"
    assert b.json()["profs"][0]["matiere"] == "Mathématiques"


def test_le_deblocage_est_refuse_tant_que_tout_n_est_pas_tranche():
    """Les trois refus, dans l'ordre où l'admin les rencontre. Avant, débloquer trop tôt passait —
    et détachait tout le monde SANS RETOUR : la ligne quitte l'état `bloque`, aucun second
    déblocage ne la reprend."""
    m = _monde(niveau="MAJ-N8", email="maj8@test.fr")
    q = f"cycle_id={m['cycle_id']}&niveau={m['niveau']}"
    with patch.object(reflabo, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200

    # 1. Aucun référentiel sur le niveau : la procédure n'a pas été refaite.
    etat = admin_client().get(f"/api/admin/labo/referentiels/correspondances?{q}").json()
    assert etat["prete"] is False and "Aucun référentiel" in etat["empechement"]
    r = _debloquer(m, {})
    assert r.status_code == 409 and "Aucun référentiel" in r.json()["detail"]

    # 2. Un référentiel, mais ses matières ne sont que PROPOSÉES — l'admin ne les a pas cochées.
    #    C'est LE cas qui détachait tout le monde en silence : `matiere_id_du_nom` n'accepte que
    #    les matières retenues, le nom ne se résolvait pas, tout passait en « matière disparue ».
    _recreer_referentiel(m, ["Mathématiques"], validee=False)
    etat = admin_client().get(f"/api/admin/labo/referentiels/correspondances?{q}").json()
    assert etat["prete"] is False and "aucune matière retenue" in etat["empechement"]
    assert _debloquer(m, {}).status_code == 409

    # 3. Tout est en place, mais l'admin n'a pas dit par quoi remplacer.
    _valider_matieres(m)
    etat = admin_client().get(f"/api/admin/labo/referentiels/correspondances?{q}").json()
    assert etat["prete"] is True
    r = _debloquer(m, {})
    assert r.status_code == 409 and "Mathématiques" in r.json()["detail"]

    with dbmod.SessionLocal() as db:                    # RIEN n'a bougé pendant ces trois refus
        ligne = db.query(ProfBloqueMaj).filter(ProfBloqueMaj.user_id == m["user_id"]).one()
        assert ligne.etat == "bloque" and ligne.resultat is None


def test_une_matiere_qu_un_prof_attend_ne_peut_pas_disparaitre():
    """La règle métier : une matière utilisée ne s'efface pas, elle se remplace. « Elle disparaît
    vraiment » n'est même pas proposé à l'écran (`peut_disparaitre`), et le serveur le refuse."""
    m = _monde(niveau="MAJ-N9", email="maj9@test.fr")
    with patch.object(reflabo, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200
    _recreer_referentiel(m, ["Sciences numériques"])
    q = f"cycle_id={m['cycle_id']}&niveau={m['niveau']}"
    etat = admin_client().get(f"/api/admin/labo/referentiels/correspondances?{q}").json()
    assert etat["attendues"][0]["peut_disparaitre"] is False

    r = _debloquer(m, {"Mathématiques": None})
    assert r.status_code == 409, r.text
    assert "ne peuvent pas disparaître" in r.json()["detail"]
    assert "1 professeur(s)" in r.json()["detail"]

    # Et une matière de remplacement qui n'appartient pas à ce référentiel est refusée aussi.
    from _profil import matiere_id
    with dbmod.SessionLocal() as db:
        ailleurs = matiere_id(db, "Histoire", "MAJ-N9-Ailleurs")
        db.commit()
    r = _debloquer(m, {"Mathématiques": ailleurs})
    assert r.status_code == 422, r.text

    with dbmod.SessionLocal() as db:
        assert db.query(ProfBloqueMaj).filter(
            ProfBloqueMaj.user_id == m["user_id"]).one().etat == "bloque"


def test_le_prof_rattache_par_son_seul_couple_de_travail_ne_perd_rien():
    """Il travaillait sur ce niveau sans y avoir son profil : rien ne partait de son profil, donc
    on ne lui parle pas d'une matière perdue. Avant, il était compté dans « n'ont PAS pu être
    rebranchés » et lisait « la matière « votre matière » ne figure plus au programme » — faux
    des deux côtés."""
    from _profil import matiere_id, niveau_id
    m = _monde(niveau="MAJ-N10", email="maj10@test.fr")          # le prof du niveau, pour le blocage
    voisin = _monde(niveau="MAJ-Intact", matiere="Histoire", email="maj10b@test.fr")
    with dbmod.SessionLocal() as db:                             # son PROFIL est ailleurs…
        u = db.get(User, voisin["user_id"])
        u.travail_matiere_id = matiere_id(db, "Mathématiques", "MAJ-N10")   # …son TRAVAIL ici
        u.travail_niveau_id = niveau_id(db, "MAJ-N10")
        db.commit()
    with patch.object(reflabo, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200
    _recreer_referentiel(m, ["Mathématiques"])
    r = _debloquer(m, {"Mathématiques": _propose(m, "Mathématiques")})
    assert r.status_code == 200, r.text
    assert voisin["email"] in [p["email"] for p in r.json()["rebranches"]]
    assert r.json()["non_rebranches"] == []                      # il n'a rien perdu

    me = prof_client(voisin["email"]).get("/api/auth/me").json()
    assert me["blocage"]["type"] == "rebranche"
    assert "ne figure plus" not in me["blocage"]["message"]       # on ne lui invente pas une perte
    with dbmod.SessionLocal() as db:
        u = db.get(User, voisin["user_id"])
        assert db.get(Matiere, u.subject_id).nom == "Histoire"    # son profil n'a jamais bougé
        assert db.get(Matiere, u.travail_matiere_id).nom == "Mathématiques"   # son travail est rebranché


def test_l_e_mail_de_fin_ne_repete_pas_la_phrase_du_modele():
    """Le modèle `referentiel_maj_fin` porte DÉJÀ « La mise à jour est terminée… » suivi de
    {suite} : {suite} ne doit donc porter que CE QUI S'AJOUTE — le second paragraphe, et rien
    quand il n'y en a pas. Le prof rattaché par son seul couple de travail, dont le message tient
    en une phrase, la recevait deux fois."""
    from _profil import matiere_id, niveau_id
    m = _monde(niveau="MAJ-N11", email="maj11@test.fr")
    voisin = _monde(niveau="MAJ-Intact2", matiere="Histoire", email="maj11b@test.fr")
    with dbmod.SessionLocal() as db:
        u = db.get(User, voisin["user_id"])
        u.travail_matiere_id = matiere_id(db, "Mathématiques", "MAJ-N11")
        u.travail_niveau_id = niveau_id(db, "MAJ-N11")
        db.commit()
    with patch.object(reflabo, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200
    _recreer_referentiel(m, ["Sciences numériques"])

    q = f"cycle_id={m['cycle_id']}&niveau={m['niveau']}"
    cible = admin_client().get(
        f"/api/admin/labo/referentiels/correspondances?{q}").json()["matieres"][0]["id"]
    with patch.object(reflabo, "_avis_maj") as avis:
        r = admin_client().post("/api/admin/labo/referentiels/debloquer", json={
            "cycle_id": m["cycle_id"], "niveau": m["niveau"],
            "correspondances": {"Mathématiques": cible}})
    assert r.status_code == 200, r.text
    suites = {c.args[1].email: c.kwargs["suite"] for c in avis.call_args_list}

    # Lui : une seule phrase à l'écran → RIEN à ajouter dans l'e-mail.
    assert suites[voisin["email"]] == ""
    # L'autre : sa matière a été remplacée → la suite le dit, et ne redit pas la phrase du modèle.
    assert "est devenue" in suites[m["email"]]
    assert "La mise à jour est terminée" not in suites[m["email"]]


def test_les_lectures_de_contenus_survivent_au_blocage():
    """« Tout ce que vous avez créé est conservé » doit être VRAI : les lectures ne passent pas
    par la porte gardée, un prof bloqué consulte donc toujours son travail."""
    m = _monde(niveau="MAJ-N7", email="maj7@test.fr")
    with patch.object(reflabo, "_avis_maj"):
        assert _supprimer(m, bloquer=True).status_code == 200
    c = prof_client(m["email"])
    assert c.get("/api/mes-contenus").status_code == 200
    assert c.get("/api/contenus/seances/formulaire").status_code == 200
