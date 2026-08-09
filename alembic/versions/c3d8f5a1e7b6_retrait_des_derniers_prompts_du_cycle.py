"""Retrait de `cycles.prompt_decoupe` et `cycles.prompt_types` : le cycle ne porte plus de prompt.

06/08/2026, suite et fin de la revision b7e1c4d9a3f2 (qui avait retire `cycles.prompt_matieres`).
Les trois prompts — matieres, decoupe, types — appartiennent au REFERENTIEL, un jeu par couple
cycle+niveau. Le cycle « BTS » porte dix-huit diplomes : ce qui est ecrit pour l'un n'apprend rien
sur l'autre.

RECOPIE AVANT SUPPRESSION, pour la decoupe uniquement. Ici, contrairement aux matieres, le prompt
du cycle est celui qui SERVAIT REELLEMENT hier encore : les referentiels portaient, eux, de vieux
prompts par couple, perimes depuis que la decoupe etait montee au cycle le 05/08. Les laisser en
place ferait REGRESSER la decoupe — un referentiel deja decoupe repartirait sur un texte plus
ancien que celui qui a produit ses unites. On ecrase donc, pour chaque referentiel, le prompt du
couple par celui de son cycle. Le resultat d'un « Decouper » ne change pas : c'est exactement le
texte qui aurait servi ce matin. Seul l'endroit ou il est range change.

Un referentiel dont le cycle n'a pas de prompt de decoupe garde le sien (cas de la Creche : son
prompt par couple est le seul qui ait jamais existe pour lui).

`cycles.prompt_types` est vide partout : rien a recopier.

`downgrade()` recree les colonnes VIDES. Les textes, eux, restent sur les referentiels — ils y
sont desormais chez eux.
"""
from alembic import op
import sqlalchemy as sa


revision = "c3d8f5a1e7b6"
down_revision = "b7e1c4d9a3f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Le prompt de decoupe du cycle descend sur CHAQUE referentiel de ce cycle, drapeau compris.
    op.execute("""
        UPDATE referentiels r
           SET prompt_decoupe = c.prompt_decoupe,
               prompt_decoupe_valide = c.prompt_decoupe_valide
          FROM niveaux n, cycles c
         WHERE r.niveau_id = n.id
           AND n.cycle_id = c.id
           AND coalesce(btrim(c.prompt_decoupe), '') <> ''
    """)
    op.drop_column("cycles", "prompt_types_valide")
    op.drop_column("cycles", "prompt_types")
    op.drop_column("cycles", "prompt_decoupe_valide")
    op.drop_column("cycles", "prompt_decoupe")


def downgrade() -> None:
    op.add_column("cycles", sa.Column("prompt_decoupe", sa.Text(), nullable=True))
    op.add_column("cycles", sa.Column("prompt_decoupe_valide", sa.Boolean(),
                                      nullable=False, server_default="0"))
    op.add_column("cycles", sa.Column("prompt_types", sa.Text(), nullable=True))
    op.add_column("cycles", sa.Column("prompt_types_valide", sa.Boolean(),
                                      nullable=False, server_default="0"))
