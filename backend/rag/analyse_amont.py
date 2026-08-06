"""Analyse amont d'un référentiel — par l'IA.

RÈGLE : l'ambiguïté d'un référentiel se détecte par l'IA, jamais à la main, et sur un cas
flou on ne décide jamais seul en silence — on signale et on attend l'arbitrage de l'admin.
Concrètement : on donne à l'IA les unités DÉJÀ découpées d'un document ; elle en DÉDUIT la règle de
classement (l'axe qui structure le document) et, pour chaque unité, dit si le classement est
clair (dans quelle(s) classe(s)) ou s'il y a un VRAI doute. L'IA propose, l'admin valide
(cap « aSchool n'invente rien »).

GÉNÉRIQUE : aucun axe (âge, matière, compétence…) n'est fourni ni codé ici — l'IA le découvre
en lisant. C'est du SOCLE, pas une fiche : rien de propre à un document.

Porte IA unique : `generate()` (backend.llm.generator) ; provider / modèle / prompt résolus EN BASE,
comme les autres outils (cf. `backend/analyse/ambiguites.py`).

TEMPÉRATURE : lue par `get_temperature(db)`, comme les 17 autres outils du produit (05/08/2026).
Ce fichier écrivait `temperature=0` EN DUR — il était le seul du backend à le faire, et cela
court-circuitait la fiche du modèle. Claude Sonnet 5 REFUSE ce paramètre (400,
« `temperature` is deprecated for this model ») : la base le sait déjà
(`ai_modeles.supporte_temperature = false`) et `get_temperature` renvoie alors None, donc le
moteur n'envoie rien. Le 0 en dur produisait deux pannes opposées selon la voie prise :
  - appels COURTS (précisions d'un type) : 400 à chaque fois — et l'appelant absorbait l'erreur
    en warning, donc les précisions ne se généraient plus DU TOUT, en silence ;
  - appels LONGS (découpe, matières, méta-prompts) : pas de 400, mais pas de déterminisme non
    plus — la voie streaming Anthropic perdait la température en route (corrigé dans generator.py).
Conséquence à connaître : sous un modèle qui refuse la température, la découpe n'est pas
reproductible, et aucun réglage ne la rendra telle. Cela se joue dans le PROMPT, pas ici.

État : brique ISOLÉE et testable — PAS encore branchée sur le découpage / l'ingestion
(pas 1 du chantier TRACKER 67 ; le remplacement de `_age_est_flou` vient dans un pas suivant).
"""
import json
import logging
import re

from sqlalchemy.orm import Session

from backend.systeme.admin import (
    get_ai_model, get_ai_provider, get_cle_texte, get_contexte_max, get_max_tokens, get_prompt,
    get_settings_dict, get_temperature,
)
from backend.llm.generator import generate, generate_cached

logger = logging.getLogger(__name__)

_CLE_PROMPT = "analyse_amont"
_CLE_DECOUPE = "decoupe_amont"
# Clé EN BASE du méta-prompt (l'instruction générique qui demande à l'IA de GÉNÉRER le prompt de
# découpe d'un document). Aucun texte de prompt en dur : le code le LIT en base (Setting).
_CLE_META = "prompt_meta_decoupe"
# Clé EN BASE du méta-prompt de CRITIQUE : l'IA relit le prompt de découpe qu'elle vient de
# générer et le corrige s'il viole le contrat (titres verbatim, JSON exact, pas de contenu,
# exclusions) AVANT de l'afficher à l'admin. Aucun texte en dur : lu en base (Setting).
_CLE_VERIF = "prompt_verif_decoupe"
# Clé EN BASE du méta-prompt des MATIÈRES : même geste que `_CLE_META`, mais il fait rédiger le
# prompt qui LIT LES MATIÈRES. Le prompt rédigé est rangé sur le CYCLE (cycles.prompt_matieres).
_CLE_META_MATIERES = "prompt_meta_matieres"
# Clé EN BASE du méta-prompt des TYPES D'ACTIVITÉ (05/08/2026) — le troisième du même geste. Le
# prompt rédigé est rangé sur le CYCLE (cycles.prompt_types) : la DONNÉE (le type) appartient au
# référentiel qui la nomme, la RECETTE qui la lit appartient à la famille.
_CLE_META_TYPES = "prompt_meta_types"

# Schéma STRICT de la découpe (Structured Outputs) : le modèle ne renvoie QUE des titres.
# `additionalProperties: false` interdit tout champ en trop (ex. « contenu ») → la génération est
# contrainte token par token, la réponse reste petite : ni troncature, ni dépassement de délai. On
# ne lit de toute façon que le titre (`_trancher_par_titres` tranche le texte réel) : le contenu que
# le modèle produisait était du poids mort. GÉNÉRIQUE : aucun axe métier ici, juste la forme.
#
# `garder` et `option` (05/08/2026). Le tranchage va d'un titre au titre SUIVANT : une zone sans
# titre reconnu se colle à sa voisine, et tout ce qui suit le dernier titre part avec lui (mesuré
# sur le BTS CIEL : deux blocs de 15 800 et 21 600 caractères, gonflés du programme des
# enseignements généraux et de la queue du document). Le prompt émet donc AUSSI les en-têtes des
# sections qu'on écarte, `garder:false` : ce sont des BORNES, elles servent à couper puis sont
# jetées. `option` porte l'option à laquelle l'unité appartient ("A", "B", "commune", ou "" si le
# document n'en a pas) : c'est ce qui remplit `referentiel_chunks.option_ab` et permet de ne
# montrer à un prof que ce qui le concerne. GÉNÉRIQUE : aucun axe métier ici, juste la forme.
_SCHEMA_DECOUPE = {
    "type": "object",
    "properties": {
        "unites": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "titre": {"type": "string"},
                    "option": {"type": "string"},
                    "garder": {"type": "boolean"},
                },
                "required": ["titre", "option", "garder"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["unites"],
    "additionalProperties": False,
}


def formater_unites(unites: list[dict]) -> str:
    """Rend les unités en texte numéroté pour le prompt : `[i] titre` puis le texte de l'unité.
    Pur (aucune IA, aucune base) → testable seul. `titre` est optionnel."""
    blocs = []
    for i, u in enumerate(unites):
        titre = (u.get("titre") or "").strip()
        texte = (u.get("texte") or "").strip()
        entete = f"[{i}] {titre}" if titre else f"[{i}]"
        blocs.append(f"{entete}\n{texte}".strip())
    return "\n\n".join(blocs)


def parser_reponse(raw: str) -> dict:
    """Extrait le JSON de la réponse du modèle : direct, dans un bloc ```json … ```, ou 1er objet
    `{...}` trouvé. Lève `ValueError` si rien d'exploitable. Même tolérance que les autres outils."""
    for candidat in _candidats_json(raw):
        try:
            data = json.loads(candidat)
        except Exception:
            continue
        if isinstance(data, dict):
            return data
    raise ValueError(f"Réponse non parseable en JSON (longueur : {len(raw)}).")


def _candidats_json(raw: str):
    yield raw
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if m:
        yield m.group(1)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        yield m.group(0)


def analyser_unites(unites: list[dict], *, db: Session) -> dict:
    """Analyse amont d'un document via l'IA. `unites` = `[{"titre","texte"}]` déjà découpées.

    Retour : `{"regle": str, "unites": [{"index", "classe": [...], "doute": bool, "raison"}]}`
    — la règle de classement que l'IA a déduite + son verdict par unité (clair vs vrai doute).

    Lève `ValueError` si l'IA ne rend pas un JSON exploitable. Laisse remonter
    `LLMRateLimitError` (surcharge transitoire) et `RuntimeError` (panne fournisseur) — l'appelant
    les traduit. Prompt / provider / modèle / température lus EN BASE."""
    prompt = get_prompt(db, _CLE_PROMPT).format(unites=formater_unites(unites))
    raw = generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, _CLE_PROMPT),
        temperature=get_temperature(db),
        json_mode=True,
        outil=_CLE_PROMPT,
    )
    return parser_reponse(raw)


# L'épuration vit à UNE seule place : backend/rag/extraction.py (porte d'extraction unique).
# Ré-exposée ici car le tranchage la ré-applique (défensif : idempotent sur un texte déjà propre).
from backend.rag.extraction import _sans_numeros_de_page


# Les caractères qui ont PLUSIEURS FORMES pour UN SEUL SENS. Un PDF officiel est composé en
# typographie soignée : apostrophe courbe, tiret cadratin, guillemets anglais. Un modèle qui
# recopie tape le clavier : apostrophe droite, trait d'union. Le sens est le même, la chaîne
# non — et le titre devient introuvable.
#
# MESURÉ le 06/08/2026 sur le BTS CIEL : sur 137 titres rendus, 16 étaient donnés pour
# « introuvables ». LES SEIZE ne différaient que par l'apostrophe (« d’équipe » contre
# « d'équipe »). Seize sur seize — dont l'activité R4, D1 et D3, perdues pour un caractère.
#
# Pourquoi cette normalisation-là est SÛRE, alors que celle des minuscules et des accents ne
# l'est pas : personne ne distingue deux sections d'un référentiel par la forme de son
# apostrophe ou de son tiret. Le sens ne vit pas là. Alors que « Unité U4 » et « UNITÉ U4 »
# peuvent, eux, désigner deux choses. On ne rend donc PAS la comparaison floue : on retire
# seulement une différence qui n'en est pas une.
_FORMES_EQUIVALENTES = str.maketrans({
    "\u2019": "'", "\u2018": "'", "\u201b": "'", "\u02bc": "'", "\u00b4": "'",  # apostrophes
    "\u2013": "-", "\u2014": "-", "\u2012": "-", "\u2011": "-", "\u2212": "-",  # tirets
    "\u201c": '"', "\u201d": '"', "\u201e": '"',                               # guillemets
})


def _replier_blancs(s: str) -> str:
    """Replie les blancs en un espace simple, et ramène les variantes typographiques à une forme.

    Deux normalisations, pas une de plus. Les blancs, parce que l'IA recopie un titre en les
    normalisant alors que le document peut porter deux espaces ou une coupure de ligne. Et les
    formes équivalentes de l'apostrophe, du tiret et des guillemets (cf. `_FORMES_EQUIVALENTES`),
    parce qu'une différence de FORME n'est pas une différence de titre.

    On ne va pas plus loin — ni minuscules, ni accents retirés, ni ponctuation ignorée : un titre
    court comme « C08 CODER » s'accrocherait alors n'importe où, et « Unité U4 » se confondrait
    avec « UNITÉ U4 », qui peuvent désigner deux choses dans un référentiel. Une normalisation
    trop large fabrique des frontières fausses, ce qui est pire que d'en manquer une.

    Ne sert QU'À COMPARER : le titre rendu à l'appelant est toujours découpé dans le texte réel,
    avec la typographie du document. Rien de ce qui s'affiche ne passe par ici.
    """
    return " ".join(s.translate(_FORMES_EQUIVALENTES).split())


def _occurrences_du_titre(lignes_repliees: list[str], titre: str) -> list[tuple[int, int]]:
    """Toutes les places où `titre` commence, en `(première ligne, ligne suivant le titre)`.

    Deux façons de reconnaître un titre, dans cet ordre :
      1. il tient dans UNE ligne (comportement d'origine, conservé tel quel) ;
      2. il est à CHEVAL sur plusieurs lignes — on recolle les lignes suivantes jusqu'à couvrir
         sa longueur, et on regarde si le tout commence par lui.

    Le second cas manquait, et il n'était pas rare : sur le BTS CIEL, 10 des 54 titres rendus
    par l'IA tenaient sur deux ou trois lignes (les six épreuves, les deux épreuves
    facultatives, une activité) parce que c'est ainsi qu'ils sont écrits dans le document. Ils
    étaient perdus à tous les coups. Cette fonction rend donc un SUR-ENSEMBLE de ce que
    l'ancienne comparaison trouvait : elle ne peut rien faire perdre.
    """
    t = _replier_blancs(titre)
    if not t:
        return []
    trouvees: list[tuple[int, int]] = []
    for i, ligne in enumerate(lignes_repliees):
        if not ligne:
            continue
        if t in ligne:                       # 1. le titre tient dans la ligne
            trouvees.append((i, i + 1))
            continue
        accumule, j = ligne, i + 1           # 2. le titre déborde sur les suivantes
        while len(accumule) < len(t) and j < len(lignes_repliees):
            if lignes_repliees[j]:
                accumule += " " + lignes_repliees[j]
            j += 1
        if accumule.startswith(t):
            trouvees.append((i, j))
    return trouvees


def _trancher_par_titres(texte: str, titres: list) -> list[dict]:
    """Tranche le TEXTE RÉEL aux lignes de titre rendues par l'IA — jamais réécrit par l'IA
    (cap « aSchool n'invente rien »). Pur, sans IA, sans base : testable seul.
    Chaque unité = du titre retenu jusqu'au titre suivant, dans l'ordre du document. Un titre
    introuvable est ignoré (on ne fabrique pas de frontière). Les numéros de page
    (lignes-nombres) sont écartés avant tranchage. Renvoie `[{"titre","texte","option"}]` dans l'ordre.

    ENTRÉES ACCEPTÉES : une chaîne (le titre seul, tout est gardé) ou un dict
    `{"titre", "option", "garder"}`. Les entrées `garder:false` sont des BORNES : elles servent à
    couper — c'est tout leur rôle — puis elles sont retirées du résultat. Sans elles, une section
    sans titre reconnu se colle à sa voisine et la queue du document part avec la dernière unité.

    LE CHOIX ENTRE PLUSIEURS OCCURRENCES. Un même intitulé figure souvent DEUX fois : une
    première dans un sommaire ou un récapitulatif, une seconde en tête de la vraie section.
    L'ancienne version retenait toujours la première : le récapitulatif raflait les titres, et
    les vraies sections, privées de frontière, se retrouvaient avalées par leur voisine. Mesuré
    le 02/08/2026 sur le BTS CIEL : 19 unités réduites à leur seule ligne de titre (la plus
    courte, 9 caractères) et 3 unités géantes emportant 75 % du document.

    LA RÈGLE : **un intitulé immédiatement suivi d'un autre intitulé de la liste ne porte aucun
    contenu — c'est une entrée de sommaire, pas une unité.** Elle ne nomme aucune section, aucun
    document, aucun métier : elle ne parle que de la forme, comme le reste du socle.

    ET SURTOUT, LE CHOIX EST GLOBAL — pas titre par titre (06/08/2026). Un curseur qui avançait
    en choisissant chaque titre pour lui seul ignorait ce que ce choix coûtait aux suivants.
    MESURÉ sur le BTS CIEL, sur les 137 titres rendus par le modèle : « Activité R3 » a cinq
    occurrences, le curseur prenait la dernière (ligne 819), et les VINGT titres qui vivent entre
    la ligne 378 et la ligne 819 devenaient « hors ordre » d'un coup — puis l'effet se propageait
    jusqu'à la fin. Bilan : 47 titres placés, 90 perdus, 23 unités là où le document en contient
    une cinquantaine ; les annexes IV et V (unités U1-U6, épreuves E1-E6, EF1, EF2) disparaissaient
    entières.

    On cherche donc l'affectation de positions, croissante en rang ET en ligne, qui place le PLUS
    de titres — un titre ne peut plus en sacrifier vingt. Même réponse du modèle, même document :
    **120 titres placés, 49 unités.** La préférence « pas le sommaire » devient une prime de
    départage (0.01 par titre) : elle tranche entre deux solutions de même taille, elle ne peut
    jamais faire perdre un titre.

    CE QUE ÇA NE RÉPARE PAS : un titre que le modèle a mal recopié n'est nulle part dans le
    document, donc il n'a aucune place à occuper. Sur les 17 titres encore perdus, 16 sont de
    ceux-là — cela se corrige dans le PROMPT, jamais ici.
    """
    # Une entrée = un titre + ce qu'on en fait. Une simple chaîne vaut « unité à garder, sans
    # option » : les appels d'avant les bornes continuent de marcher tels quels.
    entrees = [{"titre": t, "option": "", "garder": True} if isinstance(t, str)
               else {"titre": (t.get("titre") or "").strip(),
                     "option": (t.get("option") or "").strip(),
                     "garder": t.get("garder", True) is not False}
               for t in titres]

    lignes = _sans_numeros_de_page(texte).split("\n")
    lignes_repliees = [_replier_blancs(l) for l in lignes]

    occurrences = [_occurrences_du_titre(lignes_repliees, e["titre"]) for e in entrees]
    # Les lignes qui PORTENT le début d'un titre — de n'importe lequel. C'est le seul signal
    # dont la règle a besoin, et il se calcule une fois.
    portent_un_titre = {debut for liste in occurrences for debut, _ in liste}

    def _suivante_non_vide(depuis: int) -> int | None:
        for j in range(depuis, len(lignes_repliees)):
            if lignes_repliees[j]:
                return j
        return None

    # `debuts` garde le rang de l'entrée qui l'a produit : une borne coupe comme les autres, elle
    # est seulement retirée à la fin.
    # ALIGNEMENT GLOBAL — un NŒUD par occurrence possible, et on retient la suite de nœuds de
    # score maximal à rangs ET positions strictement croissants. Le gain de base est 1 par titre
    # placé ; la prime de 0.01 va à l'occurrence qui porte du contenu (celle qui n'est pas
    # immédiatement suivie d'un autre titre), ce qui départage à nombre de titres égal sans
    # jamais primer sur lui. Coût : O(nœuds²) — 137 titres du BTS CIEL font ~700 nœuds, instantané.
    # Le nœud transporte AUSSI `fin` — la ligne qui suit le titre. Un titre écrit sur DEUX lignes
    # dans le document (« C01 » puis « COMMUNIQUER EN SITUATION PROFESSIONNELLE ») serait sinon
    # étiqueté « C01 » : on garderait la première ligne pour nom d'unité, et l'admin comme le prof
    # liraient un code sans intitulé.
    noeuds: list[tuple[int, int, int, float]] = []
    for rang, places in enumerate(occurrences):
        for debut, fin in places:
            j = _suivante_non_vide(fin)
            porte_du_contenu = (j is None or j not in portent_un_titre)
            noeuds.append((rang, debut, fin, 1.0 + (0.01 if porte_du_contenu else 0.0)))

    score = [0.0] * len(noeuds)
    venant_de = [-1] * len(noeuds)
    for k, (rang_k, pos_k, _fin_k, gain_k) in enumerate(noeuds):
        score[k], venant_de[k] = gain_k, -1
        for j in range(k):
            rang_j, pos_j, _fin_j, _ = noeuds[j]
            if rang_j < rang_k and pos_j < pos_k and score[j] + gain_k > score[k]:
                score[k], venant_de[k] = score[j] + gain_k, j

    chaine: list[int] = []
    k = max(range(len(noeuds)), key=lambda i: score[i]) if noeuds else -1
    while k >= 0:
        chaine.append(k)
        k = venant_de[k]
    # (ligne de début, rang de l'entrée, ligne qui suit le titre)
    debuts = sorted((noeuds[k][1], noeuds[k][0], noeuds[k][2]) for k in chaine)

    # JOURNAL des titres PERDUS. Un titre qui ne produit aucune frontière disparaît du résultat
    # sans laisser de trace : le compte final n'est donc pas « ce que l'IA a vu » mais « ce qui a
    # survécu au tranchage ». Sans ce relevé, un essai qui rend 29 unités ne dit pas si le modèle
    # en a lu 29 ou 60 — et on règle le prompt à l'aveugle. Les deux motifs appellent deux
    # corrections OPPOSÉES, d'où la distinction :
    #   « introuvable » — le titre n'est nulle part dans le document : l'IA l'a reformulé,
    #                     abrégé ou recomposé (faute de RECOPIE) ; le tranchage n'y peut rien ;
    #   « hors ordre »  — le titre EST dans le document, mais aucune de ses places ne s'insère
    #                     dans une suite croissante : l'IA l'a émis à contre-courant de l'ordre.
    places_retenues = {rang for _, rang, _f in debuts}
    perdus = [(entrees[rang]["titre"], "introuvable" if not occurrences[rang] else "hors ordre")
              for rang in range(len(entrees)) if rang not in places_retenues]

    # UNE TRANCHE QUI NE CONTIENT QUE SON PROPRE TITRE N'EST PAS UNE UNITÉ (06/08/2026).
    #
    # Un référentiel énumère ses sections avant de les décrire : tableau de synthèse, liste des
    # blocs de compétences, renvois d'une option à l'autre. Ces lignes portent le MÊME repère que
    # les vraies sections — « C08 CODER », « C07 (uniquement pour l'option B) » — donc un prompt
    # qui reconnaît les titres par leur forme les rend comme des unités, et il a raison de le
    # faire : rien, dans la ligne elle-même, ne dit qu'elle est un renvoi.
    #
    # Ce qui le dit, c'est ce qu'il y a DERRIÈRE : rien. Deux titres consécutifs se ferment l'un
    # l'autre, et la tranche se réduit à sa ligne de titre. MESURÉ sur le BTS CIEL : 22 tranches
    # sur 76 étaient dans ce cas, de 9 à 63 caractères — dont « C08 CODER », qui fait exactement
    # ses 9 caractères de titre. Les vraies compétences, elles, en portent 1 240 à 2 471.
    #
    # Le critère est une ÉGALITÉ, pas un seuil : aucun nombre en dur, donc rien à régler quand le
    # document change. Et il ne peut pas manger une vraie petite unité — « Unité facultative UF2 »
    # ne fait que 124 caractères, mais elle en a plus que son titre, donc elle reste.
    unites: list[dict] = []
    nues: list[dict] = []
    for k, (i, rang, fin_titre) in enumerate(debuts):
        if not entrees[rang]["garder"]:
            continue          # BORNE : elle a fait son travail en fermant l'unité d'avant
        fin = debuts[k + 1][0] if k + 1 < len(debuts) else len(lignes)
        bloc = "\n".join(lignes[i:fin]).strip()
        # L'étiquette = TOUTES les lignes du titre, telles qu'écrites dans le document (jamais
        # `lignes_repliees`, qui a normalisé les apostrophes pour comparer : ce qui s'affiche garde
        # la typographie d'origine).
        titre_reel = " ".join(l.strip() for l in lignes[i:max(fin_titre, i + 1)] if l.strip())
        tranche = {"titre": titre_reel, "texte": bloc, "option": entrees[rang]["option"]}
        # « rien derrière le titre » se juge sur les blancs repliés : un titre à cheval sur deux
        # lignes porte un « \n » que son bloc porte aussi, et l'égalité brute le raterait.
        nue = _replier_blancs(bloc) == _replier_blancs(titre_reel)
        (nues if nue else unites).append(tranche)

    # LE GARDE-FOU, et il compte autant que le filtre : si écarter les tranches nues ne laissait
    # RIEN, c'est que le document n'énumère pas ses sections — il EST une liste. Un référentiel de
    # crèche peut n'être qu'une suite d'intitulés d'activités, sans description : là, les titres
    # nus SONT le contenu, et les jeter reviendrait à rendre une découpe vide.
    # La règle du projet tranche : un défaut connu vaut mieux qu'une disparition
    # (`tests/test_trancher_par_titres.py::test_un_document_entierement_en_liste_garde_ses_titres`,
    # qui est tombé quand le filtre a été posé sans ce garde-fou).
    if not unites:
        unites, nues = nues, []
    sans_contenu = [u["titre"] for u in nues]

    for titre, motif in perdus:
        logger.warning("découpe : titre %s, PERDU — « %s »", motif, titre[:150])
    for titre in sans_contenu:
        logger.info("découpe : titre SANS CONTENU, écarté (énumération) — « %s »", titre[:150])
    logger.info(
        "découpe : %d titres rendus, %d retrouvés, %d perdus (%d introuvables, %d hors ordre) "
        "→ %d unités gardées, %d bornes",
        len(entrees), len(debuts), len(perdus),
        sum(1 for _, m in perdus if m == "introuvable"),
        sum(1 for _, m in perdus if m == "hors ordre"),
        len(unites), len(debuts) - len(unites),
    )
    return unites


def generer_prompt_decoupe(texte: str, *, db: Session) -> str:
    """L'IA GÉNÈRE le prompt de découpe adapté à CE document. On lui donne le méta-prompt (lu EN
    BASE, `Setting[prompt_meta_decoupe]`) + le texte brut du PDF ; elle rend un prompt de découpe
    sur mesure (texte libre). SOCLE, générique : aucun prompt écrit en dur, aucun axe métier codé.
    Le résultat sera stocké en base par couple et validé par l'admin avant usage. Lève si le
    méta-prompt n'est pas en base (jamais de découpe silencieuse sans amorce). Laisse remonter les
    pannes IA."""
    meta = (get_settings_dict(db).get(_CLE_META) or "").strip()
    if not meta:
        raise RuntimeError(
            f"Méta-prompt absent en base (Setting '{_CLE_META}'). L'admin doit le renseigner "
            f"avant de générer un prompt de découpe (cap « tout en base »)."
        )
    # Le document s'injecte au marqueur {document} du méta-prompt (distinct de {texte}, que le
    # méta-prompt demande au prompt GÉNÉRÉ de contenir). Ajouté en fin si le marqueur est absent.
    prompt = meta.replace("{document}", texte) if "{document}" in meta else f"{meta}\n\n{texte}"
    prompt_genere = generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, "meta_decoupe"),
        temperature=get_temperature(db),
        appel_long=True,  # le méta-prompt embarque le référentiel complet
        contexte_max=get_contexte_max(db),
        outil="meta_decoupe",
    ).strip()
    # Passe d'auto-critique AVANT de renvoyer : l'IA relit son propre prompt et corrige les défauts
    # grossiers (titre paraphrasé, contenu demandé, JSON non conforme, exclusion oubliée).
    return verifier_prompt_decoupe(prompt_genere, db=db)


def generer_prompt_matieres(texte: str, *, db: Session) -> str:
    """L'IA GÉNÈRE le prompt qui lira les MATIÈRES des référentiels de ce cycle. Même geste que
    `generer_prompt_decoupe` : méta-prompt lu EN BASE (`Setting[prompt_meta_matieres]`) + le texte
    d'un référentiel du cycle, pris comme exemple de sa famille ; elle rend un prompt sur mesure
    (texte libre). SOCLE, générique : aucun prompt en dur, aucune famille de diplôme codée ici —
    c'est le document qui dicte. Le résultat est stocké sur le CYCLE et validé par l'admin avant
    usage. Lève si le méta-prompt n'est pas en base. Laisse remonter les pannes IA."""
    meta = (get_settings_dict(db).get(_CLE_META_MATIERES) or "").strip()
    if not meta:
        raise RuntimeError(
            f"Méta-prompt absent en base (Setting '{_CLE_META_MATIERES}'). L'admin doit le "
            f"renseigner avant de générer un prompt de matières (cap « tout en base »)."
        )
    # {document} = le référentiel exemple ; {texte} doit rester INTACT (le prompt généré le porte).
    prompt = meta.replace("{document}", texte) if "{document}" in meta else f"{meta}\n\n{texte}"
    return generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, "meta_matieres"),
        temperature=get_temperature(db),
        appel_long=True,  # le méta-prompt embarque le référentiel complet
        contexte_max=get_contexte_max(db),
        outil="meta_matieres",
    ).strip()


def generer_prompt_types(texte: str, *, db: Session) -> str:
    """L'IA GÉNÈRE le prompt qui lira les TYPES D'ACTIVITÉ des référentiels de ce cycle. Troisième
    exemplaire du même geste que `generer_prompt_decoupe` et `generer_prompt_matieres` :
    méta-prompt lu EN BASE (`Setting[prompt_meta_types]`) + le texte d'un référentiel du cycle,
    pris comme exemple de sa famille ; elle rend un prompt sur mesure (texte libre).

    LA RÈGLE DES DEUX ÉTAGES (05/08/2026) : la DONNÉE appartient au référentiel qui la nomme (un
    type d'activité est lu dans le document, comme une matière), la RECETTE qui la lit appartient
    au CYCLE — une famille de documents bâtis pareil se lit avec la même recette. Le résultat est
    stocké sur le cycle. Lève si le méta-prompt n'est pas en base. Laisse remonter les pannes IA."""
    meta = (get_settings_dict(db).get(_CLE_META_TYPES) or "").strip()
    if not meta:
        raise RuntimeError(
            f"Méta-prompt absent en base (Setting '{_CLE_META_TYPES}'). L'admin doit le "
            f"renseigner avant de générer un prompt de types (cap « tout en base »)."
        )
    # {document} = le référentiel exemple ; {texte} doit rester INTACT (le prompt généré le porte).
    prompt = meta.replace("{document}", texte) if "{document}" in meta else f"{meta}\n\n{texte}"
    return generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, "meta_types"),
        temperature=get_temperature(db),
        appel_long=True,  # le méta-prompt embarque le référentiel complet
        contexte_max=get_contexte_max(db),
        outil="meta_types",
    ).strip()


def verifier_prompt_decoupe(prompt_genere: str, *, db: Session) -> str:
    """L'IA RELIT le prompt de découpe qu'elle vient de générer et le CORRIGE s'il viole le contrat,
    AVANT affichage à l'admin (lui épargne un aller-retour sur les défauts grossiers). Méta-prompt de
    critique lu EN BASE (`Setting[prompt_verif_decoupe]`), jamais en dur ; on n'injecte QUE le prompt
    (`{prompt}`) — pas le document : on juge la FORMULATION du prompt, pas sa sortie. Renvoie le
    prompt corrigé (ou inchangé si rien à redire). Lève si le méta-prompt de critique est absent.
    N'est PAS appelée par `regenerer_prompt_decoupe` : après une remarque admin, la remarque fait foi."""
    meta = (get_settings_dict(db).get(_CLE_VERIF) or "").strip()
    if not meta:
        raise RuntimeError(
            f"Méta-prompt de critique absent en base (Setting '{_CLE_VERIF}'). L'admin doit le "
            f"renseigner avant la génération d'un prompt de découpe (cap « tout en base »)."
        )
    p = meta.replace("{prompt}", prompt_genere) if "{prompt}" in meta else f"{meta}\n\nPROMPT À VÉRIFIER :\n{prompt_genere}"
    return generate(
        p,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, "meta_decoupe"),
        temperature=get_temperature(db),
        outil="meta_decoupe",
    ).strip()


def regenerer_prompt_decoupe(texte: str, *, prompt_actuel: str, remarques: str, db: Session) -> str:
    """L'IA CORRIGE le prompt de découpe à partir des REMARQUES de l'admin (français clair). Même
    méta-prompt lu EN BASE (`Setting[prompt_meta_decoupe]`) + texte du PDF, auxquels on joint le
    prompt actuel et les remarques ; l'IA rend un prompt de découpe RÉVISÉ (texte libre). SOCLE,
    générique : aucun prompt écrit en dur, aucun axe métier codé. Répétable à volonté (l'admin relit,
    remet une remarque, régénère). Lève si le méta-prompt n'est pas en base. Laisse remonter les
    pannes IA."""
    meta = (get_settings_dict(db).get(_CLE_META) or "").strip()
    if not meta:
        raise RuntimeError(
            f"Méta-prompt absent en base (Setting '{_CLE_META}'). L'admin doit le renseigner "
            f"avant de régénérer un prompt de découpe (cap « tout en base »)."
        )
    base = meta.replace("{document}", texte) if "{document}" in meta else f"{meta}\n\n{texte}"
    prompt = (
        f"{base}\n\n"
        f"PROMPT DE DÉCOUPE ACTUEL (à corriger) :\n{prompt_actuel}\n\n"
        f"REMARQUES DE L'ADMIN (à prendre en compte pour produire un NOUVEAU prompt) :\n{remarques}\n\n"
        f"Produis le PROMPT DE DÉCOUPE RÉVISÉ, et RIEN d'autre."
    )
    return generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, "meta_decoupe"),
        temperature=get_temperature(db),
        appel_long=True,  # le méta-prompt embarque le référentiel complet
        contexte_max=get_contexte_max(db),
        outil="meta_decoupe",
    ).strip()


def decouper_texte(texte: str, *, db: Session, prompt: str) -> list[dict]:
    """Découpe GÉNÉRIQUE d'un référentiel PAR L'IA, pilotée par le PROMPT VALIDÉ DU COUPLE (`prompt`,
    lu en base par l'appelant — jamais écrit en dur). On injecte le texte brut à la place du marqueur
    `{texte}` (ajouté en fin si absent), l'IA rend la liste ordonnée des lignes de titre ; le texte de
    chaque unité est ensuite TRANCHÉ dans le texte réel (`_trancher_par_titres`), jamais réécrit par
    l'IA. SOCLE : aucun axe (âge, matière…) codé. Laisse remonter les pannes IA. Renvoie
    `[{"titre","texte"}]`."""
    p = prompt.replace("{texte}", texte) if "{texte}" in prompt else f"{prompt}\n\nTEXTE BRUT :\n{texte}"
    # `generate_cached` et non `generate` : c'est L'APPEL LE PLUS CHER du logiciel (~210 000 tokens
    # d'entrée — le référentiel entier), et celui qu'on relance le plus souvent en développement,
    # où seul l'affichage du résultat change. Une même découpe rejouée est alors relue sur disque :
    # zéro appel, zéro token, zéro dollar. En production, `LLM_CACHE` n'existe pas et cette ligne se
    # comporte exactement comme `generate` — un cache de développement ne sert jamais un prof.
    raw = generate_cached(
        p,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, _CLE_DECOUPE),
        temperature=get_temperature(db),
        json_mode=True,
        schema=_SCHEMA_DECOUPE,
        # Le modèle lit ici un référentiel ENTIER : plusieurs minutes de génération. Sans le mode
        # long, la requête est bornée par un délai total et se fait couper avant la fin.
        appel_long=True,
        contexte_max=get_contexte_max(db),
        outil=_CLE_DECOUPE,
        # Le référentiel est en TÊTE du prompt (le prompt en base commence par {texte}) : on le
        # désigne au fournisseur, qui le gardera pour les cinq autres outils qui liront le même
        # document — eux ne le paieront qu'à 10 %. Sans effet sur la réponse.
        prefixe_cache=texte,
    )
    data = parser_reponse(raw)
    # Les entrées arrivent DANS L'ORDRE du document, unités et bornes entremêlées : c'est cet ordre
    # qui fait les frontières. On ne trie rien, on ne filtre que les titres vides.
    entrees: list[dict] = []
    for u in data.get("unites", []):
        if isinstance(u, dict):
            t = (u.get("titre") or "").strip()
            if t:
                entrees.append({"titre": t, "option": (u.get("option") or "").strip(),
                                "garder": u.get("garder", True) is not False})
        else:
            t = str(u).strip()
            if t:
                entrees.append({"titre": t, "option": "", "garder": True})
    return _trancher_par_titres(texte, entrees)


# Clé EN BASE du prompt de vérification du couple (cycle + niveau) — vérif n°1 au dépôt.
_CLE_COUPLE = "verifier_couple"


def _schema_couple() -> dict:
    """Sortie structurée de la vérif n°1. `correspond` = le document vise-t-il bien le couple
    déclaré ; `niveau_lu` = ce que l'IA lit dans le document ; `raison` = une phrase."""
    return {
        "type": "object",
        "properties": {
            "correspond": {"type": "boolean"},
            "niveau_lu": {"type": "string"},
            "raison": {"type": "string"},
        },
        "required": ["correspond", "niveau_lu", "raison"],
        "additionalProperties": False,
    }


def verifier_couple(texte: str, cycle: str, niveau: str, *, db: Session) -> dict:
    """Vérif n°1 au dépôt : l'IA lit le couple (cycle + niveau) visé par le DOCUMENT et le compare
    au couple DÉCLARÉ par l'admin. L'IA fait la comparaison sémantique (pas de string-matching) —
    on lui donne le couple déclaré + le texte, elle renvoie son verdict.

    Retour : `{"correspond": bool, "niveau_lu": str, "raison": str}`.
    Prompt / provider / modèle / température lus EN BASE. Laisse remonter les pannes IA
    (l'appelant traduit). Lève `ValueError` si l'IA ne rend pas un JSON exploitable."""
    prompt = (get_prompt(db, _CLE_COUPLE)
              .replace("{cycle}", cycle)
              .replace("{niveau}", niveau)
              .replace("{texte}", texte))
    raw = generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, _CLE_COUPLE),
        temperature=get_temperature(db),
        json_mode=True,
        schema=_schema_couple(),
        appel_long=True,  # entrée = le référentiel entier (la sortie, elle, est courte)
        contexte_max=get_contexte_max(db),
        outil=_CLE_COUPLE,
        prefixe_cache=texte,   # le document est en tête du prompt : le fournisseur le garde
    )
    data = parser_reponse(raw)
    return {
        "correspond": bool(data.get("correspond")),
        "niveau_lu": (data.get("niveau_lu") or "").strip(),
        "raison": (data.get("raison") or "").strip(),
    }


# Clé EN BASE du prompt de détection des matières — proposées au dépôt du PDF (proposition, pas
# une matière validée : l'admin coche ce qu'il garde).
_CLE_MATIERES = "detecter_matieres"


def _schema_matieres() -> dict:
    """Sortie structurée de la détection : `matieres` = tableau de noms. `additionalProperties:
    false` interdit tout champ en trop (réponse contrainte, petite, ni troncature ni dépassement)."""
    return {
        "type": "object",
        "properties": {
            "matieres": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["matieres"],
        "additionalProperties": False,
    }


def detecter_matieres(texte: str, *, db: Session, prompt_cycle: str | None = None) -> list[str]:
    """L'IA LIT le texte d'un référentiel et PROPOSE la liste des matières (disciplines / domaines)
    qu'il structure. Proposition seulement : l'admin coche ce qu'il retient (jamais une matière
    écrite d'office).

    `prompt_cycle` : le prompt VALIDÉ du cycle (cycles.prompt_matieres), écrit par l'IA pour cette
    famille de référentiels. Quand il est fourni, c'est LUI qui lit — un prompt taillé pour des BTS
    trouve ce qu'un prompt passe-partout laisse tomber. Absent (cycle pas encore doté, prompt non
    validé) : on retombe sur le prompt général `detecter_matieres`, comme avant.

    Elle ne reçoit QUE le texte. La table des matières ne lui est plus donnée : il n'existe plus
    de catalogue commun auquel ramener le document. Chaque référentiel possède SES matières,
    nommées comme LUI les nomme — il n'y a donc rien à faire correspondre, et normaliser
    l'orthographe sur un autre diplôme serait une erreur, pas une aide.

    Prompt / provider / modèle / température lus EN BASE. Renvoie
    les noms nettoyés, sans doublon (insensible à la casse), dans l'ordre lu. Liste vide si l'IA n'en
    lit aucune. Lève `ValueError` si l'IA ne rend pas un JSON exploitable. Laisse remonter les pannes
    IA (l'appelant traduit / absorbe)."""
    prompt = (prompt_cycle or get_prompt(db, _CLE_MATIERES)).replace("{texte}", texte)
    raw = generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, _CLE_MATIERES),
        temperature=get_temperature(db),
        json_mode=True,
        schema=_schema_matieres(),
        appel_long=True,  # entrée = le référentiel entier (la sortie, elle, est courte)
        contexte_max=get_contexte_max(db),
        outil=_CLE_MATIERES,
        prefixe_cache=texte,   # le document est en tête du prompt : le fournisseur le garde
    )
    data = parser_reponse(raw)
    noms: list[str] = []
    vus: set[str] = set()
    for m in data.get("matieres", []):
        nom = (m if isinstance(m, str) else str(m)).strip()
        if nom and nom.lower() not in vus:
            vus.add(nom.lower())
            noms.append(nom)
    return noms


# Clé EN BASE du prompt de détection du COUPLE (cycle + niveau) — dépôt « PDF d'abord » :
# l'IA propose, le serveur fait la correspondance avec les tables, l'admin dispose.
_CLE_DETECTER_COUPLE = "detecter_couple"


def _schema_detecter_couple() -> dict:
    """Sortie structurée de la détection du couple : `cycle_lu` / `niveau_lu` = ce que le document
    vise, repris à l'ORTHOGRAPHE EXACTE de la liste fournie quand ça correspond (sinon le nom lu).
    Chaîne vide = le document ne permet pas de le dire."""
    return {
        "type": "object",
        "properties": {
            "cycle_lu": {"type": "string"},
            "niveau_lu": {"type": "string"},
        },
        "required": ["cycle_lu", "niveau_lu"],
        "additionalProperties": False,
    }


def detecter_couple(texte: str, *, db: Session) -> dict:
    """Dépôt « PDF d'abord » : l'IA LIT le début du document et PROPOSE le couple (cycle + niveau).
    Elle reçoit l'arbre des cycles → niveaux EXISTANTS (get, zéro copie) pour faire CORRESPONDRE
    le document avec les tables : orthographe exacte de la liste quand ça correspond, sinon le nom
    lu dans le document. La CORRESPONDANCE finale (ids) est faite par l'APPELANT contre la base —
    l'IA lit, la base tranche. Prompt / provider / modèle / température lus EN BASE. Lève
    `ValueError` si l'IA ne rend pas un JSON exploitable ; laisse remonter les pannes IA."""
    from backend.core.models_db import Cycle, Niveau
    lignes = []
    for c in db.query(Cycle).order_by(Cycle.ordre, Cycle.id).all():
        niveaux = [n.nom for n in (db.query(Niveau).filter(Niveau.cycle_id == c.id)
                                     .order_by(Niveau.ordre, Niveau.id).all())]
        lignes.append(f"- {c.nom} : {', '.join(niveaux) if niveaux else '(aucun niveau)'}")
    prompt = (get_prompt(db, _CLE_DETECTER_COUPLE)
              .replace("{cycles_existants}", "\n".join(lignes) or "(aucun cycle pour le moment)")
              .replace("{texte}", texte))
    raw = generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, _CLE_DETECTER_COUPLE),
        temperature=get_temperature(db),
        json_mode=True,
        schema=_schema_detecter_couple(),
        outil=_CLE_DETECTER_COUPLE,
        prefixe_cache=texte,   # le document est en tête du prompt : le fournisseur le garde
    )
    data = parser_reponse(raw)
    return {
        "cycle_lu": (data.get("cycle_lu") or "").strip(),
        "niveau_lu": (data.get("niveau_lu") or "").strip(),
    }


# Clé EN BASE du prompt de détection des TYPES D'ACTIVITÉ — proposés à partir des chunks du couple
# (proposition, pas une liaison validée : l'admin coche ce qu'il garde). Même patron que les matières.
_CLE_TYPES_ACTIVITE = "detecter_types_activite"


def _schema_types_activite() -> dict:
    """Sortie structurée de la détection : `types` = tableau de noms. `additionalProperties: false`
    interdit tout champ en trop (réponse contrainte, petite, ni troncature ni dépassement)."""
    return {
        "type": "object",
        "properties": {
            "types": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["types"],
        "additionalProperties": False,
    }


def detecter_types_activite(texte: str, *, db: Session, prompt_cycle: str | None = None) -> list[str]:
    """L'IA LIT le texte d'un référentiel et PROPOSE la liste des TYPES D'ACTIVITÉ (formats /
    modalités pédagogiques) qu'il met en œuvre. Proposition seulement : l'admin retient ce qu'il
    garde (jamais un type retenu d'office).

    `prompt_cycle` : le prompt du CYCLE (cycles.prompt_types), écrit par l'IA pour cette famille de
    référentiels. Quand il est fourni, c'est LUI qui lit. Absent (cycle pas encore doté) : on
    retombe sur le prompt général `detecter_types_activite`.

    Elle ne reçoit QUE le texte. Le catalogue des types ne lui est plus donné (05/08/2026) : il
    n'existe plus de liste commune à laquelle ramener le document. Chaque référentiel met en œuvre
    SES formats, nommés comme LUI les nomme — il n'y a donc rien à faire correspondre, et aligner
    le vocabulaire sur un autre diplôme serait une erreur, pas une aide. C'est le même
    raisonnement, et le même geste, que `detecter_matieres`.

    Prompt / provider / modèle / température lus EN BASE. Renvoie les noms
    nettoyés, sans doublon (insensible à la casse), dans l'ordre lu. Liste vide si l'IA n'en lit
    aucun. Lève `ValueError` si l'IA ne rend pas un JSON exploitable. Laisse remonter les pannes
    IA (l'appelant traduit)."""
    prompt = (prompt_cycle or get_prompt(db, _CLE_TYPES_ACTIVITE)).replace("{texte}", texte)
    raw = generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, _CLE_TYPES_ACTIVITE),
        temperature=get_temperature(db),
        json_mode=True,
        schema=_schema_types_activite(),
        appel_long=True,  # entrée = le référentiel entier (la sortie, elle, est courte)
        contexte_max=get_contexte_max(db),
        outil=_CLE_TYPES_ACTIVITE,
        prefixe_cache=texte,   # le document est en tête du prompt : le fournisseur le garde
    )
    data = parser_reponse(raw)
    noms: list[str] = []
    vus: set[str] = set()
    for m in data.get("types", []):
        nom = (m if isinstance(m, str) else str(m)).strip()
        if nom and nom.lower() not in vus:
            vus.add(nom.lower())
            noms.append(nom)
    return noms


# Clé EN BASE du prompt de suggestion des PRÉCISIONS d'un type d'activité pour un niveau donné.
# Ajoutée le 02/08/2026 : le texte vivait en dur dans la fonction ci-dessous, seul prompt du
# projet hors du registre administrable.
_CLE_PRECISIONS_TYPE = "suggerer_precisions_type"


def _schema_precisions_type() -> dict:
    """Sortie structurée : `precisions` = tableau de libellés. `additionalProperties: false` interdit tout
    champ en trop (réponse contrainte, petite, ni troncature ni dépassement)."""
    return {
        "type": "object",
        "properties": {"precisions": {"type": "array", "items": {"type": "string"}}},
        "required": ["precisions"],
        "additionalProperties": False,
    }


def suggerer_precisions_type(label: str, niveau: str, texte: str, *, db: Session) -> list[str]:
    """L'IA PROPOSE les PRÉCISIONS d'un type d'activité POUR CE NIVEAU, ancrées au référentiel. Une
    précision = une déclinaison concrète du type, RÉELLEMENT adaptée au niveau (ex. « Activités écrites » :
    « copie », « dictée » en primaire ; « dissertation », « mémoire » dans le supérieur). Même plomberie
    que `detecter_types_activite` : provider / modèle / température lus EN BASE, JSON
    contraint. Renvoie des libellés nettoyés, sans doublon (insensible à la casse), dans l'ordre rendu.
    Lève `ValueError` si l'IA ne rend pas un JSON exploitable (l'appelant absorbe)."""
    # Le texte de ce prompt était ÉCRIT ICI, en f-string. C'était le seul vrai prompt du projet
    # hors du registre : invisible à l'écran d'administration, donc ni lisible ni corrigeable —
    # alors que les trois autres fonctions de CE fichier passaient déjà par get_prompt.
    # `.replace()` et non `.format()`, comme sa voisine detecter_types_activite : le texte vient
    # de la base et peut porter des accolades qui ne sont pas des repères.
    prompt = (get_prompt(db, _CLE_PRECISIONS_TYPE)
              .replace("{label}", label)
              .replace("{niveau}", niveau)
              .replace("{texte}", texte))
    raw = generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        # 2000 était écrit en dur ici, avec sa raison : « 300 coupait la réponse ». La raison
        # tient, le nombre en dur non — il devient réglable. Sans surcharge en base, ceci résout
        # sur le défaut global (2048) : la marge reste au-dessus des 2000 d'avant.
        max_tokens=get_max_tokens(db, _CLE_PRECISIONS_TYPE),
        temperature=get_temperature(db),
        json_mode=True,
        schema=_schema_precisions_type(),
        outil=_CLE_PRECISIONS_TYPE,
        prefixe_cache=texte,   # le document est en tête du prompt : le fournisseur le garde
    )
    data = parser_reponse(raw)
    noms: list[str] = []
    vus: set[str] = set()
    for m in data.get("precisions", []):
        nom = (m if isinstance(m, str) else str(m)).strip()
        if nom and nom.lower() not in vus:
            vus.add(nom.lower())
            noms.append(nom)
    return noms


