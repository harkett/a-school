from fastapi import APIRouter, HTTPException
from src.activities import ACTIVITES_PAR_MATIERE

router = APIRouter()


@router.get("/activites/{matiere}")
def get_activites(matiere: str):
    if matiere not in ACTIVITES_PAR_MATIERE:
        raise HTTPException(status_code=404, detail=f"Matière inconnue : {matiere}")
    data = ACTIVITES_PAR_MATIERE[matiere]
    return [
        {
            "label": label,
            "key": cfg["key"],
            "sous_types": cfg["sous_types"],
            "params": cfg["params"],
        }
        for label, cfg in data.items()
    ]
