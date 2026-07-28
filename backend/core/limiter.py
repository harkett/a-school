from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

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
            "detail": "Trop de demandes ont été envoyées depuis cet appareil. "
                      "Patientez une heure avant de réessayer."
        },
    )
    return request.app.state.limiter._inject_headers(reponse, request.state.view_rate_limit)
