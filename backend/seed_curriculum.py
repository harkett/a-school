"""Seed initial du curriculum : cycles, niveaux, matieres, matiere_niveaux.

Données de RÉFÉRENCE (programme officiel), éditables ensuite via le CRUD admin.
Idempotent : ne réinsère jamais ce qui existe déjà → relançable sans risque.

Crèche / Supérieur : cycles seedés, mais niveaux + paires LAISSÉS VIDES
(sources à arbitrer — TRACKER § Refonte curriculum, réserve 1). À remplir via le CRUD.
"""
from backend.database import SessionLocal
from backend.models_db import Cycle, Niveau, Matiere, MatiereNiveau

CYCLES = [
    ("Crèche", 1), ("Maternelle", 2), ("Primaire", 3),
    ("Collège", 4), ("Lycée", 5), ("Supérieur", 6),
]

NIVEAUX = {  # cycle -> [(nom, ordre)]
    "Maternelle": [("PS", 1), ("MS", 2), ("GS", 3)],
    "Primaire":   [("CP", 4), ("CE1", 5), ("CE2", 6), ("CM1", 7), ("CM2", 8)],
    "Collège":    [("6e", 9), ("5e", 10), ("4e", 11), ("3e", 12)],
    "Lycée":      [("2nde", 13), ("1ère", 14), ("Terminale", 15)],
}

MATIERES = [  # cle, nom, ordre
    ("francais", "Français", 1), ("mathematiques", "Mathématiques", 2),
    ("histoire-geo", "Histoire-Géo", 3), ("langues-vivantes", "Langues Vivantes", 4),
    ("physique-chimie", "Physique-Chimie", 5), ("svt", "SVT", 6),
    ("technologie", "Technologie", 7), ("nsi", "NSI", 8),
    ("ses", "SES", 9), ("philosophie", "Philosophie", 10),
    ("arts", "Arts", 11), ("eps", "EPS", 12),
]

# Programme : matiere_cle -> niveaux où elle est enseignée
PROGRAMME = {
    "francais":         ["6e", "5e", "4e", "3e", "2nde", "1ère"],            # pas "Français" en Term
    "mathematiques":    ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"],
    "histoire-geo":     ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"],
    "langues-vivantes": ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"],
    "physique-chimie":  ["5e", "4e", "3e", "2nde", "1ère", "Terminale"],     # démarre 5e
    "svt":              ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"],
    "technologie":      ["6e", "5e", "4e", "3e"],                            # collège seulement (lycée général : non)
    "nsi":              ["1ère", "Terminale"],                               # spécialité
    "ses":              ["2nde", "1ère", "Terminale"],
    "philosophie":      ["Terminale"],
    "arts":             ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"],
    "eps":              ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"],
}


def run():
    db = SessionLocal()

    cyc = {}
    for nom, ordre in CYCLES:
        c = db.query(Cycle).filter(Cycle.nom == nom).first()
        if not c:
            c = Cycle(nom=nom, ordre=ordre)
            db.add(c)
            db.flush()
        cyc[nom] = c

    niv = {}
    for cycle_nom, lst in NIVEAUX.items():
        for nom, ordre in lst:
            n = db.query(Niveau).filter(Niveau.nom == nom, Niveau.cycle_id == cyc[cycle_nom].id).first()
            if not n:
                n = Niveau(cycle_id=cyc[cycle_nom].id, nom=nom, ordre=ordre)
                db.add(n)
                db.flush()
            niv[nom] = n

    mat = {}
    for cle, nom, ordre in MATIERES:
        m = db.query(Matiere).filter(Matiere.cle == cle).first()
        if not m:
            m = Matiere(cle=cle, nom=nom, ordre=ordre)
            db.add(m)
            db.flush()
        mat[cle] = m

    pairs = 0
    for cle, niveaux in PROGRAMME.items():
        for nnom in niveaux:
            mn = db.query(MatiereNiveau).filter(
                MatiereNiveau.matiere_id == mat[cle].id,
                MatiereNiveau.niveau_id == niv[nnom].id,
            ).first()
            if not mn:
                db.add(MatiereNiveau(matiere_id=mat[cle].id, niveau_id=niv[nnom].id))
                pairs += 1
    db.commit()

    print("cycles=%d  niveaux=%d  matieres=%d  paires=%d (nouvelles: %d)" % (
        db.query(Cycle).count(), db.query(Niveau).count(),
        db.query(Matiere).count(), db.query(MatiereNiveau).count(), pairs))
    db.close()


if __name__ == "__main__":
    run()
