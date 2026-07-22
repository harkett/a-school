from pydantic import BaseModel
from typing import Optional


class GenerateRequest(BaseModel):
    texte: str
    activite_type_id: int
    niveau: str
    sous_type: Optional[str] = None
    nb: Optional[int] = None
    avec_correction: bool = False
    langue_lv: Optional[str] = None


class GenerateResponse(BaseModel):
    resultat: str


class ExempleReferentielRequest(BaseModel):
    # Couple ACTIF affiché au prof (sélection courante, ajustement temporaire compris) —
    # pas le profil figé : l'exemple doit suivre ce que le prof voit à l'écran.
    matiere: str
    niveau: str


class ExempleReferentielResponse(BaseModel):
    available: bool          # False = pas de référentiel pour ce couple → on n'invente RIEN
    texte: Optional[str] = None
    message: Optional[str] = None  # message honnête au prof quand rien d'assez pertinent (seuil) — affiché en modale
