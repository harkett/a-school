"""Plomberie + garde-fous des tests aSchool — PostgreSQL UNIQUEMENT, JAMAIS SQLite.

Tous les tests tournent sur la base de test dédiée `aschool_test` (instance 5433),
jamais sur SQLite, jamais sur la base dev `aschool`. Trois verrous :

  1. BARRIÈRE PHYSIQUE — `create_engine("sqlite...")` lève RuntimeError immédiatement.
     Le conftest étant importé AVANT la collecte des tests, tout test qui réintroduirait
     SQLite plante à la collecte au lieu de passer « en douce ».
  2. GARDE-FOU POSITIF — le moteur de test DOIT être PostgreSQL ET viser `aschool_test`,
     sinon on refuse de tourner (et donc de TRUNCATE).
  3. ISOLATION — `TRUNCATE` entre chaque test, exclusivement sur `aschool_test`.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

# --- Amorçage, une fois pour toutes (01/08) -----------------------------------
# Cinquante-deux fichiers de tests recopiaient le même préambule : `ROOT`,
# `sys.path.insert(0, ROOT)` et, dans quarante-trois d'entre eux, `os.chdir(ROOT)`.
# Deux ennuis. D'abord `ROOT` ne désignait pas la racine du dépôt mais le dossier
# `tests/` : le chdir déplaçait donc le répertoire courant de TOUTE la suite dans
# `tests/`, sans que personne l'ait voulu. Ensuite chaque nouveau fichier devait
# penser à recopier ces lignes pour que `from _profil import …` fonctionne.
# Les deux chemins sont posés ici, une seule fois : la racine (les imports
# `backend.…`) et `tests/` (les aides partagées, `_profil`).
_RACINE = Path(__file__).resolve().parent
for _p in (_RACINE, _RACINE / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# --- Les trois garde-fous des bibliothèques de calcul (02/08) -----------------
# Trente fichiers de tests recopiaient ces trois lignes en tête, avant leurs imports. Le
# ménage du 01/08 avait factorisé le reste du préambule et les avait oubliées.
#
# Ce qu'elles font, et pourquoi elles doivent être posées ICI :
#
#   KMP_DUPLICATE_LIB_OK   torch et numpy embarquent chacun leur runtime OpenMP. Deux
#                          runtimes dans le même processus font ABORTER l'interpréteur sous
#                          Windows — pas une erreur, un arrêt net. Contournement officiel.
#   TOKENIZERS_PARALLELISM  les tokenizers HuggingFace forkent ; après un fork, ils écrivent
#                          un avertissement à chaque appel et brouillent la sortie des tests.
#   OMP_NUM_THREADS        un seul cœur pour OpenMP. Le conteneur en rend 8 au calcul
#                          (docker-compose.yml) ; pour les tests, un thread suffit et évite
#                          que trente fichiers lancés à la suite se disputent les cœurs.
#
# `setdefault`, jamais `=` : une valeur déjà posée par l'environnement (le compose, un
# lanceur) gagne. C'est ce qui permet aux 8 cœurs du conteneur de rester en place hors tests.
#
# Le conftest est importé AVANT la collecte, donc avant le premier `import torch` de n'importe
# quel fichier de tests : posées ici, elles arrivent à temps pour tous.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

# Pièces jointes : la suite écrit dans un dossier temporaire, JAMAIS dans le vrai
# data/uploads/feedbacks. Même principe que DATABASE_URL ci-dessous — la base de test
# est une autre base, le dossier de test est un autre dossier. Posé AVANT tout import
# de backend.communication.feedback, qui lit cette variable au chargement.
os.environ.setdefault("UPLOAD_DIR_FEEDBACKS", tempfile.mkdtemp(prefix="aschool_test_uploads_"))

# --- Verrou 1 : barrière physique anti-SQLite (posée avant toute collecte) ---
_real_create_engine = sqlalchemy.create_engine


def _no_sqlite_create_engine(url, *args, **kwargs):
    if str(url).startswith("sqlite"):
        raise RuntimeError(
            "SQLite INTERDIT dans les tests aSchool. Moteur unique = PostgreSQL "
            "(base de test 'aschool_test'). Tout create_engine('sqlite...') est banni "
            "— voir conftest.py. Les tests doivent passer par la redirection PostgreSQL."
        )
    return _real_create_engine(url, *args, **kwargs)


sqlalchemy.create_engine = _no_sqlite_create_engine

# --- URL de la base de test : obligatoire, PostgreSQL, base 'aschool_test' ---
from dotenv import load_dotenv  # noqa: E402

load_dotenv(dotenv_path=Path(__file__).resolve().parents[0] / ".env", override=True)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL absente du .env (postgresql .../aschool_test attendu).")
_u = make_url(TEST_DATABASE_URL)
if _u.get_backend_name() != "postgresql":
    raise RuntimeError(f"TEST_DATABASE_URL doit être PostgreSQL, reçu : {_u.get_backend_name()!r}")
if _u.database != "aschool_test":
    raise RuntimeError(f"TEST_DATABASE_URL doit viser 'aschool_test', reçu : {_u.database!r}")

# DATABASE_URL = test AVANT tout import de backend.core.database (sinon défaut SQLite de prod).
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# `lock_timeout` : un test qui laisse sa session ouverte (une exception levée avant son
# `db.close()`, par exemple) garde une transaction en cours ; le TRUNCATE de nettoyage l'attend
# alors INDÉFINIMENT et la suite entière se fige sans afficher une seule ligne — impossible à
# diagnostiquer, et chaque relance se met en file derrière la première. Avec ce plafond, le
# blocage devient une erreur immédiate qui NOMME la table : on sait quoi réparer.
# `idle_in_transaction_session_timeout` coupe la session fautive elle-même, pour que la relance
# suivante reparte sur une base saine.
_test_engine = _real_create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"options": "-c lock_timeout=15s -c idle_in_transaction_session_timeout=60s"},
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

import backend.core.database as _dbmod  # noqa: E402

_dbmod.engine = _test_engine
_dbmod.SessionLocal = _TestSession


# --- Verrou 2 : garde-fou positif (refuse tout sauf postgresql/aschool_test) ---
def _assert_test_engine():
    eng = _dbmod.engine
    assert eng.dialect.name == "postgresql", \
        f"SÉCURITÉ: moteur de test non-PostgreSQL ({eng.dialect.name}) — on s'arrête."
    assert eng.url.database == "aschool_test", \
        f"SÉCURITÉ: base de test != 'aschool_test' (reçu {eng.url.database!r}) — TRUNCATE refusé."


_assert_test_engine()

# --- Schéma sur aschool_test (l'extension vector existe déjà ; create_all fait le reste) ---
from backend.core import models_db  # noqa: E402
from backend.core.llm_prompts import PROMPTS as _PROMPTS  # noqa: E402

with _test_engine.begin() as _conn:
    _conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
# TABLE RASE AVANT create_all. Deux raisons, et la seconde a coûté cher :
#   1. `create_all` crée les tables MANQUANTES mais n'ajoute jamais une colonne à une table
#      déjà là : une base de test montée hier resterait figée sur le schéma d'hier, et la
#      suite tomberait sur une colonne inconnue — un faux échec, qui ne dit rien du code.
#   2. `Base.metadata.drop_all` ne connaît QUE les tables encore déclarées. Une table dont on
#      vient de supprimer le modèle SURVIT donc dans la base de test, et sa clé étrangère
#      empêche de retirer la table dont elle dépend : toute la suite tombait sur un
#      `DependentObjectsStillExist` qui ne parlait de rien (vu le 01/08 en retirant
#      seance_phases). On balaie donc ce qui EXISTE, pas ce qu'on croit exister.
# Les deux verrous ci-dessus garantissent qu'on ne peut viser que `aschool_test`.
# `alembic_version` est épargnée : elle n'appartient pas aux modèles.
with _test_engine.begin() as _conn:
    _a_droper = [r[0] for r in _conn.execute(text(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
    ))]
    for _t in _a_droper:
        _conn.execute(text(f'DROP TABLE IF EXISTS "{_t}" CASCADE'))
models_db.Base.metadata.create_all(bind=_test_engine)


# --- Catalogues de référence : semés par MIGRATION en prod, mais le schéma de test est monté
# par create_all (sans migrations). Le TRUNCATE (verrou 3) les vide entre chaque test → on les
# re-sème avant chaque test, sinon les FK (ex. feedbacks.statut) et le no-fallback plantent.
# Une entrée par table-catalogue : les tâches suivantes (features, durées) l'étendront ici.
_CATALOGUES_SEED = {
    "feedback_statuts": [
        {"code": "nouveau", "label": "Nouveau", "modifiable": True, "ordre": 0, "description": "Reçu, pas encore traité."},
        {"code": "en_cours", "label": "En cours", "modifiable": True, "ordre": 1, "description": "Pris en charge par l'équipe."},
        {"code": "traite", "label": "Traité", "modifiable": False, "ordre": 2, "description": "Résolu ou intégré."},
        {"code": "archive", "label": "Archivé", "modifiable": False, "ordre": 3, "description": "Clôturé."},
    ],
    # Catalogues du formulaire de séance : le serveur valide le mode et le style CONTRE ces
    # tables (plus de liste en dur), donc sans elles toute génération de séance est refusée.
    "seance_modes": [
        {"code": "standard", "label": "Séance standard", "description": "Nouvelle séance sur le thème", "ordre": 0, "actif": True},
        {"code": "remediation", "label": "Remédiation", "description": "La classe n'a pas compris, on recommence autrement", "ordre": 1, "actif": True},
        {"code": "approfondissement", "label": "Approfondissement", "description": "Aller plus loin sur un thème déjà acquis", "ordre": 2, "actif": True},
        {"code": "autonomie", "label": "Autonomie guidée", "description": "Les élèves travaillent seuls, la séance les guide", "ordre": 3, "actif": True},
    ],
    "seance_styles": [
        {"code": "classique", "label": "Classique", "description": "Fiche de préparation traditionnelle.", "ordre": 0, "actif": True},
        {"code": "ludique", "label": "Ludique", "description": "La séance passe par le jeu.", "ordre": 1, "actif": True},
        {"code": "structure", "label": "Structuré", "description": "Un découpage très net.", "ordre": 2, "actif": True},
        {"code": "concis", "label": "Très concis", "description": "Le format télégraphique.", "ordre": 3, "actif": True},
    ],
    # Critères de l'écran « Détecter les ambiguïtés » : le serveur valide les codes reçus
    # CONTRE cette table, donc sans elle toute analyse est refusée.
    "ambiguite_criteres": [
        {"code": "consigne_vague", "label": "Consigne vague", "description": "Verbe trop général sans critères précis.", "ordre": 0, "actif": True},
        {"code": "vocabulaire_non_defini", "label": "Vocabulaire technique non défini", "description": "Terme spécialisé supposé connu.", "ordre": 1, "actif": True},
        {"code": "double_sens", "label": "Double sens", "description": "Interprétable de deux façons.", "ordre": 2, "actif": True},
        {"code": "criteres_reussite_absents", "label": "Critères de réussite absents", "description": "L'élève ne sait pas ce qu'on attend.", "ordre": 3, "actif": True},
        {"code": "reference_implicite", "label": "Référence implicite", "description": "« le texte » sans préciser lequel.", "ordre": 4, "actif": True},
        {"code": "consigne_trop_longue", "label": "Consigne trop longue", "description": "Plusieurs tâches non séparées.", "ordre": 5, "actif": True},
        {"code": "autre", "label": "Autre", "description": "", "ordre": 6, "actif": True},
    ],
    "langues_lv": [
        {"code": "anglais", "label": "Anglais", "ordre": 0, "actif": True},
        {"code": "espagnol", "label": "Espagnol", "ordre": 1, "actif": True},
        {"code": "allemand", "label": "Allemand", "ordre": 2, "actif": True},
        {"code": "italien", "label": "Italien", "ordre": 3, "actif": True},
        {"code": "portugais", "label": "Portugais", "ordre": 4, "actif": True},
        {"code": "arabe", "label": "Arabe", "ordre": 5, "actif": True},
        {"code": "chinois", "label": "Chinois", "ordre": 6, "actif": True},
        {"code": "autre", "label": "Autre", "ordre": 7, "actif": True},
    ],
    # Fournisseurs LLM : catalogue semé par MIGRATION en prod (ai_fournisseurs), donc à re-semer
    # ici (create_all ne seed pas). cle_env = NOM de la variable d'env de la clé texte, lu en base
    # par get_cle_texte ; la valeur du secret vient du .env chargé par ce conftest.
    "ai_fournisseurs": [
        {"code": "groq", "label": "Groq", "actif": True, "ordre": 1, "cle_env": "GROQ_API_KEY_TEXTE"},
        {"code": "anthropic", "label": "Anthropic (Claude)", "actif": True, "ordre": 2, "cle_env": "CLAUDE_API_KEY_TEXTE"},
    ],
    # Fonctionnalités votables (écran « Bientôt disponible ») : catalogue semé par MIGRATION
    # en prod (features_votables). Sous-ensemble représentatif : deux actives + une inactive
    # (les votes d'une carte retirée restent comptés côté admin, mais la carte quitte l'écran).
    "features_votables": [
        {"code": "analyser-consigne", "label": "Analyser une consigne", "description": "Analyse d'une consigne.",
         "categorie": "Outils pédagogiques", "icone": "loupe", "ordre": 0, "actif": True},
        {"code": "quiz-interactif", "label": "Quiz interactif élèves", "description": "Quiz partagé aux élèves.",
         "categorie": "Autre", "icone": "horloge", "ordre": 1, "actif": True},
        {"code": "outil-retire", "label": "Outil retiré", "description": "Carte retirée de l'écran.",
         "categorie": "Autre", "icone": "fusee", "ordre": 2, "actif": False},
    ],
    # Réglages de `settings` SEMÉS PAR MIGRATION, que le code lit SANS défaut (get_few_shot_seuil
    # lève une erreur claire si la ligne manque — règle maison : base vide = erreur, pas repli).
    # Sans eux ici, la génération et Mes stats répondraient 500 dans les tests, à juste titre.
    "settings": [
        {"key": "few_shot_seuil", "value": "3"},
        {"key": "few_shot_extrait_max", "value": "3000"},
        # TOUS les prompts du registre (étape 9 lot C) : `get_prompt` n'a plus de repli code,
        # donc une clé non semée fait tomber l'outil qui l'utilise — ici comme en production.
        # Semés depuis le registre : ce fichier monte le schéma par create_all, pas par
        # migrations. Ce n'est PAS ce qui prouve la cohérence — la preuve, c'est
        # tests/test_prompts_en_base.py, qui compare le registre à la liste GELÉE de la
        # migration, pas à ce seed.
        *({"key": f"prompt_{cle}", "value": meta["default"]} for cle, meta in _PROMPTS.items()),
        # Seuils métier sortis du code (étape 9 lot B) : sans eux, joindre un fichier, générer
        # une séance ou déposer un cahier répondraient 500 dans les tests — à juste titre.
        {"key": "feedback_piece_jointe_max_mo", "value": "5"},
        {"key": "feedback_pieces_jointes_max", "value": "5"},
        {"key": "seance_duree_min", "value": "5"},
        {"key": "seance_duree_max", "value": "300"},
        {"key": "cahier_max_mo", "value": "20"},
    ],
}


# Outils LLM (table `outils_llm`) : semés par MIGRATION en prod, et il n'existe AUCUNE liste dans
# le code — c'est le sujet même de cette table. Les recopier ici en ferait une deuxième source qui
# dériverait ; on lit donc CELLE de la migration, par son chemin. Le fichier n'est pas importable
# par `import` (les révisions alembic ne sont pas un paquet), d'où importlib.
def _outils_llm_de_la_migration():
    """La liste de b4e8d2a6f1c9, PLUS les outils ajoutés par les migrations suivantes.

    Un outil de plus arrive par migration (c'est la règle : `outils_llm` n'a aucune liste dans le
    code). Ne lire que la migration d'origine ferait donc échouer la base de test au premier ajout,
    alors que la prod, elle, l'aurait — et le filet de test_outils_llm_en_base accuserait le code
    au lieu du seed. Toute migration qui expose une constante `OUTILS` de la même forme
    (outil, libelle, ordre, aide) est prise en compte, dans l'ordre des noms de fichier."""
    import importlib.util
    dossier = _RACINE / "alembic" / "versions"
    outils, retires = [], set()
    for chemin in sorted(dossier.glob("*.py")):
        if "OUTILS" not in chemin.read_text(encoding="utf-8"):
            continue
        spec = importlib.util.spec_from_file_location(f"_mig_outils_{chemin.stem}", chemin)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        outils.extend(getattr(module, "OUTILS", []))
        # Un outil peut aussi PARTIR (`referentiel_fusion`, 10/08/2026, avec le labo). Sans ce
        # retrait, la base de test garderait une ligne que la prod n'a plus, et le filet de
        # test_outils_llm_en_base accuserait le code d'avoir perdu un appel qui n'existe plus.
        retires.update(getattr(module, "OUTILS_RETIRES", ()))
    return [o for o in outils if o[0] not in retires]


_OUTILS_LLM = _outils_llm_de_la_migration()


# Réglages de `settings` semés par MIGRATION (constante `REGLAGES`). Même raison que pour les
# outils : la liste n'existe QUE dans les migrations depuis le 10/08/2026 — le dictionnaire en
# dur `SETTING_DEFAULTS` a été vidé, `get_settings_dict()` ne fabrique plus rien. Les recopier
# ici en ferait une deuxième source qui dériverait ; on lit donc CELLES des migrations.
def _reglages_des_migrations():
    import importlib.util
    dossier = _RACINE / "alembic" / "versions"
    reglages = {}
    for chemin in sorted(dossier.glob("*.py")):
        if "REGLAGES" not in chemin.read_text(encoding="utf-8"):
            continue
        spec = importlib.util.spec_from_file_location(f"_mig_reglages_{chemin.stem}", chemin)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        reglages.update(getattr(module, "REGLAGES", {}))
    return reglages


_REGLAGES_MIGRES = _reglages_des_migrations()


def resemer_reglages(db=None, sauf=()) -> None:
    """Repose les réglages semés par migration après un `DELETE FROM settings` de test.

    POURQUOI ELLE EXISTE. Plusieurs suites font table rase de `settings` pour partir d'un état
    connu. C'était sans conséquence tant que `SETTING_DEFAULTS` fournissait une valeur de secours
    à tout ; depuis le 10/08/2026 il n'en fournit plus (les réglages sont en base, et une ligne
    absente LÈVE). Une table `settings` vide n'est donc plus un état neutre : c'est une base
    incomplète, que le serveur refuse — à juste titre.

    Vider puis rappeler cette fonction rend l'état RÉEL d'une installation à jour. Un test qui
    veut éprouver l'absence d'UNE clé — ou qui teste l'écriture de cette clé — la nomme dans
    `sauf` : c'est plus honnête que de supprimer tout et d'espérer."""
    with _test_engine.begin() as conn:
        for cle, valeur in _REGLAGES_MIGRES.items():
            if cle in sauf:
                continue
            conn.execute(
                text("INSERT INTO settings (key, value) VALUES (:key, :value) "
                     "ON CONFLICT (key) DO NOTHING"),
                {"key": cle, "value": valeur},
            )
    if db is not None:
        db.expire_all()


def _seed_catalogues():
    with _test_engine.begin() as conn:
        for row in _CATALOGUES_SEED["feedback_statuts"]:
            conn.execute(
                text(
                    "INSERT INTO feedback_statuts (code, label, modifiable, ordre, description) "
                    "VALUES (:code, :label, :modifiable, :ordre, :description) ON CONFLICT (code) DO NOTHING"
                ),
                row,
            )
        for table in ("seance_modes", "seance_styles", "ambiguite_criteres"):
            for row in _CATALOGUES_SEED[table]:
                conn.execute(
                    text(
                        f"INSERT INTO {table} (code, label, description, ordre, actif) "
                        "VALUES (:code, :label, :description, :ordre, :actif) ON CONFLICT (code) DO NOTHING"
                    ),
                    row,
                )
        for row in _CATALOGUES_SEED["langues_lv"]:
            conn.execute(
                text(
                    "INSERT INTO langues_lv (code, label, ordre, actif) "
                    "VALUES (:code, :label, :ordre, :actif) ON CONFLICT (code) DO NOTHING"
                ),
                row,
            )
        for row in _CATALOGUES_SEED["ai_fournisseurs"]:
            conn.execute(
                text(
                    "INSERT INTO ai_fournisseurs (code, label, actif, ordre, cle_env) "
                    "VALUES (:code, :label, :actif, :ordre, :cle_env) ON CONFLICT (code) DO NOTHING"
                ),
                row,
            )
        for cle, valeur in _REGLAGES_MIGRES.items():
            conn.execute(
                text("INSERT INTO settings (key, value) VALUES (:key, :value) "
                     "ON CONFLICT (key) DO NOTHING"),
                {"key": cle, "value": valeur},
            )
        for row in _CATALOGUES_SEED["settings"]:
            conn.execute(
                text("INSERT INTO settings (key, value) VALUES (:key, :value) "
                     "ON CONFLICT (key) DO NOTHING"),
                row,
            )
        for outil, libelle, ordre, aide in _OUTILS_LLM:
            conn.execute(
                text(
                    "INSERT INTO outils_llm (outil, libelle, aide, ordre) "
                    "VALUES (:outil, :libelle, :aide, :ordre) ON CONFLICT (outil) DO NOTHING"
                ),
                {"outil": outil, "libelle": libelle, "aide": aide, "ordre": ordre},
            )
        for row in _CATALOGUES_SEED["features_votables"]:
            conn.execute(
                text(
                    "INSERT INTO features_votables (code, label, description, categorie, icone, ordre, actif) "
                    "VALUES (:code, :label, :description, :categorie, :icone, :ordre, :actif) "
                    "ON CONFLICT (code) DO NOTHING"
                ),
                row,
            )


# --- Verrou 3 : isolation par test = TRUNCATE, UNIQUEMENT sur aschool_test ---
@pytest.fixture(autouse=True)
def _clean_db():
    _assert_test_engine()      # garde-fou AVANT le test
    _seed_catalogues()         # catalogues de référence re-semés (create_all ne les seed pas)
    yield
    _assert_test_engine()      # garde-fou AVANT le TRUNCATE (re-vérifié à chaque fois)
    tables = [t.name for t in reversed(models_db.Base.metadata.sorted_tables)]
    if tables:
        with _test_engine.begin() as conn:
            conn.execute(text(
                "TRUNCATE TABLE "
                + ", ".join(f'"{t}"' for t in tables)
                + " RESTART IDENTITY CASCADE"
            ))
