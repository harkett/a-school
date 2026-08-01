"""Rien en dur dans le code : une donnée métier ou un choix de config vit EN BASE.

CE QUE CE TEST ATTRAPE — deux formes, celles que la règle nomme explicitement :
  (1) un dictionnaire, une liste, un tuple ou un ensemble de chaînes déclaré AU NIVEAU MODULE
      (« valeur, constante, dict, mapping, liste ») ;
  (2) un `if x in ("a", "b")` — la forme « if/elif » de la règle, celle qui décide d'un
      comportement métier à partir de valeurs écrites dans le code.

CE QUE CE TEST N'ATTRAPE PAS. À lire avant de croire la suite verte :
  - une comparaison isolée (`if x == "brouillon"`) — trop fréquente et trop souvent technique
    pour distinguer le métier du reste sans crier au loup en permanence ;
  - une constante seule (`TEMPERATURE_MIN = 0.0`) ;
  - une liste construite dynamiquement, ou déclarée à l'intérieur d'une fonction ;
  - le front, entièrement.
La couverture n'est donc PAS totale. Elle est mécanique et sans faux positif : ce qu'elle
signale est toujours réel. Trois tests par sujet la complètent là où elle ne va pas —
`test_catalogues_en_base.py`, `test_seuils_en_base.py`, `test_prompts_en_base.py` — et eux
vérifient la moitié qui compte le plus : base vide = erreur claire, jamais un repli code.

LISTE D'EXCEPTIONS — GELÉE le 31/07/2026. Deux catégories qu'on ne mélange jamais :
  - DETTE : donnée métier qui devrait vivre en base, à corriger un jour ;
  - EXCEPTION PERMANENTE : plomberie technique (formats de fichier, schéma JSON) ou registre
    déjà gelé et gardé par un autre test.
On ne l'allonge JAMAIS sans décision explicite de l'utilisateur.

Les clés sont « fichier:NOM » et « fichier::valeurs », jamais un numéro de ligne : insérer dix
lignes plus haut ne doit pas faire tomber la suite pour rien.

Lance avec : pytest (BDD jetable aschool_test via conftest.py — jamais la base dev).
"""
import ast
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

BACKEND = os.path.join(os.path.dirname(ROOT), "backend")

# --- DETTE — donnée métier écrite dans le code, à faire descendre en base -------------------
DETTE = {
    "backend/contenu/activites.py:_USER_PARAMS":
        "activites.py:43 — les clés (nb, sous_type, langue) SONT `type_parametres.cle` en base ; "
        "seule leur formulation est recopiée ici.",
    "backend/contenu/mes_contenus.py:JALON_LABELS":
        "mes_contenus.py:295 — libellés des jalons de l'historique ; aucune table `jalons`.",
    "backend/contenu/mes_contenus.py:PHASES_ESQUISSE":
        "mes_contenus.py:898 — les 3 phases A/B/C de l'esquisse ; aucune table.",
    "backend/systeme/maintenance.py:CATEGORIES":
        "maintenance.py:17 — catégories de ménage AVEC leurs seuils ; aucune table.",
    "backend/contenu/activites.py::academique|operationnel":
        "activites.py:438 — les deux tons de rédaction ; aucune table `tons` (44 tables, "
        "vérifié). Le PROMPT de chaque ton est en base, la LISTE des tons ne l'est pas.",
    "backend/llm/generator.py::anthropic|groq":
        "generator.py:94 — les fournisseurs IA en dur ALORS QUE la table `ai_fournisseurs` "
        "existe avec sa colonne `code`. La plus nette des cinq.",
}

# --- EXCEPTION PERMANENTE — plomberie technique ou registre déjà gardé ailleurs -------------
EXCEPTIONS_PERMANENTES = {
    # Faux ami : le nom sonne métier, le contenu est du type MIME. Vérifié avant de classer.
    "backend/communication/feedback.py:ALLOWED_TYPES":
        "feedback.py:28 — types MIME → extension. Plomberie de fichier, pas une donnée métier.",
    "backend/core/llm_prompts.py:PROMPTS":
        "llm_prompts.py:701 — le registre des prompts. Il est SEMÉ par migration et comparé à "
        "la liste gelée par test_prompts_en_base.py : la base reste la source, ce dict est le "
        "texte d'origine, pas un repli.",
    "backend/dictee/transcribe.py:_ALLOWED_EXT":
        "transcribe.py:28 — extensions audio acceptées. Technique.",
    "backend/rag/analyse_amont.py:_SCHEMA_DECOUPE":
        "analyse_amont.py:43 — schéma JSON attendu du modèle. Technique.",
    "backend/dictee/ocr.py::jpeg|jpg|png":
        "ocr.py:65 — extensions d'image acceptées. Technique.",
}

TOLERE = set(DETTE) | set(EXCEPTIONS_PERMANENTES)


def _fichiers_python():
    for racine, _, fichiers in os.walk(BACKEND):
        if "__pycache__" in racine:
            continue
        for f in sorted(fichiers):
            if f.endswith(".py"):
                yield os.path.join(racine, f)


def _chemin_court(p):
    return "backend/" + os.path.relpath(p, BACKEND).replace(os.sep, "/")


def _est_liste_de_chaines(noeud, mini):
    return (isinstance(noeud, (ast.List, ast.Tuple, ast.Set))
            and len(noeud.elts) >= mini
            and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in noeud.elts))


def _scanner():
    """Rend [(cle, chemin, ligne, description)] pour les deux formes surveillées."""
    trouves = []
    for chemin in _fichiers_python():
        court = _chemin_court(chemin)
        try:
            arbre = ast.parse(open(chemin, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue

        # Forme (1) — déclaration au niveau module
        for n in arbre.body:
            if not isinstance(n, (ast.Assign, ast.AnnAssign)):
                continue
            valeur = n.value
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
                nom = n.targets[0].id
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                nom = n.target.id
            else:
                continue
            est_dict = (isinstance(valeur, ast.Dict) and len(valeur.keys) >= 3
                        and all(isinstance(k, ast.Constant) and isinstance(k.value, str)
                                for k in valeur.keys))
            if _est_liste_de_chaines(valeur, 3) or est_dict:
                trouves.append((f"{court}:{nom}", court, n.lineno,
                                f"{nom} — liste/dict de chaînes déclaré au niveau module"))

        # Forme (2) — `x in ("a", "b")`
        for n in ast.walk(arbre):
            if not (isinstance(n, ast.Compare) and len(n.ops) == 1
                    and isinstance(n.ops[0], (ast.In, ast.NotIn))):
                continue
            cible = n.comparators[0]
            if not _est_liste_de_chaines(cible, 2):
                continue
            valeurs = "|".join(sorted(e.value for e in cible.elts))
            trouves.append((f"{court}::{valeurs}", court, n.lineno,
                            f"appartenance à ({valeurs}) écrite dans le code"))
    return trouves


def test_aucune_donnee_metier_nouvelle_ecrite_en_dur():
    """Le filet. Toute forme surveillée NON inscrite dans la liste gelée fait tomber la suite."""
    nouvelles = [
        f"{chemin}:{ligne} — {description}\n      Cette donnée doit-elle vivre en "
        f"base ? Si oui, la LIRE (get), jamais l'écrire ici."
        for cle, chemin, ligne, description in _scanner()
        if cle not in TOLERE
    ]
    assert not nouvelles, (
        "Une donnée métier est écrite en dur à un endroit NOUVEAU :\n  - "
        + "\n  - ".join(nouvelles)
        + "\n\nCe test ne s'affaiblit pas : soit la donnée descend en base, soit l'utilisateur "
          "décide explicitement de l'inscrire à la dette ou aux exceptions permanentes."
    )


def test_la_liste_ne_garde_pas_une_entree_disparue():
    """Une entrée réparée ou supprimée doit sortir de la liste, sinon la dette ment sur elle."""
    reelles = {cle for cle, _, _, _ in _scanner()}
    fantomes = sorted(TOLERE - reelles)
    assert not fantomes, (
        "Ces entrées ne sont plus dans le code mais traînent encore dans la liste :\n  - "
        + "\n  - ".join(fantomes)
        + "\n\nRetire-les du fichier : la dette doit rester comptable."
    )


def test_le_compte_de_la_dette_est_celui_du_31_07_2026():
    """Le chiffre de départ. Il ne bouge qu'en BAISSE, et une baisse fait tomber ce test —
    réparer une dette se conclut en corrigeant ce nombre."""
    assert len(DETTE) == 6, (
        f"Dette « en dur » : {len(DETTE)} entrées, 6 attendues (état gelé du 31/07/2026)."
    )
    assert len(EXCEPTIONS_PERMANENTES) == 5, (
        f"Exceptions permanentes : {len(EXCEPTIONS_PERMANENTES)}, 5 attendues."
    )
