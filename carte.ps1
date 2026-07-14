# Carte visuelle de la base aSchool - lanceur.
# Usage habituel (depuis D:\A-SCHOOL, venv actif) :  .\carte.ps1
# Regenere la carte depuis la base REELLE et l'ouvre dans Edge.
# Ne deploie rien, ne touche pas la PROD.
# $args transmis a carte.py (ex. .\carte.ps1 --no-open = regenere sans ouvrir Edge)
& "D:\A-SCHOOL\.venv\Scripts\python.exe" "D:\A-SCHOOL\outils_bdd\carte_base\carte.py" @args
