"""referentiels.texte_epure : le texte de travail epure, calcule une fois au depot et fige

Principe valide avec l'admin : on epure UNE SEULE FOIS, a la validation du depot, avec les
regles d'epuration de ce jour-la ; le resultat est STOCKE et toutes les etapes suivantes
(matieres, prompt de decoupe, decoupe, re-decoupe) le LISENT. Plus aucune re-extraction du
PDF apres la validation — une regle ajoutee plus tard ne touche jamais un depot passe.
Le PDF sur disque reste la piece d'origine intacte (relecture admin).

Remplissage UNIQUE des referentiels deja deposes : leur PDF (intact sur disque) passe une
fois par la porte d'epuration du jour, puis la colonne fait foi. Un referentiel sans PDF
sur disque reste a NULL (filet : le premier usage le calcule et l'ecrit).

Revision ID: aa11bb22cc33
Revises: b0c1d2e3f4a5
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa

revision = "aa11bb22cc33"
down_revision = "b0c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("referentiels", sa.Column("texte_epure", sa.Text(), nullable=True))

    # Remplissage unique de l'existant, via LA porte d'extraction du projet (regles du jour).
    from backend.rag.extraction import extraire_texte
    from backend.pedagogie.referentiels_admin import REFERENTIELS_DIR, _dossier_cle

    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT r.id, c.nom AS cycle, n.nom AS niveau FROM referentiels r "
        "JOIN niveaux n ON n.id = r.niveau_id JOIN cycles c ON c.id = n.cycle_id"
    )).fetchall()
    for rid, cycle, niveau in rows:
        pdf = REFERENTIELS_DIR / _dossier_cle(cycle) / _dossier_cle(niveau) / "referentiel.pdf"
        if pdf.exists():
            bind.execute(sa.text("UPDATE referentiels SET texte_epure = :t WHERE id = :i"),
                         {"t": extraire_texte(pdf), "i": rid})


def downgrade():
    op.drop_column("referentiels", "texte_epure")
