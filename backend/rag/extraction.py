"""Extraction ÉPURÉE du texte d'un référentiel PDF — LA porte unique.

Le PDF officiel reste INTACT sur le disque (pièce d'origine, relue par l'admin) ; l'épuration
se fait sur le TEXTE extrait, celui que toutes les étapes IA consomment (vérif du couple,
matières, prompt de découpe, découpe → unités). Une seule fonction, une seule place : tout
le monde lit le même texte propre.

Ce qu'on épure (bruit d'extraction, jamais du contenu) :
  - le TEXTE VERTICAL des marges de tableaux (« Tâches », « Résultats attendus »… écrits de
    bas en haut) : l'extraction le rend lettre par lettre, éparpillé dans les lignes — on
    repère sa signature géométrique (lettres seules, sans voisin horizontal, empilées à la
    même position x) et on écarte ces caractères AVANT de lire la page ;
  - les NUMÉROS DE PAGE : lignes qui ne contiennent qu'un nombre seul.

GÉNÉRIQUE : aucune règle propre à un document (positions apprises sur la page, pas codées).
Pur pdfplumber + géométrie — aucune IA, déterministe, testable.
"""
import re
from collections import defaultdict
from pathlib import Path

# Registre des règles d'épuration — LA source de ce que l'écran admin AFFICHE (consultation
# pure : l'admin voit, ne modifie pas ; une nouvelle règle se fabrique avec le DEV et s'ajoute
# ICI, à côté de son mécanisme). Toujours toutes actives : la qualité ne se désactive pas.
REGLES_EPURATION = [
    {
        "nom": "Numéros de page",
        "description": "Les lignes qui ne contiennent qu'un nombre seul (le numéro de page que "
                       "l'extraction du PDF colle au fil du texte) sont retirées. Un nombre porteur "
                       "de sens vit toujours dans une phrase ou une liste — jamais seul sur sa ligne.",
    },
    {
        "nom": "Texte vertical des marges",
        "description": "Les mots écrits verticalement dans les marges de tableaux (ex. « Tâches », "
                       "« Résultats attendus ») ressortent lettre par lettre, éparpillés dans le texte. "
                       "Leur signature géométrique — des lettres seules, sans voisines, empilées à la "
                       "même position — est repérée et ces caractères sont écartés avant la lecture.",
    },
]


def _sans_numeros_de_page(texte: str) -> str:
    """Retire les lignes qui ne contiennent QU'UN nombre : les numéros de page que l'extraction
    du PDF colle au fil du texte (ex. « 34 » seul en fin d'unité). Un nombre porteur de sens dans
    un référentiel vit toujours DANS une phrase ou une liste — jamais seul sur sa ligne. Pur,
    déterministe, testable seul."""
    return "\n".join(l for l in texte.split("\n") if not re.fullmatch(r"\s*\d{1,4}\s*", l))


def _cles_lettres_verticales(chars: list[dict]) -> set[tuple]:
    """Repère les caractères du TEXTE VERTICAL d'une page : une lettre SEULE (sans voisin
    horizontal immédiat, à gauche comme à droite) qui appartient à une pile d'au moins 3
    lettres seules à la même position x. C'est la signature d'un mot écrit de bas en haut
    dans une marge de tableau — jamais celle d'un texte normal (ses lettres se touchent).
    Renvoie les clés (x0, top, texte) des caractères à écarter. Pur, testable seul."""
    # Index par ligne visuelle (top arrondi) pour chercher les voisins sans tout balayer.
    par_ligne: dict[int, list[dict]] = defaultdict(list)
    for c in chars:
        par_ligne[round(c["top"])].append(c)

    def a_un_voisin(c: dict) -> bool:
        for k in (round(c["top"]) - 1, round(c["top"]), round(c["top"]) + 1):
            for d in par_ligne.get(k, ()):
                if d is c or abs(d["top"] - c["top"]) > 2:
                    continue
                if -1 <= d["x0"] - c["x1"] <= 3:   # un caractère commence juste après lui
                    return True
                if -1 <= c["x0"] - d["x1"] <= 3:   # un caractère finit juste avant lui
                    return True
        return False

    isolees = [c for c in chars
               if len(c["text"]) == 1 and c["text"].isalpha() and not a_un_voisin(c)]
    piles: dict[int, list[dict]] = defaultdict(list)
    for c in isolees:
        piles[int(c["x0"] // 3)].append(c)   # bande de 3 points : même colonne
    debris: set[tuple] = set()
    for pile in piles.values():
        if len(pile) >= 3:                   # une vraie colonne, pas une lettre perdue
            for c in pile:
                debris.add((c["x0"], c["top"], c["text"]))
    return debris


def extraire_texte(pdf_path: Path | str, max_pages: int | None = None) -> str:
    """Texte ÉPURÉ du PDF : extraction page par page SANS les caractères du texte vertical,
    puis retrait des lignes numéros-de-page. C'est CE texte que toutes les étapes IA lisent."""
    import pdfplumber  # import paresseux : ne pas alourdir le démarrage du serveur
    pages_txt: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        pages = pdf.pages[:max_pages] if max_pages else pdf.pages
        for page in pages:
            debris = _cles_lettres_verticales(page.chars)
            if debris:
                page = page.filter(
                    lambda o, _d=debris: not (o.get("object_type") == "char"
                                              and (o.get("x0"), o.get("top"), o.get("text")) in _d))
            pages_txt.append(page.extract_text() or "")
    return _sans_numeros_de_page("\n".join(pages_txt)).strip()
