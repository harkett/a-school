"""Le tranchage d'un référentiel en unités — la fonction PURE, sans IA et sans base.

CE QUE CE FICHIER EMPÊCHE. `_trancher_par_titres` est le pivot de toute la découpe : l'IA ne
rend que des LIGNES DE TITRE, et c'est cette fonction qui taille le texte réel entre elles
(cap « aSchool n'invente rien » : le contenu n'est jamais réécrit par le modèle). Son propre
docstring annonce « Pur, sans IA, sans base : testable seul » — et elle n'avait aucun test.
C'est ce qui a laissé passer deux défauts, mesurés le 02/08/2026 sur le référentiel BTS CIEL :

  (a) TITRES SUR PLUSIEURS LIGNES — la comparaison portait sur UNE ligne. 10 des 54 titres
      rendus par l'IA (les six épreuves E1–E6, les deux épreuves facultatives, l'activité R3
      deux fois) tenaient sur deux ou trois lignes : aucun ne pouvait être trouvé, jamais.

  (b) LE SOMMAIRE VOLAIT LES TITRES — le balayage retenait la PREMIÈRE occurrence. Sur un
      document dont le récapitulatif reprend les intitulés avant les fiches détaillées, les
      titres étaient consommés par le récapitulatif : 19 unités réduites à leur seule ligne de
      titre (la plus courte : 9 caractères), et 3 unités géantes — les fiches détaillées, dont
      les titres avaient été mangés en amont — qui avalaient 75 % du document.

Ces deux défauts sont GÉNÉRIQUES : tout référentiel dont le sommaire reprend ses intitulés, ou
dont un titre passe à la ligne, tombe dedans. Aucun n'est propre au BTS.

Chaque cas ci-dessous est un texte fabriqué de quelques lignes : c'est tout ce qu'il faut.

Lancer : docker compose exec backend python -m pytest tests/test_trancher_par_titres.py -q
"""
from backend.rag.analyse_amont import _trancher_par_titres


def _textes(unites):
    return [u["texte"] for u in unites]


# ── (a) Les titres sur plusieurs lignes ──────────────────────────────────────────────────

def test_un_titre_a_cheval_sur_deux_lignes_est_trouve():
    """LE cas qui perdait les six épreuves du BTS. L'IA rend le titre tel qu'il se lit —
    « ÉPREUVE E1 » puis son intitulé à la ligne suivante — parce que c'est ainsi qu'il est
    écrit dans le document. Comparé ligne à ligne, il n'existe pas."""
    texte = (
        "ÉPREUVE E1\n"
        "CULTURE GÉNÉRALE\n"
        "Coefficient 2. Épreuve écrite.\n"
        "\n"
        "ÉPREUVE E2\n"
        "ANGLAIS\n"
        "Coefficient 3. Épreuve orale.\n"
    )
    unites = _trancher_par_titres(texte, ["ÉPREUVE E1\nCULTURE GÉNÉRALE",
                                          "ÉPREUVE E2\nANGLAIS"])
    assert len(unites) == 2, "un titre sur deux lignes n'est pas retrouvé"
    assert "Coefficient 2" in unites[0]["texte"] and "Coefficient 3" not in unites[0]["texte"]
    assert "Coefficient 3" in unites[1]["texte"]


def test_l_espacement_du_titre_n_a_pas_a_correspondre_au_caractere_pres():
    """L'IA recopie le titre en normalisant les blancs ; le document, lui, peut porter deux
    espaces ou une tabulation. La comparaison se fait donc sur les blancs REPLIÉS — et sur eux
    seuls : ni minuscules, ni accents retirés, ni ponctuation ignorée, sans quoi un titre court
    comme « C08 CODER » s'accrocherait n'importe où."""
    texte = "Activité   R1  –  Accompagnement\ndu client\ncontenu\n\nActivité R2\nautre contenu\n"
    unites = _trancher_par_titres(texte, ["Activité R1 – Accompagnement du client", "Activité R2"])
    assert len(unites) == 2
    assert "contenu" in unites[0]["texte"]


def test_la_casse_et_les_accents_ne_sont_PAS_ignores():
    """Le corollaire, et la limite assumée : on replie les blancs, rien d'autre. Une
    normalisation plus large (minuscules, accents) ferait correspondre des titres différents —
    sur un référentiel, « Unité U4 » et « UNITÉ U4 » peuvent désigner deux choses."""
    texte = "UNITE U4\ncontenu\n"
    assert _trancher_par_titres(texte, ["Unité U4"]) == []


# ── (b) Le sommaire qui vole les titres ──────────────────────────────────────────────────

def test_le_sommaire_ne_vole_plus_les_titres_des_vraies_sections():
    """LE cas qui a produit 19 unités vides et 3 blocs géants. Les intitulés apparaissent
    DEUX fois : d'abord dans un récapitulatif où ils se suivent sans contenu, puis en tête des
    vraies sections. La première occurrence n'est pas la bonne."""
    texte = (
        "Liste des compétences\n"
        "C01 COMMUNIQUER\n"
        "C02 ORGANISER\n"
        "C03 GÉRER\n"
        "\n"
        "C01 COMMUNIQUER\n"
        "Principales activités : accueil du client.\n"
        "\n"
        "C02 ORGANISER\n"
        "Principales activités : planification.\n"
        "\n"
        "C03 GÉRER\n"
        "Principales activités : suivi du projet.\n"
    )
    unites = _trancher_par_titres(texte, ["C01 COMMUNIQUER", "C02 ORGANISER", "C03 GÉRER"])
    assert len(unites) == 3
    assert "accueil du client" in unites[0]["texte"], (
        "le récapitulatif a été retenu à la place de la vraie section")
    assert "planification" in unites[1]["texte"]
    assert "suivi du projet" in unites[2]["texte"]
    # et aucune unité ne se réduit à sa ligne de titre
    assert all(len(t) > len(u["titre"]) for u, t in zip(unites, _textes(unites)))


def test_le_titre_qui_suit_le_sommaire_ne_ramasse_pas_l_entete_suivant():
    """Le chunk 25 du BTS, en miniature : le DERNIER intitulé du récapitulatif était suivi non
    pas d'un titre mais du titre de SECTION suivant, qu'il ramassait dans sa tranche — d'où
    « C11 MAINTENIR UN RÉSEAU INFORMATIQUE » suivi de « BTS CIEL – Option B ». Il est réglé
    par la même règle : les intitulés précédents ayant déjà filé au-delà du récapitulatif, le
    curseur ne peut plus revenir en arrière."""
    texte = (
        "Liste des compétences\n"
        "C01 COMMUNIQUER\n"
        "C02 ORGANISER\n"
        "Section B : autre partie\n"
        "\n"
        "C01 COMMUNIQUER\n"
        "Contenu réel de C01.\n"
        "\n"
        "C02 ORGANISER\n"
        "Contenu réel de C02.\n"
    )
    unites = _trancher_par_titres(texte, ["C01 COMMUNIQUER", "C02 ORGANISER"])
    assert len(unites) == 2
    assert "Section B" not in unites[0]["texte"] and "Section B" not in unites[1]["texte"], (
        "le titre de la section suivante a été ramassé dans une unité")
    assert "Contenu réel de C02" in unites[1]["texte"]


def test_un_document_entierement_en_liste_garde_ses_titres():
    """La limite de la règle, écrite exprès : si TOUTES les occurrences d'un intitulé sont
    suivies d'un autre intitulé, il n'y a pas de « vraie section » à préférer. On garde alors
    la première plutôt que de perdre l'unité — un défaut connu vaut mieux qu'une disparition."""
    texte = "A – Premier\nB – Second\nC – Troisième\n"
    unites = _trancher_par_titres(texte, ["A – Premier", "B – Second", "C – Troisième"])
    assert len(unites) == 3
    assert [u["titre"] for u in unites] == ["A – Premier", "B – Second", "C – Troisième"]


# ── Les garanties qui ne doivent pas bouger ──────────────────────────────────────────────

def test_un_titre_introuvable_est_ignore_sans_fabriquer_de_frontiere():
    """Cap « aSchool n'invente rien » : un titre halluciné par l'IA ne crée pas d'unité."""
    texte = "Titre A\ncontenu de A\n\nTitre C\ncontenu de C\n"
    unites = _trancher_par_titres(texte, ["Titre A", "Titre INEXISTANT", "Titre C"])
    assert [u["titre"] for u in unites] == ["Titre A", "Titre C"]
    assert "contenu de A" in unites[0]["texte"] and "Titre C" not in unites[0]["texte"]


def test_un_document_sans_sommaire_est_tranche_comme_avant():
    """Le témoin : sur un document où chaque intitulé n'apparaît qu'une fois — le cas du
    référentiel crèche, 27 unités et aucun titre nu — le résultat ne change pas."""
    texte = ("Imagier\nMatériel : un livre cartonné.\n\n"
             "Balles en éponge\nMatériel : trois balles.\n\n"
             "Sons familiers\nSans matériel.\n")
    unites = _trancher_par_titres(texte, ["Imagier", "Balles en éponge", "Sons familiers"])
    assert len(unites) == 3
    assert "livre cartonné" in unites[0]["texte"]
    assert "trois balles" in unites[1]["texte"]
    assert "Sans matériel" in unites[2]["texte"]


def test_le_texte_precedant_le_premier_titre_reste_dehors():
    """Page de garde, sommaire, introduction : tout ce qui précède la première unité est écarté.
    C'est ce qui explique qu'une découpe saine ne « couvre » que 80 à 91 % du texte source —
    la couverture mesure la taille du préambule, pas la qualité de la découpe."""
    texte = "Page de garde\nSommaire général\n\nTitre A\ncontenu de A\n"
    unites = _trancher_par_titres(texte, ["Titre A"])
    assert len(unites) == 1
    assert "Page de garde" not in unites[0]["texte"]


def test_les_unites_sont_dans_l_ordre_et_ne_se_chevauchent_pas():
    texte = "T1\naaa\n\nT2\nbbb\n\nT3\nccc\n"
    unites = _trancher_par_titres(texte, ["T1", "T2", "T3"])
    assert [u["titre"] for u in unites] == ["T1", "T2", "T3"]
    assert "bbb" not in unites[0]["texte"] and "aaa" not in unites[1]["texte"]


def test_aucun_titre_rendu_par_l_ia_donne_zero_unite():
    assert _trancher_par_titres("du texte\net encore\n", []) == []
