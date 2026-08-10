r"""Preuve de raccordement — les précisions d'un type, son prompt, et le retrait d'une matière.

CE QUI N'ÉTAIT PAS TENU. Quatre routes d'écriture de `referentiels_admin.py` n'avaient aucun test
le 10/08/2026 : créer une précision, la supprimer, écrire le prompt de génération d'un type, et
retirer une matière du programme. Les trois premières touchent au contenu qui sert à générer ;
la quatrième décide de ce qu'un prof voit dans sa liste de matières.

CE QUE LE TEST PROUVE, en chaîne réelle :
  1. la précision est CRÉÉE en base, puis SUPPRIMÉE pour de bon (un vrai DELETE) ;
  2. le prompt d'un type s'écrit et se relit ; un prompt vide est refusé (422), et un prompt
     SANS le repère `{texte}` aussi (400) — c'est le garde-fou qui empêche qu'une génération
     ignore en silence ce que le prof a écrit ;
  3. LA GARDE DE PORTÉE : un `type_id` qui appartient à un AUTRE référentiel rend 404 — sans
     elle, l'écran d'un diplôme donnerait accès aux précisions d'un autre ;
  4. « Retirer » une matière RETENUE la désactive (`actif=False`, historique gardé) tandis que
     « Supprimer » une PROPOSITION l'efface vraiment : c'est la distinction que les deux libellés
     de l'écran annoncent, et elle est ici vérifiée des deux côtés ;
  5. sans cookie admin : 401 sur les quatre.

Lancer : docker compose exec backend python -m pytest tests/test_referentiel_types_et_precisions.py -q
"""
import backend.core.database as dbmod
from backend.core.models_db import (ActiviteType, Cycle, Matiere, Niveau, Referentiel,
                                    ReferentielTypePrecision)
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient

NIVEAU = "Niveau-essai"
AUTRE_NIVEAU = "Niveau-essai-2"


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _socle():
    """Un cycle, deux niveaux, leurs référentiels, un type par référentiel. Rendu :
    (cycle_id, type du niveau 1, type du niveau 2)."""
    db = dbmod.SessionLocal()
    try:
        cyc = Cycle(nom="Cycle-essai", ordre=0)
        db.add(cyc)
        db.flush()
        ids = []
        for nom in (NIVEAU, AUTRE_NIVEAU):
            niv = Niveau(cycle_id=cyc.id, nom=nom, ordre=0)
            db.add(niv)
            db.flush()
            ref = Referentiel(niveau_id=niv.id, nom_fixe=nom.lower().replace("-", "_"),
                              collection=nom, fichier="doc.pdf", texte_epure="TEXTE")
            db.add(ref)
            db.flush()
            t = ActiviteType(label=f"Type de {nom}", referentiel_id=ref.id, actif=True, ordre=1)
            db.add(t)
            db.flush()
            ids.append(t.id)
        db.commit()
        return cyc.id, ids[0], ids[1]
    finally:
        db.close()


def _precisions(type_id: int):
    db = dbmod.SessionLocal()
    try:
        return [p.libelle for p in db.query(ReferentielTypePrecision)
                .filter(ReferentielTypePrecision.type_activite_id == type_id).all()]
    finally:
        db.close()


def _id_precision(type_id: int):
    db = dbmod.SessionLocal()
    try:
        p = (db.query(ReferentielTypePrecision)
               .filter(ReferentielTypePrecision.type_activite_id == type_id).first())
        return p.id if p else None
    finally:
        db.close()


def test_precision_creee_puis_supprimee_pour_de_bon():
    cycle_id, type_id, _autre = _socle()
    c = _admin()
    corps = {"cycle_id": cycle_id, "niveau": NIVEAU, "type_id": type_id, "libelle": "En binôme"}

    r = c.post("/api/admin/referentiels/types-activite/precisions", json=corps)
    assert r.status_code == 200, r.text
    assert _precisions(type_id) == ["En binôme"]

    prec_id = _id_precision(type_id)
    r = c.request("DELETE", f"/api/admin/referentiels/types-activite/precisions/{prec_id}",
                  params={"cycle_id": cycle_id, "niveau": NIVEAU, "type_id": type_id})
    assert r.status_code == 200, r.text
    assert _precisions(type_id) == [], "« Supprimer » doit supprimer : la ligne est encore là."


def test_precision_refuse_un_libelle_vide():
    cycle_id, type_id, _autre = _socle()
    r = _admin().post("/api/admin/referentiels/types-activite/precisions",
                      json={"cycle_id": cycle_id, "niveau": NIVEAU, "type_id": type_id,
                            "libelle": "   "})
    assert r.status_code == 400
    assert _precisions(type_id) == []


def test_la_portee_tient_un_type_d_un_autre_referentiel_est_refuse():
    """Sans cette garde, l'écran d'un diplôme écrirait dans le référentiel du voisin."""
    cycle_id, _type_id, type_de_l_autre = _socle()
    r = _admin().post("/api/admin/referentiels/types-activite/precisions",
                      json={"cycle_id": cycle_id, "niveau": NIVEAU, "type_id": type_de_l_autre,
                            "libelle": "Intrus"})
    assert r.status_code == 404, r.text
    assert _precisions(type_de_l_autre) == []


def test_prompt_du_type_ecrit_et_relu():
    cycle_id, type_id, _autre = _socle()
    c = _admin()
    corps = {"cycle_id": cycle_id, "niveau": NIVEAU, "type_id": type_id,
             "prompt": "Rédige une consigne courte à partir de : {texte}"}

    assert c.put("/api/admin/referentiels/types-activite/prompt", json=corps).status_code == 200
    db = dbmod.SessionLocal()
    try:
        assert db.query(ActiviteType).filter(ActiviteType.id == type_id).first().prompt == corps["prompt"]
    finally:
        db.close()

    assert c.put("/api/admin/referentiels/types-activite/prompt",
                 json={**corps, "prompt": "  "}).status_code == 422
    # `{texte}` oublié : la génération marcherait en ignorant l'idée du prof. On refuse avant.
    assert c.put("/api/admin/referentiels/types-activite/prompt",
                 json={**corps, "prompt": "Rédige une consigne."}).status_code == 400
    r = c.put("/api/admin/referentiels/types-activite/prompt", json={**corps, "prompt": "  "})
    db = dbmod.SessionLocal()
    try:
        assert db.query(ActiviteType).filter(ActiviteType.id == type_id).first().prompt == corps["prompt"], (
            "Refusé, donc le prompt d'avant doit tenir."
        )
    finally:
        db.close()


def test_retirer_une_matiere_retenue_la_desactive_une_proposition_disparait():
    """Les deux gestes que l'écran nomme différemment — et il a raison de les nommer autrement."""
    cycle_id, _type_id, _autre = _socle()
    db = dbmod.SessionLocal()
    try:
        ref = (db.query(Referentiel).join(Niveau, Niveau.id == Referentiel.niveau_id)
                 .filter(Niveau.nom == NIVEAU).first())
        retenue = Matiere(nom="Maths", referentiel_id=ref.id, ordre=1, actif=True, validee=True)
        proposee = Matiere(nom="Idée en attente", referentiel_id=ref.id, ordre=2, actif=True,
                           validee=False)
        db.add_all([retenue, proposee])
        db.commit()
        id_retenue, id_proposee = retenue.id, proposee.id
    finally:
        db.close()
    c = _admin()

    r = c.post("/api/admin/referentiels/retirer-matiere",
               json={"cycle_id": cycle_id, "niveau": NIVEAU, "matiere_id": id_retenue})
    assert r.status_code == 200, r.text
    assert r.json().get("supprimee") is not True

    r = c.post("/api/admin/referentiels/retirer-matiere",
               json={"cycle_id": cycle_id, "niveau": NIVEAU, "matiere_id": id_proposee})
    assert r.status_code == 200, r.text
    assert r.json().get("supprimee") is True

    db = dbmod.SessionLocal()
    try:
        m = db.query(Matiere).filter(Matiere.id == id_retenue).first()
        assert m is not None and m.actif is False, (
            "Une matière AU PROGRAMME se retire sans s'effacer : des profs y sont rattachés."
        )
        assert db.query(Matiere).filter(Matiere.id == id_proposee).first() is None, (
            "Une PROPOSITION s'efface vraiment : la garder empêcherait de la reproposer."
        )
    finally:
        db.close()


def test_sans_cookie_admin_les_quatre_routes_refusent():
    c = TestClient(app)
    corps = {"cycle_id": 1, "niveau": NIVEAU, "type_id": 1, "libelle": "x", "prompt": "x",
             "matiere_id": 1}
    assert c.post("/api/admin/referentiels/types-activite/precisions", json=corps).status_code == 401
    assert c.request("DELETE", "/api/admin/referentiels/types-activite/precisions/1",
                     params={"cycle_id": 1, "niveau": NIVEAU, "type_id": 1}).status_code == 401
    assert c.put("/api/admin/referentiels/types-activite/prompt", json=corps).status_code == 401
    assert c.post("/api/admin/referentiels/retirer-matiere", json=corps).status_code == 401
