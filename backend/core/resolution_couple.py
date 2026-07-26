"""Résolution NOM → ID du couple du prof (matière, niveau) — une seule règle, un seul endroit.

Le profil range matière et niveau UNIQUEMENT par CLÉ (users.subject_id / niveau_id / travail_*_id) :
le nom vit dans `matieres`/`niveaux` et se relit par get (zéro copie, RÈGLE 4). Deux sens ici :
nom → id à l'écriture (matiere_id_du_nom / niveau_id_du_nom : un nom → son id SEULEMENT s'il
correspond à EXACTEMENT un enregistrement, sinon None — on ne devine jamais un id ambigu) ;
id → nom à la lecture (matiere_nom_de_id / niveau_nom_de_id)."""
from sqlalchemy.orm import Session

from backend.core.models_db import Matiere, Niveau


def matiere_id_du_nom(db: Session, nom: str | None) -> int | None:
    """id de la matière dont le nom == `nom`, si et seulement s'il y en a exactement une ; sinon None."""
    if not nom:
        return None
    rows = db.query(Matiere.id).filter(Matiere.nom == nom).all()
    return rows[0][0] if len(rows) == 1 else None


def niveau_id_du_nom(db: Session, nom: str | None) -> int | None:
    """id du niveau dont le nom == `nom`, si et seulement s'il y en a exactement un ; sinon None."""
    if not nom:
        return None
    rows = db.query(Niveau.id).filter(Niveau.nom == nom).all()
    return rows[0][0] if len(rows) == 1 else None


def matiere_nom_de_id(db: Session, matiere_id: int | None) -> str | None:
    """Nom de la matière pour cet id — get pur (le nom vit dans `matieres`, jamais recopié)."""
    if not matiere_id:
        return None
    return db.query(Matiere.nom).filter(Matiere.id == matiere_id).scalar()


def niveau_nom_de_id(db: Session, niveau_id: int | None) -> str | None:
    """Nom du niveau pour cet id — get pur (le nom vit dans `niveaux`, jamais recopié)."""
    if not niveau_id:
        return None
    return db.query(Niveau.nom).filter(Niveau.id == niveau_id).scalar()
