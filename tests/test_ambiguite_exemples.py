"""Preuve — les énoncés d'exemple de l'écran Ambiguïtés vivent EN BASE, un par couple.

Le bouton « Tester un exemple » était une façade (« Pas d'exemple disponible pour le moment »),
et l'exemple qui l'avait précédé était un texte figé PAR MATIÈRE, qui ignorait le niveau.

Ce que ces tests PROUVENT (base aschool_test via conftest.py, AUCUN appel LLM — l'application
ne génère pas ces exemples, l'admin les recolle) :
  1. L'écran admin liste TOUS les couples, y compris ceux sans exemple : c'est lui qui dit le
     travail restant, une liste des seuls exemples écrits le cacherait.
  2. Le prompt servi pour un couple porte les mêmes types ET les mêmes vérifications que
     l'analyse, lus dans le même catalogue — sauf « Autre », qui appartient au prof.
  3. La réponse se recolle d'un bloc : le serveur la découpe sur les marqueurs du prompt.
  4. Supprimer veut dire supprimer : la ligne part, le couple redevient sans exemple.

Lancer : docker compose exec backend python -m pytest tests/test_ambiguite_exemples.py -q
"""
import backend.core.database as dbmod
from backend.core.models_db import (AmbiguiteExemple, Matiere, Niveau, Referentiel,
                                    ReferentielChunk)
from backend.main import app
from backend.pedagogie.ambiguite_exemples import decouper_colle, decouper_referentiel
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient

from _profil import matiere_id           # noqa: E402


def admin_client():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


REPONSE_TYPE = """=== ENONCE ===
Sujet — Sécurisation d'un réseau d'entreprise

Le document fourni décrit l'architecture réseau d'une PME. Analysez le système.

=== DEFAUTS ===
- Référence implicite — "le document fourni" — il y en a plusieurs, lequel ?
- Consigne vague — "Analysez le système" — sans critères précis
"""


def _un_couple(db):
    """Un couple réel en base : la matière porte déjà son niveau (via son référentiel).
    `matiere_id` ne fait que `flush` — sans le commit, la matière n'existerait que dans cette
    session et l'endpoint interrogé juste après ne la verrait pas."""
    mid = matiere_id(db, "STI", "BTS CIEL")
    db.commit()
    return mid


# ── Le découpage du collé (fonction pure : testée sans passer par HTTP) ──────────────────

def test_le_colle_est_coupe_sur_les_marqueurs_du_prompt():
    enonce, defauts = decouper_colle(REPONSE_TYPE)
    assert enonce.startswith("Sujet — Sécurisation")
    assert "=== " not in enonce and "=== " not in defauts
    assert defauts.count("\n- ") == 1 and defauts.startswith("- Référence implicite")


def test_sans_marqueur_rien_n_est_devine():
    """Un texte tronqué au mauvais endroit serait pire qu'un champ vide que l'admin voit."""
    enonce, defauts = decouper_colle("Un énoncé collé sans les blocs.")
    assert enonce == "Un énoncé collé sans les blocs." and defauts == ""


def test_bloc_defauts_absent_l_enonce_reste_entier():
    enonce, defauts = decouper_colle("=== ENONCE ===\nLe sujet complet.\n")
    assert enonce == "Le sujet complet." and defauts == ""


# ── Les endpoints admin ─────────────────────────────────────────────────────────────────

def test_la_liste_montre_les_couples_sans_exemple():
    with dbmod.SessionLocal() as db:
        mid = _un_couple(db)
    r = admin_client().get("/api/admin/ambiguite-exemples")
    assert r.status_code == 200, r.text
    ligne = next(l for l in r.json() if l["matiere_id"] == mid)
    assert ligne["texte"] == "" and ligne["niveau"] == "BTS CIEL"


def test_le_prompt_du_couple_porte_les_types_et_leurs_verifications():
    with dbmod.SessionLocal() as db:
        mid = _un_couple(db)
    r = admin_client().get(f"/api/admin/ambiguite-exemples/{mid}/prompt")
    assert r.status_code == 200, r.text
    p = r.json()["prompt"]
    assert "STI" in p and "BTS CIEL" in p
    assert "Référence implicite" in p and "Ce qui doit être repérable" in p
    assert "Autre" not in p          # le critère libre appartient au prof, pas à l'exemple
    assert "{" not in p.replace("{{", "")   # tous les repères ont été remplacés


def test_coller_enregistre_les_deux_champs_puis_les_remplace():
    with dbmod.SessionLocal() as db:
        mid = _un_couple(db)
    c = admin_client()

    r = c.post(f"/api/admin/ambiguite-exemples/{mid}/coller", json={"brut": REPONSE_TYPE})
    assert r.status_code == 200, r.text
    assert r.json()["texte"].startswith("Sujet —") and "Référence implicite" in r.json()["defauts"]

    r = c.post(f"/api/admin/ambiguite-exemples/{mid}/coller",
               json={"brut": "=== ENONCE ===\nDeuxième version.\n=== DEFAUTS ===\n- Double sens"})
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        lignes = db.query(AmbiguiteExemple).filter(AmbiguiteExemple.matiere_id == mid).all()
        assert len(lignes) == 1 and lignes[0].texte == "Deuxième version."


def test_un_colle_vide_est_refuse():
    with dbmod.SessionLocal() as db:
        mid = _un_couple(db)
    r = admin_client().post(f"/api/admin/ambiguite-exemples/{mid}/coller",
                            json={"brut": "=== ENONCE ===\n   \n=== DEFAUTS ===\n- rien"})
    assert r.status_code == 400, r.text


def test_supprimer_retire_vraiment_la_ligne():
    with dbmod.SessionLocal() as db:
        mid = _un_couple(db)
    c = admin_client()
    c.post(f"/api/admin/ambiguite-exemples/{mid}/coller", json={"brut": REPONSE_TYPE})

    assert c.delete(f"/api/admin/ambiguite-exemples/{mid}").status_code == 200
    with dbmod.SessionLocal() as db:
        assert db.query(AmbiguiteExemple).count() == 0
    assert c.delete(f"/api/admin/ambiguite-exemples/{mid}").status_code == 404


def test_une_matiere_inconnue_est_un_404_pas_un_500():
    assert admin_client().get("/api/admin/ambiguite-exemples/999999/prompt").status_code == 404


# ── Côté prof : le bouton « Utiliser un exemple » ────────────────────────────────────────

def test_le_prof_recoit_l_exemple_de_son_couple():
    """L'écran du prof lit l'exemple de SON couple — écrit par l'admin, jamais généré ici."""
    from backend.securite.comptes import create_access_token
    from _profil import user_couple

    with dbmod.SessionLocal() as db:
        mid = _un_couple(db)
        db.add(user_couple(db, email="prof.exemple@aschool.fr", password_hash="x",
                           is_verified=True, subject="STI", niveau="BTS CIEL"))
        db.commit()

    admin_client().post(f"/api/admin/ambiguite-exemples/{mid}/coller", json={"brut": REPONSE_TYPE})

    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token("prof.exemple@aschool.fr"))
    r = c.get("/api/ambiguites/exemple")
    assert r.status_code == 200, r.text
    assert r.json()["disponible"] is True
    assert r.json()["texte"].startswith("Sujet — Sécurisation")


def test_un_couple_sans_exemple_le_dit_au_lieu_d_en_inventer_un():
    """`disponible: false` → l'écran cache son bouton. Pas de bouton qui répond « rien »."""
    from backend.securite.comptes import create_access_token
    from _profil import user_couple

    with dbmod.SessionLocal() as db:
        _un_couple(db)
        db.add(user_couple(db, email="prof.sansex@aschool.fr", password_hash="x",
                           is_verified=True, subject="STI", niveau="BTS CIEL"))
        db.commit()

    c = TestClient(app)
    c.cookies.set("aschool_access", create_access_token("prof.sansex@aschool.fr"))
    r = c.get("/api/ambiguites/exemple")
    assert r.status_code == 200 and r.json()["disponible"] is False


# ── Tout un référentiel d'un coup (cartouche « Ambiguïtés » de la procédure Référentiel) ────
#
# 47 couples, c'était 47 aller-retours. Ce que ces tests PROUVENT :
#   1. le découpage lit un bloc par matière, ignore le titre de niveau et la numérotation ;
#   2. RIEN n'est écrit si un seul bloc ne trouve pas sa matière — un exemple posé sur la
#      mauvaise matière serait invisible, le prof le lirait sans savoir ;
#   3. le bloc « NON TRAITEES » est remonté tel quel : c'est là que le modèle DÉCLARE ce qu'il
#      n'a pas su écrire, au lieu de deviner.

COLLE_REFERENTIEL = """## BTS CIEL (2)

### 1. STI
=== ENONCE ===
Sujet de STI

=== DEFAUTS ===
- Consigne vague — "analysez" — sans critère

### Physique
=== ENONCE ===
Sujet de physique

=== DEFAUTS ===
- Double sens — "il" — sans antécédent

=== NON TRAITEES ===
- Langage — je ne sais pas ce que recouvre cette matière ici
"""


def test_le_colle_du_referentiel_donne_un_bloc_par_matiere():
    blocs, non_traitees = decouper_referentiel(COLLE_REFERENTIEL)
    assert [b[0] for b in blocs] == ["STI", "Physique"]      # « ## niveau » et « 1. » ignorés
    assert blocs[0][1] == "Sujet de STI" and blocs[0][2].startswith("- Consigne vague")
    assert non_traitees == ["Langage"]                       # le motif seul ne sert pas au rapprochement


def test_sans_bloc_de_matiere_rien_n_est_devine():
    blocs, non_traitees = decouper_referentiel("=== ENONCE ===\nUn texte sans titre de matière.")
    assert blocs == [] and non_traitees == []


# Les extraits qui décrivent chaque matière sont cherchés par proximité de sens. Les tests ne
# jugent pas la qualité du modèle d'embedding (il tournerait 15 secondes pour rien) : ils tiennent
# les vecteurs à la main, et vérifient ce que le CODE en fait — qui entre dans le prompt, et qui
# est écarté.
DIM = 1024


def _vecteur(un: bool) -> list[float]:
    """Deux vecteurs unitaires ORTHOGONAUX : cosinus 1 entre deux identiques, 0 sinon. Le seuil
    du référentiel (`score_min`, 0.3 par défaut) tombe donc franchement entre les deux."""
    v = [0.0] * DIM
    v[0 if un else 1] = 1.0
    return v


def _poser_chunk(db, referentiel_id: int, texte: str, proche: bool = True):
    db.add(ReferentielChunk(referentiel_id=referentiel_id, chunk_index=0, option_ab="", page=1,
                            texte=texte, embedding=_vecteur(proche), embedding_model="BAAI/bge-m3"))


def _embeddings_tenus(monkeypatch, proche: bool = True):
    """`embed_texts` rendra le vecteur voulu pour CHAQUE matière — proche du chunk, ou orthogonal."""
    import backend.rag.embeddings as emb
    monkeypatch.setattr(emb, "embed_texts", lambda textes: [_vecteur(proche) for _ in textes])


def _couple_ciel(db):
    """Le référentiel BTS CIEL et son couple (cycle, niveau) — les matières y sont déjà."""
    mid = matiere_id(db, "STI", "BTS CIEL")
    db.commit()
    matiere = db.query(Matiere).filter(Matiere.id == mid).first()
    ref = db.query(Referentiel).filter(Referentiel.id == matiere.referentiel_id).first()
    niv = db.query(Niveau).filter(Niveau.id == ref.niveau_id).first()
    return niv.cycle_id, niv.nom, mid


def test_l_etat_compte_les_matieres_du_referentiel():
    with dbmod.SessionLocal() as db:
        cid, niveau, _mid = _couple_ciel(db)
    r = admin_client().get(f"/api/admin/referentiels/ambiguites/etat?cycle_id={cid}&niveau={niveau}")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["total"] >= 1 and d["ecrits"] == 0
    assert any(m["nom"] == "STI" and m["ecrit"] is False for m in d["matieres"])


def test_le_prompt_du_referentiel_porte_ses_matieres_et_les_extraits_qui_les_decrivent(monkeypatch):
    """Le NOM d'une matière ne suffit pas : « Langage » a produit un exercice de programmation
    en C pour des 0-3 ans, entré en base sans que personne le voie. Le prompt porte donc, sous
    chaque matière, les passages du référentiel qui disent ce qu'elle recouvre."""
    with dbmod.SessionLocal() as db:
        cid, niveau, mid = _couple_ciel(db)
        matiere = db.query(Matiere).filter(Matiere.id == mid).first()
        _poser_chunk(db, matiere.referentiel_id, "Ce que recouvre vraiment cette matière.")
        db.commit()
    _embeddings_tenus(monkeypatch)

    r = admin_client().get(f"/api/admin/referentiels/ambiguites/prompt?cycle_id={cid}&niveau={niveau}")
    assert r.status_code == 200, r.text
    p = r.json()["prompt"]
    assert "- STI" in p and niveau in p
    assert "Ce que recouvre vraiment cette matière." in p     # l'extrait, pas seulement le nom
    assert r.json()["sans_contexte"] == []
    assert "Référence implicite" in p and "Ce qui doit être repérable" in p
    assert "Autre" not in p                      # le critère libre appartient au prof
    assert "{" not in p.replace("{{", "")        # tous les repères remplacés


def test_une_matiere_que_le_referentiel_n_eclaire_pas_sort_du_prompt(monkeypatch):
    """Vide plutôt que faux : on ne demande pas un exemple qui serait deviné. La matière est
    nommée à l'écran, et son couple reste vide."""
    with dbmod.SessionLocal() as db:
        cid, niveau, mid = _couple_ciel(db)
        matiere = db.query(Matiere).filter(Matiere.id == mid).first()
        _poser_chunk(db, matiere.referentiel_id, "Un passage qui parle d'autre chose.")
        db.commit()
    _embeddings_tenus(monkeypatch, proche=False)     # rien ne ressort au-dessus du seuil

    r = admin_client().get(f"/api/admin/referentiels/ambiguites/prompt?cycle_id={cid}&niveau={niveau}")
    assert r.status_code == 400, r.text
    assert "rien sur quoi écrire" in r.json()["detail"]


def test_sans_decoupage_on_le_dit_au_lieu_de_partir_du_nom_seul():
    with dbmod.SessionLocal() as db:
        cid, niveau, _mid = _couple_ciel(db)
    r = admin_client().get(f"/api/admin/referentiels/ambiguites/prompt?cycle_id={cid}&niveau={niveau}")
    assert r.status_code == 400, r.text
    assert "découpé" in r.json()["detail"]


def test_un_seul_nom_inconnu_et_rien_n_est_ecrit():
    """Le refus porte sur TOUT le collage : la moitié écrite serait le pire des états — l'admin
    croirait le travail fait pour les blocs passés."""
    with dbmod.SessionLocal() as db:
        cid, niveau, _mid = _couple_ciel(db)
    brut = ("### STI\n=== ENONCE ===\nUn sujet\n=== DEFAUTS ===\n- un défaut\n\n"
            "### Matière qui n'existe pas\n=== ENONCE ===\nAutre\n=== DEFAUTS ===\n- autre\n")
    r = admin_client().post("/api/admin/referentiels/ambiguites/coller",
                            json={"cycle_id": cid, "niveau": niveau, "brut": brut})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["applique"] is False and d["ecrits"] == 0
    assert d["orphelins"] == ["Matière qui n'existe pas"]
    with dbmod.SessionLocal() as db:
        assert db.query(AmbiguiteExemple).count() == 0


def test_le_collage_ecrit_puis_remplace_et_remonte_les_non_traitees():
    with dbmod.SessionLocal() as db:
        cid, niveau, mid = _couple_ciel(db)
    c = admin_client()

    brut = ("### STI\n=== ENONCE ===\nSujet de STI\n=== DEFAUTS ===\n- un défaut\n\n"
            "=== NON TRAITEES ===\n- Langage — pas sûr de ce que ça recouvre\n")
    d = c.post("/api/admin/referentiels/ambiguites/coller",
               json={"cycle_id": cid, "niveau": niveau, "brut": brut}).json()
    assert d["applique"] is True and d["ecrits"] == 1 and d["remplaces"] == 0
    assert d["non_traitees"] == ["Langage"]

    d = c.post("/api/admin/referentiels/ambiguites/coller",
               json={"cycle_id": cid, "niveau": niveau,
                     "brut": "### sti\n=== ENONCE ===\nDeuxième version\n=== DEFAUTS ===\n- x\n"}).json()
    assert d["applique"] is True and d["remplaces"] == 1     # rapproché malgré la casse
    with dbmod.SessionLocal() as db:
        lignes = db.query(AmbiguiteExemple).filter(AmbiguiteExemple.matiere_id == mid).all()
        assert len(lignes) == 1 and lignes[0].texte == "Deuxième version"


def test_un_couple_sans_referentiel_est_un_404():
    assert admin_client().get(
        "/api/admin/referentiels/ambiguites/prompt?cycle_id=999999&niveau=Inconnu").status_code == 404


def test_la_voie_payante_ecrit_le_meme_resultat_que_le_collage(monkeypatch):
    """Les deux voies rendent la MÊME chose : même prompt, même découpage, même écriture. Sinon
    la payante deviendrait la vraie et la gratuite un pis-aller."""
    import backend.pedagogie.ambiguite_exemples as mod

    with dbmod.SessionLocal() as db:
        cid, niveau, mid = _couple_ciel(db)
        matiere = db.query(Matiere).filter(Matiere.id == mid).first()
        _poser_chunk(db, matiere.referentiel_id, "Ce que recouvre cette matière.")
        db.commit()
    _embeddings_tenus(monkeypatch)

    rendu = ("### STI\n=== ENONCE ===\nÉnoncé du moteur\n=== DEFAUTS ===\n- un défaut\n\n"
             "=== NON TRAITEES ===\n- Langage — les extraits n'en disent rien\n")
    monkeypatch.setattr(mod, "generate", lambda *a, **k: rendu)

    r = admin_client().post("/api/admin/referentiels/ambiguites/generer",
                            json={"cycle_id": cid, "niveau": niveau})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["applique"] is True and d["ecrits"] == 1 and d["non_traitees"] == ["Langage"]
    with dbmod.SessionLocal() as db:
        assert db.query(AmbiguiteExemple).filter(
            AmbiguiteExemple.matiere_id == mid).first().texte == "Énoncé du moteur"


def test_l_appel_paye_ne_perd_pas_sa_reponse_quand_un_nom_est_faux(monkeypatch):
    """Rien n'est écrit si un nom n'est pas reconnu — mais le texte revient à l'écran : sans ça,
    l'admin devrait REPAYER pour ravoir ce qu'il vient d'acheter."""
    import backend.pedagogie.ambiguite_exemples as mod

    with dbmod.SessionLocal() as db:
        cid, niveau, mid = _couple_ciel(db)
        matiere = db.query(Matiere).filter(Matiere.id == mid).first()
        _poser_chunk(db, matiere.referentiel_id, "Ce que recouvre cette matière.")
        db.commit()
    _embeddings_tenus(monkeypatch)

    rendu = "### Matière inventée\n=== ENONCE ===\nUn énoncé\n=== DEFAUTS ===\n- un défaut\n"
    monkeypatch.setattr(mod, "generate", lambda *a, **k: rendu)

    d = admin_client().post("/api/admin/referentiels/ambiguites/generer",
                            json={"cycle_id": cid, "niveau": niveau}).json()
    assert d["applique"] is False and d["orphelins"] == ["Matière inventée"]
    assert d["brut"] == rendu                    # la réponse payée revient, elle n'est pas perdue
    with dbmod.SessionLocal() as db:
        assert db.query(AmbiguiteExemple).count() == 0


def test_corriger_un_exemple_sur_place_champ_par_champ():
    """L'écran admin écrit l'exemple LÀ OÙ IL SE LIT : les deux champs partent tels qu'ils sont
    tapés, sans marqueur à respecter. Il y avait avant deux zones pour le même texte — celle du
    haut le montrait sans qu'on puisse y toucher, celle du bas était la seule où agir."""
    with dbmod.SessionLocal() as db:
        mid = _un_couple(db)
    c = admin_client()
    c.post(f"/api/admin/ambiguite-exemples/{mid}/coller", json={"brut": REPONSE_TYPE})

    r = c.put(f"/api/admin/ambiguite-exemples/{mid}",
              json={"texte": "Énoncé corrigé à la main.", "defauts": "- Double sens — « il »"})
    assert r.status_code == 200, r.text
    assert r.json()["texte"] == "Énoncé corrigé à la main."
    with dbmod.SessionLocal() as db:
        ligne = db.query(AmbiguiteExemple).filter(AmbiguiteExemple.matiere_id == mid).first()
        assert ligne.texte == "Énoncé corrigé à la main."
        assert ligne.defauts == "- Double sens — « il »"


def test_un_exemple_ne_peut_pas_etre_vide():
    """Un couple sans exemple se supprime, il ne se vide pas : le bouton du prof disparaîtrait
    sans que rien dise pourquoi la ligne est restée en base."""
    with dbmod.SessionLocal() as db:
        mid = _un_couple(db)
    r = admin_client().put(f"/api/admin/ambiguite-exemples/{mid}",
                           json={"texte": "", "defauts": "- un défaut"})
    assert r.status_code == 422, r.text


# ── Désactiver, plutôt que supprimer ────────────────────────────────────────────────────────
#
# Découvrir qu'un exemple est faux imposait de le SUPPRIMER — donc de perdre le texte qu'il
# fallait justement corriger, et de tout regénérer. « Désactiver » le retire de la vue du
# professeur et garde le texte sous la main. Ce n'est pas une suppression déguisée : le mot du
# bouton dit le geste, et il rallume ce qu'il a éteint.

def test_desactiver_retire_l_exemple_au_prof_sans_perdre_le_texte():
    from backend.securite.comptes import create_access_token
    from _profil import user_couple

    with dbmod.SessionLocal() as db:
        mid = _un_couple(db)
        db.add(user_couple(db, email="prof.eteint@aschool.fr", password_hash="x",
                           is_verified=True, subject="STI", niveau="BTS CIEL"))
        db.commit()
    a = admin_client()
    a.post(f"/api/admin/ambiguite-exemples/{mid}/coller", json={"brut": REPONSE_TYPE})

    prof = TestClient(app)
    prof.cookies.set("aschool_access", create_access_token("prof.eteint@aschool.fr"))
    assert prof.get("/api/ambiguites/exemple").json()["disponible"] is True

    r = a.put(f"/api/admin/ambiguite-exemples/{mid}/actif", json={"actif": False})
    assert r.status_code == 200 and r.json()["actif"] is False
    assert prof.get("/api/ambiguites/exemple").json()["disponible"] is False

    with dbmod.SessionLocal() as db:               # le texte est TOUJOURS là
        ligne = db.query(AmbiguiteExemple).filter(AmbiguiteExemple.matiere_id == mid).first()
        assert ligne is not None and ligne.texte.startswith("Sujet — Sécurisation")

    assert a.put(f"/api/admin/ambiguite-exemples/{mid}/actif", json={"actif": True}).json()["actif"] is True
    assert prof.get("/api/ambiguites/exemple").json()["disponible"] is True


def test_reecrire_un_exemple_eteint_le_rallume():
    """Recoller un texte, c'est dire « voilà le bon ». Le laisser éteint le rendrait invisible
    sans raison, et l'admin chercherait longtemps pourquoi le prof ne le voit pas."""
    with dbmod.SessionLocal() as db:
        mid = _un_couple(db)
    c = admin_client()
    c.post(f"/api/admin/ambiguite-exemples/{mid}/coller", json={"brut": REPONSE_TYPE})
    c.put(f"/api/admin/ambiguite-exemples/{mid}/actif", json={"actif": False})

    r = c.put(f"/api/admin/ambiguite-exemples/{mid}",
              json={"texte": "La version corrigée.", "defauts": "- un défaut"})
    assert r.status_code == 200 and r.json()["actif"] is True


def test_un_exemple_eteint_ne_compte_pas_comme_fait():
    """Le compteur de la cartouche dit ce que le PROFESSEUR reçoit : une pastille verte sur un
    exemple éteint annoncerait un travail que personne ne voit."""
    with dbmod.SessionLocal() as db:
        cid, niveau, mid = _couple_ciel(db)
    c = admin_client()
    c.post(f"/api/admin/ambiguite-exemples/{mid}/coller", json={"brut": REPONSE_TYPE})
    assert c.get(f"/api/admin/referentiels/ambiguites/etat?cycle_id={cid}&niveau={niveau}").json()["ecrits"] == 1

    c.put(f"/api/admin/ambiguite-exemples/{mid}/actif", json={"actif": False})
    d = c.get(f"/api/admin/referentiels/ambiguites/etat?cycle_id={cid}&niveau={niveau}").json()
    assert d["ecrits"] == 0
    assert any(m["nom"] == "STI" and m["ecrit"] is False for m in d["matieres"])


def test_basculer_un_couple_sans_exemple_est_un_404():
    with dbmod.SessionLocal() as db:
        mid = _un_couple(db)
    assert admin_client().put(f"/api/admin/ambiguite-exemples/{mid}/actif",
                              json={"actif": False}).status_code == 404
