"""Preuve — la fiche d'une démonstration se transporte d'une installation à l'autre.

LA PANNE QU'IL EMPÊCHE (16/08/2026). La démonstration du Collège tournait en production : son
adresse répondait, son compartiment de données était en place. Aucun professeur ne la voyait —
sa FICHE était restée sur le poste de développement. Un déploiement porte le code, jamais les
fiches saisies, et rien ne permettait de la porter à la main.

CE QUE LE TEST PROUVE :
  1. L'export rend la fiche, rattachée au NOM du référentiel et non à son numéro.
  2. L'adresse ne voyage pas — elle décrit une machine, et c'est elle qui ouvre la porte au prof.
  3. L'import retrouve le référentiel sous son nom, même s'il porte un autre numéro à l'arrivée.
  4. Référentiel absent → refus lisible, rien n'est écrit.
  5. Fiche déjà présente → refus, tant que le remplacement n'est pas demandé.
  6. Remplacement demandé → la fiche est mise à jour, et l'ADRESSE déjà en place survit.
  7. Un fichier illisible est refusé en disant ce qu'on a vu.

Base de test PostgreSQL dédiée (aschool_test via conftest.py) — JAMAIS SQLite.
Lancer : docker compose exec backend python -m pytest tests/test_transfert_demo.py -q
"""
import json

import pytest

from backend.core import database as dbmod
from backend.core.models_db import Cycle, Demo, Niveau, Referentiel
from backend.pedagogie.transfert_demo import exporter, importer, lire_fichier, resume


@pytest.fixture
def base():
    db = dbmod.SessionLocal()
    db.query(Demo).delete()
    db.query(Referentiel).delete()
    db.query(Niveau).delete()
    db.query(Cycle).delete()
    db.commit()
    yield db
    db.close()


def _referentiel(db, nom_fixe, niveau_nom, cycle_nom="Cycle du transfert"):
    cycle = Cycle(nom=cycle_nom, ordre=1)
    db.add(cycle); db.flush()
    niveau = Niveau(nom=niveau_nom, cycle_id=cycle.id, ordre=1)
    db.add(niveau); db.flush()
    ref = Referentiel(niveau_id=niveau.id, nom_fixe=nom_fixe, collection=nom_fixe,
                      nom_affichage=niveau_nom)
    db.add(ref); db.flush()
    return ref


def test_l_export_porte_la_fiche_et_le_nom_du_referentiel(base):
    ref = _referentiel(base, "ref_demo_a", "4e")
    base.add(Demo(referentiel_id=ref.id, nom_base="college4e", url="http://localhost:8096",
                  nb_activites=336, nb_sequences=78, nb_seances=168, notes="montée à la main"))
    base.commit()
    demo_id = base.query(Demo).one().id

    contenu = exporter(base, demo_id)

    assert contenu["referentiel_nom_fixe"] == "ref_demo_a"
    assert contenu["fiche"]["nom_base"] == "college4e"
    assert contenu["fiche"]["nb_activites"] == 336
    assert contenu["fiche"]["notes"] == "montée à la main"
    # Le résumé sert à annoncer le fichier avant de l'installer.
    assert resume(contenu)["compte"]["activites"] == 336


def test_l_adresse_ne_voyage_pas(base):
    """Elle décrit une machine. Importée ailleurs, elle ouvrirait l'entrée du menu prof vers une
    adresse qui n'existe pas là-bas."""
    ref = _referentiel(base, "ref_demo_b", "3e")
    base.add(Demo(referentiel_id=ref.id, nom_base="college3e", url="http://localhost:8097"))
    base.commit()

    contenu = exporter(base, base.query(Demo).one().id)

    assert "url" not in contenu["fiche"]
    assert "localhost" not in json.dumps(contenu)


def test_l_import_retrouve_le_referentiel_sous_son_nom(base):
    """Le référentiel 21 du poste peut être le 34 en production : le rattachement suit le NOM."""
    contenu = {
        "format": 1, "referentiel_nom_fixe": "ref_demo_c", "etiquette": "Collège · 4e",
        "referentiel_affichage": "4e",
        "fiche": {"nom_base": "college4e", "nb_activites": 336, "nb_sequences": 78,
                  "nb_seances": 168, "date_generation": None, "defauts_connus": None,
                  "notes": None},
    }
    # Un référentiel « décalé » pour que les identifiants ne coïncident pas.
    _referentiel(base, "ref_decalage", "6e", cycle_nom="Cycle décalage")
    ref = _referentiel(base, "ref_demo_c", "4e")
    base.commit()

    resultat = importer(base, contenu)
    base.commit()

    pose = base.query(Demo).one()
    assert pose.referentiel_id == ref.id
    assert pose.nom_base == "college4e"
    assert pose.url is None                     # à renseigner sur place
    assert resultat["remplacee"] is False


def test_referentiel_absent_refuse_sans_rien_ecrire(base):
    contenu = {"format": 1, "referentiel_nom_fixe": "ref_jamais_vu",
               "fiche": {"nom_base": "x_demo"}}
    with pytest.raises(ValueError) as e:
        importer(base, contenu)
    assert "ref_jamais_vu" in str(e.value)
    assert base.query(Demo).count() == 0


def test_fiche_deja_presente_refuse_tant_qu_on_n_a_pas_confirme(base):
    ref = _referentiel(base, "ref_demo_d", "5e")
    base.add(Demo(referentiel_id=ref.id, nom_base="ancienne", url="https://demo.aschool.fr"))
    base.commit()
    contenu = {"format": 1, "referentiel_nom_fixe": "ref_demo_d", "referentiel_affichage": "5e",
               "fiche": {"nom_base": "nouvelle"}}

    with pytest.raises(ValueError) as e:
        importer(base, contenu)
    assert "Confirmez le remplacement" in str(e.value)
    assert base.query(Demo).one().nom_base == "ancienne"


def test_le_remplacement_garde_l_adresse_en_place(base):
    """L'adresse décrit CETTE installation : l'écraser fermerait la porte aux professeurs sans
    que personne l'ait demandé."""
    ref = _referentiel(base, "ref_demo_e", "2nde")
    base.add(Demo(referentiel_id=ref.id, nom_base="ancienne", url="https://demo.aschool.fr",
                  nb_activites=1))
    base.commit()
    contenu = {"format": 1, "referentiel_nom_fixe": "ref_demo_e", "referentiel_affichage": "2nde",
               "fiche": {"nom_base": "nouvelle", "nb_activites": 42, "nb_sequences": 0,
                         "nb_seances": 0, "date_generation": None, "defauts_connus": None,
                         "notes": None}}

    resultat = importer(base, contenu, remplacer=True)
    base.commit()

    pose = base.query(Demo).one()
    assert pose.nom_base == "nouvelle"
    assert pose.nb_activites == 42
    assert pose.url == "https://demo.aschool.fr"
    assert resultat["remplacee"] is True


def test_un_fichier_illisible_dit_ce_qu_on_a_vu():
    for octets, attendu in (
        (b"", "vide"),
        (b"{ceci n'est pas du json", "export valide"),
        (b'{"autre": 1}', "ne contient pas de d"),
    ):
        with pytest.raises(ValueError) as e:
            lire_fichier(octets)
        assert attendu in str(e.value), (octets, str(e.value))


def test_un_format_inconnu_est_refuse(base):
    with pytest.raises(ValueError) as e:
        importer(base, {"format": 99, "referentiel_nom_fixe": "x", "fiche": {}})
    assert "format" in str(e.value).lower()
