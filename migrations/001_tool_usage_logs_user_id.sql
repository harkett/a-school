-- 001 — tool_usage_logs : ajoute user_id (nullable) et le remplit depuis user_email.
-- Table temoin du chantier user_email -> user_id.
-- Non destructif : user_email reste en place (le DROP viendra a l'etape contract).
ALTER TABLE tool_usage_logs ADD COLUMN user_id INTEGER;

UPDATE tool_usage_logs
SET user_id = (SELECT id FROM users WHERE users.email = tool_usage_logs.user_email)
WHERE user_id IS NULL
