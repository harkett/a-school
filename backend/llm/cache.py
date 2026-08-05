# -*- coding: utf-8 -*-
"""Cache disque des réponses LLM — pour ne PAS repayer la même question en développement.

LE PROBLÈME. Le coût en dev ne vient pas du modèle choisi, il vient de rappeler l'API à chaque
essai. Une découpe de référentiel envoie ~210 000 tokens ; la relancer trois fois pour régler un
détail d'affichage, c'est la payer trois fois pour une réponse strictement identique.

LA RÉPONSE. On appelle une fois, on range la réponse sous l'empreinte de la demande, et les essais
suivants la relisent sur disque : zéro appel, zéro token, zéro dollar, réponse instantanée.

CE MODULE NE CONNAÎT QUE DES FICHIERS. Aucune base, aucun réseau, aucun import du moteur — il ne
sait même pas ce qu'est un LLM. Le branchement se fait dans `generator.generate_cached`, qui reste
le seul endroit à savoir que ces deux mondes se parlent.

LES DEUX RÈGLES QUI FONT LA JUSTESSE DU CACHE :

  A. L'EMPREINTE PORTE TOUT CE QUI CHANGE LA RÉPONSE. Pas seulement le prompt : le fournisseur, le
     modèle, `max_tokens`, la température, le mode JSON et le schéma. Si l'un manque, on rejoue une
     réponse produite dans d'autres conditions et l'écran ment sans que rien ne le signale — c'est
     pire qu'une panne, parce qu'une panne se voit. Le contrôle en est fait par un test qui compare
     la recette de l'empreinte à la signature réelle de `generate()`.

  B. RIEN NE S'ÉCRIT SANS SUCCÈS PLEIN. Une erreur, un délai dépassé ou une réponse coupée ne
     doivent JAMAIS entrer ici : une mauvaise réponse mise en cache est figée pour toujours, et
     relancer ne la fait plus disparaître. Le tri se fait chez l'appelant (cf. `generate_cached`).

CE QUI N'EST PAS DANS L'EMPREINTE, et pourquoi :
  - la clé API : c'est un secret, il n'a rien à faire dans un nom de fichier ni dans son contenu ;
  - `read_timeout`, `retry_max`, `retry_wait_max`, `contexte_max` : du transport et des garde-fous
    d'envoi. Ils décident SI l'appel part, jamais ce que le modèle répond ;
  - `outil` : il ne sert qu'à la mesure. Deux outils qui posent la même question au même modèle
    méritent la même réponse — les inclure diviserait le cache sans rien protéger ;
  - `appel_long` : choisit le transport (flux ou non), pas le contenu demandé ;
  - la date, la durée, la taille : volatiles par nature. Un seul champ volatil dans la clé et
    l'empreinte ne se répète JAMAIS — le cache ne tomberait pas deux fois pareil et paraîtrait
    simplement inutile. Ces informations vont dans le CONTENU du fichier, jamais dans son nom.

PURGE : supprimer le dossier. Rien d'autre à faire, aucune base à nettoyer.
"""
import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

# Dossier du cache. Relatif au répertoire de travail du serveur, et IGNORÉ PAR GIT : ces fichiers
# contiennent des prompts de travail, ils n'ont rien à faire dans l'historique du projet.
DOSSIER = Path(os.getenv("LLM_CACHE_DIR") or ".llm_cache")

# Les paramètres de `generate()` qui entrent dans l'empreinte. Écrits ici en toutes lettres, à un
# seul endroit, parce que c'est la liste que le test compare à la signature réelle : un paramètre
# ajouté à `generate()` sans décision explicite fait échouer le test au lieu de troubler le cache.
PARAMS_EMPREINTE = ("prompt", "provider", "model", "max_tokens", "temperature", "json_mode", "schema")


def actif() -> bool:
    """Le cache n'est allumé que si `LLM_CACHE=1`. Absent ou différent ⇒ éteint.

    Éteint, le code se comporte EXACTEMENT comme avant son existence : `generate_cached` appelle
    `generate` et rend la main. C'est ce qui permet de le laisser branché en production sans que
    rien ne change — un cache de développement ne doit jamais servir une réponse à un prof."""
    return os.getenv("LLM_CACHE") == "1"


def empreinte(params: dict) -> str:
    """SHA-256 du JSON TRIÉ des paramètres reçus.

    Trié (`sort_keys`), parce qu'un dictionnaire construit dans un autre ordre donnerait une autre
    empreinte pour la même question — et le cache ne tomberait jamais. `ensure_ascii=False` pour
    que les accents comptent comme des accents, `default=str` pour qu'un objet inattendu se
    représente au lieu de faire lever la fonction."""
    brut = json.dumps(params, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(brut.encode("utf-8")).hexdigest()


def _fichier(cle: str) -> Path:
    return DOSSIER / f"{cle}.json"


def lire(cle: str) -> str | None:
    """La réponse déjà payée, ou None s'il n'y en a pas.

    Ne lève JAMAIS : un fichier illisible, tronqué ou d'un ancien format est traité comme absent —
    on repaie un appel, ce qui est le pire qui puisse arriver. Faire tomber une génération parce
    qu'un fichier de cache est abîmé serait le contraire du but."""
    chemin = _fichier(cle)
    try:
        if not chemin.is_file():
            return None
        data = json.loads(chemin.read_text(encoding="utf-8"))
        reponse = data.get("reponse")
        return reponse if isinstance(reponse, str) and reponse else None
    except Exception as e:
        log.warning("Cache LLM illisible (%s) — on rappelle le modèle : %s", chemin.name, e)
        return None


def ecrire(cle: str, reponse: str, meta: dict) -> None:
    """Range la réponse sous son empreinte, avec ce qui l'a produite.

    LE FICHIER CONTIENT LA DEMANDE, pas seulement la réponse : un dossier de cache qu'on ne peut pas
    relire est un dossier qu'on ne peut pas vérifier. On veut pouvoir l'ouvrir et voir de quel
    prompt et de quel modèle vient ce texte.

    ÉCRITURE ATOMIQUE (fichier temporaire puis `os.replace`) : une écriture interrompue — Ctrl-C,
    conteneur arrêté — laisserait sinon un JSON à moitié écrit qui serait relu plus tard comme une
    réponse valide. `os.replace` ne publie le fichier qu'une fois complet.

    Ne lève jamais : un disque plein ne doit pas faire échouer une génération réussie."""
    try:
        DOSSIER.mkdir(parents=True, exist_ok=True)
        contenu = json.dumps({**meta, "reponse": reponse},
                             ensure_ascii=False, indent=2, default=str)
        fd, tmp = tempfile.mkstemp(dir=str(DOSSIER), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(contenu)
            os.replace(tmp, _fichier(cle))
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except Exception as e:
        log.warning("Cache LLM non écrit — sans conséquence, l'appel suivant repaiera : %s", e)
