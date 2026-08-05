# -*- coding: utf-8 -*-
r"""Le cache disque des reponses LLM, et les deux regles qui le rendent sur.

Un cache mal fait ne tombe pas en panne : il MENT. Il rend une reponse produite dans d'autres
conditions, ou fige une reponse coupee que relancer ne fait plus disparaitre. Aucun de ces deux
defauts ne se voit a l'execution — d'ou ces tests.

REGLE A — l'empreinte porte TOUT ce qui change la reponse.
  Le piege : ajouter un parametre a `generate()` (un `schema`, un `top_p`, un `system`) et oublier
  de le mettre dans l'empreinte. Le cache continue de fonctionner, les essais deviennent faux, et
  rien ne le dit. `test_l_empreinte_couvre_tous_les_parametres_semantiques` compare la recette a la
  signature REELLE de `generate` : tout parametre nouveau doit etre classe, dans l'empreinte ou
  dans la liste des exclus motives.

REGLE B — rien ne s'ecrit sans succes plein.
  `generate_cached` s'appuie sur un fait : une reponse coupee LEVE au lieu de revenir comme une
  chaine. C'etait vrai sur trois voies du moteur et faux sur la quatrieme (`_groq` non-streaming),
  qui rendait le texte ampute. `test_les_quatre_voies_levent_sur_troncature` garde la symetrie.

Lancer : docker compose exec backend python -m pytest tests/test_cache_llm.py -q
"""
import ast
import inspect
import json
import os
from pathlib import Path

import pytest

from backend.llm import cache, generator


@pytest.fixture(autouse=True)
def _sans_ecriture_en_base(monkeypatch):
    """Neutralise la pose de ligne d'usage. `generate_cached` l'importe LOCALEMENT (le moteur ne
    traine pas la couche base au chargement) : on remplace donc la fonction dans son module
    d'origine, pas dans `generator`. Sans cela, chaque test polluerait `usage_llm`."""
    import backend.analytique.usage as u
    monkeypatch.setattr(u, "enregistrer_usage", lambda **kw: None)


# Parametres de `generate()` DELIBEREMENT hors de l'empreinte, avec la raison. Un parametre absent
# de cette liste ET de PARAMS_EMPREINTE fait echouer le test : le choix doit etre ecrit, jamais subi.
HORS_EMPREINTE = {
    "cle": "secret — n'a rien a faire dans un nom de fichier ni dans son contenu",
    "read_timeout": "transport : decide si l'appel aboutit, pas ce que le modele repond",
    "retry_max": "transport (resilience 429)",
    "retry_wait_max": "transport (resilience 429)",
    "contexte_max": "garde-fou d'envoi : decide SI l'appel part, pas ce qu'il rend",
    "appel_long": "choisit le transport (flux ou non), pas le contenu demande",
    "outil": "mesure seule — deux outils qui posent la meme question meritent la meme reponse",
    "prefixe_cache": "redite du debut du prompt, deja dans l'empreinte via `prompt` — il dit au "
                     "fournisseur ou couper, il ne change pas la question posee",
}


def test_l_empreinte_couvre_tous_les_parametres_semantiques():
    params = set(inspect.signature(generator.generate).parameters) - {"prompt"}
    couverts = set(cache.PARAMS_EMPREINTE) - {"prompt"} | set(HORS_EMPREINTE)
    oublies = sorted(params - couverts)
    assert not oublies, (
        "Ces paramètres de generate() ne sont NI dans l'empreinte du cache NI déclarés hors "
        "empreinte : s'ils changent la réponse, le cache rejouera une réponse produite dans "
        "d'autres conditions sans que rien ne le signale.\n  "
        + "\n  ".join(f"{p} — ajoutez-le à cache.PARAMS_EMPREINTE ou à HORS_EMPREINTE avec sa raison"
                      for p in oublies)
    )
    # Et l'inverse : une recette qui nomme un paramètre disparu de generate() ne protège plus rien.
    fantomes = sorted(set(cache.PARAMS_EMPREINTE) - {"prompt"} - set(inspect.signature(generator.generate).parameters))
    assert not fantomes, f"L'empreinte nomme des paramètres qui n'existent plus dans generate() : {fantomes}"


def test_generate_cached_a_la_meme_signature_que_generate():
    """Le wrapper recopie la signature. Un parametre ajoute a `generate` et oublie ici serait
    silencieusement absent de l'empreinte — le cache rendrait alors la meme reponse pour deux
    demandes differentes."""
    assert (list(inspect.signature(generator.generate_cached).parameters)
            == list(inspect.signature(generator.generate).parameters)), (
        "generate_cached et generate n'ont plus la même signature : le cache ne verrait pas le "
        "paramètre ajouté, et son empreinte deviendrait incomplète."
    )


def test_l_empreinte_change_avec_chaque_parametre_semantique():
    """Chaque parametre semantique, modifie SEUL, doit produire une autre empreinte. Sans ce test,
    un parametre present dans le dict mais ecrase par erreur passerait inapercu."""
    base = {"prompt": "p", "provider": "anthropic", "model": "m", "max_tokens": 100,
            "temperature": 0, "json_mode": False, "schema": None}
    ref = cache.empreinte(base)
    for champ, autre in [("prompt", "q"), ("provider", "groq"), ("model", "n"),
                         ("max_tokens", 200), ("temperature", 0.7), ("json_mode", True),
                         ("schema", {"type": "object"})]:
        assert cache.empreinte({**base, champ: autre}) != ref, (
            f"Changer « {champ} » ne change pas l'empreinte : le cache rendrait l'ancienne réponse."
        )


def test_l_ordre_des_cles_ne_change_pas_l_empreinte():
    """`sort_keys` : un dictionnaire construit dans un autre ordre pose la meme question. Sans le
    tri, l'empreinte ne se repeterait pas et le cache ne tomberait jamais."""
    a = cache.empreinte({"prompt": "p", "model": "m", "max_tokens": 10})
    b = cache.empreinte({"max_tokens": 10, "prompt": "p", "model": "m"})
    assert a == b


def test_eteint_par_defaut(monkeypatch):
    """Sans LLM_CACHE=1, le cache n'existe pas. C'est ce qui permet de laisser `generate_cached`
    branche en production sans qu'un prof recoive une reponse d'hier."""
    monkeypatch.delenv("LLM_CACHE", raising=False)
    assert cache.actif() is False
    monkeypatch.setenv("LLM_CACHE", "0")
    assert cache.actif() is False
    monkeypatch.setenv("LLM_CACHE", "1")
    assert cache.actif() is True


def test_ecrire_puis_lire(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "DOSSIER", tmp_path / "c")
    cle = cache.empreinte({"prompt": "bonjour"})
    assert cache.lire(cle) is None                       # rien encore
    cache.ecrire(cle, "la réponse", {"model": "m"})
    assert cache.lire(cle) == "la réponse"
    # Le fichier garde la DEMANDE a cote de la reponse : un cache illisible est un cache invérifiable.
    ecrit = json.loads((tmp_path / "c" / f"{cle}.json").read_text(encoding="utf-8"))
    assert ecrit["model"] == "m" and ecrit["reponse"] == "la réponse"


def test_un_fichier_abime_est_traite_comme_absent(tmp_path, monkeypatch):
    """Le pire qui puisse arriver est de repayer un appel. Faire tomber une generation parce qu'un
    fichier de cache est tronque serait le contraire du but."""
    monkeypatch.setattr(cache, "DOSSIER", tmp_path / "c")
    (tmp_path / "c").mkdir()
    cle = "a" * 64
    (tmp_path / "c" / f"{cle}.json").write_text("{ ceci n'est pas du JSON", encoding="utf-8")
    assert cache.lire(cle) is None


def test_aucun_fichier_temporaire_ne_reste(tmp_path, monkeypatch):
    """Ecriture atomique : le fichier n'apparait qu'une fois complet, et rien ne traine a cote."""
    monkeypatch.setattr(cache, "DOSSIER", tmp_path / "c")
    cle = cache.empreinte({"prompt": "x"})
    cache.ecrire(cle, "r", {})
    restes = [p.name for p in (tmp_path / "c").iterdir() if p.suffix == ".tmp"]
    assert not restes, f"Fichiers temporaires laissés derrière : {restes}"


def test_la_cle_api_n_est_jamais_dans_le_cache(tmp_path, monkeypatch):
    """Ni dans le nom du fichier, ni dans son contenu. Un secret ne se range pas sur disque."""
    monkeypatch.setattr(cache, "DOSSIER", tmp_path / "c")
    monkeypatch.setenv("LLM_CACHE", "1")
    secret = "sk-ceci-est-un-secret"
    appels = []

    def faux_generate(prompt, **kw):
        appels.append(kw)
        return "réponse du modèle"

    monkeypatch.setattr(generator, "generate", faux_generate)
    generator.generate_cached("prompt", cle=secret, model="m", outil="decoupe_amont")
    for fichier in (tmp_path / "c").iterdir():
        assert secret not in fichier.read_text(encoding="utf-8"), "La clé API est écrite en clair !"
        assert secret not in fichier.name


def test_le_deuxieme_appel_ne_repaie_pas(tmp_path, monkeypatch):
    """LE POINT DE TOUT L'EXERCICE : deux fois la meme demande = UN SEUL appel au modele."""
    monkeypatch.setattr(cache, "DOSSIER", tmp_path / "c")
    monkeypatch.setenv("LLM_CACHE", "1")
    nb = {"appels": 0}

    def faux_generate(prompt, **kw):
        nb["appels"] += 1
        return "découpe"

    monkeypatch.setattr(generator, "generate", faux_generate)

    a = generator.generate_cached("même prompt", cle="k", model="m", max_tokens=100)
    b = generator.generate_cached("même prompt", cle="k", model="m", max_tokens=100)
    assert a == b == "découpe"
    assert nb["appels"] == 1, "Le deuxième appel a été repayé : le cache ne sert à rien."

    # Un parametre semantique different = une autre question = un vrai appel.
    generator.generate_cached("même prompt", cle="k", model="m", max_tokens=200)
    assert nb["appels"] == 2, "Un max_tokens différent a été servi par le cache : réponse fausse."


def test_une_erreur_ne_s_ecrit_jamais(tmp_path, monkeypatch):
    """Regle B. Une reponse en cache est figee : une erreur mise en cache serait definitive."""
    monkeypatch.setattr(cache, "DOSSIER", tmp_path / "c")
    monkeypatch.setenv("LLM_CACHE", "1")

    def qui_leve(prompt, **kw):
        raise RuntimeError("Réponse coupée : le modèle a atteint sa limite de sortie.")

    monkeypatch.setattr(generator, "generate", qui_leve)
    with pytest.raises(RuntimeError):
        generator.generate_cached("p", cle="k", model="m")
    assert not (tmp_path / "c").exists() or not list((tmp_path / "c").glob("*.json"))


def test_une_reponse_vide_ne_s_ecrit_pas(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "DOSSIER", tmp_path / "c")
    monkeypatch.setenv("LLM_CACHE", "1")
    monkeypatch.setattr(generator, "generate", lambda prompt, **kw: "")
    assert generator.generate_cached("p", cle="k", model="m") == ""
    assert not (tmp_path / "c").exists() or not list((tmp_path / "c").glob("*.json"))


# ---------------------------------------------------------------------------
# Regle B, cote moteur : la troncature LEVE, sur les QUATRE voies.
# ---------------------------------------------------------------------------

def test_les_quatre_voies_levent_sur_troncature():
    """`generate_cached` n'ecrit que ce que `generate` lui rend : il compte donc sur le fait qu'une
    reponse coupee ne revient JAMAIS comme une chaine. Trois voies levaient, `_groq` non-streaming
    non — elle rendait le texte ampute comme s'il etait complet. Ce test garde les quatre alignees :
    sans lui, une decoupe coupee entrerait au cache et y resterait."""
    source = Path(generator.__file__).read_text(encoding="utf-8-sig")
    arbre = ast.parse(source)
    fonctions = {n.name: n for n in ast.walk(arbre)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    for nom in ("_anthropic", "_anthropic_stream", "_groq", "_groq_stream"):
        assert nom in fonctions, f"{nom} a disparu du moteur — ce test doit être revu."
        corps = ast.dump(fonctions[nom])
        # Le motif d'arret coupe s'appelle "max_tokens" chez Anthropic, "length" en dialecte OpenAI.
        compare = "'max_tokens'" in corps or "'length'" in corps
        leve = any(isinstance(n, ast.Raise) for n in ast.walk(fonctions[nom]))
        assert compare and leve, (
            f"{nom} ne lève pas sur une réponse coupée : elle rendrait un texte amputé que "
            f"l'appelant prendrait pour complet — et que le cache figerait pour de bon."
        )
