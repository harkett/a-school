import hashlib
import os
import secrets
import smtplib
import uuid
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import bcrypt as _bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.models_db import EmailToken, RefreshToken, User

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30
LOCKOUT_ATTEMPTS = 5
LOCKOUT_MINUTES = 30

def _hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt(12)).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _now() -> datetime:
    return datetime.utcnow()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

def _validate_password(password: str) -> str:
    password = password.strip()
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Mot de passe trop long (72 caractères maximum).")
    return password


def create_user(db: Session, email: str, password: str, subject: str = "", langue_lv: str = "") -> User:
    email = email.strip().lower()
    password = _validate_password(password)
    if db.query(User).filter(User.email == email).first():
        raise ValueError("Un compte existe déjà avec cet email.")
    user = User(
        email=email,
        password_hash=_hash_password(password),
        subject=subject or None,
        langue_lv=langue_lv or None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    email = email.strip().lower()
    password = password.strip()
    user = db.query(User).filter(User.email == email).first()

    _GENERIC = "Email ou mot de passe incorrect."

    if not user:
        _bcrypt.hashpw(b"dummy", _bcrypt.gensalt())  # constant-time même si email inconnu
        raise ValueError(_GENERIC)

    now = _now()
    if user.locked_until and user.locked_until > now:
        remaining = int((user.locked_until - now).total_seconds() / 60) + 1
        raise ValueError(f"Compte bloqué. Réessayez dans {remaining} min.")

    if not _verify_password(password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= LOCKOUT_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            user.failed_attempts = 0
        db.commit()
        raise ValueError(_GENERIC)

    if not user.is_verified:
        raise ValueError("Email non vérifié. Vérifiez votre boîte mail.")

    user.failed_attempts = 0
    user.locked_until = None
    user.last_login = now
    db.commit()
    return user


def mark_user_verified(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_verified = True
        db.commit()


# ---------------------------------------------------------------------------
# Email tokens (verify_email, reset_password)
# ---------------------------------------------------------------------------

def generate_email_token(db: Session, email: str, purpose: str) -> str:
    email = email.strip().lower()
    # Invalidate any previous unused token for same email + purpose
    db.query(EmailToken).filter(
        EmailToken.email == email,
        EmailToken.purpose == purpose,
        EmailToken.used == False,
    ).update({"used": True})

    token = secrets.token_urlsafe(32)
    db.add(EmailToken(
        token=token,
        email=email,
        purpose=purpose,
        expires_at=_now() + timedelta(minutes=60),
    ))
    db.commit()
    return token


def verify_email_token(db: Session, token: str, purpose: str) -> Optional[str]:
    entry = db.query(EmailToken).filter(
        EmailToken.token == token,
        EmailToken.purpose == purpose,
        EmailToken.used == False,
    ).first()
    if not entry or entry.expires_at < _now():
        return None
    entry.used = True
    db.commit()
    return entry.email


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def create_access_token(email: str) -> str:
    return jwt.encode(
        {"sub": email, "type": "access",
         "exp": _now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
        SECRET_KEY, algorithm=ALGORITHM,
    )


def create_refresh_token(db: Session, email: str) -> str:
    token = jwt.encode(
        {"sub": email, "type": "refresh", "jti": str(uuid.uuid4()),
         "exp": _now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)},
        SECRET_KEY, algorithm=ALGORITHM,
    )
    db.add(RefreshToken(
        user_email=email,
        token_hash=_hash_token(token),
        expires_at=_now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    db.commit()
    return token


def verify_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def rotate_refresh_token(db: Session, token: str) -> tuple[str, str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise ValueError("Token invalide.")
    if payload.get("type") != "refresh":
        raise ValueError("Token invalide.")

    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == _hash_token(token),
        RefreshToken.revoked == False,
    ).first()
    if not db_token or db_token.expires_at < _now():
        raise ValueError("Session expirée. Reconnectez-vous.")

    db_token.revoked = True
    db.commit()

    email = payload["sub"]
    return create_access_token(email), create_refresh_token(db, email)


def revoke_refresh_token(db: Session, token: str):
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == _hash_token(token),
    ).first()
    if db_token:
        db_token.revoked = True
        db.commit()


def revoke_all_refresh_tokens(db: Session, email: str):
    db.query(RefreshToken).filter(
        RefreshToken.user_email == email,
        RefreshToken.revoked == False,
    ).update({"revoked": True})
    db.commit()


# ---------------------------------------------------------------------------
# Email sending
# ---------------------------------------------------------------------------

def _smtp_send(msg):
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USERNAME", "")
    pwd = os.getenv("SMTP_PASSWORD", "")
    with smtplib.SMTP(host, port) as s:
        s.ehlo()
        s.starttls()
        s.login(user, pwd)
        s.send_message(msg)


def send_feedback_notification(prof: dict, message: str, rating: int, category: str | None, type: str = "feedback"):
    """Notifie l'admin par email à chaque feedback reçu — SMTP direct, sans A-FEEDBACK."""
    from_addr = os.getenv("FEEDBACK_FROM", "A-SCHOOL Feedback <feedback@aschool.fr>")
    to_addr   = os.getenv("FEEDBACK_NOTIFY_EMAIL", "contact@aschool.fr")
    stars     = "★" * rating + "☆" * (5 - rating)

    prenom  = prof.get("prenom") or ""
    nom     = prof.get("nom") or ""
    nom_complet = f"{prenom} {nom}".strip() or "—"
    matiere = prof.get("subject") or "—"
    niveau  = prof.get("niveau") or "—"
    email   = prof.get("email") or "—"
    cat     = category or "—"

    msg = MIMEMultipart("alternative")
    sujet_email = f"[A-SCHOOL] Nouvelle notation — {rating}/5" if type == "notation" else "[A-SCHOOL] Nouveau feedback"
    msg["Subject"] = sujet_email
    msg["From"]    = from_addr
    msg["To"]      = to_addr

    plain = (
        f"Nouveau feedback A-SCHOOL\n\n"
        f"Prénom / Nom : {nom_complet}\n"
        f"Email        : {email}\n"
        f"Matière      : {matiere}\n"
        f"Niveau       : {niveau}\n"
        f"Note         : {rating}/5  {stars}\n"
        f"Catégorie    : {cat}\n\n"
        f"Message :\n{message}\n"
    )

    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:2rem;">
      <div style="background:linear-gradient(135deg,#1e3a8a,#1F6EEB);border-radius:12px;padding:1.2rem 2rem;margin-bottom:1.5rem;">
        <h1 style="color:white;margin:0;font-size:1.3rem;">
          <span style="color:#e05a6e;">A</span>-SCHOOL — Nouveau feedback
        </h1>
      </div>

      <table style="width:100%;border-collapse:collapse;font-size:0.9rem;margin-bottom:1.5rem;">
        <tr style="background:#f8fafc;">
          <td style="padding:8px 12px;color:#64748b;font-weight:600;width:140px;">Prénom / Nom</td>
          <td style="padding:8px 12px;color:#1e293b;">{nom_complet}</td>
        </tr>
        <tr>
          <td style="padding:8px 12px;color:#64748b;font-weight:600;">Email</td>
          <td style="padding:8px 12px;"><a href="mailto:{email}" style="color:#1F6EEB;">{email}</a></td>
        </tr>
        <tr style="background:#f8fafc;">
          <td style="padding:8px 12px;color:#64748b;font-weight:600;">Matière</td>
          <td style="padding:8px 12px;color:#1e293b;">{matiere}</td>
        </tr>
        <tr>
          <td style="padding:8px 12px;color:#64748b;font-weight:600;">Niveau</td>
          <td style="padding:8px 12px;color:#1e293b;">{niveau}</td>
        </tr>
        <tr style="background:#f8fafc;">
          <td style="padding:8px 12px;color:#64748b;font-weight:600;">Note</td>
          <td style="padding:8px 12px;color:#1e293b;font-size:1.1rem;">{stars} <span style="font-size:0.85rem;color:#64748b;">({rating}/5)</span></td>
        </tr>
        <tr>
          <td style="padding:8px 12px;color:#64748b;font-weight:600;">Catégorie</td>
          <td style="padding:8px 12px;color:#1e293b;">{cat}</td>
        </tr>
      </table>

      <div style="background:#f1f5f9;border-left:4px solid #1F6EEB;border-radius:4px;padding:1rem 1.2rem;">
        <div style="color:#64748b;font-size:0.75rem;font-weight:600;margin-bottom:6px;">MESSAGE</div>
        <p style="color:#1e293b;margin:0;line-height:1.6;white-space:pre-wrap;">{message}</p>
      </div>

      <p style="color:#94a3b8;font-size:0.75rem;margin-top:1.5rem;">
        A-SCHOOL · school.afia.fr · feedback enregistré en base de données
      </p>
    </div>
    """

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    _smtp_send(msg)


def send_custom_email(email: str, prenom: str | None, subject: str, body: str):
    """Envoie un email personnalisé — utilisé pour le welcome email et les envois admin manuels."""
    app_url = os.getenv("APP_URL", "https://school.afia.fr")
    from_addr = os.getenv("SMTP_FROM", "A-SCHOOL <contact@aschool.fr>")
    nom_prenom = prenom or "cher(e) enseignant(e)"
    body_rendered = body.replace("{prenom}", nom_prenom).replace("{email}", email)
    body_html = body_rendered.replace("\n", "<br>")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = email

    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:2rem;">
      <div style="background:linear-gradient(135deg,#1e3a8a,#1F6EEB);border-radius:12px;padding:1.5rem 2rem;margin-bottom:2rem;">
        <h1 style="color:white;margin:0;font-size:1.5rem;">
          <span style="color:#A63045;">A</span>-SCHOOL
        </h1>
        <p style="color:rgba(255,255,255,0.85);margin:0.3rem 0 0;font-size:0.9rem;">
          Générateur d'activités pédagogiques
        </p>
      </div>
      <div style="font-size:0.95rem;color:#1e293b;line-height:1.75;">
        {body_html}
      </div>
      <div style="text-align:center;margin:2.5rem 0;">
        <a href="{app_url}"
           style="background:#1F6EEB;color:white;padding:14px 32px;
                  border-radius:8px;text-decoration:none;
                  font-weight:600;font-size:1rem;display:inline-block;">
          Accéder à A-SCHOOL
        </a>
      </div>
      <p style="color:#94a3b8;font-size:0.75rem;border-top:1px solid #e2e8f0;padding-top:1rem;margin-top:1rem;">
        A-SCHOOL · school.afia.fr
      </p>
    </div>
    """

    msg.attach(MIMEText(body_rendered, "plain"))
    msg.attach(MIMEText(html, "html"))
    _smtp_send(msg)


def send_reset_email(email: str, token: str):
    app_url = os.getenv("APP_URL", "https://school.afia.fr")
    from_addr = os.getenv("SMTP_FROM", "A-SCHOOL <contact@aschool.fr>")
    link = f"{app_url}/reset-password?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Réinitialisation de votre mot de passe A-SCHOOL"
    msg["From"] = from_addr
    msg["To"] = email

    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:2rem;">
      <div style="background:linear-gradient(135deg,#1e3a8a,#1F6EEB);
                  border-radius:12px;padding:1.5rem 2rem;margin-bottom:2rem;">
        <h1 style="color:white;margin:0;font-size:1.5rem;">
          <span style="color:#A63045;">A</span>-SCHOOL
        </h1>
        <p style="color:rgba(255,255,255,0.85);margin:0.3rem 0 0;font-size:0.9rem;">
          Générateur d'activités pédagogiques
        </p>
      </div>
      <p>Bonjour,</p>
      <p>Vous avez demandé la réinitialisation de votre mot de passe A-SCHOOL.
         Cliquez sur le bouton ci-dessous pour choisir un nouveau mot de passe.
         Ce lien est valable <strong>60 minutes</strong>.</p>
      <div style="text-align:center;margin:2rem 0;">
        <a href="{link}"
           style="background:#1F6EEB;color:white;padding:14px 32px;
                  border-radius:8px;text-decoration:none;
                  font-weight:600;font-size:1rem;">
          Réinitialiser mon mot de passe
        </a>
      </div>
      <p style="color:#94a3b8;font-size:0.8rem;">
        Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.<br>
        Ce lien ne peut être utilisé qu'une seule fois.
      </p>
    </div>
    """
    plain = (
        f"Bonjour,\n\nRéinitialisez votre mot de passe A-SCHOOL en cliquant sur ce lien :\n{link}\n\n"
        f"Ce lien est valable 60 minutes et ne peut être utilisé qu'une seule fois.\n\n"
        f"Si vous n'avez pas demandé cette réinitialisation, ignorez cet email."
    )
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    _smtp_send(msg)


def send_verification_email(email: str, token: str):
    app_url = os.getenv("APP_URL", "https://school.afia.fr")
    from_addr = os.getenv("SMTP_FROM", "A-SCHOOL <contact@aschool.fr>")
    link = f"{app_url}/verify-email?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Activez votre compte A-SCHOOL"
    msg["From"] = from_addr
    msg["To"] = email

    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:2rem;">
      <div style="background:linear-gradient(135deg,#1e3a8a,#1F6EEB);
                  border-radius:12px;padding:1.5rem 2rem;margin-bottom:2rem;">
        <h1 style="color:white;margin:0;font-size:1.5rem;">
          <span style="color:#A63045;">A</span>-SCHOOL
        </h1>
        <p style="color:rgba(255,255,255,0.85);margin:0.3rem 0 0;font-size:0.9rem;">
          Générateur d'activités pédagogiques
        </p>
      </div>
      <p>Bonjour,</p>
      <p>Cliquez sur le bouton ci-dessous pour activer votre compte A-SCHOOL.
         Ce lien est valable <strong>60 minutes</strong>.</p>
      <div style="text-align:center;margin:2rem 0;">
        <a href="{link}"
           style="background:#1F6EEB;color:white;padding:14px 32px;
                  border-radius:8px;text-decoration:none;
                  font-weight:600;font-size:1rem;">
          Activer mon compte
        </a>
      </div>
      <p style="color:#94a3b8;font-size:0.8rem;">
        Si vous n'avez pas créé de compte, ignorez cet email.<br>
        Ce lien ne peut être utilisé qu'une seule fois.
      </p>
    </div>
    """
    plain = (
        f"Bonjour,\n\nActivez votre compte A-SCHOOL en cliquant sur ce lien :\n{link}\n\n"
        f"Ce lien est valable 60 minutes et ne peut être utilisé qu'une seule fois.\n\n"
        f"Si vous n'avez pas créé de compte, ignorez cet email."
    )
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    _smtp_send(msg)
