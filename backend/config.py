import os

# Pas de load_dotenv() ici : le .env est chargé par les points d'entrée
# (backend/main.py, conftest.py, alembic/env.py) AVANT tout import de ce module.
# Ce module reste donc pur : il lit os.getenv, sans effet de bord à l'import.

AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")

# Une clé par USAGE facturé (stats par usage sur le tableau de bord du fournisseur).
# Voix + OCR ne lisent PLUS de clé ici : leur NOM de variable vit EN BASE (settings
# cle_env_ocr / cle_env_dictee) et le backend résout la clé par appel — ce module reste pur.
#   GROQ_API_KEY       : texte Groq UNIQUEMENT (optionnel ; vide aujourd'hui car le texte
#                        passe par Anthropic — _groq lève une erreur claire si appelé sans clé).
#   CLAUDE_API_KEY_TEXTE : texte Anthropic (optionnel à l'import ; _anthropic lève si appelé sans).
# Jamais le nom réservé ANTHROPIC_API_KEY : Claude Code le lirait → facturation croisée.
# (Mettre AUSSI ces deux noms en base = branche « fournisseurs » ai_fournisseurs.cle_env.)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
CLAUDE_API_KEY_TEXTE = os.getenv("CLAUDE_API_KEY_TEXTE", "")

# Régulation de concurrence des appels LLM (infra, pas un réglage prof) : nombre d'appels
# sortants simultanés autorisés, et délai max d'attente d'un créneau avant erreur honnête.
# Config d'infra pure : env, jamais en base.
AI_MAX_CONCURRENCY = int(os.getenv("AI_MAX_CONCURRENCY", "8"))
AI_SLOT_TIMEOUT = float(os.getenv("AI_SLOT_TIMEOUT", "30"))
