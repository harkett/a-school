# -*- coding: utf-8 -*-
"""Le prompt qui ÉCRIT la grille d'évaluation, et sa longueur réglable

DEUX LIGNES ENTRENT EN BASE :

  1. `prompt_fonctionnalites` — l'onglet sous lequel l'administrateur trouvera ce texte. Le
     libellé est le CHEMIN DANS LE MENU DU PROFESSEUR (« Mes évals → Grilles ») : c'est ainsi
     qu'on retrouve un prompt quand on vient de voir le bouton qui le déclenche.
  2. `settings.prompt_grille_generation` — le texte lui-même. Depuis que `get_prompt` n'a plus
     de repli sur le code, une clé absente fait tomber l'outil : cette ligne n'est pas un
     confort, c'est ce qui rend la fonctionnalité utilisable.

IL MANQUE VOLONTAIREMENT LA TROISIÈME, celle d'`outils_llm`. Elle viendra avec la route qui
appelle `get_max_tokens(db, "grille_generation")`, et pas avant : une ligne posée aujourd'hui
proposerait à l'administrateur de régler la longueur d'un appel qui n'existe pas encore.
`tests/test_outils_llm_en_base.py::test_aucune_ligne_orpheline` refuse ce réglage fantôme — c'est
lui qui a fait tomber la première version de cette migration. Même ordre que pour les consignes,
où le prompt est arrivé par `c5e1a9d7b3f4` et sa ligne d'outil seulement par `d1f5b8c3e7a2`.

CE PROMPT REND DU JSON, ET C'EST TOUT LE SUJET. Une grille est un TABLEAU : des critères en
lignes, des niveaux de maîtrise en colonnes, un descripteur dans chaque case. Rendue en markdown,
elle serait belle à l'écran et illisible pour le programme — il faudrait la relire au parseur pour
en ressortir quoi que ce soit. Elle arrive donc en données, et se range dans les quatre tables
posées par `c9e4b7f2a1d6`.

CE QUE LE TEXTE IMPOSE AU MODÈLE, et pourquoi. Un descripteur doit décrire un COMPORTEMENT
OBSERVABLE (« cite trois sources et les met en relation »), jamais un jugement (« bon travail ») :
c'est la seule différence entre une grille et une échelle d'appréciation, et c'est ce qu'un modèle
laissé libre écrit spontanément de travers. Quatre à six critères, pas davantage : personne ne
coche douze lignes par copie. L'échelle par défaut est celle du socle commun — l'enseignant en
impose une autre s'il le veut, le prompt le prévoit.

TEXTE GELÉ, VOLONTAIREMENT RECOPIÉ ICI (règle de b8e5f2a1c9d7) : une migration dit ce qui est
entré en base LE JOUR où elle a tourné. Elle ne va pas le relire dans un fichier qui aura changé.

downgrade : retire les deux lignes. Le prompt n'est retiré que s'il est resté identique au texte
semé, pour ne pas effacer une correction de l'administrateur.

Revision ID: d2a8f6c4b1e7
Revises: c9e4b7f2a1d6
Create Date: 2026-08-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2a8f6c4b1e7"
down_revision: Union[str, Sequence[str], None] = "c9e4b7f2a1d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FONCTIONNALITES = [
    ("grilles", "Mes évals → Grilles",
     "Le texte qui ÉCRIT la grille d'évaluation du professeur : ses critères, ses niveaux de "
     "maîtrise et le descripteur de chaque case.", 70),
]


PROMPTS_MAJ = {
    "grille_generation": 'Tu écris une GRILLE D\'ÉVALUATION CRITÉRIÉE pour un enseignant de {matiere}, niveau {niveau}.\n\nCe que l\'enseignant veut évaluer, dans ses mots :\n{texte}\n\nLes EXTRAITS DU RÉFÉRENTIEL OFFICIEL ci-dessous disent ce que cette matière recouvre réellement à ce niveau. Ils te sont donnés pour que tu n\'aies pas à l\'interpréter : un intitulé court comme « Langage » ou « Le besoin » ne veut rien dire hors de sa formation.\n\n{referentiel}\n\nUNE GRILLE CRITÉRIÉE EST UN TABLEAU. En lignes, les critères — ce que l\'élève doit démontrer. En colonnes, les niveaux de maîtrise, la MÊME échelle pour tous les critères. Dans chaque case, le descripteur : ce que l\'élève doit AVOIR FAIT pour obtenir ce niveau sur ce critère.\n\nRègles de rédaction — ce sont elles qui font qu\'une grille sert à quelque chose :\n- Un descripteur décrit un COMPORTEMENT OBSERVABLE dans le travail rendu, jamais un jugement. « Cite trois sources et les met en relation » se constate ; « Bon travail de recherche » ne se constate pas.\n- Ce qui varie d\'une colonne à l\'autre est le DEGRÉ DE RÉUSSITE, jamais le sujet : les descripteurs d\'un même critère parlent tous de la même chose, à des degrés différents.\n- Ne fais pas varier la quantité seule (« une source », « deux sources »…) quand c\'est la qualité qui est évaluée : compter n\'est pas évaluer.\n- Aucun descripteur n\'est vide, y compris le plus bas. « N\'a pas rendu » n\'est pas un descripteur ; dire ce qui EST fait, même insuffisant, en est un.\n- Pas de négation seule (« ne sait pas… ») : décris ce qui est présent dans le travail.\n- Emploie le vocabulaire de la matière et du niveau, celui des extraits ci-dessus. L\'élève doit pouvoir lire sa grille et comprendre ce qu\'on attend de lui.\n- QUATRE À SIX CRITÈRES. Au-delà, la grille cesse d\'être utilisable : personne ne coche douze lignes par copie.\n- L\'échelle par défaut est celle du socle : « Maîtrise insuffisante », « Maîtrise fragile », « Maîtrise satisfaisante », « Très bonne maîtrise ». Suis l\'échelle demandée par l\'enseignant s\'il en indique une autre.\n- Les points croissent avec le niveau de maîtrise. Le poids d\'un critère dit son importance relative dans la note (1 = ordinaire).\n\nFormat de réponse — JSON strict, rien d\'autre autour :\n{{\n  "titre": "Ce que la grille évalue, en quelques mots",\n  "niveaux_maitrise": [\n    {{"libelle": "Maîtrise insuffisante", "points": 0}}\n  ],\n  "criteres": [\n    {{\n      "libelle": "Ce que l\'élève doit démontrer, en une phrase",\n      "poids": 1,\n      "descripteurs": {{\n        "Maîtrise insuffisante": "Ce que l\'élève doit avoir fait pour obtenir ce niveau sur ce critère"\n      }}\n    }}\n  ]\n}}\n\nRègles de format :\n- "niveaux_maitrise" est ordonné de la moins bonne maîtrise à la meilleure.\n- Les clés de "descripteurs" reprennent EXACTEMENT les "libelle" de "niveaux_maitrise" — TOUS, pour CHAQUE critère, sans en omettre un seul. Une case manquante est une case que le professeur devra écrire lui-même.\n- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON.',
}


def upgrade() -> None:
    conn = op.get_bind()
    for code, label, aide, ordre in FONCTIONNALITES:
        conn.execute(sa.text(
            "INSERT INTO prompt_fonctionnalites (code, label, aide, ordre, actif) "
            "VALUES (:code, :label, :aide, :ordre, true) ON CONFLICT (code) DO NOTHING"
        ), {"code": code, "label": label, "aide": aide, "ordre": ordre})

    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(sa.text(
            "INSERT INTO settings (key, value) VALUES (:key, :value) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
        ), {"key": f"prompt_{cle}", "value": texte})


def downgrade() -> None:
    conn = op.get_bind()
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key AND value = :value"),
                     {"key": f"prompt_{cle}", "value": texte})
    for code, _label, _aide, _ordre in FONCTIONNALITES:
        conn.execute(sa.text("DELETE FROM prompt_fonctionnalites WHERE code = :c"), {"c": code})
