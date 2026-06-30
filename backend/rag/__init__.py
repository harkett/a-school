"""Pile RAG mutualisee aSchool (levier 36) — moteur sur PostgreSQL/pgvector.

Une seule infrastructure (pgvector + sentence-transformers), plusieurs referentiels
dans la table referentiel_chunks. Chaque router qui veut grounder ses generations
appelle `retrieve_pg(collection_name, question, filters)` en precisant sa cible.

Modules :
  pgvector_store : ingestion (PDF -> referentiel_chunks) + retrieve_pg (recherche cosinus)
  embeddings     : singleton SentenceTransformer (voie directe, charge une fois)
  chunker        : decoupage generique (aucun referentiel code en dur)

Voir MesMD/LEVIERS/L36.md pour le mapping leviers <-> corpus.
"""
from .pgvector_store import retrieve_pg

__all__ = ["retrieve_pg"]
