-- 005 — activites_sauvegardees : ajoute user_id (nullable) + backfill depuis user_email.
-- Table centrale (cœur "Mes activites"). Non destructif : user_email reste (DROP au contract).
ALTER TABLE activites_sauvegardees ADD COLUMN user_id INTEGER;

UPDATE activites_sauvegardees
SET user_id = (SELECT id FROM users WHERE users.email = activites_sauvegardees.user_email)
WHERE user_id IS NULL
