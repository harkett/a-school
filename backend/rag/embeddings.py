"""Singleton sentence-transformers — modele d'embeddings multilingue charge une fois.

Modele : paraphrase-multilingual-MiniLM-L12-v2 (~120 Mo, dim 384).
Charge au premier appel via ChromaDB embedding_functions, conserve en RAM
pour tous les appels suivants. Identique a la pile validee par le POC.
"""
import logging
from typing import Any

from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_embedding_fn: Any = None


def get_embedding_function() -> Any:
    """Renvoie la fonction d'embedding singleton. Charge le modele au premier appel."""
    global _embedding_fn
    if _embedding_fn is None:
        logger.info(f"[RAG] Chargement du modele d'embedding : {EMBEDDING_MODEL}")
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        logger.info("[RAG] Modele d'embedding pret")
    return _embedding_fn
