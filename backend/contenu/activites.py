"""GET /api/activites/{matiere} — les types d'activité d'un couple, LUS EN BASE.

Source UNIQUE : le CATALOGUE `types_activite` + la LIAISON `referentiel_types_activite` (le « coché »
du référentiel). Aucun type en dur, zéro copie.

Résolution du couple : par le NIVEAU (envoyé par le client, même patron qu'`exemple_referentiel`) →
le référentiel du niveau (matiere_id NULL). Repli : si le couple n'a aucun type coché (ou pas de
référentiel), on renvoie le type par DÉFAUT du catalogue (`is_default`) — « Activité d'apprentissage ».
"""
import json
import logging

import requests
from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.core.database import get_db
from backend.core.models import GenerateRequest, GenerateResponse
from backend.core.models_db import Niveau, Referentiel, ActiviteType, ReferentielActiviteType
from backend.llm.generator import generate, LLMRateLimitError
from backend.systeme.admin import get_ai_model, get_ai_provider, get_max_tokens, get_temperature

router = APIRouter()
log = logging.getLogger(__name__)

# Paramètres SAISIS par le prof qui peuvent légitimement manquer dans la requête (le front les
# retire s'ils sont vides). S'ils manquent alors que le prompt du type les exige, le .format()
# lève KeyError → faute client (400), jamais un 500. Tout AUTRE placeholder manquant = bug
# du prompt (template) → on re-lève (500), jamais masqué.
_USER_PARAMS = {
    "nb": "le nombre de questions / d'items",
    "sous_type": "le type d'exercice",
    "langue": "la langue vivante",
}


def _referentiel_du_niveau(db: Session, niveau: str) -> int | None:
    """id du référentiel du couple (niveau entier, `matiere_id` NULL), ou None.

    None si niveau vide, aucun référentiel, ou ambiguïté (même nom de niveau dans deux cycles :
    on ne peut pas trancher sans le cycle). Dans tous ces cas on retombe sur le défaut — un GET
    d'affichage ne doit JAMAIS casser la page prof."""
    if not niveau:
        return None
    rows = (db.query(Referentiel.id)
              .join(Niveau, Niveau.id == Referentiel.niveau_id)
              .filter(Niveau.nom == niveau, Referentiel.matiere_id.is_(None))
              .all())
    if len(rows) != 1:
        if len(rows) > 1:
            log.warning("[activites] ambiguïté niveau %r : %d référentiels → repli défaut", niveau, len(rows))
        return None
    return rows[0][0]


def _to_list(txt: str) -> list:
    """Colonne texte JSON → liste Python. [] si illisible (jamais de crash d'affichage)."""
    try:
        v = json.loads(txt or "[]")
        return v if isinstance(v, list) else []
    except Exception:
        return []


def types_du_couple(db: Session, niveau: str) -> list[dict]:
    """Types d'activité à afficher pour le couple, LUS EN BASE.

    1) types COCHÉS (`liaison.actif`) du référentiel du niveau, joints au catalogue (`actif`) ;
    2) si vide (pas de référentiel, ou rien de coché) → le type par DÉFAUT du catalogue.
    Renvoie `[{label, key, sous_types:[...], params:[...]}]` (ordre liaison puis catalogue)."""
    ref_id = _referentiel_du_niveau(db, niveau)
    lignes = []
    if ref_id is not None:
        lignes = (db.query(ActiviteType)
                    .join(ReferentielActiviteType,
                          ReferentielActiviteType.activite_type_id == ActiviteType.id)
                    .filter(ReferentielActiviteType.referentiel_id == ref_id,
                            ReferentielActiviteType.actif.is_(True),
                            ActiviteType.actif.is_(True))
                    .order_by(ReferentielActiviteType.ordre, ActiviteType.ordre)
                    .all())
    if not lignes:
        lignes = (db.query(ActiviteType)
                    .filter(ActiviteType.is_default.is_(True), ActiviteType.actif.is_(True))
                    .order_by(ActiviteType.ordre)
                    .all())
    return [
        {"label": t.label, "key": t.key,
         "sous_types": _to_list(t.sous_types), "params": _to_list(t.params)}
        for t in lignes
    ]


@router.get("/activites/{matiere}")
def get_activites(matiere: str, niveau: str = "", db: Session = Depends(get_db)):
    """Types d'activité du couple. `matiere` reste dans l'URL (compat front) mais n'entre PAS dans la
    résolution : le référentiel est résolu par NIVEAU (matiere_id NULL), même patron qu'`exemple_
    referentiel`. `niveau` = query envoyée par le front. Renvoie TOUJOURS un tableau (repli défaut) →
    la page prof ne casse jamais."""
    return types_du_couple(db, niveau)


def _exiger_session(aschool_access: str | None) -> None:
    """Génération réservée à un prof connecté (même posture que l'ancien /generate). Ne touche
    PAS au mécanisme d'auth : lit juste le pass court du cookie et refuse 401 s'il est absent/mort."""
    if not aschool_access or not auth_lib.verify_access_token(aschool_access):
        raise HTTPException(401, "Non connecté.")


@router.post("/generate", response_model=GenerateResponse)
def api_generate(
    req: GenerateRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Génère une activité à partir du PROMPT du type choisi, LU EN BASE (catalogue `types_activite`,
    par `activite_key`). Zéro prompt en dur. Provider / modèle / max_tokens / température lus EN BASE.

    NB : `avec_correction` et le few-shot « aSchool vous reconnaît » sont DIFFÉRÉS (rebranchés à une
    étape ultérieure) — on ne réintroduit aucun texte de prompt en dur ici. La sauvegarde côté prof
    (/api/mes-activites) reste inchangée."""
    _exiger_session(aschool_access)

    t = (db.query(ActiviteType)
           .filter(ActiviteType.key == req.activite_key, ActiviteType.actif.is_(True))
           .first())
    if t is None:
        raise HTTPException(400, f"Type d'activité inconnu : {req.activite_key}")

    # Le prompt du type (en base) + les paramètres saisis. Le texte source va au marqueur {texte}.
    kwargs = {"niveau": req.niveau}
    if req.sous_type:
        kwargs["sous_type"] = req.sous_type
    if req.nb:
        kwargs["nb"] = req.nb
    if req.activite_key.startswith("lv_"):
        kwargs["langue"] = req.langue_lv or "langues vivantes"
    try:
        prompt = t.prompt.format(texte=req.texte, **kwargs)
    except KeyError as e:
        manquant = str(e).strip("'")
        if manquant not in _USER_PARAMS:
            raise  # placeholder inconnu = bug du prompt → 500, jamais masqué
        raise HTTPException(400, f"Indiquez {_USER_PARAMS[manquant]} pour cette activité.") from e

    try:
        resultat = generate(
            prompt,
            provider=get_ai_provider(db), model=get_ai_model(db),
            max_tokens=get_max_tokens(db, "activite"), temperature=get_temperature(db),
        )
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé / trop de demandes : transitoire
    except (RuntimeError, requests.exceptions.RequestException) as e:
        log.warning("/api/generate — génération indisponible : %s", e)
        raise HTTPException(502, "Le service de génération est momentanément indisponible. Réessayez dans un instant.")
    return GenerateResponse(resultat=resultat)
