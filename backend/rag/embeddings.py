"""Singleton sentence-transformers — modele d'embeddings multilingue charge une fois.

Modele : paraphrase-multilingual-MiniLM-L12-v2 (~120 Mo, dim 384).
Charge au premier appel via ChromaDB embedding_functions, conserve en RAM
pour tous les appels suivants. Identique a la pile validee par le POC.
"""
import logging
import threading
from typing import Any

from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_embedding_fn: Any = None
_lock = threading.Lock()  # le modele peut etre charge en parallele (prechauffe au boot + 1er clic)


def get_embedding_function() -> Any:
    """Renvoie la fonction d'embedding singleton. Charge le modele au premier appel.

    Thread-safe (double-checked locking) : la prechauffe lancee au demarrage du
    serveur et une requete concurrente ne doivent jamais charger le modele deux fois."""
    global _embedding_fn
    if _embedding_fn is None:
        with _lock:
            if _embedding_fn is None:
                logger.info(f"[RAG] Chargement du modele d'embedding : {EMBEDDING_MODEL}")
                _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=EMBEDDING_MODEL
                )
                logger.info("[RAG] Modele d'embedding pret")
    return _embedding_fn


# --- Voie directe sentence-transformers (decouplee de ChromaDB) — etape 1 refonte pgvector ---
# N'enleve RIEN : get_embedding_function() (ChromaDB) reste en place. On ajoute un acces
# DIRECT au MEME modele, pour pouvoir embarquer sans ChromaDB (futur remplissage de pgvector).
_st_model: Any = None


def get_st_model() -> Any:
    """Singleton SentenceTransformer (le MEME modele que la voie ChromaDB). Charge une fois.
    Thread-safe (meme verrou que la voie ChromaDB)."""
    global _st_model
    if _st_model is None:
        with _lock:
            if _st_model is None:
                from sentence_transformers import SentenceTransformer
                logger.info(f"[RAG] Chargement direct SentenceTransformer : {EMBEDDING_MODEL}")
                _st_model = SentenceTransformer(EMBEDDING_MODEL)
    return _st_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeddings d'une liste de textes par la voie DIRECTE (sans ChromaDB), dim 384.
    Memes parametres d'encodage que le wrapper ChromaDB -> vecteurs identiques
    (a prouver par le test d'equivalence de l'etape 1, pas affirme)."""
    model = get_st_model()
    vecs = model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=False)
    return [v.tolist() for v in vecs]
