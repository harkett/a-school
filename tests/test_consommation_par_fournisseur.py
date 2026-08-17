r"""La cartouche « Consommation IA » du tableau de bord — ce que le serveur doit lui servir.

CE QUE CES TESTS PROUVENT (base aschool_test via conftest.py — JAMAIS SQLite) :

  1. `/admin/ia/usage` rend un regroupement PAR FOURNISSEUR : la question que pose
     l'administration devant une facture est « qui a été payé », et la liste de repli fait qu'il
     y en a plusieurs sur la même période.
  2. Les montants par fournisseur SOMMENT au total affiché en gros. Un écart entre le total et
     les colonnes qui le composent décrédibilise les deux d'un coup.
  3. Le coût par ACTION n'est plus muet — il l'était (`cout_usd: None`) parce que le
     regroupement mélangeait les modèles.
  4. LE COÛT SE CALCULE PAR MODÈLE PUIS SE SOMME. Deux modèles à tarifs différents sur la même
     clé doivent donner la somme des deux calculs, jamais le produit d'un mélange de tokens.
  5. Un modèle sans tarif ne rend pas la ligne muette : ses tokens comptent, et `cout_partiel`
     prévient que le montant est un plancher.

Lancer : docker compose exec backend python -m pytest tests/test_consommation_par_fournisseur.py -q
"""
from datetime import timedelta

import pytest

from conftest import resemer_reglages

from backend.core.database import SessionLocal
from backend.core.models_db import AiModele, UsageLlm
from backend.core.horloge import maintenant_utc
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient


def _client():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


# Deux tarifs volontairement très écartés : si le calcul mélangeait les tokens avant de
# multiplier, l'écart se verrait au dollar près plutôt qu'au centième.
TARIFS = {"m-cher": (30.0, 60.0), "m-pas-cher": (1.0, 2.0)}


@pytest.fixture
def deux_fournisseurs():
    """Le cas réel de la cascade : le gratuit refuse, le payant répond — et un troisième appel
    part sur un second modèle, à un autre tarif, pour le même outil."""
    resemer_reglages()
    db = SessionLocal()
    try:
        db.query(UsageLlm).delete()
        db.query(AiModele).filter(AiModele.modele.in_(list(TARIFS) + ["m-sans-tarif"])).delete(
            synchronize_session=False)
        for modele, (entree, sortie) in TARIFS.items():
            db.add(AiModele(modele=modele, label=modele, fournisseur="anthropic",
                            cout_entree_million=entree, cout_sortie_million=sortie))
        # Un modèle connu mais SANS tarif : il existe en base, son prix n'est pas renseigné.
        db.add(AiModele(modele="m-sans-tarif", label="m-sans-tarif", fournisseur="groq"))

        quand = maintenant_utc() - timedelta(hours=1)
        db.add_all([
            # Groq refuse : la ligne existe, elle ne consomme rien.
            UsageLlm(created_at=quand, fournisseur="groq", modele="m-sans-tarif", outil="activite",
                     duree_ms=120, resultat="refus", code_http=429, rang=1),
            # Anthropic répond, deux fois, sur deux modèles au tarif différent.
            UsageLlm(created_at=quand, fournisseur="anthropic", modele="m-cher", outil="activite",
                     tokens_entree=1_000_000, tokens_sortie=0, duree_ms=900,
                     motif_arret="stop", resultat="ok", rang=3),
            UsageLlm(created_at=quand, fournisseur="anthropic", modele="m-pas-cher",
                     outil="activite", tokens_entree=1_000_000, tokens_sortie=0, duree_ms=800,
                     motif_arret="stop", resultat="ok", rang=3),
            # Un appel gratuit ABOUTI chez groq, sur le modèle sans tarif.
            UsageLlm(created_at=quand, fournisseur="groq", modele="m-sans-tarif", outil="quiz",
                     tokens_entree=2000, tokens_sortie=1000, duree_ms=300,
                     motif_arret="stop", resultat="ok", rang=1),
        ])
        db.commit()
        yield
        db.query(UsageLlm).delete()
        db.query(AiModele).filter(AiModele.modele.in_(list(TARIFS) + ["m-sans-tarif"])).delete(
            synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _usage():
    r = _client().get("/api/admin/ia/usage?jours=7")
    assert r.status_code == 200, r.text
    return r.json()


def test_la_consommation_se_lit_par_fournisseur(deux_fournisseurs):
    """Sans ce regroupement, la cartouche ne peut pas dire QUI a été payé — c'est-à-dire ce que
    coûte le refus du gratuit."""
    par = {l["cle"]: l for l in _usage()["par_fournisseur"]}
    assert set(par) == {"anthropic", "groq"}, par
    # Le refus n'est pas un appel : groq n'en a qu'un, celui qui a abouti.
    assert par["groq"]["appels"] == 1
    assert par["anthropic"]["appels"] == 2


def test_les_fournisseurs_somment_au_total(deux_fournisseurs):
    """Le grand chiffre de gauche et les colonnes de droite comptent les mêmes appels."""
    data = _usage()
    somme = sum(l["cout_usd"] for l in data["par_fournisseur"])
    assert round(somme, 4) == round(data["cout_usd"], 4), data["par_fournisseur"]


def test_le_cout_par_action_n_est_plus_muet(deux_fournisseurs):
    """Il valait `None` : le regroupement mélangeait les modèles, donc les tarifs."""
    par = {l["cle"]: l for l in _usage()["par_outil"]}
    assert par["activite"]["cout_usd"] is not None


def test_deux_tarifs_se_calculent_puis_s_additionnent(deux_fournisseurs):
    """LE point du calcul. Un million de tokens d'entrée à 30 $, un million à 1 $ : 31 $.

    Un regroupement qui aurait additionné les tokens AVANT de multiplier aurait rendu 60 $ (deux
    millions au tarif du premier) ou 2 $ — un montant inventé dans les deux cas."""
    par = {l["cle"]: l for l in _usage()["par_outil"]}
    assert par["activite"]["cout_usd"] == pytest.approx(31.0, abs=0.001), par["activite"]


def test_un_modele_sans_tarif_compte_ses_tokens_et_le_dit(deux_fournisseurs):
    """Ses jetons sont réels, son prix est inconnu : la ligne reste, le montant est un plancher."""
    par = {l["cle"]: l for l in _usage()["par_fournisseur"]}
    assert par["groq"]["tokens_entree"] == 2000
    assert par["groq"]["cout_partiel"] is True
    # Et l'inverse : un fournisseur entièrement tarifé ne porte pas l'avertissement.
    assert par["anthropic"]["cout_partiel"] is False
