-- 012_create_referentiels.sql
-- Morceau 1 (fondation) du chantier « automatiser le Temps 3 ».
-- Cree la table `referentiels` : la liste DONNEE « couple -> referentiel / collection ».
-- Les regles de decoupe (chunk, frontiere, tags) restent dans la fiche Python (= code).
-- N'ajoute AUCUN routage ni branchement (morceaux 2 et 3) : rien ne lit encore cette table.
-- Idempotent : CREATE TABLE IF NOT EXISTS + INSERT OR IGNORE.

CREATE TABLE IF NOT EXISTS referentiels (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    niveau_id   INTEGER NOT NULL REFERENCES niveaux(id),
    matiere_id  INTEGER REFERENCES matieres(id),
    nom_fixe    TEXT NOT NULL UNIQUE,
    collection  TEXT NOT NULL,
    filtres     TEXT,
    fichier     TEXT,
    source      TEXT,
    date_doc    TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (niveau_id, matiere_id)
);

-- Seed idempotent de la SEULE ligne existante : BTS CIEL option A.
-- niveau_id resolu par le NOM (stable) et non un id en dur (robuste entre bases).
-- matiere_id NULL = le referentiel couvre TOUT le niveau (les 9 matieres du diplome).
INSERT OR IGNORE INTO referentiels (niveau_id, matiere_id, nom_fixe, collection, filtres, fichier, source, date_doc)
SELECT n.id, NULL, 'bts_ciel_optionA', 'bts_ciel_optionA', '{"option":"A"}', '15324-ref-bts-ciel-vpub-v01.pdf', 'REF-BTS-CIEL-2023', '2023'
FROM niveaux n
WHERE n.nom = 'BTS CIEL option A';
