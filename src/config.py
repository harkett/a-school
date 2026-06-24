import os
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")

# Régulation de concurrence des appels LLM (infra, pas un réglage prof) : nombre d'appels
# sortants simultanés autorisés, et délai max d'attente d'un créneau avant erreur honnête.
# Reste dans src/ (pur) : env, jamais en base — src/ n'importe jamais backend/.
AI_MAX_CONCURRENCY = int(os.getenv("AI_MAX_CONCURRENCY", "8"))
AI_SLOT_TIMEOUT = float(os.getenv("AI_SLOT_TIMEOUT", "30"))

if not AI_API_KEY:
    raise ValueError("AI_API_KEY manquant dans le fichier .env")
