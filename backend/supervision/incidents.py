"""Journal technique des incidents de génération (échecs côté IA).

Un incident est capturé AUTOMATIQUEMENT au moment du plantage, que le prof le signale ou non
(RÈGLE 23 : l'écran ne montre qu'un message humain, le détail technique va en base pour l'admin).
`creer_incident` renvoie une RÉFÉRENCE courte (ex. « INC-8F3A2C90 ») remontée à l'écran et qui,
plus tard, relie le message du prof (feedbacks.feedback_id) à cet incident.
"""
import logging
import uuid

from backend.core.database import session_pour, SCHEMA_REEL
from backend.core.models_db import Incident

log = logging.getLogger(__name__)

_MAX_ERREUR = 5000  # borne de prudence : une trace/HTML géant ne doit pas gonfler la ligne


def nouvelle_reference() -> str:
    """Référence d'incident courte et unique côté affichage (« INC-XXXXXXXX »)."""
    return "INC-" + uuid.uuid4().hex[:8].upper()


def creer_incident(
    *,
    endpoint: str,
    error: str,
    provider: str | None = None,
    model: str | None = None,
    matiere: str | None = None,
    niveau: str | None = None,
    type_activite: str | None = None,
    consigne: str | None = None,
    user_email: str | None = None,
) -> str | None:
    """Enregistre un incident technique et renvoie sa RÉFÉRENCE (ou None si l'écriture échoue).

    Ouvre sa PROPRE session (SessionLocal) : appelé depuis le flux SSE, où la session de requête est
    destinée à se fermer. Ne LÈVE JAMAIS : l'échec d'écriture d'un incident ne doit pas casser la
    gestion d'erreur en cours — on log et on renvoie None (l'écran retombe alors sur le message
    générique, sans référence).
    """
    ref = nouvelle_reference()
    try:
        with session_pour(SCHEMA_REEL) as db:
            db.add(Incident(
                ref=ref,
                endpoint=endpoint,
                error=(error or "")[:_MAX_ERREUR],
                provider=provider,
                model=model,
                matiere=matiere,
                niveau=niveau,
                type_activite=type_activite,
                consigne=(consigne or None),
                user_email=user_email,
            ))
            db.commit()
        return ref
    except Exception as e:  # incident non bloquant : on ne casse jamais le flux d'erreur
        log.error("Incident %s non enregistré : %s: %s", ref, type(e).__name__, e)
        return None
