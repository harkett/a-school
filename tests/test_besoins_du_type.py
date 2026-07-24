"""Champ « Nombre de questions » piloté par le prompt du couple×type (une source, pas deux).

Décision du 24/07 : la zone TEXTE est LA BASE DE TOUT (la demande de l'utilisateur — tapée,
dictée, scannée — mène la génération et sert de requête au référentiel) ; elle est TOUJOURS
affichée et exigée, pour tous les cycles. Ce qui vient du prompt, c'est le reste :

Ce que ces tests PROUVENT :
  1. GET /api/activites renvoie, pour chaque type du couple, `besoins` = la liste des trous
     saisis par le prof dans le prompt de la liaison couple×type ({texte}, {nb}, {sous_type}…),
     LUE en base à l'appel — l'écran s'en sert pour afficher « Nombre de questions » ({nb}).
     Les trous remplis par le serveur ({referentiel}, {niveau}) n'y figurent jamais.
  2. Prompt vide ou accolades cassées → besoins vides, jamais un 500.
  3. /api/generate : la recherche au référentiel reste ancrée sur le TEXTE du prof
     (anti-régression — le texte est la requête, toujours).

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

TOKEN = create_access_token("prof.test@aschool.fr")


def _client_prof():
    c = TestClient(app)
    c.cookies.set("aschool_access", TOKEN)
    return c


def _couple_avec_types(nom, ordre, prompts):
    """Cycle + niveau + référentiel + un type par prompt fourni. Renvoie (niveau_nom, [type_ids])."""
    from backend.core.models_db import (Cycle, Niveau, Referentiel, ActiviteType,
                                        ReferentielActiviteType)
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom=f"BT-{nom}", ordre=ordre)
        db.add(cy); db.flush()
        niv = Niveau(cycle_id=cy.id, nom=f"BT-Niv{nom}", ordre=ordre)
        db.add(niv); db.flush()
        ref = Referentiel(niveau_id=niv.id, matiere_id=None, nom_fixe=f"bt_{nom.lower()}",
                          collection=f"bt_{nom.lower()}", filtres=None, fichier="doc.pdf",
                          texte_epure="TEXTE")
        db.add(ref); db.flush()
        type_ids = []
        for i, (label, prompt) in enumerate(prompts):
            t = ActiviteType(label=label, ordre=i + 1, actif=True, origine="systeme")
            db.add(t); db.flush()
            db.add(ReferentielActiviteType(referentiel_id=ref.id, activite_type_id=t.id,
                                           actif=True, source="admin", prompt=prompt, ordre=i + 1))
            type_ids.append(t.id)
        db.commit()
        return niv.nom, type_ids


# ============ 1. Les besoins sortent du prompt, rien d'autre ============

def test_activites_renvoie_les_besoins_lus_du_prompt():
    niveau, (tid_avec_nb, tid_sans_nb) = _couple_avec_types("Bes", 90, [
        ("BT-Questions", "Niveau {niveau}. Texte : {texte}. Fais {nb} questions ({sous_type}).\n{referentiel}"),
        ("BT-Analyse", "Niveau {niveau}. Texte : {texte}. Analyse d'après le programme :\n{referentiel}"),
    ])
    r = _client_prof().get(f"/api/activites/Peu-Importe?niveau={niveau}")
    assert r.status_code == 200, r.text
    par_id = {t["id"]: t for t in r.json()}
    # Les 3 trous prof, dans l'ordre du prompt — {niveau}/{referentiel} exclus.
    assert par_id[tid_avec_nb]["besoins"] == ["texte", "nb", "sous_type"]
    # Pas de {nb} dans le prompt → l'écran n'affichera pas « Nombre de questions ».
    assert par_id[tid_sans_nb]["besoins"] == ["texte"]


def test_prompt_vide_ou_accolades_cassees_besoins_vides_jamais_500():
    niveau, (tid_vide, tid_casse) = _couple_avec_types("Rob", 91, [
        ("BT-SansPrompt", None),
        ("BT-Casse", "Prompt avec accolade cassée {texte"),
    ])
    r = _client_prof().get(f"/api/activites/X?niveau={niveau}")
    assert r.status_code == 200, r.text
    par_id = {t["id"]: t for t in r.json()}
    assert par_id[tid_vide]["besoins"] == []
    assert par_id[tid_casse]["besoins"] == []


# ============ 2. Génération : le texte du prof reste LA requête au référentiel ============

def test_generate_le_texte_reste_la_requete_rag():
    niveau, (tid,) = _couple_avec_types("Eco", 93, [
        ("BT-Compréhension", "Texte : {texte}\nFais des questions pour {niveau}.\n{referentiel}"),
    ])
    capture = {}

    def _faux_rag(collection, query, filters=None, top_k=None):
        capture["query"] = query
        return [{"text": "Extrait officiel.", "score": 0.9}]

    with patch("backend.contenu.activites.retrieve_pg", side_effect=_faux_rag), \
         patch("backend.contenu.activites.generate_stream", return_value=iter(["OK"])):
        r = _client_prof().post("/api/generate", json={
            "texte": "Le cycle de l'eau dans la nature.", "activite_type_id": tid, "niveau": niveau,
        })
    assert r.status_code == 200, r.text
    assert "event: done" in r.text and '"text": "OK"' in r.text
    assert capture["query"] == "Le cycle de l'eau dans la nature."
