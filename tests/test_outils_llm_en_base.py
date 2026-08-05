# -*- coding: utf-8 -*-
r"""Le filet qui empeche l'ecran des longueurs de rater un outil — ENCORE.

L'ecran « Longueur des reponses de l'IA » ne reglait que 3 outils sur 17. Pas par negligence :
les 3 cles etaient ECRITES A LA MAIN dans le backend et dans le front, et les 14 outils ajoutes
depuis n'avaient jamais eu leur ligne. L'admin ne pouvait ni les voir, ni les changer, et rien
n'avertissait — la valeur par defaut s'appliquait en silence.

La liste vit desormais en base (`outils_llm`) et l'ecran boucle dessus. Mais une table ne se
remplit pas toute seule : un developpeur qui ajoute `get_max_tokens(db, "nouvel_outil")` sans
ecrire sa migration recreerait exactement le meme trou. C'est ce que ce test rend impossible.

CE QU'IL PROUVE, en relisant le CODE REEL (pas une liste recopiee) :
  1. tout `get_max_tokens(db, "<outil>")` du backend a sa ligne dans `outils_llm` ;
  2. aucune ligne de `outils_llm` n'est orpheline (un outil que plus personne n'appelle serait
     un champ regle dans le vide — l'histoire de `max_tokens_optimiseur`, corrigee le 02/08) ;
  3. chaque ligne porte un libelle et une aide non vides : c'est ce que l'admin lit pour savoir
     ce qu'il regle.

Il resout aussi les constantes (`_CLE_DECOUPE = "decoupe_amont"`), parce que la moitie des appels
passent par elles : un test qui ne verrait que les litteraux manquerait 7 outils sur 17.

Lancer : docker compose exec backend python -m pytest tests/test_outils_llm_en_base.py -q
"""
import ast
import os

import backend.core.database as dbmod
from backend.core.models_db import OutilLlm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")


def _fichiers_python():
    for dossier, _, fichiers in os.walk(BACKEND):
        for f in fichiers:
            if f.endswith(".py"):
                yield os.path.join(dossier, f)


def _constantes_module(arbre):
    """{NOM: "valeur"} pour les affectations de chaine au niveau module — c'est par la que
    passent `_CLE_DECOUPE`, `_CLE_COUPLE` et les autres."""
    consts = {}
    for noeud in arbre.body:
        if isinstance(noeud, ast.Assign) and isinstance(noeud.value, ast.Constant) \
                and isinstance(noeud.value.value, str):
            for cible in noeud.targets:
                if isinstance(cible, ast.Name):
                    consts[cible.id] = noeud.value.value
    return consts


def _outils_appeles():
    """Les outils reellement passes a get_max_tokens dans tout le backend : {outil: [fichiers]}.
    Un appel dont l'argument n'est ni un litteral ni une constante du module est SIGNALE, pas
    ignore : un nom d'outil calcule rendrait ce filet aveugle."""
    trouves, opaques = {}, []
    for chemin in _fichiers_python():
        # utf-8-sig : quatre fichiers du backend portent un BOM. Lus en « utf-8 » stricte,
        # ast.parse levait et l'ancien filet les sautait EN SILENCE (leçon du 01/08).
        with open(chemin, encoding="utf-8-sig") as fh:
            source = fh.read()
        arbre = ast.parse(source, filename=chemin)
        consts = _constantes_module(arbre)
        rel = os.path.relpath(chemin, ROOT).replace("\\", "/")

        for noeud in ast.walk(arbre):
            if not isinstance(noeud, ast.Call):
                continue
            f = noeud.func
            nom = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)
            if nom != "get_max_tokens" or len(noeud.args) < 2:
                continue
            arg = noeud.args[1]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                trouves.setdefault(arg.value, []).append(rel)
            elif isinstance(arg, ast.Name) and arg.id in consts:
                trouves.setdefault(consts[arg.id], []).append(rel)
            elif isinstance(arg, ast.Name) and arg.id in ("outil", "cle"):
                continue  # le parametre de la fonction get_max_tokens elle-meme (sa definition)
            else:
                opaques.append(f"{rel}:{getattr(arg, 'lineno', '?')}")
    return trouves, opaques


def _outils_en_base():
    db = dbmod.SessionLocal()
    lignes = {o.outil: (o.libelle, o.aide) for o in db.query(OutilLlm).all()}
    db.close()
    return lignes


def test_tout_outil_appele_a_sa_ligne_en_base():
    appeles, _ = _outils_appeles()
    en_base = _outils_en_base()
    assert en_base, "Table `outils_llm` vide — migration b4e8d2a6f1c9 non appliquée / non semée."

    manquants = {o: sorted(set(f)) for o, f in appeles.items() if o not in en_base}
    assert not manquants, (
        "Ces outils appellent get_max_tokens mais n'ont AUCUNE ligne dans `outils_llm` : "
        "l'écran admin ne les montrera pas et l'admin ne pourra pas les régler. "
        "Ajoutez-leur une ligne par migration.\n"
        + "\n".join(f"  - {o} (appelé dans {', '.join(f)})" for o, f in sorted(manquants.items()))
    )


def test_aucune_ligne_orpheline():
    appeles, _ = _outils_appeles()
    orphelins = sorted(set(_outils_en_base()) - set(appeles))
    assert not orphelins, (
        "Ces outils sont proposés à l'admin alors que PLUS AUCUN code ne les lit — il réglerait "
        "une valeur que personne n'utilise (c'est ce qui s'était passé avec `max_tokens_optimiseur`). "
        f"Retirez leur ligne par migration : {', '.join(orphelins)}"
    )


def test_chaque_ligne_a_un_libelle_et_une_aide():
    muettes = [o for o, (libelle, aide) in _outils_en_base().items()
               if not (libelle or "").strip() or not (aide or "").strip()]
    assert not muettes, (
        "Un outil sans libellé ou sans aide laisse l'admin régler un nombre sans savoir ce qu'il "
        f"règle : {', '.join(sorted(muettes))}"
    )


def test_aucun_appel_avec_un_nom_calcule():
    _, opaques = _outils_appeles()
    assert not opaques, (
        "Le nom de l'outil y est calculé au lieu d'être écrit : ce filet ne peut plus vérifier "
        "qu'il a sa ligne en base, et le trou d'origine peut revenir sans bruit.\n  "
        + "\n  ".join(opaques)
    )
