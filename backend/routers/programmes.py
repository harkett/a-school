"""Lecture du référentiel des programmes pour le frontend (matières + niveaux).

Lecture seule. Source de vérité = les tables cycles/niveaux/matieres/matiere_niveaux.
Ne renvoie que les niveaux UTILISABLES (au moins une paire active) → un cycle sans
programme (Crèche, Supérieur) ou un niveau sans matière n'apparaît pas.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models_db import Cycle, Niveau, Matiere, MatiereNiveau
from backend.routers.admin import _require_admin

router = APIRouter()


@router.get("/programmes")
def get_programmes(db: Session = Depends(get_db)):
    matiere_objs = (db.query(Matiere).filter(Matiere.actif == True)
                      .order_by(Matiere.ordre).all())
    matieres = [{"id": m.id, "nom": m.nom} for m in matiere_objs]
    matiere_ids_actifs = {m.id for m in matiere_objs}

    niveau_ids_utiles = {
        row[0]
        for row in db.query(MatiereNiveau.niveau_id)
                     .filter(MatiereNiveau.actif == True).distinct().all()
    }

    # Matières utilisables PAR CYCLE (paire active + matière active) → menu matière du profil,
    # scopé sur le cycle du niveau choisi.
    cycle_matiere_ids = {}
    for cycle_id, matiere_id in (
        db.query(Niveau.cycle_id, MatiereNiveau.matiere_id)
          .join(MatiereNiveau, MatiereNiveau.niveau_id == Niveau.id)
          .filter(MatiereNiveau.actif == True).distinct().all()
    ):
        if matiere_id in matiere_ids_actifs:
            cycle_matiere_ids.setdefault(cycle_id, set()).add(matiere_id)

    niveaux_par_cycle = []
    matieres_par_cycle = []
    for c in db.query(Cycle).order_by(Cycle.ordre).all():
        nivs = [
            {"id": n.id, "nom": n.nom, "traite": n.traite}
            for n in db.query(Niveau).filter(Niveau.cycle_id == c.id)
                       .order_by(Niveau.ordre).all()
            if n.id in niveau_ids_utiles
        ]
        if nivs:
            niveaux_par_cycle.append({"cycle": c.nom, "niveaux": nivs})

        ids = cycle_matiere_ids.get(c.id, set())
        mats = [{"id": m.id, "nom": m.nom} for m in matiere_objs if m.id in ids]
        if mats:
            matieres_par_cycle.append({"cycle": c.nom, "matieres": mats})

    # Matières PAR NIVEAU (scope fin = le programme du diplôme/niveau, via les paires).
    # C'est ce que lit le menu matière du profil : un niveau ne propose QUE ses matières
    # (deux diplômes d'un même cycle ont des matières différentes — ex. BTS CIEL ≠ Master).
    # Ordre = ordre d'insertion des paires (= ordre du référentiel au seed), stable car une
    # paire n'est jamais supprimée (désactivation seulement). Clé = nom du niveau (unique
    # dans le référentiel actuel).
    par_niveau = {}
    for niv_nom, mid, mnom in (
        db.query(Niveau.nom, Matiere.id, Matiere.nom)
          .join(MatiereNiveau, MatiereNiveau.niveau_id == Niveau.id)
          .join(Matiere, Matiere.id == MatiereNiveau.matiere_id)
          .filter(MatiereNiveau.actif == True, Matiere.actif == True)
          .order_by(MatiereNiveau.id).all()
    ):
        par_niveau.setdefault(niv_nom, []).append({"id": mid, "nom": mnom})
    matieres_par_niveau = [{"niveau": k, "matieres": v} for k, v in par_niveau.items()]

    return {
        "matieres": matieres,
        "niveaux_par_cycle": niveaux_par_cycle,
        "matieres_par_cycle": matieres_par_cycle,
        "matieres_par_niveau": matieres_par_niveau,
    }


@router.get("/matieres")
def get_matieres(db: Session = Depends(get_db)):
    """Toutes les matières actives présentes dans au moins un couple actif, dérivées de la
    base par jointure matieres⋈matiere_niveaux. Source unique = la base ; remplace les listes
    en dur du frontend. Public (Signup en a besoin)."""
    rows = (
        db.query(Matiere)
          .join(MatiereNiveau, MatiereNiveau.matiere_id == Matiere.id)
          .filter(
              Matiere.actif == True,
              MatiereNiveau.actif == True,
          )
          .order_by(Matiere.ordre)
          .distinct()
          .all()
    )
    return [{"nom": m.nom} for m in rows]


# ───────────────────────────────────────────────────────────────────────────
# Admin — édition des programmes (garde admin, JAMAIS de DELETE sur une
# entrée de référence : on bascule `actif`, l'historique reste valide).
# ───────────────────────────────────────────────────────────────────────────

@router.get("/admin/programmes", dependencies=[Depends(_require_admin)])
def admin_programmes(db: Session = Depends(get_db)):
    """Arbre COMPLET pour la grille admin : tous les cycles (même sans niveau),
    tous les niveaux, toutes les matières (INACTIVES incluses), toutes les paires."""
    cycles = []
    for c in db.query(Cycle).order_by(Cycle.ordre).all():
        niveaux = [
            {"id": n.id, "nom": n.nom, "ordre": n.ordre}
            for n in db.query(Niveau).filter(Niveau.cycle_id == c.id)
                       .order_by(Niveau.ordre).all()
        ]
        cycles.append({"id": c.id, "nom": c.nom, "ordre": c.ordre, "niveaux": niveaux})

    matieres = [
        {"id": m.id, "nom": m.nom, "ordre": m.ordre, "actif": m.actif}
        for m in db.query(Matiere).order_by(Matiere.ordre).all()
    ]
    paires = [
        {"matiere_id": p.matiere_id, "niveau_id": p.niveau_id, "actif": p.actif}
        for p in db.query(MatiereNiveau).all()
    ]
    return {"cycles": cycles, "matieres": matieres, "paires": paires}


class PaireUpdate(BaseModel):
    matiere_id: int
    niveau_id: int
    actif: bool


@router.patch("/admin/programmes/paire", dependencies=[Depends(_require_admin)])
def admin_toggle_paire(body: PaireUpdate, db: Session = Depends(get_db)):
    """Bascule une paire matière×niveau : crée si absente, sinon met à jour `actif`.
    JAMAIS de DELETE — une paire désactivée reste en base (historique préservé)."""
    if not db.get(Matiere, body.matiere_id):
        raise HTTPException(404, "Matière inconnue.")
    if not db.get(Niveau, body.niveau_id):
        raise HTTPException(404, "Niveau inconnu.")

    paire = db.query(MatiereNiveau).filter(
        MatiereNiveau.matiere_id == body.matiere_id,
        MatiereNiveau.niveau_id == body.niveau_id,
    ).first()
    if paire:
        paire.actif = body.actif
    else:
        db.add(MatiereNiveau(
            matiere_id=body.matiere_id, niveau_id=body.niveau_id, actif=body.actif,
        ))
    db.commit()
    return {"matiere_id": body.matiere_id, "niveau_id": body.niveau_id, "actif": body.actif}


class NiveauCreate(BaseModel):
    cycle_id: int
    nom: str
    ordre: int | None = None


@router.post("/admin/programmes/niveau", dependencies=[Depends(_require_admin)])
def admin_create_niveau(body: NiveauCreate, db: Session = Depends(get_db)):
    """Crée un niveau dans un cycle (débloque Supérieur / Crèche, sans programme officiel).
    Gardes : le cycle existe + pas de doublon de nom dans le même cycle."""
    nom = body.nom.strip()
    if not nom:
        raise HTTPException(400, "Le nom du niveau est requis.")
    if not db.get(Cycle, body.cycle_id):
        raise HTTPException(404, "Cycle inconnu.")
    if db.query(Niveau).filter(Niveau.cycle_id == body.cycle_id, Niveau.nom == nom).first():
        raise HTTPException(409, "Ce niveau existe déjà dans ce cycle.")

    if body.ordre is not None:
        ordre = body.ordre
    else:
        maxo = db.query(func.max(Niveau.ordre)).filter(Niveau.cycle_id == body.cycle_id).scalar()
        ordre = (maxo or 0) + 1

    niveau = Niveau(cycle_id=body.cycle_id, nom=nom, ordre=ordre)
    db.add(niveau)
    db.commit()
    db.refresh(niveau)
    return {"id": niveau.id, "cycle_id": niveau.cycle_id, "nom": niveau.nom, "ordre": niveau.ordre}
