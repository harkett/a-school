"""Pile RAG mutualisee aSchool (levier 36).

Une seule infrastructure (ChromaDB + sentence-transformers), plusieurs
collections selon le corpus indexe. Chaque router qui veut grounder ses
generations appelle `retrieve(collection_name, question, filters)` en
precisant sa collection cible.

Modules :
  client     : singleton ChromaPersistentClient (pointe sur backend/rag/chroma_db)
  embeddings : singleton SentenceTransformerEmbeddingFunction (charge une fois au boot)
  retrieve   : fonction generique retrieve(collection, question, filters, top_k)

Voir MesMD/LEVIERS/L36.md pour le mapping leviers <-> corpus.
"""
from .retrieve import retrieve

__all__ = ["retrieve"]
