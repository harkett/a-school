"""Trace de consommation des appels LLM — ce que lit l'écran « IA › Statistiques ».

Pendant du journal applicatif de `backend/llm/generator._journal_appel`, mais DURABLE : le journal
répond à la question posée sur le moment (« cet appel a-t-il été coupé ? »), cette table répond aux
questions qui s'additionnent (« qu'a coûté la semaine ? », « quel outil consomme ? »).

RÈGLE DE CE MODULE : une statistique ne casse JAMAIS l'outil du prof. Toute écriture est enveloppée,
n'échoue pas vers l'appelant, et se contente d'un log si la base refuse. Perdre une ligne de mesure
est sans conséquence ; perdre une génération à cause d'une ligne de mesure serait absurde.
"""
import logging

from backend.core.database import session_pour, SCHEMA_REEL
from backend.core.models_db import UsageLlm

log = logging.getLogger(__name__)


def enregistrer_usage(
    *,
    fournisseur: str,
    modele: str,
    outil: str | None = None,
    tokens_entree: int | None = None,
    tokens_sortie: int | None = None,
    tokens_cache_ecriture: int | None = None,
    tokens_cache_lecture: int | None = None,
    duree_ms: int | None = None,
    motif_arret: str | None = None,
    depuis_cache: bool = False,
    resultat: str = "ok",
    code_http: int | None = None,
    rang: int | None = None,
) -> None:
    """Pose UNE ligne de TENTATIVE — aboutie ou non. Ne lève jamais.

    `resultat` / `code_http` / `rang` : ce qu'est devenue la tentative, ce que le fournisseur a
    répondu, et sa place dans la liste. Leurs défauts décrivent le succès d'un appel unique, si
    bien qu'un appelant qui ne les connaît pas écrit exactement la ligne qu'il écrivait avant.

    Ouvre sa PROPRE session (SessionLocal) plutôt que d'emprunter celle de la requête : l'appel part
    aussi du flux SSE, où la session de requête est destinée à se fermer avant la fin de la
    génération — c'est exactement le choix déjà fait par `supervision/incidents.creer_incident`.
    """
    try:
        with session_pour(SCHEMA_REEL) as db:
            db.add(UsageLlm(
                fournisseur=fournisseur,
                modele=modele,
                outil=outil,
                tokens_entree=tokens_entree,
                tokens_sortie=tokens_sortie,
                # Tokens du cache de prompt du FOURNISSEUR. Anthropic les sort de `input_tokens` :
                # les perdre ici ferait afficher une facture dix fois trop basse.
                tokens_cache_ecriture=tokens_cache_ecriture,
                tokens_cache_lecture=tokens_cache_lecture,
                duree_ms=duree_ms,
                # Le motif vient du fournisseur et peut être n'importe quelle chaîne : on borne à la
                # largeur de la colonne plutôt que de laisser la base rejeter toute la ligne.
                motif_arret=(str(motif_arret)[:50] if motif_arret is not None else None),
                # Rejeu du cache disque : l'appel a bien eu lieu côté logiciel, mais rien n'est
                # parti chez le fournisseur — tokens et coût à 0, et l'écran le dit au lieu de
                # laisser croire à un appel gratuit.
                depuis_cache=depuis_cache,
                # Borné à la largeur de la colonne, comme motif_arret : une mesure ne fait jamais
                # rejeter la ligne entière.
                resultat=(str(resultat)[:10] if resultat else "ok"),
                code_http=code_http,
                rang=rang,
            ))
            db.commit()
    except Exception as e:  # jamais bloquant : la mesure ne casse pas la génération
        log.error("Usage LLM non enregistré : %s: %s", type(e).__name__, e)
