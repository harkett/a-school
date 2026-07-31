# -*- coding: utf-8 -*-
"""few-shot « aSchool vous reconnait » : les reglages et le prompt SEMES EN BASE

Le few-shot etait affiche au prof (jauge « aSchool vous connait a X% » dans Mes stats,
astuce de l Accueil, deux mentions dans l aide) alors qu il etait explicitement DIFFERE
cote serveur. Il est livre : la generation lit desormais les activites deja produites par
ce prof, du MEME type et pour le MEME couple, et les donne en exemple de SA maniere.

Trois valeurs entrent en base (jamais en dur dans le code, regle maison) :
  - few_shot_seuil        : nombre d activites du meme type + couple a partir duquel la
                            couche s applique (3 = ce que promet l astuce de l Accueil) ;
  - few_shot_extrait_max  : nombre de caracteres gardes par exemple (le prompt reste sain
                            meme si le prof a produit des activites tres longues) ;
  - prompt_few_shot       : le texte de la couche elle-meme, modifiable a chaud dans
                            l ecran admin des prompts comme tous les autres.

Idempotent : ON CONFLICT (key) DO NOTHING — rejouer la migration ne rabote pas une valeur
que l admin aurait deja ajustee.

downgrade : on retire les trois lignes (le code n a pas de repli, la fonctionnalite
redevient donc simplement indisponible, avec un message clair).

Revision ID: f4d8b1e7c3a9
Revises: e4b8c2d6a1f7
Create Date: 2026-07-31
"""
from alembic import op
import sqlalchemy as sa

from backend.core.llm_prompts import PROMPTS


revision = "f4d8b1e7c3a9"
down_revision = "e4b8c2d6a1f7"
branch_labels = None
depends_on = None


CLES = ("few_shot_seuil", "few_shot_extrait_max", "prompt_few_shot")


def upgrade():
    valeurs = {
        "few_shot_seuil": "3",
        "few_shot_extrait_max": "3000",
        "prompt_few_shot": PROMPTS["few_shot"]["default"],
    }
    for cle, valeur in valeurs.items():
        op.execute(
            sa.text("INSERT INTO settings (key, value) VALUES (:k, :v) "
                    "ON CONFLICT (key) DO NOTHING").bindparams(k=cle, v=valeur)
        )


def downgrade():
    for cle in CLES:
        op.execute(sa.text("DELETE FROM settings WHERE key = :k").bindparams(k=cle))
