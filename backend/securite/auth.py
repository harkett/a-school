import os

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.securite import comptes
from backend.core.database import get_db
from backend.core.limiter import (
    PLAFOND_DEMANDE_RESET,
    PLAFOND_RENVOI_VERIFICATION,
    PLAFOND_SIGNUP,
    limiter,
)
from backend.core.models_db import ConnexionLog, User
from backend.core.resolution_couple import matiere_nom_de_id, niveau_nom_de_id
from backend.prof.profil import (couple_de_travail, couple_est_au_programme,
                                 matiere_demande_langue)

router = APIRouter()

_ACCESS = "aschool_access"
_REFRESH = "aschool_refresh"
_ACCESS_MAX = 15 * 60
_REFRESH_MAX = 30 * 24 * 3600


def _set_cookies(response: Response, access: str, refresh: str):
    kw = dict(httponly=True, samesite="lax", secure=os.getenv("ENV") == "production")
    response.set_cookie(_ACCESS, access, max_age=_ACCESS_MAX, **kw)
    response.set_cookie(_REFRESH, refresh, max_age=_REFRESH_MAX, **kw)


def _clear_cookies(response: Response):
    kw = dict(httponly=True, samesite="lax", secure=os.getenv("ENV") == "production", path="/")
    response.delete_cookie(_ACCESS, **kw)
    response.delete_cookie(_REFRESH, **kw)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

# `subject` et `langue_lv` ont été RETIRÉS le 31/07 (ménage) : l'écran d'inscription ne les a
# jamais envoyés (Signup.jsx n'envoie que l'e-mail et les deux mots de passe), et aucun autre
# appelant n'existe. Le prof choisit sa matière et sa langue dans Mon profil, une fois son compte
# vérifié — c'est là que le contrôle « cette matière est-elle au programme de ce niveau ? » vit.
class SignupBody(BaseModel):
    email: str
    password: str
    password_confirm: str


class LoginBody(BaseModel):
    email: str
    password: str


class ResendVerificationBody(BaseModel):
    email: str


class RequestResetBody(BaseModel):
    email: str


class ResetPasswordBody(BaseModel):
    token: str
    password: str
    password_confirm: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/auth/signup", status_code=201)
@limiter.limit(PLAFOND_SIGNUP)
def signup(body: SignupBody, request: Request, db: Session = Depends(get_db)):
    if body.password != body.password_confirm:
        raise HTTPException(400, "Les mots de passe ne correspondent pas.")
    if len(body.password) < 8:
        raise HTTPException(400, "Le mot de passe doit contenir au moins 8 caractères.")
    if len(body.password.encode("utf-8")) > 72:
        raise HTTPException(400, "Le mot de passe est trop long (72 caractères maximum).")

    allowed = os.getenv("ALLOWED_EMAILS", "")
    if allowed:
        whitelist = {e.strip().lower() for e in allowed.split(",")}
        if body.email.strip().lower() not in whitelist:
            raise HTTPException(403, "Inscription réservée aux membres autorisés.")

    try:
        user = comptes.create_user(db, body.email, body.password)
    except ValueError as e:
        raise HTTPException(400, str(e))

    token = comptes.generate_email_token(db, user.email, "verify_email")
    try:
        comptes.send_verification_email(user.email, token)
    except Exception as e:
        raise HTTPException(500, f"Erreur envoi email : {e}")

    db.add(ConnexionLog(email=user.email, user_id=user.id, action="signup", ip=request.client.host if request.client else None))
    db.commit()
    return {"status": "ok", "message": "Vérifiez votre boîte mail pour activer votre compte."}


@router.post("/auth/login")
def login(body: LoginBody, request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        user = comptes.authenticate_user(db, body.email, body.password)
    except ValueError as e:
        raise HTTPException(401, str(e))

    access = comptes.create_access_token(user.email)
    refresh = comptes.create_refresh_token(db, user.email)
    _set_cookies(response, access, refresh)
    db.add(ConnexionLog(email=user.email, user_id=user.id, action="login", ip=request.client.host if request.client else None))
    db.commit()
    # LA MÊME fiche que /auth/me, et pas une version courte : l'écran pose cette réponse comme
    # utilisateur connecté sans rappeler /auth/me derrière. Tout champ absent ici manquait à
    # l'application jusqu'au prochain rechargement de page.
    return fiche_utilisateur(db, user, user.email)


@router.post("/auth/resend-verification")
@limiter.limit(PLAFOND_RENVOI_VERIFICATION)
def resend_verification(body: ResendVerificationBody, request: Request, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    # Toujours retourner ok — ne pas révéler si l'email existe
    if user and not user.is_verified:
        token = comptes.generate_email_token(db, email, "verify_email")
        try:
            comptes.send_verification_email(email, token)
        except Exception:
            pass  # Silencieux — le frontend reçoit ok dans tous les cas
    return {"status": "ok"}


@router.post("/auth/request-reset")
@limiter.limit(PLAFOND_DEMANDE_RESET)
def request_reset(body: RequestResetBody, request: Request, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user and user.is_verified:
        token = comptes.generate_email_token(db, email, "reset_password")
        try:
            comptes.send_reset_email(email, token)
        except Exception:
            pass
    return {"status": "ok"}


@router.post("/auth/reset-password")
def reset_password(body: ResetPasswordBody, db: Session = Depends(get_db)):
    if body.password != body.password_confirm:
        raise HTTPException(400, "Les mots de passe ne correspondent pas.")
    if len(body.password) < 8:
        raise HTTPException(400, "Le mot de passe doit contenir au moins 8 caractères.")
    if len(body.password.encode("utf-8")) > 72:
        raise HTTPException(400, "Le mot de passe est trop long (72 caractères maximum).")

    email = comptes.verify_email_token(db, body.token, "reset_password")
    if not email:
        raise HTTPException(400, "Lien invalide ou expiré.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(400, "Lien invalide ou expiré.")

    user.password_hash = comptes._hash_password(body.password)
    comptes.revoke_all_refresh_tokens(db, email)
    db.commit()
    return {"status": "ok"}


@router.get("/auth/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    email = comptes.verify_email_token(db, token, "verify_email")
    if not email:
        raise HTTPException(400, "Lien invalide ou expiré.")
    comptes.mark_user_verified(db, email)
    user = db.query(User).filter(User.email == email).first()
    try:
        from backend.systeme.admin import get_welcome_template, record_email_envoi
        tpl = get_welcome_template(db)
        statut, err = "envoye", None
        try:
            comptes.send_custom_email(
                email,
                user.prenom if user else None,
                tpl.objet,
                tpl.corps,
            )
        except Exception as e:
            statut, err = "echec", str(e)
        record_email_envoi(
            db, modele_slug=tpl.slug, modele_nom=tpl.nom,
            destinataire=email, objet=tpl.objet, statut=statut, erreur=err,
        )
    except Exception:
        pass
    try:
        comptes.send_admin_new_user_notification(email, matiere_nom_de_id(db, user.subject_id) if user else None)
    except Exception:
        pass
    return {"status": "ok", "email": email}


@router.post("/auth/refresh")
def refresh(
    response: Response,
    aschool_refresh: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not aschool_refresh:
        raise HTTPException(401, "Non connecté.")
    try:
        access, new_refresh = comptes.rotate_refresh_token(db, aschool_refresh)
    except ValueError as e:
        _clear_cookies(response)
        raise HTTPException(401, str(e))
    _set_cookies(response, access, new_refresh)
    return {"status": "ok"}


@router.get("/auth/me")
def get_me(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = comptes.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    user = db.query(User).filter(User.email == email).first()
    return fiche_utilisateur(db, user, email)


def fiche_utilisateur(db: Session, user: User | None, email: str) -> dict:
    """LA fiche du prof telle que l'écran la lit — une seule, pour /auth/me ET pour /auth/login.

    POURQUOI ELLE EST DEVENUE UNE FONCTION (07/08/2026). `/auth/login` rendait sa propre fiche,
    plus courte de six champs : ni `travail_matiere`, ni `travail_niveau`, ni `profil_coherent`.
    L'écran pose pourtant cette réponse TELLE QUELLE comme utilisateur connecté (Login.jsx →
    setUser) et n'appelle plus `/auth/me` derrière. Conséquence, à chaque connexion : le couple
    de travail valait « vide », le header ne l'affichait pas, et l'écran de création n'allait
    même pas chercher ses types d'activité — la cartouche « Paramètres » restait absente. Seul
    un F5 réparait, parce qu'il relit `/auth/me`. Deux fiches pour un même prof, c'était une
    divergence qui ne pouvait que se creuser : il n'y en a plus qu'une.

    `email` est passé séparément : à la connexion il vient du compte authentifié, dans /auth/me
    du jeton — et la fonction doit répondre même quand `user` est introuvable (compte effacé
    pendant la session), sans inventer d'identité."""
    # Couple de TRAVAIL résolu EN BASE (travail si posé, sinon profil) — LA lecture unique :
    # le header et l'écran Créer affichent CE couple, le serveur génère avec CE couple.
    # /auth/me lit et rapporte, il ne refuse jamais :
    # lui qui fait s'afficher le message au prof.
    tm, tn, ajuste = couple_de_travail(db, user) if user else (None, None, False)

    # Le couple DU PROFIL (subject_id / niveau_id), pas celui de travail : c'est le profil
    # enregistré qui est en cause, et `couple_ajuste` couvre déjà l'autre cas.
    matiere_profil = matiere_nom_de_id(db, user.subject_id) if user else None
    niveau_profil  = niveau_nom_de_id(db, user.niveau_id)  if user else None

    # LE PROFIL ENREGISTRÉ TIENT-IL TOUJOURS DEBOUT ? (rétabli le 02/08/2026)
    #
    # L'écran lisait déjà `user.profil_coherent === false` (App.jsx) et le serveur ne l'a
    # JAMAIS envoyé : le champ valait `undefined`, `undefined === false` est faux, et cette
    # moitié du garde-fou ne s'exécutait pas une seule fois. Seul `!user.subject` marchait.
    # Ce qui passait à travers : un prof dont la matière a cessé d'être au programme de son
    # niveau — référentiel remplacé, matière retirée, niveau renommé — gardait un profil qui
    # ne veut plus rien dire, sans jamais être ramené sur « Mon profil ».
    #
    # La règle n'est PAS recopiée ici : c'est `couple_est_au_programme` (prof/profil.py), déjà
    # utilisée deux fois pour refuser un couple à l'écriture. Le contrôle d'écriture et celui
    # de lecture disent donc la même chose, à un seul endroit.
    #
    # PROFIL VIDE -> `None` (null), et c'est un choix. `false` prétendrait que le profil est
    # incohérent alors qu'il est simplement absent — l'écran enverrait le prof réparer quelque
    # chose qui n'existe pas. `true` prétendrait l'inverse, aussi faux. `null` dit « la question
    # ne se pose pas encore », et comme `null === false` vaut faux en JavaScript, l'écran se
    # comporte exactement comme avant : un profil vide continue de partir par `!user.subject`.
    profil_coherent = (couple_est_au_programme(db, matiere_profil, niveau_profil)
                       if (matiere_profil and niveau_profil) else None)

    return {
        "email":     email,
        "subject":   matiere_profil,
        "prenom":    user.prenom    if user else None,
        "nom":       user.nom       if user else None,
        "niveau":    niveau_profil,
        "profil_coherent": profil_coherent,
        "langue_lv": user.langue_lv if user else None,
        "travail_matiere": tm,
        "travail_niveau":  tn,
        "couple_ajuste":   ajuste,
        # La matière de travail porte-t-elle une langue ? Lu sur `matieres.demande_langue` —
        # l'écran n'a plus à reconnaître « Langues Vivantes (LV) » à son libellé pour décorer
        # le couple affiché dans le header.
        "travail_demande_langue": matiere_demande_langue(db, user) if user else False,
        # True = ne plus lancer la visite guidée de l'écran Créer (compte inconnu → True :
        # on ne guide pas un compte cassé). L'écran lit CE drapeau, jamais un stockage local.
        "guide_creer_vu":  bool(user.guide_creer_vu) if user else True,
    }


@router.post("/heartbeat")
def heartbeat():
    # Le UserSessionMiddleware met à jour last_seen sur chaque requête authentifiée.
    # Cette route existe uniquement pour que le browser puisse pinger sans payload.
    return {"status": "ok"}


@router.post("/auth/logout-inactivite")
def logout_inactivite(
    aschool_access: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    email = comptes.verify_access_token(aschool_access) if aschool_access else None
    if email:
        db.add(ConnexionLog(email=email, user_id=db.query(User.id).filter(User.email == email).scalar(), action="inactivite_logout"))
        db.commit()
    return {"status": "ok"}


@router.post("/auth/logout")
def logout(
    response: Response,
    aschool_refresh: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if aschool_refresh:
        comptes.revoke_refresh_token(db, aschool_refresh)
    _clear_cookies(response)
    return {"status": "ok"}
