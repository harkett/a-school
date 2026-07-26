import os

# Pas de load_dotenv() ici : le .env est chargé par les points d'entrée
# (backend/main.py, conftest.py, alembic/env.py) AVANT tout import de ce module.
# Ce module reste donc pur : il lit os.getenv, sans effet de bord à l'import.

AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")

# AUCUNE clé LLM n'est lue ici. Le NOM de la variable d'env de chaque clé vit EN BASE :
# texte via ai_fournisseurs.cle_env (résolu par get_cle_texte), OCR / dictée via
# settings.cle_env_ocr / cle_env_dictee (get_cle_api). Le backend lit le nom en base puis
# os.getenv(nom) à chaque appel ; la VALEUR (le secret) reste dans le .env, jamais en base.
# Jamais le nom réservé ANTHROPIC_API_KEY : Claude Code le lirait → facturation croisée.
# Ce module reste pur : os.getenv sans effet de bord.

# Régulation de concurrence des appels LLM (infra, pas un réglage prof) : nombre d'appels
# sortants simultanés autorisés, et délai max d'attente d'un créneau avant erreur honnête.
# Config d'infra pure : env, jamais en base.
AI_MAX_CONCURRENCY = int(os.getenv("AI_MAX_CONCURRENCY", "8"))
AI_SLOT_TIMEOUT = float(os.getenv("AI_SLOT_TIMEOUT", "30"))
