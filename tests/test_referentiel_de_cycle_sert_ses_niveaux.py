r"""Preuve — un référentiel de CYCLE sert toutes ses années, et jamais une année voisine.

LE DÉFAUT CORRIGÉ. `referentiels.niveau_id` répondait à « quel référentiel pour ce prof ? ». Un
programme de cycle n'étant rattaché qu'à un niveau, les profs des autres années du même cycle
n'avaient AUCUN référentiel : pas d'erreur, juste « available: false » — un défaut qui se présente
comme un état normal.

CE QUE LE TEST PROUVE :
  1. Les trois années du cycle atteignent le même référentiel par la porte unique.
  2. Une année VOISINE du même cycle en base (la 6e du collège, hors cycle 4) n'y a pas accès :
     le rattachement est explicite, jamais déduit du cycle.
  3. `UNIQUE(niveau_id)` : un niveau ne peut pas être servi par deux référentiels.
  4. Tout référentiel créé dessert d'emblée son niveau porteur — l'invariant est tenu par le
     modèle, donc il vaut aussi pour les référentiels d'un seul niveau.
  5. Le référentiel supprimé emporte ses rattachements (CASCADE), sans laisser un niveau pointer
     vers un référentiel disparu.

Base de test PostgreSQL dédiée (aschool_test via conftest.py) — JAMAIS SQLite.
Lancer : docker compose exec backend python -m pytest tests/test_referentiel_de_cycle_sert_ses_niveaux.py -q
"""
import pytest
from sqlalchemy.exc import IntegrityError

import backend.core.database as dbmod
from backend.core.models_db import Cycle, Niveau, Referentiel, ReferentielNiveau
from backend.core.resolution_couple import referentiel_du_niveau, referentiel_du_niveau_nomme

ANNEES = ("RC-5e", "RC-4e", "RC-3e")
HORS_CYCLE = "RC-6e"


@pytest.fixture
def cycle_et_referentiel():
    """Un cycle de quatre niveaux, un référentiel porté par la 4e et desservant les trois années
    du cycle 4 — la 6e reste dehors, comme dans le vrai collège."""
    db = dbmod.SessionLocal()
    try:
        cyc = Cycle(nom="RC-College", ordre=1); db.add(cyc); db.flush()
        niveaux = {}
        for i, nom in enumerate((HORS_CYCLE,) + ANNEES):
            n = Niveau(cycle_id=cyc.id, nom=nom, ordre=i); db.add(n); db.flush()
            niveaux[nom] = n.id
        ref = Referentiel(niveau_id=niveaux["RC-4e"], nom_fixe="RC-cycle4", collection="rc_cycle4")
        db.add(ref); db.flush()
        # Les DEUX autres années : ce que fait la migration pour le cycle 4 réel.
        for nom in ("RC-5e", "RC-3e"):
            db.add(ReferentielNiveau(referentiel_id=ref.id, niveau_id=niveaux[nom]))
        db.commit()
        return {"ref_id": ref.id, "niveaux": niveaux}
    finally:
        db.close()


def test_les_trois_annees_atteignent_le_meme_referentiel(cycle_et_referentiel):
    ids, rid = cycle_et_referentiel["niveaux"], cycle_et_referentiel["ref_id"]
    db = dbmod.SessionLocal()
    try:
        assert [referentiel_du_niveau(db, ids[n]) for n in ANNEES] == [rid, rid, rid]
        assert [referentiel_du_niveau_nomme(db, n) for n in ANNEES] == [rid, rid, rid]
    finally:
        db.close()


def test_une_annee_voisine_du_meme_cycle_n_y_a_pas_acces(cycle_et_referentiel):
    """Le cycle « Collège » porte la 6e, que le cycle 4 ne couvre pas : rattacher au CYCLE aurait
    donné le programme du cycle 4 aux profs de 6e."""
    db = dbmod.SessionLocal()
    try:
        assert referentiel_du_niveau(db, cycle_et_referentiel["niveaux"][HORS_CYCLE]) is None
        assert referentiel_du_niveau_nomme(db, HORS_CYCLE) is None
    finally:
        db.close()


def test_un_niveau_ne_peut_pas_etre_servi_par_deux_referentiels(cycle_et_referentiel):
    db = dbmod.SessionLocal()
    try:
        autre = Referentiel(niveau_id=cycle_et_referentiel["niveaux"][HORS_CYCLE],
                            nom_fixe="RC-autre", collection="rc_autre")
        db.add(autre); db.flush()
        db.add(ReferentielNiveau(referentiel_id=autre.id,
                                 niveau_id=cycle_et_referentiel["niveaux"]["RC-5e"]))
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback(); db.close()


def test_tout_referentiel_cree_dessert_son_niveau_porteur(cycle_et_referentiel):
    """L'invariant est tenu par le modèle : rien à écrire chez celui qui crée le référentiel."""
    db = dbmod.SessionLocal()
    try:
        seul = Referentiel(niveau_id=cycle_et_referentiel["niveaux"][HORS_CYCLE],
                           nom_fixe="RC-seul", collection="rc_seul")
        db.add(seul); db.commit()
        assert referentiel_du_niveau(db, cycle_et_referentiel["niveaux"][HORS_CYCLE]) == seul.id
    finally:
        db.close()


def test_supprimer_le_referentiel_emporte_ses_rattachements(cycle_et_referentiel):
    ids, rid = cycle_et_referentiel["niveaux"], cycle_et_referentiel["ref_id"]
    db = dbmod.SessionLocal()
    try:
        db.delete(db.get(Referentiel, rid)); db.commit()
        assert db.query(ReferentielNiveau).filter(
            ReferentielNiveau.referentiel_id == rid).count() == 0
        assert [referentiel_du_niveau(db, ids[n]) for n in ANNEES] == [None, None, None]
    finally:
        db.close()
