# -*- coding: utf-8 -*-
"""L'analyse d'equite : sa fonctionnalite, son prompt, sa ligne de longueur

Suite de b8e2d4a7c9f1 (catalogue `equite_criteres`). Trois lignes entrent en base, et elles
vont ensemble parce que la ROUTE arrive dans le meme lot : le prompt serait muet sans elle, la
ligne `outils_llm` serait orpheline sans elle (ce que tests/test_outils_llm_en_base.py refuse),
et l'ecran admin n'aurait aucun onglet ou ranger le texte sans la fonctionnalite.

  1. `prompt_fonctionnalites` : « Mes analyses -> Equite », a la suite des deux freres. Son
     `label` est le CHEMIN dans le menu du professeur, c'est ainsi qu'un prompt se retrouve.
  2. `settings.prompt_equite` : le texte d'analyse (PROMPTS_MAJ, la cle que
     tests/test_prompts_en_base.py relit).
  3. `outils_llm` : la longueur reglable de l'appel `get_max_tokens(db, "equite")`.

CE QUE LE PROMPT INTERDIT, et pourquoi c'est ecrit dedans plutot que laisse au bon sens du
modele : les biais du CORRECTEUR (effet de halo, ecart entre correcteurs, severite qui derive,
influence d'une copie sur la suivante). Ce sont les plus documentes de la recherche francaise,
le modele les connait par coeur, et aucun ne se voit dans un enonce colle. Sans interdiction
explicite, il en parle — et l'outil promet ce qu'il ne peut pas tenir. Ils sont traites dans
l'aide de l'ecran, avec cette raison.

TEXTE GELE, VOLONTAIREMENT RECOPIE ICI (regle de b8e5f2a1c9d7) : une migration seme dans six
mois EXACTEMENT ce qu'elle semait le jour de son ecriture, elle n'importe pas le registre.

downgrade : retire les trois lignes. Le prompt n'est retire que s'il est reste identique au
texte seme, pour ne pas effacer une correction de l'admin.

Revision ID: f4c8a2e6d9b3
Revises: b8e2d4a7c9f1
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4c8a2e6d9b3"
down_revision: Union[str, Sequence[str], None] = "b8e2d4a7c9f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FONCTIONNALITES = [
    ('analyse_equite', 'Mes analyses → Équité',
     "Le texte qui ANALYSE l'évaluation du prof et en rend les biais d'équité.", 60),
]


PROMPTS_MAJ = {
    "equite": 'Tu es un expert en évaluation scolaire et en équité des épreuves, pour l\'enseignement secondaire français (collège et lycée, 6e à Terminale).\n\nUn enseignant de {matiere}, niveau {niveau}, te soumet une évaluation.\n\nTa mission : repérer ce qui rend cette évaluation INÉQUITABLE — ce qu\'elle demande EN PLUS de la compétence visée, et qui n\'est pas également disponible à tous les élèves. Un élève ne doit pas être pénalisé pour une raison étrangère à ce que l\'évaluation veut mesurer.\n\nÉnoncé soumis :\n{texte}\n\nBarème fourni par l\'enseignant :\n{bareme}\n\nBiais à rechercher — UNIQUEMENT ceux-ci, l\'enseignant les a choisis. Traite-les UN PAR UN, dans l\'ordre, en effectuant la vérification écrite sous chacun avant de passer au suivant :\n{criteres}\n\nFormat de réponse — JSON strict, rien d\'autre autour :\n{{\n  "biais": [\n    {{\n      "extrait": "fragment exact de l\'énoncé ou du barème en cause, ou une chaîne vide si le défaut porte sur l\'ensemble",\n      "critere": "Culture et milieu",\n      "consequence": "Quels élèves sont pénalisés, et pourquoi cela n\'a rien à voir avec la compétence évaluée",\n      "correction": "Ce qu\'il faut changer, concrètement, sans baisser l\'exigence"\n    }}\n  ],\n  "verdict": "Phrase de synthèse courte sur l\'équité globale de cette évaluation."\n}}\n\nRègles :\n- Ne signaler QUE les biais listés ci-dessus. Un défaut d\'un type non demandé n\'est pas à remonter.\n- Aucun biais n\'est facultatif : effectuer la vérification de CHACUN avant de répondre, y compris ceux qui demandent de relire l\'évaluation en entier. Un biais sans défaut réel ne produit simplement aucune entrée.\n- Le champ "critere" reprend EXACTEMENT l\'un des libellés listés.\n- NE JAMAIS parler des biais du correcteur — effet de halo, écart entre deux correcteurs, sévérité qui dérive au fil du paquet, influence d\'une copie sur la suivante. Ils sont réels, mais ils ne se voient pas dans un texte : cet outil ne les traite pas.\n- Ne pas confondre exigence et inéquité : une évaluation difficile n\'est pas injuste. N\'est un biais que ce qui pénalise certains élèves pour une raison étrangère à la compétence évaluée.\n- La correction doit conserver le niveau d\'exigence : on retire l\'obstacle, on ne simplifie pas la tâche.\n- Citer des extraits textuels exacts dans le champ "extrait" (reprendre mot pour mot), ou laisser ce champ vide quand le défaut porte sur l\'ensemble de l\'évaluation.\n- Si l\'évaluation est équitable sur tous les biais demandés, retourner "biais": [] et un verdict positif.\n- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON.',
}


OUTILS = [
    ("equite", "Analyse de l'équité d'une évaluation", 55,
     "Relit l'évaluation collée par le professeur et rend les biais d'équité "
     "trouvés, une carte par biais. Sortie moyenne, plus longue quand plusieurs biais sont "
     "cochés."),
]


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
    for code, _label, _aide, _ordre in FONCTIONNALITES:
        conn.execute(sa.text("DELETE FROM prompt_fonctionnalites WHERE code = :c"), {"c": code})
