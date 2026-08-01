"""L'heure du serveur, à UN seul endroit.

`datetime.utcnow()` est DÉPRÉCIÉ depuis Python 3.12 : il rend une heure UTC sans le dire
(un datetime « naïf », sans fuseau), ce qui a produit assez de bugs pour que Python le
retire. Il était appelé 49 fois dans le backend.

Le remplacement évident — `datetime.now(timezone.utc)` — ne convient PAS ici : il rend un
datetime AVEC fuseau, alors que toutes les colonnes de la base sont naïves (`DateTime` sans
`timezone=True`). Comparer les deux lève `TypeError: can't compare offset-naive and
offset-aware datetimes` : la moitié des routes tomberait, et seulement à l'exécution.

D'où cette fonction : on prend l'heure UTC en le disant (`timezone.utc`), puis on retire le
fuseau pour rester exactement dans le format de la base. Comportement identique à
`utcnow()`, à la lettre près, sans l'avertissement — et le jour où l'on passera la base en
colonnes avec fuseau, il n'y aura qu'ICI à changer.
"""
from datetime import datetime, timezone


def maintenant_utc() -> datetime:
    """L'instant présent en UTC, sans fuseau attaché — le format des colonnes de la base."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
