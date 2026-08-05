# -*- coding: utf-8 -*-
"""ai_fournisseurs / ai_modeles : les caracteristiques que le code devinait

Etape 1 de la specification « gestion des fournisseurs IA » : les deux tables portent desormais ce
qui, jusqu'ici, etait ecrit dans le code ou pas ecrit du tout.

`ai_fournisseurs`
- `type_api` : « anthropic » (SDK natif) ou « openai_compat » (chat/completions). C'est CE champ
  qui doit remplacer le `if fournisseur == ...` de generator.py — un fournisseur de plus ne sera
  plus une modification de code, mais une ligne.
- `base_url` : l'adresse d'appel. Celle d'Infomaniak porte le NUMERO DE PRODUIT du compte, qui
  change d'une installation a l'autre : elle est donc semee avec le marqueur `{produit}`, a
  substituer depuis AITOOLS_PRODUCT_ID (.env). Un secret ne descend jamais en base ; un numero de
  produit n'en est pas un, mais il reste propre a l'installation, d'ou le marqueur.
- `sortie_max` : plafond de sortie du FOURNISSEUR, dont ses modeles heritent. Les 5 000 tokens
  d'Infomaniak ne sont pas une limite de mistral24b : les trois modeles du produit la partagent,
  c'est le produit AI Tools qui la pose. Un modele garde le droit de la surcharger (sa propre
  colonne `sortie_max`) ; sans valeur, il prend celle de son fournisseur.

`ai_modeles`
- `contexte_max` : fenetre TOTALE (entree + sortie). C'est la borne qui manquait le plus :
  mistral24b l'a a 32 000 et refuse en 400 un referentiel de 46 000 tokens, apres avoir fait
  attendre. Mesuree fournisseur par fournisseur, pas recopiee d'une documentation.
- `supporte_schema` / `supporte_stream` : sortie contrainte et flux. Verifies en appelant les
  trois fournisseurs — tous les trois savent faire, la colonne existe pour le jour ou un modele
  ne saura pas.
- `cout_entree_million` / `cout_sortie_million` : laisses VIDES. Aucun tarif n'est invente ici ;
  ils seront saisis quand l'ecran des statistiques les demandera.

Valeurs semees : mesurees (Infomaniak) ou publiees par le fournisseur (Anthropic, Groq).

downgrade : drop des colonnes ajoutees.

Revision ID: e2a4c6b8d0f3
Revises: d9e1f3a5b7c2
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e2a4c6b8d0f3"
down_revision: Union[str, Sequence[str], None] = "d9e1f3a5b7c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (code, type_api, base_url, sortie_max) — l'URL d'Infomaniak porte le marqueur {produit}.
# sortie_max NULL = le fournisseur n'impose pas de plafond commun a ses modeles.
_FOURNISSEURS = [
    ("groq", "openai_compat", "https://api.groq.com/openai/v1", None),
    ("anthropic", "anthropic", None, None),
    ("infomaniak", "openai_compat", "https://api.infomaniak.com/1/ai/{produit}/openai", 5000),
]

# (fournisseur, modele, contexte_max) — fenetre TOTALE entree + sortie.
_CONTEXTES = [
    ("anthropic", "claude-sonnet-5", 200000),
    ("anthropic", "claude-opus-4-8", 200000),
    ("groq", "llama-3.3-70b-versatile", 131072),
    ("groq", "openai/gpt-oss-120b", 131072),
    ("infomaniak", "mistral24b", 32000),
]


def upgrade() -> None:
    op.add_column("ai_fournisseurs", sa.Column("type_api", sa.String(length=30), nullable=False, server_default="openai_compat"))
    op.add_column("ai_fournisseurs", sa.Column("base_url", sa.String(length=255), nullable=True))
    op.add_column("ai_fournisseurs", sa.Column("sortie_max", sa.Integer(), nullable=True))
    op.add_column("ai_fournisseurs", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.add_column("ai_fournisseurs", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    op.add_column("ai_modeles", sa.Column("contexte_max", sa.Integer(), nullable=True))
    op.add_column("ai_modeles", sa.Column("supporte_schema", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("ai_modeles", sa.Column("supporte_stream", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("ai_modeles", sa.Column("cout_entree_million", sa.Numeric(10, 4), nullable=True))
    op.add_column("ai_modeles", sa.Column("cout_sortie_million", sa.Numeric(10, 4), nullable=True))
    op.add_column("ai_modeles", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.add_column("ai_modeles", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    conn = op.get_bind()
    for code, type_api, base_url, sortie_max in _FOURNISSEURS:
        conn.execute(
            sa.text("UPDATE ai_fournisseurs SET type_api = :type_api, base_url = :base_url, "
                    "sortie_max = :sortie_max WHERE code = :code"),
            {"code": code, "type_api": type_api, "base_url": base_url, "sortie_max": sortie_max},
        )
    for fournisseur, modele, contexte in _CONTEXTES:
        conn.execute(
            sa.text("UPDATE ai_modeles SET contexte_max = :contexte WHERE fournisseur = :fournisseur AND modele = :modele"),
            {"fournisseur": fournisseur, "modele": modele, "contexte": contexte},
        )


def downgrade() -> None:
    for colonne in ("created_at", "updated_at", "cout_sortie_million", "cout_entree_million",
                    "supporte_stream", "supporte_schema", "contexte_max"):
        op.drop_column("ai_modeles", colonne)
    for colonne in ("created_at", "updated_at", "sortie_max", "base_url", "type_api"):
        op.drop_column("ai_fournisseurs", colonne)
