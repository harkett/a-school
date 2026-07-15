# Carte visuelle de la base aSchool - lanceur.
# Usage habituel (depuis D:\A-SCHOOL\Scripts, venv actif) :  .\carte.ps1
# Regenere la carte depuis la base REELLE et l'ouvre dans Edge.
# Ne deploie rien, ne touche pas la PROD.
# $args transmis a carte.py (ex. .\carte.ps1 --no-open = regenere sans ouvrir Edge)
# Le depot = le dossier parent de ce script (Scripts/ -> racine du depot).
$root = Split-Path -Parent $PSScriptRoot
& "$root\.venv\Scripts\python.exe" "$root\outils_bdd\carte_base\carte.py" @args
