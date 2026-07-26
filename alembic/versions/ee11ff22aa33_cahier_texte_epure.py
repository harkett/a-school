"""cahiers_prof.texte_epure : le texte de travail epure du cahier des charges du prof, extrait
une fois au depot et fige (meme principe que referentiels.texte_epure)

Pourquoi : la generation doit LIRE le cahier des charges du prof pour appliquer les regles de
son ecole par-dessus le programme officiel. Le PDF seul n'est pas exploitable — il faut son
TEXTE. On l'extrait UNE SEULE FOIS au depot (porte unique rag.extraction) et on le FIGE ici ;
la generation le lit ensuite (get, zero copie). Le PDF sur disque reste la piece d'origine.

Remplissage UNIQUE des cahiers deja deposes : leur PDF (intact sur disque, data/uploads/
cahiers/<user_id>/cahier.pdf) passe une fois par la porte d'epuration du jour. Un cahier sans
PDF sur disque reste a NULL (la generation se fera alors sans cahier, sans regression).

Revision ID: ee11ff22aa33
Revises: dd00ee11ff22
Create Date: 2026-07-26
"""
from alembic import op
import sqlalchemy as sa

revision = "ee11ff22aa33"
down_revision = "dd00ee11ff22"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("cahiers_prof", sa.Column("texte_epure", sa.Text(), nullable=True))

    # Remplissage unique de l'existant, via LA porte d'extraction du projet (regles du jour).
    from backend.rag.extraction import extraire_texte
    from backend.prof.profil import UPLOADS_CAHIERS_DIR

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, user_id FROM cahiers_prof")).fetchall()
    for cid, user_id in rows:
        pdf = UPLOADS_CAHIERS_DIR / str(user_id) / "cahier.pdf"
        if pdf.exists():
            bind.execute(sa.text("UPDATE cahiers_prof SET texte_epure = :t WHERE id = :i"),
                         {"t": extraire_texte(pdf), "i": cid})


def downgrade():
    op.drop_column("cahiers_prof", "texte_epure")
