r"""Un refus n'est pas une consommation — et un refus n'est pas un appel muet.

CE QUI A CHANGÉ SOUS LES ÉCRANS. `usage_llm` ne portait que les appels ABOUTIS ; elle porte
maintenant les TENTATIVES, refus compris (colonne `resultat`). Les deux écrans qui la lisent ont
été écrits avant ce changement et ne le savaient pas :

  * « IA › Statistiques » compte des appels et des tokens. Un refus n'a produit aucun token, mais
    il aurait été compté dans le NOMBRE d'appels — donc dans les moyennes, et dans le nombre
    affiché à l'admin qui cherche à comprendre sa facture. Une facture ne compte pas ce qui n'a
    pas été livré.
  * « IA › Journal » montre les appels un par un. Un refus s'y affichait comme une ligne à zéro
    token, sans motif d'arrêt (« — ») : indiscernable d'un appel dont on ignore la fin, alors
    qu'on sait très exactement ce qui s'est passé.

LE CAS QUI N'EST PAS UN REFUS. `coupe` — la réponse tronquée sur la limite de sortie — RESTE
comptée dans les statistiques : elle a bien été produite, et elle se facture. La masquer ferait
disparaître de l'écran une dépense réelle, et c'est précisément la dépense qu'on veut voir.

Lancer : docker compose exec backend python -m pytest tests/test_refus_hors_consommation.py -q
"""
from datetime import timedelta

import pytest

from conftest import resemer_reglages

from backend.core.database import SessionLocal
from backend.core.models_db import UsageLlm
from backend.core.horloge import maintenant_utc
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient


def _client():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


@pytest.fixture
def trois_tentatives():
    """Un succès, un refus, une réponse coupée — chez le même fournisseur, sur le même outil, pour
    que seule la colonne `resultat` les distingue."""
    resemer_reglages()
    db = SessionLocal()
    try:
        db.query(UsageLlm).delete()
        quand = maintenant_utc() - timedelta(hours=1)
        db.add_all([
            UsageLlm(created_at=quand, fournisseur="groq", modele="m-test", outil="activite",
                     tokens_entree=1000, tokens_sortie=500, duree_ms=900,
                     motif_arret="stop", resultat="ok"),
            # Un refus : aucun token, un code, et rien à facturer.
            UsageLlm(created_at=quand, fournisseur="groq", modele="m-test", outil="activite",
                     duree_ms=120, resultat="refus", code_http=429),
            # Une réponse coupée : elle a consommé, elle se facture, elle reste dans les totaux.
            UsageLlm(created_at=quand, fournisseur="groq", modele="m-test", outil="activite",
                     tokens_entree=800, tokens_sortie=400, duree_ms=700,
                     motif_arret="length", resultat="coupe"),
        ])
        db.commit()
        yield
        db.query(UsageLlm).delete()
        db.commit()
    finally:
        db.close()


def test_les_statistiques_ne_comptent_pas_le_refus(trois_tentatives):
    """Deux appels comptés sur trois lignes : le refus n'a rien consommé, il n'est pas de la
    consommation. C'est le défaut que la nouvelle colonne aurait introduit sans ce filtre."""
    r = _client().get("/api/admin/ia/usage?jours=7")
    assert r.status_code == 200, r.text
    lignes = [l for l in r.json()["par_outil"] if l["cle"] == "activite"]
    assert lignes, "l'outil de test n'apparaît pas dans les statistiques"
    assert lignes[0]["appels"] == 2, (
        f"{lignes[0]['appels']} appels comptés au lieu de 2 : le refus est compté comme un appel."
    )


def test_la_reponse_coupee_reste_dans_les_totaux(trois_tentatives):
    """Elle a été produite et elle se paie : 1 000 + 800 en entrée, 500 + 400 en sortie."""
    r = _client().get("/api/admin/ia/usage?jours=7")
    ligne = next(l for l in r.json()["par_outil"] if l["cle"] == "activite")
    assert ligne["tokens_entree"] == 1800, ligne
    assert ligne["tokens_sortie"] == 900, ligne


def test_le_journal_montre_le_refus_et_le_nomme(trois_tentatives):
    """L'inverse des statistiques : le journal doit TOUT montrer, c'est sa raison d'être. Et il
    doit rendre `resultat` et `code_http`, sans quoi l'écran ne peut pas distinguer un refus d'un
    appel à zéro token."""
    r = _client().get("/api/admin/ia/journal?jours=7")
    assert r.status_code == 200, r.text
    corps = r.json()
    nos_lignes = [l for l in corps["lignes"] if l["modele"] == "m-test"]
    assert len(nos_lignes) == 3, f"{len(nos_lignes)} lignes au journal au lieu de 3"

    refus = [l for l in nos_lignes if l["resultat"] == "refus"]
    assert len(refus) == 1, "le refus n'est pas identifiable au journal"
    assert refus[0]["code_http"] == 429, refus[0]
    assert refus[0]["cout_usd"] is None, "un refus n'a rien coûté, il ne peut pas porter un prix"


def test_le_cout_total_du_journal_ignore_le_refus(trois_tentatives):
    """Le montant affiché est une estimation de facture : ce qui n'est pas parti ne s'y ajoute pas.
    Sans tarif sur le modèle de test, le total reste nul et se déclare partiel — ce qui suffit :
    le test porte sur le fait que le refus n'introduit pas de montant."""
    corps = _client().get("/api/admin/ia/journal?jours=7").json()
    assert corps["cout_usd"] == 0


# ── Ce que la liste a rattrapé ──────────────────────────────────────────────────────────────────

def test_les_generations_sauvees_se_comptent():
    """Une réponse obtenue au rang 2 ou plus est une génération que la version précédente aurait
    perdue : le premier avait refusé, et il n'y avait personne derrière lui.

    Le rang 1 n'est PAS compté — un succès du premier appelé, c'est exactement ce qui se passait
    avant, il n'y a rien à en dire."""
    resemer_reglages()
    db = SessionLocal()
    try:
        db.query(UsageLlm).delete()
        quand = maintenant_utc() - timedelta(hours=1)
        db.add_all([
            # Un succès du premier : normal, ne compte pas.
            UsageLlm(created_at=quand, fournisseur="groq", modele="m", outil="activite",
                     tokens_entree=10, tokens_sortie=5, resultat="ok", rang=1),
            # Un refus puis un succès au rang 2 : UNE génération sauvée.
            UsageLlm(created_at=quand, fournisseur="groq", modele="m", outil="activite",
                     resultat="refus", code_http=429, rang=1),
            UsageLlm(created_at=quand, fournisseur="anthropic", modele="c", outil="activite",
                     tokens_entree=10, tokens_sortie=5, resultat="ok", rang=2),
            # Un appel sans rang du tout (aucune liste) : ne compte pas non plus.
            UsageLlm(created_at=quand, fournisseur="groq", modele="m", outil="activite",
                     tokens_entree=10, tokens_sortie=5, resultat="ok"),
        ])
        db.commit()

        corps = _client().get("/api/admin/ia/usage?jours=7").json()
        assert corps["appels_rattrapes"] == 1, (
            f"{corps['appels_rattrapes']} génération(s) comptée(s) au lieu de 1"
        )
    finally:
        db.query(UsageLlm).delete()
        db.commit()
        db.close()
