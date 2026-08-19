# -*- coding: utf-8 -*-
"""L'unité sait d'où elle vient, de quoi elle parle, et jusqu'à quand elle vaut.

Étape 1 du chantier « la matière sur l'unité, et le dépôt par arrêté » :
  - `referentiel_documents` : un document déposé = un morceau de texte épuré, avec son identifiant ;
  - `referentiel_chunks.document_id` : l'unité dit de quel document elle sort ;
  - `referentiel_chunk_matieres` : la liaison unité <-> matière, par clé étrangère ;
  - `referentiel_chunks.portee` : 'matiere' ou 'formation', NOT NULL, sans valeur par défaut ;
  - `referentiel_chunks.valide_du` / `valide_au` : la plage qui remplace l'écrasement.

CE QUE LA MIGRATION FAIT DE L'EXISTANT. Chaque référentiel a exactement un document aujourd'hui :
on le crée à partir de sa propre fiche (nom du fichier, source, date, texte épuré), et toutes ses
unités s'y rattachent. Leur portée est posée à 'matiere' — donc SANS matière liée : c'est l'état
vrai du chantier, l'étiquetage est l'étape 2, et l'écran le comptera tel quel. Les poser en
'formation' aurait été confortable et faux : les textes de cadre auraient été noyés parmi les
programmes, et on aurait cru le travail fait.

Revision ID: d4a7c1f60b93
Revises: c3d9a1e75b42
Create Date: 2026-08-19
"""
from alembic import op
import sqlalchemy as sa

revision = "d4a7c1f60b93"
down_revision = "c3d9a1e75b42"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. LE DOCUMENT — ce qui manquait pour désigner une partie d'un référentiel.
    op.create_table(
        "referentiel_documents",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("referentiel_id", sa.Integer(),
                  sa.ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fichier", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("date_doc", sa.Text(), nullable=True),
        sa.Column("texte_epure", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_referentiel_documents_referentiel_id", "referentiel_documents",
                    ["referentiel_id"])

    # UN DOCUMENT PAR RÉFÉRENTIEL EXISTANT, tiré de sa propre fiche : c'est bien le document
    # qu'on a déposé, et son texte est celui qui a servi à la découpe.
    op.execute("""
        INSERT INTO referentiel_documents (referentiel_id, fichier, source, date_doc, texte_epure, created_at)
        SELECT id, COALESCE(fichier, 'referentiel.pdf'), source, date_doc, texte_epure, created_at
        FROM referentiels
    """)

    # 2. L'UNITÉ DIT SON DOCUMENT. Colonne posée nullable, remplie, puis verrouillée : une base
    #    qui porte déjà des unités ne peut pas recevoir une colonne NOT NULL d'un seul geste.
    op.add_column("referentiel_chunks", sa.Column("document_id", sa.Integer(), nullable=True))
    op.execute("""
        UPDATE referentiel_chunks c
        SET document_id = d.id
        FROM referentiel_documents d
        WHERE d.referentiel_id = c.referentiel_id
    """)
    op.alter_column("referentiel_chunks", "document_id", nullable=False)
    op.create_foreign_key("fk_referentiel_chunks_document", "referentiel_chunks",
                          "referentiel_documents", ["document_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_referentiel_chunks_document_id", "referentiel_chunks", ["document_id"])

    # 3. LA PORTÉE. Aucune valeur par défaut ne reste après la migration : écrire une unité, c'est
    #    dire ce qu'elle couvre. L'existant part en 'matiere' — donc en « à étiqueter », visible.
    op.add_column("referentiel_chunks", sa.Column("portee", sa.String(length=10), nullable=True))
    op.execute("UPDATE referentiel_chunks SET portee = 'matiere' WHERE portee IS NULL")
    op.alter_column("referentiel_chunks", "portee", nullable=False)
    op.create_check_constraint("ck_referentiel_chunks_portee", "referentiel_chunks",
                               "portee IN ('matiere', 'formation')")

    # 4. LA PLAGE DE VALIDITÉ. Le début des unités déjà en base est le jour de leur écriture —
    #    la date qu'elles portent déjà ; la fin reste vide : elles sont en vigueur.
    op.add_column("referentiel_chunks", sa.Column("valide_du", sa.Date(), nullable=True))
    op.add_column("referentiel_chunks", sa.Column("valide_au", sa.Date(), nullable=True))
    op.execute("UPDATE referentiel_chunks SET valide_du = created_at::date WHERE valide_du IS NULL")
    op.alter_column("referentiel_chunks", "valide_du", nullable=False)

    # 5. LA LIAISON UNITÉ <-> MATIÈRE. Elle naît VIDE : l'étiquetage des référentiels existants
    #    est l'étape 2, et une liaison inventée ici serait un étiquetage faux.
    op.create_table(
        "referentiel_chunk_matieres",
        sa.Column("chunk_id", sa.Integer(),
                  sa.ForeignKey("referentiel_chunks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("matiere_id", sa.Integer(),
                  sa.ForeignKey("matieres.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_referentiel_chunk_matieres_matiere_id", "referentiel_chunk_matieres",
                    ["matiere_id"])


def downgrade() -> None:
    op.drop_index("ix_referentiel_chunk_matieres_matiere_id", table_name="referentiel_chunk_matieres")
    op.drop_table("referentiel_chunk_matieres")
    op.drop_column("referentiel_chunks", "valide_au")
    op.drop_column("referentiel_chunks", "valide_du")
    op.drop_constraint("ck_referentiel_chunks_portee", "referentiel_chunks", type_="check")
    op.drop_column("referentiel_chunks", "portee")
    op.drop_index("ix_referentiel_chunks_document_id", table_name="referentiel_chunks")
    op.drop_constraint("fk_referentiel_chunks_document", "referentiel_chunks", type_="foreignkey")
    op.drop_column("referentiel_chunks", "document_id")
    op.drop_index("ix_referentiel_documents_referentiel_id", table_name="referentiel_documents")
    op.drop_table("referentiel_documents")
