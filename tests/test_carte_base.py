r"""La carte de la base : une page rendue par le serveur, et un classement qui suit le schema.

CE QUE CES TESTS PROUVENT, et pourquoi ils existent.

1. LA ROUTE. `POST /admin/base/carte` lancait `outils_bdd/carte_base/carte.py` en
   sous-processus, et ce script se termine par `cmd /c start msedge`. Le backend tourne dans un
   conteneur Linux : la route ne pouvait PAR CONSTRUCTION jamais aboutir, et l'ecran offrait
   quand meme le bouton. Elle est desormais un GET qui CONSTRUIT la page et la renvoie —
   HTML autonome, moteur de dessin embarque, donc valable depuis le poste comme depuis le VPS.

2. LE CLASSEMENT. `DOMAINS` datait : il nommait 7 tables disparues et ignorait 15 tables
   vivantes — activites, seances, sequences comprises. Elles tombaient dans « systeme » par
   defaut. La carte se dessinait quand meme : c'est exactement le genre de panne qui ne se
   signale pas. Ce test compare `DOMAINS` a la base REELLE, dans les deux sens.

Lancer : docker exec a-school-backend-1 python -m pytest tests/test_carte_base.py -q
"""
import importlib.util
import os
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from sqlalchemy import text

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient

SCRIPT = Path(__file__).resolve().parents[1] / "outils_bdd" / "carte_base" / "carte.py"


def _outil():
    """Charge carte.py par son chemin — `outils_bdd` n'est pas un paquet, comme dans la route."""
    spec = importlib.util.spec_from_file_location("carte_base_outil_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tables_reelles():
    with dbmod.engine.connect() as c:
        return {r[0] for r in c.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))}


def _tables_classees(module):
    classees = set()
    for _, _, _, _, noms in module.DOMAINS.values():
        classees |= set(noms)
    return classees


def test_le_script_de_la_carte_est_la_ou_la_route_le_cherche():
    """La route resout ce chemin exact : s'il bouge, elle rend un 500 et personne ne le sait."""
    assert SCRIPT.exists(), f"Script de la carte introuvable : {SCRIPT}"


def test_aucune_table_vivante_ne_tombe_dans_systeme_par_defaut():
    module = _outil()
    manquantes = sorted(_tables_reelles() - _tables_classees(module))
    assert not manquantes, (
        "Ces tables existent en base et ne sont nommees dans AUCUN domaine de carte.py — "
        "elles seront dessinees en « systeme », quel que soit leur vrai sujet :\n  - "
        + "\n  - ".join(manquantes)
        + "\n\nRanger chaque nom dans le domaine voulu, au dictionnaire DOMAINS."
    )


def test_aucun_domaine_ne_nomme_une_table_disparue():
    module = _outil()
    # `alembic_version` est absente de la base de TEST — elle est batie par create_all, pas par
    # la chaine des migrations. Elle existe bien en dev et en prod : ce n'est pas un fantome.
    fantomes = sorted(_tables_classees(module) - _tables_reelles() - {"alembic_version"})
    assert not fantomes, (
        "carte.py classe des tables qui n'existent plus en base :\n  - "
        + "\n  - ".join(fantomes)
        + "\n\nLes retirer de DOMAINS : un classement qui nomme des morts ne prouve rien."
    )


def test_la_route_rend_la_carte_elle_meme():
    """La preuve du changement : une page HTML, pas un « ok » sur un processus parti mourir."""
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    r = c.get("/api/admin/base/carte")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/html")
    corps = r.text
    assert "<html" in corps.lower()
    # La carte est AUTONOME : le moteur de dessin est dans la page, aucun appel reseau. C'est ce
    # qui lui permet de s'ouvrir depuis n'importe ou — y compris un VPS sans acces au CDN.
    assert 'src="http' not in corps and "src='http" not in corps, (
        "La carte va chercher un fichier dehors : elle ne s'affichera pas hors ligne."
    )
    assert "mermaid" in corps.lower(), "Le moteur de dessin n'est pas dans la page."
    # Elle est dessinee sur la base REELLE : une table du schema doit y figurer.
    assert "users" in corps


def test_la_carte_exige_le_cookie_admin():
    assert TestClient(app).get("/api/admin/base/carte").status_code == 401
