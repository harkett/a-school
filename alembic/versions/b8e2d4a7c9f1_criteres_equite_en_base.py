# -*- coding: utf-8 -*-
"""Criteres d'equite EN BASE (catalogue), pour l'ecran « Equite d'une evaluation »

Meme moule que `ambiguite_criteres` (revision c7a3f1d95b28) : l'ecran dessine ses cases avec
ces lignes, le serveur valide sur elles les codes recus, le prompt recoit les `label` +
`verification` coches, et le `critere` rendu par le modele est recolle dessus. Une seule
source, jamais recopiee.

POURQUOI UNE LISTE COCHABLE ET PAS UNE NOTE D'EQUITE. Verifier l'equite d'une evaluation est
une procedure connue — la revue d'equite — et elle se fait critere par critere, avec une
grille : chaque point se valide ou se signale separement (Cnesco, recommandations du jury ;
ETS, regles de conception d'epreuves equitables ; Smarter Balanced, revue d'equite et de
sensibilite). Une note globale ne dirait a personne quoi corriger.

CE QUE LA LISTE NE CONTIENT PAS. Les biais du CORRECTEUR — effet de halo, ecart entre
correcteurs, derive de severite, effet de contraste entre copies — sont les mieux documentes
en France, mais ils demandent plusieurs copies, plusieurs correcteurs ou de la duree. Un
enonce colle seul n'en montre aucun. Ils sont traites dans l'AIDE de l'ecran, pas dans
l'analyse : promettre de les detecter serait mentir sur ce que l'outil fait.

Restent les 9 biais DU SUJET ci-dessous, tous de meme forme : quelque chose est demande EN
PLUS de la competence visee, et il n'est pas egalement disponible a tous les eleves.

`temps_insuffisant` porte sa propre condition d'application dans sa `verification` : sans
duree ecrite sur le sujet, il se tait. Un critere qui juge au doigt mouille abime la confiance
dans les huit autres.

Pas d'ecran admin : `ambiguite_criteres` n'en a pas non plus, la migration fait foi.
Pas de cle etrangere : une analyse d'equite n'est sauvegardee nulle part.

downgrade : drop de la table (le catalogue n'est reference par aucune autre).

Revision ID: b8e2d4a7c9f1
Revises: e3a9c7b1d4f6
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8e2d4a7c9f1"
down_revision: Union[str, Sequence[str], None] = "e3a9c7b1d4f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (code, label, description, verification, ordre)
#   description  = la phrase que le prof lit (case a cocher + onglet « Comment ca marche »)
#   verification = le controle envoye au modele. « Cherche les biais » le laisserait choisir
#                  ou chercher : il prendrait le plus facile a voir. Ici on lui dit quoi faire.
_CRITERES = [
    ("savoir_non_enseigne", "Savoir non enseigné",
     "Réussir demande une connaissance qui n'est pas au programme du niveau.",
     "Repère chaque connaissance et chaque savoir-faire nécessaires pour répondre. Signale ceux "
     "qui ne relèvent pas du niveau visé et que l'énoncé ne fournit pas : l'élève qui les possède "
     "les tient d'ailleurs que du cours.", 0),

    ("culture_et_milieu", "Culture et milieu",
     "L'énoncé suppose une expérience de vie que tous les élèves n'ont pas : voyages, vacances, "
     "argent, forme de la famille, loisirs.",
     "Relis chaque situation, contexte et exemple. Signale ceux qui supposent une expérience non "
     "partagée — partir en vacances, avoir sa chambre, disposer d'un budget, une famille d'une "
     "certaine forme, une pratique culturelle — car l'élève qui ne l'a pas vécue doit d'abord "
     "l'imaginer avant de répondre.", 1),

    ("stereotype", "Stéréotype",
     "Les rôles, les prénoms ou les exemples penchent toujours du même côté.",
     "Compare les rôles attribués : qui décide, qui exécute, qui répare, qui s'occupe des autres. "
     "Signale les répartitions systématiques selon le genre, l'origine ou le milieu, ainsi que les "
     "prénoms et les métiers employés toujours dans le même sens.", 2),

    ("poids_de_la_lecture", "Poids de la lecture",
     "Il faut d'abord bien lire pour montrer ce qu'on sait : la lecture prend le pas sur la "
     "compétence évaluée.",
     "Mesure ce que l'élève doit lire avant de pouvoir répondre : longueur, phrases imbriquées, "
     "vocabulaire étranger à la compétence visée, mise en page dense. Ne signale ce point que si "
     "la compétence évaluée n'est pas la lecture elle-même.", 3),

    ("materiel_suppose", "Matériel supposé",
     "Ordinateur, connexion, imprimante, calculatrice ou logiciel tenus pour acquis.",
     "Relève tout outil, support ou accès nécessaire pour faire le travail. Signale ceux que "
     "l'établissement ne fournit pas et que l'énoncé suppose disponibles à la maison.", 4),

    ("bareme_absent_ou_decale", "Barème absent ou décalé",
     "Pas de barème, ou un barème qui ne suit pas ce que l'énoncé demande.",
     "Si un barème est fourni, mets chaque point en face de ce qui est demandé : signale les "
     "tâches longues faiblement payées, les points donnés à ce qui n'est pas demandé, et les "
     "critères annoncés sans être chiffrés. Si aucun barème n'est fourni, dis-le une seule fois "
     "et n'invente aucune répartition.", 5),

    ("double_peine", "Double peine",
     "La même erreur coûte des points deux fois.",
     "Suis les questions qui réutilisent un résultat précédent et les critères qui se recouvrent "
     "(l'orthographe comptée dans deux rubriques, un même calcul évalué deux fois). Signale les "
     "endroits où une erreur unique fait perdre des points à plusieurs endroits.", 6),

    ("question_verrouillante", "Question qui verrouille",
     "Rater une question rend les suivantes impossibles.",
     "Vérifie pour chaque question si elle peut être traitée sans avoir réussi les précédentes. "
     "Signale les enchaînements où un échec initial bloque la suite, et indique à partir de "
     "quelle question le blocage court.", 7),

    ("temps_insuffisant", "Temps insuffisant",
     "La durée annoncée ne permet pas de finir : c'est la vitesse qui est évaluée, pas la "
     "compétence.",
     "N'applique ce contrôle QUE si une durée est écrite sur le sujet. Dans ce cas, estime le "
     "temps de lecture, de réflexion et de rédaction, puis signale l'écart avec la durée "
     "annoncée. Si aucune durée n'est écrite, ne dis rien : ne suppose aucun horaire.", 8),
]


def upgrade() -> None:
    op.create_table(
        "equite_criteres",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("verification", sa.Text(), nullable=False, server_default=""),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("code", name="uq_equite_criteres_code"),
    )

    conn = op.get_bind()
    ins = sa.text(
        "INSERT INTO equite_criteres (code, label, description, verification, ordre) "
        "VALUES (:code, :label, :description, :verification, :ordre) "
        "ON CONFLICT (code) DO NOTHING"
    )
    for code, label, description, verification, ordre in _CRITERES:
        conn.execute(ins, {
            "code": code, "label": label, "description": description,
            "verification": verification, "ordre": ordre,
        })


def downgrade() -> None:
    op.drop_table("equite_criteres")
