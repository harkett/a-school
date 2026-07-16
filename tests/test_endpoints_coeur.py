"""Filet de test — les 5 endpoints cœur d'aSchool (Phase 1 du plan de reprise).

Lance avec :  pytest   (suite pytest — convention unique du projet)

Couverture (choix (b) : happy path + cas d'erreur connus) :
  - generate, generate-sequence, optimize-sequence, detect-ambiguites, analyser-consigne
  - happy path : 200 + sortie cohérente (Groq MOCKÉ — aucun appel réseau)
  - auth      : 401 sans cookie / token invalide
  - validation: 400 (entrée vide / invalide) et 422 (champ requis manquant)
  - résilience : panne LLM amont -> 502 (/api/generate) / 500 (outils via generate())

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
from backend.auth import create_access_token
from fastapi.testclient import TestClient

TOKEN = create_access_token("filet-test@local.test")


def authed():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def noauth():
    return TestClient(app)


# ----- Sorties Groq canned (valides) pour le happy path -----
SEQ_MD = "# Séance : Test\n**Matière :** SVT | **Niveau :** 3e | **Durée :** 55 min\n\n## Phase 1 — Intro (55 min)\n**Objectif :** découvrir\n"
OPT_JSON = '{"problemes": [{"type": "Surcharge cognitive", "detail": "trop de notions"}], "sequence_optimisee": "# Séance optimisée", "score": "À revoir — 1 problème(s) détecté(s)"}'
AMB_JSON = '{"ambiguites": [{"extrait": "analysez", "type": "Consigne vague", "risque": "flou", "reformulation": "Identifiez X"}], "verdict": "Énoncé à clarifier."}'
CON_JSON = '{"analyses": [{"axe": "Clarté linguistique", "severite": "Élevée", "extrait": "expliquez", "probleme": "vague", "conseil": "précisez"}], "verdict": "À clarifier.", "version_optimisee": "Consigne réécrite."}'


# ===================== HAPPY PATH (200 + sortie cohérente) =====================

def test_generate_sequence_happy():
    with patch("backend.sequence.sequence.generate", return_value=SEQ_MD):
        r = authed().post("/api/generate-sequence", json={
            "theme": "Photosynthèse", "matiere": "SVT", "niveau": "3e",
            "duree": 55, "mode": "standard", "description_classe": ""})
    assert r.status_code == 200, r.text
    assert "Phase 1" in r.json()["resultat"]


def test_optimize_happy():
    with patch("backend.sequence.optimiseur.generate", return_value=OPT_JSON):
        r = authed().post("/api/optimize-sequence", json={
            "sequence": "# Séance\n## Phase 1 (55 min)", "matiere": "SVT", "niveau": "3e"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["score"] and len(d["problemes"]) == 1


def test_ambiguites_happy():
    with patch("backend.analyse.ambiguites.generate", return_value=AMB_JSON):
        r = authed().post("/api/detect-ambiguites", json={
            "texte": "Analysez le document.", "matiere": "SVT", "niveau": "3e"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["verdict"] and len(d["ambiguites"]) == 1


def test_consigne_happy():
    with patch("backend.analyse.consigne.generate", return_value=CON_JSON):
        r = authed().post("/api/analyser-consigne", json={
            "consigne": "Expliquez la photosynthèse.", "matiere": "SVT", "niveau": "3e"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["version_optimisee"] and len(d["analyses"]) == 1


# ===================== AUTH 401 (sans cookie) =====================

def test_401_sans_cookie():
    c = noauth()
    cases = [
        ("/api/generate-sequence", {"theme": "x", "matiere": "SVT", "niveau": "3e", "duree": 55}),
        ("/api/optimize-sequence", {"sequence": "x", "matiere": "SVT", "niveau": "3e"}),
        ("/api/detect-ambiguites", {"texte": "x", "matiere": "SVT", "niveau": "3e"}),
        ("/api/analyser-consigne", {"consigne": "x", "matiere": "SVT", "niveau": "3e"}),
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
    # generate-sequence : thème vide, durée invalide, mode invalide, remédiation sans description
    assert c.post("/api/generate-sequence", json={"theme": "  ", "matiere": "SVT", "niveau": "3e", "duree": 55}).status_code == 400
    assert c.post("/api/generate-sequence", json={"theme": "X", "matiere": "SVT", "niveau": "3e", "duree": 999}).status_code == 400
    assert c.post("/api/generate-sequence", json={"theme": "X", "matiere": "SVT", "niveau": "3e", "duree": 55, "mode": "n_importe_quoi"}).status_code == 400
    assert c.post("/api/generate-sequence", json={"theme": "X", "matiere": "SVT", "niveau": "3e", "duree": 55, "mode": "remediation", "description_classe": ""}).status_code == 400
    # optimize / ambiguites / consigne : entrée vide
    assert c.post("/api/optimize-sequence", json={"sequence": "   ", "matiere": "SVT", "niveau": "3e"}).status_code == 400
    assert c.post("/api/detect-ambiguites", json={"texte": "   ", "matiere": "SVT", "niveau": "3e"}).status_code == 400
    assert c.post("/api/analyser-consigne", json={"consigne": "   ", "matiere": "SVT", "niveau": "3e"}).status_code == 400


# ===================== RÉSILIENCE — panne LLM amont =====================
# Les 4 outils (ambiguites/consigne/optimiseur/sequence) passent par generate().
# Une panne LLM (generate lève RuntimeError) -> 500 côté outil (Tâche 2 : unification
# sur 500 ; chaîne de repli abandonnée, plus de 502 « externe » Groq).

def test_endpoint_outil_llm_down_500():
    """Si le LLM est down (generate lève RuntimeError), l'optimiseur renvoie 500."""
    with patch("backend.sequence.optimiseur.generate", side_effect=RuntimeError("LLM down")):
        r = authed().post("/api/optimize-sequence", json={
            "sequence": "# Séance\n## Phase 1 (55 min)", "matiere": "SVT", "niveau": "3e"})
    assert r.status_code == 500, r.text


# ===================== Programmes — lecture référentiel (profil) =====================
# Ne renvoie que les niveaux UTILISABLES (>= 1 paire active), groupés par cycle.
# Un cycle sans paire (ex. Supérieur) ne doit PAS apparaître -> coeur du fix P5.11.

def test_programmes_niveaux_utilisables_groupes_par_cycle():
    from backend.core.models_db import Cycle, Niveau, Matiere, MatiereNiveau
    db = dbmod.SessionLocal()
    col = Cycle(nom="Collège", ordre=4); db.add(col)
    sup = Cycle(nom="Supérieur", ordre=6); db.add(sup); db.flush()
    n6 = Niveau(cycle_id=col.id, nom="6e", ordre=9); db.add(n6)
    nbts = Niveau(cycle_id=sup.id, nom="BTS", ordre=20); db.add(nbts)  # aucune paire -> exclu
    mat = Matiere(nom="Mathématiques", ordre=2); db.add(mat); db.flush()
    db.add(MatiereNiveau(matiere_id=mat.id, niveau_id=n6.id))
    db.commit(); db.close()

    data = noauth().get("/api/programmes").json()
    assert any(m["nom"] == "Mathématiques" for m in data["matieres"])
    cycles = {g["cycle"]: [n["nom"] for n in g["niveaux"]] for g in data["niveaux_par_cycle"]}
    assert cycles.get("Collège") == ["6e"]      # niveau avec paire -> présent
    assert "Supérieur" not in cycles            # cycle sans paire -> absent (P5.11)


def test_programmes_matieres_par_cycle():
    # Matières scopées par cycle (menu matière du profil) : paire active + matière active.
    # BDD de test partagée -> identifiants uniques (mpc-*) pour ne rien collisionner.
    from backend.core.models_db import Cycle, Niveau, Matiere, MatiereNiveau
    db = dbmod.SessionLocal()
    cA = Cycle(nom="MPC-Cycle-A", ordre=40); db.add(cA)
    cB = Cycle(nom="MPC-Cycle-B", ordre=41); db.add(cB); db.flush()
    nA = Niveau(cycle_id=cA.id, nom="MPC-nivA", ordre=40); db.add(nA)
    nB = Niveau(cycle_id=cB.id, nom="MPC-nivB", ordre=41); db.add(nB); db.flush()
    m1 = Matiere(nom="MPC-Mat1", ordre=40); db.add(m1)
    m2 = Matiere(nom="MPC-Mat2", ordre=41); db.add(m2)
    inact = Matiere(nom="MPC-Inactive", ordre=99, actif=False); db.add(inact)
    db.flush()
    db.add(MatiereNiveau(matiere_id=m1.id, niveau_id=nA.id))                  # Mat1 -> Cycle-A
    db.add(MatiereNiveau(matiere_id=m2.id, niveau_id=nB.id))                  # Mat2 -> Cycle-B
    db.add(MatiereNiveau(matiere_id=inact.id, niveau_id=nA.id))               # matière INACTIVE -> exclue
    db.add(MatiereNiveau(matiere_id=m1.id, niveau_id=nB.id, actif=False))     # paire INACTIVE -> Mat1 pas en Cycle-B
    db.commit(); db.close()

    data = noauth().get("/api/programmes").json()
    parc = {g["cycle"]: [m["nom"] for m in g["matieres"]] for g in data["matieres_par_cycle"]}
    assert parc.get("MPC-Cycle-A") == ["MPC-Mat1"]   # la matière inactive est exclue malgré sa paire
    assert parc.get("MPC-Cycle-B") == ["MPC-Mat2"]   # Mat1 absent : sa seule paire ici est inactive


def test_programmes_matieres_par_niveau():
    # Matières scopées par NIVEAU (le programme du diplôme) : paire active + matière active,
    # dans l'ORDRE D'INSERTION des paires (= ordre du référentiel), PAS l'ordre global matiere.
    from backend.core.models_db import Cycle, Niveau, Matiere, MatiereNiveau
    db = dbmod.SessionLocal()
    cyc = Cycle(nom="MPN-Cycle", ordre=50); db.add(cyc); db.flush()
    niv = Niveau(cycle_id=cyc.id, nom="MPN-Diplome", ordre=50); db.add(niv); db.flush()
    # ordre GLOBAL volontairement DÉCROISSANT (99,98,97) : si l'API ordonnait par matiere.ordre
    # on aurait C,B,A — le test attend A,B,C, donc il prouve l'ordre d'insertion des paires.
    mA = Matiere(nom="MPN-A", ordre=99); db.add(mA)
    mB = Matiere(nom="MPN-B", ordre=98); db.add(mB)
    mC = Matiere(nom="MPN-C", ordre=97); db.add(mC)
    mInact = Matiere(nom="MPN-Inact", ordre=96, actif=False); db.add(mInact)
    mD = Matiere(nom="MPN-D", ordre=95); db.add(mD)
    db.flush()
    db.add(MatiereNiveau(matiere_id=mA.id, niveau_id=niv.id))                 # A
    db.add(MatiereNiveau(matiere_id=mB.id, niveau_id=niv.id))                 # B
    db.add(MatiereNiveau(matiere_id=mC.id, niveau_id=niv.id))                 # C
    db.add(MatiereNiveau(matiere_id=mInact.id, niveau_id=niv.id))             # matière INACTIVE -> exclue
    db.add(MatiereNiveau(matiere_id=mD.id, niveau_id=niv.id, actif=False))    # paire INACTIVE -> exclue
    db.commit(); db.close()

    data = noauth().get("/api/programmes").json()
    parn = {g["niveau"]: [m["nom"] for m in g["matieres"]] for g in data["matieres_par_niveau"]}
    assert parn.get("MPN-Diplome") == ["MPN-A", "MPN-B", "MPN-C"]  # ordre d'insertion, exclusions OK


def test_programmes_niveau_ref_disponible_expose():
    # niveaux_par_cycle expose `refDisponible`, DÉRIVÉ (jamais stocké) : vrai ssi le niveau a
    # un référentiel réellement ingéré (>= 1 chunk). Référentiel sans chunk => faux ;
    # pas de référentiel du tout => faux.
    from backend.core.models_db import (
        Cycle, Niveau, Matiere, MatiereNiveau, Referentiel, ReferentielChunk,
    )
    db = dbmod.SessionLocal()
    cyc = Cycle(nom="NT-Cycle", ordre=60); db.add(cyc); db.flush()
    nDispo     = Niveau(cycle_id=cyc.id, nom="NT-Dispo", ordre=60);     db.add(nDispo)
    nSansChunk = Niveau(cycle_id=cyc.id, nom="NT-SansChunk", ordre=61); db.add(nSansChunk)
    nSansRef   = Niveau(cycle_id=cyc.id, nom="NT-SansRef", ordre=62);   db.add(nSansRef)
    m = Matiere(nom="NT-Mat", ordre=60); db.add(m); db.flush()
    # une paire par niveau => les trois apparaissent dans l'endpoint
    db.add_all([
        MatiereNiveau(matiere_id=m.id, niveau_id=nDispo.id),
        MatiereNiveau(matiere_id=m.id, niveau_id=nSansChunk.id),
        MatiereNiveau(matiere_id=m.id, niveau_id=nSansRef.id),
    ])
    # référentiel + 1 chunk => nDispo disponible (matiere_id=None = couvre tout le niveau)
    refDispo = Referentiel(niveau_id=nDispo.id, matiere_id=None,
                           nom_fixe="NT-ref-dispo", collection="nt_dispo")
    db.add(refDispo); db.flush()
    db.add(ReferentielChunk(referentiel_id=refDispo.id, chunk_index=0, option_ab="A",
                            page=1, texte="x", embedding=[0.0] * 1024, embedding_model="test"))
    # référentiel SANS chunk => nSansChunk reste indisponible (prouve la règle >= 1 chunk)
    db.add(Referentiel(niveau_id=nSansChunk.id, matiere_id=None,
                       nom_fixe="NT-ref-sanschunk", collection="nt_sanschunk"))
    db.commit(); db.close()

    data = noauth().get("/api/programmes").json()
    grp = next(g for g in data["niveaux_par_cycle"] if g["cycle"] == "NT-Cycle")
    flags = {n["nom"]: n["refDisponible"] for n in grp["niveaux"]}
    assert flags == {"NT-Dispo": True, "NT-SansChunk": False, "NT-SansRef": False}


# ===================== Programmes ADMIN — CRUD (T1) =====================
# GET arbre complet (inactives incluses) + PATCH bascule paire (cree/desactive,
# JAMAIS de DELETE) + POST niveau (debloque superieur/creche, avec gardes).

def admin_client():
    from backend.systeme.admin import _make_admin_token
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def test_admin_programmes_arbre_complet_inactives_incluses():
    from backend.core.models_db import Cycle, Niveau, Matiere
    db = dbmod.SessionLocal()
    cyc = Cycle(nom="CycleAdminTest", ordre=99); db.add(cyc); db.flush()
    db.add(Niveau(cycle_id=cyc.id, nom="NivA", ordre=1))
    db.add(Matiere(nom="MatAdmin", ordre=99, actif=False))  # INACTIVE
    db.commit(); db.close()

    assert noauth().get("/api/admin/programmes").status_code == 401  # garde admin

    data = admin_client().get("/api/admin/programmes").json()
    assert "CycleAdminTest" in {c["nom"] for c in data["cycles"]}
    assert any(m["nom"] == "MatAdmin" and m["actif"] is False for m in data["matieres"])  # inactive presente


def test_admin_toggle_paire_cree_puis_desactive_sans_delete():
    from backend.core.models_db import Cycle, Niveau, Matiere, MatiereNiveau
    db = dbmod.SessionLocal()
    cyc = Cycle(nom="CycPaire", ordre=98); db.add(cyc); db.flush()
    niv = Niveau(cycle_id=cyc.id, nom="NivP", ordre=1); db.add(niv); db.flush()
    mat = Matiere(nom="MatPaire", ordre=98); db.add(mat); db.flush()
    mid, nid = mat.id, niv.id
    db.commit(); db.close()

    cl = admin_client()
    assert cl.patch("/api/admin/programmes/paire",
                    json={"matiere_id": mid, "niveau_id": nid, "actif": True}).status_code == 200

    def _paire():
        d = dbmod.SessionLocal()
        p = d.query(MatiereNiveau).filter_by(matiere_id=mid, niveau_id=nid).first()
        res = (p is not None, p.actif if p else None)
        d.close()
        return res

    assert _paire() == (True, True)   # creee active
    cl.patch("/api/admin/programmes/paire", json={"matiere_id": mid, "niveau_id": nid, "actif": False})
    assert _paire() == (True, False)  # ligne CONSERVEE, actif False (pas de DELETE)

    assert cl.patch("/api/admin/programmes/paire",
                    json={"matiere_id": 999999, "niveau_id": nid, "actif": True}).status_code == 404


# ===================== P4.7 — jalon few-shot « aSchool vous reconnaît » =====================
# Le toast est piloté par le backend : few_shot_just_reached=True UNE seule fois, au
# franchissement réel du seuil de SAUVEGARDES (_FEW_SHOT_MIN), par couple (prof, type).
# Robustesse exigée : jamais raté, jamais rejoué (au-delà du seuil, ni après suppression).

def _save_payload(key="comprehension"):
    return {
        "activite_key": key, "activite_label": "Compréhension",
        "niveau": "3e", "texte_source": "La photosynthèse.", "resultat": "1. ? 2. ?",
    }


def _client_for(email):
    """Client authentifié pour un prof réel en base (la route save lit user_id depuis users)."""
    from backend.core.models_db import User
    db = dbmod.SessionLocal()
    if not db.query(User).filter(User.email == email).first():
        db.add(User(email=email, password_hash="x", is_verified=True))
        db.commit()
    db.close()
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(email))
    return c


def _reached(client, key="comprehension"):
    return client.post("/api/mes-activites", json=_save_payload(key)).json()["few_shot_just_reached"]


def test_few_shot_franchi_une_seule_fois_au_seuil():
    c = _client_for("fewshot-1@local.test")
    assert [_reached(c) for _ in range(3)] == [False, False, True]   # vrai à la 3e seulement
    assert _reached(c) is False                                      # 4e -> plus jamais


def test_few_shot_pas_rejoue_apres_suppression():
    c = _client_for("fewshot-2@local.test")
    ids = [c.post("/api/mes-activites", json=_save_payload()).json()["id"] for _ in range(3)]
    assert c.delete(f"/api/mes-activites/{ids[0]}").status_code == 200   # compte 3 -> 2
    assert _reached(c) is False                                          # repasse par 3 -> pas de rejeu


def test_few_shot_etanche_par_type_et_par_prof():
    c = _client_for("fewshot-3@local.test")
    assert [_reached(c, "typeA") for _ in range(3)] == [False, False, True]
    assert _reached(c, "typeB") is False                 # autre type, MÊME prof -> compteur indépendant
    c2 = _client_for("fewshot-4@local.test")
    assert _reached(c2, "typeA") is False                # autre prof, même type -> indépendant aussi


def test_few_shot_pas_rate_si_le_compte_saute_le_seuil():
    """Le compte atteint directement 4 sans que la logique jalon n'ait jamais vu 3
    (ex. sauvegardes concurrentes) : le >= garantit qu'on ne rate PAS le franchissement
    -> few_shot_just_reached = True une seule fois, jamais ensuite."""
    from backend.core.models_db import User, ActiviteSauvegardee
    db = dbmod.SessionLocal()
    db.add(User(email="fewshot-5@local.test", password_hash="x", is_verified=True))
    db.commit()
    uid = db.query(User.id).filter(User.email == "fewshot-5@local.test").scalar()
    # 3 sauvegardes posées DIRECTEMENT en base : la route n'a jamais évalué le jalon à 3
    for _ in range(3):
        db.add(ActiviteSauvegardee(user_id=uid, activite_key="saut", activite_label="X",
                                   niveau="3e", avec_correction=False, texte_source="t", resultat="r"))
    db.commit(); db.close()

    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token("fewshot-5@local.test"))
    assert _reached(c, "saut") is True     # 1er POST -> compte passe à 4 -> franchissement quand même
    assert _reached(c, "saut") is False    # ensuite -> jalon déjà posé -> plus jamais


# ===================== /api/matieres — matières dérivées de la base =====================
# GET /api/matieres dérive les matières de la BASE par jointure matieres⋈matiere_niveaux
# (plus de liste en dur, plus de filtre par catégorie). Données préfixées (BDD partagée)
# pour ne rien collisionner.

def test_matieres_derive_de_la_base():
    from backend.core.models_db import Cycle, Niveau, Matiere, MatiereNiveau
    db = dbmod.SessionLocal()
    c = Cycle(nom="P510-Cyc", ordre=510); db.add(c); db.flush()
    n = Niveau(cycle_id=c.id, nom="P510-4e", ordre=510); db.add(n); db.flush()
    mFr   = Matiere(nom="P510-Français", ordre=5101); db.add(mFr)
    mMath = Matiere(nom="P510-Maths",    ordre=5102); db.add(mMath)
    db.flush()
    db.add(MatiereNiveau(matiere_id=mFr.id,   niveau_id=n.id))
    db.add(MatiereNiveau(matiere_id=mMath.id, niveau_id=n.id))
    db.commit(); db.close()

    noms = [m["nom"] for m in noauth().get("/api/matieres").json()]
    assert "P510-Français" in noms and "P510-Maths" in noms   # matières actives à paire active


