# -*- coding: utf-8 -*-
"""Génère les documents crèche d'aSchool à partir des quatre sources analysées.

UN SEUL DOCUMENT, ET IL SE RESTREINT — c'est le correctif principal du 08/08/2026.

La version d'avant mettait tout dedans : les activités d'éveil, les temps du quotidien, ET le
fonctionnement de l'établissement (relation aux parents, transmissions à l'équipe, organisation de
la journée, qualité de vie au travail). Or la recherche vectorielle ne filtre que sur
`referentiel_id` — voir `retrieve_pg` dans backend/rag/pgvector_store.py, la seule autre clause
(`option_ab`) ne joue que pour les diplômes à options, ce que la crèche n'a pas. Une fiche
« La qualité de vie au travail » pouvait donc remonter sur une demande d'activité d'éveil.

Le document ne garde donc QUE ce que le professionnel fait avec l'enfant : Doc 1, Doc 2, et la
première partie du Doc 3. Les treize fiches de fonctionnement interne sont retirées. Elles restent
disponibles dans `d_metier.py` — la liste METIER n'est simplement plus rendue — si le besoin d'un
référentiel séparé se présente un jour.

CONSÉQUENCE SUR LE DOC 4. Il n'était source que des fiches « métier » : il quitte donc entièrement
le référentiel principal. C'était le point le plus sérieux relevé à la relecture — la fiche
« La santé, la prévention et les premiers soins » s'appuyait sur lui seul, qui n'est qu'une liste
de puces sans contexte (« Administrer un médicament ou utiliser un aérosol selon les directives du
médecin »). Isolée en chunk, cette fiche livrait une consigne d'acte de soin sans aucun garde-fou.
Le volet santé du Doc 3 reste couvert dans le principal par ses propres fiches de partie 1.

CE QUI NE CHANGE PAS DEPUIS LA VERSION PRÉCÉDENTE.

1. LE PLAN NE RÉPOND PAS À LA PLACE DES PROMPTS. Aucun regroupement par domaine : une suite de
   fiches, toutes bâties pareil. Ce sont des ATTRIBUTS écrits dans chaque fiche — `Forme`,
   `Ce que l'enfant développe` — qui portent l'information ; le regroupement est le travail des
   prompts, pas celui du plan.

2. LES SOURCES SONT CROISÉES, PAS EMPILÉES. Le Doc 1 et le Doc 2 décrivent les mêmes objets sans
   le dire de la même façon : chaque fiche prend des deux.

3. RIEN N'EST INVENTÉ. Chaque fiche porte sa source. Ce qui n'est dans aucun des quatre documents
   n'est pas dans ceux-ci. Les titres de fiches sont ceux que la source imprime EN TÊTE DE FICHE,
   et non ceux de son sommaire — le Doc 2 diverge sur trois d'entre elles (« Une petite parlotte »
   au corps contre « C'est le moment de parler doucement » au sommaire, « Je suis là » contre
   « Je suis ici », « Est-ce que tu peux m'imiter ? » contre « Pouvez-vous m'imiter ? »). C'est le
   corps qui fait foi : c'est ce que le professionnel a sous les yeux.
"""
import os
import sys

from fpdf import FPDF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from d_eveil import EVEIL                    # noqa: E402
from d_sans_materiel import SANS_MATERIEL    # noqa: E402
from d_psy import PSYCHOSOCIAL               # noqa: E402
from d_quotidien import QUOTIDIEN            # noqa: E402
from d_metier import METIER                  # noqa: E402

F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BLEU = (30, 58, 95)
GRIS = (90, 100, 115)
GRIS_C = (140, 150, 165)
NOIR = (35, 40, 50)
FILET = (205, 213, 224)
FOND = (246, 248, 251)

PIED = "Référentiel maison aSchool — en service, sans valeur institutionnelle"

# ─────────────────────────────────────────────────────────── notices de sources, par document
NOTICE_D1 = (
  "DOC 1 — UNICEF",
  "Manuel d'activité pour le développement de la petite enfance — Module III, in Manuel Éducation "
  "en situation d'urgence et de crise (ESU), Kits d'éducation de l'UNICEF, Division des "
  "approvisionnements (WSEC), Copenhague. Auteur : Miresi Busana, 1ʳᵉ édition, 2013. Périmètre "
  "repris : Unité I / Activité II (activités manuelles et artistiques, de jeu, d'expression, de "
  "lecture) et Unité II (activités psychosociales), pour les tranches d'âge touchant 0-3 ans. "
  "Unités III et IV écartées, hors périmètre éveil.")

NOTICE_D2 = (
  "DOC 2 — UNICEF",
  "Le kit pour le développement de la petite enfance — Guide d'activités : une boîte à trésors "
  "pleine d'activités. Unité du Développement de la petite enfance de l'UNICEF, avec Cassie "
  "Landers, consultante ; illustrations de Joan Auclair. Prototype non préparé selon les normes "
  "officielles de publication. Périmètre repris : les 22 activités marquées « Bébés » ou « 1-3 "
  "ans » — 14 avec matériel, 8 sans matériel. Les activités « 4-6 ans » sont écartées. Les titres "
  "retenus sont ceux imprimés en tête de fiche, non ceux du sommaire, qui en diffère sur trois "
  "d'entre elles.")

NOTICE_D3_P1 = (
  "DOC 3 — ÉTAT FRANÇAIS",
  "Référentiel national de la qualité d'accueil du jeune enfant. Avril 2025. Ministère du Travail, "
  "de la Santé, des Solidarités et des Familles. Élaboration pilotée par l'Inspection générale des "
  "affaires sociales : Dr Nicole Bohic et Jean-Baptiste Frossard. Deux ans de travaux, 7 groupes "
  "de travail, près de 2 000 professionnels consultés. Base légale : article L214-1-1 du code de "
  "l'action sociale et des familles. Périmètre repris ICI : les 22 fiches de sa PREMIÈRE PARTIE, "
  "la relation au jeune enfant. Ses parties 2 et 3 — la relation aux familles et la qualité "
  "organisationnelle — sont écartées : elles portent sur le fonctionnement du service, non sur ce "
  "que le professionnel fait avec l'enfant. Document public librement réutilisable.")

NOTICE_D3_P23 = (
  "DOC 3 — ÉTAT FRANÇAIS",
  "Référentiel national de la qualité d'accueil du jeune enfant. Avril 2025. Ministère du Travail, "
  "de la Santé, des Solidarités et des Familles. Élaboration pilotée par l'Inspection générale des "
  "affaires sociales : Dr Nicole Bohic et Jean-Baptiste Frossard. Base légale : article L214-1-1 "
  "du code de l'action sociale et des familles. Périmètre repris ICI : ses DEUXIÈME et TROISIÈME "
  "PARTIES — la relation aux familles, et la qualité organisationnelle. Sa première partie n'est "
  "pas dans ce document : elle est dans le référentiel d'éveil. Document public librement "
  "réutilisable.")

NOTICE_D4 = (
  "DOC 4 — CAHIER DES CHARGES D'ÉDUCATRICE DE LA PETITE ENFANCE",
  "Cahier des charges / rôle — Éducatrice de la petite enfance (EDE), établissement d'accueil "
  "privé. Périmètre repris : les missions du métier — éduquer et socialiser, fonction de soins et "
  "de santé, organiser et planifier, fonction sociale et de communication, déontologie, "
  "auto-analyse. Le vocabulaire local (outils internes, intitulés de diplômes propres au pays "
  "d'origine) est écarté. Ce document ne porte aucun contenu pédagogique et ne développe rien : "
  "c'est une liste de missions, sans contexte ni mode d'emploi. Il ne sert donc JAMAIS de source "
  "principale à une fiche — seulement à corroborer et à nommer des missions que les trois autres "
  "décrivent sans les nommer. C'est la raison pour laquelle il ne figure pas dans le référentiel "
  "d'éveil.")

# ─────────────────────────────────────────────────────────── les deux documents
PRINCIPAL = {
  "titre": "Référentiel d'éveil 0-3 ans",
  "sous_titre": "Activités d'éveil et temps du quotidien\npour les métiers de la petite enfance",
  "entete": "Référentiel d'éveil 0-3 ans — aSchool",
  "activites": EVEIL + SANS_MATERIEL + PSYCHOSOCIAL,
  "pratiques": QUOTIDIEN,
  "destinataire":
    "Le destinataire est le professionnel qui accueille et anime l'éveil des tout-petits : "
    "éducateur de jeunes enfants, auxiliaire de puériculture, assistant maternel. Le format des "
    "activités est celui d'une activité animée par l'adulte avec l'enfant — pas d'exercices "
    "« questions-réponses » adressés à l'enfant.",
  "perimetre":
    "Ce document ne traite QUE de ce que le professionnel fait avec l'enfant : les activités "
    "d'éveil et les temps du quotidien. Tout ce qui relève du fonctionnement de l'établissement — "
    "relation aux familles, transmissions à l'équipe, organisation de la journée, projet "
    "pédagogique, qualité de vie au travail — en est écarté. Ce retrait n'est pas éditorial : la "
    "recherche documentaire d'aSchool ne filtre que par référentiel, si bien qu'une fiche "
    "d'organisation interne rangée ici ressortirait en réponse à une demande d'activité d'éveil.",
  "notices": [NOTICE_D1, NOTICE_D2, NOTICE_D3_P1],
  "droits": [
    "Les Doc 1 et Doc 2 sont des publications de l'UNICEF : leur réutilisation reste à traiter au "
    "moment de la diffusion.",
    "Le Doc 3 est un document public de l'État français, librement réutilisable, dont la diffusion "
    "est explicitement encouragée.",
  ],
  "avertissement_unicef": True,
  "sortie": "/app/referentiel_creche/REFERENTIEL-EVEIL-0-3-aSchool-CC.pdf",
}

INTERNE = {
  "titre": "Fonctionnement et pratique d'établissement",
  "sous_titre": "Relation aux familles, travail en équipe et organisation\ndans un lieu d'accueil "
                "0-3 ans",
  "entete": "Fonctionnement et pratique d'établissement — aSchool",
  "activites": [],
  "pratiques": METIER,
  "destinataire":
    "Le destinataire est l'équipe d'un lieu d'accueil et sa direction. Ce document ne décrit "
    "aucune activité à mener avec un enfant : il porte sur la relation aux familles, le travail "
    "en équipe et l'organisation du service.",
  "perimetre":
    "Ce document est SÉPARÉ du référentiel d'éveil, et ce n'est pas un choix de présentation. La "
    "recherche documentaire d'aSchool ne filtre que par référentiel : rangées avec les activités, "
    "ces fiches pourraient ressortir en réponse à une demande d'activité d'éveil. Elles ne "
    "doivent donc être ingérées que dans un référentiel qui leur est propre, ou pas du tout.",
  "notices": [NOTICE_D3_P23, NOTICE_D4],
  "droits": [
    "Le Doc 3 est un document public de l'État français, librement réutilisable, dont la diffusion "
    "est explicitement encouragée.",
    "Le Doc 4 est un document interne d'un établissement privé : son autorisation de réutilisation "
    "est à obtenir avant toute diffusion hors d'aSchool. Son nom, son adresse et son vocabulaire "
    "local en ont été retirés.",
  ],
  "avertissement_unicef": False,
  "sortie": "/app/referentiel_creche/REFERENTIEL-FONCTIONNEMENT-0-3-aSchool-CC.pdf",
}


class Doc(FPDF):
    # fpdf laisse le curseur horizontal là où le texte s'est arrêté. Un bloc écrit à la suite
    # démarre alors décalé, et finit par n'avoir plus la largeur d'un seul caractère — la
    # génération s'arrête là. On remet donc le curseur à la marge après chaque bloc ; les cadres,
    # qui travaillent en retrait, repositionnent le leur avant chaque appel.
    def multi_cell(self, *a, **k):
        r = super().multi_cell(*a, **k)
        self.set_x(self.l_margin)
        return r

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("DJ", "", 7.5)
        self.set_text_color(*GRIS_C)
        self.cell(0, 5, self.entete, 0, 0, "L")
        self.cell(0, 5, self.section, 0, 1, "R")
        self.set_draw_color(*FILET)
        self.line(15, 18, 195, 18)
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font("DJ", "", 7)
        self.set_text_color(*GRIS_C)
        self.cell(0, 4, PIED, 0, 1, "C")
        self.cell(0, 4, str(self.page_no()), 0, 0, "C")


def construire(spec):
    """Rend UN des deux documents. Tout ce qui les distingue est dans `spec` : rien n'est décidé
    ici. Renvoie (chemin, nb_pages, nb_fiches)."""
    doc = Doc(format="A4")
    doc.section = ""
    doc.entete = spec["entete"]
    doc.add_font("DJ", "", F, uni=True)
    doc.add_font("DJ", "B", FB, uni=True)
    doc.set_auto_page_break(True, margin=20)
    doc.set_margins(15, 15, 15)

    def titre_fiche(t):
        """Le titre d'une unité : UNE ligne physique, sans numéro, sans préfixe. C'est cette ligne
        que la découpe cherchera — elle ne doit jamais être coupée en deux ni précédée d'un
        chiffre."""
        doc.set_x(doc.l_margin)
        doc.ln(3)
        if doc.get_y() > 250:
            doc.add_page()
        doc.set_font("DJ", "B", 11.5)
        doc.set_text_color(*BLEU)
        doc.multi_cell(0, 6, t)
        doc.set_draw_color(*FILET)
        doc.line(15, doc.get_y() + 0.5, 195, doc.get_y() + 0.5)
        doc.ln(2.5)

    def rubrique(etiquette, texte):
        """Une rubrique interne : étiquette + deux-points, sur la même ligne que son contenu. C'est
        ce format que le prompt de découpe apprendra à NE PAS relever."""
        if not texte:
            return
        doc.set_x(doc.l_margin)
        doc.set_font("DJ", "B", 8.5)
        doc.set_text_color(*GRIS)
        largeur = doc.get_string_width(etiquette + " : ") + 1
        doc.cell(largeur, 4.6, etiquette + " :", 0, 0)
        doc.set_font("DJ", "", 8.5)
        doc.set_text_color(*NOIR)
        doc.multi_cell(0, 4.6, texte)
        doc.ln(0.8)

    def puces(etiquette, items, sous_titre=None):
        if not items:
            return
        doc.set_x(doc.l_margin)
        if etiquette:
            doc.set_font("DJ", "B", 8.5)
            doc.set_text_color(*GRIS)
            doc.multi_cell(0, 4.6, etiquette + " :")
        if sous_titre:
            doc.set_font("DJ", "B", 8.5)
            doc.set_text_color(*BLEU)
            doc.multi_cell(0, 4.4, "  " + sous_titre)
        doc.set_font("DJ", "", 8.5)
        doc.set_text_color(*NOIR)
        for it in items:
            x = doc.get_x()
            doc.cell(4, 4.4, "", 0, 0)
            doc.set_x(x + 4)
            doc.multi_cell(0, 4.4, "— " + it)
        doc.ln(0.8)

    def fiche_activite(f):
        titre_fiche(f["titre"])
        rubrique("Forme", f.get("forme"))
        rubrique("Âge", f.get("age"))
        rubrique("Matériel", f.get("materiel") or "aucun")
        rubrique("Ce que l'enfant développe", f.get("developpe"))
        blocs = f.get("faire") or []
        doc.set_font("DJ", "B", 8.5)
        doc.set_text_color(*GRIS)
        doc.multi_cell(0, 4.6, "Ce que fait le professionnel :")
        for tranche, items in blocs:
            puces(None, items, sous_titre=tranche)
        puces("À observer", f.get("observer"))
        puces("Prolongements", f.get("prolongements"))
        puces("Sécurité", f.get("securite"))
        rubrique("Source", f.get("source"))

    def fiche_pratique(f):
        titre_fiche(f["titre"])
        rubrique("Forme", f.get("forme"))
        puces("À retenir", f.get("retenir"))
        puces("Ce que fait le professionnel", f.get("faire"))
        puces("Ce que le professionnel ne fait pas", f.get("pasfaire"))
        rubrique("Source", f.get("source"))

    def encadre(titre, lignes):
        if doc.get_y() > 225:
            doc.add_page()
        y0 = doc.get_y()
        doc.set_fill_color(*FOND)
        doc.set_draw_color(*FILET)
        doc.set_font("DJ", "B", 9)
        doc.set_text_color(*BLEU)
        doc.set_x(18)
        doc.multi_cell(174, 5.4, titre, 0, "L")
        doc.set_font("DJ", "", 8.5)
        doc.set_text_color(*NOIR)
        for l in lignes:
            doc.set_x(18)
            doc.multi_cell(174, 4.4, l)
        y1 = doc.get_y()
        doc.rect(15, y0 - 2, 180, y1 - y0 + 4)
        doc.ln(5)
        doc.set_x(doc.l_margin)

    # ─────────────────────────────────────────────────────── page de titre
    doc.add_page()
    doc.ln(38)
    doc.set_font("DJ", "B", 27)
    doc.set_text_color(*BLEU)
    doc.set_x(15)
    doc.multi_cell(0, 13, spec["titre"], 0, "C")
    doc.set_font("DJ", "", 13)
    doc.set_text_color(*GRIS)
    doc.set_x(15)
    doc.multi_cell(0, 7, spec["sous_titre"], 0, "C")
    doc.ln(6)
    doc.set_font("DJ", "", 10)
    doc.set_text_color(*GRIS_C)
    doc.set_x(15)
    doc.multi_cell(0, 5.5, "CRÈCHE · NIVEAU BMG_0-3", 0, "C")
    doc.ln(16)
    lignes = [
      "Ce document est élaboré en interne par aSchool à partir de publications extérieures, dont "
      "il reprend et croise le contenu. Il n'a aucune valeur institutionnelle : aucune des sources "
      "ne l'a relu ni validé.",
      "",
    ]
    if spec["avertissement_unicef"]:
        lignes += [
          "Reprise de l'avertissement UNICEF : « Les opinions et points de vue exprimés dans le "
          "présent document sont entièrement ceux de leurs auteurs et ne peuvent en aucune manière "
          "être attribués au Fonds des Nations Unies pour l'enfance (UNICEF)… Le texte n'a pas été "
          "préparé en conformité avec les normes officielles de publication. »",
        ]
    else:
        lignes += [
          "Il n'engage ni le ministère chargé des Solidarités et des Familles, ni l'établissement "
          "dont le cahier des charges a été utilisé.",
        ]
    encadre("RÉFÉRENTIEL MAISON — SANS VALEUR INSTITUTIONNELLE", lignes)

    # ─────────────────────────────────────────────────────── préambule
    doc.add_page()
    doc.section = "Préambule"
    doc.set_font("DJ", "B", 15)
    doc.set_text_color(*BLEU)
    doc.multi_cell(0, 8, "Préambule")
    doc.ln(2)

    paragraphes = [("À qui s'adresse ce document", spec["destinataire"]),
                   ("Ce que ce document contient, et ce qu'il ne contient pas", spec["perimetre"])]
    if spec["activites"]:
        paragraphes += [
         ("Tranches d'âge",
          "Ce document reprend les tranches telles que les sources les distinguent : Bébés (0-1 "
          "an) et 1-3 ans, ou « Bébés-3 ans » quand la source ne les sépare pas. Le contenu « 4-6 "
          "ans » et « 4-8 ans » des sources est écarté, hors périmètre crèche. Le référentiel ne "
          "subdivise pas lui-même la bande 1-3 : les sources ne la distinguent pas, et aSchool "
          "n'invente pas cette finesse."),
         ("Le jeu, moteur de l'apprentissage",
          "Le cerveau grandit plus vite pendant les cinq premières années qu'à tout autre moment. "
          "C'est par le jeu que les enfants apprennent : en jouant, ils se servent de tous leurs "
          "sens — ouïe, vue, goût, toucher, odorat, mouvement — pour récolter des informations sur "
          "le monde et se construire. Le rôle de l'adulte est d'accompagner, parler, écouter, "
          "encourager, rassurer — jamais de punir verbalement ou physiquement."),
        ]
    for t, corps in paragraphes:
        doc.set_x(doc.l_margin)
        doc.set_font("DJ", "B", 10)
        doc.set_text_color(*BLEU)
        doc.multi_cell(0, 5.5, t)
        doc.set_font("DJ", "", 9)
        doc.set_text_color(*NOIR)
        doc.multi_cell(0, 4.8, corps)
        doc.ln(3)

    # Le mode d'emploi énumère TOUTES les rubriques qui existent réellement, et dit qu'il y a deux
    # gabarits. La version d'avant n'en documentait que trois sur onze, en oubliant les deux plus
    # fréquentes du document : un mode d'emploi qui ne décrivait pas ce qu'il y a dans les pages.
    lire = [
      "Chaque fiche se tient seule : on peut la consulter sans lire ce qui précède ni ce qui suit. "
      "Les rubriques s'écrivent sous la forme « étiquette : contenu ».",
      "",
      "Rubriques communes à toutes les fiches :",
      "Forme — COMMENT le travail se déroule, avec le mot employé par la source qui l'énonce. Une "
      "même fiche peut en porter deux quand deux sources la décrivent différemment.",
      "Ce que fait le professionnel — les gestes, tels que la source les formule. C'est la rubrique "
      "la plus fournie du document.",
      "Source — le ou les documents d'origine, et l'endroit précis qui a été repris.",
    ]
    if spec["activites"]:
        lire += [
          "",
          "Il y a DEUX gabarits de fiche, selon ce que la source fournit.",
          "",
          "Une fiche d'ACTIVITÉ porte en plus : Âge (les tranches distinguées par la source) ; "
          "Matériel (« aucun » s'il n'en faut pas) ; Ce que l'enfant développe (SUR QUOI porte le "
          "travail, dans les termes de la source) ; À observer ; Prolongements ; Sécurité.",
          "Une fiche de PRATIQUE porte en plus : À retenir (l'essentiel de la fiche, en tête) ; "
          "Ce que le professionnel ne fait pas — présente seulement quand la source proscrit "
          "explicitement quelque chose.",
          "",
          "Une rubrique absente veut dire que la source ne dit rien sur ce point : elle n'est "
          "jamais remplie d'office.",
        ]
    else:
        lire += [
          "",
          "Toutes les fiches de ce document sont des fiches de PRATIQUE. Elles portent en plus : "
          "À retenir (l'essentiel de la fiche, en tête) ; Ce que le professionnel ne fait pas — "
          "présente seulement quand la source proscrit explicitement quelque chose.",
          "",
          "Une rubrique absente veut dire que la source ne dit rien sur ce point : elle n'est "
          "jamais remplie d'office.",
        ]
    encadre("COMMENT LIRE UNE FICHE", lire)

    if spec["activites"]:
        encadre("SÉCURITÉ — RÈGLE GÉNÉRALE, VALABLE POUR TOUTE ACTIVITÉ", [
          "Les enfants sont en permanence sous la supervision d'un adulte responsable ; on ne les "
          "laisse jamais seuls.",
          "Aucun objet susceptible d'être porté à la bouche n'est laissé sans surveillance auprès "
          "d'un enfant de moins de trois ans.",
          "Jamais de punition verbale ou physique.",
          "Une rubrique Sécurité n'apparaît dans une fiche que lorsque la source signale un risque "
          "propre à cette activité-là. Son absence ne dispense pas de la présente règle.",
        ])

    # ─────────────────────────────────────────────────────── les fiches
    doc.add_page()
    doc.section = "Fiches"
    doc.set_font("DJ", "B", 15)
    doc.set_text_color(*BLEU)
    doc.multi_cell(0, 8, "Les fiches")
    doc.set_x(doc.l_margin)
    doc.set_font("DJ", "", 9)
    doc.set_text_color(*GRIS)
    doc.multi_cell(0, 4.8,
      "Elles se suivent sans regroupement : ni chapitre par domaine, ni chapitre par famille. Ce "
      "qui distingue une fiche d'une autre est écrit DANS la fiche, à la rubrique Forme. L'ordre "
      "est celui des sources.")
    doc.ln(3)

    for f in spec["activites"]:
        fiche_activite(f)
    for f in spec["pratiques"]:
        fiche_pratique(f)

    # ─────────────────────────────────────────────────────── sources
    doc.add_page()
    doc.section = "Sources"
    doc.set_font("DJ", "B", 15)
    doc.set_text_color(*BLEU)
    doc.multi_cell(0, 8, "Sources & attribution")
    doc.set_x(doc.l_margin)
    doc.set_font("DJ", "", 9)
    doc.set_text_color(*NOIR)
    doc.multi_cell(0, 4.8,
      "Ce document est une compilation, un croisement et une adaptation aSchool des publications "
      "suivantes, dont il reprend le contenu. Rien n'y a été inventé : aucune activité, aucune "
      "pratique, aucune tranche d'âge élargie au-delà de ce que les sources énoncent.")
    doc.ln(3)

    for titre, corps in spec["notices"]:
        doc.set_x(doc.l_margin)
        doc.set_font("DJ", "B", 9.5)
        doc.set_text_color(*BLEU)
        doc.multi_cell(0, 5.2, titre)
        doc.set_font("DJ", "", 8.5)
        doc.set_text_color(*NOIR)
        doc.multi_cell(0, 4.4, corps)
        doc.ln(2.5)

    encadre("STATUTS JURIDIQUES — ILS NE SONT PAS LES MÊMES", spec["droits"])

    doc.output(spec["sortie"])
    return spec["sortie"], doc.page_no(), len(spec["activites"]) + len(spec["pratiques"])


chemin, pages, fiches = construire(PRINCIPAL)
print(f"{chemin} — {pages} pages, {fiches} fiches")
