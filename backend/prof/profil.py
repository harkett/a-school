import unicodedata
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Cookie, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.core.database import get_db
from backend.core.models_db import CahierProf, Cycle, Matiere, MatiereNiveau, Niveau, Referentiel, User
from backend.core.nommage import dossier_cle as _dossier_cle
from backend.core.resolution_couple import matiere_id_du_nom, matiere_nom_de_id, niveau_id_du_nom, niveau_nom_de_id

router = APIRouter()

# Dossier des référentiels déposés — même convention de rangement que le dépôt admin
# (REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf). La règle de nommage vient de
# `backend.core.nommage` : module neutre (aucune dépendance), donc l'importer ne couple
# toujours pas le routeur du profil au module RAG — et la règle n'a plus qu'une seule source.
_ROOT = Path(__file__).resolve().parents[2]
REFERENTIELS_DIR = _ROOT / "REFERENTIELS"
# Cahier des charges depose par le PROF (1 PDF/prof) : hors depot (data/ est gitignore), persiste
# sur le serveur. Nom de disque fixe (cahier.pdf) par dossier prop, comme le referentiel admin.
UPLOADS_CAHIERS_DIR = _ROOT / "data" / "uploads" / "cahiers"


def couple_de_travail(db: Session, user: User) -> tuple[str | None, str | None, bool]:
    """Le couple sur lequel le prof TRAVAILLE, résolu depuis la base — LA seule règle,
    à UN seul endroit : le couple de travail s'il est posé (les deux clés non NULL),
    sinon le couple du profil. Renvoie (matiere, niveau, ajuste) ; ajuste=True quand le
    prof travaille hors de son profil. Le nom se relit par get sur `matieres`/`niveaux`
    (zéro copie). Lu par /auth/me ET par les actions (génération, idée, exemple)."""
    if user.travail_matiere_id and user.travail_niveau_id:
        return matiere_nom_de_id(db, user.travail_matiere_id), niveau_nom_de_id(db, user.travail_niveau_id), True
    return matiere_nom_de_id(db, user.subject_id), niveau_nom_de_id(db, user.niveau_id), False


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
        "subject":   matiere_nom_de_id(db, user.subject_id) or "",
        "niveau":    niveau_nom_de_id(db, user.niveau_id) or "",
        "langue_lv": user.langue_lv or "",
        "mobile":    user.mobile    or "",
    }


@router.patch("/user/profile")
def update_profile(body: ProfileBody, aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    # Contrôle métier AVANT d'écrire — même règle que « Changer niveau et/ou matière » :
    # une paire complète doit exister au programme officiel, le front seul ne suffit pas.
    # Un profil encore incomplet (matière OU niveau vide) reste enregistrable tel quel.
    matiere, niveau = (body.subject or "").strip(), (body.niveau or "").strip()
    if matiere and niveau and not _couple_est_au_programme(db, matiere, niveau):
        raise HTTPException(400, "Cette matière n'est pas enseignée à ce niveau dans les programmes. Choisissez une matière proposée pour ce niveau.")
    user.prenom     = body.prenom    or None
    user.nom        = body.nom       or None
    user.subject_id = matiere_id_du_nom(db, matiere or None)   # RÈGLE 4 : matière rangée UNIQUEMENT par clé (put)
    user.niveau_id  = niveau_id_du_nom(db, niveau or None)
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
    profil_matiere = matiere_nom_de_id(db, user.subject_id) or ""
    profil_niveau = niveau_nom_de_id(db, user.niveau_id) or ""
    if matiere == profil_matiere and niveau == profil_niveau:
        user.travail_matiere_id = None   # même couple que le profil → aucun écart à stocker
        user.travail_niveau_id = None
    else:
        user.travail_matiere_id = matiere_id_du_nom(db, matiere)   # RÈGLE 4 : couple de travail rangé UNIQUEMENT par clé (put)
        user.travail_niveau_id = niveau_id_du_nom(db, niveau)
    db.commit()
    tm, tn, ajuste = couple_de_travail(db, user)
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
    user.travail_matiere_id = None
    user.travail_niveau_id = None
    db.commit()
    tm, tn, ajuste = couple_de_travail(db, user)
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


@router.get("/user/referentiel/pdf")
def get_mon_referentiel_pdf(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """Le PDF D'ORIGINE du niveau du prof — le fichier déposé par l'admin, servi TEL QUEL et affiché
    dans la visionneuse du navigateur (inline). get pur, aucune écriture. VERROUILLÉ sur SON niveau
    (users.niveau_id, comme les deux endpoints ci-dessus). Chemin sur disque : même convention que le
    dépôt admin — REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf. Le nom montré au navigateur est le
    VRAI nom déposé (referentiels.fichier), pas le nom de disque figé. 404 si rien à servir."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    ref = _referentiel_du_profil(db, user)
    if ref is None:
        raise HTTPException(404, "Aucun programme officiel n'est disponible pour votre niveau.")
    niveau = db.get(Niveau, ref.niveau_id)
    cycle = db.get(Cycle, niveau.cycle_id) if niveau else None
    if not niveau or not cycle:
        raise HTTPException(404, "Aucun programme officiel n'est disponible pour votre niveau.")
    pdf = REFERENTIELS_DIR / _dossier_cle(cycle.nom) / _dossier_cle(niveau.nom) / "referentiel.pdf"
    if not pdf.exists():
        raise HTTPException(404, "Aucun programme officiel n'est disponible pour votre niveau.")
    # Nom affiché = le vrai nom déposé ; en-tête sûr même avec accents (ASCII + filename* RFC 5987).
    nom = ref.fichier or "referentiel.pdf"
    ascii_nom = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode() or "referentiel.pdf"
    cd = f"inline; filename=\"{ascii_nom}\"; filename*=UTF-8''{quote(nom)}"
    return FileResponse(str(pdf), media_type="application/pdf", headers={"Content-Disposition": cd})


# ── Cahier des charges du PROF — document interne à son école/structure, déposé par LUI ──
#    (1 PDF par prof ; re-déposer remplace). Le pourquoi et l'extraction du texte viendront plus
#    tard. Écran = fenêtre sur la table cahiers_prof : get (état/PDF), put (dépôt). Auth inchangée.

def _cahier_du_profil(db: Session, user: User) -> CahierProf | None:
    return db.query(CahierProf).filter(CahierProf.user_id == user.id).first()


def texte_cahier_du_profil(db: Session, user: User) -> str:
    """Le TEXTE de travail du cahier des charges du prof (cahiers_prof.texte_epure), lu EN BASE
    au moment de générer (get, zéro copie). Chaîne VIDE s'il n'a pas déposé de cahier (ou texte
    non exploitable) : la génération se fait alors sans cahier, à l'identique. Lu par la génération
    (et, plus tard, exemple / idée) pour appliquer les règles de l'école par-dessus le programme."""
    cahier = _cahier_du_profil(db, user)
    return (cahier.texte_epure or "").strip() if cahier else ""


def _cahier_pdf_path(user: User) -> Path:
    return UPLOADS_CAHIERS_DIR / str(user.id) / "cahier.pdf"


@router.get("/user/cahier")
def get_mon_cahier(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """État du cahier des charges du prof : { present, fichier }. get pur, aucune écriture."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    cahier = _cahier_du_profil(db, user)
    if cahier is None:
        return {"present": False, "fichier": None}
    return {"present": True, "fichier": cahier.fichier}


@router.post("/user/cahier")
async def deposer_mon_cahier(file: UploadFile = File(...), aschool_access: str = Cookie(default=None),
                             db: Session = Depends(get_db)):
    """Dépôt du cahier des charges du prof (PDF) — CREATE si absent, UPDATE sinon (re-déposer
    remplace : 1 par prof). Le PDF est écrit sur disque (nom fixe cahier.pdf, dossier du prof) et
    la ligne cahiers_prof porte le nom d'origine. Messages d'erreur humains (règle des 2 publics)."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    nom = (file.filename or "cahier.pdf").strip()
    if not nom.lower().endswith(".pdf"):
        raise HTTPException(422, "Le fichier doit être un PDF (extension .pdf).")
    content = await file.read()
    if not content:
        raise HTTPException(422, "Le fichier est vide.")
    if not content[:4] == b"%PDF":
        raise HTTPException(422, "Ce fichier n'est pas un vrai PDF.")
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(413, "Le PDF dépasse 20 Mo — merci d'en déposer un plus léger.")
    dossier = _cahier_pdf_path(user).parent
    dossier.mkdir(parents=True, exist_ok=True)
    _cahier_pdf_path(user).write_bytes(content)
    # LE texte de travail du cahier : extrait UNE fois ici (porte unique rag.extraction, comme le
    # référentiel officiel) et figé en base — c'est LUI que la génération lira (get, zéro copie).
    try:
        from backend.rag.extraction import extraire_texte   # import paresseux (pdfplumber)
        texte_epure = extraire_texte(_cahier_pdf_path(user))
    except Exception:
        raise HTTPException(400, "Impossible de lire le contenu de ce PDF — merci d'en déposer un autre.")
    cahier = _cahier_du_profil(db, user)
    if cahier is None:
        db.add(CahierProf(user_id=user.id, fichier=nom, texte_epure=texte_epure))   # CREATE (aucun cahier encore)
    else:
        cahier.fichier = nom                               # UPDATE (re-dépôt = remplacement)
        cahier.texte_epure = texte_epure                   # le NOUVEAU PDF impose SON texte de travail
    db.commit()
    return {"present": True, "fichier": nom}


@router.get("/user/cahier/pdf")
def get_mon_cahier_pdf(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """Sert le cahier des charges déposé par le prof, affiché dans la visionneuse du navigateur
    (inline), avec le vrai nom d'origine. get pur, verrouillé sur SON dépôt. 404 si rien."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    cahier = _cahier_du_profil(db, user)
    pdf = _cahier_pdf_path(user)
    if cahier is None or not pdf.exists():
        raise HTTPException(404, "Aucun cahier des charges déposé.")
    nom = cahier.fichier or "cahier.pdf"
    ascii_nom = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode() or "cahier.pdf"
    cd = f"inline; filename=\"{ascii_nom}\"; filename*=UTF-8''{quote(nom)}"
    return FileResponse(str(pdf), media_type="application/pdf", headers={"Content-Disposition": cd})
