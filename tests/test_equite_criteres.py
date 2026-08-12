"""Preuve — l'analyse d'équité ne cherche QUE les biais cochés, et seulement ceux du SUJET.

Le jumeau de test_ambiguites_criteres.py, plus les deux garde-fous propres à cet écran : le
barème facultatif, et le refus des biais du correcteur.

Ce que ces tests PROUVENT (base aschool_test via conftest.py, LLM MOQUÉ — aucun appel réel) :
  1. Les biais viennent du CATALOGUE `equite_criteres` : l'écran reçoit exactement les lignes
     sur lesquelles le serveur validera, et désactiver une ligne la retire des deux.
  2. Le serveur ne fait pas confiance à l'écran : rien de coché ou un code inconnu → 400 humain
     et AUCUN appel LLM.
  3. Seuls les libellés cochés partent au modèle, chacun avec SA vérification.
  4. LE BARÈME EST FACULTATIF, et son absence est DITE au modèle — sans quoi il inventerait une
     répartition de points pour avoir quelque chose à juger.
  5. LE PROMPT INTERDIT LES BIAIS DU CORRECTEUR. C'est la promesse centrale de l'écran : l'effet
     de halo ne se voit pas dans un énoncé collé, l'outil ne doit pas prétendre le trouver.
  6. Un biais rendu hors liste est ÉCARTÉ — pas rangé dans un « Autre », cette liste n'en a pas.

Lancer : docker compose exec backend python -m pytest tests/test_equite_criteres.py -q
"""
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import backend.core.database as dbmod
from backend.core.models_db import EquiteCritere
from backend.main import app
from backend.securite.comptes import create_access_token

from _profil import user_couple

EMAIL = "prof.equite@aschool.fr"
RIEN_TROUVE = '{"biais": [], "verdict": "RAS"}'
SUJET = "Racontez vos dernières vacances en 20 lignes. (10 points)"


def _client():
    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token(EMAIL))
    return c


def _prof():
    with dbmod.SessionLocal() as db:
        db.add(user_couple(db, email=EMAIL, password_hash="x", is_verified=True,
                           subject="Français", niveau="4e"))
        db.commit()


def _analyser(corps, reponse_llm=RIEN_TROUVE):
    """Un POST complet avec le LLM moqué. Renvoie (réponse HTTP, mock generate)."""
    with patch("backend.analyse.equite.generate", return_value=reponse_llm) as gen, \
         patch("backend.analyse.equite.get_cle_texte", return_value="cle-test"):
        return _client().post("/api/detect-equite", json=corps), gen


def _prompt(gen):
    return gen.call_args.args[0]


# ── Le catalogue : une seule vérité pour l'écran et pour le serveur ──────────────────────

def test_l_ecran_recoit_les_neuf_biais_du_catalogue():
    _prof()
    r = _client().get("/api/equite/criteres")
    assert r.status_code == 200, r.text
    codes = [c["code"] for c in r.json()]
    assert len(codes) == 9
    assert codes[0] == "savoir_non_enseigne" and codes[-1] == "temps_insuffisant"
    # Chaque biais porte sa description : c'est elle que le prof lit au survol de la case.
    assert all(c["description"].strip() for c in r.json())


def test_pas_de_ligne_autre_contrairement_aux_ambiguites():
    """L'équité se juge sur des motifs connus. Un biais écrit à la main par le prof ne serait
    vérifiable par rien — la case n'existe donc pas."""
    _prof()
    assert "autre" not in [c["code"] for c in _client().get("/api/equite/criteres").json()]


def test_desactiver_une_ligne_la_retire_de_l_ecran_et_des_valeurs_acceptees():
    _prof()
    with dbmod.SessionLocal() as db:
        db.query(EquiteCritere).filter(EquiteCritere.code == "stereotype").update({"actif": False})
        db.commit()

    assert "stereotype" not in [c["code"] for c in _client().get("/api/equite/criteres").json()]
    r, gen = _analyser({"texte": SUJET, "criteres": ["stereotype"]})
    assert r.status_code == 400, r.text
    gen.assert_not_called()


def test_catalogue_vide_erreur_dite_jamais_un_repli_silencieux():
    """Règle maison : une base vide se dit. Sans catalogue, l'écran n'invente pas neuf cases."""
    _prof()
    with dbmod.SessionLocal() as db:
        db.query(EquiteCritere).delete()
        db.commit()
    r = _client().get("/api/equite/criteres")
    assert r.status_code == 500
    assert "migration" in r.json()["detail"].lower()


# ── Le serveur ne fait pas confiance à l'écran ───────────────────────────────────────────

@pytest.mark.parametrize("corps", [
    {"texte": SUJET},                                     # rien de coché
    {"texte": SUJET, "criteres": []},
    {"texte": SUJET, "criteres": ["biais_invente_xxx"]},   # code inventé
    {"texte": "   ", "criteres": ["stereotype"]},          # évaluation vide
])
def test_requete_incomplete_400_humain_et_zero_appel_llm(corps):
    _prof()
    r, gen = _analyser(corps)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] and not r.json()["detail"].startswith("Traceback")
    gen.assert_not_called()


# ── Ce qui part vraiment au modèle ───────────────────────────────────────────────────────

def test_seuls_les_biais_coches_partent_au_modele_avec_leur_verification():
    _prof()
    r, gen = _analyser({"texte": SUJET, "criteres": ["culture_et_milieu", "materiel_suppose"]})
    assert r.status_code == 200, r.text
    prompt = _prompt(gen)
    assert "Culture et milieu" in prompt and "Matériel supposé" in prompt
    assert "Stéréotype" not in prompt and "Double peine" not in prompt
    # La vérification accompagne le libellé : sans elle, le modèle choisit où chercher.
    assert "Vérification :" in prompt


def test_sans_bareme_l_absence_est_dite_au_modele():
    """Un repère vide sous « Barème fourni » ferait inventer une répartition de points."""
    _prof()
    r, gen = _analyser({"texte": SUJET, "criteres": ["bareme_absent_ou_decale"]})
    assert r.status_code == 200, r.text
    assert "aucun barème fourni" in _prompt(gen)


def test_le_bareme_colle_arrive_dans_le_prompt():
    _prof()
    r, gen = _analyser({"texte": SUJET, "criteres": ["bareme_absent_ou_decale"],
                        "bareme": "Orthographe 5 pts, contenu 5 pts"})
    assert r.status_code == 200, r.text
    prompt = _prompt(gen)
    assert "Orthographe 5 pts" in prompt and "aucun barème fourni" not in prompt


def test_le_prompt_interdit_les_biais_du_correcteur():
    """LA promesse de l'écran. Ces biais sont les mieux documentés de la recherche française et
    le modèle les connaît par cœur : sans interdiction écrite, il en parle — et l'outil promet
    alors ce qu'un énoncé collé ne peut pas montrer."""
    _prof()
    r, gen = _analyser({"texte": SUJET, "criteres": ["stereotype"]})
    assert r.status_code == 200, r.text
    prompt = _prompt(gen)
    assert "NE JAMAIS parler des biais du correcteur" in prompt
    assert "effet de halo" in prompt


# ── Le biais rendu est recollé sur ce qui a été coché ────────────────────────────────────

def _carte(critere_rendu):
    return json.dumps({"verdict": "RAS", "biais": [
        {"extrait": "vacances", "critere": critere_rendu,
         "consequence": "pénalise ceux qui ne partent pas", "correction": "changer le contexte"},
    ]})


def test_un_biais_invente_par_le_modele_est_ecarte():
    """Pas de repli « Autre » comme chez les ambiguïtés : cette liste n'en a pas. Une carte dont
    on ne sait pas de quel biais elle parle ne s'affiche pas."""
    _prof()
    r, _ = _analyser({"texte": SUJET, "criteres": ["culture_et_milieu"]},
                     reponse_llm=_carte("Manque d'inclusivité"))
    assert r.status_code == 200, r.text
    assert r.json()["biais"] == []


def test_un_biais_non_coche_ne_passe_pas_pour_un_biais_coche():
    _prof()
    r, _ = _analyser({"texte": SUJET, "criteres": ["culture_et_milieu"]},
                     reponse_llm=_carte("Stéréotype"))
    assert r.json()["biais"] == []


def test_un_biais_coche_est_rendu_tel_quel_meme_avec_une_casse_differente():
    _prof()
    r, _ = _analyser({"texte": SUJET, "criteres": ["culture_et_milieu"]},
                     reponse_llm=_carte("CULTURE ET MILIEU"))
    assert r.json()["biais"][0]["critere"] == "Culture et milieu"


def test_un_biais_sans_extrait_reste_affiche():
    """« Temps insuffisant » et « barème absent » portent sur l'ensemble de l'évaluation : ils
    n'ont aucun passage à citer, et la carte ne doit pas disparaître pour autant."""
    _prof()
    sans_extrait = json.dumps({"verdict": "RAS", "biais": [
        {"critere": "Temps insuffisant", "consequence": "pénalise les élèves lents",
         "correction": "allonger la durée"},
    ]})
    r, _ = _analyser({"texte": SUJET, "criteres": ["temps_insuffisant"]}, reponse_llm=sans_extrait)
    assert r.status_code == 200, r.text
    assert r.json()["biais"][0]["extrait"] == ""
