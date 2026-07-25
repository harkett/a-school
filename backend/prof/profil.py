import re
import unicodedata
from pathlib import Path

from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.core.database import get_db
from backend.core.models_db import Cycle, Matiere, MatiereNiveau, Niveau, Referentiel, User
from backend.core.resolution_couple import matiere_id_du_nom, niveau_id_du_nom

router = APIRouter()

# Dossier des référentiels déposés — même convention de rangement que le dépôt admin
# (REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf). `_dossier_cle` réplique la règle de nommage
# (accents ôtés, MAJUSCULES) — identique à referentiels_admin/pgvector_store, gardée LOCALE ici
# pour ne pas coupler le routeur du profil au module RAG (même choix que pgvector_store).
_ROOT = Path(__file__).resolve().parents[2]
REFERENTIELS_DIR = _ROOT / "REFERENTIELS"


def _dossier_cle(nom: str) -> str:
    s = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()
    return s or "REFERENTIEL"


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
    user.prenom     = body.prenom    or None
    user.nom        = body.nom       or None
    user.subject    = body.subject   or None
    user.subject_id = matiere_id_du_nom(db, body.subject or None)   # RÈGLE 4 : la CLÉ posée en plus du texte (double écriture, transition)
    user.niveau     = body.niveau    or None
    user.niveau_id  = niveau_id_du_nom(db, body.niveau or None)
    user.langue_lv  = body.langue_lv or None
    user.mobile     = body.mobile    or None
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
        user.travail_matiere_id = None
        user.travail_niveau_id = None
    else:
        user.travail_matiere = matiere
        user.travail_niveau = niveau
        user.travail_matiere_id = matiere_id_du_nom(db, matiere)   # RÈGLE 4 : la CLÉ posée en plus du texte (double écriture, transition)
        user.travail_niveau_id = niveau_id_du_nom(db, niveau)
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
    user.travail_matiere_id = None
    user.travail_niveau_id = None
    db.commit()
    tm, tn, ajuste = couple_de_travail(user)
    return {"status": "ok", "travail_matiere": tm, "travail_niveau": tn, "couple_ajuste": ajuste}


# ── Programme officiel du prof : voir, depuis son profil, le référentiel déposé par l'admin ──
#    LECTURE SEULE (le prof consulte, il n'écrit rien → aucun Valider/Annuler). Zéro nouvelle
#    donnée : le nom EXACT déposé vit déjà en base (referentiels.fichier) et le PDF sur disque.

def _referentiel_du_profil(db: Session, user: User) -> Referentiel | None:
    """Le référentiel officiel du NIVEAU de profil du prof (matiere_id NULL), lu PAR SA CLÉ
    (users.niveau_id → referentiels.niveau_id). La clé lève toute ambiguïté — un niveau = une
    ligne — donc plus de correspondance par nom ni de garde « len == 1 » (fini le bidouillage).
    None si le prof n'a pas de niveau (niveau_id NULL) ou si ce niveau n'a pas de référentiel :
    la carte du profil affiche alors « indisponible »."""
    if not user.niveau_id:
        return None
    return (db.query(Referentiel)
              .filter(Referentiel.niveau_id == user.niveau_id, Referentiel.matiere_id.is_(None))
              .first())


@router.get("/user/referentiel")
def get_mon_referentiel(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """Le programme officiel du niveau du prof : { disponible, fichier }. `fichier` = le NOM EXACT
    du document déposé par l'admin (colonne referentiels.fichier, get — pas le nom de disque figé
    « referentiel.pdf »). disponible=false s'il n'y a pas encore de référentiel pour son niveau."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    ref = _referentiel_du_profil(db, user)
    if ref is None:
        return {"disponible": False, "fichier": None}
    return {"disponible": True, "fichier": ref.fichier or "referentiel.pdf"}


@router.get("/user/referentiel/texte")
def get_mon_referentiel_texte(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """Le programme du niveau du prof en TEXTE PROPRE — get pur de `referentiels.texte_epure`, la
    version épurée/lisible déjà figée au dépôt (rag.extraction), PAS le PDF brut. VERROUILLÉ sur SON
    niveau (couple résolu en base, l'écran n'envoie aucun identifiant). 404 humain si rien à montrer."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    ref = _referentiel_du_profil(db, user)
    if ref is None or not (ref.texte_epure or "").strip():
        raise HTTPException(404, "Aucun programme officiel n'est disponible pour votre niveau.")
    return {"texte": ref.texte_epure}
