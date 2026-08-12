"""Chantier « suppression des familles » — le dépôt en couple cycle → niveau.

Ce que ces tests verrouillent :
  - le dépôt (`valider-flux`) exige un niveau EXISTANT (`niveau_id`) : refus si inconnu ou hors
    du cycle, et il ne crée JAMAIS de niveau (une seule place pour créer : POST /admin/niveaux).
  - les endpoints famille ont disparu (404).
  - la création cycle/niveau est relogée dans programmes.py (unicité 409, cycle inconnu 404).

BDD de test PostgreSQL dédiée (aschool_test via conftest.py), IA et texte du PDF mockés.

Lancer : docker compose exec backend python -m pytest tests/test_depot_couple.py -q
"""
import os
import uuid
from unittest.mock import patch


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


def _deposer(client, corps):
    """Le dépôt par `/valider-flux`, rendu comme une réponse ordinaire.

    La route ne rend plus un objet mais un flux NDJSON : une ligne par tâche terminée, puis
    `{"fin": …}` ou `{"erreur": …}`. Le refus n'a donc plus de code HTTP propre — il arrive
    DANS le flux, en 200, parce qu'au moment où il survient les en-têtes sont déjà partis.
    Ce lecteur rend `(fin, erreur)` : le test assure sur le message, plus sur le code.

    Il a remplacé `/admin/referentiels/verifier` le 10/08/2026 — même dépôt, même code de fond
    (`_enregistrer_referentiel`), mais cette porte-là n'était plus appelée par aucun écran."""
    import json
    r = client.post("/api/admin/referentiels/valider-flux", json=corps)
    assert r.status_code == 200, r.text
    fin = erreur = None
    for ligne in r.text.splitlines():
        if not ligne.strip():
            continue
        d = json.loads(ligne)
        if "fin" in d:
            fin = d["fin"]
        elif "erreur" in d:
            erreur = d["erreur"]
    return fin, erreur



def _purge(token):
    (refadm.STAGING_DIR / f"{token}.pdf").unlink(missing_ok=True)


def test_valider_niveau_inconnu_404_et_ne_cree_jamais_de_niveau():
    from backend.core.models_db import Niveau
    cid = _cycle()
    token = _staged_token()
    try:
        _fin, erreur = _deposer(admin_client(), {
            "token": token, "cycle_id": cid, "niveau_id": 999999})
        assert erreur and "niveau" in erreur.lower(), erreur
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
        _fin, erreur = _deposer(admin_client(), {
            "token": token, "cycle_id": cid, "niveau_id": nid})
        assert erreur and "niveau" in erreur.lower(), erreur
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
        ref = Referentiel(niveau_id=nid, nom_fixe="dc_edit", collection="dc_edit",
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
            fin, erreur = _deposer(admin_client(), {
                "token": token, "cycle_id": cid, "niveau_id": nid})
        assert erreur is None, erreur
        assert fin["pages"] == 2
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
        db.add(Referentiel(niveau_id=nid, nom_fixe="dc_lect", collection="dc_lect",
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
        # Le prompt de découpe vit sur le RÉFÉRENTIEL (06/08/2026) : posé là, aucune rédaction IA
        # n'est déclenchée et la découpe part directement.
        db.add(Referentiel(niveau_id=nid, nom_fixe="dc_dec", collection="dc_dec",
                           filtres=None, fichier="doc.pdf", texte_epure="TEXTE FIGE EN BASE",
                           prompt_decoupe="PROMPT {texte}", prompt_decoupe_valide=True))
        db.commit()
    with patch("backend.rag.analyse_amont.decouper_texte",
               return_value=[{"titre": "T", "texte": "TEXTE FIGE EN BASE"}]) as mocked:
        r = admin_client().post("/api/admin/referentiels/prompt-decoupe/decouper", json={
            "cycle_id": cid, "niveau": "DC-NivDec"})
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 1
    args, _kwargs = mocked.call_args
    assert args[0] == "TEXTE FIGE EN BASE"     # le texte vient de la colonne, pas du PDF


def test_ajouter_type_le_cree_dans_le_referentiel():
    """L'ajout MANUEL d'un type le crée DANS le référentiel du couple : origine 'admin', RETENU
    d'emblée (l'admin n'a pas à se proposer ce qu'il vient d'écrire), prompt gabarit posé.
    Anti-doublon par libellé DANS ce référentiel. Rien n'est écrit hors de ce document."""
    from backend.core.models_db import Referentiel, ActiviteType
    cid = _cycle("DC-Typ", 81)
    nid = _niveau(cid, "DC-NivTyp", 81)
    with dbmod.SessionLocal() as db:
        db.add(Referentiel(niveau_id=nid, nom_fixe="dc_typ", collection="dc_typ",
                           filtres=None, fichier="doc.pdf"))
        db.commit()
    c = admin_client()
    r = c.post("/api/admin/referentiels/types-activite", json={
        "label": "Atelier cuisine", "cycle_id": cid, "niveau": "DC-NivTyp"})
    assert r.status_code == 200, r.text
    assert r.json()["deja_present"] is False
    with dbmod.SessionLocal() as db:
        ref = db.query(Referentiel).filter(Referentiel.niveau_id == nid).one()
        t = (db.query(ActiviteType)
               .filter(ActiviteType.referentiel_id == ref.id,
                       ActiviteType.label == "Atelier cuisine").first())
        assert t is not None and t.origine == "admin"
        assert t.validee is True and t.actif is True
        assert (t.prompt or "").strip()          # gabarit posé : le type est opérationnel
    # Deuxieme fois, meme libelle : la ligne existante est renvoyee, jamais un sosie.
    r2 = c.post("/api/admin/referentiels/types-activite", json={
        "label": "atelier CUISINE", "cycle_id": cid, "niveau": "DC-NivTyp"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["deja_present"] is True
    with dbmod.SessionLocal() as db:
        ref = db.query(Referentiel).filter(Referentiel.niveau_id == nid).one()
        assert db.query(ActiviteType).filter(ActiviteType.referentiel_id == ref.id).count() == 1


def test_detecter_types_propose_dans_le_referentiel():
    """La détection (IA mockée) écrit les types DANS le référentiel, NON RETENUS : ce sont des
    propositions, l'admin garde ce qu'il veut. Un type déjà présent est laissé tel quel (jamais
    de doublon). Chaque ligne naît origine='ia', avec son prompt gabarit."""
    from backend.core.models_db import Cycle, Referentiel, ActiviteType
    cid = _cycle("DC-Det", 82)
    nid = _niveau(cid, "DC-NivDet", 82)
    with dbmod.SessionLocal() as db:
        ref = Referentiel(niveau_id=nid, nom_fixe="dc_det", collection="dc_det",
                          filtres=None, fichier="doc.pdf", texte_epure="TEXTE DE TRAVAIL")
        db.add(ref); db.flush()
        # Type DEJA present dans CE referentiel (l'admin l'avait retenu).
        db.add(ActiviteType(referentiel_id=ref.id, label="Évaluation", ordre=1, actif=True,
                            validee=True, origine="admin", prompt="P {texte} {referentiel}"))
        # Le prompt de types du cycle existe : la detection ne le fait pas ecrire par l'IA.
        db.get(Cycle, cid).prompt_types = "Lis {texte}."
        db.commit()
    with patch("backend.rag.analyse_amont.detecter_types_activite",
               return_value=["Évaluation", "Type que le document nomme"]):
        r = admin_client().post("/api/admin/referentiels/types-activite/detecter", json={
            "cycle_id": cid, "niveau": "DC-NivDet"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert [x["label"] for x in d["proposes"]] == ["Type que le document nomme"]
    assert [x["label"] for x in d["deja_presents"]] == ["Évaluation"]
    with dbmod.SessionLocal() as db:
        ref = db.query(Referentiel).filter(Referentiel.niveau_id == nid).one()
        nouveau = (db.query(ActiviteType)
                     .filter(ActiviteType.referentiel_id == ref.id,
                             ActiviteType.label == "Type que le document nomme").first())
        assert nouveau is not None and nouveau.origine == "ia" and nouveau.actif is True
        assert nouveau.validee is False, "Un type détecté ne doit jamais être retenu d'office."
        assert (nouveau.prompt or "").strip()
        # Le type deja retenu n'a pas bouge.
        deja = (db.query(ActiviteType)
                  .filter(ActiviteType.referentiel_id == ref.id,
                          ActiviteType.label == "Évaluation").one())
        assert deja.validee is True and deja.origine == "admin"


def test_supprimer_type_efface_vraiment_et_la_detection_le_recree():
    """Le ✕ SUPPRIME le type du référentiel pour de vrai (ses précisions partent en cascade —
    plus rien en base, on n'en parle plus). Une détection ultérieure le recrée si l'IA le relit
    dans le document, sans mémoire des retraits passés — mais en PROPOSITION."""
    from backend.core.models_db import (Cycle, Referentiel, ActiviteType,
                                        ReferentielTypePrecision)
    cid = _cycle("DC-Rel", 83)
    nid = _niveau(cid, "DC-NivRel", 83)
    with dbmod.SessionLocal() as db:
        ref = Referentiel(niveau_id=nid, nom_fixe="dc_rel", collection="dc_rel",
                          filtres=None, fichier="doc.pdf", texte_epure="TEXTE")
        db.add(ref); db.flush()
        t1 = ActiviteType(referentiel_id=ref.id, label="Évaluation", ordre=1, actif=True,
                          validee=True, origine="ia", prompt="P {texte} {referentiel}")
        db.add(t1); db.flush()
        db.add(ReferentielTypePrecision(type_activite_id=t1.id,
                                        libelle="évaluation pratique", ordre=0, source="ia"))
        db.get(Cycle, cid).prompt_types = "Lis {texte}."
        db.commit()
        t1_id = t1.id
        ref_id = ref.id
    c = admin_client()
    # SUPPRESSION (✕) : le type ET sa précision disparaissent de la base.
    r = c.delete(f"/api/admin/referentiels/types-activite/{t1_id}"
                 f"?cycle_id={cid}&niveau=DC-NivRel")
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        assert db.query(ActiviteType).filter(
            ActiviteType.referentiel_id == ref_id).count() == 0     # supprimé, vraiment
        assert db.query(ReferentielTypePrecision).filter(
            ReferentielTypePrecision.type_activite_id == t1_id).count() == 0   # cascade
    # DÉTECTION relancée : l'IA relit le type → la ligne se RECRÉE, en proposition.
    with patch("backend.rag.analyse_amont.detecter_types_activite", return_value=["Évaluation"]):
        r2 = c.post("/api/admin/referentiels/types-activite/detecter", json={
            "cycle_id": cid, "niveau": "DC-NivRel"})
    assert r2.status_code == 200, r2.text
    assert [x["label"] for x in r2.json()["proposes"]] == ["Évaluation"]
    with dbmod.SessionLocal() as db:
        t = db.query(ActiviteType).filter(ActiviteType.referentiel_id == ref_id).one()
        assert t.actif is True and t.validee is False and (t.prompt or "").strip()


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
        db.add(Referentiel(niveau_id=nid, nom_fixe="dc_deja", collection="dc_deja",
                           filtres=None, fichier="mon-document.pdf"))
        db.commit()
    d, erreur = _deposer(admin_client(), {
        "token": "jeton-consomme-inexistant", "cycle_id": cid, "niveau_id": nid})
    assert erreur is None, erreur
    assert d["ok"] is True and d["deja_valide"] is True
    assert d["niveau"] == "DC-NivDeja" and d["fichier_origine"] == "mon-document.pdf"


def test_valider_jeton_consomme_sans_referentiel_400_message_honnete():
    """Jeton absent ET aucun référentiel pour le couple : vrai échec — message clair (« recommencez
    le dépôt »), plus jamais le « aperçu expiré ? » fictif (rien n'expire dans la zone d'attente)."""
    cid = _cycle("DC-Sans", 87)
    nid = _niveau(cid, "DC-NivSans", 87)
    _fin, erreur = _deposer(admin_client(), {
        "token": "jeton-inexistant", "cycle_id": cid, "niveau_id": nid})
    assert erreur and "Recommencez le dépôt" in erreur, erreur
    assert "expiré" not in erreur


def test_detecter_couple_ia_meme_patron():
    """detecter_couple (analyse_amont) : prompt seedé au catalogue (get_prompt), arbre des cycles →
    niveaux EXISTANTS injecté dans le prompt, retour nettoyé (strip) — même patron que les matières."""
    from backend.rag import analyse_amont as am
    cid = _cycle("DC-Arb", 92)
    _niveau(cid, "DC-NivArb", 92)
    with dbmod.SessionLocal() as db:
        with patch.object(am, "generate",
                          return_value='{"cycle_lu": " DC-Arb ", "niveau_lu": " DC-NivArb "}') as g:
            out = am.detecter_couple("TEXTE-DU-DOCUMENT", db=db)
    assert out == {"cycle_lu": "DC-Arb", "niveau_lu": "DC-NivArb"}
    prompt_envoye = g.call_args[0][0]
    assert "- DC-Arb : DC-NivArb" in prompt_envoye    # l'arbre existant est bien injecté
    assert "TEXTE-DU-DOCUMENT" in prompt_envoye       # le texte du document aussi


def test_depot_nettoie_les_apercus_abandonnes():
    """La zone d'attente est TRANSITOIRE : chaque nouveau dépôt supprime les aperçus abandonnés
    plus vieux que le TTL (`staging_ttl_heures` en base, défaut 24 h) ; un aperçu récent survit.
    Constat d'origine (24/07) : 33 PDF / 202 Mo accumulés depuis le 13/07, jamais nettoyés."""
    import time as _time
    vieux = refadm.STAGING_DIR / "test-vieux-abandonne.pdf"
    recent = refadm.STAGING_DIR / "test-recent-en-cours.pdf"
    vieux.write_bytes(b"%PDF-fake")
    recent.write_bytes(b"%PDF-fake")
    ts = _time.time() - 25 * 3600                      # 25 h > TTL par défaut (24 h)
    os.utime(vieux, (ts, ts))
    token = None
    try:
        with patch.object(refadm, "_apercu", return_value=(1, "aperçu")):
            r = admin_client().post("/api/admin/referentiels/preparer-depot",
                                    files={"file": ("doc.pdf", b"%PDF-nouveau", "application/pdf")})
        assert r.status_code == 200, r.text
        token = r.json()["token"]
        assert not vieux.exists()                      # l'abandonné (25 h) est parti
        assert recent.exists()                         # le récent survit (son aperçu peut être ouvert)
    finally:
        vieux.unlink(missing_ok=True)
        recent.unlink(missing_ok=True)
        if token:
            _purge(token)


def test_enregistrer_matiere_longue_passe_et_trop_longue_422():
    """Cas réel du 24/07 : « Conception et réalisation d'orthèses temporaires et d'aides
    techniques » (70 car.) explosait contre VARCHAR(64) en 500 brut à l'écran. La colonne passe
    à 255 ; au-delà, refus 422 en langage humain — jamais un « Internal Server Error »."""
    from backend.core.models_db import Matiere, Referentiel
    cid = _cycle("DC-Long", 88)
    nid = _niveau(cid, "DC-NivLong", 88)
    with dbmod.SessionLocal() as db:      # la matière vit dans le référentiel du niveau
        db.add(Referentiel(niveau_id=nid, nom_fixe="dc_long", collection="dc_long",
                           fichier="doc.pdf", texte_epure="TEXTE"))
        db.commit()
    c = admin_client()
    long70 = "Conception et réalisation d'orthèses temporaires et d'aides techniques"
    r = c.post("/api/admin/referentiels/matieres", json={
        "cycle_id": cid, "niveau": "DC-NivLong", "matieres": [long70]})
    assert r.status_code == 200, r.text
    assert r.json()["nb_ajoutees"] == 1
    with dbmod.SessionLocal() as db:
        mat = db.query(Matiere).filter(Matiere.nom == long70).first()
        assert mat is not None                     # les 70 caractères sont EN BASE, intacts
        mat_id = mat.id
    trop = "X" * 256
    r2 = c.post("/api/admin/referentiels/matieres", json={
        "cycle_id": cid, "niveau": "DC-NivLong", "matieres": [trop]})
    assert r2.status_code == 422, r2.text
    assert "trop long" in r2.json()["detail"]      # message humain, pas de 500 brut
    # Même garde au renommage (l'autre seul endroit qui écrit matieres.nom).
    r3 = c.patch("/api/admin/referentiels/matiere", json={
        "matiere_id": mat_id, "nouveau_nom": trop})
    assert r3.status_code == 422, r3.text


def test_page_contenu_arbre_complet():
    """GET /admin/contenu = l'arbre COMPLET en UNE lecture : cycle → niveau → référentiel du couple
    (états lus, unités comptées), matières de CE référentiel avec leur état, types liés avec les
    précisions du couple. Un niveau SANS référentiel apparaît quand même (referentiel et
    referentiel_id à null) — l'admin voit le « à remplir ».

    C'est la lecture unique de la page « Formations » : elle en faisait deux et les
    recollait. L'arbre porte donc TOUTES les matières du référentiel, y compris celles que le prof
    ne voit pas — retirée du programme (actif=false) ou seulement proposée (validee=false) — et
    l'id du référentiel, qu'il faut pour y créer une matière."""
    from backend.core.models_db import (Referentiel, ReferentielChunk, Matiere,
                                        ActiviteType, ReferentielTypePrecision)
    cid = _cycle("DC-Cont", 84)
    nid = _niveau(cid, "DC-NivCont", 84)
    nid_vide = _niveau(cid, "DC-NivVide", 85)
    with dbmod.SessionLocal() as db:
        ref = Referentiel(niveau_id=nid, nom_fixe="dc_cont", collection="dc_cont",
                          filtres=None, fichier="doc.pdf", source="education.gouv.fr",
                          texte_epure="TEXTE FIGE", decoupe_valide=True)
        db.add(ref); db.flush()
        t1 = ActiviteType(referentiel_id=ref.id, label="DC-Évaluation", ordre=1, actif=True,
                          validee=True, origine="ia", prompt="P")
        db.add(t1); db.flush()
        db.add(Matiere(referentiel_id=ref.id, nom="DC-Cuisine", ordre=1, actif=True, validee=True,
                       demande_langue=True))
        db.add(Matiere(referentiel_id=ref.id, nom="DC-Retiree", ordre=2, actif=False, validee=True))
        db.add(Matiere(referentiel_id=ref.id, nom="DC-Proposee", ordre=3, actif=True, validee=False))
        db.add(ReferentielChunk(referentiel_id=ref.id, chunk_index=0, option_ab="", page=1,
                                texte="Unité 1", embedding=[0.0] * 1024, embedding_model="test"))

        db.add(ReferentielTypePrecision(type_activite_id=t1.id,
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
    assert plein["referentiel_id"] is not None      # l'id qu'il faut pour y créer une matière
    # Les TROIS matières du référentiel sont là, chacune avec son état : l'admin gère ici ce que
    # le prof ne voit pas. Filtrer les inactives priverait l'écran du bouton « remettre ».
    etats = {m["nom"]: (m["validee"], m["actif"]) for m in plein["matieres"]}
    assert etats == {"DC-Cuisine": (True, True),      # au programme
                     "DC-Retiree": (True, False),     # retirée du programme, jamais supprimée
                     "DC-Proposee": (False, True)}    # lue dans le document, pas encore retenue
    # `demande_langue` voyage avec la matière : c'est LUI qui fait apparaître le choix de la
    # langue au profil du prof, et la case qui le règle est sur cet écran-là.
    langue = {m["nom"]: m["demande_langue"] for m in plein["matieres"]}
    assert langue == {"DC-Cuisine": True, "DC-Retiree": False, "DC-Proposee": False}
    assert plein["types"] == [{"id": plein["types"][0]["id"], "label": "DC-Évaluation",
                               "validee": True, "actif": True, "origine": "ia",
                               "precisions": ["évaluation pratique"]}]

    vide = par_nom["DC-NivVide"]
    assert vide["referentiel"] is None      # le niveau sans dépôt reste VISIBLE : à remplir
    assert vide["referentiel_id"] is None   # rien à adresser : pas de champ « + Matière » à l'écran
    assert vide["matieres"] == [] and vide["types"] == []


# ── Épuration : les en-têtes et pieds de page ───────────────────────────────────────────────
#
# Le bandeau répété en haut ou en bas des pages est collé au fil du texte par l'extraction, et
# le saut de page tombe souvent AU MILIEU d'une phrase : « Référentiel maison aSchool — en
# service, sans valeur institutionnelle » s'est ainsi retrouvé planté au beau milieu d'une fiche
# d'activité du référentiel crèche, où le modèle l'a lu comme du contenu.
#
# Ce que ces tests PROUVENT — et surtout ce qu'ils PROTÈGENT : la répétition seule ne suffit pas
# à condamner une ligne. Sur le BTS CIEL, « Face à un ensemble de faits, des actions appropriées »
# revient sur douze pages, et « Pôle « VALORISATION DE LA DONNÉE ET CYBERSÉCURITÉ » » sur cinq —
# ce sont du contenu, et le second porte le rattachement des unités qui le suivent.

HAUTEUR = 842.0     # A4 en points, comme les référentiels en service


def _ligne(texte: str, pourcent: float) -> dict:
    return {"text": texte, "top": HAUTEUR * pourcent / 100.0}


def test_le_bandeau_repete_dans_la_marge_est_retire():
    from backend.rag.extraction import _sans_bandeaux

    pages = [[_ligne("Référentiel d'éveil 0-3 ans — aSchool", 5.5),
              _ligne(f"Contenu propre de la page {i}", 40.0),
              _ligne("Référentiel maison aSchool — sans valeur institutionnelle", 95.6)]
             for i in range(4)]

    propres = _sans_bandeaux(pages, HAUTEUR)
    assert all("aSchool" not in p for p in propres)
    assert propres[0] == "Contenu propre de la page 0"


def test_une_phrase_qui_se_repete_dans_le_texte_n_est_pas_un_bandeau():
    """Elle coule avec le texte : sa hauteur change à chaque page. C'est ce qui la sauve."""
    from backend.rag.extraction import _sans_bandeaux

    pages = [[_ligne("− Face à un ensemble de faits, des actions appropriées", h)]
             for h in (57.1, 80.9, 77.8, 82.9, 66.7)]

    assert all("Face à un ensemble" in p for p in _sans_bandeaux(pages, HAUTEUR))


def test_un_titre_de_section_repete_juste_sous_la_marge_est_garde():
    """« Pôle « VALORISATION… » » vit à 7,9 % : hors marge, donc hors de portée de la règle.
    Il porte le rattachement des unités qui le suivent — le perdre coûterait plus cher qu'un
    bandeau oublié."""
    from backend.rag.extraction import _sans_bandeaux

    pages = [[_ligne("Pôle « VALORISATION DE LA DONNÉE ET CYBERSÉCURITÉ »", 7.9)] for _ in range(5)]
    assert all("VALORISATION" in p for p in _sans_bandeaux(pages, HAUTEUR))


def test_deux_pages_ne_font_pas_un_bandeau():
    """Deux pourraient être une coïncidence de mise en page ; trois, non."""
    from backend.rag.extraction import _sans_bandeaux

    pages = [[_ligne("Peut-être un bandeau", 96.0)] for _ in range(2)]
    assert all("Peut-être" in p for p in _sans_bandeaux(pages, HAUTEUR))


def test_le_pied_qui_porte_son_numero_de_page_est_reconnu_quand_meme():
    """« …, Page170. » change à chaque page : sans neutraliser les nombres, un pied sur deux ne
    se reconnaîtrait jamais lui-même (cas réel, référentiel Ergothérapie)."""
    from backend.rag.extraction import _sans_bandeaux

    pages = [[_ligne("Contenu", 40.0),
              _ligne(f"BO Santé – Solidarité no2010/7 du 15 août 2010, Page{170 + i}.", 94.5)]
             for i in range(4)]

    propres = _sans_bandeaux(pages, HAUTEUR)
    assert all("BO Santé" not in p for p in propres)
    assert all("Contenu" in p for p in propres)


def test_la_regle_est_annoncee_a_l_admin():
    """L'écran admin liste les règles d'épuration : une règle qui agit sans être écrite là
    serait une transformation invisible du document déposé."""
    from backend.rag.extraction import REGLES_EPURATION

    assert any("En-têtes et pieds" in r["nom"] for r in REGLES_EPURATION)
