r"""Preuve — un programme de CYCLE ne sert au prof que SON année (+ le commun du cycle).

LE DÉFAUT CORRIGÉ. Le programme du cycle 4 est UN document pour TROIS années : le référentiel
de la 4e contenait aussi les entrées de français et les thèmes d'histoire-géo de 5e et de 3e.
Un prof de 4e pouvait donc recevoir une activité bâtie sur un contenu qu'il n'enseigne pas.

CE QUE LE TEST PROUVE (embeddings MOCKÉS — déterministe, aucun modèle chargé, 0 €) :
  1. Le prof de 4e reçoit ses unités de 4e ET les unités communes (annee IS NULL), et JAMAIS
     celles de 5e ou de 3e.
  2. Le prof de 5e du même référentiel reçoit les siennes — la découpe n'est pas rejouée, c'est
     bien le MÊME document qui sert deux années différemment.
  3. `annee=None` (prof sans niveau résolu) ne rend que le commun, jamais une année : le repli
     est étroit, il ne fuit pas.
  4. Un référentiel d'un seul niveau (toutes ses unités en NULL) rend TOUT — le filtre n'ampute
     personne d'autre.
  5. `annee` est OBLIGATOIRE : un appel qui l'oublie lève TypeError au lieu de fuir en silence.
     C'est le point le plus important : un paramètre optionnel se serait oublié un jour, et la
     fuite serait revenue sans le moindre message.

Base de test PostgreSQL dédiée (aschool_test via conftest.py) — JAMAIS SQLite.
Lancer : docker compose exec backend python -m pytest tests/test_annee_du_cycle_filtre_le_rag.py -q
"""
from datetime import date
from unittest.mock import patch

import pytest

import backend.core.database as dbmod
from backend.core.models_db import (Cycle, Niveau, Referentiel, ReferentielChunk,
                                    ReferentielDocument)
from backend.rag.pgvector_store import retrieve_pg

VECTEUR = [0.1] * 1024          # un seul vecteur pour toutes les unités : le tri par distance
                                # est alors sans effet, et seul le FILTRE explique ce qui sort.

# (texte, annee) — le cycle 4 en miniature : 3 unités datées, 2 communes.
UNITES = [("Le voyage et l'aventure", "5e"),
          ("Dire l'amour", "4e"),
          ("Se raconter, se representer", "3e"),
          ("Volet 1 : les specificites du cycle 4", None),
          ("Reperes de progressivite : des la 5e, puis en 3e", None)]


@pytest.fixture
def cycle4():
    """Un référentiel de CYCLE (5 unités) + un référentiel d'un seul niveau (2 unités, sans
    année). Nettoyé par le TRUNCATE de conftest.py."""
    db = dbmod.SessionLocal()
    try:
        cyc = Cycle(nom="AN-College", ordre=1)
        db.add(cyc); db.flush()
        n4 = Niveau(cycle_id=cyc.id, nom="AN-4e", ordre=1)
        n_bts = Niveau(cycle_id=cyc.id, nom="AN-BTS", ordre=2)
        db.add_all([n4, n_bts]); db.flush()
        ref = Referentiel(niveau_id=n4.id, nom_fixe="AN-cycle4", collection="an_cycle4")
        solo = Referentiel(niveau_id=n_bts.id, nom_fixe="AN-solo", collection="an_solo")
        db.add_all([ref, solo]); db.flush()
        # Chaque unité sort d'un document et dit ce qu'elle couvre : ici aucune matière n'est
        # liée, donc le tri par matière ne s'applique pas — seule l'année filtre, comme avant.
        doc = ReferentielDocument(referentiel_id=ref.id, fichier="cycle4.pdf")
        doc_solo = ReferentielDocument(referentiel_id=solo.id, fichier="solo.pdf")
        db.add_all([doc, doc_solo]); db.flush()
        for i, (texte, annee) in enumerate(UNITES):
            db.add(ReferentielChunk(referentiel_id=ref.id, document_id=doc.id,
                                    portee="matiere", valide_du=date.today(),
                                    chunk_index=i, option_ab="",
                                    annee=annee, page=1, texte=texte,
                                    embedding=VECTEUR, embedding_model="test"))
        for i, texte in enumerate(["Bloc 1 du BTS", "Bloc 2 du BTS"]):
            db.add(ReferentielChunk(referentiel_id=solo.id, document_id=doc_solo.id,
                                    portee="matiere", valide_du=date.today(),
                                    chunk_index=i, option_ab="",
                                    annee=None, page=1, texte=texte,
                                    embedding=VECTEUR, embedding_model="test"))
        db.commit()
    finally:
        db.close()


def _textes(collection, annee, top_k=10):
    """retrieve_pg avec l'embedding de la QUESTION mocké — aucun modèle n'est chargé."""
    with patch("backend.rag.pgvector_store.embed_texts", return_value=[VECTEUR]):
        chunks = retrieve_pg(collection, "une question", top_k=top_k,
                             schema="public", annee=annee, matiere=None)
    return {c["text"] for c in chunks}


def test_le_prof_de_4e_recoit_sa_4e_et_le_commun_jamais_les_autres_annees(cycle4):
    textes = _textes("an_cycle4", "4e")
    assert "Dire l'amour" in textes
    assert "Volet 1 : les specificites du cycle 4" in textes
    assert "Reperes de progressivite : des la 5e, puis en 3e" in textes
    assert "Le voyage et l'aventure" not in textes      # 5e — la fuite d'avant
    assert "Se raconter, se representer" not in textes  # 3e — la fuite d'avant
    assert len(textes) == 3


def test_le_meme_document_sert_la_5e_sans_etre_redecoupe(cycle4):
    textes = _textes("an_cycle4", "5e")
    assert "Le voyage et l'aventure" in textes
    assert "Dire l'amour" not in textes
    assert len(textes) == 3                             # sa 5e + les 2 communes


def test_sans_annee_le_repli_ne_rend_que_le_commun(cycle4):
    textes = _textes("an_cycle4", None)
    assert textes == {"Volet 1 : les specificites du cycle 4",
                      "Reperes de progressivite : des la 5e, puis en 3e"}


def test_un_referentiel_d_un_seul_niveau_rend_tout(cycle4):
    """Toutes ses unités sont en NULL : le filtre ne lui retire rien, quelle que soit l'année."""
    assert _textes("an_solo", "AN-BTS") == {"Bloc 1 du BTS", "Bloc 2 du BTS"}


def test_annee_est_obligatoire(cycle4):
    """Sans valeur par défaut : l'oubli est une erreur immédiate, jamais une fuite silencieuse."""
    with pytest.raises(TypeError):
        retrieve_pg("an_cycle4", "une question", schema="public", matiere=None)
