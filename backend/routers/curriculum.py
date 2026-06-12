"""Lecture du référentiel curriculum pour le frontend (matières + niveaux).

Lecture seule. Source de vérité = les tables cycles/niveaux/matieres/matiere_niveaux.
Ne renvoie que les niveaux UTILISABLES (au moins une paire active) → un cycle sans
programme (Crèche, Supérieur) ou un niveau sans matière n'apparaît pas.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models_db import Cycle, Niveau, Matiere, MatiereNiveau

router = APIRouter()


@router.get("/curriculum")
def get_curriculum(db: Session = Depends(get_db)):
    matieres = [
        {"id": m.id, "cle": m.cle, "nom": m.nom}
        for m in db.query(Matiere).filter(Matiere.actif == True)
                   .order_by(Matiere.ordre).all()
    ]

    niveau_ids_utiles = {
        row[0]
        for row in db.query(MatiereNiveau.niveau_id)
                     .filter(MatiereNiveau.actif == True).distinct().all()
    }

    niveaux_par_cycle = []
    for c in db.query(Cycle).order_by(Cycle.ordre).all():
        nivs = [
            {"id": n.id, "nom": n.nom}
            for n in db.query(Niveau).filter(Niveau.cycle_id == c.id)
                       .order_by(Niveau.ordre).all()
            if n.id in niveau_ids_utiles
        ]
        if nivs:
            niveaux_par_cycle.append({"cycle": c.nom, "niveaux": nivs})

    return {"matieres": matieres, "niveaux_par_cycle": niveaux_par_cycle}
