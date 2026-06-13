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

from fastapi import APIRouter, Cookie, HTTPException

from backend import auth as auth_lib
from backend.models import ExempleReferentielRequest, ExempleReferentielResponse
from backend.rag import retrieve
from src.generator import generate
from src.prompts import build_exemple_referentiel_prompt

router = APIRouter()
log = logging.getLogger(__name__)


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
):
    _get_email(aschool_access)

    resolved = _resolve_collection(req.niveau)
    if resolved is None:
        # Règle d'or : pas de référentiel pour ce couple → on n'invente RIEN.
        log.info(f"[exemple-ref] aucun référentiel pour niveau='{req.niveau}' → available=false")
        return ExempleReferentielResponse(available=False)

    collection, filters = resolved
    chunks = retrieve(collection, req.matiere, filters=filters, top_k=4)
    if not chunks:
        log.info(f"[exemple-ref] retrieve vide ({collection}, matiere='{req.matiere}') → available=false")
        return ExempleReferentielResponse(available=False)

    prompt = build_exemple_referentiel_prompt(chunks, matiere=req.matiere, niveau=req.niveau)
    texte = generate(prompt)
    log.info(f"[exemple-ref] généré pour couple ({req.matiere}, {req.niveau}) — {len(chunks)} chunks ancrés")
    return ExempleReferentielResponse(available=True, texte=texte)
