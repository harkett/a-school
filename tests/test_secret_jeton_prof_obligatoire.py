"""Le jeton du PROF ne peut plus etre signe avec une valeur ecrite dans le depot.

CE QUE CES TESTS PROUVENT. `backend/securite/comptes.py` faisait :

    SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")

Sur un serveur demarre sans `JWT_SECRET`, les jetons d'acces de TOUS les profs etaient donc
signes avec une chaine que n'importe qui lit dans le code source. MESURE sur le code d'avant,
avec ADMIN_JWT_SECRET pose (donc le garde-fou admin ne bloquait rien) :

    BOOT OK — le serveur demarre, aucun message.
    secret des jetons PROF : 'change-me-in-production'
    jeton FORGE accepte comme : victime@aschool.fr

Un tiers ayant lu le depot fabriquait un jeton valide pour le compte de son choix. Le meme
raisonnement avait pourtant deja ferme le trou cote ADMIN (`_admin_secret`, cf.
test_secret_admin_obligatoire.py) — il n'avait pas ete applique au jeton prof, celui qui
protege les donnees des enseignants.

DEUX DEFAUTS SECONDAIRES, reels aussi, couverts ici :
  - `comptes.py` lisait la variable a l'import, `middleware.py` a CHAQUE requete ;
  - leurs replis DIFFERAIENT ("change-me-in-production" contre ""), donc un serveur mal
    configure signait avec l'un et verifiait avec l'autre : aucune session ne tenait, et rien
    n'expliquait pourquoi.

Lancer : docker compose exec backend python -m pytest tests/test_secret_jeton_prof_obligatoire.py -q
"""
import ast
import importlib
import inspect
import os

import pytest
from jose import jwt

import backend.core.cles as cles
import backend.core.middleware as middleware
import backend.securite.comptes as comptes
from backend.core.cles import secret_obligatoire


# ── La regle partagee ────────────────────────────────────────────────────────────────────

def test_aucun_nom_pose_leve(monkeypatch):
    monkeypatch.delenv("UN_SECRET_QUELCONQUE", raising=False)
    with pytest.raises(RuntimeError, match="SÉCURITÉ"):
        secret_obligatoire("UN_SECRET_QUELCONQUE", usage="l'essai", quoi_poser="Posez-le.")


def test_un_secret_blanc_ne_compte_pas(monkeypatch):
    """« » passe le `or` mais ne protege rien — meme piege que cote admin."""
    monkeypatch.setenv("UN_SECRET_QUELCONQUE", "   ")
    with pytest.raises(RuntimeError, match="SÉCURITÉ"):
        secret_obligatoire("UN_SECRET_QUELCONQUE", usage="l'essai", quoi_poser="Posez-le.")


def test_l_ordre_des_noms_est_respecte(monkeypatch):
    """C'est ce qui permet a l'admin de garder SA regle (ADMIN_JWT_SECRET sinon JWT_SECRET)
    tout en partageant la lecture et le refus."""
    monkeypatch.setenv("PREMIER_NOM", "le-bon")
    monkeypatch.setenv("SECOND_NOM", "le-repli")
    assert secret_obligatoire("PREMIER_NOM", "SECOND_NOM", usage="x", quoi_poser="y") == "le-bon"
    monkeypatch.delenv("PREMIER_NOM")
    assert secret_obligatoire("PREMIER_NOM", "SECOND_NOM", usage="x", quoi_poser="y") == "le-repli"


def test_le_message_dit_quoi_poser(monkeypatch):
    """Regle 23 : le message doit etre actionnable. Il nomme la variable a poser, sinon il ne
    sert qu'a constater la panne."""
    monkeypatch.delenv("MANQUANT", raising=False)
    with pytest.raises(RuntimeError) as e:
        secret_obligatoire("MANQUANT", usage="les jetons d'essai",
                           quoi_poser="Posez MANQUANT dans le .env du serveur.")
    assert "MANQUANT" in str(e.value) and "les jetons d'essai" in str(e.value)


# ── Le refus tombe AU DEMARRAGE ──────────────────────────────────────────────────────────

def test_sans_jwt_secret_le_module_refuse_de_se_charger():
    """LE test du point. Le secret est resolu au niveau module : sans JWT_SECRET, importer
    `backend.core.cles` LEVE — donc `comptes`, `middleware` et l'application entiere ne
    montent pas. On ne demarre pas un serveur qui signerait avec une valeur connue.

    Pas de `monkeypatch` ici : la remise en etat doit se faire AVANT le rechargement final,
    et l'ordre des teardowns de pytest ne le garantit pas."""
    avant = os.environ.pop("JWT_SECRET", None)
    assert avant, "ce test suppose un JWT_SECRET pose au depart (il l'est dans le .env)"
    try:
        with pytest.raises(RuntimeError, match="SÉCURITÉ"):
            importlib.reload(cles)
    finally:
        os.environ["JWT_SECRET"] = avant
        importlib.reload(cles)

    assert cles.SECRET_JETON_PROF == avant


# ── Les consequences concretes ───────────────────────────────────────────────────────────

def test_un_jeton_signe_avec_l_ancien_repli_est_rejete():
    """La consequence directe : la valeur qui trainait dans le depot ne signe plus rien."""
    forge = jwt.encode({"sub": "victime@aschool.fr", "type": "access", "exp": 9999999999},
                       "change-me-in-production", algorithm="HS256")
    assert comptes.verify_access_token(forge) is None, (
        "un jeton forge avec « change-me-in-production » est encore accepte"
    )


def test_un_jeton_signe_avec_la_chaine_vide_est_rejete():
    """L'autre ancien repli, celui du middleware."""
    forge = jwt.encode({"sub": "victime@aschool.fr", "type": "access", "exp": 9999999999},
                       "", algorithm="HS256")
    assert comptes.verify_access_token(forge) is None


def test_signature_et_verification_lisent_la_meme_valeur():
    """Le second defaut : `comptes` lisait a l'import, `middleware` a CHAQUE requete, avec des
    replis differents — deux valeurs possibles pour une seule cle.

    On verifie la valeur, puis la SOURCE : qu'aucun des deux ne relise l'environnement pour son
    compte. C'est la source qui prouve qu'il n'y a plus qu'une lecture ; l'egalite des valeurs,
    seule, pourrait tenir par hasard sur un poste bien configure — c'est-a-dire exactement dans
    le cas ou le defaut ne se voit pas.

    (Egalite et non identite : le test de rechargement ci-dessus reconstruit la chaine de
    `cles`, donc l'identite dependrait de l'ordre des tests.)"""
    assert comptes.SECRET_JETON_PROF == middleware.SECRET_JETON_PROF == cles.SECRET_JETON_PROF

    # Lecture de l'ARBRE et non du texte : les deux fichiers CITENT l'ancien appel dans leurs
    # commentaires, pour expliquer ce qui a ete retire. Un `in source` confondrait la citation
    # avec le retour du defaut ; l'AST ne voit que le code.
    for module in (comptes, middleware):
        arbre = ast.parse(inspect.getsource(module))
        lectures = [n for n in ast.walk(arbre)
                    if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute) and n.func.attr == "getenv"
                    and n.args and isinstance(n.args[0], ast.Constant)
                    and "JWT_SECRET" in str(n.args[0].value)]
        assert not lectures, (
            f"{module.__name__} relit JWT_SECRET pour son compte (ligne "
            f"{lectures[0].lineno}) : la seconde lecture est revenue"
        )


def test_le_jeton_prof_reste_utilisable_de_bout_en_bout():
    """Un garde-fou qui casse la connexion ne garde rien. Emission puis verification."""
    jeton = comptes.create_access_token("prof.secret@aschool.fr")
    assert comptes.verify_access_token(jeton) == "prof.secret@aschool.fr"
