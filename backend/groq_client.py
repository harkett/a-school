import logging
import requests
from fastapi import HTTPException
from src.config import AI_API_KEY

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

FALLBACK_CHAIN = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
]

FALLBACK_STATUSES = {429, 413, 503}

_headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}

log = logging.getLogger(__name__)


def call_groq(body: dict) -> str:
    primary_model = body.get("model")
    models_to_try = [primary_model] + [m for m in FALLBACK_CHAIN if m != primary_model]

    for i, model in enumerate(models_to_try):
        attempt_body = {**body, "model": model}
        r = requests.post(GROQ_URL, headers=_headers, json=attempt_body, timeout=90)

        if r.ok:
            if i > 0:
                log.warning(f"Groq fallback réussi sur {model} (primaire={primary_model})")
            return r.json()["choices"][0]["message"]["content"]

        if r.status_code in FALLBACK_STATUSES:
            log.warning(f"Groq {r.status_code} sur {model} — passage au suivant")
            continue

        raise HTTPException(status_code=502, detail=f"Erreur Groq {r.status_code}: {r.text[:200]}")

    raise HTTPException(status_code=429, detail="Tous les modèles Groq sont indisponibles — réessayez dans quelques minutes.")
