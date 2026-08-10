r"""Preuve de raccordement — toutes les lectures répondent, et aucune ne s'ouvre par erreur.

CE QUI N'ÉTAIT PAS TENU. Trente-six routes `GET` n'avaient aucun test le 10/08/2026 : vingt-sept
côté administration (journaux, métriques, statistiques, état du référentiel) et neuf publiques ou
côté prof. Une lecture qui tombe est moins grave qu'une écriture qui dérape — mais une lecture qui
s'OUVRE sans cookie livre le journal des connexions, la liste des comptes et les métriques du
serveur à qui passe.

CE QUE LE TEST PROUVE, en balayage complet :
  1. chacune des 27 routes d'administration répond **401 sans cookie admin** — c'est le sens qui
     compte : une garde oubliée sur une seule d'entre elles, et le test tombe en la nommant ;
  2. avec le cookie, chacune répond sans planter : 200 (elle rend), ou 422 (il lui manque un
     paramètre d'URL), ou 404 (la ressource demandée n'existe pas dans une base de test vide).
     Un 500 est un échec — c'est exactement ce qu'on cherche : une lecture qui casse sur base
     vide, personne ne le voit avant la première installation neuve ;
  3. les routes publiques répondent sans session (`/api/health`, `/api/version`), et celles qui
     demandent une session la réclament vraiment.

Lancer : docker compose exec backend python -m pytest tests/test_lectures_admin_et_publiques.py -q
"""
import pytest

from conftest import resemer_reglages

from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient

# Les 27 lectures d'administration qui n'étaient tenues par rien.
LECTURES_ADMIN = [
    "/api/admin/audit-log",
    "/api/admin/check",
    "/api/admin/db-size",
    "/api/admin/demos/proposition",
    "/api/admin/failed-attempts",
    "/api/admin/feature-votes",
    "/api/admin/fonctionnalites",
    "/api/admin/ia/catalogue",
    "/api/admin/ia/en-cours",
    "/api/admin/ia/usage",
    "/api/admin/logs",
    "/api/admin/maintenance/stats",
    "/api/admin/mise-en-route/etat",
    "/api/admin/referentiels/depot-pdf",
    "/api/admin/referentiels/epuration",
    "/api/admin/referentiels/etat",
    "/api/admin/referentiels/liste",
    "/api/admin/referentiels/pdf",
    "/api/admin/referentiels/prompts-matieres",
    "/api/admin/server-metrics",
    "/api/admin/sessions",
    "/api/admin/stats/analytique",
    "/api/admin/stats/general",
    "/api/admin/stats/logins",
    "/api/admin/stats/overview",
    "/api/admin/stats/vitalite",
    "/api/admin/users",
]

# Ce qu'une lecture a le droit de répondre sur une base de test vide. 500 n'en fait pas partie.
ACCEPTABLES = (200, 404, 422)


@pytest.mark.parametrize("chemin", LECTURES_ADMIN)
def test_lecture_admin_fermee_sans_cookie(chemin):
    r = TestClient(app).get(chemin)
    assert r.status_code == 401, (
        f"{chemin} rend {r.status_code} sans cookie admin : cette lecture est ouverte."
    )


@pytest.mark.parametrize("chemin", LECTURES_ADMIN)
def test_lecture_admin_repond_sans_planter(chemin):
    """Sur une base vide — l'état d'une installation neuve, celui que personne n'éprouve."""
    resemer_reglages()
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    r = c.get(chemin)
    assert r.status_code in ACCEPTABLES, (
        f"{chemin} rend {r.status_code} sur une base vide.\n{r.text[:400]}"
    )


def test_les_lectures_publiques_repondent_sans_session():
    """Deux seulement, et c'est voulu : l'état du service et sa version. Tout le reste demande
    à savoir qui appelle."""
    c = TestClient(app)
    for chemin in ("/api/health", "/api/version"):
        assert c.get(chemin).status_code == 200, chemin


def test_les_lectures_du_prof_reclament_une_session():
    """Ce qui touche au travail d'un prof ne se lit pas sans savoir qui appelle."""
    c = TestClient(app)
    for chemin in ("/api/contenus/seances/formulaire", "/api/user/cahier/pdf"):
        r = c.get(chemin)
        assert r.status_code in (401, 422), f"{chemin} rend {r.status_code} sans session."


def test_les_catalogues_de_feedback_sont_ouverts_et_c_est_voulu():
    """`statuts` et `limites` sont des CATALOGUES : la liste des états possibles et la taille
    maximale d'une pièce jointe. L'écran en a besoin AVANT d'ouvrir le formulaire, et ils ne
    disent rien de personne. Ce test fige ce choix : s'ils se mettent un jour à rendre des
    données d'utilisateur, il faudra le décider ici."""
    c = TestClient(app)
    for chemin in ("/api/feedback/statuts", "/api/feedback/limites"):
        r = c.get(chemin)
        assert r.status_code == 200, f"{chemin} rend {r.status_code}"


def test_les_routes_de_demonstration_n_existent_pas_sur_une_instance_ordinaire():
    """`/demo/etat` est la seule qui répond partout : le front l'interroge pour savoir s'il doit
    allumer le bandeau, et « non » est une réponse légitime."""
    c = TestClient(app)
    assert c.get("/api/demo/etat").status_code == 200
    assert c.get("/api/demo/etat").json()["mode_demo"] is False
    for chemin in ("/api/demo/aller", "/api/demo/pour-moi"):
        assert c.get(chemin).status_code in (401, 404), chemin
