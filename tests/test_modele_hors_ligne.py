"""Garde-fou — le modele d'embedding ne part JAMAIS chercher quoi que ce soit sur le reseau.

CE QUE CE FICHIER EMPECHE. `HF_HUB_OFFLINE` / `TRANSFORMERS_OFFLINE` n'etaient poses que dans
`backend/main.py`, donc pour le SERVEUR seul. Tout ce qui charge le modele sans passer par lui
— cette suite de tests, un script, un `docker exec python -c` — partait sans garde-fou.
Constate le 02/08/2026 : un appel direct a `retrieve_pg` repondait

    Warning: You are sending unauthenticated requests to the HF Hub.

Rien n'avait casse, parce que le cache etait la. C'est exactement le probleme : ca ne se voit
que le jour ou le cache manque — machine neuve, `docker/hf-cache` non recopie, volume perdu.
Ce jour-la, le serveur echoue net (« modele absent du cache ») pendant que la suite de tests
part chercher 2,2 Go sans le dire, ou reste pendue sur un reseau lent.

LA CONTRAINTE QUI DECIDE DE TOUT : `huggingface_hub` fige la valeur dans une constante au
premier chargement de `huggingface_hub.constants`. Apres, plus rien ne la bouge. Un test qui
se contenterait de lire `os.environ` ne prouverait donc RIEN — la variable peut etre posee et
arrivee trop tard. On verifie la constante REELLEMENT en vigueur.

Lancer : docker compose exec backend python -m pytest tests/test_modele_hors_ligne.py -q
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sans_les_variables(code: str) -> str:
    """Lance `code` dans un process neuf D'OU LES DEUX VARIABLES SONT RETIREES.

    C'est la seule facon de tester le garde-fou du CODE : dans la boite, docker-compose.yml
    les pose deja (ceinture), et un test qui les verrait ne dirait rien du filet."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}
    r = subprocess.run([sys.executable, "-c", code], cwd=REPO, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout.strip()


def test_la_constante_en_vigueur_est_bien_hors_ligne():
    """LE test du point : charger le modele par la voie la plus courte — celle du script et du
    `docker exec` — laisse `huggingface_hub` en mode hors-ligne, SANS aucune variable posee par
    l'environnement. C'est `backend/rag/embeddings.py` qui le garantit."""
    sortie = _sans_les_variables(
        "import backend.rag.embeddings\n"
        "from huggingface_hub import constants\n"
        "print(constants.HF_HUB_OFFLINE)"
    )
    assert sortie == "True", (
        "le modele peut aller sur le reseau depuis un point d'entree autre que le serveur : "
        f"huggingface_hub.constants.HF_HUB_OFFLINE = {sortie}"
    )


def test_le_garde_fou_precede_le_chargement_de_huggingface_hub():
    """La valeur ne suffit pas : il faut qu'elle soit posee AVANT que `huggingface_hub.constants`
    soit charge, sinon elle n'a aucun effet. On verifie l'ordre, pas le resultat."""
    sortie = _sans_les_variables(
        "import sys\n"
        "import backend.rag.embeddings\n"
        "print('huggingface_hub.constants' in sys.modules)"
    )
    assert sortie == "False", (
        "`huggingface_hub.constants` est deja charge quand le garde-fou s'execute : la "
        "constante est figee avant, et poser la variable ne sert plus a rien"
    )


def test_poser_la_variable_trop_tard_ne_sert_a_rien():
    """Le temoin, mesure, qui justifie l'emplacement choisi. Si ce test venait a passer un jour,
    c'est que `huggingface_hub` a change de facon de lire la variable — et alors tout ce
    raisonnement (et l'emplacement du garde-fou) serait a revoir."""
    sortie = _sans_les_variables(
        "from huggingface_hub import constants\n"     # fige la constante ICI, a False
        "import backend.rag.embeddings\n"             # son setdefault arrive apres
        "print(constants.HF_HUB_OFFLINE)"
    )
    assert sortie == "False", (
        "huggingface_hub ne fige plus sa constante au chargement : le garde-fou pourrait "
        "vivre ailleurs, et le commentaire de backend/rag/embeddings.py est a reecrire"
    )


def test_le_serveur_reste_couvert_lui_aussi():
    """`backend/main.py` portait ces deux lignes ; elles en sont parties. Le serveur passe par
    le meme chemin que les autres — on le verifie plutot que de le supposer."""
    sortie = _sans_les_variables(
        "import backend.main\n"
        "import backend.rag.embeddings\n"
        "from huggingface_hub import constants\n"
        "print(constants.HF_HUB_OFFLINE)"
    )
    assert sortie == "True"
