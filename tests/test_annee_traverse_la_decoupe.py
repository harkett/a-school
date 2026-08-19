r"""Preuve — l'année rendue par la découpe arrive intacte dans la colonne, et "" devient NULL.

CE QUE LE TEST PROUVE (IA MOCKÉE — aucun appel, 0 €) :
  1. Une unité que la découpe dit restreinte à une année arrive avec cette année en base.
  2. Une unité sans année (chaîne vide) arrive en NULL — PAS en chaîne vide. C'est vital : le
     filtre RAG lit NULL comme « commune à tout le cycle ». Une chaîne vide stockée telle quelle
     n'est égale à aucune année, et l'unité disparaîtrait pour TOUS les profs.
  3. Le champ traverse `_trancher_par_titres` sans se mélanger à `option` : deux unités voisines
     gardent chacune la sienne.
  4. Une découpe muette (aucune année rendue) ne marque rien : tout reste commun, personne n'est
     amputé — le repli d'un prompt qui n'a pas encore appris l'année.

Base de test PostgreSQL dédiée (aschool_test via conftest.py) — JAMAIS SQLite.
Lancer : docker compose exec backend python -m pytest tests/test_annee_traverse_la_decoupe.py -q
"""
from backend.rag.analyse_amont import _trancher_par_titres, _SCHEMA_DECOUPE

TEXTE = "\n".join([
    "Classe de 5e",
    "Theme 1 Chretientes et islam",
    "Contenu du theme de cinquieme, sur plusieurs lignes.",
    "Theme 2 Societe et pouvoir",
    "Contenu du second theme de cinquieme.",
    "Volet 1 les specificites du cycle",
    "Contenu commun a tout le cycle, valable pour toutes les annees.",
])


def _entrees():
    return [
        {"titre": "Classe de 5e", "option": "", "annee": "", "garder": False},
        {"titre": "Theme 1 Chretientes et islam", "option": "Histoire", "annee": "5e", "garder": True},
        {"titre": "Theme 2 Societe et pouvoir", "option": "Histoire", "annee": "5e", "garder": True},
        {"titre": "Volet 1 les specificites du cycle", "option": "", "annee": "", "garder": True},
    ]


def test_le_schema_exige_l_annee():
    """Strict et `required` : le champ existe même si le prompt du couple oublie de le demander."""
    item = _SCHEMA_DECOUPE["properties"]["unites"]["items"]
    assert "annee" in item["properties"]
    assert "annee" in item["required"]
    assert item["additionalProperties"] is False


def test_l_annee_traverse_le_tranchage_sans_se_melanger_a_l_option():
    unites = _trancher_par_titres(TEXTE, _entrees())
    par_titre = {u["titre"]: u for u in unites}
    assert par_titre["Theme 1 Chretientes et islam"]["annee"] == "5e"
    assert par_titre["Theme 1 Chretientes et islam"]["option"] == "Histoire"
    assert par_titre["Volet 1 les specificites du cycle"]["annee"] == ""
    assert par_titre["Volet 1 les specificites du cycle"]["option"] == ""


def test_une_decoupe_muette_ne_marque_rien():
    """Aucune année rendue : tout reste commun. Le prof garde tout, personne n'est amputé."""
    entrees = [dict(e, annee="") for e in _entrees()]
    assert {u["annee"] for u in _trancher_par_titres(TEXTE, entrees)} == {""}


def test_une_entree_sans_le_champ_ne_casse_pas():
    """Les appels d'avant le champ (dicts à trois clés, ou simples chaînes) marchent tels quels."""
    entrees = [{"titre": e["titre"], "option": e["option"], "garder": e["garder"]}
               for e in _entrees()]
    assert {u["annee"] for u in _trancher_par_titres(TEXTE, entrees)} == {""}
    assert {u["annee"] for u in _trancher_par_titres(TEXTE, ["Theme 1 Chretientes et islam"])} == {""}


def test_chaine_vide_devient_NULL_en_base(monkeypatch):
    """Le bout de la chaîne : ce que la découpe rend finit dans la colonne, "" en NULL."""
    import backend.core.database as dbmod
    from backend.core.models_db import (Cycle, Niveau, Referentiel, ReferentielChunk,
                                        ReferentielDocument)
    from backend.rag import pgvector_store as pg

    db = dbmod.SessionLocal()
    try:
        cyc = Cycle(nom="TA-Cycle", ordre=1); db.add(cyc); db.flush()
        niv = Niveau(cycle_id=cyc.id, nom="TA-5e", ordre=1); db.add(niv); db.flush()
        ref = Referentiel(niveau_id=niv.id, nom_fixe="TA-ref", collection="ta_ref",
                          texte_epure=TEXTE, prompt_decoupe="p")
        db.add(ref); db.flush()
        # Le document du dépôt : les unités écrites par la découpe s'y rattachent.
        db.add(ReferentielDocument(referentiel_id=ref.id, fichier="doc.pdf", texte_epure=TEXTE))
        db.commit()
        rid = ref.id
    finally:
        db.close()

    chunks = [{"text": "Theme 1", "page": 1, "meta": {"option": "Histoire", "annee": "5e"}},
              {"text": "Volet 1", "page": 1, "meta": {"option": "", "annee": ""}}]
    monkeypatch.setattr(pg, "embed_texts", lambda textes: [[0.2] * 1024 for _ in textes])
    monkeypatch.setattr(pg, "_pdf_path_for", lambda db, ref: __import__("pathlib").Path(__file__))
    pg.ingest_pgvector(collection="ta_ref", decoupe_prete={"prompt": "p", "chunks": chunks})

    db = dbmod.SessionLocal()
    try:
        lignes = (db.query(ReferentielChunk.texte, ReferentielChunk.annee)
                    .filter(ReferentielChunk.referentiel_id == rid)
                    .order_by(ReferentielChunk.chunk_index).all())
    finally:
        db.close()
    assert dict(lignes) == {"Theme 1": "5e", "Volet 1": None}   # None, jamais ""
