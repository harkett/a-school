"""LABO — la procédure « Référentiels » reconstruite, sur SON back.

Ces tests ne visent QUE `backend/pedagogie/referentiels_labo.py` et ses routes
`/api/admin/labo/referentiels/…`. L'écran historique (`referentiels_admin.py`) a les siens
ailleurs et n'est jamais appelé ici : c'est tout l'intérêt du labo — ce qu'on corrige d'un côté
ne peut pas déplacer l'autre.

Ce qu'ils verrouillent, dans l'ordre des étapes déjà reconstruites :
  1. LE COUPLE D'ABORD : le dépôt exige cycle + niveau, et refuse un couple inconnu ;
  2. le document va DIRECTEMENT à sa place et sa ligne `referentiel_documents` naît avec lui —
     plus de zone d'attente, plus de jeton, plus rien à balayer ;
  3. UN RÉFÉRENTIEL TIENT PARFOIS EN PLUSIEURS PDF : on empile, on ordonne, on retire, et c'est la
     FUSION qui clôture — elle seule fabrique `referentiel.pdf` et crée la fiche `referentiels` ;
  4. un couple déjà servi refuse le dépôt (on supprime d'abord), un dépôt refusé ne laisse rien ;
  5. un document DÉJÀ CONNU est reconnu sur son CONTENU (SHA-256), jamais sur son nom ;
  6. la suppression d'un référentiel : ce qui part est compté en base, elle emporte les morceaux,
     et le refus « des profs travaillent dessus » reste la règle.

BDD de test PostgreSQL dédiée (aschool_test via conftest.py), texte du PDF mocké.

Lancer : docker compose exec backend python -m pytest tests/test_labo_referentiels.py -q
"""
import hashlib
import shutil
from unittest.mock import patch

import backend.core.database as dbmod
import backend.pedagogie.referentiels_labo as reflabo
from backend.core.models_db import Referentiel, ReferentielDocument
from backend.main import app
from fastapi.testclient import TestClient


def admin_client():
    from backend.systeme.admin import _make_admin_token
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _cycle(nom="LB-Cycle", ordre=80):
    from backend.core.models_db import Cycle
    with dbmod.SessionLocal() as db:
        c = Cycle(nom=nom, ordre=ordre)
        db.add(c); db.commit(); db.refresh(c)
        return c.id


def _niveau(cycle_id, nom="LB-Niv", ordre=80):
    from backend.core.models_db import Niveau
    with dbmod.SessionLocal() as db:
        n = Niveau(cycle_id=cycle_id, nom=nom, ordre=ordre)
        db.add(n); db.commit(); db.refresh(n)
        return n.id


def _effacer(cycle):
    """Le labo range pour de vrai : les tests effacent le dossier du cycle qu'ils ont créé."""
    shutil.rmtree(reflabo.REFERENTIELS_DIR / _dossier(cycle), ignore_errors=True)


def _dossier(nom):
    from backend.core.nommage import dossier_cle
    return dossier_cle(nom)


# ── Étape 1 — déposer le document ────────────────────────────────────────────

def _fusion_bidon(db, cycle, niveau, documents, max_pages, destination):
    """Remplace l'IA dans les tests : ni appel au fournisseur, ni écriture PDF réelle (les
    contenus factices « %PDF-… » ne sont pas de vrais PDF). Ce qui se vérifie ici, c'est la
    plomberie autour — l'ORDRE des documents, l'empreinte du PRODUIT, la fiche, les rattachements.
    Le fusionné porte donc la trace des morceaux, dans l'ordre, à la lettre."""
    destination.write_bytes(b"%PDF-" + b"+".join(c.read_bytes() for _, c in documents))


def _constituer(cid, nid):
    """La constitution du référentiel, appelée comme l'écran le fait — c'est elle qui crée la
    fiche du couple. L'IA est TOUJOURS remplacée ici : aucun test n'appelle le fournisseur."""
    with patch.object(reflabo, "_fusionner_par_ia", side_effect=_fusion_bidon), \
         patch.object(reflabo, "_apercu", return_value=(4, "aperçu du référentiel")):
        return admin_client().post("/api/admin/labo/referentiels/constituer",
                                   json={"cycle_id": cid, "niveau_id": nid})


def test_le_depot_range_le_document_et_ecrit_sa_ligne():
    """Le couple étant donné, la place du document l'est aussi : il va DIRECTEMENT dans
    REFERENTIELS/<CYCLE>/<NIVEAU>/, sous un nom de disque à lui, et sa ligne
    `referentiel_documents` naît avec lui.

    Mais le dépôt NE CLÔTURE RIEN : pas de `referentiel.pdf`, pas de fiche `referentiels`. Un
    référentiel peut tenir en plusieurs PDF — c'est la fusion qui décide que c'est fini."""
    cid = _cycle("LB-Depot", 90)
    nid = _niveau(cid, "LB-NivDepot", 90)
    try:
        with patch.object(reflabo, "_apercu", return_value=(3, "les 25 lignes")):
            r = admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                                    data={"cycle_id": cid, "niveau_id": nid},
                                    files={"file": ("Le vrai nom.pdf", b"%PDF-reel", "application/pdf")})
        assert r.status_code == 200, r.text
        d = r.json()
        assert (d["cycle"], d["niveau"], d["filename"]) == ("LB-Depot", "LB-NivDepot", "Le vrai nom.pdf")
        assert d["pages"] == 3 and d["apercu"] == "les 25 lignes" and d["deja"] is None
        assert [x["fichier"] for x in d["documents"]] == ["Le vrai nom.pdf"]
        assert d["total_pages"] == 3

        dossier = reflabo.REFERENTIELS_DIR / "LB_DEPOT" / "LB_NIVDEPOT"
        deposes = list(dossier.glob("doc-*.pdf"))
        assert len(deposes) == 1 and deposes[0].read_bytes() == b"%PDF-reel"
        assert not list(dossier.glob("*.depot"))          # aucun fichier de travail oublié
        assert not (dossier / "referentiel.pdf").exists()  # RIEN n'est clôturé
        with dbmod.SessionLocal() as db:
            doc = db.query(ReferentielDocument).filter(ReferentielDocument.niveau_id == nid).one()
            assert doc.fichier_origine == "Le vrai nom.pdf"   # le nom D'ORIGINE
            assert doc.fichier_disque == deposes[0].name      # ≠ le nom sur le disque
            assert doc.ordre == 0 and doc.pages == 3 and doc.source == "depot"
            assert doc.referentiel_id is None                 # pas encore fusionné
            assert doc.empreinte == hashlib.sha256(b"%PDF-reel").hexdigest()
            assert db.query(Referentiel).filter(Referentiel.niveau_id == nid).count() == 0
    finally:
        _effacer("LB-Depot")


def test_la_fusion_cree_le_referentiel_et_rattache_ses_morceaux():
    """Le geste qui clôture : les documents sont assemblés DANS L'ORDRE, l'empreinte est celle du
    FUSIONNÉ (pas d'un morceau), la fiche naît, et les morceaux lui sont rattachés — on saura
    toujours de quoi le référentiel est fait."""
    cid = _cycle("LB-Fusion", 60)
    nid = _niveau(cid, "LB-NivFusion", 60)
    try:
        with patch.object(reflabo, "_apercu", return_value=(2, "aperçu")):
            for nom, contenu in [("un.pdf", b"%PDF-un"), ("deux.pdf", b"%PDF-deux")]:
                assert admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                                           data={"cycle_id": cid, "niveau_id": nid},
                                           files={"file": (nom, contenu, "application/pdf")}
                                           ).status_code == 200
        r = _constituer(cid,nid)
        assert r.status_code == 200, r.text
        assert r.json()["documents"] == 2 and r.json()["pages"] == 4

        attendu = b"%PDF-" + b"%PDF-un" + b"+" + b"%PDF-deux"
        fusionne = reflabo.REFERENTIELS_DIR / "LB_FUSION" / "LB_NIVFUSION" / "referentiel.pdf"
        assert fusionne.read_bytes() == attendu          # l'ordre des dépôts est respecté
        assert not list(fusionne.parent.glob("*.travail"))
        assert len(list(fusionne.parent.glob("doc-*.pdf"))) == 2   # les morceaux survivent
        with dbmod.SessionLocal() as db:
            ref = db.query(Referentiel).filter(Referentiel.niveau_id == nid).one()
            assert ref.empreinte == hashlib.sha256(attendu).hexdigest()
            assert ref.nom_fixe == "lb_nivfusion" and ref.collection == "lb_nivfusion"
            docs = db.query(ReferentielDocument).filter(ReferentielDocument.niveau_id == nid).all()
            assert {d.referentiel_id for d in docs} == {ref.id}
    finally:
        _effacer("LB-Fusion")


def test_un_seul_document_devient_le_referentiel_sans_ia():
    """LE CAS ORDINAIRE, et celui qu'on avait maltraité. Un couple servi par UN document n'a rien
    à fusionner : ce document EST le référentiel officiel, complet, déjà contrôlé au dépôt. Il est
    repris TEL QUEL.

    Trois choses se vérifient ici, et chacune était fausse avant :
      • l'IA n'est PAS appelée — la faire réécrire 88 pages officielles en 15 les abîme, et coûte
        des jetons pour détruire de l'information ;
      • le contenu est la copie EXACTE du document, à l'octet près ;
      • `fusion_max_pages` (15) ne s'y applique pas : 88 pages passent, ce plafond borne ce que
        l'IA PRODUIT, pas un document officiel qu'on reprend intact."""
    cid = _cycle("LB-Seul", 59)
    nid = _niveau(cid, "LB-NivSeul", 59)
    dossier = reflabo.REFERENTIELS_DIR / "LB_SEUL" / "LB_NIVSEUL"
    contenu = b"%PDF-le-referentiel-officiel-complet"
    try:
        assert _depot(cid, nid, "referentiel-bts.pdf", contenu).status_code == 200
        with patch.object(reflabo, "_fusionner_par_ia") as ia, \
             patch.object(reflabo, "_apercu", return_value=(88, "aperçu")):
            r = admin_client().post("/api/admin/labo/referentiels/constituer",
                                    json={"cycle_id": cid, "niveau_id": nid})
        assert r.status_code == 200, r.text
        ia.assert_not_called()                       # pas un jeton dépensé
        d = r.json()
        assert d["par_ia"] is False and d["documents"] == 1
        assert d["pages"] == 88                      # le plafond de 15 ne le concerne pas
        assert d["filename"] == "referentiel-bts.pdf"    # son VRAI nom, pas un nom fabriqué

        assert (dossier / "referentiel.pdf").read_bytes() == contenu    # copie à l'octet près
        assert len(list(dossier.glob("doc-*.pdf"))) == 1               # le morceau reste en place
        assert not list(dossier.glob("*.travail"))
        with dbmod.SessionLocal() as db:
            ref = db.query(Referentiel).filter(Referentiel.niveau_id == nid).one()
            assert ref.empreinte == hashlib.sha256(contenu).hexdigest()
            doc = db.query(ReferentielDocument).filter(ReferentielDocument.niveau_id == nid).one()
            assert doc.referentiel_id == ref.id      # le morceau dit de quoi il est fait
    finally:
        _effacer("LB-Seul")


def test_un_couple_qui_a_deja_un_referentiel_refuse_le_depot():
    """Un nouveau document n'écrase pas l'ancien en douce : c'est une nouvelle procédure, donc on
    supprime d'abord. Le message le dit, et RIEN n'est touché — ni le PDF en place, ni la fiche."""
    cid = _cycle("LB-Pris", 91)
    nid = _niveau(cid, "LB-NivPris", 91)
    dossier = reflabo.REFERENTIELS_DIR / "LB_PRIS" / "LB_NIVPRIS"
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "referentiel.pdf").write_bytes(b"%PDF-le-premier")
    try:
        with dbmod.SessionLocal() as db:
            db.add(Referentiel(niveau_id=nid, nom_fixe="lb_nivpris", collection="lb_nivpris",
                               fichier="premier.pdf"))
            db.commit()
        with patch.object(reflabo, "_apercu", return_value=(1, "aperçu")):
            r = admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                                    data={"cycle_id": cid, "niveau_id": nid},
                                    files={"file": ("second.pdf", b"%PDF-le-second", "application/pdf")})
        assert r.status_code == 409, r.text
        assert "a déjà un référentiel" in r.json()["detail"]
        assert "Supprimez-le d'abord" in r.json()["detail"]
        assert (dossier / "referentiel.pdf").read_bytes() == b"%PDF-le-premier"   # intact
        with dbmod.SessionLocal() as db:
            assert db.query(Referentiel).filter(Referentiel.niveau_id == nid).one().fichier == "premier.pdf"
    finally:
        _effacer("LB-Pris")


def test_un_couple_inconnu_est_refuse():
    """Le labo ne crée JAMAIS un cycle ni un niveau — ils se créent à une seule place, l'écran
    Programmes. Et un niveau qui n'est pas de ce cycle n'est pas ce couple."""
    cid = _cycle("LB-Inconnu", 92)
    autre = _cycle("LB-Autre", 93)
    nid_autre = _niveau(autre, "LB-NivAutre", 93)
    fichier = {"file": ("doc.pdf", b"%PDF-x", "application/pdf")}
    r = admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                            data={"cycle_id": 999999, "niveau_id": nid_autre}, files=fichier)
    assert r.status_code == 404 and "Cycle inconnu" in r.json()["detail"]
    r = admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                            data={"cycle_id": cid, "niveau_id": nid_autre}, files=fichier)
    assert r.status_code == 404 and "Niveau inconnu" in r.json()["detail"]


def test_un_document_refuse_ne_laisse_rien_derriere_lui():
    """Un dépôt refusé ne doit rien laisser : ni fichier, ni fichier de travail, ni ligne en base.
    Le document n'est écrit sous un nom de travail que le temps d'être contrôlé.

    Le nombre de pages n'est plus jugé ICI — il l'est sur le total, à la fusion. Ce qui se juge au
    dépôt, c'est ce qui rend le morceau inutilisable : ce n'est pas un PDF, ou il ne se lit pas
    (chiffré, abîmé)."""
    cid = _cycle("LB-Refus", 94)
    nid = _niveau(cid, "LB-NivRefus", 94)
    dossier = reflabo.REFERENTIELS_DIR / "LB_REFUS" / "LB_NIVREFUS"
    try:
        # Ce n'est pas un PDF : refusé avant même d'être écrit.
        r = admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                                data={"cycle_id": cid, "niveau_id": nid},
                                files={"file": ("faux.pdf", b"CECI-N-EST-PAS-UN-PDF", "application/pdf")})
        assert r.status_code == 400 and "n'est pas un PDF" in r.json()["detail"]

        # C'en est un, mais il ne se lit pas — un PDF chiffré échoue exactement comme ça.
        with patch.object(reflabo, "_apercu", side_effect=RuntimeError("fichier protégé")):
            r = admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                                    data={"cycle_id": cid, "niveau_id": nid},
                                    files={"file": ("protege.pdf", b"%PDF-chiffre", "application/pdf")})
        assert r.status_code == 400 and "Lecture du PDF impossible" in r.json()["detail"]

        if dossier.exists():
            assert not list(dossier.glob("doc-*.pdf"))
            assert not list(dossier.glob("*.depot"))
            assert not (dossier / "referentiel.pdf").exists()
        with dbmod.SessionLocal() as db:
            assert db.query(ReferentielDocument).filter(ReferentielDocument.niveau_id == nid).count() == 0
            assert db.query(Referentiel).filter(Referentiel.niveau_id == nid).count() == 0
    finally:
        _effacer("LB-Refus")


def test_la_fusion_refuse_un_produit_trop_long():
    """Le plafond porte sur ce que l'IA PRODUIT, pas sur ce qu'elle lit : des documents longs sont
    normaux, c'est la raison d'être de la fusion. Si le référentiel obtenu déborde, on ne le coupe
    pas en deux — on le dit. Refus → pas de fiche, pas de referentiel.pdf, et les morceaux restent
    en place (on relance, on ne recommence pas tout)."""
    cid = _cycle("LB-Plafond", 61)
    nid = _niveau(cid, "LB-NivPlafond", 61)
    try:
        with patch.object(reflabo, "_apercu", return_value=(120, "aperçu")):
            for nom in ("a.pdf", "b.pdf"):           # 240 pages EN ENTRÉE : ça ne gêne pas
                assert admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                                           data={"cycle_id": cid, "niveau_id": nid},
                                           files={"file": (nom, b"%PDF-" + nom.encode(), "application/pdf")}
                                           ).status_code == 200
        # …mais l'IA rend 40 pages là où le plafond en autorise 15.
        with patch.object(reflabo, "_fusionner_par_ia", side_effect=_fusion_bidon), \
             patch.object(reflabo, "_apercu", return_value=(40, "aperçu")):
            r = admin_client().post("/api/admin/labo/referentiels/constituer",
                                    json={"cycle_id": cid, "niveau_id": nid})
        assert r.status_code == 502, r.text
        assert "40 pages" in r.json()["detail"] and "15" in r.json()["detail"]
        dossier = reflabo.REFERENTIELS_DIR / "LB_PLAFOND" / "LB_NIVPLAFOND"
        assert not (dossier / "referentiel.pdf").exists()
        assert not list(dossier.glob("*.travail"))
        assert len(list(dossier.glob("doc-*.pdf"))) == 2     # les morceaux ne sont pas perdus
        with dbmod.SessionLocal() as db:
            assert db.query(Referentiel).filter(Referentiel.niveau_id == nid).count() == 0
    finally:
        _effacer("LB-Plafond")


def test_document_deja_connu_reconnu_sur_le_contenu_pas_sur_le_nom():
    """Le même document déposé pour un second couple ne passe pas inaperçu : la reconnaissance se
    fait sur l'EMPREINTE du contenu (SHA-256), jamais sur le nom — même contenu sous un autre nom
    = reconnu, même nom avec un autre contenu = inconnu. On PRÉVIENT sans bloquer : un même
    programme peut légitimement servir deux niveaux, le dépôt aboutit dans tous les cas."""
    cid = _cycle("LB-Empr", 95)
    n1 = _niveau(cid, "LB-NivEmpr1", 95)
    n2 = _niveau(cid, "LB-NivEmpr2", 96)
    n3 = _niveau(cid, "LB-NivEmpr3", 97)
    contenu = b"%PDF-le-referentiel-officiel"
    try:
        with patch.object(reflabo, "_apercu", return_value=(1, "aperçu")):
            r1 = admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                                     data={"cycle_id": cid, "niveau_id": n1},
                                     files={"file": ("officiel.pdf", contenu, "application/pdf")})
            assert r1.status_code == 200, r1.text
            assert r1.json()["deja"] is None                  # jamais vu : rien à signaler
        # Le premier couple est mené au bout : le document reste reconnaissable après la fusion —
        # c'est le MORCEAU qu'on compare, et il survit au montage.
        assert _constituer(cid,n1).status_code == 200

        with patch.object(reflabo, "_apercu", return_value=(1, "aperçu")):
            # MÊME contenu, AUTRE nom, autre couple → reconnu, et le dépôt aboutit quand même.
            r2 = admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                                     data={"cycle_id": cid, "niveau_id": n2},
                                     files={"file": ("copie-telechargee.pdf", contenu, "application/pdf")})
            assert r2.status_code == 200, r2.text
            assert r2.json()["deja"] == {"ou": "valide", "fichier": "officiel.pdf",
                                         "cycle": "LB-Empr", "niveau": "LB-NivEmpr1"}

            # MÊME nom, AUTRE contenu → inconnu (le nom ne prouve rien).
            r3 = admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                                     data={"cycle_id": cid, "niveau_id": n3},
                                     files={"file": ("officiel.pdf", b"%PDF-un-autre", "application/pdf")})
            assert r3.status_code == 200, r3.text
            assert r3.json()["deja"] is None
        with dbmod.SessionLocal() as db:
            emp = {d.niveau_id: d.empreinte for d in db.query(ReferentielDocument).filter(
                ReferentielDocument.niveau_id.in_([n1, n2, n3])).all()}
            assert emp[n1] == emp[n2] and emp[n3] != emp[n1]
    finally:
        _effacer("LB-Empr")


def test_le_document_se_relit_par_son_couple():
    """« Voir le PDF » ne passe pas par un jeton : le référentiel est à sa place, le couple suffit
    à le retrouver. Chaque MORCEAU se relit aussi, par son identifiant — c'est le bouton « Voir »
    de sa ligne, celui qui sert AVANT la constitution. Couple sans référentiel → 404."""
    cid = _cycle("LB-Lire", 98)
    nid = _niveau(cid, "LB-NivLire", 98)
    vide = _niveau(cid, "LB-NivVide", 99)
    try:
        with patch.object(reflabo, "_apercu", return_value=(1, "aperçu")):
            dep = admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                                      data={"cycle_id": cid, "niveau_id": nid},
                                      files={"file": ("doc.pdf", b"%PDF-le-vrai-contenu",
                                                      "application/pdf")})
        assert dep.status_code == 200, dep.text
        # AVANT : le morceau se lit, le référentiel du couple n'existe pas encore.
        doc_id = dep.json()["document_id"]
        m = admin_client().get(f"/api/admin/labo/referentiels/document-pdf?document_id={doc_id}")
        assert m.status_code == 200 and m.content == b"%PDF-le-vrai-contenu"
        assert admin_client().get(
            f"/api/admin/labo/referentiels/pdf?cycle_id={cid}&niveau=LB-NivLire").status_code == 404

        assert _constituer(cid,nid).status_code == 200
        r = admin_client().get(
            f"/api/admin/labo/referentiels/pdf?cycle_id={cid}&niveau=LB-NivLire")
        assert r.status_code == 200, r.text
        assert r.headers["content-type"] == "application/pdf"
        assert "inline" in r.headers["content-disposition"]
        # UN SEUL document : le référentiel est sa copie EXACTE — pas de trace de montage.
        assert r.content == b"%PDF-le-vrai-contenu"
        assert admin_client().get(
            f"/api/admin/labo/referentiels/pdf?cycle_id={cid}&niveau=LB-NivVide").status_code == 404
        assert vide  # le niveau existe bien, c'est le document qui manque
    finally:
        _effacer("LB-Lire")


# ── Étape 3 — supprimer un référentiel ───────────────────────────────────────

def _referentiel_complet(cycle="LB-Supp", niveau="LB-NivSupp", ordre=83, avec_pdf=True):
    """Un référentiel mené AU BOUT de la procédure : matières, unités découpées, un type d'activité
    coché et ses précisions, plus le PDF sur disque. C'est exactement ce que le refus « déjà
    ingéré » rendait indestructible."""
    from backend.core.models_db import (Referentiel, Matiere, ReferentielChunk, ActiviteType,
                                        ReferentielTypePrecision)
    cid = _cycle(cycle, ordre)
    nid = _niveau(cid, niveau, ordre)
    with dbmod.SessionLocal() as db:
        ref = Referentiel(niveau_id=nid, nom_fixe=f"lb_supp_{ordre}", collection=f"lb_supp_{ordre}",
                          fichier="referentiel.pdf", texte_epure="TEXTE", decoupe_valide=True)
        db.add(ref); db.commit(); db.refresh(ref)
        db.add_all([Matiere(referentiel_id=ref.id, nom=f"Matière {i}", ordre=i, actif=True, validee=True)
                    for i in range(3)])
        db.add_all([ReferentielChunk(referentiel_id=ref.id, chunk_index=i, option_ab="", page=1,
                                     texte=f"unité {i}", embedding=[0.0] * 1024, embedding_model="test")
                    for i in range(5)])
        typ = ActiviteType(referentiel_id=ref.id, label=f"Type {ordre}", origine="admin",
                           validee=True, prompt="P")
        db.add(typ); db.commit(); db.refresh(typ)
        db.add_all([ReferentielTypePrecision(type_activite_id=typ.id, libelle=f"Précision {i}")
                    for i in range(2)])
        db.commit()
        ref_id = ref.id
    if avec_pdf:
        dossier = reflabo.REFERENTIELS_DIR / _dossier(cycle) / _dossier(niveau)
        dossier.mkdir(parents=True, exist_ok=True)
        (dossier / "referentiel.pdf").write_bytes(b"%PDF-fake")
    return cid, nid, ref_id


def test_bilan_de_suppression_compte_en_base():
    """La première boîte de dialogue dit CE QUI PART, avec des nombres LUS EN BASE — jamais
    estimés. C'est cette route qui les fournit."""
    import shutil as _shutil
    cid, _, _ = _referentiel_complet(ordre=84)
    try:
        r = admin_client().get(
            f"/api/admin/labo/referentiels/supprimer-bilan?cycle_id={cid}&niveau=LB-NivSupp")
        assert r.status_code == 200, r.text
        assert r.json() == {"existe": True, "fichier": "referentiel.pdf", "matieres": 3, "unites": 5,
                            "types": 1, "precisions": 2, "pdf": True, "profs": 0,
                            # nommément, pas un nombre : c'est ce que la première boîte affiche
                            "profs_liste": []}
    finally:
        _shutil.rmtree(reflabo.REFERENTIELS_DIR / "LB_SUPP", ignore_errors=True)


def test_supprimer_un_referentiel_deja_decoupe_marche():
    """Aucun refus « déjà ingéré : n unité(s) » : il protégeait la mauvaise chose (les unités se
    recalculent depuis le PDF) et verrouillait le catalogue — un référentiel mené au bout ne
    pourrait plus jamais être retiré. Tout part avec lui : matières, unités, types, précisions,
    et le PDF sur disque."""
    import shutil as _shutil
    from backend.core.models_db import (Referentiel, Matiere, ReferentielChunk,
                                        ActiviteType, ReferentielTypePrecision)
    cid, _, ref_id = _referentiel_complet(ordre=85)
    pdf = reflabo.REFERENTIELS_DIR / "LB_SUPP" / "LB_NIVSUPP" / "referentiel.pdf"
    try:
        assert pdf.exists()
        r = admin_client().post("/api/admin/labo/referentiels/supprimer",
                                json={"cycle_id": cid, "niveau": "LB-NivSupp"})
        assert r.status_code == 200, r.text
        with dbmod.SessionLocal() as db:
            assert db.query(Referentiel).filter(Referentiel.id == ref_id).count() == 0
            assert db.query(Matiere).filter(Matiere.referentiel_id == ref_id).count() == 0
            assert db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == ref_id).count() == 0
            assert db.query(ActiviteType).filter(
                ActiviteType.referentiel_id == ref_id).all() == []
            assert db.query(ReferentielTypePrecision).count() == 0
        assert not pdf.exists()                      # le document part aussi
    finally:
        _shutil.rmtree(reflabo.REFERENTIELS_DIR / "LB_SUPP", ignore_errors=True)


def test_supprimer_refuse_toujours_si_des_profs_travaillent_dessus():
    """L'AUTRE refus, lui, ne bouge pas : des profs rattachés à une matière de ce référentiel,
    c'est du vrai monde. 409, et RIEN n'est effacé. (Le contournement assumé par l'admin est
    vérifié dans tests/test_maj_referentiel.py.)"""
    import shutil as _shutil
    from backend.core.models_db import Referentiel, Matiere, User
    cid, _, ref_id = _referentiel_complet(ordre=86)
    try:
        with dbmod.SessionLocal() as db:
            mat = db.query(Matiere).filter(Matiere.referentiel_id == ref_id).first()
            db.add(User(email="prof.labo.supp@test.fr", password_hash="x", subject_id=mat.id))
            db.commit()
        r = admin_client().post("/api/admin/labo/referentiels/supprimer",
                                json={"cycle_id": cid, "niveau": "LB-NivSupp"})
        assert r.status_code == 409, r.text
        assert "professeur(s) travaillent" in r.json()["detail"]
        with dbmod.SessionLocal() as db:             # rien n'a bougé
            assert db.query(Referentiel).filter(Referentiel.id == ref_id).count() == 1
        # …et le bilan l'annonce AVANT le clic, pour que la première boîte ne mente pas.
        b = admin_client().get(
            f"/api/admin/labo/referentiels/supprimer-bilan?cycle_id={cid}&niveau=LB-NivSupp")
        assert b.json()["profs"] == 1
    finally:
        _shutil.rmtree(reflabo.REFERENTIELS_DIR / "LB_SUPP", ignore_errors=True)


def test_la_liste_des_catalogues_est_lue_en_base():
    """La colonne « Catalogues » du labo est une fenêtre sur la base — jamais une copie. Le back
    du labo a la sienne : l'écran n'appelle plus une seule route de l'ancien."""
    import shutil as _shutil
    cid, nid, _ = _referentiel_complet(cycle="LB-Liste", niveau="LB-NivListe", ordre=87)
    try:
        r = admin_client().get("/api/admin/labo/referentiels/liste")
        assert r.status_code == 200, r.text
        ligne = [x for x in r.json()["referentiels"] if x["niveau_id"] == nid]
        assert len(ligne) == 1
        assert ligne[0]["cycle"] == "LB-Liste" and ligne[0]["niveau"] == "LB-NivListe"
        assert ligne[0]["cycle_id"] == cid
        assert ligne[0]["complet"] is True           # `decoupe_valide` : la procédure est au bout
    finally:
        _shutil.rmtree(reflabo.REFERENTIELS_DIR / "LB_LISTE", ignore_errors=True)


# ── Étape 2 bis — trouver le lien officiel ───────────────────────────────────
#
# Le moteur de recherche n'est JAMAIS appelé pour de vrai ici : ces tests vérifient notre
# plomberie (clé, couple, tri, panne), pas l'index de Tavily. Un test qui sort sur le réseau
# échouerait un jour sans que le code ait bougé.

class _Reponse:
    """Ce que `httpx.post` rend, réduit à ce que la route utilise."""
    def __init__(self, data=None, erreur=None):
        self._data, self._erreur = data or {}, erreur

    def raise_for_status(self):
        if self._erreur:
            raise self._erreur

    def json(self):
        return self._data


def test_la_recherche_ne_sannonce_que_si_la_cle_est_la():
    """Sans clé, l'écran ne doit pas montrer un bouton qui répondrait par une erreur : le serveur
    le dit lui-même. La clé vit dans le .env, jamais en base."""
    import os
    c = admin_client()
    with patch.dict(os.environ, {reflabo.TAVILY_CLE_ENV: ""}):
        assert c.get("/api/admin/labo/referentiels/recherche-dispo").json() == {"disponible": False}
    with patch.dict(os.environ, {reflabo.TAVILY_CLE_ENV: "tvly-peu-importe"}):
        assert c.get("/api/admin/labo/referentiels/recherche-dispo").json() == {"disponible": True}


def test_chercher_un_lien_sans_cle_refuse_et_ne_sort_pas():
    """Pas de clé, pas de recherche — et surtout aucun appel réseau au passage."""
    import os
    cid = _cycle("LB-Sans", 71)
    nid = _niveau(cid, "LB-NivSans", 71)
    with patch.dict(os.environ, {reflabo.TAVILY_CLE_ENV: ""}), \
         patch.object(reflabo.httpx, "post") as moteur:
        r = admin_client().post("/api/admin/labo/referentiels/chercher-lien",
                                json={"cycle_id": cid, "niveau_id": nid})
    assert r.status_code == 503, r.text
    assert reflabo.TAVILY_CLE_ENV in r.json()["detail"]
    moteur.assert_not_called()


def test_la_question_de_l_admin_part_telle_quelle():
    """CE QUE L'ADMIN A ÉCRIT EST CE QUI PART. Rien n'est ajouté à sa question, aucun domaine n'est
    imposé, et un SEUL appel est fait au moteur.

    C'est le contraire de la version précédente, qui fabriquait la question dans son dos
    (« programme d'enseignement officiel en vigueur classe de … toutes disciplines ») et la bridait
    sur deux domaines de l'Éducation nationale. Réglée sur quatre couples du collège et du lycée,
    elle ne rendait RIEN sur un BTS — et jetait au passage le bon PDF, publié ailleurs."""
    import os
    cid = _cycle("LB-Piste", 72)
    nid = _niveau(cid, "LB-NivPiste", 72)
    faux = _Reponse({"results": [
        {"url": "https://eduscol.education.gouv.fr/doc/programme-67722.pdf", "title": "Programme"},
    ]})
    with patch.dict(os.environ, {reflabo.TAVILY_CLE_ENV: "tvly-x"}), \
         patch.object(reflabo.httpx, "post", return_value=faux) as moteur:
        r = admin_client().post("/api/admin/labo/referentiels/chercher-lien",
                                json={"cycle_id": cid, "niveau_id": nid,
                                      "question": "référentiel BTS CIEL option B annexe arrêté"})
    assert r.status_code == 200, r.text
    assert r.json()["question"] == "référentiel BTS CIEL option B annexe arrêté"

    moteur.assert_called_once()                  # un seul appel : la recherche, et rien d'autre
    envoi = moteur.call_args.kwargs
    assert envoi["json"]["query"] == "référentiel BTS CIEL option B annexe arrêté"
    assert "include_domains" not in envoi["json"]     # aucun site n'est imposé
    assert envoi["json"]["search_depth"] == "advanced"
    assert envoi["headers"]["Authorization"] == "Bearer tvly-x"


def test_sans_question_le_serveur_propose_le_couple():
    """Le champ vide n'est pas une erreur : on retombe sur la proposition — le cycle et le niveau,
    rien de plus. C'est le point de départ que l'écran affiche, et que l'admin réécrit."""
    import os
    cid = _cycle("LB-Defaut", 78)
    nid = _niveau(cid, "LB-NivDefaut", 78)
    with patch.dict(os.environ, {reflabo.TAVILY_CLE_ENV: "tvly-x"}), \
         patch.object(reflabo.httpx, "post", return_value=_Reponse({"results": []})) as moteur:
        r = admin_client().post("/api/admin/labo/referentiels/chercher-lien",
                                json={"cycle_id": cid, "niveau_id": nid, "question": "   "})
    assert r.status_code == 200, r.text
    assert r.json()["question"] == "LB-Defaut LB-NivDefaut"
    assert moteur.call_args.kwargs["json"]["query"] == "LB-Defaut LB-NivDefaut"


def test_tout_ce_que_le_moteur_rend_est_montre():
    """AUCUN FILTRE. Pages web, sites non officiels, projets de programmes : tout remonte, dans
    l'ordre du moteur. Seuls partent les doublons d'adresse et les lignes vides — ce ne sont pas
    des résultats. Le drapeau `pdf` est une INDICATION pour l'écran, jamais un tri : c'est l'admin
    qui juge, et « Récupérer » qui refusera ce qui n'est pas déposable."""
    import os
    cid = _cycle("LB-Brut", 75)
    nid = _niveau(cid, "LB-NivBrut", 75)
    page = "https://www.education.gouv.fr/les-programmes-470408"
    pdf = "https://eduscol.education.gouv.fr/doc/programme-67722.pdf"
    ailleurs = "https://www.enseignementsup-recherche.gouv.fr/referentiel-bts-ciel.pdf"
    projet = "https://www.education.gouv.fr/files/csp---projet-de-programmes-441420.pdf"
    faux = _Reponse({"results": [
        {"url": page, "title": "Les programmes"},
        {"url": pdf, "title": "Programme"},
        {"url": ailleurs, "title": "Référentiel BTS CIEL"},   # un autre domaine : il RESTE
        {"url": projet, "title": "CSP — projet de programmes"},
        {"url": pdf, "title": "Le même, deux fois"},          # doublon : une seule ligne
        {"url": "", "title": "ligne vide"},                   # rien à montrer
    ]})
    with patch.dict(os.environ, {reflabo.TAVILY_CLE_ENV: "tvly-x"}), \
         patch.object(reflabo.httpx, "post", return_value=faux):
        r = admin_client().post("/api/admin/labo/referentiels/chercher-lien",
                                json={"cycle_id": cid, "niveau_id": nid})
    assert r.status_code == 200, r.text
    pistes = r.json()["pistes"]
    assert [p["url"] for p in pistes] == [page, pdf, ailleurs, projet]   # l'ordre du moteur
    assert [p["pdf"] for p in pistes] == [False, True, True, True]
    assert pistes[0]["titre"] == "Les programmes"


def test_chercher_un_lien_pour_un_couple_deja_servi_refuse():
    """Inutile de proposer un lien là où le dépôt serait refusé : même règle que `preparer-lien`,
    et le moteur n'est pas dérangé pour rien."""
    import os
    import shutil as _shutil
    cid, nid, _ = _referentiel_complet(cycle="LB-Servi", niveau="LB-NivServi", ordre=73)
    try:
        with patch.dict(os.environ, {reflabo.TAVILY_CLE_ENV: "tvly-x"}), \
             patch.object(reflabo.httpx, "post") as moteur:
            r = admin_client().post("/api/admin/labo/referentiels/chercher-lien",
                                    json={"cycle_id": cid, "niveau_id": nid})
        assert r.status_code == 409, r.text
        assert "a déjà un référentiel" in r.json()["detail"]
        moteur.assert_not_called()
    finally:
        _shutil.rmtree(reflabo.REFERENTIELS_DIR / "LB_SERVI", ignore_errors=True)


def test_moteur_en_panne_le_dit_sans_rien_casser():
    """La recherche est une aide : quand elle tombe, l'écran l'annonce et la saisie à la main
    reste entière. Rien n'est écrit, rien n'est déposé."""
    import os
    cid = _cycle("LB-Panne", 74)
    nid = _niveau(cid, "LB-NivPanne", 74)
    with patch.dict(os.environ, {reflabo.TAVILY_CLE_ENV: "tvly-x"}), \
         patch.object(reflabo.httpx, "post", side_effect=RuntimeError("réseau coupé")):
        r = admin_client().post("/api/admin/labo/referentiels/chercher-lien",
                                json={"cycle_id": cid, "niveau_id": nid})
    assert r.status_code == 502, r.text
    assert "réseau coupé" in r.json()["detail"]
    with dbmod.SessionLocal() as db:
        assert db.query(Referentiel).filter(Referentiel.niveau_id == nid).first() is None


# ── Étape 2 bis — plusieurs documents pour un seul référentiel ───────────────

def _depot(cid, nid, nom, contenu=None, pages=1):
    with patch.object(reflabo, "_apercu", return_value=(pages, "aperçu")):
        return admin_client().post("/api/admin/labo/referentiels/preparer-depot",
                                   data={"cycle_id": cid, "niveau_id": nid},
                                   files={"file": (nom, contenu or f"%PDF-{nom}".encode(),
                                                   "application/pdf")})


def test_l_ordre_des_documents_est_une_donnee():
    """L'ordre décide du référentiel final : il vit EN BASE, pas dans l'écran. On l'envoie en
    entier — un ordre partiel laisserait des documents au rang de leur voisin — et la fusion le
    suit à la lettre."""
    cid = _cycle("LB-Ordre", 62)
    nid = _niveau(cid, "LB-NivOrdre", 62)
    try:
        ids = [_depot(cid, nid, n).json()["document_id"] for n in ("a.pdf", "b.pdf", "c.pdf")]
        # Un ordre incomplet est refusé : on ne devine pas la place des absents.
        r = admin_client().post("/api/admin/labo/referentiels/documents/ordre",
                                json={"niveau_id": nid, "documents": ids[:2]})
        assert r.status_code == 422 and "ne correspond pas" in r.json()["detail"]

        r = admin_client().post("/api/admin/labo/referentiels/documents/ordre",
                                json={"niveau_id": nid, "documents": [ids[2], ids[0], ids[1]]})
        assert r.status_code == 200, r.text
        assert [d["fichier"] for d in r.json()["documents"]] == ["c.pdf", "a.pdf", "b.pdf"]

        assert _constituer(cid,nid).status_code == 200
        fusionne = reflabo.REFERENTIELS_DIR / "LB_ORDRE" / "LB_NIVORDRE" / "referentiel.pdf"
        assert fusionne.read_bytes() == b"%PDF-%PDF-c.pdf+%PDF-a.pdf+%PDF-b.pdf"
    finally:
        _effacer("LB-Ordre")


def test_retirer_un_document_avant_la_fusion_et_plus_apres():
    """Retirer un morceau efface sa ligne ET son fichier, et resserre les rangs. Une fois le
    couple fusionné, c'est refusé : les morceaux disent de quoi le référentiel est fait, en
    retirer un en douce serait un mensonge."""
    cid = _cycle("LB-Retrait", 63)
    nid = _niveau(cid, "LB-NivRetrait", 63)
    dossier = reflabo.REFERENTIELS_DIR / "LB_RETRAIT" / "LB_NIVRETRAIT"
    try:
        ids = [_depot(cid, nid, n).json()["document_id"] for n in ("un.pdf", "deux.pdf", "trois.pdf")]
        r = admin_client().post("/api/admin/labo/referentiels/documents/retirer",
                                json={"document_id": ids[0]})
        assert r.status_code == 200, r.text
        assert [d["fichier"] for d in r.json()["documents"]] == ["deux.pdf", "trois.pdf"]
        assert len(list(dossier.glob("doc-*.pdf"))) == 2        # le fichier est parti avec la ligne
        with dbmod.SessionLocal() as db:
            restants = (db.query(ReferentielDocument)
                          .filter(ReferentielDocument.niveau_id == nid)
                          .order_by(ReferentielDocument.ordre).all())
            assert [d.ordre for d in restants] == [0, 1]        # les rangs se resserrent

        assert _constituer(cid,nid).status_code == 200
        r = admin_client().post("/api/admin/labo/referentiels/documents/retirer",
                                json={"document_id": ids[1]})
        assert r.status_code == 409, r.text
        assert "est constitué" in r.json()["detail"]
        assert len(list(dossier.glob("doc-*.pdf"))) == 2        # rien n'a bougé
    finally:
        _effacer("LB-Retrait")


def test_un_couple_en_cours_reste_visible_dans_la_colonne():
    """Un travail commencé ne disparaît pas de l'écran : tant qu'il a des documents sans fiche, le
    couple figure dans la colonne, marqué « en cours », avec le nombre de documents déposés. Après
    la fusion, il y figure comme référentiel — une seule ligne, jamais deux."""
    cid = _cycle("LB-Encours", 64)
    nid = _niveau(cid, "LB-NivEncours", 64)
    try:
        _depot(cid, nid, "un.pdf")
        _depot(cid, nid, "deux.pdf")
        lignes = [x for x in admin_client().get(
            "/api/admin/labo/referentiels/liste").json()["referentiels"] if x["niveau_id"] == nid]
        assert len(lignes) == 1
        assert lignes[0]["en_cours"] is True and lignes[0]["documents"] == 2
        assert lignes[0]["id"] is None and lignes[0]["cycle"] == "LB-Encours"

        assert _constituer(cid,nid).status_code == 200
        lignes = [x for x in admin_client().get(
            "/api/admin/labo/referentiels/liste").json()["referentiels"] if x["niveau_id"] == nid]
        assert len(lignes) == 1                        # la ligne « en cours » a disparu
        assert lignes[0]["en_cours"] is False and lignes[0]["id"] is not None
    finally:
        _effacer("LB-Encours")


def test_supprimer_le_referentiel_emporte_ses_documents():
    """La suppression efface le dossier ENTIER du couple : le fusionné et les morceaux qui l'ont
    composé. Leurs lignes partent avec la fiche (CASCADE) — un fichier que plus aucune ligne ne
    réclame n'a rien à faire sur le disque."""
    cid = _cycle("LB-SuppDoc", 65)
    nid = _niveau(cid, "LB-NivSuppDoc", 65)
    dossier = reflabo.REFERENTIELS_DIR / "LB_SUPPDOC" / "LB_NIVSUPPDOC"
    try:
        _depot(cid, nid, "un.pdf")
        _depot(cid, nid, "deux.pdf")
        assert _constituer(cid,nid).status_code == 200
        assert (dossier / "referentiel.pdf").exists() and len(list(dossier.glob("doc-*.pdf"))) == 2

        r = admin_client().post("/api/admin/labo/referentiels/supprimer",
                                json={"cycle_id": cid, "niveau": "LB-NivSuppDoc"})
        assert r.status_code == 200, r.text
        assert not dossier.exists()
        with dbmod.SessionLocal() as db:
            assert db.query(ReferentielDocument).filter(
                ReferentielDocument.niveau_id == nid).count() == 0
            assert db.query(Referentiel).filter(Referentiel.niveau_id == nid).count() == 0
    finally:
        _effacer("LB-SuppDoc")


def test_on_n_empile_plus_apres_la_fusion():
    """Le couple est clôturé : un dépôt de plus est refusé, et la fusion ne se rejoue pas. Pour
    changer la composition, on supprime le référentiel et on refait la procédure."""
    cid = _cycle("LB-Clos", 66)
    nid = _niveau(cid, "LB-NivClos", 66)
    try:
        _depot(cid, nid, "un.pdf")
        assert _constituer(cid,nid).status_code == 200
        r = _depot(cid, nid, "deux.pdf")
        assert r.status_code == 409 and "a déjà un référentiel" in r.json()["detail"]
        assert _constituer(cid,nid).status_code == 409
    finally:
        _effacer("LB-Clos")


def test_la_fusion_sans_document_est_refusee():
    """Rien à fusionner = rien ne se crée. Un couple vide ne doit pas produire une fiche sans
    document — c'est exactement le demi-état qu'on refuse."""
    cid = _cycle("LB-Vide", 67)
    nid = _niveau(cid, "LB-NivVide2", 67)
    r = _constituer(cid,nid)
    assert r.status_code == 409 and "Aucun document" in r.json()["detail"]
    with dbmod.SessionLocal() as db:
        assert db.query(Referentiel).filter(Referentiel.niveau_id == nid).count() == 0


# ── La fusion PAR L'IA — ce qui lui est envoyé, et ce qu'on fait de sa réponse ─

def test_la_fusion_envoie_les_textes_a_l_ia_et_ecrit_ce_qu_elle_rend():
    """Le cœur du geste : les documents sont LUS (leur texte entier), donnés à l'IA avec le
    couple et la longueur visée, et c'est SA réponse qui devient le référentiel. Rien n'est
    empilé, et le plafond de pages part du réglage EN BASE."""
    cid = _cycle("LB-IA", 68)
    nid = _niveau(cid, "LB-NivIA", 68)
    vu = {}

    def faux_generate(prompt, **kw):
        vu["prompt"] = prompt
        vu["max_tokens"] = kw.get("max_tokens")
        return "## Mathématiques\n- Résoudre un problème\n\n## Français\n- Lire un texte long"

    try:
        _depot(cid, nid, "programme.pdf")
        _depot(cid, nid, "bulletin.pdf")
        with patch.object(reflabo, "_texte_du_pdf", side_effect=lambda c: f"texte de {c.name}"), \
             patch.object(reflabo, "generate", side_effect=faux_generate), \
             patch.object(reflabo, "_ecrire_pdf",
                          side_effect=lambda t, dest, titre: dest.write_bytes(f"%PDF-{t}".encode())), \
             patch.object(reflabo, "_apercu", return_value=(3, "aperçu")):
            r = admin_client().post("/api/admin/labo/referentiels/constituer",
                                    json={"cycle_id": cid, "niveau_id": nid})
        assert r.status_code == 200, r.text

        # Ce que l'IA a reçu : le couple, les DEUX documents nommés, et la longueur visée.
        assert "LB-IA" in vu["prompt"] and "LB-NivIA" in vu["prompt"]
        assert "programme.pdf" in vu["prompt"] and "bulletin.pdf" in vu["prompt"]
        assert "15 pages" in vu["prompt"]                     # le réglage `fusion_max_pages`
        # Ce qu'on en a fait : sa réponse EST le référentiel.
        fusionne = reflabo.REFERENTIELS_DIR / "LB_IA" / "LB_NIVIA" / "referentiel.pdf"
        assert b"## Mathematiques".replace(b"Mathematiques", b"Math\xc3\xa9matiques") in fusionne.read_bytes()
        assert len(list(fusionne.parent.glob("doc-*.pdf"))) == 2    # les morceaux sont intacts
    finally:
        _effacer("LB-IA")


def test_des_documents_sans_texte_sont_refuses_avant_l_ia():
    """Un PDF scanné ne contient aucun texte : l'envoyer reviendrait à demander à l'IA d'inventer
    un référentiel à partir de rien. On refuse avant l'appel, et on dit pourquoi.

    DEUX documents ici, et c'est nécessaire : à un seul, l'IA n'est pas appelée du tout — le
    document est repris tel quel, scanné ou non, et il n'y a rien à refuser."""
    cid = _cycle("LB-Scan", 69)
    nid = _niveau(cid, "LB-NivScan", 69)
    try:
        _depot(cid, nid, "scan1.pdf")
        _depot(cid, nid, "scan2.pdf")
        with patch.object(reflabo, "_texte_du_pdf", return_value="   "), \
             patch.object(reflabo, "generate") as ia:
            r = admin_client().post("/api/admin/labo/referentiels/constituer",
                                    json={"cycle_id": cid, "niveau_id": nid})
        assert r.status_code == 400, r.text
        assert "scannés" in r.json()["detail"]
        ia.assert_not_called()                       # pas un jeton dépensé pour rien
        with dbmod.SessionLocal() as db:
            assert db.query(Referentiel).filter(Referentiel.niveau_id == nid).count() == 0
    finally:
        _effacer("LB-Scan")


# ── Ce que l'écran ne doit plus pouvoir faire dire au serveur ────────────────

def test_le_meme_document_deux_fois_sur_le_meme_couple_est_refuse():
    """Il passait sans un mot : deux lignes, les pages comptées deux fois, et l'IA payée pour lire
    deux fois la même chose. Le refus porte sur le CONTENU, pas sur le nom — et il ne vaut que
    pour CE couple : ailleurs, le même programme reste légitime (on prévient seulement)."""
    cid = _cycle("LB-Jumeau", 70)
    n1 = _niveau(cid, "LB-NivJumeau1", 70)
    n2 = _niveau(cid, "LB-NivJumeau2", 71)
    contenu = b"%PDF-le-meme-exactement"
    try:
        assert _depot(cid, n1, "officiel.pdf", contenu).status_code == 200
        r = _depot(cid, n1, "renomme-mais-identique.pdf", contenu)     # même couple, même contenu
        assert r.status_code == 409, r.text
        assert "déjà dans la liste" in r.json()["detail"]
        assert "officiel.pdf" in r.json()["detail"]                    # on dit SOUS QUEL NOM

        dossier = reflabo.REFERENTIELS_DIR / "LB_JUMEAU" / "LB_NIVJUMEAU1"
        assert len(list(dossier.glob("doc-*.pdf"))) == 1               # rien n'a été écrit en plus
        assert not list(dossier.glob("*.depot"))
        with dbmod.SessionLocal() as db:
            assert db.query(ReferentielDocument).filter(
                ReferentielDocument.niveau_id == n1).count() == 1

        # AUTRE couple : accepté, avec l'avertissement « déjà connu ».
        r2 = _depot(cid, n2, "officiel.pdf", contenu)
        assert r2.status_code == 200, r2.text
        assert r2.json()["deja"]["niveau"] == "LB-NivJumeau1"
    finally:
        _effacer("LB-Jumeau")


def test_apres_la_fusion_l_ordre_ne_change_plus():
    """Le référentiel est écrit : changer l'ordre en base annoncerait une composition que
    `referentiel.pdf` ne suit pas. Même refus que le retrait, et pour la même raison."""
    cid = _cycle("LB-Fige", 71)
    nid = _niveau(cid, "LB-NivFige", 72)
    try:
        ids = [_depot(cid, nid, n).json()["document_id"] for n in ("un.pdf", "deux.pdf")]
        assert _constituer(cid,nid).status_code == 200
        r = admin_client().post("/api/admin/labo/referentiels/documents/ordre",
                                json={"niveau_id": nid, "documents": [ids[1], ids[0]]})
        assert r.status_code == 409, r.text
        assert "est constitué" in r.json()["detail"]
        with dbmod.SessionLocal() as db:
            ordres = {d.fichier_origine: d.ordre for d in db.query(ReferentielDocument)
                      .filter(ReferentielDocument.niveau_id == nid).all()}
            assert ordres == {"un.pdf": 0, "deux.pdf": 1}     # inchangé
    finally:
        _effacer("LB-Fige")


def test_reconstituer_dit_que_c_est_deja_fait():
    """L'écran qui a lâché avant le serveur reclique. Le refus doit alors dire CE QUI EST VRAI —
    « c'est déjà fait » — et non « impossible, supprimez-le d'abord » : le travail a abouti, il
    n'y a rien à supprimer ni à refaire."""
    cid = _cycle("LB-Refusion", 72)
    nid = _niveau(cid, "LB-NivRefusion", 73)
    try:
        _depot(cid, nid, "un.pdf")
        assert _constituer(cid,nid).status_code == 200
        r = _constituer(cid,nid)
        assert r.status_code == 409, r.text
        detail = r.json()["detail"]
        assert "déjà" in detail and "constitué" in detail
        assert "Supprimez-le d'abord" not in detail          # le message du dépôt, pas celui-ci
    finally:
        _effacer("LB-Refusion")


def test_supprimer_rend_le_couple_entierement_libre():
    """C'est la SEULE sortie de l'état « fusionné ». Elle doit tout rendre : la fiche, le dossier,
    les morceaux — et surtout la possibilité de recommencer. Un couple à moitié libéré serait un
    cul-de-sac : plus de référentiel, mais plus moyen d'en refaire un."""
    cid = _cycle("LB-Libre", 73)
    nid = _niveau(cid, "LB-NivLibre", 74)
    dossier = reflabo.REFERENTIELS_DIR / "LB_LIBRE" / "LB_NIVLIBRE"
    try:
        _depot(cid, nid, "un.pdf")
        _depot(cid, nid, "deux.pdf")
        assert _constituer(cid,nid).status_code == 200
        assert admin_client().post("/api/admin/labo/referentiels/supprimer",
                                   json={"cycle_id": cid, "niveau": "LB-NivLibre"}
                                   ).status_code == 200
        # 1. plus rien en base, plus rien sur le disque
        assert not dossier.exists()
        with dbmod.SessionLocal() as db:
            assert db.query(Referentiel).filter(Referentiel.niveau_id == nid).count() == 0
            assert db.query(ReferentielDocument).filter(
                ReferentielDocument.niveau_id == nid).count() == 0
        # 2. le couple ne figure plus dans la colonne, ni comme référentiel ni comme « en cours »
        lignes = [x for x in admin_client().get(
            "/api/admin/labo/referentiels/liste").json()["referentiels"] if x["niveau_id"] == nid]
        assert lignes == []
        # 3. et la procédure peut recommencer, du dépôt jusqu'à la fusion
        assert _depot(cid, nid, "un.pdf").status_code == 200      # même nom, même contenu qu'avant
        assert _constituer(cid,nid).status_code == 200
    finally:
        _effacer("LB-Libre")
