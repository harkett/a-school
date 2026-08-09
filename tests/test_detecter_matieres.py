r"""Preuve — détection IA des matières au dépôt du PDF.

`detecter_matieres(texte, db=)` : l'IA rend un JSON {matieres:[...]} ; on prouve le parsing, le
nettoyage et la déduplication (insensible à la casse) SANS appeler de vrai LLM (generate mocké),
et le remplissage des repères du prompt.

L'ÉCRITURE de ces propositions en base (matières du référentiel, `validee=false`) est prouvée
par tests/test_matieres_candidates_en_base.py — elle ne passe plus par une table à part.

Lancer : docker compose exec backend python -m pytest tests/test_detecter_matieres.py -q
"""
import json
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import backend.core.database as dbmod
import backend.rag.analyse_amont as amont


def test_detecter_matieres_ne_recoit_que_le_texte(monkeypatch):
    """L'IA ne reçoit PLUS aucune liste de matières : il n'existe plus de catalogue commun auquel
    ramener le document, chaque référentiel nomme les siennes. Preuve : des matières bien
    présentes en base n'apparaissent nulle part dans le prompt envoyé à `generate`, qui ne porte
    que le texte du document — et aucun repère resté en clair."""
    from backend.core.models_db import Cycle, Matiere, Niveau, Referentiel
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom="Collège", ordre=1); db.add(cy); db.flush()
        niv = Niveau(cycle_id=cy.id, nom="5e", ordre=1); db.add(niv); db.flush()
        # Une matière vit dans le référentiel qui la nomme : pas de référentiel, pas de matière.
        ref = Referentiel(niveau_id=niv.id, nom_fixe="5e", collection="5e"); db.add(ref); db.flush()
        # Noms volontairement improbables : le prompt cite lui-même « Mathématiques » dans un
        # exemple, un nom courant ferait passer le test pour de mauvaises raisons.
        db.add(Matiere(referentiel_id=ref.id, nom="ZZ-Discipline-Alpha", ordre=1, actif=True, validee=True))
        db.add(Matiere(referentiel_id=ref.id, nom="ZZ-Discipline-Beta", ordre=2, actif=True, validee=True))
        db.commit()
    capture = {}

    def faux_generate(prompt, **k):
        capture["prompt"] = prompt
        return json.dumps({"matieres": []})

    monkeypatch.setattr(amont, "generate", faux_generate)
    with dbmod.SessionLocal() as db:
        amont.detecter_matieres("texte du référentiel", db=db)
    p = capture["prompt"]
    assert "ZZ-Discipline-Alpha" not in p and "ZZ-Discipline-Beta" not in p  # aucune liste injectée
    assert "{matieres_existantes}" not in p                          # ni le repère, ni son texte
    assert "{texte}" not in p and "texte du référentiel" in p        # le seul trou est rempli


def test_detecter_types_ne_recoit_que_le_texte(monkeypatch):
    """Calque des matières pour les TYPES D'ACTIVITÉ (05/08/2026) : l'IA ne reçoit PLUS de
    catalogue. Il n'existe plus de liste commune à laquelle ramener le document — chaque
    référentiel met en œuvre SES formats, nommés comme LUI les nomme. Preuve : le prompt envoyé
    ne porte ni le repère {types_existants}, ni aucun libellé venu d'un autre référentiel.

    Et le PROMPT DU CYCLE l'emporte quand il existe : la donnée appartient au référentiel, la
    recette qui la lit appartient à la famille."""
    capture = {}

    def faux_generate(prompt, **k):
        capture["prompt"] = prompt
        return json.dumps({"types": []})

    monkeypatch.setattr(amont, "generate", faux_generate)
    with dbmod.SessionLocal() as db:
        amont.detecter_types_activite("texte du référentiel", db=db)
    p = capture["prompt"]
    assert "{types_existants}" not in p and "{texte}" not in p
    assert "texte du référentiel" in p

    with dbmod.SessionLocal() as db:
        amont.detecter_types_activite("texte du référentiel", db=db,
                                      prompt_referentiel="RECETTE DU RÉFÉRENTIEL : {texte}")
    assert capture["prompt"] == "RECETTE DU RÉFÉRENTIEL : texte du référentiel"


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
