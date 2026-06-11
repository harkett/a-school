# Migrations — discipline de schéma

> Mise en place le 11/06/2026 pour le chantier `user_email → user_id`. Avant, aucune
> discipline de migration n'existait (schéma créé par `create_all`).

## Principe

- Chaque changement de schéma/données est un **fichier SQL numéroté** : `NNN_description.sql`
  (`001_`, `002_`, …), appliqué **dans l'ordre**.
- Chaque fichier doit être **idempotent** quand c'est possible (`IF NOT EXISTS`, etc.) :
  le relancer ne casse rien.
- Le runner applique chaque fichier **dans une transaction** (`BEGIN … COMMIT`,
  `ROLLBACK` si erreur) — donc **tout ou rien**, jamais à moitié.
- L'état est suivi dans la table **`schema_migrations`** (`filename`, `applied_at`) :
  un fichier déjà appliqué n'est jamais rejoué.

## Règles d'écriture des fichiers `.sql`

- Statements séparés par `;`.
- Commentaires uniquement en **lignes `--`** (pas de `/* … */`).
- Pas de `;` à l'intérieur d'une chaîne (le découpage est simple, volontairement).

## Usage

```powershell
# Voir ce qui serait appliqué, sans rien faire :
.\.venv\Scripts\python.exe migrations\run_migrations.py --db data\aschool.db --dry-run

# Appliquer (TOUJOURS sur une COPIE d'abord pendant le chantier) :
.\.venv\Scripts\python.exe migrations\run_migrations.py --db data\aschool_copie.db
```

## Règle d'or du chantier

On déroule **d'abord sur une copie** (`data\aschool_copie.db`), on vérifie les chiffres,
**puis** seulement sur la vraie base — et jamais sans GO explicite.
