# -*- coding: utf-8 -*-
"""Une note au carnet : le vrai problème de fond — ce qui existe en double

CONSTATÉ LE 16/08/2026, en direct. Une correction posée sur la boîte de dialogue de
l'application n'a rien changé à l'écran : l'administration en avait une SECONDE, écrite à la
main, qui prenait le canal. Le défaut avait survécu à sa propre correction.

CE N'EST PAS UN ACCIDENT, c'est la façon dont le travail avance : on trouve mieux en cours de
route, on écrit le neuf, et l'ancien reste — parce que le supprimer demande de vérifier qui s'en
sert, et que ça n'est jamais urgent.

Cette note porte le message à donner à une session dédiée, avec les pistes déjà relevées.

downgrade : retire la note.

Revision ID: b8e4a2f7d3c9
Revises: a7d3f9b5c2e8
Create Date: 2026-08-16
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "b8e4a2f7d3c9"
down_revision: Union[str, Sequence[str], None] = "a7d3f9b5c2e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TITRE = "Chasse aux doublons et au code mort — message pour la session dédiée"

DETAIL = """LA MISSION, EN UNE PHRASE : trouver ce qui existe en DOUBLE dans cette application, et ce que plus rien n'utilise. Ni réparer des boutons, ni refaire de l'ergonomie — ces chantiers-là existent, ils sont ailleurs.

POURQUOI C'EST LE VRAI PROBLÈME, avec l'exemple vécu le 16/08/2026. L'application a une boîte de dialogue unique depuis le 30/07 : bandeau, icône, titre, croix. Une correction y est posée. L'écran ne change pas. Raison : `AdminLayout` appelait `registerErrorHandler` et rendait sa PROPRE modale, écrite à la main, qui volait le canal dès qu'on entrait dans l'administration. Le défaut avait survécu à sa correction, et rien ne le signalait — les deux boîtes fonctionnaient.

CE QUI REND LA CHOSE COÛTEUSE : un code mort ne gêne personne, il dort. Un code en DOUBLE, lui, ment. Les deux chemins marchent, rien ne dit lequel est le vrai, et une session qui arrive derrière corrige le mauvais — puis conclut que le défaut est ailleurs.

LES PISTES DÉJÀ RELEVÉES, à vérifier une par une (aucune n'est un ordre de suppression) :

1. `deploy/restaurer-bases.sh` raisonne encore en CINQ BASES de démonstration. Elles sont devenues cinq schémas d'une seule base le 12/08 ; le script est le dernier endroit qui croit au monde d'avant. Il écrase aussi la base réelle, où vivent maintenant de vrais professeurs inscrits — donc à ne pas se contenter de « moderniser ».

2. Les cinq bases `ciela_demo`, `cielb_demo`, `creche_demo`, `crsa_demo`, `ergo_demo` existent encore SUR LE POSTE ET SUR LE SERVEUR, et plus rien ne les lit depuis la bascule en schémas.

3. Côté administration, deux entrées de menu pour le même objet : « Référentiel » et « Consulter ».

4. Les statistiques vivent à TROIS endroits : IA → Statistiques, Analytique, Supervision → Serveur.

5. Deux mécaniques d'aide pour le même écran : la bulle de survol du menu, et le « i » de l'en-tête. Deux textes à tenir à jour, deux façons de les écrire.

6. Côté professeur, les MENTIONS LÉGALES existent en deux versions qui se contredisent : la fenêtre du pied de page, et la page `/mentions-legales`. La seconde annonce une suppression des données que la première ne mentionne pas. Deux textes juridiques différents, c'est le doublon le plus cher de la liste.

7. Le même écran s'appelle « Ambiguïté » dans le menu et « Ambiguïtés » sur l'accueil, avec deux aides rédigées différemment.

8. Le centre d'aide décrit le produit d'AVANT : dix-neuf fiches, une seule mention de « séance », une de « séquence », rien sur « Mes évals » ni sur les démonstrations. Du contenu mort, pas du code mort — même effet.

9. Les boutons : chaque écran réécrit ses hauteurs et ses couleurs à la main plutôt que de partir des mêmes styles. C'est la forme la plus répandue du doublon dans cette application, et la moins visible.

10. `FenetrePro` est la coquille commune, mais plusieurs écrans dessinent encore leur propre fenêtre à côté (l'aide de l'administration l'a fait, le panneau « Comment ça marche ? » de l'écran Référentiel le fait toujours).

LA MÉTHODE, dans cet ordre :
  - CHERCHER ET LISTER d'abord, ne rien supprimer. Un inventaire écrit vaut mieux qu'une suppression rapide ;
  - pour chaque doublon, dire lequel est le VRAI et pourquoi — celui que l'application utilise vraiment, pas le plus récent ;
  - vérifier qui appelle l'autre AVANT de le retirer. Un « code mort » qui ne l'est pas casse en silence ;
  - la suite de tests doit rester verte à chaque étape, jamais seulement à la fin.

CE QUI N'EST PAS DE CE CHANTIER, et qui a sa propre liste : le menu qui ne s'allume pas, le numéro de version faux au pied du menu, le menu inaccessible au clavier, la largeur figée sur petit écran, le texte d'astuce coupé, le mot « admin » quasi invisible mais cliquable par un professeur. Ce sont des défauts d'ergonomie et de finition, pas des doublons. Les mélanger donnerait une session qui répare des boutons au lieu de chercher ce qui existe en double."""


def upgrade() -> None:
    op.execute(
        sa.text("INSERT INTO taches_a_faire (titre, detail) VALUES (:titre, :detail)")
        .bindparams(titre=TITRE, detail=DETAIL)
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM taches_a_faire WHERE titre = :titre").bindparams(titre=TITRE)
    )
