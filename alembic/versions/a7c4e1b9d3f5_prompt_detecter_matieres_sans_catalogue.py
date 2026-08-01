# -*- coding: utf-8 -*-
"""met a jour EN BASE le prompt `detecter_matieres` : plus de catalogue commun

LOT 3 du chantier Matiere. Le prompt de detection recevait la table des matieres de
l'application ({matieres_existantes}) pour ramener le document a un vocabulaire commun. Ce
catalogue n'existe plus : chaque referentiel possede SES matieres, nommees comme le document
les nomme. Le prompt ne recoit donc plus que {texte}.

POURQUOI UNE MIGRATION, ET PAS SEULEMENT LE REGISTRE. Le prompt VIT EN BASE (settings,
`prompt_detecter_matieres`, seme par b8e5f2a1c9d7) et `get_prompt` n'a plus de repli code :
c'est la ligne en base que le serveur envoie a l'IA. Sans cette mise a jour, la base garderait
l'ancien texte, avec un {matieres_existantes} que plus personne ne remplit — l'IA recevrait
donc ce repere en clair au milieu de sa consigne.

ECRASEMENT ASSUME : la ligne est reecrite quelle que soit sa valeur, y compris si l'admin
l'avait retouchee. Tout texte qui porte encore {matieres_existantes} est casse (repere
orphelin), et le garde-fou d'ecriture (`valider_prompt`) refuserait desormais de l'enregistrer.

Le TEXTE est FIGE ici, jamais importe de `llm_prompts` : une migration doit semer ce qu'elle
disait le jour ou elle a ete ecrite, pas le texte du jour ou on la rejoue (cf.
tests/test_prompts_en_base.py). `PROMPTS_MAJ` est lu par ce test, qui compose seed + mises a
jour pour verifier que le registre et une base neuve disent la meme chose.

downgrade : remet le texte d'origine, avec son {matieres_existantes} (fige lui aussi).

Revision ID: a7c4e1b9d3f5
Revises: f8b3d5c7a1e9
Create Date: 2026-08-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7c4e1b9d3f5"
down_revision: Union[str, Sequence[str], None] = "f8b3d5c7a1e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Texte FIGE du prompt apres le chantier Matiere (cle du registre -> texte).
PROMPTS_MAJ = {
    "detecter_matieres": """Tu lis un référentiel officiel et tu en dégages la liste des MATIÈRES (disciplines, domaines d'apprentissage) qu'il structure à ce niveau.

Texte du référentiel :
{texte}

Ta tâche :
- Repère les matières, disciplines ou domaines d'apprentissage que ce référentiel organise (ses grands champs).
- Donne le nom de chaque matière TEL QU'IL APPARAÎT DANS LE DOCUMENT : son orthographe, ses majuscules, ses accents. Ce document nomme SES matières ; il n'y a aucune liste extérieure à laquelle les ramener, et aucun nom à normaliser.
- Garde des noms courts et lisibles : le nom de la matière, pas une phrase ni un intitulé de chapitre.
- Ne sépare jamais un intitulé qui désigne UNE seule discipline, même si son nom est composé (par exemple « Prévention-santé-environnement » ou « Éducation physique et sportive » restent entières).
- Sépare en revanche un intitulé qui en énumère visiblement plusieurs (par exemple « Mathématiques et physique-chimie » donne deux matières), en gardant pour chacune le nom que le document lui donne.

Règle :
- "matieres" : la liste des noms de matières, sans doublon.
- N'invente aucune matière absente du document. Si aucune n'apparaît clairement, renvoie une liste vide.

Réponds UNIQUEMENT en JSON, avec exactement cette clé : matieres (un tableau de chaînes).""",
}

# Texte FIGE d'AVANT (pour le downgrade) — celui seme par b8e5f2a1c9d7.
_AVANT = {
    "detecter_matieres": """Tu lis un référentiel officiel et tu en dégages la liste des MATIÈRES (disciplines, domaines d'apprentissage) qu'il structure à ce niveau.

Matières déjà connues de l'application :
{matieres_existantes}

Texte du référentiel :
{texte}

Ta tâche :
- Repère les matières, disciplines ou domaines d'apprentissage que ce référentiel organise (ses grands champs).
- Fais CORRESPONDRE ce que tu lis avec les matières déjà connues :
  - Si un intitulé du document correspond à une matière déjà connue, reprends EXACTEMENT le nom de la liste (même orthographe, mêmes majuscules), pas celui du document.
  - Si un intitulé du document REGROUPE plusieurs matières déjà connues (par exemple « Mathématiques et physique-chimie »), sépare-le : donne chacune de ces matières comme une entrée à part, avec le nom exact de la liste.
  - Si un intitulé du document ne correspond à aucune matière connue, donne son nom tel qu'il apparaît dans le document, court et lisible (le nom de la matière, pas une phrase).
- Ne sépare jamais un intitulé qui désigne UNE seule discipline, même si son nom est composé (par exemple « Prévention-santé-environnement » ou « Éducation physique et sportive » restent entières).

Règle :
- "matieres" : la liste des noms de matières, sans doublon.
- N'invente aucune matière absente du document : la liste des matières connues sert à faire correspondre et à séparer, jamais à ajouter une matière que le document ne couvre pas. Si aucune n'apparaît clairement, renvoie une liste vide.

Réponds UNIQUEMENT en JSON, avec exactement cette clé : matieres (un tableau de chaînes).""",
}

_SQL = sa.text(
    "INSERT INTO settings (key, value) VALUES (:key, :value) "
    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
)


def _ecrire(textes: dict) -> None:
    conn = op.get_bind()
    for cle, texte in textes.items():
        conn.execute(_SQL, {"key": f"prompt_{cle}", "value": texte})


def upgrade() -> None:
    _ecrire(PROMPTS_MAJ)


def downgrade() -> None:
    _ecrire(_AVANT)
