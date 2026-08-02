# -*- coding: utf-8 -*-
"""seme EN BASE le prompt `suggerer_precisions_type` (bouton « generer les precisions »)

Ce texte etait ECRIT EN DUR dans backend/rag/analyse_amont.py, en f-string, au milieu de la
fonction qui l'envoie au modele. C'etait le SEUL vrai prompt du projet hors du registre : l'admin
ne pouvait ni le lire, ni le corriger, ni savoir qu'il existait — alors que les trois autres
fonctions du meme fichier passaient deja par get_prompt.

POURQUOI UNE MIGRATION, ET PAS SEULEMENT LE REGISTRE. `get_prompt` n'a plus de repli sur le
texte du code (etape 9 lot C) : c'est la ligne EN BASE que le serveur envoie au modele. Ajouter
la cle au seul registre ferait tomber le bouton « generer les precisions » sur toute base
existante, avec « Prompt absent en base (migration non appliquee ?) ».

INSERT ... ON CONFLICT DO NOTHING, et non DO UPDATE : cette migration SEME une cle neuve. Si
une base la porte deja — base montee depuis le registre, reseed manuel — c'est sa valeur qui
fait foi, pas celle d'ici. Une migration de seed n'ecrase pas un texte que l'admin a pu
retoucher ; ecraser est le travail d'une migration de MISE A JOUR, qui le dit dans son nom.

Le TEXTE est FIGE ici, jamais importe de `llm_prompts` : une migration doit semer ce qu'elle
disait le jour ou elle a ete ecrite, pas le texte du jour ou on la rejoue (cf.
tests/test_prompts_en_base.py). Il est repris MOT POUR MOT de la f-string d'origine, retours a
la ligne compris ; seules les valeurs interpolees deviennent des reperes {label} {niveau} {texte}.

`PROMPTS_MAJ` est le nom que lit tests/test_prompts_en_base.py pour composer « seed + mises a
jour » et verifier qu'une base neuve et le registre disent la meme chose. Le nom parle de mise
a jour, mais le test s'en sert comme d'un cumul : une cle neuve y entre aussi.

downgrade : retire la ligne. Le code, lui, ne sait plus faire sans — un downgrade rend donc le
bouton « generer les precisions » inoperant, exactement comme avant que la cle existe.

Revision ID: f2e3d4c5b6a7
Revises: d4f8a2b6c9e3
Create Date: 2026-08-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2e3d4c5b6a7"
down_revision: Union[str, Sequence[str], None] = "d4f8a2b6c9e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Texte FIGE, repris mot pour mot de la f-string retiree de analyse_amont.py.
PROMPTS_MAJ = {
    "suggerer_precisions_type": """Tu es un concepteur pédagogique.
Pour le type d'activité « {label} » enseigné au niveau « {niveau} », propose 3 à 6 PRÉCISIONS : des déclinaisons concrètes de ce type, réellement adaptées à ce niveau (ni trop enfantines, ni trop avancées).
Appuie-toi sur le référentiel officiel ci-dessous pour rester dans le programme :
{texte}

Rends UNIQUEMENT des libellés courts (2 à 4 mots), en minuscules.""",
}

_INSERE = sa.text(
    "INSERT INTO settings (key, value) VALUES (:key, :value) ON CONFLICT (key) DO NOTHING"
)


def upgrade() -> None:
    conn = op.get_bind()
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(_INSERE, {"key": f"prompt_{cle}", "value": texte})


def downgrade() -> None:
    conn = op.get_bind()
    for cle in PROMPTS_MAJ:
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {"key": f"prompt_{cle}"})
