# -*- coding: utf-8 -*-
"""prompts des TYPES D'ACTIVITE : plus de catalogue commun, et un meta-prompt par cycle

Suite directe de e4a7c2b9d5f8, qui vient de rendre les types propres au referentiel. Deux textes
a mettre en base :

  - `detecter_types_activite` recevait le catalogue de l'application ({types_existants}) pour
    ramener le document a un vocabulaire commun. Ce catalogue n'existe plus : chaque referentiel
    possede SES types, nommes comme le document les nomme. Le prompt ne recoit donc plus que
    {texte} — exactement ce qui a ete fait pour les matieres par a7c4e1b9d3f5 ;
  - `meta_types` est NOUVEAU : la RECETTE monte au cycle, il faut donc le meta-prompt qui la fait
    ecrire par l'IA au premier referentiel de la famille. Meme geste que `meta_matieres` et
    `meta_decoupe`, mode « replace » (le prompt redige porte {texte} et un exemple JSON).

POURQUOI UNE MIGRATION, ET PAS SEULEMENT LE REGISTRE. Les prompts VIVENT EN BASE (settings) et
`get_prompt` n'a plus de repli code : c'est la ligne en base que le serveur envoie a l'IA. Sans
cette mise a jour, la base garderait un {types_existants} que plus personne ne remplit — l'IA
recevrait ce repere en clair au milieu de sa consigne — et `meta_types` n'existerait nulle part.

ECRASEMENT ASSUME pour `detecter_types_activite` : la ligne est reecrite quelle que soit sa
valeur, y compris retouchee par l'admin. Tout texte qui porte encore {types_existants} est casse
(repere orphelin), et le garde-fou d'ecriture refuserait desormais de l'enregistrer.

Le TEXTE est FIGE ici, jamais importe de `llm_prompts` (cf. tests/test_prompts_en_base.py).

downgrade : remet le texte d'origine, avec son {types_existants}, et retire `meta_types`.

Revision ID: f5b8d3c1a9e7
Revises: e4a7c2b9d5f8
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa


revision = "f5b8d3c1a9e7"
down_revision = "e4a7c2b9d5f8"
branch_labels = None
depends_on = None


PROMPTS_MAJ = {
    "detecter_types_activite": """Tu lis un référentiel officiel et tu en dégages la liste des TYPES D'ACTIVITÉ (formats ou modalités d'activité pédagogique) qu'il met en œuvre à ce niveau.

Texte du référentiel :
{texte}

Ta tâche :
- Repère les types d'activité, formats ou modalités de travail que ce référentiel met réellement en œuvre (par exemple : atelier, mise en situation, travaux pratiques, projet, évaluation — selon ce qui apparaît réellement).
- Donne le nom de chaque type TEL QU'IL RESSORT DU DOCUMENT : ses mots, son orthographe. Ce document met en œuvre SES formats de travail ; il n'existe aucune liste extérieure à laquelle les ramener, et aucun libellé à normaliser.
- Garde des libellés courts et lisibles : le nom du type, pas une phrase ni un intitulé de chapitre.

Règle :
- "types" : la liste des libellés de types d'activité, sans doublon.
- N'invente aucun type absent du document. Si aucun n'apparaît clairement, renvoie une liste vide.

Réponds UNIQUEMENT en JSON, avec exactement cette clé : types (un tableau de chaînes).""",

    "meta_types": """Tu prépares la lecture des TYPES D'ACTIVITÉ d'un référentiel officiel pour un logiciel pédagogique.

Un type d'activité est un FORMAT de travail que le document met en œuvre (atelier, mise en situation, travaux pratiques, projet, évaluation…), pas une matière ni une compétence.

On te donne le TEXTE BRUT d'un référentiel (extrait d'un PDF), pris comme EXEMPLE de sa famille :
---
{document}
---

Ta tâche : RÉDIGER LE PROMPT qui, appliqué à un référentiel de cette famille, en sortira la liste COMPLÈTE des types d'activité qu'il met en œuvre. Tu ne nommes aucun type toi-même.

Observe d'abord CE document : où ses formats de travail apparaissent-ils ? Des modalités décrites dans les unités, un tableau d'activités professionnelles, des verbes de mise en œuvre répétés, une partie « démarche pédagogique » — chaque famille de référentiel a sa façon de faire. Décris ces repères concrets dans le prompt que tu rédiges, en reprenant les mots du document.

Le prompt que tu rédiges DOIT :
- viser la FAMILLE, pas cet exemplaire : un autre référentiel du même type doit pouvoir passer dedans (ne cite jamais un type précis en exemple, ni un intitulé propre à ce document) ;
- dire OÙ regarder dans le document, avec les repères que tu viens d'observer ;
- s'en tenir aux formats RÉELLEMENT mis en œuvre par le document, sans compléter par ce qui se pratique ailleurs dans l'enseignement ;
- demander des libellés COURTS et lisibles (le nom du format, pas une phrase), avec les mots du document ;
- écarter ce qui n'est pas un format de travail : matières, compétences, savoirs, blocs de certification ;
- contenir le marqueur {texte} à l'endroit où le texte du document sera inséré ;
- imposer une sortie JSON stricte : {"types":["...","..."]} et rien d'autre autour.

Réponds UNIQUEMENT par le texte du prompt, sans aucun commentaire autour.""",
}


# Texte FIGE d'AVANT (downgrade) — celui seme par b8e5f2a1c9d7, avec son catalogue commun.
_AVANT = {
    "detecter_types_activite": """Tu lis un référentiel officiel et tu en dégages la liste des TYPES D'ACTIVITÉ (formats ou modalités d'activité pédagogique) qu'il met en œuvre à ce niveau.

Types d'activité déjà connus de l'application :
{types_existants}

Texte du référentiel :
{texte}

Ta tâche :
- Repère les types d'activité, formats ou modalités de travail que ce référentiel met réellement en œuvre (par exemple : atelier, mise en situation, travaux pratiques, projet, évaluation — selon ce qui apparaît réellement).
- Fais CORRESPONDRE ce que tu lis avec les types déjà connus :
  - Si ce que tu lis correspond à un type déjà connu, reprends EXACTEMENT le libellé de la liste (même orthographe, mêmes majuscules), pas la formulation du document.
  - Si ce que tu lis ne correspond à aucun type connu, donne son nom tel qu'il ressort du document, court et lisible (le nom du type, pas une phrase).

Règle :
- "types" : la liste des libellés de types d'activité, sans doublon.
- N'invente aucun type absent du document : la liste des types connus sert à faire correspondre, jamais à ajouter un type que le document ne met pas en œuvre. Si aucun n'apparaît clairement, renvoie une liste vide.

Réponds UNIQUEMENT en JSON, avec exactement cette clé : types (un tableau de chaînes).""",
}


_SQL = sa.text(
    "INSERT INTO settings (key, value) VALUES (:key, :value) "
    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
)


def upgrade() -> None:
    conn = op.get_bind()
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(_SQL, {"key": f"prompt_{cle}", "value": texte})


def downgrade() -> None:
    conn = op.get_bind()
    for cle, texte in _AVANT.items():
        conn.execute(_SQL, {"key": f"prompt_{cle}", "value": texte})
    conn.execute(sa.text("DELETE FROM settings WHERE key = 'prompt_meta_types'"))
