-- Exécuté UNE SEULE FOIS, à la création d'une base vide (dossier data neuf).
-- pgvector : le type VECTOR doit exister AVANT les migrations Alembic (colonnes VECTOR).
CREATE EXTENSION IF NOT EXISTS vector;
