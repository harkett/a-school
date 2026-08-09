r"""Les types d'activité appartiennent au référentiel : jamais deux fois le même libellé DANS un
référentiel, et aucune contagion d'un référentiel à l'autre.

CE QUE CE FICHIER PROUVE, et pourquoi il a changé de sujet le 05/08/2026. Il gardait auparavant
un CATALOGUE GLOBAL de types (partagé crèche -> doctorat) contre les doublons de libellé : la
détection ne voyait pas les types désactivés et en recréait des sosies. Ce catalogue n'existe
plus. Un type d'activité est une donnée LUE DANS LE DOCUMENT, comme une matière, et il vit sur
le référentiel qui le nomme (migration e4a7c2b9d5f8).

La règle à tenir a donc changé d'échelle, et c'est elle qui compte maintenant :

  1. dans UN référentiel, un libellé n'apparaît qu'une fois (l'anti-doublon de `matieres.nom`,
     transposé — et désormais tenu par un UNIQUE en base, plus seulement par le code) ;
  2. deux référentiels peuvent porter le MÊME libellé sans rien partager : c'est tout le sujet du
     chantier. Lire « Projet » dans un BTS ne doit rien écrire chez la crèche ;
  3. la détection PROPOSE (`validee=false`) et ne retient jamais d'office : une lecture d'IA
     n'entre pas dans les menus d'un professeur toute seule ;
  4. relancer la détection ne DÉ-retient pas ce que l'admin avait retenu.

L'IA est remplacée par un espion qui rend le libellé voulu : c'est le COMPORTEMENT qu'on tient,
pas une tournure de code.

Lancer : docker compose exec backend python -m pytest tests/test_catalogue_types_sans_doublon.py -q
"""
from sqlalchemy import func

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.core.models_db import ActiviteType, Cycle, Niveau
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient

NIVEAU = "5e"
AUTRE_NIVEAU = "TAD-Creche"
LIBELLE = "Exercice de repérage"


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _decor(niveau=NIVEAU) -> tuple[int, int]:
    """Le couple (cycle, niveau) avec son référentiel, table rase sur nos libellés. Le prompt de
    types du cycle est POSÉ EN BASE : sans lui, la détection le ferait écrire par l'IA (appel réel).
    Renvoie (cycle_id, referentiel_id)."""
    from _profil import referentiel_id
    with dbmod.SessionLocal() as db:
        ref_id = referentiel_id(db, niveau)
        niv = db.query(Niveau).filter(Niveau.nom == niveau).one()
        db.query(ActiviteType).filter(
            ActiviteType.referentiel_id == ref_id,
            func.lower(ActiviteType.label) == LIBELLE.lower()).delete(synchronize_session=False)
        cyc = db.get(Cycle, niv.cycle_id)
        cyc.prompt_types = "Lis {texte} et donne les types."
        db.commit()
        return niv.cycle_id, ref_id


def _detecter(monkeypatch, cycle_id, niveau=NIVEAU, libelles=(LIBELLE,)):
    """Lance la détection en remplaçant l'IA par un espion qui rend NOS libellés."""
    import backend.rag.analyse_amont as amont
    monkeypatch.setattr(amont, "detecter_types_activite",
                        lambda texte, db=None, prompt_referentiel=None: list(libelles))
    return _admin().post("/api/admin/referentiels/types-activite/detecter",
                         json={"cycle_id": cycle_id, "niveau": niveau})


def _lignes(ref_id):
    with dbmod.SessionLocal() as db:
        return (db.query(ActiviteType)
                  .filter(ActiviteType.referentiel_id == ref_id,
                          func.lower(ActiviteType.label) == LIBELLE.lower()).all())


def test_la_detection_propose_sans_retenir(monkeypatch):
    """Le cœur de la décision : l'IA propose, l'admin retient. Un type détecté arrive NON retenu."""
    cycle_id, ref_id = _decor()
    r = _detecter(monkeypatch, cycle_id)
    assert r.status_code == 200, r.text
    lignes = _lignes(ref_id)
    assert len(lignes) == 1
    assert lignes[0].validee is False, (
        "Le type détecté est arrivé RETENU : une lecture d'IA entrerait directement dans les "
        "menus des professeurs, sans que l'admin ait rien décidé."
    )
    assert lignes[0].origine == "ia"
    assert [t["id"] for t in r.json()["proposes"]] == [lignes[0].id]


def test_relancer_la_detection_ne_cree_pas_de_doublon(monkeypatch):
    """Deux passages, une seule ligne : l'anti-doublon par libellé DANS le référentiel."""
    cycle_id, ref_id = _decor()
    _detecter(monkeypatch, cycle_id)
    r = _detecter(monkeypatch, cycle_id)
    assert r.status_code == 200, r.text
    assert len(_lignes(ref_id)) == 1
    assert [t["label"] for t in r.json()["deja_presents"]] == [LIBELLE]


def test_relancer_la_detection_ne_deretient_pas(monkeypatch):
    """La décision de l'admin tient : un type qu'il a retenu reste retenu après une relecture."""
    cycle_id, ref_id = _decor()
    _detecter(monkeypatch, cycle_id)
    tid = _lignes(ref_id)[0].id
    r = _admin().put("/api/admin/referentiels/types-activite",
                     json={"cycle_id": cycle_id, "niveau": NIVEAU, "type_id": tid, "validee": True})
    assert r.status_code == 200, r.text

    _detecter(monkeypatch, cycle_id)
    with dbmod.SessionLocal() as db:
        assert db.get(ActiviteType, tid).validee is True, (
            "Une nouvelle détection a dé-retenu un type que l'admin avait mis au programme."
        )


def test_deux_referentiels_ne_se_contaminent_pas(monkeypatch):
    """LE point du chantier. Le même libellé lu dans deux documents donne DEUX lignes distinctes,
    chacune chez elle : rien n'est partagé, et retenir l'une ne retient pas l'autre."""
    cycle_a, ref_a = _decor(NIVEAU)
    cycle_b, ref_b = _decor(AUTRE_NIVEAU)
    _detecter(monkeypatch, cycle_a, NIVEAU)
    _detecter(monkeypatch, cycle_b, AUTRE_NIVEAU)

    a, b = _lignes(ref_a), _lignes(ref_b)
    assert len(a) == 1 and len(b) == 1
    assert a[0].id != b[0].id, (
        "Les deux référentiels partagent la MÊME ligne de type : le catalogue global est de "
        "retour, et le vocabulaire d'un diplôme déborde sur l'autre."
    )

    r = _admin().put("/api/admin/referentiels/types-activite",
                     json={"cycle_id": cycle_a, "niveau": NIVEAU, "type_id": a[0].id,
                           "validee": True})
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        assert db.get(ActiviteType, b[0].id).validee is False, (
            "Retenir un type dans un référentiel l'a retenu dans l'autre."
        )


def test_aucun_libelle_en_double_dans_un_referentiel():
    """Le fait, mesuré sur toute la base : deux lignes de même libellé DANS un référentiel = la
    panne, quelle qu'en soit la cause. Ce test survivrait à une réécriture complète des routes."""
    with dbmod.SessionLocal() as db:
        doublons = (db.query(ActiviteType.referentiel_id, func.lower(ActiviteType.label),
                             func.count())
                      .group_by(ActiviteType.referentiel_id, func.lower(ActiviteType.label))
                      .having(func.count() > 1).all())
    assert not doublons, (
        "Des libellés en double dans un même référentiel : "
        + ", ".join(f"référentiel {r} : « {lib} » ×{n}" for r, lib, n in doublons)
    )
