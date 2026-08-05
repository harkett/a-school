# -*- coding: utf-8 -*-
"""Remonte {texte} en tete des prompts de decoupe DEJA generes

POURQUOI. Les cinq autres outils qui lisent un referentiel entier profitent depuis peu du cache de
prompt du fournisseur : le document, place en tete de la requete, devient un prefixe commun que
seul le premier appel paie plein tarif (-51 % mesure). La DECOUPE, elle, restait au plein tarif —
alors que c'est l'appel LE PLUS CHER du logiciel (~70 000 tokens d'entree).

La raison n'est pas dans le code : le prompt de decoupe n'est pas ecrit a la main, il est REDIGE
par l'IA a partir du document, puis relu et valide par l'admin. Le meta-prompt ne demandait que la
PRESENCE du marqueur `{texte}`, pas sa position — l'IA le placait donc la ou il tombe naturellement
en francais, tout a la fin. Mesure du 05/08/2026 sur les quatre prompts existants : position ~4 000
sur ~4 020 caracteres. Le meta-prompt exige desormais la premiere position (`fa1b5c9e7d24`), ce qui
regle le cas des prompts A VENIR. Cette migration-ci s'occupe de ceux qui existent deja.

CE QU'ELLE FAIT, ET RIEN D'AUTRE : elle DEPLACE. Pas un mot des consignes n'est reecrit, ajoute ou
retire. `{texte}` remonte en premiere ligne, la phrase qui l'annoncait (« Voici le texte a
traiter : ») disparait puisqu'elle n'annonce plus rien, et les consignes suivent derriere un
separateur. C'est aussi la forme recommandee pour un long document : la matiere d'abord, la
question ensuite.

L'ENVELOPPE MARKDOWN. Deux des quatre prompts sont enveloppes en entier dans un bloc de code
(``` en position 0, ``` a la fin) : une bavure de redaction, l'IA ayant rendu son prompt « en bloc
de code » au lieu de le rendre brut. Elle etait sans consequence jusqu'ici. Elle en a une
maintenant : trois caracteres devant le document suffisent a detruire le prefixe commun, donc tout
le benefice. L'enveloppe est donc retiree — le contenu, lui, ne bouge pas d'un caractere.

GARDE-FOU. Un prompt n'est transforme QUE s'il se termine par un motif reconnu (une amorce connue,
puis `{texte}`, puis plus rien). Tout autre prompt est laisse EXACTEMENT tel quel : mieux vaut
manquer une economie que decouper au jugé un texte qu'un administrateur a relu et valide. Le
nombre de prompts touches est journalise.

downgrade : refait le chemin inverse (consignes, amorce, `{texte}` a la fin). L'enveloppe ```
n'est PAS remise : c'etait un artefact, pas une consigne.

Revision ID: fb2d6e8a4c19
Revises: fa1b5c9e7d24
Create Date: 2026-08-05
"""
import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fb2d6e8a4c19"
down_revision: Union[str, Sequence[str], None] = "fa1b5c9e7d24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

log = logging.getLogger("alembic.runtime.migration")

MARQUEUR = "{texte}"
SEPARATEUR = "\n\n---\n\n"

# Les phrases par lesquelles les prompts rediges annoncent le document. Liste EXPLICITE : une
# formulation inconnue laisse le prompt intact plutot que d'etre devinee.
AMORCES = (
    "Voici le texte à traiter :",
    "Voici le texte a traiter :",
    "Texte à traiter :",
    "Texte brut :",
    "Texte du référentiel :",
    "Texte du document :",
)

# Les colonnes qui portent un prompt de decoupe redige par l'IA.
CIBLES = (("cycles", "prompt_decoupe"), ("referentiels", "prompt_decoupe"))


def _sans_enveloppe(p: str) -> str:
    """Retire le bloc de code markdown qui entoure parfois le prompt ENTIER (cf. l'en-tete).
    N'intervient que si le texte commence ET finit par ``` : un prompt qui contient des blocs de
    code a l'interieur (l'exemple JSON) n'est pas concerne."""
    t = p.strip()
    if not (t.startswith("```") and t.endswith("```") and len(t) > 6):
        return p
    corps = t[3:-3]
    # ```json au lieu de ``` : on enleve aussi le mot de langage colle a l'ouverture.
    if corps[:1] not in ("\n", "\r"):
        corps = corps.split("\n", 1)[1] if "\n" in corps else corps
    return corps.strip()


def _en_tete(p: str) -> str | None:
    """Le prompt avec `{texte}` remonte en premiere position, ou None si le motif n'est pas reconnu."""
    p = _sans_enveloppe(p)
    i = p.find(MARQUEUR)
    if i < 0 or p[i + len(MARQUEUR):].strip():
        return None            # marqueur absent, ou suivi d'autre chose que du blanc
    if p.startswith(MARQUEUR):
        return None            # deja en tete : rien a faire
    avant = p[:i].rstrip()
    for amorce in AMORCES:
        if avant.endswith(amorce):
            consignes = avant[: -len(amorce)].rstrip()
            return MARQUEUR + SEPARATEUR + consignes if consignes else None
    return None                # aucune amorce connue : on ne touche pas


def _a_la_fin(p: str) -> str | None:
    """Le chemin inverse, pour le downgrade."""
    if not p.startswith(MARQUEUR + SEPARATEUR):
        return None
    consignes = p[len(MARQUEUR + SEPARATEUR):].rstrip()
    return f"{consignes}\n\n{AMORCES[0]}\n\n{MARQUEUR}"


def _transformer(transforme) -> None:
    bind = op.get_bind()
    for table, colonne in CIBLES:
        lignes = bind.execute(
            sa.text(f"SELECT id, {colonne} FROM {table} WHERE {colonne} IS NOT NULL")
        ).fetchall()
        touches, laisses = 0, []
        for ident, texte in lignes:
            nouveau = transforme(texte or "")
            if nouveau is None:
                laisses.append(ident)
                continue
            bind.execute(
                sa.text(f"UPDATE {table} SET {colonne} = :v WHERE id = :i"),
                {"v": nouveau, "i": ident},
            )
            touches += 1
        log.info("%s.%s : %d prompt(s) deplace(s), %d laisse(s) intact(s) %s",
                 table, colonne, touches, len(laisses), laisses or "")


def upgrade() -> None:
    _transformer(_en_tete)


def downgrade() -> None:
    _transformer(_a_la_fin)
