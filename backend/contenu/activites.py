"""GET /api/activites/{matiere} — les types d'activité d'un couple, LUS EN BASE.

Source UNIQUE : le CATALOGUE `types_activite` + la LIAISON `referentiel_types_activite` (le « coché »
du référentiel). Aucun type en dur, zéro copie.

Résolution du couple : par le NIVEAU (envoyé par le client, même patron qu'`exemple_referentiel`) →
le référentiel du niveau (matiere_id NULL). Repli : si le couple n'a aucun type coché (ou pas de
référentiel), on renvoie le type par DÉFAUT du catalogue (`is_default`) — « Activité d'apprentissage ».
"""
import json
import logging

from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.core.database import get_db
from backend.core.models import GenerateRequest
from backend.core.models_db import (
    Niveau, Referentiel, ActiviteType, ReferentielActiviteType, ReferentielTypePrecision, TypeParametre,
)
from backend.llm.generator import generate_stream, acquire_llm_slot, release_llm_slot, LLMRateLimitError
from backend.rag.pgvector_store import retrieve_pg
from backend.systeme.admin import (
    get_ai_model, get_ai_provider, get_max_tokens, get_temperature, get_rag_top_k,
    get_stream_silence_timeout,
)

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


def types_du_couple(db: Session, niveau: str) -> list[dict]:
    """Types d'activité à afficher pour le couple, LUS EN BASE.

    1) types COCHÉS (`liaison.actif`) du référentiel du niveau, joints au catalogue (`actif`) ;
    2) si vide (pas de référentiel, ou rien de coché) → le type par DÉFAUT du catalogue.
    Précisions et paramètres LUS dans leurs tables filles (`type_precisions` ordonnées par `ordre`,
    `type_parametres`) — plus de blob JSON. Renvoie `[{label, key, sous_types:[...], params:[...]}]`
    (ordre liaison puis catalogue)."""
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

    # Précisions / paramètres de chaque type, LUS dans leurs tables filles (une requête chacune,
    # groupée par type). Ordre des précisions = `ordre`. Zéro JSON, une donnée = une ligne.
    type_ids = [t.id for t in lignes]
    prec_par_type: dict[int, list[str]] = {}
    par_par_type: dict[int, list[str]] = {}
    if type_ids:
        # Précisions PAR COUPLE (table fille de la liaison `referentiel_type_precisions`), comme le
        # prompt : chaque couple a SES précisions. On passe par les liaisons de CE référentiel — pas
        # de repli sur une table globale. Sans référentiel (types par défaut) : aucune précision.
        if ref_id is not None:
            type_par_lien = {
                lien_id: tid
                for tid, lien_id in (db.query(ReferentielActiviteType.activite_type_id,
                                              ReferentielActiviteType.id)
                                       .filter(ReferentielActiviteType.referentiel_id == ref_id,
                                               ReferentielActiviteType.actif.is_(True),
                                               ReferentielActiviteType.activite_type_id.in_(type_ids))
                                       .all())
            }
            if type_par_lien:
                for lien_id, libelle in (db.query(ReferentielTypePrecision.referentiel_activite_type_id,
                                                  ReferentielTypePrecision.libelle)
                                           .filter(ReferentielTypePrecision.referentiel_activite_type_id
                                                   .in_(list(type_par_lien.keys())))
                                           .order_by(ReferentielTypePrecision.referentiel_activite_type_id,
                                                     ReferentielTypePrecision.ordre)
                                           .all()):
                    prec_par_type.setdefault(type_par_lien[lien_id], []).append(libelle)
        for tid, cle in (db.query(TypeParametre.type_activite_id, TypeParametre.cle)
                           .filter(TypeParametre.type_activite_id.in_(type_ids))
                           .all()):
            par_par_type.setdefault(tid, []).append(cle)

    return [
        {"id": t.id, "label": t.label,
         "sous_types": prec_par_type.get(t.id, []), "params": par_par_type.get(t.id, [])}
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


@router.post("/generate")
def api_generate(
    req: GenerateRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Génère une activité EN STREAMING à partir du PROMPT du COUPLE × type, LU EN BASE sur la
    liaison `referentiel_types_activite` (une seule place, zéro copie) — PAS le catalogue global.
    Le couple est résolu par le NIVEAU (même patron que `types_du_couple`). Le prompt contient deux
    marqueurs : {texte} (l'idée du prof, elle mène) et {referentiel} (extraits du programme officiel
    du couple, récupérés par RAG sur l'idée du prof). Provider / modèle / max_tokens / température /
    coupure de silence lus EN BASE.

    Réponse : flux SSE (`text/event-stream`) — événements `delta` (morceau de texte), `error`
    (échec technique survenu APRÈS le début du flux) et `done` (fin normale). Les échecs MÉTIER
    (référentiel absent, type pas prêt, RAG vide, saturation) sont renvoyés AVANT le flux, en JSON
    HTTP classique (4xx/429) — l'écran affiche alors leur message tel quel.

    NB : `avec_correction` et le few-shot « aSchool vous reconnaît » sont DIFFÉRÉS. La sauvegarde
    côté prof (/api/mes-activites) reste inchangée (déclenchée par l'écran à la fin du flux)."""
    _exiger_session(aschool_access)

    # 1. Le COUPLE : le référentiel du niveau. Sans référentiel, aucun prompt de couple → rien à générer.
    ref_id = _referentiel_du_niveau(db, req.niveau)
    if ref_id is None:
        raise HTTPException(400, "Ce niveau n'a pas encore de référentiel officiel. La génération n'est pas encore possible ici.")

    # 2. Le type choisi (catalogue), retrouvé par son id — sert à retrouver la ligne de liaison.
    t = (db.query(ActiviteType)
           .filter(ActiviteType.id == req.activite_type_id, ActiviteType.actif.is_(True))
           .first())
    if t is None:
        raise HTTPException(400, "Type d'activité inconnu.")

    # 3. Le PROMPT du COUPLE × type, LU EN BASE sur la liaison (coché + non vide). Une seule source
    # par donnée, zéro prompt en dur, zéro repli sur un prompt global : le prompt est propre au couple.
    lien = (db.query(ReferentielActiviteType)
              .filter(ReferentielActiviteType.referentiel_id == ref_id,
                      ReferentielActiviteType.activite_type_id == t.id,
                      ReferentielActiviteType.actif.is_(True))
              .first())
    modele = lien.prompt if (lien and lien.prompt and lien.prompt.strip()) else None
    if modele is None:
        raise HTTPException(400, "Ce type d'activité n'est pas encore prêt pour ce niveau.")

    # 4. Le {referentiel} : extraits du programme officiel du couple les plus proches de l'idée du prof
    # (RAG pgvector), filtrés au SEUIL du référentiel (lu en base). Rien d'assez pertinent → on n'invente
    # RIEN, on le dit au prof (règle 23). Même voie que « Tester un exemple ».
    ref = (db.query(Referentiel.collection, Referentiel.filtres, Referentiel.score_min)
             .filter(Referentiel.id == ref_id).first())
    collection, filtres_json, seuil = ref
    filters = json.loads(filtres_json) if filtres_json else None
    chunks = retrieve_pg(collection, req.texte, filters=filters, top_k=get_rag_top_k(db))
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        raise HTTPException(400, "aSchool n'a pas trouvé, dans le référentiel officiel, de passage assez pertinent. Reformulez votre idée avec des termes plus proches du programme.")
    referentiel_txt = "\n\n".join(c["text"] for c in chunks)

    # 5. Remplissage. Le texte source → {texte}, les extraits officiels → {referentiel}. Les autres
    # paramètres (niveau, sous_type, nb, langue) restent disponibles si l'admin les a mis dans le prompt.
    kwargs = {"niveau": req.niveau, "referentiel": referentiel_txt}
    if req.sous_type:
        kwargs["sous_type"] = req.sous_type
    if req.nb:
        kwargs["nb"] = req.nb
    # LV : signalée par la présence de `langue_lv` (le front ne l'envoie que pour la matière LV),
    # plus par un préfixe de clé — la clé disparaît, la langue vient de la donnée réelle.
    if req.langue_lv:
        kwargs["langue"] = req.langue_lv or "langues vivantes"
    try:
        prompt = modele.format(texte=req.texte, **kwargs)
    except KeyError as e:
        manquant = str(e).strip("'")
        if manquant not in _USER_PARAMS:
            raise  # placeholder inconnu = bug du prompt → 500, jamais masqué
        raise HTTPException(400, f"Indiquez {_USER_PARAMS[manquant]} pour cette activité.") from e

    # 6. Réglages LLM lus EN BASE, AVANT le flux (get) — passés en valeurs au flux (aucune lecture
    # de base pendant le streaming, la session de requête étant destinée à se fermer). `silence` =
    # coupure de silence admin en base (zéro délai en dur).
    provider = get_ai_provider(db)
    model = get_ai_model(db)
    max_toks = get_max_tokens(db, "activite")
    temp = get_temperature(db)
    silence = get_stream_silence_timeout(db)

    # 7. Créneau LLM pris AVANT le flux : si saturation, message MÉTIER « service très demandé »
    # renvoyé en 429 pré-flux (jamais après le début du flux, où le statut 200 est déjà parti).
    try:
        acquire_llm_slot()
    except LLMRateLimitError as e:
        log.warning("/api/generate — service très demandé : %s", e)   # détail technique = logs
        raise HTTPException(429, "Le service est très demandé en ce moment. Réessayez dans un instant.")

    def flux():
        # Le créneau est RENDU dans le finally — donc dans TOUS les cas : fin normale, erreur
        # technique en cours de flux, ET déconnexion du prof (Starlette ferme ce générateur →
        # GeneratorExit remonte jusqu'au finally). GeneratorExit est une BaseException : le
        # `except Exception` ne l'attrape pas (pas de faux événement `error`), le finally, lui,
        # s'exécute toujours. Un créneau jamais rendu = perdu jusqu'au redémarrage : c'est le
        # piège à ne pas laisser passer.
        try:
            for morceau in generate_stream(
                prompt, provider=provider, model=model,
                max_tokens=max_toks, temperature=temp, read_timeout=silence,
            ):
                yield f"event: delta\ndata: {json.dumps({'text': morceau}, ensure_ascii=False)}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            # Détail technique = logs (règle 23) ; l'écran ne recevra qu'un `error` neutre.
            log.warning("/api/generate — flux interrompu : %s", e)
            yield "event: error\ndata: {}\n\n"
        finally:
            release_llm_slot()

    return StreamingResponse(
        flux(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
