import os
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")

# Une clé par fournisseur (étape 3 « séparer les clés ») — chaque adaptateur lit SA clé.
# GROQ_API_KEY   : texte Groq + OCR + dictée Whisper (Groq est le seul chemin voix/OCR).
# CLAUDE_API_KEY : texte Anthropic (optionnel à l'import ; _anthropic lève si appelé sans clé).
# Jamais le nom réservé ANTHROPIC_API_KEY : Claude Code le lirait → facturation croisée.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

# Régulation de concurrence des appels LLM (infra, pas un réglage prof) : nombre d'appels
# sortants simultanés autorisés, et délai max d'attente d'un créneau avant erreur honnête.
# Reste dans src/ (pur) : env, jamais en base — src/ n'importe jamais backend/.
AI_MAX_CONCURRENCY = int(os.getenv("AI_MAX_CONCURRENCY", "8"))
AI_SLOT_TIMEOUT = float(os.getenv("AI_SLOT_TIMEOUT", "30"))

# Garde-fou : la dictée (Whisper) et l'OCR passent TOUJOURS par Groq → GROQ_API_KEY est obligatoire.
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY manquant dans le fichier .env (obligatoire : voix + OCR passent par Groq)")
