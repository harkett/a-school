"""Filet de reproductibilite des tables cycles / niveaux.

Ces tables portent une DECISION HUMAINE (les 11 cycles, 88 niveaux), pas une
donnee extraite d'un referentiel. Elles ne sont donc PAS reconstructibles par
re-ingestion. Ce script les capture dans cycles_niveaux.json (source de verite
committee) et sait les rejouer sur une base neuve.

Outil de MAINTENANCE (hors application) : il vit dans outils_bdd/, pas sous backend/.
Il ne porte AUCUNE donnee en dur : toute la donnee vit dans le JSON. Conforme a la
doctrine "script ephemere" (CLAUDE.md) : ce qui est interdit, c'est qu'un script
PERSISTE en PORTANT la donnee ; celui-ci la lit depuis le JSON committe, il a donc
le droit de rester.

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
load_dotenv()

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


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--rejouer"
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
