"""Fonction generique retrieve — point d'appel unique pour tous les routers.

Usage :
    from backend.rag import retrieve

    chunks = retrieve(
        collection_name="maths_cycle4",
        question="Que doit-on enseigner sur les identites remarquables en 3e ?",
        filters={"programme": "2020"},
        top_k=4,
    )
    for c in chunks:
        print(c["text"], c["page"], c["programme"], c["score"])
"""
import logging
from typing import Any

from .client import get_client
from .embeddings import get_embedding_function

logger = logging.getLogger(__name__)


def retrieve(
    collection_name: str,
    question: str,
    filters: dict[str, Any] | None = None,
    top_k: int = 4,
) -> list[dict[str, Any]]:
    """Recherche les chunks les plus pertinents pour une question.

    Args:
        collection_name: nom de la collection ChromaDB (ex: "maths_cycle4").
        question: question prof a embedder et chercher.
        filters: filtres sur les metadonnees. Format ChromaDB `where`.
                 None ou {} = pas de filtre.
                 Single-field : {"programme": "2020"} fonctionne directement.
                 Multi-field  : ChromaDB rejette le dict implicite (un seul operateur par where).
                                Utiliser la syntaxe $and explicite, exemple :
                                {"$and": [{"programme": {"$eq": "2026"}},
                                          {"niveau":    {"$eq": "5e"}}]}
                                Pertinent quand le corpus 2026 (indexe par niveau) sera en place.
        top_k: nombre de chunks renvoyes (defaut 4).

    Returns:
        Liste de chunks tries par pertinence decroissante. Chaque chunk :
            {
                "text": str,         # contenu du chunk
                "page": int|str,     # numero de page dans le document source
                "source": str,       # identifiant document (ex: "BOEN_2020-07-30")
                "programme": str,    # millesime programme (ex: "2020", "2026")
                "score": float,      # 1 - distance cosinus, [0, 1], plus haut = plus pertinent
            }
    """
    q = (question or "").strip()
    if not q:
        logger.warning("[RAG] retrieve appele avec question vide, renvoie []")
        return []

    client = get_client()
    ef = get_embedding_function()
    collection = client.get_collection(name=collection_name, embedding_function=ef)

    where = filters if filters else None

    logger.info(
        f"[RAG] retrieve collection={collection_name} top_k={top_k} "
        f"filters={where} question={q[:80]!r}"
    )

    results = collection.query(query_texts=[q], n_results=top_k, where=where)
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results.get("distances", [[None] * len(docs)])[0]

    chunks = [
        {
            "text": doc,
            "page": meta.get("page", "?"),
            "source": meta.get("source", "?"),
            "programme": meta.get("programme", "?"),
            "score": round(1 - d, 3) if d is not None else None,
        }
        for doc, meta, d in zip(docs, metas, distances)
    ]

    logger.info(
        f"[RAG] retrieve -> {len(chunks)} chunks, "
        f"scores: {[c['score'] for c in chunks]}"
    )
    return chunks
