"""Singleton sentence-transformers — modele d'embeddings multilingue charge une fois.

Modele : paraphrase-multilingual-MiniLM-L12-v2 (~120 Mo, dim 384). Charge au premier
appel par la voie DIRECTE sentence-transformers (sans ChromaDB), conserve en RAM pour
tous les appels suivants. C'est le modele utilise par le RAG pgvector (embed_texts).
"""
import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_st_model: Any = None
_lock = threading.Lock()  # le modele peut etre charge en parallele (prechauffe au boot + 1er clic)


def get_st_model() -> Any:
    """Singleton SentenceTransformer. Charge une fois, thread-safe (double-checked locking) :
    la prechauffe lancee au demarrage du serveur et une requete concurrente ne doivent
    jamais charger le modele deux fois."""
    global _st_model
    if _st_model is None:
        with _lock:
            if _st_model is None:
                from sentence_transformers import SentenceTransformer
                logger.info(f"[RAG] Chargement SentenceTransformer : {EMBEDDING_MODEL}")
                _st_model = SentenceTransformer(EMBEDDING_MODEL)
                logger.info("[RAG] Modele d'embedding pret")
    return _st_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeddings d'une liste de textes par la voie DIRECTE sentence-transformers, dim 384."""
    model = get_st_model()
    vecs = model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=False)
    return [v.tolist() for v in vecs]
