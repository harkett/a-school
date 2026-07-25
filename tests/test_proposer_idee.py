"""Bouton « Propose-moi une idée » — POST /api/proposer-idee (même famille que « Tester un exemple »).

Ce que ces tests PROUVENT :
  1. Cas nominal : l'idée est générée à partir des choix du prof (type + précision + niveau),
     la requête RAG est construite sur ces choix, et le texte revient (available:true) —
     destiné à être écrit DANS la zone texte, jamais à la remplacer. La ligne « Objet : »
     ouvrant la réponse IA est détachée et revient dans `objet` (champ Objet de l'écran).
  2. Réponse IA SANS ligne « Objet : » → on ne perd RIEN : objet None, texte entier.
  3. Pas de référentiel pour le niveau → available:false, AUCUN appel LLM (on n'invente rien).
  4. Référentiel présent mais rien d'assez pertinent (seuil `score_min` lu en base) →
     available:false + message honnête, AUCUN appel LLM.
  5. Type d'activité inconnu → 400 humain.

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


def _couple(nom, ordre, avec_ref=True):
    """Cycle + niveau (+ référentiel) + un type actif. Renvoie (niveau_nom, type_id)."""
    from backend.core.models_db import Cycle, Niveau, Referentiel, ActiviteType
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom=f"PI-{nom}", ordre=ordre)
        db.add(cy); db.flush()
        niv = Niveau(cycle_id=cy.id, nom=f"PI-Niv{nom}", ordre=ordre)
        db.add(niv); db.flush()
        if avec_ref:
            db.add(Referentiel(niveau_id=niv.id, matiere_id=None, nom_fixe=f"pi_{nom.lower()}",
                               collection=f"pi_{nom.lower()}", filtres=None, fichier="doc.pdf",
                               texte_epure="TEXTE"))
        t = ActiviteType(label=f"PI-Manuelle-{nom}", ordre=1, actif=True, origine="systeme")
        db.add(t); db.flush()
        db.commit()
        return niv.nom, t.id


def test_proposer_idee_nominal_ancre_sur_type_precision_niveau():
    niveau, tid = _couple("Ok", 95)
    capture = {}

    def _faux_rag(collection, query, filters=None, top_k=None):
        capture["query"] = query
        return [{"text": "Extrait officiel.", "score": 0.9, "page": 3}]

    reponse_ia = ("Objet : Pâte à modeler — exploration libre\n\n"
                  "Explorer la pâte à modeler avec les tout-petits.\n\n"
                  "L'objectif est de développer la motricité fine.")
    with patch("backend.contenu.activites.retrieve_pg", side_effect=_faux_rag), \
         patch("backend.contenu.activites.generate", return_value=reponse_ia) as gen:
        r = _client_prof().post("/api/proposer-idee", json={
            "activite_type_id": tid, "niveau": niveau, "sous_type": "exploration pâte à modeler"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["available"] is True
    # La ligne « Objet : » est détachée pour le champ Objet ; la zone texte reçoit le reste.
    assert data["objet"] == "Pâte à modeler — exploration libre"
    assert data["texte"] == ("Explorer la pâte à modeler avec les tout-petits.\n\n"
                             "L'objectif est de développer la motricité fine.")
    # La recherche est construite sur ce que le prof a VRAIMENT choisi.
    assert capture["query"] == f"Idée d'activité pour le type d'activité PI-Manuelle-Ok (exploration pâte à modeler), niveau {niveau}"
    # Et le prompt du LLM porte le type, la précision, l'extrait ancré et la consigne Objet.
    prompt = gen.call_args.args[0]
    assert "PI-Manuelle-Ok" in prompt and "exploration pâte à modeler" in prompt and "Extrait officiel." in prompt
    assert "Objet :" in prompt


def test_reponse_sans_ligne_objet_ne_perd_rien():
    niveau, tid = _couple("SansObjet", 94)
    with patch("backend.contenu.activites.retrieve_pg",
               return_value=[{"text": "Extrait officiel.", "score": 0.9, "page": 3}]), \
         patch("backend.contenu.activites.generate",
               return_value="Explorer librement les couleurs au doigt."):
        r = _client_prof().post("/api/proposer-idee", json={"activite_type_id": tid, "niveau": niveau})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["available"] is True
    assert data["objet"] is None
    assert data["texte"] == "Explorer librement les couleurs au doigt."


def test_sans_referentiel_available_false_et_zero_appel_llm():
    niveau, tid = _couple("SansRef", 96, avec_ref=False)
    with patch("backend.contenu.activites.retrieve_pg") as rag, \
         patch("backend.contenu.activites.generate") as gen:
        r = _client_prof().post("/api/proposer-idee", json={"activite_type_id": tid, "niveau": niveau})
    assert r.status_code == 200, r.text
    assert r.json()["available"] is False
    rag.assert_not_called()
    gen.assert_not_called()


def test_rien_d_assez_pertinent_message_honnete_et_zero_appel_llm():
    niveau, tid = _couple("Seuil", 97)
    with patch("backend.contenu.activites.retrieve_pg",
               return_value=[{"text": "Hors sujet.", "score": 0.05}]), \
         patch("backend.contenu.activites.generate") as gen:
        r = _client_prof().post("/api/proposer-idee", json={"activite_type_id": tid, "niveau": niveau})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["available"] is False
    assert "pertinent" in data["message"]
    gen.assert_not_called()


def test_type_inconnu_400_humain():
    niveau, _ = _couple("Inconnu", 98)
    r = _client_prof().post("/api/proposer-idee", json={"activite_type_id": 999999, "niveau": niveau})
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Type d'activité inconnu."
