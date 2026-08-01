"""GET /api/programmes/couverture — vitrine « Programmes couverts » (page À propos du prof).

Ce que ces tests PROUVENT :
  1. La couverture liste TOUS les cycles/niveaux, Y COMPRIS un niveau SANS matière rattachée
     (comme BTS / BUT / Master / Doctorat dans la vraie base) — là où /programmes le masque.
  2. refDisponible est DÉRIVÉ, zéro copie : vrai UNIQUEMENT si le niveau a un référentiel
     réellement ingéré (au moins un chunk), faux sinon.

BDD de test PostgreSQL dédiée (aschool_test via conftest.py).
"""


import backend.core.database as dbmod
from backend.main import app
from fastapi.testclient import TestClient


def _couverture():
    r = TestClient(app).get('/api/programmes/couverture')
    assert r.status_code == 200, r.text
    return {b['cycle']: b['niveaux'] for b in r.json()['cycles']}


def test_niveau_sans_matiere_est_present_et_a_venir():
    from backend.core.models_db import Cycle, Niveau
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom='CV-Doctorat', ordre=900)
        db.add(cy); db.flush()
        db.add(Niveau(cycle_id=cy.id, nom='CV-Doctorat Physique', ordre=1))  # AUCUNE paire matière
        db.commit()
    niveaux = _couverture().get('CV-Doctorat')
    assert niveaux is not None, "un cycle sans matière doit quand même apparaître dans la vitrine"
    assert [n['nom'] for n in niveaux] == ['CV-Doctorat Physique']
    assert niveaux[0]['refDisponible'] is False   # pas de référentiel → à venir (gris)


def test_ref_disponible_vrai_seulement_avec_un_chunk():
    from backend.core.models_db import Cycle, Niveau, Referentiel, ReferentielChunk
    with dbmod.SessionLocal() as db:
        cy = Cycle(nom='CV-Creche', ordre=901)
        db.add(cy); db.flush()
        n_ok = Niveau(cycle_id=cy.id, nom='CV-Avec', ordre=1); db.add(n_ok); db.flush()
        n_ko = Niveau(cycle_id=cy.id, nom='CV-Sans', ordre=2); db.add(n_ko); db.flush()
        # n_ok : référentiel + 1 chunk → disponible ; n_ko : aucun référentiel.
        ref = Referentiel(niveau_id=n_ok.id, nom_fixe='cv_avec', collection='cv_avec',
                          filtres=None, fichier='doc.pdf', texte_epure='TEXTE')
        db.add(ref); db.flush()
        db.add(ReferentielChunk(referentiel_id=ref.id, chunk_index=0, option_ab='', page=1,
                                texte='x', embedding=[0.1] * 1024, embedding_model='test'))
        db.commit()
    par_nom = {n['nom']: n['refDisponible'] for n in _couverture()['CV-Creche']}
    assert par_nom['CV-Avec'] is True     # référentiel + chunk → disponible (gras)
    assert par_nom['CV-Sans'] is False    # rien → à venir (gris)
