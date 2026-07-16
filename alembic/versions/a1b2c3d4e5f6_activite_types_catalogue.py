"""types d'activite : catalogue GLOBAL + liaison referentiel (N-N)

L'ancienne table activite_types portait `referentiel_id` -> « 1 type = 1 referentiel » (faux :
seuls les couples avec un PDF ingere pouvaient avoir des types). On la REMPLACE par le bon modele :

  - activite_types            = CATALOGUE global (un type defini une seule fois, partage). `key`
                                UNIQUE ; `is_default` = repli « Activite d'apprentissage » (un seul,
                                garanti par l'index partiel ux_default).
  - referentiel_activite_types = LIAISON N-N (le « coche/decoche ») : le referentiel active/desactive
                                des types du catalogue. FK CASCADE des deux cotes ; unicite
                                (referentiel_id, activite_type_id) ; `source` = 'ia' | 'admin'.

L'ancienne table etait VIDE (0 ligne) et le Setting `type_activite_defaut` n'existait pas : aucune
donnee a migrer. Cette migration cree la STRUCTURE (catalogue + liaison) ET seede le catalogue : le
defaut `is_default=true` + les 13 familles d'activite. Le seed est ici = source de verite versionnee,
reproductible a chaque reconstruction.

downgrade : recree l'ancienne activite_types (ancree au referentiel), telle que f7a8b9c0d1e2.

Revision ID: a1b2c3d4e5f6
Revises: f7a8b9c0d1e2
Create Date: 2026-07-16
"""
import json

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


# Prompt NEUTRE du type par defaut — valable de la creche au doctorat (aucune matiere nommee).
# Editable en base ensuite. N'utilise que {niveau} et {texte} (params vides pour le defaut).
_PROMPT_DEFAUT = (
    "Tu es un enseignant experimente.\n"
    "A partir du contenu ci-dessous, concois une activite d'apprentissage adaptee a des eleves "
    "de {niveau}.\n"
    "Propose une activite claire et directement exploitable (objectif, consigne, deroule), fidele "
    "au contenu.\n\n"
    "Contenu :\n---\n{texte}\n---\n"
)


def upgrade() -> None:
    # 1) On retire l'ancienne table (vide, ancree au referentiel) — plus rien ne la reference.
    op.drop_table("activite_types")

    # 2) Le CATALOGUE global.
    op.create_table(
        "activite_types",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("sous_types", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("params", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("key", name="uq_activite_types_key"),
    )
    # Un SEUL defaut : index unique partiel sur is_default = true.
    op.create_index(
        "ux_default", "activite_types", ["is_default"],
        unique=True, postgresql_where=sa.text("is_default"),
    )

    # 3) La LIAISON N-N (le coche/decoche).
    op.create_table(
        "referentiel_activite_types",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "referentiel_id", sa.Integer(),
            sa.ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "activite_type_id", sa.Integer(),
            sa.ForeignKey("activite_types.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("referentiel_id", "activite_type_id", name="uq_ref_activite_type"),
    )
    op.create_index("ix_ref_activite_types_referentiel_id", "referentiel_activite_types", ["referentiel_id"])
    op.create_index("ix_ref_activite_types_activite_type_id", "referentiel_activite_types", ["activite_type_id"])

    # 4) Seed du catalogue : le defaut (repli) + les 13 familles d'activite.
    catalogue = sa.table(
        "activite_types",
        sa.column("key", sa.String),
        sa.column("label", sa.String),
        sa.column("sous_types", sa.Text),
        sa.column("params", sa.Text),
        sa.column("prompt", sa.Text),
        sa.column("is_default", sa.Boolean),
        sa.column("actif", sa.Boolean),
        sa.column("ordre", sa.Integer),
    )
    familles = [
        ("decouverte_manipulation", "Découverte / manipulation", "exploration sensorielle, manipulation d'objets, expérimentation"),
        ("activites_orales",         "Activités orales",          "échange, débat, exposé, présentation, récitation"),
        ("activites_ecrites",        "Activités écrites",         "copie, dictée, rédaction, prise de notes, dissertation"),
        ("lecture_recherche",        "Lecture / recherche",       "lecture, recherche documentaire, revue de littérature"),
        ("entrainement_application", "Entraînement / application", "exercices, problèmes, travaux dirigés (TD)"),
        ("experimentales_pratiques", "Expérimentales / pratiques", "travaux pratiques (TP), ateliers, laboratoire"),
        ("projet",                   "Projet",                    "projet individuel, projet de groupe, chef-d'œuvre, mémoire"),
        ("evaluation",               "Évaluation",                "contrôle, examen, soutenance, auto-évaluation"),
        ("collaboratives",           "Collaboratives",            "travail de groupe, tutorat, entraide"),
        ("artistiques_creatives",    "Artistiques / créatives",   "arts plastiques, musique, théâtre, expression corporelle"),
        ("physiques_motrices",       "Physiques / motrices",      "motricité, EPS, sport"),
        ("terrain_immersion",        "Terrain / immersion",       "sortie, visite, stage, terrain, enquête"),
        ("numeriques",               "Numériques",                "usage d'outils numériques, codage, e-learning"),
    ]
    lignes = [{
        "key": "activite_apprentissage",
        "label": "Activité d'apprentissage",
        "sous_types": "[]",
        "params": "[]",
        "prompt": _PROMPT_DEFAUT,
        "is_default": True,
        "actif": True,
        "ordre": 0,
    }]
    for i, (key, label, sous_types) in enumerate(familles, start=1):
        lignes.append({
            "key": key,
            "label": label,
            "sous_types": json.dumps([s.strip() for s in sous_types.split(",")], ensure_ascii=False),
            "params": "[]",
            "prompt": "",
            "is_default": False,
            "actif": True,
            "ordre": i,
        })
    op.bulk_insert(catalogue, lignes)


def downgrade() -> None:
    # Retire le nouveau modele.
    op.drop_index("ix_ref_activite_types_activite_type_id", table_name="referentiel_activite_types")
    op.drop_index("ix_ref_activite_types_referentiel_id", table_name="referentiel_activite_types")
    op.drop_table("referentiel_activite_types")
    op.drop_index("ux_default", table_name="activite_types")
    op.drop_table("activite_types")

    # Recree l'ancienne activite_types (ancree au referentiel) telle que f7a8b9c0d1e2.
    op.create_table(
        "activite_types",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "referentiel_id", sa.Integer(),
            sa.ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("sous_types", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("params", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("referentiel_id", "key", name="uq_activite_types_ref_key"),
    )
    op.create_index("ix_activite_types_referentiel_id", "activite_types", ["referentiel_id"])
