r"""Preuve — la liste des référentiels montre TOUS les niveaux desservis, pas seulement le porteur.

LE DÉFAUT CORRIGÉ. La liste affichait « Collège · 4e » pour un document qui sert aussi la 5e et la
3e. Un administrateur venu modifier le programme de la 3e ne trouvait aucune ligne pour la 3e : il
en déduisait qu'il n'y en avait pas, et en déposait un second. Rien ne le détrompait.

CE QUE LE TEST PROUVE :
  1. Le nom se calcule depuis les niveaux desservis, dans l'ordre du cycle.
  2. Un référentiel d'un seul niveau écrit ce seul niveau — les autres ne changent pas d'aspect.
  3. Le nom SUIT les rattachements : un niveau ajouté, un niveau retiré, et il se réécrit.
  4. La liste admin le renvoie, et renvoie TOUJOURS le niveau porteur à côté — c'est lui qui
     ouvre la fiche du couple, le remplacer casserait la navigation.

Base de test PostgreSQL dédiée (aschool_test via conftest.py) — JAMAIS SQLite.
Lancer : docker compose exec backend python -m pytest tests/test_nom_affichage_du_referentiel.py -q
"""
import pytest

import backend.core.database as dbmod
from backend.core.models_db import Cycle, Niveau, Referentiel, ReferentielNiveau
from backend.core.resolution_couple import recalculer_nom_affichage

ANNEES = ("NA-5e", "NA-4e", "NA-3e")


@pytest.fixture
def cycle():
    db = dbmod.SessionLocal()
    try:
        cyc = Cycle(nom="NA-College", ordre=1); db.add(cyc); db.flush()
        ids = {}
        for i, nom in enumerate(ANNEES):           # ordre 0,1,2 = l'ordre du cycle
            n = Niveau(cycle_id=cyc.id, nom=nom, ordre=i); db.add(n); db.flush()
            ids[nom] = n.id
        ref = Referentiel(niveau_id=ids["NA-4e"], nom_fixe="NA-ref", collection="na_ref")
        db.add(ref); db.flush()
        rid = ref.id
        db.commit()
        return {"rid": rid, "ids": ids}
    finally:
        db.close()


def test_un_seul_niveau_ecrit_ce_seul_niveau(cycle):
    """L'état des cinq référentiels d'un seul niveau : leur ligne ne change pas d'aspect."""
    db = dbmod.SessionLocal()
    try:
        assert recalculer_nom_affichage(db, cycle["rid"]) == "NA-4e"
        db.commit()
        assert db.get(Referentiel, cycle["rid"]).nom_affichage == "NA-4e"
    finally:
        db.close()


def test_le_nom_suit_les_rattachements(cycle):
    """Ajout puis retrait : le nom se réécrit, il ne reste jamais sur une valeur périmée."""
    db = dbmod.SessionLocal()
    try:
        for nom in ("NA-5e", "NA-3e"):
            db.add(ReferentielNiveau(referentiel_id=cycle["rid"], niveau_id=cycle["ids"][nom]))
        db.flush()
        assert recalculer_nom_affichage(db, cycle["rid"]) == "NA-5e, NA-4e, NA-3e"

        db.query(ReferentielNiveau).filter(
            ReferentielNiveau.referentiel_id == cycle["rid"],
            ReferentielNiveau.niveau_id == cycle["ids"]["NA-5e"]).delete()
        db.flush()
        assert recalculer_nom_affichage(db, cycle["rid"]) == "NA-4e, NA-3e"
        db.commit()
    finally:
        db.close()


def test_l_ordre_est_celui_du_cycle_pas_celui_des_rattachements(cycle):
    """La 3e est rattachée AVANT la 5e : le nom doit quand même dire « 5e, 4e, 3e »."""
    db = dbmod.SessionLocal()
    try:
        db.add(ReferentielNiveau(referentiel_id=cycle["rid"], niveau_id=cycle["ids"]["NA-3e"]))
        db.flush()
        db.add(ReferentielNiveau(referentiel_id=cycle["rid"], niveau_id=cycle["ids"]["NA-5e"]))
        db.flush()
        assert recalculer_nom_affichage(db, cycle["rid"]) == "NA-5e, NA-4e, NA-3e"
        db.commit()
    finally:
        db.close()


def test_la_liste_admin_rend_le_nom_ET_le_niveau_porteur(cycle):
    """Le porteur reste dans la réponse : c'est lui qui ouvre la fiche du couple."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.systeme.admin import _make_admin_token

    db = dbmod.SessionLocal()
    try:
        for nom in ("NA-5e", "NA-3e"):
            db.add(ReferentielNiveau(referentiel_id=cycle["rid"], niveau_id=cycle["ids"][nom]))
        db.flush()
        recalculer_nom_affichage(db, cycle["rid"])
        db.commit()
    finally:
        db.close()

    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    r = c.get("/api/admin/referentiels/liste")
    assert r.status_code == 200, r.text
    ligne = next(x for x in r.json()["referentiels"] if x["id"] == cycle["rid"])
    assert ligne["nom_affichage"] == "NA-5e, NA-4e, NA-3e"
    assert ligne["niveau"] == "NA-4e"          # le porteur, intact — il ouvre la fiche
