# -*- coding: utf-8 -*-
"""les TYPES D'ACTIVITE deviennent propres au REFERENTIEL (comme les matieres)

CONSTAT. Un type d'activite est une donnee LUE DANS LE DOCUMENT, au meme titre qu'une matiere :
le referentiel dit quels formats de travail il met en oeuvre. Il vivait pourtant dans un
CATALOGUE GLOBAL (`types_activite`, partage creche -> doctorat), seme en dur par la migration
a1b2c3d4e5f6 (13 familles + un defaut), auquel chaque referentiel se raccrochait par une table
de liaison N-N (`referentiel_types_activite`).

Ce catalogue etait le vestige du temps ou la liste precedait les referentiels. Tout ce qui avait
du sens metier l'avait deja quitte : le PROMPT vivait sur la liaison (e5f6a7b8c9d0), et les
PRECISIONS avaient deja fait ce meme chemin depuis l'ancien catalogue global `type_precisions`
(supprime par dd44ee55ff66). Le seed etait ce qui forcait tout le reste du montage.

CE QUE CA CORRIGEAIT. La detection creait un type inconnu directement dans la table PARTAGEE,
sans clic, et le retrait ne le defaisait pas (decocher supprimait le lien, jamais le type) : le
catalogue ne faisait que grossir. Pire, son contenu etait injecte comme vocabulaire dans le
prompt de detection de TOUS les autres couples — le vocabulaire creche debordait sur le BTS.

CE QUE FAIT CETTE MIGRATION :
  - `cycles.prompt_types` / `prompt_types_valide` : la RECETTE (le prompt qui lit les types) monte
    au CYCLE, comme `prompt_matieres` et `prompt_decoupe`. La donnee au referentiel, la recette au
    cycle — chacune a son etage ;
  - `types_activite` gagne `referentiel_id` (CASCADE), `validee` (proposE par l'IA / RETENU par
    l'admin, comme `matieres.validee`) et `prompt` (descendu de la liaison) ; il perd `is_default` ;
  - chaque LIAISON existante devient UNE LIGNE de type, portee par son referentiel : 33 liaisons
    -> 33 types. `validee=true` pour toutes : ces types sont deja EN SERVICE chez les profs, les
    retrograder en propositions les ferait disparaitre de leurs menus. `origine` reprend la
    `source` du lien telle quelle ('ia' | 'admin' | 'systeme') — on ne reecrit pas l'histoire ;
  - les PRECISIONS pendent desormais sur le type (`type_activite_id`) et non plus sur la liaison ;
  - les ACTIVITES DEJA GENEREES sont repointees vers le type de LEUR referentiel, retrouve par
    (niveau, libelle). La migration LEVE si une seule ne trouve pas sa cible : casser
    l'historique d'un prof en silence serait pire que de s'arreter ;
  - la liaison est supprimee, les lignes du catalogue global aussi.

LE REPLI DU PROF. `is_default` servait le type « Activite d'apprentissage » quand un couple
n'avait rien coche. Il devient un LIBELLE DE SECOURS EN DUR (backend/contenu/activites.py) : il
ne perd rien, ce type n'avait de prompt pour aucun couple, donc il n'etait deja pas generable —
il ne servait que d'affichage.

Revision ID: e4a7c2b9d5f8
Revises: d4f6b8a0c2e3
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa


revision = "e4a7c2b9d5f8"
down_revision = "d4f6b8a0c2e3"
branch_labels = None
depends_on = None


# L'outil LLM que cette migration ajoute — MEME FORME que `OUTILS` de b4e8d2a6f1c9
# (outil, libelle, ordre, aide). Le nom de la constante est lu par conftest.py, qui compose la
# table `outils_llm` de la base de test depuis les migrations : la liste n'existe nulle part
# ailleurs dans le code, et la recopier en ferait une seconde source qui dériverait.
OUTILS = [
    ("meta_types", "Repérage des titres — types d'activité", 150,
     "Fait rédiger par l'IA le prompt qui lira les types d'activité du cycle. "
     "Sortie courte (un prompt)."),
]


def upgrade() -> None:
    conn = op.get_bind()

    # Garde : `few_shot_milestones` pointe lui aussi sur l'ancien catalogue. La table est vide au
    # jour de cette migration ; si elle ne l'etait pas, la suppression des lignes globales
    # echouerait sur sa cle etrangere — mieux vaut le dire ici que de le decouvrir en plein DROP.
    reste = conn.execute(sa.text("SELECT count(*) FROM few_shot_milestones")).scalar()
    if reste:
        raise RuntimeError(
            f"{reste} ligne(s) dans few_shot_milestones pointent vers l'ancien catalogue global "
            f"des types d'activite. Cette migration ne sait pas les rattacher a un referentiel : "
            f"traitez-les avant de la rejouer."
        )

    # 1. La RECETTE monte au cycle (la detection s'y raccordera ; NULL = repli sur le prompt general).
    op.add_column("cycles", sa.Column("prompt_types", sa.Text(), nullable=True))
    op.add_column("cycles", sa.Column("prompt_types_valide", sa.Boolean(), nullable=False,
                                      server_default="0"))
    # Le nouvel appel IA (`meta_types`) a sa ligne dans `outils_llm`, sinon l'ecran des longueurs
    # ne le montrerait pas — et tests/test_outils_llm_en_base.py le refuserait, a raison.
    for outil, libelle, ordre, aide in OUTILS:
        conn.execute(sa.text(
            "INSERT INTO outils_llm (outil, libelle, aide, ordre) "
            "VALUES (:outil, :libelle, :aide, :ordre) ON CONFLICT (outil) DO NOTHING"
        ), {"outil": outil, "libelle": libelle, "aide": aide, "ordre": ordre})

    # 2. Les colonnes du nouveau modele, d'abord permissives (les lignes globales existent encore).
    op.add_column("types_activite", sa.Column("referentiel_id", sa.Integer(), nullable=True))
    op.add_column("types_activite", sa.Column("validee", sa.Boolean(), nullable=False,
                                              server_default="false"))
    op.add_column("types_activite", sa.Column("prompt", sa.Text(), nullable=False,
                                              server_default=""))
    # Le defaut d'`origine` suit le nouveau modele : un type nait desormais d'une lecture du
    # document. 'systeme' reste une valeur LUE (les liens herites), plus une valeur ECRITE.
    op.alter_column("types_activite", "origine", server_default="ia")

    # 3. Une liaison = un type du referentiel. Boucle Python (33 lignes) plutot qu'un INSERT
    #    ... SELECT : il faut GARDER la correspondance lien -> nouveau type pour repointer les
    #    precisions juste apres, et un SQL qui la retrouverait apres coup devrait deviner.
    liens = conn.execute(sa.text(
        "SELECT l.id, l.referentiel_id, l.actif, l.source, l.ordre, l.prompt, t.label "
        "FROM referentiel_types_activite l "
        "JOIN types_activite t ON t.id = l.activite_type_id "
        "ORDER BY l.referentiel_id, l.ordre, l.id"
    )).fetchall()

    type_par_lien: dict[int, int] = {}
    for lien in liens:
        type_par_lien[lien.id] = conn.execute(sa.text(
            "INSERT INTO types_activite "
            "  (referentiel_id, label, actif, validee, ordre, origine, prompt) "
            "VALUES (:ref, :label, :actif, true, :ordre, :origine, :prompt) "
            "RETURNING id"
        ), {
            "ref": lien.referentiel_id,
            "label": lien.label,
            "actif": lien.actif,
            "ordre": lien.ordre,
            "origine": lien.source,
            "prompt": lien.prompt or "",
        }).scalar()

    # 4. Les precisions descendent de la liaison sur le type.
    op.add_column("referentiel_type_precisions",
                  sa.Column("type_activite_id", sa.Integer(), nullable=True))
    for lien_id, type_id in type_par_lien.items():
        conn.execute(sa.text(
            "UPDATE referentiel_type_precisions SET type_activite_id = :t "
            "WHERE referentiel_activite_type_id = :l"
        ), {"t": type_id, "l": lien_id})
    orphelines = conn.execute(sa.text(
        "SELECT count(*) FROM referentiel_type_precisions WHERE type_activite_id IS NULL"
    )).scalar()
    if orphelines:
        raise RuntimeError(
            f"{orphelines} precision(s) sans type d'accueil apres l'eclatement des liaisons. "
            f"La migration s'arrete plutot que de les perdre."
        )
    op.drop_constraint("uq_ref_type_precisions_lien_libelle", "referentiel_type_precisions",
                       type_="unique")
    op.drop_column("referentiel_type_precisions", "referentiel_activite_type_id")
    op.alter_column("referentiel_type_precisions", "type_activite_id", nullable=False)
    op.create_index("ix_referentiel_type_precisions_type_activite_id",
                    "referentiel_type_precisions", ["type_activite_id"])
    op.create_foreign_key("referentiel_type_precisions_type_activite_id_fkey",
                          "referentiel_type_precisions", "types_activite",
                          ["type_activite_id"], ["id"], ondelete="CASCADE")
    op.create_unique_constraint("uq_ref_type_precisions_type_libelle",
                                "referentiel_type_precisions", ["type_activite_id", "libelle"])

    # 5. Les activites deja generees suivent leur referentiel. Le couple (niveau, libelle) est ce
    #    que la ligne d'activite porte deja : `activite_label` y est fige depuis c5d6e7f8a9b0.
    for a in conn.execute(sa.text(
        "SELECT id, activite_label, niveau FROM activites ORDER BY id"
    )).fetchall():
        cible = conn.execute(sa.text(
            "SELECT t.id FROM types_activite t "
            "JOIN referentiels r ON r.id = t.referentiel_id "
            "JOIN niveaux n ON n.id = r.niveau_id "
            "WHERE t.referentiel_id IS NOT NULL "
            "  AND n.nom = :niveau AND lower(t.label) = lower(:label) "
            "LIMIT 1"
        ), {"niveau": a.niveau or "", "label": a.activite_label}).scalar()
        if cible is None:
            raise RuntimeError(
                f"L'activite {a.id} (« {a.activite_label} », niveau « {a.niveau} ») ne retrouve "
                f"pas son type dans le referentiel de ce niveau. La migration s'arrete : "
                f"repointer au hasard casserait l'historique de ce professeur."
            )
        conn.execute(sa.text("UPDATE activites SET activite_type_id = :t WHERE id = :a"),
                     {"t": cible, "a": a.id})

    # 6. L'ancien monde s'en va : la liaison, puis les lignes du catalogue global.
    op.drop_table("referentiel_types_activite")
    conn.execute(sa.text("DELETE FROM types_activite WHERE referentiel_id IS NULL"))
    op.drop_index("ux_default", table_name="types_activite")
    op.drop_column("types_activite", "is_default")

    # 7. Le nouveau modele se referme : plus un seul type sans referentiel, un libelle unique par
    #    referentiel (l'anti-doublon de `matieres`, transpose).
    op.alter_column("types_activite", "referentiel_id", nullable=False)
    op.create_index("ix_types_activite_referentiel_id", "types_activite", ["referentiel_id"])
    op.create_foreign_key("types_activite_referentiel_id_fkey", "types_activite", "referentiels",
                          ["referentiel_id"], ["id"], ondelete="CASCADE")
    op.create_unique_constraint("uq_types_activite_referentiel_label", "types_activite",
                                ["referentiel_id", "label"])


def downgrade() -> None:
    """Remonte un catalogue global (un type par libelle distinct) et la liaison qui l'accrochait
    aux referentiels. Les prompts et precisions retournent sur la liaison. Ce qui ne peut pas
    revenir : `validee` (le catalogue n'avait pas la notion) et le defaut `is_default`, qui est
    repose sur « Activite d'apprentissage » s'il existe encore quelque part."""
    conn = op.get_bind()

    op.drop_constraint("uq_types_activite_referentiel_label", "types_activite", type_="unique")
    op.drop_constraint("types_activite_referentiel_id_fkey", "types_activite", type_="foreignkey")
    op.drop_index("ix_types_activite_referentiel_id", table_name="types_activite")
    op.add_column("types_activite", sa.Column("is_default", sa.Boolean(), nullable=False,
                                              server_default="false"))
    op.alter_column("types_activite", "referentiel_id", nullable=True)

    op.create_table(
        "referentiel_types_activite",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("referentiel_id", sa.Integer(),
                  sa.ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activite_type_id", sa.Integer(),
                  sa.ForeignKey("types_activite.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("referentiel_id", "activite_type_id", name="uq_ref_activite_type"),
    )
    op.create_index("ix_referentiel_types_activite_referentiel_id",
                    "referentiel_types_activite", ["referentiel_id"])
    op.create_index("ix_referentiel_types_activite_activite_type_id",
                    "referentiel_types_activite", ["activite_type_id"])

    # Un type global par libelle distinct, puis une liaison par ligne actuelle.
    global_par_label: dict[str, int] = {}
    lien_par_type: dict[int, int] = {}
    for t in conn.execute(sa.text(
        "SELECT id, referentiel_id, label, actif, ordre, origine, prompt FROM types_activite "
        "WHERE referentiel_id IS NOT NULL ORDER BY referentiel_id, ordre, id"
    )).fetchall():
        cle = t.label.lower()
        if cle not in global_par_label:
            global_par_label[cle] = conn.execute(sa.text(
                "INSERT INTO types_activite (label, actif, ordre, origine, is_default, prompt, "
                "                            referentiel_id, validee) "
                "VALUES (:label, true, :ordre, :origine, false, '', NULL, false) RETURNING id"
            ), {"label": t.label, "ordre": t.ordre, "origine": t.origine}).scalar()
        lien_par_type[t.id] = conn.execute(sa.text(
            "INSERT INTO referentiel_types_activite "
            "  (referentiel_id, activite_type_id, actif, source, ordre, prompt) "
            "VALUES (:ref, :type, :actif, :source, :ordre, :prompt) RETURNING id"
        ), {"ref": t.referentiel_id, "type": global_par_label[cle], "actif": t.actif,
            "source": t.origine, "ordre": t.ordre, "prompt": t.prompt or ""}).scalar()

    # Les activites repointent vers le type GLOBAL de meme libelle.
    conn.execute(sa.text(
        "UPDATE activites a SET activite_type_id = g.id "
        "FROM types_activite g "
        "WHERE g.referentiel_id IS NULL AND lower(g.label) = lower(a.activite_label)"
    ))

    # Les precisions remontent sur la liaison.
    op.add_column("referentiel_type_precisions",
                  sa.Column("referentiel_activite_type_id", sa.Integer(), nullable=True))
    for type_id, lien_id in lien_par_type.items():
        conn.execute(sa.text(
            "UPDATE referentiel_type_precisions SET referentiel_activite_type_id = :l "
            "WHERE type_activite_id = :t"
        ), {"l": lien_id, "t": type_id})
    op.drop_constraint("uq_ref_type_precisions_type_libelle", "referentiel_type_precisions",
                       type_="unique")
    op.drop_column("referentiel_type_precisions", "type_activite_id")
    op.alter_column("referentiel_type_precisions", "referentiel_activite_type_id", nullable=False)
    op.create_index("ix_referentiel_type_precisions_referentiel_activite_type_id",
                    "referentiel_type_precisions", ["referentiel_activite_type_id"])
    op.create_foreign_key("referentiel_type_precisions_referentiel_activite_type_id_fkey",
                          "referentiel_type_precisions", "referentiel_types_activite",
                          ["referentiel_activite_type_id"], ["id"], ondelete="CASCADE")
    op.create_unique_constraint("uq_ref_type_precisions_lien_libelle",
                                "referentiel_type_precisions",
                                ["referentiel_activite_type_id", "libelle"])

    # Les lignes par referentiel disparaissent, le catalogue global reste.
    conn.execute(sa.text("DELETE FROM types_activite WHERE referentiel_id IS NOT NULL"))
    conn.execute(sa.text(
        "UPDATE types_activite SET is_default = true WHERE id = ("
        "  SELECT id FROM types_activite WHERE lower(label) = 'activité d''apprentissage' LIMIT 1)"
    ))
    op.create_index("ux_default", "types_activite", ["is_default"], unique=True,
                    postgresql_where=sa.text("is_default"))
    op.drop_column("types_activite", "prompt")
    op.drop_column("types_activite", "validee")
    op.drop_column("types_activite", "referentiel_id")
    op.alter_column("types_activite", "origine", server_default="systeme")

    conn.execute(sa.text("DELETE FROM outils_llm WHERE outil = 'meta_types'"))
    op.drop_column("cycles", "prompt_types_valide")
    op.drop_column("cycles", "prompt_types")
