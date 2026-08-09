"""Supprime `profs_bloques_maj` : le blocage des profs pendant une mise a jour de referentiel.

07/08/2026. CE QUE CETTE TABLE FAISAIT. Quand l'admin supprimait le referentiel d'un niveau, le
serveur detachait lui-meme la matiere des profs concernes (`users.subject_id` remis a NULL) pour
que la suppression passe, memorisait le nom perdu ici, et refusait toute generation tant que la
ligne existait.

POURQUOI ELLE PART. La base refusait DEJA la suppression : `fk_users_subject_id` est en NO ACTION,
une matiere portee par un prof ne peut pas disparaitre. Le code contournait sa propre garde
d'integrite pour reconstruire en Python une protection que PostgreSQL assurait gratuitement — et
cette protection-la, elle, ne se levait pas toute seule. Une ligne posee le 03/08/2026 par une
suppression qui n'a jamais abouti a laisse un compte incapable de generer pendant quatre jours,
devant un referentiel intact et une matiere valide.

CE QUI TIENT LA PLACE : le refus 409 « n professeur(s) travaillent sur une matiere de ce
referentiel ». L'admin change leur matiere d'abord. Rien d'autre n'est necessaire.

LES DONNEES PERDUES : les lignes en cours. Elles ne portaient qu'un nom de matiere memorise le
temps d'une suppression — or plus aucune suppression ne detache personne, ce nom n'a plus d'usage.

DOWNGRADE : la table se recree vide. Le mecanisme, lui, ne revient pas — il n'est plus dans le
code. C'est voulu : une revision qui ressusciterait la pratique n'aurait aucun interet.
"""
from alembic import op
import sqlalchemy as sa


revision = "d7c1e9a4b502"
down_revision = "c9e4b1a7d306"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("profs_bloques_maj")


def downgrade() -> None:
    op.create_table(
        "profs_bloques_maj",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("niveau_id", sa.Integer(), nullable=False),
        sa.Column("matiere_nom", sa.String(length=128), nullable=True),
        sa.Column("travail_niveau_id", sa.Integer(), nullable=True),
        sa.Column("travail_matiere_nom", sa.String(length=128), nullable=True),
        sa.Column("etat", sa.String(length=16), nullable=False, server_default="bloque"),
        sa.Column("resultat", sa.String(length=32), nullable=True),
        sa.Column("bloque_le", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("debloque_le", sa.DateTime(), nullable=True),
        sa.Column("remplacee_par", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["niveau_id"], ["niveaux.id"]),
        sa.UniqueConstraint("user_id", "niveau_id", name="uq_profs_bloques_maj_user_niveau"),
    )
    op.create_index("ix_profs_bloques_maj_user", "profs_bloques_maj", ["user_id"])
