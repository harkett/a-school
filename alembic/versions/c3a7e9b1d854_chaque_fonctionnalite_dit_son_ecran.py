# -*- coding: utf-8 -*-
"""`fonctionnalites` gagne la colonne `composant` : la ligne dit enfin OU vit son ecran.

CE QUI MANQUAIT. Le tableau de bord annonce 55 fonctionnalites, chacune « fait », « en cours » ou
« a venir ». RIEN ne reliait une ligne au code qui la porte. Le 10/08/2026 la ligne « Labo »
annoncait encore « fait » alors que l'ecran, ses treize routes et sa suite de tests avaient ete
supprimes le matin meme (migration b8f2d6c4a917). Aucun test ne pouvait le voir : il n'y avait
rien a confronter.

CE QUE FAIT CETTE MIGRATION. Elle ajoute `composant` — le chemin, depuis `frontend/`, du fichier
qui REND cet ecran — et le renseigne pour les 51 lignes qui en ont un. Les quatre « Mes evals » et
« Equite d'une evaluation » restent a NULL : rien n'est ecrit, il n'y a pas de fichier a citer.

CE QUE CA PERMET. `tests/test_tableau_de_bord_dit_vrai.py` peut desormais tomber : toute ligne qui
n'est pas « a venir » doit citer un composant, et ce fichier doit exister. Supprimez un ecran sans
toucher sa ligne, et la suite le dit — c'est exactement le cas du Labo, qui serait passe inapercu
une seconde fois.

PLUSIEURS LIGNES PARTAGENT UN COMPOSANT, et c'est normal : les six premieres cartouches de
l'ecran Referentiel sont six etapes d'un meme fichier. On decrit ce que l'admin voit, pas le
decoupage des fichiers.

Revision ID: c3a7e9b1d854
Revises: b8f2d6c4a917
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa


revision = "c3a7e9b1d854"
down_revision = "b8f2d6c4a917"
branch_labels = None
depends_on = None


# (ecran, nom) -> chemin du composant, depuis `frontend/`.
COMPOSANTS = {
    # --- admin -------------------------------------------------------------
    ("Référentiel", "Dépôt du PDF et épuration"):        "src/pages/AdminReferentiels.jsx",
    ("Référentiel", "Prompt des matières"):              "src/pages/AdminReferentiels.jsx",
    ("Référentiel", "Prompt de découpe"):                "src/pages/AdminReferentiels.jsx",
    ("Référentiel", "Prompt des types d'activité"):      "src/pages/AdminReferentiels.jsx",
    ("Référentiel", "Prompt des précisions"):            "src/pages/AdminReferentiels.jsx",
    ("Référentiel", "Découpe en unités et embeddings"):  "src/pages/AdminReferentiels.jsx",
    ("Référentiel", "Consulter un référentiel"):         "src/pages/AdminReferentielsConsulter.jsx",
    ("Formations", "Contenus par cycle et niveau"):      "src/pages/AdminContenu.jsx",
    ("IA", "Fournisseurs et modèles"):                   "src/pages/AdminIAFournisseurs.jsx",
    ("IA", "Prompts (prof, admin, référentiels, autres)"): "src/pages/AdminPrompts.jsx",
    ("IA", "Réglages de génération"):                    "src/pages/AdminParametresGeneration.jsx",
    ("IA", "Statistiques d'appels et coûts"):            "src/pages/AdminIAStatistiques.jsx",
    ("Profs", "Profils des enseignants"):                "src/pages/AdminProfils.jsx",
    ("Communication", "Mail groupé"):                    "src/pages/AdminCommunication.jsx",
    ("Communication", "Feedbacks reçus"):                "src/pages/AdminFeedbacks.jsx",
    ("Supervision", "Sessions en cours"):                "src/pages/AdminSessions.jsx",
    ("Supervision", "Métriques serveur"):                "src/pages/AdminServeur.jsx",
    ("Supervision", "Alertes automatiques"):             "src/pages/AdminAlertes.jsx",
    ("Supervision", "Journal des connexions"):           "src/pages/AdminLogs.jsx",
    ("Supervision", "Tentatives échouées"):              "src/pages/AdminTentatives.jsx",
    ("Supervision", "Audit des actions sensibles"):      "src/pages/AdminAudit.jsx",
    ("Analytique", "Vue générale"):                      "src/pages/AdminAnalytiqueGeneral.jsx",
    ("Analytique", "Détail par prof, matière, niveau"):  "src/pages/AdminAnalytique.jsx",
    ("Base de données", "Base réelle et garde-fou"):     "src/pages/AdminBase.jsx",
    ("Base de données", "Bases de démonstration"):       "src/pages/AdminBaseDemos.jsx",
    ("Système", "Email de bienvenue"):                   "src/pages/AdminParametresEmail.jsx",
    ("Système", "Table des paramètres"):                 "src/pages/AdminParametres.jsx",
    ("Système", "Maintenance de la base"):               "src/pages/AdminMaintenance.jsx",
    ("Outils", "Mon compte"):                            "src/pages/AdminCompte.jsx",
    ("Outils", "Aide"):                                  "src/pages/AdminAide.jsx",
    # --- prof --------------------------------------------------------------
    ("Accueil", "Tableau de bord du prof"):              "src/components/Accueil.jsx",
    ("Accueil", "Accès rapide aux outils d'analyse"):    "src/components/Accueil.jsx",
    ("Génération", "Créer une activité"):                "src/components/ActiviteEcran.jsx",
    ("Génération", "Créer une séance"):                  "src/components/SeanceEcran.jsx",
    ("Génération", "Créer une séquence"):                "src/components/SequenceEcran.jsx",
    ("Mes contenus", "Séquences"):                       "src/components/contenus/SequencesContenus.jsx",
    ("Mes contenus", "Séances"):                         "src/components/contenus/SeancesContenus.jsx",
    ("Mes contenus", "Activités"):                       "src/components/contenus/ActivitesContenus.jsx",
    ("Mes contenus", "Partager un contenu"):             "src/components/MesContenus.jsx",
    ("Mes contenus", "Supprimer un contenu"):            "src/components/contenus/ConfirmerSuppression.jsx",
    ("Mes analyses", "Ambiguïtés d'un énoncé"):          "src/components/Ambiguites.jsx",
    ("Mes analyses", "Qualité d'une consigne"):          "src/components/Consigne.jsx",
    ("Mon compte", "Mon profil"):                        "src/components/MonProfil.jsx",
    ("Mon compte", "Mes feedbacks"):                     "src/pages/MesFeedbacks.jsx",
    ("Mon compte", "Mes stats"):                         "src/components/MesStats.jsx",
    ("Aide", "Centre d'aide"):                           "src/components/Aide.jsx",
    ("Aide", "Bientôt disponible et idées"):             "src/components/BientotDisponible.jsx",
    ("Aide", "Notation de la plateforme"):               "src/components/Notation.jsx",
    ("Aide", "À propos"):                                "src/components/APropos.jsx",
    ("Aide", "Accès aux démonstrations"):                "src/components/Sidebar.jsx",
}


def upgrade() -> None:
    op.add_column("fonctionnalites", sa.Column("composant", sa.Text(), nullable=True))
    conn = op.get_bind()
    for (ecran, nom), chemin in COMPOSANTS.items():
        conn.execute(
            sa.text("UPDATE fonctionnalites SET composant = :c WHERE ecran = :e AND nom = :n"),
            {"c": chemin, "e": ecran, "n": nom},
        )


def downgrade() -> None:
    op.drop_column("fonctionnalites", "composant")
