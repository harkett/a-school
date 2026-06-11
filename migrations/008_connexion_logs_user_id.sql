-- 008 — connexion_logs (JOURNAL) : ajoute user_id NULLABLE + backfill depuis email.
-- La colonne email RESTE (elle enregistre aussi des non-users : logins d'adresses inconnues).
-- user_id rempli quand l'email correspond a un user, NULL sinon (≈ 13 lignes attendues NULL).
ALTER TABLE connexion_logs ADD COLUMN user_id INTEGER;

UPDATE connexion_logs
SET user_id = (SELECT id FROM users WHERE users.email = connexion_logs.email)
WHERE user_id IS NULL
