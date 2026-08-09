"""Stockage RAG sur PostgreSQL/pgvector — moteur unique du RAG (ChromaDB retiré le 29/06/2026).

Ingestion d'un référentiel DEPUIS SON PDF vers la table referentiel_chunks. La découpe est
GÉNÉRIQUE : produite par l'IA à partir du PROMPT VALIDÉ du couple (EN BASE), sans aucune fiche
en dur. Le moteur orchestre : découpe IA -> embeddings -> insertion. Tout couple est ingérable.

Lancer (venv, racine, .env chargé) :
    python -m backend.rag.pgvector_store --collection bebes_0_1_an     # un couple crèche
    python -m backend.rag.pgvector_store --collection moyens_1_2_ans  # un autre couple
    python -m backend.rag.pgvector_store --collection moyens_1_2_ans --dry-run
"""
from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select, delete, func

from backend.core.database import SessionLocal
from backend.core.models_db import Cycle, Niveau, Referentiel, ReferentielChunk
# Règle de nommage des dossiers, à UNE seule source : elle était recopiée à l'identique ici,
# dans referentiels_admin et dans profil.py.
from backend.core.nommage import dossier_cle as _dossier_cle
from .embeddings import embed_texts, EMBEDDING_MODEL  # voie directe (pas ChromaDB)

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[2]            # racine du depot
REFERENTIELS_DIR = _ROOT / "REFERENTIELS"

# Dossier des sauvegardes horodatées, filet AVANT toute suppression de chunks.
# Convention projet *.bak-* (jamais commitée, cf. .gitignore).
BACKUP_DIR = Path(__file__).parent / "backups"


def _pdf_path_for(db, ref: Referentiel) -> Path:
    """Chemin du PDF du référentiel, dérivé du couple cycle/niveau :
    REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf (convention de rangement du dépôt admin)."""
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


# ── LE CHEMIN DU RETOUR ──────────────────────────────────────────────────────────────────
# La sauvegarde ci-dessus existait depuis le début ; RIEN dans le dépôt ne savait la relire.
# Elle protégeait donc la donnée sans protéger l'opération : on pouvait constater qu'on avait
# tout perdu, pas le défaire. Les deux fonctions suivantes ferment la boucle.
#
# CE QUI REND LA CHOSE POSSIBLE, et ce n'est pas rien : le fichier porte les EMBEDDINGS. Une
# restauration ne repasse donc ni par le PDF, ni par la découpe IA, ni par la vectorisation —
# c'est une lecture de fichier et un INSERT. Aucun appel externe, aucun aléa de modèle.

def lire_sauvegarde(chemin: Path) -> list[dict]:
    """Lit un dump JSONL écrit par `_sauvegarder_chunks_avant_purge`. NE TOUCHE À AUCUNE BASE.

    Séparée de la restauration exprès : on veut pouvoir vérifier un fichier sans rien risquer
    (c'est le mode par défaut de outils_bdd/restaurer_chunks.py). Toute anomalie lève une erreur
    qui DIT quoi faire — un fichier douteux ne doit jamais arriver jusqu'au delete."""
    # Les champs du format de fichier — les mêmes que ceux écrits par la sauvegarde ci-dessus,
    # `id` et `created_at` exclus DÉLIBÉRÉMENT (ils sont regénérés par la base à la
    # réinsertion : un chunk restauré est le même chunk, pas la même ligne).
    # Déclarée ICI et non au niveau module : elle n'a qu'un lecteur, et le filet « rien en dur »
    # surveille les listes de chaînes de niveau module. Sa liste d'exceptions est GELÉE et ne
    # s'allonge que sur décision explicite — une constante privée à une fonction n'a pas besoin
    # de cette décision. (À déplacer si un second lecteur apparaît un jour ; ce sera alors un
    # vrai contrat partagé, et une entrée d'exception se justifiera, comme _SCHEMA_DECOUPE.)
    champs = ("referentiel_id", "chunk_index", "option_ab", "page",
              "texte", "embedding", "embedding_model")
    if not chemin.exists():
        raise RuntimeError(
            f"Sauvegarde introuvable : {chemin}\n"
            f"  Les sauvegardes vivent dans {BACKUP_DIR} et portent un nom en *.bak-*.jsonl."
        )
    lignes: list[dict] = []
    with chemin.open("r", encoding="utf-8") as f:
        for no, brute in enumerate(f, start=1):
            brute = brute.strip()
            if not brute:
                continue
            try:
                obj = json.loads(brute)
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"Sauvegarde illisible : la ligne {no} de {chemin.name} n'est pas du JSON ({e}). "
                    f"Aucune restauration n'a été tentée, la base est intacte."
                ) from e
            manquants = [c for c in champs if c not in obj]
            if manquants:
                raise RuntimeError(
                    f"Sauvegarde incomplète : la ligne {no} de {chemin.name} n'a pas "
                    f"{', '.join(manquants)}. Ce fichier ne vient pas de la sauvegarde avant purge. "
                    f"Aucune restauration n'a été tentée, la base est intacte."
                )
            lignes.append(obj)
    if not lignes:
        # Restaurer un fichier vide, ce serait purger sans rien rendre. C'est la seule
        # manière dont cet outil pourrait détruire quelque chose : on la ferme ici.
        raise RuntimeError(
            f"Sauvegarde vide : {chemin.name} ne porte aucun chunk. Restaurer un fichier vide "
            f"reviendrait à effacer les chunks sans rien remettre — refusé."
        )
    return lignes


def restaurer_chunks_depuis_sauvegarde(db, chemin: Path, rid: int, collection: str | None = None,
                                       modele_courant: str = EMBEDDING_MODEL) -> dict:
    """Rejoue un dump JSONL dans referentiel_chunks : purge les chunks de `rid` et réinsère ceux
    du fichier, VECTEURS COMPRIS. L'inverse exact de `_sauvegarder_chunks_avant_purge`.

    TROIS REFUS, et l'ordre entre eux est le sujet.
      1. le fichier vise un autre référentiel  -> refus
      2. le fichier vient d'un autre modèle    -> refus
      3. l'état courant n'a pas pu être sauvé  -> refus (la sauvegarde RAISE, le delete n'est
                                                  jamais atteint — même garde-fou structurel
                                                  que dans `ingest_pgvector`)
    Les deux premiers tombent AVANT le troisième, et les trois AVANT le delete : on ne purge
    jamais pour découvrir ensuite que le fichier était mauvais. Une restauration est une purge
    comme une autre — d'où le filet n° 3 : un filet ne détruit pas l'état qu'on voudra peut-être
    reprendre (on peut se tromper de fichier, et vouloir revenir de la restauration elle-même).

    Pourquoi PAS de contrôle de dimension en plus : c'est exactement le rôle d'`embedding_model`
    (« garde-fou : interdit de comparer un jour des vecteurs de modèles différents », modèle
    ReferentielChunk). Même modèle = même dimension ; ajouter un second contrôle du même fait
    serait le doublon qu'on a démonté trois fois (points 13, 21, 25)."""
    lignes = lire_sauvegarde(chemin)

    # 1. Le bon référentiel. Un fichier porte le nom de sa collection, mais c'est le
    #    referentiel_id ÉCRIT DANS CHAQUE LIGNE qui fait foi — un nom de fichier se renomme.
    autres = sorted({l["referentiel_id"] for l in lignes} - {rid})
    if autres:
        raise RuntimeError(
            f"Refus : {chemin.name} contient les chunks du référentiel {autres} et non {rid}"
            + (f" (collection '{collection}')" if collection else "")
            + ".\n  Restaurer ce fichier ici écraserait un couple avec le contenu d'un autre.\n"
              "  Vérifiez la collection demandée, ou choisissez la sauvegarde de CE couple."
        )

    # 2. Le bon modèle. Des vecteurs de deux modèles ne se comparent pas : la recherche
    #    rendrait des résultats faux SANS jamais échouer — le pire des deux mondes.
    modeles = sorted({(l.get("embedding_model") or "") for l in lignes})
    if modeles != [modele_courant]:
        raise RuntimeError(
            f"Refus : {chemin.name} porte des vecteurs de {modeles} alors que le modèle courant "
            f"est '{modele_courant}'.\n"
            "  Deux modèles ne produisent pas des vecteurs comparables : la recherche rendrait\n"
            "  des résultats faux sans jamais signaler d'erreur.\n"
            "  Il faut réingérer le couple avec le modèle courant, pas restaurer ce fichier."
        )

    # 3. Filet avant de remplacer l'existant (RAISE si échec -> le delete n'est jamais atteint).
    filet = _sauvegarder_chunks_avant_purge(db, rid, collection)

    db.execute(delete(ReferentielChunk).where(ReferentielChunk.referentiel_id == rid))
    for l in lignes:
        db.add(ReferentielChunk(
            referentiel_id=rid,
            chunk_index=l["chunk_index"],
            option_ab=l["option_ab"],
            page=l["page"],
            texte=l["texte"],
            embedding=l["embedding"],
            embedding_model=l["embedding_model"],
        ))
    db.commit()

    # Preuve après, comme la sauvegarde a sa preuve avant.
    n = db.scalar(
        select(func.count()).select_from(ReferentielChunk)
        .where(ReferentielChunk.referentiel_id == rid)
    )
    if n != len(lignes):
        raise RuntimeError(
            f"Restauration incomplète : {n} chunks en base sur {len(lignes)} attendus "
            f"({chemin.name}). L'état d'avant est dans {filet.get('sauvegarde')}."
        )
    logger.info(f"[RAG-pg] Restauration : {n} chunks depuis {chemin.name} (referentiel {rid})")
    return {
        "referentiel_id": rid,
        "fichier": chemin.name,
        "restaures": n,
        "sauvegarde_avant_restauration": filet,
        "embedding_model": modele_courant,
    }


def _decouper_ia(texte: str, prompt: str) -> list[dict]:
    """Découpe d'un référentiel PAR L'IA (SOCLE, générique) : reçoit le TEXTE DE TRAVAIL du
    couple (colonne referentiels.texte_epure, figée à la validation du dépôt — plus aucune
    extraction PDF ici) et délègue à `analyse_amont.decouper_texte`, piloté par le PROMPT VALIDÉ
    DU COUPLE (`prompt`, lu en base par l'appelant). Renvoie des chunks `{text, page, meta}`
    directement consommables par la suite du pipeline."""
    from backend.rag.analyse_amont import decouper_texte
    db = SessionLocal()
    try:
        unites = decouper_texte(texte, db=db, prompt=prompt)
    finally:
        db.close()
    # `option` vient de la découpe (05/08/2026) : "A"/"B" quand la section n'appartient qu'à une
    # option, "commune" quand le document la dit commune, "" quand il n'a pas d'options. C'est ce
    # qui remplit `referentiel_chunks.option_ab` — jamais déduit ici, seulement transporté.
    return [{"text": u["texte"], "page": 1, "meta": {"option": u.get("option", "")}}
            for u in unites]


def ingest_pgvector(collection: str, dry_run: bool = False, on_progress=None,
                    decoupe_prete: dict | None = None) -> dict:
    """(Re)construit referentiel_chunks pour LE référentiel de `collection`, depuis son PDF.
    Idempotent : supprime les chunks du même referentiel_id (après sauvegarde) puis réinsère.
    Ne touche aucun autre référentiel. La découpe est produite par l'IA à partir du PROMPT
    VALIDÉ du couple (EN BASE) — aucune fiche en dur, tout couple est ingérable.
    `on_progress(etape, fait, total)` : avancement RÉEL remonté à l'appelant (jauge de l'écran) —
    étapes 'decoupe' (IA, durée inconnue), 'vectorisation' (fait/total unités), 'ecriture'.
    `decoupe_prete` = {"prompt", "chunks"} : la découpe que l'admin vient de VOIR et d'accepter
    (aperçu). Réutilisée UNIQUEMENT si son prompt est identique au prompt validé en base —
    sinon (prompt corrigé entre-temps, cache absent) l'IA redécoupe comme avant."""
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
        pdf_path = _pdf_path_for(db, ref)
        # LE prompt de découpe est celui du RÉFÉRENTIEL (06/08/2026) : un par couple cycle+niveau.
        # Il a vécu une journée sur le cycle ; c'était faux — le cycle « BTS » porte dix-huit
        # diplômes qui n'ont pas la même ossature. Il SERT dès qu'il existe —
        # `prompt_decoupe_valide` dit seulement s'il a été relu par l'admin.
        prompt_txt = ref.prompt_decoupe or ""
        # LE texte de travail : colonne texte_epure, figée à la validation du dépôt (get).
        # Filet pour un dépôt antérieur à la colonne (NULL) : calcul UNIQUE depuis le PDF
        # d'origine (porte unique rag.extraction) puis ÉCRIT en base — plus jamais recalculé.
        texte_epure = (ref.texte_epure or "").strip()
        if not texte_epure:
            if not pdf_path.exists():
                raise RuntimeError(f"Texte de travail absent et PDF introuvable : {pdf_path}")
            from backend.rag.extraction import extraire_texte
            texte_epure = extraire_texte(pdf_path)
            ref.texte_epure = texte_epure
            db.commit()
    finally:
        db.close()

    if not prompt_txt.strip():
        raise RuntimeError(
            "Découpe refusée : ce référentiel n'a pas de prompt de découpe. Il est écrit par "
            "l'IA à la découpe (cap « aSchool n'invente rien »)."
        )

    # 2. Découpe : elle est FOURNIE par l'appelant (`decoupe_prete`), qui vient de l'obtenir de
    #    l'IA. Cette fonction n'appelle PLUS l'IA elle-même : elle écrit ce qu'on lui donne.
    #    Elle le faisait avant quand la découpe manquait — en silence, sur le document entier —
    #    et c'est ce repli qui a fini par être refusé par le fournisseur (crèche, 08/08/2026).
    if not (decoupe_prete and decoupe_prete.get("chunks")):
        raise RuntimeError(
            "Aucune découpe à enregistrer pour ce référentiel. Lancez d'abord « Découper » : "
            "c'est ce bouton-là qui appelle l'IA. Celui-ci ne fait qu'écrire ce que vous avez vu."
        )
    if decoupe_prete.get("prompt") != prompt_txt:
        raise RuntimeError(
            "Le prompt de découpe a changé depuis l'aperçu affiché : celui-ci ne correspond plus "
            "au document découpé. Relancez « Découper » pour en obtenir un à jour."
        )
    chunks = decoupe_prete["chunks"]
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

    # 3. Embeddings puis (re)écriture, sous sauvegarde-avant-purge. Vectorisation par petits lots
    #    pour remonter un avancement RÉEL (les vecteurs sont indépendants texte par texte : lots ou
    #    pas, le résultat est identique — voie directe, dim 1024, BGE-M3).
    textes = [c["text"] for c in chunks]
    if on_progress:
        on_progress("vectorisation", 0, len(textes))
    vecs: list = []
    LOT = 4   # petits lots : la jauge avance souvent (le gain de regroupement est négligeable sur des unités longues)
    for i in range(0, len(textes), LOT):
        vecs.extend(embed_texts(textes[i:i + LOT]))
        if on_progress:
            on_progress("vectorisation", min(i + LOT, len(textes)), len(textes))
    if len(vecs) != len(chunks):
        raise RuntimeError(f"Embeddings {len(vecs)} != chunks {len(chunks)}")
    if on_progress:
        on_progress("ecriture", 0, 0)

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
            # Demander l'option B, c'est demander CE QUI CONCERNE l'option B : ses propres unités,
            # celles que le document dit COMMUNES aux options, et celles qui n'en portent aucune
            # (documents sans options, ou découpes d'avant le champ). Un `== option` strict
            # amputerait un prof d'option B de la moitié de son référentiel. (05/08/2026)
            stmt = stmt.where(ReferentielChunk.option_ab.in_([option, "commune", ""]))
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
