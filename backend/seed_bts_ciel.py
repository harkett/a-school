"""Seed du cas-test BTS CIEL option A — PREMIER cas de la procédure « référentiel → matières ».

Source = référentiel officiel éduscol STI (BTS CIEL, rénovation rentrée 2023) :
grille horaire (p.81, enseignements) + blocs de compétences option A (p.29).
Le RÉFÉRENTIEL fait foi sur les libellés. Idempotent : relançable sans risque.

Procédure répétable (à généraliser ensuite à tout BTS, puis aux autres cycles) :
  1 référentiel officiel → 1 NIVEAU (le diplôme/option) dans son cycle
                         + ses MATIÈRES + ses PAIRES matière×niveau.

Lancer (depuis la racine du projet, dans le venv) :  python -m backend.seed_bts_ciel
"""
from sqlalchemy import func

from backend.database import SessionLocal
from backend.models_db import Cycle, Niveau, Matiere, MatiereNiveau

CYCLE = "Supérieur"            # le niveau s'y rattache (déjà seedé par seed_programmes)
NIVEAU = "BTS CIEL option A"   # = le diplôme + option (l'unité de la procédure)

# Matières du BTS CIEL option A — libellés EXACTS du référentiel officiel. (cle, nom, ordre)
# « mathematiques » est RÉUTILISÉE (déjà en base) : le get-or-create par clé la retrouve.
MATIERES = [
    # 4 générales (grille horaire p.81)
    ("culture-generale-expression", "Culture générale et expression", 29),
    ("anglais",                     "Anglais",                        30),
    ("mathematiques",               "Mathématiques",                   2),  # réutilisée
    ("physique",                    "Physique",                       31),
    # 5 professionnelles (cœur option A — blocs de compétences p.29)
    ("informatique",                "Informatique",                   32),
    ("reseaux",                     "Réseaux",                        33),
    ("cybersecurite",               "Cybersécurité",                  34),
    ("developpement",               "Développement",                  35),
    ("maintenance",                 "Maintenance",                    36),
]


def run():
    db = SessionLocal()
    try:
        cycle = db.query(Cycle).filter(Cycle.nom == CYCLE).first()
        if not cycle:
            raise SystemExit(
                f"Cycle « {CYCLE} » absent — lancer d'abord `python -m backend.seed_programmes`."
            )

        # 1. Le niveau (le diplôme/option) — créé si absent, ordre = suite du cycle.
        niveau = (db.query(Niveau)
                    .filter(Niveau.nom == NIVEAU, Niveau.cycle_id == cycle.id).first())
        niveau_cree = False
        if not niveau:
            maxo = db.query(func.max(Niveau.ordre)).filter(Niveau.cycle_id == cycle.id).scalar()
            niveau = Niveau(cycle_id=cycle.id, nom=NIVEAU, ordre=(maxo or 0) + 1, traite=True)
            db.add(niveau)
            db.flush()
            niveau_cree = True
        elif not niveau.traite:
            niveau.traite = True   # niveau traité (vrai référentiel posé) → sélectionnable au profil

        # 2. Les matières — get-or-create par clé (libellé du référentiel ; existantes intactes).
        mats, mat_creees, mat_reutilisees = {}, 0, 0
        for cle, nom, ordre in MATIERES:
            m = db.query(Matiere).filter(Matiere.cle == cle).first()
            if not m:
                m = Matiere(cle=cle, nom=nom, ordre=ordre)
                db.add(m)
                db.flush()
                mat_creees += 1
            else:
                mat_reutilisees += 1
            mats[cle] = m

        # 3. Les paires matière×niveau (le « programme officiel » du diplôme).
        paires = 0
        for cle, _, _ in MATIERES:
            mn = (db.query(MatiereNiveau)
                    .filter(MatiereNiveau.matiere_id == mats[cle].id,
                            MatiereNiveau.niveau_id == niveau.id).first())
            if not mn:
                db.add(MatiereNiveau(matiere_id=mats[cle].id, niveau_id=niveau.id))
                paires += 1

        db.commit()

        print(f"Niveau « {NIVEAU} » (cycle {CYCLE}) : "
              f"{'créé' if niveau_cree else 'déjà présent'} (id={niveau.id})")
        print(f"Matières : {mat_creees} créées, {mat_reutilisees} réutilisées "
              f"(sur {len(MATIERES)} attendues)")
        print(f"Paires matière×niveau : {paires} nouvelles "
              f"(total pour ce niveau : "
              f"{db.query(MatiereNiveau).filter(MatiereNiveau.niveau_id == niveau.id).count()})")
    finally:
        db.close()


if __name__ == "__main__":
    run()
