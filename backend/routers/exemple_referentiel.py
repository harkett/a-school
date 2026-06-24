"""Endpoint « Tester un exemple » ancré sur le référentiel — Slice 2a du Chantier B.

Le bouton « Tester un exemple » ne sert plus un texte figé par matière (qui ignorait
le niveau) : il demande ici un TEXTE SOURCE généré par le LLM, ANCRÉ sur le référentiel
officiel du couple matière+niveau actif.

Règle d'or : si le couple n'a pas de référentiel vectorisé, on répond {available:false}
— le bouton n'inventera RIEN (pas d'appel LLM, pas de texte fabriqué).

Aujourd'hui un seul couple-source est vectorisé (BTS CIEL option A, cf. slice 1). Le
routage couple→collection deviendra data-driven quand on élargira les gates RAG.
"""
import logging

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models import ExempleReferentielRequest, ExempleReferentielResponse
from backend.rag import retrieve
from backend.rag.referentiels import bts_ciel_option_a as ciel_fiche
from backend.routers.admin import get_ai_model, get_ai_provider, get_max_tokens, get_temperature
from src.generator import generate, LLMRateLimitError
from src.prompts import build_exemple_referentiel_prompt

router = APIRouter()
log = logging.getLogger(__name__)

# Wording validé (version C) — message honnête au prof quand aucun extrait n'est assez
# pertinent. NE PAS reformuler sans validation : ce texte est le contrat avec le prof.
AUCUN_EXTRAIT_PERTINENT = (
    "aSchool n'a pas trouvé, dans le référentiel officiel, de passage assez "
    "pertinent pour générer un exemple fidèle. Essayez de reformuler votre "
    "demande avec des termes plus proches du programme."
)


def _resolve_collection(niveau: str) -> tuple[str, dict] | None:
    """Couple → (collection, filtres ChromaDB). None = pas de référentiel pour ce couple.

    Minimal aujourd'hui (1 référentiel vectorisé : BTS CIEL option A). Les filtres
    cadenassent le bon couple : niveau exact + option A (jamais l'option B électronique)."""
    if (niveau or "").strip() == "BTS CIEL option A":
        filters = {"$and": [
            {"niveau": {"$eq": "BTS CIEL option A"}},
            {"option": {"$eq": "A"}},
        ]}
        return "bts_ciel_optionA", filters
    return None


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


@router.post("/exemple-referentiel", response_model=ExempleReferentielResponse)
def api_exemple_referentiel(
    req: ExempleReferentielRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    _get_email(aschool_access)

    resolved = _resolve_collection(req.niveau)
    if resolved is None:
        # Règle d'or : pas de référentiel pour ce couple → on n'invente RIEN.
        log.info(f"[exemple-ref] aucun référentiel pour niveau='{req.niveau}' → available=false")
        return ExempleReferentielResponse(available=False)

    collection, filters = resolved
    chunks = retrieve(collection, req.matiere, filters=filters, top_k=4)
    # Filtre STRICT de pertinence : un chunk sous le seuil n'ancre JAMAIS une génération
    # (pas de « meilleur quand même »). Le seuil vit dans la fiche du référentiel.
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= ciel_fiche.SCORE_MIN]
    if not chunks:
        # Rien d'assez pertinent : on n'invente RIEN, on le dit honnêtement au prof (generate PAS appelé).
        log.info(f"[exemple-ref] aucun chunk >= seuil {ciel_fiche.SCORE_MIN} ({collection}, matiere='{req.matiere}') → available=false + message")
        return ExempleReferentielResponse(available=False, message=AUCUN_EXTRAIT_PERTINENT)

    prompt = build_exemple_referentiel_prompt(chunks, matiere=req.matiere, niveau=req.niveau)
    try:
        texte = generate(prompt, provider=get_ai_provider(db), model=get_ai_model(db), max_tokens=get_max_tokens(db, "exemple"), temperature=get_temperature(db))
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    log.info(f"[exemple-ref] généré pour couple ({req.matiere}, {req.niveau}) — {len(chunks)} chunks ancrés (>= {ciel_fiche.SCORE_MIN})")
    return ExempleReferentielResponse(available=True, texte=texte)
