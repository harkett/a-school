"""Empreinte SHA-256 du contenu : reconnaître un document déjà connu.

Redéposer deux fois le même PDF passait inaperçu — deuxième fichier en zone d'attente, deuxième
ligne, aucun signal. La reconnaissance se fait sur le CONTENU (SHA-256, 64 caractères hex) et
jamais sur le nom : le même document téléchargé deux fois porte souvent deux noms, et deux
documents différents portent parfois le même.

Deux colonnes, une de chaque côté du geste :
  · `referentiel_depots.empreinte` — calculée à chaque dépôt. NOT NULL (le calcul ne peut pas
    échouer : le contenu est en main). Indexée, jamais unique — on PRÉVIENT, on ne bloque pas :
    redéposer le même document reste permis, l'admin reste maître de la suite.
  · `referentiels.empreinte` — écrite à la validation. NULLABLE : elle vaut pour les documents
    validés à partir de maintenant, et pour les anciens elle est RÉTRO-REMPLIE ci-dessous en
    relisant leur PDF sur disque (REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf). Un fichier
    absent ou illisible laisse NULL — un rétro-remplissage n'a pas à faire échouer la migration.

Revision ID: d4f6a8c0b2e5
Revises: c3d5e7f9a1b2
"""
import hashlib
import logging
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "d4f6a8c0b2e5"
down_revision = "c3d5e7f9a1b2"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

_ROOT = Path(__file__).resolve().parents[2]
_REFERENTIELS_DIR = _ROOT / "REFERENTIELS"


def _cle(nom: str) -> str:
    """Règle de nommage des dossiers — importée du code applicatif, pas recopiée ici."""
    from backend.core.nommage import dossier_cle
    return dossier_cle(nom)


def upgrade() -> None:
    op.add_column("referentiel_depots", sa.Column("empreinte", sa.String(length=64), nullable=False,
                                                  server_default=""))
    op.alter_column("referentiel_depots", "empreinte", server_default=None)
    op.create_index("ix_referentiel_depots_empreinte", "referentiel_depots", ["empreinte"])
    op.add_column("referentiels", sa.Column("empreinte", sa.String(length=64), nullable=True))

    conn = op.get_bind()
    # Rétro-remplissage n°1 : les dépôts DÉJÀ en zone d'attente. Leur fichier est là, leur ligne
    # aussi — sans ça ils garderaient une empreinte vide et ne seraient jamais reconnus. Un
    # fichier introuvable ne peut pas laisser NOT NULL sans valeur : la ligne part, ce qui est
    # exactement la règle de la zone d'attente (jamais de ligne sans fichier).
    for depot in conn.execute(sa.text("SELECT id, chemin FROM referentiel_depots")).mappings().all():
        f = _ROOT / depot["chemin"]
        if not f.exists():
            conn.execute(sa.text("DELETE FROM referentiel_depots WHERE id = :i"), {"i": depot["id"]})
            logger.info("Empreinte : dépôt %s sans fichier — ligne retirée", depot["id"])
            continue
        conn.execute(sa.text("UPDATE referentiel_depots SET empreinte = :e WHERE id = :i"),
                     {"e": hashlib.sha256(f.read_bytes()).hexdigest(), "i": depot["id"]})

    # Rétro-remplissage n°2 : les référentiels DÉJÀ validés ont leur PDF rangé sur le disque. On le
    # relit pour qu'ils soient reconnus, eux aussi, dès le premier dépôt qui suivra.
    lignes = conn.execute(sa.text(
        "SELECT r.id, c.nom AS cycle, n.nom AS niveau FROM referentiels r "
        "JOIN niveaux n ON n.id = r.niveau_id JOIN cycles c ON c.id = n.cycle_id"
    )).mappings().all()
    for ligne in lignes:
        pdf = _REFERENTIELS_DIR / _cle(ligne["cycle"]) / _cle(ligne["niveau"]) / "referentiel.pdf"
        if not pdf.exists():
            logger.info("Empreinte : PDF absent pour %s · %s — laissé à NULL", ligne["cycle"], ligne["niveau"])
            continue
        empreinte = hashlib.sha256(pdf.read_bytes()).hexdigest()
        conn.execute(sa.text("UPDATE referentiels SET empreinte = :e WHERE id = :i"),
                     {"e": empreinte, "i": ligne["id"]})
        logger.info("Empreinte : %s · %s → %s", ligne["cycle"], ligne["niveau"], empreinte[:12])


def downgrade() -> None:
    op.drop_column("referentiels", "empreinte")
    op.drop_index("ix_referentiel_depots_empreinte", table_name="referentiel_depots")
    op.drop_column("referentiel_depots", "empreinte")
