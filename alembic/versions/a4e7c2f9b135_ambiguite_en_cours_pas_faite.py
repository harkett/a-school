# -*- coding: utf-8 -*-
"""Le tableau de bord dit « Ambiguites : fait », l'ecran est grise depuis hier

CONSTAT du 12/08/2026. L'entree « Ambiguite » du menu prof est grisee et non cliquable, et la
carte « Ambiguites » de l'Accueil porte « bientot » : l'outil ne fonctionne pas encore, on ne
veut pas qu'un prof tombe dessus. Or la ligne de `fonctionnalites` qui le decrit porte toujours
l'etat `fait`.

Deux ecrans, deux verites — exactement le defaut que la table `fonctionnalites` existe pour
empecher. Un tableau de bord qui annonce livre ce que le menu refuse d'ouvrir ne se contredit
nulle part visiblement : il faut avoir les deux ecrans sous les yeux pour le voir. C'est le meme
defaut que le Labo le 10/08, dans l'autre sens.

CE QUE FAIT CETTE MIGRATION. Elle passe la ligne a `en_cours`, pas a `a_venir` : le travail
existe, il tourne, il est meme deploye — il n'est simplement pas en etat d'etre montre a un prof.
`a_venir` decrirait un chantier pas commence, ce qui serait faux dans l'autre sens.

`composant` NE CHANGE PAS. `src/components/Ambiguites.jsx` existe toujours, et le filet
`test_tableau_de_bord_dit_vrai` exige un fichier reel pour toute ligne qui n'est pas « a venir ».
La `note` porte la preuve, comme le veut la table : c'est elle qui rend l'etat verifiable.

QUAND L'OUTIL SERA PRET, trois gestes vont ensemble et aucun ne se suffit : degriser l'entree du
menu (`Sidebar.jsx`), retirer le drapeau `bientot` de la carte de l'Accueil (`Accueil.jsx`), et
repasser cette ligne a `fait` par une nouvelle migration.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a4e7c2f9b135"
down_revision: Union[str, Sequence[str], None] = "d7f3b1e9a5c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ECRAN = "Mes analyses"
NOM = "Ambiguïtés d'un énoncé"
NOTE = "Écran grisé côté prof (menu et Accueil) : l'outil n'est pas en état d'être montré."


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE fonctionnalites SET etat = 'en_cours', note = :note "
                "WHERE ecran = :e AND nom = :n"),
        {"note": NOTE, "e": ECRAN, "n": NOM},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE fonctionnalites SET etat = 'fait', note = NULL "
                "WHERE ecran = :e AND nom = :n"),
        {"e": ECRAN, "n": NOM},
    )
