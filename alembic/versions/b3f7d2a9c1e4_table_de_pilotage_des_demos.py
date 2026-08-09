"""Cree `demos` : le PILOTAGE des bases de demonstration, jamais leur contenu.

07/08/2026. Une demonstration est une base PostgreSQL A PART (ciela_demo, cielb_demo…) qui
contient un referentiel deja fabrique, un compte de demonstration et du contenu d'exemple. Cette
table-ci vit dans la base REELLE et se contente de dire, pour chaque niveau, OU est sa
demonstration et OU elle en est.

`nom_base` EST DU TEXTE ET NON UNE CLE ETRANGERE : PostgreSQL ne sait pas referencer une autre
base. Le lien ne peut donc etre qu'un nom, tenu juste a la main. Convention : `<option>_demo`, en
minuscules et sans tiret (un tiret obligerait a ecrire le nom entre guillemets dans TOUTE commande
SQL, et un oubli se lirait comme une soustraction).

UNE SEULE DEMONSTRATION PAR REFERENTIEL (`uq_demos_referentiel`) : deux demonstrations du meme
niveau n'auraient aucun sens et l'admin ne saurait pas laquelle est livree.

CASCADE sur `referentiel_id` : le referentiel disparu, sa demonstration ne designe plus rien.
Meme regle que `matieres` et `types_activite`, qui tombent deja avec lui.

AUCUNE LIGNE N'EST SEMEE ICI. La table nait vide : `ciela_demo` existe deja sur le serveur, mais
l'inscrire depuis une migration reviendrait a coder en dur un etat de machine qui n'est vrai que
sur la mienne. C'est l'ecran d'administration qui la declarera.
"""
from alembic import op
import sqlalchemy as sa


revision = "b3f7d2a9c1e4"
down_revision = "a8d3f1e6c9b2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "demos",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True, nullable=False),
        sa.Column("referentiel_id", sa.Integer(), nullable=False),
        sa.Column("nom_base", sa.Text(), nullable=False),
        sa.Column("statut", sa.String(length=16), nullable=False, server_default="a_faire"),
        sa.Column("nb_activites", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("nb_sequences", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("nb_seances", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("date_generation", sa.DateTime(), nullable=True),
        sa.Column("date_dernier_test", sa.DateTime(), nullable=True),
        sa.Column("defauts_connus", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["referentiel_id"], ["referentiels.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("referentiel_id", name="uq_demos_referentiel"),
    )


def downgrade():
    op.drop_table("demos")
