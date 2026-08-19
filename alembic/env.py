"""Alembic — environnement de migrations aSchool.

Câblé sur l'app : l'URL vient de DATABASE_URL (.env, même source que l'app), jamais
en dur dans alembic.ini ; les métadonnées cibles = le modèle ORM (backend.core.models_db).
Garde-fou : refuse de tourner si le moteur n'est pas PostgreSQL (SQLite jamais touché)."""
import os
import re
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# env.py vit dans alembic/ : racine projet sur le path pour pouvoir importer backend.*
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

# .env pour DATABASE_URL. SANS override : un DATABASE_URL fourni dans le shell l'emporte
# (utile pour viser une base scratch vide lors de la génération de la baseline).
load_dotenv(dotenv_path=_ROOT / ".env")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# URL pilotée par le .env (jamais en dur dans alembic.ini).
_db_url = os.getenv("DATABASE_URL")
if not _db_url:
    raise SystemExit("DATABASE_URL absente du .env — Alembic ne sait pas quelle base viser.")
# GARDE-FOU : jamais autre chose que PostgreSQL (SQLite, le filet, n'est jamais touché).
if not _db_url.startswith("postgresql"):
    raise SystemExit(f"ARRET : DATABASE_URL = '{_db_url.split('://')[0]}://…', Alembic exige postgresql.")
config.set_main_option("sqlalchemy.url", _db_url)

# Métadonnées cibles = le modèle ORM. Importer models_db enregistre les 22 tables sur Base.metadata.
from backend.core.database import Base
from backend.core import models_db  # noqa: F401  (effet de bord : enregistre les tables)

target_metadata = Base.metadata

# --- Un schéma par démonstration ------------------------------------------------------------
# `alembic -x schema=crsa upgrade head` migre le schéma `crsa`, et lui seul. Sans `-x schema`,
# STRICTEMENT RIEN NE CHANGE : le réel se migre comme avant, dans `public`.
#
# POURQUOI UNE `alembic_version` PAR SCHÉMA. Les démonstrations partagent une base. Une
# seule table de version, et le premier schéma migré ferait croire que tous le sont — les
# autres resteraient en arrière sans que rien ne le dise. Elles ne sont d'ailleurs
# DÉJÀ PAS au même niveau : trois en b7e1f4a9c3d2, deux en a4d8f2c6e1b9 au moment de la bascule.
#
# `schema_translate_map` fait viser le bon schéma aux migrations, qui nomment leurs tables sans
# préfixe — exactement comme `session_pour()` le fait pour l'application. Attention : il ne
# traduit PAS le SQL écrit à la main dans un `op.execute()`. Une migration qui en contient doit
# qualifier ses tables elle-même.
_schema = context.get_x_argument(as_dictionary=True).get("schema")
if _schema and not re.fullmatch(r"[a-z0-9_]{1,63}", _schema):
    raise SystemExit(f"ARRET : '{_schema}' n'est pas un nom de schéma acceptable.")


def run_migrations_offline() -> None:
    """Mode 'offline' : génère le SQL sans connexion."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Mode 'online' : connexion réelle à la base."""
    # LE `search_path` SE POSE À L'OUVERTURE DE LA CONNEXION, jamais par un `SET` ensuite.
    # Mesuré le 10/08/2026 : un `connection.exec_driver_sql("SET search_path …")` déclenche
    # l'ouverture automatique d'une transaction ; Alembic voit alors `in_transaction()` vrai,
    # en conclut que l'appelant gère lui-même la validation, et ne commite plus. Résultat, il
    # ANNONÇAIT « Running upgrade … » pour les neuf migrations, rendait 0, et la base n'avait
    # pas bougé d'un octet — `few_shot_milestones` était toujours là. Un échec qui se présente
    # comme un succès : la pire forme. Passé en paramètre de connexion, le chemin est en place
    # avant la première requête et Alembic garde la main sur sa transaction.
    kwargs = {"poolclass": pool.NullPool}
    if _schema:
        kwargs["connect_args"] = {"options": f"-c search_path={_schema},public"}
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        **kwargs,
    )
    with connectable.connect() as connection:
        if _schema:
            # Le translate_map et le `search_path` ci-dessus ne font PAS double emploi. Le
            # premier ne traduit que ce qui passe par les objets SQLAlchemy ; or SEPT des
            # migrations restantes écrivent leur SQL à la main — « DELETE FROM settings »,
            # « UPDATE fonctionnalites » — et ces noms-là ne sont pas traduits. Sans le chemin,
            # elles s'exécuteraient dans le `public` vide de la base des démonstrations : les
            # DELETE ne trouveraient rien, l'estampille monterait quand même, et les
            # schémas se diraient à jour sans l'être.
            connection = connection.execution_options(schema_translate_map={None: _schema})
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_schemas=bool(_schema),
            version_table_schema=_schema,   # None hors démonstration = comportement d'avant
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
