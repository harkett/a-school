"""CONVERTIR EN EUROS — un taux, une source, une date.

POURQUOI CE MODULE EXISTE. Les fournisseurs d'IA n'annoncent pas leurs prix dans la même monnaie :
Infomaniak facture en francs suisses, tous les autres en dollars. Comparer deux tarifs sans les
ramener à la même unité, c'est se tromper de 17 % ou plus — et ce chiffre-là décide de l'ordre
dans lequel on appelle les fournisseurs.

CE QU'ON NE FAIT PAS : figer un taux dans le code. Il serait faux dès le lendemain, et faux en
silence : personne ne relit une constante. Le tarif reste donc stocké DANS SA MONNAIE D'ORIGINE —
celle que le fournisseur affiche sur sa page, vérifiable d'un coup d'œil — et l'euro se calcule au
moment de l'affichage.

LA SOURCE : la Banque centrale européenne, via `api.frankfurter.dev`. Gratuite, sans clé, sans
compte, sans quota — c'est le service de référence pour les taux BCE. Aucun euro dépensé, aucune
inscription à maintenir.

CE QUI SE PASSE QUAND ELLE NE RÉPOND PAS. On garde le dernier taux connu, avec sa date, et l'écran
dit de quand il date. Un taux d'hier vaut infiniment mieux qu'une conversion absente ou qu'un
chiffre inventé : sur des tarifs qui bougent de quelques dixièmes de pour cent par jour, l'ordre de
grandeur reste juste. S'il n'y a AUCUN taux connu, on ne convertit pas — et on le dit.
"""
import json
import logging
import urllib.request
from datetime import date, timedelta

log = logging.getLogger(__name__)

# La monnaie de référence de l'application : celle dans laquelle l'administrateur raisonne, et
# celle des factures qu'il reçoit.
DEVISE_APP = "EUR"

# Les monnaies dans lesquelles nos fournisseurs annoncent leurs prix. Écrites ici parce que
# l'écran ne doit proposer que ce que le convertisseur sait traiter — offrir le yen dans une combo
# alors qu'aucun taux ne suit ne raccorderait rien.
DEVISES = ("EUR", "USD", "CHF")

# Combien de temps un taux reste bon. Les taux BCE sont publiés une fois par jour ouvré : au-delà
# d'un jour on retente, en deçà on ne dérange personne.
FRAICHEUR = timedelta(days=1)

_SOURCE = "https://api.frankfurter.dev/v1/latest?base={devise}&symbols=EUR"

# Le cache du processus : {devise: (taux, date_du_relevé)}. Il n'a pas besoin de survivre au
# redémarrage — le premier affichage qui suit rappelle la source, et l'appel dure une fraction de
# seconde. Un taux en base ajouterait une table et une migration pour économiser une requête.
_cache: dict[str, tuple[float, date]] = {}


def _relever(devise: str) -> tuple[float, date] | None:
    """Interroge la BCE. Rend `None` si elle ne répond pas — jamais d'exception.

    Une conversion est un CONFORT d'affichage : elle ne doit pas pouvoir faire tomber l'écran des
    tarifs, ni la page des statistiques, pour un service tiers momentanément absent."""
    try:
        # `User-Agent` OBLIGATOIRE : sans en-tête, le service répond 403 à l'agent par défaut de
        # Python — le même piège que chez Groq, et le même message trompeur (« Forbidden » pour une
        # requête parfaitement licite).
        requete = urllib.request.Request(_SOURCE.format(devise=devise),
                                         headers={"User-Agent": "aSchool/1.0"})
        with urllib.request.urlopen(requete, timeout=5) as r:
            corps = json.loads(r.read().decode("utf-8"))
        taux = float(corps["rates"]["EUR"])
        jour = date.fromisoformat(corps["date"])
        return taux, jour
    except Exception as e:  # réseau, format, clé absente : tous traités pareil
        log.warning("Taux de change %s→EUR non relevé (%s) : %s", devise, type(e).__name__, e)
        return None


def taux_vers_euro(devise: str) -> tuple[float, date] | None:
    """Combien vaut UNE unité de `devise` en euros, et de quand date ce chiffre.

    `None` = on ne sait pas, et il ne faut donc rien afficher — ni zéro, ni le montant d'origine
    déguisé en euros."""
    devise = (devise or "").upper()
    if devise == DEVISE_APP:
        return 1.0, date.today()
    if devise not in DEVISES:
        return None

    connu = _cache.get(devise)
    if connu and (date.today() - connu[1]) <= FRAICHEUR:
        return connu

    frais = _relever(devise)
    if frais is not None:
        _cache[devise] = frais
        return frais
    # La source n'a pas répondu : le dernier taux connu, même périmé, reste plus utile que rien.
    return connu


def en_euros(montant, devise: str):
    """Convertit un montant, ou rend `None` si le taux est inconnu.

    Rend un flottant arrondi à quatre décimales : ces montants sont des tarifs au million de
    tokens, où le quatrième chiffre après la virgule pèse encore."""
    if montant is None:
        return None
    t = taux_vers_euro(devise)
    if t is None:
        return None
    return round(float(montant) * t[0], 4)
