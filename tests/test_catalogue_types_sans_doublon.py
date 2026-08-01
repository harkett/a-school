r"""Le catalogue des types d'activité n'a jamais deux fois le même libellé.

CE QUE CE TEST PROUVE, et pourquoi il existe. Le catalogue s'identifie par LIBELLÉ, insensible
à la casse — c'est écrit dans le modèle lui-même (models_db.py, ActiviteType : « l'anti-doublon
du catalogue se fait par `label` »). Mais AUCUN unique ne le tient en base : la règle vivait
uniquement dans le code, et le code la disait de deux façons différentes.

  - `ajouter_type_catalogue` cherchait le libellé SANS filtrer sur `actif` ;
  - `detecter_types_activite_couple` (la détection IA) cherchait AVEC `actif.is_(True)`.

Conséquence : un type que l'admin avait DÉSACTIVÉ devenait invisible pour la détection, qui en
recréait un SECOND portant exactement le même libellé. Le catalogue se retrouvait avec deux
lignes homonymes, sans que rien ne tombe — et l'écran des types en affichait deux identiques,
l'une utilisable, l'autre non.

Le choix retenu : recherche par libellé SEUL. Un type désactivé reste désactivé — on ne le
ressuscite pas dans le dos de l'admin — mais on ne crée JAMAIS son sosie.

Ce fichier teste le COMPORTEMENT (l'IA est remplacée par un espion qui rend le libellé voulu),
pas le texte du source : c'est la panne qu'on veut tenir, pas une tournure de code.

Lancer : docker exec a-school-backend-1 python -m pytest tests/test_catalogue_types_sans_doublon.py -q
"""
import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from sqlalchemy import func

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.core.models_db import ActiviteType, Niveau, ReferentielActiviteType
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient

NIVEAU = "5e"
LIBELLE = "Exercice de repérage"


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _decor(actif: bool) -> tuple[int, int]:
    """Le couple (cycle, niveau) avec son référentiel, et LE type au libellé visé, actif ou non.
    Renvoie (cycle_id, id du type)."""
    from _profil import referentiel_id
    with dbmod.SessionLocal() as db:
        ref_id = referentiel_id(db, NIVEAU)
        niv = db.query(Niveau).filter(Niveau.nom == NIVEAU).one()
        # Table rase sur ce libellé : chaque test part du même point.
        for t in db.query(ActiviteType).filter(func.lower(ActiviteType.label) == LIBELLE.lower()).all():
            db.query(ReferentielActiviteType).filter(
                ReferentielActiviteType.activite_type_id == t.id).delete()
            db.delete(t)
        db.flush()
        t = ActiviteType(label=LIBELLE, ordre=42, actif=actif, origine="admin")
        db.add(t)
        db.flush()
        # Aucune liaison pour ce couple : la détection doit vouloir en créer une.
        db.query(ReferentielActiviteType).filter(
            ReferentielActiviteType.referentiel_id == ref_id,
            ReferentielActiviteType.activite_type_id == t.id).delete()
        db.commit()
        return niv.cycle_id, t.id


def _detecter(monkeypatch, cycle_id):
    """Lance la détection en remplaçant l'IA par un espion qui rend NOTRE libellé."""
    import backend.rag.analyse_amont as amont
    monkeypatch.setattr(amont, "detecter_types_activite", lambda texte, db: [LIBELLE])
    return _admin().post("/api/admin/referentiels/types-activite/detecter",
                         json={"cycle_id": cycle_id, "niveau": NIVEAU})


def _lignes_du_libelle():
    with dbmod.SessionLocal() as db:
        return db.query(ActiviteType).filter(
            func.lower(ActiviteType.label) == LIBELLE.lower()).all()


def test_un_type_actif_est_reutilise_jamais_recree(monkeypatch):
    """Le cas nominal, pour que le test suivant veuille dire quelque chose."""
    cycle_id, tid = _decor(actif=True)
    r = _detecter(monkeypatch, cycle_id)
    assert r.status_code == 200, r.text
    lignes = _lignes_du_libelle()
    assert len(lignes) == 1 and lignes[0].id == tid
    assert [t["id"] for t in r.json()["coches_ia"]] == [tid]


def test_un_type_desactive_ne_produit_pas_un_sosie(monkeypatch):
    """LA régression à empêcher : c'est ici qu'une SECONDE ligne du même libellé apparaissait."""
    cycle_id, tid = _decor(actif=False)
    r = _detecter(monkeypatch, cycle_id)
    assert r.status_code == 200, r.text
    lignes = _lignes_du_libelle()
    assert len(lignes) == 1, (
        f"Le catalogue contient maintenant {len(lignes)} lignes « {LIBELLE} » : la détection a "
        f"recréé le type parce qu'elle ne voyait pas celui que l'admin avait désactivé. "
        f"Aucun unique en base ne l'empêche — la règle ne tient que par le code."
    )
    assert lignes[0].id == tid


def test_un_type_desactive_reste_desactive(monkeypatch):
    """L'autre moitié du choix : ne pas doublonner ne veut pas dire réactiver sans le dire."""
    cycle_id, tid = _decor(actif=False)
    _detecter(monkeypatch, cycle_id)
    with dbmod.SessionLocal() as db:
        assert db.get(ActiviteType, tid).actif is False, (
            "Le type désactivé a été ressuscité : la décision de l'admin doit tenir."
        )
        assert db.query(ReferentielActiviteType).filter(
            ReferentielActiviteType.activite_type_id == tid).count() == 0, (
            "Une liaison a été créée vers un type désactivé : le prof ne le verra jamais "
            "(types_du_couple filtre sur `actif`), mais l'écran admin le comptera."
        )


def test_aucun_libelle_en_double_dans_le_catalogue():
    """Le fait, mesuré : deux lignes de même libellé (à la casse près) = la panne, quelle qu'en
    soit la cause. Ce test-là survivrait à une réécriture complète des deux routes."""
    with dbmod.SessionLocal() as db:
        doublons = (db.query(func.lower(ActiviteType.label), func.count())
                      .group_by(func.lower(ActiviteType.label))
                      .having(func.count() > 1).all())
    assert not doublons, (
        "Le catalogue contient des libellés en double : "
        + ", ".join(f"« {lib} » ×{n}" for lib, n in doublons)
    )
