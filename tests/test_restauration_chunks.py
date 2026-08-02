"""Le CHEMIN DU RETOUR des chunks RAG : sauvegarder, purger, restaurer — vecteurs compris.

CE QUE CE FICHIER EMPÊCHE. La sauvegarde avant purge existait depuis le début et elle tenait
(tests/test_rag_backup.py) : dump JSONL, relecture, comptage, RAISE avant le delete. Mais RIEN
dans le dépôt ne savait la rejouer. Elle protégeait donc la DONNÉE sans protéger l'OPÉRATION :
on pouvait constater qu'on avait tout perdu, pas le défaire. Trois sauvegardes dormaient sur le
disque depuis le 16/07 sans qu'aucun code sache les lire.

C'est ce qui interdisait toute réingestion. Le test qui compte est le premier ci-dessous : il
fait l'aller-retour COMPLET sur une vraie base — sauvegarde, purge, restauration, comparaison
ligne à ligne. C'est lui qui transforme « il existe un fichier » en « on sait revenir ».

LES VECTEURS SONT DANS LE FICHIER, et c'est ce qui rend la chose gratuite : restaurer ne
repasse ni par le PDF, ni par la découpe IA, ni par la vectorisation. Le test le vérifie
explicitement — un retour qui perdrait les embeddings coûterait une re-vectorisation complète
et ne serait plus un retour, mais une réingestion.

Les trois refus sont éprouvés UN PAR UN, et chacun vérifie en plus que la base n'a pas bougé :
un refus qui purgerait d'abord et refuserait ensuite serait pire que pas de refus du tout.

Contrairement à test_rag_backup.py (db factice, aucune connexion), ce fichier tourne sur la
VRAIE base de test `aschool_test` : c'est le seul moyen de prouver que les 1024 flottants
reviennent tels quels à travers la colonne Vector(1024).

Lancer : docker compose exec backend python -m pytest tests/test_restauration_chunks.py -q
"""
import json

import pytest

import backend.core.database as dbmod
from backend.core.models_db import Cycle, Niveau, Referentiel, ReferentielChunk
from backend.rag import pgvector_store

MODELE = "BAAI/bge-m3"
DIM = 1024


def _vecteur(graine: int) -> list[float]:
    """1024 flottants EXACTEMENT représentables en float32.

    pgvector stocke des float4 : avec 0.1, la base rendrait 0.10000000149011612 et la
    comparaison échouerait pour une raison qui n'a rien à voir avec la restauration. Les
    multiples de 1/256 traversent l'aller-retour sans perte, donc une différence constatée
    est une VRAIE différence."""
    return [((graine * 37 + k) % 512) / 256.0 for k in range(DIM)]


def _couple(nom: str, ordre: int, nb_chunks: int, modele: str = MODELE) -> tuple[int, list[dict]]:
    """Un référentiel et ses chunks, en base. Renvoie (referentiel_id, chunks attendus)."""
    attendus = [
        {"chunk_index": i, "option_ab": ["A", "B", ""][i % 3], "page": i + 1,
         "texte": f"Unité {i} du couple {nom} — accents é à ç, guillemets « ».",
         "embedding": _vecteur(i), "embedding_model": modele}
        for i in range(nb_chunks)
    ]
    with dbmod.SessionLocal() as db:
        cyc = Cycle(nom=f"RC-{nom}", ordre=ordre); db.add(cyc); db.flush()
        niv = Niveau(cycle_id=cyc.id, nom=f"RC-Niv-{nom}", ordre=ordre); db.add(niv); db.flush()
        ref = Referentiel(niveau_id=niv.id, nom_fixe=f"rc_{nom}", collection=f"rc_{nom}")
        db.add(ref); db.flush()
        rid = ref.id
        for c in attendus:
            db.add(ReferentielChunk(referentiel_id=rid, **c))
        db.commit()
    return rid, attendus


def _chunks_en_base(rid: int) -> list[dict]:
    with dbmod.SessionLocal() as db:
        rows = db.query(ReferentielChunk).filter(
            ReferentielChunk.referentiel_id == rid
        ).order_by(ReferentielChunk.chunk_index).all()
        return [{"chunk_index": r.chunk_index, "option_ab": r.option_ab, "page": r.page,
                 "texte": r.texte, "embedding": [float(x) for x in r.embedding],
                 "embedding_model": r.embedding_model} for r in rows]


def _purger(rid: int) -> None:
    with dbmod.SessionLocal() as db:
        db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == rid).delete()
        db.commit()


# ── LE LIVRABLE : l'aller-retour complet ────────────────────────────────────────────────

def test_aller_retour_complet_sauvegarde_purge_restaure_a_l_identique(tmp_path, monkeypatch):
    """Sauvegarder, tout perdre, tout retrouver — texte ET vecteurs, ligne à ligne.

    C'est LE test du point : sans lui, « il existe un fichier de sauvegarde » n'est pas
    « on sait revenir ». Il échoue si on retire la restauration : la base reste vide."""
    monkeypatch.setattr(pgvector_store, "BACKUP_DIR", tmp_path)
    rid, attendus = _couple("aller", 90, 5)

    # 1. Sauvegarder
    with dbmod.SessionLocal() as db:
        res = pgvector_store._sauvegarder_chunks_avant_purge(db, rid, "rc_aller")
    assert res["lignes"] == 5
    fichier = tmp_path / res["sauvegarde"]

    # 2. Tout perdre — la situation qu'on veut pouvoir défaire
    _purger(rid)
    assert _chunks_en_base(rid) == []

    # 3. Restaurer
    with dbmod.SessionLocal() as db:
        rapport = pgvector_store.restaurer_chunks_depuis_sauvegarde(db, fichier, rid, "rc_aller")
    assert rapport["restaures"] == 5

    # 4. Comparer LIGNE À LIGNE, vecteurs compris
    rendus = _chunks_en_base(rid)
    assert len(rendus) == len(attendus)
    for attendu, rendu in zip(attendus, rendus):
        assert rendu == attendu, f"le chunk {attendu['chunk_index']} n'est pas revenu à l'identique"


def test_les_vecteurs_voyagent_dans_le_fichier_donc_aucune_revectorisation(tmp_path, monkeypatch):
    """Ce qui rend le retour gratuit. Le dump porte les 1024 flottants : si le fichier ne
    les contenait pas, restaurer coûterait une re-vectorisation complète du couple — et
    ce ne serait plus un retour, mais une réingestion."""
    monkeypatch.setattr(pgvector_store, "BACKUP_DIR", tmp_path)
    rid, attendus = _couple("vecteurs", 91, 3)
    with dbmod.SessionLocal() as db:
        res = pgvector_store._sauvegarder_chunks_avant_purge(db, rid, "rc_vecteurs")

    lignes = [json.loads(l) for l in (tmp_path / res["sauvegarde"]).read_text(
        encoding="utf-8").splitlines()]
    assert [len(l["embedding"]) for l in lignes] == [DIM, DIM, DIM]
    assert lignes[0]["embedding"] == attendus[0]["embedding"]


# ── LES TROIS REFUS, un par un — et la base ne bouge dans aucun ─────────────────────────

def test_refus_un_fichier_qui_vise_un_autre_referentiel(tmp_path, monkeypatch):
    """Le fichier porte un nom de collection, mais un nom se renomme : c'est le
    referentiel_id écrit dans chaque ligne qui fait foi. Sans ce refus, restaurer la
    sauvegarde du mauvais couple écraserait un référentiel avec le contenu d'un autre."""
    monkeypatch.setattr(pgvector_store, "BACKUP_DIR", tmp_path)
    rid_a, _ = _couple("autreA", 92, 3)
    rid_b, avant_b = _couple("autreB", 93, 2)
    with dbmod.SessionLocal() as db:
        res = pgvector_store._sauvegarder_chunks_avant_purge(db, rid_a, "rc_autreA")

    with pytest.raises(RuntimeError, match="et non"):
        with dbmod.SessionLocal() as db:
            pgvector_store.restaurer_chunks_depuis_sauvegarde(
                db, tmp_path / res["sauvegarde"], rid_b, "rc_autreB")

    assert _chunks_en_base(rid_b) == avant_b, "le refus a quand même touché la base"


def test_refus_un_fichier_d_un_autre_modele_d_embedding(tmp_path, monkeypatch):
    """Des vecteurs de deux modèles ne se comparent pas. Le danger n'est pas le plantage,
    c'est l'absence de plantage : la recherche rendrait des résultats faux sans jamais
    signaler d'erreur. C'est le rôle de la colonne embedding_model."""
    monkeypatch.setattr(pgvector_store, "BACKUP_DIR", tmp_path)
    rid, avant = _couple("modele", 94, 3, modele="un-vieux-modele")
    with dbmod.SessionLocal() as db:
        res = pgvector_store._sauvegarder_chunks_avant_purge(db, rid, "rc_modele")

    with pytest.raises(RuntimeError, match="vieux-modele"):
        with dbmod.SessionLocal() as db:
            pgvector_store.restaurer_chunks_depuis_sauvegarde(
                db, tmp_path / res["sauvegarde"], rid, "rc_modele", modele_courant=MODELE)

    assert _chunks_en_base(rid) == avant, "le refus a quand même touché la base"


def test_l_etat_courant_est_sauvegarde_avant_d_etre_ecrase(tmp_path, monkeypatch):
    """Une restauration est une purge comme une autre : elle détruit l'état présent. On peut
    se tromper de fichier — il faut donc pouvoir revenir de la restauration elle-même."""
    monkeypatch.setattr(pgvector_store, "BACKUP_DIR", tmp_path)
    rid, _ = _couple("filet", 95, 4)
    with dbmod.SessionLocal() as db:
        vieux = pgvector_store._sauvegarder_chunks_avant_purge(db, rid, "rc_filet")

    # L'état change : on remplace les 4 chunks par 1 seul.
    _purger(rid)
    with dbmod.SessionLocal() as db:
        db.add(ReferentielChunk(referentiel_id=rid, chunk_index=0, option_ab="", page=1,
                                texte="etat intermediaire", embedding=_vecteur(99),
                                embedding_model=MODELE))
        db.commit()
    intermediaire = _chunks_en_base(rid)

    with dbmod.SessionLocal() as db:
        rapport = pgvector_store.restaurer_chunks_depuis_sauvegarde(
            db, tmp_path / vieux["sauvegarde"], rid, "rc_filet")

    assert rapport["restaures"] == 4
    filet = rapport["sauvegarde_avant_restauration"]
    assert filet["lignes"] == 1, "l'état d'avant la restauration n'a pas été sauvé"

    # Et ce filet est lui-même rejouable : on revient de la restauration.
    with dbmod.SessionLocal() as db:
        pgvector_store.restaurer_chunks_depuis_sauvegarde(
            db, tmp_path / filet["sauvegarde"], rid, "rc_filet")
    assert _chunks_en_base(rid) == intermediaire


# ── Ce que la lecture refuse avant même d'approcher la base ─────────────────────────────

def test_un_fichier_vide_ne_sert_pas_de_purge_deguisee(tmp_path, monkeypatch):
    """La seule manière dont cet outil pourrait détruire quelque chose : rejouer un fichier
    sans lignes, c'est-à-dire purger sans rien remettre. Refusé à la lecture."""
    monkeypatch.setattr(pgvector_store, "BACKUP_DIR", tmp_path)
    rid, avant = _couple("vide", 96, 2)
    vide = tmp_path / "referentiel_chunks-rc_vide.bak-20260802-000000-000000.jsonl"
    vide.write_text("", encoding="utf-8")

    with pytest.raises(RuntimeError, match="vide"):
        with dbmod.SessionLocal() as db:
            pgvector_store.restaurer_chunks_depuis_sauvegarde(db, vide, rid, "rc_vide")
    assert _chunks_en_base(rid) == avant


def test_un_fichier_absent_ou_abime_le_dit_au_lieu_de_planter(tmp_path):
    """Règle 23 : le message nomme le fichier et dit où chercher. Une ligne de JSON abîmée
    arrête tout AVANT la base — la moitié d'un fichier restaurée serait le pire résultat."""
    with pytest.raises(RuntimeError, match="introuvable"):
        pgvector_store.lire_sauvegarde(tmp_path / "pas_la.jsonl")

    abime = tmp_path / "abime.jsonl"
    abime.write_text('{"referentiel_id": 1, "chunk_index": 0, "option_ab": "", "page": 1,'
                     ' "texte": "ok", "embedding": [0.5], "embedding_model": "m"}\n'
                     'ceci n est pas du json\n', encoding="utf-8")
    with pytest.raises(RuntimeError, match="ligne 2"):
        pgvector_store.lire_sauvegarde(abime)

    incomplet = tmp_path / "incomplet.jsonl"
    incomplet.write_text('{"referentiel_id": 1, "chunk_index": 0}\n', encoding="utf-8")
    with pytest.raises(RuntimeError, match="embedding"):
        pgvector_store.lire_sauvegarde(incomplet)
