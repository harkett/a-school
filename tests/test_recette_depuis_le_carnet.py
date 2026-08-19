# -*- coding: utf-8 -*-
"""COCHER NE COCHE PAS — la recette décide.

Une note du carnet ne devient « faite » que si la recette est verte. Ces tests tiennent la règle
par les deux bouts : le verdict qui coche, celui qui refuse, et les chemins qui pourraient la
contourner sans qu'on s'en aperçoive.

Le lanceur (deploy/recette/serveur.js) n'est PAS démarré ici : c'est un conteneur avec un vrai
navigateur, il n'a rien à faire dans une suite unitaire. On remplace donc ses réponses — ce qu'on
vérifie, c'est la décision prise à partir d'elles, pas Playwright lui-même.
"""
import pytest
from fastapi.testclient import TestClient

import backend.core.database as dbmod
from backend.main import app
from backend.core.models_db import TacheAFaire
from backend.systeme import admin as mod_admin
from backend.systeme.admin import _make_admin_token

# La porte d'entrée admin, ouverte par le cookie signé — c'est le motif de toute la maison
# (tests/test_admin_ia_catalogue_crud.py). Ce n'est pas elle qu'on éprouve ici.
client = TestClient(app)
client.cookies.set("aschool_admin", _make_admin_token())


@pytest.fixture
def note():
    """Une note fraîche, retirée à la fin. Le carnet est celui de l'admin : on n'y laisse rien."""
    db = dbmod.SessionLocal()
    t = TacheAFaire(titre="Note de recette (test)", detail="jetable")
    db.add(t)
    db.commit()
    db.refresh(t)
    ident = t.id
    db.close()
    yield ident
    db = dbmod.SessionLocal()
    ligne = db.get(TacheAFaire, ident)
    if ligne is not None:
        db.delete(ligne)
        db.commit()
    db.close()


def _lanceur(monkeypatch, reponse):
    """Le lanceur répond ce qu'on veut, sans conteneur ni navigateur."""
    monkeypatch.setattr(mod_admin, "_appeler_le_lanceur", lambda chemin, methode="GET": reponse)


def _relire(ident):
    db = dbmod.SessionLocal()
    t = db.get(TacheAFaire, ident)
    vue = {"fait": t.fait, "etat": t.recette_etat, "detail": t.recette_detail, "at": t.recette_at}
    db.close()
    return vue


# ── LA RÈGLE ──────────────────────────────────────────────────────────────────────────────────

def test_recette_verte_coche_la_note(note, monkeypatch):
    """Verte : la case tombe, datée. C'est le seul chemin par lequel elle peut tomber."""
    _lanceur(monkeypatch, {"enCours": False, "verdict": "verte", "total": 5, "faits": 5,
                           "etape": "Terminé", "detail": None})
    r = client.get(f"/api/admin/taches-a-faire/{note}/recette")
    assert r.status_code == 200

    apres = _relire(note)
    assert apres["fait"] is True
    assert apres["etat"] == "verte"
    assert apres["at"] is not None


def test_recette_ratee_laisse_la_note_a_faire(note, monkeypatch):
    """Ratée : la note NE se coche pas, et elle porte le motif — sans quoi on relance à l'aveugle."""
    _lanceur(monkeypatch, {"enCours": False, "verdict": "ratee", "total": 5, "faits": 3,
                           "etape": "Terminé avec des échecs",
                           "detail": "A échoué : « le menu designe toujours la page affichee »"})
    client.get(f"/api/admin/taches-a-faire/{note}/recette")

    apres = _relire(note)
    assert apres["fait"] is False
    assert apres["etat"] == "ratee"
    assert "le menu" in apres["detail"]


def test_pendant_le_passage_rien_ne_bouge(note, monkeypatch):
    """Tant qu'elle tourne, la note reste exactement ce qu'elle était. Un état intermédiaire
    écrit en base laisserait la note bloquée si le navigateur se fermait en route."""
    _lanceur(monkeypatch, {"enCours": True, "verdict": None, "total": 5, "faits": 2,
                           "etape": "la grille se génère", "detail": None})
    client.get(f"/api/admin/taches-a-faire/{note}/recette")

    apres = _relire(note)
    assert apres["fait"] is False
    assert apres["etat"] is None
    assert apres["at"] is None


def test_le_passage_impossible_ne_marque_rien(note, monkeypatch):
    """« IMPOSSIBLE » N'ACCUSE PAS LA NOTE. Le lanceur le rend quand il n'a RIEN parcouru :
    l'application construite n'a pas répondu, le navigateur n'a pas démarré. Écrire « recette à
    refaire » là-dessus accuserait un travail que personne n'a regardé — la note ressort intacte,
    et c'est l'écran qui dit qu'elle n'a jamais été testée."""
    _lanceur(monkeypatch, {"enCours": False, "verdict": "impossible", "total": 0, "faits": 0,
                           "etape": "L’application n’a pas répondu",
                           "detail": "L’application construite n’a pas répondu en une minute."})
    r = client.get(f"/api/admin/taches-a-faire/{note}/recette")
    assert r.status_code == 200
    assert r.json()["detail"]  # le motif remonte quand même à l'écran

    apres = _relire(note)
    assert apres["fait"] is False
    assert apres["etat"] is None
    assert apres["at"] is None


def test_le_passage_impossible_ne_decoche_pas_une_note_faite(note, monkeypatch):
    """L'autre bout de la même règle : une note gagnée ne se perd pas parce que le conteneur a
    lâché. Rien n'a été parcouru, donc rien ne change — dans les deux sens."""
    db = dbmod.SessionLocal()
    t = db.get(TacheAFaire, note)
    t.fait = True
    t.recette_etat = "verte"
    db.commit()
    db.close()

    _lanceur(monkeypatch, {"enCours": False, "verdict": "impossible", "total": 0, "faits": 0,
                           "etape": "Le navigateur n’a pas pu démarrer", "detail": "spawn npx ENOENT"})
    client.get(f"/api/admin/taches-a-faire/{note}/recette")

    apres = _relire(note)
    assert apres["fait"] is True
    assert apres["etat"] == "verte"


def test_une_note_deja_faite_qui_rate_se_decoche(note, monkeypatch):
    """Le carnet ne peut pas afficher « faite » sur un travail qui casse. Une note cochée avant
    que la règle existe redescend au premier passage rouge."""
    db = dbmod.SessionLocal()
    t = db.get(TacheAFaire, note)
    t.fait = True
    db.commit()
    db.close()

    _lanceur(monkeypatch, {"enCours": False, "verdict": "ratee", "total": 5, "faits": 1,
                           "etape": "Terminé avec des échecs", "detail": "A échoué : « un scénario »"})
    client.get(f"/api/admin/taches-a-faire/{note}/recette")

    assert _relire(note)["fait"] is False


# ── LES CHEMINS DÉTOURNÉS ─────────────────────────────────────────────────────────────────────

def test_modifier_une_note_faite_ne_la_decoche_pas(note):
    """Le formulaire n'envoie que le titre et le détail. Avec un défaut à False, corriger une
    faute de frappe dans une note faite la remettait à faire — sans que personne l'ait demandé."""
    db = dbmod.SessionLocal()
    t = db.get(TacheAFaire, note)
    t.fait = True
    t.recette_etat = "verte"
    db.commit()
    db.close()

    r = client.put(f"/api/admin/taches-a-faire/{note}",
                   json={"titre": "Titre corrigé", "detail": "toujours jetable"})
    assert r.status_code == 200

    apres = _relire(note)
    assert apres["fait"] is True
    assert apres["etat"] == "verte"


def test_decocher_efface_le_verdict(note):
    """Décocher retire une affirmation. Garder la pastille verte sur une note redevenue à faire
    ferait passer un verdict périmé pour un verdict courant."""
    db = dbmod.SessionLocal()
    t = db.get(TacheAFaire, note)
    t.fait = True
    t.recette_etat = "verte"
    t.recette_detail = None
    db.commit()
    db.close()

    r = client.put(f"/api/admin/taches-a-faire/{note}",
                   json={"titre": "Note de recette (test)", "fait": False})
    assert r.status_code == 200

    apres = _relire(note)
    assert apres["fait"] is False
    assert apres["etat"] is None
    assert apres["at"] is None


def test_le_service_absent_le_dit_et_ne_coche_rien(note, monkeypatch):
    """Sans le conteneur de recette, on ne coche pas « au bénéfice du doute » : on explique
    comment le démarrer, et la note reste à faire."""
    from fastapi import HTTPException

    def absent(chemin, methode="GET"):
        raise HTTPException(503, mod_admin.RECETTE_ABSENTE)

    monkeypatch.setattr(mod_admin, "_appeler_le_lanceur", absent)
    r = client.post(f"/api/admin/taches-a-faire/{note}/recette")

    assert r.status_code == 503
    assert "profile recette" in r.json()["detail"]
    assert _relire(note)["fait"] is False


def test_note_inconnue(monkeypatch):
    _lanceur(monkeypatch, {"enCours": False, "verdict": "verte", "total": 1, "faits": 1})
    assert client.get("/api/admin/taches-a-faire/999999/recette").status_code == 404
