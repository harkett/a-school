"""
feedback_client.py — Client HTTP pour le microservice A-FEEDBACK (AFIA)
=======================================================================

INTÉGRATION DANS UNE APP CLIENTE
---------------------------------
1. Copier ce fichier à la racine de l'application cible.
2. Ajouter dans le .env de l'app : FEEDBACK_URL=http://localhost:8001
3. Appeler send_async() dans une app FastAPI/asyncio, send() ailleurs.

UTILISATION — app FastAPI (async) :
    from feedback_client import send_async
    await send_async(app="nom-app", user_id="user_42", message="...", rating=5)

UTILISATION — script ou app non-async :
    from feedback_client import send
    send(app="nom-app", user_id="user_42", message="...", rating=4)

RÈGLES IMPORTANTES
------------------
- Le champ `app` doit être en minuscules et correspondre à la clé dans APP_EMAILS
  sur le serveur A-FEEDBACK (déclenche la notification email à l'admin).
- Les deux fonctions retournent True si succès, False en cas d'erreur réseau ou HTTP.
- Un retour False est silencieux : l'app cliente ne crashe jamais à cause d'A-FEEDBACK.
- Timeout fixé à 3 secondes pour ne pas bloquer l'utilisateur.

CHAMPS
------
- app      : identifiant de l'application (str, max 100 car.) — ex : "a-viewcam"
- user_id  : identifiant de l'utilisateur connecté (str, max 255 car.)
- message  : texte du retour (str, 1–2000 car.)
- rating   : note de 1 à 5 (int)
"""

import logging
import os

import httpx

FEEDBACK_URL = os.getenv("FEEDBACK_URL", "http://localhost:8001")
logger = logging.getLogger(__name__)


async def send_async(
    app: str, user_id: str, message: str, rating: int,
    category: str | None = None, user_email: str | None = None
) -> bool:
    """Envoie un retour de façon async — à utiliser dans les apps FastAPI / asyncio."""
    try:
        payload: dict = {"app": app, "user_id": user_id, "message": message, "rating": rating}
        if category is not None:
            payload["category"] = category
        if user_email is not None:
            payload["user_email"] = user_email
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(f"{FEEDBACK_URL}/feedback", json=payload)
            response.raise_for_status()
            return response.status_code == 201
    except httpx.HTTPStatusError as e:
        logger.warning("[A-FEEDBACK] Erreur HTTP %s", e.response.status_code)
        return False
    except httpx.RequestError:
        logger.warning("[A-FEEDBACK] Service indisponible — retour non enregistré")
        return False


def send(
    app: str, user_id: str, message: str, rating: int,
    category: str | None = None, user_email: str | None = None
) -> bool:
    """Envoie un retour de façon synchrone — pour les scripts, CLI ou apps non-async."""
    try:
        payload: dict = {"app": app, "user_id": user_id, "message": message, "rating": rating}
        if category is not None:
            payload["category"] = category
        if user_email is not None:
            payload["user_email"] = user_email
        response = httpx.post(f"{FEEDBACK_URL}/feedback", json=payload, timeout=3.0)
        response.raise_for_status()
        return response.status_code == 201
    except httpx.HTTPStatusError as e:
        logger.warning("[A-FEEDBACK] Erreur HTTP %s", e.response.status_code)
        return False
    except httpx.RequestError:
        logger.warning("[A-FEEDBACK] Service indisponible — retour non enregistré")
        return False
