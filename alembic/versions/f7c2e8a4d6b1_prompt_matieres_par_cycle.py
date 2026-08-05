# -*- coding: utf-8 -*-
"""Le prompt de lecture des MATIERES devient propre au CYCLE, ecrit par l'IA et valide par l'admin

Constat (BTS CIEL, 88 pages) : le prompt unique `detecter_matieres`, ecrit d'avance pour tous les
referentiels, rendait 6 matieres sur les 12 de la grille horaire. Un referentiel de BTS n'a rien a
voir avec un programme de college, encore moins avec un referentiel de creche : un seul prompt ne
peut pas lire correctement les trois.

La decoupe reglait deja ce probleme avec un META-prompt : l'IA lit le document et REDIGE le prompt
qui le decoupera, l'admin le relit et le valide. Les matieres se contentaient d'un prompt fige.
Cette migration leur donne le meme geste, range au niveau du CYCLE : un cycle = une famille de
documents batis pareil, donc le prompt ecrit sur le premier BTS sert a tous les BTS.

Ce que fait cette migration :
  - `cycles.prompt_matieres` : le prompt du cycle (NULL = pas encore ecrit) ;
  - `cycles.prompt_matieres_valide` : false tant que l'admin ne l'a pas relu — non valide, il ne
    sert PAS et la detection retombe sur le prompt general (aucune regression) ;
  - seme `prompt_meta_matieres` : le meta-prompt qui fait REDIGER le prompt du cycle.

Le TEXTE du meta-prompt est FIGE ici, jamais importe de `llm_prompts` : une migration doit semer
ce qu'elle disait le jour ou elle a ete ecrite (cf. tests/test_prompts_en_base.py).

Revision ID: f7c2e8a4d6b1
Revises: e5a1c3d7b9f2
Create Date: 2026-08-04
"""
from alembic import op
import sqlalchemy as sa

revision = "f7c2e8a4d6b1"
down_revision = "e5a1c3d7b9f2"
branch_labels = None
depends_on = None


PROMPTS_MAJ = {
    "meta_matieres": """Tu prépares la lecture des MATIÈRES d'un référentiel officiel pour un logiciel pédagogique.

On te donne le TEXTE BRUT d'un référentiel (extrait d'un PDF), pris comme EXEMPLE de sa famille :
---
{document}
---

Ta tâche : RÉDIGER LE PROMPT qui, appliqué à un référentiel de cette famille, en sortira la liste COMPLÈTE de ses matières. Tu ne listes aucune matière toi-même.

Observe d'abord CE document : où ses matières sont-elles énumérées ? Un tableau d'horaires, une liste d'unités, une suite de domaines, des titres de parties — chaque famille de référentiel a sa façon de faire. Décris ces repères concrets dans le prompt que tu rédiges, en reprenant les mots du document.

Le prompt que tu rédiges DOIT :
- viser la FAMILLE, pas cet exemplaire : un autre référentiel du même type doit pouvoir passer dedans (ne cite jamais une matière précise en exemple, ni un intitulé propre à ce document) ;
- dire OÙ regarder dans le document, avec les repères que tu viens d'observer ;
- exiger la liste ENTIÈRE de l'endroit repéré, ligne à ligne, y compris les sous-lignes, les enseignements secondaires et les options facultatives — ne rien laisser de côté sous prétexte que c'est un détail ;
- écarter ce qui ne concerne pas le référentiel visé : autre option du même diplôme, autre niveau, tableaux de correspondance avec un ancien programme ;
- demander le nom de chaque matière TEL QU'IL APPARAÎT dans le document (orthographe, majuscules, accents), sans le normaliser ni le reformuler ;
- demander une relecture avant de répondre : toute ligne de l'endroit repéré a-t-elle été reprise ?
- contenir le marqueur {texte} à l'endroit où le texte du document sera inséré ;
- imposer une sortie JSON stricte : {"matieres":["...","..."]} et rien d'autre autour.

Réponds UNIQUEMENT par le texte du prompt, sans aucun commentaire autour.""",
}

_SQL = sa.text(
    "INSERT INTO settings (key, value) VALUES (:key, :value) "
    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
)


def upgrade() -> None:
    op.add_column("cycles", sa.Column("prompt_matieres", sa.Text(), nullable=True))
    op.add_column("cycles", sa.Column("prompt_matieres_valide", sa.Boolean(), nullable=False,
                                      server_default="0"))
    conn = op.get_bind()
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(_SQL, {"key": f"prompt_{cle}", "value": texte})


def downgrade() -> None:
    conn = op.get_bind()
    for cle in list(PROMPTS_MAJ):
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {"key": f"prompt_{cle}"})
    op.drop_column("cycles", "prompt_matieres_valide")
    op.drop_column("cycles", "prompt_matieres")
