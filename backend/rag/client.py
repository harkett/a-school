"""Singleton ChromaDB persistant — point d'entree unique pour tous les routers.

La base vit dans backend/rag/chroma_db/ (copie depuis le POC le 15/05/2026).
Le client est instancie une seule fois au premier appel et reutilise ensuite.
"""
from pathlib import Path
from typing import Any
import logging

import chromadb

logger = logging.getLogger(__name__)

DB_DIR = Path(__file__).parent / "chroma_db"

_client: Any = None


def get_client() -> Any:
    """Renvoie le client ChromaDB singleton. Initialise au premier appel."""
    global _client
    if _client is None:
        if not DB_DIR.exists():
            raise RuntimeError(
                f"ChromaDB introuvable : {DB_DIR}. "
                f"Lance l'ingestion d'un referentiel (python -m backend.rag.ingest_referentiel)."
            )
        logger.info(f"[RAG] Initialisation ChromaDB depuis {DB_DIR}")
        _client = chromadb.PersistentClient(path=str(DB_DIR))
    return _client
