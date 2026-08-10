r"""L'écran Paramètres promet un « écran dédié » — ce test vérifie qu'il existe vraiment.

LA PANNE QU'IL EMPÊCHE. L'écran Système › Paramètres liste `settings` en lecture seule et marque
certaines lignes « réglable sur son écran dédié ». Ce marquage venait d'une liste RECOPIÉE à la
main (`_PARAM_ECRAN_DEDIE_EXACTS` / `_PREFIXES`), que rien ne confrontait à la réalité. Le
10/08/2026 elle mentait dans les deux sens :

  - elle promettait un écran à `rag_top_k`, qui n'en a aucun — l'admin cherchait un formulaire
    inexistant ;
  - elle taisait `stream_silence_timeout`, `ai_retry_max` et `ai_retry_wait_max`, qui ont pourtant
    chacun le leur dans Système › Génération — l'admin les croyait figés ;
  - son préfixe `max_tokens_` désignait un écran supprimé le jour même.

Sa propre entrée de dette l'avait annoncé mot pour mot : « ajouter demain un réglage à écran
dédié sans toucher cette liste, et l'écran Paramètres ment sans que rien ne tombe. Aucun test ne
la garde. » Celui-ci la garde.

CE QU'IL PROUVE, et comment. Il ne compare pas la liste à une autre liste — ce serait recopier le
problème. Il LIT LE CODE des routes `PUT` de réglage et en extrait les clés `settings` qu'elles
écrivent vraiment, puis confronte les deux ensembles dans les deux sens.

Lancer : docker compose exec backend python -m pytest tests/test_ecran_dedie_dit_vrai.py -q
"""
import ast
import inspect
import re

from backend.main import app
from backend.systeme import admin as adm

# Les routes `PUT` qui règlent une ou plusieurs clés de `settings` depuis un écran dédié.
# `/admin/settings` en est exclu : c'est l'écran GÉNÉRIQUE, celui qui porte le marquage — s'il
# comptait, tout serait « dédié » et le repère ne dirait plus rien.
_ROUTE_GENERIQUE = "/api/admin/settings"


def _routes_de_reglage():
    """Les endpoints PUT montés sous /api/admin, sauf l'écran générique."""
    out = []
    for r in app.routes:
        methodes = getattr(r, "methods", None) or set()
        chemin = getattr(r, "path", "")
        if "PUT" in methodes and chemin.startswith("/api/admin/") and chemin != _ROUTE_GENERIQUE:
            out.append((chemin, r.endpoint))
    return out


def _cles_ecrites(fonction) -> set[str]:
    """Les clés `settings` qu'une route écrit, lues DANS SON CODE.

    On cherche les chaînes littérales qui servent de clé : `Setting(key="…")`, une comparaison
    `Setting.key == "…"`, ou un tuple `("cle", valeur)` passé à une boucle d'écriture. Une clé
    calculée à l'exécution (`f"max_tokens_{outil}"`) n'est pas visée : ce cas a disparu avec
    l'écran des longueurs, et s'il revenait, ce test le dirait en ne trouvant rien."""
    try:
        source = inspect.getsource(fonction)
    except (OSError, TypeError):
        return set()
    source = inspect.cleandoc(source)
    cles = set()
    # `Setting(key="x")` et `Setting.key == "x"` — les deux formes d'écriture du projet.
    cles |= set(re.findall(r'Setting\(\s*key\s*=\s*["\']([a-z_][a-z0-9_]*)["\']', source))
    cles |= set(re.findall(r'Setting\.key\s*==\s*["\']([a-z_][a-z0-9_]*)["\']', source))
    # `_ecrire("x", …)` — l'écriture passe parfois par une fonction locale.
    cles |= set(re.findall(r'_ecrire\(\s*["\']([a-z_][a-z0-9_]*)["\']', source))
    # `for key, val in (("ai_retry_max", …), …)` — plusieurs clés d'un coup.
    cles |= set(re.findall(r'\(\s*["\']([a-z_][a-z0-9_]*)["\']\s*,\s*body\.', source))
    return cles


def _cles_a_ecran_dedie() -> set[str]:
    reelles = set()
    for _chemin, fonction in _routes_de_reglage():
        reelles |= _cles_ecrites(fonction)
    return reelles


def test_le_code_expose_bien_des_cles_a_lire():
    """Garde-fou du test lui-même : s'il ne trouvait plus rien, les deux suivants passeraient
    en annonçant une cohérence qu'ils n'auraient pas vérifiée."""
    trouvees = _cles_a_ecran_dedie()
    assert len(trouvees) >= 4, (
        f"Ce test ne sait plus lire les routes de réglage (trouvé : {sorted(trouvees)}). "
        "Les formes d'écriture ont dû changer — mettez `_cles_ecrites` à jour, sinon les deux "
        "tests suivants ne prouvent plus rien."
    )


def test_aucune_cle_marquee_sans_ecran_reel():
    """Le premier sens : promettre un écran qui n'existe pas envoie l'admin chercher dans le
    vide. C'est ce que faisait `rag_top_k`."""
    reelles = _cles_a_ecran_dedie()
    menteuses = sorted(adm._PARAM_ECRAN_DEDIE_EXACTS - reelles)
    assert not menteuses, (
        f"Ces clés sont annoncées « réglables sur leur écran dédié », mais aucune route PUT ne "
        f"les écrit : {menteuses}. Retirez-les de `_PARAM_ECRAN_DEDIE_EXACTS`, ou donnez-leur "
        f"l'écran promis."
    )


def test_aucun_ecran_reel_sans_sa_cle_marquee():
    """L'autre sens, celui qui s'installe tout seul : un réglage reçoit son formulaire, personne
    ne pense à cette liste, et l'écran Paramètres le montre comme figé. Trois clés étaient dans
    ce cas le 10/08/2026."""
    reelles = _cles_a_ecran_dedie()
    oubliees = sorted(
        c for c in reelles
        if c not in adm._PARAM_ECRAN_DEDIE_EXACTS
        and not c.startswith(adm._PARAM_ECRAN_DEDIE_PREFIXES)
    )
    assert not oubliees, (
        f"Ces clés ont bel et bien un écran dédié, mais l'écran Paramètres les montre comme si "
        f"elles n'en avaient pas : {oubliees}. Ajoutez-les à `_PARAM_ECRAN_DEDIE_EXACTS`."
    )


def test_les_prefixes_designent_encore_quelque_chose():
    """Un préfixe survit à l'écran qu'il désignait — `max_tokens_` l'a fait. Il ne casse rien,
    et c'est bien le problème : il ment sans bruit jusqu'à ce que quelqu'un le lise."""
    from backend.core.llm_prompts import PROMPTS
    connues = {f"prompt_{c}" for c in PROMPTS} | _cles_a_ecran_dedie()
    morts = [p for p in adm._PARAM_ECRAN_DEDIE_PREFIXES
             if not any(k.startswith(p) for k in connues)]
    assert not morts, (
        f"Ces préfixes ne désignent plus aucune clé existante : {morts}. Leur écran a disparu — "
        f"retirez-les de `_PARAM_ECRAN_DEDIE_PREFIXES`."
    )
