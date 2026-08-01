"""Résolution NOM → ID du couple du prof (matière, niveau) — une seule règle, un seul endroit.

Le profil range matière et niveau UNIQUEMENT par CLÉ (users.subject_id / niveau_id / travail_*_id) :
le nom vit dans `matieres`/`niveaux` et se relit par get (zéro copie, RÈGLE 4). Deux sens ici :
nom → id à l'écriture, id → nom à la lecture (matiere_nom_de_id / niveau_nom_de_id).

UNE MATIÈRE SE RÉSOUT DANS UN RÉFÉRENTIEL, JAMAIS GLOBALEMENT. Depuis que chaque référentiel
possède ses matières, plusieurs « Mathématiques » coexistent en base — une par diplôme qui en
nomme une. Chercher par le nom seul ne pouvait donc plus rendre qu'un doublon ambigu, c'est-à-dire
rien. `matiere_id_du_nom` demande le NIVEAU : il donne le référentiel, le référentiel donne SA
matière. Le niveau, lui, reste unique par son nom (cf. `niveau_id_du_nom`).
"""
from sqlalchemy.orm import Session

from backend.core.models_db import Matiere, Niveau, Referentiel


def matiere_id_du_nom(db: Session, nom: str | None, niveau_id: int | None) -> int | None:
    """id de LA matière de ce nom DANS le référentiel de ce niveau, sinon None.

    None si le nom ou le niveau manque, si le niveau n'a pas de référentiel, ou si son
    référentiel ne nomme pas cette matière. Seules les matières RETENUES par l'admin (`validee`)
    et actives sont résolues : une proposition de la détection n'entre jamais dans un profil.
    L'unicité (referentiel_id, nom) garantit qu'il n'y a jamais deux réponses possibles."""
    if not nom or not niveau_id:
        return None
    return (db.query(Matiere.id)
              .join(Referentiel, Referentiel.id == Matiere.referentiel_id)
              .filter(Referentiel.niveau_id == niveau_id,
                      Matiere.nom == nom,
                      Matiere.validee.is_(True),
                      Matiere.actif.is_(True))
              .scalar())


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
