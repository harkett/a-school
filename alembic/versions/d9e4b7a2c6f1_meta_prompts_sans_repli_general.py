# -*- coding: utf-8 -*-
"""Les quatre méta-prompts perdent leur repli général : ils vivent sur le référentiel, ou nulle part.

CONSTAT. Chacun des quatre méta-prompts — matières, découpe, types d'activité, précisions — se
lisait à deux endroits, dans cet ordre : la colonne du référentiel, puis, si elle était vide, une
ligne partagée de `settings`. Ce repli est un vestige de l'époque où un seul texte servait tous les
diplômes ; la bascule qui a donné à chaque référentiel ses propres prompts l'a laissé derrière elle.

POURQUOI IL DOIT PARTIR. Un méta-prompt lit un document pour écrire le prompt qui le lira ensuite.
Le gabarit général a été écrit devant des référentiels de diplôme : il cherche une grille
d'horaires, des unités d'enseignement, des options. Appliqué à un programme de crèche, il ne rend
pas un prompt approximatif — il en rend un FAUX, qui ira chercher ce qui n'existe pas et rendra une
liste inventée. Le repli n'évitait pas une panne : il en fabriquait une silencieuse, et payante.

ET IL NE SERVAIT JAMAIS. C'est l'administrateur qui crée un référentiel. Un référentiel sans
prompts n'est de toute façon pas utilisable : il n'a ni matières, ni découpe, ni types. Le cas que
le repli prétendait couvrir — « générer quand même » — est un cas qu'on ne veut pas.

CE QUE FAIT CETTE MIGRATION. Elle retire les quatre lignes de `settings`. Le code ne les lit plus
(`rag/analyse_amont`, quatre générateurs) et les quatre portes de lecture ne les proposent plus
(`pedagogie/referentiels_admin`) : les laisser en base serait garder un texte que rien n'atteint.

CE QU'ELLE NE TOUCHE PAS. `prompt_verif_decoupe` reste. Ce méta-prompt-là ne lit aucun document :
il fait relire à l'IA le prompt qu'elle vient d'écrire, pour vérifier qu'il respecte le contrat de
sortie. Générique par nature, il n'a pas d'équivalent par référentiel — et il est bien appelé, par
`generer_prompt_decoupe`.

LES COLONNES DES RÉFÉRENTIELS NE BOUGENT PAS. Les trois BTS portent déjà leur copie du texte
général, figée lors de la bascule ; elle devient simplement leur seule source. Un référentiel dont
une case est vide ne pourra plus générer le prompt correspondant — c'est le but : il lèvera avec un
message qui dit où écrire, au lieu de dépenser un appel pour un résultat faux.

Revision ID: d9e4b7a2c6f1
Revises: c4d8e2a7f9b1
Create Date: 2026-08-08
"""
from alembic import op
import sqlalchemy as sa


revision = "d9e4b7a2c6f1"
down_revision = "c4d8e2a7f9b1"
branch_labels = None
depends_on = None


# Les quatre clés retirées. Nommées ici et nulle part ailleurs : la liste n'existe que dans cette
# migration, comme les autres migrations porteuses de données (OUTILS, PROMPTS_MAJ, FONCTIONNALITES).
CLES_RETIREES = (
    "prompt_meta_matieres",
    "prompt_meta_decoupe",
    "prompt_meta_types",
    "prompt_meta_precisions",
)


def upgrade() -> None:
    conn = op.get_bind()
    for cle in CLES_RETIREES:
        conn.execute(sa.text("DELETE FROM settings WHERE key = :k"), {"k": cle})


def downgrade() -> None:
    """Recrée les quatre lignes, VIDES.

    Leur contenu n'est pas restituable : c'étaient des textes écrits à la main, dont la copie vit
    désormais sur les référentiels qui les ont reçus (`referentiels.prompt_meta_*`). Recréer des
    lignes vides suffit à rendre le schéma identique ; le texte, lui, se recopie d'un référentiel
    si le besoin s'en présentait."""
    conn = op.get_bind()
    for cle in CLES_RETIREES:
        deja = conn.execute(sa.text("SELECT 1 FROM settings WHERE key = :k"), {"k": cle}).scalar()
        if not deja:
            conn.execute(sa.text("INSERT INTO settings (key, value) VALUES (:k, '')"), {"k": cle})
