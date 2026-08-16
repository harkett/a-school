import logging
import os
import re
import secrets
import unicodedata
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy import create_engine, func, text
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import Session

from backend.securite.audit import log_admin_action
from backend.core.cles import secret_obligatoire
from backend.core.database import get_db, get_db_size_mb, engine
from backend.core.schema_requete import schema_de
from backend.core.limiter import limiter
from backend.core.catalogues import catalogue
from backend.core.devises import DEVISES, en_euros
from backend.systeme.releve_tarifs import lire_page, relever
from backend.core.llm_prompts import PROMPTS
from backend.core.models_db import Activite, AdminAlert, AdminAuditLog, AiFournisseur, AiModele, ConnexionLog, Cycle, Demo, EmailEnvoi, EmailTemplate, EmailToken, FailedLoginAttempt, Feedback, FeedbackStatut, Incident, Matiere, Niveau, OutilLlm, PromptFonctionnalite, Referentiel, RefreshToken, Seance, Sequence, Setting, UsageLlm, User, UserSession, TacheAFaire, TachePlanifiee
# La fabrique du jeton de passage vit chez le prof (backend/prof/demo.py) : l'admin emprunte la
# MÊME, il n'en a pas une seconde. Import du module et non des fonctions — les deux modules se
# citent, et le module entier évite d'avoir à ordonner leurs imports.
from backend.prof import demo
from backend.core.resolution_couple import matiere_id_du_nom, matiere_nom_de_id, niveau_id_du_nom, niveau_nom_de_id
from backend.core.horloge import maintenant_utc

router = APIRouter()

_COOKIE  = "aschool_admin"
_MAX_AGE = 4 * 3600
_ALGO    = "HS256"


def _admin_secret() -> str:
    """Secret DÉDIÉ aux jetons admin, distinct du JWT_SECRET des jetons prof (isolation : un
    jeton prof ne peut pas servir de jeton admin même si le rôle n'était pas vérifié).

    Repli assumé sur JWT_SECRET tant qu'ADMIN_JWT_SECRET n'est pas posé — poser le second
    invalide les sessions admin en cours, l'admin se reconnecte, désormais isolé.

    MAIS PLUS DE CHAÎNE VIDE. Le `os.getenv("JWT_SECRET", "")` d'avant faisait qu'un serveur
    démarré sans aucun des deux secrets signait ses jetons admin avec `""` — c'est-à-dire
    avec un secret que le monde entier connaît, sans le moindre message. Une clé de signature
    vide n'est jamais un cas légitime : on refuse, comme le projet refuse déjà une base qui
    n'est pas PostgreSQL. Le message dit quoi poser.

    L'ORDRE des deux noms est la règle propre à l'admin ; la LECTURE et le REFUS, eux, sont
    ceux de `backend/core/cles.py`, partagés avec le jeton prof — le trou fermé ici l'était
    encore côté prof, parce que le raisonnement avait été recopié au lieu d'être mis en
    commun. Une seule copie, donc, qu'on ne peut plus corriger à moitié."""
    return secret_obligatoire(
        "ADMIN_JWT_SECRET", "JWT_SECRET",
        usage="les jetons admin",
        quoi_poser=(
            "Posez ADMIN_JWT_SECRET (recommandé, il isole l'admin du prof) ou, à défaut, "
            "JWT_SECRET dans le .env du serveur. Sans lui, les jetons admin seraient signés "
            "avec une chaîne vide."
        ),
    )


# AU DÉMARRAGE, pas au premier clic : le serveur refuse de monter sans secret, comme la suite
# de tests refuse de tourner sur autre chose que PostgreSQL. Découvrir ça à la première
# connexion admin — ou pire, ne jamais le découvrir — n'est pas une option pour une clé de
# signature. Cette ligne s'exécute à l'import du module, donc au boot de l'application.
_admin_secret()


def _make_admin_token() -> str:
    exp = maintenant_utc() + timedelta(hours=4)
    return jwt.encode({"sub": "admin", "role": "admin", "exp": exp}, _admin_secret(), algorithm=_ALGO)


def _verify_admin_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, _admin_secret(), algorithms=[_ALGO])
        return payload.get("role") == "admin"
    except JWTError:
        return False


def _require_admin(aschool_admin: str = Cookie(default=None)):
    if not aschool_admin or not _verify_admin_token(aschool_admin):
        raise HTTPException(401, "Votre session administrateur a expiré. Reconnectez-vous pour continuer.")


# LE DERNIER REPLI EN DUR — et il n'y en a plus qu'un.
#
# Ce dictionnaire portait 18 réglages, dont 16 SANS aucune ligne en base : `get_settings_dict()`
# partait de lui puis écrasait avec la base, donc c'était le code qui gagnait, en silence, pendant
# que chaque écran affirme que la base est la source unique. Un admin ne pouvait ni les voir ni
# les changer — il ne pouvait pas savoir qu'ils existaient. Les 14 réellement lus ont été SEMÉS
# en base (migration f1c9a3e7b5d2, valeurs identiques : rien n'a changé de comportement) ;
# `max_tokens_default` est mort avec son écran, `prompt_gabarit_type` doublait une ligne existante
# et annulait le filet de `get_prompt` (qui doit LEVER si la base est incomplète).
#
# CE QUI RESTE N'EST PAS UN RÉGLAGE, C'EST UN FILET. Si la ligne 'welcome' d'`email_templates`
# manque, le mail de bienvenue part quand même (`_WelcomeFallback`) : un inscrit qui ne le reçoit
# pas ne peut pas valider son compte. Ici, et ici seulement, un repli vaut mieux qu'un refus.
#
# N'AJOUTEZ RIEN ICI. Un réglage nouveau se sème par migration — c'est le seul endroit où il
# devient visible, lisible et modifiable.
SETTING_DEFAULTS = {
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
    # max_tokens : UN défaut global, et rien d'autre ici. Aucun outil n'est traité à part — une
    # surcharge `max_tokens_<outil>` n'existe que si l'admin l'a posée depuis l'écran. Lu au
    # runtime via get_max_tokens(db, outil), rechargeable à chaud comme ai_model.
}


def get_settings_dict(db: Session) -> dict:
    """Les réglages, LUS EN BASE. `SETTING_DEFAULTS` n'y ajoute plus que le filet du mail de
    bienvenue (voir son en-tête) : ce dictionnaire ne fabrique donc plus de valeur que personne
    n'a choisie. Une clé absente est absente — et les lecteurs ci-dessous le disent."""
    rows = db.query(Setting).all()
    result = dict(SETTING_DEFAULTS)
    for row in rows:
        result[row.key] = row.value
    return result


# Les valeurs SEMÉES par les migrations f1c9a3e7b5d2 et a4d8f2c6e1b9, recopiées ici pour un seul
# usage : le repli sur une valeur ILLISIBLE. La distinction est celle de tout le projet —
#   • ligne ABSENTE  = base incomplète (migration non appliquée). On le DIT, on ne devine pas.
#   • valeur FAUTIVE = erreur de saisie réparable. On tient sur la valeur d'origine plutôt que
#     de faire tomber une génération pour une virgule de trop.
# Ce n'est donc pas un repli de configuration : rien ici n'est lu quand la base répond.
VALEURS_ORIGINE = {
    "rag_top_k": "4",
    "stream_silence_timeout": "30",
    "ai_retry_max": "2",
    "ai_retry_wait_max": "10",
    "stats_minutes_par_activite": "15",
}


def _reglage(db: Session, cle: str) -> str:
    """Un réglage TEXTE lu en base. Ligne absente -> 500 explicite, jamais une valeur inventée."""
    s = get_settings_dict(db)
    if cle not in s:
        raise HTTPException(
            500,
            f"Réglage « {cle} » absent de la base (migration non appliquée ?). "
            f"Le serveur ne choisit pas de valeur à votre place.",
        )
    return s[cle]


def _reglage_ou_none(db: Session, cle: str):
    """Le même réglage, mais SANS refuser quand la ligne manque — réservé aux écrans de CHOIX.

    `_reglage` refuse, et c'est juste partout où la valeur sert à travailler : générer sans
    savoir avec quel modèle n'a pas de sens. Mais l'écran où l'on CHOISIT le modèle, lui, doit
    pouvoir s'ouvrir avant que le choix existe — sinon on perd l'écran par lequel on répare,
    exactement quand on en a besoin. C'est le raisonnement déjà tenu par `GET /admin/prompts`.

    Rend None si la ligne manque : l'écran montre « aucun choix », ce qui est la vérité."""
    return get_settings_dict(db).get(cle)


def _reglage_borne(db: Session, cle: str, mini: int, maxi: int) -> int:
    """Un GARDE-FOU technique, entier et borné — et il ne fait JAMAIS tomber une génération.

    La différence avec `_reglage` est celle entre un choix et un garde-fou. Le modèle d'IA est un
    choix : personne ne peut le faire à la place de l'administrateur, alors on refuse. Le nombre
    de re-tentatives sur un 429, la coupure de silence du flux, le top_k du RAG sont des réglages
    fins de plomberie : les faire lever priverait un professeur de sa génération pour une ligne
    manquante — le remède serait pire que le mal. On retombe donc sur la valeur qu'a semée la
    migration, aussi bien pour une ligne absente que pour une valeur illisible.

    Hors bornes = ramené dans les bornes, jamais refusé : les bornes existent pour ça."""
    s = get_settings_dict(db)
    try:
        v = int(s[cle])
    except (KeyError, TypeError, ValueError):
        v = int(VALEURS_ORIGINE[cle])
    return max(mini, min(maxi, v))


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


def get_ai_model(db: Session) -> str:
    """Modèle LLM texte courant, lu en base au moment de l'appel (repli sur le défaut
    code). Source unique de résolution du modèle pour tous les routers — branche sur
    l'existant (get_settings_dict). Côté backend uniquement : la valeur (chaîne) descend
    ensuite dans generate(), qui reste pur (aucune connaissance de la base)."""
    return _reglage(db, "ai_model")


def get_ai_provider(db: Session) -> str:
    """Fournisseur LLM texte courant, lu en base au moment de l'appel (repli sur le défaut
    code). Source unique de résolution du fournisseur pour tous les routers — même moule que
    get_ai_model (branche sur get_settings_dict). La valeur (chaîne) descend ensuite dans
    generate() via le paramètre `provider`, qui reste pur (aucune connaissance de la base)."""
    return _reglage(db, "ai_provider")


def get_ocr_model(db: Session) -> str:
    """Modèle OCR (Groq vision) courant, lu en base au moment de l'appel (repli sur le défaut
    code). Même moule que get_ai_model. La valeur (chaîne) descend ensuite dans transcribe_image,
    qui reste pur (aucune connaissance de la base). Le fournisseur OCR reste Groq (seul moteur
    vision, pas d'alternative) : seul le modèle est administrable."""
    return _reglage(db, "ocr_model")


def get_cle_api(db: Session, cle_setting: str) -> str:
    """Résout la clé API d'un usage (OCR, dictée) : le NOM de la variable d'environnement
    vit EN BASE (settings.<cle_setting>), sa VALEUR (le secret) reste dans le .env — jamais
    en base. On lit le nom en base, puis os.getenv(nom). Erreurs CLAIRES (jamais un vide
    silencieux) : nom absent de la base (migration non appliquée) ou clé absente du .env.
    Côté backend uniquement : la clé descend ensuite en paramètre dans src (qui reste pur)."""
    nom = get_settings_dict(db).get(cle_setting)
    if not nom:
        raise HTTPException(500, f"Configuration manquante : « {cle_setting} » absent en base (migration non appliquée ?).")
    cle = os.getenv(nom, "")
    if not cle:
        raise HTTPException(500, f"Clé API absente du .env : la variable « {nom} » n'est pas définie.")
    return cle


def get_cle_texte(db: Session) -> str:
    """Résout la clé API TEXTE du fournisseur ACTIF. Le NOM de sa variable d'environnement vit
    EN BASE (ai_fournisseurs.cle_env), sa VALEUR (le secret) reste dans le .env — jamais en base.
    On lit le fournisseur actif (get_ai_provider), puis SON cle_env en base, puis os.getenv(nom).
    Zéro nom de variable en dur : la source unique est la ligne ai_fournisseurs. Erreurs CLAIRES
    (jamais un vide silencieux). Même moule que get_cle_api (OCR/dictée) ; la clé descend ensuite
    en paramètre dans generate(), qui reste pur (aucune connaissance de la base)."""
    provider = get_ai_provider(db)
    f = db.query(AiFournisseur).filter(AiFournisseur.code == provider).first()
    if f is None:
        raise HTTPException(500, f"Configuration manquante : fournisseur « {provider} » absent de la table ai_fournisseurs.")
    if not f.cle_env:
        raise HTTPException(500, f"Configuration manquante : « cle_env » vide pour « {provider} » (migration non appliquée ?).")
    cle = os.getenv(f.cle_env, "")
    if not cle:
        raise HTTPException(500, f"Clé API absente du .env : la variable « {f.cle_env} » n'est pas définie.")
    return cle


# Bornes de top_k (nb de chunks ramenés par le RAG). MIN 1 (au moins un extrait) ;
# MAX = garde-fou coût/pertinence.
RAG_TOP_K_MIN = 1
RAG_TOP_K_MAX = 20


_log = logging.getLogger(__name__)


def liste_fournisseurs(db: Session) -> list[dict]:
    """L'ORDRE D'APPEL — le catalogue, et rien d'autre.

    Une entrée par fournisseur actif, dans l'ordre de `ai_fournisseurs.ordre`, chacune portant de
    quoi l'appeler sans rien redemander à la base : son code, SA clé, SON modèle recommandé, et les
    bornes de ce modèle.

    IL N'Y A PLUS DE FOURNISSEUR « EN SERVICE ». C'était le principe de l'ancien système : un élu,
    désigné dans un écran, seul appelé, et un échec pour le professeur quand il refusait. Ici, la
    liste est l'ordre : le premier est appelé d'abord parce qu'il est premier au catalogue — pas
    parce qu'un réglage l'a sacré. L'administrateur range, il ne choisit plus.

    C'EST CE QUI FAIT QUE LE GRATUIT PASSE D'ABORD. Groq est premier au catalogue parce qu'il ne
    coûte rien ; les payants suivent, classés par leur prix. Un ordre qui dépendrait d'un réglage
    séparé pourrait, lui, placer un payant devant le gratuit — c'est exactement ce qui se passait.

    CHAQUE ENTRÉE PORTE LES SIENS. `mistral3` n'existe pas chez Anthropic, la clé d'Anthropic
    n'ouvre pas Infomaniak, et la fenêtre de l'un n'est pas celle de l'autre. Reprendre les valeurs
    du premier pour appeler le second, c'est le faire échouer à coup sûr.

    CE QUI EST ÉCARTÉ, EN SILENCE ET VOLONTAIREMENT :
      * les fournisseurs `actif = false` — « pas encore disponible » veut dire ce qu'il dit ;
      * ceux dont la clé manque du `.env` ;
      * ceux dont le catalogue n'a aucun modèle actif.
    Une clé absente ne doit pas faire échouer la génération d'un professeur : elle doit retirer ce
    fournisseur de la liste, c'est tout. Le journal du serveur le note, l'écran des fournisseurs le
    montre déjà.

    LISTE VIDE = aucun appel possible. Le cas ne se produit que sur une installation neuve, avant
    la première configuration.
    """
    # PAS DE BASE, PAS DE LISTE. Le mode long de la découpe appelle avec `db=None`, le fournisseur
    # lui étant passé tout résolu. Rendre vide plutôt que lever : cet appel marchait avant la
    # liste, il doit marcher après.
    if db is None:
        return []
    voies: list[dict] = []
    for f in (db.query(AiFournisseur)
                .filter(AiFournisseur.actif.is_(True))
                .order_by(AiFournisseur.ordre.asc(), AiFournisseur.code.asc()).all()):
        cle = os.getenv(f.cle_env, "") if f.cle_env else ""
        if not cle:
            _log.warning("Fournisseur écarté de la liste : « %s » n'a pas de clé dans le .env (%s).",
                         f.code, f.cle_env or "—")
            continue
        # Le modèle recommandé du fournisseur — la colonne existe et l'écran s'en sert déjà pour
        # proposer un défaut. Faute de recommandé, le premier actif : mieux vaut un modèle du bon
        # fournisseur que pas de fournisseur du tout.
        modele = (db.query(AiModele)
                    .filter(AiModele.fournisseur == f.code, AiModele.actif.is_(True))
                    .order_by(AiModele.recommande.desc(), AiModele.ordre.asc()).first())
        if modele is None:
            _log.warning("Fournisseur écarté de la liste : « %s » n'a aucun modèle actif.", f.code)
            continue
        voies.append({
            "provider": f.code,
            "cle": cle,
            "model": modele.modele,
            # Le plafond de sortie du modèle, sinon celui du fournisseur. Infomaniak REFUSE au-delà
            # de 5 000 (422) : lui envoyer le plafond réglé pour un autre le ferait échouer pour la
            # seule raison qu'on ne l'a pas borné.
            "max_tokens": modele.max_tokens or f.max_tokens,
            # SA fenêtre à lui. Le contrôle amont se rejoue donc à chaque rang : un document trop
            # gros pour Infomaniak (32 000) tient chez Anthropic (1 000 000).
            "contexte_max": modele.contexte_max,
        })
    return voies


def get_rag_top_k(db: Session) -> int:
    """Nombre de chunks ramenés par le RAG (top_k), lu en base au moment de l'appel (repli
    sur le défaut code). Même motif que get_max_tokens : rechargeable à chaud. Renvoie un int
    borné [MIN, MAX] ; valeur corrompue / hors bornes -> défaut."""
    return _reglage_borne(db, "rag_top_k", RAG_TOP_K_MIN, RAG_TOP_K_MAX)


# Bornes de la coupure de silence du flux (secondes). MIN = un plancher qui laisse le modèle
# « respirer » entre deux morceaux ; MAX = garde-fou pour ne pas laisser un flux muet pendre trop
# longtemps. Ce n'est PAS la durée totale d'une génération (le délai se réarme à chaque morceau).
STREAM_SILENCE_MIN = 5
STREAM_SILENCE_MAX = 300


def get_stream_silence_timeout(db: Session) -> int:
    """Coupure de silence du flux de génération (secondes), lue en base au moment de l'appel
    (rechargeable à chaud, même motif que get_rag_top_k). Renvoie un int borné [MIN, MAX] ;
    valeur corrompue / hors bornes -> défaut code."""
    return _reglage_borne(db, "stream_silence_timeout", STREAM_SILENCE_MIN, STREAM_SILENCE_MAX)


# Bornes de la résilience 429 (retry). retry_max borné pour ne jamais boucler à l'infini ;
# wait_max borné pour ne jamais laisser un prof attendre trop longtemps une re-tentative.
RETRY_MAX_MIN = 0
RETRY_MAX_MAX = 5
RETRY_WAIT_MIN = 1
RETRY_WAIT_MAX = 60


def get_retry_max(db: Session) -> int:
    """Nombre de re-tentatives sur un 429 fournisseur, lu en base au moment de l'appel (rechargeable
    à chaud, même motif que get_stream_silence_timeout). Renvoie un int borné [MIN, MAX] ; valeur
    corrompue / hors bornes -> défaut code (jamais d'exception)."""
    return _reglage_borne(db, "ai_retry_max", RETRY_MAX_MIN, RETRY_MAX_MAX)


def get_retry_wait_max(db: Session) -> int:
    """Plafond d'attente (secondes) PAR re-tentative sur un 429, lu en base au moment de l'appel.
    Le back attend min(Retry-After fournisseur, ce plafond). Renvoie un int borné [MIN, MAX] ;
    valeur corrompue / hors bornes -> défaut code (jamais d'exception)."""
    return _reglage_borne(db, "ai_retry_wait_max", RETRY_WAIT_MIN, RETRY_WAIT_MAX)


def get_contexte_max(db: Session) -> int | None:
    """Fenêtre TOTALE du modèle courant (entrée + sortie), lue EN BASE (ai_modeles.contexte_max).
    None = fenêtre inconnue → aucun contrôle en amont, comme avant.

    Deux bornes à ne pas confondre : `max_tokens` limite ce que le modèle ÉCRIT, celle-ci ce qu'il
    peut TENIR. Plafonner la sortie ne sauve pas un document trop gros — l'entrée seule suffit à
    faire refuser l'appel (400), après plusieurs minutes d'attente."""
    modele = (
        db.query(AiModele)
        .filter(AiModele.fournisseur == get_ai_provider(db), AiModele.modele == get_ai_model(db))
        .first()
    )
    return modele.contexte_max if modele else None


def get_max_tokens_modele(db: Session) -> int | None:
    """`max_tokens` applicable au modèle courant, lu EN BASE. None = aucune valeur connue.

    HÉRITAGE : la valeur du MODÈLE l'emporte si elle existe, sinon celle de son FOURNISSEUR. Les
    5 000 tokens d'Infomaniak ne tiennent pas à un modèle en particulier — les trois du produit les
    partagent — les poser sur le fournisseur évite de les recopier à chaque modèle ajouté, et un
    modèle qui ferait exception garde le droit de les surcharger.

    Ce n'est pas un réglage : c'est ce que le fournisseur ACCEPTE. Il refuse la requête en 422
    au-delà — sans ce garde-fou, toute demande plus haute fait échouer la génération entière au
    lieu de la raccourcir.

    Nom en `_modele` pour ne pas se confondre avec `get_max_tokens(db, outil)`, qui lit encore les
    réglages d'écran : celle-ci dit ce que le MODÈLE accepte, l'autre ce qu'on lui DEMANDE."""
    # Lecture TOLÉRANTE du couple courant : cette fonction est appelée par l'écran de choix du
    # modèle, qui doit s'ouvrir avant même qu'un modèle soit choisi. Sans couple, aucune fiche —
    # donc None, et l'appelant applique son filet.
    provider = _reglage_ou_none(db, "ai_provider")
    modele_courant = _reglage_ou_none(db, "ai_model")
    if not provider or not modele_courant:
        return None
    modele = (
        db.query(AiModele)
        .filter(AiModele.fournisseur == provider, AiModele.modele == modele_courant)
        .first()
    )
    if modele is not None and modele.max_tokens:
        return modele.max_tokens
    fournisseur = db.query(AiFournisseur).filter(AiFournisseur.code == provider).first()
    return fournisseur.max_tokens if fournisseur else None


# Valeur envoyée quand le modèle en service n'a PAS de `max_tokens` en base. Ce n'est pas un
# réglage : c'est un filet, parce que l'API exige toujours un nombre et qu'une fiche incomplète ne
# doit pas empêcher de générer. Volontairement modeste — une réponse courte se voit et se corrige
# en remplissant la fiche ; un grand nombre envoyé à un modèle qui le refuse fait échouer l'appel.
MAX_TOKENS_SANS_FICHE = 4096


def get_max_tokens(db: Session, outil: str) -> int:
    """Ce qu'on demande au modèle d'écrire au plus, POUR TOUS LES OUTILS : son `max_tokens` de
    fiche (modèle, sinon fournisseur). Lecture par requête -> rechargeable à chaud.

    POURQUOI PLUS DE RÉGLAGE PAR OUTIL. `max_tokens` n'allonge ni ne raccourcit une réponse : le
    modèle s'arrête quand il a fini. Ce nombre ne fait QUE couper s'il dépasse. Régler 17 outils à
    la main, c'était donc régler 17 couperets — et un seul avait une valeur voulue. Le résultat
    tenait de la panne : un référentiel découpé à 5 000 jetons parce qu'un réglage hérité
    d'Infomaniak survivait au passage chez Anthropic, alors que le modèle en service en acceptait
    128 000. Le seul chiffre qui a du sens est celui du modèle, et il est déjà sur sa fiche.

    LA LONGUEUR VOULUE SE DIT DANS LE PROMPT, pas ici — la découpe le fait déjà (« le texte doit
    tenir en N caractères »). C'est la seule consigne que le modèle sait respecter.

    `outil` reste dans la signature : les 17 appelants ne changent pas, et le jour où un outil aura
    besoin d'une exception, elle se posera ici sans les toucher."""
    return get_max_tokens_modele(db) or MAX_TOKENS_SANS_FICHE


# `get_outils_llm` A ÉTÉ SUPPRIMÉE le 10/08/2026. Elle rendait la table `outils_llm` triée pour
# l'écran des longueurs — écran supprimé le même jour (migration e2b6d4a8f7c1), et elle n'avait
# pas d'autre appelant. La table, elle, RESTE : l'écran des statistiques y lit le libellé lisible
# de chaque outil (`analytique/stats.py`), et il la lit directement.


# Bornes de température (Phase 4.1.d). Plage standard des API compatibles OpenAI/Groq.
# Rappel : « le mieux » N'EST PAS « le plus haut » — haute température = sorties moins fiables
# (hallucinations, format cassé). Pour du pédagogique, le bon réglage est bas à modéré.
TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 2.0


def modele_supporte_temperature(db: Session) -> bool:
    """Le modèle en service accepte-t-il `temperature` ? Lu EN BASE (ai_modeles). Vrai par défaut :
    c'est le cas général, et un modèle absent de la fiche ne doit pas faire perdre un réglage.

    Les Claude Opus 4.x et les modèles 5 la REJETTENT en 400. C'était écrit en dur dans le moteur,
    au nom du fournisseur entier — donc invisible ici, et faux pour tout modèle Anthropic futur qui
    l'accepterait. La question se pose au modèle, pas au code."""
    provider = _reglage_ou_none(db, "ai_provider")
    courant = _reglage_ou_none(db, "ai_model")
    if not provider or not courant:
        return True   # aucun couple choisi : on ne prive pas l'admin du réglage
    modele = (
        db.query(AiModele)
        .filter(AiModele.fournisseur == provider, AiModele.modele == courant)
        .first()
    )
    return True if modele is None else bool(modele.supporte_temperature)


def get_temperature(db: Session):
    """Température courante (GLOBALE), lue en base au moment de l'appel (rechargeable à chaud,
    même motif que get_max_tokens). Renvoie un float dans [MIN, MAX], ou None si non réglée ->
    generate() n'envoie alors RIEN et le fournisseur applique son défaut (comportement
    historique = zéro régression). Valeur corrompue / hors bornes -> None (jamais d'exception).

    None AUSSI quand le modèle en service ne la supporte pas. Un seul endroit décide, ici : les 17
    outils appellent tous cette fonction, aucun n'a à connaître la question. C'est ce qui permet au
    moteur d'oublier « Anthropic refuse la température » — il envoie ce qu'on lui donne."""
    if not modele_supporte_temperature(db):
        return None
    raw = get_settings_dict(db).get("ai_temperature", "")
    if raw is None or str(raw).strip() == "":
        return None
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    return v if TEMPERATURE_MIN <= v <= TEMPERATURE_MAX else None


def get_minutes_par_activite(db: Session) -> int:
    """Minutes « gagnées » comptées par activité créée (KPI Mes stats), lues en base au
    moment de l'appel (surcharge `stats_minutes_par_activite`, défaut code) — même moule
    hybride que get_max_tokens. Valeur corrompue -> défaut, jamais d'exception."""
    try:
        return int(get_settings_dict(db)["stats_minutes_par_activite"])
    except (KeyError, TypeError, ValueError):
        return int(VALEURS_ORIGINE["stats_minutes_par_activite"])


def _reglage_entier(db: Session, cle: str, minimum: int) -> int:
    """Réglage NUMÉRIQUE dont la valeur initiale est SEMÉE par migration — pas de défaut code
    (règle maison : la base est la source unique, une base vide est une erreur qu'on dit, pas
    un cas qu'on rattrape en douce). Ligne absente ou valeur inexploitable -> 500 explicite."""
    row = db.query(Setting).filter(Setting.key == cle).first()
    try:
        valeur = int((row.value or "").strip())
    except (AttributeError, TypeError, ValueError):
        raise HTTPException(500, f"Réglage « {cle} » absent ou illisible en base (migration non appliquée ?).")
    if valeur < minimum:
        raise HTTPException(500, f"Réglage « {cle} » invalide en base (attendu : au moins {minimum}).")
    return valeur


def get_few_shot_seuil(db: Session) -> int:
    """Nombre d'activités du même type ET du même couple à partir duquel la génération
    s'inspire du style du prof (few-shot). Semé à 3 par migration — c'est ce que l'astuce
    de l'Accueil promet au prof, et ce que Mes stats affiche."""
    return _reglage_entier(db, "few_shot_seuil", minimum=1)


def get_few_shot_extrait_max(db: Session) -> int:
    """Nombre de caractères gardés par activité donnée en exemple au few-shot."""
    return _reglage_entier(db, "few_shot_extrait_max", minimum=200)


def get_prompt(db: Session, key: str) -> str:
    """Prompt courant d'un outil, LU EN BASE (`prompt_<key>`). Lu par requête -> rechargeable à
    chaud. Le contenu en base est validé À L'ÉCRITURE (repères obligatoires présents + .format()
    sans casse), donc sûr ici.

    PLUS DE REPLI SUR LE DÉFAUT CODE (étape 9 lot C). Il rendait la base facultative : 32 des 35
    prompts n'y étaient pas et tout marchait, donc rien ne le disait. Ce que la base contient
    n'était pas la vérité, c'était un cache partiel. Ligne absente -> erreur explicite, comme
    `_reglage_entier` (règle maison : une base vide se dit, elle ne se rattrape pas en douce).
    Les textes de `llm_prompts.PROMPTS` restent la RÉFÉRENCE : ils alimentent la migration de
    seed et le bouton « revenir au défaut » de l'écran admin — le runtime, lui, ne les lit plus.

    Le chemin de réparation est /admin/prompts, qui dit quelle clé manque sans jamais lever."""
    base = get_settings_dict(db).get(f"prompt_{key}", "")
    if base and base.strip():
        return base
    if key not in PROMPTS:
        raise HTTPException(500, f"Prompt « {key} » inconnu : aucun outil ne le déclare.")
    raise HTTPException(500, f"Prompt « {key} » absent en base (migration non appliquée ?).")


def valider_prompt(key: str, template: str) -> str | None:
    """Garde-fou d'écriture d'un prompt. Renvoie un message d'erreur (langage humain) si le
    prompt est invalide, sinon None.

    (1) Chaque repère obligatoire `{x}` doit rester présent — vrai dans les DEUX modes : c'est
        la seule garantie que la valeur atteindra vraiment le modèle.
    (2) Le reste dépend du MODE déclaré au registre (cf. l'en-tête de `PROMPTS`) :
        - "format" (défaut) : le texte doit `.format()` sans lever — un repère inconnu ou des
          accolades déséquilibrées casseraient la génération ;
        - "replace" : on N'APPELLE PAS `.format()`. Ces prompts DÉCRIVENT un autre prompt ;
          leurs autres accolades sont du texte à préserver, pas des repères. Les formater
          lèverait sur leur contenu même — donc un tel contrôle refuserait le texte LÉGITIME.
    """
    meta = PROMPTS.get(key)
    if meta is None:
        return "Prompt inconnu."
    required = meta["placeholders"]
    for ph in required:
        if "{" + ph + "}" not in template:
            return (f"Le repère {{{ph}}} est obligatoire dans ce prompt et a disparu. "
                    f"Remettez-le tel quel avant d'enregistrer.")
    if meta.get("mode", "format") == "replace":
        return None
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
        payload = jwt.decode(token, _admin_secret(), algorithms=[_ALGO])
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
    # AMORÇAGE SEUL, et non « les deux ouvrent ». Le mot de passe du .env sert tant qu'aucun
    # n'a été choisi ; dès qu'un existe en base, lui seul ouvre. C'est déjà la règle appliquée
    # par /admin/change-password (voir plus bas, `if pwd_setting: ... else: ...`) : la connexion
    # faisait `env_ok or db_ok`, donc l'ancien mot de passe du .env continuait d'ouvrir APRÈS
    # un changement — le bouton « changer mon mot de passe » ne fermait rien. Les deux routes
    # disent maintenant la même chose.
    # SECOURS en cas d'oubli : supprimer la ligne `admin_password_hash` de la table `settings`
    # remet le mot de passe du .env en service (procédure dans PROJET.md).
    if pwd_setting:
        try:
            password_ok = _bcrypt.checkpw(body.password.encode("utf-8"), pwd_setting.value.encode("utf-8"))
        except Exception:
            password_ok = False
    else:
        password_ok = bool(expected_pass) and secrets.compare_digest(body.password, expected_pass)
    ok = username_ok and password_ok
    if not ok:
        attempt = FailedLoginAttempt(
            ip_address=ip,
            username=body.username,
            user_agent=request.headers.get("user-agent", ""),
        )
        db.add(attempt)
        db.commit()
        since = maintenant_utc() - timedelta(hours=1)
        count = db.query(FailedLoginAttempt).filter(
            FailedLoginAttempt.ip_address == ip,
            FailedLoginAttempt.attempt_at >= since,
        ).count()
        # Le seuil de blocage était écrit « 10 » ici, juste à côté du réglage `alerte_tentatives_1h`
        # qui vaut 10 en base : deux vérités pour un seul nombre, dont une seule se règle.
        if count >= _reglage_entier(db, "alerte_tentatives_1h", 1):
            db.query(FailedLoginAttempt).filter(
                FailedLoginAttempt.ip_address == ip,
                FailedLoginAttempt.attempt_at >= since,
            ).update({"blocked": True})
            db.commit()
        raise HTTPException(401, "Identifiants incorrects.")
    response.set_cookie(_COOKIE, _make_admin_token(), max_age=_MAX_AGE, httponly=True, samesite="lax", secure=os.getenv("ENV") == "production")
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
    if "miroir" in n:
        type_ = "miroir"
    elif "test" in n:
        type_ = "test"
    elif n in ("aschool", "aschool_dev"):
        type_ = "reelle"
    else:
        type_ = "autre"
    return {"base": nom, "host": engine.url.host, "port": engine.url.port, "type": type_}


@router.get("/admin/base/carte")
def admin_base_carte(_: None = Depends(_require_admin)):
    """Rend la carte visuelle de la base : structure RÉELLE lue dans information_schema, dessinée
    par `outils_bdd/carte_base/carte.py`. Lecture seule, aucune écriture.

    Elle est CONSTRUITE ET RENVOYÉE ici, page HTML autonome (le moteur de dessin est embarqué,
    aucun appel réseau) — donc elle marche depuis n'importe où : le conteneur du poste comme le
    VPS. L'ancienne version lançait le script en sous-processus et se terminait par
    `cmd /c start msedge` : sur un serveur Linux, elle ne pouvait par construction jamais
    aboutir, et l'écran offrait quand même le bouton. Une route qui ne peut pas tenir sa
    promesse n'est pas une route, c'est un piège.

    Le moteur passé à `lire_schema` est celui de l'APPLICATION : la carte montre la base où le
    serveur tourne vraiment, jamais celle qu'un fichier .env raconte."""
    import importlib.util
    from pathlib import Path
    from fastapi.responses import HTMLResponse
    from backend.core.database import engine

    script = Path(__file__).resolve().parents[2] / "outils_bdd" / "carte_base" / "carte.py"
    if not script.exists():
        raise HTTPException(500, "Script de la carte introuvable (outils_bdd/carte_base/carte.py).")
    # `outils_bdd` n'est pas un paquet : on charge le module par son chemin.
    spec = importlib.util.spec_from_file_location("carte_base_outil", script)
    carte = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(carte)
        html = carte.construire_html(carte.lire_schema(engine))
    except Exception as e:
        raise HTTPException(500, f"Construction de la carte impossible : {e}")
    return HTMLResponse(html)


@router.get("/admin/feedbacks")
def get_feedbacks(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    rows = (
        db.query(Feedback, User.email)
        .outerjoin(User, User.id == Feedback.user_id)
        .order_by(Feedback.created_at.desc())
        .limit(200)
        .all()
    )
    # Incident technique rattaché (Fix 2) : le prof a signalé depuis un échec de génération, l'incident
    # (erreur brute + contexte) est relié via incidents.feedback_id → l'admin voit ce qui a planté.
    # Une seule requête pour tous les feedbacks affichés ; un feedback sans incident garde `incident: None`.
    ids = [f.id for f, _ in rows]
    incidents_par_feedback = {}
    if ids:
        for inc in (
            db.query(Incident)
            .filter(Incident.feedback_id.in_(ids))
            .order_by(Incident.created_at.desc())
            .all()
        ):
            incidents_par_feedback.setdefault(inc.feedback_id, inc)
    # L'échange qui suit chaque retour (réponses de l'administration et du prof), en UNE requête.
    from backend.communication import echange
    echanges = echange.messages_par_feedback(db, ids)
    return [
        {
            "id":       f.id,
            "email":    email,
            "type":     f.type,
            "message":  f.message,
            "rating":   f.rating,
            "category": f.category,
            "contexte": f.contexte,
            "statut":   f.statut,
            "date":     f.created_at.strftime("%d/%m/%Y %H:%M"),
            "incident": _incident_dict(incidents_par_feedback.get(f.id)),
            "messages": echange.serialiser(echanges.get(f.id, []), vu_par_admin=True,
                                           email_prof=email),
        }
        for f, email in rows
    ]


def _incident_dict(inc):
    """Vue admin d'un incident technique rattaché à un feedback (None si aucun)."""
    if inc is None:
        return None
    return {
        "ref":           inc.ref,
        "date":          inc.created_at.strftime("%d/%m/%Y %H:%M") if inc.created_at else None,
        "endpoint":      inc.endpoint,
        "provider":      inc.provider,
        "model":         inc.model,
        "error":         inc.error,
        "matiere":       inc.matiere,
        "niveau":        inc.niveau,
        "type_activite": inc.type_activite,
        "consigne":      inc.consigne,
    }


class StatutBody(BaseModel):
    statut: str


def codes_statuts_assignables(db: Session) -> set[str]:
    """Codes de statut qu'un admin peut ASSIGNER à un feedback (toutes les lignes du
    catalogue `feedback_statuts`), lus EN BASE. Aucune liste en dur. Table vide = migration
    non appliquée -> on lève (erreur claire) plutôt que de retomber sur du dur caché."""
    codes = {c for (c,) in db.query(FeedbackStatut.code).all()}
    if not codes:
        raise HTTPException(500, "Statuts de feedback absents en base (migration non appliquée ?).")
    return codes


def codes_statuts_modifiables(db: Session) -> set[str]:
    """Codes de statut dans lesquels un feedback reste modifiable par son auteur
    (`modifiable=true`), lus EN BASE. Notion SOURCE (statut actuel du feedback), distincte des
    statuts assignables. Un ensemble vide de modifiables est légitime ; mais table vide =
    migration non appliquée -> on lève (même contrôle que codes_statuts_assignables)."""
    rows = db.query(FeedbackStatut.code, FeedbackStatut.modifiable).all()
    if not rows:
        raise HTTPException(500, "Statuts de feedback absents en base (migration non appliquée ?).")
    return {code for code, modifiable in rows if modifiable}


def code_statut_initial(db: Session) -> str:
    """Code du statut qu'un retour porte à son dépôt, lu EN BASE : celui d'`ordre` minimal.

    Le tableau de bord admin comptait `Feedback.statut == "nouveau"`, écrit en dur — alors que
    les statuts vivent en base depuis le chantier `feedback_statuts` et que leur ordre y est
    porté par une colonne. Renommer le premier statut, ou en insérer un avant lui, faisait
    tomber ce compteur à zéro sans qu'aucune erreur ne le signale : un compteur faux ne se
    plaint pas, il compte mal.

    Table vide = migration non appliquée -> on lève (même contrôle que codes_statuts_assignables).
    """
    code = (db.query(FeedbackStatut.code)
              .order_by(FeedbackStatut.ordre.asc())
              .limit(1)
              .scalar())
    if not code:
        raise HTTPException(500, "Statuts de feedback absents en base (migration non appliquée ?).")
    return code


def labels_statuts(db: Session) -> dict[str, str]:
    """Libellé de chaque statut de feedback (code -> label), lu EN BASE. L'écran prof affiche
    CE libellé — plus de copie « Nouveau »/« Traité » côté front. Table vide = migration non
    appliquée -> on lève (même contrôle que codes_statuts_assignables)."""
    rows = db.query(FeedbackStatut.code, FeedbackStatut.label).all()
    if not rows:
        raise HTTPException(500, "Statuts de feedback absents en base (migration non appliquée ?).")
    return dict(rows)


@router.get("/admin/feedback-statuts", dependencies=[Depends(_require_admin)])
def lister_feedback_statuts(db: Session = Depends(get_db)):
    """Catalogue des statuts de feedback, LU EN BASE — l'écran admin n'en garde plus de copie
    (libellés, filtres et ordre sortaient d'une liste en dur : un statut ajouté en base se
    serait affiché « Nouveau »). Même source que l'écran prof. Table vide = migration non
    appliquée -> erreur claire, jamais de repli en dur."""
    rows = (db.query(FeedbackStatut)
              .order_by(FeedbackStatut.ordre, FeedbackStatut.code).all())
    if not rows:
        raise HTTPException(500, "Statuts de feedback absents en base (migration non appliquée ?).")
    return [{"code": s.code, "label": s.label, "ordre": s.ordre, "modifiable": s.modifiable}
            for s in rows]


@router.patch("/admin/feedbacks/{feedback_id}/statut")
def update_feedback_statut(
    feedback_id: int,
    body: StatutBody,
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    if body.statut not in codes_statuts_assignables(db):
        raise HTTPException(400, "Statut invalide.")
    fb = db.get(Feedback, feedback_id)
    if not fb:
        raise HTTPException(404, "Feedback introuvable.")
    fb.statut = body.statut
    db.commit()
    return {"status": "ok"}


class ReponseBody(BaseModel):
    corps: str


@router.post("/admin/feedbacks/{feedback_id}/messages")
def repondre_au_feedback(
    feedback_id: int,
    body: ReponseBody,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    """L'administration répond au prof SUR son retour. La réponse s'écrit en base et se lit
    dans aSchool ; le prof reçoit un avis par mail qui n'en porte pas le contenu."""
    from backend.communication import echange

    fb = db.get(Feedback, feedback_id)
    if not fb:
        raise HTTPException(404, "Feedback introuvable.")

    try:
        message, statut_avis, erreur_avis = echange.ajouter_message(
            db, fb, body.corps, est_admin=True,
        )
    except echange.CorpsInvalide as e:
        raise HTTPException(400, str(e))

    email_prof = db.query(User.email).filter(User.id == fb.user_id).scalar()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="REPONSE_FEEDBACK",
        target_email=email_prof,
        ip=request.client.host if request.client else None,
        details=f"Réponse déposée sur le retour #{feedback_id} (avis par mail : {statut_avis})",
    )
    return {
        "status": "ok",
        "message": echange.serialiser([message], vu_par_admin=True, email_prof=email_prof)[0],
        # La réponse est enregistrée dans tous les cas ; l'avis, lui, a pu échouer.
        "avis_envoye": statut_avis == "envoye",
        "avis_erreur": erreur_avis,
    }


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


class UpdateUserBody(BaseModel):
    prenom: str = ""
    nom: str = ""
    subject: str = ""
    niveau: str = ""


@router.get("/admin/users")
def get_users(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    # Compté sur le monde NEUF (table activites) — décision 30/07, l'ancien monde disparaît.
    counts = dict(
        db.query(Activite.user_id, func.count(Activite.id))
        .group_by(Activite.user_id)
        .all()
    )
    return [
        {
            "email":        u.email,
            "prenom":       u.prenom or "",
            "nom":          u.nom or "",
            "subject":      matiere_nom_de_id(db, u.subject_id) or "",
            "niveau":       niveau_nom_de_id(db, u.niveau_id) or "",
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
    # Couple rangé UNIQUEMENT par clé (put). Le NIVEAU d'abord : c'est lui qui donne le
    # référentiel, et le référentiel qui donne SA matière — le nom d'une matière ne désigne rien
    # tout seul depuis que chaque diplôme nomme les siennes.
    niveau_id   = niveau_id_du_nom(db, body.niveau or None)
    subject_nom = (body.subject or "").strip()
    subject_id  = matiere_id_du_nom(db, subject_nom or None, niveau_id)

    # Le couple doit être AU PROGRAMME. Sans ce contrôle, l'admin pouvait ranger un prof sur
    # « Français en Crèche » : un couple qui n'existe nulle part, que les écrans du prof ne
    # savent pas servir. Un profil incomplet (aucun des deux) reste permis — c'est l'état normal
    # d'un compte qui vient de naître.
    if subject_nom and not niveau_id:
        raise HTTPException(
            400,
            "Choisissez d'abord le niveau : une matière appartient au programme d'un niveau."
        )
    if subject_nom and not subject_id:
        raise HTTPException(
            400,
            f"« {body.subject} » n'est pas au programme de « {body.niveau} ». "
            "Ajoutez-la au référentiel de ce niveau dans Formations, "
            "ou choisissez-en une autre."
        )

    user.prenom     = body.prenom or None
    user.nom        = body.nom or None
    user.subject_id = subject_id
    user.niveau_id  = niveau_id
    db.commit()
    return {"status": "ok"}


@router.delete("/admin/user/{email}")
def delete_user(email: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    # CE QUI EST PURGÉ ICI : les tables reliées au compte SANS cascade en base (email_tokens et
    # connexion_logs n'ont même pas de clé étrangère : ce sont des journaux à l'email).
    # CE QUI PART TOUT SEUL : les tables dont la clé étrangère porte ON DELETE (migration
    # e4b8c2d6a1f7) — cahiers_prof, feature_votes, tool_usage_logs en CASCADE,
    # incidents.feedback_id en SET NULL (l'incident technique survit).
    # Ne PAS les rajouter à la main ici : la base est la garantie, pas cette liste.
    # (Cette liste citait aussi user_enseignements : cette table a été SUPPRIMÉE depuis, par
    # la migration f8b3d5c7a1e9. Elle illustrait exactement le risque qu'elle annonce — une
    # liste recopiée à côté de la base finit par décrire une base qui n'existe plus.)
    db.query(EmailToken).filter(EmailToken.email == email).delete()
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete()
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    # Contenus du monde NEUF (trou repéré au check-up 30/07 : la purge n'effaçait que
    # l'ancien monde). Les versions d'activités suivent par CASCADE (FK).
    db.query(Activite).filter(Activite.user_id == user.id).delete()
    db.query(Seance).filter(Seance.user_id == user.id).delete()
    db.query(Sequence).filter(Sequence.user_id == user.id).delete()
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
    # `None` et non `""` : le défaut vide faisait qu'un PUT ne portant QUE l'objet écrivait
    # aussi un corps vide en base — enregistrer un champ effaçait l'autre (trouvé le 01/08).
    # Seuls les champs réellement envoyés sont écrits (voir `exclude_unset` ci-dessous).
    welcome_email_subject: str | None = None
    welcome_email_body: str | None = None


@router.get("/admin/settings")
def get_settings(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    return get_settings_dict(db)


@router.put("/admin/settings")
def save_settings(body: SettingsBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    fournis = body.dict(exclude_unset=True)
    if not fournis:
        raise HTTPException(400, "Aucun réglage fourni.")
    for key, value in fournis.items():
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


# ── Écran « Paramètres » : la table settings en LECTURE SEULE (clé / valeur) ──
# Écran de consultation : il lit la base et l'affiche, il ne modifie rien. Changer une valeur
# passe par un autre moyen. RÈGLE SUR LES SECRETS : un secret ne se règle JAMAIS depuis l'UI et
# ne vit JAMAIS en base — la base porte le NOM de la variable, le .env porte sa valeur. Un
# secret modifiable à l'écran serait un secret lisible à l'écran.
# Certaines clés ont un ÉCRAN DÉDIÉ (validé) où elles se règlent vraiment ; on les marque pour
# indiquer où (repère, pas un blocage).
#
# CETTE LISTE A MENTI DANS LES DEUX SENS, et c'est le défaut que sa propre entrée de dette
# annonçait : « ajouter un réglage à écran dédié sans toucher cette liste, et l'écran Paramètres
# ment sans que rien ne tombe » (constat du 10/08/2026). Elle promettait un écran à `rag_top_k`,
# qui n'en a aucun — ni route ni formulaire ; elle taisait `stream_silence_timeout` et les deux
# `ai_retry_*`, qui ont pourtant le leur dans Système › Génération ; et son préfixe `max_tokens_`
# désignait un écran supprimé le même jour.
#
# Elle est maintenant VÉRIFIÉE : `test_ecran_dedie_dit_vrai` la compare aux clés que les routes
# `PUT` dédiées écrivent réellement, en lisant leur code. Ajouter un réglage à écran dédié sans
# l'inscrire ici fait désormais tomber la suite.
_PARAM_ECRAN_DEDIE_EXACTS = {"ai_model", "ai_provider", "ai_temperature",
                             "stream_silence_timeout", "ai_retry_max", "ai_retry_wait_max"}
# `prompt_` : écran IA › Prompts (PUT /admin/prompts). Aucun autre préfixe — `max_tokens_` est
# mort avec son écran, et `welcome_email_` ne désigne plus aucune ligne (le mail de bienvenue
# vit dans `email_templates` depuis f3a1b2c3d4e5).
_PARAM_ECRAN_DEDIE_PREFIXES = ("prompt_",)


def _param_a_ecran_dedie(key: str) -> bool:
    return key in _PARAM_ECRAN_DEDIE_EXACTS or key.startswith(_PARAM_ECRAN_DEDIE_PREFIXES)


def _resoudre_pointeur(db: Session, key: str, value: str):
    """Une clé « pointeur » désigne une ligne d'une table catalogue (relation STRUCTURELLE, en
    code — pas une donnée métier). On renvoie (label lisible, ligne pointée complète) pour que
    l'écran montre le LIBELLÉ (jamais le code) et le contenu réel derrière le pointeur.
    Clé non pointeur, ou cible absente : (None, None)."""
    if key == "ai_provider":
        f = db.query(AiFournisseur).filter(AiFournisseur.code == value).first()
        if f:
            return f.label, {"table": "ai_fournisseurs", "code": f.code, "label": f.label,
                             "cle_env": f.cle_env, "actif": f.actif, "ordre": f.ordre}
    elif key == "ai_model":
        m = db.query(AiModele).filter(AiModele.modele == value).first()
        if m:
            return m.label, {"table": "ai_modeles", "fournisseur": m.fournisseur, "modele": m.modele,
                             "label": m.label, "recommande": m.recommande, "actif": m.actif, "ordre": m.ordre}
    return None, None


@router.get("/admin/parametres")
def get_parametres(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Liste les LIGNES RÉELLES de la table settings (clé / valeur), triées par clé. Jamais le
    merge avec les défauts code : cet écran lit la base, pas les défauts.
    `label` = libellé lisible quand la clé pointe vers un catalogue (affiché à la place du code) ;
    `pointe_vers` = la ligne catalogue complète derrière le pointeur (ou None) ;
    `ecran_dedie` = True si la clé est pilotée par un écran dédié (repère côté UI)."""
    rows = db.query(Setting).order_by(Setting.key.asc()).all()
    out = []
    for r in rows:
        label, pointe_vers = _resoudre_pointeur(db, r.key, r.value)
        out.append({
            "key": r.key, "value": r.value, "label": label,
            "ecran_dedie": _param_a_ecran_dedie(r.key),
            "pointe_vers": pointe_vers,
        })
    return out


class AiModelBody(BaseModel):
    model_config = {"protected_namespaces": ()}  # autorise un champ nommé `model` (pydantic v2)
    model: str


@router.get("/admin/ai-models")
def get_ai_models(fournisseur: str | None = Query(None), db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Modèles LLM texte d'un fournisseur, lus EN BASE (table `ai_modeles`), + modèle courant
    + modèle recommandé — alimente la combo et la validation admin. Plus AUCUNE liste en dur :
    ajouter un modèle = une ligne en base. Tri : le `recommande` d'abord, puis `ordre`.
    `fournisseur` (optionnel) = fournisseur SÉLECTIONNÉ dans la combo (pas encore enregistré) ;
    absent → fournisseur COURANT en base. `recommande` = nom du modèle marqué (affiché
    « (recommandé) »), ou None."""
    fournisseur = (fournisseur or "").strip() or _reglage_ou_none(db, "ai_provider")
    modeles = (
        db.query(AiModele)
        .filter(AiModele.fournisseur == fournisseur, AiModele.actif.is_(True))
        .order_by(AiModele.recommande.desc(), AiModele.ordre.asc())
        .all()
    )
    recommande = next((m.modele for m in modeles if m.recommande), None)
    return {
        "supported": [{"modele": m.modele, "label": m.label} for m in modeles],
        "current": _reglage_ou_none(db, "ai_model"),
        "recommande": recommande,
        # Ce qui TRAVAILLE en ce moment, en un bloc : le fournisseur, son modèle et le `max_tokens`
        # qui s'applique vraiment (celui de la fiche du modèle, sinon de son fournisseur). Les
        # écrans qui posent le repère « IA » l'affichent — devant une réponse coupée ou un refus,
        # ces trois valeurs sont exactement ce qu'on cherche, et les aller chercher ailleurs
        # demandait trois requêtes. On passe par `get_max_tokens_modele` et non `get_max_tokens` :
        # il n'y a pas d'outil nommé « default », et en inventer un ferait croire à un réglage.
        "courant": {
            "fournisseur": _reglage_ou_none(db, "ai_provider"),
            "modele": _reglage_ou_none(db, "ai_model"),
            "max_tokens": get_max_tokens_modele(db) or MAX_TOKENS_SANS_FICHE,
        },
    }


@router.put("/admin/ai-model")
def save_ai_model(body: AiModelBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Écrit le modèle LLM texte. Endpoint DÉDIÉ (le PUT /admin/settings email reste
    intact). Validation stricte : vide ou hors liste blanche → 400 (message humain pour
    la modale admin), rien n'est écrit. Sinon upsert de la clé `ai_model` + audit."""
    valeur = (body.model or "").strip()
    fournisseur = get_ai_provider(db)
    connu = (
        db.query(AiModele)
        .filter(
            AiModele.fournisseur == fournisseur,
            AiModele.modele == valeur,
            AiModele.actif.is_(True),
        )
        .first()
    )
    if not connu:
        dispo = (
            db.query(AiModele)
            .filter(AiModele.fournisseur == fournisseur, AiModele.actif.is_(True))
            .order_by(AiModele.recommande.desc(), AiModele.ordre.asc())
            .all()
        )
        raise HTTPException(
            400,
            f"Modèle inconnu ou vide pour le fournisseur « {fournisseur} ». "
            f"Modèles disponibles : {', '.join(m.modele for m in dispo) or '(aucun)'}.",
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


@router.get("/admin/ia/catalogue")
def get_ia_catalogue(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """LE CATALOGUE : tous les fournisseurs et tous leurs modèles, avec leurs caractéristiques —
    écran « IA › Fournisseurs & modèles ». À ne pas confondre avec /admin/ai-providers et
    /admin/ai-models, qui alimentent les COMBOS de l'écran Génération : ceux-là ne montrent que ce
    qui est sélectionnable, celui-ci montre tout, y compris ce qui est désactivé et les bornes.

    AUCUNE clé n'est renvoyée. Seulement le NOM de sa variable d'environnement et un booléen qui
    dit si elle est renseignée : un fournisseur raccordé mais sans clé est la panne la plus
    fréquente, et la seule chose que l'écran doit en dire, c'est « présente ou pas »."""
    fournisseurs = db.query(AiFournisseur).order_by(AiFournisseur.ordre.asc()).all()
    modeles = db.query(AiModele).order_by(AiModele.fournisseur.asc(), AiModele.ordre.asc()).all()
    # DEUX requêtes groupées plutôt qu'un comptage par ligne : avec dix fournisseurs et trente
    # modèles, la seconde façon ferait quarante requêtes pour afficher un écran.
    appels_par_fournisseur = {
        code: n for code, n in db.query(UsageLlm.fournisseur, func.count(UsageLlm.id))
                                 .group_by(UsageLlm.fournisseur).all()
    }
    appels_par_modele = {
        (f, m): n for f, m, n in db.query(UsageLlm.fournisseur, UsageLlm.modele, func.count(UsageLlm.id))
                                   .group_by(UsageLlm.fournisseur, UsageLlm.modele).all()
    }
    return {
        "fournisseurs": [
            {
                "code": f.code, "label": f.label, "actif": f.actif, "ordre": f.ordre,
                "type_api": f.type_api, "base_url": f.base_url, "max_tokens": f.max_tokens,
                "cle_env": f.cle_env,
                "cle_configuree": bool(f.cle_env and os.getenv(f.cle_env, "").strip()),
                # Nombre d'appels déjà passés chez lui. Zéro ⇒ il peut encore être supprimé ;
                # au-delà, il ne peut plus qu'être désactivé — son historique deviendrait
                # illisible. L'écran a besoin du CHIFFRE, pas d'un booléen : « a déjà répondu à
                # 412 appels » explique l'interdit, « impossible » le subit.
                "appels": appels_par_fournisseur.get(f.code, 0),
                # « gratuit » ou « payant », tel que l'administrateur l'a dit. L'écran range la
                # liste en deux zones avec ça — et rien d'autre : le tarif des modèles ne dit pas
                # si le fournisseur facture, il dit combien quand il facture.
                "tarification": f.tarification,
                # L'adresse de sa grille : l'écran en fait un lien, et n'offre le bouton
                # « Relever les tarifs » que si elle est renseignée.
                "lien_tarifs": f.lien_tarifs,
            }
            for f in fournisseurs
        ],
        "modeles": [
            {
                "fournisseur": m.fournisseur, "modele": m.modele, "label": m.label,
                "recommande": m.recommande, "actif": m.actif, "ordre": m.ordre,
                "contexte_max": m.contexte_max, "max_tokens": m.max_tokens,
                "supporte_schema": m.supporte_schema, "supporte_stream": m.supporte_stream,
                "supporte_temperature": m.supporte_temperature,
                "appels": appels_par_modele.get((m.fournisseur, m.modele), 0),
                # Le prix TEL QUE LE FOURNISSEUR L'AFFICHE, et sa devise. Vérifiable sur sa page
                # sans calcul — c'est la seule façon de contrôler une saisie.
                "cout_entree_million": float(m.cout_entree_million) if m.cout_entree_million is not None else None,
                "cout_sortie_million": float(m.cout_sortie_million) if m.cout_sortie_million is not None else None,
                "devise": m.devise,
                # Le nom sous lequel le fournisseur le PUBLIE, quand il diffère du nom
                # d'appel : c'est celui qu'on retrouve sur sa grille tarifaire.
                "nom_fournisseur": m.nom_fournisseur,
                # Et le même prix en euros, au taux du jour. Calculé ici plutôt qu'à l'écran :
                # deux écrans qui convertiraient chacun de leur côté finiraient par diverger.
                "cout_entree_eur": en_euros(m.cout_entree_million, m.devise),
                "cout_sortie_eur": en_euros(m.cout_sortie_million, m.devise),
            }
            for m in modeles
        ],
        # Ce qui est EN SERVICE, pour que l'écran marque la ligne active : le catalogue et le
        # réglage sont deux écrans différents, mais lire l'un sans savoir où pointe l'autre oblige
        # à faire l'aller-retour.
        "courant": {"fournisseur": get_ai_provider(db), "modele": get_ai_model(db)},
        # Les types d'API que le moteur sait construire : l'écran ne doit proposer que ceux-là,
        # sinon on raccorde un fournisseur que rien ne sait appeler.
        "types_api": list(_TYPES_API),
    }


# --- CRUD du catalogue IA -------------------------------------------------------------------
#
# Jusqu'ici, raccorder un fournisseur ou offrir un modèle de plus demandait une MIGRATION, donc un
# développeur. Ces cinq endpoints le rendent à l'administrateur.
#
# Ce qui reste interdit, et pourquoi :
#   - la CLÉ ne passe jamais par ici : on écrit le NOM de sa variable d'environnement, la valeur
#     reste au .env. Un secret qui transite par une API d'écran finit dans un journal.
#   - on ne supprime pas ce qui est EN SERVICE : l'application se retrouverait à appeler un
#     fournisseur qui n'existe plus, et l'erreur tomberait chez le prof, pas ici.
#   - on ne supprime pas un fournisseur qui a des modèles : ils partiraient avec, en silence.
#     L'ordre est explicite — ses modèles d'abord, lui ensuite.
# Supprimer supprime VRAIMENT (DELETE) : « désactiver » est un autre geste, il a sa case.


# Les deux seules réponses possibles à « est-ce que ce fournisseur coûte quelque chose ? ». Écrites
# ici plutôt que devinées à l'écran : la combo de l'administrateur et la validation de l'API doivent
# proposer et accepter exactement la même chose.
_TARIFICATIONS = ("gratuit", "payant")


def _verifie_tarification(valeur: str) -> None:
    """Refuse toute autre réponse. Une troisième valeur ferait disparaître le fournisseur de
    l'écran — il ne serait ni dans la zone des gratuits, ni dans celle des payants — sans qu'aucun
    message n'explique pourquoi."""
    if valeur not in _TARIFICATIONS:
        raise HTTPException(400, f"Tarification inconnue. Un fournisseur est "
                                 f"{' ou '.join(_TARIFICATIONS)}.")


class FournisseurBody(BaseModel):
    """Un fournisseur. `code` est l'identifiant technique : il ne change jamais après création
    (le réglage en service et les modèles le référencent)."""
    code: str
    label: str
    type_api: str
    base_url: str | None = None
    cle_env: str
    max_tokens: int | None = None
    actif: bool = True
    ordre: int = 0
    # « gratuit » ou « payant ». Défaut « payant » : c'est celui qui ne peut pas tromper —
    # annoncer gratuit à tort ferait ranger un service qui facture parmi ceux qui ne coûtent rien.
    tarification: str = "payant"
    # L'adresse de sa grille tarifaire publique, celle que le relevé ira lire.
    lien_tarifs: str | None = None


class ModeleBody(BaseModel):
    model_config = {"protected_namespaces": ()}
    fournisseur: str
    modele: str
    label: str
    contexte_max: int | None = None
    max_tokens: int | None = None
    supporte_schema: bool = True
    supporte_stream: bool = True
    supporte_temperature: bool = True
    recommande: bool = False
    actif: bool = True
    ordre: int = 0
    # LE PRIX, DANS LA MONNAIE DU FOURNISSEUR. Ces deux colonnes existaient déjà et servaient à
    # l'écran des statistiques, mais AUCUNE ROUTE NE LES ÉCRIVAIT : seule une migration pouvait les
    # renseigner. Or un tarif change — DeepSeek le 16/08, Anthropic le 1er septembre — et attendre
    # un développeur pour saisir deux nombres n'a pas de sens.
    #
    # `None` reste permis, et veut dire « pas encore relevé ». L'écran l'affiche comme tel plutôt
    # que d'inventer un zéro, qui se lirait comme « gratuit ».
    cout_entree_million: float | None = None
    cout_sortie_million: float | None = None
    devise: str = "USD"
    # Le nom PUBLIC du modèle chez le fournisseur, quand il n'est pas son nom d'appel. Vide = les
    # deux sont le même.
    nom_fournisseur: str | None = None


# Les deux familles d'API que le moteur sait construire. Écrites ici parce que ce sont des
# BRANCHES DE CODE (un adaptateur chacune), pas des données : offrir « mistral_natif » dans une
# combo alors qu'aucun client ne sait le parler ne raccorderait rien.
_TYPES_API = ("openai_compat", "anthropic")


def _devise_valide(devise: str) -> str:
    """La monnaie doit être une de celles que le convertisseur sait ramener en euros.

    Sans ce contrôle, une saisie libre (« chf », « francs », « €ur ») entrerait en base et le
    montant deviendrait inconvertible — donc invisible dans les comparaisons, en silence."""
    d = (devise or "").strip().upper()
    if d not in DEVISES:
        raise HTTPException(400, f"Monnaie « {devise} » inconnue. Attendu : {', '.join(DEVISES)}.")
    return d


def _a_deja_servi(db: Session, code: str, modele: str | None = None) -> int:
    """Nombre d'appels déjà passés chez ce fournisseur (ou avec ce modèle précis).

    POURQUOI ON REGARDE ÇA AVANT DE SUPPRIMER. `usage_llm` garde le CODE du fournisseur et le NOM
    du modèle pour chaque appel, mais pas leur libellé ni leur tarif — ceux-là vivent dans
    `ai_fournisseurs` et `ai_modeles`. Supprimer la ligne du catalogue ne détruit donc pas
    l'historique : elle le rend ILLISIBLE. L'écran des statistiques perd le nom, et surtout il ne
    sait plus calculer le coût, puisque le tarif appartenait au modèle effacé.

    C'est une perte silencieuse, et irréversible : personne ne s'en aperçoit avant de chercher
    combien a coûté le mois dernier."""
    q = db.query(UsageLlm).filter(UsageLlm.fournisseur == code)
    if modele is not None:
        q = q.filter(UsageLlm.modele == modele)
    return q.count()


def _verifie_pas_en_service(db: Session, code: str, modele: str | None = None) -> None:
    """Refuse de toucher à ce qui travaille.

    CE QUI TRAVAILLE A CHANGÉ DE SENS. Il n'y a plus UN fournisseur élu et des figurants : il y a
    une liste, et TOUS ceux qui y sont répondent aux professeurs. Ce garde-fou ne regardait que
    l'élu — on pouvait donc supprimer le deuxième ou le troisième de la liste pendant qu'il
    travaillait, sans un mot d'avertissement.

    LE DERNIER NE SE SUPPRIME JAMAIS. Retirer le seul fournisseur qui reste, c'est éteindre l'IA
    de toute l'application par un clic dans un écran de catalogue.

    UN PARMI PLUSIEURS, EN REVANCHE, PEUT PARTIR : la liste continue sans lui, c'est exactement ce
    pour quoi elle existe. Le message le dit, plutôt que d'interdire."""
    liste = liste_fournisseurs(db)
    codes = [v["provider"] for v in liste]
    if code not in codes:
        return
    if modele is None:
        if len(codes) <= 1:
            raise HTTPException(400, f"« {code} » est le seul fournisseur d'IA opérationnel : le "
                                     f"supprimer arrêterait toutes les générations. Raccordez-en "
                                     f"un autre avant.")
        return
    # Le modèle appelé chez ce fournisseur — celui de la liste, pas un réglage global.
    en_usage = next((v["model"] for v in liste if v["provider"] == code), None)
    if en_usage == modele and len(codes) <= 1:
        raise HTTPException(400, f"« {modele} » est le seul modèle du seul fournisseur d'IA : le "
                                 f"supprimer arrêterait toutes les générations.")


@router.post("/admin/ia/fournisseurs")
def creer_fournisseur(body: FournisseurBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Raccorde un fournisseur. Le code doit être libre et le type d'API connu du moteur."""
    code = (body.code or "").strip().lower()
    if not code or not (body.label or "").strip():
        raise HTTPException(400, "Le code et le libellé sont obligatoires.")
    if body.type_api not in _TYPES_API:
        raise HTTPException(400, f"Type d'API inconnu. Le moteur sait parler : {', '.join(_TYPES_API)}.")
    _verifie_tarification(body.tarification)
    if db.query(AiFournisseur).filter(AiFournisseur.code == code).first():
        raise HTTPException(400, f"Le fournisseur « {code} » existe déjà.")
    db.add(AiFournisseur(
        code=code, label=body.label.strip(), type_api=body.type_api,
        base_url=(body.base_url or "").strip() or None, cle_env=(body.cle_env or "").strip(),
        max_tokens=body.max_tokens, actif=body.actif, ordre=body.ordre,
        tarification=body.tarification,
        lien_tarifs=(body.lien_tarifs or "").strip() or None,
    ))
    db.commit()
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="CREATE_AI_FOURNISSEUR",
                     target_email=None, ip=request.client.host if request.client else None,
                     details=f"Fournisseur IA ajouté : {code}")
    return {"status": "ok"}


class TacheBody(BaseModel):
    """Ce que l'administrateur règle sur une tâche. Ni le code ni la fonction : seulement le QUAND,
    le SI et le À QUI."""
    actif: bool = True
    type_planif: str = "quotidien"
    heure: int | None = None
    minute: int | None = None
    intervalle_minutes: int | None = None
    destinataire: str | None = None


def _tache_vue(t: TachePlanifiee) -> dict:
    """Une tâche telle que l'écran la montre : son réglage, son texte, et son dernier passage.

    Le libellé et la description viennent du REGISTRE (le code), pas de la base : ils décrivent ce
    que la fonction fait. Les stocker permettrait de renommer « Veille des tarifs » en « Sauvegarde »
    sans que rien ne change au travail exécuté."""
    from backend.systeme.planificateur import TACHES, prochain_passage
    fiche = TACHES.get(t.code, {})
    suivant = prochain_passage(t.code)
    return {
        "code": t.code,
        "libelle": fiche.get("libelle", t.code),
        "description": fiche.get("description", ""),
        # Une ligne en base dont le code n'existe plus dans le registre : la fonction a été retirée
        # sans nettoyer la table. L'écran le dit plutôt que d'afficher une tâche qui ne fera rien.
        "orpheline": t.code not in TACHES,
        "actif": t.actif,
        "type_planif": t.type_planif,
        "heure": t.heure, "minute": t.minute,
        "intervalle_minutes": t.intervalle_minutes,
        "destinataire": t.destinataire,
        "dernier_passage": t.dernier_passage.isoformat() if t.dernier_passage else None,
        "dernier_resultat": t.dernier_resultat,
        "dernier_ok": t.dernier_ok,
        "derniere_duree_ms": t.derniere_duree_ms,
        # Le prochain passage est demandé à l'ORDONNANCEUR, pas recalculé ici : lui seul sait ce
        # qui est réellement programmé. Un calcul refait à l'écran pourrait annoncer une heure que
        # rien ne déclenchera.
        "prochain_passage": suivant.isoformat() if suivant else None,
    }


@router.get("/admin/taches")
def lister_taches(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Les travaux que l'application fait toute seule — écran « Planificateur »."""
    taches = db.query(TachePlanifiee).order_by(TachePlanifiee.code.asc()).all()
    return {"taches": [_tache_vue(t) for t in taches],
            # L'adresse qui reçoit quand une tâche n'en précise aucune. Montrée pour que le champ
            # vide ne se lise pas « personne ne sera prévenu ».
            "destinataire_par_defaut": os.getenv("ADMIN_EMAIL", "") or None}


@router.put("/admin/taches/{code}")
def regler_tache(code: str, body: TacheBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Change le réglage d'une tâche, et le rend effectif TOUT DE SUITE.

    La reprogrammation immédiate n'est pas un raffinement : sans elle, l'administrateur règle 22 h,
    voit 22 h à l'écran, et la tâche continue de partir à 6 h jusqu'au prochain redémarrage."""
    from backend.systeme.planificateur import programmer_tout
    t = db.query(TachePlanifiee).filter(TachePlanifiee.code == code).first()
    if t is None:
        raise HTTPException(404, f"Tâche « {code} » introuvable.")
    if body.type_planif not in ("quotidien", "intervalle"):
        raise HTTPException(400, "Planification inconnue : « quotidien » ou « intervalle ».")
    if body.type_planif == "quotidien":
        if not (0 <= (body.heure or 0) <= 23) or not (0 <= (body.minute or 0) <= 59):
            raise HTTPException(400, "L'heure doit être entre 0 h 00 et 23 h 59.")
    elif not (1 <= (body.intervalle_minutes or 0) <= 1440):
        raise HTTPException(400, "L'intervalle doit être compris entre 1 et 1440 minutes (24 h).")

    t.actif = body.actif
    t.type_planif = body.type_planif
    t.heure = body.heure
    t.minute = body.minute
    t.intervalle_minutes = body.intervalle_minutes
    t.destinataire = (body.destinataire or "").strip() or None
    db.commit()
    programmer_tout()
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="REGLER_TACHE",
                     target_email=None, ip=request.client.host if request.client else None,
                     details=f"Tâche planifiée modifiée : {code}")
    db.refresh(t)
    return {"status": "ok", "tache": _tache_vue(t)}


@router.post("/admin/taches/{code}/executer")
def executer_tache(code: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Lance la tâche MAINTENANT, par le même chemin que l'ordonnanceur.

    Le même chemin, c'est ce qui rend l'essai probant : ce qu'on voit ici est exactement ce qui se
    produira à 6 h 05, résultat écrit sur la ligne compris."""
    from backend.systeme.planificateur import executer
    t = db.query(TachePlanifiee).filter(TachePlanifiee.code == code).first()
    if t is None:
        raise HTTPException(404, f"Tâche « {code} » introuvable.")
    issue = executer(code)
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="EXECUTER_TACHE",
                     target_email=None, ip=request.client.host if request.client else None,
                     details=f"Tâche lancée à la main : {code}")
    db.refresh(t)
    return {"status": "ok", "ok": issue["ok"], "resultat": issue["resultat"], "tache": _tache_vue(t)}


@router.put("/admin/ia/fournisseurs/{code}")
def modifier_fournisseur(code: str, body: FournisseurBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Modifie un fournisseur. Le `code` de l'URL fait foi : renommer l'identifiant technique
    orpheliserait ses modèles et le réglage en service, donc il ne bouge pas."""
    f = db.query(AiFournisseur).filter(AiFournisseur.code == code).first()
    if f is None:
        raise HTTPException(404, f"Fournisseur « {code} » introuvable.")
    if body.type_api not in _TYPES_API:
        raise HTTPException(400, f"Type d'API inconnu. Le moteur sait parler : {', '.join(_TYPES_API)}.")
    _verifie_tarification(body.tarification)
    if not (body.label or "").strip():
        raise HTTPException(400, "Le libellé est obligatoire.")
    # Désactiver le DERNIER fournisseur opérationnel éteint l'IA de toute l'application. En
    # désactiver un parmi plusieurs est légitime : la liste continue sans lui.
    if not body.actif:
        codes = [v["provider"] for v in liste_fournisseurs(db)]
        if code in codes and len(codes) <= 1:
            raise HTTPException(400, f"« {code} » est le seul fournisseur d'IA opérationnel : le "
                                     f"désactiver arrêterait toutes les générations. Raccordez-en "
                                     f"un autre avant.")
    f.label = body.label.strip()
    f.type_api = body.type_api
    f.base_url = (body.base_url or "").strip() or None
    f.cle_env = (body.cle_env or "").strip()
    f.max_tokens = body.max_tokens
    f.actif = body.actif
    f.ordre = body.ordre
    f.tarification = body.tarification
    f.lien_tarifs = (body.lien_tarifs or "").strip() or None
    db.commit()
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="UPDATE_AI_FOURNISSEUR",
                     target_email=None, ip=request.client.host if request.client else None,
                     details=f"Fournisseur IA modifié : {code}")
    return {"status": "ok"}


@router.delete("/admin/ia/fournisseurs/{code}")
def supprimer_fournisseur(code: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Supprime un fournisseur — un vrai DELETE, et seulement s'il n'a JAMAIS servi.

    DÉCIDÉ LE 15/08/2026. Un fournisseur qui a répondu au moins une fois ne se supprime plus : il
    se DÉSACTIVE. La suppression reste ouverte pour ce qui n'a jamais servi — un fournisseur ajouté
    par erreur, ou raccordé puis jamais appelé.

    LA RAISON N'EST PAS LA PRUDENCE, C'EST L'HISTORIQUE. Les appels passés gardent le code du
    fournisseur, pas son libellé ni ses tarifs : effacer sa ligne rend le journal et les
    statistiques illisibles, et les coûts incalculables. Désactiver donne le même résultat visible
    — il n'est plus jamais appelé — sans rien perdre, et se défait d'une coche le jour où le
    problème qui l'a fait écarter est réglé."""
    f = db.query(AiFournisseur).filter(AiFournisseur.code == code).first()
    if f is None:
        raise HTTPException(404, f"Fournisseur « {code} » introuvable.")
    appels = _a_deja_servi(db, code)
    if appels:
        raise HTTPException(400, f"« {f.label} » a déjà répondu à {appels} appel(s) : le supprimer "
                                 f"rendrait ces appels illisibles dans le journal et leur coût "
                                 f"incalculable. Désactivez-le — il ne sera plus jamais appelé, et "
                                 f"vous pourrez le réactiver quand vous voudrez.")
    _verifie_pas_en_service(db, code)
    restants = db.query(AiModele).filter(AiModele.fournisseur == code).count()
    if restants:
        raise HTTPException(400, f"« {code} » a encore {restants} modèle(s). Supprimez-les d'abord : "
                                 f"les effacer avec lui, sans le dire, serait pire.")
    db.delete(f)
    db.commit()
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="DELETE_AI_FOURNISSEUR",
                     target_email=None, ip=request.client.host if request.client else None,
                     details=f"Fournisseur IA supprimé : {code}")
    return {"status": "ok"}


@router.post("/admin/ia/modeles")
def creer_modele(body: ModeleBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Ajoute un modèle à un fournisseur existant. `modele` est l'identifiant EXACT attendu par
    son API — une approximation est refusée par le fournisseur, pas par nous."""
    nom = (body.modele or "").strip()
    if not nom or not (body.label or "").strip():
        raise HTTPException(400, "L'identifiant du modèle et son libellé sont obligatoires.")
    if db.query(AiFournisseur).filter(AiFournisseur.code == body.fournisseur).first() is None:
        raise HTTPException(400, f"Fournisseur « {body.fournisseur} » inconnu.")
    if db.query(AiModele).filter(AiModele.fournisseur == body.fournisseur, AiModele.modele == nom).first():
        raise HTTPException(400, f"Le modèle « {nom} » existe déjà chez ce fournisseur.")
    if body.recommande:
        _retirer_recommande(db, body.fournisseur)
    db.add(AiModele(
        fournisseur=body.fournisseur, modele=nom, label=body.label.strip(),
        contexte_max=body.contexte_max, max_tokens=body.max_tokens,
        supporte_schema=body.supporte_schema, supporte_stream=body.supporte_stream,
        supporte_temperature=body.supporte_temperature,
        recommande=body.recommande, actif=body.actif, ordre=body.ordre,
        cout_entree_million=body.cout_entree_million,
        cout_sortie_million=body.cout_sortie_million,
        devise=_devise_valide(body.devise),
        nom_fournisseur=(body.nom_fournisseur or "").strip() or None,
    ))
    db.commit()
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="CREATE_AI_MODELE",
                     target_email=None, ip=request.client.host if request.client else None,
                     details=f"Modèle IA ajouté : {body.fournisseur}/{nom}")
    return {"status": "ok"}


def _retirer_recommande(db: Session, fournisseur: str) -> None:
    """UN SEUL modèle recommandé par fournisseur : « recommandé » veut dire « celui-là », pas
    « ceux-là ». Poser la marque la retire donc aux autres, au lieu de laisser l'écran choisir
    au hasard lequel afficher en premier."""
    (db.query(AiModele)
       .filter(AiModele.fournisseur == fournisseur, AiModele.recommande.is_(True))
       .update({"recommande": False}))


@router.put("/admin/ia/modeles/{code}/{modele:path}")
def modifier_modele(code: str, modele: str, body: ModeleBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Modifie un modèle. Le couple (fournisseur, identifiant) de l'URL fait foi : le réglage en
    service pointe dessus par son nom, le renommer le rendrait introuvable.

    `{modele:path}` : certains identifiants contiennent une barre oblique (« openai/gpt-oss-120b »)
    — sans `:path`, la route ne les attraperait jamais."""
    m = (db.query(AiModele)
           .filter(AiModele.fournisseur == code, AiModele.modele == modele).first())
    if m is None:
        raise HTTPException(404, f"Modèle « {modele} » introuvable chez « {code} ».")
    if not (body.label or "").strip():
        raise HTTPException(400, "Le libellé est obligatoire.")
    # Désactiver le modèle appelé chez ce fournisseur le retire de la liste avec lui, s'il est son
    # seul modèle actif. Interdit uniquement si c'est le dernier fournisseur debout.
    if not body.actif:
        liste = liste_fournisseurs(db)
        appele = next((v["model"] for v in liste if v["provider"] == code), None)
        if appele == modele and len(liste) <= 1:
            raise HTTPException(400, f"« {modele} » est le modèle du seul fournisseur d'IA "
                                     f"opérationnel : le désactiver arrêterait toutes les "
                                     f"générations.")
    if body.recommande and not m.recommande:
        _retirer_recommande(db, code)
    m.label = body.label.strip()
    m.contexte_max = body.contexte_max
    m.max_tokens = body.max_tokens
    m.supporte_schema = body.supporte_schema
    m.supporte_stream = body.supporte_stream
    m.supporte_temperature = body.supporte_temperature
    m.recommande = body.recommande
    m.actif = body.actif
    m.ordre = body.ordre
    m.cout_entree_million = body.cout_entree_million
    m.cout_sortie_million = body.cout_sortie_million
    m.devise = _devise_valide(body.devise)
    m.nom_fournisseur = (body.nom_fournisseur or "").strip() or None
    db.commit()
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="UPDATE_AI_MODELE",
                     target_email=None, ip=request.client.host if request.client else None,
                     details=f"Modèle IA modifié : {code}/{modele}")
    return {"status": "ok"}


@router.post("/admin/ia/fournisseurs/{code}/relever-tarifs")
def relever_tarifs(code: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Va lire la grille tarifaire du fournisseur et remplit le prix de ses modèles.

    CE QUE ÇA REMPLACE : la saisie à la main, modèle par modèle, en gardant la page du fournisseur
    ouverte dans un autre onglet. Long, et surtout périssable — un prix changé chez lui restait
    faux chez nous jusqu'à ce que quelqu'un s'en aperçoive.

    AUCUNE IA N'EST APPELÉE. Une grille tarifaire est un tableau : un nom, deux montants. Une
    expression régulière le lit sans se tromper et sans rien coûter ; un modèle de langage
    coûterait de l'argent et pourrait inventer un chiffre.

    ON N'ÉCRIT QUE CE QU'ON A LU. Un modèle dont le nom n'est pas sur la page, ou qui n'est suivi
    que d'un seul montant, est laissé tel quel et rendu dans `ignores` avec sa raison. Un tarif
    absent se voit à l'écran (« non relevé ») ; un tarif faux ne se voit pas.

    LA DEVISE VIENT DE LA PAGE quand elle y est écrite (Infomaniak annonce en CHF). Sinon celle du
    modèle est conservée : mieux vaut garder ce qu'on savait que d'affirmer des dollars."""
    f = db.query(AiFournisseur).filter(AiFournisseur.code == code).first()
    if f is None:
        raise HTTPException(404, f"Fournisseur « {code} » introuvable.")
    if not (f.lien_tarifs or "").strip():
        raise HTTPException(400, f"« {f.label} » n'a pas d'adresse de page tarifaire. Renseignez "
                                 f"« lien_tarifs » sur sa fiche, puis relancez le relevé.")

    try:
        page = lire_page(f.lien_tarifs)
    except ValueError as e:
        raise HTTPException(400, str(e))

    modeles = db.query(AiModele).filter(AiModele.fournisseur == code).all()
    # On cherche par le nom PUBLIC quand il existe — chez Infomaniak la grille dit
    # « mistralai/Ministral-3-14B-Instruct-2512 » là où l'appel dit « mistral3 ». À défaut, le nom
    # d'appel suffit : chez Anthropic et Groq, les deux sont le même.
    cherches = {m.modele: (m.nom_fournisseur or m.modele) for m in modeles}
    releves = relever(page, list(set(cherches.values())))

    faits, ignores = [], []
    for m in modeles:
        trouve = releves.get(cherches[m.modele])
        if not trouve:
            ignores.append({"modele": m.modele, "cherche": cherches[m.modele],
                            "raison": "introuvable sur la page"})
            continue
        avant = (m.cout_entree_million, m.cout_sortie_million, m.devise)
        m.cout_entree_million = trouve["entree"]
        m.cout_sortie_million = trouve["sortie"]
        if trouve["devise"]:
            m.devise = trouve["devise"]
        # « inchangé » n'est pas « échoué » : le dire évite de croire que le relevé n'a pas marché
        # parce que rien ne bouge à l'écran.
        change = (float(avant[0]) if avant[0] is not None else None,
                  float(avant[1]) if avant[1] is not None else None,
                  avant[2]) != (trouve["entree"], trouve["sortie"], m.devise)
        faits.append({"modele": m.modele, "entree": trouve["entree"], "sortie": trouve["sortie"],
                      "devise": m.devise, "change": change})
    db.commit()
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="RELEVE_TARIFS_IA",
                     target_email=None, ip=request.client.host if request.client else None,
                     details=f"Tarifs relevés chez {code} : {len(faits)} modèle(s), {len(ignores)} ignoré(s)")
    return {"status": "ok", "releves": faits, "ignores": ignores, "source": f.lien_tarifs}


@router.delete("/admin/ia/modeles/{code}/{modele:path}")
def supprimer_modele(code: str, modele: str, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Supprime un modèle — un vrai DELETE, et seulement s'il n'a JAMAIS servi.

    Même règle que pour le fournisseur, et pour la même raison : le tarif appartient au modèle.
    L'effacer après qu'il a produit des tokens rend leur coût incalculable pour toujours."""
    m = (db.query(AiModele)
           .filter(AiModele.fournisseur == code, AiModele.modele == modele).first())
    if m is None:
        raise HTTPException(404, f"Modèle « {modele} » introuvable chez « {code} ».")
    appels = _a_deja_servi(db, code, modele)
    if appels:
        raise HTTPException(400, f"« {modele} » a déjà produit {appels} réponse(s) : le supprimer "
                                 f"rendrait leur coût incalculable. Désactivez-le plutôt — il ne "
                                 f"sera plus proposé, et rien n'est perdu.")
    _verifie_pas_en_service(db, code, modele)
    db.delete(m)
    db.commit()
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="DELETE_AI_MODELE",
                     target_email=None, ip=request.client.host if request.client else None,
                     details=f"Modèle IA supprimé : {code}/{modele}")
    return {"status": "ok"}


class AiProviderBody(BaseModel):
    provider: str


@router.get("/admin/ai-providers")
def get_ai_providers(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Fournisseurs LLM offerts + fournisseur courant — alimente la combo admin et sa
    validation. Lus EN BASE (table `ai_fournisseurs`), plus AUCUNE liste en dur. Miroir de
    GET /admin/ai-models. On n'expose comme sélectionnables QUE les fournisseurs `actif`
    (opérationnels) ; les autres apparaissent « pas encore disponible » (grisés).
    `all` = tous les fournisseurs connus (lignes de la table) + drapeau `available` = actif."""
    fournisseurs = db.query(AiFournisseur).order_by(AiFournisseur.ordre.asc()).all()
    return {
        "supported": [f.code for f in fournisseurs if f.actif],
        "current": _reglage_ou_none(db, "ai_provider"),
        "all": [
            {"name": f.code, "label": f.label, "available": f.actif}
            for f in fournisseurs
        ],
    }


@router.put("/admin/ai-provider")
def save_ai_provider(body: AiProviderBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Écrit le fournisseur LLM texte. Endpoint DÉDIÉ (PUT email et PUT ai-model restent intacts). Validation stricte contre la BASE (table `ai_fournisseurs`, fournisseurs
    `actif`) : vide ou hors liste → 400 (message humain pour la modale admin), rien n'est écrit.
    Sinon upsert de la clé `ai_provider` + audit."""
    valeur = (body.provider or "").strip()
    actifs = [f.code for f in db.query(AiFournisseur).filter(AiFournisseur.actif.is_(True)).order_by(AiFournisseur.ordre.asc()).all()]
    if valeur not in actifs:
        raise HTTPException(
            400,
            f"Fournisseur inconnu ou vide. Choisissez un fournisseur pris en charge : "
            f"{', '.join(actifs) or '(aucun)'}.",
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


# L'ÉCRAN DES LONGUEURS N'EXISTE PLUS (10/08/2026). Il y avait ici un `GET`/`PUT
# /admin/max-tokens` : un défaut global plus une surcharge par outil, écrits dans `settings`.
# Le moteur ne les lisait DÉJÀ plus — `get_max_tokens()` rend le `max_tokens` de la fiche du
# modèle (sinon du fournisseur, sinon MAX_TOKENS_SANS_FICHE) — et l'onglet avait été retiré du
# front. Restaient deux routes qui écrivaient des lignes que personne ne relisait : un admin
# pouvait y régler un couperet sans effet, et croire l'avoir réglé. La longueur se voit et se
# règle là où elle est vraie : IA › Fournisseurs & modèles.


class TemperatureBody(BaseModel):
    temperature: float | None = None  # None / absente = défaut du fournisseur (non réglée)


@router.get("/admin/temperature")
def get_temperature_settings(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Température courante (float, ou None = défaut fournisseur) + bornes — alimente le
    formulaire admin et sa validation.

    `supportee` dit si le MODÈLE EN SERVICE accepte ce paramètre. L'écran s'en sert pour le dire au
    lieu de laisser régler une valeur qui ne partira pas : jusqu'ici l'admin saisissait une
    température sur un Claude, validait, et elle était jetée en silence par le moteur. La valeur
    reste lisible et modifiable — elle redeviendra active au prochain modèle qui l'accepte."""
    raw = get_settings_dict(db).get("ai_temperature", "")
    val = None
    if raw not in (None, ""):
        try:
            val = float(raw)
        except (TypeError, ValueError):
            val = None
    return {
        "temperature": val,
        "bounds": {"min": TEMPERATURE_MIN, "max": TEMPERATURE_MAX},
        "supportee": modele_supporte_temperature(db),
        "modele": get_ai_model(db),
    }


@router.put("/admin/temperature")
def save_temperature(body: TemperatureBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Écrit la température globale. Endpoint DÉDIÉ (les autres PUT restent intacts).
    `temperature` absente/None -> on revient au défaut du fournisseur (clé vidée). Sinon
    validation stricte dans [MIN, MAX], sinon 400 + message humain pour la modale admin, rien
    écrit."""
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


class StreamTimeoutBody(BaseModel):
    timeout: int


@router.get("/admin/stream-timeout")
def get_stream_timeout_settings(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Coupure de silence courante (secondes) + bornes — alimente le formulaire admin et sa
    validation. Miroir de GET /admin/temperature."""
    return {
        "timeout": get_stream_silence_timeout(db),
        "bounds": {"min": STREAM_SILENCE_MIN, "max": STREAM_SILENCE_MAX},
    }


@router.put("/admin/stream-timeout")
def save_stream_timeout(body: StreamTimeoutBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Écrit la coupure de silence du flux (secondes). Endpoint DÉDIÉ. Validation stricte : entier
    dans [MIN, MAX], sinon 400 + message humain pour la modale admin, rien n'est écrit."""
    if not (STREAM_SILENCE_MIN <= body.timeout <= STREAM_SILENCE_MAX):
        raise HTTPException(
            400,
            f"Valeur hors limites : {body.timeout}. Le délai doit être un nombre entier de "
            f"secondes entre {STREAM_SILENCE_MIN} et {STREAM_SILENCE_MAX}.",
        )
    row = db.query(Setting).filter(Setting.key == "stream_silence_timeout").first()
    if row:
        row.value = str(body.timeout)
    else:
        db.add(Setting(key="stream_silence_timeout", value=str(body.timeout)))
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="UPDATE_STREAM_TIMEOUT",
        target_email=None,
        ip=request.client.host if request.client else None,
        details=f"Coupure de silence du flux mise à jour : {body.timeout} s",
    )
    return {"status": "ok"}


class RetryBody(BaseModel):
    retry_max: int
    retry_wait_max: int


@router.get("/admin/retry")
def get_retry_settings(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Résilience 429 courante (nb de re-tentatives + plafond d'attente par tentative) + bornes —
    alimente le formulaire admin et sa validation. Même moule que GET /admin/stream-timeout."""
    return {
        "retry_max": get_retry_max(db),
        "retry_wait_max": get_retry_wait_max(db),
        "bounds": {
            "retry_max": {"min": RETRY_MAX_MIN, "max": RETRY_MAX_MAX},
            "retry_wait_max": {"min": RETRY_WAIT_MIN, "max": RETRY_WAIT_MAX},
        },
    }


@router.put("/admin/retry")
def save_retry(body: RetryBody, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Écrit la résilience 429 (nb de re-tentatives + plafond d'attente par tentative, en secondes).
    Endpoint DÉDIÉ. Validation stricte : deux entiers dans leurs bornes, sinon 400 + message humain
    pour la modale admin, rien n'est écrit."""
    if not (RETRY_MAX_MIN <= body.retry_max <= RETRY_MAX_MAX):
        raise HTTPException(
            400,
            f"Nombre de re-tentatives hors limites : {body.retry_max}. Il doit être un nombre entier "
            f"entre {RETRY_MAX_MIN} et {RETRY_MAX_MAX} (0 = aucune re-tentative).",
        )
    if not (RETRY_WAIT_MIN <= body.retry_wait_max <= RETRY_WAIT_MAX):
        raise HTTPException(
            400,
            f"Plafond d'attente hors limites : {body.retry_wait_max}. Il doit être un nombre entier "
            f"de secondes entre {RETRY_WAIT_MIN} et {RETRY_WAIT_MAX}.",
        )
    for key, val in (("ai_retry_max", body.retry_max), ("ai_retry_wait_max", body.retry_wait_max)):
        row = db.query(Setting).filter(Setting.key == key).first()
        if row:
            row.value = str(val)
        else:
            db.add(Setting(key=key, value=str(val)))
    db.commit()
    log_admin_action(
        db=db,
        admin_email=_get_admin_email(request),
        action="UPDATE_RETRY",
        target_email=None,
        ip=request.client.host if request.client else None,
        details=f"Résilience 429 mise à jour : {body.retry_max} re-tentative(s), plafond {body.retry_wait_max} s",
    )
    return {"status": "ok"}


class PromptBody(BaseModel):
    key: str
    text: str


@router.get("/admin/prompts")
def get_prompts_settings(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Liste des prompts d'outils administrables : libellé, repères obligatoires, texte EN BASE,
    et le texte de référence du registre (pour « revenir au défaut »). Les activités (catalogue)
    ne sont PAS ici.

    CET ÉCRAN EST LE DIAGNOSTIC. Depuis que `get_prompt` n'a plus de repli, un prompt absent de
    la base fait tomber l'outil qui l'utilise : il faut donc pouvoir voir LEQUEL manque. D'où
    `en_base` par ligne — et surtout, cet endpoint ne lève JAMAIS sur une clé absente. S'il
    tombait en bloc, on perdrait l'écran par lequel on répare, exactement quand on en a besoin.
    C'est la raison pour laquelle il lit `settings` directement au lieu d'appeler `get_prompt`."""
    s = get_settings_dict(db)
    out = []
    for key, meta in PROMPTS.items():
        en_base = s.get(f"prompt_{key}", "")
        present = bool(en_base and en_base.strip())
        out.append({
            "key": key,
            "label": meta["label"],
            # Le nom COURT de l'onglet quand la fonctionnalité porte plusieurs textes. Vide =
            # l'écran retombe sur le libellé complet.
            "onglet": meta.get("onglet", ""),
            # À quoi sert ce texte, en une phrase — vide si le registre n'en donne pas.
            "role": meta.get("role", ""),
            "placeholders": meta["placeholders"],
            # L'onglet de l'écran admin « Prompts » : « fonctionnalites »,
            # « referentiels_communs » ou « autres » (registre, pas de table).
            "categorie": meta["categorie"],
            # Sous quelle FONCTIONNALITÉ la ligne se range dans l'onglet — la clé d'une entrée de
            # `FONCTIONNALITES`, servie juste dessous. Vide hors de cet onglet.
            "fonctionnalite": meta.get("fonctionnalite", ""),
            # `current` = ce que le serveur utilisera VRAIMENT. Absent en base = plus rien à
            # utiliser : on montre le texte de référence, mais `en_base` dit la vérité.
            "current": en_base if present else meta["default"],
            "default": meta["default"],
            "is_default": not present or en_base == meta["default"],
            "en_base": present,
        })
    # Les fonctionnalités elles-mêmes, dans leur ordre d'affichage : l'écran ne les connaît pas,
    # il les reçoit. Une fonctionnalité ajoutée au registre apparaît sans toucher au front.
    fonctionnalites = [
        {"cle": f.code, "label": f.label, "aide": f.aide}
        for f in catalogue(db, PromptFonctionnalite, "fonctionnalités des prompts")
    ]
    return {"prompts": out, "fonctionnalites": fonctionnalites,
            "manquants": [p["key"] for p in out if not p["en_base"]]}


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
    """Retour au défaut d'un outil : RÉÉCRIT en base le texte de référence (`llm_prompts.PROMPTS`).

    Cette route SUPPRIMAIT la ligne, en s'appuyant sur un repli code de `get_prompt` qui
    n'existe plus depuis l'étape 9 lot C : `get_prompt` lève désormais un 500 quand la ligne
    manque. Le bouton « revenir au prompt par défaut » RENDAIT donc l'outil inutilisable au
    lieu de le réparer (trouvé le 01/08). La base reste la source unique : revenir au défaut,
    c'est y RÉÉCRIRE la référence, jamais retirer la ligne. Idempotent."""
    if key not in PROMPTS:
        raise HTTPException(400, "Prompt inconnu.")
    defaut = PROMPTS[key]["default"]
    row = db.query(Setting).filter(Setting.key == f"prompt_{key}").first()
    if row is None or row.value != defaut:
        if row:
            row.value = defaut
        else:
            db.add(Setting(key=f"prompt_{key}", value=defaut))
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
    from backend.securite import comptes
    token = comptes.generate_email_token(db, email, "reset_password")
    try:
        comptes.send_reset_email(email, token)
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
    from backend.securite import comptes
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
            comptes.send_custom_email(email, user.prenom, body.subject, body.body)
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
    from backend.securite import comptes
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    try:
        comptes.send_custom_email(email, user.prenom, body.subject, body.body)
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
    from backend.securite import comptes
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
        comptes.send_custom_email(to, None, t.objet, t.corps)
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
    from backend.securite import comptes
    admin_email = os.getenv("SMTP_USERNAME", "")
    if not admin_email:
        raise HTTPException(500, "SMTP_USERNAME non configure.")
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(404, "Modele introuvable.")
    try:
        comptes.send_custom_email(admin_email, "Admin", t.objet, t.corps)
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
    now = maintenant_utc()
    user_ids = {s.user_id for s in sessions if s.user_id is not None}
    email_par_id = dict(
        db.query(User.id, User.email).filter(User.id.in_(user_ids)).all()
    ) if user_ids else {}

    # LE LIEU SE RÉSOUT ICI, ET UNE SEULE FOIS PAR SESSION. Pas à la connexion : aucune page de
    # professeur n'attend après un service extérieur. C'est l'administrateur qui ouvre cet écran
    # qui paie l'attente, et seulement pour les sessions dont le lieu manque encore.
    from backend.systeme.localisation_ip import assurer_localisations
    assurer_localisations(db, sessions)

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
            "lieu":      s.localisation or "—",
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
    from backend.securite.comptes import send_custom_email
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
    today = maintenant_utc().date()
    threshold_online = maintenant_utc() - timedelta(seconds=90)
    return {
        "total_profs":        db.query(User).filter(User.is_verified == True).count(),
        "connexions_today":   db.query(ConnexionLog).filter(
                                  ConnexionLog.action == "login",
                                  func.date(ConnexionLog.created_at) == today
                              ).count(),
        # Le statut initial est LU EN BASE (ordre minimal), jamais écrit ici : voir
        # code_statut_initial(). Le `default="nouveau"` de la colonne, lui, reste — une valeur
        # par défaut SQL doit être littérale, et ce n'est pas elle qui posait problème.
        "feedbacks_nouveaux": db.query(Feedback).filter(
                                  Feedback.statut == code_statut_initial(db)
                              ).count(),
        "alertes_nonlues":    db.query(AdminAlert).filter(AdminAlert.is_read == False).count(),
        "sessions_online":    db.query(UserSession).filter(
                                  UserSession.is_active == True,
                                  UserSession.last_seen >= threshold_online
                              ).count(),
    }


@router.get("/admin/stats/logins")
def stats_logins(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    since = maintenant_utc() - timedelta(days=30)
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
def db_size(request: Request, _: None = Depends(_require_admin)):
    # Le schéma de la requête, pas la base : les cinq démonstrations partagent la leur, et sans
    # cette précision chacune se verrait attribuer le total des cinq.
    return {"size_mb": get_db_size_mb(schema_de(request))}


@router.get("/admin/alerts")
def get_alerts(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Les alertes, non lues d'abord. Chacune dit désormais DE QUI elle parle, ce qu'elle a
    mesuré et où aller vérifier — au lieu de renvoyer le lecteur chercher lui-même."""
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
            "code":       r.code or "",
            "title":      r.title,
            "message":    r.message,
            # De qui parle l'alerte. Vide pour les alertes de machine — processeur, disque : elles
            # ne parlent de personne, et inventer un professeur serait pire que la case vide.
            "prof":       r.user_email or "",
            "user_id":    r.user_id,
            # Les faits mesurés, tels quels : l'écran les affiche sans avoir à relire la phrase.
            "donnees":    r.donnees or None,
            "lien":       r.lien or "",
            "is_read":    r.is_read,
            "read_by":    r.read_by or "",
            "date":       r.created_at.strftime("%d/%m/%Y %H:%M"),
        }
        for r in rows
    ]


@router.get("/admin/alerts/statistiques")
def get_alerts_statistiques(jours: int = 30, db: Session = Depends(get_db),
                            _: None = Depends(_require_admin)):
    """Combien d'alertes, de quel genre, sur la période — et les comptes les plus signalés.

    C'EST CE QUE `code` A RENDU POSSIBLE. Tant que le genre d'une alerte n'existait que dans son
    titre, tout comptage passait par une comparaison de phrases : un titre reformulé cassait la
    série, et rien ne se suivait dans le temps."""
    depuis = maintenant_utc() - timedelta(days=max(1, min(365, jours)))
    par_code = (db.query(AdminAlert.code, AdminAlert.level, func.count().label("n"))
                .filter(AdminAlert.created_at >= depuis)
                .group_by(AdminAlert.code, AdminAlert.level)
                .order_by(func.count().desc()).all())
    par_prof = (db.query(AdminAlert.user_email, func.count().label("n"))
                .filter(AdminAlert.created_at >= depuis, AdminAlert.user_email.isnot(None))
                .group_by(AdminAlert.user_email)
                .order_by(func.count().desc()).limit(10).all())
    return {
        "jours": jours,
        "total": sum(n for _, _, n in par_code),
        "non_lues": db.query(AdminAlert).filter(AdminAlert.created_at >= depuis,
                                                AdminAlert.is_read == False).count(),  # noqa: E712
        "par_genre": [{"code": c or "(sans genre)", "niveau": niv, "nombre": n}
                      for c, niv, n in par_code],
        "profs_les_plus_signales": [{"prof": e, "nombre": n} for e, n in par_prof],
    }


# LES SEUILS DE SURVEILLANCE, RÉGLABLES DEPUIS L'ÉCRAN — ce que le menu promettait déjà.
#
# LE DÉFAUT CORRIGÉ. Les sept seuils vivaient en base, donc « sans développeur » — sauf qu'aucun
# écran ne les modifiait : l'écran « Paramètres » est en lecture seule, et l'aide du menu affirmait
# pourtant que les seuils se règlent dans Supervision → Alertes. Une valeur en base que personne ne
# peut atteindre n'est pas mieux qu'une valeur écrite dans le code — elle est pire, parce qu'on la
# croit modifiable.
#
# LES BORNES NE SONT PAS DU CONFORT. Un seuil de 0 appareil alerterait sur chaque connexion et
# noierait l'écran ; une fenêtre de 0 minute ne verrait jamais deux sessions ensemble. Un réglage
# impossible est refusé plutôt qu'écrit puis silencieusement ignoré par la surveillance.
_SEUILS_ALERTES = {
    "alerte_cpu_pct":      ("Processeur — seuil d'alerte", "%", 1, 100),
    "alerte_disque_pct":   ("Disque — seuil d'alerte", "%", 1, 100),
    "alerte_tentatives_1h": ("Tentatives de connexion échouées en 1 h", "tentatives", 1, 10000),
    "alerte_anti_flood_h": ("Ne pas répéter la même alerte pendant", "heures", 1, 168),
    "alerte_postes_max":   ("Appareils simultanés tolérés par compte", "appareils", 1, 100),
    "alerte_distance_km":  ("Distance entre deux connexions simultanées", "km", 1, 20000),
    "alerte_fenetre_min":  ("Ce que « en même temps » veut dire", "minutes", 1, 1440),
}


@router.get("/admin/alerts/seuils")
def get_seuils_alertes(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Les seuils tels qu'ils sont EN BASE — pas les valeurs de départ du code."""
    valeurs = {r.key: r.value for r in db.query(Setting)
               .filter(Setting.key.in_(_SEUILS_ALERTES.keys())).all()}
    return {"seuils": [
        {"cle": cle, "libelle": libelle, "unite": unite, "min": mini, "max": maxi,
         "valeur": valeurs.get(cle)}
        for cle, (libelle, unite, mini, maxi) in _SEUILS_ALERTES.items()
    ]}


class SeuilsAlertesBody(BaseModel):
    seuils: dict[str, float]


@router.put("/admin/alerts/seuils")
def put_seuils_alertes(body: SeuilsAlertesBody, request: Request,
                       db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Écrit les seuils. Un seul hors bornes fait tout refuser — on n'enregistre pas à moitié."""
    if not body.seuils:
        raise HTTPException(400, "Aucun seuil fourni.")
    for cle, valeur in body.seuils.items():
        if cle not in _SEUILS_ALERTES:
            raise HTTPException(400, f"Réglage inconnu : {cle}")
        libelle, unite, mini, maxi = _SEUILS_ALERTES[cle]
        if not (mini <= valeur <= maxi):
            raise HTTPException(400, f"« {libelle} » doit être entre {mini} et {maxi} {unite}.")

    for cle, valeur in body.seuils.items():
        # Un entier s'écrit sans décimale : « 4 » et non « 4.0 » — cette valeur se relit à l'écran.
        texte = str(int(valeur)) if float(valeur).is_integer() else str(valeur)
        row = db.query(Setting).filter(Setting.key == cle).first()
        if row:
            row.value = texte
        else:
            db.add(Setting(key=cle, value=texte))
    db.commit()
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="SEUILS_ALERTES",
                     ip=request.client.host if request.client else None,
                     details=", ".join(f"{c}={v:g}" for c, v in body.seuils.items()))
    return {"status": "ok"}


@router.post("/admin/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int, request: Request, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    alert = db.query(AdminAlert).filter(AdminAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alerte introuvable.")
    alert.is_read  = True
    alert.read_by  = _get_admin_email(request)
    alert.read_at  = maintenant_utc()
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
    # `to_char` et non `strftime` : strftime est une fonction SQLITE. Elle est restée là
    # après la bascule vers PostgreSQL, où elle n'existe pas — la route répondait 500 à
    # chaque appel de l'écran Serveur, et aucun test ne la couvrait (corrigé le 01/08).
    heure = func.to_char(ConnexionLog.created_at, 'HH24')
    rows = (
        db.query(heure.label("hour"), func.count(ConnexionLog.id).label("count"))
        .filter(ConnexionLog.action == "login")
        .group_by(heure)
        .order_by(heure)
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
        db.query(ConnexionLog, User.subject_id)
        .outerjoin(User, User.id == ConnexionLog.user_id)
        .order_by(ConnexionLog.created_at.desc())
        .limit(200)
        .all()
    )
    noms = {sid: matiere_nom_de_id(db, sid) for sid in {s for _, s in rows if s}}
    return [
        {
            "id":      l.id,
            "email":   l.email,
            "subject": noms.get(subject_id) or "—",
            "action":  l.action,
            "ip":      l.ip,
            "date":    l.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        for l, subject_id in rows
    ]


@router.get("/admin/stats/analytique")
def get_stats_analytique(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Analytique par prof, comptée sur le monde NEUF (table activites — décision 30/07)."""
    rows = (
        db.query(
            User.email,
            User.prenom,
            User.nom,
            User.subject_id,
            User.niveau_id.label("niveau_profil_id"),
            Activite.matiere.label("activite_matiere"),
            Activite.niveau.label("activite_niveau"),
            Activite.activite_type_id,
            Activite.activite_label,
            func.count(Activite.id).label("nb"),
        )
        .join(User, User.id == Activite.user_id, isouter=True)
        # `User.id` DOIT figurer ici. Le SELECT prend cinq colonnes de `users` (email, prénom,
        # nom, subject_id, niveau_id) : sans la clé primaire dans le GROUP BY, PostgreSQL refuse
        # la requête en bloc — « column users.email must appear in the GROUP BY clause ». L'écran
        # Analytique > Activités rendait donc une 500 à chaque ouverture, quel que soit le contenu
        # de la base (constaté le 10/08/2026 en écrivant le test qui manquait à cette route).
        # Avec `User.id`, la dépendance fonctionnelle rend les quatre autres licites, et la
        # granularité ne bouge pas : `Activite.user_id` groupait déjà par prof.
        .group_by(
            User.id,
            Activite.user_id,
            Activite.matiere,
            Activite.niveau,
            Activite.activite_type_id,
            Activite.activite_label,
        )
        .all()
    )

    _mat_cache: dict = {}
    def _mat(mid):
        if mid not in _mat_cache:
            _mat_cache[mid] = matiere_nom_de_id(db, mid)
        return _mat_cache[mid]
    _niv_cache: dict = {}
    def _niv(nid):
        if nid not in _niv_cache:
            _niv_cache[nid] = niveau_nom_de_id(db, nid)
        return _niv_cache[nid]

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
                "subject": _mat(row.subject_id) or "",
                "niveau_profil": _niv(row.niveau_profil_id) or "",
                "total": 0,
                "par_matiere": {},
            }
        prof = profs_dict[email]
        prof["total"] += row.nb

        mat = row.activite_matiere or _mat(row.subject_id) or "—"
        niv = row.activite_niveau or "—"
        typ = row.activite_label or "—"

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


# ---------------------------------------------------------------------------
# Bases de démonstration — PILOTAGE (table `demos`), jamais leur contenu
# ---------------------------------------------------------------------------
# Une démonstration vit dans une base PostgreSQL À PART (ciela_demo, cielb_demo…). Ces routes ne
# l'ouvrent JAMAIS : elles lisent et écrivent la fiche qui la décrit, dans la base réelle. C'est
# pourquoi les compteurs sont saisis et non calculés — les recompter voudrait dire se connecter
# ailleurs, ce que ce moteur-ci ne fait pas.

# LE STATUT A ÉTÉ SUPPRIMÉ (16/08/2026). Cinq mots — À faire, En cours, Fabriquée, Testée,
# Validée — dont deux seulement agissaient, et au même endroit : ouvrir l'entrée « Démonstration »
# du menu prof. Or une démonstration qui n'est pas prête n'a pas d'adresse, et cette absence
# suffisait déjà à la tenir fermée. Cinq mots à comprendre pour un contrôle qui existait en double.
# La règle tient maintenant en une phrase : une démonstration est visitable dès qu'elle a une adresse.


class DemoIn(BaseModel):
    referentiel_id: int
    nom_base: str
    url: str | None = None
    nb_activites: int = 0
    nb_sequences: int = 0
    nb_seances: int = 0
    date_generation: datetime | None = None
    date_dernier_test: datetime | None = None
    defauts_connus: str | None = None
    notes: str | None = None


def _demo_en_dict(d: Demo, cycle_nom: str | None, niveau_nom: str | None) -> dict:
    return {
        "id": d.id,
        "referentiel_id": d.referentiel_id,
        "cycle": cycle_nom,
        "niveau": niveau_nom,
        "nom_base": d.nom_base,
        "url": d.url,
        "nb_activites": d.nb_activites,
        "nb_sequences": d.nb_sequences,
        "nb_seances": d.nb_seances,
        "date_generation": d.date_generation.isoformat() if d.date_generation else None,
        "date_dernier_test": d.date_dernier_test.isoformat() if d.date_dernier_test else None,
        "defauts_connus": d.defauts_connus,
        "notes": d.notes,
    }


def _valider_demo(body: DemoIn, db: Session) -> tuple[str, str | None]:
    """Refuse tôt ce que la base refuserait tard, avec un message lisible. Rend (nom_base, url)
    nettoyés. Le nom de base est contraint à la convention `<option>_demo` : minuscules, chiffres
    et soulignés. Un tiret obligerait à écrire le nom entre guillemets dans toute commande SQL."""
    nom = (body.nom_base or "").strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9_]*", nom):
        raise HTTPException(400, "Nom de base invalide : minuscules, chiffres et soulignés, "
                                 "commençant par une lettre (ex. ciela_demo).")
    if not db.get(Referentiel, body.referentiel_id):
        raise HTTPException(404, "Référentiel introuvable.")
    if min(body.nb_activites, body.nb_sequences, body.nb_seances) < 0:
        raise HTTPException(400, "Les compteurs ne peuvent pas être négatifs.")
    # L'adresse est ce que le navigateur du prof va ouvrir : on refuse tout ce qui n'est pas une
    # adresse http(s), et on retire la barre finale pour ne pas fabriquer « …//demo » plus loin.
    url = (body.url or "").strip().rstrip("/") or None
    if url and not re.fullmatch(r"https?://[^\s]+", url):
        raise HTTPException(400, "Adresse invalide : attendue sous la forme https://demo.exemple.fr")
    return nom, url


@router.get("/admin/demos")
def admin_demos_liste(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Les démonstrations déclarées, et les référentiels qui n'en ont pas encore.

    Les deux voyagent ensemble parce que l'écran a besoin des deux : la liste à afficher, et le
    choix à proposer quand on ajoute. `uq_demos_referentiel` interdit un second enregistrement
    pour le même référentiel — autant ne pas le proposer plutôt que de laisser l'admin buter."""
    lignes = (
        db.query(Demo, Cycle.nom, Niveau.nom)
        .join(Referentiel, Referentiel.id == Demo.referentiel_id)
        .join(Niveau, Niveau.id == Referentiel.niveau_id)
        .outerjoin(Cycle, Cycle.id == Niveau.cycle_id)
        .order_by(Cycle.nom, Niveau.nom)
        .all()
    )
    pris = {d.referentiel_id for d, _c, _n in lignes}
    libres = (
        db.query(Referentiel.id, Cycle.nom, Niveau.nom)
        .join(Niveau, Niveau.id == Referentiel.niveau_id)
        .outerjoin(Cycle, Cycle.id == Niveau.cycle_id)
        .order_by(Cycle.nom, Niveau.nom)
        .all()
    )
    return {
        "demos": [_demo_en_dict(d, c, n) for d, c, n in lignes],
        "referentiels_libres": [
            {"id": rid, "cycle": c, "niveau": n} for rid, c, n in libres if rid not in pris
        ],
    }


@router.get("/admin/demos/proposition")
def admin_demos_proposition(referentiel_id: int = Query(...),
                            db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Ce que l'écran peut renseigner tout seul quand l'admin choisit un référentiel.

    POURQUOI CETTE ROUTE EXISTE. La fiche se remplissait entièrement à la main, y compris les
    trois compteurs — et le commentaire d'en-tête de ce bloc l'expliquait par le fait que ce
    moteur n'ouvre pas les bases de démonstration. C'était un choix, pas une limite : le serveur
    PostgreSQL est le même conteneur, le même utilisateur, et seul le nom de base change. On
    ouvre donc une connexion le temps de trois `count(*)`, et on la referme.

    ELLE NE DÉCIDE RIEN : elle PROPOSE. Tout ce qu'elle renvoie reste modifiable à l'écran, et
    rien n'est enregistré ici. Si la base n'existe pas encore — cas normal, l'admin déclare la
    fiche AVANT que le dev fabrique — les compteurs valent zéro et `base_trouvee` est faux.

    LE NOM DE BASE NE SE DÉDUIT PAS DU RÉFÉRENTIEL : un nom court comme `ciela_demo` ne se
    calcule pas depuis l'intitulé complet du niveau, ni `ergo_demo` depuis « licence_ergotherapie ». On regarde donc ce
    qui EXISTE sur le serveur : les bases en `_demo` qu'aucune fiche ne revendique. S'il n'en
    reste qu'une, c'est celle-là — et c'est le cas réel, puisqu'on déclare la fiche d'une
    démonstration à la fois. Sinon on propose un nom bâti sur le nom du référentiel, que
    l'admin corrigera."""
    ref = db.query(Referentiel).filter(Referentiel.id == referentiel_id).first()
    if not ref:
        raise HTTPException(404, "Référentiel inconnu.")

    # Les bases `_demo` du serveur, moins celles qu'une fiche revendique déjà.
    presentes = [r[0] for r in db.execute(text(
        r"SELECT datname FROM pg_database WHERE datname LIKE '%\_demo' ORDER BY datname"
    )).all()]
    declarees = {n for (n,) in db.query(Demo.nom_base).all()}
    candidates = [n for n in presentes if n not in declarees]

    if len(candidates) == 1:
        nom_base = candidates[0]
    else:
        # Repli : le nom du référentiel, ramené à des minuscules et des soulignés.
        base = re.sub(r"[^a-z0-9]+", "_", (ref.nom_fixe or "").lower()).strip("_")
        nom_base = f"{base}_demo" if base else ""

    # L'adresse suit le port libre suivant : les piles se numérotent à la file (5174, 5175…).
    ports = [int(m.group(1)) for (u,) in db.query(Demo.url).all() if u
             for m in [re.search(r":(\d{4,5})", u)] if m]
    url = f"http://localhost:{max(ports) + 1}" if ports else ""

    compteurs = {"nb_sequences": 0, "nb_seances": 0, "nb_activites": 0}
    base_trouvee = nom_base in presentes
    erreur = None
    if base_trouvee:
        # Une connexion jetable vers l'autre base : même serveur, même utilisateur, seul le nom
        # change. On dérive l'URL de l'objet `engine.url` et JAMAIS de son `str()` : SQLAlchemy
        # y remplace le mot de passe par des étoiles, et la connexion échouerait sur un refus
        # d'authentification. `dispose()` en sortie — aucun pool ne reste ouvert vers une démo.
        autre = create_engine(engine.url.set(database=nom_base),
                              pool_pre_ping=True, poolclass=NullPool)
        try:
            with autre.connect() as conn:
                for cle, table in (("nb_sequences", "sequences"), ("nb_seances", "seances"),
                                   ("nb_activites", "activites")):
                    compteurs[cle] = conn.execute(text(f"SELECT count(*) FROM {table}")).scalar() or 0
        except ProgrammingError:
            # Base présente mais pas encore migrée : les tables n'existent pas. Ce n'est pas une
            # erreur — c'est l'état normal entre le temps 1 et le temps 5 de la fabrication.
            base_trouvee = False
        except SQLAlchemyError as e:
            # Tout le reste — base injoignable, droits refusés — se DIT. Un `except` muet
            # renverrait trois zéros qui passeraient pour un comptage, et c'est exactement
            # ainsi qu'un mot de passe masqué est passé inaperçu la première fois.
            base_trouvee = False
            erreur = type(e).__name__
        finally:
            autre.dispose()

    return {"nom_base": nom_base, "url": url, "base_trouvee": base_trouvee,
            "candidates": candidates, "erreur": erreur, **compteurs}


@router.post("/admin/demos")
def admin_demos_creer(body: DemoIn, request: Request,
                      db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    nom, url = _valider_demo(body, db)
    if db.query(Demo).filter(Demo.referentiel_id == body.referentiel_id).first():
        raise HTTPException(409, "Ce référentiel a déjà une démonstration.")
    d = Demo(referentiel_id=body.referentiel_id, nom_base=nom, url=url,
             nb_activites=body.nb_activites, nb_sequences=body.nb_sequences,
             nb_seances=body.nb_seances, date_generation=body.date_generation,
             date_dernier_test=body.date_dernier_test,
             defauts_connus=body.defauts_connus, notes=body.notes)
    db.add(d)
    db.commit()
    db.refresh(d)
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="DEMO_CREEE",
                     ip=request.client.host if request.client else None,
                     details=f"Démonstration déclarée : {nom} (référentiel #{d.referentiel_id})")
    return {"id": d.id}


@router.put("/admin/demos/{demo_id}")
def admin_demos_modifier(demo_id: int, body: DemoIn, request: Request,
                         db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    d = db.get(Demo, demo_id)
    if not d:
        raise HTTPException(404, "Démonstration introuvable.")
    nom, url = _valider_demo(body, db)
    doublon = (db.query(Demo)
                 .filter(Demo.referentiel_id == body.referentiel_id, Demo.id != demo_id)
                 .first())
    if doublon:
        raise HTTPException(409, "Ce référentiel a déjà une démonstration.")
    d.referentiel_id = body.referentiel_id
    d.nom_base = nom
    d.url = url
    d.nb_activites = body.nb_activites
    d.nb_sequences = body.nb_sequences
    d.nb_seances = body.nb_seances
    d.date_generation = body.date_generation
    d.date_dernier_test = body.date_dernier_test
    d.defauts_connus = body.defauts_connus
    d.notes = body.notes
    db.commit()
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="DEMO_MODIFIEE",
                     ip=request.client.host if request.client else None,
                     details=f"Démonstration modifiée : {nom} (référentiel #{d.referentiel_id})")
    return {"status": "ok"}


@router.get("/admin/demos/{demo_id}/aller")
def admin_demos_aller(demo_id: int, request: Request,
                      db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Visiter N'IMPORTE QUELLE démonstration depuis l'écran d'administration.

    POURQUOI CETTE PORTE EXISTE EN PLUS DE CELLE DU PROF. Le passage du prof (`/demo/aller`)
    l'envoie vers la démonstration de SON niveau, et seulement si elle est testée ou validée :
    c'est juste pour lui. L'admin, lui, doit pouvoir ouvrir celle de la crèche le matin et celle
    du BTS l'après-midi — et surtout AVANT qu'elle soit déclarée testée, puisque c'est en la
    visitant qu'il le décide. Sans cette porte, il n'existait aucun moyen de relire une
    démonstration qui ne correspond pas à son propre couple : il fallait se fabriquer un compte.

    L'IDENTITÉ EMPORTÉE est celle de l'administrateur (`ADMIN_EMAIL`), avec le niveau de la
    démonstration visée et la première matière de son référentiel — sinon il arriverait sans
    couple et l'écran lui demanderait de compléter son profil avant de rien voir.

    LE JETON est le même que celui du prof, fabriqué au même endroit (`demo.passage`) : cinq
    minutes, signé, porteur de noms et jamais d'identifiants.
    """
    d = db.get(Demo, demo_id)
    if not d:
        raise HTTPException(404, "Démonstration introuvable.")
    if not d.url:
        raise HTTPException(409, "Cette démonstration n'a pas d'adresse : renseignez-la d'abord.")
    if not demo.secret_pose():
        raise HTTPException(409, "DEMO_SECRET n'est pas posé sur ce serveur : le passage est impossible.")
    email = (os.getenv("ADMIN_EMAIL") or "").strip()
    if not email:
        raise HTTPException(409, "ADMIN_EMAIL n'est pas posé sur ce serveur : "
                                 "le visiteur n'aurait pas d'identité.")

    ref = db.get(Referentiel, d.referentiel_id)
    niveau = db.get(Niveau, ref.niveau_id) if ref else None
    matiere = (db.query(Matiere)
                 .filter(Matiere.referentiel_id == d.referentiel_id, Matiere.actif.is_(True))
                 .order_by(Matiere.ordre, Matiere.nom)
                 .first())
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="DEMO_VISITEE",
                     ip=request.client.host if request.client else None,
                     details=f"Visite de la démonstration {d.nom_base} ({niveau.nom if niveau else '?'})")
    return RedirectResponse(
        demo.passage(d.url, email, "Admin", "aSchool",
                     matiere.nom if matiere else None,
                     niveau.nom if niveau else None),
        status_code=307,
    )


@router.delete("/admin/demos/{demo_id}")
def admin_demos_supprimer(demo_id: int, request: Request,
                          db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Supprime la FICHE, pas la base PostgreSQL — celle-ci vit ailleurs et se détruit à la main.
    Le bouton doit donc dire « Retirer de la liste » et non « Supprimer la démo »."""
    d = db.get(Demo, demo_id)
    if not d:
        raise HTTPException(404, "Démonstration introuvable.")
    nom = d.nom_base
    db.delete(d)
    db.commit()
    log_admin_action(db=db, admin_email=_get_admin_email(request), action="DEMO_RETIREE",
                     ip=request.client.host if request.client else None,
                     details=f"Fiche retirée de la liste : {nom} (la base PostgreSQL, elle, reste)")
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# LE CARNET DE L'ADMINISTRATEUR — écran « Tâches à faire »
#
# À NE PAS CONFONDRE avec `/admin/taches` juste au-dessus, qui règle le PLANIFICATEUR : là, des
# travaux que le serveur exécute tout seul ; ici, des notes que personne n'exécute. Le préfixe
# d'URL les sépare (`taches-a-faire`), et les deux écrans portent des noms différents.
# ---------------------------------------------------------------------------

class TacheAFaireBody(BaseModel):
    titre: str
    detail: str | None = None
    fait: bool = False


def _tache_a_faire_vue(t: TacheAFaire) -> dict:
    return {
        "id": t.id,
        "titre": t.titre,
        "detail": t.detail,
        "fait": t.fait,
        "fait_at": t.fait_at.isoformat() if t.fait_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("/admin/taches-a-faire")
def lister_taches_a_faire(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Le carnet, à faire d'abord. Une note cochée descend, elle ne disparaît pas : c'est la
    trace de ce qui a été décidé, et parfois la preuve qu'on l'avait déjà tranché."""
    lignes = (
        db.query(TacheAFaire)
        .order_by(TacheAFaire.fait.asc(), TacheAFaire.created_at.desc())
        .all()
    )
    return {"taches": [_tache_a_faire_vue(t) for t in lignes]}


@router.post("/admin/taches-a-faire", status_code=201)
def creer_tache_a_faire(body: TacheAFaireBody, db: Session = Depends(get_db),
                        _: None = Depends(_require_admin)):
    titre = (body.titre or "").strip()
    if not titre:
        raise HTTPException(400, "Une note sans titre ne se retrouve pas : donnez-lui un titre.")
    t = TacheAFaire(titre=titre[:200], detail=(body.detail or "").strip() or None)
    db.add(t)
    db.commit()
    return _tache_a_faire_vue(t)


@router.put("/admin/taches-a-faire/{tache_id}")
def modifier_tache_a_faire(tache_id: int, body: TacheAFaireBody, db: Session = Depends(get_db),
                           _: None = Depends(_require_admin)):
    t = db.get(TacheAFaire, tache_id)
    if t is None:
        raise HTTPException(404, "Note introuvable.")
    titre = (body.titre or "").strip()
    if not titre:
        raise HTTPException(400, "Une note sans titre ne se retrouve pas : donnez-lui un titre.")
    t.titre = titre[:200]
    t.detail = (body.detail or "").strip() or None
    # LA DATE SUIT LA CASE, dans les deux sens : décocher une note la remet à faire, et garder
    # une date de clôture sur une note rouverte la ferait passer pour terminée dans tout comptage.
    if body.fait and not t.fait:
        t.fait_at = maintenant_utc()
    elif not body.fait:
        t.fait_at = None
    t.fait = body.fait
    db.commit()
    return _tache_a_faire_vue(t)


@router.delete("/admin/taches-a-faire/{tache_id}")
def supprimer_tache_a_faire(tache_id: int, db: Session = Depends(get_db),
                            _: None = Depends(_require_admin)):
    """Supprime VRAIMENT la ligne. Un carnet qu'on ne peut pas raturer se remplit de notes mortes,
    et plus personne ne le lit."""
    t = db.get(TacheAFaire, tache_id)
    if t is None:
        raise HTTPException(404, "Note introuvable.")
    db.delete(t)
    db.commit()
    return {"status": "ok"}
