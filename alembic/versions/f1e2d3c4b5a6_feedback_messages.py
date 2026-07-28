"""Table `feedback_messages` : la RÉPONSE de l'admin et la suite de l'échange sur un retour.

Le canal prof → admin existait déjà et fonctionne (le prof écrit, c'est en base, l'admin le
reçoit par mail et le classe). Il manquait le retour : l'admin n'avait AUCUN endroit où écrire,
et le prof ne voyait qu'une étiquette de statut avancer. Cette table porte l'échange qui SUIT
le message d'ouverture — elle ne le remplace pas : `feedbacks.message` reste le premier message
(toujours modifiable par son auteur selon `feedback_statuts.modifiable`). Zéro copie, rien
d'existant n'est déplacé.

`auteur_est_admin` est un booléen et non une clé vers `users` : l'administrateur n'a pas de
compte dans l'application (connexion par un circuit séparé), et un échange n'a que deux côtés.
Le nom affiché se calcule à la lecture selon qui regarde — c'est de la présentation, pas une
donnée à ranger. Le prof, lui, est déjà identifié par `feedbacks.user_id`.

CASCADE sur `feedback_id` : supprimer un retour emporte son échange, comme aujourd'hui.

Sème aussi le modèle d'email « reponse_feedback » (mode auto, non supprimable) : le mail ne
porte QUE l'avis « vous avez une réponse », jamais son contenu, qui reste dans aSchool.
Semé sans id explicite (serial) + ON CONFLICT (slug) DO NOTHING, comme `feedback_statuts` —
aucun setval, la séquence se place seule.

Revision ID: f1e2d3c4b5a6
Revises: 5ca8e6b20fcc
"""
import sqlalchemy as sa
from alembic import op

revision = "f1e2d3c4b5a6"
down_revision = "5ca8e6b20fcc"
branch_labels = None
depends_on = None


# Les deux sens de l'avis. Aucun ne porte le contenu du message : il se lit dans aSchool.
_TEMPLATES = [
    {
        "slug": "reponse_feedback",
        "nom": "Réponse à un retour (vers le prof)",
        "description": "Prévient le prof qu'une réponse a été déposée sur son retour. "
                       "N'emporte pas le contenu : il se lit dans aSchool.",
        "objet": "Vous avez une réponse à votre retour aSchool",
        "corps": "Bonjour {prenom},\n\n"
                 "Vous avez une réponse à l'un des retours que vous avez envoyés depuis aSchool.\n\n"
                 "Connectez-vous et ouvrez « Mes retours » pour la lire et poursuivre l'échange.\n\n"
                 "L'équipe aSchool",
    },
    {
        "slug": "reponse_prof",
        "nom": "Réponse d'un prof (vers l'administration)",
        "description": "Prévient l'administration qu'un prof a répondu sur un retour en cours. "
                       "N'emporte pas le contenu : il se lit dans l'écran Retours utilisateurs.",
        "objet": "[aSchool] Un prof a répondu sur un retour",
        "corps": "Un prof a répondu sur un retour en cours.\n\n"
                 "Ouvrez l'écran « Retours utilisateurs » pour lire l'échange et poursuivre.\n\n"
                 "aSchool",
    },
]


def upgrade() -> None:
    op.create_table(
        "feedback_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("feedback_id", sa.Integer(),
                  sa.ForeignKey("feedbacks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("auteur_est_admin", sa.Boolean(), nullable=False),
        sa.Column("corps", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_feedback_messages_feedback_id_created_at",
        "feedback_messages", ["feedback_id", "created_at"],
    )

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
    op.drop_index("ix_feedback_messages_feedback_id_created_at", table_name="feedback_messages")
    op.drop_table("feedback_messages")
