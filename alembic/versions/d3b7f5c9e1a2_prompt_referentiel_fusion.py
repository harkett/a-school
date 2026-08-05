# -*- coding: utf-8 -*-
"""seme EN BASE le prompt `referentiel_fusion` — l'IA tire UN referentiel des documents fournis.

Un couple recoit parfois plusieurs PDF (au lycee, un par matiere ; ailleurs, un programme et son
bulletin officiel). Les coller bout a bout additionne surtout les redites. Le bouton
« Fusionner » demande donc a l'IA de LIRE les documents et d'en tirer un seul referentiel, sans
doublon, borne en nombre de pages.

POURQUOI UNE MIGRATION. Les prompts vivent EN BASE (`settings`, `prompt_<cle>`) et `get_prompt`
n'a plus de repli code : sans cette ligne, le bouton tomberait sur « prompt absent en base ».

Le TEXTE est FIGE ici, jamais importe de `llm_prompts` : une migration doit semer ce qu'elle
disait le jour ou elle a ete ecrite (cf. tests/test_prompts_en_base.py, qui lit `PROMPTS_MAJ`).

Revision ID: d3b7f5c9e1a2
Revises: c7e9a1b5d2f4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3b7f5c9e1a2"
down_revision: Union[str, Sequence[str], None] = "c7e9a1b5d2f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROMPTS_MAJ = {
    "referentiel_fusion": """Tu reçois les documents officiels fournis pour un même niveau scolaire. Tu en tires UN SEUL référentiel de travail, complet et sans redite.

Couple visé :
- Cycle : {cycle}
- Niveau : {niveau}

Documents fournis :
{documents}

Ta tâche :
- Retiens ce qui vaut pour CE niveau : les matières enseignées, et pour chacune ce que l'élève doit savoir et savoir faire.
- Un même contenu revient souvent d'un document à l'autre (un programme et son bulletin officiel disent la même chose) : ne l'écris QU'UNE FOIS, dans sa formulation la plus complète.
- Quand deux documents se contredisent, garde ce qui vaut pour le niveau visé et ignore l'autre. N'explique pas ton choix dans le texte.
- Écarte ce qui n'est pas du programme : préambules administratifs, sommaires, références d'arrêtés, mentions légales, pagination, remerciements.
- N'ajoute RIEN qui ne soit pas dans les documents. Tu résumes et tu ordonnes, tu n'inventes pas.

Forme attendue :
- Une matière par section, introduite par une ligne « ## » suivie du nom de la matière tel que les documents le nomment.
- Sous chaque matière, des lignes courtes commençant par « - », une idée par ligne.
- Pas d'introduction, pas de conclusion, pas de commentaire sur ton travail : le texte du référentiel, et rien d'autre.
- {consigne_taille}

Réponds uniquement par ce texte.""",
}

_SQL = sa.text(
    "INSERT INTO settings (key, value) VALUES (:key, :value) "
    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
)


# Le plafond du referentiel PRODUIT par la fusion. En base, comme les autres plafonds
# (`depot_max_mo`, `depot_max_pages`) : l'admin doit pouvoir le changer sans toucher au code.
# Il ne remplace pas `depot_max_pages` — celui-la borne un document DEPOSE, celui-ci le resultat.
#
# `max_tokens_referentiel_fusion` VA AVEC, et les deux doivent s'accorder : la consigne envoyee au
# modele prend la PLUS PETITE des deux bornes (pages voulues / jetons disponibles). Sans surcharge,
# on retombait sur `max_tokens_default` = 8000 jetons, soit ~28 000 signes ≈ 10 pages : le plafond
# de 15 pages etait alors inatteignable, et le reglage mentait. 12000 jetons ≈ 42 000 signes, de
# quoi ecrire les 15 pages annoncees.
REGLAGES = {"fusion_max_pages": "15", "max_tokens_referentiel_fusion": "12000"}


def upgrade() -> None:
    conn = op.get_bind()
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(_SQL, {"key": f"prompt_{cle}", "value": texte})
    for cle, valeur in REGLAGES.items():
        conn.execute(_SQL, {"key": cle, "value": valeur})


def downgrade() -> None:
    conn = op.get_bind()
    for cle in list(PROMPTS_MAJ):
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {"key": f"prompt_{cle}"})
    for cle in REGLAGES:
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {"key": cle})
