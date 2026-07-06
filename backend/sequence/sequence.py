from fastapi import APIRouter, Depends, HTTPException, Cookie, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import ToolUsageLog, SequenceSauvegardee, User
from backend.systeme.admin import get_ai_model, get_ai_provider, get_max_tokens, get_temperature, get_prompt
from src.generator import generate, LLMRateLimitError

router = APIRouter()

DUREES_VALIDES = {30, 45, 50, 55, 60, 90, 120}
MODES_VALIDES  = {"standard", "remediation"}


class SequenceRequest(BaseModel):
    theme: str
    matiere: str
    niveau: str
    duree: int
    mode: str = "standard"
    description_classe: str = ""


class SequenceResponse(BaseModel):
    resultat: str


# Prompts (standard + remédiation) déplacés dans backend/llm_prompts.py
# (administrables en base, lus via get_prompt).


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


@router.post("/generate-sequence", response_model=SequenceResponse)
def api_generate_sequence(
    req: SequenceRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)

    if not req.theme.strip():
        raise HTTPException(400, "Le thème ne peut pas être vide.")
    if req.duree not in DUREES_VALIDES:
        raise HTTPException(400, "Durée invalide.")
    if req.mode not in MODES_VALIDES:
        raise HTTPException(400, "Mode invalide.")
    if req.mode == "remediation" and not req.description_classe.strip():
        raise HTTPException(400, "La description de la classe est requise pour le mode remédiation.")

    try:
        if req.mode == "remediation":
            prompt = get_prompt(db, "sequence_remediation").format(
                matiere=req.matiere,
                niveau=req.niveau,
                duree=req.duree,
                theme=req.theme.strip(),
                description_classe=req.description_classe.strip(),
            )
        else:
            prompt = get_prompt(db, "sequence_standard").format(
                matiere=req.matiere,
                niveau=req.niveau,
                duree=req.duree,
                theme=req.theme.strip(),
            )

        resultat = generate(prompt, provider=get_ai_provider(db), model=get_ai_model(db), max_tokens=get_max_tokens(db, "sequence"), temperature=get_temperature(db))
    except HTTPException:
        raise
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    except Exception as e:
        raise HTTPException(500, str(e))

    try:
        db.add(SequenceSauvegardee(
            user_id=db.query(User.id).filter(User.email == email).scalar(),
            matiere=req.matiere,
            niveau=req.niveau,
            theme=req.theme.strip(),
            duree=req.duree,
            mode=req.mode,
            description_classe=req.description_classe.strip(),
            resultat=resultat,
        ))
        db.add(ToolUsageLog(user_id=db.query(User.id).filter(User.email == email).scalar(), tool="sequence"))
        db.commit()
    except Exception:
        pass

    return SequenceResponse(resultat=resultat)


@router.get("/mes-sequences")
def api_mes_sequences(
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    rows = (
        db.query(SequenceSauvegardee)
        .filter(SequenceSauvegardee.user_id == db.query(User.id).filter(User.email == email).scalar())
        .order_by(SequenceSauvegardee.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "theme": r.theme,
            "matiere": r.matiere,
            "niveau": r.niveau,
            "duree": r.duree,
            "mode": r.mode,
            "description_classe": r.description_classe,
            "resultat": r.resultat,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.delete("/mes-sequences/{seq_id}")
def api_delete_sequence(
    seq_id: int,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    seq = db.query(SequenceSauvegardee).filter(
        SequenceSauvegardee.id == seq_id,
        SequenceSauvegardee.user_id == db.query(User.id).filter(User.email == email).scalar(),
    ).first()
    if not seq:
        raise HTTPException(404, "Séquence introuvable.")
    db.delete(seq)
    db.commit()
    return {"ok": True}


class PartagerSeqRequest(BaseModel):
    partagee: bool
    anonyme: Optional[bool] = None


@router.patch("/mes-sequences/{seq_id}")
def api_toggle_partage_sequence(
    seq_id: int,
    req: PartagerSeqRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    seq = db.query(SequenceSauvegardee).filter(
        SequenceSauvegardee.id == seq_id,
        SequenceSauvegardee.user_id == db.query(User.id).filter(User.email == email).scalar(),
    ).first()
    if not seq:
        raise HTTPException(404, "Séquence introuvable.")
    seq.partagee = req.partagee
    if req.anonyme is not None:
        seq.anonyme = req.anonyme
    db.commit()
    return {"ok": True}


@router.get("/mon-reseau/sequences")
def api_bibliotheque_sequences(
    matiere: Optional[str] = Query(default=None),
    niveau: Optional[str] = Query(default=None),
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    query = (
        db.query(SequenceSauvegardee, User)
        .join(User, User.id == SequenceSauvegardee.user_id)
        .filter(SequenceSauvegardee.partagee == True)
        .filter(SequenceSauvegardee.user_id != db.query(User.id).filter(User.email == email).scalar())
        .filter(User.is_active == True)
    )
    if matiere:
        query = query.filter(SequenceSauvegardee.matiere == matiere)
    if niveau:
        query = query.filter(SequenceSauvegardee.niveau == niveau)
    rows = query.order_by(SequenceSauvegardee.id.desc()).all()
    return [
        {
            "id": s.id,
            "theme": s.theme,
            "matiere": s.matiere,
            "niveau": s.niveau,
            "duree": s.duree,
            "mode": s.mode,
            "resultat": s.resultat,
            "partagee_par": "Anonyme" if s.anonyme else (f"{u.prenom or ''} {u.nom or ''}".strip() or "Anonyme"),
        }
        for s, u in rows
    ]
