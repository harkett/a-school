"""Les secrets de signature des jetons — une seule lecture, une seule règle, AUCUN repli.

POURQUOI CE MODULE. `JWT_SECRET` était lu à trois endroits, de trois façons différentes :

    backend/securite/comptes.py    os.getenv("JWT_SECRET", "change-me-in-production")
    backend/core/middleware.py     os.getenv("JWT_SECRET", "")
    backend/systeme/admin.py       ADMIN_JWT_SECRET ou JWT_SECRET, sinon refus

Le premier est le grave. Sur un serveur démarré sans `JWT_SECRET`, les jetons d'accès des
PROFS étaient signés avec « change-me-in-production » — une chaîne que n'importe qui lit dans
le dépôt. Quiconque connaît le projet pouvait forger un jeton valide pour n'importe quel
compte. Le serveur démarrait normalement, sans un mot.

Le raisonnement qui a fermé ce trou côté admin (`_admin_secret`, 02/08) n'avait pas été
appliqué au jeton PROF — alors que c'est celui-là qui protège les données des enseignants.

Les deux replis DIFFÉRAIENT aussi : un serveur mal configuré signait avec
« change-me-in-production » et vérifiait avec `""`. Aucun jeton n'aurait été reconnu, et rien
n'aurait expliqué pourquoi — juste des sessions qui ne tiennent pas.

POURQUOI ICI, ET PAS DANS backend/config.py. `config.py` est bien le module qui lit
l'environnement, et il est aussi un module feuille (il n'importe que `os`) : les trois
appelants pourraient l'importer sans cycle. Mais il est importé par `backend/llm/generator.py`
— donc un refus posé là ferait qu'un script de génération de texte exigerait `JWT_SECRET`, qui
ne le concerne en rien. Le refus doit tomber quand l'APPLICATION démarre, pas quand une valeur
de configuration quelconque est lue. Ce module-ci n'est importé que par les trois modules qui
signent ou vérifient un jeton : alembic, les outils de base et les scripts n'en dépendent pas.
Il n'importe lui-même que `os` — aucun cycle possible, par construction.

QUAND LE REFUS TOMBE : AU DÉMARRAGE. `SECRET_JETON_PROF` est résolu au niveau module, donc à
l'import, donc au boot de l'application — même choix que `_admin_secret()`, qui est déjà appelé
à l'import de `backend.systeme.admin` pour cette raison. Un refus au premier usage laisserait
un serveur monter, répondre, accepter des inscriptions, et ne révéler le trou qu'à la première
connexion — ou jamais, si le trou est justement que tout marche. Une clé de signature manquante
n'est pas un cas dégradé qu'on traverse : c'est un serveur qu'il ne faut pas exposer.

RÉSOLU UNE FOIS, PAS À CHAQUE REQUÊTE. `comptes.py` lisait la variable à l'import et
`middleware.py` à chaque requête. Signer et vérifier doivent employer la MÊME valeur : une
variable d'environnement changée en cours de route désynchroniserait les deux, et toutes les
sessions tomberaient sans raison lisible. Les deux lisent désormais la même constante.
"""
import os


def secret_obligatoire(*noms: str, usage: str, quoi_poser: str) -> str:
    """Rend le premier des `noms` posé et non vide dans l'environnement. Sinon : LÈVE.

    Pas de valeur par défaut, jamais — ni chaîne vide, ni chaîne d'exemple. Une clé de
    signature absente n'a pas de repli raisonnable : signer avec une valeur connue est pire
    que ne pas démarrer, parce que ça ne se voit pas. Même refus explicite que celui du projet
    devant une base qui n'est pas PostgreSQL.

    `.strip()` et pas seulement « non vide » : « `JWT_SECRET=   ` » dans un .env passe le test
    du `or` mais ne protège rien.
    """
    for nom in noms:
        valeur = os.getenv(nom) or ""
        if valeur.strip():
            return valeur
    raise RuntimeError(f"SÉCURITÉ : aucun secret de signature pour {usage}. {quoi_poser}")


# Le secret des jetons PROF : émission (backend/securite/comptes.py) et vérification
# (backend/core/middleware.py) lisent CETTE ligne, pas l'environnement chacune de leur côté.
SECRET_JETON_PROF = secret_obligatoire(
    "JWT_SECRET",
    usage="les jetons des profs (connexion, session, renouvellement)",
    quoi_poser=(
        "Posez JWT_SECRET dans le .env du serveur — une valeur longue et tirée au hasard, "
        "par exemple `python -c \"import secrets; print(secrets.token_hex(32))\"`. "
        "Sans lui, les jetons d'accès seraient signés avec une valeur connue, et n'importe "
        "qui pourrait en fabriquer un pour n'importe quel compte."
    ),
)
