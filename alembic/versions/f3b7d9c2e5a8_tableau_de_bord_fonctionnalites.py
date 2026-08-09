# -*- coding: utf-8 -*-
"""Le tableau de bord gagne sa moitié manquante : l'état des FONCTIONNALITÉS.

CONSTAT. L'écran « Mise en route » dérivait huit étapes des vraies tables — clé IA, SMTP, un
référentiel découpé, une activité générée — et affichait « Tout est prêt » dès qu'elles étaient
vertes. Elles le sont. Pendant ce temps « Mes évals » est vide, l'équité n'est pas écrite et le
partage de contenus est un bouton inactif. L'écran disait vrai sur la plomberie et faux sur le
produit : il mesurait que l'installation est branchée, pas que la plateforme est finie.

CE QUE FAIT CETTE MIGRATION. Elle crée `fonctionnalites` et la sème avec l'inventaire des deux
côtés de l'application, relevé dans le code : les entrées des deux menus, les pages, les boutons
posés mais inactifs, les écrans qui rendent « en cours de développement ».

LES TROIS ÉTATS, ET RIEN DE PLUS :
  fait      livré et utilisable ;
  en_cours  commencé, visible dans l'interface, mais pas utilisable ;
  a_venir   rien encore.

LA COLONNE `note` EST LA PREUVE. Elle dit d'où vient l'état — « bouton posé, inactif », « page
vide », « menu désactivé ». Une ligne « en cours » sans sa raison est invérifiable, donc
incontestable, donc inutile.

QUI TIENDRA CETTE TABLE. La session qui code, par migration, à chaque livraison. L'administrateur
consulte, il n'édite pas : c'est le motif d'`outils_llm`, dont la liste vit aussi dans les
migrations et nulle part ailleurs.

CE QU'ELLE NE TOUCHE PAS. Les huit étapes techniques restent dérivées des vraies tables. Elles
n'entrent pas dans cette table : une donnée qui se lit ne se déclare jamais.

Revision ID: f3b7d9c2e5a8
Revises: e2a6c8d4f1b7
Create Date: 2026-08-07
"""
from alembic import op
import sqlalchemy as sa


revision = "f3b7d9c2e5a8"
down_revision = "e2a6c8d4f1b7"
branch_labels = None
depends_on = None


# L'inventaire au 07/08/2026 — (domaine, écran, nom, état, note).
# Relevé dans le code, pas de mémoire : chaque « en_cours » et chaque « a_venir » porte
# l'endroit qui le prouve. Le nom de la constante suit la convention des autres migrations
# porteuses de données (OUTILS, PROMPTS_MAJ) : la liste n'existe qu'ici.
FONCTIONNALITES = [
    # -- COTE ADMIN --------------------------------------------------------------------------
    ("admin", "Référentiel", "Dépôt du PDF et épuration", "fait", None),
    ("admin", "Référentiel", "Prompt des matières", "fait", None),
    ("admin", "Référentiel", "Prompt de découpe", "fait", None),
    ("admin", "Référentiel", "Prompt des types d'activité", "fait", None),
    ("admin", "Référentiel", "Prompt des précisions", "fait", None),
    ("admin", "Référentiel", "Découpe en unités et embeddings", "fait", None),
    ("admin", "Référentiel", "Consulter un référentiel", "fait", None),
    ("admin", "Formations", "Contenus par cycle et niveau", "fait", None),

    ("admin", "IA", "Fournisseurs et modèles", "fait", None),
    ("admin", "IA", "Prompts (prof, admin, référentiels, autres)", "fait", None),
    ("admin", "IA", "Réglages de génération", "fait", None),
    ("admin", "IA", "Statistiques d'appels et coûts", "fait", None),

    ("admin", "Profs", "Profils des enseignants", "fait", None),
    ("admin", "Communication", "Mail groupé", "fait", None),
    ("admin", "Communication", "Feedbacks reçus", "fait", None),

    ("admin", "Supervision", "Sessions en cours", "fait", None),
    ("admin", "Supervision", "Métriques serveur", "fait", None),
    ("admin", "Supervision", "Alertes automatiques", "fait", None),
    ("admin", "Supervision", "Journal des connexions", "fait", None),
    ("admin", "Supervision", "Tentatives échouées", "fait", None),
    ("admin", "Supervision", "Audit des actions sensibles", "fait", None),

    ("admin", "Analytique", "Vue générale", "fait", None),
    ("admin", "Analytique", "Détail par prof, matière, niveau", "fait", None),

    ("admin", "Base de données", "Base réelle et garde-fou", "fait", None),
    ("admin", "Base de données", "Bases de démonstration", "en_cours",
     "écran posé, aucune démonstration branchée"),

    ("admin", "Système", "Email de bienvenue", "fait", None),
    ("admin", "Système", "Table des paramètres", "fait", None),
    ("admin", "Système", "Maintenance de la base", "fait", None),

    ("admin", "Outils", "Labo", "fait", None),
    ("admin", "Outils", "Mon compte", "fait", None),
    ("admin", "Outils", "Aide", "fait", None),

    # -- COTE PROF ---------------------------------------------------------------------------
    ("prof", "Accueil", "Tableau de bord du prof", "fait", None),
    ("prof", "Accueil", "Accès rapide aux outils d'analyse", "fait", None),

    ("prof", "Génération", "Créer une activité", "fait", None),
    ("prof", "Génération", "Créer une séance", "fait", None),
    ("prof", "Génération", "Créer une séquence", "fait", None),

    ("prof", "Mes contenus", "Séquences", "fait", None),
    ("prof", "Mes contenus", "Séances", "fait", None),
    ("prof", "Mes contenus", "Activités", "fait", None),
    ("prof", "Mes contenus", "Partager un contenu", "en_cours",
     "bouton posé dans les trois listes, inactif"),
    ("prof", "Mes contenus", "Supprimer un contenu", "en_cours",
     "bouton posé dans les trois listes, inactif"),

    ("prof", "Mes analyses", "Ambiguïtés d'un énoncé", "fait", None),
    ("prof", "Mes analyses", "Qualité d'une consigne", "fait", None),
    ("prof", "Mes analyses", "Équité d'une évaluation", "a_venir",
     "la page rend « Outil en cours de développement »"),

    ("prof", "Mes évals", "Sujets, grilles et quiz", "a_venir",
     "entrée de menu désactivée, aucun écran"),

    ("prof", "Mon compte", "Mon profil", "fait", None),
    ("prof", "Mon compte", "Mes feedbacks", "fait", None),
    ("prof", "Mon compte", "Mes stats", "fait", None),

    ("prof", "Aide", "Centre d'aide", "fait", None),
    ("prof", "Aide", "Bientôt disponible et idées", "fait", None),
    ("prof", "Aide", "Notation de la plateforme", "fait", None),
    ("prof", "Aide", "À propos", "fait", None),
    ("prof", "Aide", "Accès aux démonstrations", "en_cours",
     "lien posé dans le menu, grisé tant qu'aucune démonstration n'a d'adresse"),
]


def upgrade() -> None:
    op.create_table(
        "fonctionnalites",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("domaine", sa.String(16), nullable=False),
        sa.Column("ecran", sa.String(80), nullable=False),
        sa.Column("nom", sa.String(120), nullable=False),
        sa.Column("etat", sa.String(16), nullable=False, server_default="a_venir"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("domaine", "ecran", "nom", name="uq_fonctionnalites_domaine_ecran_nom"),
    )
    # L'index sert le seul tri de l'écran : par domaine, puis dans l'ordre de la liste.
    op.create_index("ix_fonctionnalites_domaine_ordre", "fonctionnalites", ["domaine", "ordre"])

    conn = op.get_bind()
    for ordre, (domaine, ecran, nom, etat, note) in enumerate(FONCTIONNALITES, start=1):
        conn.execute(
            sa.text(
                "INSERT INTO fonctionnalites (domaine, ecran, nom, etat, note, ordre) "
                "VALUES (:d, :e, :n, :s, :note, :o)"
            ),
            {"d": domaine, "e": ecran, "n": nom, "s": etat, "note": note, "o": ordre},
        )


def downgrade() -> None:
    op.drop_index("ix_fonctionnalites_domaine_ordre", table_name="fonctionnalites")
    op.drop_table("fonctionnalites")
