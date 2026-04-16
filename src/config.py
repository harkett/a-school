import os
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gemini-1.5-flash")

if not AI_API_KEY:
    raise ValueError("AI_API_KEY manquant dans le fichier .env")
