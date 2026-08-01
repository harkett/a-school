"""Filet de test — les endpoints cœur d'aSchool.

Lance avec :  pytest   (suite pytest — convention unique du projet)

Couverture (happy path + cas d'erreur connus) — generate-sequence et optimize-sequence
ont été DÉMOLIS le 30/07 avec l'ancien monde :
  - detect-ambiguites, analyser-consigne
  - happy path : 200 + sortie cohérente (Groq MOCKÉ — aucun appel réseau)
  - auth      : 401 sans cookie / token invalide
  - validation: 400 (entrée vide / invalide)
  - résilience : panne LLM amont -> 500 (outils via generate())

Garde-fous : BDD de test PostgreSQL dédiée (aschool_test, via conftest.py — jamais la base dev),
user de test fictif, JWT signé via create_access_token (secret jamais exposé).
Verrouille l'existant contre une régression — n'introduit aucun comportement nouveau.
"""
import os
import sys
from unittest.mock import patch

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.main import app
from backend.securite.comptes import create_access_token
from fastapi.testclient import TestClient

TOKEN = create_access_token("filet-test@local.test")


def authed():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def _prof_filet():
    """Ambiguïtés et Consigne résolvent le couple EN BASE (couple_de_travail) : le prof
    du filet doit exister avec un profil complet (SVT × 3e, comme les anciens corps)."""
    from _profil import user_couple
    with dbmod.SessionLocal() as db:
        db.add(user_couple(db, email="filet-test@local.test", password_hash="x",
                           is_verified=True, subject="SVT", niveau="3e"))
        db.commit()


def noauth():
    return TestClient(app)


# ----- Sorties Groq canned (valides) pour le happy path -----
# (SEQ_MD / OPT_JSON supprimés le 30/07 avec l'outil Séquence et l'Optimiseur — ancien monde.)
AMB_JSON = '{"ambiguites": [{"extrait": "analysez", "type": "Consigne vague", "risque": "flou", "reformulation": "Identifiez X"}], "verdict": "Énoncé à clarifier."}'
CON_JSON = '{"analyses": [{"axe": "Clarté linguistique", "severite": "Élevée", "extrait": "expliquez", "probleme": "vague", "conseil": "précisez"}], "verdict": "À clarifier.", "version_optimisee": "Consigne réécrite."}'


# ===================== HAPPY PATH (200 + sortie cohérente) =====================

def test_ambiguites_happy():
    _prof_filet()
    with patch("backend.analyse.ambiguites.generate", return_value=AMB_JSON):
        r = authed().post("/api/detect-ambiguites", json={"texte": "Analysez le document."})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["verdict"] and len(d["ambiguites"]) == 1


def test_consigne_happy():
    _prof_filet()
    with patch("backend.analyse.consigne.generate", return_value=CON_JSON):
        r = authed().post("/api/analyser-consigne", json={"consigne": "Expliquez la photosynthèse."})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["version_optimisee"] and len(d["analyses"]) == 1


# ===================== AUTH 401 (sans cookie) =====================

def test_401_sans_cookie():
    c = noauth()
    cases = [
        ("/api/detect-ambiguites", {"texte": "x"}),
        ("/api/analyser-consigne", {"consigne": "x"}),
    ]
    for path, body in cases:
        r = c.post(path, json=body)
        assert r.status_code == 401, f"{path} -> {r.status_code} (attendu 401)"


def test_401_token_invalide():
    c = TestClient(app)
    c.cookies.set("aschool_access", "ceci.nest.pas.un.jwt")
    r = c.post("/api/detect-ambiguites", json={"texte": "x", "matiere": "SVT", "niveau": "3e"})
    assert r.status_code == 401, r.text


# ===================== VALIDATION 400 / 422 =====================

def test_400_entrees_vides_ou_invalides():
    c = authed()
    # ambiguites / consigne : entrée vide (le prof du filet existe avec son couple)
    _prof_filet()
    assert c.post("/api/detect-ambiguites", json={"texte": "   "}).status_code == 400
    assert c.post("/api/analyser-consigne", json={"consigne": "   "}).status_code == 400


# ===================== RÉSILIENCE — panne LLM amont =====================
# Les outils d'analyse passent par generate(). Une panne LLM (generate lève RuntimeError)
# -> 500 côté outil (unification sur 500, plus de 502 « externe » Groq).

def test_endpoint_outil_llm_down_500():
    """Si le LLM est down (generate lève RuntimeError), l'analyse renvoie 500."""
    _prof_filet()
    with patch("backend.analyse.ambiguites.generate", side_effect=RuntimeError("LLM down")):
        r = authed().post("/api/detect-ambiguites", json={"texte": "Analysez le document."})
    assert r.status_code == 500, r.text


# ===================== Programmes — lecture référentiel (profil) =====================
# Ne renvoie que les niveaux UTILISABLES (>= 1 matière au programme), groupés par cycle.
# Un cycle dont aucun niveau n'a de matière (ex. Supérieur) ne doit PAS apparaître.

def test_programmes_niveaux_utilisables_groupes_par_cycle():
    from backend.core.models_db import Cycle, Niveau, Matiere, Referentiel
    db = dbmod.SessionLocal()
    col = Cycle(nom="Collège", ordre=4); db.add(col)
    sup = Cycle(nom="Supérieur", ordre=6); db.add(sup); db.flush()
    n6 = Niveau(cycle_id=col.id, nom="6e", ordre=9); db.add(n6)
    nbts = Niveau(cycle_id=sup.id, nom="BTS", ordre=20); db.add(nbts)  # aucun référentiel -> exclu
    db.flush()
    ref6 = Referentiel(niveau_id=n6.id, nom_fixe="p_6e", collection="p_6e"); db.add(ref6); db.flush()
    db.add(Matiere(referentiel_id=ref6.id, nom="Mathématiques", ordre=2, validee=True))
    db.commit(); db.close()

    data = noauth().get("/api/programmes").json()
    assert any(m["nom"] == "Mathématiques" for m in data["matieres"])
    cycles = {g["cycle"]: [n["nom"] for n in g["niveaux"]] for g in data["niveaux_par_cycle"]}
    assert cycles.get("Collège") == ["6e"]      # niveau avec matière -> présent
    assert "Supérieur" not in cycles            # aucun référentiel, donc aucune matière -> absent


def test_programmes_matieres_par_cycle():
    # Matières scopées par cycle (menu matière du profil) : matière du référentiel d'un niveau du
    # cycle, RETENUE (validee) et active. BDD partagée -> identifiants uniques (mpc-*).
    from backend.core.models_db import Cycle, Niveau, Matiere, Referentiel
    db = dbmod.SessionLocal()
    cA = Cycle(nom="MPC-Cycle-A", ordre=40); db.add(cA)
    cB = Cycle(nom="MPC-Cycle-B", ordre=41); db.add(cB); db.flush()
    nA = Niveau(cycle_id=cA.id, nom="MPC-nivA", ordre=40); db.add(nA)
    nB = Niveau(cycle_id=cB.id, nom="MPC-nivB", ordre=41); db.add(nB); db.flush()
    refA = Referentiel(niveau_id=nA.id, nom_fixe="mpc_a", collection="mpc_a"); db.add(refA)
    refB = Referentiel(niveau_id=nB.id, nom_fixe="mpc_b", collection="mpc_b"); db.add(refB)
    db.flush()
    db.add(Matiere(referentiel_id=refA.id, nom="MPC-Mat1", ordre=40, validee=True))
    db.add(Matiere(referentiel_id=refB.id, nom="MPC-Mat2", ordre=41, validee=True))
    # Une matière INACTIVE et une matière PROPOSÉE mais pas encore retenue : ni l'une ni l'autre
    # n'entre dans les menus du prof.
    db.add(Matiere(referentiel_id=refA.id, nom="MPC-Inactive", ordre=99, actif=False, validee=True))
    db.add(Matiere(referentiel_id=refB.id, nom="MPC-Proposee", ordre=98, validee=False))
    db.commit(); db.close()

    data = noauth().get("/api/programmes").json()
    parc = {g["cycle"]: [m["nom"] for m in g["matieres"]] for g in data["matieres_par_cycle"]}
    assert parc.get("MPC-Cycle-A") == ["MPC-Mat1"]   # la matière inactive est exclue
    assert parc.get("MPC-Cycle-B") == ["MPC-Mat2"]   # la simple proposition est exclue


def test_programmes_matieres_par_niveau():
    # Matières scopées par NIVEAU (le programme du diplôme) = les matières de SON référentiel,
    # retenues et actives, dans l'ordre porté par la ligne (`ordre`, l'ordre du document).
    from backend.core.models_db import Cycle, Niveau, Matiere, Referentiel
    db = dbmod.SessionLocal()
    cyc = Cycle(nom="MPN-Cycle", ordre=50); db.add(cyc); db.flush()
    niv = Niveau(cycle_id=cyc.id, nom="MPN-Diplome", ordre=50); db.add(niv); db.flush()
    ref = Referentiel(niveau_id=niv.id, nom_fixe="mpn", collection="mpn"); db.add(ref); db.flush()
    # Insertion volontairement DÉSORDONNÉE (C, A, B) : le test attend A, B, C — il prouve donc
    # que c'est `ordre` qui range, pas l'ordre d'écriture en base.
    db.add(Matiere(referentiel_id=ref.id, nom="MPN-C", ordre=3, validee=True))
    db.add(Matiere(referentiel_id=ref.id, nom="MPN-A", ordre=1, validee=True))
    db.add(Matiere(referentiel_id=ref.id, nom="MPN-B", ordre=2, validee=True))
    db.add(Matiere(referentiel_id=ref.id, nom="MPN-Inact", ordre=4, actif=False, validee=True))
    db.add(Matiere(referentiel_id=ref.id, nom="MPN-Proposee", ordre=5, validee=False))
    db.commit(); db.close()

    data = noauth().get("/api/programmes").json()
    parn = {g["niveau"]: [m["nom"] for m in g["matieres"]] for g in data["matieres_par_niveau"]}
    assert parn.get("MPN-Diplome") == ["MPN-A", "MPN-B", "MPN-C"]  # ordre du document, exclusions OK


def test_programmes_niveau_ref_disponible_expose():
    # niveaux_par_cycle expose `refDisponible`, DÉRIVÉ (jamais stocké) : vrai ssi le niveau a
    # un référentiel réellement ingéré (>= 1 chunk). Référentiel sans chunk => faux ;
    # pas de référentiel du tout => faux.
    from backend.core.models_db import (
        Cycle, Niveau, Matiere, Referentiel, ReferentielChunk,
    )
    db = dbmod.SessionLocal()
    cyc = Cycle(nom="NT-Cycle", ordre=60); db.add(cyc); db.flush()
    nDispo     = Niveau(cycle_id=cyc.id, nom="NT-Dispo", ordre=60);     db.add(nDispo)
    nSansChunk = Niveau(cycle_id=cyc.id, nom="NT-SansChunk", ordre=61); db.add(nSansChunk)
    nSansRef   = Niveau(cycle_id=cyc.id, nom="NT-SansRef", ordre=62);   db.add(nSansRef)
    db.flush()
    # référentiel + 1 chunk => nDispo disponible
    refDispo = Referentiel(niveau_id=nDispo.id,
                           nom_fixe="NT-ref-dispo", collection="nt_dispo")
    # référentiel SANS chunk => nSansChunk reste indisponible (prouve la règle >= 1 chunk)
    refSansChunk = Referentiel(niveau_id=nSansChunk.id,
                               nom_fixe="NT-ref-sanschunk", collection="nt_sanschunk")
    db.add_all([refDispo, refSansChunk]); db.flush()
    # une matière par référentiel => les deux niveaux apparaissent dans l'endpoint. NT-SansRef,
    # lui, n'a pas de référentiel : il ne peut porter aucune matière, donc il n'apparaît pas.
    db.add(Matiere(referentiel_id=refDispo.id, nom="NT-Mat", ordre=60, validee=True))
    db.add(Matiere(referentiel_id=refSansChunk.id, nom="NT-Mat", ordre=60, validee=True))
    db.add(ReferentielChunk(referentiel_id=refDispo.id, chunk_index=0, option_ab="A",
                            page=1, texte="x", embedding=[0.0] * 1024, embedding_model="test"))
    db.commit(); db.close()

    data = noauth().get("/api/programmes").json()
    grp = next(g for g in data["niveaux_par_cycle"] if g["cycle"] == "NT-Cycle")
    flags = {n["nom"]: n["refDisponible"] for n in grp["niveaux"]}
    assert flags == {"NT-Dispo": True, "NT-SansChunk": False}


# ===================== Programmes ADMIN — CRUD (T1) =====================
# GET arbre complet (cycle -> niveau -> matieres de SON referentiel, inactives et non validees
# incluses) + POST niveau (debloque superieur/creche, avec gardes) + POST/PATCH matiere.

def admin_client():
    from backend.systeme.admin import _make_admin_token
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def test_admin_programmes_arbre_complet_inactives_incluses():
    """L'arbre admin montre TOUT : le niveau sans référentiel (à remplir), et les matières du
    référentiel y compris celles que le prof ne voit pas — inactive, ou seulement proposée."""
    from backend.core.models_db import Cycle, Niveau, Matiere, Referentiel
    db = dbmod.SessionLocal()
    cyc = Cycle(nom="CycleAdminTest", ordre=99); db.add(cyc); db.flush()
    nivA = Niveau(cycle_id=cyc.id, nom="NivA", ordre=1)
    nivVide = Niveau(cycle_id=cyc.id, nom="NivVide", ordre=2)
    db.add_all([nivA, nivVide]); db.flush()
    ref = Referentiel(niveau_id=nivA.id, nom_fixe="adm_a", collection="adm_a")
    db.add(ref); db.flush()
    db.add(Matiere(referentiel_id=ref.id, nom="MatAdmin", ordre=99, actif=False, validee=True))
    db.add(Matiere(referentiel_id=ref.id, nom="MatProposee", ordre=98, validee=False))
    db.commit(); db.close()

    assert noauth().get("/api/admin/programmes").status_code == 401  # garde admin

    data = admin_client().get("/api/admin/programmes").json()
    cycle = next(c for c in data["cycles"] if c["nom"] == "CycleAdminTest")
    par_nom = {n["nom"]: n for n in cycle["niveaux"]}
    mats = {m["nom"]: m for m in par_nom["NivA"]["matieres"]}
    assert mats["MatAdmin"]["actif"] is False          # inactive : présente quand même
    assert mats["MatProposee"]["validee"] is False     # proposée : présente quand même
    # Le niveau sans référentiel apparaît, vide : l'admin voit ce qui reste à déposer.
    assert par_nom["NivVide"]["referentiel_id"] is None
    assert par_nom["NivVide"]["matieres"] == []


# RETIRE (chantier Matiere) : test_admin_toggle_paire_cree_puis_desactive_sans_delete prouvait
# PATCH /admin/programmes/paire. La paire matiere x niveau n'existe plus, et l'endpoint avec elle.
# Le geste equivalent — activer/desactiver une matiere du referentiel, JAMAIS de DELETE — est
# prouve par test_admin_creer_matiere_encadre_et_toggle_actif_sans_delete.


def test_admin_delete_user_purge_tout_ce_qui_pend_au_compte():
    """Bug bloquant du check-up 31/07 : supprimer un prof qui a VOTÉ une fonctionnalité ou
    UTILISÉ un outil levait une violation de clé étrangère (500, compte non supprimé), et un
    incident rattaché à son feedback bloquait la purge des feedbacks. Le nettoyage est
    désormais garanti par la BASE (ON DELETE, migration e4b8c2d6a1f7) : ce test crée un prof
    avec TOUT ce qui peut pendre à un compte, le supprime, et vérifie qu'il ne reste rien —
    sauf l'incident technique, qui survit en perdant son lien."""
    from backend.core.models_db import (Activite, ActiviteType, FeatureVote, Feedback,
                                        FewShotMilestone, Incident, Seance,
                                        Sequence, ToolUsageLog, User)
    from _profil import user_couple

    # `with` obligatoire : une session laissée ouverte bloque le TRUNCATE de fin de test
    # (transaction idle) et gèle toute la suite de la suite.
    with dbmod.SessionLocal() as db:
        u = user_couple(db, email="suppr-total@local.test", password_hash="x",
                        is_verified=True, subject="SVT", niveau="3e")
        db.add(u); db.flush()
        uid = u.id

        typ = db.query(ActiviteType).first()
        if not typ:
            typ = ActiviteType(label="Test suppression", ordre=900)
            db.add(typ); db.flush()
        # Tout ce qui peut pendre à un compte, dont les 5 liens qui cassaient la suppression.
        db.add(FeatureVote(user_id=uid, feature_key="quiz-interactif"))       # cassait (FK)
        db.add(ToolUsageLog(user_id=uid, tool="consigne", score_label="3"))   # cassait (FK)
        db.add(FewShotMilestone(user_id=uid, activite_type_id=typ.id))        # cassait (FK)
        db.add(Sequence(user_id=uid, titre="Séq"))
        db.add(Seance(user_id=uid, titre="Séance"))
        db.add(Activite(user_id=uid, activite_type_id=typ.id, activite_label="Act"))
        fb = Feedback(user_id=uid, message="Bravo", rating=5, statut="nouveau")
        db.add(fb); db.flush()
        db.add(Incident(ref="INC-SUPPR-1", endpoint="/api/x", error="boom",
                        feedback_id=fb.id))                                  # cassait la purge feedbacks
        db.commit()

    r = admin_client().delete("/api/admin/user/suppr-total@local.test")
    assert r.status_code == 200, r.text   # avant la réparation : 500 (IntegrityError)

    with dbmod.SessionLocal() as d:
        restes = {
            "user":          d.query(User).filter(User.id == uid).count(),
            "votes":         d.query(FeatureVote).filter(FeatureVote.user_id == uid).count(),
            "usages":        d.query(ToolUsageLog).filter(ToolUsageLog.user_id == uid).count(),
            "jalons":        d.query(FewShotMilestone).filter(FewShotMilestone.user_id == uid).count(),
            "activites":     d.query(Activite).filter(Activite.user_id == uid).count(),
            "seances":       d.query(Seance).filter(Seance.user_id == uid).count(),
            "sequences":     d.query(Sequence).filter(Sequence.user_id == uid).count(),
            "feedbacks":     d.query(Feedback).filter(Feedback.user_id == uid).count(),
        }
        # L'incident TECHNIQUE survit, orphelin de son feedback (journal, pas donnée du prof).
        inc_restant = d.query(Incident).filter(Incident.ref == "INC-SUPPR-1").first()
        survivant = (inc_restant is not None, inc_restant.feedback_id if inc_restant else "absent")

    assert restes == dict.fromkeys(restes, 0), f"reste des lignes après suppression : {restes}"
    assert survivant == (True, None)


def test_admin_feedback_statuts_lus_en_base():
    """L'écran admin n'a plus de copie en dur des statuts : il lit le catalogue en base
    (libellés + ordre), comme l'écran prof. Le conftest sème les 4 statuts de référence."""
    assert noauth().get("/api/admin/feedback-statuts").status_code == 401   # garde admin
    d = admin_client().get("/api/admin/feedback-statuts").json()
    assert [s["code"] for s in d] == ["nouveau", "en_cours", "traite", "archive"]  # ordre de la base
    assert {s["label"] for s in d} == {"Nouveau", "En cours", "Traité", "Archivé"}


def test_admin_update_user_refuse_un_couple_hors_programme():
    """PATCH /admin/user rangeait matière et niveau par clés SANS vérifier que le couple
    existe au programme : l'admin pouvait poser « Français en Crèche ». Désormais refusé."""
    from backend.core.models_db import User
    from _profil import referentiel_id, user_couple

    with dbmod.SessionLocal() as db:
        u = user_couple(db, email="couple-prog@local.test", password_hash="x",
                        is_verified=True, subject="P900-Maths", niveau="P900-6e")
        db.add(u)
        # Deuxième niveau avec SON référentiel, qui ne nomme PAS « P900-Maths » : le couple
        # (P900-Maths, P900-Creche) n'existe donc nulle part — c'est le couple interdit.
        referentiel_id(db, "P900-Creche")
        db.commit()

    cl = admin_client()
    hors = cl.patch("/api/admin/user/couple-prog@local.test",
                    json={"prenom": "A", "nom": "B", "subject": "P900-Maths", "niveau": "P900-Creche"})
    assert hors.status_code == 400
    assert "programme" in hors.json()["detail"]

    ok = cl.patch("/api/admin/user/couple-prog@local.test",
                  json={"prenom": "A", "nom": "B", "subject": "P900-Maths", "niveau": "P900-6e"})
    assert ok.status_code == 200                      # le couple au programme passe

    # Profil incomplet (niveau seul) : toujours permis — état normal d'un compte qui vient de naître.
    assert cl.patch("/api/admin/user/couple-prog@local.test",
                    json={"prenom": "A", "nom": "B", "subject": "", "niveau": "P900-6e"}).status_code == 200

    with dbmod.SessionLocal() as d:
        reste = d.query(User).filter(User.email == "couple-prog@local.test").first()
        assert reste.subject_id is None               # l'écriture refusée n'a rien laissé derrière


def test_admin_creer_matiere_encadre_et_toggle_actif_sans_delete():
    # La maison des matières : POST création DANS un référentiel (garde nom vide / référentiel
    # inconnu / doublon insensible à la casse DANS CE référentiel) + PATCH actif (bascule, ligne
    # CONSERVEE — jamais de DELETE). Le même nom dans un AUTRE référentiel reste permis.
    from backend.core.models_db import Matiere
    from _profil import referentiel_id
    with dbmod.SessionLocal() as db:
        ref_id = referentiel_id(db, "MM-Niveau")
        autre_ref_id = referentiel_id(db, "MM-Autre")
        db.commit()
    cl = admin_client()

    assert noauth().post("/api/admin/matieres",
                         json={"referentiel_id": ref_id, "nom": "MatMaison"}).status_code == 401
    assert cl.post("/api/admin/matieres",
                   json={"referentiel_id": ref_id, "nom": "   "}).status_code == 400
    assert cl.post("/api/admin/matieres",
                   json={"referentiel_id": 999999, "nom": "MatMaison"}).status_code == 404

    r = cl.post("/api/admin/matieres", json={"referentiel_id": ref_id, "nom": "MatMaison"})
    assert r.status_code == 200
    mid = r.json()["id"]
    assert r.json()["actif"] is True and r.json()["validee"] is True   # saisie admin = retenue
    assert cl.post("/api/admin/matieres",
                   json={"referentiel_id": ref_id, "nom": "matmaison"}).status_code == 409  # doublon (casse)
    # Le même nom dans un autre référentiel : deux matières distinctes, c'est le modèle.
    assert cl.post("/api/admin/matieres",
                   json={"referentiel_id": autre_ref_id, "nom": "MatMaison"}).status_code == 200

    assert cl.patch("/api/admin/matieres/actif",
                    json={"matiere_id": mid, "actif": False}).status_code == 200

    db = dbmod.SessionLocal()
    m = db.get(Matiere, mid)
    presente, actif = m is not None, (m.actif if m else None)
    db.close()
    assert (presente, actif) == (True, False)  # ligne CONSERVEE, inactive (pas de DELETE)

    assert cl.patch("/api/admin/matieres/actif",
                    json={"matiere_id": mid, "actif": True}).json()["actif"] is True  # réactivable
    assert cl.patch("/api/admin/matieres/actif",
                    json={"matiere_id": 999999, "actif": True}).status_code == 404


def test_admin_matiere_demande_langue_se_regle_et_se_relit():
    """« Cette matiere porte une langue » : le drapeau qui fait apparaitre le choix de la langue
    au profil du prof et l'injecte dans la generation. Une matiere naissant TOUJOURS a false
    (creation admin comme detection), il faut pouvoir le poser -- sinon le sous-menu langue du
    profil devient inatteignable. La case de la page « Programmes & contenu » ecrit ici, et
    l'arbre /admin/contenu le relit."""
    from _profil import referentiel_id
    with dbmod.SessionLocal() as db:
        ref_id = referentiel_id(db, "ML-Niveau")
        db.commit()
    cl = admin_client()

    mid = cl.post("/api/admin/matieres",
                  json={"referentiel_id": ref_id, "nom": "ML-Anglais"}).json()["id"]
    # Elle nait a « non », alors meme que son libelle est celui d'une langue : c'est le drapeau
    # qui decide, jamais le nom.
    with dbmod.SessionLocal() as db:
        from backend.core.models_db import Matiere
        assert db.get(Matiere, mid).demande_langue is False

    assert noauth().patch("/api/admin/matieres/demande-langue",
                          json={"matiere_id": mid, "demande_langue": True}).status_code == 401
    assert cl.patch("/api/admin/matieres/demande-langue",
                    json={"matiere_id": 999999, "demande_langue": True}).status_code == 404

    assert cl.patch("/api/admin/matieres/demande-langue",
                    json={"matiere_id": mid, "demande_langue": True}).json()["demande_langue"] is True
    arbre = cl.get("/api/admin/contenu").json()
    lue = next(m for c in arbre["cycles"] for n in c["niveaux"] for m in n["matieres"]
               if m["id"] == mid)
    assert lue["demande_langue"] is True          # relu dans l'arbre : la case se rouvre cochee
    assert cl.patch("/api/admin/matieres/demande-langue",
                    json={"matiere_id": mid, "demande_langue": False}).json()["demande_langue"] is False


# ===================== /api/matieres — deux questions, deux réponses =====================
# Sans argument : les NOMS distincts de toutes les matières au programme (ce que lisent les trois
# filtres admin, qui trient de l'historique rangé par nom). Avec ?niveau_id= : les matières du
# RÉFÉRENTIEL de ce niveau, avec leur id. Données préfixées (BDD partagée) pour ne rien collisionner.

def test_matieres_derive_de_la_base():
    from backend.core.models_db import Cycle, Niveau, Matiere, Referentiel
    db = dbmod.SessionLocal()
    c = Cycle(nom="P510-Cyc", ordre=510); db.add(c); db.flush()
    n4 = Niveau(cycle_id=c.id, nom="P510-4e", ordre=510); db.add(n4)
    n3 = Niveau(cycle_id=c.id, nom="P510-3e", ordre=511); db.add(n3); db.flush()
    ref4 = Referentiel(niveau_id=n4.id, nom_fixe="p510_4e", collection="p510_4e"); db.add(ref4)
    ref3 = Referentiel(niveau_id=n3.id, nom_fixe="p510_3e", collection="p510_3e"); db.add(ref3)
    db.flush()
    db.add(Matiere(referentiel_id=ref4.id, nom="P510-Français", ordre=5101, validee=True))
    db.add(Matiere(referentiel_id=ref4.id, nom="P510-Maths",    ordre=5102, validee=True))
    # Même nom dans l'autre référentiel : le catalogue global ne le compte qu'une fois.
    db.add(Matiere(referentiel_id=ref3.id, nom="P510-Maths",    ordre=5103, validee=True))
    db.add(Matiere(referentiel_id=ref3.id, nom="P510-Proposee", ordre=5104, validee=False))
    db.commit()
    n4_id = n4.id
    db.close()

    noms = [m["nom"] for m in noauth().get("/api/matieres").json()]
    assert "P510-Français" in noms and "P510-Maths" in noms   # matières retenues et actives
    assert noms.count("P510-Maths") == 1                      # un seul nom, malgré deux matières
    assert "P510-Proposee" not in noms                        # une proposition n'est pas au programme

    du_niveau = noauth().get(f"/api/matieres?niveau_id={n4_id}").json()
    assert [m["nom"] for m in du_niveau] == ["P510-Français", "P510-Maths"]
    assert all(m["id"] for m in du_niveau)                    # scopé au référentiel = id sans ambiguïté


