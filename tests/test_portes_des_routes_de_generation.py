r"""Preuve de raccordement — aucune route de génération ne s'ouvre sans session valide.

CE QUI N'ÉTAIT PAS TENU. Onze routes `POST /api/contenus/**` et sept validations de prompts du
référentiel n'avaient AUCUN test le 10/08/2026. Ce sont les portes les plus coûteuses de
l'application : derrière chacune, un appel à un fournisseur d'IA qui se facture. Une porte
ouverte, ce n'est pas seulement une fuite de données — c'est une facture.

CE QUE CE TEST PROUVE, et SES LIMITES, dites franchement :
  - il prouve LA PORTE : sans cookie de session (ou sans cookie admin pour les routes du
    référentiel), chacune répond 401 et rien ne part chez le fournisseur ;
  - il ne prouve PAS ce que la route génère. Ça, il faudrait appeler un modèle, donc payer.
    Le comportement de génération se vérifie par les suites qui simulent le LLM.

C'est la moitié qui manquait, et c'est celle qui coûte cher quand elle lâche.

Lancer : docker compose exec backend python -m pytest tests/test_portes_des_routes_de_generation.py -q
"""
import pytest

from backend.main import app
from fastapi.testclient import TestClient

# Les routes de génération du prof : session obligatoire (cookie `aschool_access`).
GENERATION_PROF = [
    "/api/contenus/seances/proposer-theme",
    "/api/contenus/seances/proposer-competences",
    "/api/contenus/seances/proposer-materiel",
    "/api/contenus/seances/proposer-contraintes",
    "/api/contenus/seances/proposer-esquisse",
    "/api/contenus/seances/generer",
    "/api/contenus/sequences/proposer-objectif",
    "/api/contenus/sequences/proposer-competences",
    "/api/contenus/sequences/generer-plan",
]

# Les routes du référentiel : cookie admin obligatoire. Elles écrivent ou déclenchent une lecture
# de document, toutes derrière `_require_admin`.
REFERENTIEL_ADMIN = [
    "/api/admin/referentiels/prompt-decoupe/valider",
    "/api/admin/referentiels/prompt-matieres/valider",
    "/api/admin/referentiels/prompt-types/valider",
    "/api/admin/referentiels/prompt-precisions/valider",
    "/api/admin/referentiels/prompt-meta-matieres",
    "/api/admin/referentiels/prompt-meta-types",
    "/api/admin/referentiels/prompt-meta-precisions",
    "/api/admin/referentiels/matieres-proposer",
    "/api/admin/referentiels/decoupe/valider",
    "/api/admin/referentiels/controle-couple",
    "/api/admin/referentiels/preparer-lien",
    "/api/admin/referentiels/types-activite/precisions/generer",
]


@pytest.mark.parametrize("chemin", GENERATION_PROF)
def test_generation_prof_fermee_sans_session(chemin):
    """Sans cookie de session : 401, et aucun appel n'a pu partir — la garde est une dépendance,
    elle s'exécute AVANT le corps de la route."""
    r = TestClient(app).post(chemin, json={})
    assert r.status_code == 401, f"{chemin} rend {r.status_code} au lieu de 401"


@pytest.mark.parametrize("chemin", REFERENTIEL_ADMIN)
def test_referentiel_ferme_sans_cookie_admin(chemin):
    r = TestClient(app).post(chemin, json={})
    assert r.status_code == 401, f"{chemin} rend {r.status_code} au lieu de 401"


def test_une_session_invalide_ne_vaut_pas_une_session():
    """Le cas qui compte vraiment : un cookie PRÉSENT mais faux. Un test qui n'éprouve que
    l'absence de cookie laisserait passer une vérification de signature manquante."""
    c = TestClient(app)
    c.cookies.set("aschool_access", "jeton.completement.invente")
    for chemin in GENERATION_PROF[:3]:
        assert c.post(chemin, json={}).status_code == 401, chemin

    a = TestClient(app)
    a.cookies.set("aschool_admin", "jeton.completement.invente")
    for chemin in REFERENTIEL_ADMIN[:3]:
        assert a.post(chemin, json={}).status_code == 401, chemin
