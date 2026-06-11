-- 010 — CONTRACT : sur les 7 tables prof, passe la relation sur user_id et SUPPRIME user_email.
-- Methode SQLite : reconstruction de table (CREATE __new + INSERT SELECT + DROP + RENAME + index).
-- user_id devient INTEGER NOT NULL REFERENCES users(id). Les colonnes user_email disparaissent.
-- foreign_keys=ON (runner) => chaque INSERT valide que user_id reference un users.id reel, sinon ROLLBACK.
-- Les journaux (connexion_logs, email_tokens) NE SONT PAS touches : leur colonne email reste.

-- ===== refresh_tokens =====
CREATE TABLE refresh_tokens__new (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token_hash VARCHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    revoked BOOLEAN NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (token_hash)
);
INSERT INTO refresh_tokens__new (id, user_id, token_hash, expires_at, revoked)
    SELECT id, user_id, token_hash, expires_at, revoked FROM refresh_tokens;
DROP TABLE refresh_tokens;
ALTER TABLE refresh_tokens__new RENAME TO refresh_tokens;
CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens (user_id);

-- ===== feedbacks =====
CREATE TABLE feedbacks__new (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    message TEXT NOT NULL,
    rating INTEGER NOT NULL,
    category VARCHAR(64),
    created_at DATETIME NOT NULL,
    type VARCHAR(16) DEFAULT 'feedback',
    statut VARCHAR(16) NOT NULL DEFAULT 'nouveau',
    updated_at DATETIME,
    attachment_path VARCHAR(500),
    PRIMARY KEY (id)
);
INSERT INTO feedbacks__new (id, user_id, message, rating, category, created_at, type, statut, updated_at, attachment_path)
    SELECT id, user_id, message, rating, category, created_at, type, statut, updated_at, attachment_path FROM feedbacks;
DROP TABLE feedbacks;
ALTER TABLE feedbacks__new RENAME TO feedbacks;
CREATE INDEX ix_feedbacks_user_id ON feedbacks (user_id);

-- ===== sequences_sauvegardees =====
CREATE TABLE sequences_sauvegardees__new (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    matiere VARCHAR(64) NOT NULL,
    niveau VARCHAR(32) NOT NULL,
    theme VARCHAR(300) NOT NULL,
    duree INTEGER NOT NULL,
    mode VARCHAR(32) NOT NULL,
    description_classe TEXT NOT NULL,
    resultat TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    anonyme BOOLEAN NOT NULL DEFAULT 0,
    partagee BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (id)
);
INSERT INTO sequences_sauvegardees__new (id, user_id, matiere, niveau, theme, duree, mode, description_classe, resultat, created_at, anonyme, partagee)
    SELECT id, user_id, matiere, niveau, theme, duree, mode, description_classe, resultat, created_at, anonyme, partagee FROM sequences_sauvegardees;
DROP TABLE sequences_sauvegardees;
ALTER TABLE sequences_sauvegardees__new RENAME TO sequences_sauvegardees;
CREATE INDEX ix_sequences_sauvegardees_user_id ON sequences_sauvegardees (user_id);

-- ===== activites_sauvegardees =====
CREATE TABLE activites_sauvegardees__new (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    activite_key VARCHAR(64) NOT NULL,
    activite_label VARCHAR(128) NOT NULL,
    niveau VARCHAR(32) NOT NULL,
    sous_type VARCHAR(64),
    nb INTEGER,
    avec_correction BOOLEAN NOT NULL,
    texte_source TEXT NOT NULL,
    resultat TEXT NOT NULL,
    objet TEXT DEFAULT NULL,
    partagee BOOLEAN NOT NULL DEFAULT 0,
    matiere VARCHAR(64),
    created_at DATETIME,
    anonyme BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (id)
);
INSERT INTO activites_sauvegardees__new (id, user_id, activite_key, activite_label, niveau, sous_type, nb, avec_correction, texte_source, resultat, objet, partagee, matiere, created_at, anonyme)
    SELECT id, user_id, activite_key, activite_label, niveau, sous_type, nb, avec_correction, texte_source, resultat, objet, partagee, matiere, created_at, anonyme FROM activites_sauvegardees;
DROP TABLE activites_sauvegardees;
ALTER TABLE activites_sauvegardees__new RENAME TO activites_sauvegardees;
CREATE INDEX ix_activites_sauvegardees_user_id ON activites_sauvegardees (user_id);

-- ===== user_sessions =====
CREATE TABLE user_sessions__new (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    session_key VARCHAR(64) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    browser VARCHAR(100),
    os VARCHAR(100),
    device_type VARCHAR(20),
    login_at DATETIME NOT NULL,
    last_seen DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (session_key)
);
INSERT INTO user_sessions__new (id, user_id, session_key, ip_address, user_agent, browser, os, device_type, login_at, last_seen, is_active)
    SELECT id, user_id, session_key, ip_address, user_agent, browser, os, device_type, login_at, last_seen, is_active FROM user_sessions;
DROP TABLE user_sessions;
ALTER TABLE user_sessions__new RENAME TO user_sessions;
CREATE INDEX ix_user_sessions_user_id ON user_sessions (user_id);

-- ===== feature_votes =====
CREATE TABLE feature_votes__new (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    feature_key VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id)
);
INSERT INTO feature_votes__new (id, user_id, feature_key, created_at)
    SELECT id, user_id, feature_key, created_at FROM feature_votes;
DROP TABLE feature_votes;
ALTER TABLE feature_votes__new RENAME TO feature_votes;
CREATE INDEX ix_feature_votes_user_id ON feature_votes (user_id);
CREATE UNIQUE INDEX ix_feature_votes_unique ON feature_votes (user_id, feature_key);

-- ===== tool_usage_logs =====
CREATE TABLE tool_usage_logs__new (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    tool VARCHAR(32) NOT NULL,
    score_label VARCHAR(32),
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id)
);
INSERT INTO tool_usage_logs__new (id, user_id, tool, score_label, created_at)
    SELECT id, user_id, tool, score_label, created_at FROM tool_usage_logs;
DROP TABLE tool_usage_logs;
ALTER TABLE tool_usage_logs__new RENAME TO tool_usage_logs;
CREATE INDEX ix_tool_usage_logs_user_id ON tool_usage_logs (user_id);
