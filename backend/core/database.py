import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from starlette.requests import Request

# Moteur UNIQUE = PostgreSQL. SQLite est BANNI (cap aSchool : tout en base relationnelle pro).
# DATABASE_URL doit être posée (.env) et pointer PostgreSQL, sinon on REFUSE de démarrer —
# même esprit que le garde-fou Alembic. load_dotenv() est appelé dans main.py AVANT cet import.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
    raise RuntimeError(
        "DATABASE_URL doit pointer PostgreSQL — SQLite est banni dans aSchool. "
        "Renseigne une URL 'postgresql+psycopg://…' dans le .env."
    )

# Le schéma de l'application RÉELLE. Une démonstration a le sien, nommé d'après son
# sous-domaine ; tout le reste — le réel, les scripts, les tâches de fond — vit ici.
SCHEMA_REEL = "public"

# PostgreSQL (psycopg, synchrone) : pool robuste.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def session_pour(schema: str) -> Session:
    """Une session dont TOUTES les requêtes visent `schema`.

    C'EST LA SEULE PORTE. Aucun `SessionLocal()` nu ne doit subsister dans le code : une
    session sans schéma lit `public`, c'est-à-dire le réel — et une démonstration qui lit le
    réel ne lève aucune erreur, elle rend simplement le mauvais contenu.

    `schema_translate_map={None: schema}` s'applique aux 40 modèles ORM, qui ne déclarent
    aucun `schema=` : SQLAlchemy remplace leur schéma nul par celui-ci au moment de compiler
    la requête. Pas de `SET search_path` — il vaut pour la CONNEXION, donc pour tout ce que le
    pool lui repassera ensuite, et une session qui oublierait de le reposer hériterait du
    schéma du visiteur précédent. Ici la traduction est portée par la requête elle-même.

    `engine.execution_options()` rend un moteur léger qui PARTAGE le pool du moteur d'origine :
    aucune connexion supplémentaire n'est ouverte. Le moteur est relu à chaque appel (et non
    figé à l'import) pour que la redirection du conftest vers `aschool_test` reste effective.
    """
    return SessionLocal(bind=engine.execution_options(schema_translate_map={None: schema}))


def schema_de_session(db: Session) -> str:
    """Le schéma que cette session vise — pour le repasser à un appelé qui ouvre la sienne.

    `retrieve_pg` est le cas d'usage : elle ouvre sa propre session et n'a pas la requête HTTP
    sous la main. Lui faire relire le schéma depuis la session de l'endpoint évite d'ajouter un
    `Request` à sept signatures d'appelants."""
    options = db.get_bind().get_execution_options() or {}
    return (options.get("schema_translate_map") or {}).get(None) or SCHEMA_REEL


def get_db(request: Request):
    """La dépendance des 209 endpoints — inchangée pour eux, mais désormais schéma-consciente.

    Le schéma vient de `request.state.schema_db`, posé par `SchemaRequeteMiddleware`. Le repli
    sur le réel couvre le cas où la requête n'est pas passée par lui (un test qui appelle la
    dépendance à la main) : le réel, jamais une démonstration au hasard."""
    db = session_pour(getattr(request.state, "schema_db", SCHEMA_REEL))
    try:
        yield db
    finally:
        db.close()


def get_db_size_mb(schema: str = SCHEMA_REEL) -> float:
    """Taille du SCHÉMA en Mo — plus celle de la base entière.

    `pg_database_size(current_database())` rendait le même chiffre à tout le monde : les cinq
    démonstrations partagent maintenant une seule base — la leur, distincte du réel — et cette
    mesure aurait affiché le total des cinq à chacune. On somme donc les tables du schéma. `pg_total_relation_size` comprend
    déjà les index et le TOAST de chaque table, d'où le filtre sur les seules tables ordinaires
    et vues matérialisées (`r`, `m`) : compter aussi les index les compterait deux fois."""
    with engine.connect() as conn:
        size = conn.execute(
            text(
                "SELECT COALESCE(SUM(pg_total_relation_size(c.oid)), 0) "
                "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = :schema AND c.relkind IN ('r', 'm')"
            ),
            {"schema": schema},
        ).scalar()
    return round((size or 0) / 1024**2, 2)
