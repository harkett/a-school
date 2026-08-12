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
    {
        "nom": "En-têtes et pieds de page",
        "description": "La bande répétée en haut ou en bas de chaque page (titre du document, "
                       "mention d'usage, nom de l'éditeur) est collée au fil du texte par "
                       "l'extraction, souvent AU MILIEU d'une phrase coupée par le saut de page. "
                       "Elle est reconnue à sa POSITION : un même texte, toujours à la même "
                       "hauteur exacte, dans la marge haute ou basse, sur au moins trois pages. "
                       "Une phrase de contenu se répète parfois d'une page à l'autre, mais jamais "
                       "au millimètre près dans la marge — c'est ce qui la met à l'abri.",
    },
]


def _sans_numeros_de_page(texte: str) -> str:
    """Retire les lignes qui ne contiennent QU'UN nombre : les numéros de page que l'extraction
    du PDF colle au fil du texte (ex. « 34 » seul en fin d'unité). Un nombre porteur de sens dans
    un référentiel vit toujours DANS une phrase ou une liste — jamais seul sur sa ligne. Pur,
    déterministe, testable seul."""
    return "\n".join(l for l in texte.split("\n") if not re.fullmatch(r"\s*\d{1,4}\s*", l))


# Ce qui fait un bandeau, et non une phrase qui se répète.
#
# Mesuré sur les référentiels en service (11/08/2026) : les vrais en-têtes et pieds se tiennent
# à 4,4 % / 5,5 % / 5,7 % du haut, ou à 94,5 % / 95,6 % / 97,8 % — toujours la MÊME valeur d'une
# page à l'autre. Juste en dessous commence le contenu : un titre de section répété (« Pôle
# « VALORISATION DE LA DONNÉE ET CYBERSÉCURITÉ » », BTS CIEL) vit à 7,9 %, et il porte le
# rattachement des unités qui le suivent — le perdre coûterait plus cher que garder un bandeau.
_MARGE_HAUTE = 6.0      # % de la hauteur de page
_MARGE_BASSE = 94.0
_PAGES_POUR_UN_BANDEAU = 3


def _bandeaux(lignes_par_page: list[list[dict]], hauteur: float) -> set[tuple]:
    """Les (position, texte) qui reviennent à l'identique dans les marges → ce sont des bandeaux.

    La répétition SEULE ne suffit pas : « Ce que fait le professionnel : » ouvre chaque fiche
    d'un référentiel crèche, et « Face à un ensemble de faits, des actions appropriées » revient
    sur douze pages du BTS CIEL — mais à chaque fois à une hauteur différente, parce que c'est du
    texte qui coule. Un bandeau, lui, est posé : même texte, même hauteur, page après page.
    Pur, déterministe, testable seul."""
    from collections import Counter

    vus = Counter()
    for lignes in lignes_par_page:
        # `set` : deux lignes identiques SUR LA MÊME PAGE ne comptent que pour une page.
        vus.update({_repere(l, hauteur) for l in lignes if _dans_la_marge(l, hauteur)})
    return {cle for cle, n in vus.items() if n >= _PAGES_POUR_UN_BANDEAU}


def _dans_la_marge(ligne: dict, hauteur: float) -> bool:
    pc = 100.0 * ligne["top"] / hauteur if hauteur else 0.0
    return pc <= _MARGE_HAUTE or pc >= _MARGE_BASSE


def _repere(ligne: dict, hauteur: float) -> tuple:
    """Le texte ET sa hauteur au dixième de pour-cent : c'est le couple qui identifie un bandeau.

    Les nombres sont neutralisés avant de comparer : la moitié des pieds de page portent leur
    numéro (« BO Santé — Protection sociale — Solidarite no2010/7 du 15 août 2010, Page170. »),
    et un texte qui change à chaque page ne se reconnaîtrait jamais lui-même."""
    sans_nombres = re.sub(r"\d+", "#", ligne["text"])
    return (round(1000.0 * ligne["top"] / hauteur) if hauteur else 0, sans_nombres)


def _sans_bandeaux(lignes_par_page: list[list[dict]], hauteur: float) -> list[str]:
    """Le texte des pages, débarrassé de leurs en-têtes et pieds répétés.

    L'extraction les colle au fil du texte, et le saut de page tombe souvent AU MILIEU d'une
    phrase : le bandeau se retrouve alors planté entre deux morceaux d'une même consigne. Le
    modèle, lui, le lit comme du contenu — un référentiel crèche a ainsi vu « Référentiel maison
    aSchool — en service, sans valeur institutionnelle » atterrir au beau milieu d'une fiche
    d'activité."""
    a_retirer = _bandeaux(lignes_par_page, hauteur)
    return ["\n".join(l["text"] for l in lignes
                      if not (_dans_la_marge(l, hauteur) and _repere(l, hauteur) in a_retirer))
            for lignes in lignes_par_page]


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


def lignes_de_bandeau(pdf_path: Path | str) -> set[str]:
    """Les TEXTES des en-têtes et pieds d'un PDF, nombres neutralisés — pour nettoyer après coup
    ce qui a déjà été découpé et rangé en base.

    Les documents déjà ingérés portent leurs bandeaux DANS leurs unités : les redécouper coûterait
    un appel d'IA par référentiel pour un défaut d'extraction. Cette fonction permet de les en
    retirer sans rien redemander à personne."""
    import pdfplumber  # import paresseux, comme extraire_texte

    lignes_par_page: list[list[dict]] = []
    hauteur = 0.0
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            hauteur = hauteur or page.height
            lignes_par_page.append(page.extract_text_lines() or [])
    return {texte for _position, texte in _bandeaux(lignes_par_page, float(hauteur or 0))}


def est_une_ligne_de_bandeau(ligne: str, bandeaux: set[str]) -> bool:
    """La ligne, comparée aux bandeaux du document — nombres neutralisés des deux côtés."""
    return re.sub(r"\d+", "#", ligne.strip()) in bandeaux


def extraire_texte(pdf_path: Path | str, max_pages: int | None = None) -> str:
    """Texte ÉPURÉ du PDF : extraction page par page SANS les caractères du texte vertical, puis
    retrait des numéros de page et des bandeaux d'en-tête et de pied. C'est CE texte que toutes
    les étapes IA lisent.

    Les bandeaux sont repérés à leur position sur la page, pas à leur place dans le flux : le
    numéro de page qui les suit parfois ne gêne donc plus rien, et il part au tour d'après."""
    import pdfplumber  # import paresseux : ne pas alourdir le démarrage du serveur
    lignes_par_page: list[list[dict]] = []
    hauteur = 0.0
    with pdfplumber.open(str(pdf_path)) as pdf:
        pages = pdf.pages[:max_pages] if max_pages else pdf.pages
        for page in pages:
            hauteur = hauteur or page.height
            debris = _cles_lettres_verticales(page.chars)
            if debris:
                page = page.filter(
                    lambda o, _d=debris: not (o.get("object_type") == "char"
                                              and (o.get("x0"), o.get("top"), o.get("text")) in _d))
            # `extract_text_lines` au lieu de `extract_text` : le rendu est identique (vérifié),
            # mais chaque ligne arrive avec sa position — sans elle, impossible de distinguer un
            # bandeau d'une phrase qui se répète.
            lignes_par_page.append(page.extract_text_lines() or [])
    hauteur = float(hauteur or 0)
    return _sans_numeros_de_page(
        "\n".join(_sans_bandeaux(lignes_par_page, hauteur))).strip()
