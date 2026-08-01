"""Cahier des charges du prof BRANCHÉ sur la génération — POST /api/generate (Étape 2).

Ce que ces tests PROUVENT :
  1. Cahier déposé (cahiers_prof.texte_epure non vide) → son texte est AJOUTÉ au prompt envoyé à
     l'IA, sous l'intitulé « Cahier des charges de l'établissement… », APRÈS le programme officiel
     (les règles de l'école s'appliquent par-dessus le programme). Lu EN BASE (get, zéro copie).
  2. Aucun cahier → prompt STRICTEMENT identique au gabarit du couple rempli (aucune régression).
  3. Cahier au texte VIDE (PDF sans texte exploitable) → traité comme pas de cahier (rien ajouté).

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
from backend.core.llm_prompts import PROMPTS
from fastapi.testclient import TestClient

TOKEN = create_access_token("prof.test@aschool.fr")

GABARIT = "Texte : {texte}\nFais des questions pour {niveau}.\n{referentiel}"
CONTROLE_QUALITE = PROMPTS["controle_qualite"]["default"]   # dernière couche du prompt, toujours ajoutée


def _client_prof():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def _preparer(nom, ordre, prompt, cahier_texte=None):
    """Cycle + niveau + référentiel + type relié (avec son prompt) + LE PROF EN BASE (son profil
    porte ce niveau). Si `cahier_texte` est fourni, dépose un cahier des charges pour ce prof
    (cahiers_prof.texte_epure). Renvoie (niveau_nom, type_id)."""
    from backend.core.models_db import (Cycle, Niveau, Referentiel, ActiviteType,
                                        ReferentielActiviteType, CahierProf)
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom=f"CG-{nom}", ordre=ordre); db.add(cy); db.flush()
        niv = Niveau(cycle_id=cy.id, nom=f"CG-Niv{nom}", ordre=ordre); db.add(niv); db.flush()
        ref = Referentiel(niveau_id=niv.id, nom_fixe=f"cg_{nom.lower()}",
                          collection=f"cg_{nom.lower()}", filtres=None, fichier="doc.pdf",
                          texte_epure="TEXTE")
        db.add(ref); db.flush()
        t = ActiviteType(label=f"CG-Type{nom}", ordre=1, actif=True, origine="systeme")
        db.add(t); db.flush()
        db.add(ReferentielActiviteType(referentiel_id=ref.id, activite_type_id=t.id,
                                       actif=True, source="admin", prompt=prompt, ordre=1))
        from _profil import user_couple
        u = user_couple(db, email="prof.test@aschool.fr", password_hash="x", is_verified=True,
                    subject=f"CG-Matiere-{nom}", niveau=niv.nom)
        db.add(u); db.flush()
        if cahier_texte is not None:
            db.add(CahierProf(user_id=u.id, fichier="cahier.pdf", texte_epure=cahier_texte))
        db.commit()
        return niv.nom, t.id


def _generer(tid):
    faux_rag = [{"text": "Extrait officiel.", "score": 0.9}]
    with patch("backend.contenu.activites.retrieve_pg", return_value=faux_rag), \
         patch("backend.contenu.activites.generate_stream", return_value=iter(["OK"])) as gen:
        r = _client_prof().post("/api/generate", json={
            "texte": "Le cycle de l'eau.", "activite_type_id": tid})
    assert r.status_code == 200, r.text
    assert "event: done" in r.text
    return gen.call_args.args[0]   # le prompt réellement envoyé à l'IA


def test_cahier_present_est_injecte_apres_le_programme_officiel():
    _niveau, tid = _preparer("Avec", 90, GABARIT, cahier_texte="RÈGLE ÉCOLE : pas de note chiffrée.")
    prompt = _generer(tid)
    # Le gabarit du couple rempli est là, intact (programme officiel inclus)...
    assert prompt.startswith("Texte : Le cycle de l'eau.")
    assert "Extrait officiel." in prompt
    # ...et le cahier est AJOUTÉ après, sous son intitulé.
    assert "Cahier des charges de l'établissement" in prompt
    assert "RÈGLE ÉCOLE : pas de note chiffrée." in prompt
    # Ordre garanti : le programme officiel vient AVANT le bloc cahier (règles par-dessus).
    assert prompt.index("Extrait officiel.") < prompt.index("Cahier des charges de l'établissement")


def test_sans_cahier_prompt_strictement_identique():
    niveau, tid = _preparer("Sans", 91, GABARIT, cahier_texte=None)
    prompt = _generer(tid)
    # Aucun cahier ajouté : le prompt = gabarit du couple rempli + le CONTRÔLE QUALITÉ (toujours là).
    assert prompt == GABARIT.format(texte="Le cycle de l'eau.", niveau=niveau,
                                    referentiel="Extrait officiel.") + "\n\n" + CONTROLE_QUALITE
    assert "Cahier des charges de l'établissement" not in prompt


def test_cahier_texte_vide_ne_change_rien():
    # Cahier déposé mais texte épuré vide (PDF scanné sans texte) → traité comme pas de cahier.
    niveau, tid = _preparer("Vide", 92, GABARIT, cahier_texte="   ")
    prompt = _generer(tid)
    assert prompt == GABARIT.format(texte="Le cycle de l'eau.", niveau=niveau,
                                    referentiel="Extrait officiel.") + "\n\n" + CONTROLE_QUALITE
    assert "Cahier des charges de l'établissement" not in prompt


# ── « Propose-moi une idée » (/api/proposer-idee) : même branchement du cahier ──

def _idee(tid):
    faux_rag = [{"text": "Extrait officiel.", "score": 0.9, "page": 2}]
    with patch("backend.contenu.activites.retrieve_pg", return_value=faux_rag), \
         patch("backend.contenu.activites.generate", return_value="Une idée simple.") as gen:
        r = _client_prof().post("/api/proposer-idee", json={"activite_type_id": tid})
    assert r.status_code == 200, r.text
    assert r.json()["available"] is True
    return gen.call_args.args[0]   # le prompt réellement envoyé à l'IA


def test_idee_cahier_present_est_injecte():
    _niveau, tid = _preparer("IdeeAvec", 93, GABARIT, cahier_texte="RÈGLE ÉCOLE IDÉE.")
    prompt = _idee(tid)
    assert "Cahier des charges de l'établissement" in prompt
    assert "RÈGLE ÉCOLE IDÉE." in prompt


def test_idee_sans_cahier_pas_de_bloc():
    _niveau, tid = _preparer("IdeeSans", 94, GABARIT, cahier_texte=None)
    prompt = _idee(tid)
    assert "Cahier des charges de l'établissement" not in prompt


# ── « Document d'exemple » (/api/exemple-referentiel) : même branchement du cahier ──

def _exemple():
    faux_rag = [{"text": "Extrait officiel.", "score": 0.9, "page": 2}]
    with patch("backend.pedagogie.exemple_referentiel.retrieve_pg", return_value=faux_rag), \
         patch("backend.pedagogie.exemple_referentiel.generate", return_value="Texte exemple.") as gen:
        r = _client_prof().post("/api/exemple-referentiel", json={})
    assert r.status_code == 200, r.text
    assert r.json()["available"] is True
    return gen.call_args.args[0]


def test_exemple_cahier_present_est_injecte():
    _preparer("ExAvec", 95, GABARIT, cahier_texte="RÈGLE ÉCOLE EXEMPLE.")
    prompt = _exemple()
    assert "Cahier des charges de l'établissement" in prompt
    assert "RÈGLE ÉCOLE EXEMPLE." in prompt


def test_exemple_sans_cahier_pas_de_bloc():
    _preparer("ExSans", 96, GABARIT, cahier_texte=None)
    prompt = _exemple()
    assert "Cahier des charges de l'établissement" not in prompt
