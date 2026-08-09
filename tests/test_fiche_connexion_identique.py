r"""Preuve de raccordement — /auth/login et /auth/me rendent LA MÊME fiche.

LE DÉFAUT QUI A COÛTÉ CE TEST (constaté le 07/08/2026, présent depuis longtemps). Après chaque
connexion, l'écran de création d'activité s'affichait VIDE : pas de cartouche « Paramètres de
l'activité », donc aucun type à choisir, donc aucune activité possible. Un F5 réparait — parfois
il en fallait plusieurs. Le header, lui, n'affichait pas le couple de travail.

La cause n'était pas dans l'écran. `/auth/login` rendait sa propre fiche, plus courte de six
champs que celle de `/auth/me` : ni `travail_matiere`, ni `travail_niveau`, ni `profil_coherent`.
Or l'écran POSE la réponse de la connexion comme utilisateur connecté (Login.jsx → setUser) et
ne rappelle pas `/auth/me` derrière. Le couple de travail valait donc « vide » ; l'appel qui
lit les types d'activité est conditionné à la matière, il ne partait même pas. Le F5 réparait
parce qu'il relit `/auth/me`, la fiche complète.

Ce que ce test PROUVE :
  1. les deux routes rendent EXACTEMENT le même jeu de clés — aucune ne peut maigrir sans le dire ;
  2. les valeurs concordent, champ par champ, pour un même prof ;
  3. `travail_matiere` et `travail_niveau` sont RENSEIGNÉS à la connexion — c'est la panne d'origine ;
  4. un prof sans couple de travail posé reçoit quand même celui de son profil (le repli du
     serveur vaut pour la connexion comme pour la relecture).

Lancer : docker compose exec backend python -m pytest tests/test_fiche_connexion_identique.py -q
"""
import bcrypt
from fastapi.testclient import TestClient

import backend.core.database as dbmod
from backend.main import app
from backend.core.models_db import Cycle, Matiere, Niveau, Referentiel, User

EMAIL = "prof.fiche@aschool.fr"
MDP = "MotDePasse-Test-1"

# Les champs sans lesquels l'écran ne sait pas travailler. Ils étaient TOUS absents de la
# réponse de connexion ; on les nomme un par un pour qu'un retrait se voie.
INDISPENSABLES = ("travail_matiere", "travail_niveau", "travail_demande_langue",
                  "profil_coherent", "couple_ajuste", "guide_creer_vu")


def _semer():
    """Un prof avec un couple au programme. Rend (matiere, niveau)."""
    db = dbmod.SessionLocal()
    db.query(User).filter(User.email == EMAIL).delete()
    db.query(Matiere).delete()
    db.query(Referentiel).delete()
    db.query(Niveau).delete()
    db.query(Cycle).delete()
    db.commit()

    cycle = Cycle(nom="Cycle fiche", ordre=1)
    db.add(cycle)
    db.flush()
    niveau = Niveau(nom="Niveau fiche", cycle_id=cycle.id, ordre=1)
    db.add(niveau)
    db.flush()
    ref = Referentiel(niveau_id=niveau.id, nom_fixe="Référentiel fiche", collection="fiche")
    db.add(ref)
    db.flush()
    matiere = Matiere(nom="Matière fiche", referentiel_id=ref.id, ordre=1, actif=True)
    db.add(matiere)
    db.flush()
    db.add(User(
        email=EMAIL,
        password_hash=bcrypt.hashpw(MDP.encode(), bcrypt.gensalt()).decode(),
        is_verified=True, is_active=True, failed_attempts=0, guide_creer_vu=False,
        prenom="Prof", nom="Fiche",
        subject_id=matiere.id, niveau_id=niveau.id,
    ))
    db.commit()
    noms = (matiere.nom, niveau.nom)
    db.close()
    return noms


def _connexion(client):
    r = client.post("/api/auth/login", json={"email": EMAIL, "password": MDP})
    assert r.status_code == 200, r.text
    return r.json()


def test_les_deux_fiches_ont_exactement_les_memes_champs():
    _semer()
    c = TestClient(app)
    fiche_login = _connexion(c)
    fiche_me = c.get("/api/auth/me").json()
    assert set(fiche_login) == set(fiche_me), (
        "champs manquants à la connexion : "
        f"{sorted(set(fiche_me) - set(fiche_login))}"
    )


def test_les_deux_fiches_disent_la_meme_chose():
    _semer()
    c = TestClient(app)
    fiche_login = _connexion(c)
    fiche_me = c.get("/api/auth/me").json()
    assert fiche_login == fiche_me


def test_le_couple_de_travail_arrive_des_la_connexion():
    """LA panne d'origine : sans ces deux valeurs, l'écran de création reste vide."""
    matiere, niveau = _semer()
    fiche = _connexion(TestClient(app))
    assert fiche["travail_matiere"] == matiere
    assert fiche["travail_niveau"] == niveau


def test_aucun_champ_indispensable_ne_manque_a_la_connexion():
    _semer()
    fiche = _connexion(TestClient(app))
    manquants = [k for k in INDISPENSABLES if k not in fiche]
    assert not manquants, f"absents de la fiche de connexion : {manquants}"


def test_sans_couple_de_travail_pose_le_profil_prend_le_relais():
    """Le prof n'a pas cliqué « Changer niveau et/ou matière » : son profil fait foi, et la
    connexion doit le dire aussi bien que la relecture."""
    matiere, niveau = _semer()
    db = dbmod.SessionLocal()
    u = db.query(User).filter(User.email == EMAIL).first()
    u.travail_matiere_id = None
    u.travail_niveau_id = None
    db.commit()
    db.close()
    fiche = _connexion(TestClient(app))
    assert fiche["travail_matiere"] == matiere
    assert fiche["travail_niveau"] == niveau
