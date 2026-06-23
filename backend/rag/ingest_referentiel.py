"""Ingestion d'un référentiel officiel dans ChromaDB — orchestrateur.

Moteur générique (chunker) + fiche du référentiel : ce module ORCHESTRE, il ne porte
plus aucune constante propre à un référentiel. La fiche (ici
backend/rag/referentiels/bts_ciel_option_a.py) fournit le PDF, les tailles de chunk,
le détecteur de frontière et le constructeur de métadonnées. Le découpeur (chunker.py)
ne connaît aucun référentiel. Ajouter un référentiel = écrire une autre fiche, zéro
ligne touchée au moteur.

re-extraction PROPRE du PDF (pdfplumber, UTF-8) → découpe générique → embeddings avec le
MÊME modèle que le corpus existant → collection dédiée de la fiche, chaque chunk tagué
{niveau, option} DÈS l'ingestion.

Idempotent : la collection cible est supprimée puis reconstruite à chaque run.
Ne touche JAMAIS les autres collections.

Lancer (venv, depuis la racine) :
    python -m backend.rag.ingest_referentiel             # construit la collection
    python -m backend.rag.ingest_referentiel --dry-run   # rapport de découpage, rien écrit
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import pdfplumber

from .client import get_client
from .embeddings import get_embedding_function
from .chunker import build_chunks
from .referentiels import bts_ciel_option_a as fiche


def extract_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """(n° de page commençant à 1, texte propre) pour chaque page du PDF."""
    pages: list[tuple[int, str]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            pages.append((i, page.extract_text() or ""))
    return pages


def ingest(chunks: list[dict]) -> int:
    """(Re)construit la collection cible. Ne touche pas aux autres collections."""
    client = get_client()
    ef = get_embedding_function()
    if fiche.COLLECTION in {c.name for c in client.list_collections()}:
        client.delete_collection(fiche.COLLECTION)  # idempotent — rebuild propre
    col = client.create_collection(
        name=fiche.COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},  # cohérent avec retrieve() (score = 1 - distance)
    )
    ids, docs, metas = [], [], []
    for idx, ch in enumerate(chunks):
        ids.append(f"ciel-A-{idx:04d}")
        docs.append(ch["text"])
        metas.append(ch["meta"])  # métadonnées entièrement posées par la fiche
    BATCH = 64
    for i in range(0, len(ids), BATCH):
        col.add(ids=ids[i:i + BATCH], documents=docs[i:i + BATCH], metadatas=metas[i:i + BATCH])
    return col.count()


def refresh_extraction_txt(pages: list[tuple[int, str]], out_path: Path) -> None:
    """Réécrit extraction-texte.txt en UTF-8 propre (l'ancienne version était en
    encodage cassé : « r�seaux », « cybers�curit� »…). Caillou enlevé en entier."""
    out_path.write_text("\n".join(t for _, t in pages), encoding="utf-8")


def _report(pages: list[tuple[int, str]], chunks: list[dict]) -> None:
    by_opt = Counter(c["meta"]["option"] for c in chunks)
    b_pages = sorted({c["page"] for c in chunks if c["meta"]["option"] == "B"})
    print(f"PDF        : {fiche.PDF_PATH.name}")
    print(f"Pages      : {len(pages)}")
    print(f"Chunks     : {len(chunks)}  (par option : {dict(by_opt)})")
    print(f"Pages 'B'  : {b_pages}  (sections option B : {sorted(fiche.OPTION_B_SECTIONS)})")
    # 1er chunk de chaque bloc B + 1er chunk général (pour vérifier le découpage à l'œil)
    for opt in ("A", "B"):
        sample = next((c for c in chunks if c["meta"]["option"] == opt), None)
        if sample:
            head = sample["text"].replace("\n", " ")[:90]
            print(f"  [{opt}] p.{sample['page']} : {head}…")


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingestion référentiel → ChromaDB (BTS CIEL option A).")
    ap.add_argument("--dry-run", action="store_true", help="rapport de découpage sans écrire dans ChromaDB")
    args = ap.parse_args()

    if not fiche.PDF_PATH.exists():
        sys.exit(f"PDF introuvable : {fiche.PDF_PATH}")

    pages = extract_pages(fiche.PDF_PATH)
    chunks = build_chunks(
        pages,
        max_chars=fiche.MAX_CHARS,
        min_chars=fiche.MIN_CHARS,
        overlap_chars=fiche.OVERLAP_CHARS,
        is_boundary=fiche.section_boundary,
        chunk_metadata=fiche.chunk_metadata,
        dedup_key=fiche.dedup_key,
    )
    _report(pages, chunks)

    if args.dry_run:
        print("DRY-RUN — aucune écriture (ni ChromaDB ni extraction-texte.txt).")
        return

    n = ingest(chunks)
    refresh_extraction_txt(pages, fiche.EXTRACTION_TXT)
    print(f"Collection '{fiche.COLLECTION}' : {n} chunks écrits (niveau='{fiche.NIVEAU}').")
    print(f"Extraction propre réécrite : {fiche.EXTRACTION_TXT.name}")


if __name__ == "__main__":
    main()
