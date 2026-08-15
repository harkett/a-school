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

from backend.securite import comptes
from backend.core.database import get_db, schema_de_session
from backend.core.resolution_couple import referentiel_du_niveau_nomme
from backend.core.models import ExempleReferentielResponse
from backend.core.models_db import Niveau, Referentiel, User
from backend.prof.profil import couple_de_travail, texte_cahier_du_profil
from backend.rag.pgvector_store import retrieve_pg
from backend.systeme.admin import (get_ai_model, get_ai_provider, get_cle_texte, get_max_tokens,
                                   get_rag_top_k, get_retry_max, get_retry_wait_max, get_temperature)
from backend.llm.generator import generate, LLMRateLimitError
from backend.llm.prompts import build_exemple_referentiel_prompt, ajouter_cahier_au_prompt

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
# jamais de formulation par matière en dur, et jamais de supposition sur l'âge de l'élève : les
# cinq autres requêtes RAG du projet (activites.py, mes_contenus.py ×4) sont neutres, celle-ci
# l'est enfin aussi.
#
# CE QUI A ÉTÉ MESURÉ (02/08/2026), sur les DEUX référentiels réels — bebes_0_1_an (27 chunks,
# 5 matières) et bts_ciel_option_a (46 chunks, 6 matières), seuil 0.3 pour les deux.
#
#   LA MÉTRIQUE : le nombre de chunks de RANG 1 DISTINCTS sur l'ensemble des matières du
#   couple. Une requête qui rend le MÊME extrait pour six matières différentes n'ancre pas six
#   fois, elle ancre une fois — et le score, lui, ne le montre pas.
#
#   NE PAS MESURER LE SEUIL : il ne discrimine RIEN ici. Tous les chunks des deux collections
#   passent 0.3, pour toutes les formulations essayées (27/27 et 46/46). Le nombre d'extraits
#   retenus vaut donc toujours 4 (rag_top_k), quelle que soit la requête. Ce qui change n'est
#   pas COMBIEN d'extraits remontent, mais LESQUELS. Inutile de recompter, c'est fait.
#
#   NE PAS SE FIER AU SCORE DE RANG 1 NON PLUS : entre l'ancienne formulation et celle-ci,
#   l'écart moyen tient dans 0.04 sur des scores autour de 0.63 — un tableau de scores conclut
#   « ça ne change presque rien », et c'est faux.
#
#   RÉSULTATS (rang 1 distincts, deux relevés indépendants) :
#
#                                     Bébés        BTS
#     ancienne (« activité d'éveil »)  5/5      2/6 et 3/6
#     celle-ci (« idée d'activité »)  4/5 et 5/5    4/6
#
#   Sept autres formulations ont été essayées (nom seul, « contenus et attendus du programme »,
#   variantes activité/pédagogique) : aucune ne dépasse 4/6 sur BTS, et toutes font moins bien
#   que celles-ci au total. Aucune n'atteint 5/5 sur Bébés ET plus de 2/6 sur BTS.
#
# CE QUE LA MESURE A MONTRÉ AU PASSAGE, et que la requête ne peut pas réparer : sous l'ancienne
# formulation, le chunk de rang 1 de CINQ matières BTS sur six était le même — « C11 MAINTENIR
# UN RÉSEAU INFORMATIQUE — BTS CIEL Option B », un extrait de l'Option B servi dans un
# référentiel Option A, y compris pour l'anglais. La collection contient 10 chunks Option B sur
# 46, et 4 doublons (46 lignes pour 42 textes distincts). Aucune formulation ne choisit bien
# dans un sac pollué : c'est l'ingestion qu'il faut reprendre, pas cette ligne.
REQUETE_GABARIT = "Idée d'activité de {matiere}, niveau {niveau}, ancrée sur le programme"


def _resolve_collection(db: Session, niveau: str) -> tuple[str, dict | None, float] | None:
    """Niveau → (collection, filtres ChromaDB, seuil). None = pas de référentiel pour ce couple.

    Data-driven : lit la table `referentiels` (plus de couple en dur, plus de seuil en dur).
    Jointure DIRECTE referentiels → niveaux en UN seul SELECT (n.nom = :niveau), pas « résoudre
    l'id puis requêter » (forme fragile si un nom de niveau n'est pas unique).

    Trois branches assumées :
      - 0 ligne → None (couple « en construction » : on n'invente RIEN).
      - 1 ligne → (collection, filtres parsés depuis la colonne JSON, seuil `score_min`).
      - >1 ligne → on LÈVE bruyamment. Deux niveaux de même nom dans deux cycles
        différents sont légitimes par design (clé réelle = (nom, cycle_id)) et /api/...
        n'envoie pas le cycle → on ne peut pas trancher ici. C'est une AMBIGUÏTÉ de nom,
        pas une corruption : on refuse plutôt que de choisir une ligne au hasard."""
    if not niveau:
        return None
    # LA porte unique (15/08/2026) : le référentiel qui SERT ce niveau, pas celui qui le porte.
    # Un programme de cycle en sert plusieurs — cherché ici sur `referentiels.niveau_id`, il
    # laissait les profs des autres années du cycle sans aucun extrait.
    rid = referentiel_du_niveau_nomme(db, niveau)
    if rid is None:
        return None
    if len(rows) > 1:
        log.error(f"[exemple-ref] ambiguïté niveau : {len(rows)} référentiels pour nom={niveau!r}")
        raise HTTPException(500, f"Ambiguïté niveau : {len(rows)} référentiels trouvés pour ce nom de niveau. Configuration à corriger.")
    collection, filtres_json, score_min = rows[0]
    filters = json.loads(filtres_json) if filtres_json else None
    return collection, filters, score_min


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = comptes.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


@router.post("/exemple-referentiel", response_model=ExempleReferentielResponse)
def api_exemple_referentiel(
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Le couple (matière + niveau) est LU EN BASE — le couple de TRAVAIL du prof, résolu
    par couple_de_travail (travail si posé, sinon profil). L'écran n'envoie plus rien
    (décision du 25/07) : le document d'exemple suit TOUJOURS le couple que le prof voit."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(401, "Non connecté.")
    matiere, niveau, _ = couple_de_travail(db, user)
    if not matiere or not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    resolved = _resolve_collection(db, niveau)
    if resolved is None:
        # Règle d'or : pas de référentiel pour ce couple → on n'invente RIEN.
        log.info(f"[exemple-ref] aucun référentiel pour niveau='{niveau}' → available=false")
        return ExempleReferentielResponse(available=False)

    collection, filters, seuil = resolved
    # Filtre STRICT de pertinence : un chunk sous le seuil n'ancre JAMAIS une génération
    # (pas de « meilleur quand même »). Le seuil vit EN BASE, par référentiel
    # (`referentiels.score_min`, résolu ci-dessus) — plus aucune constante en dur.
    requete = REQUETE_GABARIT.format(matiere=matiere, niveau=niveau)
    chunks = retrieve_pg(collection, requete, filters=filters, top_k=get_rag_top_k(db),
                         schema=schema_de_session(db), annee=niveau)
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        # Rien d'assez pertinent : on n'invente RIEN, on le dit honnêtement au prof (generate PAS appelé).
        log.info(f"[exemple-ref] aucun chunk >= seuil {seuil} ({collection}, matiere='{matiere}') → available=false + message")
        return ExempleReferentielResponse(available=False, message=AUCUN_EXTRAIT_PERTINENT)

    prompt = build_exemple_referentiel_prompt(db, chunks, matiere=matiere, niveau=niveau)
    # Cahier des charges de l'établissement (get, zéro copie) ajouté par-dessus le programme officiel —
    # même geste que générer et « Propose-moi une idée ». Pas de cahier → prompt inchangé.
    prompt = ajouter_cahier_au_prompt(db, prompt, texte_cahier_du_profil(db, user))
    try:
        # retry_max / retry_wait_max : même politique de rattrapage qu'ailleurs, lue en base.
        # Elle manquait ici : le réglage `ai_retry_max` de l'admin ne s'appliquait pas.
        texte = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), model=get_ai_model(db),
                         max_tokens=get_max_tokens(db, "exemple"), temperature=get_temperature(db),
                         retry_max=get_retry_max(db), retry_wait_max=get_retry_wait_max(db),
                         outil="exemple")
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    log.info(f"[exemple-ref] généré pour couple ({matiere}, {niveau}) — {len(chunks)} chunks ancrés (>= {seuil})")
    return ExempleReferentielResponse(available=True, texte=texte)
