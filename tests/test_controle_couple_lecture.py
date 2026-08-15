"""Preuve — le contrôle du couple lit le document ENTIER, UNE fois, et le dit quand il échoue.

Le 14/08/2026, le dépôt du programme du cycle 4 (139 pages) a rendu « Contrôle du document
impossible (réseau) » alors que rien n'était en panne : le contrôle lisait d'abord six pages,
n'y trouvait pas « 4e » — un programme de cycle ne nomme ses années qu'en cours de route — puis
relisait tout, et l'écran abandonnait à 45 secondes en accusant le réseau.

Ce que ces tests PROUVENT :
  1. le document est lu UNE seule fois, et en ENTIER (plus de première passe à six pages) ;
  2. un niveau nommé loin dans le document est trouvé ;
  3. un niveau absent est refusé en DISANT quels mots manquent.

Ni IA, ni réseau : le texte du PDF est mocké, la recherche est locale.

Lancer : docker compose exec backend python -m pytest tests/test_controle_couple_lecture.py -q
"""
import uuid
from unittest.mock import patch

import backend.core.database as dbmod
import backend.pedagogie.referentiels_admin as refadm
from backend.main import app
from fastapi.testclient import TestClient


def admin_client():
    from backend.systeme.admin import _make_admin_token
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _couple(cycle_nom="CC-Collège", niveau_nom="CC-4e"):
    from backend.core.models_db import Cycle, Niveau
    with dbmod.SessionLocal() as db:
        c = Cycle(nom=cycle_nom, ordre=80)
        db.add(c); db.commit(); db.refresh(c)
        n = Niveau(cycle_id=c.id, nom=niveau_nom, ordre=80)
        db.add(n); db.commit(); db.refresh(n)
        return c.id, n.id


def _token():
    t = uuid.uuid4().hex
    (refadm.STAGING_DIR / f"{t}.pdf").write_bytes(b"%PDF-fake")
    return t


def _controler(texte_du_pdf, cycle_nom="CC-Collège", niveau_nom="CC-4e"):
    """Appelle le contrôle avec un PDF dont le texte est imposé. Rend (réponse, appels de lecture)."""
    cid, nid = _couple(cycle_nom, niveau_nom)
    token = _token()
    appels = []

    def _faux_texte(tok, max_pages=6):
        appels.append(max_pages)
        return texte_du_pdf

    try:
        with patch.object(refadm, "_texte_staged", _faux_texte):
            r = admin_client().post("/api/admin/referentiels/controle-couple",
                                    json={"token": token, "cycle_id": cid, "niveau_id": nid})
        assert r.status_code == 200, r.text
        return r.json(), appels
    finally:
        (refadm.STAGING_DIR / f"{token}.pdf").unlink(missing_ok=True)


# Le niveau ne paraît qu'APRÈS un long début : le cas qui faisait lire le document deux fois.
DEBUT_SANS_NIVEAU = "Programme du cycle 4\n" + ("Volet 1 : les spécificités du cycle.\n" * 200)


def test_le_document_est_lu_une_seule_fois_et_en_entier():
    d, appels = _controler(DEBUT_SANS_NIVEAU + "Thème 1 : la classe de CC-4e découvre…")
    assert appels == [None], appels          # None = toutes les pages ; une seule lecture
    assert d["trouve"] is True


def test_niveau_absent_refuse_en_disant_ce_qui_manque():
    d, appels = _controler(DEBUT_SANS_NIVEAU + "Thème 1 : la classe de CC-3e découvre…")
    assert appels == [None], appels
    assert d["trouve"] is False
    assert d["manquants"] == ["cc", "4e"] or "4e" in d["manquants"], d["manquants"]


def test_le_cycle_seul_ne_suffit_pas():
    """« CC-Collège » est dans le document, « CC-4e » non : le cycle ne vaut pas autorisation."""
    d, _ = _controler("Programme du cycle CC-Collège, toutes années confondues.")
    assert d["cycle_trouve"] is True
    assert d["trouve"] is False
