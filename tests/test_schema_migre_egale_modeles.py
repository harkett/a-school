"""Garde-fou — le schema que produisent les MIGRATIONS est celui que declarent les MODELES.

CE QUE CE FICHIER EMPECHE. Le 02/08/2026, `alembic check` sortait en FAILED sur 9 operations
reparties sur 3 tables : des index renommes a moitie (une table renommee le 16/07 dont les
index avaient garde l'ancien nom) et un index redondant sur cahiers_prof. Rien n'etait casse
— memes colonnes, memes garanties — mais tant que la comparaison echoue, elle ne peut plus
servir a rien : la derive SUIVANTE se serait cachee derriere celle-la, et on aurait refait ce
point six mois plus tard avec neuf ecarts de plus par-dessus.

POURQUOI CE TEST ET PAS LA SUITE ORDINAIRE. Le schema de test est monte par
`Base.metadata.create_all` (conftest.py), pas par les migrations : la base de test et la base
reelle n'ont donc pas forcement les memes index. Et monter le schema de test PAR les
migrations ne reparerait rien — aucun test n'assertit sur un index, aucun ne le pourrait
utilement : un index est invisible a la correction, il ne change que la vitesse. La suite
passerait a l'identique dans les deux cas. C'est `alembic check` qui voit la difference, parce
que c'est exactement son travail : comparer les deux schemas. Il lui faut juste une base
montee par migrations pour s'y appuyer — c'est ce que ce fichier lui fabrique.

CE QU'IL FAIT. Une base JETABLE (`aschool_verif_schema`, ni la dev ni la base de test), les 84
migrations rejouees dessus, puis `alembic check` par-dessus. Environ 6 secondes. La base est
detruite dans tous les cas, y compris si le test echoue.

CE QUI LE FAIT ECHOUER. Toute divergence entre les migrations et models_db.py : une colonne
ajoutee au modele sans migration, un index renomme d'un cote seulement, un type change. Le
message d'alembic nomme la table et l'operation manquante.

QUAND IL ECHOUE, LA REPARATION est presque toujours : `alembic revision --autogenerate -m
"..."`, puis on RELIT le fichier genere avant de le garder (l'autogeneration propose parfois
des suppressions qu'on ne veut pas).

Lancer : docker compose exec backend python -m pytest tests/test_schema_migre_egale_modeles.py -q
"""
import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

# conftest.py a charge le .env (override=True) et verifie que cette URL vise bien aschool_test.
TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]

# Racine du depot : alembic.ini y vit, et alembic doit tourner depuis la.
RACINE = Path(__file__).resolve().parents[1]

# Base jetable. Le nom porte « verif » exprès : il ne peut se confondre avec aucune base
# vivante, et le garde-fou ci-dessous refuse de tourner s'il derivait un jour.
BASE_JETABLE = "aschool_verif_schema"


def _url_vers(nom_base: str) -> str:
    """Meme serveur, memes identifiants que la base de test — une autre base.

    `render_as_string(hide_password=False)` et non `str(url)` : `str()` d'une URL SQLAlchemy
    REMPLACE le mot de passe par `***`. L'URL obtenue se lit tres bien et echoue a la
    connexion avec « password authentication failed » — un quart d'heure perdu le 02/08."""
    return make_url(TEST_DATABASE_URL).set(database=nom_base).render_as_string(hide_password=False)


def _sql_admin(*ordres: str) -> None:
    """CREATE/DROP DATABASE exigent l'autocommit et une connexion a une AUTRE base."""
    moteur = create_engine(_url_vers("postgres"), isolation_level="AUTOCOMMIT")
    try:
        with moteur.connect() as c:
            for o in ordres:
                c.execute(text(o))
    finally:
        moteur.dispose()


@pytest.fixture
def base_jetable():
    """Une base neuve, vide, detruite ensuite quoi qu'il arrive.

    GARDE-FOU : on n'accepte de DROP que le nom fige ci-dessus. Sans ce verrou, une faute de
    frappe dans BASE_JETABLE pourrait viser une base vivante — le meme genre de risque que
    conftest.py couvre pour le TRUNCATE, avec la meme reponse : on refuse au lieu de deviner.
    """
    assert BASE_JETABLE not in ("aschool_dev", "aschool_test", "postgres"), \
        f"SECURITE : la base jetable vise {BASE_JETABLE!r} — refus de la detruire."

    # WITH (FORCE) : une connexion oubliee par une execution precedente empecherait le DROP.
    _sql_admin(f'DROP DATABASE IF EXISTS "{BASE_JETABLE}" WITH (FORCE)',
               f'CREATE DATABASE "{BASE_JETABLE}"')
    # pgvector : la premiere migration qui pose une colonne Vector echoue sans l'extension.
    moteur = create_engine(_url_vers(BASE_JETABLE), isolation_level="AUTOCOMMIT")
    try:
        with moteur.connect() as c:
            c.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    finally:
        moteur.dispose()

    try:
        yield _url_vers(BASE_JETABLE)
    finally:
        _sql_admin(f'DROP DATABASE IF EXISTS "{BASE_JETABLE}" WITH (FORCE)')


def _alembic(commande: list[str], url: str) -> subprocess.CompletedProcess:
    """alembic/env.py lit DATABASE_URL de l'environnement SANS override du .env : la valeur
    posee ici l'emporte donc, et vise la base jetable — jamais la dev, jamais la base de test."""
    env = {**os.environ, "DATABASE_URL": url}
    return subprocess.run(["alembic", *commande], cwd=RACINE, env=env,
                          capture_output=True, text=True)


def test_les_migrations_produisent_exactement_le_schema_des_modeles(base_jetable):
    montee = _alembic(["upgrade", "head"], base_jetable)
    assert montee.returncode == 0, (
        "les migrations ne se rejouent plus sur une base neuve — le deploiement echouerait "
        f"au meme endroit :\n{montee.stderr[-3000:]}"
    )

    verif = _alembic(["check"], base_jetable)
    assert verif.returncode == 0, (
        "le schema MIGRE et les MODELES ont diverge : `alembic check` propose des operations "
        "qu'aucune migration ne porte. Autrement dit, la base reelle n'est pas ce que "
        "models_db.py declare, et plus rien ne surveillera la derive suivante.\n"
        "Reparation : `alembic revision --autogenerate -m \"...\"`, PUIS relire le fichier "
        f"genere avant de le garder.\n\n{verif.stdout[-3000:]}{verif.stderr[-3000:]}"
    )


def test_une_seule_tete_alembic():
    """Deux tetes = deux migrations qui se declarent filles du meme parent. `upgrade head`
    devient ambigu et le deploiement s'arrete. C'est arrive le 02/08 (un identifiant de
    revision choisi deja pris) : le cas se detecte en une seconde, il n'a pas a se decouvrir
    en production.

    Pas de base jetable ici : `alembic heads` lit les FICHIERS de migration, il ne se connecte
    a rien. On lui passe quand meme une URL, parce qu'env.py refuse de demarrer sans."""
    r = _alembic(["heads"], _url_vers(BASE_JETABLE))
    assert r.returncode == 0, r.stderr[-2000:]
    tetes = [l for l in r.stdout.splitlines() if "(head)" in l]
    assert len(tetes) == 1, f"{len(tetes)} tetes alembic au lieu d'une :\n" + "\n".join(tetes)
