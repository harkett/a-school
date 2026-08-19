# -*- coding: utf-8 -*-
"""L'unité sait d'où elle vient, de quoi elle parle, et jusqu'à quand elle vaut (19/08/2026).

CE QUE CES TROIS SCÉNARIOS TIENNENT — les trois raisons d'être de l'étape 1 du chantier
« la matière sur l'unité, et le dépôt par arrêté » :

  1. UN REDÉPÔT NE TOUCHE QUE SES UNITÉS. Avant, refaire un texte effaçait la découpe du
     référentiel ENTIER : rien ne désignait les unités venues du document remplacé. Une réforme
     d'un seul programme obligeait donc à tout refaire — et à tout repayer.

  2. LA MATIÈRE TRIE. La recherche ne classait que sur la ressemblance du texte : rien
     n'empêchait un prof de maths de recevoir une unité de français. Les textes de CADRE
     (portée `formation`), eux, ne se rattachent à personne et arrivent à tout le monde.

  3. CE QUI EST FERMÉ NE SERT PLUS. Une unité dont la plage est close reste en base — c'est
     tout l'intérêt de la plage, le texte d'avant n'est pas détruit — mais elle ne doit plus
     nourrir une seule génération.

Lancer : docker compose exec backend python -m pytest tests/test_document_matiere_validite.py -q
"""
from datetime import date, timedelta
from unittest.mock import patch

import backend.core.database as dbmod
from backend.core.models_db import (Cycle, Matiere, Niveau, Referentiel, ReferentielChunk,
                                    ReferentielChunkMatiere, ReferentielDocument)
from backend.rag import pgvector_store as pg

DIM = 1024
VECTEUR = [0.1] * DIM


def _referentiel(nom: str, ordre: int) -> int:
    with dbmod.SessionLocal() as db:
        cyc = Cycle(nom=f"DM-{nom}", ordre=ordre); db.add(cyc); db.flush()
        niv = Niveau(cycle_id=cyc.id, nom=f"DM-Niv-{nom}", ordre=ordre); db.add(niv); db.flush()
        ref = Referentiel(niveau_id=niv.id, nom_fixe=f"dm_{nom}", collection=f"dm_{nom}",
                          texte_epure="TEXTE", prompt_decoupe="p", prompt_decoupe_valide=True)
        db.add(ref); db.flush()
        db.commit()
        return ref.id


def _document(rid: int, fichier: str) -> int:
    with dbmod.SessionLocal() as db:
        doc = ReferentielDocument(referentiel_id=rid, fichier=fichier, texte_epure="TEXTE")
        db.add(doc); db.flush(); db.commit()
        return doc.id


def _unite(rid: int, doc_id: int, texte: str, *, portee: str = "matiere",
           matiere_id: int | None = None, valide_du: date | None = None,
           valide_au: date | None = None, index: int = 0) -> int:
    with dbmod.SessionLocal() as db:
        u = ReferentielChunk(referentiel_id=rid, document_id=doc_id, portee=portee,
                             valide_du=valide_du or date.today(), valide_au=valide_au,
                             chunk_index=index, option_ab="", page=1, texte=texte,
                             embedding=VECTEUR, embedding_model=pg.EMBEDDING_MODEL)
        db.add(u); db.flush()
        if matiere_id is not None:
            db.add(ReferentielChunkMatiere(chunk_id=u.id, matiere_id=matiere_id))
        db.commit()
        return u.id


def _matiere(rid: int, nom: str, ordre: int) -> int:
    with dbmod.SessionLocal() as db:
        m = Matiere(referentiel_id=rid, nom=nom, ordre=ordre, actif=True, validee=True)
        db.add(m); db.flush(); db.commit()
        return m.id


def _textes(collection: str, matiere: str | None, annee: str | None = None) -> set[str]:
    """La recherche, avec l'embedding de la question mocké — aucun modèle n'est chargé."""
    with patch.object(pg, "embed_texts", return_value=[VECTEUR]):
        chunks = pg.retrieve_pg(collection, "une question", top_k=50, schema="public",
                                annee=annee, matiere=matiere)
    return {c["text"] for c in chunks}


# ── 1. LE REDÉPÔT NE TOUCHE QUE SES UNITÉS ───────────────────────────────────────────────────

def test_redecouper_un_document_laisse_les_unites_de_l_autre():
    rid = _referentiel("Deux", 401)
    arrete_a = _document(rid, "arrete-A.pdf")
    arrete_b = _document(rid, "arrete-B.pdf")
    _unite(rid, arrete_a, "Unite de l arrete A", index=0)
    _unite(rid, arrete_b, "Unite de l arrete B", index=0)

    # La découpe vise LE document courant — le plus récent, donc l'arrêté B.
    with dbmod.SessionLocal() as db:
        assert pg.document_courant(db, rid) == arrete_b

    neuve = [{"text": "Unite refaite de B", "page": 1, "meta": {"option": "", "annee": ""}}]
    with patch.object(pg, "embed_texts", side_effect=lambda t: [VECTEUR for _ in t]), \
         patch.object(pg, "_sauvegarder_chunks_avant_purge", return_value={"sauvegarde": None}):
        pg.ingest_pgvector(collection="dm_Deux", decoupe_prete={"prompt": "p", "chunks": neuve})

    with dbmod.SessionLocal() as db:
        restant = {c.texte: c.document_id for c in
                   db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == rid).all()}
    # L'unité de l'arrêté A n'a pas bougé : c'est tout le chantier.
    assert restant == {"Unite de l arrete A": arrete_a, "Unite refaite de B": arrete_b}


def test_une_unite_neuve_nait_a_etiqueter_et_en_vigueur():
    """Portée 'matiere' SANS liaison = « reste à étiqueter », et non « vaut pour toutes »."""
    rid = _referentiel("Neuve", 402)
    _document(rid, "arrete.pdf")
    neuve = [{"text": "Unite fraiche", "page": 1, "meta": {"option": "", "annee": ""}}]
    with patch.object(pg, "embed_texts", side_effect=lambda t: [VECTEUR for _ in t]), \
         patch.object(pg, "_sauvegarder_chunks_avant_purge", return_value={"sauvegarde": None}):
        pg.ingest_pgvector(collection="dm_Neuve", decoupe_prete={"prompt": "p", "chunks": neuve})

    with dbmod.SessionLocal() as db:
        u = db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == rid).one()
        assert u.portee == "matiere"
        assert u.valide_du == date.today()
        assert u.valide_au is None
        assert db.query(ReferentielChunkMatiere).filter(
            ReferentielChunkMatiere.chunk_id == u.id).count() == 0


# ── 2. LA MATIÈRE TRIE, LE CADRE PASSE TOUJOURS ──────────────────────────────────────────────

def test_le_prof_recoit_sa_matiere_et_les_textes_de_cadre_jamais_une_autre_matiere():
    rid = _referentiel("Tri", 403)
    doc = _document(rid, "arrete.pdf")
    maths = _matiere(rid, "DM-Maths", 1)
    francais = _matiere(rid, "DM-Francais", 2)
    _unite(rid, doc, "Theoreme", matiere_id=maths, index=0)
    _unite(rid, doc, "Figures de style", matiere_id=francais, index=1)
    _unite(rid, doc, "Socle commun", portee="formation", index=2)

    assert _textes("dm_Tri", "DM-Maths") == {"Theoreme", "Socle commun"}
    assert _textes("dm_Tri", "DM-Francais") == {"Figures de style", "Socle commun"}
    # Prof sans matière résolue : il reste le cadre, jamais le programme d'une matière.
    assert _textes("dm_Tri", None) == {"Socle commun"}


def test_un_referentiel_sans_aucune_liaison_rend_tout_comme_avant():
    """LE TEMPS DU CHANTIER. Les référentiels existants ne sont pas encore étiquetés (étape 2) :
    tant qu'aucune unité n'est liée, la matière ne peut rien trier — et ils continuent de
    servir. Filtrer là-dessus aurait vidé la recherche du jour au lendemain."""
    rid = _referentiel("Pas-Etiquete", 404)
    doc = _document(rid, "arrete.pdf")
    _matiere(rid, "DM-Maths", 1)
    _unite(rid, doc, "Une unite", index=0)
    _unite(rid, doc, "Une autre", index=1)

    assert _textes("dm_Pas-Etiquete", "DM-Maths") == {"Une unite", "Une autre"}
    assert _textes("dm_Pas-Etiquete", "DM-Nimporte-Quoi") == {"Une unite", "Une autre"}


def test_le_cadre_s_ajoute_a_la_matiere_et_ne_lui_prend_pas_ses_places():
    """LE CADRE NE CONCOURT PAS, ET IL NE S'ÉTALE PAS. Mesuré le 19/08/2026 sur le Collège 4e :
    dans une recherche unique, les 9 unités de socle prenaient 3 places sur 5 en français — elles
    gagnent au classement parce qu'elles parlent large. La discipline garde donc toutes les
    places demandées, et le cadre en reçoit UNE de plus, à part : ces textes sont les plus gros
    du référentiel (3 451 caractères de moyenne) et chacun part dans un appel payant."""
    rid = _referentiel("Cadre", 406)
    doc = _document(rid, "arrete.pdf")
    maths = _matiere(rid, "DM-Maths", 1)
    for i in range(3):
        _unite(rid, doc, f"Programme {i}", matiere_id=maths, index=i)
    for i in range(5):
        _unite(rid, doc, f"Socle {i}", portee="formation", index=10 + i)

    rendu = _textes("dm_Cadre", "DM-Maths")
    programme = {t for t in rendu if t.startswith("Programme")}
    cadre = {t for t in rendu if t.startswith("Socle")}
    assert len(programme) == 3, "la discipline a perdu des places"
    assert len(cadre) == pg.CADRE_MAX, f"le cadre déborde son plafond : {len(cadre)}"

    # Prof sans matière résolue : il n'y a aucune place à protéger, le cadre reprend les siennes.
    assert len(_textes("dm_Cadre", None)) == 5


# ── 3. CE QUI EST FERMÉ NE SERT PLUS ─────────────────────────────────────────────────────────

def test_une_unite_fermee_reste_en_base_mais_ne_sort_plus():
    rid = _referentiel("Plage", 405)
    doc = _document(rid, "arrete.pdf")
    maths = _matiere(rid, "DM-Maths", 1)
    hier = date.today() - timedelta(days=1)
    _unite(rid, doc, "Ancien programme", matiere_id=maths, index=0,
           valide_du=hier - timedelta(days=365), valide_au=hier)
    _unite(rid, doc, "Programme en vigueur", matiere_id=maths, index=1, valide_du=hier)
    # Un texte qui n'entre en vigueur que demain ne sert pas non plus aujourd'hui.
    _unite(rid, doc, "Programme a venir", matiere_id=maths, index=2,
           valide_du=date.today() + timedelta(days=1))

    assert _textes("dm_Plage", "DM-Maths") == {"Programme en vigueur"}
    with dbmod.SessionLocal() as db:
        assert db.query(ReferentielChunk).filter(
            ReferentielChunk.referentiel_id == rid).count() == 3   # rien n'a été détruit
