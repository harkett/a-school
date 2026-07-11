"""seed ai_modeles (3 modeles) + settings prompts de decoupe (meta + verif)

Ces donnees sont STRUCTURELLES : sans elles l'application ne fonctionne pas en
production. Elles voyagent donc dans une migration (regle CLAUDE.md « Penser au
deploiement »), jamais par un script jetable qui n'atteindrait que le miroir.

- ai_modeles : la table est creee VIDE par a4b5c6d7e8f9 ; sans lignes, AUCUN modele
  n'est selectionnable a l'ecran. On seed les 3 modeles offerts (2 Anthropic, 1 Groq),
  le `recommande` de chaque fournisseur affiche en premier.
- settings : `prompt_meta_decoupe` (l'IA GENERE le prompt de decoupe d'un document) et
  `prompt_verif_decoupe` (l'IA RELIT/CORRIGE ce prompt avant l'admin). Ni l'un ni l'autre
  n'a de defaut en dur dans SETTING_DEFAULTS -> sans eux, generer/verifier LEVE.

Idempotent et non destructif : `ON CONFLICT DO NOTHING` -> jamais de doublon, et jamais
d'ecrasement d'une valeur deja editee par l'admin (ex. un prompt affine en base).

Revision ID: b5c6d7e8f9a0
Revises: a4b5c6d7e8f9
Create Date: 2026-07-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b5c6d7e8f9a0"
down_revision: Union[str, Sequence[str], None] = "a4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Modeles LLM texte offerts a l'admin (id API exact = colonne `modele`).
_AI_MODELES = [
    {"fournisseur": "anthropic", "modele": "claude-sonnet-5", "label": "Claude Sonnet 5", "recommande": True, "actif": True, "ordre": 0},
    {"fournisseur": "anthropic", "modele": "claude-opus-4-8", "label": "Claude Opus 4.8", "recommande": False, "actif": True, "ordre": 1},
    {"fournisseur": "groq", "modele": "llama-3.3-70b-versatile", "label": "Llama 3.3 70B", "recommande": True, "actif": True, "ordre": 0},
]

# Meta-prompt : l'IA GENERE le prompt de decoupe sur mesure d'un document (marqueur {document}).
_PROMPT_META_DECOUPE = """
Tu prepares le decoupage d'un referentiel officiel pour un logiciel pedagogique.

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

Reponds UNIQUEMENT par le texte du prompt de decoupe, sans aucun commentaire autour.
""".strip()

# Meta-prompt de CRITIQUE : l'IA relit le prompt genere et le corrige (marqueur {prompt}).
_PROMPT_VERIF_DECOUPE = """
Tu es un relecteur exigeant. On te donne un PROMPT DE DÉCOUPE destiné à découper un référentiel en unités. Vérifie qu'il respecte STRICTEMENT ce contrat :

1. TITRES VERBATIM (priorité absolue) : le prompt doit exiger que chaque unité renvoie sa LIGNE DE TITRE EXACTEMENT telle qu'elle apparaît dans le document, mot pour mot, jamais reformulée ni résumée. C'est vital : le code retrouve ensuite chaque titre dans le texte réel pour trancher ; un titre paraphrasé fait perdre la frontière.
2. FORMAT JSON EXACT : le prompt doit imposer la sortie {"unites":[{"titre":"..."}]} — une clé "unites" contenant une liste d'objets à clé "titre", et rien d'autre.
3. PAS DE CONTENU : le prompt ne doit PAS demander le contenu, le déroulé ni le détail des unités. Le code reconstitue le contenu lui-même en tranchant le texte réel ; un contenu demandé à l'IA est du gaspillage de tokens (et serait jeté).
4. EXCLUSIONS : le prompt doit écarter ce qui n'est pas une unité (page de titre, introduction, avertissements, en-têtes de partie ou de section, notes, renvois, sources, attributions).

Si le prompt viole un ou plusieurs de ces points, RENVOIE une version CORRIGÉE du prompt qui les respecte tous. S'il les respecte déjà, renvoie-le INCHANGÉ.

Ne renvoie QUE le prompt (corrigé ou inchangé), sans commentaire, sans explication, sans balise de code.

PROMPT À VÉRIFIER :
{prompt}
""".strip()


def upgrade() -> None:
    conn = op.get_bind()

    # ai_modeles : 3 lignes, jamais de doublon (unique fournisseur+modele).
    for m in _AI_MODELES:
        conn.execute(
            sa.text(
                "INSERT INTO ai_modeles (fournisseur, modele, label, recommande, actif, ordre) "
                "VALUES (:fournisseur, :modele, :label, :recommande, :actif, :ordre) "
                "ON CONFLICT (fournisseur, modele) DO NOTHING"
            ),
            m,
        )

    # settings : les 2 prompts de decoupe. ON CONFLICT (key) DO NOTHING : ne jamais
    # ecraser une valeur deja editee par l'admin en base.
    for key, value in (
        ("prompt_meta_decoupe", _PROMPT_META_DECOUPE),
        ("prompt_verif_decoupe", _PROMPT_VERIF_DECOUPE),
    ):
        conn.execute(
            sa.text(
                "INSERT INTO settings (key, value) VALUES (:key, :value) "
                "ON CONFLICT (key) DO NOTHING"
            ),
            {"key": key, "value": value},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM settings WHERE key IN ('prompt_meta_decoupe', 'prompt_verif_decoupe')")
    )
    for m in _AI_MODELES:
        conn.execute(
            sa.text("DELETE FROM ai_modeles WHERE fournisseur = :fournisseur AND modele = :modele"),
            {"fournisseur": m["fournisseur"], "modele": m["modele"]},
        )
