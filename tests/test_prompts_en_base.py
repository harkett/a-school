"""Étape 9 lot C — les prompts vivent EN BASE, et plus rien ne le cache.

Le registre déclare 35 prompts ; la base de dev n'en contenait que 3. Les 32 autres tournaient
sur le repli code de `get_prompt` : ça marchait toujours, donc personne ne voyait que la base
n'était pas la source. Ce lot sème d'abord, coupe le repli ensuite.

CE FICHIER EST LE FILET QUI REMPLACE LE REPLI. Sans lui, quelqu'un ajoute un prompt au registre,
oublie de le semer, et c'est la production qui l'apprend à la première génération.

Le test central compare le registre à la LISTE GELÉE DE LA MIGRATION, pas au contenu de la base
de test : `conftest.py` sème depuis le registre (il monte le schéma par `create_all`, sans
migrations), donc comparer le registre à la base ne prouverait rien — les deux viennent du même
dictionnaire. La migration, elle, est un texte figé, écrit une fois : c'est le seul témoin
indépendant.

Lance avec : pytest (BDD jetable aschool_test via conftest.py — jamais la base dev).
"""
import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.core.database as dbmod  # noqa: E402  (redirigé vers aschool_test par conftest)

from backend.core.llm_prompts import PROMPTS  # noqa: E402
from backend.core.models_db import SeanceMode, SeanceStyle, Setting  # noqa: E402
from backend.systeme.admin import get_prompts_settings  # noqa: E402


VERSIONS = os.path.join(os.path.dirname(ROOT), "alembic", "versions")


def _charger(nom: str):
    """Charge un fichier de migration comme module. Import par chemin, volontairement :
    `alembic/versions` n'est pas un paquet importable, et surtout on veut lire CE fichier-là —
    celui qui sera rejoué sur une base neuve."""
    spec = importlib.util.spec_from_file_location(f"_migration_{nom}",
                                                  os.path.join(VERSIONS, nom))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prompts_geles() -> dict[str, str]:
    """Ce qu'une base NEUVE contiendra vraiment : le seed gelé, PUIS les mises à jour gelées des
    migrations suivantes, appliquées dans l'ordre de la chaîne.

    Une migration ne se retouche jamais une fois appliquée : un prompt qui change se corrige par
    une migration DE MISE À JOUR, qui expose son texte figé dans `PROMPTS_MAJ`. Sans cette
    composition, ce fichier comparerait le registre au texte du premier jour et interdirait toute
    évolution — ou pire, la laisserait passer sans que la base la reçoive."""
    textes = dict(_charger("b8e5f2a1c9d7_seed_tous_les_prompts_geles.py").PROMPTS_GELES)

    # Les mises à jour, rangées dans l'ordre de la chaîne (down_revision -> revision), pour que
    # deux migrations touchant le même prompt s'appliquent comme sur une vraie base.
    majs = {}
    for nom in sorted(os.listdir(VERSIONS)):
        if not nom.endswith(".py"):
            continue
        with open(os.path.join(VERSIONS, nom), encoding="utf-8") as f:
            if "PROMPTS_MAJ" not in f.read():
                continue
        m = _charger(nom)
        majs[m.revision] = (m.down_revision, dict(m.PROMPTS_MAJ))

    ordonnees, restants = [], dict(majs)
    precedente = "b8e5f2a1c9d7"
    while restants:
        suivante = next((r for r, (dr, _) in restants.items() if dr == precedente), None)
        if suivante is None:            # mise à jour posée plus loin dans la chaîne : ordre du nom
            suivante = sorted(restants)[0]
        ordonnees.append(restants.pop(suivante)[1])
        precedente = suivante
    for maj in ordonnees:
        textes.update(maj)
    return textes


def test_chaque_prompt_du_registre_est_seme_par_la_migration():
    """LE test du lot. Ajouter un prompt au registre sans l'ajouter à la migration fait tomber
    la suite ici — au lieu que la production l'apprenne à la première génération."""
    geles = _prompts_geles()
    manquants = sorted(set(PROMPTS) - set(geles))
    assert not manquants, (
        f"Ces prompts existent au registre mais ne sont semés par aucune migration : {manquants}. "
        f"Sans repli code, l'outil qui les utilise tombera sur une base neuve.")


def test_la_migration_ne_seme_rien_qui_n_existe_plus():
    """L'autre sens : un prompt retiré du registre mais toujours semé laisserait une ligne morte
    en base, que plus personne ne lit et que personne ne pense à retirer."""
    orphelins = sorted(set(_prompts_geles()) - set(PROMPTS))
    assert not orphelins, f"Semés par la migration mais absents du registre : {orphelins}."


def test_les_textes_semes_sont_bien_ceux_du_registre():
    """Le gel doit être fidèle AU MOMENT OÙ IL A ÉTÉ PRIS. Si ce test tombe, c'est qu'un prompt
    a été retouché dans le registre sans nouvelle migration : la base d'aujourd'hui et celle
    d'une installation neuve ne diraient plus la même chose. Le remède est une migration de
    mise à jour, jamais une retouche de la migration déjà appliquée."""
    geles = _prompts_geles()
    divergents = sorted(cle for cle, meta in PROMPTS.items()
                        if cle in geles and geles[cle] != meta["default"])
    assert not divergents, (
        f"Registre et migration ne disent plus la même chose pour : {divergents}. "
        f"Ajoutez une migration de mise à jour au lieu de modifier celle qui est appliquée.")


def test_la_migration_est_gelee_elle_n_importe_pas_le_registre():
    """Une migration qui lirait `PROMPTS` sèmerait le texte DU JOUR OÙ ON LA REJOUE : deux
    installations faites à deux dates n'auraient pas le même contenu, et l'historique ne
    voudrait plus rien dire. On vérifie le fichier lui-même."""
    dossier = os.path.join(os.path.dirname(ROOT), "alembic", "versions")
    fautives = []
    for nom in os.listdir(dossier):
        if not nom.endswith(".py"):
            continue
        with open(os.path.join(dossier, nom), encoding="utf-8") as f:
            corps = f.read()
        # On ignore les docstrings : plusieurs migrations EXPLIQUENT la règle en citant le module.
        lignes_de_code = [l for l in corps.splitlines()
                          if l.startswith(("import ", "from ")) and "llm_prompts" in l]
        if lignes_de_code:
            fautives.append(nom)
    assert not fautives, (
        f"Ces migrations importent le registre au lieu de figer leur texte : {fautives}.")


def test_chaque_prompt_du_registre_a_sa_ligne_en_base():
    """Le raccordement : ce que le registre déclare existe réellement dans la base sur laquelle
    tourne l'application. (Sur la base de test, c'est conftest qui sème — la garantie de fond
    est donnée par les tests ci-dessus, qui, eux, ne dépendent pas de conftest.)"""
    with dbmod.SessionLocal() as db:
        en_base = {r.key[len("prompt_"):] for r in
                   db.query(Setting).filter(Setting.key.like("prompt_%")).all()}
        manquants = sorted(set(PROMPTS) - en_base)
        assert not manquants, f"Prompts absents de la base : {manquants}."


def test_chaque_mode_et_style_de_seance_a_son_prompt():
    """Couplage créé par le lot A, à ne pas laisser sans garde : la clé du prompt d'une séance
    est CONSTRUITE depuis le catalogue en base (`seance_{code}`, `seance_style_{code}`,
    mes_contenus.py). Un mode ajouté en base invente donc une clé que le registre n'a pas — et,
    sans repli, la génération tombe pour ce mode-là seulement. Ce test tient les deux bouts."""
    with dbmod.SessionLocal() as db:
        sans_prompt = []
        for mode in db.query(SeanceMode).filter(SeanceMode.actif.is_(True)).all():
            if f"seance_{mode.code}" not in PROMPTS:
                sans_prompt.append(f"mode « {mode.code} » → prompt seance_{mode.code}")
        for style in db.query(SeanceStyle).filter(SeanceStyle.actif.is_(True)).all():
            if f"seance_style_{style.code}" not in PROMPTS:
                sans_prompt.append(f"style « {style.code} » → prompt seance_style_{style.code}")
        assert not sans_prompt, (
            "Ces lignes de catalogue n'ont aucun prompt correspondant : " + " ; ".join(sans_prompt))


def test_l_ecran_admin_dit_quel_prompt_manque_sans_jamais_tomber():
    """Le chemin de réparation. Sans repli, un prompt absent casse son outil — il faut donc que
    l'écran d'administration DISE lequel manque. S'il levait, on perdrait l'écran par lequel on
    répare, précisément au moment où on en a besoin."""
    with dbmod.SessionLocal() as db:
        db.query(Setting).filter(Setting.key == "prompt_correction").delete()
        db.commit()

        rendu = get_prompts_settings(db=db, _=None)   # ne lève pas

        assert "correction" in rendu["manquants"]
        ligne = next(p for p in rendu["prompts"] if p["key"] == "correction")
        assert ligne["en_base"] is False
        # Les autres restent lisibles : une clé manquante n'aveugle pas tout l'écran.
        assert all(p["en_base"] for p in rendu["prompts"] if p["key"] != "correction")
