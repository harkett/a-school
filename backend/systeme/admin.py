import os
import re
import secrets
import unicodedata
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.securite.audit import log_admin_action
from backend.core.database import get_db, get_db_size_mb, engine
from backend.core.limiter import limiter
from backend.core.llm_prompts import PROMPTS
from backend.core.models_db import ActiviteSauvegardee, AdminAlert, AdminAuditLog, ConnexionLog, EmailEnvoi, EmailTemplate, EmailToken, FailedLoginAttempt, Feedback, RefreshToken, Setting, User, UserSession

router = APIRouter()

_COOKIE  = "aschool_admin"
_MAX_AGE = 4 * 3600
_ALGO    = "HS256"


def _make_admin_token() -> str:
    secret = os.getenv("JWT_SECRET", "")
    exp = datetime.utcnow() + timedelta(hours=4)
    return jwt.encode({"sub": "admin", "role": "admin", "exp": exp}, secret, algorithm=_ALGO)


def _verify_admin_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET", ""), algorithms=[_ALGO])
        return payload.get("role") == "admin"
    except JWTError:
        return False


def _require_admin(aschool_admin: str = Cookie(default=None)):
    if not aschool_admin or not _verify_admin_token(aschool_admin):
        raise HTTPException(401, "Accès réservé à l'administrateur.")


SETTING_DEFAULTS = {
    # Modèle LLM texte — administrable à chaud (Phase 4.1.a). Défaut = valeur historique
    # du .env ; surchargée par une ligne `ai_model` en base si présente. Lu au runtime
    # via get_ai_model(), jamais figé au boot.
    "ai_model": "llama-3.3-70b-versatile",
    # Fournisseur LLM texte — administrable à chaud (Phase 4.1.e). Défaut = valeur historique
    # du .env ; surchargée par une ligne `ai_provider` en base si présente. Lu au runtime via
    # get_ai_provider(), jamais figé au boot. Même moule que ai_model. (La clé API reste un
    # secret hors base — sujet séparé, pas traité ici.)
    "ai_provider": "groq",
    "welcome_email_subject": "Bienvenue sur aSchool !",
    "welcome_email_body": (
        "Bonjour {prenom},\n\n"
        "Votre compte aSchool est maintenant actif !\n\n"
        "aSchool est votre assistant pédagogique : générez des activités adaptées à votre matière "
        "et à vos élèves en quelques secondes.\n\n"
        "Connectez-vous dès maintenant sur aschool.fr\n\n"
        "Parlez-en à vos collègues — plus on est nombreux, plus aSchool s'améliore !\n\n"
        "Bonne utilisation,\nL'équipe aSchool"
    ),
    # max_tokens administrable (Phase 4.1.c) — HYBRIDE : un défaut global + surcharges
    # par outil seulement là où c'est nécessaire. Lu au runtime via get_max_tokens(db, outil),
    # jamais figé au boot (rechargeable à chaud, comme ai_model). Valeurs en chaîne (Setting.value).
    # SEEDING des 3 surcharges = NON NÉGOCIABLE : sans elles, ambiguïtés/séquence/optimiseur
    # retomberaient au défaut 2048 -> activités tronquées (régression). activité/exemple/consigne
    # n'ont PAS de clé -> ils résolvent sur le défaut global.
    "max_tokens_default": "2048",
    "max_tokens_ambiguites": "3000",
    "max_tokens_sequence": "4000",
    "max_tokens_optimiseur": "6000",
    # Température LLM — administrable à chaud (Phase 4.1.d), GLOBALE (un seul réglage pour tous
    # les outils de génération). Défaut = "" (non réglée) -> get_temperature() renvoie None ->
    # generate() n'envoie rien -> le fournisseur applique SON défaut = comportement historique,
    # zéro régression. L'optimiseur n'utilise PAS ce réglage (température 0 figée en dur, JSON
    # déterministe). « Plus haut » N'EST PAS « mieux » : haute température = sorties moins fiables.
    "ai_temperature": "",
    # Nb de chunks que le RAG ramène (top_k) pour ancrer une génération. Réglage admin en
    # base, sûr à changer à chaud (aucun ré-index). Défaut 4. Lu via get_rag_top_k(db).
    "rag_top_k": "4",
}


def get_settings_dict(db: Session) -> dict:
    rows = db.query(Setting).all()
    result = dict(SETTING_DEFAULTS)
    for row in rows:
        result[row.key] = row.value
    return result


# Slug stable du mail de bienvenue (modele 'auto', non supprimable) dans email_templates.
WELCOME_SLUG = "welcome"


class _WelcomeFallback:
    """Repli si la ligne 'welcome' est absente (base non migree / seed manquant) :
    le mail de bienvenue part TOUJOURS, jamais de regression."""
    slug = WELCOME_SLUG
    nom = "Email de bienvenue"
    objet = SETTING_DEFAULTS["welcome_email_subject"]
    corps = SETTING_DEFAULTS["welcome_email_body"]


def record_email_envoi(db: Session, *, modele_slug: str, modele_nom: str,
                       destinataire: str, objet: str, statut: str, erreur: str | None = None):
    """Ecrit une ligne dans le journal des envois (onglet Suivi). Appele apres chaque
    envoi reel (manuel + bienvenue auto). Ne leve jamais : le suivi ne doit pas casser
    un envoi qui a reussi."""
    try:
        db.add(EmailEnvoi(
            modele_slug=modele_slug, modele_nom=modele_nom, destinataire=destinataire,
            objet=objet or "", statut=statut, erreur=erreur,
        ))
        db.commit()
    except Exception:
        db.rollback()


def get_welcome_template(db: Session):
    """Modele du mail de bienvenue, lu en base (slug 'welcome'), repli sur le
    defaut code. Source unique du contenu envoye automatiquement a l'inscription."""
    tpl = db.query(EmailTemplate).filter(EmailTemplate.slug == WELCOME_SLUG).first()
    return tpl or _WelcomeFallback()


def _slugify_email_template(nom: str) -> str:
    base = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_")
    return base or "modele"


# Liste blanche des modèles LLM texte autorisés (Phase 4.1.b). Une saisie hors de cette
# liste est REFUSÉE avant d'atteindre la base (la génération ne tombera jamais sur un
# modèle inconnu). Démarrage volontaire à une entrée — extensible : ajouter un ID Groq ici.
SUPPORTED_AI_MODELS = ["llama-3.3-70b-versatile"]


# Liste blanche des fournisseurs LLM offerts à l'admin (Phase 4.1.e). MÊME logique que
# SUPPORTED_AI_MODELS : une saisie hors liste est REFUSÉE avant la base. On n'y met QUE les
# fournisseurs réellement opérationnels (joignabilité) — aujourd'hui Groq seul. Ajouter un
# fournisseur = une ligne ici, le jour où sa clé est provisionnée (générique, aucun cas
# spécial : Anthropic/Gemini/… sont des fournisseurs comme les autres).
SUPPORTED_AI_PROVIDERS = ["groq"]


def get_ai_model(db: Session) -> str:
    """Modèle LLM texte courant, lu en base au moment de l'appel (repli sur le défaut
    code). Source unique de résolution du modèle pour tous les routers — branche sur
    l'existant (get_settings_dict). Côté backend uniquement : la valeur (chaîne) descend
    ensuite dans generate(), qui reste pur (aucune connaissance de la base)."""
    return get_settings_dict(db)["ai_model"]


def get_ai_provider(db: Session) -> str:
    """Fournisseur LLM texte courant, lu en base au moment de l'appel (repli sur le défaut
    code). Source unique de résolution du fournisseur pour tous les routers — même moule que
    get_ai_model (branche sur get_settings_dict). La valeur (chaîne) descend ensuite dans
    generate() via le paramètre `provider`, qui reste pur (aucune connaissance de la base)."""
    return get_settings_dict(db)["ai_provider"]


# Bornes de top_k (nb de chunks ramenés par le RAG). MIN 1 (au moins un extrait) ;
# MAX = garde-fou coût/pertinence.
RAG_TOP_K_MIN = 1
RAG_TOP_K_MAX = 20


def get_rag_top_k(db: Session) -> int:
    """Nombre de chunks ramenés par le RAG (top_k), lu en base au moment de l'appel (repli
    sur le défaut code). Même motif que get_max_tokens : rechargeable à chaud. Renvoie un int
    borné [MIN, MAX] ; valeur corrompue / hors bornes -> défaut."""
    raw = get_settings_dict(db)["rag_top_k"]
    try:
        v = int(raw)
    except (TypeError, ValueError):
        return int(SETTING_DEFAULTS["rag_top_k"])
    return max(RAG_TOP_K_MIN, min(RAG_TOP_K_MAX, v))


# Bornes de max_tokens (Phase 4.1.c). MIN = plancher dur : empêche une valeur si basse
# qu'elle tronquerait tout (garde-fou répondant au risque de troncature silencieuse).
# MAX = plafond INTERNE CIEL, VOLONTAIREMENT bien en-dessous du max output théorique du
# modèle — ce n'est PAS le plafond du fournisseur, c'est notre garde-fou coût/quota figé.
MAX_TOKENS_MIN = 256
MAX_TOKENS_MAX = 8000


def get_max_tokens(db: Session, outil: str) -> int:
    """max_tokens courant pour un outil, lu en base au moment de l'appel (HYBRIDE :
    surcharge `max_tokens_<outil>` si présente, sinon défaut global `max_tokens_default`,
    sinon défaut code). Même motif que get_ai_model : lecture par requête -> rechargeable
    à chaud. Renvoie un int (Setting.value est une chaîne)."""
    s = get_settings_dict(db)
    raw = s.get(f"max_tokens_{outil}", s["max_tokens_default"])
    try:
        return int(raw)
    except (TypeError, ValueError):
        return int(s["max_tokens_default"])


# Bornes de température (Phase 4.1.d). Plage standard des API compatibles OpenAI/Groq.
# Rappel : « le mieux » N'EST PAS « le plus haut » — haute température = sorties moins fiables
# (hallucinations, format cassé). Pour du pédagogique, le bon réglage est bas à modéré.
TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 2.0


def get_temperature(db: Session):
    """Température courante (GLOBALE), lue en base au moment de l'appel (rechargeable à chaud,
    même motif que get_max_tokens). Renvoie un float dans [MIN, MAX], ou None si non réglée ->
    generate() n'envoie alors RIEN et le fournisseur applique son défaut (comportement
    historique = zéro régression). Valeur corrompue / hors bornes -> None (jamais d'exception).
    L'optimiseur n'utilise PAS ce réglage (température 0 figée en dur pour un JSON déterministe)."""
    raw = get_settings_dict(db).get("ai_temperature", "")
    if raw is None or str(raw).strip() == "":
        return None
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    return v if TEMPERATURE_MIN <= v <= TEMPERATURE_MAX else None


def get_prompt(db: Session, key: str) -> str:
    """Prompt courant d'un outil : surcharge base `prompt_<key>` si présente et non vide,
    sinon défaut code (llm_prompts.PROMPTS). Lu par requête -> rechargeable à chaud. Le contenu
    en base est validé À L'ÉCRITURE (repères obligatoires présents + .format() sans casse),
    donc sûr ici."""
    base = get_settings_dict(db).get(f"prompt_{key}", "")
    if base and base.strip():
        return base
    return PROMPTS[key]["default"]


def valider_prompt(key: str, template: str) -> str | None:
    """Garde-fou d'écriture d'un prompt. Renvoie un message d'erreur (langage humain) si le
    prompt est invalide, sinon None. (1) chaque repère obligatoire `{x}` doit rester présent ;
    (2) le texte doit `.format()` sans lever (repère inconnu / accolades mal équilibrées)."""
    meta = PROMPTS.get(key)
    if meta is None:
        return "Prompt inconnu."
    required = meta["placeholders"]
    for ph in required:
        if "{" + ph + "}" not in template:
            return (f"Le repère {{{ph}}} est obligatoire dans ce prompt et a disparu. "
                    f"Remettez-le tel quel avant d'enregistrer.")
    try:
        template.format(**{ph: "x" for ph in required})
    except (KeyError, IndexError, ValueError):
        return ("Le prompt contient un repère inconnu ou des accolades mal équilibrées. "
                "N'utilisez que les repères indiqués ; dans un exemple JSON, doublez les accolades : {{ }}.")
    return None


class AdminLoginBody(BaseModel):
    username: str
    password: str


def _get_admin_email(request: Request) -> str:
    token = request.cookies.get(_COOKIE)
    if not token:
        return "admin"
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET", ""), algorithms=[_ALGO])
        return payload.get("sub", "admin")
    except JWTError:
        return "admin"


@router.post("/admin/login")
@limiter.limit("10/hour")
def admin_login(request: Request, body: AdminLoginBody, response: Response, db: Session = Depends(get_db)):
    import bcrypt as _bcrypt
    expected_user = os.getenv("ADMIN_USERNAME", "")
    expected_pass = os.getenv("ADMIN_PASSWORD", "")
    ip = request.client.host if request.client else None
    pwd_setting = db.query(Setting).filter(Setting.key == "admin_password_hash").first()
    username_ok = bool(expected_user) and secrets.compare_digest(body.username, expected_user)
    env_ok = bool(expected_pass) and secrets.compare_digest(body.password, expected_pass)
    db_ok = False
    if pwd_setting:
        try:
            db_ok = _bcrypt.checkpw(body.password.encode("utf-8"), pwd_setting.value.encode("utf-8"))
        except Exception:
            pass
    password_ok = env_ok or db_ok
    ok = username_ok and password_ok
    if not ok:
        attempt = FailedLoginAttempt(
            ip_address=ip,
            username=body.username,
            user_agent=request.headers.get("user-agent", ""),
        )
        db.add(attempt)
        db.commit()
        since = datetime.utcnow() - timedelta(hours=1)
        count = db.query(FailedLoginAttempt).filter(
            FailedLoginAttempt.ip_address == ip,
            FailedLoginAttempt.attempt_at >= since,
        ).count()
        if count >= 10:
            db.query(FailedLoginAttempt).filter(
                FailedLoginAttempt.ip_address == ip,
                FailedLoginAttempt.attempt_at >= since,
            ).update({"blocked": True})
            db.commit()
        raise HTTPException(401, "Identifiants incorrects.")
    response.set_cookie(_COOKIE, _make_admin_token(), max_age=_MAX_AGE, httponly=True, samesite="lax")
    admin_email = os.getenv("ADMIN_EMAIL", expected_user)
    db.add(ConnexionLog(email=admin_email, action="admin_login", ip=ip))
    db.commit()
    return {"status": "ok"}


@router.post("/admin/logout")
def admin_logout(response: Response):
    response.delete_cookie(_COOKIE)
    return {"status": "ok"}


@router.get("/admin/check")
def admin_check(_: None = Depends(_require_admin)):
    return {"status": "ok"}


@router.get("/admin/base")
def admin_base(_: None = Depends(_require_admin)):
    """Sur quelle base l'app est-elle RÉELLEMENT connectée ? Vérité terrain via
    current_database() (la connexion vivante, pas l'.env). Host/port depuis le moteur.
    Le `type` (réelle / miroir / test) est dérivé du nom — garde-fou « miroir vs réelle »."""
    with engine.connect() as conn:
        nom = conn.execute(text("SELECT current_database()")).scalar()
    n = (nom or "").lower()
    if n == "aschool":
        type_ = "reelle"
    elif "miroir" in n:
        type_ = "miroir"
    elif "test" in n:
        type_ = "test"
    else:
        type_ = "autre"
    return {"base": nom, "host": engine.url.host, "port": engine.url.port, "type": type_}


@router.get("/admin/feedbacks")
def get_feedbacks(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(Feedback, User.email)
        .outerjoin(User, User.id == Feedback.user_id)
        .order_by(Feedback.created_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id":       f.id,
            "email":    email,
            "type":     f.type,
            "message":  f.message,
            "rating":   f.rating,
            "category": f.category,
            "statut":   f.statut,
            "date":     f.created_at.strftime("%d/%m/%Y %H:%M"),
        }
        for f, email in rows
    ]


class StatutBody(BaseModel):
    statut: str

_STATUTS_VALIDES = {"nouveau", "en_cours", "traite", "archive"}

@router.patch("/admin/feedbacks/{feedback_id}/statut")
def update_feedback_statut(
    feedback_id: int,
    body: StatutBody,
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    if body.statut not in _STATUTS_VALIDES:
        raise HTTPException(400, "Statut invalide.")
    fb = db.get(Feedback, feedback_id)
    if not fb:
        raise HTTPException(404, "Feedback introuvable.")
    fb.statut = body.statut
    db.commit()
    return {"status": "ok"}


@router.delete("/admin/feedbacks/{feedback_id}")
def delete_feedback(
    feedback_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    fb = db.get(Feedback, feedback_id)
    if not fb:
        raise HTTPException(404, "Feedback introuvable.")
    target_email = db.query(User.email).filter(User.id == fb.user_id).scalar()
    db.delete(fb)
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="DELETE_FEEDBACK",
        target_email=target_email,
        ip=request.client.host if request.client else None,
        details=f"Feedback #{feedback_id} supprimé ({fb.type} / {fb.category or '—'})",
    )
    return {"status": "ok"}


@router.get("/admin/activites")
def get_activites_admin(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    from src.activities import ACTIVITES_PAR_MATIERE, ACTIVITES_PAR_ACTIVITE

    matieres = list(ACTIVITES_PAR_MATIERE.keys())
    total_entrees = sum(len(a) for a in ACTIVITES_PAR_MATIERE.values())

    par_matiere = {
        matiere: [
            {
                "nom": nom,
                "key": data["key"],
                "sous_types": data["sous_types"],
                "nb_sous_types": len(data["sous_types"]),
            }
            for nom, data in activites.items()
        ]
        for matiere, activites in ACTIVITES_PAR_MATIERE.items()
    }

    matrice = [
        {
            "activite": activite,
            "matieres": list(matieres_data.keys()),
        }
        for activite, matieres_data in ACTIVITES_PAR_ACTIVITE.items()
    ]

    total_generees = db.query(func.count(ActiviteSauvegardee.id)).scalar() or 0
    generees_par_matiere = dict(
        db.query(User.subject, func.count(ActiviteSauvegardee.id))
        .join(ActiviteSauvegardee, User.id == ActiviteSauvegardee.user_id)
        .filter(User.subject.isnot(None))
        .group_by(User.subject)
        .all()
    )

    return {
        "stats": {
            "nb_matieres": len(matieres),
            "nb_activites_uniques": len(ACTIVITES_PAR_ACTIVITE),
            "nb_entrees": total_entrees,
            "total_generees": total_generees,
        },
        "matieres": matieres,
        "par_matiere": par_matiere,
        "matrice": matrice,
        "generees_par_matiere": generees_par_matiere,
    }


class UpdateUserBody(BaseModel):
    prenom: str = ""
    nom: str = ""
    subject: str = ""
    niveau: str = ""


@router.get("/admin/users")
def get_users(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    counts = dict(
        db.query(ActiviteSauvegardee.user_id, func.count(ActiviteSauvegardee.id))
        .group_by(ActiviteSauvegardee.user_id)
        .all()
    )
    return [
        {
            "email":        u.email,
            "prenom":       u.prenom or "",
            "nom":          u.nom or "",
            "subject":      u.subject or "",
            "niveau":       u.niveau or "",
            "created_at":   u.created_at.strftime("%d/%m/%Y"),
            "last_login":   u.last_login.strftime("%d/%m/%Y %H:%M") if u.last_login else "—",
            "is_active":    u.is_active,
            "is_verified":  u.is_verified,
            "nb_activites": counts.get(u.id, 0),
        }
        for u in users
    ]


@router.patch("/admin/user/{email}")
def update_user_profile(email: str, body: UpdateUserBody, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    user.prenom  = body.prenom or None
    user.nom     = body.nom or None
    user.subject = body.subject or None
    user.niveau  = body.niveau or None
    db.commit()
    return {"status": "ok"}


@router.delete("/admin/user/{email}")
def delete_user(email: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    db.query(EmailToken).filter(EmailToken.email == email).delete()
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete()
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    db.query(ActiviteSauvegardee).filter(ActiviteSauvegardee.user_id == user.id).delete()
    db.query(ConnexionLog).filter(ConnexionLog.user_id == user.id).delete()
    db.query(Feedback).filter(Feedback.user_id == user.id).delete()
    db.delete(user)
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="DELETE_USER",
        target_email=email,
        ip=request.client.host if request.client else None,
        details="Compte supprimé avec toutes ses données",
    )
    return {"status": "ok"}


@router.post("/admin/user/{email}/verify")
def verify_user(email: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    if user.is_verified:
        raise HTTPException(400, "Ce compte est déjà vérifié.")
    user.is_verified = True
    user.is_active = True
    db.query(EmailToken).filter(EmailToken.email == email, EmailToken.purpose == "verify_email").delete()
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="VERIFY_USER",
        target_email=email,
        ip=request.client.host if request.client else None,
        details="Compte validé manuellement par l'admin",
    )
    return {"status": "ok"}


class ChangePasswordBody(BaseModel):
    old_password: str
    new_password: str
    new_password_confirm: str


@router.post("/admin/change-password")
def change_admin_password(body: ChangePasswordBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    import bcrypt as _bcrypt
    if body.new_password != body.new_password_confirm:
        raise HTTPException(400, "Les mots de passe ne correspondent pas.")
    if len(body.new_password) < 8:
        raise HTTPException(400, "Minimum 8 caractères.")
    expected_pass = os.getenv("ADMIN_PASSWORD", "")
    pwd_setting = db.query(Setting).filter(Setting.key == "admin_password_hash").first()
    if pwd_setting:
        try:
            old_ok = _bcrypt.checkpw(body.old_password.encode("utf-8"), pwd_setting.value.encode("utf-8"))
        except Exception:
            old_ok = False
    else:
        old_ok = bool(expected_pass) and secrets.compare_digest(body.old_password, expected_pass)
    if not old_ok:
        raise HTTPException(400, "Mot de passe actuel incorrect.")
    new_hash = _bcrypt.hashpw(body.new_password.encode("utf-8"), _bcrypt.gensalt(12)).decode("utf-8")
    if pwd_setting:
        pwd_setting.value = new_hash
    else:
        db.add(Setting(key="admin_password_hash", value=new_hash))
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="CHANGE_PASSWORD",
        target_email=None,
        ip=request.client.host if request.client else None,
        details="Mot de passe admin modifié via l'interface",
    )
    return {"status": "ok"}


class SettingsBody(BaseModel):
    welcome_email_subject: str = ""
    welcome_email_body: str = ""


@router.get("/admin/settings")
def get_settings(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    return get_settings_dict(db)


@router.put("/admin/settings")
def save_settings(body: SettingsBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    for key, value in body.dict().items():
        row = db.query(Setting).filter(Setting.key == key).first()
        if row:
            row.value = value
        else:
            db.add(Setting(key=key, value=value))
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="UPDATE_SETTINGS",
        target_email=None,
        ip=request.client.host if request.client else None,
        details="Paramètres email mis à jour",
    )
    return {"status": "ok"}


class AiModelBody(BaseModel):
    model_config = {"protected_namespaces": ()}  # autorise un champ nommé `model` (pydantic v2)
    model: str


@router.get("/admin/ai-models")
def get_ai_models(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Modèles LLM texte pris en charge + modèle courant — alimente la validation
    et le hint du formulaire admin."""
    return {"supported": SUPPORTED_AI_MODELS, "current": get_ai_model(db)}


@router.put("/admin/ai-model")
def save_ai_model(body: AiModelBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Écrit le modèle LLM texte. Endpoint DÉDIÉ (le PUT /admin/settings email reste
    intact). Validation stricte : vide ou hors liste blanche → 400 (message humain pour
    la modale admin), rien n'est écrit. Sinon upsert de la clé `ai_model` + audit."""
    valeur = (body.model or "").strip()
    if valeur not in SUPPORTED_AI_MODELS:
        raise HTTPException(
            400,
            f"Modèle inconnu ou vide. Saisissez un modèle pris en charge : "
            f"{', '.join(SUPPORTED_AI_MODELS)}.",
        )
    row = db.query(Setting).filter(Setting.key == "ai_model").first()
    if row:
        row.value = valeur
    else:
        db.add(Setting(key="ai_model", value=valeur))
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="UPDATE_AI_MODEL",
        target_email=None,
        ip=request.client.host if request.client else None,
        details=f"Modèle LLM mis à jour : {valeur}",
    )
    return {"status": "ok"}


class AiProviderBody(BaseModel):
    provider: str


@router.get("/admin/ai-providers")
def get_ai_providers(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Fournisseurs LLM offerts (liste blanche) + fournisseur courant — alimente la combo
    admin et sa validation. Miroir de GET /admin/ai-models. On n'expose QUE les fournisseurs
    opérationnels (joignabilité) ; les autres apparaîtront ici une fois leur clé configurée."""
    return {"supported": SUPPORTED_AI_PROVIDERS, "current": get_ai_provider(db)}


@router.put("/admin/ai-provider")
def save_ai_provider(body: AiProviderBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Écrit le fournisseur LLM texte. Endpoint DÉDIÉ (PUT email + PUT ai-model + PUT max-tokens
    restent intacts). Validation stricte : vide ou hors liste blanche → 400 (message humain pour
    la modale admin), rien n'est écrit. Sinon upsert de la clé `ai_provider` + audit."""
    valeur = (body.provider or "").strip()
    if valeur not in SUPPORTED_AI_PROVIDERS:
        raise HTTPException(
            400,
            f"Fournisseur inconnu ou vide. Choisissez un fournisseur pris en charge : "
            f"{', '.join(SUPPORTED_AI_PROVIDERS)}.",
        )
    row = db.query(Setting).filter(Setting.key == "ai_provider").first()
    if row:
        row.value = valeur
    else:
        db.add(Setting(key="ai_provider", value=valeur))
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="UPDATE_AI_PROVIDER",
        target_email=None,
        ip=request.client.host if request.client else None,
        details=f"Fournisseur LLM mis à jour : {valeur}",
    )
    return {"status": "ok"}


class MaxTokensBody(BaseModel):
    default: int
    ambiguites: int
    sequence: int
    optimiseur: int


@router.get("/admin/max-tokens")
def get_max_tokens_settings(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Valeurs max_tokens courantes (défaut global + 3 surcharges) + bornes — alimente
    le formulaire admin et sa validation. Miroir de GET /admin/ai-models."""
    s = get_settings_dict(db)
    return {
        "default": int(s["max_tokens_default"]),
        "overrides": {
            "ambiguites": int(s["max_tokens_ambiguites"]),
            "sequence": int(s["max_tokens_sequence"]),
            "optimiseur": int(s["max_tokens_optimiseur"]),
        },
        "bounds": {"min": MAX_TOKENS_MIN, "max": MAX_TOKENS_MAX},
    }


@router.put("/admin/max-tokens")
def save_max_tokens(body: MaxTokensBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Écrit le défaut global + les 3 surcharges. Endpoint DÉDIÉ (PUT /admin/settings email
    et PUT /admin/ai-model restent intacts). Validation stricte : chaque valeur doit être un
    entier dans [MIN, MAX], sinon 400 + message humain pour la modale admin, rien n'est écrit."""
    valeurs = {
        "max_tokens_default": body.default,
        "max_tokens_ambiguites": body.ambiguites,
        "max_tokens_sequence": body.sequence,
        "max_tokens_optimiseur": body.optimiseur,
    }
    for cle, v in valeurs.items():
        if not (MAX_TOKENS_MIN <= v <= MAX_TOKENS_MAX):
            raise HTTPException(
                400,
                f"Valeur hors limites : {v}. Chaque max_tokens doit être un nombre entier "
                f"entre {MAX_TOKENS_MIN} et {MAX_TOKENS_MAX}.",
            )
    for cle, v in valeurs.items():
        row = db.query(Setting).filter(Setting.key == cle).first()
        if row:
            row.value = str(v)
        else:
            db.add(Setting(key=cle, value=str(v)))
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="UPDATE_MAX_TOKENS",
        target_email=None,
        ip=request.client.host if request.client else None,
        details=(
            f"max_tokens mis à jour — défaut {body.default}, ambiguïtés {body.ambiguites}, "
            f"séquence {body.sequence}, optimiseur {body.optimiseur}"
        ),
    )
    return {"status": "ok"}


class TemperatureBody(BaseModel):
    temperature: float | None = None  # None / absente = défaut du fournisseur (non réglée)


@router.get("/admin/temperature")
def get_temperature_settings(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Température courante (float, ou None = défaut fournisseur) + bornes — alimente le
    formulaire admin et sa validation. Miroir de GET /admin/max-tokens."""
    raw = get_settings_dict(db).get("ai_temperature", "")
    val = None
    if raw not in (None, ""):
        try:
            val = float(raw)
        except (TypeError, ValueError):
            val = None
    return {"temperature": val, "bounds": {"min": TEMPERATURE_MIN, "max": TEMPERATURE_MAX}}


@router.put("/admin/temperature")
def save_temperature(body: TemperatureBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Écrit la température globale. Endpoint DÉDIÉ (les autres PUT restent intacts).
    `temperature` absente/None -> on revient au défaut du fournisseur (clé vidée). Sinon
    validation stricte dans [MIN, MAX], sinon 400 + message humain pour la modale admin, rien
    écrit. L'optimiseur n'est pas concerné (température 0 figée en dur)."""
    if body.temperature is None:
        valeur = ""
    else:
        if not (TEMPERATURE_MIN <= body.temperature <= TEMPERATURE_MAX):
            raise HTTPException(
                400,
                f"Température hors limites : {body.temperature}. Elle doit être un nombre entre "
                f"{TEMPERATURE_MIN} et {TEMPERATURE_MAX} (laisser vide = défaut du fournisseur).",
            )
        valeur = str(body.temperature)
    row = db.query(Setting).filter(Setting.key == "ai_temperature").first()
    if row:
        row.value = valeur
    else:
        db.add(Setting(key="ai_temperature", value=valeur))
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="UPDATE_TEMPERATURE",
        target_email=None,
        ip=request.client.host if request.client else None,
        details=f"Température mise à jour : {valeur or 'défaut fournisseur'}",
    )
    return {"status": "ok"}


class PromptBody(BaseModel):
    key: str
    text: str


@router.get("/admin/prompts")
def get_prompts_settings(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Liste des prompts d'outils administrables : libellé, repères obligatoires, texte courant
    (surcharge base ou défaut), et drapeau is_default + texte par défaut (pour « revenir au
    défaut »). Les activités (catalogue) ne sont PAS ici."""
    s = get_settings_dict(db)
    out = []
    for key, meta in PROMPTS.items():
        override = s.get(f"prompt_{key}", "")
        actif = override if (override and override.strip()) else meta["default"]
        out.append({
            "key": key,
            "label": meta["label"],
            "placeholders": meta["placeholders"],
            "current": actif,
            "default": meta["default"],
            "is_default": not (override and override.strip()),
        })
    return {"prompts": out}


@router.put("/admin/prompts")
def save_prompt(body: PromptBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Écrit un prompt d'outil. Endpoint DÉDIÉ. Garde-fou : un repère obligatoire manquant ou
    des accolades cassées -> 400 + message humain pour la modale, RIEN écrit (plantage rendu
    impossible). Texte identique au défaut accepté tel quel (override volontaire)."""
    if body.key not in PROMPTS:
        raise HTTPException(400, "Prompt inconnu.")
    err = valider_prompt(body.key, body.text)
    if err:
        raise HTTPException(400, err)
    cle = f"prompt_{body.key}"
    row = db.query(Setting).filter(Setting.key == cle).first()
    if row:
        row.value = body.text
    else:
        db.add(Setting(key=cle, value=body.text))
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="UPDATE_PROMPT",
        target_email=None,
        ip=request.client.host if request.client else None,
        details=f"Prompt '{body.key}' mis à jour",
    )
    return {"status": "ok"}


@router.delete("/admin/prompts/{key}")
def reset_prompt(key: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Vrai retour au défaut d'un outil : SUPPRIME la surcharge en base (ligne `prompt_<key>`).
    `get_prompt` retombe alors sur le défaut code — qui pourra évoluer librement. Idempotent :
    rien en base -> déjà au défaut, on renvoie ok sans erreur."""
    if key not in PROMPTS:
        raise HTTPException(400, "Prompt inconnu.")
    row = db.query(Setting).filter(Setting.key == f"prompt_{key}").first()
    if row:
        db.delete(row)
        db.commit()
        log_admin_action(
            db=db,
            admin_email=_get_admin_email(request),
            action="RESET_PROMPT",
            target_email=None,
            ip=request.client.host if request.client else None,
            details=f"Prompt '{key}' remis au défaut",
        )
    return {"status": "ok"}


class SendEmailBody(BaseModel):
    subject: str
    body: str


@router.post("/admin/user/{email}/reset-password")
def admin_reset_password(email: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    from backend import auth as auth_lib
    token = auth_lib.generate_email_token(db, email, "reset_password")
    try:
        auth_lib.send_reset_email(email, token)
    except Exception as e:
        raise HTTPException(500, f"Erreur envoi email : {e}")
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="RESET_PASSWORD",
        target_email=email,
        ip=request.client.host if request.client else None,
        details="Lien de réinitialisation envoyé par l'admin",
    )
    return {"status": "ok"}


@router.patch("/admin/user/{email}/toggle-active")
def toggle_user_active(email: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    user.is_active = not user.is_active
    if not user.is_active:
        db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True,
        ).update({"is_active": False})
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="ACTIVATE_USER" if user.is_active else "DEACTIVATE_USER",
        target_email=email,
        ip=request.client.host if request.client else None,
        details=f"Compte {'activé' if user.is_active else 'désactivé'}",
    )
    return {"status": "ok", "is_active": user.is_active}


class MailGroupeBody(BaseModel):
    emails: list[str]
    subject: str
    body: str


@router.post("/admin/mail-groupe")
def mail_groupe(body: MailGroupeBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    from backend import auth as auth_lib
    if not body.emails:
        raise HTTPException(400, "Aucun destinataire.")
    if not body.subject.strip():
        raise HTTPException(400, "Objet requis.")
    if not body.body.strip():
        raise HTTPException(400, "Message requis.")
    sent = 0
    errors = []
    for email in body.emails:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            errors.append(email)
            continue
        try:
            auth_lib.send_custom_email(email, user.prenom, body.subject, body.body)
            sent += 1
        except Exception:
            errors.append(email)
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="MAIL_GROUPE",
        target_email=None,
        ip=request.client.host if request.client else None,
        details=f"{sent} email(s) envoyé(s) sur {len(body.emails)} — {len(errors)} erreur(s)",
    )
    return {"sent": sent, "errors": errors, "total": len(body.emails)}


@router.post("/admin/user/{email}/send-email")
def send_email_to_user(email: str, body: SendEmailBody, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    from backend import auth as auth_lib
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    try:
        auth_lib.send_custom_email(email, user.prenom, body.subject, body.body)
    except Exception as e:
        raise HTTPException(500, f"Erreur envoi email : {e}")
    return {"status": "ok"}


@router.post("/admin/settings/test-email")
def test_welcome_email(body: SettingsBody, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    from backend import auth as auth_lib
    admin_email = os.getenv("SMTP_USERNAME", "")
    if not admin_email:
        raise HTTPException(500, "SMTP_USERNAME non configuré.")
    settings = get_settings_dict(db)
    subject = body.welcome_email_subject or settings["welcome_email_subject"]
    content = body.welcome_email_body    or settings["welcome_email_body"]
    try:
        auth_lib.send_custom_email(admin_email, "Admin", subject, content)
    except Exception as e:
        raise HTTPException(500, f"Erreur envoi email : {e}")
    return {"status": "ok"}


# ── Modeles d'email (collection maitre-detail) ─────────────────────────────
# Remplace la config plate du seul mail de bienvenue par une liste de modeles.
# 'auto'   = parti tout seul sur un evenement (bienvenue). Non supprimable.
# 'manuel' = envoye a la demande vers une adresse saisie (ex. UNICEF).

def _serialize_email_template(t: EmailTemplate) -> dict:
    return {
        "id": t.id, "slug": t.slug, "nom": t.nom,
        "description": t.description,
        "objet": t.objet, "corps": t.corps,
        "mode_envoi": t.mode_envoi, "supprimable": t.supprimable,
    }


class EmailTemplateCreate(BaseModel):
    nom: str


class EmailTemplateUpdate(BaseModel):
    nom: str | None = None
    description: str = ""
    objet: str = ""
    corps: str = ""


class EmailTemplateSend(BaseModel):
    to: str


@router.get("/admin/email-templates")
def list_email_templates(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(EmailTemplate)
        .order_by(EmailTemplate.supprimable.asc(), EmailTemplate.created_at.asc())
        .all()
    )
    return [_serialize_email_template(t) for t in rows]


@router.post("/admin/email-templates")
def create_email_template(body: EmailTemplateCreate, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    nom = body.nom.strip()
    if not nom:
        raise HTTPException(400, "Nom requis.")
    slug = _slugify_email_template(nom)
    existing = {s for (s,) in db.query(EmailTemplate.slug).all()}
    candidate, i = slug, 2
    while candidate in existing:
        candidate, i = f"{slug}_{i}", i + 1
    t = EmailTemplate(slug=candidate, nom=nom, description="", objet="", corps="", mode_envoi="manuel", supprimable=True)
    db.add(t)
    db.commit()
    db.refresh(t)
    log_admin_action(
        db=db, admin_email=_get_admin_email(request), action="CREATE_EMAIL_TEMPLATE",
        target_email=None, ip=request.client.host if request.client else None,
        details=f"Modele email cree : '{t.nom}' ({t.slug})",
    )
    return _serialize_email_template(t)


@router.put("/admin/email-templates/{template_id}")
def update_email_template(template_id: int, body: EmailTemplateUpdate, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(404, "Modele introuvable.")
    # mode_envoi / slug / supprimable NON editables : protege la semantique du modele
    # 'welcome' (reste 'auto' et non supprimable).
    t.description = body.description
    t.objet = body.objet
    t.corps = body.corps
    if body.nom is not None and body.nom.strip():
        t.nom = body.nom.strip()
    db.commit()
    log_admin_action(
        db=db, admin_email=_get_admin_email(request), action="UPDATE_EMAIL_TEMPLATE",
        target_email=None, ip=request.client.host if request.client else None,
        details=f"Modele email mis a jour : '{t.nom}' ({t.slug})",
    )
    return _serialize_email_template(t)


@router.delete("/admin/email-templates/{template_id}")
def delete_email_template(template_id: int, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(404, "Modele introuvable.")
    if not t.supprimable:
        raise HTTPException(400, "Ce modele ne peut pas etre supprime.")
    nom, slug = t.nom, t.slug
    db.delete(t)
    db.commit()
    log_admin_action(
        db=db, admin_email=_get_admin_email(request), action="DELETE_EMAIL_TEMPLATE",
        target_email=None, ip=request.client.host if request.client else None,
        details=f"Modele email supprime : '{nom}' ({slug})",
    )
    return {"status": "ok"}


@router.post("/admin/email-templates/{template_id}/send")
def send_email_template(template_id: int, body: EmailTemplateSend, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Envoi MANUEL du modele vers une adresse saisie (ex. UNICEF). Passe par la
    porte SMTP unique via send_custom_email()."""
    from backend import auth as auth_lib
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(404, "Modele introuvable.")
    to = body.to.strip()
    if not to or "@" not in to:
        raise HTTPException(400, "Adresse destinataire invalide.")
    if not t.objet.strip() or not t.corps.strip():
        raise HTTPException(400, "Objet et corps requis avant l'envoi.")
    statut, err = "envoye", None
    try:
        auth_lib.send_custom_email(to, None, t.objet, t.corps)
    except Exception as e:
        statut, err = "echec", str(e)
    # Suivi : on trace l'envoi (reussi OU echoue) avant de repondre.
    record_email_envoi(db, modele_slug=t.slug, modele_nom=t.nom, destinataire=to,
                       objet=t.objet, statut=statut, erreur=err)
    log_admin_action(
        db=db, admin_email=_get_admin_email(request), action="SEND_EMAIL_TEMPLATE",
        target_email=None, ip=request.client.host if request.client else None,
        details=f"Modele '{t.slug}' envoye a {to} ({statut})",
    )
    if statut == "echec":
        raise HTTPException(500, f"Erreur envoi email : {err}")
    return {"status": "ok"}


@router.get("/admin/email-envois")
def list_email_envois(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Journal des envois (onglet Suivi), du plus recent au plus ancien."""
    rows = (
        db.query(EmailEnvoi)
        .order_by(EmailEnvoi.envoye_le.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": r.id, "modele_slug": r.modele_slug, "modele_nom": r.modele_nom,
            "destinataire": r.destinataire, "objet": r.objet,
            "statut": r.statut, "erreur": r.erreur,
            "envoye_le": r.envoye_le.strftime("%d/%m/%Y %H:%M"),
        }
        for r in rows
    ]


@router.post("/admin/email-templates/{template_id}/test")
def test_email_template(template_id: int, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Envoi de TEST du modele vers l'adresse SMTP de l'admin (verifie la config)."""
    from backend import auth as auth_lib
    admin_email = os.getenv("SMTP_USERNAME", "")
    if not admin_email:
        raise HTTPException(500, "SMTP_USERNAME non configure.")
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(404, "Modele introuvable.")
    try:
        auth_lib.send_custom_email(admin_email, "Admin", t.objet, t.corps)
    except Exception as e:
        raise HTTPException(500, f"Erreur envoi email : {e}")
    return {"status": "ok"}


@router.get("/admin/sessions")
def get_sessions(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    sessions = (
        db.query(UserSession)
        .filter(UserSession.is_active == True)
        .order_by(UserSession.last_seen.desc())
        .limit(100)
        .all()
    )
    now = datetime.utcnow()
    user_ids = {s.user_id for s in sessions if s.user_id is not None}
    email_par_id = dict(
        db.query(User.id, User.email).filter(User.id.in_(user_ids)).all()
    ) if user_ids else {}

    def _fmt_duration(s):
        delta = now - s.login_at
        total_min = max(0, int(delta.total_seconds() // 60))
        h, m = divmod(total_min, 60)
        if h > 0:
            return f"{h}h {m:02d}min" if m else f"{h}h"
        return f"{m}min" if m else "< 1min"

    return [
        {
            "id":        s.id,
            "email":     email_par_id.get(s.user_id, "—"),
            "browser":   s.browser or "—",
            "os":        s.os or "—",
            "device":    s.device_type or "—",
            "ip":        s.ip_address or "—",
            "login_at":  s.login_at.strftime("%d/%m/%Y %H:%M"),
            "last_seen": s.last_seen.strftime("%d/%m/%Y %H:%M"),
            "is_online": s.is_online,
            "duree":     _fmt_duration(s),
        }
        for s in sessions
    ]


class ForceLogoutBody(BaseModel):
    raison: str = ""


@router.post("/admin/force-logout/{session_id}")
def force_logout(
    session_id: int,
    body: ForceLogoutBody,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    from backend.auth import send_custom_email
    session_obj = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session_obj:
        raise HTTPException(404, "Session introuvable.")
    target_email = db.query(User.email).filter(User.id == session_obj.user_id).scalar()
    admin_email = os.getenv("ADMIN_EMAIL", "")
    if admin_email and target_email == admin_email:
        raise HTTPException(403, "Impossible de déconnecter la session administrateur.")
    session_obj.is_active = False
    db.commit()
    raison = body.raison.strip()
    details = f"Session {session_obj.session_key[:8]}... déconnectée"
    if raison:
        details += f" — Raison : {raison}"
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="FORCE_LOGOUT",
        target_email=target_email,
        ip=request.client.host if request.client else None,
        details=details,
    )
    try:
        raison_txt = f"\n\nRaison indiquée : {raison}" if raison else ""
        send_custom_email(
            email=target_email,
            prenom=None,
            subject="Votre session aSchool a été fermée",
            body=(
                f"Bonjour {{prenom}},\n\n"
                f"Votre session aSchool a été fermée par l'administrateur.{raison_txt}\n\n"
                f"Si vous pensez qu'il s'agit d'une erreur, contactez l'administrateur.\n\n"
                f"L'équipe aSchool"
            ),
        )
    except Exception:
        pass
    return {"status": "ok"}


@router.get("/admin/stats/overview")
def stats_overview(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    today = datetime.utcnow().date()
    threshold_online = datetime.utcnow() - timedelta(seconds=90)
    return {
        "total_profs":        db.query(User).filter(User.is_verified == True).count(),
        "connexions_today":   db.query(ConnexionLog).filter(
                                  ConnexionLog.action == "login",
                                  func.date(ConnexionLog.created_at) == today
                              ).count(),
        "feedbacks_nouveaux": db.query(Feedback).filter(Feedback.statut == "nouveau").count(),
        "alertes_nonlues":    db.query(AdminAlert).filter(AdminAlert.is_read == False).count(),
        "sessions_online":    db.query(UserSession).filter(
                                  UserSession.is_active == True,
                                  UserSession.last_seen >= threshold_online
                              ).count(),
    }


@router.get("/admin/stats/logins")
def stats_logins(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    since = datetime.utcnow() - timedelta(days=30)
    rows = (
        db.query(
            func.date(ConnexionLog.created_at).label("day"),
            func.count(ConnexionLog.id).label("count"),
        )
        .filter(ConnexionLog.action == "login", ConnexionLog.created_at >= since)
        .group_by(func.date(ConnexionLog.created_at))
        .order_by(func.date(ConnexionLog.created_at))
        .all()
    )
    return [{"day": str(r.day), "count": r.count} for r in rows]


@router.get("/admin/server-metrics")
def server_metrics(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    import psutil
    cpu   = psutil.cpu_percent(interval=1)
    ram   = psutil.virtual_memory()
    disk  = psutil.disk_usage('/')
    up_h  = round((datetime.now(timezone.utc).timestamp() - psutil.boot_time()) / 3600, 1)
    return {
        "cpu_percent":  cpu,
        "ram_used_gb":  round(ram.used / 1024**3, 1),
        "ram_total_gb": round(ram.total / 1024**3, 1),
        "ram_percent":  ram.percent,
        "disk_used_gb": round(disk.used / 1024**3, 1),
        "disk_total_gb":round(disk.total / 1024**3, 1),
        "disk_percent": disk.percent,
        "uptime_hours": up_h,
    }


@router.get("/admin/db-size")
def db_size(_: None = Depends(_require_admin)):
    return {"size_mb": get_db_size_mb()}


@router.get("/admin/alerts")
def get_alerts(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(AdminAlert)
        .order_by(AdminAlert.is_read.asc(), AdminAlert.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id":         r.id,
            "level":      r.level,
            "title":      r.title,
            "message":    r.message,
            "is_read":    r.is_read,
            "read_by":    r.read_by or "",
            "date":       r.created_at.strftime("%d/%m/%Y %H:%M"),
        }
        for r in rows
    ]


@router.post("/admin/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    alert = db.query(AdminAlert).filter(AdminAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alerte introuvable.")
    alert.is_read  = True
    alert.read_by  = _get_admin_email(request)
    alert.read_at  = datetime.utcnow()
    db.commit()
    return {"status": "ok"}


@router.get("/admin/audit-log")
def get_audit_log(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(AdminAuditLog)
        .order_by(AdminAuditLog.timestamp.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id":           r.id,
            "admin_email":  r.admin_email or "admin",
            "action":       r.action,
            "target_email": r.target_email or "—",
            "ip":           r.ip_address or "—",
            "details":      r.details or "",
            "date":         r.timestamp.strftime("%d/%m/%Y %H:%M"),
        }
        for r in rows
    ]


@router.get("/admin/stats/hours")
def stats_hours(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(
            func.strftime('%H', ConnexionLog.created_at).label("hour"),
            func.count(ConnexionLog.id).label("count"),
        )
        .filter(ConnexionLog.action == "login")
        .group_by(func.strftime('%H', ConnexionLog.created_at))
        .order_by(func.strftime('%H', ConnexionLog.created_at))
        .all()
    )
    hours_map = {r.hour: r.count for r in rows}
    return [{"hour": f"{h:02d}h", "count": hours_map.get(f"{h:02d}", 0)} for h in range(24)]


@router.get("/admin/failed-attempts")
def get_failed_attempts(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(FailedLoginAttempt)
        .order_by(FailedLoginAttempt.attempt_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id":         r.id,
            "ip":         r.ip_address or "—",
            "username":   r.username or "—",
            "user_agent": r.user_agent or "—",
            "blocked":    r.blocked,
            "date":       r.attempt_at.strftime("%d/%m/%Y %H:%M"),
        }
        for r in rows
    ]


@router.get("/admin/logs")
def get_logs(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(ConnexionLog, User.subject)
        .outerjoin(User, User.id == ConnexionLog.user_id)
        .order_by(ConnexionLog.created_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id":      l.id,
            "email":   l.email,
            "subject": subject or "—",
            "action":  l.action,
            "ip":      l.ip,
            "date":    l.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        for l, subject in rows
    ]


@router.get("/admin/stats/analytique")
def get_stats_analytique(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(
            User.email,
            User.prenom,
            User.nom,
            User.subject,
            User.niveau.label("niveau_profil"),
            ActiviteSauvegardee.matiere.label("activite_matiere"),
            ActiviteSauvegardee.niveau.label("activite_niveau"),
            ActiviteSauvegardee.activite_key,
            ActiviteSauvegardee.activite_label,
            func.count(ActiviteSauvegardee.id).label("nb"),
        )
        .join(User, User.id == ActiviteSauvegardee.user_id, isouter=True)
        .group_by(
            ActiviteSauvegardee.user_id,
            ActiviteSauvegardee.matiere,
            ActiviteSauvegardee.niveau,
            ActiviteSauvegardee.activite_key,
            ActiviteSauvegardee.activite_label,
        )
        .all()
    )

    profs_dict: dict = {}
    totaux_matiere: dict = {}
    totaux_niveau: dict = {}
    totaux_type: dict = {}
    grand_total = 0

    for row in rows:
        email = row.email
        if email not in profs_dict:
            profs_dict[email] = {
                "email": email,
                "prenom": row.prenom or "",
                "nom": row.nom or "",
                "subject": row.subject or "",
                "niveau_profil": row.niveau_profil or "",
                "total": 0,
                "par_matiere": {},
            }
        prof = profs_dict[email]
        prof["total"] += row.nb

        mat = row.activite_matiere or row.subject or "—"
        niv = row.activite_niveau or "—"
        typ = row.activite_label or row.activite_key or "—"

        if mat not in prof["par_matiere"]:
            prof["par_matiere"][mat] = {"total": 0, "par_niveau": {}}
        mat_data = prof["par_matiere"][mat]
        mat_data["total"] += row.nb

        if niv not in mat_data["par_niveau"]:
            mat_data["par_niveau"][niv] = {"total": 0, "par_type": {}}
        niv_data = mat_data["par_niveau"][niv]
        niv_data["total"] += row.nb
        niv_data["par_type"][typ] = niv_data["par_type"].get(typ, 0) + row.nb

        totaux_matiere[mat] = totaux_matiere.get(mat, 0) + row.nb
        totaux_niveau[niv] = totaux_niveau.get(niv, 0) + row.nb
        totaux_type[typ] = totaux_type.get(typ, 0) + row.nb
        grand_total += row.nb

    profs = sorted(profs_dict.values(), key=lambda p: -p["total"])

    return {
        "profs": profs,
        "totaux": {
            "par_matiere": dict(sorted(totaux_matiere.items(), key=lambda x: -x[1])),
            "par_niveau":  dict(sorted(totaux_niveau.items(),  key=lambda x: -x[1])),
            "par_type":    dict(list(sorted(totaux_type.items(), key=lambda x: -x[1]))[:20]),
            "grand_total": grand_total,
        },
    }
