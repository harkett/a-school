"""Filet de reproductibilite des tables cycles / niveaux.

Ces tables portent une DECISION HUMAINE (les 11 cycles, 88 niveaux), pas une
donnee extraite d'un referentiel. Elles ne sont donc PAS reconstructibles par
re-ingestion. Ce script les capture dans cycles_niveaux.json (source de verite
committee) et sait les rejouer sur une base neuve.

Outil de MAINTENANCE (hors application) : il vit dans outils_bdd/, pas sous backend/.
Il ne porte AUCUNE donnee en dur : toute la donnee vit dans le JSON.

DOCTRINE DU SCRIPT EPHEMERE : ce qui est interdit, ce n'est pas qu'un script reste, c'est
qu'il reste en PORTANT la donnee — la donnee y devient une seconde source de verite que
personne ne pense a mettre a jour. Celui-ci lit le JSON committe : il a donc le droit de rester.

RECONSTRUCTION, PAS CORRECTION.
  Le mode "rejouer" fait un insert-si-absent (par id) : il n'ecrase JAMAIS une
  ligne existante. Donc :
    - sur une base VIDE  -> reconstruit fidelement les 11 cycles / 88 niveaux ;
    - sur une base PLEINE -> tous les ids existent, tout est saute, zero effet.
  Pour CORRIGER une donnee existante : ecran admin, ou base neuve. Pas ici.

Usage (depuis la racine du depot) :
  python outils_bdd/rebuild_cycles_niveaux.py --export   # base  -> JSON  (apres un ajout humain)
  python outils_bdd/rebuild_cycles_niveaux.py            # JSON  -> base  (idempotent, defaut)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Racine du depot sur le sys.path : ce script vit dans outils_bdd/, on doit pouvoir
# importer le package backend (lance par chemin, sys.path[0] = outils_bdd/, pas la racine).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

# .env AVANT d'importer backend.core.database : son garde-fou (refus sans
# DATABASE_URL PostgreSQL) se declenche des l'import, donc l'env doit etre pret.
#
# `override=False` — LE DEFAUT, ET C'EST DELIBERE (corrige le 02/08/2026). Avec `override=True`,
# le .env ecrasait l'environnement DEJA POSE. Or le .env porte l'adresse de la base vue DE LA
# MACHINE (127.0.0.1:5433) tandis que le conteneur joint la base par le nom du service
# (db:5432, pose par docker-compose.yml APRES env_file, exprES). Lance dans la boite — ce que
# le README de ce dossier indique de faire, et le seul endroit ou Python existe encore sur ce
# poste — ce script visait donc 127.0.0.1:5433, qui n'y existe pas : "Connection refused".
# L'environnement gagne, le .env comble les trous. Meme regle que les `setdefault` du conftest.
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

from sqlalchemy import text  # noqa: E402

from backend.core.database import SessionLocal  # noqa: E402
from backend.core.models_db import Cycle, Niveau  # noqa: E402

DATA_FILE = Path(__file__).with_name("cycles_niveaux.json")


def export(session) -> None:
    """Base -> JSON : capture l'etat reel (id compris) dans DATA_FILE."""
    cycles = session.query(Cycle).order_by(Cycle.id).all()
    niveaux = session.query(Niveau).order_by(Niveau.id).all()
    payload = {
        "_note": (
            "Decision humaine (11 cycles / 88 niveaux). Non reconstructible par "
            "re-ingestion. Source de verite pour reconstruire une base neuve. "
            "Edition manuelle reservee a l'ajout humain d'un cycle/niveau, suivi "
            "d'un --export. RECONSTRUCTION, PAS CORRECTION."
        ),
        "cycles": [
            {"id": c.id, "nom": c.nom, "ordre": c.ordre} for c in cycles
        ],
        "niveaux": [
            {"id": n.id, "cycle_id": n.cycle_id, "nom": n.nom, "ordre": n.ordre}
            for n in niveaux
        ],
    }
    DATA_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[export] {len(cycles)} cycles / {len(niveaux)} niveaux -> {DATA_FILE.name}")


def _reset_sequence(session, table: str) -> None:
    """Recale la sequence d'auto-increment sur MAX(id) apres des inserts d'ids explicites.

    Sans ca, le prochain insert automatique entrerait en collision avec un id
    deja pose par la reconstruction.
    """
    session.execute(
        text(
            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
            f"(SELECT MAX(id) FROM {table}))"
        )
    )


def rejouer(session) -> None:
    """JSON -> base : insert-si-absent (par id), idempotent. N'ecrase jamais l'existant."""
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    c_ins = c_skip = 0
    for c in data["cycles"]:
        if session.get(Cycle, c["id"]) is None:
            session.add(Cycle(id=c["id"], nom=c["nom"], ordre=c["ordre"]))
            c_ins += 1
        else:
            c_skip += 1

    n_ins = n_skip = 0
    for n in data["niveaux"]:
        if session.get(Niveau, n["id"]) is None:
            session.add(
                Niveau(
                    id=n["id"],
                    cycle_id=n["cycle_id"],
                    nom=n["nom"],
                    ordre=n["ordre"],
                )
            )
            n_ins += 1
        else:
            n_skip += 1

    session.flush()
    _reset_sequence(session, "cycles")
    _reset_sequence(session, "niveaux")
    session.commit()

    print(
        f"[rejouer] cycles : {c_ins} inseres, {c_skip} deja la "
        f"| niveaux : {n_ins} inseres, {n_skip} deja la"
    )


def _base_visee() -> str:
    """« hote:port/base », sans le mot de passe (str() d'une URL SQLAlchemy le masque deja).

    AFFICHE AVANT D'AGIR : le .env de la machine et l'environnement de la boite ne visent pas
    la meme base, et ce script ECRIT. Le README dit « verifier .env avant de rejouer » — vrai
    sur la machine, mais dans le conteneur c'est l'environnement qui decide. Plutot que de
    demander a l'operateur de deviner laquelle des deux gagne, on la lui montre."""
    from backend.core.database import engine
    u = engine.url
    return f"{u.host}:{u.port}/{u.database}"


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--rejouer"
    print(f"[base] {_base_visee()}")
    session = SessionLocal()
    try:
        if mode == "--export":
            export(session)
        elif mode in ("--rejouer", ""):
            if not DATA_FILE.exists():
                sys.exit(f"[erreur] snapshot introuvable : {DATA_FILE}. Lance d'abord --export.")
            rejouer(session)
        else:
            sys.exit(f"[erreur] mode inconnu : {mode!r} (attendu : --export ou --rejouer)")
    finally:
        session.close()


if __name__ == "__main__":
    main()
