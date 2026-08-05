# -*- coding: utf-8 -*-
"""`outils_llm` : les outils qui appellent l'IA, un par ligne — l'ecran des longueurs les montre TOUS.

L'ecran « Longueur des reponses de l'IA » ne reglait que 3 outils sur 17 : `max_tokens_default`,
`max_tokens_ambiguites`, `max_tokens_sequence`, ecrits a la main dans le backend ET dans le front.
Les 14 autres prenaient le defaut global en silence — l'admin ne pouvait ni les voir ni les
changer — et `max_tokens_referentiel_fusion` (12 000, seme par d3b7f5c9e1a2) vivait en base sans
aucun ecran pour l'afficher.

Taper les 17 dans l'ecran aurait remplace 3 valeurs en dur par 17, et le 18e outil serait redevenu
invisible. La liste descend donc EN BASE : l'ecran lit cette table, une ligne = un champ. Le jour
ou un developpeur ajoute un `get_max_tokens(db, "<outil>")`, il ajoute sa ligne par migration et
l'ecran le montre sans etre retouche. `tests/test_outils_llm_en_base.py` relit le code et tombe si
un appel n'a pas sa ligne — le filet qui empeche l'oubli de recommencer.

LA VALEUR N'EST PAS ICI. Elle reste dans `settings`, sous `max_tokens_<outil>` : c'est ce que
`get_max_tokens` lit depuis toujours, et sa lecture etait deja generique. Cette table ne porte que
l'identite de l'outil. Pas de ligne `max_tokens_<outil>` = l'outil suit le defaut global.

Au passage, `max_tokens_ambiguites` et `max_tokens_sequence` partent : rien ne justifiait que ces
deux outils-la soient regles a part. Ils suivent le defaut global comme tous les autres.

Revision ID: b4e8d2a6f1c9
Revises: a1f4c8e2b6d9
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4e8d2a6f1c9"
down_revision: Union[str, Sequence[str], None] = "a1f4c8e2b6d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Les 17 outils qui appellent `get_max_tokens` au 05/08/2026. Le nom technique est le mot EXACT
# passe a l'appel — pas une approximation : `detecter_types_activite`, pas « types_activite ».
# L'ordre suit ce que l'admin cherche : ce qui produit du contenu pour le prof d'abord, les
# referentiels ensuite, les petites detections techniques en dernier.
OUTILS = [
    ("activite", "Activité complète", 10,
     "Le document remis à l'élève : consignes, exercices, corrigé. C'est la sortie longue du "
     "logiciel — une valeur trop basse coupe le corrigé sans prévenir."),
    ("sequence", "Séquence pédagogique", 20,
     "Plusieurs séances enchaînées, rédigées d'un seul tenant. Demande plus de place qu'une "
     "activité seule."),
    ("idee", "Idées d'activité", 30,
     "Les quelques propositions faites au professeur avant de rédiger. Une liste d'idées reste "
     "courte : inutile de monter haut."),
    ("consigne", "Analyse d'une consigne", 40,
     "Relit la consigne écrite par le professeur et la commente. Sortie brève."),
    ("ambiguites", "Détecteur d'ambiguïtés", 50,
     "Liste les passages qu'un élève pourrait comprendre de travers. Sortie moyenne, plus longue "
     "quand le document soumis est long."),
    ("ocr", "Lecture d'une image (dictée)", 60,
     "Transcrit le texte d'une photo. La longueur nécessaire suit celle du document photographié : "
     "trop bas, la fin de la page manque."),
    ("exemple", "Exemple tiré d'un référentiel", 70,
     "Un exemple court affiché pour illustrer ce que contient un référentiel."),
    ("referentiel_fusion", "Fusion des documents d'un référentiel", 100,
     "Tire UN seul référentiel des PDF déposés pour un couple. À accorder avec le nombre de pages "
     "voulu (réglage « fusion_max_pages ») : c'est la plus petite des deux bornes qui l'emporte, "
     "donc une longueur trop basse rend le nombre de pages inatteignable."),
    ("analyse_amont", "Analyse d'un référentiel", 110,
     "Première lecture du référentiel déposé : ce qu'il contient, comment il est bâti."),
    ("decoupe_amont", "Découpe d'un référentiel", 120,
     "Recopie le référentiel en morceaux exploitables. C'est l'outil qui a besoin du plus de "
     "place : une valeur trop basse tronque la découpe en silence."),
    ("meta_decoupe", "Repérage des titres — découpe", 130,
     "Repère les titres du document pour savoir où couper. Sortie courte (une liste de titres)."),
    ("meta_matieres", "Repérage des titres — matières", 140,
     "Repère les titres qui annoncent une matière. Sortie courte."),
    ("verifier_couple", "Vérification du couple cycle / niveau", 200,
     "Répond si le document déposé correspond bien au cycle et au niveau annoncés. Sortie très "
     "courte."),
    ("detecter_couple", "Détection du couple cycle / niveau", 210,
     "Devine le cycle et le niveau à partir du document. Sortie très courte."),
    ("detecter_matieres", "Détection des matières", 220,
     "Liste les matières trouvées dans le référentiel. Sortie courte, proportionnelle au nombre "
     "de matières."),
    ("detecter_types_activite", "Détection des types d'activité", 230,
     "Liste les types d'activité que le référentiel permet. Sortie courte."),
    ("suggerer_precisions_type", "Suggestion de précisions de type", 240,
     "Propose les précisions à demander au professeur pour un type d'activité donné. Sortie "
     "courte."),
]

# Les deux surcharges qui traitaient ambiguites et sequence a part (voir l'en-tete).
SURCHARGES_RETIREES = ("max_tokens_ambiguites", "max_tokens_sequence")


def upgrade() -> None:
    op.create_table(
        "outils_llm",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("outil", sa.String(50), nullable=False),
        sa.Column("libelle", sa.String(150), nullable=False),
        sa.Column("aide", sa.Text(), nullable=False, server_default=""),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("outil", name="uq_outils_llm_outil"),
    )
    conn = op.get_bind()
    insert = sa.text(
        "INSERT INTO outils_llm (outil, libelle, aide, ordre) "
        "VALUES (:outil, :libelle, :aide, :ordre) ON CONFLICT (outil) DO NOTHING"
    )
    for outil, libelle, ordre, aide in OUTILS:
        conn.execute(insert, {"outil": outil, "libelle": libelle, "aide": aide, "ordre": ordre})

    for cle in SURCHARGES_RETIREES:
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {"key": cle})



def downgrade() -> None:
    # Les deux surcharges ne sont PAS remises : rien ne justifiait ces deux exceptions, et un
    # `downgrade` n'est pas fait pour ressusciter un reglage dont on vient de dire qu'il n'a pas
    # lieu d'etre. L'admin peut les reposer depuis l'ecran, comme pour n'importe quel outil.
    op.drop_table("outils_llm")
