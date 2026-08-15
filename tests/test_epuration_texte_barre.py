r"""Preuve — le TEXTE BARRÉ ne sort plus de l'extraction.

Un programme officiel publié en version comparative (le cycle 4 de 2020, celui du collège)
garde ses passages SUPPRIMÉS, barrés d'un trait : l'œil les saute, l'extraction les recopiait
au milieu du texte en vigueur, et l'IA les lisait comme du programme à enseigner.

Ce que ces tests PROUVENT — la règle reconnaît la barre à sa GÉOMÉTRIE, jamais à sa couleur :
  1. un trait fin au MILIEU des lettres → les lettres partent ;
  2. le même trait posé SOUS les lettres (soulignement, celui des AJOUTS du même document)
     → rien ne part ;
  3. un trait entre deux lignes (bordure de tableau) → rien ne part ;
  4. un trait qui ne couvre qu'UN caractère → rien ne part : c'est le caractère lui-même
     (Word trace certaines puces de liste deux fois, le glyphe et un rectangle par-dessus) ;
  5. de bout en bout, sur un vrai PDF : la ligne barrée est absente du texte extrait, sa
     voisine intacte est là.

Ni IA, ni base, ni réseau : géométrie pure.

Lancer : docker compose exec backend python -m pytest tests/test_epuration_texte_barre.py -q
"""
from fpdf import FPDF

from backend.rag.extraction import REGLES_EPURATION, _cles_texte_barre, extraire_texte


def _lettres(texte: str, *, top: float = 100.0, hauteur: float = 11.0,
             x0: float = 70.0, largeur: float = 6.0) -> list[dict]:
    """Une ligne de caractères posés côte à côte, comme pdfplumber les rend."""
    return [{"text": c, "x0": x0 + i * largeur, "x1": x0 + (i + 1) * largeur,
             "top": top, "bottom": top + hauteur}
            for i, c in enumerate(texte)]


def _trait(x0: float, x1: float, top: float, epaisseur: float = 0.6) -> dict:
    return {"x0": x0, "x1": x1, "top": top, "bottom": top + epaisseur}


def test_barre_au_milieu_les_lettres_partent():
    chars = _lettres("supprime")
    # 100 + 11/2 = 105,5 : la barre passe sur le centre des lettres.
    cles = _cles_texte_barre(chars, [_trait(70.0, 118.0, 105.2)])
    assert len(cles) == len(chars)
    assert {c[2] for c in cles} == set("suprime")


def test_soulignement_sous_les_lettres_rien_ne_part():
    """Le trait des AJOUTS passe SOUS le texte : mesuré à 4,8 points du centre, quand la barre
    de suppression est à 0,6. C'est cet écart, et lui seul, qui les sépare."""
    chars = _lettres("ajoute")
    assert _cles_texte_barre(chars, [_trait(70.0, 106.0, 110.3)]) == set()


def test_bordure_de_tableau_rien_ne_part():
    chars = _lettres("cellule")
    assert _cles_texte_barre(chars, [_trait(60.0, 300.0, 120.0)]) == set()


def test_trait_sur_un_seul_caractere_rien_ne_part():
    """La puce « - » d'une liste, tracée deux fois par Word : le glyphe et un rectangle dessus.
    Une barre de suppression barre des MOTS — un trait qui ne couvre qu'une lettre n'en est pas une."""
    chars = _lettres("- puce", largeur=6.0)
    puce = chars[0]
    assert _cles_texte_barre(chars, [_trait(puce["x0"], puce["x1"], 105.2)]) == set()


def test_aplat_de_couleur_n_est_pas_un_trait():
    """Un surlignage recouvre la ligne entière : trop épais pour être une barre."""
    chars = _lettres("surligne")
    assert _cles_texte_barre(chars, [_trait(70.0, 118.0, 100.0, epaisseur=11.0)]) == set()


def test_de_bout_en_bout_la_ligne_barree_ne_sort_pas(tmp_path):
    """Le vrai chemin : un PDF où une ligne est barrée, lu par la porte unique."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, "Cette phrase est en vigueur.", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "S", 12)          # S = barré
    pdf.cell(0, 10, "Cette phrase a ete supprimee.", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, "Celle-ci revient au programme.", new_x="LMARGIN", new_y="NEXT")
    chemin = tmp_path / "comparatif.pdf"
    chemin.write_bytes(bytes(pdf.output()))

    texte = extraire_texte(chemin)
    assert "Cette phrase est en vigueur." in texte
    assert "Celle-ci revient au programme." in texte
    assert "supprimee" not in texte


def test_la_regle_est_annoncee_a_l_admin():
    """L'écran des règles d'épuration est alimenté par ce registre : une règle qui agit sans y
    figurer serait un traitement invisible."""
    assert any(r["nom"] == "Texte barré" for r in REGLES_EPURATION)
