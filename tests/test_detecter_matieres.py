r"""Preuve — détection IA des matières au dépôt du PDF + écriture EN BASE des candidates.

Deux briques neuves (tâche « au dépôt, l'IA lit le PDF et propose des matières ») :
  1. `_ecrire_candidates(db, niveau_id, noms)` = pendant écriture de `_lire_candidates` : une ligne
     par niveau dans `matieres_candidates`, ÉCRASÉE par le nouveau PDF (get-or-create). Round-trip
     avec `_lire_candidates` + preuve de l'écrasement (2e dépôt remplace le 1er).
  2. `detecter_matieres(texte, db=)` = l'IA rend un JSON {matieres:[...]} ; on prouve le parsing,
     le nettoyage et la déduplication (insensible à la casse) SANS appeler de vrai LLM (generate mocké).

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_detecter_matieres.py -q
"""
import json
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod
import backend.rag.analyse_amont as amont
from backend.core.models_db import Cycle, Niveau
from backend.pedagogie.referentiels_admin import _ecrire_candidates, _lire_candidates

CYCLE = "Crèche"
NIVEAU = "Bébés (0-1 an)"


def _niveau():
    """Crée cycle + niveau, renvoie niveau_id."""
    db = dbmod.SessionLocal()
    try:
        cy = Cycle(nom=CYCLE, ordre=1); db.add(cy); db.flush()
        niv = Niveau(cycle_id=cy.id, nom=NIVEAU, ordre=1); db.add(niv); db.flush()
        db.commit()
        return niv.id
    finally:
        db.close()


def test_ecrire_puis_lire_candidates():
    """Écriture EN BASE puis relecture : ce que _ecrire_candidates pose, _lire_candidates le rend."""
    niveau_id = _niveau()
    db = dbmod.SessionLocal()
    try:
        _ecrire_candidates(db, niveau_id, ["Langage", "Motricité", "Éveil"])
        assert _lire_candidates(db, niveau_id) == ["Langage", "Motricité", "Éveil"]
    finally:
        db.close()


def test_nouveau_pdf_ecrase_les_candidates():
    """Le nouveau PDF ÉCRASE la proposition précédente (une ligne par niveau, jamais d'empilement)."""
    niveau_id = _niveau()
    db = dbmod.SessionLocal()
    try:
        _ecrire_candidates(db, niveau_id, ["Ancienne A", "Ancienne B"])
        _ecrire_candidates(db, niveau_id, ["Nouvelle X"])          # 2e dépôt
        assert _lire_candidates(db, niveau_id) == ["Nouvelle X"]   # l'ancien a disparu
    finally:
        db.close()


def test_detecter_matieres_injecte_la_table_des_matieres(monkeypatch):
    """L'IA reçoit la table des matières ACTIVES dans son prompt (get, zéro copie) pour faire
    correspondre le document avec l'existant. Preuve : les matières actives figurent dans le prompt
    envoyé à `generate`, pas les inactives, et les deux trous {matieres_existantes}/{texte} sont remplis."""
    from backend.core.models_db import Matiere
    with dbmod.SessionLocal() as db:
        db.add(Matiere(nom="Mathématiques", ordre=1, actif=True))
        db.add(Matiere(nom="Physique-Chimie", ordre=2, actif=True))
        db.add(Matiere(nom="Vieille matière", ordre=3, actif=False))
        db.commit()
    capture = {}

    def faux_generate(prompt, **k):
        capture["prompt"] = prompt
        return json.dumps({"matieres": []})

    monkeypatch.setattr(amont, "generate", faux_generate)
    with dbmod.SessionLocal() as db:
        amont.detecter_matieres("texte du référentiel", db=db)
    p = capture["prompt"]
    assert "- Mathématiques" in p and "- Physique-Chimie" in p
    assert "Vieille matière" not in p                      # inactive = hors liste
    assert "{matieres_existantes}" not in p and "{texte}" not in p
    assert "texte du référentiel" in p


def test_detecter_types_injecte_le_catalogue(monkeypatch):
    """Calque des matières pour les TYPES D'ACTIVITÉ : l'IA reçoit le catalogue des types ACTIFS
    dans son prompt (get, zéro copie) pour faire correspondre le document avec l'existant. Preuve :
    les types actifs figurent dans le prompt envoyé à `generate`, pas les inactifs, et les deux
    trous {types_existants}/{texte} sont remplis."""
    from backend.core.models_db import ActiviteType
    with dbmod.SessionLocal() as db:
        db.add(ActiviteType(label="Travaux pratiques", ordre=1, actif=True, origine="systeme"))
        db.add(ActiviteType(label="Évaluation", ordre=2, actif=True, origine="systeme"))
        db.add(ActiviteType(label="Vieux type", ordre=3, actif=False, origine="admin"))
        db.commit()
    capture = {}

    def faux_generate(prompt, **k):
        capture["prompt"] = prompt
        return json.dumps({"types": []})

    monkeypatch.setattr(amont, "generate", faux_generate)
    with dbmod.SessionLocal() as db:
        amont.detecter_types_activite("texte du référentiel", db=db)
    p = capture["prompt"]
    assert "- Travaux pratiques" in p and "- Évaluation" in p
    assert "Vieux type" not in p                          # inactif = hors liste
    assert "{types_existants}" not in p and "{texte}" not in p
    assert "texte du référentiel" in p


def test_detecter_matieres_parse_nettoie_dedoublonne(monkeypatch):
    """L'IA rend un JSON {matieres:[...]} : on prouve le parsing, le strip et la déduplication
    (insensible à la casse), sans appeler de vrai LLM. On mocke la porte IA unique `generate`."""
    reponse = json.dumps({"matieres": ["  Langage ", "Motricité", "langage", "", "Éveil"]},
                         ensure_ascii=False)
    monkeypatch.setattr(amont, "generate", lambda *a, **k: reponse)
    db = dbmod.SessionLocal()
    try:
        noms = amont.detecter_matieres("texte du référentiel", db=db)
        # "langage" (doublon casse) et "" (vide) écartés ; ordre de lecture conservé
        assert noms == ["Langage", "Motricité", "Éveil"]
    finally:
        db.close()
