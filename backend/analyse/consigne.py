from fastapi import APIRouter, Depends, HTTPException, Cookie
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.analyse.commun import email_de_session, json_du_modele
from backend.core.database import get_db, schema_de_session
from backend.core.models import ExempleReferentielResponse
from backend.core.models_db import ToolUsageLog, User
from backend.pedagogie.exemple_referentiel import (AUCUN_EXTRAIT_PERTINENT, REQUETE_GABARIT,
                                                   _resolve_collection)
from backend.prof.profil import couple_de_travail
from backend.rag.pgvector_store import retrieve_pg
from backend.systeme.admin import (get_ai_model, get_ai_provider, liste_fournisseurs, get_cle_texte, get_max_tokens,
                                   get_rag_top_k, get_retry_max, get_retry_wait_max,
                                   get_temperature, get_prompt)
from backend.llm.generator import generate, LLMRateLimitError
from backend.llm.prompts import build_consigne_exemple_prompt

router = APIRouter()


class ConsigneRequest(BaseModel):
    consigne: str


class AxeAnalyse(BaseModel):
    axe: str
    severite: str
    extrait: str
    probleme: str
    conseil: str


class ConsigneResponse(BaseModel):
    analyses: list[AxeAnalyse]
    verdict: str
    version_optimisee: str


# Prompt déplacé dans backend/core/llm_prompts.py (administrable en base, lu via get_prompt).


# Le prompt d'exemple a le DROIT DE NE PAS ÉCRIRE : quand les extraits du référentiel ne
# suffisent pas à savoir ce que la matière recouvre à ce niveau, il répond par ce marqueur au
# lieu de deviner une consigne plausible. Une consigne inventée hors du programme serait pire
# qu'une absence de consigne — le prof la croirait tirée de SA formation.
#
# Le marqueur est une CONVENTION DU TEXTE, administrable comme lui : on le reconnaît, mais on ne
# tombe pas si l'admin le retire du prompt (le modèle rendrait alors une consigne, cas normal).
MARQUEUR_PAS_DE_CONSIGNE = "=== PAS DE CONSIGNE ==="


def _refus_ou_texte(brut: str) -> ExempleReferentielResponse:
    """La réponse du modèle, rangée : soit une consigne à poser dans la zone, soit un refus
    motivé à montrer au prof. Rien ne part dans la zone tant que le marqueur y est."""
    texte = (brut or "").strip()
    if MARQUEUR_PAS_DE_CONSIGNE not in texte:
        return ExempleReferentielResponse(available=True, texte=texte)

    # Ce qui suit le marqueur est la raison écrite par le modèle. On la nettoie de son étiquette
    # (« Raison : ») pour ne pas la montrer telle quelle au prof, et on retombe sur le message
    # commun si elle est vide — un refus sans motif n'apprend rien.
    reste = texte.split(MARQUEUR_PAS_DE_CONSIGNE, 1)[1].strip()
    if reste.lower().startswith("raison"):
        reste = reste.split(":", 1)[-1].strip() if ":" in reste else ""
    return ExempleReferentielResponse(available=False, message=reste or AUCUN_EXTRAIT_PERTINENT)


@router.post("/consignes/exemple-genere", response_model=ExempleReferentielResponse)
def api_exemple_consigne_genere(
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """« Propose-moi un exemple » : la consigne de démonstration ÉCRITE À LA DEMANDE du prof,
    pour SON couple, ancrée sur les extraits de son référentiel.

    Le jumeau exact de `api_exemple_ambiguites_genere` : un clic, un appel, un texte posé dans
    la zone — rien n'est rangé en base. Une consigne de démonstration n'a aucune raison d'être
    la même deux fois, et l'ancrage vient d'où il doit venir : le référentiel du couple, jamais
    l'intuition du modèle sur un nom de matière.

    Règle d'or : pas de référentiel pour ce couple, ou rien d'assez pertinent au seuil
    (`referentiels.score_min`) → available:false, et `generate` n'est PAS appelé (rien payé).
    On n'invente RIEN — et le modèle lui-même a le droit de s'arrêter là (voir le marqueur)."""
    email = email_de_session(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    matiere, niveau, _ = couple_de_travail(db, user)
    if not matiere or not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    resolu = _resolve_collection(db, niveau)
    if resolu is None:
        return ExempleReferentielResponse(available=False)
    collection, filtres, seuil = resolu

    chunks = retrieve_pg(collection, REQUETE_GABARIT.format(matiere=matiere, niveau=niveau),
                         filters=filtres, top_k=get_rag_top_k(db),
                         schema=schema_de_session(db), annee=niveau, matiere=matiere)
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        # Rien d'assez pertinent : on le dit au prof, et `generate` n'est PAS appelé (rien payé).
        return ExempleReferentielResponse(available=False, message=AUCUN_EXTRAIT_PERTINENT)

    prompt = build_consigne_exemple_prompt(db, chunks, matiere=matiere, niveau=niveau)
    # Pas de cahier des charges de l'établissement ici, contrairement aux prompts de génération :
    # ses règles servent à rendre un contenu PROPRE, et cette consigne-ci doit être imparfaite.
    try:
        brut = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
                        model=get_ai_model(db),
                        max_tokens=get_max_tokens(db, "consigne_exemple_genere"),
                        temperature=get_temperature(db), retry_max=get_retry_max(db),
                        retry_wait_max=get_retry_wait_max(db), outil="consigne_exemple_genere")
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))   # surchargé/trop de demandes : transitoire, pas une panne
    return _refus_ou_texte(brut)


@router.post("/analyser-consigne", response_model=ConsigneResponse)
def api_analyser_consigne(
    req: ConsigneRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = email_de_session(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    if not req.consigne.strip():
        raise HTTPException(400, "La consigne ne peut pas être vide.")

    # Couple résolu EN BASE (couple_de_travail, décision 25/07) — l'écran n'envoie plus
    # matière/niveau, le serveur ne fait plus confiance au corps de la requête.
    matiere, niveau, _ajuste = couple_de_travail(db, user)
    if not matiere or not niveau:
        raise HTTPException(400, "Votre profil n'a pas encore de matière et de niveau — complétez Mon profil avant de lancer l'analyse.")

    prompt = get_prompt(db, "consigne").format(
        matiere=matiere,
        niveau=niveau,
        consigne=req.consigne.strip(),
    )

    try:
        # retry_max / retry_wait_max : même politique de rattrapage qu'ailleurs, lue en base.
        # Elle manquait ici : le réglage `ai_retry_max` de l'admin ne s'appliquait pas.
        raw = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db), model=get_ai_model(db),
                       max_tokens=get_max_tokens(db, "consigne"), temperature=get_temperature(db),
                       retry_max=get_retry_max(db), retry_wait_max=get_retry_wait_max(db),
                       outil="consigne")
        data = json_du_modele(raw)
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    except ValueError:
        raise HTTPException(500, "Le modèle n'a pas retourné un résultat exploitable. Réessayez.")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    nb = len(data.get("analyses", []))

    # Même correction et même raison qu'à l'identique dans analyse/ambiguites.py : une
    # statistique ne casse jamais l'outil du prof, mais un commit() qui échoue laisse la
    # session en état d'échec — le rollback est ce qui la rend réutilisable.
    try:
        db.add(ToolUsageLog(user_id=user.id, tool="consigne", score_label=str(nb),
                            matiere=matiere, niveau=niveau))
        db.commit()
    except Exception:
        db.rollback()

    return ConsigneResponse(
        analyses=[AxeAnalyse(**a) for a in data.get("analyses", [])],
        verdict=data.get("verdict", ""),
        version_optimisee=data.get("version_optimisee", req.consigne),
    )
