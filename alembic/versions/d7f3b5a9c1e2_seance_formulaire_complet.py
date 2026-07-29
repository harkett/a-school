"""Séance du monde neuf : le FORMULAIRE ENTIER vit en base + versions restaurables.

Constat (comparaison maquette ↔ table, validée avec l'utilisateur) : 6 champs du formulaire
Séance n'avaient AUCUNE colonne — mode, compétences, matériel, esquisse A/B/C, contraintes,
style. Sans eux, générer aurait perdu la moitié de la saisie (aucune réouverture préremplie
possible). Règle du chantier : chaque champ de l'écran vit en base (reprise complète), comme
pour l'activité.

- `mode`  : standard / remediation / approfondissement / autonomie (le prompt du mode est en base).
- `competences` : liste JSON de chaînes (les chips « Compétences / attendus »).
- `esquisse`    : JSON {a, b, c} — l'esquisse du déroulé écrite PAR le prof (une entrée, pas le résultat).
- `materiel`, `contraintes` : textes libres.
- `style` : classique / ludique / structure / concis (couche de style du prompt, en base).

`seance_versions` = le même moule qu'`activite_versions` (règle 0) : chaque génération EMPILE
une photo restaurable — on n'écrase jamais un déroulé généré.

Revision ID: d7f3b5a9c1e2
Revises: c5e9a1b3d7f4
"""
import sqlalchemy as sa
from alembic import op

revision = "d7f3b5a9c1e2"
down_revision = "c5e9a1b3d7f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("seances", sa.Column("mode", sa.String(32), nullable=True))
    op.add_column("seances", sa.Column("competences", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("seances", sa.Column("materiel", sa.Text(), nullable=False, server_default=""))
    op.add_column("seances", sa.Column("esquisse", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("seances", sa.Column("contraintes", sa.Text(), nullable=False, server_default=""))
    op.add_column("seances", sa.Column("style", sa.String(32), nullable=True))

    op.create_table(
        "seance_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("seance_id", sa.Integer(),
                  sa.ForeignKey("seances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jalon", sa.String(32), nullable=False, server_default="generation"),
        sa.Column("style", sa.String(32), nullable=True),
        sa.Column("resultat", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seance_versions_seance_id", "seance_versions", ["seance_id"])


def downgrade() -> None:
    op.drop_index("ix_seance_versions_seance_id", table_name="seance_versions")
    op.drop_table("seance_versions")
    op.drop_column("seances", "style")
    op.drop_column("seances", "contraintes")
    op.drop_column("seances", "esquisse")
    op.drop_column("seances", "materiel")
    op.drop_column("seances", "competences")
    op.drop_column("seances", "mode")
