# -*- coding: utf-8 -*-
"""Rend en PDF le référentiel corrigé (HAB-CORRIGE.md).

POURQUOI CE SCRIPT EXISTE. Le PDF d'origine abîmait les mots à l'extraction : 68 espaces
parasites au milieu de mots (« Parler auss i », « des chaînette s »), mesurés avec pdfplumber,
c'est-à-dire l'extracteur que l'application utilise réellement (backend/rag/extraction.py). Ces
mots brisés partaient tels quels dans tous les prompts et dans les vecteurs d'embedding. Le même
extracteur sur un PDF produit par ce moteur-ci en trouve zéro. Le texte a donc été réparé à la
relecture, puis rendu ici.

Le Markdown d'entrée est plat : `## ` pour tout titre, `Étiquette : contenu` pour toute rubrique,
`— ` pour toute puce. Une section est une FICHE quand son premier bloc commence par « Forme : » ;
sinon c'est une section de préambule ou de sources. Rien d'autre n'est deviné.
"""
import io
import os
import sys

from fpdf import FPDF

# Les DejaVu, là où elles se trouvent : le dossier système du conteneur Linux, sinon celles que
# matplotlib embarque — le script doit tourner des deux côtés.
_DEJAVU = "/usr/share/fonts/truetype/dejavu"
if not os.path.isdir(_DEJAVU):
    import matplotlib
    _DEJAVU = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
F = os.path.join(_DEJAVU, "DejaVuSans.ttf")
FB = os.path.join(_DEJAVU, "DejaVuSans-Bold.ttf")

BLEU = (30, 58, 95)
GRIS = (90, 100, 115)
GRIS_C = (140, 150, 165)
NOIR = (35, 40, 50)
FILET = (205, 213, 224)
FOND = (246, 248, 251)

PIED = "Référentiel maison aSchool — en service, sans valeur institutionnelle"
ENTETE = "Référentiel d'éveil 0-3 ans — aSchool"

# Les étiquettes de rubrique, dans l'ordre des deux gabarits. Une ligne qui commence par l'une
# d'elles suivie de « : » est une rubrique ; toute autre ligne est du texte courant.
ETIQUETTES = ("Forme", "Âge", "Matériel", "Ce que l'enfant développe",
              "Ce que fait le professionnel", "À observer", "Prolongements", "Sécurité",
              "Source", "À retenir", "Ce que le professionnel ne fait pas")


class Doc(FPDF):
    # fpdf laisse le curseur horizontal là où le texte s'est arrêté. Un bloc écrit à la suite
    # démarre décalé et finit par n'avoir plus la largeur d'un caractère — la génération s'arrête
    # là. On remet le curseur à la marge après chaque bloc.
    def multi_cell(self, *a, **k):
        r = super().multi_cell(*a, **k)
        self.set_x(self.l_margin)
        return r

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("DJ", "", 7.5)
        self.set_text_color(*GRIS_C)
        self.cell(0, 5, ENTETE, 0, 0, "L")
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


def decouper(chemin):
    """Le Markdown en sections `(titre, [lignes])`, dans l'ordre du fichier."""
    sections, titre, corps = [], None, []
    for ligne in io.open(chemin, encoding="utf-8").read().splitlines():
        if ligne.startswith("## "):
            if titre is not None:
                sections.append((titre, corps))
            titre, corps = ligne[3:].strip(), []
        elif titre is not None:
            corps.append(ligne)
    if titre is not None:
        sections.append((titre, corps))
    return [(t, [l for l in c if l.strip()]) for t, c in sections]


doc = Doc(format="A4")
doc.section = ""
doc.add_font("DJ", "", F, uni=True)
doc.add_font("DJ", "B", FB, uni=True)
doc.set_auto_page_break(True, margin=20)
doc.set_margins(15, 15, 15)


def bloc(texte, taille=9, gras=False, couleur=NOIR, hauteur=4.8):
    doc.set_x(doc.l_margin)
    doc.set_font("DJ", "B" if gras else "", taille)
    doc.set_text_color(*couleur)
    doc.multi_cell(0, hauteur, texte)


def rubrique(etiquette, contenu):
    """Étiquette en gras sur la même ligne que son contenu — le format que le prompt de découpe
    apprend à ne PAS relever comme un titre."""
    doc.set_x(doc.l_margin)
    doc.set_font("DJ", "B", 8.5)
    doc.set_text_color(*GRIS)
    largeur = doc.get_string_width(etiquette + " : ") + 1
    doc.cell(largeur, 4.6, etiquette + " :", 0, 0)
    doc.set_font("DJ", "", 8.5)
    doc.set_text_color(*NOIR)
    doc.multi_cell(0, 4.6, contenu.strip() or " ")
    doc.ln(0.8)


def puce(texte):
    doc.set_x(doc.l_margin)
    doc.set_font("DJ", "", 8.5)
    doc.set_text_color(*NOIR)
    x = doc.get_x()
    doc.cell(4, 4.4, "", 0, 0)
    doc.set_x(x + 4)
    doc.multi_cell(0, 4.4, texte)


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


def titre_fiche(t):
    """UNE ligne physique, sans numéro, sans préfixe : c'est cette ligne que la découpe cherche."""
    doc.set_x(doc.l_margin)
    doc.ln(3)
    if doc.get_y() > 250:
        doc.add_page()
    doc.set_text_color(*BLEU)
    # Le titre tient sur UNE ligne physique, quoi qu'il arrive : c'est ce que la découpe exige
    # (elle a interdiction d'assembler un titre à partir de deux lignes voisines). Un titre trop
    # long rétrécit plutôt que de se couper.
    taille = 11.5
    dispo = doc.w - doc.l_margin - doc.r_margin
    doc.set_font("DJ", "B", taille)
    while doc.get_string_width(t) > dispo and taille > 7.5:
        taille -= 0.25
        doc.set_font("DJ", "B", taille)
    doc.multi_cell(0, 6, t)
    doc.set_draw_color(*FILET)
    doc.line(15, doc.get_y() + 0.5, 195, doc.get_y() + 0.5)
    doc.ln(2.5)


def rendre_fiche(titre, corps):
    titre_fiche(titre)
    for l in corps:
        s = l.strip()
        depart = next((e for e in ETIQUETTES if s.startswith(e + " :")), None)
        if depart:
            rubrique(depart, s[len(depart) + 2:])
        elif s.startswith("— "):
            puce(s)
        else:                      # sous-titre de tranche d'âge (« Bébés », « 1-3 ans »)
            doc.set_x(doc.l_margin)
            doc.set_font("DJ", "B", 8.5)
            doc.set_text_color(*BLEU)
            doc.multi_cell(0, 4.4, "  " + s)


ici = os.path.dirname(os.path.abspath(__file__))
sections = decouper(os.path.join(ici, "HAB-CORRIGE.md"))
est_fiche = [bool(c) and c[0].strip().startswith("Forme :") for _, c in sections]

# ─────────────────────────────────────────────── page de titre : la première section
doc.add_page()
doc.ln(38)
titre_doc, corps_doc = sections[0]
doc.set_font("DJ", "B", 27)
doc.set_text_color(*BLEU)
doc.set_x(15)
doc.multi_cell(0, 13, titre_doc.split(" — ")[0], 0, "C")
doc.set_font("DJ", "", 12)
doc.set_text_color(*GRIS)
for l in corps_doc:
    doc.set_x(15)
    doc.multi_cell(0, 6.5, l.strip(), 0, "C")
doc.ln(14)

doc.section = "Préambule"
for (titre, corps), fiche in list(zip(sections, est_fiche))[1:]:
    if fiche:
        doc.section = "Fiches"
        rendre_fiche(titre, corps)
        continue
    # Une section en capitales est un encadré ; les autres sont des titres courants.
    if titre.upper() == titre and len(titre) > 4:
        encadre(titre, [l.strip() for l in corps])
    elif not corps:                                    # intertitre seul : ouvre une page
        doc.add_page()
        doc.section = titre.capitalize() if titre.isupper() else titre
        bloc(titre, taille=15, gras=True, couleur=BLEU, hauteur=8)
        doc.ln(2)
    else:
        if doc.get_y() > 245:
            doc.add_page()
        bloc(titre, taille=10, gras=True, couleur=BLEU, hauteur=5.5)
        for l in corps:
            s = l.strip()
            depart = next((e for e in ETIQUETTES if s.startswith(e + " :")), None)
            if depart:
                rubrique(depart, s[len(depart) + 2:])
            elif s.startswith("— "):
                puce(s)
            else:
                bloc(s)
        doc.ln(3)

sortie = os.path.join(ici, "REFERENTIEL-EVEIL-0-3-aSchool-HAB-corrige.pdf")
doc.output(sortie)
print(f"{sortie} — {doc.page_no()} pages, {sum(est_fiche)} fiches, "
      f"{len(sections) - sum(est_fiche)} sections")
