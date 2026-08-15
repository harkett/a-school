r"""Preuve du RELEVÉ DES TARIFS — lire la grille du fournisseur sans se tromper de ligne.

CE QUE LA FONCTIONNALITÉ FAIT. L'administrateur saisissait les prix à la main, modèle par modèle,
en gardant la page du fournisseur ouverte dans un autre onglet. Le bouton « Relever les tarifs »
va lire cette page et remplit le prix d'entrée et de sortie de chaque modèle qu'il y retrouve.

CE QU'ELLE N'APPELLE PAS : aucune IA, aucune clé, aucun euro. Une grille tarifaire est un tableau ;
une expression régulière le lit, et ne peut pas inventer un chiffre.

CE QUE CES TESTS PROTÈGENT, dans l'ordre du danger :
  1. LA CONFUSION DE MODÈLES — « qwen3 » ne doit pas se reconnaître dans « Qwen/Qwen3.5-122B » :
     ce sont deux modèles, à deux prix (0,40 contre 3,20 en sortie). C'est la seule erreur qui
     écrirait un tarif FAUX sans que rien ne le signale ;
  2. le format réel d'une page — après réduction du HTML, une cellule devient « CHF | 0.30 » :
     exiger un simple espace entre la devise et le montant ne trouvait rien ;
  3. le silence prudent — nom absent, un seul montant : on n'écrit pas, on signale.

Aucun accès réseau : les tests travaillent sur des pages écrites ici. La vraie page d'Infomaniak
a servi à écrire le module, pas à le tester — une suite qui dépend d'un site tiers échoue le jour
où il change de mise en page, pour une raison qui n'est pas la nôtre.

Lancer : docker compose exec backend python -m pytest tests/test_releve_tarifs.py -q
"""
from backend.systeme.releve_tarifs import _texte, relever

# Le format d'Infomaniak, réduit comme le fait `_texte` : nom, puis « Token entrant / sortant ».
PAGE_INFOMANIAK = _texte(
    "<div><p>Qwen/Qwen3.5-122B-A10B-FP8</p>"
    "<span>Token entrant :</span><span>CHF</span><span>0.40</span><span>/ 1M tokens</span>"
    "<span>Token sortant :</span><span>CHF</span><span>3.20</span><span>/ 1M tokens</span></div>"
    "<div><p>mistralai/Ministral-3-14B-Instruct-2512</p>"
    "<span>Token entrant :</span><span>CHF</span><span>0.30</span><span>/ 1M tokens</span>"
    "<span>Token sortant :</span><span>CHF</span><span>0.40</span><span>/ 1M tokens</span></div>"
)


def test_le_nom_public_ramene_le_bon_couple_de_prix():
    """Le cas nominal : le nom de la grille, ses deux montants, sa devise."""
    r = relever(PAGE_INFOMANIAK, ["mistralai/Ministral-3-14B-Instruct-2512"])
    assert r == {"mistralai/Ministral-3-14B-Instruct-2512":
                 {"entree": 0.30, "sortie": 0.40, "devise": "CHF"}}


def test_un_nom_court_ne_vole_pas_le_tarif_d_un_modele_plus_recent():
    """LE TEST QUI COMPTE. « qwen3 » est contenu dans « Qwen/Qwen3.5-122B-A10B-FP8 », et une
    recherche naïve lui donnait 0,40 / 3,20 — le tarif d'un autre modèle, huit fois plus cher en
    sortie. Rien à l'écran n'aurait dit que le chiffre venait de la mauvaise ligne."""
    assert relever(PAGE_INFOMANIAK, ["qwen3"]) == {}


def test_la_devise_est_lue_sur_la_page_pas_supposee():
    """Infomaniak facture en francs suisses, les autres en dollars. Supposer USD ferait afficher
    un prix faux de 15 % après conversion — et c'est ce prix-là qui classe la liste."""
    page = _texte("<p>modele-x</p><span>$</span><span>3</span><span>$</span><span>15</span>")
    assert relever(page, ["modele-x"])["modele-x"]["devise"] == "USD"


def test_un_seul_montant_ne_donne_rien():
    """Un prix d'entrée sans prix de sortie n'est pas un demi-relevé : c'est une page qu'on n'a pas
    comprise. On préfère « non relevé » à un tarif à moitié faux."""
    page = _texte("<p>modele-y</p><span>CHF</span><span>0.30</span><p>autre-chose</p>")
    assert relever(page, ["modele-y"]) == {}


def test_un_nom_absent_de_la_page_est_simplement_absent():
    """Le modèle est laissé tel quel : le relevé ne remet jamais un tarif à zéro."""
    assert relever(PAGE_INFOMANIAK, ["mistral24b"]) == {}


def test_le_separateur_de_cellules_ne_colle_pas_les_nombres():
    """« <td>0.30</td><td>0.40</td> » réduit sans séparateur donnerait « 0.300.40 » — un montant
    inventé de toutes pièces. `_texte` pose un « | » entre les balises."""
    t = _texte("<td>0.30</td><td>0.40</td>")
    assert "0.300.40" not in t
