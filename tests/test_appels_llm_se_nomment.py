# -*- coding: utf-8 -*-
r"""Un appel LLM qui ne dit pas d'ou il vient est une depense anonyme.

L'ecran « IA > Statistiques » compte les tokens et les euros. Il sait dire COMBIEN et sur QUEL
MODELE, mais la question que l'admin pose vraiment devant une facture, c'est QUI a depense. Cette
reponse ne peut venir que de l'appelant : le moteur, lui, ne voit qu'un prompt.

D'ou le parametre `outil=` de `generate()` / `generate_stream()`. Il ne change RIEN a la requete —
il ne sert qu'a la mesure. C'est precisement ce qui le rend fragile : on peut l'oublier sans que
rien ne casse, ni au test, ni a l'execution. L'appel part, la reponse arrive, le prof est servi, et
la ligne se range en silence sous « Non precise ». C'est ce qui etait arrive aux 25 appels du
backend : un seul se nommait.

CE QUE CE TEST PROUVE, en relisant le CODE REEL :
  1. tout appel a `generate` / `generate_stream` porte un `outil=` ;
  2. ce nom n'est pas invente : il a sa ligne dans `outils_llm`, la meme table que celle qui donne
     son plafond a l'outil (`get_max_tokens`). Un nom ecrit de travers ferait apparaitre une
     tache fantome dans les statistiques, a cote de la vraie ;
  3. le nom est ECRIT (litteral ou constante de module), pas calcule — sinon ce filet devient
     aveugle exactement comme l'ancien.

Il ne verifie PAS l'inverse (« tout outil en base est appele ») : `test_outils_llm_en_base` le fait
deja, et depuis les appels a `get_max_tokens`, qui est la reference. `ocr` en est l'exemple : il a
sa ligne, il a son plafond, mais il ne passe pas par `generate()` (corps multimodal) — il se
journalise directement dans `transcribe_image`.

Lancer : docker compose exec backend python -m pytest tests/test_appels_llm_se_nomment.py -q
"""
import ast
import os

import backend.core.database as dbmod
from backend.core.models_db import OutilLlm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")

_APPELS = ("generate", "generate_stream", "generate_cached")


def _fichiers_python():
    for dossier, _, fichiers in os.walk(BACKEND):
        for f in fichiers:
            if f.endswith(".py"):
                yield os.path.join(dossier, f)


def _constantes_module(arbre):
    """{NOM: "valeur"} des affectations de chaine au niveau module — c'est par la que passent
    `_CLE_DECOUPE`, `_CLE_COUPLE` et leurs voisines."""
    consts = {}
    for noeud in arbre.body:
        if isinstance(noeud, ast.Assign) and isinstance(noeud.value, ast.Constant) \
                and isinstance(noeud.value.value, str):
            for cible in noeud.targets:
                if isinstance(cible, ast.Name):
                    consts[cible.id] = noeud.value.value
    return consts


def _appels_llm():
    """Parcourt le backend et rend (nommes, muets, opaques).

    nommes  : {outil: [fichier:ligne]}
    muets   : ["fichier:ligne"] — aucun `outil=`
    opaques : ["fichier:ligne"] — `outil=` present mais calcule (illisible pour ce filet)

    La DEFINITION de generate/generate_stream (dans llm/generator.py) n'est pas un appel : seuls
    les `ast.Call` sont regardes, la definition est un `ast.FunctionDef`. Les appels internes du
    moteur (`_anthropic(...)`, `_groq(...)`) portent d'autres noms et ne sont pas comptes."""
    nommes, muets, opaques = {}, [], []
    for chemin in _fichiers_python():
        # utf-8-sig : quatre fichiers du backend portent un BOM. En « utf-8 » stricte, ast.parse
        # levait et l'ancien filet les sautait EN SILENCE (leçon du 01/08).
        with open(chemin, encoding="utf-8-sig") as fh:
            arbre = ast.parse(fh.read(), filename=chemin)
        consts = _constantes_module(arbre)
        rel = os.path.relpath(chemin, ROOT).replace("\\", "/")

        for noeud in ast.walk(arbre):
            if not isinstance(noeud, ast.Call):
                continue
            f = noeud.func
            nom = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)
            if nom not in _APPELS:
                continue
            ou = f"{rel}:{noeud.lineno}"
            arg = next((k.value for k in noeud.keywords if k.arg == "outil"), None)
            if arg is None:
                muets.append(ou)
            elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                nommes.setdefault(arg.value, []).append(ou)
            elif isinstance(arg, ast.Name) and arg.id in consts:
                nommes.setdefault(consts[arg.id], []).append(ou)
            elif isinstance(arg, ast.Name) and arg.id == "outil":
                continue  # relais interne : la valeur vient de l'appelant, deja verifie chez lui
            else:
                opaques.append(ou)
    return nommes, muets, opaques


def _outils_en_base():
    db = dbmod.SessionLocal()
    outils = {o.outil for o in db.query(OutilLlm).all()}
    db.close()
    return outils


def test_tout_appel_llm_dit_de_quel_outil_il_vient():
    _, muets, _ = _appels_llm()
    assert not muets, (
        "Ces appels LLM ne passent pas `outil=` : leurs tokens seront comptés sous « Non précisé » "
        "dans IA › Statistiques, et l'admin ne saura pas d'où vient la dépense. Ajoutez "
        "`outil=\"<le même mot que get_max_tokens>\"`.\n  " + "\n  ".join(muets)
    )


def test_le_nom_donne_existe_bien_en_base():
    nommes, _, _ = _appels_llm()
    en_base = _outils_en_base()
    assert en_base, "Table `outils_llm` vide — migration b4e8d2a6f1c9 non appliquée / non semée."

    inconnus = {o: sorted(set(f)) for o, f in nommes.items() if o not in en_base}
    assert not inconnus, (
        "Ces appels se nomment avec un mot qui n'est PAS dans `outils_llm` : les statistiques "
        "afficheraient une tâche fantôme à côté de la vraie, et l'admin ne pourrait pas régler son "
        "plafond. Corrigez le mot, ou ajoutez sa ligne par migration.\n"
        + "\n".join(f"  - {o} (dans {', '.join(f)})" for o, f in sorted(inconnus.items()))
    )


def test_aucun_nom_calcule():
    _, _, opaques = _appels_llm()
    assert not opaques, (
        "Le nom de l'outil y est calculé au lieu d'être écrit : ce filet ne peut plus vérifier "
        "qu'il correspond à une ligne en base.\n  " + "\n  ".join(opaques)
    )
