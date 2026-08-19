"""Migre CHAQUE schéma de démonstration jusqu'à `head`, et le dit schéma par schéma.

    docker exec -e DATABASE_URL=postgresql+psycopg://aschool:aschool@db:5432/aschool_demos \
        a-school-backend-1 python outils_bdd/migrer_les_demos.py

POURQUOI UN SCRIPT ET PAS UN `alembic upgrade head`. Les démonstrations partagent une base
et ont chacune leur table `alembic_version`, dans leur schéma. Un `upgrade head` ordinaire n'en
verrait qu'une — celle de `public`, qui n'existe pas ici — et ne migrerait rien.

IL S'ARRÊTE AU PREMIER ÉCHEC, ET IL NOMME LE FAUTIF. Continuer laisserait la base avec des
schémas à des niveaux différents et un rapport qui dit « terminé » : c'est l'état le plus cher à
diagnostiquer, parce que l'application répond quand même. Les schémas déjà migrés le restent —
une migration est validée schéma par schéma, il n'y a rien à défaire.

LA LISTE DES SCHÉMAS VIENT DE LA BASE, comme la liste blanche du routage : ce qui est là est ce
qui se migre. `public` est exclu — il ne porte que l'extension `vector`.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

URL = os.getenv("DATABASE_URL") or sys.exit("DATABASE_URL absente.")

# ALEMBIC SE PREND À CÔTÉ DE L'INTERPRÉTEUR QUI NOUS EXÉCUTE, jamais dans le PATH. Sur le VPS il
# vit dans `.venv/bin/` et le PATH ne le connaît pas : lancé par `.venv/bin/python`, ce script
# tombait sur « No such file or directory: 'alembic' ». Dans le conteneur, les deux sont dans
# `/usr/local/bin` — la règle vaut partout.
ALEMBIC = str(Path(sys.executable).parent / "alembic")
if "demo" not in URL.rsplit("/", 1)[-1]:
    sys.exit(f"ARRET : {URL.rsplit('/', 1)[-1]!r} ne ressemble pas à la base des démonstrations.")

moteur = create_engine(URL)
with moteur.connect() as conn:
    schemas = [r[0] for r in conn.execute(text(
        r"SELECT nspname FROM pg_namespace "
        r"WHERE nspname NOT LIKE 'pg\_%' "
        "AND nspname NOT IN ('public', 'information_schema') ORDER BY 1"
    ))]

if not schemas:
    sys.exit("Aucun schéma de démonstration dans cette base.")
tete = subprocess.run([ALEMBIC, "heads"], capture_output=True, text=True).stdout.split()[0]
print(f"{len(schemas)} schémas à migrer vers {tete} : {', '.join(schemas)}\n")

for schema in schemas:
    if not re.fullmatch(r"[a-z0-9_]{1,63}", schema):
        sys.exit(f"ARRET : nom de schéma inattendu {schema!r}.")
    print(f"── {schema}")
    fait = subprocess.run([ALEMBIC, "-x", f"schema={schema}", "upgrade", "head"],
                          capture_output=True, text=True)
    if fait.returncode != 0:
        print(fait.stdout, fait.stderr, sep="\n")
        sys.exit(f"\nARRET sur le schéma « {schema} ». Les schémas suivants n'ont pas été migrés.")
    # ON RELIT LA BASE, ET ON COMPARE. Un code de retour nul ne prouve rien : Alembic peut
    # annoncer neuf migrations, rendre 0 et n'avoir rien écrit (mesuré le 10/08/2026 — une
    # transaction ouverte trop tôt l'empêchait de valider). La seule preuve qu'un schéma est
    # à jour, c'est son estampille relue dans la base, comparée à la tête des migrations.
    with moteur.connect() as conn:
        version = conn.execute(text(f"SELECT version_num FROM {schema}.alembic_version")).scalar()
    if version != tete:
        sys.exit(f"   ARRET : {schema} est resté en {version}, la tête est {tete}. Alembic "
                 f"a rendu 0 sans écrire — les schémas suivants n'ont pas été migrés.")
    print(f"   à jour : {version}")

print(f"\nLes {len(schemas)} schémas sont à head ({tete}).")
