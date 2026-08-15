r"""La température réglée doit ATTEINDRE le modèle — sur les deux voies, flux compris.

CE QUE CE FICHIER EMPÊCHE DE REVENIR (constaté le 05/08/2026).

Le paramètre `temperature` existait partout, était documenté comme « transmis si l'appelant l'a
passé »… et se perdait en route sur TROIS maillons de la voie streaming Anthropic :

  1. `generate(..., appel_long=True)` appelait `_anthropic_stream` sans le passer ;
  2. `generate_stream(...)` faisait la même chose ;
  3. `_anthropic_stream` appelait `_anthropic_kwargs` sans le passer non plus.

`_groq_stream`, lui, le recevait — le défaut ne se voyait donc que chez un fournisseur, sur une
seule voie, et sans aucun message. Une génération en flux ignorait le réglage de l'admin en
silence, et la découpe (qui passe par `appel_long`) tournait au défaut du modèle : elle rendait
53, puis 52, puis 29 unités sur le MÊME document.

CE QUE ÇA NE PROMET PAS. Que la sortie soit déterministe : sous un modèle qui refuse la
température (Claude Sonnet 5 répond 400, « `temperature` is deprecated for this model »),
`get_temperature` renvoie None et rien n'est envoyé — c'est voulu, la fiche du modèle décide.
Ce test garde le TUYAU, pas la reproductibilité, qui se joue dans le prompt.

Lancer : docker compose exec backend python -m pytest tests/test_temperature_atteint_le_modele.py -q
"""
import inspect

from backend.llm import generator


# ── 1. Le corps de requête : ce qui part vraiment chez Anthropic ────────────────────────────

def test_le_corps_anthropic_porte_la_temperature_quand_elle_est_donnee():
    kwargs = generator._anthropic_kwargs("bonjour", model="claude-sonnet-5", max_tokens=16,
                                         json_mode=False, schema=None, temperature=0)
    assert kwargs.get("temperature") == 0, (
        "La température n'entre pas dans le corps de la requête Anthropic : le réglage de "
        "l'admin n'atteindrait jamais le modèle."
    )


def test_le_corps_anthropic_n_invente_pas_de_temperature():
    """L'autre sens, tout aussi important : `None` veut dire « n'envoie rien ». C'est ce qui
    permet de parler à un modèle qui REFUSE le paramètre (400) sans le savoir ici."""
    kwargs = generator._anthropic_kwargs("bonjour", model="claude-sonnet-5", max_tokens=16,
                                         json_mode=False, schema=None, temperature=None)
    assert "temperature" not in kwargs, (
        "Une température est envoyée alors que l'appelant n'en a passé aucune : un modèle qui "
        "refuse le paramètre répondrait 400 sur TOUS les appels."
    )


# ── 2. Les maillons de passage : chaque étage doit transmettre ──────────────────────────────
#
# On relit le CODE des trois endroits, comme le fait test_prompt_du_couple_valide_a_l_ecriture :
# un corps de requête juste ne sert à rien si personne ne lui donne la valeur.

def _source(fn) -> str:
    return inspect.getsource(fn)


def test_generate_transmet_la_temperature_au_flux_anthropic():
    """`appel_long=True` (la découpe, les matières, les méta-prompts) passe par ce chemin.

    Lu dans `_appeler` : depuis que `generate` descend une LISTE de fournisseurs, c'est elle qui
    porte l'appel aux adaptateurs. Le maillon vérifié est le même, il a seulement changé de nom."""
    src = _source(generator._appeler)
    appel = src[src.index("_anthropic_stream("):]
    assert "temperature=temperature" in appel[:appel.index(")")], (
        "generate(appel_long=True) appelle _anthropic_stream sans température : tous les appels "
        "longs tourneraient au défaut du modèle, sans que rien ne le dise."
    )


def test_generate_stream_transmet_la_temperature_au_flux_anthropic():
    """La génération d'activités des professeurs passe par ce chemin."""
    src = _source(generator.generate_stream)
    appel = src[src.index("_anthropic_stream("):]
    assert "temperature=temperature" in appel[:appel.index(")")], (
        "generate_stream appelle _anthropic_stream sans température : les générations en flux "
        "ignoreraient le réglage de l'admin."
    )


def test_le_flux_anthropic_transmet_la_temperature_au_corps():
    """Le dernier maillon : reçue par `_anthropic_stream`, elle doit arriver dans le corps."""
    src = _source(generator._anthropic_stream)
    appel = src[src.index("_anthropic_kwargs("):]
    assert "temperature=temperature" in appel[:appel.index(")")], (
        "_anthropic_stream reçoit la température mais ne la met pas dans le corps : elle est "
        "perdue au dernier étage, celui qu'on regarde le moins."
    )


def test_le_flux_groq_transmet_aussi_la_temperature():
    """Il était déjà juste — on le garde tel quel, pour que le défaut ne se déplace pas."""
    for fn in (generator._appeler, generator.generate_stream):
        src = _source(fn)
        appel = src[src.index("_groq_stream("):]
        assert "temperature=temperature" in appel[:appel.index(")")], (
            f"{fn.__name__} appelle _groq_stream sans température."
        )
