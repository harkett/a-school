"""L'administration devient un compte — la ligne `users` de l'administrateur

Suite de `c1f7a3e8b2d4` (la colonne `role`). Celle-ci pose l'administrateur EXISTANT dans la
table, à partir de ce que l'installation sait déjà de lui :

  · son adresse — `ADMIN_EMAIL`, ou `ADMIN_USERNAME` s'il porte déjà une adresse ;
  · son mot de passe — l'empreinte bcrypt déjà choisie (`settings.admin_password_hash`) si elle
    existe, sinon celle calculée depuis `ADMIN_PASSWORD`. Le mot de passe n'est jamais écrit :
    on ne pose qu'une empreinte, exactement comme pour un professeur.

RIEN N'EST INVENTÉ. Si l'installation n'a ni adresse ni mot de passe d'administration, la
migration ne crée aucun compte et se tait : le filet de `admin_login` (les variables
d'environnement tant qu'aucun compte `admin` n'existe) continue de fonctionner. C'est le cas
d'une base neuve, d'une base de test ou d'un poste où l'administration n'a jamais servi.

SI L'ADRESSE EST DÉJÀ UN COMPTE — l'administrateur s'était inscrit comme professeur — on ne
touche PAS à son mot de passe : on ne fait que lui poser le rôle. Écraser son empreinte le
déconnecterait de son propre compte.

Revision ID: d3b9e5a7c2f8
Revises: c1f7a3e8b2d4
Create Date: 2026-08-17
"""
import os

from alembic import op
import sqlalchemy as sa

revision = 'd3b9e5a7c2f8'
down_revision = 'c1f7a3e8b2d4'
branch_labels = None
depends_on = None


def _adresse() -> str:
    """L'adresse de l'administrateur, telle que l'installation la connaît."""
    for cle in ("ADMIN_EMAIL", "ADMIN_USERNAME"):
        valeur = (os.getenv(cle) or "").strip()
        if "@" in valeur:
            return valeur
    return ""


def upgrade():
    bind = op.get_bind()
    adresse = _adresse()
    if not adresse:
        return

    # L'empreinte : celle qui a été choisie depuis l'écran d'administration, sinon celle du
    # mot de passe d'installation. Jamais le mot de passe lui-même.
    empreinte = bind.execute(sa.text(
        "SELECT value FROM settings WHERE key = 'admin_password_hash'")).scalar()
    if not empreinte:
        clair = os.getenv("ADMIN_PASSWORD") or ""
        if not clair:
            return
        import bcrypt
        empreinte = bcrypt.hashpw(clair.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")

    existant = bind.execute(sa.text("SELECT id FROM users WHERE email = :e"),
                            {"e": adresse}).scalar()
    if existant:
        # Le compte existe déjà : on lui pose le rôle, et RIEN d'autre.
        bind.execute(sa.text("UPDATE users SET role = 'admin' WHERE id = :i"), {"i": existant})
        return

    bind.execute(sa.text("""
        INSERT INTO users (email, password_hash, is_verified, is_active, role, created_at,
                           failed_attempts)
        VALUES (:e, :h, true, true, 'admin', NOW(), 0)
    """), {"e": adresse, "h": empreinte})


def downgrade():
    # On ne supprime pas le compte : il porte peut-être déjà des contenus, et sa suppression
    # emporterait ce qui pend à sa clé. Il redevient un professeur, comme les autres.
    adresse = _adresse()
    if adresse:
        op.get_bind().execute(sa.text("UPDATE users SET role = 'prof' WHERE email = :e"),
                              {"e": adresse})
