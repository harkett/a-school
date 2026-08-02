r"""La politique de rattrapage sur 429 s'applique à TOUS les appels IA du prof, pas à certains.

CE QUE CE TEST PROUVE, et pourquoi il existe. `ai_retry_max` et `ai_retry_wait_max` sont deux
réglages ADMIN, en base, rechargeables à chaud : sur une limite de débit du fournisseur (429),
le serveur re-tente au lieu d'abandonner. L'appelant doit les LIRE et les passer à `generate()`
— le moteur reste pur, il ne va rien chercher tout seul, et son défaut est `retry_max=0`.

Trois outils du prof ne les passaient pas :
  - « Détecteur d'ambiguïtés » (analyse/ambiguites.py) ;
  - « Analyse de consigne » (analyse/consigne.py) ;
  - « Tester un exemple » (pedagogie/exemple_referentiel.py).

Ils rendaient donc 429 au prof dès la PREMIÈRE limite du fournisseur, pendant que la séance,
la séquence et l'activité re-tentaient tranquillement. Le réglage de l'admin ne s'appliquait
pas à ces écrans-là, et rien ne le disait : la panne ressemble à « le service est très demandé »,
un message parfaitement crédible.

Ce test lit les appels réels plutôt qu'un comportement simulé : ce qui compte est qu'AUCUN site
d'appel n'oublie la politique, y compris ceux qu'on écrira demain.

Lancer : docker compose exec backend python -m pytest tests/test_rattrapage_429_partout.py -q
"""
import ast
import os


RACINE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(os.path.dirname(RACINE), "backend")

# Les appels IA qui NE sont PAS déclenchés par le prof : le traitement d'un référentiel au dépôt
# (analyse_amont) est un geste ADMIN, long et surveillé, qui rend son erreur à l'écran admin.
# On le nomme ici plutôt que de l'exclure en silence.
HORS_PORTEE = {
    "backend/rag/analyse_amont.py": "traitement d'un référentiel au dépôt — geste admin, pas prof",
}


def _appels_generate():
    """[(fichier, ligne, nom, arguments nommés)] pour chaque appel à generate/generate_stream."""
    trouves = []
    for racine, _, fichiers in os.walk(BACKEND):
        if "__pycache__" in racine:
            continue
        for nom_f in sorted(fichiers):
            if not nom_f.endswith(".py"):
                continue
            chemin = os.path.join(racine, nom_f)
            court = "backend/" + os.path.relpath(chemin, BACKEND).replace(os.sep, "/")
            if court == "backend/llm/generator.py":      # le moteur lui-même
                continue
            with open(chemin, encoding="utf-8-sig") as f:
                arbre = ast.parse(f.read())
            for n in ast.walk(arbre):
                if not isinstance(n, ast.Call):
                    continue
                cible = n.func.id if isinstance(n.func, ast.Name) else None
                if cible in ("generate", "generate_stream"):
                    trouves.append((court, n.lineno, cible,
                                    {kw.arg for kw in n.keywords if kw.arg}))
    return trouves


def test_il_y_a_bien_des_appels_a_analyser():
    """Garde-fou du garde-fou : un scanner qui ne trouve rien passerait au vert pour rien."""
    assert len(_appels_generate()) >= 10


def test_chaque_appel_du_prof_passe_la_politique_de_rattrapage():
    oublis = [
        f"{fichier}:{ligne} — {nom}(…) sans "
        + " ni ".join(sorted({"retry_max", "retry_wait_max"} - args))
        for fichier, ligne, nom, args in _appels_generate()
        if fichier not in HORS_PORTEE and not {"retry_max", "retry_wait_max"} <= args
    ]
    assert not oublis, (
        "Ces appels IA n'appliquent pas la politique de rattrapage sur 429 — le réglage admin "
        "`ai_retry_max` ne les concerne pas, et le prof reçoit un refus dès la première limite "
        "du fournisseur :\n  - " + "\n  - ".join(oublis)
        + "\n\nAjouter retry_max=get_retry_max(db), retry_wait_max=get_retry_wait_max(db)."
    )


def test_les_exclusions_nommees_existent_encore():
    """Une exclusion qui désigne un fichier disparu masquerait un vrai oubli le jour où un
    fichier reprend ce nom. La liste doit rester vraie."""
    fichiers = {f for f, _, _, _ in _appels_generate()}
    fantomes = sorted(set(HORS_PORTEE) - fichiers)
    assert not fantomes, f"Exclusions qui ne correspondent plus à aucun appel : {fantomes}"
