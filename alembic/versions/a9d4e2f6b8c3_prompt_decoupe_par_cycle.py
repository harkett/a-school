# -*- coding: utf-8 -*-
"""Le prompt de DECOUPE devient propre au CYCLE, comme celui des matieres

Constat (BTS CIEL, 05/08/2026) : le prompt de decoupe etait ecrit POUR UN DOCUMENT. Son titre
disait « Referentiel BTS Cybersecurite, Informatique et reseaux, Electronique », ses reperes
citaient « Activite R1 », « C0X » — et ce dernier motif, borne a un chiffre, ratait C10 et C11.
Chaque referentiel depose demandait donc une generation IA + une relecture humaine, et repartait
avec les memes defauts.

Or l'ossature decrite par ce prompt (activites, competences, unites certificatives, ce qu'on
ecarte) est celle de TOUS les BTS. Ce qui etait propre au document n'etait pas la regle, seulement
les exemples. Cette migration range donc le prompt de decoupe la ou il vit vraiment : sur le
CYCLE — une famille de documents batis pareil — exactement comme `prompt_matieres`.

Ce que fait cette migration :
  - `cycles.prompt_decoupe` : le prompt de decoupe du cycle (NULL = pas encore ecrit) ;
  - `cycles.prompt_decoupe_valide` : false tant que l'admin ne l'a pas relu. Comme pour les
    matieres, le prompt SERT des qu'il existe : ce drapeau dit seulement s'il a ete relu ;
  - reecrit `prompt_meta_decoupe` : il demandait un prompt « sur mesure pour CE document precis »
    — c'etait la cause de la specialisation. Il demande desormais un prompt qui vise la FAMILLE,
    decrit des FORMES et non des identifiants, ne borne aucune serie de codes, et ecarte PAR
    NATURE plutot que par numero d'annexe.

Les colonnes `referentiels.prompt_decoupe` / `prompt_decoupe_valide` ne sont PAS supprimees :
elles gardent l'historique des couples deja traites. La decoupe, elle, lit le cycle.

Le TEXTE du meta-prompt est FIGE ici, jamais importe de `llm_prompts` : une migration doit semer
ce qu'elle disait le jour ou elle a ete ecrite (cf. tests/test_prompts_en_base.py).

Revision ID: a9d4e2f6b8c3
Revises: f7c2e8a4d6b1
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa

revision = "a9d4e2f6b8c3"
down_revision = "f7c2e8a4d6b1"
branch_labels = None
depends_on = None


# L'ANCIEN texte, remis tel quel par le downgrade (il demandait un prompt par document).
META_DECOUPE_AVANT = """Tu prepares le decoupage d'un referentiel officiel pour un logiciel pedagogique.

On te donne le TEXTE BRUT d'un referentiel (extrait d'un PDF) :
---
{document}
---

Ta mission : REDIGER un PROMPT de decoupe sur mesure pour CE document precis. Ce prompt sera ensuite donne a une IA pour qu'elle decoupe le document en ne gardant QUE ses vraies unites de contenu (les elements concrets et decrits que l'utilisateur exploitera : activites, fiches, competences... selon ce que contient ce document), et en ecartant tout le texte qui les entoure (page de titre, avertissements, introduction, mode d'emploi, en-tetes de partie ou de section, notes, renvois, listes de simples mentions, sources et attribution).

Le prompt que tu rediges DOIT :
- etre adapte a la structure reelle de CE document : nomme les reperes concrets que tu observes (comment une vraie unite de contenu se presente ici ; ce qui n'est que du texte d'entourage) ;
- demander, pour chaque unite retenue, UNIQUEMENT sa ligne de titre recopiee exactement telle qu'elle apparait dans le texte ;
- contenir le marqueur {texte} a l'endroit ou le texte brut du document sera insere ;
- imposer une sortie JSON stricte : {"unites":[{"titre":"..."}]} et rien d'autre autour.

Reponds UNIQUEMENT par le texte du prompt de decoupe, sans aucun commentaire autour."""


PROMPTS_MAJ = {
    "meta_decoupe": """Tu prépares le découpage des référentiels d'une FAMILLE de diplômes pour un logiciel pédagogique.

On te donne le TEXTE BRUT d'un référentiel (extrait d'un PDF), pris comme EXEMPLE de sa famille :
---
{document}
---

Ta mission : RÉDIGER LE PROMPT qui découpera N'IMPORTE QUEL référentiel de cette famille. Ce prompt sera ensuite donné à une IA pour qu'elle ne garde QUE les vraies unités de contenu (les éléments concrets et décrits que l'utilisateur exploitera : activités, compétences, unités certificatives, fiches… selon ce que contient cette famille de documents), et écarte tout le texte qui les entoure (page de titre, sommaire, avertissements, introductions, mode d'emploi, en-têtes de partie ou de section, notes, renvois, listes de simples mentions, sources et attribution).

Observe d'abord CE document : comment une vraie unité de contenu s'y présente-t-elle ? Décris ces repères dans le prompt que tu rédiges — mais décris-les comme des FORMES, pas comme les identifiants de cet exemplaire.

Le prompt que tu rédiges DOIT :
- viser la FAMILLE, pas cet exemplaire : un autre référentiel du même type doit pouvoir passer dedans, sans jamais nommer la spécialité de celui-ci ;
- décrire des FORMES, pas des codes précis : « ligne commençant par « Activité » suivi d'un identifiant » plutôt que « Activité R1 ». Si tu donnes un code en exemple, présente-le comme un exemple parmi d'autres, jamais comme la règle ;
- ne borner AUCUNE série : un code peut compter un ou plusieurs chiffres et changer de forme d'une spécialité à l'autre (C01 à C09 mais aussi C10, C11, C12…, ou C1.2, CP3…). Le prompt doit exiger la série entière — un motif borné à un chiffre laisse tomber les unités suivantes ;
- désigner ce qu'on écarte PAR NATURE (règlement d'examen, grille horaire, tableaux de correspondance ancien/nouveau diplôme, tableaux de synthèse, dispenses, modalités administratives), jamais par numéro d'annexe ou de section : la numérotation change d'un document à l'autre ;
- prévoir les documents à plusieurs options sans les supposer : formuler les consignes qui les concernent de façon conditionnelle, inoffensive pour un document mono-option ;
- demander, pour chaque unité retenue, UNIQUEMENT sa ligne de titre recopiée EXACTEMENT telle qu'elle apparaît dans le texte — jamais son contenu, son déroulé ni son détail ;
- contenir le marqueur {texte} à l'endroit où le texte brut du document sera inséré ;
- imposer une sortie JSON stricte : {"unites":[{"titre":"..."}]} et rien d'autre autour.

Réponds UNIQUEMENT par le texte du prompt de découpe, sans aucun commentaire autour.""",
}

_SQL = sa.text(
    "INSERT INTO settings (key, value) VALUES (:key, :value) "
    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
)


def upgrade() -> None:
    op.add_column("cycles", sa.Column("prompt_decoupe", sa.Text(), nullable=True))
    op.add_column("cycles", sa.Column("prompt_decoupe_valide", sa.Boolean(), nullable=False,
                                      server_default="0"))
    conn = op.get_bind()
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(_SQL, {"key": f"prompt_{cle}", "value": texte})


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(_SQL, {"key": "prompt_meta_decoupe", "value": META_DECOUPE_AVANT})
    op.drop_column("cycles", "prompt_decoupe_valide")
    op.drop_column("cycles", "prompt_decoupe")
