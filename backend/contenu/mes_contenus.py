"""« Mes contenus » — le monde NEUF du prof (modèle playlist : séquence ⊃ séances ⊃ activités).

DÉCISION utilisateur (29/07) : ce monde est le futur REMPLAÇANT de Mes outils. Il ne lit et
n'écrit QUE ses tables neuves (`sequences`, `seances`, `seance_phases`, `activites`,
`activite_versions`). L'ancien monde (`activites_sauvegardees`, `sequences_sauvegardees`)
ne s'affiche JAMAIS ici — il vit sa vie dans Mes outils jusqu'à sa suppression finale, et
ne sert que de modèle de code.

L'activité applique la règle 0 NATIVEMENT : écrite en base à la génération même (POST à la
première, PUT aux suivantes), chaque jalon fige une version restaurable (`activite_versions`)
— l'historique s'empile, on n'écrase jamais.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.core.models_db import Activite, ActiviteVersion, Seance, Sequence, User
from backend.prof.profil import couple_de_travail

router = APIRouter()


def _iso(dt: datetime | None) -> str | None:
    return dt.replace(tzinfo=timezone.utc).isoformat() if dt else None


@router.get("/mes-contenus")
def lister(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sequences = db.query(Sequence).filter(Sequence.user_id == user.id).all()
    seances = db.query(Seance).filter(Seance.user_id == user.id).all()
    activites = db.query(Activite).filter(Activite.user_id == user.id).all()

    titres_sequences = {s.id: s.titre for s in sequences}
    titres_seances = {s.id: s.titre for s in seances}
    nb_seances_par_sequence: dict[int, int] = {}
    for s in seances:
        if s.sequence_id is not None:
            nb_seances_par_sequence[s.sequence_id] = nb_seances_par_sequence.get(s.sequence_id, 0) + 1

    contenus = []
    for s in sequences:
        contenus.append({
            "type": "sequence",
            "id": s.id,
            "titre": s.titre,
            "matiere": s.matiere,
            "niveau": s.niveau,
            "parent": None,                       # une séquence est le sommet : jamais rangée
            "nb_seances": nb_seances_par_sequence.get(s.id, 0),
            "resultat": None,
            "created_at": _iso(s.created_at),
            "updated_at": _iso(s.updated_at),
        })
    for s in seances:
        parent = None
        if s.sequence_id is not None:
            parent = {"type": "sequence", "id": s.sequence_id,
                      "titre": titres_sequences.get(s.sequence_id, "")}
        contenus.append({
            "type": "seance",
            "id": s.id,
            "titre": s.titre,
            "matiere": s.matiere,
            "niveau": s.niveau,
            "parent": parent,
            "nb_seances": None,
            "duree": s.duree_minutes,
            "mode": None,
            "contexte": s.description,
            "resultat": s.resultat,
            "created_at": _iso(s.created_at),
            "updated_at": _iso(s.updated_at),
        })
    for a in activites:
        parent = None
        if a.seance_id is not None:
            parent = {"type": "seance", "id": a.seance_id,
                      "titre": titres_seances.get(a.seance_id, "")}
        contenus.append({
            "type": "activite",
            "id": a.id,
            "titre": a.objet or a.activite_label,
            "matiere": a.matiere,
            "niveau": a.niveau,
            "parent": parent,
            "nb_seances": None,
            "resultat": a.resultat,
            # De quoi ROUVRIR l'activité dans son écran (reprise complète) :
            "activite_type_id": a.activite_type_id,
            "activite_label": a.activite_label,
            "sous_type": a.sous_type,
            "nb": a.nb,
            "avec_correction": a.avec_correction,
            "objet": a.objet,
            "ton": a.ton,
            "texte_source": a.texte_source,
            "statut": a.statut,
            "created_at": _iso(a.created_at),
            "updated_at": _iso(a.updated_at),
        })

    # Plus récent en haut, tous types mélangés (dernière modification, sinon création).
    contenus.sort(key=lambda c: c["updated_at"] or c["created_at"] or "", reverse=True)

    return {
        "contenus": contenus,
        "compteurs": {
            "tout": len(contenus),
            "sequences": len(sequences),
            "seances": len(seances),
            "activites": len(activites),
        },
    }


# ---------------------------------------------------------------------------
# Activités du monde neuf — auto-save règle 0 (POST = 1re génération, PUT = jalons suivants)
# ---------------------------------------------------------------------------

class ActiviteCorps(BaseModel):
    activite_type_id: int
    activite_label: str
    sous_type: Optional[str] = None
    nb: Optional[int] = None
    avec_correction: bool = False
    objet: Optional[str] = None
    ton: Optional[str] = None
    texte_source: str
    resultat: str


def _activite_de(user: User, activite_id: int, db: Session) -> Activite:
    activite = (
        db.query(Activite)
        .filter(Activite.id == activite_id, Activite.user_id == user.id)
        .first()
    )
    if not activite:
        raise HTTPException(404, "Activité introuvable.")
    return activite


@router.post("/contenus/activites")
def creer_activite(
    corps: ActiviteCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Première génération = l'activité NAÎT en base (auto-save, règle 0) + version 'generation'.
    Le couple matière/niveau est lu EN BASE (couple de travail), jamais envoyé par l'écran."""
    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")
    activite = Activite(
        user_id=user.id,
        activite_type_id=corps.activite_type_id,
        activite_label=corps.activite_label,
        sous_type=corps.sous_type,
        nb=corps.nb,
        avec_correction=corps.avec_correction,
        objet=corps.objet or None,
        matiere=matiere or None,
        niveau=niveau,
        ton=corps.ton,
        texte_source=corps.texte_source,
        resultat=corps.resultat,
    )
    db.add(activite)
    db.flush()
    db.add(ActiviteVersion(activite_id=activite.id, jalon="generation",
                           ton=corps.ton, resultat=corps.resultat))
    db.commit()
    return {"id": activite.id}


@router.put("/contenus/activites/{activite_id}")
def regenerer_activite(
    activite_id: int,
    corps: ActiviteCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Jalon suivant (régénération, changement de ton/texte) : l'ÉTAT COURANT est mis à jour
    et une NOUVELLE version s'empile — on n'écrase jamais une version (règle 0)."""
    activite = _activite_de(user, activite_id, db)
    activite.activite_type_id = corps.activite_type_id
    activite.activite_label = corps.activite_label
    activite.sous_type = corps.sous_type
    activite.nb = corps.nb
    activite.avec_correction = corps.avec_correction
    activite.objet = corps.objet or None
    activite.ton = corps.ton
    activite.texte_source = corps.texte_source
    activite.resultat = corps.resultat
    db.add(ActiviteVersion(activite_id=activite.id, jalon="generation",
                           ton=corps.ton, resultat=corps.resultat))
    db.commit()
    return {"ok": True, "id": activite.id}
