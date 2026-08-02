from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.securite import comptes

limiter = Limiter(key_func=get_remote_address)

# Plafonds de débit des routes OUVERTES (aucune authentification) qui déclenchent un envoi
# d'email. Sans plafond, n'importe qui fait envoyer des mails par le serveur sous le nom de
# domaine aschool.fr. Comptés PAR ADRESSE IP (get_remote_address).
# Valeur haute sur l'inscription : un établissement sort sur UNE seule IP publique, donc une
# équipe entière qui crée ses comptes pendant la même séance ne doit pas être bloquée.
# Les deux autres routes envoient un mail vers une adresse QUELCONQUE sans authentification :
# ce sont les vraies portes d'abus, elles sont donc plus serrées.
# Valeurs destinées à passer EN BASE (Lot 2).
PLAFOND_SIGNUP = "20/hour"
PLAFOND_RENVOI_VERIFICATION = "5/hour"
PLAFOND_DEMANDE_RESET = "5/hour"


# ── Routes AUTHENTIFIÉES qui dépensent de l'argent à chaque appel ───────────────────────
# Ajoutés le 02/08/2026. /api/ocr et /api/transcribe n'avaient AUCUNE authentification et
# AUCUN plafond, alors qu'elles consomment les clés payantes du propriétaire : n'importe qui,
# sans compte, pouvait les appeler en boucle. Une OCR de PDF scanné, c'est jusqu'à 15 appels
# modèle pour UNE seule requête (backend/dictee/ocr.py:14).
#
# COMPTÉS PAR UTILISATEUR, PAS PAR ADRESSE — et c'est un choix, pas un défaut.
# Sur les trois routes ouvertes ci-dessus, l'adresse est la seule clé possible : il n'y a
# personne à désigner. Mais elle a le défaut décrit plus haut — un établissement entier sort
# sur UNE adresse publique, et le premier qui abuse plafonne tous les autres. Ici la route est
# authentifiée : la clé juste est celle qui désigne le responsable de la dépense, c'est-à-dire
# le compte. Voir cle_utilisateur() juste en dessous.
#
# DETTE ASSUMÉE, et dite comme telle : ces deux valeurs sont EN DUR, exactement comme les
# trois du dessus, et pour la même raison qu'elles doivent en sortir (Lot 2). Les basculer en
# base toutes seules aurait éclaté le même réglage entre deux endroits — la moitié en base, la
# moitié dans le code — ce qui est pire que la dette actuelle. Les cinq bougeront ensemble.
PLAFOND_DICTEE = "60/hour"   # une dictée = un appel ; 60/h, soit une par minute sans répit
PLAFOND_OCR    = "30/hour"   # une OCR = jusqu'à 15 appels ; 30/h borne à 450 pages par heure


def cle_utilisateur(request: Request) -> str:
    """Qui répond de la dépense : le compte, et l'adresse seulement à défaut.

    Le jeton lui-même ne peut pas servir de clé : il est renouvelé toutes les 15 minutes
    (ACCESS_TOKEN_EXPIRE_MINUTES), et le compteur repartirait donc de zéro à chaque
    renouvellement — un plafond horaire qui se remet à zéro quatre fois par heure n'est pas un
    plafond. On lit l'e-mail que le jeton porte, qui lui ne change pas.

    Le repli par adresse ne sert qu'aux requêtes sans jeton valide. Elles reçoivent 401 avant
    d'atteindre le plafond (la dépendance d'authentification est résolue avant l'appel), mais
    une fonction de clé doit toujours rendre quelque chose.
    """
    jeton = request.cookies.get("aschool_access")
    if jeton:
        email = comptes.verify_access_token(jeton)
        if email:
            return f"compte:{email}"
    return get_remote_address(request)


def plafond_depasse(request: Request, exc: RateLimitExceeded) -> Response:
    """Réponse affichée quand un plafond de débit est atteint — message HUMAIN (RÈGLE 23).

    Le gestionnaire fourni par slowapi renvoie « Rate limit exceeded: 20 per 1 hour » sous la
    clé `error`. Deux problèmes : le texte est technique et en anglais, et les écrans lisent
    tous `detail` (Signup.jsx), jamais `error` — le prof y voyait « Erreur 429 ».
    Les en-têtes de slowapi (Retry-After, compteurs) sont conservés tels quels.
    """
    reponse = JSONResponse(
        status_code=429,
        content={
            # « depuis cet appareil » était juste tant que tout se comptait par adresse. Les
            # plafonds de la dictée et de l'OCR se comptent par COMPTE : la même phrase y
            # aurait désigné le mauvais responsable, et envoyé chercher la panne du mauvais
            # côté. Formulation qui reste vraie dans les deux cas.
            "detail": "Trop de demandes ont été envoyées en peu de temps. "
                      "Patientez une heure avant de réessayer."
        },
    )
    return request.app.state.limiter._inject_headers(reponse, request.state.view_rate_limit)
