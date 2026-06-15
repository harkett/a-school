-- 011 — Ajout du champ `categorie` sur la table `cycles`.
-- Catégorie (famille) du cycle : 'secondaire' (Collège, Lycée), 'superieur', 'creche',
-- 'primaire', 'maternelle'. Sert à dériver « les matières classiques » par jointure
-- (categorie='secondaire') au lieu des listes en dur du frontend.
--
-- Cette migration ne fait QUE créer la colonne (nullable). Le REMPLISSAGE se fait en
-- Python depuis la liste canonique de backend/seed_programmes.py (pas de noms accentués
-- tapés à la main ici) : lancer `python -m backend.seed_programmes` après cette migration.
ALTER TABLE cycles ADD COLUMN categorie VARCHAR(20);
