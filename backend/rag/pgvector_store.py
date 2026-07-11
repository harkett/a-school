"""Stockage RAG sur PostgreSQL/pgvector — moteur unique du RAG (ChromaDB retiré le 29/06/2026).

Ingestion d'un référentiel DEPUIS SON PDF vers la table referentiel_chunks. Ce module ne
connaît AUCUN référentiel en propre : la SOURCE (où lire, comment extraire, comment découper)
vient de la FICHE du référentiel, résolue par sa `collection` via le registre `get_fiche()`.

CIEL, crèche… chaque référentiel apporte sa méthode d'extraction (`fiche.extract_pages`) ;
le moteur ne fait qu'orchestrer extraction -> découpe générique -> embeddings -> insertion.

Lancer (venv, racine, .env chargé) :
    python -m backend.rag.pgvector_store --collection bebes_0_1_an     # un couple crèche
    python -m backend.rag.pgvector_store --collection moyens_1_2_ans  # un autre couple
    python -m backend.rag.pgvector_store --collection moyens_1_2_ans --dry-run
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select, delete, func

from backend.core.database import SessionLocal
from backend.core.models_db import Cycle, Niveau, Referentiel, ReferentielChunk
from .chunker import build_chunks                     # découpeur générique, sans référentiel
from .embeddings import embed_texts, EMBEDDING_MODEL  # voie directe (pas ChromaDB)
from .referentiels import get_fiche                   # registre collection -> fiche

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[2]            # racine du projet (d:\A-SCHOOL)
REFERENTIELS_DIR = _ROOT / "REFERENTIELS"

# Dossier des sauvegardes horodatées, filet AVANT toute suppression de chunks.
# Convention projet *.bak-* (jamais commitée, cf. .gitignore).
BACKUP_DIR = Path(__file__).parent / "backups"


def _dossier_cle(nom: str) -> str:
    """Nom de cycle/niveau → nom de dossier-clé : accents enlevés, MAJUSCULES, non-alphanum → « _ ».
    Ex. « Moyens (1-2 ans) » → « MOYENS_1_2_ANS ». Même règle que referentiels_admin._dossier_cle."""
    s = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()
    return s or "REFERENTIEL"


def _pdf_path_for(db, ref: Referentiel, fiche) -> Path:
    """Chemin du PDF du référentiel. Si la fiche fixe un PDF_PATH (cas CIEL), on l'utilise ;
    sinon on le dérive du couple cycle/niveau : REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf
    (convention de rangement du dépôt admin)."""
    fixe = getattr(fiche, "PDF_PATH", None)
    if fixe is not None:
        return Path(fixe)
    niveau = db.get(Niveau, ref.niveau_id)
    cycle = db.get(Cycle, niveau.cycle_id)
    return REFERENTIELS_DIR / _dossier_cle(cycle.nom) / _dossier_cle(niveau.nom) / "referentiel.pdf"


def _sauvegarder_chunks_avant_purge(db, rid: int, collection: str | None = None) -> dict:
    """Sauvegarde horodatée des chunks d'un référentiel AVANT toute suppression.

    Règle absolue : suppression = sauvegarde .bak + preuve avant. Lit les chunks existants du
    référentiel `rid`, écrit un dump JSONL (1 chunk/ligne) sous BACKUP_DIR (*.bak-*, gitignore),
    relit le fichier et exige lignes_écrites == chunks_lus — sinon RAISE, de sorte que le delete
    appelant n'est jamais atteint. Cas 0 chunk : rien à écraser, aucun fichier écrit."""
    rows = db.execute(
        select(
            ReferentielChunk.chunk_index,
            ReferentielChunk.option_ab,
            ReferentielChunk.page,
            ReferentielChunk.texte,
            ReferentielChunk.embedding,
            ReferentielChunk.embedding_model,
        )
        .where(ReferentielChunk.referentiel_id == rid)
        .order_by(ReferentielChunk.chunk_index)
    ).all()

    if not rows:
        return {"sauvegarde": None, "lignes": 0, "note": "0 chunk existant -- rien a sauvegarder"}

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d-%H%M%S-%f")  # microsecondes : pas de collision
    chemin = BACKUP_DIR / f"referentiel_chunks-{collection or 'referentiel'}.bak-{horodatage}.jsonl"

    # Mode exclusif "x" : si le nom existe déjà, on RAISE plutôt que d'écraser un backup
    # existant (un filet ne détruit jamais un autre filet).
    with chemin.open("x", encoding="utf-8") as f:
        for (chunk_index, option_ab, page, texte, embedding, embedding_model) in rows:
            f.write(json.dumps({
                "referentiel_id": rid,
                "chunk_index": chunk_index,
                "option_ab": option_ab,
                "page": page,
                "texte": texte,
                "embedding": [float(x) for x in embedding],
                "embedding_model": embedding_model,
            }, ensure_ascii=False) + "\n")

    # Preuve avant : relire le fichier et exiger le bon compte, sinon ANNULER (raise).
    with chemin.open("r", encoding="utf-8") as f:
        lignes_ecrites = sum(1 for _ in f)
    if lignes_ecrites != len(rows):
        raise RuntimeError(
            f"Sauvegarde incomplete : {lignes_ecrites} lignes ecrites sur {len(rows)} "
            f"chunks ({chemin.name}). Suppression annulee."
        )
    logger.info(f"[RAG-pg] Sauvegarde avant purge : {lignes_ecrites} chunks -> {chemin.name}")
    return {"sauvegarde": chemin.name, "lignes": lignes_ecrites}


def _decouper_ia(pdf_path, prompt: str) -> list[dict]:
    """Découpe d'un référentiel PAR L'IA (SOCLE, générique) : lit le TEXTE BRUT du PDF et délègue à
    `analyse_amont.decouper_texte`, piloté par le PROMPT VALIDÉ DU COUPLE (`prompt`, lu en base par
    l'appelant). Remplace l'ancienne extraction regex + motif de la fiche. Renvoie des chunks
    `{text, page, meta}` directement consommables par la suite du pipeline."""
    import pdfplumber
    from backend.rag.analyse_amont import decouper_texte
    with pdfplumber.open(str(pdf_path)) as pdf:
        texte = "\n".join((p.extract_text() or "") for p in pdf.pages)
    db = SessionLocal()
    try:
        unites = decouper_texte(texte, db=db, prompt=prompt)
    finally:
        db.close()
    return [{"text": u["texte"], "page": 1, "meta": {"option": ""}} for u in unites]


def ingest_pgvector(collection: str, dry_run: bool = False) -> dict:
    """(Re)construit referentiel_chunks pour LE référentiel de `collection`, depuis son PDF.
    Idempotent : supprime les chunks du même referentiel_id (après sauvegarde) puis réinsère.
    Ne touche aucun autre référentiel. La méthode d'extraction et les réglages de découpe
    viennent de la fiche du référentiel (registre `get_fiche`)."""
    fiche = get_fiche(collection)

    # 1. Résoudre le référentiel (id) et le chemin du PDF (courte ouverture DB).
    db = SessionLocal()
    try:
        ref = db.execute(
            select(Referentiel).where(Referentiel.collection == collection)
        ).scalar_one_or_none()
        if ref is None:
            raise RuntimeError(
                f"Aucun référentiel en base pour collection='{collection}'. "
                f"Le couple (niveau + PDF) doit exister dans la table referentiels."
            )
        rid = ref.id
        pdf_path = _pdf_path_for(db, ref, fiche)
        prompt_ok = ref.prompt_decoupe_valide
        prompt_txt = ref.prompt_decoupe or ""
    finally:
        db.close()

    if not pdf_path.exists():
        raise RuntimeError(f"PDF introuvable : {pdf_path}")
    if not prompt_ok:
        raise RuntimeError(
            "Découpe refusée : le prompt de découpe du couple n'est pas validé. "
            "L'admin doit le générer puis le valider (cap « aSchool n'invente rien »)."
        )

    # 2. Découpe PAR L'IA (SOCLE, générique), pilotée par le PROMPT VALIDÉ du couple (base).
    chunks = _decouper_ia(pdf_path, prompt_txt)
    # Verdict d'analyse amont de l'IA, PERSISTÉ (calculé une fois) et relu -> MÊME verdict que
    # l'aperçu (jamais deux appels IA divergents). Doute par unité reconstitué des libellés (pur).
    doutes = None
    if hasattr(fiche, "doutes_depuis_labels"):
        db_ia = SessionLocal()
        try:
            ref_ia = db_ia.execute(
                select(Referentiel).where(Referentiel.collection == collection)
            ).scalar_one_or_none()
            labels = _labels_douteux(db_ia, ref_ia, fiche, chunks) if ref_ia is not None else []
        finally:
            db_ia.close()
        doutes = fiche.doutes_depuis_labels(chunks, labels)
    # Filtrage par niveau À L'INGESTION (structurel) : si la fiche le prévoit, chaque collection
    # ne garde que les chunks de son niveau (ex. crèche : Bébés -> 0-1, Moyens/Grands -> 1-3).
    # Sinon (CIEL), aucun filtre. Aucune colonne en base — cf. immuabilité de la structure.
    filtrer = getattr(fiche, "filtrer_chunks", None)
    if filtrer is not None:
        chunks = filtrer(chunks, collection, doutes)
    by_opt = Counter(c["meta"]["option"] for c in chunks)
    report = {
        "collection": collection,
        "pdf": pdf_path.name,
        "total_chunks_PDF": len(chunks),
        "par_option_PDF": dict(by_opt),
    }
    if dry_run:
        report["mode"] = "dry-run (aucune ecriture)"
        return report

    # 3. Embeddings puis (re)écriture, sous sauvegarde-avant-purge.
    vecs = embed_texts([c["text"] for c in chunks])   # voie directe, dim 1024 (BGE-M3)
    if len(vecs) != len(chunks):
        raise RuntimeError(f"Embeddings {len(vecs)} != chunks {len(chunks)}")

    db = SessionLocal()
    try:
        sauvegarde = _sauvegarder_chunks_avant_purge(db, rid, collection)  # RAISE si échec -> delete jamais atteint
        db.execute(delete(ReferentielChunk).where(ReferentielChunk.referentiel_id == rid))
        for idx, (ch, vec) in enumerate(zip(chunks, vecs)):
            db.add(ReferentielChunk(
                referentiel_id=rid,
                chunk_index=idx,
                option_ab=ch["meta"]["option"],   # "A"/"B" (CIEL) ou "" (crèche), posé par la fiche
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
            "sauvegarde_avant_purge": sauvegarde,
            "inseres_en_base": n,
            "par_option_en_base": per_opt,
            "embedding_model": EMBEDDING_MODEL,
        })
        return report
    finally:
        db.close()


def _labels_douteux(db, ref, fiche, chunks: list) -> list:
    """Verdict d'analyse amont de l'IA, PERSISTÉ (referentiels.doutes_ia) : calculé UNE fois via la
    fiche (si la colonne est vide) puis relu. L'aperçu ET l'ingestion passent par ici → ils tranchent
    le MÊME verdict, jamais deux appels IA divergents (l'IA n'est pas parfaitement répétable). Renvoie
    la liste des libellés jugés douteux (vide si la fiche n'expose pas d'analyse amont)."""
    import json
    if not hasattr(fiche, "libelles_douteux"):
        return []
    if ref.doutes_ia is not None:
        try:
            data = json.loads(ref.doutes_ia)
            if isinstance(data, list):
                return [str(x) for x in data]
        except Exception:
            pass   # colonne illisible -> on recalcule proprement ci-dessous
    labels = fiche.libelles_douteux(chunks, db=db)   # UN appel IA, puis on le fige
    ref.doutes_ia = json.dumps(labels, ensure_ascii=False)
    db.commit()
    return labels


def apercu_decoupage(collection: str) -> dict:
    """Aperçu du découpage d'un référentiel : découpe le PDF avec EXACTEMENT les réglages de la fiche
    (comme l'ingestion), NE VECTORISE RIEN et n'écrit AUCUN chunk. Seule écriture possible : au tout
    premier appel, le verdict d'analyse amont de l'IA est calculé UNE fois et figé (colonne doutes_ia)
    — ensuite il est relu. Renvoie l'aperçu produit par la fiche (unités, titres, bandes, cas flous,
    totaux par niveau). Lève si la règle n'est pas validée (même garde-fou que l'ingestion)."""
    fiche = get_fiche(collection)
    apercu = getattr(fiche, "apercu_unites", None)
    if apercu is None:
        raise RuntimeError(f"Aperçu de découpage non disponible pour collection='{collection}'.")

    db = SessionLocal()
    try:
        ref = db.execute(
            select(Referentiel).where(Referentiel.collection == collection)
        ).scalar_one_or_none()
        if ref is None:
            raise RuntimeError(f"Aucun référentiel en base pour collection='{collection}'.")
        pdf_path = _pdf_path_for(db, ref, fiche)
        if not pdf_path.exists():
            raise RuntimeError(f"PDF introuvable : {pdf_path}")
        if not ref.prompt_decoupe_valide:
            raise RuntimeError(
                "Découpe refusée : le prompt de découpe du couple n'est pas validé "
                "(l'admin doit le générer puis le valider)."
            )

        chunks = _decouper_ia(pdf_path, ref.prompt_decoupe or "")   # découpe PAR L'IA, prompt validé du couple
        # Verdict d'analyse amont de l'IA, PERSISTÉ (calculé une fois) et relu ici -> MÊME verdict que
        # l'ingestion. On reconstitue le doute par unité depuis les libellés persistés (pur, sans IA).
        doutes = None
        if hasattr(fiche, "doutes_depuis_labels"):
            labels = _labels_douteux(db, ref, fiche, chunks)
            doutes = fiche.doutes_depuis_labels(chunks, labels)
        resultat = apercu(chunks, collection, doutes=doutes)
        # Résumé du filtre par niveau — on exécute le VRAI filtre (filtrer_chunks, lecture seule) et on
        # joint son verdict à l'aperçu, pour la cartouche « Résultat du filtre » de l'écran admin. ok=True
        # -> couple prêt (X/Y retenues) ; ok=False -> refus (message clair, un cas non tranché reste).
        try:
            gardes = fiche.filtrer_chunks(chunks, collection, doutes)
            resultat["filtre"] = {"ok": True, "gardes": len(gardes), "total": len(chunks), "message": None}
        except Exception as e:
            resultat["filtre"] = {"ok": False, "gardes": 0, "total": len(chunks), "message": str(e)}
        return resultat
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
    l'embedding de la question. Ne touche PAS ChromaDB. Lecture seule (SELECT).

    filters : {"option": "A"} (forme simple) ou None. score = 1 - distance cosinus,
    arrondi 3 décimales."""
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

        qvec = embed_texts([q])[0]                       # voie directe, dim 1024 (BGE-M3)
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
    ap = argparse.ArgumentParser(description="Ingestion référentiel -> pgvector (PostgreSQL).")
    ap.add_argument("--collection", default="bebes_0_1_an",
                    help="collection du référentiel à (re)construire (défaut : Bébés 0-1)")
    ap.add_argument("--dry-run", action="store_true", help="rapport sans écriture")
    args = ap.parse_args()
    print(json.dumps(ingest_pgvector(collection=args.collection, dry_run=args.dry_run),
                     ensure_ascii=False, indent=2))
