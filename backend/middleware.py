import os
from datetime import datetime

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.database import SessionLocal
from backend.models_db import User, UserSession

_REFRESH_COOKIE = "aschool_refresh"
_ALGO = "HS256"


class UserSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get(_REFRESH_COOKIE)
        email = None
        session_key = None

        # Phase 1 — vérification AVANT traitement (force-logout immédiat)
        if token:
            try:
                payload = jwt.decode(
                    token, os.getenv("JWT_SECRET", ""), algorithms=[_ALGO]
                )
                if payload.get("type") == "refresh":
                    email = payload.get("sub")
                    session_key = payload.get("jti")
                    if session_key:
                        db = SessionLocal()
                        try:
                            session = (
                                db.query(UserSession)
                                .filter(UserSession.session_key == session_key)
                                .first()
                            )
                            if session and not session.is_active:
                                resp = Response(
                                    '{"detail":"Session déconnectée."}',
                                    status_code=401,
                                    media_type="application/json",
                                )
                                resp.delete_cookie("aschool_refresh")
                                resp.delete_cookie("aschool_access")
                                return resp
                        finally:
                            db.close()
            except JWTError:
                pass

        # Phase 2 — traitement de la requête
        response = await call_next(request)

        # Phase 3 — upsert UserSession (crée ou met à jour last_seen)
        if email and session_key:
            try:
                from user_agents import parse as parse_ua

                ua_string = request.headers.get("user-agent", "")
                ua = parse_ua(ua_string)
                db = SessionLocal()
                try:
                    session = (
                        db.query(UserSession)
                        .filter(UserSession.session_key == session_key)
                        .first()
                    )
                    if session:
                        now = datetime.utcnow()
                        gap = (now - session.last_seen).total_seconds()
                        session.last_seen = now
                        # Reprise après 30+ min d'inactivité → met à jour last_login
                        if gap > 1800:
                            user = db.query(User).filter(User.email == email).first()
                            if user:
                                user.last_login = now
                    else:
                        db.add(
                            UserSession(
                                user_email=email,
                                session_key=session_key,
                                ip_address=request.client.host if request.client else None,
                                user_agent=ua_string[:500],
                                browser=f"{ua.browser.family} {ua.browser.version_string}"[:100],
                                os=f"{ua.os.family} {ua.os.version_string}"[:100],
                                device_type=(
                                    "mobile" if ua.is_mobile
                                    else "tablet" if ua.is_tablet
                                    else "desktop"
                                ),
                            )
                        )
                    db.commit()
                except Exception:
                    db.rollback()
                finally:
                    db.close()
            except Exception:
                pass  # Ne jamais bloquer une requête à cause du tracking de session

        return response
