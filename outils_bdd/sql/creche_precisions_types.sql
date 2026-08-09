-- ============================================================================
-- Creche · BMG_0-3 (referentiel 2) — les 4 PRECISIONS de type d'activite,
-- posees a la main dans `aschool_dev` le 08/08/2026.
--
-- Une precision est un sous-type : le prof choisit « jeu avec un jouet », puis
-- « encastrement dans des trous ». `source = 'admin'` dit qu'elle a ete saisie,
-- non deduite par l'IA. `ordre` fixe l'affichage dans la liste.
--
-- Les ids sont ceux des types du referentiel 2 dans aschool_dev :
--   75 = jeu avec un jouet
--   77 = activite recreative
--   82 = activite psychosociale manuelle et artistique
-- Six des neuf types de ce referentiel n'ont volontairement pas de precision :
-- le prof choisit alors un type sans sous-type.
--
-- Rejouer ce fichier tel quel sur une AUTRE base n'a pas de sens — les ids y
-- seraient differents. Pour une base de demonstration, les precisions se
-- copient avec le referentiel :
--   \copy (SELECT p.* FROM referentiel_type_precisions p
--          JOIN types_activite t ON t.id = p.type_activite_id
--          WHERE t.referentiel_id = 2) TO STDOUT
-- ============================================================================

BEGIN;
INSERT INTO referentiel_type_precisions (type_activite_id, libelle, ordre, source) VALUES
  (75, 'dénombrement des éléments',   0, 'admin'),
  (75, 'encastrement dans des trous', 1, 'admin'),
  (77, 'jeu chanté',                  0, 'admin'),
  (82, 'empreinte de main',           0, 'admin');
COMMIT;
