"""L'état d'une ingestion de découpe — GET /admin/referentiels/decoupe/statut.

CE QUE CE FICHIER EMPÊCHE. La route n'avait aucun test, et elle mentait pendant une REPRISE :
elle testait `decoupe_valide` AVANT le travail en cours. Ce drapeau reste posé depuis la
première ingestion — sur une réingestion il gagnait donc contre la réalité. Mesuré le
02/08/2026 sur le BTS CIEL : pendant onze minutes de vectorisation, l'écran affichait
`status: done` avec `chunks: 46` (les anciens, pas encore purgés) alors que l'avancement réel
était à 0/44. Un admin qui réingère croyait que c'était fini avant que ça n'ait commencé.

Ce n'était pas une donnée manquante : `_INGESTIONS` portait la vérité, et le garde de
`valider_decoupe` la lisait déjà correctement. C'était un ordre de conditions.

LES QUATRE ÉTATS SONT TESTÉS, pas seulement celui qu'on répare : le risque d'une correction
d'ordre, c'est de déplacer le mensonge ailleurs. `idle`, le premier `done`, `error` et
`absent` doivent se comporter exactement comme avant.

Lancer : docker compose exec backend python -m pytest tests/test_statut_decoupe.py -q
"""
import backend.core.database as dbmod
import backend.pedagogie.referentiels_admin as refadm
from backend.core.models_db import Cycle, Niveau, Referentiel, ReferentielChunk
from backend.main import app
from fastapi.testclient import TestClient

CYCLE, NIVEAU, COLLECTION = "SD-Cycle", "SD-Niveau", "sd_couple"


def admin_client():
    from backend.systeme.admin import _make_admin_token
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _couple(decoupe_valide: bool, chunks: int = 0) -> int:
    """Un couple complet en base. Renvoie le cycle_id (la route interroge par cycle + nom)."""
    with dbmod.SessionLocal() as db:
        cyc = Cycle(nom=CYCLE, ordre=97); db.add(cyc); db.flush()
        niv = Niveau(cycle_id=cyc.id, nom=NIVEAU, ordre=97); db.add(niv); db.flush()
        ref = Referentiel(niveau_id=niv.id, nom_fixe=COLLECTION, collection=COLLECTION,
                          decoupe_valide=decoupe_valide)
        db.add(ref); db.flush()
        for i in range(chunks):
            db.add(ReferentielChunk(referentiel_id=ref.id, chunk_index=i, option_ab="", page=1,
                                    texte=f"unite {i}", embedding=[0.5] * 1024,
                                    embedding_model="BAAI/bge-m3"))
        db.commit()
        return cyc.id


def _job(etat: dict | None) -> None:
    """Pose (ou retire) l'état d'orchestration RUNTIME du couple."""
    with refadm._INGESTIONS_LOCK:
        if etat is None:
            refadm._INGESTIONS.pop(COLLECTION, None)
        else:
            refadm._INGESTIONS[COLLECTION] = etat


def _statut(cycle_id: int) -> dict:
    r = admin_client().get("/api/admin/referentiels/decoupe/statut",
                           params={"cycle_id": cycle_id, "niveau": NIVEAU})
    assert r.status_code == 200
    return r.json()


# ── LE DÉFAUT MESURÉ ────────────────────────────────────────────────────────────────────

def test_une_reingestion_en_cours_ne_dit_plus_done(monkeypatch):
    """LE cas des onze minutes. Le couple est DÉJÀ validé (46 chunks de la fois d'avant) et une
    nouvelle ingestion tourne : la route doit dire `running`, pas `done`.

    Elle rend aussi les chiffres d'avant — 46 chunks, decoupe_valide vrai — et c'est normal :
    ils sont vrais tant que la purge n'a pas eu lieu. Ce qui était faux, c'est le VERDICT."""
    cid = _couple(decoupe_valide=True, chunks=46)
    _job({"status": "running", "chunks": None, "message": None,
          "progress": {"etape": "vectorisation", "fait": 0, "total": 44}})
    try:
        s = _statut(cid)
    finally:
        _job(None)
    assert s["status"] == "running", "le drapeau de la fois d'avant l'emporte encore"
    assert s["progress"] == {"etape": "vectorisation", "fait": 0, "total": 44}
    assert s["decoupe_valide"] is True and s["chunks"] == 46


def test_une_reingestion_qui_echoue_ne_dit_plus_done(monkeypatch):
    """Même cause, second visage : sur un couple déjà validé, une reprise en ERREUR rendait
    `done` — et son message n'arrivait jamais à l'écran. C'est le même défaut, pas un autre."""
    cid = _couple(decoupe_valide=True, chunks=46)
    _job({"status": "error", "chunks": None, "message": "Découpe par l'IA impossible : 429"})
    try:
        s = _statut(cid)
    finally:
        _job(None)
    assert s["status"] == "error"
    assert "429" in s["message"]


# ── LES TROIS AUTRES ÉTATS : ILS NE DOIVENT PAS BOUGER ──────────────────────────────────

def test_idle_inchange():
    """Rien en cours, jamais ingéré : `idle`. Le risque d'une correction d'ordre est de
    déplacer le mensonge — ces trois-là le vérifient."""
    cid = _couple(decoupe_valide=False)
    _job(None)
    s = _statut(cid)
    assert s["status"] == "idle" and s["chunks"] == 0 and s["decoupe_valide"] is False


def test_le_premier_done_inchange():
    """Ingestion aboutie, plus rien en cours : `done`. Sans job, c'est le drapeau qui répond —
    c'est lui qui distingue « déjà ingéré » de « jamais ingéré »."""
    cid = _couple(decoupe_valide=True, chunks=44)
    _job(None)
    s = _statut(cid)
    assert s["status"] == "done" and s["chunks"] == 44


def test_le_done_du_job_juste_apres_l_ingestion_inchange():
    """Juste après l'aboutissement, les deux sources disent la même chose. Lire le job d'abord
    ne change donc rien ici — vérifié plutôt que supposé."""
    cid = _couple(decoupe_valide=True, chunks=44)
    _job({"status": "done", "chunks": 44, "message": None})
    try:
        s = _statut(cid)
    finally:
        _job(None)
    assert s["status"] == "done" and s["chunks"] == 44


def test_la_premiere_ingestion_en_cours_inchangee():
    """Couple jamais ingéré, ingestion en cours : `running` — c'était déjà le cas avant, par la
    branche `elif`. La correction ne doit pas l'avoir déplacé."""
    cid = _couple(decoupe_valide=False)
    _job({"status": "running", "chunks": None, "message": None,
          "progress": {"etape": "decoupe", "fait": 0, "total": 0}})
    try:
        s = _statut(cid)
    finally:
        _job(None)
    assert s["status"] == "running" and s["chunks"] == 0


def test_une_premiere_ingestion_en_erreur_inchangee():
    """Couple jamais ingéré, ingestion échouée : `error` + message. Inchangé."""
    cid = _couple(decoupe_valide=False)
    _job({"status": "error", "chunks": None, "message": "Prompt de découpe non validé"})
    try:
        s = _statut(cid)
    finally:
        _job(None)
    assert s["status"] == "error" and "Prompt" in s["message"]


def test_couple_absent_inchange():
    """Aucun référentiel pour ce couple : `absent`, et surtout aucune erreur 500."""
    with dbmod.SessionLocal() as db:
        cyc = Cycle(nom="SD-Vide", ordre=98); db.add(cyc); db.flush()
        db.add(Niveau(cycle_id=cyc.id, nom=NIVEAU, ordre=98))
        db.commit()
        cid = cyc.id
    s = _statut(cid)
    assert s["status"] == "absent" and s["chunks"] == 0
