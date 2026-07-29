"""« Mes contenus » — le monde NEUF du prof (modèle playlist : séquence ⊃ séances ⊃ activités).

DÉCISION utilisateur (29/07) : ce monde est le futur REMPLAÇANT de Mes outils. Il ne lit et
n'écrit QUE ses tables neuves (`sequences`, `seances`, `seance_phases`, `activites`,
`activite_versions`). L'ancien monde (`activites_sauvegardees`, `sequences_sauvegardees`)
ne s'affiche JAMAIS ici — il vit sa vie dans Mes outils jusqu'à sa suppression finale, et
ne sert que de modèle de code.

L'activité applique la règle 0 NATIVEMENT : écrite en base à la génération même (POST à la
première, PUT aux suivantes), chaque jalon fige une version restaurable (`activite_versions`)
— l'historique s'empile, on n'écrase jamais.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.core.models_db import Activite, ActiviteVersion, Seance, SeanceVersion, Sequence, User
from backend.llm.generator import generate_stream, acquire_llm_slot, release_llm_slot, LLMRateLimitError
from backend.prof.profil import couple_de_travail
from backend.supervision.incidents import creer_incident
from backend.systeme.admin import (
    get_ai_model, get_ai_provider, get_cle_texte, get_max_tokens, get_temperature,
    get_stream_silence_timeout, get_retry_max, get_retry_wait_max, get_prompt,
)

router = APIRouter()
log = logging.getLogger(__name__)


def _json_liste(brut: str | None) -> list:
    """Colonne JSON texte → liste Python, sans jamais casser l'écran sur une ligne ancienne."""
    try:
        v = json.loads(brut or "[]")
        return v if isinstance(v, list) else []
    except ValueError:
        return []


def _json_dict(brut: str | None) -> dict:
    try:
        v = json.loads(brut or "{}")
        return v if isinstance(v, dict) else {}
    except ValueError:
        return {}


def _iso(dt: datetime | None) -> str | None:
    return dt.replace(tzinfo=timezone.utc).isoformat() if dt else None


@router.get("/mes-contenus")
def lister(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sequences = db.query(Sequence).filter(Sequence.user_id == user.id).all()
    seances = db.query(Seance).filter(Seance.user_id == user.id).all()
    activites = db.query(Activite).filter(Activite.user_id == user.id).all()

    titres_sequences = {s.id: s.titre for s in sequences}
    titres_seances = {s.id: s.titre for s in seances}
    nb_seances_par_sequence: dict[int, int] = {}
    for s in seances:
        if s.sequence_id is not None:
            nb_seances_par_sequence[s.sequence_id] = nb_seances_par_sequence.get(s.sequence_id, 0) + 1

    contenus = []
    for s in sequences:
        contenus.append({
            "type": "sequence",
            "id": s.id,
            "titre": s.titre,
            "matiere": s.matiere,
            "niveau": s.niveau,
            "parent": None,                       # une séquence est le sommet : jamais rangée
            "nb_seances": nb_seances_par_sequence.get(s.id, 0),
            "resultat": None,
            "created_at": _iso(s.created_at),
            "updated_at": _iso(s.updated_at),
        })
    for s in seances:
        parent = None
        if s.sequence_id is not None:
            parent = {"type": "sequence", "id": s.sequence_id,
                      "titre": titres_sequences.get(s.sequence_id, "")}
        contenus.append({
            "type": "seance",
            "id": s.id,
            "titre": s.titre,
            "matiere": s.matiere,
            "niveau": s.niveau,
            "parent": parent,
            "nb_seances": None,
            "resultat": s.resultat,
            # De quoi ROUVRIR la séance dans son écran (reprise complète du formulaire) :
            "duree": s.duree_minutes,
            "mode": s.mode,
            "contexte": s.description,
            "competences": _json_liste(s.competences),
            "materiel": s.materiel,
            "esquisse": _json_dict(s.esquisse),
            "contraintes": s.contraintes,
            "style": s.style,
            "created_at": _iso(s.created_at),
            "updated_at": _iso(s.updated_at),
        })
    for a in activites:
        parent = None
        if a.seance_id is not None:
            parent = {"type": "seance", "id": a.seance_id,
                      "titre": titres_seances.get(a.seance_id, "")}
        contenus.append({
            "type": "activite",
            "id": a.id,
            "titre": a.objet or a.activite_label,
            "matiere": a.matiere,
            "niveau": a.niveau,
            "parent": parent,
            "nb_seances": None,
            "resultat": a.resultat,
            # De quoi ROUVRIR l'activité dans son écran (reprise complète) :
            "activite_type_id": a.activite_type_id,
            "activite_label": a.activite_label,
            "sous_type": a.sous_type,
            "nb": a.nb,
            "avec_correction": a.avec_correction,
            "objet": a.objet,
            "ton": a.ton,
            "texte_source": a.texte_source,
            "statut": a.statut,
            "created_at": _iso(a.created_at),
            "updated_at": _iso(a.updated_at),
        })

    # Plus récent en haut, tous types mélangés — sur la date de CRÉATION : c'est elle que la
    # ligne affiche (badge calendrier), l'ordre à l'écran suit donc ce que le prof lit.
    contenus.sort(key=lambda c: c["created_at"] or "", reverse=True)

    return {
        "contenus": contenus,
        "compteurs": {
            "tout": len(contenus),
            "sequences": len(sequences),
            "seances": len(seances),
            "activites": len(activites),
        },
    }


# ---------------------------------------------------------------------------
# Activités du monde neuf — auto-save règle 0 (POST = 1re génération, PUT = jalons suivants)
# ---------------------------------------------------------------------------

class ActiviteCorps(BaseModel):
    activite_type_id: int
    activite_label: str
    sous_type: Optional[str] = None
    nb: Optional[int] = None
    avec_correction: bool = False
    objet: Optional[str] = None
    ton: Optional[str] = None
    texte_source: str
    resultat: str


def _activite_de(user: User, activite_id: int, db: Session) -> Activite:
    activite = (
        db.query(Activite)
        .filter(Activite.id == activite_id, Activite.user_id == user.id)
        .first()
    )
    if not activite:
        raise HTTPException(404, "Activité introuvable.")
    return activite


@router.post("/contenus/activites")
def creer_activite(
    corps: ActiviteCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Première génération = l'activité NAÎT en base (auto-save, règle 0) + version 'generation'.
    Le couple matière/niveau est lu EN BASE (couple de travail), jamais envoyé par l'écran."""
    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")
    activite = Activite(
        user_id=user.id,
        activite_type_id=corps.activite_type_id,
        activite_label=corps.activite_label,
        sous_type=corps.sous_type,
        nb=corps.nb,
        avec_correction=corps.avec_correction,
        objet=corps.objet or None,
        matiere=matiere or None,
        niveau=niveau,
        ton=corps.ton,
        texte_source=corps.texte_source,
        resultat=corps.resultat,
    )
    db.add(activite)
    db.flush()
    db.add(ActiviteVersion(activite_id=activite.id, jalon="generation",
                           ton=corps.ton, resultat=corps.resultat))
    db.commit()
    return {"id": activite.id}


@router.put("/contenus/activites/{activite_id}")
def regenerer_activite(
    activite_id: int,
    corps: ActiviteCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Jalon suivant (régénération, changement de ton/texte) : l'ÉTAT COURANT est mis à jour
    et une NOUVELLE version s'empile — on n'écrase jamais une version (règle 0)."""
    activite = _activite_de(user, activite_id, db)
    activite.activite_type_id = corps.activite_type_id
    activite.activite_label = corps.activite_label
    activite.sous_type = corps.sous_type
    activite.nb = corps.nb
    activite.avec_correction = corps.avec_correction
    activite.objet = corps.objet or None
    activite.ton = corps.ton
    activite.texte_source = corps.texte_source
    activite.resultat = corps.resultat
    db.add(ActiviteVersion(activite_id=activite.id, jalon="generation",
                           ton=corps.ton, resultat=corps.resultat))
    db.commit()
    return {"ok": True, "id": activite.id}


# ---------------------------------------------------------------------------
# Séances du monde neuf — génération en STREAMING + auto-save règle 0
# (même mécanique que l'activité : le flux d'abord, l'écran enregistre à la réussite)
# ---------------------------------------------------------------------------

MODES_SEANCE = {"standard", "remediation", "approfondissement", "autonomie"}
STYLES_SEANCE = {"classique", "ludique", "structure", "concis"}


class SeanceGeneration(BaseModel):
    """Ce que l'écran envoie pour GÉNÉRER : le formulaire entier, sans résultat.
    Le couple matière/niveau est lu EN BASE (couple de travail), jamais envoyé."""
    theme: str
    contexte: str = ""
    duree: int
    mode: str
    competences: list[str] = []
    materiel: str = ""
    esquisse: dict = {}
    contraintes: str = ""
    style: Optional[str] = None


class SeanceCorps(SeanceGeneration):
    """Ce que l'écran enregistre (règle 0) : le formulaire + le déroulé généré."""
    resultat: str


def _bloc_precisions(req: SeanceGeneration) -> str:
    """Les champs optionnels du formulaire, ajoutés au prompt du mode — uniquement ceux
    qui sont remplis. Vide si le prof n'a rien précisé."""
    lignes = []
    if req.contexte.strip():
        lignes.append(f"- Contexte de la classe : {req.contexte.strip()}")
    comps = [c.strip() for c in req.competences if c and c.strip()]
    if comps:
        lignes.append("- Compétences / attendus visés : " + " ; ".join(comps))
    if req.materiel.strip():
        lignes.append(f"- Matériel disponible : {req.materiel.strip()}")
    esquisse = {k: (req.esquisse.get(k) or "").strip() for k in ("a", "b", "c")}
    if any(esquisse.values()):
        morceaux = []
        if esquisse["a"]:
            morceaux.append(f"mise en route : {esquisse['a']}")
        if esquisse["b"]:
            morceaux.append(f"activité principale : {esquisse['b']}")
        if esquisse["c"]:
            morceaux.append(f"retour / trace écrite : {esquisse['c']}")
        lignes.append("- Esquisse du déroulé voulue par l'enseignant (à respecter) : " + " | ".join(morceaux))
    if req.contraintes.strip():
        lignes.append(f"- Contraintes / consignes spéciales : {req.contraintes.strip()}")
    if not lignes:
        return ""
    return "PRÉCISIONS DE L'ENSEIGNANT — à intégrer à la séance :\n" + "\n".join(lignes)


def _valider_generation(req: SeanceGeneration) -> None:
    if not req.theme.strip():
        raise HTTPException(400, "Décrivez d'abord le thème ou l'objectif de la séance.")
    if not (5 <= req.duree <= 300):
        raise HTTPException(400, "Indiquez une durée entre 5 et 300 minutes.")
    if req.mode not in MODES_SEANCE:
        raise HTTPException(400, "Choisissez un mode de séance.")
    if req.style is not None and req.style not in STYLES_SEANCE:
        raise HTTPException(400, "Style de production inconnu.")


@router.post("/contenus/seances/generer")
def generer_seance(
    req: SeanceGeneration,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Génération d'une séance en STREAMING (SSE delta/error/done) — même mécanique que
    /api/generate : prompt du MODE lu en base (registre des prompts), précisions du formulaire
    ajoutées, couche de STYLE facultative, créneau LLM pris avant le flux, incident en base
    si le flux casse. L'ÉCRITURE (règle 0) suit côté écran : POST/PUT /contenus/seances."""
    _valider_generation(req)
    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    prompt = get_prompt(db, f"seance_{req.mode}").format(
        matiere=matiere or "", niveau=niveau, duree=req.duree, theme=req.theme.strip(),
    )
    precisions = _bloc_precisions(req)
    if precisions:
        prompt = prompt + "\n\n" + precisions
    if req.style:
        prompt = prompt + "\n\n" + get_prompt(db, f"seance_style_{req.style}")

    # Réglages LLM lus EN BASE avant le flux (la session de requête va se fermer).
    provider = get_ai_provider(db)
    model = get_ai_model(db)
    cle = get_cle_texte(db)
    max_toks = get_max_tokens(db, "sequence")
    temp = get_temperature(db)
    silence = get_stream_silence_timeout(db)
    retry_max = get_retry_max(db)
    retry_wait_max = get_retry_wait_max(db)
    email = user.email

    try:
        acquire_llm_slot()
    except LLMRateLimitError as e:
        log.warning("/api/contenus/seances/generer — service très demandé : %s", e)
        raise HTTPException(429, "Le service est très demandé en ce moment. Réessayez dans un instant.")

    def flux():
        # Créneau rendu dans le finally, dans TOUS les cas (fin, erreur, déconnexion du prof).
        try:
            for morceau in generate_stream(
                prompt, cle=cle, provider=provider, model=model,
                max_tokens=max_toks, temperature=temp, read_timeout=silence,
                retry_max=retry_max, retry_wait_max=retry_wait_max,
            ):
                yield f"event: delta\ndata: {json.dumps({'text': morceau}, ensure_ascii=False)}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            log.warning("/api/contenus/seances/generer — flux interrompu : %s", e)
            ref = creer_incident(
                endpoint="/api/contenus/seances/generer",
                error=f"{type(e).__name__}: {e}",
                provider=provider, model=model,
                matiere=matiere, niveau=niveau, type_activite=f"Séance ({req.mode})",
                consigne=req.theme.strip(), user_email=email,
            )
            data = json.dumps({"ref": ref}, ensure_ascii=False) if ref else "{}"
            yield f"event: error\ndata: {data}\n\n"
        finally:
            release_llm_slot()

    return StreamingResponse(
        flux(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _seance_de(user: User, seance_id: int, db: Session) -> Seance:
    seance = (
        db.query(Seance)
        .filter(Seance.id == seance_id, Seance.user_id == user.id)
        .first()
    )
    if not seance:
        raise HTTPException(404, "Séance introuvable.")
    return seance


def _remplir_seance(seance: Seance, corps: SeanceCorps, matiere: str | None, niveau: str) -> None:
    seance.titre = corps.theme.strip()
    seance.description = corps.contexte.strip()
    seance.matiere = matiere or None
    seance.niveau = niveau
    seance.duree_minutes = corps.duree
    seance.mode = corps.mode
    seance.competences = json.dumps([c.strip() for c in corps.competences if c and c.strip()], ensure_ascii=False)
    seance.materiel = corps.materiel.strip()
    seance.esquisse = json.dumps({k: (corps.esquisse.get(k) or "").strip() for k in ("a", "b", "c")}, ensure_ascii=False)
    seance.contraintes = corps.contraintes.strip()
    seance.style = corps.style
    seance.resultat = corps.resultat


@router.post("/contenus/seances")
def creer_seance(
    corps: SeanceCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Première génération réussie = la séance NAÎT en base (auto-save, règle 0) + version."""
    _valider_generation(corps)
    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")
    seance = Seance(user_id=user.id, titre="")
    _remplir_seance(seance, corps, matiere, niveau)
    db.add(seance)
    db.flush()
    db.add(SeanceVersion(seance_id=seance.id, jalon="generation",
                         style=corps.style, resultat=corps.resultat))
    db.commit()
    return {"id": seance.id}


@router.put("/contenus/seances/{seance_id}")
def regenerer_seance(
    seance_id: int,
    corps: SeanceCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Régénération : l'état courant est mis à jour, une NOUVELLE version s'empile (règle 0).
    Le CLOISONNEMENT passe en premier : une séance qui n'est pas à soi = 404, avant tout."""
    seance = _seance_de(user, seance_id, db)
    _valider_generation(corps)
    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")
    _remplir_seance(seance, corps, matiere, niveau)
    db.add(SeanceVersion(seance_id=seance.id, jalon="generation",
                         style=corps.style, resultat=corps.resultat))
    db.commit()
    return {"ok": True, "id": seance.id}
