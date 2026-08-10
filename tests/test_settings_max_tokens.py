r"""Preuve de raccordement — max_tokens vient de la FICHE DU MODELE, plus d'un reglage d'ecran.

CE QUI A CHANGE, ET POURQUOI. Il a existe un ecran « Longueur (tokens) » ou l'admin reglait 17
outils un par un, plus un defaut global. Ces reglages ne servaient a rien de bon : `max_tokens`
n'allonge ni ne raccourcit une reponse — le modele s'arrete quand il a fini de dire ce qu'il a a
dire. Ce nombre ne fait QUE couper s'il depasse. Regler 17 outils, c'etait donc regler 17
couperets, et sur les 17 un seul avait recu une valeur voulue.

Le degat n'etait pas theorique : un referentiel s'est fait decouper a 5 000 jetons parce qu'un
reglage herite d'Infomaniak (dont le produit plafonne a 5 000) avait survecu au passage chez
Anthropic — alors que le modele en service en acceptait 128 000. Le message d'erreur accusait le
modele d'avoir « atteint sa limite », ce qui envoyait chercher au mauvais endroit.

La seule valeur qui a du sens est celle du modele, et elle est deja sur sa fiche
(`ai_modeles.max_tokens`, sinon `ai_fournisseurs.max_tokens`). La longueur VOULUE, elle, se dit
dans le prompt — la seule consigne qu'un modele sait respecter.

Ce que le test PROUVE (la chaine reelle remonte la bonne valeur, pas « le code existe ») :
  1. get_max_tokens() rend le `max_tokens` du MODELE en service, pour n'importe quel outil.
  2. TOUS les outils rendent la meme valeur — aucun n'est traite a part.
  3. Un `max_tokens` absent sur le modele fait heriter celui du FOURNISSEUR.
  4. Absent des deux -> filet MAX_TOKENS_SANS_FICHE, jamais une exception ni un zero (l'API exige
     un nombre : une fiche incomplete ne doit pas empecher de generer).
  5. La valeur change A CHAUD (meme process, sans redemarrage).
  6. Les anciens reglages `max_tokens_*` en base n'ont PLUS AUCUN EFFET — c'est le coeur de la
     correction : leur presence residuelle ne doit plus jamais rabaisser une generation.

Lancer : docker compose exec backend python -m pytest tests/test_settings_max_tokens.py -q
"""
# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
# `settings` vidée n'est plus un état neutre : les réglages vivent en base depuis le
# 10/08/2026 et une ligne absente fait lever pour un CHOIX (modèle, fournisseur). On
# repose donc ce qu'une installation à jour possède — sauf la clé que ce fichier teste.
from conftest import resemer_reglages

import backend.core.database as dbmod

from backend.core.models_db import AiFournisseur, AiModele, Setting
from backend.systeme.admin import get_max_tokens, get_max_tokens_modele, MAX_TOKENS_SANS_FICHE

_FOURNISSEUR = "fournisseur_test_maxtokens"
_MODELE = "modele-test-maxtokens"

# Un echantillon des 17 : deux outils que l'ancien ecran surchargeait, deux qu'il ignorait.
_OUTILS = ("decoupe_amont", "referentiel_fusion", "activite", "consigne")


def _table_rase(*, modele_max, fournisseur_max, reglages=None):
    """Pose un couple fournisseur/modele EN SERVICE avec les bornes voulues, et les reglages
    `max_tokens_*` demandes. Rend la session ouverte sur cet etat."""
    db = dbmod.SessionLocal()
    db.query(Setting).delete()
    db.query(AiModele).filter(AiModele.modele == _MODELE).delete()
    db.query(AiFournisseur).filter(AiFournisseur.code == _FOURNISSEUR).delete()

    db.add(AiFournisseur(code=_FOURNISSEUR, label="Test", cle_env="TEST_KEY",
                         max_tokens=fournisseur_max))
    db.add(AiModele(fournisseur=_FOURNISSEUR, modele=_MODELE, label="Test",
                    max_tokens=modele_max))
    # Le couple en service : c'est ce que lisent get_ai_provider / get_ai_model.
    db.add(Setting(key="ai_provider", value=_FOURNISSEUR))
    db.add(Setting(key="ai_model", value=_MODELE))
    for cle, valeur in (reglages or {}).items():
        db.add(Setting(key=cle, value=valeur))
    db.commit()
    return db


def _nettoyer(db):
    db.query(Setting).delete()
    db.query(AiModele).filter(AiModele.modele == _MODELE).delete()
    db.query(AiFournisseur).filter(AiFournisseur.code == _FOURNISSEUR).delete()
    db.commit()
    db.close()


def test_max_tokens_vient_du_modele():
    """1. La valeur rendue est celle de la fiche du modele, telle quelle."""
    db = _table_rase(modele_max=128000, fournisseur_max=5000)
    try:
        assert get_max_tokens_modele(db) == 128000
        assert get_max_tokens(db, "decoupe_amont") == 128000
    finally:
        _nettoyer(db)


def test_tous_les_outils_rendent_la_meme_valeur():
    """2. Aucun outil n'est traite a part : plus de reglage par outil, plus d'exception cachee."""
    db = _table_rase(modele_max=64000, fournisseur_max=None)
    try:
        assert {get_max_tokens(db, o) for o in _OUTILS} == {64000}
    finally:
        _nettoyer(db)


def test_modele_sans_valeur_herite_du_fournisseur():
    """3. Les 5 000 d'Infomaniak tiennent au produit, pas au modele : l'heritage doit jouer."""
    db = _table_rase(modele_max=None, fournisseur_max=5000)
    try:
        assert get_max_tokens(db, "activite") == 5000
    finally:
        _nettoyer(db)


def test_fiche_vide_des_deux_cotes_rend_le_filet():
    """4. L'API exige toujours un nombre : une fiche incomplete ne bloque pas la generation."""
    db = _table_rase(modele_max=None, fournisseur_max=None)
    try:
        valeur = get_max_tokens(db, "activite")
        assert valeur == MAX_TOKENS_SANS_FICHE
        assert valeur > 0  # jamais zero : l'appel serait refuse
    finally:
        _nettoyer(db)


def test_changement_a_chaud_sans_redemarrage():
    """5. Corriger la fiche suffit — pas de redemarrage, comme pour le choix du modele."""
    db = _table_rase(modele_max=8000, fournisseur_max=None)
    try:
        assert get_max_tokens(db, "consigne") == 8000
        db.query(AiModele).filter(AiModele.modele == _MODELE).update({"max_tokens": 96000})
        db.commit()
        assert get_max_tokens(db, "consigne") == 96000
    finally:
        _nettoyer(db)


def test_anciens_reglages_en_base_sont_sans_effet():
    """6. LE COEUR DE LA CORRECTION. Un `max_tokens_<outil>` residuel — celui qui a fait decouper
    un referentiel a 5 000 jetons — ne doit plus jamais rabaisser la demande."""
    db = _table_rase(
        modele_max=128000, fournisseur_max=None,
        reglages={"max_tokens_default": "5000", "max_tokens_decoupe_amont": "5000"},
    )
    try:
        assert get_max_tokens(db, "decoupe_amont") == 128000
        assert get_max_tokens(db, "activite") == 128000
    finally:
        _nettoyer(db)
