# -*- coding: utf-8 -*-
"""le gabarit des types nomme {sous_type} : la precision du prof entre enfin dans le prompt

CE QUI NE MARCHAIT PAS. Le prof choisit un type d'activite, puis une PRECISION dans la liste
deroulante de l'ecran (Parametres.jsx). Ce choix partait bien au serveur, qui le posait dans
`kwargs["sous_type"]` (activites.py). Et la, plus rien : AUCUN des 100 prompts de
`types_activite` ne nommait {sous_type}, si bien que `modele.format(...)` le laissait tomber
sans un mot. Le prof designait « synthese de documents », l'IA fabriquait une epreuve ecrite
quelconque. Aucune erreur, aucun journal, rien : la plus silencieuse des pannes.

CE QUE FAIT CETTE MIGRATION, EN DEUX TEMPS.
1. Le GABARIT (`settings.prompt_gabarit_type`) nomme desormais {sous_type}. Il ne sert qu'aux
   types crees ENSUITE : `_generer_prompt_type` copie le gabarit au moment ou le type nait, et
   ne repasse jamais sur un prompt deja pose (c'est ecrit dans sa docstring). D'ou le temps 2.
2. Les prompts DEJA POSES sont reposes depuis le nouveau gabarit — mais UNIQUEMENT ceux qui en
   sortent encore, reconnus a leur premiere ligne. Un prompt reecrit a la main par l'admin ne
   commence pas par « Tu es un enseignant experimente. » et garde sa redaction : on ne detruit
   pas un texte que quelqu'un a pris la peine d'ecrire pour corriger un defaut d'usine.
   Au 15/08/2026 : 91 prompts reposes, 9 laisses intacts (referentiel bmg_0_3).

POURQUOI LA PRECISION N'EST PAS DEVENUE OBLIGATOIRE. {sous_type} appartient a `_USER_PARAMS` :
un repere que le prof remplit, et dont l'absence vaut 400 « Indiquez... ». Ici ce 400 serait
sans issue — un type qui n'a aucune precision n'affiche meme pas le selecteur. `api_generate`
fournit donc TOUJOURS `sous_type`, quitte a le laisser vide, et le gabarit dit a l'IA quoi
faire d'une ligne blanche. Voir le commentaire pose au meme moment dans activites.py.

Le TEXTE est FIGE ici, jamais importe de `llm_prompts` : une migration seme ce qu'elle disait
le jour ou elle a ete ecrite, pas le texte du jour ou on la rejoue (tests/test_prompts_en_base.py).
`PROMPTS_MAJ` est lu par ce test, qui compose seed + mises a jour pour verifier que le registre
et une base neuve disent la meme chose.

downgrade : remet le gabarit d'avant (fige lui aussi) et repose les prompts qui portent la
ligne de precision — le chemin exact du retour, sans toucher davantage aux prompts a la main.

Revision ID: f4c9e2b7a5d3
Revises: a3f7d2c8e5b1
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4c9e2b7a5d3"
down_revision: Union[str, Sequence[str], None] = "a3f7d2c8e5b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Texte FIGE du gabarit APRES l'ajout de la precision (cle du registre -> texte).
PROMPTS_MAJ = {
    "gabarit_type": """Tu es un enseignant expérimenté.
Conçois une activité du type « {label} » adaptée à des élèves de {niveau}.

Précision demandée par le professeur — quand elle est là, elle resserre le type et prime sur lui ;
quand la ligne est vide, aucune précision n'a été choisie et le type suffit :
{sous_type}

Pars de l'idée du professeur ci-dessous — garde son intention et son style, c'est elle qui mène :
{texte}

Appuie-toi sur le programme officiel ci-dessous pour cadrer et enrichir l'activité, sans t'en écarter :
{referentiel}

Rends une activité claire et directement exploitable (objectif, consigne, déroulé).""",
}

# Texte FIGE d'AVANT (pour le downgrade) — celui que portait la base jusqu'au 15/08/2026.
_AVANT = {
    "gabarit_type": """Tu es un enseignant expérimenté.
Conçois une activité du type « {label} » adaptée à des élèves de {niveau}.

Pars de l'idée du professeur ci-dessous — garde son intention et son style, c'est elle qui mène :
{texte}

Appuie-toi sur le programme officiel ci-dessous pour cadrer et enrichir l'activité, sans t'en écarter :
{referentiel}

Rends une activité claire et directement exploitable (objectif, consigne, déroulé).""",
}

_SQL_SETTING = sa.text(
    "INSERT INTO settings (key, value) VALUES (:key, :value) "
    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
)

# Repose le prompt de chaque type SUR LE GABARIT DONNE, en remplissant {label} et {niveau}
# exactement comme le fait `_generer_prompt_type`. Le WHERE est le garde-fou : seuls les prompts
# qui commencent encore par la premiere ligne du gabarit sont touches.
_SQL_TYPES = sa.text(
    "UPDATE types_activite t "
    "   SET prompt = replace(replace(:gabarit, '{label}', t.label), '{niveau}', n.nom) "
    "  FROM referentiels r, niveaux n "
    " WHERE r.id = t.referentiel_id AND n.id = r.niveau_id "
    "   AND t.prompt LIKE :debut"
)


def _appliquer(textes: dict) -> None:
    conn = op.get_bind()
    gabarit = textes["gabarit_type"]
    conn.execute(_SQL_SETTING, {"key": "prompt_gabarit_type", "value": gabarit})
    conn.execute(_SQL_TYPES, {"gabarit": gabarit,
                              "debut": gabarit.split("\n")[0] + "%"})


def upgrade() -> None:
    _appliquer(PROMPTS_MAJ)


def downgrade() -> None:
    _appliquer(_AVANT)
