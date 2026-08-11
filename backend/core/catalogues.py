"""Lecture des CATALOGUES de référence (modes de séance, styles, critères d'ambiguïté…).

Toutes ces tables partagent le même moule — `code` / `label` / `ordre` / `actif` — et la même
règle : les valeurs initiales sont SEMÉES PAR MIGRATION, jamais écrites dans le code. Le
lecteur vivait dans `contenu/mes_contenus.py` tant qu'un seul monde s'en servait ; il est ici
depuis que l'analyse d'ambiguïtés lit son propre catalogue, pour qu'il n'en existe pas deux
copies avec deux messages d'erreur différents.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session


def catalogue(db: Session, modele, quoi: str) -> list:
    """Un catalogue de référence, lu EN BASE — jamais une liste en dur. Les valeurs initiales
    sont SEMÉES par migration : une table vide n'est pas un cas à rattraper en douce, c'est
    une erreur qu'on dit (même geste que `_reglage_entier`)."""
    lignes = db.query(modele).filter(modele.actif.is_(True)).order_by(modele.ordre, modele.id).all()
    if not lignes:
        raise HTTPException(500, f"Catalogue « {quoi} » vide en base (migration non appliquée ?).")
    return lignes
