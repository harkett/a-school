"""ajoute les colonnes regle de decoupe + arbitrage sur referentiels (EN BASE)

La regle de decoupe d'un couple (objet a deux faces : explication claire + motif regex, statut
valide, depose_par) et l'arbitrage des cas flous ({label: [bandes]}) vivaient dans des fichiers
a cote du PDF (regle-decoupe.json / arbitrage-flou.json). Regle « toute donnee metier en base » :
ils deviennent des colonnes de `referentiels` (une regle + un arbitrage par referentiel).

Colonnes :
  - regle_explication (Text)  : face claire lue par l'admin pour valider
  - regle_motif       (Text)  : critere technique (regex) execute par la fiche a l'ingestion
  - regle_depose_par  (Text)  : 'dev' | 'admin'
  - regle_valide      (Bool)  : decoupage refuse tant que False (defaut false)
  - arbitrage         (Text)  : JSON {label flou: [bandes]} ; NULL = aucun cas tranche

La donnee des 3 regle-decoupe.json creche existants est versee par un script ephemere, puis les
fichiers sont supprimes. Aucun arbitrage-flou.json n'existait (colonne arbitrage laissee NULL).

downgrade : supprime les 5 colonnes.

Revision ID: a3c4d5e6f7a8
Revises: f2b3c4d5e6f7
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a3c4d5e6f7a8"
down_revision = "f2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("regle_explication", sa.Text(), nullable=True))
    op.add_column("referentiels", sa.Column("regle_motif", sa.Text(), nullable=True))
    op.add_column("referentiels", sa.Column("regle_depose_par", sa.Text(), nullable=True))
    op.add_column("referentiels", sa.Column("regle_valide", sa.Boolean(), nullable=False, server_default="0"))
    op.add_column("referentiels", sa.Column("arbitrage", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("referentiels", "arbitrage")
    op.drop_column("referentiels", "regle_valide")
    op.drop_column("referentiels", "regle_depose_par")
    op.drop_column("referentiels", "regle_motif")
    op.drop_column("referentiels", "regle_explication")
