"""Chantier « suppression des familles » — le dépôt en couple cycle → niveau.

Ce que ces tests verrouillent :
  - `valider` exige un niveau EXISTANT (`niveau_id`) : 404 si inconnu ou hors du cycle,
    et ne crée JAMAIS de niveau (une seule place pour créer : POST /admin/niveaux).
  - `verifier-depot` = la seule vérif n°1 : verdict couple SEUL (plus de verdict famille).
  - les endpoints famille ont disparu (404).
  - la création cycle/niveau est relogée dans programmes.py (unicité 409, cycle inconnu 404).

BDD de test PostgreSQL dédiée (aschool_test via conftest.py), IA et texte du PDF mockés.
"""
import os
import sys
import uuid
from unittest.mock import patch

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod
import backend.pedagogie.referentiels_admin as refadm
from backend.main import app
from fastapi.testclient import TestClient


def admin_client():
    from backend.systeme.admin import _make_admin_token
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _cycle(nom="DC-Cycle", ordre=70):
    from backend.core.models_db import Cycle
    with dbmod.SessionLocal() as db:
        c = Cycle(nom=nom, ordre=ordre)
        db.add(c); db.commit(); db.refresh(c)
        return c.id


def _niveau(cycle_id, nom="DC-Niv", ordre=70):
    from backend.core.models_db import Niveau
    with dbmod.SessionLocal() as db:
        n = Niveau(cycle_id=cycle_id, nom=nom, ordre=ordre)
        db.add(n); db.commit(); db.refresh(n)
        return n.id


def _staged_token():
    """Pose un faux document en zone d'attente : `valider` vérifie seulement l'existence
    du fichier avant les contrôles cycle/niveau (le contenu n'est jamais lu dans ces tests)."""
    token = uuid.uuid4().hex
    (refadm.STAGING_DIR / f"{token}.pdf").write_bytes(b"%PDF-fake")
    return token


def _purge(token):
    (refadm.STAGING_DIR / f"{token}.pdf").unlink(missing_ok=True)


def test_valider_niveau_inconnu_404_et_ne_cree_jamais_de_niveau():
    from backend.core.models_db import Niveau
    cid = _cycle()
    token = _staged_token()
    try:
        r = admin_client().post("/api/admin/referentiels/valider", json={
            "token": token, "cycle_id": cid, "niveau_id": 999999})
        assert r.status_code == 404, r.text
        with dbmod.SessionLocal() as db:
            assert db.query(Niveau).count() == 0   # aucun niveau créé en douce
    finally:
        _purge(token)


def test_valider_niveau_d_un_autre_cycle_404():
    cid = _cycle("DC-A", 71)
    autre = _cycle("DC-B", 72)
    nid = _niveau(autre, "DC-NivB", 71)
    token = _staged_token()
    try:
        r = admin_client().post("/api/admin/referentiels/valider", json={
            "token": token, "cycle_id": cid, "niveau_id": nid})
        assert r.status_code == 404, r.text
    finally:
        _purge(token)


def test_verifier_depot_verdict_couple_seul():
    cid = _cycle()
    nid = _niveau(cid)
    token = _staged_token()
    verdict = {"correspond": True, "niveau_lu": "DC-Niv", "raison": "ok"}
    try:
        with patch.object(refadm, "_texte_staged", return_value="texte du document"), \
             patch("backend.rag.analyse_amont.verifier_couple", return_value=verdict):
            r = admin_client().post("/api/admin/referentiels/verifier-depot", json={
                "token": token, "cycle_id": cid, "niveau_id": nid})
        assert r.status_code == 200, r.text
        assert r.json() == {"couple": verdict}   # verdict couple SEUL — plus aucune clé famille
    finally:
        _purge(token)


def test_endpoints_famille_disparus():
    c = admin_client()
    assert c.get("/api/admin/familles").status_code == 404
    assert c.get("/api/admin/fc-autorisees").status_code == 404
    assert c.post("/api/admin/referentiels/detecter-famille", json={"token": "x"}).status_code == 404


def test_sans_numeros_de_page():
    """Les lignes qui ne contiennent QU'UN nombre (numéros de page collés par l'extraction PDF)
    sont écartées au tranchage ; les nombres DANS une phrase restent."""
    from backend.rag.analyse_amont import _sans_numeros_de_page
    texte = "Titre A\nRéaliser une pâte à choux\n34\nCuire 20 minutes au four\n 7 \nTitre B"
    assert _sans_numeros_de_page(texte) == "Titre A\nRéaliser une pâte à choux\nCuire 20 minutes au four\nTitre B"


def test_lettres_verticales_ecartees():
    """Le texte VERTICAL des marges (lettres seules empilées à la même position x) est repéré ;
    un mot horizontal normal (lettres qui se touchent) ne l'est jamais."""
    from backend.rag.extraction import _cles_lettres_verticales

    def ch(t, x0, top, largeur=5):
        return {"text": t, "x0": x0, "x1": x0 + largeur, "top": top}

    horizontal = [ch(l, 100 + i * 5, 50) for i, l in enumerate("Cuire")]       # lettres collées
    colonne = [ch(l, 40, 30 + i * 12) for i, l in enumerate("Tâches")]         # pile verticale
    debris = _cles_lettres_verticales(horizontal + colonne)
    assert debris == {(40, 30 + i * 12, l) for i, l in enumerate("Tâches")}


def test_modifier_unite_recalcule_l_empreinte():
    """PUT d'une unité : le texte est écrit ET l'empreinte recalculée dans le MÊME geste (mock du
    calcul). Garde : 404 si l'unité n'appartient pas au couple ; 400 si texte vide."""
    from backend.core.models_db import Referentiel, ReferentielChunk
    cid = _cycle("DC-Edit", 75)
    nid = _niveau(cid, "DC-NivEdit", 75)
    with dbmod.SessionLocal() as db:
        ref = Referentiel(niveau_id=nid, matiere_id=None, nom_fixe="dc_edit", collection="dc_edit",
                          filtres=None, fichier="doc.pdf")
        db.add(ref); db.flush()
        ch = ReferentielChunk(referentiel_id=ref.id, chunk_index=0, option_ab="", page=1,
                              texte="Titre\nRéaliser une pâte\n34", embedding=[0.0] * 1024,
                              embedding_model="test")
        db.add(ch); db.commit()
        chunk_id = ch.id
    c = admin_client()
    with patch("backend.rag.embeddings.embed_texts", return_value=[[0.5] * 1024]) as mocked:
        r = c.put("/api/admin/referentiels/decoupe/unite", json={
            "cycle_id": cid, "niveau": "DC-NivEdit", "unite_id": chunk_id,
            "texte": "Titre\nRéaliser une pâte"})
    assert r.status_code == 200, r.text
    mocked.assert_called_once()                    # l'empreinte SUIT le texte : recalcul obligatoire
    with dbmod.SessionLocal() as db:
        ch2 = db.get(ReferentielChunk, chunk_id)
        assert ch2.texte == "Titre\nRéaliser une pâte"
        assert abs(float(ch2.embedding[0]) - 0.5) < 1e-6   # la nouvelle empreinte est bien écrite
    assert c.put("/api/admin/referentiels/decoupe/unite", json={
        "cycle_id": cid, "niveau": "DC-NivEdit", "unite_id": 999999, "texte": "x"}).status_code == 404
    assert c.put("/api/admin/referentiels/decoupe/unite", json={
        "cycle_id": cid, "niveau": "DC-NivEdit", "unite_id": chunk_id, "texte": "  "}).status_code == 400


def test_valider_ecrit_le_texte_epure():
    """La validation du dépôt calcule le texte ÉPURÉ UNE SEULE FOIS (porte unique, mockée) et le
    FIGE en base (colonne texte_epure) : le put du principe « épurer une fois au dépôt, lire
    ensuite ». La détection des matières lit CE texte (mockée ici, best-effort)."""
    import shutil as _shutil
    from backend.core.models_db import Referentiel
    cid = _cycle("DC-Epure", 77)
    nid = _niveau(cid, "DC-NivEpure", 77)
    token = _staged_token()
    try:
        with patch("pdfplumber.open") as popen, \
             patch("backend.rag.extraction.extraire_texte", return_value="TEXTE PROPRE DU JOUR"), \
             patch("backend.rag.analyse_amont.detecter_matieres", return_value=[]):
            popen.return_value.__enter__.return_value.pages = [None, None]
            r = admin_client().post("/api/admin/referentiels/valider", json={
                "token": token, "cycle_id": cid, "niveau_id": nid})
        assert r.status_code == 200, r.text
        assert r.json()["pages"] == 2
        with dbmod.SessionLocal() as db:
            ref = db.query(Referentiel).filter(Referentiel.niveau_id == nid).first()
            assert ref is not None
            assert ref.texte_epure == "TEXTE PROPRE DU JOUR"   # figé en base, règles du jour
    finally:
        _purge(token)
        _shutil.rmtree(refadm.REFERENTIELS_DIR / "DC_EPURE", ignore_errors=True)


def test_lire_document_epure():
    """GET /epure (lien « Voir le document épuré ») : get PUR de la colonne texte_epure, figée au
    dépôt — aucun recalcul à l'affichage. 404 si le couple n'a pas de référentiel."""
    from backend.core.models_db import Referentiel
    cid = _cycle("DC-Lect", 78)
    nid = _niveau(cid, "DC-NivLect", 78)
    with dbmod.SessionLocal() as db:
        db.add(Referentiel(niveau_id=nid, matiere_id=None, nom_fixe="dc_lect", collection="dc_lect",
                           filtres=None, fichier="doc.pdf", texte_epure="Un texte de travail propre"))
        db.commit()
    c = admin_client()
    r = c.get(f"/api/admin/referentiels/epure?cycle_id={cid}&niveau=DC-NivLect")
    assert r.status_code == 200, r.text
    assert r.json() == {"texte": "Un texte de travail propre"}
    _niveau(cid, "DC-SansRef", 79)   # niveau sans référentiel → rien à montrer
    assert c.get(f"/api/admin/referentiels/epure?cycle_id={cid}&niveau=DC-SansRef").status_code == 404


def test_decoupe_lit_le_texte_en_base():
    """La découpe lit le texte de travail EN BASE (texte_epure) — plus aucune extraction du PDF :
    le texte passé à l'IA est EXACTEMENT la colonne figée au dépôt (règles de ce jour-là)."""
    from backend.core.models_db import Referentiel
    cid = _cycle("DC-Dec", 80)
    nid = _niveau(cid, "DC-NivDec", 80)
    with dbmod.SessionLocal() as db:
        db.add(Referentiel(niveau_id=nid, matiere_id=None, nom_fixe="dc_dec", collection="dc_dec",
                           filtres=None, fichier="doc.pdf", prompt_decoupe="PROMPT",
                           prompt_decoupe_valide=True, texte_epure="TEXTE FIGE EN BASE"))
        db.commit()
    with patch("backend.rag.analyse_amont.decouper_texte",
               return_value=[{"titre": "T", "texte": "TEXTE FIGE EN BASE"}]) as mocked:
        r = admin_client().post("/api/admin/referentiels/prompt-decoupe/decouper", json={
            "cycle_id": cid, "niveau": "DC-NivDec"})
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 1
    args, _kwargs = mocked.call_args
    assert args[0] == "TEXTE FIGE EN BASE"     # le texte vient de la colonne, pas du PDF


def test_ajouter_type_colle_au_couple():
    """L'ajout d'un type (saisie manuelle) le crée au catalogue (anti-doublon) ET le COLLE au
    couple dans le même geste : liaison active, source='admin', prompt gabarit posé. Une
    suggestion IA (suggestion_ia=true) trace 'ia' sur le type et sur la liaison."""
    from backend.core.models_db import Referentiel, ActiviteType, ReferentielActiviteType
    cid = _cycle("DC-Typ", 81)
    nid = _niveau(cid, "DC-NivTyp", 81)
    with dbmod.SessionLocal() as db:
        db.add(Referentiel(niveau_id=nid, matiere_id=None, nom_fixe="dc_typ", collection="dc_typ",
                           filtres=None, fichier="doc.pdf"))
        db.commit()
    c = admin_client()
    r = c.post("/api/admin/referentiels/types-activite/catalogue", json={
        "label": "Atelier cuisine", "cycle_id": cid, "niveau": "DC-NivTyp"})
    assert r.status_code == 200, r.text
    assert r.json()["deja_present"] is False
    with dbmod.SessionLocal() as db:
        t = db.query(ActiviteType).filter(ActiviteType.label == "Atelier cuisine").first()
        assert t is not None and t.origine == "admin"
        l = (db.query(ReferentielActiviteType)
               .filter(ReferentielActiviteType.activite_type_id == t.id).first())
        assert l is not None and l.actif is True and l.source == "admin"
        assert (l.prompt or "").strip()          # gabarit posé : le type est opérationnel
    r2 = c.post("/api/admin/referentiels/types-activite/catalogue", json={
        "label": "Mise en situation", "cycle_id": cid, "niveau": "DC-NivTyp", "suggestion_ia": True})
    assert r2.status_code == 200, r2.text
    with dbmod.SessionLocal() as db:
        t2 = db.query(ActiviteType).filter(ActiviteType.label == "Mise en situation").first()
        l2 = (db.query(ReferentielActiviteType)
                .filter(ReferentielActiviteType.activite_type_id == t2.id).first())
        assert t2.origine == "ia" and l2.source == "ia"


def test_detecter_types_coche_par_correspondance_avec_prompt():
    """La détection (IA mockée) colle TOUT au couple : un libellé qui correspond au catalogue
    réutilise le type (badge Système·IA à l'écran) ; un libellé inconnu est CRÉÉ au catalogue
    (origine='ia') dans le même geste. Chaque liaison naît active, source='ia', prompt gabarit posé."""
    from backend.core.models_db import Referentiel, ActiviteType, ReferentielActiviteType
    cid = _cycle("DC-Det", 82)
    nid = _niveau(cid, "DC-NivDet", 82)
    with dbmod.SessionLocal() as db:
        db.add(Referentiel(niveau_id=nid, matiere_id=None, nom_fixe="dc_det", collection="dc_det",
                           filtres=None, fichier="doc.pdf", texte_epure="TEXTE DE TRAVAIL"))
        db.add(ActiviteType(label="Évaluation", ordre=1, actif=True, origine="systeme"))
        db.commit()
    with patch("backend.rag.analyse_amont.detecter_types_activite",
               return_value=["Évaluation", "Type inconnu du catalogue"]):
        r = admin_client().post("/api/admin/referentiels/types-activite/detecter", json={
            "cycle_id": cid, "niveau": "DC-NivDet"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert [x["label"] for x in d["coches_ia"]] == ["Évaluation", "Type inconnu du catalogue"]
    assert [x["label"] for x in d["crees"]] == ["Type inconnu du catalogue"]   # créé au catalogue
    with dbmod.SessionLocal() as db:
        nouveau = db.query(ActiviteType).filter(ActiviteType.label == "Type inconnu du catalogue").first()
        assert nouveau is not None and nouveau.origine == "ia" and nouveau.actif is True
        liens = db.query(ReferentielActiviteType).order_by(ReferentielActiviteType.id).all()
        assert len(liens) == 2
        for l in liens:
            assert l.source == "ia" and l.actif is True and (l.prompt or "").strip()


def test_retirer_type_supprime_le_lien_et_la_detection_le_recree():
    """Modèle SIMPLE : le ✕ SUPPRIME le lien couple×type pour de vrai (ses précisions partent en
    cascade — plus rien en base, on n'en parle plus). Une détection ultérieure recrée la ligne si
    l'IA relit le type dans le document (avec prompt gabarit), sans mémoire des retraits passés."""
    from backend.core.models_db import (Referentiel, ActiviteType, ReferentielActiviteType,
                                        ReferentielTypePrecision)
    cid = _cycle("DC-Rel", 83)
    nid = _niveau(cid, "DC-NivRel", 83)
    with dbmod.SessionLocal() as db:
        ref = Referentiel(niveau_id=nid, matiere_id=None, nom_fixe="dc_rel", collection="dc_rel",
                          filtres=None, fichier="doc.pdf", texte_epure="TEXTE")
        t1 = ActiviteType(label="Évaluation", ordre=1, actif=True, origine="systeme")
        db.add_all([ref, t1]); db.flush()
        lien = ReferentielActiviteType(referentiel_id=ref.id, activite_type_id=t1.id,
                                       actif=True, source="ia", prompt="P")
        db.add(lien); db.flush()
        db.add(ReferentielTypePrecision(referentiel_activite_type_id=lien.id,
                                        libelle="évaluation pratique", ordre=0, source="ia"))
        db.commit()
        t1_id = t1.id
    c = admin_client()
    # RETRAIT (✕) : le lien ET sa précision disparaissent de la base.
    r = c.put("/api/admin/referentiels/types-activite", json={
        "cycle_id": cid, "niveau": "DC-NivRel", "activite_type_id": t1_id, "actif": False})
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        assert db.query(ReferentielActiviteType).count() == 0     # supprimé, vraiment
        assert db.query(ReferentielTypePrecision).count() == 0    # précisions parties en cascade
    # DÉTECTION relancée : l'IA relit le type → la ligne se RECRÉE, prompt gabarit posé.
    with patch("backend.rag.analyse_amont.detecter_types_activite", return_value=["Évaluation"]):
        r2 = c.post("/api/admin/referentiels/types-activite/detecter", json={
            "cycle_id": cid, "niveau": "DC-NivRel"})
    assert r2.status_code == 200, r2.text
    assert [x["label"] for x in r2.json()["coches_ia"]] == ["Évaluation"]
    with dbmod.SessionLocal() as db:
        l = db.query(ReferentielActiviteType).first()
        assert l is not None and l.actif is True and (l.prompt or "").strip()


def test_creation_cycle_niveau_relogee():
    c = admin_client()
    r = c.post("/api/admin/cycles", json={"nom": "DC-Nouveau"})
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    assert c.post("/api/admin/cycles", json={"nom": "dc-nouveau"}).status_code == 409       # unicité (casse ignorée)
    r2 = c.post("/api/admin/niveaux", json={"cycle_id": cid, "nom": "DC-Spécialité"})
    assert r2.status_code == 200, r2.text
    assert c.post("/api/admin/niveaux", json={"cycle_id": cid, "nom": "dc-spécialité"}).status_code == 409
    assert c.post("/api/admin/niveaux", json={"cycle_id": 999999, "nom": "X"}).status_code == 404


def test_valider_jeton_consomme_avec_referentiel_dit_deja_valide():
    """Reclic après une validation qui a ABOUTI (jeton consommé, référentiel en base) : le serveur
    répond la VÉRITÉ — succès `deja_valide` (l'écran se resynchronise) — au lieu du mensonge
    « aperçu expiré ? » (cas réel du 24/07 : validation ~3 min > patience de l'écran, reclics)."""
    from backend.core.models_db import Referentiel
    cid = _cycle("DC-Deja", 86)
    nid = _niveau(cid, "DC-NivDeja", 86)
    with dbmod.SessionLocal() as db:
        db.add(Referentiel(niveau_id=nid, matiere_id=None, nom_fixe="dc_deja", collection="dc_deja",
                           filtres=None, fichier="mon-document.pdf"))
        db.commit()
    r = admin_client().post("/api/admin/referentiels/valider", json={
        "token": "jeton-consomme-inexistant", "cycle_id": cid, "niveau_id": nid})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ok"] is True and d["deja_valide"] is True
    assert d["niveau"] == "DC-NivDeja" and d["fichier_origine"] == "mon-document.pdf"


def test_valider_jeton_consomme_sans_referentiel_400_message_honnete():
    """Jeton absent ET aucun référentiel pour le couple : vrai échec — message clair (« recommencez
    le dépôt »), plus jamais le « aperçu expiré ? » fictif (rien n'expire dans la zone d'attente)."""
    cid = _cycle("DC-Sans", 87)
    nid = _niveau(cid, "DC-NivSans", 87)
    r = admin_client().post("/api/admin/referentiels/valider", json={
        "token": "jeton-inexistant", "cycle_id": cid, "niveau_id": nid})
    assert r.status_code == 400, r.text
    assert "Recommencez le dépôt" in r.json()["detail"]
    assert "expiré" not in r.json()["detail"]


def test_page_contenu_arbre_complet():
    """GET /admin/contenu = l'arbre COMPLET en une lecture : cycle → niveau → référentiel du couple
    (états lus, unités comptées), matières du programme, types liés avec les précisions du couple.
    Un niveau SANS référentiel apparaît quand même (referentiel: null) — l'admin voit le « à remplir »."""
    from backend.core.models_db import (Referentiel, ReferentielChunk, Matiere, MatiereNiveau,
                                        ActiviteType, ReferentielActiviteType, ReferentielTypePrecision)
    cid = _cycle("DC-Cont", 84)
    nid = _niveau(cid, "DC-NivCont", 84)
    nid_vide = _niveau(cid, "DC-NivVide", 85)
    with dbmod.SessionLocal() as db:
        m = Matiere(nom="DC-Cuisine", ordre=1, actif=True)
        db.add(m); db.flush()
        db.add(MatiereNiveau(matiere_id=m.id, niveau_id=nid, actif=True))
        ref = Referentiel(niveau_id=nid, matiere_id=None, nom_fixe="dc_cont", collection="dc_cont",
                          filtres=None, fichier="doc.pdf", source="education.gouv.fr",
                          texte_epure="TEXTE FIGE", decoupe_valide=True)
        t1 = ActiviteType(label="DC-Évaluation", ordre=1, actif=True, origine="systeme")
        db.add_all([ref, t1]); db.flush()
        db.add(ReferentielChunk(referentiel_id=ref.id, chunk_index=0, option_ab="", page=1,
                                texte="Unité 1", embedding=[0.0] * 1024, embedding_model="test"))
        lien = ReferentielActiviteType(referentiel_id=ref.id, activite_type_id=t1.id,
                                       actif=True, source="ia", prompt="P")
        db.add(lien); db.flush()
        db.add(ReferentielTypePrecision(referentiel_activite_type_id=lien.id,
                                        libelle="évaluation pratique", ordre=0, source="ia"))
        db.commit()

    r = admin_client().get("/api/admin/contenu")
    assert r.status_code == 200, r.text
    cycle = next(c for c in r.json()["cycles"] if c["id"] == cid)
    assert cycle["nom"] == "DC-Cont"
    par_nom = {n["nom"]: n for n in cycle["niveaux"]}

    plein = par_nom["DC-NivCont"]
    assert plein["referentiel"] == {"fichier": "doc.pdf", "source": "education.gouv.fr",
                                    "date_doc": None, "epure": True, "decoupe_valide": True,
                                    "nb_unites": 1}
    assert [m["nom"] for m in plein["matieres"]] == ["DC-Cuisine"]
    assert plein["types"] == [{"id": plein["types"][0]["id"], "label": "DC-Évaluation",
                               "source": "ia", "origine": "systeme",
                               "precisions": ["évaluation pratique"]}]

    vide = par_nom["DC-NivVide"]
    assert vide["referentiel"] is None      # le niveau sans dépôt reste VISIBLE : à remplir
    assert vide["matieres"] == [] and vide["types"] == []
