# -*- coding: utf-8 -*-
"""LE PLANIFICATEUR — les travaux que l'application fait toute seule, réglés par l'administrateur.

CE QU'IL REMPLACE. Les deux travaux automatiques de l'application — la surveillance du serveur, la
veille des tarifs d'IA — étaient écrits dans `main.py` : leur heure, leur fréquence, leur existence
même. Changer « 6 h 05 » en « 22 h 00 » demandait un développeur, une relecture et un
redéploiement. C'est un réglage d'exploitation, pas du code.

CE QUI RESTE DANS LE CODE, ET POURQUOI. La FONCTION exécutée, forcément : on ne met pas du Python
en base. Le registre `TACHES` ci-dessous fait le lien entre un code stocké en base et la fonction
qui porte le travail. Ce qui vit en base, c'est tout le reste : activée ou non, à quelle heure, à
quelle cadence, à qui l'on écrit, et ce que le dernier passage a donné.

CE QUE L'ADMINISTRATEUR PEUT FAIRE SANS PERSONNE : activer, désactiver, changer l'heure, changer le
destinataire, et lancer un passage tout de suite pour vérifier — sans attendre le lendemain.

UNE TÂCHE QUI ÉCHOUE NE TUE PAS LES AUTRES. Chaque exécution est enveloppée : l'erreur est écrite
dans la ligne de la tâche (`dernier_resultat`), visible à l'écran, et l'ordonnanceur continue.
"""
import logging
import time

from backend.core.database import session_pour, INSTANCE_DEMOS, SCHEMA_REEL
from backend.core.horloge import maintenant_utc
from backend.core.models_db import TachePlanifiee

log = logging.getLogger(__name__)


def _veille_tarifs(destinataire: str | None) -> str:
    """Relève les tarifs des fournisseurs d'IA et prévient si un prix a changé."""
    from backend.systeme.veille_tarifs import veiller
    changements = veiller(destinataire=destinataire)
    if not changements:
        return "Aucun changement de tarif."
    return (f"{len(changements)} tarif(s) mis à jour : "
            + ", ".join(f"{c['fournisseur']} / {c['modele']}" for c in changements))


def _surveillance(destinataire: str | None) -> str:
    """Contrôle le processeur, le disque et les tentatives d'intrusion."""
    from backend.supervision.alerts import run_all_checks
    run_all_checks()
    return "Contrôles effectués."


# LE REGISTRE — la seule chose qui ne peut pas descendre en base : une fonction Python.
# `libelle` et `description` sont ici parce qu'ils décrivent le CODE, pas une préférence : si la
# fonction change de nature, son texte change avec elle, dans le même commit.
TACHES = {
    "veille_tarifs": {
        "fonction": _veille_tarifs,
        "libelle": "Veille des tarifs d'IA",
        "description": (
            "Relit la grille tarifaire publique de chaque fournisseur, écrit en base les prix qui "
            "ont changé, et envoie un courriel quand c'est le cas. N'écrit jamais l'ordre d'appel : "
            "c'est l'administrateur qui décide de réordonner ou non. Ne coûte rien — la page est "
            "lue, aucune IA n'est appelée."),
    },
    "surveillance": {
        "fonction": _surveillance,
        "libelle": "Surveillance du serveur",
        "description": (
            "Contrôle la charge du processeur, la place disque et les tentatives de connexion "
            "échouées. Émet une alerte en base, au journal et par courriel quand un seuil est "
            "dépassé (les seuils se règlent dans Surveillance → Alertes)."),
    },
}

# L'ordonnanceur de l'application. Posé par `main.py` au démarrage : ce module ne le crée pas, il
# s'en sert — deux ordonnanceurs voudraient dire deux fois chaque travail.
_scheduler = None


def _declencheur(t: TachePlanifiee) -> tuple[str, dict]:
    """Comment APScheduler doit déclencher cette tâche, d'après sa ligne en base."""
    if t.type_planif == "intervalle":
        return "interval", {"minutes": max(1, t.intervalle_minutes or 5)}
    return "cron", {"hour": t.heure or 0, "minute": t.minute or 0}


def executer(code: str) -> dict:
    """Lance une tâche, chronomètre, et écrit le résultat dans sa ligne.

    Appelée par l'ordonnanceur comme par le bouton « Exécuter maintenant » : un seul chemin, donc
    un essai manuel prouve vraiment ce que fera le passage automatique."""
    debut = time.monotonic()
    db = session_pour(SCHEMA_REEL)
    try:
        t = db.query(TachePlanifiee).filter(TachePlanifiee.code == code).first()
        if t is None or code not in TACHES:
            log.warning("Planificateur — tâche « %s » inconnue", code)
            return {"ok": False, "resultat": "Tâche inconnue."}
        try:
            resultat = TACHES[code]["fonction"](t.destinataire or None)
            ok = True
        except Exception as e:
            # L'échec d'une tâche est une information d'exploitation : il se lit sur sa ligne, il
            # ne disparaît pas dans les journaux et n'emporte pas les autres tâches.
            log.exception("Planificateur — « %s » a échoué", code)
            resultat, ok = f"Échec : {type(e).__name__} — {e}", False

        t.dernier_passage = maintenant_utc()
        t.dernier_resultat = resultat[:500]
        t.dernier_ok = ok
        t.derniere_duree_ms = int((time.monotonic() - debut) * 1000)
        db.commit()
        return {"ok": ok, "resultat": resultat}
    finally:
        db.close()


def programmer_tout(scheduler=None) -> int:
    """(Re)programme toutes les tâches actives d'après la base. Rend le nombre de tâches posées.

    Rappelée après chaque modification de l'écran : une heure changée doit s'appliquer tout de
    suite, pas au prochain redémarrage — sinon l'administrateur croit avoir réglé quelque chose
    qui ne bougera qu'à la prochaine mise en service."""
    global _scheduler
    if scheduler is not None:
        _scheduler = scheduler
    if _scheduler is None:
        return 0

    # AUCUN TRAVAIL AUTOMATIQUE DANS UNE INSTANCE DE DÉMONSTRATION, et le refus est ici plutôt que
    # dans `main.py` pour qu'aucun appelant ne puisse le contourner — l'écran d'administration
    # rappelle cette fonction à chaque modification.
    #
    # DEUX RAISONS, ET LA PREMIÈRE SUFFIT. Au démarrage, aucune requête n'a été servie : il n'y a
    # ni `Host` ni schéma résolu, et une instance de démonstration en porte autant qu'elle sert de
    # démonstrations. « Le schéma de la démonstration » n'existe pas à cet instant — viser l'un
    # d'eux serait un choix arbitraire, les viser tous multiplierait chaque travail par leur
    # nombre. La seconde : surveiller un serveur ou relever des tarifs de fournisseurs depuis un
    # bac à sable n'a pas d'objet, et ces travaux écrivent à quelqu'un.
    #
    # Sans ce garde-fou, le process des démonstrations ne démarrait pas du tout : `TachePlanifiee`
    # était lu dans le `public` de `aschool_demos`, qui ne porte que l'extension `vector`.
    if INSTANCE_DEMOS:
        log.info("Instance de démonstration : aucun travail automatique n'est programmé.")
        return 0

    db = session_pour(SCHEMA_REEL)
    try:
        taches = db.query(TachePlanifiee).all()
    finally:
        db.close()

    poses = 0
    for t in taches:
        if _scheduler.get_job(t.code):
            _scheduler.remove_job(t.code)
        if not t.actif or t.code not in TACHES:
            continue
        genre, reglages = _declencheur(t)
        _scheduler.add_job(executer, genre, args=[t.code], id=t.code,
                           replace_existing=True, **reglages)
        poses += 1
    log.info("Planificateur : %s tâche(s) active(s)", poses)
    return poses


def prochain_passage(code: str):
    """Quand cette tâche repassera, d'après l'ordonnanceur lui-même — pas d'après un calcul refait
    à l'écran, qui pourrait dire autre chose que ce qui se produira vraiment."""
    if _scheduler is None:
        return None
    job = _scheduler.get_job(code)
    return getattr(job, "next_run_time", None) if job else None
