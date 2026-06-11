#!/usr/bin/env python
"""
Runner de migrations SQL — discipline minimale, sans dependance externe.

Applique, dans l'ordre, les fichiers migrations/NNN_*.sql non encore appliques.
Chaque fichier est joue dans UNE transaction (BEGIN ... COMMIT ; ROLLBACK si erreur),
et l'enregistrement dans schema_migrations se fait dans la MEME transaction
=> tout ou rien. Relancer n'applique que ce qui manque.

Usage :
  python migrations/run_migrations.py --db data/aschool.db [--dry-run]
"""
import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

MIG_DIR = Path(__file__).resolve().parent


def _statements(sql: str):
    """Decoupe un fichier SQL en statements, en retirant les lignes de commentaire --."""
    for chunk in sql.split(";"):
        lines = [ln for ln in chunk.splitlines() if not ln.strip().startswith("--")]
        stmt = "\n".join(lines).strip()
        if stmt:
            yield stmt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="chemin de la base SQLite")
    ap.add_argument("--dry-run", action="store_true", help="liste sans appliquer")
    args = ap.parse_args()

    if not Path(args.db).exists():
        print(f"Base introuvable : {args.db}")
        return 1

    con = sqlite3.connect(args.db)
    con.isolation_level = None  # on gere les transactions a la main
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " filename TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )

    done = {r[0] for r in cur.execute("SELECT filename FROM schema_migrations")}
    files = sorted(MIG_DIR.glob("[0-9][0-9][0-9]_*.sql"))
    pending = [f for f in files if f.name not in done]

    if not pending:
        print("Aucune migration en attente. Base a jour.")
        return 0

    print("Migrations en attente :", ", ".join(f.name for f in pending))
    if args.dry_run:
        print("(dry-run : rien applique)")
        return 0

    for f in pending:
        try:
            cur.execute("BEGIN")
            for stmt in _statements(f.read_text(encoding="utf-8")):
                cur.execute(stmt)
            cur.execute(
                "INSERT INTO schema_migrations(filename, applied_at) VALUES (?, ?)",
                (f.name, datetime.utcnow().isoformat()),
            )
            cur.execute("COMMIT")
            print("OK   :", f.name)
        except Exception as e:  # noqa: BLE001
            cur.execute("ROLLBACK")
            print(f"ECHEC: {f.name} -> {e}  (ROLLBACK, rien applique pour ce fichier)")
            return 1

    print("Toutes les migrations en attente ont ete appliquees.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
