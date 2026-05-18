import logging
import os
import unicodedata

from fastapi import APIRouter, HTTPException, Cookie, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import GenerateRequest, GenerateResponse
from backend.models_db import ActiviteSauvegardee, User
from backend import auth as auth_lib
from src.prompts import build_prompt
from src.generator import generate

router = APIRouter()
log = logging.getLogger(__name__)

_FEW_SHOT_MIN = 3  # nombre minimum d'activités sauvegardées pour activer le few-shot

# Gates RAG — matières et niveaux éligibles selon les corpus indexés actuels
SUBJECT_RAG_ELIGIBLE = {"mathematiques", "maths", "math"}
CYCLE4_LEVELS = {"5e", "4e", "3e"}


def _norm_subject(s: str | None) -> str:
    """Normalise une matière pour comparaison robuste (casse + accents + espaces)."""
    return (
        unicodedata.normalize("NFKD", s or "")
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .strip()
    )


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


def _get_exemples(db: Session, email: str, activite_key: str) -> list[str]:
    rows = (
        db.query(ActiviteSauvegardee.resultat)
        .filter(
            ActiviteSauvegardee.user_email == email,
            ActiviteSauvegardee.activite_key == activite_key,
        )
        .order_by(ActiviteSauvegardee.id.desc())
        .all()
    )
    if len(rows) < _FEW_SHOT_MIN:
        return []
    return [r.resultat for r in rows[:2]]


def _maybe_retrieve_rag(user: User | None, req: GenerateRequest) -> list[dict] | None:
    """Décide si le RAG s'active et appelle retrieve. Logs INFO à chaque gate pour observabilité prod.
    Retourne None si gate échoue OU retrieve échoue (fallback silencieux no-RAG)."""
    if os.getenv("RAG_ENABLED", "false").lower() != "true":
        log.info("[RAG] skip — RAG_ENABLED=false")
        return None

    subject_norm = _norm_subject(user.subject if user else None)
    if subject_norm not in SUBJECT_RAG_ELIGIBLE:
        log.info(f"[RAG] skip — subject '{user.subject if user else None}' (norm='{subject_norm}') not eligible")
        return None

    if req.niveau not in CYCLE4_LEVELS:
        log.info(f"[RAG] skip — niveau '{req.niveau}' not in cycle 4 {CYCLE4_LEVELS}")
        return None

    programme = os.getenv("RAG_PROGRAMME_DEFAULT", "2020")
    # TODO L36: filtre niveau désactivé — pas de métadonnée niveau dans corpus actuel (BOEN cycle 4 en bloc)
    #          ré-activer quand corpus aura métadonnées niveau propres
    # TODO L36: top_k=4 est empirique — calibrer après 10+ tests sur générations réelles
    try:
        from backend.rag import retrieve

        chunks = retrieve(
            collection_name="maths_cycle4",
            question=req.texte,
            filters={"programme": programme},
            top_k=4,
        )
        log.info(f"[RAG] activated — collection=maths_cycle4 programme={programme} niveau={req.niveau} chunks={len(chunks)}")
        return chunks
    except Exception as e:
        log.warning(f"[RAG] retrieve failed — fallback no-RAG: {e}")
        return None


@router.post("/generate", response_model=GenerateResponse)
def api_generate(
    req: GenerateRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    try:
        user = db.query(User).filter(User.email == email).first()
        exemples = _get_exemples(db, email, req.activite_key)
        rag_chunks = _maybe_retrieve_rag(user, req)

        kwargs = {"niveau": req.niveau}
        if req.sous_type:
            kwargs["sous_type"] = req.sous_type
        if req.nb:
            kwargs["nb"] = req.nb
        if req.activite_key.startswith("lv_"):
            kwargs["langue"] = req.langue_lv or "langues vivantes"

        prompt = build_prompt(
            req.activite_key,
            req.texte,
            avec_correction=req.avec_correction,
            exemples=exemples,
            rag_chunks=rag_chunks,
            **kwargs,
        )
        if os.getenv("RAG_DEBUG_PROMPT", "false").lower() == "true":
            log.info(f"[RAG] prompt final (debug):\n---PROMPT START---\n{prompt}\n---PROMPT END---")
        resultat = generate(prompt)
        return GenerateResponse(resultat=resultat, chunks=rag_chunks)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
