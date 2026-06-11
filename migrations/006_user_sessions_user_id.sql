-- 006 — user_sessions : ajoute user_id (nullable) + backfill depuis user_email.
-- Non destructif : user_email reste (DROP au contract).
ALTER TABLE user_sessions ADD COLUMN user_id INTEGER;

UPDATE user_sessions
SET user_id = (SELECT id FROM users WHERE users.email = user_sessions.user_email)
WHERE user_id IS NULL
