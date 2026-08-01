import logging
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Cookie, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.securite import comptes
from backend.communication import echange
from backend.core.database import get_db
from backend.core.models_db import Feedback, FeedbackStatut, Incident, User
from backend.core.resolution_couple import matiere_nom_de_id, niveau_nom_de_id
from backend.systeme.admin import _reglage_entier, codes_statuts_modifiables, labels_statuts

# A-FEEDBACK a été retiré le 28/04/2026 — notification par SMTP direct uniquement.
router = APIRouter()
logger = logging.getLogger(__name__)

# Ancré sur la RACINE DU DÉPÔT, jamais sur le répertoire courant : un chemin relatif suivait
# le cwd de qui lançait le processus (les tests écrivaient ailleurs, ou pire dans le vrai
# data/ selon l'endroit d'où pytest partait). parents[2] = la racine, depuis backend/communication/.
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads" / "feedbacks"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Formats acceptés : type MIME -> extension. Reste du code (et non en base) parce que ce
# n'est pas un choix de gestion mais une capacité technique — ce sont les formats que la
# chaîne sait réellement recevoir et servir. L'écran ne les recopie plus : il les LIT ici,
# par /feedback/limites.
ALLOWED_TYPES = {
    "image/png":        ".png",
    "image/jpeg":       ".jpg",
    "application/pdf":  ".pdf",
    "text/plain":       ".txt",
}
# Libellés des formats tels qu'on les annonce au prof (« PNG, JPEG, PDF, TXT ») — dérivés des
# extensions ci-dessus, jamais réécrits à la main.
FORMATS_LISIBLES = [e.lstrip(".").upper().replace("JPG", "JPEG") for e in ALLOWED_TYPES.values()]


def _limites_pieces_jointes(db: Session) -> tuple[int, int]:
    """(taille max en Mo, nombre max de fichiers) — SEMÉS PAR MIGRATION, lus en base.
    Ces deux nombres étaient écrits dans le code du serveur ET recopiés dans l'écran."""
    return (_reglage_entier(db, "feedback_piece_jointe_max_mo", 1),
            _reglage_entier(db, "feedback_pieces_jointes_max", 1))


@router.get("/feedback/limites", status_code=200)
def limites_pieces_jointes(db: Session = Depends(get_db)):
    """Ce que l'écran a le droit de joindre : taille, nombre, formats. L'écran LIT ces valeurs
    au lieu de les connaître — sinon changer la limite en base n'aurait changé que la moitié de
    l'application, et le prof lirait « max 5 Mo » en se faisant refuser à 4."""
    taille_mo, nombre = _limites_pieces_jointes(db)
    return {
        "taille_max_mo": taille_mo,
        "nombre_max": nombre,
        "mime_acceptes": list(ALLOWED_TYPES.keys()),
        "formats_lisibles": FORMATS_LISIBLES,
    }


class FeedbackBody(BaseModel):
    type: str = "feedback"
    message: str = Field(min_length=1, max_length=2000)
    rating: int = Field(ge=0, le=5, default=0)
    category: str | None = None
    attachment_path: str | None = None
    # D'où le prof envoie (« Écran Créer une activité · Français × 6e ») — affiché dans la
    # fenêtre avant envoi, figé à l'envoi, jamais modifiable ensuite.
    contexte: str | None = Field(default=None, max_length=160)
    # Réf d'incident technique (échec de génération) : présente si le prof a cliqué « signaler » depuis
    # la modale d'erreur. Sert à RELIER ce feedback à l'incident déjà enregistré en base (une seule place).
    incident_ref: str | None = Field(default=None, max_length=24)


class FeedbackUpdateBody(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    category: str | None = None
    attachment_path: str | None = None


class MessageBody(BaseModel):
    """Une réponse du prof DANS l'échange (pas une modification de son message d'ouverture)."""
    corps: str = Field(min_length=1, max_length=echange.CORPS_MAX)


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Connexion requise.")
    email = comptes.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


@router.get("/feedback/statuts", status_code=200)
def lister_statuts(db: Session = Depends(get_db)):
    """Le catalogue des statuts tel que le PROF le voit : le libellé de la pastille et la phrase
    qui l'explique, lus EN BASE (`feedback_statuts`). L'écran d'aide les recopiait — il les lit.
    Le pendant admin est /admin/feedback-statuts : même table, même autorité."""
    rows = (db.query(FeedbackStatut.code, FeedbackStatut.label, FeedbackStatut.description)
              .order_by(FeedbackStatut.ordre, FeedbackStatut.id).all())
    if not rows:
        raise HTTPException(500, "Statuts de feedback absents en base (migration non appliquée ?).")
    return [{"code": c, "label": l, "description": d} for c, l, d in rows]


# ── Upload fichier joint ──────────────────────────────────────────────────────

@router.post("/feedback/upload", status_code=200)
async def upload_attachment(
    file: UploadFile = File(...),
    aschool_access: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    _get_email(aschool_access)  # auth uniquement

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Format non accepté. Seuls {', '.join(FORMATS_LISIBLES)} sont autorisés.")

    taille_mo, _ = _limites_pieces_jointes(db)
    content = await file.read()
    if len(content) > taille_mo * 1024 * 1024:
        raise HTTPException(400, f"Fichier trop volumineux. Maximum {taille_mo} Mo.")

    ext = ALLOWED_TYPES[file.content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / filename
    dest.write_bytes(content)

    return {"path": filename}


# ── Télécharger un fichier joint (prof propriétaire ou admin) ─────────────────

@router.get("/feedback/attachment/{filename}", status_code=200)
def get_attachment(
    filename: str,
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
    aschool_admin: str | None = Cookie(default=None),
):
    # Sécurité : nom de fichier sans chemin
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Nom de fichier invalide.")

    # Auth : prof ou admin
    is_admin = False
    if aschool_admin:
        payload = comptes.verify_access_token(aschool_admin)
        is_admin = bool(payload)

    if not is_admin:
        email = _get_email(aschool_access)
        fb = (
            db.query(Feedback)
            .filter(
                Feedback.user_id == db.query(User.id).filter(User.email == email).scalar(),
                Feedback.attachment_path == filename,
            )
            .first()
        )
        if not fb:
            raise HTTPException(403, "Accès refusé.")

    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Fichier introuvable.")

    return FileResponse(str(path))


def _controler_nombre_pieces(db: Session, chemins: str | None) -> None:
    """Le nombre de pièces jointes était contrôlé UNIQUEMENT par le navigateur : une limite que
    seul l'écran fait respecter n'est pas une limite. Le serveur la fait respecter aussi, sur la
    même valeur en base — le prof, lui, ne voit aucune différence (l'écran l'arrête avant)."""
    if not chemins:
        return
    _, nombre_max = _limites_pieces_jointes(db)
    if len([c for c in chemins.split(",") if c.strip()]) > nombre_max:
        raise HTTPException(400, f"Vous ne pouvez pas joindre plus de {nombre_max} fichiers à un retour.")


# ── Soumettre un feedback ──────────────────────────────────────────────────────

@router.post("/feedback", status_code=200)
def submit_feedback(
    body: FeedbackBody,
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    email = _get_email(aschool_access)
    _controler_nombre_pieces(db, body.attachment_path)

    fb = Feedback(
        type=body.type,
        user_id=db.query(User.id).filter(User.email == email).scalar(),
        message=body.message,
        rating=body.rating,
        category=body.category,
        attachment_path=body.attachment_path,
        contexte=body.contexte,
    )
    db.add(fb)
    db.commit()

    # Rattachement de l'incident technique : si le prof a cliqué « signaler » depuis un échec de
    # génération, la réf d'incident voyage avec le message. On relie l'incident (une seule place :
    # incidents.feedback_id) → l'admin voit, sur ce feedback, ce qui a techniquement planté.
    # Best-effort : une réf inconnue ou déjà reliée n'empêche JAMAIS l'enregistrement du feedback.
    if body.incident_ref:
        try:
            db.query(Incident).filter(
                Incident.ref == body.incident_ref, Incident.feedback_id.is_(None)
            ).update({"feedback_id": fb.id}, synchronize_session=False)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("Rattachement incident %s -> feedback %s echoue : %s", body.incident_ref, fb.id, e)

    user = db.query(User).filter(User.email == email).first()
    prof = {
        "email":   email,
        "prenom":  user.prenom  if user else None,
        "nom":     user.nom     if user else None,
        "subject": matiere_nom_de_id(db, user.subject_id) if user else None,
        "niveau":  niveau_nom_de_id(db, user.niveau_id)  if user else None,
    }
    try:
        comptes.send_feedback_notification(prof, body.message, body.rating, body.category, body.type,
                                            contexte=body.contexte, incident_ref=body.incident_ref)
    except Exception as e:
        logger.error(f"Notification feedback non envoyée : {type(e).__name__}: {e}")

    return {"status": "ok"}


# ── Mes feedbacks ──────────────────────────────────────────────────────────────

@router.get("/feedback/mes-feedbacks", status_code=200)
def mes_feedbacks(
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    email = _get_email(aschool_access)
    rows = (
        db.query(Feedback)
        .filter(Feedback.user_id == db.query(User.id).filter(User.email == email).scalar(), Feedback.type != "notation")
        .order_by(Feedback.created_at.desc())
        .all()
    )
    modifiables = codes_statuts_modifiables(db)  # lu une fois en base, pas par ligne
    labels = labels_statuts(db)                  # idem : le libellé affiché vient de la base
    # L'échange des retours affichés, en UNE requête (pas une par carte).
    echanges = echange.messages_par_feedback(db, [f.id for f in rows])
    return [
        {
            "id":              f.id,
            "category":        f.category,
            "message":         f.message,
            "contexte":        f.contexte,
            "statut":          f.statut or "nouveau",
            "statut_label":    labels.get(f.statut or "nouveau", f.statut or "nouveau"),
            "created_at":      f.created_at.strftime("%d/%m/%Y") if f.created_at else "—",
            "updated_at":      f.updated_at.strftime("%d/%m/%Y") if f.updated_at else None,
            "attachment_path": f.attachment_path,
            "modifiable":      (f.statut or "nouveau") in modifiables,
            "messages":        echange.serialiser(echanges.get(f.id, []), vu_par_admin=False),
        }
        for f in rows
    ]


# ── Répondre dans l'échange (côté prof) ────────────────────────────────────────

@router.post("/feedback/{feedback_id}/messages", status_code=200)
def repondre_feedback(
    feedback_id: int,
    body: MessageBody,
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    """Le prof poursuit l'échange sur SON retour. Distinct de PATCH /feedback/{id}, qui
    réécrit son message d'ouverture : ici on ajoute, on n'efface rien."""
    email = _get_email(aschool_access)

    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(404, "Retour introuvable.")
    if fb.user_id != db.query(User.id).filter(User.email == email).scalar():
        raise HTTPException(403, "Ce retour ne vous appartient pas.")

    try:
        message, statut_avis, _ = echange.ajouter_message(db, fb, body.corps, est_admin=False)
    except echange.CorpsInvalide as e:
        raise HTTPException(400, str(e))

    return {
        "status": "ok",
        "message": echange.serialiser([message], vu_par_admin=False)[0],
        # L'avis à l'administration a-t-il pu partir ? Le message, lui, est enregistré.
        "avis_envoye": statut_avis == "envoye",
    }


# ── Modifier un feedback ───────────────────────────────────────────────────────

@router.patch("/feedback/{feedback_id}", status_code=200)
def update_feedback(
    feedback_id: int,
    body: FeedbackUpdateBody,
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    email = _get_email(aschool_access)

    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(404, "Feedback introuvable.")
    if fb.user_id != db.query(User.id).filter(User.email == email).scalar():
        raise HTTPException(403, "Ce feedback ne vous appartient pas.")
    if (fb.statut or "nouveau") not in codes_statuts_modifiables(db):
        raise HTTPException(400, "Ce feedback ne peut plus être modifié.")
    _controler_nombre_pieces(db, body.attachment_path)

    fb.message         = body.message
    fb.category        = body.category
    fb.attachment_path = body.attachment_path
    fb.updated_at      = datetime.utcnow()
    db.commit()

    user = db.query(User).filter(User.email == email).first()
    prof = {
        "email":   email,
        "prenom":  user.prenom  if user else None,
        "nom":     user.nom     if user else None,
        "subject": matiere_nom_de_id(db, user.subject_id) if user else None,
        "niveau":  niveau_nom_de_id(db, user.niveau_id)  if user else None,
    }
    try:
        comptes.send_feedback_update_notification(prof, body.message, body.category)
    except Exception as e:
        logger.error(f"Notification modification feedback non envoyée : {type(e).__name__}: {e}")

    return {"status": "ok"}
