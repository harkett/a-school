import uuid
import json
import smtplib
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TOKEN_FILE = Path("data/magic_tokens.json")
SESSION_FILE = Path("data/sessions.json")
TOKEN_EXPIRY_MINUTES = 15
SESSION_EXPIRY_DAYS = 30


def _load_tokens() -> dict:
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    return {}


def _save_tokens(tokens: dict):
    TOKEN_FILE.parent.mkdir(exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(tokens), encoding="utf-8")


def generate_magic_token(email: str, matiere: str = "Français") -> str:
    tokens = _load_tokens()
    now = datetime.now()
    tokens = {k: v for k, v in tokens.items()
              if datetime.fromisoformat(v["expires"]) > now}
    token = str(uuid.uuid4())
    tokens[token] = {
        "email": email,
        "matiere": matiere,
        "expires": (now + timedelta(minutes=TOKEN_EXPIRY_MINUTES)).isoformat()
    }
    _save_tokens(tokens)
    return token


def peek_magic_token(token: str) -> dict | None:
    """Vérifie que le token est valide SANS le consommer."""
    tokens = _load_tokens()
    entry = tokens.get(token)
    if not entry:
        return None
    if datetime.fromisoformat(entry["expires"]) < datetime.now():
        return None
    return {"email": entry["email"], "matiere": entry.get("matiere", "Français")}


def verify_magic_token(token: str) -> dict | None:
    """Vérifie et consomme le token (usage unique)."""
    tokens = _load_tokens()
    entry = tokens.get(token)
    if not entry:
        return None
    if datetime.fromisoformat(entry["expires"]) < datetime.now():
        return None
    del tokens[token]
    _save_tokens(tokens)
    return {"email": entry["email"], "matiere": entry.get("matiere", "Français")}


def send_magic_link(email: str, token: str):
    cfg = st.secrets["smtp"]
    base_url = st.secrets.get("app", {}).get("base_url", "https://school.afia.fr")
    link = f"{base_url}/?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Votre lien de connexion A-SCHOOL"
    msg["From"] = f"A-SCHOOL <{cfg['from_email']}>"
    msg["To"] = email

    html = f"""
    <div style="font-family: sans-serif; max-width: 520px; margin: 0 auto; padding: 2rem;">
        <div style="background: linear-gradient(135deg,#1e3a8a,#2563eb);
                    border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 2rem;">
            <h1 style="color:white; margin:0; font-size:1.5rem;">A-SCHOOL</h1>
            <p style="color:rgba(255,255,255,0.85); margin:0.3rem 0 0 0; font-size:0.9rem;">
                Générateur d'activités pédagogiques
            </p>
        </div>
        <p>Bonjour,</p>
        <p>Cliquez sur le bouton ci-dessous pour vous connecter à A-SCHOOL.
           Ce lien est valable <strong>{TOKEN_EXPIRY_MINUTES} minutes</strong>.</p>
        <div style="text-align:center; margin: 2rem 0;">
            <a href="{link}"
               style="background:#2563eb; color:white; padding:14px 32px;
                      border-radius:8px; text-decoration:none;
                      font-weight:600; font-size:1rem;">
                Se connecter à A-SCHOOL
            </a>
        </div>
        <p style="color:#94a3b8; font-size:0.8rem;">
            Si vous n'avez pas demandé ce lien, ignorez cet email.<br>
            Ce lien ne peut être utilisé qu'une seule fois.
        </p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(cfg["host"], int(cfg["port"])) as server:
        server.starttls()
        server.login(cfg["username"], cfg["password"])
        server.send_message(msg)


def _load_sessions() -> dict:
    if SESSION_FILE.exists():
        return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    return {}


def _save_sessions(sessions: dict):
    SESSION_FILE.parent.mkdir(exist_ok=True)
    SESSION_FILE.write_text(json.dumps(sessions), encoding="utf-8")


def create_session(email: str, matiere: str = "Français") -> str:
    sessions = _load_sessions()
    now = datetime.now()
    sessions = {k: v for k, v in sessions.items()
                if datetime.fromisoformat(v["expires"]) > now}
    token = str(uuid.uuid4())
    sessions[token] = {
        "email": email,
        "matiere": matiere,
        "expires": (now + timedelta(days=SESSION_EXPIRY_DAYS)).isoformat()
    }
    _save_sessions(sessions)
    return token


def get_session(token: str) -> dict | None:
    if not token:
        return None
    sessions = _load_sessions()
    entry = sessions.get(token)
    if not entry:
        return None
    if datetime.fromisoformat(entry["expires"]) < datetime.now():
        del sessions[token]
        _save_sessions(sessions)
        return None
    return {"email": entry["email"], "matiere": entry.get("matiere", "Français")}


def delete_session(token: str):
    sessions = _load_sessions()
    sessions.pop(token, None)
    _save_sessions(sessions)


def notify_admin_connexion(email: str, method: str):
    """Envoie un email à l'admin à chaque nouvelle connexion."""
    cfg = st.secrets["smtp"]
    msg = MIMEText(f"Nouvelle connexion sur A-SCHOOL\n\nEmail : {email}\nMéthode : {method}\nDate : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    msg["Subject"] = f"[A-SCHOOL] Connexion — {email}"
    msg["From"] = f"A-SCHOOL <{cfg['from_email']}>"
    msg["To"] = "harketti@afia.fr"
    with smtplib.SMTP(cfg["host"], int(cfg["port"])) as server:
        server.starttls()
        server.login(cfg["username"], cfg["password"])
        server.send_message(msg)


def get_current_user() -> dict | None:
    """Retourne l'utilisateur connecté (Google ou Magic link) ou None."""
    # Google OAuth
    try:
        if hasattr(st, "user") and st.user.is_logged_in:
            return {
                "email": st.user.email,
                "name": st.user.name,
                "method": "google"
            }
    except AttributeError:
        pass
    # Magic link
    if st.session_state.get("user_email"):
        return {
            "email": st.session_state["user_email"],
            "name": st.session_state.get("user_name", st.session_state["user_email"]),
            "method": "magic_link"
        }
    return None
