"""Case « Inclure une proposition de correction » BRANCHÉE sur la génération (24/07).

Avant : la case n'était qu'une étiquette (sauvegardée dans Mes activités) — le prompt de
génération ne la lisait jamais (« DIFFÉRÉ »). Désormais :

Ce que ces tests PROUVENT :
  1. Case COCHÉE → la consigne du corrigé (registre des prompts admin, clé `correction`)
     est ajoutée au prompt envoyé à l'IA, AVANT le bloc CONTRÔLE QUALITÉ final — le corrigé
     sortira sous l'activité, et le contrôle qualité le relit lui aussi.
  2. Case DÉCOCHÉE (ou absente) → le prompt est le gabarit du couple rempli SANS la consigne
     du corrigé (le CONTRÔLE QUALITÉ, lui, est TOUJOURS ajouté en dernier).

NB (ordre voulu) : le CONTRÔLE QUALITÉ est la dernière couche du prompt, APRÈS la consigne du
corrigé — c'est une relecture finale qui couvre l'activité ET son corrigé.

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

CONSIGNE_CORRIGE = PROMPTS["correction"]["default"]
CONTROLE_QUALITE = PROMPTS["controle_qualite"]["default"]   # dernière couche, toujours ajoutée


def _client_prof():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def _couple_avec_type(nom, ordre, prompt):
    """Cycle + niveau + référentiel + un type relié avec son prompt + LE PROF EN BASE (son
    profil porte ce niveau : la génération lit le couple EN BASE, plus le corps — 25/07).
    Renvoie (niveau_nom, type_id)."""
    from backend.core.models_db import (Cycle, Niveau, Referentiel, ActiviteType,
                                        ReferentielActiviteType, User)
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom=f"CO-{nom}", ordre=ordre)
        db.add(cy); db.flush()
        niv = Niveau(cycle_id=cy.id, nom=f"CO-Niv{nom}", ordre=ordre)
        db.add(niv); db.flush()
        ref = Referentiel(niveau_id=niv.id, nom_fixe=f"co_{nom.lower()}",
                          collection=f"co_{nom.lower()}", filtres=None, fichier="doc.pdf",
                          texte_epure="TEXTE")
        db.add(ref); db.flush()
        t = ActiviteType(label=f"CO-Type{nom}", ordre=1, actif=True, origine="systeme")
        db.add(t); db.flush()
        db.add(ReferentielActiviteType(referentiel_id=ref.id, activite_type_id=t.id,
                                       actif=True, source="admin", prompt=prompt, ordre=1))
        from _profil import user_couple
        db.add(user_couple(db, email="prof.test@aschool.fr", password_hash="x", is_verified=True,
                    subject=f"CO-Matiere-{nom}", niveau=niv.nom))
        db.commit()
        return niv.nom, t.id


GABARIT = "Texte : {texte}\nFais des questions pour {niveau}.\n{referentiel}"


def _generer(niveau, tid, avec_correction):
    faux_rag = [{"text": "Extrait officiel.", "score": 0.9}]
    # Le niveau ne part plus du corps de requête : il est lu EN BASE (profil du prof).
    with patch("backend.contenu.activites.retrieve_pg", return_value=faux_rag), \
         patch("backend.contenu.activites.generate_stream", return_value=iter(["OK"])) as gen:
        r = _client_prof().post("/api/generate", json={
            "texte": "Le cycle de l'eau.", "activite_type_id": tid,
            "avec_correction": avec_correction,
        })
    assert r.status_code == 200, r.text
    assert "event: done" in r.text
    return gen.call_args.args[0]   # le prompt réellement envoyé à l'IA


def test_case_cochee_la_consigne_du_corrige_est_ajoutee():
    niveau, tid = _couple_avec_type("Coche", 88, GABARIT)
    prompt = _generer(niveau, tid, avec_correction=True)
    # Le gabarit du couple rempli est là, intact, en tête.
    assert prompt.startswith("Texte : Le cycle de l'eau.")
    assert "Extrait officiel." in prompt
    # La consigne du corrigé (registre admin) est présente — le corrigé sort sous l'activité.
    assert "\n\n" + CONSIGNE_CORRIGE in prompt
    # Le CONTRÔLE QUALITÉ termine le prompt (toujours ajouté) et vient APRÈS le corrigé : c'est
    # la relecture finale, qui couvre l'activité ET son corrigé (ordre voulu).
    assert prompt.endswith("\n\n" + CONTROLE_QUALITE)
    assert prompt.index(CONSIGNE_CORRIGE) < prompt.index(CONTROLE_QUALITE)


def test_case_decochee_pas_de_corrige_dans_le_prompt():
    niveau, tid = _couple_avec_type("Sans", 89, GABARIT)
    prompt = _generer(niveau, tid, avec_correction=False)
    # Décochée : gabarit du couple rempli + le CONTRÔLE QUALITÉ (toujours là), rien d'autre.
    assert prompt == GABARIT.format(texte="Le cycle de l'eau.", niveau=niveau,
                                    referentiel="Extrait officiel.") + "\n\n" + CONTROLE_QUALITE
    assert CONSIGNE_CORRIGE not in prompt
