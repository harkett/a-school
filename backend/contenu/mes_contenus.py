"""« Mes contenus » — le monde NEUF du prof (modèle playlist : séquence ⊃ séances ⊃ activités).

DÉCISION utilisateur (29/07, aboutie le 30/07) : ce monde EST le produit. Il ne lit et
n'écrit QUE ses tables neuves (`sequences`, `seances`, `seance_phases`, `activites`,
`activite_versions`). L'ancien monde a été démoli puis droppé le 30/07.

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
from backend.core.models_db import Activite, ActiviteVersion, Referentiel, Seance, SeanceVersion, Sequence, User
from backend.llm.generator import generate, generate_stream, acquire_llm_slot, release_llm_slot, LLMRateLimitError
from backend.prof.profil import couple_de_travail, texte_cahier_du_profil
from backend.llm.prompts import ajouter_cahier_au_prompt
from backend.rag.pgvector_store import retrieve_pg
from backend.supervision.incidents import creer_incident
from backend.systeme.admin import (
    get_ai_model, get_ai_provider, get_cle_texte, get_max_tokens, get_temperature,
    get_stream_silence_timeout, get_retry_max, get_retry_wait_max, get_prompt, get_rag_top_k,
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
            # De quoi ROUVRIR la séquence dans son écran (reprise complète du formulaire) :
            "contexte": s.contexte,
            "ampleur": s.ampleur,
            "competences": _json_liste(s.competences),
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
    # Rattachement OPTIONNEL à une séance : posé à la NAISSANCE seulement (création depuis
    # l'écran Séance). Le PUT de régénération ne touche jamais au rattachement.
    seance_id: Optional[int] = None


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
    # Rattachement à la naissance (création depuis l'écran Séance) : la séance doit
    # appartenir au prof connecté — sinon 404, on n'écrit rien.
    if corps.seance_id is not None:
        _seance_de(user, corps.seance_id, db)
    activite = Activite(
        user_id=user.id,
        seance_id=corps.seance_id,
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


class RattacherSeanceCorps(BaseModel):
    seance_id: Optional[int] = None   # null = détacher


@router.put("/contenus/activites/{activite_id}/seance")
def rattacher_activite_seance(
    activite_id: int,
    corps: RattacherSeanceCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rattache l'activité à une séance, ou la DÉTACHE (seance_id null). Un seul parent :
    rattacher une activité déjà rangée ailleurs la DÉPLACE (l'écran confirme avant).
    Détacher ≠ supprimer : l'activité reste dans Mes contenus, simplement « non rangée ».
    Contrôles avant écriture : l'activité ET la séance visée appartiennent au prof."""
    activite = _activite_de(user, activite_id, db)
    if corps.seance_id is not None:
        _seance_de(user, corps.seance_id, db)
    activite.seance_id = corps.seance_id
    db.commit()
    return {"ok": True, "id": activite.id, "seance_id": activite.seance_id}


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


_AUCUN_EXTRAIT_POUR_THEME = (
    "aSchool n'a pas trouvé, dans le référentiel officiel, de passage assez pertinent "
    "pour proposer un thème fidèle. Décrivez votre thème directement dans la zone de "
    "texte — ou dictez-le avec le micro."
)


@router.post("/contenus/seances/proposer-theme")
def proposer_theme_seance(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bouton « Propose-moi un thème » de l'écran Séance — la version séance de
    « Propose-moi une idée » : aSchool écrit le thème/objectif à la place du prof, ANCRÉ
    sur le programme officiel du niveau (extraits RAG, seuil du référentiel lu en base).
    Règle d'or : pas de référentiel → available:false ; rien d'assez pertinent →
    available:false + message honnête. On n'invente RIEN hors du programme. Le couple est
    LU EN BASE (couple de travail), jamais envoyé par l'écran."""
    from backend.contenu.activites import _referentiel_du_niveau  # même résolution que l'activité

    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    ref_id = _referentiel_du_niveau(db, niveau)
    if ref_id is None:
        return {"available": False}

    ref = (db.query(Referentiel.collection, Referentiel.filtres, Referentiel.score_min)
             .filter(Referentiel.id == ref_id).first())
    collection, filtres_json, seuil = ref
    filters = json.loads(filtres_json) if filtres_json else None
    requete = f"Thème de séance de {matiere or 'la matière du prof'}, niveau {niveau} : notions et objectifs du programme"
    chunks = retrieve_pg(collection, requete, filters=filters, top_k=get_rag_top_k(db))
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        log.info("[proposer-theme] aucun chunk >= seuil %s (%s, %s) → available=false", seuil, collection, niveau)
        return {"available": False, "message": _AUCUN_EXTRAIT_POUR_THEME}

    referentiel_txt = "\n\n".join(c["text"] for c in chunks)
    prompt = get_prompt(db, "seance_proposer_theme").format(
        matiere=matiere or "", niveau=niveau, referentiel=referentiel_txt,
    )
    # Cahier des charges de l'établissement (get, zéro copie) ajouté par-dessus le programme
    # officiel — même geste que « Propose-moi une idée ».
    prompt = ajouter_cahier_au_prompt(prompt, texte_cahier_du_profil(db, user))
    try:
        texte = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), model=get_ai_model(db),
                         max_tokens=get_max_tokens(db, "idee"), temperature=get_temperature(db),
                         retry_max=get_retry_max(db), retry_wait_max=get_retry_wait_max(db))
    except LLMRateLimitError as e:
        log.warning("[proposer-theme] service très demandé : %s", e)
        raise HTTPException(429, "Le service est très demandé en ce moment. Réessayez dans un instant.")
    return {"available": True, "texte": texte.strip()}


_AUCUN_EXTRAIT_POUR_COMPETENCES = (
    "aSchool n'a pas trouvé, dans le référentiel officiel, de passage assez pertinent "
    "pour proposer des compétences fidèles au programme. Ajoutez vos compétences à la main."
)


class ProposerCompetencesBody(BaseModel):
    """Ce que l'écran envoie pour « Propose-moi des compétences » : le thème saisi en ①,
    qui ancre les suggestions. Le couple est LU EN BASE, jamais envoyé."""
    theme: str = ""


@router.post("/contenus/seances/proposer-competences")
def proposer_competences_seance(
    corps: ProposerCompetencesBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bouton « Propose-moi des compétences » de l'écran Séance (cartouche Contenu
    pédagogique) : aSchool propose 3 à 5 compétences/attendus TIRÉS DU PROGRAMME officiel,
    ancrés sur le THÈME saisi en cartouche ① — le prof adopte ou ignore, il ne rédige plus
    de mémoire. Même moule que « proposer-theme » (RAG + seuil du référentiel) et même
    règle d'or : pas de référentiel → available:false ; rien d'assez pertinent → message
    honnête. PAS de cahier des charges ici : les compétences viennent du programme SEUL."""
    from backend.contenu.activites import _referentiel_du_niveau  # même résolution que l'activité

    theme = corps.theme.strip()
    if not theme:
        raise HTTPException(400, "Décrivez d'abord le thème de la séance : les compétences proposées s'appuient dessus.")

    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    ref_id = _referentiel_du_niveau(db, niveau)
    if ref_id is None:
        return {"available": False}

    ref = (db.query(Referentiel.collection, Referentiel.filtres, Referentiel.score_min)
             .filter(Referentiel.id == ref_id).first())
    collection, filtres_json, seuil = ref
    filters = json.loads(filtres_json) if filtres_json else None
    requete = f"Compétences et attendus du programme de {matiere or 'la matière du prof'}, niveau {niveau}, autour de : {theme}"
    chunks = retrieve_pg(collection, requete, filters=filters, top_k=get_rag_top_k(db))
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        log.info("[proposer-competences] aucun chunk >= seuil %s (%s, %s) → available=false", seuil, collection, niveau)
        return {"available": False, "message": _AUCUN_EXTRAIT_POUR_COMPETENCES}

    referentiel_txt = "\n\n".join(c["text"] for c in chunks)
    prompt = get_prompt(db, "seance_proposer_competences").format(
        matiere=matiere or "", niveau=niveau, theme=theme, referentiel=referentiel_txt,
    )
    try:
        texte = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), model=get_ai_model(db),
                         max_tokens=get_max_tokens(db, "idee"), temperature=get_temperature(db),
                         retry_max=get_retry_max(db), retry_wait_max=get_retry_wait_max(db))
    except LLMRateLimitError as e:
        log.warning("[proposer-competences] service très demandé : %s", e)
        raise HTTPException(429, "Le service est très demandé en ce moment. Réessayez dans un instant.")

    # Une compétence par ligne (le prompt l'exige) — on nettoie les puces résiduelles, on borne à 6.
    competences = [l.strip(" \t-•*–—").strip() for l in texte.splitlines()]
    competences = [c for c in competences if c][:6]
    if not competences:
        return {"available": False, "message": _AUCUN_EXTRAIT_POUR_COMPETENCES}
    return {"available": True, "competences": competences}


class ProposerLigneBody(BaseModel):
    """Ce que l'écran envoie pour les « Propose-moi… » des champs à UNE ligne (matériel,
    contraintes) : le thème (obligatoire, il ancre la proposition) + le cadre déjà saisi.
    Le couple est LU EN BASE, jamais envoyé."""
    theme: str = ""
    mode: Optional[str] = None
    duree: Optional[int] = None
    contexte: str = ""


def _digest_seance(corps: ProposerLigneBody) -> str:
    """La séance telle que remplie, résumée pour le prompt — seulement ce qui est saisi."""
    lignes = [f"Thème de la séance : {corps.theme.strip()}"]
    if corps.mode:
        lignes.append(f"Mode : {corps.mode}")
    if corps.duree:
        lignes.append(f"Durée : {corps.duree} minutes")
    if corps.contexte.strip():
        lignes.append(f"Contexte de la classe : {corps.contexte.strip()}")
    return "\n".join(lignes)


def _proposer_ligne(cle_prompt: str, corps: ProposerLigneBody, user: User, db: Session) -> dict:
    """Tronc commun des « Propose-moi… » à une ligne (matériel, contraintes) — principe
    maison : aSchool propose, le prof corrige. PAS de RAG ici : le matériel et les
    contraintes ne sont pas du contenu du programme officiel, la proposition s'ancre
    honnêtement sur le thème et le cadre saisis (digest), sans rien prétendre du programme."""
    theme = corps.theme.strip()
    if not theme:
        raise HTTPException(400, "Décrivez d'abord le thème de la séance : la proposition s'appuie dessus.")
    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    prompt = get_prompt(db, cle_prompt).format(
        matiere=matiere or "", niveau=niveau, seance=_digest_seance(corps),
    )
    try:
        texte = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), model=get_ai_model(db),
                         max_tokens=get_max_tokens(db, "idee"), temperature=get_temperature(db),
                         retry_max=get_retry_max(db), retry_wait_max=get_retry_wait_max(db))
    except LLMRateLimitError as e:
        log.warning("[%s] service très demandé : %s", cle_prompt, e)
        raise HTTPException(429, "Le service est très demandé en ce moment. Réessayez dans un instant.")

    # Champ à UNE ligne : on aplatit les retours résiduels du modèle.
    ligne = " ".join(texte.strip().split())
    if not ligne:
        return {"available": False, "message": "Pas de proposition possible pour le moment. Remplissez le champ à la main."}
    return {"available": True, "texte": ligne}


@router.post("/contenus/seances/proposer-materiel")
def proposer_materiel_seance(
    corps: ProposerLigneBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bouton « Propose-moi du matériel nécessaire » de l'écran Séance."""
    return _proposer_ligne("seance_proposer_materiel", corps, user, db)


@router.post("/contenus/seances/proposer-contraintes")
def proposer_contraintes_seance(
    corps: ProposerLigneBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bouton « Propose-moi des contraintes spéciales » de l'écran Séance."""
    return _proposer_ligne("seance_proposer_contraintes", corps, user, db)


PHASES_ESQUISSE = {
    "a": "A. Mise en route",
    "b": "B. Activité principale",
    "c": "C. Retour / trace écrite",
}


class ProposerEsquisseBody(ProposerLigneBody):
    """« Propose-moi cette phase » de l'esquisse A/B/C : la phase visée + l'esquisse déjà
    saisie (les autres zones alimentent le prompt — la proposition complète un déroulé)."""
    phase: str = ""
    esquisse: dict = {}


@router.post("/contenus/seances/proposer-esquisse")
def proposer_esquisse_seance(
    corps: ProposerEsquisseBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bouton « Propose-moi cette phase » d'une zone de l'esquisse (A, B ou C) — principe
    maison : aSchool propose la phase visée, ancrée sur le thème/cadre ET sur les autres
    phases déjà esquissées ; le prof corrige. Pas de RAG (même logique que matériel)."""
    if corps.phase not in PHASES_ESQUISSE:
        raise HTTPException(400, "Phase inconnue — attendu : a, b ou c.")
    theme = corps.theme.strip()
    if not theme:
        raise HTTPException(400, "Décrivez d'abord le thème de la séance : la proposition s'appuie dessus.")
    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    # Digest = thème + cadre + les AUTRES phases déjà esquissées (la cohérence du déroulé).
    digest = _digest_seance(corps)
    autres = [f"{PHASES_ESQUISSE[k]} : {(corps.esquisse.get(k) or '').strip()}"
              for k in ("a", "b", "c")
              if k != corps.phase and (corps.esquisse.get(k) or "").strip()]
    if autres:
        digest += "\n\nPhases déjà esquissées par l'enseignant (à respecter) :\n" + "\n".join(autres)

    prompt = get_prompt(db, "seance_proposer_esquisse").format(
        matiere=matiere or "", niveau=niveau, seance=digest, phase=PHASES_ESQUISSE[corps.phase],
    )
    try:
        texte = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), model=get_ai_model(db),
                         max_tokens=get_max_tokens(db, "idee"), temperature=get_temperature(db),
                         retry_max=get_retry_max(db), retry_wait_max=get_retry_wait_max(db))
    except LLMRateLimitError as e:
        log.warning("[proposer-esquisse] service très demandé : %s", e)
        raise HTTPException(429, "Le service est très demandé en ce moment. Réessayez dans un instant.")

    ligne = " ".join(texte.strip().split())
    if not ligne:
        return {"available": False, "message": "Pas de proposition possible pour le moment. Remplissez la zone à la main."}
    return {"available": True, "texte": ligne}


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


@router.get("/contenus/seances/{seance_id}/activites")
def lister_activites_seance(
    seance_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Les activités RATTACHÉES à une séance — pour la cartouche « Activités de cette
    séance » de l'écran Séance et le détail de la liste Séances. Chaque ligne porte de quoi
    ROUVRIR l'activité dans son écran (reprise complète), comme les lignes de /mes-contenus."""
    seance = _seance_de(user, seance_id, db)
    activites = (
        db.query(Activite)
        .filter(Activite.user_id == user.id, Activite.seance_id == seance.id)
        .order_by(Activite.created_at.asc())
        .all()
    )
    return {"activites": [{
        "type": "activite",
        "id": a.id,
        "titre": a.objet or a.activite_label,
        "matiere": a.matiere,
        "niveau": a.niveau,
        "seance_id": a.seance_id,
        "resultat": a.resultat,
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
    } for a in activites]}


# ---------------------------------------------------------------------------
# Séquences du monde neuf — le PLAN se génère en STREAMING (les lignes apparaissent une à
# une à l'écran) et le plan EST la liste des séances : chaque ligne devient une vraie ligne
# `seances` (rattachée, ordonnée, déroulé vide = « à générer »). Jamais de plan stocké en
# texte à côté (zéro copie). Écriture (règle 0) : UNE transaction à la FIN du flux —
# séquence + séances ensemble (POST /contenus/sequences). Décisions utilisateur du 30/07.
# ---------------------------------------------------------------------------

_AUCUN_EXTRAIT_POUR_OBJECTIF = (
    "aSchool n'a pas trouvé, dans le référentiel officiel, de passage assez pertinent "
    "pour proposer un objectif fidèle. Décrivez votre objectif directement dans la zone "
    "de texte — ou dictez-le avec le micro."
)


@router.post("/contenus/sequences/proposer-objectif")
def proposer_objectif_sequence(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bouton « Propose-moi un objectif » de l'écran Séquence — même moule que le
    « Propose-moi un thème » de la séance : aSchool écrit l'objectif général à la place du
    prof, ANCRÉ sur le programme officiel du niveau (extraits RAG, seuil du référentiel lu
    en base), cahier des charges de l'établissement ajouté par-dessus. Règle d'or : pas de
    référentiel → available:false ; rien d'assez pertinent → message honnête."""
    from backend.contenu.activites import _referentiel_du_niveau  # même résolution que l'activité

    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    ref_id = _referentiel_du_niveau(db, niveau)
    if ref_id is None:
        return {"available": False}

    ref = (db.query(Referentiel.collection, Referentiel.filtres, Referentiel.score_min)
             .filter(Referentiel.id == ref_id).first())
    collection, filtres_json, seuil = ref
    filters = json.loads(filtres_json) if filtres_json else None
    requete = f"Objectif de séquence de {matiere or 'la matière du prof'}, niveau {niveau} : notions et objectifs du programme"
    chunks = retrieve_pg(collection, requete, filters=filters, top_k=get_rag_top_k(db))
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        log.info("[proposer-objectif] aucun chunk >= seuil %s (%s, %s) → available=false", seuil, collection, niveau)
        return {"available": False, "message": _AUCUN_EXTRAIT_POUR_OBJECTIF}

    referentiel_txt = "\n\n".join(c["text"] for c in chunks)
    prompt = get_prompt(db, "sequence_proposer_objectif").format(
        matiere=matiere or "", niveau=niveau, referentiel=referentiel_txt,
    )
    prompt = ajouter_cahier_au_prompt(prompt, texte_cahier_du_profil(db, user))
    try:
        texte = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), model=get_ai_model(db),
                         max_tokens=get_max_tokens(db, "idee"), temperature=get_temperature(db),
                         retry_max=get_retry_max(db), retry_wait_max=get_retry_wait_max(db))
    except LLMRateLimitError as e:
        log.warning("[proposer-objectif] service très demandé : %s", e)
        raise HTTPException(429, "Le service est très demandé en ce moment. Réessayez dans un instant.")
    return {"available": True, "texte": texte.strip()}


class ProposerCompetencesSequenceBody(BaseModel):
    """Ce que l'écran envoie pour « Propose-moi des compétences » de la SÉQUENCE :
    l'objectif saisi en ①, qui ancre les suggestions. Le couple est LU EN BASE."""
    objectif: str = ""


@router.post("/contenus/sequences/proposer-competences")
def proposer_competences_sequence(
    corps: ProposerCompetencesSequenceBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bouton « Propose-moi des compétences » de l'écran Séquence — même moule que la
    version séance (RAG + seuil du référentiel, PAS de cahier des charges : les compétences
    viennent du programme SEUL), ancré sur l'OBJECTIF général au lieu du thème."""
    from backend.contenu.activites import _referentiel_du_niveau  # même résolution que l'activité

    objectif = corps.objectif.strip()
    if not objectif:
        raise HTTPException(400, "Décrivez d'abord l'objectif général de la séquence : les compétences proposées s'appuient dessus.")

    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    ref_id = _referentiel_du_niveau(db, niveau)
    if ref_id is None:
        return {"available": False}

    ref = (db.query(Referentiel.collection, Referentiel.filtres, Referentiel.score_min)
             .filter(Referentiel.id == ref_id).first())
    collection, filtres_json, seuil = ref
    filters = json.loads(filtres_json) if filtres_json else None
    requete = f"Compétences et attendus du programme de {matiere or 'la matière du prof'}, niveau {niveau}, autour de : {objectif}"
    chunks = retrieve_pg(collection, requete, filters=filters, top_k=get_rag_top_k(db))
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        log.info("[proposer-competences-seq] aucun chunk >= seuil %s (%s, %s) → available=false", seuil, collection, niveau)
        return {"available": False, "message": _AUCUN_EXTRAIT_POUR_COMPETENCES}

    referentiel_txt = "\n\n".join(c["text"] for c in chunks)
    prompt = get_prompt(db, "sequence_proposer_competences").format(
        matiere=matiere or "", niveau=niveau, objectif=objectif, referentiel=referentiel_txt,
    )
    try:
        texte = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), model=get_ai_model(db),
                         max_tokens=get_max_tokens(db, "idee"), temperature=get_temperature(db),
                         retry_max=get_retry_max(db), retry_wait_max=get_retry_wait_max(db))
    except LLMRateLimitError as e:
        log.warning("[proposer-competences-seq] service très demandé : %s", e)
        raise HTTPException(429, "Le service est très demandé en ce moment. Réessayez dans un instant.")

    competences = [l.strip(" \t-•*–—").strip() for l in texte.splitlines()]
    competences = [c for c in competences if c][:6]
    if not competences:
        return {"available": False, "message": _AUCUN_EXTRAIT_POUR_COMPETENCES}
    return {"available": True, "competences": competences}


def _sequence_de(user: User, sequence_id: int, db: Session) -> Sequence:
    sequence = (
        db.query(Sequence)
        .filter(Sequence.id == sequence_id, Sequence.user_id == user.id)
        .first()
    )
    if not sequence:
        raise HTTPException(404, "Séquence introuvable.")
    return sequence


@router.get("/contenus/sequences/{sequence_id}/seances")
def lister_seances_sequence(
    sequence_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Les séances RATTACHÉES à une séquence, dans l'ordre du plan (position) — pour le plan
    de l'écran Séquence (reprise) et le détail de la page Séquences. Chaque ligne porte son
    ÉTAT (« à générer » = resultat vide) et de quoi ROUVRIR la séance dans son écran."""
    sequence = _sequence_de(user, sequence_id, db)
    seances = (
        db.query(Seance)
        .filter(Seance.user_id == user.id, Seance.sequence_id == sequence.id)
        .order_by(Seance.position.asc(), Seance.id.asc())
        .all()
    )
    return {"seances": [{
        "type": "seance",
        "id": s.id,
        "titre": s.titre,
        "position": s.position,
        "matiere": s.matiere,
        "niveau": s.niveau,
        "resultat": s.resultat,
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
    } for s in seances]}


class SequencePlanGeneration(BaseModel):
    """Ce que l'écran envoie pour GÉNÉRER le plan : le formulaire entier, sans les lignes.
    Le couple matière/niveau est lu EN BASE (couple de travail), jamais envoyé."""
    objectif: str
    contexte: str = ""
    ampleur: str = ""
    competences: list[str] = []


class SequenceCorps(SequencePlanGeneration):
    """Ce que l'écran enregistre à la FIN du flux (règle 0) : le formulaire + les lignes du
    plan — chaque ligne devient une vraie séance « à générer »."""
    seances: list[str] = []


def _bloc_precisions_sequence(req: SequencePlanGeneration) -> str:
    """Les champs optionnels du formulaire Séquence, ajoutés au prompt du plan — uniquement
    ceux qui sont remplis. Vide si le prof n'a rien précisé."""
    lignes = []
    if req.contexte.strip():
        lignes.append(f"- Contexte de la classe : {req.contexte.strip()}")
    if req.ampleur.strip():
        lignes.append(f"- Ampleur souhaitée pour la séquence : {req.ampleur.strip()}")
    comps = [c.strip() for c in req.competences if c and c.strip()]
    if comps:
        lignes.append("- Compétences / attendus visés : " + " ; ".join(comps))
    if not lignes:
        return ""
    return "PRÉCISIONS DE L'ENSEIGNANT — à intégrer au plan :\n" + "\n".join(lignes)


def _nettoyer_ligne_plan(ligne: str) -> str:
    """Une ligne du plan → un titre de séance propre : puces et numérotation de tête
    retirées (« 3. », « 12) »…), même si le prompt les interdit — on ne fait jamais
    confiance à la forme d'une sortie de modèle."""
    l = ligne.strip(" \t-•*–—").strip()
    i = 0
    while i < len(l) and l[i].isdigit():
        i += 1
    if 0 < i < len(l) and l[i] in ".)":
        l = l[i + 1:]
    return l.strip(" \t-•*–—").strip()


@router.post("/contenus/sequences/generer-plan")
def generer_plan_sequence(
    req: SequencePlanGeneration,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Génération du PLAN d'une séquence en STREAMING (SSE delta/error/done) — décision
    utilisateur du 30/07 : les lignes apparaissent une à une à l'écran, jamais d'appel long
    silencieux. Même mécanique que la génération de séance (prompt au registre, créneau LLM,
    incident si le flux casse). L'ÉCRITURE (règle 0) suit côté écran à la FIN du flux :
    POST /contenus/sequences — une transaction, séquence + séances ensemble."""
    if not req.objectif.strip():
        raise HTTPException(400, "Décrivez d'abord l'objectif général de la séquence.")
    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    prompt = get_prompt(db, "sequence_generer_plan").format(
        matiere=matiere or "", niveau=niveau, objectif=req.objectif.strip(),
    )
    precisions = _bloc_precisions_sequence(req)
    if precisions:
        prompt = prompt + "\n\n" + precisions

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
        log.warning("/api/contenus/sequences/generer-plan — service très demandé : %s", e)
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
            log.warning("/api/contenus/sequences/generer-plan — flux interrompu : %s", e)
            ref = creer_incident(
                endpoint="/api/contenus/sequences/generer-plan",
                error=f"{type(e).__name__}: {e}",
                provider=provider, model=model,
                matiere=matiere, niveau=niveau, type_activite="Séquence (plan)",
                consigne=req.objectif.strip(), user_email=email,
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


@router.post("/contenus/sequences")
def creer_sequence(
    corps: SequenceCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fin du flux réussie = la séquence NAÎT en base avec SES séances, en UNE transaction
    (règle 0, décision 30/07). Chaque ligne du plan = une vraie ligne `seances` : rattachée
    (sequence_id), ordonnée (position 1..n), titre pré-rempli, déroulé VIDE (« à générer »).
    Pas de table de versions : le résultat d'une séquence, ce sont ses séances. Le plan ne
    se génère que sur une séquence NEUVE (v1) : ce POST crée, il n'écrase jamais."""
    if not corps.objectif.strip():
        raise HTTPException(400, "Décrivez d'abord l'objectif général de la séquence.")
    titres = [t for t in (_nettoyer_ligne_plan(l) for l in corps.seances) if t]
    if not titres:
        raise HTTPException(400, "Le plan est vide : générez d'abord la liste des séances.")
    if len(titres) > 300:
        raise HTTPException(400, "Le plan dépasse 300 séances — précisez une ampleur plus réduite et régénérez.")
    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    sequence = Sequence(
        user_id=user.id,
        titre=corps.objectif.strip(),
        contexte=corps.contexte.strip(),
        ampleur=corps.ampleur.strip(),
        competences=json.dumps([c.strip() for c in corps.competences if c and c.strip()], ensure_ascii=False),
        matiere=matiere or None,
        niveau=niveau,
    )
    db.add(sequence)
    db.flush()
    seances = [
        Seance(user_id=user.id, sequence_id=sequence.id, position=i + 1,
               titre=t, matiere=matiere or None, niveau=niveau)
        for i, t in enumerate(titres)
    ]
    db.add_all(seances)
    db.commit()
    return {"id": sequence.id, "seances": [
        {"id": s.id, "titre": s.titre, "position": s.position, "resultat": ""}
        for s in seances
    ]}
