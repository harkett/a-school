"""Filet de test — les 5 endpoints cœur d'aSchool (Phase 1 du plan de reprise).

Lance avec :  pytest   (suite pytest — convention unique du projet)

Couverture (choix (b) : happy path + cas d'erreur connus) :
  - generate, generate-sequence, optimize-sequence, detect-ambiguites, analyser-consigne
  - happy path : 200 + sortie cohérente (Groq MOCKÉ — aucun appel réseau)
  - auth      : 401 sans cookie / token invalide
  - validation: 400 (entrée vide / invalide) et 422 (champ requis manquant)
  - résilience Groq : fallback 429/413/503 (testé au niveau de call_groq) + propagation 502

Garde-fous : BDD SQLite EN MÉMOIRE (la vraie data/aschool.db n'est jamais ouverte),
user de test fictif, JWT signé via create_access_token (secret jamais exposé).
Verrouille l'existant contre une régression — n'introduit aucun comportement nouveau.
"""
import os
import sys
from unittest.mock import patch

import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

# --- Rediriger la BDD vers une SQLite EN MÉMOIRE avant d'importer l'app ---
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.database as dbmod
_mem = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
dbmod.engine = _mem
dbmod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_mem)

from backend import models_db
models_db.Base.metadata.create_all(bind=_mem)

from backend.main import app
from backend.auth import create_access_token
from backend.groq_client import call_groq
from fastapi import HTTPException
from fastapi.testclient import TestClient

assert "memory" in str(dbmod.engine.url), "SECURITE: engine non redirige vers la memoire"

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


class FakeResp:
    def __init__(self, status, payload=None, text=""):
        self.status_code = status
        self.ok = 200 <= status < 300
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def _groq_content(content):
    """Réponse HTTP Groq OK avec le contenu donné (format chat completions)."""
    return FakeResp(200, {"choices": [{"message": {"content": content}}]})


# ===================== HAPPY PATH (200 + sortie cohérente) =====================

def test_generate_happy():
    with patch("backend.routers.generate.generate", return_value="1. Question ? 2. Autre ?"):
        r = authed().post("/api/generate", json={
            "texte": "La photosynthèse.", "activite_key": "comprehension",
            "niveau": "3e", "sous_type": "simples", "nb": 3, "avec_correction": False})
    assert r.status_code == 200, r.text
    assert r.json()["resultat"].startswith("1. Question")


def test_generate_sequence_happy():
    with patch("backend.routers.sequence.call_groq", return_value=SEQ_MD), \
         patch("backend.routers.sequence.AI_PROVIDER", "groq"):
        r = authed().post("/api/generate-sequence", json={
            "theme": "Photosynthèse", "matiere": "SVT", "niveau": "3e",
            "duree": 55, "mode": "standard", "description_classe": ""})
    assert r.status_code == 200, r.text
    assert "Phase 1" in r.json()["resultat"]


def test_optimize_happy():
    with patch("backend.routers.optimiseur.call_groq", return_value=OPT_JSON), \
         patch("backend.routers.optimiseur.AI_PROVIDER", "groq"):
        r = authed().post("/api/optimize-sequence", json={
            "sequence": "# Séance\n## Phase 1 (55 min)", "matiere": "SVT", "niveau": "3e"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["score"] and len(d["problemes"]) == 1


def test_ambiguites_happy():
    with patch("backend.routers.ambiguites.call_groq", return_value=AMB_JSON), \
         patch("backend.routers.ambiguites.AI_PROVIDER", "groq"):
        r = authed().post("/api/detect-ambiguites", json={
            "texte": "Analysez le document.", "matiere": "SVT", "niveau": "3e"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["verdict"] and len(d["ambiguites"]) == 1


def test_consigne_happy():
    with patch("backend.routers.consigne.call_groq", return_value=CON_JSON), \
         patch("backend.routers.consigne.AI_PROVIDER", "groq"):
        r = authed().post("/api/analyser-consigne", json={
            "consigne": "Expliquez la photosynthèse.", "matiere": "SVT", "niveau": "3e"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["version_optimisee"] and len(d["analyses"]) == 1


# ===================== AUTH 401 (sans cookie) =====================

def test_401_sans_cookie():
    c = noauth()
    cases = [
        ("/api/generate", {"texte": "x", "activite_key": "comprehension", "niveau": "3e"}),
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


def test_422_champ_requis_manquant():
    # Pydantic rejette un payload incomplet (activite_key manquant) avant tout traitement.
    r = authed().post("/api/generate", json={"texte": "x", "niveau": "3e"})
    assert r.status_code == 422, r.text


# ===================== RÉSILIENCE GROQ (fallback + propagation) =====================

def test_call_groq_fallback_429_puis_succes():
    """429 sur le 1er modèle -> bascule sur le suivant -> succès."""
    seq = [FakeResp(429, text="rate limit"), _groq_content("OK_FALLBACK")]
    with patch("backend.groq_client.requests.post", side_effect=seq):
        out = call_groq({"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "x"}]})
    assert out == "OK_FALLBACK"


def test_call_groq_413_et_503_declenchent_fallback():
    """413 et 503 sont des statuts de fallback (pas seulement 429)."""
    for status in (413, 503):
        seq = [FakeResp(status, text="big/down"), _groq_content("OK")]
        with patch("backend.groq_client.requests.post", side_effect=seq):
            out = call_groq({"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "x"}]})
        assert out == "OK", f"status {status} aurait dû déclencher le fallback"


def test_call_groq_erreur_non_fallback_leve_502():
    """Un statut hors fallback (400) -> HTTPException 502, pas de boucle infinie."""
    with patch("backend.groq_client.requests.post", return_value=FakeResp(400, text="bad request")):
        try:
            call_groq({"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "x"}]})
            assert False, "aurait dû lever HTTPException"
        except HTTPException as e:
            assert e.status_code == 502


def test_call_groq_tous_modeles_satures_leve_429():
    """Tous les modèles renvoient 429 -> HTTPException 429 (épuisement propre)."""
    with patch("backend.groq_client.requests.post", return_value=FakeResp(429, text="rate limit")):
        try:
            call_groq({"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "x"}]})
            assert False, "aurait dû lever HTTPException"
        except HTTPException as e:
            assert e.status_code == 429


def test_endpoint_propage_groq_down_502():
    """Si Groq est down (call_groq lève 502), l'endpoint propage le 502."""
    with patch("backend.routers.optimiseur.call_groq", side_effect=HTTPException(502, "Groq down")), \
         patch("backend.routers.optimiseur.AI_PROVIDER", "groq"):
        r = authed().post("/api/optimize-sequence", json={
            "sequence": "# Séance\n## Phase 1 (55 min)", "matiere": "SVT", "niveau": "3e"})
    assert r.status_code == 502, r.text


# ===================== P3.4 — /api/generate : durcissement des erreurs =====================
# /api/generate ne passe PAS par call_groq (générateur src.generator). Son except fourre-tout
# renvoyait 500 pour tout. P3.4 distingue : clé inconnue -> 400, Groq down -> 502.

def test_generate_activite_inconnue_400():
    """Clé d'activité absente du catalogue -> 400 (faute client), pas 500.
    Échoue dans build_prompt avant tout appel Groq : aucun mock nécessaire."""
    r = authed().post("/api/generate", json={
        "texte": "La photosynthèse.", "activite_key": "nexiste_pas",
        "niveau": "3e", "sous_type": "simples", "nb": 3, "avec_correction": False})
    assert r.status_code == 400, r.text


def test_generate_groq_down_502():
    """Groq répond non-ok (generate lève RuntimeError) -> 502 (panne amont), pas 500."""
    with patch("backend.routers.generate.generate", side_effect=RuntimeError("Erreur 503: service unavailable")):
        r = authed().post("/api/generate", json={
            "texte": "La photosynthèse.", "activite_key": "comprehension",
            "niveau": "3e", "sous_type": "simples", "nb": 3, "avec_correction": False})
    assert r.status_code == 502, r.text


def test_generate_reseau_down_502():
    """Réseau Groq injoignable (requests.ConnectionError) -> 502, pas 500."""
    with patch("backend.routers.generate.generate",
               side_effect=requests.exceptions.ConnectionError("connexion refusée")):
        r = authed().post("/api/generate", json={
            "texte": "La photosynthèse.", "activite_key": "comprehension",
            "niveau": "3e", "sous_type": "simples", "nb": 3, "avec_correction": False})
    assert r.status_code == 502, r.text


# ===================== P3.6 — /api/generate : param requis manquant -> 400 =====================
# "comprehension" exige {nb} ET {sous_type} dans son template. Le frontend supprime ces champs
# s'ils sont vides ; sans garde, .format() lève KeyError -> 500. P3.6 : faute client -> 400.
# Échoue dans build_prompt avant tout appel Groq : aucun mock nécessaire.

def test_generate_nb_manquant_400():
    """Activité exigeant {nb} appelée sans nb -> 400 (faute client), pas 500."""
    r = authed().post("/api/generate", json={
        "texte": "La photosynthèse.", "activite_key": "comprehension",
        "niveau": "3e", "sous_type": "simples", "avec_correction": False})
    assert r.status_code == 400, r.text


def test_generate_sous_type_manquant_400():
    """Activité exigeant {sous_type} appelée sans sous_type -> 400 (faute client), pas 500."""
    r = authed().post("/api/generate", json={
        "texte": "La photosynthèse.", "activite_key": "comprehension",
        "niveau": "3e", "nb": 3, "avec_correction": False})
    assert r.status_code == 400, r.text


