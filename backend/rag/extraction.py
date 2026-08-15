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
  - les NUMÉROS DE PAGE : lignes qui ne contiennent qu'un nombre seul ;
  - le TEXTE BARRÉ des versions comparatives : les passages supprimés du programme,
    que l'extraction rend au milieu du texte en vigueur — repérés au trait fin qui
    les traverse en leur milieu, jamais à leur couleur.

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
    {
        "nom": "Texte barré",
        "description": "Un document publié en version comparative garde ses passages SUPPRIMÉS, "
                       "barrés d'un trait — l'œil les saute, l'extraction les recopie comme du "
                       "texte en vigueur. Le trait est reconnu à sa géométrie : une barre fine "
                       "posée au MILIEU des lettres qu'elle recouvre. C'est ce qui la distingue "
                       "d'un soulignement (qui passe sous les lettres) et d'une bordure de "
                       "tableau (qui tombe entre deux lignes).",
    },
]


def _est_un_numero_de_page(ligne: str) -> bool:
    """Une ligne qui ne contient QU'UN nombre, et rien d'autre."""
    return bool(re.fullmatch(r"\s*\d{1,4}\s*", ligne))


def _sans_numeros_de_page(texte: str) -> str:
    """Retire les lignes qui ne contiennent QU'UN nombre : les numéros de page que l'extraction
    du PDF colle au fil du texte (ex. « 34 » seul en fin d'unité). Un nombre porteur de sens dans
    un référentiel vit toujours DANS une phrase ou une liste — jamais seul sur sa ligne. Pur,
    déterministe, testable seul.

    HORS TABLEAU seulement : `extraire_texte` épargne les cellules, où un nombre seul est une
    donnée (voir sa docstring)."""
    return "\n".join(l for l in texte.split("\n") if not _est_un_numero_de_page(l))


# Ce qui fait un bandeau, et non une phrase qui se répète.
#
# Mesuré sur les référentiels en service (11/08/2026) : les vrais en-têtes et pieds se tiennent
# à 4,4 % / 5,5 % / 5,7 % du haut, ou à 94,5 % / 95,6 % / 97,8 % — toujours la MÊME valeur d'une
# page à l'autre. Juste en dessous commence le contenu : un titre de section répété (un pôle de
# compétences, sur un référentiel professionnel) vit à 7,9 %, et il porte le
# rattachement des unités qui le suivent — le perdre coûterait plus cher que garder un bandeau.
_MARGE_HAUTE = 6.0      # % de la hauteur de page
_MARGE_BASSE = 94.0
_PAGES_POUR_UN_BANDEAU = 3


def _bandeaux(lignes_par_page: list[list[dict]], hauteur: float) -> set[tuple]:
    """Les (position, texte) qui reviennent à l'identique dans les marges → ce sont des bandeaux.

    La répétition SEULE ne suffit pas : « Ce que fait le professionnel : » ouvre chaque fiche
    d'un référentiel crèche, et une même phrase de cadrage revient sur douze pages d'un autre
    document — mais à chaque fois à une hauteur différente, parce que c'est du
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


# Ce qui fait une barre de suppression, et non un soulignement ni une bordure de tableau.
#
# Mesuré sur le programme du cycle 4 (version comparative de 2020, 1 071 caractères supprimés) :
# la barre est un rectangle plein de 0,6 point de haut, posé à 0,6 point du centre de lettres qui
# en font 11 — autant dire dessus. Le soulignement vert qui marque les AJOUTS du même document
# passe, lui, à 4,8 points sous ce centre, et les bordures de tableau tombent entre deux lignes :
# c'est la hauteur, et elle seule, qui sépare le texte mort du texte vivant. La couleur ne le
# ferait pas — le rouge est la convention de CE document, le trait est celle de tous.
_EPAISSEUR_TRAIT_MAX = 2.5      # points ; au-delà c'est un aplat de couleur, plus un trait
_ECART_MILIEU_MAX = 0.25        # part de la hauteur du caractère
_COUVERTURE_MIN = 0.5           # part du caractère que le trait doit recouvrir
_CARACTERES_POUR_UNE_BARRE = 2  # en dessous, le trait n'est pas une barre : c'est un glyphe


def _cles_texte_barre(chars: list[dict], traits: list[dict]) -> set[tuple]:
    """Repère les caractères BARRÉS d'une page : ceux qu'un trait fin traverse en son milieu.

    Renvoie les clés (x0, top, texte) des caractères à écarter — même forme que les lettres
    verticales, pour le même filtre. Pur, déterministe, testable seul."""
    barres = [t for t in traits
              if 0 < (t["bottom"] - t["top"]) <= _EPAISSEUR_TRAIT_MAX and (t["x1"] - t["x0"]) > 1]
    if not barres or not chars:
        return set()

    # Index par hauteur du MILIEU du caractère : un trait ne peut barrer que ce qu'il croise à sa
    # propre hauteur. Sans cet index, chaque bordure de tableau ferait un tour complet de la page.
    par_milieu: dict[int, list[dict]] = defaultdict(list)
    for c in chars:
        par_milieu[round((c["top"] + c["bottom"]) / 2)].append(c)
    # La fenêtre de recherche suit la plus grande lettre de la page : un titre barré en corps 40
    # a son centre bien plus loin du trait qu'une lettre de texte courant.
    fenetre = max(1, int(_ECART_MILIEU_MAX * max(c["bottom"] - c["top"] for c in chars)) + 1)

    debris: set[tuple] = set()
    for t in barres:
        milieu = (t["top"] + t["bottom"]) / 2
        recouverts: list[tuple] = []
        for k in range(round(milieu) - fenetre, round(milieu) + fenetre + 1):
            for c in par_milieu.get(k, ()):
                hauteur = c["bottom"] - c["top"]
                largeur = c["x1"] - c["x0"]
                if hauteur <= 0 or largeur <= 0:
                    continue
                if abs(milieu - (c["top"] + c["bottom"]) / 2) > _ECART_MILIEU_MAX * hauteur:
                    continue
                couvert = min(c["x1"], t["x1"]) - max(c["x0"], t["x0"])
                if couvert >= _COUVERTURE_MIN * largeur:
                    recouverts.append((c["x0"], c["top"], c["text"]))
        # Une barre de suppression barre des MOTS. Un trait qui ne couvre qu'un caractère unique
        # EST ce caractère : Word trace certaines puces de liste deux fois, le glyphe « - » et un
        # rectangle exactement dessus — trois tirets de puce partaient ainsi avec le texte mort.
        if len(recouverts) >= _CARACTERES_POUR_UNE_BARRE:
            debris.update(recouverts)
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
            lignes_par_page.append(_lignes_de_la_page(page))
    return {texte for _position, texte in _bandeaux(lignes_par_page, float(hauteur or 0))}


def est_une_ligne_de_bandeau(ligne: str, bandeaux: set[str]) -> bool:
    """La ligne, comparée aux bandeaux du document — nombres neutralisés des deux côtés."""
    return re.sub(r"\d+", "#", ligne.strip()) in bandeaux


_ECART_LIGNES_MAX = 2.5   # en hauteurs de ligne ; au-delà, deux blocs distincts


def _est_en_gras(ligne: dict) -> bool:
    """Vrai si TOUS les caractères de la ligne sont dans une graisse forte. Une ligne mixte
    (un mot en gras dans une phrase normale) n'est pas un titre."""
    chars = ligne.get("chars") or []
    if not chars:
        return False
    return all("bold" in (c.get("fontname") or "").lower() for c in chars)


def _recoller_les_titres(lignes: list[dict]) -> list[dict]:
    """Dans une CELLULE de tableau, un titre trop long pour la largeur est coupé en plusieurs
    lignes. Mesuré le 14/08/2026 sur le programme du cycle 4, cellule (68,307)-(205,570) :

        'Thème 1' / 'Chrétientés et islam' / '(VIe-XIIIe siècles), des' / 'mondes en contact'

    quatre lignes en Helvetica-Bold, suivies du contenu en Helvetica. Le titre réel n'existe donc
    nulle part comme ligne — et la découpe ANCRE ses unités sur des lignes recopiées à l'identique.

    La graisse tranche sans ambiguïté : on fusionne les suites de lignes entièrement en gras, tant
    qu'elles se suivent verticalement. Le reste n'est jamais touché."""
    recollees: list[dict] = []
    for ligne in lignes:
        precedente = recollees[-1] if recollees else None
        if (precedente is not None and _est_en_gras(precedente) and _est_en_gras(ligne)
                and ligne["top"] - precedente["bottom"]
                    <= _ECART_LIGNES_MAX * (precedente["bottom"] - precedente["top"])):
            precedente["text"] = f"{precedente['text'].rstrip()} {ligne['text'].lstrip()}"
            precedente["chars"] = list(precedente["chars"]) + list(ligne["chars"])
            precedente["x1"] = max(precedente["x1"], ligne["x1"])
            precedente["bottom"] = ligne["bottom"]
            continue
        recollees.append(dict(ligne))
    return recollees


def _lignes_de_la_page(page) -> list[dict]:
    """Les lignes d'une page — les zones de TABLEAU lues cellule par cellule.

    POURQUOI. `extract_text_lines` groupe les caractères par bande horizontale. Sur une page mise
    en tableau à deux colonnes, il recolle donc le titre de la colonne de gauche et la phrase de
    la colonne de droite sur UNE MÊME LIGNE. Mesuré le 14/08/2026 sur le programme du cycle 4 :

        « Le vote, un droit fondamental en La conquête progressive du droit de vote. »

    Le titre réel — « Le vote, un droit fondamental en démocratie » — n'existe alors nulle part
    comme ligne. Or la découpe ANCRE ses unités sur des lignes de titre recopiées à l'identique :
    34 titres sur 216 étaient introuvables, soit 34 unités perdues, sur trois matières entières
    (Histoire-géographie, Enseignement moral et civique, Histoire des arts).

    COMMENT. `find_tables()` rend la bbox de chaque tableau et de chaque cellule. On lit alors la
    page par bandes horizontales, dans l'ordre : ce qui précède le premier tableau, puis chaque
    tableau cellule par cellule (gauche puis droite, ligne de tableau après ligne de tableau), puis
    ce qui suit. Une page sans tableau garde exactement le comportement d'avant.

    Chaque ligne conserve sa position (`top`, `x0`…) : `_bandeaux` en a besoin pour distinguer un
    en-tête répété d'une phrase qui se répète."""
    try:
        tables = page.find_tables()
    except Exception:      # pdfplumber peut buter sur une page tordue : on ne perd pas la page
        tables = []
    if not tables:
        return page.extract_text_lines() or []

    def _bande(haut: float, bas: float) -> list[dict]:
        """Les lignes d'une tranche horizontale de la page. Une tranche vide ne coûte rien."""
        if bas - haut < 1:
            return []
        try:
            return page.crop((0, max(0, haut), page.width, min(page.height, bas))
                             ).extract_text_lines() or []
        except Exception:
            return []

    lignes: list[dict] = []
    bas_precedent = 0.0
    for table in sorted(tables, key=lambda t: t.bbox[1]):
        _x0, haut, _x1, bas = table.bbox
        lignes += _bande(bas_precedent, haut)          # le texte courant qui précède le tableau
        for rang in table.rows:
            for cellule in rang.cells:
                if cellule is None:
                    continue
                try:
                    for ligne in _recoller_les_titres(
                            page.crop(cellule).extract_text_lines() or []):
                        lignes.append({**ligne, "en_cellule": True})
                except Exception:
                    continue
        bas_precedent = max(bas_precedent, bas)
    lignes += _bande(bas_precedent, page.height)       # la queue de page
    return lignes


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
            debris |= _cles_texte_barre(page.chars, page.rects + page.lines)
            if debris:
                page = page.filter(
                    lambda o, _d=debris: not (o.get("object_type") == "char"
                                              and (o.get("x0"), o.get("top"), o.get("text")) in _d))
            # Chaque ligne arrive avec sa position — sans elle, impossible de distinguer un
            # bandeau d'une phrase qui se répète. Et les tableaux se lisent cellule par cellule,
            # sinon deux colonnes se retrouvent recollées sur la même ligne (cf. la fonction).
            lignes_par_page.append(_lignes_de_la_page(page))
    hauteur = float(hauteur or 0)

    # UN SEUL passage : bandeaux et numéros de page se retirent ensemble, parce que le second
    # dépend de la PROVENANCE de la ligne — information que `_sans_bandeaux` a déjà perdue
    # lorsqu'il rend des chaînes. (Les deux fonctions restent utilisables seules : elles servent
    # ailleurs, et leurs tests les prennent une par une.)
    #
    # UN NOMBRE SEUL DANS UNE CELLULE EST UNE DONNÉE. Mesuré le 14/08/2026 sur le programme du
    # cycle 4, tableau « Compétences travaillées / Domaines du socle » du Français : la cellule
    # (391,284)-(527,368) porte « 1 » — le domaine du socle travaillé par le bloc « Écrire ».
    # Le filtre l'effaçait, et ce bloc était le seul des cinq à n'avoir aucun domaine. Un numéro
    # de page, lui, ne tombe jamais dans une cellule.
    a_retirer = _bandeaux(lignes_par_page, hauteur)
    pages: list[str] = []
    for lignes in lignes_par_page:
        gardees = [l["text"] for l in lignes
                   if not (_dans_la_marge(l, hauteur) and _repere(l, hauteur) in a_retirer)
                   and (l.get("en_cellule") or not _est_un_numero_de_page(l["text"]))]
        pages.append("\n".join(gardees))
    return "\n".join(pages).strip()
