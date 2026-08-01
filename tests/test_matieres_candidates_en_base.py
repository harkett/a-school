r"""Preuve — une matiere PROPOSEE par la detection et une matiere RETENUE par l'admin sont la
MEME ligne de `matieres`, distinguee par `validee`.

Avant : une table `matieres_candidates` (un tableau JSON de noms par niveau) vivait a cote de la
table `matieres` et doublait la meme information. Apres : la detection ecrit directement dans
`matieres` (referentiel du niveau, `validee=false`), cocher bascule `validee` a true. Une seule
place pour la donnee — get pour lire, put pour ecrire, zero copie.

Ce que ce test PROUVE (base aschool_test) :
  1. Aucune matiere -> `etat_couple` renvoie matieres: [] et candidates: [].
  2. `_ecrire_matieres_proposees` pose des lignes NON validees -> elles sortent en `candidates`,
     jamais en `matieres` : une proposition d'IA n'entre pas dans le programme toute seule.
  3. Rejouer la detection n'ecrit pas de doublon (anti-doublon insensible a la casse), et une
     matiere DEJA RETENUE n'est jamais redegradee en proposition.
  4. Une matiere validee sort en `matieres` et disparait des `candidates`.

Lancer : docker exec a-school-backend-1 python -m pytest tests/test_matieres_candidates_en_base.py -q
"""
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod
from backend.core.models_db import Cycle, Matiere, Niveau, Referentiel
from backend.pedagogie.referentiels_admin import _ecrire_matieres_proposees, etat_couple

CYCLE = "Crèche"
NIVEAU = "Bébés (0-1 an)"


def _couple():
    """Crée cycle + niveau + le référentiel du niveau. Renvoie (cycle_id, referentiel_id)."""
    db = dbmod.SessionLocal()
    try:
        cy = Cycle(nom=CYCLE, ordre=1); db.add(cy); db.flush()
        niv = Niveau(cycle_id=cy.id, nom=NIVEAU, ordre=1); db.add(niv); db.flush()
        ref = Referentiel(niveau_id=niv.id, nom_fixe="bebes_0_1_an", collection="bebes_0_1_an",
                          fichier="referentiel.pdf", texte_epure="TEXTE")
        db.add(ref); db.commit()
        return cy.id, ref.id
    finally:
        db.close()


def test_aucune_matiere_renvoie_deux_listes_vides():
    cycle_id, _ = _couple()
    db = dbmod.SessionLocal()
    try:
        etat = etat_couple(cycle_id=cycle_id, niveau=NIVEAU, db=db)
        assert etat["matieres"] == [] and etat["candidates"] == []
    finally:
        db.close()


def test_la_detection_propose_elle_ne_retient_pas():
    noms = ["Langage", "Éveil sensoriel", "Motricité"]
    cycle_id, ref_id = _couple()
    db = dbmod.SessionLocal()
    try:
        _ecrire_matieres_proposees(db, ref_id, noms)
        etat = etat_couple(cycle_id=cycle_id, niveau=NIVEAU, db=db)
        assert etat["candidates"] == noms      # proposées, elles attendent l'admin
        assert etat["matieres"] == []          # aucune n'est entrée au programme d'office
        # Les lignes sont bien dans `matieres`, sur le référentiel — pas dans une table à côté.
        assert db.query(Matiere).filter(Matiere.referentiel_id == ref_id).count() == 3
    finally:
        db.close()


def test_rejouer_la_detection_ne_doublonne_pas_et_respecte_le_choix_de_l_admin():
    cycle_id, ref_id = _couple()
    db = dbmod.SessionLocal()
    try:
        _ecrire_matieres_proposees(db, ref_id, ["Langage", "Motricité"])
        # L'admin RETIENT « Langage ».
        db.query(Matiere).filter(Matiere.referentiel_id == ref_id,
                                 Matiere.nom == "Langage").update({"validee": True})
        db.commit()

        # Nouveau PDF : la détection relit les mêmes noms (à la casse près) + un nouveau.
        _ecrire_matieres_proposees(db, ref_id, ["langage", "MOTRICITÉ", "Éveil"])

        noms = sorted(n for (n,) in db.query(Matiere.nom)
                        .filter(Matiere.referentiel_id == ref_id).all())
        assert noms == ["Langage", "Motricité", "Éveil"]        # aucun doublon de casse
        etat = etat_couple(cycle_id=cycle_id, niveau=NIVEAU, db=db)
        assert etat["matieres"] == [{"id": etat["matieres"][0]["id"], "nom": "Langage"}]
        assert sorted(etat["candidates"]) == ["Motricité", "Éveil"]
    finally:
        db.close()
