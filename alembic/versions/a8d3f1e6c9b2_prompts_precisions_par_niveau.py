"""Ajoute les prompts des PRECISIONS sur le referentiel : prompt, drapeau de relecture, meta.

07/08/2026. Quatrieme et dernier couple, jumeau exact de f4a2b6c8e5d1 (types) :
  - `prompt_precisions`        : le prompt qui LIT les precisions d'un type dans ce document ;
  - `prompt_precisions_valide` : l'admin l'a relu (le prompt SERT des qu'il existe) ;
  - `prompt_meta_precisions`   : la consigne qui sert a ECRIRE ce prompt-la.

Il n'en existait AUCUN par niveau : le seul texte etait le defaut du code (registre
`suggerer_precisions_type`), le meme pour une creche et pour un BTS. Le document etait pourtant
deja injecte — mais rien n'obligeait le modele a s'y tenir, d'ou des precisions plausibles et
inventees
plutot que tirees du vocabulaire du document.

REPLI CONSERVE : colonnes NULL = les reglages generaux servent, comme avant. Aucun niveau n'est
modifie par cette revision.
"""
from alembic import op
import sqlalchemy as sa


revision = "a8d3f1e6c9b2"
down_revision = "f4a2b6c8e5d1"
branch_labels = None
depends_on = None

# Le TEXTE est FIGE ici, jamais importe de `llm_prompts` (cf. tests/test_prompts_en_base.py) :
# une migration doit produire le meme resultat quel que soit le code deploye plus tard.
# Le dict s'appelle PROMPTS_MAJ : c'est le nom que la suite de tests reconnait pour verifier
# qu'aucun prompt du registre n'arrive en production sans avoir ete seme.
PROMPTS_MAJ = {
    "meta_precisions": """Tu prépares la lecture des PRÉCISIONS d'un type d'activité, dans un référentiel officiel, pour un logiciel pédagogique.

Une précision est une déclinaison CONCRÈTE d'un type d'activité, telle que le document la met en œuvre (pour un type « activités écrites » : ce que le référentiel demande réellement d'écrire), et non une idée générale de ce qui se pratique à ce niveau.

On te donne le TEXTE BRUT d'un référentiel (extrait d'un PDF), pris comme EXEMPLE de sa famille :
---
{document}
---

Ta tâche : RÉDIGER LE PROMPT qui, appliqué à un référentiel de cette famille et à UN type d'activité donné, en sortira les précisions de ce type. Tu ne nommes aucune précision toi-même.

Observe d'abord CE document : où les déclinaisons concrètes du travail apparaissent-elles ? Des tâches détaillées sous chaque activité, des productions attendues, des situations d'évaluation décrites, une liste de savoir-faire — chaque famille de référentiel a sa façon de faire. Décris ces repères concrets dans le prompt que tu rédiges, en reprenant les mots du document.

Le prompt que tu rédiges DOIT :
- viser la FAMILLE, pas cet exemplaire : un autre référentiel du même type doit pouvoir passer dedans (ne cite jamais une précision précise en exemple, ni un intitulé propre à ce document) ;
- dire OÙ regarder dans le document, avec les repères que tu viens d'observer ;
- s'en tenir à ce que le document nomme RÉELLEMENT, sans compléter par ce qui se pratique ailleurs dans l'enseignement ;
- reprendre le vocabulaire du document, jamais un vocabulaire inventé ;
- ne jamais répéter le nom du type dans la précision (le type est déjà connu) ;
- demander de 3 à 6 précisions, en libellés COURTS (2 à 4 mots), en minuscules ;
- contenir le marqueur {texte} à l'endroit où le texte du document sera inséré, EN TÊTE du prompt ;
- contenir le marqueur {label} à l'endroit où le nom du type d'activité sera inséré ;
- imposer une sortie JSON stricte : {"precisions":["...","..."]} et rien d'autre autour.

Réponds UNIQUEMENT par le texte du prompt, sans aucun commentaire autour.""",
}


# Le nouvel appel IA a sa ligne dans `outils_llm`, sinon l'ecran des longueurs ne le montre pas.
# La constante s'appelle OUTILS : conftest.py lit les migrations par ce nom pour monter la base
# de test — `outils_llm` n'a AUCUNE liste dans le code, c'est le sujet meme de cette table.
OUTILS = [
    ("meta_precisions",
     "Precisions — meta-prompt (redaction du prompt des precisions)",
     76,
     "Reponse attendue : le TEXTE d'un prompt, quelques milliers de caracteres. "
     "L'entree, elle, porte le referentiel entier."),
]


_SQL_SETTING = sa.text(
    "INSERT INTO settings (key, value) VALUES (:key, :value) "
    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
)


def upgrade() -> None:
    op.add_column("referentiels", sa.Column("prompt_precisions", sa.Text(), nullable=True))
    op.add_column("referentiels", sa.Column("prompt_precisions_valide", sa.Boolean(),
                                            nullable=False, server_default="0"))
    op.add_column("referentiels", sa.Column("prompt_meta_precisions", sa.Text(), nullable=True))

    conn = op.get_bind()
    # Le meta-prompt GENERAL : sans lui, `generer_prompt_precisions` leve des le premier appel.
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(_SQL_SETTING, {"key": f"prompt_{cle}", "value": texte})
    for outil, libelle, ordre, aide in OUTILS:
        conn.execute(sa.text(
            "INSERT INTO outils_llm (outil, libelle, aide, ordre) "
            "VALUES (:outil, :libelle, :aide, :ordre) ON CONFLICT (outil) DO NOTHING"
        ), {"outil": outil, "libelle": libelle, "aide": aide, "ordre": ordre})


def downgrade() -> None:
    conn = op.get_bind()
    for outil, _l, _o, _a in OUTILS:
        conn.execute(sa.text("DELETE FROM outils_llm WHERE outil = :o"), {"o": outil})
    for cle in PROMPTS_MAJ:
        conn.execute(sa.text("DELETE FROM settings WHERE key = :k"), {"k": f"prompt_{cle}"})
    op.drop_column("referentiels", "prompt_meta_precisions")
    op.drop_column("referentiels", "prompt_precisions_valide")
    op.drop_column("referentiels", "prompt_precisions")
