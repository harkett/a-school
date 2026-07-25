"""Résolution NOM → ID du couple du prof (matière, niveau) — une seule règle, un seul endroit.

Le profil range désormais matière et niveau par CLÉ (users.subject_id / niveau_id / travail_*_id).
Tant que les colonnes texte existent (transition RÈGLE 4), les ÉCRITURES posent la clé EN PLUS du
texte (« double écriture ») pour que la clé reste toujours fraîche. La règle unique ci-dessous :
un nom → son id SEULEMENT s'il correspond à EXACTEMENT un enregistrement — sinon None : on ne
devine jamais un id ambigu (même règle que le backfill de la migration bb88cc99dd00)."""
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
