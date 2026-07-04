"""cree la table email_templates + seed du modele 'welcome' (mail de bienvenue)

Remplace les 2 cles plates `welcome_email_subject` / `welcome_email_body` de la
table `settings` par une collection de modeles d'email (table `email_templates`).
Le mail de bienvenue devient une ligne : slug='welcome', mode_envoi='auto',
supprimable=False.

Seed sans regression : si une personnalisation du mail de bienvenue existe deja
dans `settings` (l'admin l'a editee), on la RECOPIE ; sinon on retombe sur le
texte par defaut historique (identique a SETTING_DEFAULTS). Les anciennes cles
`settings` sont laissees en place (inoffensives) — le code lit desormais la table.

downgrade : supprime la table (le mail de bienvenue reste servi par le repli code).

Revision ID: f3a1b2c3d4e5
Revises: e1f2a3b4c5d6
Create Date: 2026-07-04
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f3a1b2c3d4e5"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


# Defaut historique du mail de bienvenue (miroir de SETTING_DEFAULTS dans admin.py).
_WELCOME_SUBJECT = "Bienvenue sur aSchool !"
_WELCOME_BODY = (
    "Bonjour {prenom},\n\n"
    "Votre compte aSchool est maintenant actif !\n\n"
    "aSchool est votre assistant pedagogique : generez des activites adaptees a votre matiere "
    "et a vos eleves en quelques secondes.\n\n"
    "Connectez-vous des maintenant sur aschool.fr\n\n"
    "Parlez-en a vos collegues — plus on est nombreux, plus aSchool s'ameliore !\n\n"
    "Bonne utilisation,\nL'equipe aSchool"
)


def upgrade() -> None:
    op.create_table(
        "email_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("nom", sa.String(length=128), nullable=False),
        sa.Column("objet", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("corps", sa.Text(), nullable=False, server_default=""),
        sa.Column("mode_envoi", sa.String(length=16), nullable=False, server_default="manuel"),
        sa.Column("supprimable", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_email_templates_slug"),
    )

    # Seed du modele 'welcome' : recopie la perso existante (settings) si presente,
    # sinon le defaut historique.
    conn = op.get_bind()
    subject = conn.execute(
        sa.text("SELECT value FROM settings WHERE key = 'welcome_email_subject'")
    ).scalar()
    body = conn.execute(
        sa.text("SELECT value FROM settings WHERE key = 'welcome_email_body'")
    ).scalar()

    conn.execute(
        sa.text(
            "INSERT INTO email_templates (slug, nom, objet, corps, mode_envoi, supprimable) "
            "VALUES ('welcome', 'Email de bienvenue', :objet, :corps, 'auto', false)"
        ),
        {
            "objet": subject if subject else _WELCOME_SUBJECT,
            "corps": body if body else _WELCOME_BODY,
        },
    )


def downgrade() -> None:
    op.drop_table("email_templates")
