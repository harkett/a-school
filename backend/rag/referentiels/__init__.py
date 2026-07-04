"""Fiches de réglages des référentiels — une fiche par référentiel (ou par famille de mise en page).

Le moteur RAG (client, embeddings, chunker, retrieve) ne connaît aucun référentiel.
Chaque fiche de ce package apporte SES réglages : comment extraire le PDF, comment découper,
comment taguer les chunks. CIEL est la première fiche ; la crèche est la deuxième et sert ses
TROIS couples (Bébés, Moyens, Grands), qui partagent le même document.

Le registre `FICHES` fait le lien COLLECTION -> fiche. C'est le pointeur data-driven (embryon du
registre « couple -> méthode » de la tâche D57) : plusieurs collections peuvent viser la même fiche.
"""
from . import bts_ciel_option_a, creche_0_3_ans

FICHES = {
    "bts_ciel_option_a": bts_ciel_option_a,
    "bebes_0_1_an": creche_0_3_ans,
    "moyens_1_2_ans": creche_0_3_ans,
    "grands_2_3_ans": creche_0_3_ans,
}


def get_fiche(collection: str):
    """Fiche (méthode d'extraction + découpe) d'une collection. Lève si inconnue :
    on ne devine pas une méthode d'extraction, on la déclare dans le registre."""
    fiche = FICHES.get(collection)
    if fiche is None:
        raise RuntimeError(
            f"Aucune fiche d'extraction pour collection='{collection}'. "
            f"Déclarer la fiche dans backend/rag/referentiels/__init__.py (FICHES)."
        )
    return fiche
