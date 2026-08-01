r"""Preuve — détection IA des matières au dépôt du PDF.

`detecter_matieres(texte, db=)` : l'IA rend un JSON {matieres:[...]} ; on prouve le parsing, le
nettoyage et la déduplication (insensible à la casse) SANS appeler de vrai LLM (generate mocké),
et le remplissage des repères du prompt.

L'ÉCRITURE de ces propositions en base (matières du référentiel, `validee=false`) est prouvée
par tests/test_matieres_candidates_en_base.py — elle ne passe plus par une table à part.

Lancer : docker exec a-school-backend-1 python -m pytest tests/test_detecter_matieres.py -q
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


def test_detecter_matieres_injecte_la_table_des_matieres(monkeypatch):
    """L'IA reçoit la table des matières ACTIVES dans son prompt (get, zéro copie) pour faire
    correspondre le document avec l'existant. Preuve : les matières actives figurent dans le prompt
    envoyé à `generate`, pas les inactives, et les deux trous {matieres_existantes}/{texte} sont remplis."""
    from backend.core.models_db import Cycle, Matiere, Niveau, Referentiel
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom="Collège", ordre=1); db.add(cy); db.flush()
        niv = Niveau(cycle_id=cy.id, nom="5e", ordre=1); db.add(niv); db.flush()
        # Une matière vit dans le référentiel qui la nomme : pas de référentiel, pas de matière.
        ref = Referentiel(niveau_id=niv.id, nom_fixe="5e", collection="5e"); db.add(ref); db.flush()
        db.add(Matiere(referentiel_id=ref.id, nom="Mathématiques", ordre=1, actif=True, validee=True))
        db.add(Matiere(referentiel_id=ref.id, nom="Physique-Chimie", ordre=2, actif=True, validee=True))
        db.add(Matiere(referentiel_id=ref.id, nom="Vieille matière", ordre=3, actif=False, validee=True))
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
