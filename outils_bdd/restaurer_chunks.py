"""Rejoue une sauvegarde de chunks RAG dans la base — le chemin du retour.

POURQUOI CET OUTIL EXISTE. Avant toute suppression de chunks, `ingest_pgvector` écrit un
dump JSONL, le relit et compte ses lignes : le filet est ancien et il tient. Mais RIEN dans
le dépôt ne savait le rejouer. La sauvegarde protégeait donc la donnée sans protéger
l'opération : on pouvait constater qu'on avait tout perdu, pas le défaire. Tant que c'était
vrai, aucune réingestion ne pouvait être autorisée. C'est ce fichier qui lève ce préalable.

CE QUE ÇA COÛTE : rien. Le dump porte le texte ET les embeddings (1024 flottants par chunk).
Une restauration ne repasse ni par le PDF, ni par la découpe IA, ni par la vectorisation.
C'est une lecture de fichier et un INSERT.

POURQUOI IL VIT ICI, dans outils_bdd/, et pourquoi il a le droit d'y RESTER. La doctrine du
« script éphémère » — écrite dans rebuild_cycles_niveaux.py — n'interdit pas qu'un script
reste : elle interdit qu'il reste EN PORTANT LA DONNÉE, car la donnée y devient une seconde
source de vérité que personne ne met à jour. Celui-ci ne porte aucune donnée : il lit un
fichier de sauvegarde. Et outils_bdd/ est précisément le dossier des FILETS PERMANENTS —
rebuild_cycles_niveaux.py y est né du jour où un script éphémère avait été supprimé sans
laisser de trace rejouable. C'est exactement le même manque qu'on répare ici.

POURQUOI PAS D'ÉCRAN ADMIN. Une restauration est rare, destructrice, et suppose de choisir
un fichier sur le disque du serveur. Un bouton la mettrait à portée de clic à côté des gestes
courants, et ajouterait une porte qui purge des chunks — on vient d'en fermer une (point 10).
Le geste doit rester délibéré : on ouvre un terminal, on lit d'abord, on écrit ensuite.

USAGE (dans le conteneur : docker compose exec backend python outils_bdd/restaurer_chunks.py …)

    --lister                                        # les sauvegardes disponibles
    --collection <col> --fichier <chemin>           # VÉRIFIE seulement, n'écrit rien (défaut)
    --collection <col> --fichier <chemin> --restaurer   # écrit, après avoir sauvé l'état courant

Le mode par défaut est la vérification : il applique les trois refus et dit ce qui SERAIT
fait, sans toucher la base. Il faut demander `--restaurer` pour écrire. Même principe que le
`--dry-run` de l'ingestion et que le mode sûr par défaut de rebuild_cycles_niveaux.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Racine du dépôt sur le sys.path : ce script vit dans outils_bdd/, on doit pouvoir importer
# le package backend (lancé par chemin, sys.path[0] = outils_bdd/, pas la racine).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

# .env AVANT d'importer backend.core.database : son garde-fou (refus sans DATABASE_URL
# PostgreSQL) se déclenche dès l'import, donc l'environnement doit être prêt.
#
# `override=False` — LE DÉFAUT, ET C'EST DÉLIBÉRÉ. Avec `override=True`, le `.env` écrase
# l'environnement déjà posé. Or le `.env` porte l'adresse de la base VUE DE LA MACHINE
# (127.0.0.1:5433) tandis que le conteneur, lui, joint la base par le nom du service
# (db:5432, posé par docker-compose.yml APRÈS env_file, exprès). Lancé dans la boîte avec
# `override=True`, cet outil visait donc 127.0.0.1:5433, qui n'existe pas là-dedans —
# constaté du premier coup. L'environnement gagne, le .env comble les trous : même règle
# que les `setdefault` du conftest.
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

from sqlalchemy import func, select  # noqa: E402

from backend.core.database import SessionLocal  # noqa: E402
from backend.core.models_db import Referentiel, ReferentielChunk  # noqa: E402
from backend.rag.embeddings import EMBEDDING_MODEL  # noqa: E402
from backend.rag.pgvector_store import (  # noqa: E402
    BACKUP_DIR,
    lire_sauvegarde,
    restaurer_chunks_depuis_sauvegarde,
)


def dbmod_engine_repr() -> str:
    """« hote:port/base », sans le mot de passe (str() d'une URL SQLAlchemy le masque déjà)."""
    from backend.core.database import engine
    u = engine.url
    return f"{u.host}:{u.port}/{u.database}"


def lister() -> None:
    """Les sauvegardes présentes sur le disque, la plus récente d'abord."""
    fichiers = sorted(BACKUP_DIR.glob("*.bak-*.jsonl"), reverse=True)
    if not fichiers:
        print(f"Aucune sauvegarde dans {BACKUP_DIR}.")
        return
    print(f"{len(fichiers)} sauvegarde(s) dans {BACKUP_DIR} :\n")
    for f in fichiers:
        try:
            lignes = lire_sauvegarde(f)
            rids = sorted({l["referentiel_id"] for l in lignes})
            modeles = sorted({l["embedding_model"] for l in lignes})
            etat = f"{len(lignes):4d} chunks | referentiel {rids} | {', '.join(modeles)}"
        except RuntimeError as e:
            etat = f"ILLISIBLE : {str(e).splitlines()[0]}"
        print(f"  {f.name}\n      {etat}")


def _referentiel(db, collection: str) -> Referentiel:
    ref = db.execute(
        select(Referentiel).where(Referentiel.collection == collection)
    ).scalar_one_or_none()
    if ref is None:
        connues = [c for (c,) in db.execute(select(Referentiel.collection).order_by(Referentiel.collection))]
        raise SystemExit(
            f"ARRET : aucun referentiel pour collection={collection!r}.\n"
            f"  Collections en base : {', '.join(connues) or '(aucune)'}"
        )
    return ref


def main() -> None:
    p = argparse.ArgumentParser(description="Rejoue une sauvegarde de chunks RAG dans la base.")
    p.add_argument("--lister", action="store_true", help="liste les sauvegardes disponibles et sort")
    p.add_argument("--collection", help="collection du couple visé (ex. bebes_0_1_an)")
    p.add_argument("--fichier", help="chemin du dump .jsonl à rejouer")
    p.add_argument("--restaurer", action="store_true",
                   help="ÉCRIT réellement (sans ce drapeau : vérification seule)")
    a = p.parse_args()

    if a.lister:
        lister()
        return
    if not a.collection or not a.fichier:
        p.error("il faut --collection ET --fichier (ou --lister)")

    chemin = Path(a.fichier)
    if not chemin.is_absolute() and not chemin.exists():
        chemin = BACKUP_DIR / chemin      # confort : un simple nom de fichier suffit

    db = SessionLocal()
    try:
        ref = _referentiel(db, a.collection)
        actuels = db.scalar(
            select(func.count()).select_from(ReferentielChunk)
            .where(ReferentielChunk.referentiel_id == ref.id)
        )
        try:
            lignes = lire_sauvegarde(chemin)
        except RuntimeError as e:
            raise SystemExit(f"ARRET : {e}")

        # La base est NOMMÉE : une commande destructrice ne doit jamais laisser deviner sur
        # quoi elle agit (le .env de la machine et celui de la boîte ne visent pas la même).
        print(f"Base        : {dbmod_engine_repr()}")
        print(f"Couple      : {a.collection} (referentiel {ref.id})")
        print(f"En base     : {actuels} chunks")
        print(f"Sauvegarde  : {chemin.name} -> {len(lignes)} chunks")
        print(f"Modele      : fichier {sorted({l['embedding_model'] for l in lignes})} "
              f"| courant '{EMBEDDING_MODEL}'")

        if not a.restaurer:
            # Vérification seule : on applique quand même les deux refus de contenu, pour
            # que « ça passera » soit une information et pas un espoir.
            mauvais = sorted({l["referentiel_id"] for l in lignes} - {ref.id})
            modeles = sorted({l["embedding_model"] or "" for l in lignes})
            if mauvais:
                raise SystemExit(f"\nREFUS : ce fichier vise le referentiel {mauvais}, pas {ref.id}.")
            if modeles != [EMBEDDING_MODEL]:
                raise SystemExit(f"\nREFUS : vecteurs de {modeles}, modele courant '{EMBEDDING_MODEL}'.")
            print(f"\nVERIFICATION SEULE — rien n'a ete ecrit.")
            print(f"  Une restauration remplacerait les {actuels} chunks actuels par les "
                  f"{len(lignes)} du fichier,")
            print(f"  apres avoir sauvegarde l'etat actuel dans {BACKUP_DIR}.")
            print(f"  Pour le faire : relancer la meme commande avec --restaurer")
            return

        try:
            res = restaurer_chunks_depuis_sauvegarde(db, chemin, ref.id, a.collection)
        except RuntimeError as e:
            raise SystemExit(f"ARRET : {e}")
        filet = res["sauvegarde_avant_restauration"]
        print(f"\nRESTAURE : {res['restaures']} chunks en base.")
        print(f"  Etat d'avant sauvegarde dans : {filet.get('sauvegarde') or '(rien a sauver, 0 chunk)'}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
