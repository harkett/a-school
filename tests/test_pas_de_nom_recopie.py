"""Aucun nom recopié depuis une table de référence : on range l'identifiant, pas le libellé.

CE QUE CE TEST ATTRAPE
Une colonne TEXTE qui porte le nom d'une donnée possédée par une table de référence
(`matiere`, `niveau`, `mode`, `style`, `langue_lv`, `cycle`) alors que la table de référence
existe — et qui n'a NI clé étrangère NI colonne `<nom>_id` sœur pour la relier. C'est le motif
exact de la violation : le nom est recopié au lieu d'être lu (get) chez son propriétaire.
Renommer une matière laisse alors derrière lui autant de copies périmées qu'il y a de lignes.

CE QUE CE TEST N'ATTRAPE PAS, et c'est voulu :
  - une colonne AVEC clé étrangère sur le `code` du catalogue (`feedbacks.statut`,
    `ai_modeles.fournisseur`) : c'est l'identifiant, donc c'est conforme ;
  - un libellé figé volontairement (`activites.activite_label`) : le nom de colonne ne
    correspond à aucune entrée de l'annuaire, et c'est le motif « facture validée » — une
    photo gelée par l'usage, pas une copie vivante ;
  - un nom seulement APPROCHANT (`email_envois.modele_nom`, `incidents.model`,
    `email_templates.mode_envoi`) : la correspondance est EXACTE, jamais par sous-chaîne,
    sinon le test crierait sur du bruit et on finirait par ne plus le lire.

Il travaille sur les MODÈLES SQLAlchemy, pas sur la base en direct : le résultat est le même
sur une base neuve, une base dev à moitié migrée ou une base vide.

LISTE D'EXCEPTIONS — GELÉE le 31/07/2026. Elle porte l'état des lieux du jour et RIEN d'autre.
Deux catégories qu'on ne mélange jamais :
  - DETTE : à corriger un jour, ça se compte et ça se vide au fil des chantiers ;
  - EXCEPTION PERMANENTE : une copie volontaire et justifiée, qui ne partira jamais.
On ne l'allonge JAMAIS sans décision explicite de l'utilisateur. Un ajout silencieux ici vaut
suppression du test.

Lance avec : pytest (BDD jetable aschool_test via conftest.py — jamais la base dev).
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from sqlalchemy import String, Text  # noqa: E402

from backend.core import models_db  # noqa: E402

# --- L'annuaire : quel NOM appartient à quelle table de référence ------------------------
# Clé = nom EXACT de colonne interdit ailleurs. Valeur = « table.colonne » du propriétaire.
ANNUAIRE = {
    "matiere": "matieres.nom",
    "niveau": "niveaux.nom",
    "cycle": "cycles.nom",
    "mode": "seance_modes.code",
    "style": "seance_styles.code",
    "langue_lv": "langues_lv.label",
}

# Les tables PROPRIÉTAIRES (et leurs tables de liaison) : chez elles, le nom est chez lui.
TABLES_PROPRIETAIRES = {
    "matieres", "niveaux", "cycles", "seance_modes", "seance_styles", "langues_lv",
    "matiere_niveaux", "matieres_candidates", "fiches_matieres",
}

# --- DETTE — état des lieux GELÉ au 31/07/2026 (9 + 1 colonnes) ---------------------------
# À corriger un jour : la colonne texte doit devenir `<nom>_id` avec sa clé étrangère.
DETTE = {
    "sequences.matiere":      "models_db.py:255 — recopie matieres.nom",
    "sequences.niveau":       "models_db.py:256 — recopie niveaux.nom",
    "seances.matiere":        "models_db.py:318 — recopie matieres.nom",
    "seances.niveau":         "models_db.py:319 — recopie niveaux.nom",
    "seances.mode":           "models_db.py:322 — recopie seance_modes.code",
    "seances.style":          "models_db.py:327 — recopie seance_styles.code",
    "seance_versions.style":  "models_db.py:342 — recopie seance_styles.code",
    "activites.matiere":      "models_db.py:384 — recopie matieres.nom",
    "activites.niveau":       "models_db.py:385 — recopie niveaux.nom",
    # Dette RECONNUE PAR LE MODÈLE LUI-MÊME : « `code` est là pour la clé étrangère du jour
    # où » (models_db.py:294). Le modèle annonce la réparation, donc c'est une dette, pas une
    # exception permanente.
    "users.langue_lv":        "models_db.py:294 — recopie langues_lv.label, FK annoncée « le jour où »",
}

# --- EXCEPTION PERMANENTE — copies volontaires, elles ne partiront pas ---------------------
# Motif « facture validée » : un journal fige ce qui était vrai au moment des faits. Relire le
# référentiel donnerait le nom D'AUJOURD'HUI et falsifierait l'archive.
EXCEPTIONS_PERMANENTES = {
    "incidents.matiere": "models_db.py:155 — instantané figé de la tentative (journal)",
    "incidents.niveau":  "models_db.py:155 — instantané figé de la tentative (journal)",
}

TOLERE = set(DETTE) | set(EXCEPTIONS_PERMANENTES)


def _colonnes_suspectes():
    """Toutes les colonnes texte qui portent un nom de l'annuaire hors de chez elles."""
    trouvees = []
    for table in models_db.Base.metadata.sorted_tables:
        if table.name in TABLES_PROPRIETAIRES:
            continue
        for col in table.columns:
            if col.name not in ANNUAIRE:
                continue
            if not isinstance(col.type, (String, Text)):
                continue
            # Reliée par clé étrangère → c'est l'identifiant, pas une copie.
            if col.foreign_keys:
                continue
            # Colonne `<nom>_id` sœur → la relation existe déjà, le texte est un doublon
            # d'affichage : on le signale quand même (c'est PIRE, deux places pour une donnée).
            trouvees.append((f"{table.name}.{col.name}", ANNUAIRE[col.name]))
    return trouvees


def test_aucune_copie_nouvelle_d_une_donnee_de_reference():
    """Le filet. Toute copie NON inscrite dans la liste gelée fait tomber la suite."""
    nouvelles = [
        f"{cible} recopie {proprio} — il faut stocker {cible.split('.')[1]}_id "
        f"(clé étrangère vers {proprio.split('.')[0]}), pas le nom."
        for cible, proprio in _colonnes_suspectes()
        if cible not in TOLERE
    ]
    assert not nouvelles, (
        "Un nom de référence est recopié à un endroit NOUVEAU :\n  - "
        + "\n  - ".join(nouvelles)
        + "\n\nCe test ne s'affaiblit pas : soit la colonne devient `<nom>_id`, soit "
          "l'utilisateur décide explicitement de l'inscrire à la dette."
    )


def test_l_annuaire_dit_vrai_sur_les_tables_de_reference():
    """Garde-fou de l'annuaire : si une table de référence est renommée ou supprimée, ce test
    tombe AVANT que le test principal ne devienne muet en silence."""
    manquants = []
    for nom, proprio in ANNUAIRE.items():
        table, colonne = proprio.split(".")
        if table not in models_db.Base.metadata.tables:
            manquants.append(f"{nom} → table {table} introuvable")
        elif colonne not in models_db.Base.metadata.tables[table].columns:
            manquants.append(f"{nom} → colonne {proprio} introuvable")
    assert not manquants, (
        "L'annuaire des tables de référence pointe dans le vide :\n  - " + "\n  - ".join(manquants)
    )


def test_la_dette_est_reelle_elle_ne_se_perime_pas_en_silence():
    """L'inverse du filet : une entrée de dette DÉJÀ RÉPARÉE doit sortir de la liste. Sans ce
    test, la dette resterait affichée à 10 pour l'éternité et ne compterait plus rien."""
    reelles = {cible for cible, _ in _colonnes_suspectes()}
    reparees = sorted(TOLERE - reelles)
    assert not reparees, (
        "Ces entrées sont réparées dans les modèles mais traînent encore dans la liste :\n  - "
        + "\n  - ".join(reparees)
        + "\n\nRetire-les du fichier : la dette doit rester comptable."
    )


def test_le_compte_de_la_dette_est_celui_du_31_07_2026():
    """Le chiffre de départ, écrit noir sur blanc. Il ne bouge qu'en BAISSE, et une baisse fait
    tomber ce test — c'est voulu : réparer une dette se conclut en corrigeant ce nombre."""
    assert len(DETTE) == 10, (
        f"Dette « nom recopié » : {len(DETTE)} entrées, 10 attendues (état gelé du 31/07/2026). "
        "Une réparation ? Baisse le nombre ici. Une entrée nouvelle ? Elle n'a rien à faire "
        "dans cette liste sans décision de l'utilisateur."
    )
    assert len(EXCEPTIONS_PERMANENTES) == 2, (
        f"Exceptions permanentes : {len(EXCEPTIONS_PERMANENTES)}, 2 attendues "
        "(incidents.matiere et incidents.niveau)."
    )
