from fastapi import APIRouter

from src.activities import ACTIVITES_PAR_MATIERE, ACTIVITES_GENERIQUES

router = APIRouter()


@router.get("/activites/{matiere}")
def get_activites(matiere: str):
    # Matière du catalogue → ses activités propres. Sinon (matières hors catalogue, ex.
    # BTS CIEL : Réseaux, Cybersécurité…) → repli générique, pour ne JAMAIS bloquer le prof
    # avec 0 type. On ne renvoie plus de 404 : le front recevait l'objet d'erreur à la place
    # d'un tableau → crash `activites.find`.
    data = ACTIVITES_PAR_MATIERE.get(matiere, ACTIVITES_GENERIQUES)
    return [
        {
            "label": label,
            "key": cfg["key"],
            "sous_types": cfg["sous_types"],
            "params": cfg["params"],
        }
        for label, cfg in data.items()
    ]
