-- 002 — sequences_sauvegardees : ajoute user_id (nullable) + backfill depuis user_email.
-- Non destructif : user_email reste (DROP a l'etape contract).
ALTER TABLE sequences_sauvegardees ADD COLUMN user_id INTEGER;

UPDATE sequences_sauvegardees
SET user_id = (SELECT id FROM users WHERE users.email = sequences_sauvegardees.user_email)
WHERE user_id IS NULL
