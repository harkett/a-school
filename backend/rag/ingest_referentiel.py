"""Ingestion d'un référentiel officiel dans ChromaDB — brique (1) du Chantier B.

Slice 1 — BTS CIEL option A (1er cas de la procédure « référentiel → RAG ») :
re-extraction PROPRE du PDF (pdfplumber, UTF-8 — l'ancienne extraction-texte.txt
était en encodage cassé) → découpe → embeddings avec le MÊME modèle que le corpus
existant → collection dédiée `bts_ciel_optionA`, chaque chunk tagué {niveau, option}
DÈS l'ingestion.

Non négociable : le `niveau` est posé à l'ingestion. Le corpus `maths_cycle4` ne
l'a pas (« cycle 4 en bloc », filtre niveau désactivé dans generate.py) — c'est
exactement le défaut qu'on ne reproduit PAS ici.

Découpage option A / B : seules 3 sections du référentiel sont spécifiques à
l'option B (II.2.3, III.1.3, III.2.2). Tout le reste (présentation, activités/
compétences option A, et surtout les enseignements généraux III.3 — Maths,
Anglais, Français…) s'applique à l'option A → tagué 'A'. Le détecteur se cale sur
le NUMÉRO de section (ASCII, robuste à l'encodage), en ignorant le sommaire.

Idempotent : la collection cible est supprimée puis reconstruite à chaque run.
Ne touche JAMAIS les autres collections (`maths_cycle4` reste intacte).

Lancer (venv, depuis la racine) :
    python -m backend.rag.ingest_referentiel             # construit la collection
    python -m backend.rag.ingest_referentiel --dry-run   # rapport de découpage, rien écrit
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import pdfplumber

from .client import get_client
from .embeddings import get_embedding_function

# --- Cible : BTS CIEL option A ---
_ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = _ROOT / "REFERENTIELS" / "BTS-CIEL-option-A" / "15324-ref-bts-ciel-vpub-v01.pdf"
EXTRACTION_TXT = PDF_PATH.parent / "extraction-texte.txt"

COLLECTION = "bts_ciel_optionA"
NIVEAU = "BTS CIEL option A"          # non négociable — posé sur CHAQUE chunk
CYCLE = "Supérieur"
SOURCE = "REF-BTS-CIEL-2023"
LABEL = "Référentiel BTS CIEL — éduscol STI, rénovation 2023"

MAX_CHARS = 900   # taille cible d'un chunk
MIN_CHARS = 60    # en dessous, on ne crée pas un chunk isolé (bruit : n° de page, titres orphelins)

# Sections SPÉCIFIQUES à l'option B → tag 'B'. Tout autre en-tête reconnu → retour 'A'.
OPTION_B_SECTIONS = {"II.2.3", "III.1.3", "III.2.2"}
# En-tête de section = « ANNEXE <romain> » OU un numéro « <romain>.<n>[.<n>[.<n>]] ».
SECTION_RE = re.compile(r"^(ANNEXE\s+[IVX]+|[IVX]+\.\d+(?:\.\d+){0,2})\b")
TOC_RE = re.compile(r"\.{4,}")  # lignes du sommaire (pointillés de table des matières)


def extract_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """(n° de page commençant à 1, texte propre) pour chaque page du PDF."""
    pages: list[tuple[int, str]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            pages.append((i, page.extract_text() or ""))
    return pages


def _section_number(line: str) -> str | None:
    """Numéro de section si `line` est un en-tête (hors sommaire), sinon None."""
    s = line.strip()
    if not s or TOC_RE.search(s):
        return None
    m = SECTION_RE.match(s)
    return m.group(0) if m else None


def build_chunks(pages: list[tuple[int, str]]) -> list[dict]:
    """Découpe en chunks (≤ MAX_CHARS), un seul n° de page par chunk, tagué de
    l'option courante. L'état option traverse les pages et bascule aux en-têtes."""
    chunks: list[dict] = []
    option = "A"  # défaut : commun / option A
    for page_no, text in pages:
        buf: list[str] = []
        buf_len = 0

        def flush() -> None:
            nonlocal buf, buf_len
            content = "\n".join(buf).strip()
            if len(content) >= MIN_CHARS:
                chunks.append({"text": content, "page": page_no, "option": option})
            buf, buf_len = [], 0

        for line in text.splitlines():
            num = _section_number(line)
            if num is not None:
                flush()  # un nouvel en-tête ferme le chunk courant…
                option = "B" if num in OPTION_B_SECTIONS else "A"  # …et (re)fixe l'option
            buf.append(line)
            buf_len += len(line) + 1
            if buf_len >= MAX_CHARS:
                flush()
        flush()
    return chunks


def ingest(chunks: list[dict]) -> int:
    """(Re)construit la collection cible. Ne touche pas aux autres collections."""
    client = get_client()
    ef = get_embedding_function()
    if COLLECTION in {c.name for c in client.list_collections()}:
        client.delete_collection(COLLECTION)  # idempotent — rebuild propre
    col = client.create_collection(
        name=COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},  # cohérent avec retrieve() (score = 1 - distance)
    )
    ids, docs, metas = [], [], []
    for idx, ch in enumerate(chunks):
        ids.append(f"ciel-A-{idx:04d}")
        docs.append(ch["text"])
        metas.append({
            "source": SOURCE,
            "label": LABEL,
            "cycle": CYCLE,
            "niveau": NIVEAU,        # <-- non négociable, sur CHAQUE chunk
            "option": ch["option"],
            "page": ch["page"],
        })
    BATCH = 64
    for i in range(0, len(ids), BATCH):
        col.add(ids=ids[i:i + BATCH], documents=docs[i:i + BATCH], metadatas=metas[i:i + BATCH])
    return col.count()


def refresh_extraction_txt(pages: list[tuple[int, str]], out_path: Path) -> None:
    """Réécrit extraction-texte.txt en UTF-8 propre (l'ancienne version était en
    encodage cassé : « r�seaux », « cybers�curit� »…). Caillou enlevé en entier."""
    out_path.write_text("\n".join(t for _, t in pages), encoding="utf-8")


def _report(pages: list[tuple[int, str]], chunks: list[dict]) -> None:
    by_opt = Counter(c["option"] for c in chunks)
    b_pages = sorted({c["page"] for c in chunks if c["option"] == "B"})
    print(f"PDF        : {PDF_PATH.name}")
    print(f"Pages      : {len(pages)}")
    print(f"Chunks     : {len(chunks)}  (par option : {dict(by_opt)})")
    print(f"Pages 'B'  : {b_pages}  (sections option B : {sorted(OPTION_B_SECTIONS)})")
    # 1er chunk de chaque bloc B + 1er chunk général (pour vérifier le découpage à l'œil)
    for opt in ("A", "B"):
        sample = next((c for c in chunks if c["option"] == opt), None)
        if sample:
            head = sample["text"].replace("\n", " ")[:90]
            print(f"  [{opt}] p.{sample['page']} : {head}…")


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingestion référentiel → ChromaDB (BTS CIEL option A).")
    ap.add_argument("--dry-run", action="store_true", help="rapport de découpage sans écrire dans ChromaDB")
    args = ap.parse_args()

    if not PDF_PATH.exists():
        sys.exit(f"PDF introuvable : {PDF_PATH}")

    pages = extract_pages(PDF_PATH)
    chunks = build_chunks(pages)
    _report(pages, chunks)

    if args.dry_run:
        print("DRY-RUN — aucune écriture (ni ChromaDB ni extraction-texte.txt).")
        return

    n = ingest(chunks)
    refresh_extraction_txt(pages, EXTRACTION_TXT)
    print(f"Collection '{COLLECTION}' : {n} chunks écrits (niveau='{NIVEAU}').")
    print(f"Extraction propre réécrite : {EXTRACTION_TXT.name}")


if __name__ == "__main__":
    main()
