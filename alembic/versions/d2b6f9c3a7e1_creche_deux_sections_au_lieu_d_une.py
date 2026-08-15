# -*- coding: utf-8 -*-
"""La crèche tient deux sections — Bébés (0-1 an) et Moyens-Grands (1-3 ans) — sur un seul référentiel

CE QUE DIT LE RÉFÉRENTIEL, ET RIEN DE PLUS. Son préambule est explicite : « Ce document reprend
les tranches telles que les sources les distinguent : Bébés (0-1 an) et 1-3 ans […] Le référentiel
ne subdivise pas lui-même la bande 1-3 : les sources ne la distinguent pas, et aSchool n'invente
pas cette finesse. » DEUX tranches, donc deux niveaux. Un découpage bébés / moyens / grands aurait
fabriqué une frontière que le document refuse de tracer.

LE MONTAGE EST CELUI DU CYCLE 4. Un document, plusieurs niveaux desservis (`referentiel_niveaux`),
et l'unité qui ne vaut que pour une tranche la porte dans `annee`. Le filtre RAG lit déjà
`annee IS NULL OR annee = <niveau du prof>` : rien à toucher côté code.

CE QUI SÉPARE LES DEUX SECTIONS. La ligne « Âge : » de chaque fiche, et elle seule :
  - pas de ligne Âge (22)                        → commune
  - la ligne nomme les bébés ou les tout-petits  → commune (25)
  - la ligne ne parle que de tranches chiffrées  → réservée aux 1-3 ans (14)
« Tout-petits » reste COMMUN à dessein : ce sont quatre activités manuelles, et rien dans le
document ne dit qu'elles excluent un bébé. Le classer en 1-3 aurait retiré au niveau Bébés une
fiche que sa source ne lui interdit pas. Aucune fiche n'est réservée aux 0-1 an : la section
Bébés voit les 47 communes, la section Moyens-Grands les 61.

LE NIVEAU EXISTANT EST RENOMMÉ, PAS REMPLACÉ. `BMG_0-3` était un code technique qui désignait
déjà toute la crèche ; il devient la section Bébés et garde son id, donc le référentiel porteur
et sa liaison restent en place. Zéro prof y était inscrit au moment de la bascule.

downgrade : refond les deux sections en `BMG_0-3`, efface les années, et rend son nom d'affichage
au référentiel. Rien n'est perdu — la ligne « Âge : » du texte reste la source.

Revision ID: d2b6f9c3a7e1
Revises: f3c7b1e5d9a2
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op


revision: str = "d2b6f9c3a7e1"
down_revision: Union[str, Sequence[str], None] = "f3c7b1e5d9a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BEBES = "Bébés (0-1 an)"
MOYENS_GRANDS = "Moyens-Grands (1-3 ans)"

# La ligne « Âge : » d'une fiche. `(?in)` : insensible à la casse, et `^`/`$` accrochent les
# lignes du chunk, pas ses deux extrémités — la ligne Âge est au milieu du texte.
LIGNE_AGE = r"(?in)^\s*.ge\s*:\s*(.+)$"
# Ce qui rend une fiche commune aux deux sections dès lors qu'elle porte une ligne Âge.
NOMME_LES_PETITS = r"b.b.|tout-petit"


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE niveaux SET nom = '{BEBES}', ordre = 1
         WHERE cycle_id = (SELECT id FROM cycles WHERE nom = 'Crèche')
           AND nom = 'BMG_0-3'
        """
    )
    op.execute(
        f"""
        INSERT INTO niveaux (cycle_id, nom, ordre)
        SELECT c.id, '{MOYENS_GRANDS}', 2
          FROM cycles c
         WHERE c.nom = 'Crèche'
           AND NOT EXISTS (SELECT 1 FROM niveaux n
                            WHERE n.cycle_id = c.id AND n.nom = '{MOYENS_GRANDS}')
        """
    )
    # Le référentiel de la crèche dessert désormais ses deux sections. `referentiel_niveaux`
    # porte UNIQUE(niveau_id) : le nouveau niveau ne peut être pris par personne d'autre.
    op.execute(
        f"""
        INSERT INTO referentiel_niveaux (referentiel_id, niveau_id)
        SELECT rn.referentiel_id, mg.id
          FROM niveaux mg
          JOIN cycles c ON c.id = mg.cycle_id AND c.nom = 'Crèche'
          JOIN niveaux b ON b.cycle_id = c.id AND b.nom = '{BEBES}'
          JOIN referentiel_niveaux rn ON rn.niveau_id = b.id
         WHERE mg.nom = '{MOYENS_GRANDS}'
           AND NOT EXISTS (SELECT 1 FROM referentiel_niveaux x WHERE x.niveau_id = mg.id)
        """
    )
    # `annee` porte le NOM du niveau, car c'est le nom que le filtre RAG reçoit du prof.
    op.execute(
        f"""
        UPDATE referentiel_chunks ch
           SET annee = '{MOYENS_GRANDS}'
          FROM referentiel_niveaux rn
          JOIN niveaux b ON b.id = rn.niveau_id AND b.nom = '{BEBES}'
          JOIN cycles c ON c.id = b.cycle_id AND c.nom = 'Crèche'
         WHERE ch.referentiel_id = rn.referentiel_id
           AND ch.annee IS NULL
           AND substring(ch.texte from '{LIGNE_AGE}') IS NOT NULL
           AND substring(ch.texte from '{LIGNE_AGE}') !~* '{NOMME_LES_PETITS}'
        """
    )
    op.execute(
        """
        UPDATE referentiels r
           SET nom_affichage = (
               SELECT string_agg(n.nom, ', ' ORDER BY n.ordre)
                 FROM referentiel_niveaux rn
                 JOIN niveaux n ON n.id = rn.niveau_id
                WHERE rn.referentiel_id = r.id)
         WHERE r.id IN (SELECT rn.referentiel_id
                          FROM referentiel_niveaux rn
                          JOIN niveaux n ON n.id = rn.niveau_id
                          JOIN cycles c ON c.id = n.cycle_id
                         WHERE c.nom = 'Crèche')
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        UPDATE referentiel_chunks SET annee = NULL
         WHERE annee = '{MOYENS_GRANDS}'
        """
    )
    op.execute(
        f"""
        DELETE FROM referentiel_niveaux rn
         USING niveaux n, cycles c
         WHERE rn.niveau_id = n.id AND n.cycle_id = c.id
           AND c.nom = 'Crèche' AND n.nom = '{MOYENS_GRANDS}'
        """
    )
    op.execute(
        f"""
        DELETE FROM niveaux n
         USING cycles c
         WHERE n.cycle_id = c.id AND c.nom = 'Crèche' AND n.nom = '{MOYENS_GRANDS}'
        """
    )
    op.execute(
        f"""
        UPDATE niveaux SET nom = 'BMG_0-3', ordre = 1
         WHERE cycle_id = (SELECT id FROM cycles WHERE nom = 'Crèche')
           AND nom = '{BEBES}'
        """
    )
    op.execute(
        """
        UPDATE referentiels r
           SET nom_affichage = (
               SELECT string_agg(n.nom, ', ' ORDER BY n.ordre)
                 FROM referentiel_niveaux rn
                 JOIN niveaux n ON n.id = rn.niveau_id
                WHERE rn.referentiel_id = r.id)
         WHERE r.id IN (SELECT rn.referentiel_id
                          FROM referentiel_niveaux rn
                          JOIN niveaux n ON n.id = rn.niveau_id
                          JOIN cycles c ON c.id = n.cycle_id
                         WHERE c.nom = 'Crèche')
        """
    )
