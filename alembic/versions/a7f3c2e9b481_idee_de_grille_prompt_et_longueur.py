# -*- coding: utf-8 -*-
"""« Propose-moi une idée » côté grilles : son prompt et sa longueur

DEUX LIGNES ENTRENT EN BASE, et cette fois elles arrivent ENSEMBLE :

  1. `settings.prompt_grille_idee` — le texte. Depuis que `get_prompt` n'a plus de repli sur le
     code, une clé absente fait tomber l'outil : cette ligne n'est pas un confort.
  2. `outils_llm.grille_idee` — le champ par lequel l'administrateur règle la longueur de la
     réponse, puisque la route appelle `get_max_tokens(db, "grille_idee")`.

Le prompt de la grille (`d2a8f6c4b1e7`) avait dû laisser sa ligne d'outil à une migration
suivante : l'appel n'existait pas encore, et `test_aucune_ligne_orpheline` refuse un réglage que
rien ne déclenche. Ici la route `POST /contenus/grilles/proposer-idee` arrive dans le même
changement, donc les deux lignes peuvent tenir dans la même migration.

`prompt_fonctionnalites` n'a RIEN à recevoir : ce prompt se range sous l'onglet « grilles », posé
par `d2a8f6c4b1e7`. Deux textes sous une même fonctionnalité, comme l'analyse et son exemple.

CE PROMPT N'ÉCRIT PAS DE GRILLE. Il rend la DEMANDE que le professeur aurait tapée lui-même —
deux ou trois phrases, posées dans la zone de « Nouvelle grille », qu'il relit et modifie avant de
cliquer « Générer la grille ». D'où sa longueur modeste : ce n'est pas la grille, c'est son point
de départ.

`{demande}` EST CE QUI LE DISTINGUE de son frère des activités. Là-bas, le type d'activité choisi
par le professeur donne l'axe de recherche ; une grille n'a pas de type. Sans le thème tapé dans
la fenêtre, les extraits arriveraient au hasard du référentiel entier et l'idée rendue serait
juste, dans le programme, et sans rapport avec ce que l'enseignant a en tête. Ce thème sert deux
fois : requête envoyée au référentiel, puis élément du prompt.

TEXTE GELÉ, VOLONTAIREMENT RECOPIÉ ICI (règle de b8e5f2a1c9d7) : une migration dit ce qui est
entré en base LE JOUR où elle a tourné. Elle ne va pas le relire dans un fichier qui aura changé.

downgrade : retire les deux lignes. Le prompt n'est retiré que s'il est resté identique au texte
semé, pour ne pas effacer une correction de l'administrateur.

Revision ID: a7f3c2e9b481
Revises: 35290b3472b1
Create Date: 2026-08-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7f3c2e9b481"
down_revision: Union[str, Sequence[str], None] = "35290b3472b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROMPTS_MAJ = {
    "grille_idee": (
        "Tu es enseignant·e pour le niveau « {niveau} », en {matiere}.\n"
        "\n"
        "Un professeur cherche une idée de production à évaluer.\n"
        "Le professeur indique le thème ou le support qu'il a en tête : « {demande} ».\n"
        "Ton idée porte sur CE thème.\n"
        "À partir des EXTRAITS du référentiel officiel ci-dessous, propose UNE idée, écrite comme "
        "la demande que le professeur taperait lui-même : 2 à 3 phrases concrètes disant ce que "
        "les élèves rendent et ce qu'on y regarde.\n"
        "\n"
        "Contraintes : reste dans le périmètre du référentiel ; ne rédige PAS la grille, ni "
        "critères, ni niveaux de maîtrise ; aucun titre, aucune liste — uniquement le texte de la "
        "demande.\n"
        "\n"
        "## Extraits du référentiel officiel — {niveau}\n"
        "\n"
        "{referentiel}\n"
        "\n"
        "## Idée à proposer\n"
    ),
}


OUTILS = [
    ("grille_idee", "Idée de grille à la demande", 71,
     "Rend la demande que le professeur aurait écrite lui-même sur le thème qu'il indique — deux "
     "ou trois phrases, pas une grille. La grille, elle, s'écrit au clic suivant et a son propre "
     "réglage : une valeur haute ici ne servirait qu'à payer des phrases que personne ne lit."),
]


def upgrade() -> None:
    conn = op.get_bind()
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(sa.text(
            "INSERT INTO settings (key, value) VALUES (:key, :value) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
        ), {"key": f"prompt_{cle}", "value": texte})

    for outil, libelle, ordre, aide in OUTILS:
        conn.execute(sa.text(
            "INSERT INTO outils_llm (outil, libelle, aide, ordre) "
            "VALUES (:outil, :libelle, :aide, :ordre) ON CONFLICT (outil) DO NOTHING"
        ), {"outil": outil, "libelle": libelle, "aide": aide, "ordre": ordre})


def downgrade() -> None:
    conn = op.get_bind()
    for outil, _libelle, _ordre, _aide in OUTILS:
        conn.execute(sa.text("DELETE FROM outils_llm WHERE outil = :o"), {"o": outil})
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key AND value = :value"),
                     {"key": f"prompt_{cle}", "value": texte})
