"""Preuve — la grille du professeur se range EN DONNÉES, et chaque geste s'écrit à l'instant.

Ce que ces tests PROUVENT (base aschool_test via conftest.py, LLM MOQUÉ — aucun appel réel) :

  1. LA GRILLE EST UN TABLEAU EN BASE, pas un texte. Une génération remplit les quatre tables :
     la grille, ses colonnes, ses lignes, et le descripteur de chaque case.
  2. LE COUPLE VIENT DE LA BASE. L'écran n'envoie que la demande ; matière et niveau sont lus
     sur le profil, jamais reçus du client.
  3. RIEN N'EST INVENTÉ HORS SOL. Pas d'extrait assez pertinent dans le référentiel → 400 et
     AUCUN appel au modèle (rien n'est payé pour une génération qu'on sait sans ancrage).
  4. LE SERVEUR NE CROIT PAS LE MODÈLE SUR PAROLE. Un descripteur rangé sous une colonne qui
     n'existe pas est écarté ; une réponse sans critère est refusée.
  5. UNE GRILLE NE NAÎT QUE D'UNE GÉNÉRATION — il n'y a pas de « grille vide » à remplir soi-même.
  6. L'ÉCRITURE EST AU GESTE. Ajouter un critère, écrire une case, renommer une colonne : chaque
     appel laisse la base dans un état complet — il n'y a pas de brouillon à côté des tables.
  7. UNE CASE VIDÉE N'A PAS DE LIGNE. L'absence est le vide, il n'y a pas deux façons de dire
     « rien ».
  8. CE QUI APPARTIENT À UN AUTRE PROFESSEUR EST INTROUVABLE, y compris par la porte des
     critères et des colonnes, qui ne passent pas par l'identifiant de la grille.
  9. SUPPRIMER VEUT DIRE SUPPRIMER : la grille part, ses lignes, ses colonnes et ses cases avec.

Lancer : docker compose exec backend python -m pytest tests/test_grilles.py -q
"""
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

import backend.core.database as dbmod
from backend.core.models_db import (
    Grille, GrilleCellule, GrilleCritere, GrilleNiveauMaitrise, User,
)
from backend.main import app
from backend.securite.comptes import create_access_token

from _profil import user_couple

EMAIL = "prof.grilles@aschool.fr"
AUTRE = "autre.prof.grilles@aschool.fr"

# Ce qu'un modèle bien élevé rend : une échelle, des critères, un descripteur par case.
GRILLE_LLM = json.dumps({
    "titre": "Exposé oral sur une œuvre",
    "niveaux_maitrise": [
        {"libelle": "Maîtrise insuffisante", "points": 0},
        {"libelle": "Maîtrise fragile", "points": 1},
        {"libelle": "Maîtrise satisfaisante", "points": 2},
        {"libelle": "Très bonne maîtrise", "points": 3},
    ],
    "criteres": [
        {"libelle": "Structure le propos", "poids": 2, "descripteurs": {
            "Maîtrise insuffisante": "Enchaîne les idées sans ordre repérable",
            "Maîtrise fragile": "Annonce un plan mais ne le suit pas",
            "Maîtrise satisfaisante": "Annonce un plan et le suit",
            "Très bonne maîtrise": "Annonce un plan, le suit, et relie chaque partie à la suivante",
        }},
        {"libelle": "Appuie ses affirmations sur le texte", "poids": 1, "descripteurs": {
            "Maîtrise insuffisante": "Affirme sans citer",
            "Maîtrise fragile": "Cite une fois, sans commenter",
            "Maîtrise satisfaisante": "Cite et commente chaque citation",
            "Très bonne maîtrise": "Cite, commente, et met deux passages en relation",
        }},
    ],
})

EXTRAITS = [{"text": "L'élève présente une œuvre à l'oral.", "page": 12, "score": 0.9}]

# Ce que rend « Propose-moi une idée » : la DEMANDE que le prof aurait tapée, pas une grille.
IDEE_LLM = ("Les élèves câblent un petit réseau local puis rendent un compte rendu décrivant "
            "leur installation et les tests menés. On y regarde la justesse du schéma, la "
            "méthode de test et la clarté des explications.\n")


def _client(email=EMAIL):
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(email))
    return c


def _prof(email=EMAIL):
    with dbmod.SessionLocal() as db:
        if db.query(User).filter(User.email == email).first():
            return          # déjà semé par un test précédent
        db.add(user_couple(db, email=email, password_hash="x", is_verified=True,
                           subject="Français", niveau="4e"))
        db.commit()


def _generer(texte="Un exposé oral sur une œuvre", reponse=GRILLE_LLM, extraits=EXTRAITS):
    """Un POST de génération, LLM et RAG moqués. Renvoie (réponse HTTP, mock generate)."""
    with patch("backend.contenu.grilles.generate", return_value=reponse) as gen, \
         patch("backend.contenu.grilles.retrieve_pg", return_value=extraits), \
         patch("backend.contenu.grilles.get_cle_texte", return_value="cle-test"):
        return _client().post("/api/contenus/grilles/generer", json={"texte": texte}), gen


def _une_grille(titre=None):
    """L'identifiant d'une grille prête à retoucher. UNE SEULE FAÇON D'EN OBTENIR UNE : la
    génération. Il n'y a pas de « créer une grille vide » — un tableau nu à remplir case par case
    n'est pas un service, le professeur a déjà un tableur."""
    reponse = GRILLE_LLM
    if titre:
        data = json.loads(GRILLE_LLM)
        data["titre"] = titre
        reponse = json.dumps(data)
    r, _ = _generer(reponse=reponse)
    assert r.status_code == 200, r.text
    return r.json()["id"]


# ── 1 & 2. La grille arrive en données, sur le couple lu en base ─────────────────────────

def test_la_generation_remplit_les_quatre_tables():
    _prof()
    r, _ = _generer()
    assert r.status_code == 200, r.text
    grille = r.json()

    assert grille["titre"] == "Exposé oral sur une œuvre"
    assert [n["libelle"] for n in grille["niveaux_maitrise"]] == [
        "Maîtrise insuffisante", "Maîtrise fragile", "Maîtrise satisfaisante", "Très bonne maîtrise"]
    assert [n["points"] for n in grille["niveaux_maitrise"]] == [0, 1, 2, 3]
    assert len(grille["criteres"]) == 2

    # Les CASES sont bien là, et indexées par l'identifiant de leur colonne.
    ids_colonnes = {str(n["id"]) for n in grille["niveaux_maitrise"]}
    premier = grille["criteres"][0]
    assert set(premier["descripteurs"]) == ids_colonnes
    haut = str(grille["niveaux_maitrise"][-1]["id"])
    assert premier["descripteurs"][haut].startswith("Annonce un plan, le suit")

    # Et en base : huit cases pour deux critères × quatre colonnes, pas une de moins.
    with dbmod.SessionLocal() as db:
        gid = grille["id"]
        assert db.query(GrilleNiveauMaitrise).filter_by(grille_id=gid).count() == 4
        criteres = db.query(GrilleCritere).filter_by(grille_id=gid).all()
        assert len(criteres) == 2
        cases = (db.query(GrilleCellule)
                   .filter(GrilleCellule.critere_id.in_([c.id for c in criteres])).count())
        assert cases == 8


def test_le_couple_est_lu_en_base_pas_recu_de_l_ecran():
    """L'écran n'envoie que la demande. Le prompt part quand même avec matière et niveau."""
    _prof()
    r, gen = _generer()
    assert r.status_code == 200, r.text
    assert r.json()["matiere"] == "Français" and r.json()["niveau"] == "4e"
    prompt = gen.call_args.args[0]
    assert "Français" in prompt and "4e" in prompt
    # La demande du prof part telle qu'il l'a écrite, et les extraits du référentiel avec.
    assert "Un exposé oral sur une œuvre" in prompt
    assert "L'élève présente une œuvre à l'oral." in prompt


def test_la_demande_du_prof_est_gardee_telle_quelle():
    _prof()
    r, _ = _generer(texte="  Un exposé oral sur une œuvre  ")
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        assert db.get(Grille, r.json()["id"]).contexte == "Un exposé oral sur une œuvre"


# ── 3. Rien n'est inventé hors sol, et rien n'est payé pour rien ─────────────────────────

def test_sans_extrait_pertinent_aucun_appel_au_modele():
    _prof()
    r, gen = _generer(extraits=[])
    assert r.status_code == 400
    assert "pertinent" in r.json()["detail"]
    gen.assert_not_called()


def test_une_demande_vide_est_refusee_avant_tout_appel():
    _prof()
    r, gen = _generer(texte="   ")
    assert r.status_code == 400
    gen.assert_not_called()


# ── 10. « Propose-moi une idée » — le thème du prof mène, et le refus ne coûte rien ───────

def _proposer(theme="les réseaux", reponse=IDEE_LLM, extraits=EXTRAITS):
    """Un POST sur « Propose-moi une idée », LLM et RAG moqués. Renvoie (réponse, mocks)."""
    with patch("backend.contenu.grilles.generate", return_value=reponse) as gen, \
         patch("backend.contenu.grilles.retrieve_pg", return_value=extraits) as rag, \
         patch("backend.contenu.grilles.get_cle_texte", return_value="cle-test"):
        r = _client().post("/api/contenus/grilles/proposer-idee", json={"theme": theme})
        return r, gen, rag


def test_le_theme_du_prof_est_la_requete_envoyee_au_referentiel():
    """LE POINT DE TOUT LE DISPOSITIF. Sans le thème, les extraits seraient pris au hasard du
    référentiel entier et l'idée rendue serait quelconque. Il sert DEUX fois : requête au
    référentiel, puis élément du prompt."""
    _prof()
    r, gen, rag = _proposer(theme="  les réseaux  ")
    assert r.status_code == 200, r.text
    assert rag.call_args.args[1] == "les réseaux"       # la requête RAG, pas un gabarit fixe
    prompt = gen.call_args.args[0]
    assert "les réseaux" in prompt
    # Le couple est lu en base, comme partout — l'écran n'envoie que le thème.
    assert "Français" in prompt and "4e" in prompt
    assert "L'élève présente une œuvre à l'oral." in prompt


def test_l_idee_revient_au_prof_sans_ecrire_de_grille():
    """Ce bouton amorce la zone de saisie, il ne crée RIEN en base : la grille naît au clic
    suivant, celui de « Générer la grille »."""
    _prof()
    with dbmod.SessionLocal() as db:
        avant = db.query(Grille).count()
    r, _, _ = _proposer()
    assert r.status_code == 200, r.text
    assert r.json()["available"] is True
    assert r.json()["texte"] == IDEE_LLM.strip()
    with dbmod.SessionLocal() as db:
        assert db.query(Grille).count() == avant


def test_sans_extrait_pertinent_l_idee_est_refusee_sans_appel_au_modele():
    """Le refus n'est PAS une erreur : `available:false` + un message, pour que la fenêtre reste
    ouverte et que le prof reformule sur place. Et il ne coûte rien — on s'arrête après la
    recherche, avant le modèle."""
    _prof()
    r, gen, _ = _proposer(extraits=[])
    assert r.status_code == 200, r.text
    assert r.json()["available"] is False
    assert r.json()["message"]
    assert r.json()["texte"] is None
    gen.assert_not_called()


def test_un_theme_vide_est_refuse_avant_toute_recherche():
    _prof()
    r, gen, rag = _proposer(theme="   ")
    assert r.status_code == 400
    gen.assert_not_called()
    rag.assert_not_called()


# ── 4. Le serveur ne croit pas le modèle sur parole ──────────────────────────────────────

def test_un_descripteur_sous_une_colonne_inconnue_est_ecarte():
    """Le prompt exige que les clés reprennent les libellés — une consigne n'est pas une
    garantie. Une case dont on ne sait pas de quelle colonne elle parle ne s'écrit pas."""
    _prof()
    bancal = json.loads(GRILLE_LLM)
    bancal["criteres"][0]["descripteurs"]["Excellent"] = "Colonne qui n'existe pas"
    r, _ = _generer(reponse=json.dumps(bancal))
    assert r.status_code == 200, r.text
    premier = r.json()["criteres"][0]
    assert len(premier["descripteurs"]) == 4          # les quatre vraies, pas la cinquième
    assert "Colonne qui n'existe pas" not in premier["descripteurs"].values()


def test_une_reponse_sans_critere_est_refusee():
    _prof()
    vide = json.loads(GRILLE_LLM)
    vide["criteres"] = []
    r, _ = _generer(reponse=json.dumps(vide))
    assert r.status_code == 500
    assert "exploitable" in r.json()["detail"]
    # Et rien n'a été écrit : une grille sans critère n'est pas une grille.
    with dbmod.SessionLocal() as db:
        assert db.query(Grille).filter(Grille.titre == vide["titre"]).count() == 0


def test_deux_colonnes_de_meme_nom_sont_fusionnees_pas_refusees():
    """La table interdit le doublon. Faire échouer toute la génération dessus coûterait au
    professeur un appel qu'il a déjà payé — on garde la première, on ignore la seconde."""
    _prof()
    double = json.loads(GRILLE_LLM)
    double["niveaux_maitrise"].append({"libelle": "Maîtrise fragile", "points": 9})
    r, _ = _generer(reponse=json.dumps(double))
    assert r.status_code == 200, r.text
    libelles = [n["libelle"] for n in r.json()["niveaux_maitrise"]]
    assert libelles.count("Maîtrise fragile") == 1


def test_une_reponse_illisible_ne_laisse_rien_en_base():
    _prof()
    with dbmod.SessionLocal() as db:
        avant = db.query(Grille).count()
    r, _ = _generer(reponse="Bonjour, voici votre grille !")
    assert r.status_code == 500
    with dbmod.SessionLocal() as db:
        assert db.query(Grille).count() == avant


# ── 5, 6 & 7. Une seule porte d'entrée, puis l'écriture au geste ───────────────────────────────────────────────────────────

def test_une_grille_ne_se_cree_que_par_generation():
    """Il n'y a qu'une porte d'entrée. La route « créer une grille vide » a existé un temps ; elle
    est partie le 17/08/2026 — un tableau nu à remplir case par case n'est pas un service, le
    professeur a déjà un tableur. Ce test empêche qu'elle revienne sans qu'on le décide."""
    _prof()
    r = _client().post("/api/contenus/grilles", json={"titre": "Grille à la main"})
    assert r.status_code == 405, r.text      # la ressource existe en GET, pas en POST


def test_chaque_geste_s_ecrit_a_l_instant():
    _prof()
    c = _client()
    gid = _une_grille()

    crit = c.post(f"/api/contenus/grilles/{gid}/criteres",
                  json={"libelle": "Justifie ses réponses", "poids": 2}).json()["id"]
    niv = c.post(f"/api/contenus/grilles/{gid}/niveaux",
                 json={"libelle": "Acquis", "points": 3}).json()["id"]

    # Chaque appel a laissé la base dans un état complet — aucun « valider » n'est nécessaire.
    # La grille arrive écrite par la génération : les ajouts s'y AJOUTENT.
    lu = c.get(f"/api/contenus/grilles/{gid}").json()
    assert "Justifie ses réponses" in [x["libelle"] for x in lu["criteres"]]
    assert "Acquis" in [x["libelle"] for x in lu["niveaux_maitrise"]]

    r = c.put("/api/contenus/grilles/cellules", json={
        "critere_id": crit, "niveau_maitrise_id": niv,
        "descripteur": "Donne la règle qui appuie sa réponse"})
    assert r.status_code == 200, r.text
    lu = c.get(f"/api/contenus/grilles/{gid}").json()
    ligne = next(x for x in lu["criteres"] if x["id"] == crit)
    assert ligne["descripteurs"][str(niv)] == "Donne la règle qui appuie sa réponse"


def test_une_case_videe_n_a_plus_de_ligne():
    _prof()
    c = _client()
    gid = _une_grille()
    crit = c.post(f"/api/contenus/grilles/{gid}/criteres", json={"libelle": "X"}).json()["id"]
    niv = c.post(f"/api/contenus/grilles/{gid}/niveaux", json={"libelle": "A"}).json()["id"]
    corps = {"critere_id": crit, "niveau_maitrise_id": niv}

    c.put("/api/contenus/grilles/cellules", json={**corps, "descripteur": "quelque chose"})
    with dbmod.SessionLocal() as db:
        assert db.query(GrilleCellule).filter_by(critere_id=crit).count() == 1

    c.put("/api/contenus/grilles/cellules", json={**corps, "descripteur": "   "})
    with dbmod.SessionLocal() as db:
        assert db.query(GrilleCellule).filter_by(critere_id=crit).count() == 0


def test_deux_colonnes_de_meme_nom_sont_refusees_a_la_main():
    """À la main, contrairement à la génération, le professeur peut corriger : on le lui dit."""
    _prof()
    c = _client()
    gid = _une_grille()
    c.post(f"/api/contenus/grilles/{gid}/niveaux", json={"libelle": "Acquis"})
    r = c.post(f"/api/contenus/grilles/{gid}/niveaux", json={"libelle": "Acquis"})
    assert r.status_code == 400
    assert "existe déjà" in r.json()["detail"]


def test_une_case_ne_s_ecrit_pas_au_croisement_de_deux_grilles():
    _prof()
    c = _client()
    a = _une_grille("Grille A")
    b = _une_grille("Grille B")
    crit = c.post(f"/api/contenus/grilles/{a}/criteres", json={"libelle": "X"}).json()["id"]
    niv = c.post(f"/api/contenus/grilles/{b}/niveaux", json={"libelle": "A"}).json()["id"]
    r = c.put("/api/contenus/grilles/cellules", json={
        "critere_id": crit, "niveau_maitrise_id": niv, "descripteur": "nulle part"})
    assert r.status_code == 400
    assert "même grille" in r.json()["detail"]


def test_la_duplication_donne_deux_grilles_independantes():
    _prof()
    r, _ = _generer()
    source = r.json()["id"]
    c = _client()
    copie = c.post(f"/api/contenus/grilles/{source}/dupliquer").json()

    assert copie["id"] != source
    assert copie["titre"].endswith("(copie)")
    assert len(copie["criteres"]) == 2 and len(copie["niveaux_maitrise"]) == 4
    assert copie["criteres"][0]["descripteurs"]        # les cases ont suivi

    # Retoucher la copie ne touche pas la source.
    c.put(f"/api/contenus/grilles/criteres/{copie['criteres'][0]['id']}",
          json={"libelle": "Renommé dans la copie", "poids": 1})
    assert c.get(f"/api/contenus/grilles/{source}").json()["criteres"][0]["libelle"] == \
        "Structure le propos"


# ── 8. Ce qui appartient à un autre professeur est introuvable ───────────────────────────

def test_la_grille_d_un_autre_prof_est_introuvable():
    _prof()
    _prof(AUTRE)
    r, _ = _generer()
    gid = r.json()["id"]
    voleur = _client(AUTRE)
    assert voleur.get(f"/api/contenus/grilles/{gid}").status_code == 404
    assert voleur.delete(f"/api/contenus/grilles/{gid}").status_code == 404
    assert gid not in [g["id"] for g in voleur.get("/api/contenus/grilles").json()]


def test_le_critere_d_un_autre_prof_est_introuvable_par_sa_propre_porte():
    """Les critères et les colonnes se modifient par leur identifiant, sans passer par celui de
    la grille : la vérification du propriétaire est donc une jointure, pas un contrôle de chemin."""
    _prof()
    _prof(AUTRE)
    r, _ = _generer()
    grille = r.json()
    voleur = _client(AUTRE)
    crit = grille["criteres"][0]["id"]
    niv = grille["niveaux_maitrise"][0]["id"]
    assert voleur.put(f"/api/contenus/grilles/criteres/{crit}",
                      json={"libelle": "volé", "poids": 1}).status_code == 404
    assert voleur.delete(f"/api/contenus/grilles/criteres/{crit}").status_code == 404
    assert voleur.put(f"/api/contenus/grilles/niveaux/{niv}",
                      json={"libelle": "volé", "points": 0}).status_code == 404
    assert voleur.put("/api/contenus/grilles/cellules", json={
        "critere_id": crit, "niveau_maitrise_id": niv, "descripteur": "volé"}).status_code == 404


# ── 9. Supprimer veut dire supprimer ─────────────────────────────────────────────────────

def test_supprimer_emporte_les_lignes_les_colonnes_et_les_cases():
    _prof()
    r, _ = _generer()
    gid = r.json()["id"]
    with dbmod.SessionLocal() as db:
        criteres = [c.id for c in db.query(GrilleCritere).filter_by(grille_id=gid).all()]

    assert _client().delete(f"/api/contenus/grilles/{gid}").status_code == 200

    with dbmod.SessionLocal() as db:
        assert db.get(Grille, gid) is None
        assert db.query(GrilleCritere).filter_by(grille_id=gid).count() == 0
        assert db.query(GrilleNiveauMaitrise).filter_by(grille_id=gid).count() == 0
        assert db.query(GrilleCellule).filter(GrilleCellule.critere_id.in_(criteres)).count() == 0


def test_supprimer_une_colonne_emporte_la_case_de_chaque_critere():
    _prof()
    r, _ = _generer()
    grille = r.json()
    colonne = grille["niveaux_maitrise"][0]["id"]
    criteres = [c["id"] for c in grille["criteres"]]

    assert _client().delete(f"/api/contenus/grilles/niveaux/{colonne}").status_code == 200

    with dbmod.SessionLocal() as db:
        assert db.query(GrilleCellule).filter(
            GrilleCellule.critere_id.in_(criteres),
            GrilleCellule.niveau_maitrise_id == colonne).count() == 0
        # Les trois autres colonnes de chaque critère sont intactes.
        assert db.query(GrilleCellule).filter(GrilleCellule.critere_id.in_(criteres)).count() == 6
