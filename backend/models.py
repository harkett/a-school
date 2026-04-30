from pydantic import BaseModel
from typing import Optional


class GenerateRequest(BaseModel):
    texte: str
    activite_key: str
    niveau: str
    sous_type: Optional[str] = None
    nb: Optional[int] = None
    avec_correction: bool = False
    langue_lv: Optional[str] = None


class GenerateResponse(BaseModel):
    resultat: str
