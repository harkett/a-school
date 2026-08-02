# -*- coding: utf-8 -*-
"""adopte au registre les 3 prompts consommes par replace (meta/verif decoupe, gabarit type)

CE QUE CETTE MIGRATION REPARE. Trois prompts vivaient HORS du registre `PROMPTS` :

  - `prompt_meta_decoupe` : lu a chaque generation d un prompt de decoupe. Ses seules portes
    etaient GET/PUT /admin/referentiels/meta-prompt, qu AUCUN ecran n appelle.
  - `prompt_verif_decoupe` : lu a chaque decoupe lui aussi — et AUCUNE route ne permettait de
    le corriger. Ni ecran, ni endpoint : il etait semé une fois, puis intouchable.
  - `prompt_gabarit_type` : il FABRIQUE le prompt de chaque couple x type au coche. Il n avait
    pas de ligne en base du tout — seulement un repli code dans SETTING_DEFAULTS — donc aucune
    porte non plus. S il etait mauvais, la faute tombait chez le PROF, pas chez l admin.

Hors registre, ils echappaient a tout : l ecran Prompts ne les voyait pas, `valider_prompt` ne
les gardait pas, et rien ne verifiait qu une base neuve les contenait.

POURQUOI IL A FALLU UN CHAMP `mode`. Leur texte CASSE `.format()`, mesure sur le contenu reel :
KeyError 'texte' pour le meta-prompt, KeyError '"unites"' pour celui de critique. C est normal —
ils DECRIVENT un autre prompt, leurs accolades sont du texte a preserver. Ils sont consommes par
`str.replace`. Le registre porte donc `mode: "replace"`, et `valider_prompt` verifie alors la
PRESENCE des reperes sans jamais formater.

ON CONFLICT DO NOTHING, et c est un choix : cette migration ADOPTE, elle ne corrige pas. Les
deux premieres lignes existent deja (semees par b5c6d7e8f9a0, meme texte) ; ecraser risquerait
d effacer un texte qu un administrateur aurait affine. Seul `prompt_gabarit_type` est vraiment
cree ici — il n avait jamais eu de ligne.

Le TEXTE est FIGE ici, jamais importe de `llm_prompts` : une migration seme ce qu elle disait le
jour ou elle a ete ecrite (cf. tests/test_prompts_en_base.py). `PROMPTS_MAJ` est lu par ce test,
qui compose seed + mises a jour pour verifier que registre et base neuve concordent.

downgrade : retire la SEULE ligne que cette migration cree (`prompt_gabarit_type`). Les deux
autres appartiennent a b5c6d7e8f9a0, dont le downgrade s en charge — les effacer ici les
supprimerait deux fois et casserait un retour en arriere partiel.

Revision ID: d4f8a2b6c9e3
Revises: c1e7a3d9b2f4
Create Date: 2026-08-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4f8a2b6c9e3"
down_revision: Union[str, Sequence[str], None] = "c1e7a3d9b2f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Texte FIGE des 3 prompts adoptes (cle du registre -> texte).
PROMPTS_MAJ = {
    "meta_decoupe": """Tu prepares le decoupage d'un referentiel officiel pour un logiciel pedagogique.

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

Reponds UNIQUEMENT par le texte du prompt de decoupe, sans aucun commentaire autour.""",
    "verif_decoupe": """Tu es un relecteur exigeant. On te donne un PROMPT DE DÉCOUPE destiné à découper un référentiel en unités. Vérifie qu'il respecte STRICTEMENT ce contrat :

1. TITRES VERBATIM (priorité absolue) : le prompt doit exiger que chaque unité renvoie sa LIGNE DE TITRE EXACTEMENT telle qu'elle apparaît dans le document, mot pour mot, jamais reformulée ni résumée. C'est vital : le code retrouve ensuite chaque titre dans le texte réel pour trancher ; un titre paraphrasé fait perdre la frontière.
2. FORMAT JSON EXACT : le prompt doit imposer la sortie {"unites":[{"titre":"..."}]} — une clé "unites" contenant une liste d'objets à clé "titre", et rien d'autre.
3. PAS DE CONTENU : le prompt ne doit PAS demander le contenu, le déroulé ni le détail des unités. Le code reconstitue le contenu lui-même en tranchant le texte réel ; un contenu demandé à l'IA est du gaspillage de tokens (et serait jeté).
4. EXCLUSIONS : le prompt doit écarter ce qui n'est pas une unité (page de titre, introduction, avertissements, en-têtes de partie ou de section, notes, renvois, sources, attributions).

Si le prompt viole un ou plusieurs de ces points, RENVOIE une version CORRIGÉE du prompt qui les respecte tous. S'il les respecte déjà, renvoie-le INCHANGÉ.

Ne renvoie QUE le prompt (corrigé ou inchangé), sans commentaire, sans explication, sans balise de code.

PROMPT À VÉRIFIER :
{prompt}""",
    "gabarit_type": """Tu es un enseignant expérimenté.
Conçois une activité du type « {label} » adaptée à des élèves de {niveau}.

Pars de l'idée du professeur ci-dessous — garde son intention et son style, c'est elle qui mène :
{texte}

Appuie-toi sur le programme officiel ci-dessous pour cadrer et enrichir l'activité, sans t'en écarter :
{referentiel}

Rends une activité claire et directement exploitable (objectif, consigne, déroulé).""",
}

# La seule ligne que cette migration CREE : les deux autres existaient deja.
_CREEE_ICI = ("gabarit_type",)


def upgrade() -> None:
    conn = op.get_bind()
    for cle, texte in PROMPTS_MAJ.items():
        conn.execute(
            sa.text(
                "INSERT INTO settings (key, value) VALUES (:key, :value) "
                "ON CONFLICT (key) DO NOTHING"
            ),
            {"key": f"prompt_{cle}", "value": texte},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for cle in _CREEE_ICI:
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"),
                     {"key": f"prompt_{cle}"})
