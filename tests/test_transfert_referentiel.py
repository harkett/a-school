r"""Preuve du TRANSFERT D'UN RÉFÉRENTIEL — d'une installation à l'autre, sans le refaire.

CE QUE ÇA RÉSOUT. Les référentiels se construisent sur le poste de développement : la procédure
est longue, elle se reprend en plusieurs fois, et on ne la refait pas en production. Or un
déploiement porte le CODE et la STRUCTURE de la base — jamais son contenu. Constaté le
16/08/2026 : le référentiel Collège (5e, 4e, 3e) absent du serveur après un déploiement pourtant
complet, le code et les colonnes bien arrivés, la ligne non.

CE QUE CES TESTS PROTÈGENT :
  1. l'aller-retour ne perd rien — niveaux, matières, types, précisions, unités ET vecteurs ;
  2. les identifiants sont réattribués : le n° 21 d'ici peut être pris là-bas ;
  3. les précisions suivent le NOUVEAU type, jamais l'ancien — sinon elles pointeraient sur un
     type d'un autre référentiel, ou sur rien ;
  4. un import qui écraserait un référentiel déjà présent est REFUSÉ, en français, avant d'écrire ;
  5. un refus ne laisse rien derrière lui — pas de référentiel à moitié posé, l'état le plus cher
     à diagnostiquer parce que l'application répond quand même ;
  6. un fichier d'un autre format est refusé plutôt qu'importé de travers.

Lancer : docker compose exec backend python -m pytest tests/test_transfert_referentiel.py -q
"""
import json

import backend.core.database as dbmod
from backend.core.models_db import (Cycle, Matiere, Niveau, Referentiel, ReferentielChunk,
                                    ActiviteType, ReferentielTypePrecision)
from backend.main import app
from backend.pedagogie.transfert_referentiel import FORMAT, exporter, importer
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient
from sqlalchemy import text


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _table_rase():
    db = dbmod.SessionLocal()
    try:
        db.execute(text("DELETE FROM referentiel_type_precisions"))
        db.execute(text("DELETE FROM referentiel_chunks"))
        db.execute(text("DELETE FROM referentiel_niveaux"))
        db.execute(text("DELETE FROM types_activite WHERE referentiel_id IS NOT NULL"))
        db.execute(text("DELETE FROM matieres WHERE referentiel_id IS NOT NULL"))
        db.execute(text("DELETE FROM referentiels"))
        db.commit()
    finally:
        db.close()


def _semer(nom_fixe="test_transfert") -> tuple[int, list[int]]:
    """Un référentiel complet et minuscule : deux niveaux, une matière, un type, une précision,
    deux unités dont une vectorisée."""
    db = dbmod.SessionLocal()
    try:
        cycle = db.query(Cycle).first()
        if cycle is None:
            cycle = Cycle(nom="Cycle d'essai", ordre=99)
            db.add(cycle)
            db.commit()
        niveaux = db.query(Niveau).filter(Niveau.cycle_id == cycle.id).limit(2).all()
        if len(niveaux) < 2:
            for i in range(2 - len(niveaux)):
                db.add(Niveau(cycle_id=cycle.id, nom=f"Niveau essai {i}", ordre=90 + i))
            db.commit()
            niveaux = db.query(Niveau).filter(Niveau.cycle_id == cycle.id).limit(2).all()

        r = Referentiel(niveau_id=niveaux[0].id, nom_fixe=nom_fixe, collection=nom_fixe,
                        source="essai", decoupe_valide=True)
        db.add(r)
        db.commit()
        # Le rattachement au niveau PORTEUR est posé tout seul, par un écouteur du modèle
        # (`models_db.py` : « tout référentiel dessert d'emblée son niveau porteur »). On n'ajoute
        # donc que le second — le refaire ici tomberait sur la contrainte d'unicité.
        db.execute(text("INSERT INTO referentiel_niveaux (referentiel_id, niveau_id) "
                        "VALUES (:r, :n)"), {"r": r.id, "n": niveaux[1].id})
        db.add(Matiere(nom="Matière d'essai", ordre=1, actif=True, referentiel_id=r.id))
        t = ActiviteType(label="Type d'essai", actif=True, ordre=1, referentiel_id=r.id)
        db.add(t)
        db.commit()
        db.add(ReferentielTypePrecision(libelle="Précision d'essai", ordre=1, source="essai",
                                        type_activite_id=t.id))
        # `option_ab` ne se devine pas : la colonne refuse le vide (les référentiels BTS CIEL
        # portent deux options dans un même document). « commun » est ce qu'écrit la découpe.
        db.add(ReferentielChunk(referentiel_id=r.id, chunk_index=0, texte="Unité une",
                                option_ab="commun", page=1,
                                embedding=[0.1] * 1024, embedding_model="essai"))
        # Le vecteur est OBLIGATOIRE en base : une unité sans vecteur ne serait jamais retrouvée
        # par la recherche. Les deux en portent donc un.
        db.add(ReferentielChunk(referentiel_id=r.id, chunk_index=1, texte="Unité deux",
                                option_ab="commun", page=2,
                                embedding=[0.2] * 1024, embedding_model="essai"))
        db.commit()
        return r.id, [n.id for n in niveaux]
    finally:
        db.close()


def _compter(db, referentiel_id: int) -> dict:
    def n(sql, **p):
        return db.execute(text(sql), {"r": referentiel_id, **p}).scalar()
    return {
        "niveaux": n("SELECT count(*) FROM referentiel_niveaux WHERE referentiel_id = :r"),
        "matieres": n("SELECT count(*) FROM matieres WHERE referentiel_id = :r"),
        "types": n("SELECT count(*) FROM types_activite WHERE referentiel_id = :r"),
        "precisions": n("SELECT count(*) FROM referentiel_type_precisions WHERE type_activite_id "
                        "IN (SELECT id FROM types_activite WHERE referentiel_id = :r)"),
        "chunks": n("SELECT count(*) FROM referentiel_chunks WHERE referentiel_id = :r"),
        "vecteurs": n("SELECT count(*) FROM referentiel_chunks WHERE referentiel_id = :r "
                      "AND embedding IS NOT NULL"),
    }


def test_l_aller_retour_ne_perd_rien():
    """LE POINT QUI COMPTE. Ce qui part doit arriver entier — et surtout les vecteurs : ce sont
    eux qui rendent l'opération gratuite, puisque rien n'est recalculé."""
    _table_rase()
    ancien, _ = _semer()
    db = dbmod.SessionLocal()
    try:
        contenu = exporter(db, ancien)
        avant = _compter(db, ancien)
        # On retire l'original : sans ça, les contraintes d'unicité refusent l'import — et c'est
        # exactement ce qu'un autre test vérifie.
        db.execute(text("DELETE FROM referentiels WHERE id = :r"), {"r": ancien})
        db.commit()

        resultat = importer(db, contenu)
        db.commit()
        apres = _compter(db, resultat["referentiel_id"])
    finally:
        db.close()

    assert apres == avant, f"perte au transfert : {avant} → {apres}"
    assert avant["vecteurs"] == 2, "sans vecteur transporté, ce test ne prouverait rien"


def test_les_identifiants_sont_reattribues():
    """Le n° d'ici n'est pas forcément libre là-bas. Le référentiel repart avec un numéro neuf."""
    _table_rase()
    ancien, _ = _semer()
    db = dbmod.SessionLocal()
    try:
        contenu = exporter(db, ancien)
        db.execute(text("DELETE FROM referentiels WHERE id = :r"), {"r": ancien})
        db.commit()
        resultat = importer(db, contenu)
        db.commit()
        neuf = resultat["referentiel_id"]
        # Les lignes filles pointent le NOUVEAU référentiel, pas l'ancien numéro.
        orphelines = db.execute(
            text("SELECT count(*) FROM referentiel_chunks WHERE referentiel_id = :a"),
            {"a": ancien}).scalar()
    finally:
        db.close()
    assert orphelines == 0, "des lignes montrent encore l'ancien identifiant"
    assert neuf > 0


def test_les_precisions_suivent_le_nouveau_type():
    """Une précision rattachée à l'ANCIEN identifiant de type désignerait le type d'un autre
    référentiel — ou rien. C'est le lien le plus facile à casser, et le plus discret."""
    _table_rase()
    ancien, _ = _semer()
    db = dbmod.SessionLocal()
    try:
        contenu = exporter(db, ancien)
        db.execute(text("DELETE FROM referentiels WHERE id = :r"), {"r": ancien})
        db.commit()
        resultat = importer(db, contenu)
        db.commit()
        lien = db.execute(text(
            """SELECT p.type_activite_id = t.id FROM referentiel_type_precisions p
               JOIN types_activite t ON t.id = p.type_activite_id
               WHERE t.referentiel_id = :r"""), {"r": resultat["referentiel_id"]}).scalar()
    finally:
        db.close()
    assert lien is True, "la précision ne pointe pas sur un type de CE référentiel"


def test_un_referentiel_deja_present_est_refuse_sans_rien_ecrire():
    """Le refus doit tomber AVANT la première écriture, et parler français : la contrainte de la
    base rendrait un message que personne ne peut lire."""
    _table_rase()
    ancien, _ = _semer()
    db = dbmod.SessionLocal()
    try:
        contenu = exporter(db, ancien)
        avant = db.query(Referentiel).count()
        erreur = None
        try:
            importer(db, contenu)
        except ValueError as e:
            erreur = str(e)
        db.rollback()
        apres = db.query(Referentiel).count()
    finally:
        db.close()

    assert erreur is not None, "importer par-dessus un référentiel existant devait être refusé"
    assert "existe déjà" in erreur or "dessert déjà" in erreur
    assert apres == avant, "un refus ne doit rien laisser derrière lui"


def test_un_fichier_d_un_autre_format_est_refuse():
    """Un fichier d'une version différente n'a pas les mêmes tables : l'importer de travers
    poserait un référentiel incomplet, qui répond quand même."""
    db = dbmod.SessionLocal()
    try:
        erreur = None
        try:
            importer(db, {"format": FORMAT + 99, "referentiel": {}, "tables": {}})
        except ValueError as e:
            erreur = str(e)
        db.rollback()
    finally:
        db.close()
    assert erreur is not None and "format" in erreur.lower()


def test_les_deux_routes_repondent_et_le_fichier_se_relit():
    """L'écran passe par là : l'export doit rendre un fichier téléchargeable, et ce fichier doit
    être exactement ce que l'import sait relire."""
    _table_rase()
    ancien, _ = _semer()
    c = _admin()

    r = c.get(f"/api/admin/referentiels/exporter?id={ancien}")
    assert r.status_code == 200, r.text[:200]
    assert "attachment" in r.headers.get("content-disposition", "")
    contenu = json.loads(r.content.decode("utf-8"))
    assert contenu["format"] == FORMAT
    assert len(contenu["tables"]["referentiel_chunks"]) == 2

    # Le référentiel existe encore : l'import doit être refusé proprement, pas exploser.
    fichier = {"fichier": ("essai.json", r.content, "application/json")}
    rr = c.post("/api/admin/referentiels/importer", files=fichier)
    assert rr.status_code == 400
    assert "déjà" in rr.json()["detail"]

    assert c.get("/api/admin/referentiels/exporter?id=999999").status_code == 404


def test_sans_cookie_admin_les_deux_routes_refusent():
    """Un référentiel est le fruit d'un travail long : il ne s'exporte pas sans être administrateur,
    et surtout il ne s'importe pas."""
    c = TestClient(app)
    assert c.get("/api/admin/referentiels/exporter?id=1").status_code == 401
    assert c.post("/api/admin/referentiels/importer",
                  files={"fichier": ("x.json", b"{}", "application/json")}).status_code == 401


def test_chaque_refus_dit_ce_qu_il_a_vu():
    """« Import impossible » est le pire message : il oblige a deviner, puis a lire un journal de
    serveur. Constaté le 16/08/2026 — le fichier était trop lourd pour le serveur web, et rien ne
    le disait. Chaque refus nomme donc le fichier ET la raison."""
    c = _admin()

    def _refus(contenu, nom="essai.json"):
        r = c.post("/api/admin/referentiels/importer",
                   files={"fichier": (nom, contenu, "application/json")})
        assert r.status_code == 400, r.text[:200]
        return r.json()["detail"]

    assert "vide" in _refus(b"")
    illisible = _refus(b"\xff\xfe\x00 pas du texte", nom="photo.png")
    assert "photo.png" in illisible and "json" in illisible.lower()
    casse = _refus(b'{"format": 1, "referentiel": {', nom="tronque.json")
    assert "tronque.json" in casse and "ligne" in casse
    autre = _refus(b'{"ceci": "est un json valide"}', nom="autre.json")
    assert "autre.json" in autre and "aucun référentiel" in autre
