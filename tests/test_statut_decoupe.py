"""L'état de la découpe d'un couple — GET /admin/referentiels/decoupe/statut.

CE FICHIER A CHANGÉ DE SUJET LE 09/08/2026, et c'est le fond de l'affaire.

Il verrouillait jusque-là un ORDRE DE CONDITIONS. La route mentait pendant une reprise : elle
testait `decoupe_valide` avant le travail en cours, et ce drapeau — posé à la première
ingestion — gagnait contre la réalité. Mesuré le 02/08/2026 sur le BTS CIEL : pendant onze
minutes de vectorisation, l'écran affichait `done` avec les 46 unités de la fois d'avant alors
que l'avancement réel était à 0/44. La vérité était dans `_INGESTIONS`, un dictionnaire
d'orchestration tenu en mémoire.

CE DICTIONNAIRE N'EXISTE PLUS. Le 08/08/2026, « Valider le découpage » a cessé de lancer quoi
que ce soit : il ne fait plus qu'un put sur `decoupe_valide`. Plus rien ne tourne en tâche de
fond, donc plus rien à départager — la route lit la base, et la base ne ment pas. Les six tests
qui posaient un faux job échouaient depuis, sur un `_INGESTIONS_LOCK` disparu : ils gardaient un
mécanisme mort.

CE QUI EST VÉRIFIÉ MAINTENANT — le contrat réel, trois états et rien de plus :
`absent` (aucun référentiel), `idle` (référentiel non validé), `done` (référentiel validé),
`chunks` compté en base pour CE référentiel, et `progress`/`message` toujours nuls. Ce dernier
point n'est pas décoratif : c'est lui qui dirait qu'une orchestration est revenue par la fenêtre.

Lancer : docker compose exec backend python -m pytest tests/test_statut_decoupe.py -q
"""
from datetime import date

import backend.core.database as dbmod
from backend.core.models_db import (Cycle, Niveau, Referentiel, ReferentielChunk,
                                    ReferentielDocument)
from backend.main import app
from fastapi.testclient import TestClient

CYCLE, NIVEAU, COLLECTION = "SD-Cycle", "SD-Niveau", "sd_couple"


def admin_client():
    from backend.systeme.admin import _make_admin_token
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _couple(decoupe_valide: bool, chunks: int = 0, suffixe: str = "") -> int:
    """Un couple complet en base. Renvoie le cycle_id (la route interroge par cycle + nom).

    `suffixe` sert quand un même test crée plusieurs couples : `cycles.nom` ET
    `referentiels.nom_fixe` sont UNIQUES, deux homonymes dans le même test lèvent une violation
    de contrainte. Entre deux tests la question ne se pose pas — le conftest TRUNCATE."""
    with dbmod.SessionLocal() as db:
        cyc = Cycle(nom=CYCLE + suffixe, ordre=97); db.add(cyc); db.flush()
        niv = Niveau(cycle_id=cyc.id, nom=NIVEAU, ordre=97); db.add(niv); db.flush()
        ref = Referentiel(niveau_id=niv.id, nom_fixe=COLLECTION + suffixe,
                          collection=COLLECTION + suffixe,
                          decoupe_valide=decoupe_valide)
        db.add(ref); db.flush()
        doc = ReferentielDocument(referentiel_id=ref.id, fichier="doc.pdf")
        db.add(doc); db.flush()
        for i in range(chunks):
            db.add(ReferentielChunk(referentiel_id=ref.id, document_id=doc.id, portee="matiere",
                                    valide_du=date.today(), chunk_index=i, option_ab="", page=1,
                                    texte=f"unite {i}", embedding=[0.5] * 1024,
                                    embedding_model="BAAI/bge-m3"))
        db.commit()
        return cyc.id


def _statut(cycle_id: int) -> dict:
    r = admin_client().get("/api/admin/referentiels/decoupe/statut",
                           params={"cycle_id": cycle_id, "niveau": NIVEAU})
    assert r.status_code == 200
    return r.json()


# ── LES TROIS ÉTATS ─────────────────────────────────────────────────────────────────────

def test_couple_absent():
    """Aucun référentiel pour ce couple : `absent`, et surtout aucune erreur 500."""
    with dbmod.SessionLocal() as db:
        cyc = Cycle(nom="SD-Vide", ordre=98); db.add(cyc); db.flush()
        db.add(Niveau(cycle_id=cyc.id, nom=NIVEAU, ordre=98))
        db.commit()
        cid = cyc.id
    s = _statut(cid)
    assert s["status"] == "absent" and s["chunks"] == 0


def test_idle_referentiel_pas_encore_valide():
    """Un référentiel existe, le découpage n'est pas validé : `idle`."""
    cid = _couple(decoupe_valide=False)
    s = _statut(cid)
    assert s["status"] == "idle" and s["chunks"] == 0 and s["decoupe_valide"] is False


def test_done_referentiel_valide():
    """Découpage validé : `done`, et le nombre d'unités réellement en base."""
    cid = _couple(decoupe_valide=True, chunks=44)
    s = _statut(cid)
    assert s["status"] == "done" and s["chunks"] == 44 and s["decoupe_valide"] is True


def test_les_unites_sont_comptees_sans_le_drapeau():
    """Des unités écrites mais pas encore validées : `idle` MALGRÉ les 46 unités.

    C'est l'état exact de l'ancien bug, vu de l'autre côté : le compte et le verdict sont deux
    choses. Ici le compte dit 46 et le verdict dit « pas validé » — les deux sont vrais."""
    cid = _couple(decoupe_valide=False, chunks=46)
    s = _statut(cid)
    assert s["status"] == "idle" and s["chunks"] == 46


# ── PLUS AUCUNE ORCHESTRATION ───────────────────────────────────────────────────────────

def test_ni_progression_ni_message_quel_que_soit_l_etat():
    """La route ne rend plus jamais d'avancement ni de message : il n'y a plus de tâche de fond.

    Si ces deux champs se remettaient à vivre, c'est qu'une orchestration serait revenue — et
    avec elle le risque d'un verdict qui contredit la base."""
    for i, (valide, chunks) in enumerate(((False, 0), (True, 44), (False, 46))):
        s = _statut(_couple(decoupe_valide=valide, chunks=chunks, suffixe=f"-{i}"))
        assert s["progress"] is None and s["message"] is None
