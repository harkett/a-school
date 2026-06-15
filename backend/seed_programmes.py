"""Seed initial des programmes : cycles, niveaux, matieres, matiere_niveaux.

Données de RÉFÉRENCE (programme officiel), éditables ensuite via le CRUD admin.
Idempotent : ne réinsère jamais ce qui existe déjà → relançable sans risque.

Collège / Lycée : organisés par MATIÈRES (les 12). Crèche / Supérieur : organisés
par AXES (cf. SPEC-MODULE-CRECHE §4 et SPEC-MODULE-SUPERIEUR §3) — même grille
« quelque chose × niveau », un axe est juste une matière au sens de la table.
Collision « Autonomie » (axe crèche + axe supérieur) → clés préfixées par cycle
(creche-* / sup-*), libellé affiché inchangé.
"""
from backend.database import SessionLocal
from backend.models_db import Cycle, Niveau, Matiere, MatiereNiveau

CYCLES = [  # nom, ordre, categorie (famille du cycle)
    ("Crèche", 1, "creche"), ("Maternelle", 2, "maternelle"), ("Primaire", 3, "primaire"),
    ("Collège", 4, "secondaire"), ("Lycée", 5, "secondaire"), ("Supérieur", 6, "superieur"),
]

NIVEAUX = {  # cycle -> [(nom, ordre)] — ordre interprété PAR cycle (jamais comparé entre cycles)
    "Crèche":     [("Groupe A — Nourrisson (0-12 mois)", 1),
                   ("Groupe B — Jeune marcheur (12-24 mois)", 2),
                   ("Groupe C — Grand explorateur (24-36 mois)", 3)],
    "Maternelle": [("PS", 1), ("MS", 2), ("GS", 3)],
    "Primaire":   [("CP", 4), ("CE1", 5), ("CE2", 6), ("CM1", 7), ("CM2", 8)],
    "Collège":    [("6e", 9), ("5e", 10), ("4e", 11), ("3e", 12)],
    "Lycée":      [("2nde", 13), ("1ère", 14), ("Terminale", 15)],
    "Supérieur":  [("BUT", 2), ("Licence", 3), ("Master", 4),
                   ("Écoles spécialisées", 5), ("CFA", 6), ("Formation continue", 7)],
    # NB : pas de « BTS » générique (placeholder erroné — toujours « BTS + spécialité »).
    # Les BTS réels sont des niveaux à part entière (ex. seed_bts_ciel.py).
}

# Cycles dont les niveaux ont reçu leur VRAI référentiel → traite=True (sélectionnables).
# Les autres (Crèche, Supérieur encore en axes…) restent traite=False (« en cours »).
CYCLES_TRAITES = {"Collège", "Lycée"}

MATIERES = [  # cle, nom, ordre
    ("francais", "Français", 1), ("mathematiques", "Mathématiques", 2),
    # Libellés alignés sur le nom canonique du PROFIL (MonProfil.jsx) — réconciliation :
    # « Langues Vivantes (LV) » est notamment testé par MonProfil.jsx:123 → ne pas changer.
    ("histoire-geo", "Histoire-Géographie", 3), ("langues-vivantes", "Langues Vivantes (LV)", 4),
    ("physique-chimie", "Physique-Chimie", 5), ("svt", "SVT", 6),
    ("technologie", "Technologie", 7), ("nsi", "NSI", 8),
    ("ses", "SES", 9), ("philosophie", "Philosophie", 10),
    ("arts", "Arts", 11), ("eps", "EPS", 12),
    # Crèche — 9 axes (SPEC-MODULE-CRECHE §4), clés préfixées creche-
    ("creche-securite-affective",     "Sécurité affective",         13),
    ("creche-developpement-cognitif", "Développement cognitif",     14),
    ("creche-developpement-langage",  "Développement du langage",   15),
    ("creche-developpement-moteur",   "Développement moteur",       16),
    ("creche-socialisation",          "Socialisation",              17),
    ("creche-autonomie",              "Autonomie",                  18),
    ("creche-bien-etre-quotidien",    "Bien-être quotidien",        19),
    ("creche-relation-familles",      "Relation avec les familles", 20),
    ("creche-amenagement-espaces",    "Aménagement des espaces",    21),
    # Supérieur — 7 axes (SPEC-MODULE-SUPERIEUR §3, v2.1), clés préfixées sup-
    ("sup-connaissances-disciplinaires", "Connaissances disciplinaires", 22),
    ("sup-competences-professionnelles", "Compétences professionnelles", 23),
    ("sup-competences-transversales",    "Compétences transversales",    24),
    ("sup-autonomie",                    "Autonomie",                    25),
    ("sup-recherche-innovation",         "Recherche et Innovation",      26),
    ("sup-professionnalisation",         "Professionnalisation",         27),
    ("sup-evaluation",                   "Évaluation",                   28),
]

# Programme : matiere_cle -> niveaux où elle est enseignée
PROGRAMME = {
    "francais":         ["6e", "5e", "4e", "3e", "2nde", "1ère"],            # pas "Français" en Term
    "mathematiques":    ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"],
    "histoire-geo":     ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"],
    "langues-vivantes": ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"],
    "physique-chimie":  ["5e", "4e", "3e", "2nde", "1ère", "Terminale"],     # démarre 5e
    "svt":              ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"],
    "technologie":      ["6e", "5e", "4e", "3e"],                            # collège seulement (lycée général : non)
    "nsi":              ["1ère", "Terminale"],                               # spécialité
    "ses":              ["2nde", "1ère", "Terminale"],
    "philosophie":      ["Terminale"],
    "arts":             ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"],
    "eps":              ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale"],
}

# Crèche & Supérieur : grille PLEINE — chaque axe couvre TOUS les niveaux de son cycle
# (aucune restriction par niveau dans les référentiels, contrairement au collège/lycée).
_CRECHE_NIVEAUX = [nom for nom, _ in NIVEAUX["Crèche"]]
_SUP_NIVEAUX    = [nom for nom, _ in NIVEAUX["Supérieur"]]
for _cle, _nom, _ordre in MATIERES:
    if _cle.startswith("creche-"):
        PROGRAMME[_cle] = _CRECHE_NIVEAUX
    elif _cle.startswith("sup-"):
        PROGRAMME[_cle] = _SUP_NIVEAUX


def run():
    db = SessionLocal()

    cyc = {}
    for nom, ordre, categorie in CYCLES:
        c = db.query(Cycle).filter(Cycle.nom == nom).first()
        if not c:
            c = Cycle(nom=nom, ordre=ordre, categorie=categorie)
            db.add(c)
            db.flush()
        elif c.categorie != categorie:
            c.categorie = categorie   # le fichier fait foi sur la catégorie (réconciliation idempotente)
        cyc[nom] = c

    niv = {}
    for cycle_nom, lst in NIVEAUX.items():
        traite = cycle_nom in CYCLES_TRAITES
        for nom, ordre in lst:
            n = db.query(Niveau).filter(Niveau.nom == nom, Niveau.cycle_id == cyc[cycle_nom].id).first()
            if not n:
                n = Niveau(cycle_id=cyc[cycle_nom].id, nom=nom, ordre=ordre, traite=traite)
                db.add(n)
                db.flush()
            elif n.traite != traite:
                n.traite = traite   # le fichier fait foi sur l'état « traité » (réconciliation idempotente)
            niv[nom] = n

    # Nettoyage : suppression FRANCHE du niveau « BTS » générique s'il existe (placeholder
    # erroné, jamais une vraie donnée d'historique) + ses paires d'axes.
    bts = db.query(Niveau).filter(Niveau.nom == "BTS", Niveau.cycle_id == cyc["Supérieur"].id).first()
    bts_supprime = False
    if bts:
        db.query(MatiereNiveau).filter(MatiereNiveau.niveau_id == bts.id).delete()
        db.delete(bts)
        db.flush()
        bts_supprime = True

    mat = {}
    for cle, nom, ordre in MATIERES:
        m = db.query(Matiere).filter(Matiere.cle == cle).first()
        if not m:
            m = Matiere(cle=cle, nom=nom, ordre=ordre)
            db.add(m)
            db.flush()
        elif m.nom != nom or m.ordre != ordre:
            m.nom = nom        # le fichier fait foi sur le libellé → réconciliation idempotente (clé inchangée)
            m.ordre = ordre
        mat[cle] = m

    pairs = 0
    for cle, niveaux in PROGRAMME.items():
        for nnom in niveaux:
            mn = db.query(MatiereNiveau).filter(
                MatiereNiveau.matiere_id == mat[cle].id,
                MatiereNiveau.niveau_id == niv[nnom].id,
            ).first()
            if not mn:
                db.add(MatiereNiveau(matiere_id=mat[cle].id, niveau_id=niv[nnom].id))
                pairs += 1
    db.commit()

    traites = db.query(Niveau).filter(Niveau.traite == True).count()
    print("cycles=%d  niveaux=%d (traités=%d)  matieres=%d  paires=%d (nouvelles: %d)" % (
        db.query(Cycle).count(), db.query(Niveau).count(), traites,
        db.query(Matiere).count(), db.query(MatiereNiveau).count(), pairs))
    print("BTS générique supprimé." if bts_supprime else "BTS générique : déjà absent.")
    db.close()


if __name__ == "__main__":
    run()
