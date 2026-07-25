from fastapi import APIRouter, Cookie, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.core.database import get_db
from backend.core.models_db import Matiere, MatiereNiveau, Niveau, User

router = APIRouter()


def couple_de_travail(user: User) -> tuple[str | None, str | None, bool]:
    """Le couple sur lequel le prof TRAVAILLE, résolu depuis la base — LA seule règle,
    à UN seul endroit : le couple de travail s'il est posé (les deux colonnes non NULL),
    sinon le couple du profil. Renvoie (matiere, niveau, ajuste) ; ajuste=True quand le
    prof travaille hors de son profil. Lu par /auth/me (affichage) ET par les actions
    (génération, idée, exemple) — jamais recopié."""
    if user.travail_matiere and user.travail_niveau:
        return user.travail_matiere, user.travail_niveau, True
    return user.subject, user.niveau, False


def _couple_est_au_programme(db: Session, matiere: str, niveau: str) -> bool:
    """La paire (matière, niveau) existe-t-elle dans le programme officiel ? Lue sur
    `matiere_niveaux` (paires actives, matière active) par les NOMS — la même convention
    que le profil du prof (colonnes texte)."""
    return db.query(MatiereNiveau.id).join(Matiere, Matiere.id == MatiereNiveau.matiere_id) \
             .join(Niveau, Niveau.id == MatiereNiveau.niveau_id) \
             .filter(Matiere.nom == matiere, Niveau.nom == niveau,
                     MatiereNiveau.actif.is_(True), Matiere.actif.is_(True)) \
             .first() is not None


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


class ProfileBody(BaseModel):
    prenom: str = ""
    nom: str = ""
    subject: str = ""
    niveau: str = ""
    langue_lv: str = ""
    mobile: str = ""


@router.get("/user/profile")
def get_profile(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    return {
        "email":     user.email,
        "prenom":    user.prenom    or "",
        "nom":       user.nom       or "",
        "subject":   user.subject   or "",
        "niveau":    user.niveau    or "",
        "langue_lv": user.langue_lv or "",
        "mobile":    user.mobile    or "",
    }


@router.patch("/user/profile")
def update_profile(body: ProfileBody, aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    user.prenom    = body.prenom    or None
    user.nom       = body.nom       or None
    user.subject   = body.subject   or None
    user.niveau    = body.niveau    or None
    user.langue_lv = body.langue_lv or None
    user.mobile    = body.mobile    or None
    db.commit()
    return {"status": "ok"}


class CoupleTravailBody(BaseModel):
    matiere: str
    niveau: str


@router.put("/user/couple-travail")
def put_couple_travail(body: CoupleTravailBody, aschool_access: str = Cookie(default=None),
                       db: Session = Depends(get_db)):
    """Valider de « Changer niveau et/ou matière » = PUT : le couple de travail s'écrit EN BASE
    (il survit au rechargement de la page et à un changement d'appareil — c'est LUI que le
    serveur lit pour générer). Contrôle métier avant d'écrire : la paire doit exister au
    programme officiel. Choisir son propre couple de profil = revenir au profil (efface
    l'écart, on ne stocke jamais une copie du profil)."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    matiere, niveau = body.matiere.strip(), body.niveau.strip()
    if not matiere or not niveau:
        raise HTTPException(400, "Choisissez un niveau et une matière avant de valider.")
    if not _couple_est_au_programme(db, matiere, niveau):
        raise HTTPException(400, "Cette matière n'est pas enseignée à ce niveau dans les programmes. Choisissez une matière proposée pour ce niveau.")
    if matiere == (user.subject or "") and niveau == (user.niveau or ""):
        user.travail_matiere = None   # même couple que le profil → aucun écart à stocker
        user.travail_niveau = None
    else:
        user.travail_matiere = matiere
        user.travail_niveau = niveau
    db.commit()
    tm, tn, ajuste = couple_de_travail(user)
    return {"status": "ok", "travail_matiere": tm, "travail_niveau": tn, "couple_ajuste": ajuste}


@router.put("/user/guide-creer-vu")
def put_guide_creer_vu(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """La visite guidée de l'écran Créer vient d'être terminée (ou passée) : on le note EN
    BASE pour ne plus la lancer automatiquement — sur cet appareil comme sur les autres.
    Idempotent : re-noter un guide déjà vu ne change rien."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    user.guide_creer_vu = True
    db.commit()
    return {"status": "ok", "guide_creer_vu": True}


@router.delete("/user/couple-travail")
def delete_couple_travail(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """« Revenir à mon profil » = effacement de l'écart : le couple de travail redevient
    celui du profil (les deux colonnes repassent à NULL). Aucun contrôle à faire : on
    supprime une donnée que seul son propriétaire référence."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    user.travail_matiere = None
    user.travail_niveau = None
    db.commit()
    tm, tn, ajuste = couple_de_travail(user)
    return {"status": "ok", "travail_matiere": tm, "travail_niveau": tn, "couple_ajuste": ajuste}
