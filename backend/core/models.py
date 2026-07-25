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


class ProposerIdeeRequest(BaseModel):
    # Ce que le prof a DÉJÀ choisi à l'écran : le type d'activité (id), le niveau actif
    # (ajustement temporaire compris) et la précision éventuelle. L'idée proposée s'écrit
    # DANS la zone texte — elle ne remplace jamais la demande du prof, elle l'amorce.
    activite_type_id: int
    niveau: str
    sous_type: Optional[str] = None


class ProposerIdeeResponse(BaseModel):
    available: bool          # False = pas de référentiel ou rien d'assez pertinent → on n'invente RIEN
    texte: Optional[str] = None
    objet: Optional[str] = None    # titre court pour le champ « Objet » (ligne « Objet : » de l'IA) — None si absent
    message: Optional[str] = None  # message honnête au prof (seuil) — affiché en modale


class ExempleReferentielResponse(BaseModel):
    available: bool          # False = pas de référentiel pour ce couple → on n'invente RIEN
    texte: Optional[str] = None
    message: Optional[str] = None  # message honnête au prof quand rien d'assez pertinent (seuil) — affiché en modale
