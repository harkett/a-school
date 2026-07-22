"""remplir type_precisions / type_parametres depuis le JSON existant (sous_types / params)

Deplace la donnee : chaque valeur des blobs JSON `types_activite.sous_types` et `.params` devient
UNE ligne dans les tables filles. Data-driven : on LIT la base a l'execution (zero valeur en dur),
donc marche aussi bien sur la base existante que sur une base neuve (le seed a deja rempli le JSON
avant cette migration). `ordre` = position dans la liste (on garde l'ordre du menu). `source` =
'systeme' (ces valeurs viennent du seed). On NE touche PAS aux colonnes JSON ni au modele : elles
restent lues par l'ancien code jusqu'a la bascule (tache 3). La suppression des colonnes viendra
apres le rebranchement.

Revision ID: a1c2e3f4b5d6
Revises: f0e1d2c3b4a5
Create Date: 2026-07-21
"""
import json

from alembic import op
import sqlalchemy as sa

revision = "a1c2e3f4b5d6"
down_revision = "f0e1d2c3b4a5"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, sous_types, params FROM types_activite")).all()

    prec_ins = sa.text(
        "INSERT INTO type_precisions (type_activite_id, libelle, ordre, source) "
        "VALUES (:tid, :libelle, :ordre, 'systeme')"
    )
    par_ins = sa.text(
        "INSERT INTO type_parametres (type_activite_id, cle, source) "
        "VALUES (:tid, :cle, 'systeme')"
    )

    for tid, sous_types, params in rows:
        for i, libelle in enumerate(json.loads(sous_types or "[]")):
            bind.execute(prec_ins, {"tid": tid, "libelle": libelle, "ordre": i})
        for cle in json.loads(params or "[]"):
            bind.execute(par_ins, {"tid": tid, "cle": cle})


def downgrade():
    # A cette etape de l'historique les deux tables etaient VIDES (creees par la migration
    # precedente) : on les revide integralement pour revenir a cet etat.
    op.execute("DELETE FROM type_parametres")
    op.execute("DELETE FROM type_precisions")
