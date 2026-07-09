"""Endpoint « Tester un exemple » ancré sur le référentiel — Slice 2a du Chantier B.

Le bouton « Tester un exemple » ne sert plus un texte figé par matière (qui ignorait
le niveau) : il demande ici un TEXTE SOURCE généré par le LLM, ANCRÉ sur le référentiel
officiel du couple matière+niveau actif.

Règle d'or : si le couple n'a pas de référentiel vectorisé, on répond {available:false}
— le bouton n'inventera RIEN (pas d'appel LLM, pas de texte fabriqué).

Les couples-sources vectorisés vivent dans la table referentiels ; le routage
couple→collection est data-driven : il lit cette table (morceau 2).
"""
import json
import logging

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.core.database import get_db
from backend.core.models import ExempleReferentielRequest, ExempleReferentielResponse
from backend.core.models_db import Niveau, Referentiel
from backend.rag.pgvector_store import retrieve_pg
from backend.systeme.admin import get_ai_model, get_ai_provider, get_max_tokens, get_temperature, get_rag_top_k
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

# Gabarit de requête RAG (acteur « requête ») — UNIFORME pour tout couple ({matiere}/{niveau}),
# jamais de formulation par matière en dur. Choisi = T2, prouvé sur le miroir Bébés : une phrase
# de tâche cherche mieux que le nom seul de la matière (score rang 1 relevé, bonne fiche nette).
# NB : formulation calibrée crèche ; à réexaminer quand un couple non-crèche sera branché.
REQUETE_GABARIT = "Activité d'éveil pour développer {matiere} chez un enfant de {niveau}"


def _resolve_collection(db: Session, niveau: str) -> tuple[str, dict | None, float] | None:
    """Niveau → (collection, filtres ChromaDB, seuil). None = pas de référentiel pour ce couple.

    Data-driven : lit la table `referentiels` (plus de couple en dur, plus de seuil en dur).
    Jointure DIRECTE referentiels → niveaux en UN seul SELECT (n.nom = :niveau AND matiere_id
    IS NULL), pas « résoudre l'id puis requêter » (forme fragile si un nom de niveau n'est pas unique).

    Trois branches assumées :
      - 0 ligne → None (couple « en construction » : on n'invente RIEN).
      - 1 ligne → (collection, filtres parsés depuis la colonne JSON, seuil `score_min`).
      - >1 ligne → on LÈVE bruyamment. Deux niveaux de même nom dans deux cycles
        différents sont légitimes par design (clé réelle = (nom, cycle_id)) et /api/...
        n'envoie pas le cycle → on ne peut pas trancher ici. C'est une AMBIGUÏTÉ de nom,
        pas une corruption : on refuse plutôt que de choisir une ligne au hasard."""
    if not niveau:
        return None
    rows = (
        db.query(Referentiel.collection, Referentiel.filtres, Referentiel.score_min)
        .join(Niveau, Niveau.id == Referentiel.niveau_id)
        .filter(Niveau.nom == niveau, Referentiel.matiere_id.is_(None))
        .all()
    )
    if not rows:
        return None
    if len(rows) > 1:
        log.error(f"[exemple-ref] ambiguïté niveau : {len(rows)} référentiels pour nom={niveau!r} (matiere_id NULL)")
        raise HTTPException(500, f"Ambiguïté niveau : {len(rows)} référentiels trouvés pour ce nom de niveau. Configuration à corriger.")
    collection, filtres_json, score_min = rows[0]
    filters = json.loads(filtres_json) if filtres_json else None
    return collection, filters, score_min


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

    resolved = _resolve_collection(db, req.niveau)
    if resolved is None:
        # Règle d'or : pas de référentiel pour ce couple → on n'invente RIEN.
        log.info(f"[exemple-ref] aucun référentiel pour niveau='{req.niveau}' → available=false")
        return ExempleReferentielResponse(available=False)

    collection, filters, seuil = resolved
    # Filtre STRICT de pertinence : un chunk sous le seuil n'ancre JAMAIS une génération
    # (pas de « meilleur quand même »). Le seuil vit EN BASE, par référentiel
    # (`referentiels.score_min`, résolu ci-dessus) — plus aucune constante en dur.
    requete = REQUETE_GABARIT.format(matiere=req.matiere, niveau=req.niveau)
    chunks = retrieve_pg(collection, requete, filters=filters, top_k=get_rag_top_k(db))
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        # Rien d'assez pertinent : on n'invente RIEN, on le dit honnêtement au prof (generate PAS appelé).
        log.info(f"[exemple-ref] aucun chunk >= seuil {seuil} ({collection}, matiere='{req.matiere}') → available=false + message")
        return ExempleReferentielResponse(available=False, message=AUCUN_EXTRAIT_PERTINENT)

    prompt = build_exemple_referentiel_prompt(chunks, matiere=req.matiere, niveau=req.niveau)
    try:
        texte = generate(prompt, provider=get_ai_provider(db), model=get_ai_model(db), max_tokens=get_max_tokens(db, "exemple"), temperature=get_temperature(db))
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    log.info(f"[exemple-ref] généré pour couple ({req.matiere}, {req.niveau}) — {len(chunks)} chunks ancrés (>= {seuil})")
    return ExempleReferentielResponse(available=True, texte=texte)
