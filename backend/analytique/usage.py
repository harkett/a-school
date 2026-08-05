"""Trace de consommation des appels LLM — ce que lit l'écran « IA › Statistiques ».

Pendant du journal applicatif de `backend/llm/generator._journal_appel`, mais DURABLE : le journal
répond à la question posée sur le moment (« cet appel a-t-il été coupé ? »), cette table répond aux
questions qui s'additionnent (« qu'a coûté la semaine ? », « quel outil consomme ? »).

RÈGLE DE CE MODULE : une statistique ne casse JAMAIS l'outil du prof. Toute écriture est enveloppée,
n'échoue pas vers l'appelant, et se contente d'un log si la base refuse. Perdre une ligne de mesure
est sans conséquence ; perdre une génération à cause d'une ligne de mesure serait absurde.
"""
import logging

from backend.core.database import SessionLocal
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
) -> None:
    """Pose UNE ligne de consommation. Ne lève jamais.

    Ouvre sa PROPRE session (SessionLocal) plutôt que d'emprunter celle de la requête : l'appel part
    aussi du flux SSE, où la session de requête est destinée à se fermer avant la fin de la
    génération — c'est exactement le choix déjà fait par `supervision/incidents.creer_incident`.
    """
    try:
        with SessionLocal() as db:
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
            ))
            db.commit()
    except Exception as e:  # jamais bloquant : la mesure ne casse pas la génération
        log.error("Usage LLM non enregistré : %s: %s", type(e).__name__, e)
