"""Stockage RAG sur PostgreSQL/pgvector — remplacant futur de client.py (ChromaDB).

Etape 2 (refonte RAG) : ingestion d'un referentiel DEPUIS LE PDF vers la table
referentiel_chunks. Ce module N'IMPORTE NI N'APPELLE ChromaDB : pas de client.py,
pas de get_client, pas de get_embedding_function. La SOURCE des chunks est le PDF
(extract_pages + build_chunks generique), jamais ChromaDB.

Lancer (venv, racine, .env charge) :
    python -m backend.rag.pgvector_store             # (re)construit referentiel_chunks
    python -m backend.rag.pgvector_store --dry-run   # rapport de decoupage, rien ecrit
"""
from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Any

import pdfplumber
from sqlalchemy import select, delete, func

from backend.database import SessionLocal
from backend.models_db import Referentiel, ReferentielChunk, Niveau
from .chunker import build_chunks                     # generique, SANS ChromaDB (chunker.py)
from .embeddings import embed_texts, EMBEDDING_MODEL  # voie DIRECTE etape 1 (pas ChromaDB)
from .referentiels import bts_ciel_option_a as fiche

logger = logging.getLogger(__name__)


def extract_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """(n° page depuis 1, texte) — re-extraction directe du PDF (pdfplumber).
    Reimplemente ici pour que ce module ne depende PAS de ingest_referentiel.py
    (lequel importe client.py/ChromaDB). Meme logique d'extraction."""
    pages: list[tuple[int, str]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            pages.append((i, page.extract_text() or ""))
    return pages


def build_chunks_from_pdf() -> list[dict]:
    """Chunks generes DEPUIS LE PDF (source unique). Aucune lecture ChromaDB."""
    pages = extract_pages(fiche.PDF_PATH)
    return build_chunks(
        pages,
        max_chars=fiche.MAX_CHARS,
        min_chars=fiche.MIN_CHARS,
        overlap_chars=fiche.OVERLAP_CHARS,
        is_boundary=fiche.section_boundary,
        chunk_metadata=fiche.chunk_metadata,
        dedup_key=fiche.dedup_key,
    )


def _resolve_referentiel_id(db) -> int:
    """id du referentiel pour ce couple (lookup par collection = fiche.COLLECTION)."""
    rid = db.scalar(select(Referentiel.id).where(Referentiel.collection == fiche.COLLECTION))
    if rid is None:
        raise RuntimeError(
            f"Aucun referentiel en base pour collection='{fiche.COLLECTION}'. "
            f"Le couple (niveau + PDF) doit exister dans la table referentiels."
        )
    return rid


def ingest_pgvector(dry_run: bool = False) -> dict:
    """(Re)construit referentiel_chunks pour CE referentiel, depuis le PDF. Idempotent :
    supprime les chunks du meme referentiel_id puis reinsere. Ne touche aucun autre
    referentiel, ni ChromaDB."""
    if not fiche.PDF_PATH.exists():
        raise RuntimeError(f"PDF introuvable : {fiche.PDF_PATH}")

    chunks = build_chunks_from_pdf()
    by_opt = Counter(c["meta"]["option"] for c in chunks)
    report = {
        "pdf": fiche.PDF_PATH.name,
        "total_chunks_PDF": len(chunks),
        "par_option_PDF": dict(by_opt),
    }
    if dry_run:
        report["mode"] = "dry-run (aucune ecriture)"
        return report

    vecs = embed_texts([c["text"] for c in chunks])   # voie DIRECTE etape 1, dim 384
    if len(vecs) != len(chunks):
        raise RuntimeError(f"Embeddings {len(vecs)} != chunks {len(chunks)}")

    db = SessionLocal()
    try:
        rid = _resolve_referentiel_id(db)
        db.execute(delete(ReferentielChunk).where(ReferentielChunk.referentiel_id == rid))
        for idx, (ch, vec) in enumerate(zip(chunks, vecs)):
            db.add(ReferentielChunk(
                referentiel_id=rid,
                chunk_index=idx,
                option_ab=ch["meta"]["option"],   # "A" / "B" pose par la fiche
                page=ch["page"],
                texte=ch["text"],
                embedding=vec,
                embedding_model=EMBEDDING_MODEL,
            ))
        db.commit()
        n = db.scalar(
            select(func.count()).select_from(ReferentielChunk)
            .where(ReferentielChunk.referentiel_id == rid)
        )
        if n != len(chunks):
            raise RuntimeError(f"Incomplet : {n} ranges sur {len(chunks)} attendus")
        per_opt = dict(db.execute(
            select(ReferentielChunk.option_ab, func.count())
            .where(ReferentielChunk.referentiel_id == rid)
            .group_by(ReferentielChunk.option_ab)
        ).all())
        report.update({
            "referentiel_id": rid,
            "inseres_en_base": n,
            "par_option_en_base": per_opt,
            "embedding_model": EMBEDDING_MODEL,
        })
        return report
    finally:
        db.close()


def retrieve_pg(
    collection_name: str,
    question: str,
    filters: dict[str, Any] | None = None,
    top_k: int = 4,
) -> list[dict[str, Any]]:
    """Recherche pgvector (cosinus) sur referentiel_chunks — MEME forme de sortie que
    retrieve() ChromaDB (text, page, source, score=1-distance, meta). Voie DIRECTE pour
    l'embedding de la question (etape 1). Ne touche PAS ChromaDB. Lecture seule (SELECT).

    filters : {"option": "A"} (forme simple) ou None. score = 1 - distance cosinus,
    arrondi 3 decimales — strictement comme retrieve() (retrieve.py:82)."""
    q = (question or "").strip()
    if not q:
        logger.warning("[RAG-pg] retrieve_pg appele avec question vide, renvoie []")
        return []

    option = filters.get("option") if filters else None

    db = SessionLocal()
    try:
        ref = db.execute(
            select(Referentiel.id, Referentiel.source, Niveau.nom)
            .join(Niveau, Niveau.id == Referentiel.niveau_id)
            .where(Referentiel.collection == collection_name)
        ).first()
        if ref is None:
            logger.warning(f"[RAG-pg] collection inconnue: {collection_name!r} -> []")
            return []
        rid, source, niveau_nom = ref

        qvec = embed_texts([q])[0]                       # voie DIRECTE (etape 1), dim 384
        dist = ReferentielChunk.embedding.cosine_distance(qvec).label("distance")
        stmt = (
            select(ReferentielChunk.texte, ReferentielChunk.page,
                   ReferentielChunk.option_ab, dist)
            .where(ReferentielChunk.referentiel_id == rid)
        )
        if option is not None:
            stmt = stmt.where(ReferentielChunk.option_ab == option)
        stmt = stmt.order_by(dist).limit(top_k)
        rows = db.execute(stmt).all()
    finally:
        db.close()

    chunks = [
        {
            "text": texte,
            "page": page,
            "source": source,
            "score": round(1 - d, 3) if d is not None else None,
            "meta": {"source": source, "niveau": niveau_nom, "option": opt, "page": page},
        }
        for (texte, page, opt, d) in rows
    ]
    logger.info(
        f"[RAG-pg] retrieve_pg collection={collection_name} top_k={top_k} option={option} "
        f"-> {len(chunks)} chunks, scores={[c['score'] for c in chunks]}"
    )
    return chunks


if __name__ == "__main__":
    import argparse
    import json
    ap = argparse.ArgumentParser(description="Ingestion referentiel -> pgvector (PostgreSQL).")
    ap.add_argument("--dry-run", action="store_true", help="rapport sans ecriture")
    print(json.dumps(ingest_pgvector(dry_run=ap.parse_args().dry_run), ensure_ascii=False, indent=2))
