"""Bouton « Valider le référentiel » — le dépôt raconté TÂCHE PAR TÂCHE.

Ce que ces tests verrouillent :
  - le flux annonce d'abord SES tâches (l'écran ne les connaît pas d'avance, il ne les
    écrit nulle part en dur), puis en déclare une par une comme faites, puis conclut ;
  - chaque tâche annoncée est effectivement déclarée faite, dans l'ordre annoncé ;
  - le résultat final est le MÊME que celui de l'endpoint classique, et la ligne du
    référentiel est bien EN BASE à l'arrivée ;
  - un échec sort en une ligne « erreur » lisible, jamais en pleine page HTML.

BDD de test PostgreSQL dédiée (aschool_test via conftest.py), texte du PDF mocké.

Lancer : docker compose exec backend python -m pytest tests/test_valider_flux.py -q
"""
import asyncio
import json
import uuid

from unittest.mock import patch

import backend.core.database as dbmod
import backend.pedagogie.referentiels_admin as refadm


def _cycle(nom, ordre):
    from backend.core.models_db import Cycle
    with dbmod.SessionLocal() as db:
        c = Cycle(nom=nom, ordre=ordre)
        db.add(c); db.commit(); db.refresh(c)
        return c.id


def _niveau(cycle_id, nom, ordre):
    from backend.core.models_db import Niveau
    with dbmod.SessionLocal() as db:
        n = Niveau(cycle_id=cycle_id, nom=nom, ordre=ordre)
        db.add(n); db.commit(); db.refresh(n)
        return n.id


def _staged_token():
    token = uuid.uuid4().hex
    (refadm.STAGING_DIR / f"{token}.pdf").write_bytes(b"%PDF-fake")
    return token


def _lignes(body):
    """Déroule le flux et rend la liste des messages (une ligne NDJSON = un message)."""
    reponse = refadm.valider_flux(body)
    assert reponse.media_type == "application/x-ndjson"

    async def _lire():
        return [json.loads(l) async for l in reponse.body_iterator if l.strip()]

    return asyncio.run(_lire())


def test_le_flux_annonce_ses_taches_puis_les_coche_une_a_une():
    """L'écran n'a aucune liste en dur : il dresse la sienne avec la PREMIÈRE ligne du flux,
    puis coche à mesure. Donc toute tâche annoncée doit finir par être déclarée faite."""
    cid = _cycle("VF-Cycle", 90)
    nid = _niveau(cid, "VF-Niveau", 90)
    token = _staged_token()
    body = refadm.ValiderBody(token=token, cycle_id=cid, niveau_id=nid,
                              fichier_origine="ref-officiel.pdf", source="dépôt manuel")
    try:
        with patch("backend.rag.extraction.extraire_texte", return_value="TEXTE ÉPURÉ"), \
             patch("pdfplumber.open") as ouvrir:
            ouvrir.return_value.__enter__.return_value.pages = [object()]
            msgs = _lignes(body)
    finally:
        (refadm.STAGING_DIR / f"{token}.pdf").unlink(missing_ok=True)

    annoncees = [t["id"] for t in msgs[0]["taches"]]
    assert annoncees == [t["id"] for t in refadm.TACHES_VALIDATION]
    assert all(t["libelle"] for t in msgs[0]["taches"])     # chaque tâche a un libellé affichable

    faites = [m["faite"] for m in msgs if "faite" in m]
    assert faites == annoncees          # toutes, et dans l'ordre annoncé

    fin = [m["fin"] for m in msgs if "fin" in m]
    assert len(fin) == 1 and fin[0]["ok"] is True
    assert fin[0]["niveau"] == "VF-Niveau"
    assert "fin" in msgs[-1]            # « fin » est le dernier mot du flux


def test_le_flux_ecrit_vraiment_en_base():
    """La validation, c'est l'écriture : à la ligne « base », le référentiel EXISTE."""
    from backend.core.models_db import Referentiel
    cid = _cycle("VF-Cycle2", 91)
    nid = _niveau(cid, "VF-Niveau2", 91)
    token = _staged_token()
    body = refadm.ValiderBody(token=token, cycle_id=cid, niveau_id=nid,
                              fichier_origine="ref-officiel.pdf")
    try:
        with patch("backend.rag.extraction.extraire_texte", return_value="TEXTE ÉPURÉ"), \
             patch("pdfplumber.open") as ouvrir:
            ouvrir.return_value.__enter__.return_value.pages = [object()]
            msgs = _lignes(body)
    finally:
        (refadm.STAGING_DIR / f"{token}.pdf").unlink(missing_ok=True)

    assert "base" in [m.get("faite") for m in msgs]
    with dbmod.SessionLocal() as db:
        ref = db.query(Referentiel).filter(Referentiel.niveau_id == nid).first()
        assert ref is not None
        assert ref.fichier == "ref-officiel.pdf"
        assert ref.texte_epure == "TEXTE ÉPURÉ"      # le texte de travail est FIGÉ à la validation


def test_la_preuve_du_controle_du_niveau_est_figee_en_base():
    """Le contrôle n°1 (le document nomme-t-il le niveau ?) autorise le dépôt mais ne vivait
    qu'à l'écran. C'est une PREUVE : elle est figée sur la ligne du référentiel, et se relit
    telle quelle après coup."""
    from backend.core.models_db import Referentiel
    cid = _cycle("VF-Cycle4", 93)
    nid = _niveau(cid, "VF-Niveau4", 93)
    token = _staged_token()
    body = refadm.ValiderBody(token=token, cycle_id=cid, niveau_id=nid,
                              fichier_origine="ref.pdf",
                              controle_niveau={"niveau": "VF-Niveau4", "trouve": True, "manquants": []})
    try:
        with patch("backend.rag.extraction.extraire_texte", return_value="TEXTE"), \
             patch("pdfplumber.open") as ouvrir:
            ouvrir.return_value.__enter__.return_value.pages = [object()]
            _lignes(body)
    finally:
        (refadm.STAGING_DIR / f"{token}.pdf").unlink(missing_ok=True)

    with dbmod.SessionLocal() as db:
        ref = db.query(Referentiel).filter(Referentiel.niveau_id == nid).first()
        preuve = json.loads(ref.controle_niveau)
    assert preuve == {"niveau": "VF-Niveau4", "trouve": True, "manquants": []}


def test_un_echec_sort_en_une_ligne_erreur_lisible():
    """Jeton disparu et aucun référentiel pour ce couple : le flux dit pourquoi, en français,
    et n'annonce aucune tâche faite."""
    cid = _cycle("VF-Cycle3", 92)
    nid = _niveau(cid, "VF-Niveau3", 92)
    body = refadm.ValiderBody(token="jeton-inexistant", cycle_id=cid, niveau_id=nid)

    msgs = _lignes(body)

    assert "taches" in msgs[0]                       # la liste est annoncée avant tout travail
    assert not [m for m in msgs if "faite" in m]     # rien n'a été fait
    assert "erreur" in msgs[-1] and "document en attente" in msgs[-1]["erreur"]
