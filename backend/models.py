from pydantic import BaseModel
from typing import Optional, List, Dict, Any


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
    chunks: Optional[List[Dict[str, Any]]] = None  # populated only when RAG used — V2: filtrer selon rôle utilisateur si corpus internes


class ExempleReferentielRequest(BaseModel):
    # Couple ACTIF affiché au prof (sélection courante, ajustement temporaire compris) —
    # pas le profil figé : l'exemple doit suivre ce que le prof voit à l'écran.
    matiere: str
    niveau: str


class ExempleReferentielResponse(BaseModel):
    available: bool          # False = pas de référentiel pour ce couple → on n'invente RIEN
    texte: Optional[str] = None
