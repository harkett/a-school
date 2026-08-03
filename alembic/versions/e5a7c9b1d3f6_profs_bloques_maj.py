"""Table `profs_bloques_maj` + les deux modèles d'e-mail de la mise à jour d'un référentiel.

L'Éducation nationale publie une nouvelle version d'un programme : l'admin doit pouvoir
supprimer le référentiel du couple et refaire la procédure MÊME QUAND des profs travaillent
dessus. Impossible jusqu'ici — la suppression était refusée dès qu'un prof était rattaché, et
la clé étrangère `fk_users_subject_id` (NO ACTION) faisait de toute façon ÉCHOUER l'écriture,
pas un refus poli.

Cette table porte les deux choses que la suppression détruirait :
  · l'attente du prof (il ne peut pas générer sur ce niveau) ;
  · la MÉMOIRE de sa matière — son NOM, seul rescapé : l'identifiant meurt avec le référentiel
    (CASCADE sur `matieres`), le nom se re-résout dans le nouveau (`matiere_id_du_nom`).

Une ligne par prof ET par niveau : un prof peut avoir son profil sur un niveau et son couple de
travail sur un autre, tous deux mis à jour l'un après l'autre.

Sème aussi les deux modèles d'e-mail (mode auto, non supprimables), comme `reponse_feedback` :
le texte se corrige dans Admin → Email sans passer par le code. Un prof bloqué qui ne se
connecte pas ce jour-là ne verrait rien à l'écran — c'est exactement celui qui appelle.

Revision ID: e5a7c9b1d3f6
Revises: d4f6a8c0b2e5
"""
import sqlalchemy as sa
from alembic import op

revision = "e5a7c9b1d3f6"
down_revision = "d4f6a8c0b2e5"
branch_labels = None
depends_on = None


# Français simple, aucun terme technique : un prof qui ne comprend pas appelle, ou croit que le
# produit est cassé. {prenom} est rendu par l'envoi ; {matiere} et {niveau} par l'appelant.
_TEMPLATES = [
    {
        "slug": "referentiel_maj_debut",
        "nom": "Mise à jour du programme — début (vers le prof)",
        "description": "Prévient le prof que le programme officiel de son niveau est en cours de "
                       "mise à jour et que la génération est momentanément indisponible pour lui.",
        "objet": "Votre programme est en cours de mise à jour",
        "corps": "Bonjour {prenom},\n\n"
                 "Le programme officiel de votre niveau est en cours de mise à jour. La génération "
                 "est momentanément indisponible pour vous.\n\n"
                 "Vous n'avez rien à faire : tout ce que vous avez créé est conservé, et vous "
                 "pourrez reprendre dès que ce sera terminé.\n\n"
                 "L'équipe aSchool",
    },
    {
        "slug": "referentiel_maj_fin",
        "nom": "Mise à jour du programme — fin (vers le prof)",
        "description": "Prévient le prof que la mise à jour est terminée. Dit si sa matière a été "
                       "rebranchée, ou qu'elle a disparu du nouveau document et qu'il doit rechoisir.",
        "objet": "Votre programme est de nouveau disponible",
        "corps": "Bonjour {prenom},\n\n"
                 "La mise à jour est terminée. Vous pouvez de nouveau générer.\n\n"
                 "{suite}\n\n"
                 "L'équipe aSchool",
    },
]


def upgrade() -> None:
    op.create_table(
        "profs_bloques_maj",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("niveau_id", sa.Integer(), sa.ForeignKey("niveaux.id"), nullable=False),
        sa.Column("matiere_nom", sa.Text(), nullable=True),
        sa.Column("travail_niveau_id", sa.Integer(), nullable=True),
        sa.Column("travail_matiere_nom", sa.Text(), nullable=True),
        sa.Column("etat", sa.String(length=12), nullable=False, server_default="bloque"),
        sa.Column("resultat", sa.String(length=20), nullable=True),
        sa.Column("bloque_le", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("debloque_le", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "niveau_id", name="uq_profs_bloques_maj_user_niveau"),
    )
    op.create_index("ix_profs_bloques_maj_user", "profs_bloques_maj", ["user_id"])

    conn = op.get_bind()
    insert = sa.text(
        "INSERT INTO email_templates (slug, nom, description, objet, corps, mode_envoi, supprimable) "
        "VALUES (:slug, :nom, :description, :objet, :corps, 'auto', false) "
        "ON CONFLICT (slug) DO NOTHING"
    )
    for modele in _TEMPLATES:
        conn.execute(insert, modele)


def downgrade() -> None:
    op.get_bind().execute(
        sa.text("DELETE FROM email_templates WHERE slug = ANY(:slugs)"),
        {"slugs": [m["slug"] for m in _TEMPLATES]},
    )
    op.drop_index("ix_profs_bloques_maj_user", table_name="profs_bloques_maj")
    op.drop_table("profs_bloques_maj")
