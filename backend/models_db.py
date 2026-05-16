from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, DateTime, Index, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    subject: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prenom: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nom: Mapped[str | None] = mapped_column(String(64), nullable=True)
    niveau: Mapped[str | None] = mapped_column(String(16), nullable=True)
    langue_lv: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1', nullable=False)


class EmailToken(Base):
    __tablename__ = "email_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(86), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)  # verify_email | reset_password
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ConnexionLog(Base):
    __tablename__ = "connexion_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(16), nullable=False)  # signup | login
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="feedback")  # feedback | notation
    message: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    statut: Mapped[str] = mapped_column(String(16), nullable=False, default="nouveau")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    attachment_path: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")


class SequenceSauvegardee(Base):
    __tablename__ = "sequences_sauvegardees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    matiere: Mapped[str] = mapped_column(String(64), nullable=False)
    niveau: Mapped[str] = mapped_column(String(32), nullable=False)
    theme: Mapped[str] = mapped_column(String(300), nullable=False)
    duree: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")
    description_classe: Mapped[str] = mapped_column(Text, nullable=False, default="")
    resultat: Mapped[str] = mapped_column(Text, nullable=False)
    partagee: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='0')
    anonyme: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='0')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ActiviteSauvegardee(Base):
    __tablename__ = "activites_sauvegardees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    activite_key: Mapped[str] = mapped_column(String(64), nullable=False)
    activite_label: Mapped[str] = mapped_column(String(128), nullable=False)
    niveau: Mapped[str] = mapped_column(String(32), nullable=False)
    sous_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avec_correction: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    matiere: Mapped[str | None] = mapped_column(String(64), nullable=True)
    objet: Mapped[str | None] = mapped_column(String(150), nullable=True)
    partagee: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='0')
    anonyme: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='0')
    texte_source: Mapped[str] = mapped_column(Text, nullable=False)
    resultat: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)


# ---------------------------------------------------------------------------
# Admin backoffice — Phase 0
# ---------------------------------------------------------------------------

class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    session_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(100), nullable=True)
    os: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    login_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def is_online(self) -> bool:
        delta = datetime.now(timezone.utc) - self.last_seen.replace(tzinfo=timezone.utc)
        return self.is_active and delta.total_seconds() < 90


class FailedLoginAttempt(Base):
    __tablename__ = "failed_login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    attempt_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AdminAlert(Base):
    __tablename__ = "admin_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class FeatureVote(Base):
    __tablename__ = "feature_votes"
    __table_args__ = (Index("ix_feature_votes_unique", "user_email", "feature_key", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    feature_key: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class FicheMatiere(Base):
    __tablename__ = "fiches_matieres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    matiere_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    statut: Mapped[str] = mapped_column(String(16), nullable=False, default="brouillon")  # brouillon | publie | a_reviser
    accroche: Mapped[str | None] = mapped_column(Text, nullable=True)
    pour_qui: Mapped[str | None] = mapped_column(Text, nullable=True)
    ameliorations: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ToolUsageLog(Base):
    __tablename__ = "tool_usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tool: Mapped[str] = mapped_column(String(32), nullable=False)  # sequence | optimiseur
    score_label: Mapped[str | None] = mapped_column(String(32), nullable=True)  # Bon | Moyen | À revoir
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# STT — Speech-to-Text (Deepgram)
# Spec : MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md §3.3, §7.3, §9.4
# ---------------------------------------------------------------------------

# Constantes de validation (discipline applicative — pas de CHECK SQL)
STT_MESSAGE_MODES = ("neutral", "volume")
STT_MESSAGE_CODES = ("preventive", "unavailable", "saturation", "session_expired")
STT_CREDIT_EVENT_TYPES = ("snapshot", "recharge", "reset")


class STTCreditHistory(Base):
    __tablename__ = "stt_credit_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)  # snapshot | recharge | reset
    balance_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    remaining_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_total_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class STTMessage(Base):
    __tablename__ = "stt_messages"
    __table_args__ = (Index("ix_stt_messages_mode_code", "mode", "code", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)  # neutral | volume
    code: Mapped[str] = mapped_column(String(32), nullable=False)  # preventive | unavailable | saturation | session_expired
    content: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class STTKeytermGlobal(Base):
    __tablename__ = "stt_keyterms_global"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class STTKeytermBySubject(Base):
    __tablename__ = "stt_keyterms_by_subject"
    __table_args__ = (
        Index("ix_stt_keyterms_by_subject_uniq", "subject", "term", unique=True),
        Index("ix_stt_keyterms_by_subject_subject", "subject"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(64), nullable=False)
    term: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
