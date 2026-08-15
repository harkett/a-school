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
from difflib import SequenceMatcher
import re

from sqlalchemy.orm import Session

from backend.systeme.admin import (
    get_ai_model, get_ai_provider, liste_fournisseurs, get_cle_texte, get_contexte_max, get_max_tokens, get_prompt,
    get_settings_dict, get_temperature,
)
from backend.llm.generator import generate, generate_cached

logger = logging.getLogger(__name__)

_CLE_PROMPT = "analyse_amont"
_CLE_DECOUPE = "decoupe_amont"
# LES QUATRE MÉTA-PROMPTS N'ONT PLUS DE CLÉ GÉNÉRALE (08/08/2026). Ils vivent UNIQUEMENT sur le
# référentiel qui les emploie — `referentiels.prompt_meta_matieres`, `_decoupe`, `_types`,
# `_precisions` — et le code les reçoit par l'argument `meta_referentiel`. Le repli sur un
# `Setting` partagé a été retiré : un gabarit écrit pour une famille de diplômes, appliqué à un
# document qu'il ne connaît pas, ne rend pas un prompt approximatif mais un prompt FAUX (il fait
# chercher une grille d'horaires dans un programme de crèche). Et il ne servait jamais : c'est
# l'admin qui crée un référentiel, il en écrit les prompts avant de s'en servir.
#
# Reste ce seul Setting, qui n'a pas d'équivalent par référentiel parce qu'il ne lit AUCUN
# document : le méta-prompt de CRITIQUE. L'IA y relit le prompt de découpe qu'elle vient de
# générer et le corrige s'il viole le contrat (titres verbatim, JSON exact, pas de contenu,
# exclusions) avant de l'afficher à l'admin. Générique par nature, donc partagé.
_CLE_VERIF = "prompt_verif_decoupe"

# Schéma STRICT de la découpe (Structured Outputs) : le modèle ne renvoie QUE des titres.
# `additionalProperties: false` interdit tout champ en trop (ex. « contenu ») → la génération est
# contrainte token par token, la réponse reste petite : ni troncature, ni dépassement de délai. On
# ne lit de toute façon que le titre (`_trancher_par_titres` tranche le texte réel) : le contenu que
# le modèle produisait était du poids mort. GÉNÉRIQUE : aucun axe métier ici, juste la forme.
#
# `garder` et `option` (05/08/2026). Le tranchage va d'un titre au titre SUIVANT : une zone sans
# titre reconnu se colle à sa voisine, et tout ce qui suit le dernier titre part avec lui (mesuré :
# deux blocs de 15 800 et 21 600 caractères, gonflés de sections hors périmètre et de la queue du
# document). Le prompt émet donc AUSSI les en-têtes des
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
                    # L'ANNEE DU CYCLE ('5e', '4e', '3e'…), chaine vide quand l'unite vaut pour
                    # tout le cycle. Un programme de cycle est UN document pour PLUSIEURS annees :
                    # sans ce champ, le prof d'une annee recoit le contenu des deux autres.
                    # Dans `required` comme les autres : le schema est strict, donc le champ
                    # existe meme si le prompt du couple oublie de le demander — il vaut alors
                    # "", c'est-a-dire « commune », le repli qui n'ampute personne.
                    "annee": {"type": "string"},
                    "garder": {"type": "boolean"},
                },
                "required": ["titre", "option", "annee", "garder"],
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
        provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
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
# MESURÉ le 06/08/2026 : sur 137 titres rendus, 16 étaient donnés pour « introuvables ». LES
# SEIZE ne différaient que par l'apostrophe (« d’équipe » contre « d'équipe »). Seize sur seize,
# perdues pour un caractère.
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

    Le second cas manquait, et il n'était pas rare : mesuré, 10 des 54 titres rendus par l'IA
    tenaient sur deux ou trois lignes parce que c'est ainsi qu'ils sont écrits dans le document. Ils
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


# SEUIL DU DÉDOUBLONNAGE — mesuré, pas choisi (07/08/2026).
#
# Un référentiel à plusieurs options répète ses passages communs, une fois par option. Le prompt
# de découpe liste TOUTES les occurrences (une entrée = une frontière, sinon l'unité d'avant
# déborde) : c'est donc ici, après tranchage, que les répétitions se fondent.
#
# LE CRITÈRE NE PEUT PAS ÊTRE LE TITRE. Mesuré sur un document à options, six paires portent le
# même intitulé et se répartissent en DEUX familles nettes :
#   - le même passage répété     : 93,6 % — 98,9 % — 89,8 % de similarité ;
#   - deux passages différents   : 21,6 % — 10,4 % — 12,7 %.
# Aucune paire n'est identique au caractère près (10 à 17 caractères d'écart : mise en forme,
# mention d'option). Un test d'égalité ne fusionnerait donc RIEN, et un test sur le titre seul
# ferait perdre une compétence sur deux — trois d'entre elles ont le même intitulé dans les deux
# options mais leurs propres connaissances associées.
#
# 0.75 tombe au milieu du fossé : 15 points sous la plus basse des vraies répétitions, 53 points
# au-dessus de la plus haute des fausses. Aucune des douze unités mesurées n'est près du seuil.
_SEUIL_DOUBLON = 0.75


def _dedoublonner(unites: list[dict]) -> list[dict]:
    """Fond les unités qui sont LE MÊME passage répété, garde celles qui n'en ont que le titre.

    Deux unités sont le même passage si leurs TITRES se recouvrent — égaux, ou l'un début de
    l'autre (le document ajoute parfois « (activité commune aux deux options) » à une seule des
    deux occurrences ; R3, en base, porte ainsi deux intitulés pour la même activité) — ET si
    leurs TEXTES se ressemblent au-delà du seuil.

    LE RECOUVREMENT, ET NON UNE RESSEMBLANCE DE TITRE. Mesuré : « Unité U4 » et « Unité U5 »
    diffèrent d'un caractère sur huit, soit 87 % de similarité — un seuil sur le titre les
    déclarait jumelles, et leurs textes (363 et 364 caractères, même structure) passaient aussi
    le seuil de contenu. Deux unités distinctes du diplôme disparaissaient donc dans une seule.
    Un titre court ne pardonne aucune approximation : sur huit caractères, un seul porte le sens.

    La première occurrence est gardée, la seconde jetée. Le journal dit ce qui a fondu et ce qui
    a été laissé distinct : sans lui, un seuil mal placé se verrait seulement au bout de la
    chaîne, dans une réponse d'IA appauvrie.

    Coût : les textes ne sont comparés que si les titres le sont déjà — `quick_ratio` (linéaire)
    élimine avant le `ratio` (quadratique). Sur 53 unités, instantané."""
    garde: list[dict] = []
    for u in unites:
        jumelle = None
        tu = _replier_blancs(u["titre"]).lower()
        for v in garde:
            tv = _replier_blancs(v["titre"]).lower()
            if not (tu.startswith(tv) or tv.startswith(tu)):
                continue
            m = SequenceMatcher(None, u["texte"], v["texte"])
            if m.quick_ratio() < _SEUIL_DOUBLON:
                continue      # borne SUPÉRIEURE du ratio : sous le seuil, inutile de calculer
            if m.ratio() >= _SEUIL_DOUBLON:
                jumelle = v
                break
        if jumelle is None:
            garde.append(u)
            continue
        # Le passage est commun aux deux options : il ne peut plus être dit propre à l'une d'elles.
        if jumelle["option"] and jumelle["option"] != u["option"]:
            jumelle["option"] = ""
        logger.info("découpe : doublon fondu — « %s » (%d car.) repris de « %s » (%d car.)",
                    u["titre"][:90], len(u["texte"]), jumelle["titre"][:90], len(jumelle["texte"]))
    return garde


def _trancher_par_titres(texte: str, titres: list) -> list[dict]:
    """Tranche le TEXTE RÉEL aux lignes de titre rendues par l'IA — jamais réécrit par l'IA
    (cap « aSchool n'invente rien »). Pur, sans IA, sans base : testable seul.
    Chaque unité = du titre retenu jusqu'au titre suivant, dans l'ordre du document. Un titre
    introuvable est ignoré (on ne fabrique pas de frontière). Les numéros de page
    (lignes-nombres) sont écartés avant tranchage. Renvoie `[{"titre","texte","option","annee"}]` dans l'ordre.

    ENTRÉES ACCEPTÉES : une chaîne (le titre seul, tout est gardé) ou un dict
    `{"titre", "option", "annee", "garder"}`. Les entrées `garder:false` sont des BORNES : elles servent à
    couper — c'est tout leur rôle — puis elles sont retirées du résultat. Sans elles, une section
    sans titre reconnu se colle à sa voisine et la queue du document part avec la dernière unité.

    LE CHOIX ENTRE PLUSIEURS OCCURRENCES. Un même intitulé figure souvent DEUX fois : une
    première dans un sommaire ou un récapitulatif, une seconde en tête de la vraie section.
    L'ancienne version retenait toujours la première : le récapitulatif raflait les titres, et
    les vraies sections, privées de frontière, se retrouvaient avalées par leur voisine. Mesuré
    le 02/08/2026 : 19 unités réduites à leur seule ligne de titre (la plus courte, 9 caractères)
    et 3 unités géantes emportant 75 % du document.

    LA RÈGLE : **un intitulé immédiatement suivi d'un autre intitulé de la liste ne porte aucun
    contenu — c'est une entrée de sommaire, pas une unité.** Elle ne nomme aucune section, aucun
    document, aucun métier : elle ne parle que de la forme, comme le reste du socle.

    ET SURTOUT, LE CHOIX EST GLOBAL — pas titre par titre (06/08/2026). Un curseur qui avançait
    en choisissant chaque titre pour lui seul ignorait ce que ce choix coûtait aux suivants.
    MESURÉ sur 137 titres rendus par le modèle : un intitulé à cinq occurrences voyait le curseur
    prendre la dernière (ligne 819), et les VINGT titres qui vivent entre la ligne 378 et la ligne
    819 devenaient « hors ordre » d'un coup — puis l'effet se propageait jusqu'à la fin. Bilan :
    47 titres placés, 90 perdus, 23 unités là où le document en contient une cinquantaine ; deux
    annexes entières disparaissaient.

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
    entrees = [{"titre": t, "option": "", "annee": "", "garder": True} if isinstance(t, str)
               else {"titre": (t.get("titre") or "").strip(),
                     "option": (t.get("option") or "").strip(),
                     "annee": (t.get("annee") or "").strip(),
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
    # jamais primer sur lui. Coût : O(nœuds²) — 137 titres font ~700 nœuds, instantané.
    # Le nœud transporte AUSSI `fin` — la ligne qui suit le titre. Un titre écrit sur DEUX lignes
    # dans le document (un code seul, puis son intitulé) serait sinon étiqueté par ce seul code :
    # on garderait la première ligne pour nom d'unité, et l'admin comme le prof
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
    # l'autre, et la tranche se réduit à sa ligne de titre. MESURÉ : 22 tranches sur 76 étaient
    # dans ce cas, de 9 à 63 caractères — la plus courte faisant exactement ses 9 caractères de
    # titre. Les vraies unités, elles, en portent 1 240 à 2 471.
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
        tranche = {"titre": titre_reel, "texte": bloc, "option": entrees[rang]["option"],
                   "annee": entrees[rang]["annee"]}
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
    # Les répétitions d'un document à plusieurs options se fondent ICI, sur le contenu réellement
    # tranché — le modèle, lui, a listé toutes les occurrences pour que chacune fasse frontière.
    avant = len(unites)
    unites = _dedoublonner(unites)
    if len(unites) != avant:
        logger.info("découpe : %d unités après dédoublonnage (%d fondues)",
                    len(unites), avant - len(unites))
    return unites


def generer_prompt_decoupe(texte: str, *, db: Session, meta_referentiel: str | None = None) -> str:
    """L'IA GÉNÈRE le prompt de découpe adapté à CE document. On lui donne le méta-prompt + le
    texte brut du PDF ; elle rend un prompt de découpe sur mesure (texte libre). SOCLE, générique :
    aucun prompt écrit en dur, aucun axe métier codé. Le résultat sera stocké en base par couple et
    validé par l'admin avant usage. Laisse remonter les pannes IA.

    `meta_referentiel` : le méta-prompt de CE référentiel (`referentiels.prompt_meta_decoupe`).
    C'est la SEULE source depuis le 08/08/2026 — le repli sur un réglage général a été retiré :
    un gabarit générique appliqué à un document qu'il ne connaît pas ne rend pas un prompt
    approximatif, il en rend un FAUX. Lève s'il est vide : jamais de découpe sans amorce
    écrite pour ce document."""
    meta = (meta_referentiel or "").strip()
    if not meta:
        raise RuntimeError(
            "Méta-prompt de découpe absent : écrivez-le sur CE référentiel "
            "(Prompts → Référentiels, ligne « prompt_meta_decoupe » de ce niveau)."
        )
    # Le document s'injecte au marqueur {document} du méta-prompt (distinct de {texte}, que le
    # méta-prompt demande au prompt GÉNÉRÉ de contenir). Ajouté en fin si le marqueur est absent.
    prompt = meta.replace("{document}", texte) if "{document}" in meta else f"{meta}\n\n{texte}"
    prompt_genere = generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
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


def generer_prompt_matieres(texte: str, *, db: Session, meta_referentiel: str | None = None) -> str:
    """L'IA GÉNÈRE le prompt qui lira les MATIÈRES de CE référentiel. Même geste que
    `generer_prompt_decoupe` : méta-prompt lu EN BASE + le texte du référentiel lui-même ; elle
    rend un prompt sur mesure (texte libre). SOCLE, générique : aucun prompt en dur, aucune famille
    de diplôme codée ici — c'est le document qui dicte. Le résultat est stocké sur le RÉFÉRENTIEL
    (le couple cycle+niveau) et validé par l'admin avant usage. Lève si le méta-prompt n'est pas en
    base. Laisse remonter les pannes IA.

    `meta_referentiel` : le méta-prompt de CE référentiel (`referentiels.prompt_meta_matieres`),
    seule source depuis le 08/08/2026. Le repli sur le réglage général a été retiré : il faisait
    chercher une grille d'horaires dans un programme de crèche."""
    meta = (meta_referentiel or "").strip()
    if not meta:
        raise RuntimeError(
            "Méta-prompt des matières absent : écrivez-le sur CE référentiel "
            "(Prompts → Référentiels, ligne « prompt_meta_matieres » de ce niveau)."
        )
    # {document} = le référentiel exemple ; {texte} doit rester INTACT (le prompt généré le porte).
    prompt = meta.replace("{document}", texte) if "{document}" in meta else f"{meta}\n\n{texte}"
    return generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, "meta_matieres"),
        temperature=get_temperature(db),
        appel_long=True,  # le méta-prompt embarque le référentiel complet
        contexte_max=get_contexte_max(db),
        outil="meta_matieres",
    ).strip()


def generer_prompt_types(texte: str, *, db: Session, meta_referentiel: str | None = None) -> str:
    """L'IA GÉNÈRE le prompt qui lira les TYPES D'ACTIVITÉ des référentiels de ce cycle. Troisième
    exemplaire du même geste que `generer_prompt_decoupe` et `generer_prompt_matieres` :
    méta-prompt lu EN BASE (`Setting[prompt_meta_types]`) + le texte d'un référentiel du cycle,
    pris comme exemple de sa famille ; elle rend un prompt sur mesure (texte libre).

    LA RÈGLE DES DEUX ÉTAGES (05/08/2026) : la DONNÉE appartient au référentiel qui la nomme (un
    type d'activité est lu dans le document, comme une matière), la RECETTE qui la lit appartient
    au CYCLE — une famille de documents bâtis pareil se lit avec la même recette. Le résultat est
    stocké sur le cycle. Lève si le méta-prompt n'est pas en base. Laisse remonter les pannes IA.

    `meta_referentiel` : le méta-prompt de CE référentiel (`referentiels.prompt_meta_types`),
    seule source depuis le 08/08/2026 (repli général retiré, comme pour les trois autres)."""
    meta = (meta_referentiel or "").strip()
    if not meta:
        raise RuntimeError(
            "Méta-prompt des types d'activité absent : écrivez-le sur CE référentiel "
            "(Prompts → Référentiels, ligne « prompt_meta_types » de ce niveau)."
        )
    # {document} = le référentiel exemple ; {texte} doit rester INTACT (le prompt généré le porte).
    prompt = meta.replace("{document}", texte) if "{document}" in meta else f"{meta}\n\n{texte}"
    return generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, "meta_types"),
        temperature=get_temperature(db),
        appel_long=True,  # le méta-prompt embarque le référentiel complet
        contexte_max=get_contexte_max(db),
        outil="meta_types",
    ).strip()


def generer_prompt_precisions(texte: str, *, db: Session, meta_referentiel: str | None = None) -> str:
    """L'IA GÉNÈRE le prompt qui lira les PRÉCISIONS d'un type d'activité dans CE référentiel.
    Quatrième exemplaire du même geste que `generer_prompt_types` : méta-prompt lu EN BASE + le
    texte du référentiel comme exemple ; elle rend un prompt sur mesure (texte libre).

    `meta_referentiel` : le méta-prompt de CE référentiel (`referentiels.prompt_meta_precisions`),
    seule source depuis le 08/08/2026 (repli général retiré, comme pour les trois autres).

    Le prompt rendu porte DEUX repères, et non un : {texte} (le document) et {label} (le type dont
    on veut les précisions). Lève si le méta-prompt n'est pas en base."""
    meta = (meta_referentiel or "").strip()
    if not meta:
        raise RuntimeError(
            "Méta-prompt des précisions absent : écrivez-le sur CE référentiel "
            "(Prompts → Référentiels, ligne « prompt_meta_precisions » de ce niveau)."
        )
    # {document} = le référentiel exemple ; {texte} et {label} doivent rester INTACTS (le prompt
    # généré les porte).
    prompt = meta.replace("{document}", texte) if "{document}" in meta else f"{meta}\n\n{texte}"
    return generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, "meta_precisions"),
        temperature=get_temperature(db),
        appel_long=True,  # le méta-prompt embarque le référentiel complet
        contexte_max=get_contexte_max(db),
        outil="meta_precisions",
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
        provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, "meta_decoupe"),
        temperature=get_temperature(db),
        outil="meta_decoupe",
    ).strip()


# `regenerer_prompt_decoupe` a été SUPPRIMÉE le 08/08/2026. Elle corrigeait un prompt de découpe à
# partir des remarques de l'admin, et lisait pour cela le méta-prompt GÉNÉRAL — celui-là même qui
# vient de disparaître. Aucun appelant : ni route, ni écran, ni test. Elle n'a donc jamais servi.


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
        provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
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
                                "annee": (u.get("annee") or "").strip(),
                                "garder": u.get("garder", True) is not False})
        else:
            t = str(u).strip()
            if t:
                entrees.append({"titre": t, "option": "", "annee": "", "garder": True})
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
        provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
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


def detecter_matieres(texte: str, *, db: Session, prompt_referentiel: str | None = None) -> list[str]:
    """L'IA LIT le texte d'un référentiel et PROPOSE la liste des matières (disciplines / domaines)
    qu'il structure. Proposition seulement : l'admin coche ce qu'il retient (jamais une matière
    écrite d'office).

    `prompt_referentiel` : le prompt de CE référentiel (referentiels.prompt_matieres), écrit pour
    ce couple cycle+niveau et pour lui seul. Quand il est fourni, c'est LUI qui lit — un prompt
    taillé pour ce diplôme trouve ce qu'un prompt passe-partout laisse tomber. Rangé sur le
    référentiel et non sur le cycle depuis le 06/08/2026 : deux diplômes du même cycle ne se lisent
    pas avec les mêmes repères (un prompt écrit sur les options d'un diplôme n'apprend rien sur le
    diplôme voisin). Absent (référentiel pas encore doté) : on retombe sur le
    prompt général `detecter_matieres`, comme avant.

    Elle ne reçoit QUE le texte. La table des matières ne lui est plus donnée : il n'existe plus
    de catalogue commun auquel ramener le document. Chaque référentiel possède SES matières,
    nommées comme LUI les nomme — il n'y a donc rien à faire correspondre, et normaliser
    l'orthographe sur un autre diplôme serait une erreur, pas une aide.

    Prompt / provider / modèle / température lus EN BASE. Renvoie
    les noms nettoyés, sans doublon (insensible à la casse), dans l'ordre lu. Liste vide si l'IA n'en
    lit aucune. Lève `ValueError` si l'IA ne rend pas un JSON exploitable. Laisse remonter les pannes
    IA (l'appelant traduit / absorbe)."""
    prompt = (prompt_referentiel or get_prompt(db, _CLE_MATIERES)).replace("{texte}", texte)
    raw = generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
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
        provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
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


def detecter_types_activite(texte: str, *, db: Session, prompt_referentiel: str | None = None) -> list[str]:
    """L'IA LIT le texte d'un référentiel et PROPOSE la liste des TYPES D'ACTIVITÉ (formats /
    modalités pédagogiques) qu'il met en œuvre. Proposition seulement : l'admin retient ce qu'il
    garde (jamais un type retenu d'office).

    `prompt_referentiel` : le prompt de CE référentiel (referentiels.prompt_types), écrit pour ce
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
    prompt = (prompt_referentiel or get_prompt(db, _CLE_TYPES_ACTIVITE)).replace("{texte}", texte)
    raw = generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
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


def suggerer_precisions_type(label: str, niveau: str, texte: str, *, db: Session,
                            prompt_referentiel: str | None = None) -> list[str]:
    """L'IA PROPOSE les PRÉCISIONS d'un type d'activité POUR CE NIVEAU, ancrées au référentiel. Une
    précision = une déclinaison concrète du type, RÉELLEMENT adaptée au niveau (ex. « Activités écrites » :
    « copie », « dictée » en primaire ; « dissertation », « mémoire » dans le supérieur). Même plomberie
    que `detecter_types_activite` : provider / modèle / température lus EN BASE, JSON
    contraint. Renvoie des libellés nettoyés, sans doublon (insensible à la casse), dans l'ordre rendu.
    Lève `ValueError` si l'IA ne rend pas un JSON exploitable (l'appelant absorbe).

    `prompt_referentiel` : le prompt de CE référentiel (`referentiels.prompt_precisions`), écrit
    pour ce document. Quand il est fourni, c'est LUI qui lit — même règle que
    `detecter_types_activite` et `detecter_matieres`. Absent : le prompt général reprend la main,
    qui ne connaît aucun document et rend des précisions plausibles plutôt que vérifiables."""
    # Le texte de ce prompt était ÉCRIT ICI, en f-string. C'était le seul vrai prompt du projet
    # hors du registre : invisible à l'écran d'administration, donc ni lisible ni corrigeable —
    # alors que les trois autres fonctions de CE fichier passaient déjà par get_prompt.
    # `.replace()` et non `.format()`, comme sa voisine detecter_types_activite : le texte vient
    # de la base et peut porter des accolades qui ne sont pas des repères.
    prompt = ((prompt_referentiel or get_prompt(db, _CLE_PRECISIONS_TYPE))
              .replace("{label}", label)
              .replace("{niveau}", niveau)
              .replace("{texte}", texte))
    raw = generate(
        prompt,
        cle=get_cle_texte(db),
        provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
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


