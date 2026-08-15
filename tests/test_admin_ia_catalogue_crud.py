r"""Preuve de raccordement — le CRUD du catalogue IA écrit VRAIMENT en base, et refuse ce qu'il doit.

CE QUE CES SIX ROUTES CHANGENT. Raccorder un fournisseur ou offrir un modèle de plus demandait
une migration, donc un développeur ; l'admin le fait maintenant depuis son écran. Six routes
d'écriture — trois pour les fournisseurs, trois pour les modèles — et AUCUNE n'avait de test le
10/08/2026. Une route qui écrit sans test est une route dont on découvre le comportement en
production.

CE QUE LE TEST PROUVE, en chaîne réelle :
  1. POST crée pour de bon (la ligne est en base, relue depuis une autre session) ;
  2. PUT modifie, et le `code` de l'URL fait foi — l'identifiant technique ne bouge pas ;
  3. DELETE supprime VRAIMENT (la ligne n'est plus là), ce n'est pas un `actif=False` déguisé ;
  4. les trois refus qui protègent le service : type d'API inconnu, fournisseur EN SERVICE,
     fournisseur qui a encore des modèles ;
  5. sans cookie admin : 401 sur les six.

CE QU'IL N'APPELLE PAS : aucun fournisseur d'IA. Ces routes ne parlent qu'à la base — elles
décrivent le catalogue, elles ne s'en servent pas.

Lancer : docker compose exec backend python -m pytest tests/test_admin_ia_catalogue_crud.py -q
"""
from conftest import resemer_reglages

import backend.core.database as dbmod
from backend.core.models_db import AiFournisseur, AiModele, Setting
from backend.main import app
from backend.systeme.admin import _make_admin_token
from fastapi.testclient import TestClient

FOURNISSEUR = {"code": "essai_llm", "label": "Essai", "type_api": "openai_compat",
               "base_url": "https://exemple.test/v1", "cle_env": "ESSAI_API_KEY",
               "max_tokens": 4096, "actif": True, "ordre": 9}
MODELE = {"fournisseur": "essai_llm", "modele": "essai/petit-1", "label": "Petit 1",
          "contexte_max": 8192, "max_tokens": 2048, "actif": True, "ordre": 1}


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


def _en_service(fournisseur: str, modele: str) -> None:
    """Pose le couple en service SANS passer par les écrans : c'est l'état qu'on veut éprouver."""
    db = dbmod.SessionLocal()
    try:
        for cle, val in (("ai_provider", fournisseur), ("ai_model", modele)):
            db.query(Setting).filter(Setting.key == cle).delete()
            db.add(Setting(key=cle, value=val))
        db.commit()
    finally:
        db.close()


def _lire_fournisseur(code: str):
    db = dbmod.SessionLocal()
    try:
        return db.query(AiFournisseur).filter(AiFournisseur.code == code).first()
    finally:
        db.close()


def _lire_modele(code: str, modele: str):
    db = dbmod.SessionLocal()
    try:
        return (db.query(AiModele)
                  .filter(AiModele.fournisseur == code, AiModele.modele == modele).first())
    finally:
        db.close()


def test_fournisseur_cree_modifie_supprime():
    """Le cycle complet, chaque étape vérifiée EN BASE et non sur le code retour."""
    resemer_reglages()
    c = _admin()

    assert c.post("/api/admin/ia/fournisseurs", json=FOURNISSEUR).status_code == 200
    f = _lire_fournisseur("essai_llm")
    assert f is not None and f.label == "Essai" and f.cle_env == "ESSAI_API_KEY"

    modifie = {**FOURNISSEUR, "label": "Essai renommé", "ordre": 3}
    assert c.put("/api/admin/ia/fournisseurs/essai_llm", json=modifie).status_code == 200
    f = _lire_fournisseur("essai_llm")
    assert f.label == "Essai renommé" and f.ordre == 3

    assert c.delete("/api/admin/ia/fournisseurs/essai_llm").status_code == 200
    assert _lire_fournisseur("essai_llm") is None, (
        "« Supprimer » doit supprimer : la ligne est encore là."
    )


def test_modele_cree_modifie_supprime():
    resemer_reglages()
    c = _admin()
    c.post("/api/admin/ia/fournisseurs", json=FOURNISSEUR)

    assert c.post("/api/admin/ia/modeles", json=MODELE).status_code == 200
    m = _lire_modele("essai_llm", "essai/petit-1")
    assert m is not None and m.contexte_max == 8192

    # L'identifiant contient une barre oblique : c'est le cas que `{modele:path}` doit attraper.
    modifie = {**MODELE, "label": "Petit 1 (revu)", "max_tokens": 4096}
    r = c.put("/api/admin/ia/modeles/essai_llm/essai/petit-1", json=modifie)
    assert r.status_code == 200, r.text
    m = _lire_modele("essai_llm", "essai/petit-1")
    assert m.label == "Petit 1 (revu)" and m.max_tokens == 4096

    assert c.delete("/api/admin/ia/modeles/essai_llm/essai/petit-1").status_code == 200
    assert _lire_modele("essai_llm", "essai/petit-1") is None


def test_type_api_inconnu_refuse():
    """Offrir une famille d'API que le moteur ne sait pas parler ne raccorderait rien."""
    resemer_reglages()
    r = _admin().post("/api/admin/ia/fournisseurs", json={**FOURNISSEUR, "type_api": "mistral_natif"})
    assert r.status_code == 400
    assert _lire_fournisseur("essai_llm") is None, "Refusé, donc rien ne doit être écrit."


def test_on_ne_supprime_pas_le_dernier_fournisseur_debout(monkeypatch):
    """CE QUI A CHANGÉ. Le code protégeait le fournisseur « en service » — l'élu unique de l'ancien
    système. Il n'y a plus d'élu : il y a une LISTE, et tous ceux qui y sont répondent aux
    professeurs. En retirer un parmi plusieurs est légitime, la liste continue sans lui.

    Ce qui reste interdit, c'est de retirer LE DERNIER : un clic dans un écran de catalogue
    éteindrait l'IA de toute l'application.

    Le fournisseur doit être VRAIMENT opérationnel pour compter — clé présente dans
    l'environnement et modèle actif — sinon il n'est pas dans la liste et rien ne le protège."""
    resemer_reglages()
    monkeypatch.setenv("ESSAI_API_KEY", "clé-de-test")
    c = _admin()
    c.post("/api/admin/ia/fournisseurs", json=FOURNISSEUR)
    c.post("/api/admin/ia/modeles", json=MODELE)

    r = c.delete("/api/admin/ia/fournisseurs/essai_llm")
    assert r.status_code == 400, f"la suppression a été acceptée : {r.status_code}"
    assert _lire_fournisseur("essai_llm") is not None


def test_on_ne_supprime_pas_un_fournisseur_qui_a_des_modeles():
    """Ils partiraient avec, en silence. L'ordre est explicite : ses modèles d'abord."""
    resemer_reglages()
    c = _admin()
    c.post("/api/admin/ia/fournisseurs", json=FOURNISSEUR)
    c.post("/api/admin/ia/modeles", json=MODELE)

    r = c.delete("/api/admin/ia/fournisseurs/essai_llm")
    assert r.status_code == 400 and "modèle" in r.json()["detail"]
    assert _lire_fournisseur("essai_llm") is not None


def test_sans_cookie_admin_les_six_routes_refusent():
    """Le catalogue IA porte les noms des variables d'environnement : il ne s'ouvre pas."""
    c = TestClient(app)
    appels = [
        ("post", "/api/admin/ia/fournisseurs", FOURNISSEUR),
        ("put", "/api/admin/ia/fournisseurs/essai_llm", FOURNISSEUR),
        ("delete", "/api/admin/ia/fournisseurs/essai_llm", None),
        ("post", "/api/admin/ia/modeles", MODELE),
        ("put", "/api/admin/ia/modeles/essai_llm/essai/petit-1", MODELE),
        ("delete", "/api/admin/ia/modeles/essai_llm/essai/petit-1", None),
    ]
    for methode, chemin, corps in appels:
        r = getattr(c, methode)(chemin, json=corps) if corps else getattr(c, methode)(chemin)
        assert r.status_code == 401, f"{methode.upper()} {chemin} devrait refuser, il rend {r.status_code}"


# ── Ce qui a servi ne se supprime plus ──────────────────────────────────────────────────────────
#
# DÉCIDÉ LE 15/08/2026. Les appels passés gardent le CODE du fournisseur et le NOM du modèle, mais
# ni le libellé ni les tarifs — ceux-là vivent dans le catalogue. Effacer la ligne ne détruit pas
# l'historique : elle le rend ILLISIBLE, et surtout elle rend les coûts incalculables, puisque le
# tarif appartenait au modèle effacé. C'est une perte silencieuse, que personne ne remarque avant
# de chercher combien a coûté le mois dernier.

def _pose_un_appel(fournisseur: str, modele: str):
    """Une ligne dans `usage_llm` — le fournisseur a répondu une fois."""
    from backend.core.database import SessionLocal
    from backend.core.models_db import UsageLlm
    db = SessionLocal()
    try:
        db.add(UsageLlm(fournisseur=fournisseur, modele=modele, outil="essai",
                        tokens_entree=10, tokens_sortie=5, resultat="ok"))
        db.commit()
    finally:
        db.close()


def _efface_les_appels(fournisseur: str):
    from backend.core.database import SessionLocal
    from backend.core.models_db import UsageLlm
    db = SessionLocal()
    try:
        db.query(UsageLlm).filter(UsageLlm.fournisseur == fournisseur).delete()
        db.commit()
    finally:
        db.close()


def test_un_fournisseur_qui_a_servi_ne_se_supprime_plus():
    """Il se désactive. Le message doit dire le nombre d'appels : « impossible » se subit,
    « il a déjà répondu à 1 appel » s'explique."""
    resemer_reglages()
    c = _admin()
    c.post("/api/admin/ia/fournisseurs", json=FOURNISSEUR)
    _pose_un_appel("essai_llm", "essai/petit-1")
    try:
        r = c.delete("/api/admin/ia/fournisseurs/essai_llm")
        assert r.status_code == 400, "un fournisseur qui a servi a pu être supprimé"
        detail = r.json()["detail"]
        assert "Désactivez" in detail, f"le message ne propose pas la désactivation : {detail}"
        assert _lire_fournisseur("essai_llm") is not None
    finally:
        _efface_les_appels("essai_llm")


def test_un_modele_qui_a_produit_ne_se_supprime_plus():
    """Son tarif disparaîtrait avec lui, et le coût des réponses déjà produites deviendrait
    incalculable pour toujours."""
    resemer_reglages()
    c = _admin()
    c.post("/api/admin/ia/fournisseurs", json=FOURNISSEUR)
    c.post("/api/admin/ia/modeles", json=MODELE)
    _pose_un_appel("essai_llm", "essai/petit-1")
    try:
        r = c.delete("/api/admin/ia/modeles/essai_llm/essai/petit-1")
        assert r.status_code == 400, "un modèle qui a produit a pu être supprimé"
        assert "Désactivez" in r.json()["detail"]
    finally:
        _efface_les_appels("essai_llm")


def test_ce_qui_n_a_jamais_servi_se_supprime_encore():
    """La règle n'est pas « on ne supprime plus rien » : un fournisseur raccordé par erreur, qui
    n'a jamais été appelé, n'a aucun historique à protéger."""
    resemer_reglages()
    c = _admin()
    c.post("/api/admin/ia/fournisseurs", json=FOURNISSEUR)

    r = c.delete("/api/admin/ia/fournisseurs/essai_llm")
    assert r.status_code == 200, f"un fournisseur jamais utilisé devrait être supprimable : {r.text[:200]}"
    assert _lire_fournisseur("essai_llm") is None


def test_le_catalogue_dit_combien_d_appels_chacun_a_recus():
    """Sans ce chiffre, l'écran ne peut pas griser le bouton : l'admin découvrirait l'interdit
    après avoir cliqué, et sans savoir pourquoi."""
    resemer_reglages()
    c = _admin()
    c.post("/api/admin/ia/fournisseurs", json=FOURNISSEUR)
    c.post("/api/admin/ia/modeles", json=MODELE)
    _pose_un_appel("essai_llm", "essai/petit-1")
    try:
        corps = c.get("/api/admin/ia/catalogue").json()
        f = next(x for x in corps["fournisseurs"] if x["code"] == "essai_llm")
        m = next(x for x in corps["modeles"] if x["modele"] == "essai/petit-1")
        assert f["appels"] == 1, f"le catalogue annonce {f['appels']} appel(s) au lieu de 1"
        assert m["appels"] == 1
    finally:
        _efface_les_appels("essai_llm")


def test_la_tarification_est_dite_par_l_admin_et_relue_telle_quelle():
    """Gratuit ou payant : une DÉCISION, jamais un calcul.

    Le tarif des modèles ne peut pas répondre à cette question — un prix à zéro veut aussi bien
    dire « offert » que « pas encore relevé », et un plan gratuit devient payant sans qu'aucun
    chiffre ne bouge chez nous. Ce test vérifie donc les trois moments : ce qu'on écrit à la
    création, ce qu'on peut changer ensuite, et ce que l'écran relit."""
    resemer_reglages()
    c = _admin()
    # Défaut : « payant ». C'est celui qui ne peut pas tromper — annoncer gratuit à tort ferait
    # ranger parmi les gratuits un service qui facture.
    c.post("/api/admin/ia/fournisseurs", json=FOURNISSEUR)
    assert _lire_fournisseur("essai_llm").tarification == "payant"

    r = c.put("/api/admin/ia/fournisseurs/essai_llm",
              json={**FOURNISSEUR, "tarification": "gratuit"})
    assert r.status_code == 200, r.text[:200]
    assert _lire_fournisseur("essai_llm").tarification == "gratuit"

    corps = c.get("/api/admin/ia/catalogue").json()
    f = next(x for x in corps["fournisseurs"] if x["code"] == "essai_llm")
    assert f["tarification"] == "gratuit", "l'écran ne peut pas ranger la liste sans ce champ"


def test_une_tarification_inconnue_est_refusee():
    """Une troisième valeur ferait disparaître le fournisseur de l'écran : ni dans la zone des
    gratuits, ni dans celle des payants, et aucun message pour dire pourquoi."""
    resemer_reglages()
    c = _admin()
    r = c.post("/api/admin/ia/fournisseurs", json={**FOURNISSEUR, "tarification": "offert"})
    assert r.status_code == 400, f"« offert » aurait dû être refusé : {r.status_code}"
    assert _lire_fournisseur("essai_llm") is None, "refusé, donc rien n'est écrit"


def test_le_modele_garde_les_deux_noms_du_fournisseur():
    """Le nom d'APPEL et le nom PUBLIC sont deux faits du fournisseur, pas deux façons de nommer.

    Infomaniak n'accepte que « mistral3 » dans une requête — le nom long est refusé — mais publie
    « mistralai/Ministral-3-14B-Instruct-2512 » dans sa liste et sur sa grille tarifaire. Sans les
    deux, retrouver ce que coûte un modèle se fait au jugé."""
    resemer_reglages()
    c = _admin()
    c.post("/api/admin/ia/fournisseurs", json=FOURNISSEUR)
    c.post("/api/admin/ia/modeles",
           json={**MODELE, "nom_fournisseur": "essai-labo/Petit-1-14B-Instruct"})

    corps = c.get("/api/admin/ia/catalogue").json()
    m = next(x for x in corps["modeles"] if x["modele"] == "essai/petit-1")
    assert m["nom_fournisseur"] == "essai-labo/Petit-1-14B-Instruct"
    assert m["modele"] == "essai/petit-1", "le nom d'appel ne bouge pas : c'est lui qui part dans la requête"

    # Vide quand les deux noms sont le même (Anthropic, Groq) : on n'écrit pas deux fois la même
    # chose, et « vide » se lit « identique ».
    r = c.put("/api/admin/ia/modeles/essai_llm/essai/petit-1",
              json={**MODELE, "nom_fournisseur": "   "})
    assert r.status_code == 200, r.text[:200]
    corps = c.get("/api/admin/ia/catalogue").json()
    m = next(x for x in corps["modeles"] if x["modele"] == "essai/petit-1")
    assert m["nom_fournisseur"] is None, "un nom vide se range en base comme absent, pas comme espaces"
