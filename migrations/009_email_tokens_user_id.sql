-- 009 — email_tokens (JOURNAL) : ajoute user_id NULLABLE + backfill depuis email.
-- La colonne email RESTE (un token peut viser un email sans user : reset anti-enumeration, user supprime).
-- user_id rempli quand l'email correspond a un user, NULL sinon (≈ 1 ligne attendue NULL).
ALTER TABLE email_tokens ADD COLUMN user_id INTEGER;

UPDATE email_tokens
SET user_id = (SELECT id FROM users WHERE users.email = email_tokens.email)
WHERE user_id IS NULL
