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


def test_on_ne_supprime_pas_ce_qui_travaille():
    """Le fournisseur EN SERVICE : le supprimer ferait tomber l'erreur chez le prof, pas ici."""
    resemer_reglages()
    c = _admin()
    c.post("/api/admin/ia/fournisseurs", json=FOURNISSEUR)
    _en_service("essai_llm", "essai/petit-1")

    r = c.delete("/api/admin/ia/fournisseurs/essai_llm")
    assert r.status_code == 400 and "en service" in r.json()["detail"]
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
