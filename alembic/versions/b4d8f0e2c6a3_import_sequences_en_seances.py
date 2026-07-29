"""Import des anciennes « séquences » en SÉANCES (elles en sont) + colonnes mode/import_source_id.

L'outil « Séquence » a toujours généré des séances (le prompt prépare « une séance de X
minutes » en 5-6 phases) : ses sauvegardes (`sequences_sauvegardees`) rejoignent donc la
table `seances` du modèle « Mes contenus », sous leur vrai nom. Chaque résultat est aussi
DÉCOUPÉ en phases structurées (`seance_phases`) via le parser partagé
`backend.sequence.phases.decouper_phases` — zéro copie de logique.

- `seances.mode` : le mode de génération (standard/remédiation) voyage avec la séance,
  il sert au « Recharger » (pré-remplir l'outil).
- `seances.import_source_id` (UNIQUE) : l'id d'origine dans `sequences_sauvegardees` —
  l'import est REJOUABLE sans doublon (ON CONFLICT DO NOTHING), et la provenance reste lisible.

`sequences_sauvegardees` n'est PAS détruite : « Mon réseau » (partages) la lit encore ;
son extinction viendra quand le partage des séances existera dans le nouveau modèle.

Revision ID: b4d8f0e2c6a3
Revises: a3c7e9d1b5f2
"""
import sqlalchemy as sa
from alembic import op

from backend.sequence.phases import decouper_phases

revision = "b4d8f0e2c6a3"
down_revision = "a3c7e9d1b5f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("seances", sa.Column("mode", sa.String(32), nullable=False, server_default="standard"))
    op.add_column("seances", sa.Column("import_source_id", sa.Integer(), nullable=True))
    op.create_index("ux_seances_import_source_id", "seances", ["import_source_id"], unique=True)

    conn = op.get_bind()
    anciennes = conn.execute(sa.text(
        "SELECT id, user_id, matiere, niveau, theme, duree, mode, description_classe, resultat, created_at "
        "FROM sequences_sauvegardees ORDER BY id"
    )).mappings().all()

    for r in anciennes:
        nouveau = conn.execute(sa.text(
            "INSERT INTO seances (user_id, titre, matiere, niveau, duree_minutes, mode, description, "
            "                     resultat, import_source_id, created_at, updated_at) "
            "VALUES (:user_id, :titre, :matiere, :niveau, :duree, :mode, :description, "
            "        :resultat, :source_id, :created_at, :created_at) "
            "ON CONFLICT (import_source_id) DO NOTHING RETURNING id"
        ), {
            "user_id": r["user_id"],
            "titre": (r["theme"] or "Séance")[:300],
            "matiere": r["matiere"],
            "niveau": r["niveau"],
            "duree": r["duree"],
            "mode": r["mode"],
            "description": r["description_classe"] or "",
            "resultat": r["resultat"],
            "source_id": r["id"],
            "created_at": r["created_at"],
        }).scalar()
        if nouveau is None:
            continue    # déjà importée (rejeu) — jamais de doublon
        for ph in decouper_phases(r["resultat"]):
            conn.execute(sa.text(
                "INSERT INTO seance_phases (seance_id, position, titre, contenu, duree_minutes) "
                "VALUES (:seance_id, :position, :titre, :contenu, :duree_minutes)"
            ), {"seance_id": nouveau, **ph})


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "DELETE FROM seance_phases WHERE seance_id IN "
        "(SELECT id FROM seances WHERE import_source_id IS NOT NULL)"
    ))
    conn.execute(sa.text("DELETE FROM seances WHERE import_source_id IS NOT NULL"))
    op.drop_index("ux_seances_import_source_id", table_name="seances")
    op.drop_column("seances", "import_source_id")
    op.drop_column("seances", "mode")
