"""Attend que la base réponde, puis rend la main. Lancé AVANT `alembic upgrade head`.

POURQUOI. Au démarrage du serveur, la commande est `alembic upgrade head && uvicorn …`. Si la
base n'est pas encore prête, alembic échoue, le `&&` coupe, et le conteneur meurt. Il repart
tout seul (`restart: unless-stopped`) et finit par réussir — donc personne ne l'a jamais vu.

Ce n'est pas théorique, c'est mesuré (02/08/2026), sur un redémarrage à froid du moteur :

    18:50:27  FATAL:  the database system is starting up
    18:50:32  FATAL:  the database system is starting up
    18:50:38  FATAL:  the database system is starting up
    18:50:42  INFO:   Uvicorn running on http://0.0.0.0:8001

Trois morts en quinze secondes avant que ça tienne. Une reproduction sur cinq démarrages à
froid ; jamais sur un simple `docker start` (cinq essais) ni après un arrêt brutal de la base
(cinq essais) — la machine froide est ce qui ouvre le créneau.

CE QUE `depends_on` NE COUVRE PAS, et c'est LA question à laquelle ce fichier répond.
docker-compose.yml déclare bien `depends_on: db: condition: service_healthy`, et il le fait
correctement : au `docker compose up`, la base est attendue jusqu'à ce qu'elle réponde. Mais
cet ordonnancement appartient à compose, et ne vaut qu'au moment où c'est COMPOSE qui démarre
les choses. Au lancement du moteur, ce n'est pas compose : c'est le démon qui relance tout seul
les conteneurs marqués `restart: unless-stopped`, sans ordre et sans attendre la santé de
personne. Démontré :

    docker start   backend            ->  backend démarre pendant que la base est ARRÊTÉE
    docker compose up -d backend      ->  base attendue, base saine, PUIS backend

Les deux garde-fous ne font donc pas double emploi : `depends_on` couvre le chemin normal
(`compose up`), celui-ci couvre le chemin qu'il ne peut pas atteindre (allumer l'ordinateur).
Retirer l'un ou l'autre rouvre un des deux chemins.

LE PLAFOND. La base répond 386 ms après le démarrage de son conteneur, et sa reprise après un
arrêt brutal prend 47 ms (mesuré sur cette machine). L'épisode réel le plus long observé a duré
15 s. Le plafond est à 60 s : cent fois la valeur normale, quatre fois le pire cas vu — assez
large pour une machine froide et chargée, assez court pour qu'une base réellement en panne se
signale en une minute au lieu de tourner indéfiniment. Une attente sans fin serait pire que le
défaut qu'on répare : le conteneur aurait l'air vivant en ne faisant rien.

Lancer à la main : docker compose exec backend python outils_bdd/attendre_la_base.py
"""
import os
import sys
import time

PLAFOND_SECONDES = 60
PAUSE_SECONDES = 1.0


def attendre(url: str, plafond: float = PLAFOND_SECONDES) -> None:
    """Rend la main dès que la base accepte une connexion. Sort en erreur passé le plafond.

    On ouvre une VRAIE connexion, pas un simple test de port : une base en cours de démarrage
    écoute déjà mais refuse (« the database system is starting up »), et c'est précisément ce
    cas-là qu'on attend. Un test de port dirait « c'est bon » trop tôt.
    """
    import psycopg   # importé ici : le module doit pouvoir se lire sans la dépendance

    debut = time.monotonic()
    derniere = ""
    premiere_tentative = True
    while True:
        try:
            with psycopg.connect(url, connect_timeout=3):
                if not premiere_tentative:
                    attendu = time.monotonic() - debut
                    print(f"  la base répond ({attendu:.0f} s d'attente), on continue.", flush=True)
                return
        except Exception as e:
            derniere = str(e).strip().splitlines()[-1] if str(e).strip() else e.__class__.__name__
            ecoule = time.monotonic() - debut
            if ecoule >= plafond:
                print(
                    f"\nARRÊT : la base n'a pas répondu au bout de {plafond:.0f} secondes.\n"
                    f"  Dernier refus : {derniere}\n"
                    f"  Vérifiez qu'elle est bien démarrée, puis relancez.\n",
                    file=sys.stderr, flush=True,
                )
                raise SystemExit(1)
            if premiere_tentative:
                # Rien n'est affiché quand la base répond du premier coup — le démarrage normal
                # reste silencieux, et cette ligne n'apparaît que le jour où elle sert.
                print("  la base n'est pas encore prête, j'attends…", flush=True)
                premiere_tentative = False
        time.sleep(PAUSE_SECONDES)


def main() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("ARRÊT : DATABASE_URL n'est pas renseignée — impossible de savoir quelle base attendre.",
              file=sys.stderr)
        raise SystemExit(1)
    # SQLAlchemy écrit `postgresql+psycopg://…` ; psycopg attend `postgresql://…`.
    attendre(url.replace("postgresql+psycopg://", "postgresql://", 1))


if __name__ == "__main__":
    main()
