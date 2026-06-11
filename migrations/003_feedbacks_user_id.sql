-- 003 — feedbacks : ajoute user_id (nullable) + backfill depuis user_email.
-- Non destructif : user_email reste (DROP a l'etape contract).
ALTER TABLE feedbacks ADD COLUMN user_id INTEGER;

UPDATE feedbacks
SET user_id = (SELECT id FROM users WHERE users.email = feedbacks.user_email)
WHERE user_id IS NULL
