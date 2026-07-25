"""Case « Inclure une proposition de correction » BRANCHÉE sur la génération (24/07).

Avant : la case n'était qu'une étiquette (sauvegardée dans Mes activités) — le prompt de
génération ne la lisait jamais (« DIFFÉRÉ »). Désormais :

Ce que ces tests PROUVENT :
  1. Case COCHÉE → la consigne du corrigé (registre des prompts admin, clé `correction`)
     est ajoutée à la FIN du prompt envoyé à l'IA — le corrigé sortira sous l'activité.
  2. Case DÉCOCHÉE (ou absente) → le prompt est STRICTEMENT le gabarit du couple rempli,
     sans la consigne — zéro changement pour l'existant.

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


def _client_prof():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def _couple_avec_type(nom, ordre, prompt):
    """Cycle + niveau + référentiel + un type relié avec son prompt. Renvoie (niveau_nom, type_id)."""
    from backend.core.models_db import (Cycle, Niveau, Referentiel, ActiviteType,
                                        ReferentielActiviteType)
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom=f"CO-{nom}", ordre=ordre)
        db.add(cy); db.flush()
        niv = Niveau(cycle_id=cy.id, nom=f"CO-Niv{nom}", ordre=ordre)
        db.add(niv); db.flush()
        ref = Referentiel(niveau_id=niv.id, matiere_id=None, nom_fixe=f"co_{nom.lower()}",
                          collection=f"co_{nom.lower()}", filtres=None, fichier="doc.pdf",
                          texte_epure="TEXTE")
        db.add(ref); db.flush()
        t = ActiviteType(label=f"CO-Type{nom}", ordre=1, actif=True, origine="systeme")
        db.add(t); db.flush()
        db.add(ReferentielActiviteType(referentiel_id=ref.id, activite_type_id=t.id,
                                       actif=True, source="admin", prompt=prompt, ordre=1))
        db.commit()
        return niv.nom, t.id


GABARIT = "Texte : {texte}\nFais des questions pour {niveau}.\n{referentiel}"


def _generer(niveau, tid, avec_correction):
    faux_rag = [{"text": "Extrait officiel.", "score": 0.9}]
    with patch("backend.contenu.activites.retrieve_pg", return_value=faux_rag), \
         patch("backend.contenu.activites.generate_stream", return_value=iter(["OK"])) as gen:
        r = _client_prof().post("/api/generate", json={
            "texte": "Le cycle de l'eau.", "activite_type_id": tid, "niveau": niveau,
            "avec_correction": avec_correction,
        })
    assert r.status_code == 200, r.text
    assert "event: done" in r.text
    return gen.call_args.args[0]   # le prompt réellement envoyé à l'IA


def test_case_cochee_la_consigne_du_corrige_est_ajoutee_a_la_fin():
    niveau, tid = _couple_avec_type("Coche", 88, GABARIT)
    prompt = _generer(niveau, tid, avec_correction=True)
    # La consigne du corrigé (registre admin) termine le prompt — le corrigé sort sous l'activité.
    assert prompt.endswith("\n\n" + CONSIGNE_CORRIGE)
    # Et le gabarit du couple rempli est bien là, intact, AVANT la consigne.
    assert prompt.startswith("Texte : Le cycle de l'eau.")
    assert "Extrait officiel." in prompt


def test_case_decochee_prompt_strictement_identique_a_l_existant():
    niveau, tid = _couple_avec_type("Sans", 89, GABARIT)
    prompt = _generer(niveau, tid, avec_correction=False)
    assert prompt == GABARIT.format(texte="Le cycle de l'eau.", niveau=niveau,
                                    referentiel="Extrait officiel.")
    assert CONSIGNE_CORRIGE not in prompt
