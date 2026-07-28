from pydantic import BaseModel
from typing import Optional


# Décision du 25/07 : l'écran n'envoie PLUS matière/niveau — le serveur lit le couple de
# TRAVAIL du prof EN BASE (users.travail_matiere_id/travail_niveau_id, sinon le profil) au
# moment de chaque action. Une donnée, une place : le couple affiché EST le couple généré.
class GenerateRequest(BaseModel):
    texte: str
    activite_type_id: int
    sous_type: Optional[str] = None
    nb: Optional[int] = None
    avec_correction: bool = False
    # Ton de rédaction choisi PAR LE BOUTON de génération : 'academique' | 'operationnel'.
    # Absent (None) = aucune couche de style ajoutée (rétrocompatible).
    ton: Optional[str] = None


class GenerateResponse(BaseModel):
    resultat: str


class ProposerIdeeRequest(BaseModel):
    # Ce que le prof a DÉJÀ choisi à l'écran : le type d'activité (id) et la précision
    # éventuelle — le couple, lui, est lu EN BASE. L'idée proposée s'écrit DANS la zone
    # texte — elle ne remplace jamais la demande du prof, elle l'amorce.
    activite_type_id: int
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
