-- 004 — feature_votes : ajoute user_id (nullable) + backfill depuis user_email.
-- Non destructif : user_email reste (DROP a l'etape contract).
ALTER TABLE feature_votes ADD COLUMN user_id INTEGER;

UPDATE feature_votes
SET user_id = (SELECT id FROM users WHERE users.email = feature_votes.user_email)
WHERE user_id IS NULL
