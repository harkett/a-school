-- 007 — refresh_tokens : ajoute user_id (nullable) + backfill depuis user_email.
-- Non destructif : user_email reste (DROP au contract).
ALTER TABLE refresh_tokens ADD COLUMN user_id INTEGER;

UPDATE refresh_tokens
SET user_id = (SELECT id FROM users WHERE users.email = refresh_tokens.user_email)
WHERE user_id IS NULL
