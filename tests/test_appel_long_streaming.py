r"""Un appel qui fait LIRE UN DOCUMENT ENTIER au modèle doit passer par le FLUX, pas par la voie
non-streaming.

CE QUE CES TESTS PROUVENT, et pourquoi ils existent. La voie non-streaming borne la requête par un
délai TOTAL (`timeout=60` dans `_anthropic`). Tant que les documents restaient courts, la découpe
tenait dedans ; le jour où elle a lu un référentiel complet (88 pages), l'API a coupé en cours de
génération — « Request timed out or interrupted ». Le flux, lui, ne connaît qu'un délai de SILENCE
qui se RÉARME à chaque morceau reçu : une génération lente mais qui progresse n'est jamais coupée.

Le piège n'est pas le chiffre 60, c'est la FRONTIÈRE : elle est invisible. Un appel long écrit sans
`appel_long=True` hérite des 60 s en silence et ne tombe que le jour où le document grossit. Ces
tests gèlent les deux moitiés de la frontière :

  - le mode long emprunte bien le flux, ET y emporte le SCHÉMA (Structured Outputs) — sans lui, la
    découpe rendrait un JSON libre, sans `option` ni `garder`, et le tranchage repartirait à zéro ;
  - le mode court, lui, ne bouge pas : il reste sur la voie non-streaming.

Aucun appel réseau ici : les adaptateurs fournisseur sont remplacés, on n'observe que l'aiguillage.

Lancer : docker compose exec backend python -m pytest tests/test_appel_long_streaming.py -q
"""
import backend.llm.generator as g


def _faux_flux(recu):
    """Remplace un adaptateur de flux : note ce qu'il reçoit, rend deux morceaux à recoller."""
    def adaptateur(prompt, **kw):
        recu.update(kw)
        recu["prompt"] = prompt
        yield '{"unites":'
        yield "[]}"
    return adaptateur


def test_appel_long_passe_par_le_flux_et_recolle_les_morceaux(monkeypatch):
    recu = {}
    monkeypatch.setattr(g, "_anthropic_stream", _faux_flux(recu))
    sortie = g.generate("coucou", cle="k", provider="anthropic", appel_long=True)
    assert sortie == '{"unites":[]}'  # l'appelant reçoit UNE chaîne, comme en non-streaming
    assert recu["prompt"] == "coucou"


def test_appel_long_emporte_le_schema_dans_le_flux(monkeypatch):
    """Sans ce passage, la sortie contrainte (option / garder) tomberait dès qu'on streame."""
    recu = {}
    monkeypatch.setattr(g, "_anthropic_stream", _faux_flux(recu))
    schema = {"type": "object", "properties": {"unites": {"type": "array"}}}
    g.generate("x", cle="k", provider="anthropic", schema=schema, json_mode=True, appel_long=True)
    assert recu["schema"] == schema
    assert recu["json_mode"] is True


def test_appel_long_groq_emporte_aussi_le_schema(monkeypatch):
    """Le contrat de sortie ne doit pas dépendre du fournisseur : basculer Groq ne le perd pas."""
    recu = {}
    monkeypatch.setattr(g, "_groq_stream", _faux_flux(recu))
    schema = {"type": "object"}
    g.generate("x", cle="k", provider="groq", schema=schema, appel_long=True)
    assert recu["schema"] == schema


def test_appel_court_reste_en_non_streaming(monkeypatch):
    """L'autre moitié de la frontière : sans `appel_long`, rien ne change pour les appels courts."""
    passages = []
    monkeypatch.setattr(g, "_anthropic", lambda p, **kw: passages.append("court") or "réponse")
    monkeypatch.setattr(g, "_anthropic_stream", _faux_flux({}))
    assert g.generate("x", cle="k", provider="anthropic") == "réponse"
    assert passages == ["court"]


def test_les_deux_voies_construisent_le_meme_corps_de_requete():
    """Flux et non-flux lisent le MÊME constructeur : impossible qu'`output_config` existe d'un côté
    et pas de l'autre (c'est exactement ce qui manquait avant)."""
    schema = {"type": "object"}
    corps = g._anthropic_kwargs("p", model="m", max_tokens=8000, json_mode=True, schema=schema)
    assert corps["output_config"] == {"format": {"type": "json_schema", "schema": schema}}
    assert "system" not in corps  # le schéma PRIME sur json_mode
    sans_schema = g._anthropic_kwargs("p", model="m", max_tokens=10, json_mode=True, schema=None)
    assert "output_config" not in sans_schema and sans_schema["system"]


def test_le_delai_du_flux_est_un_silence_pas_un_total():
    """Le client du flux porte un délai de LECTURE (réarmable), jamais un délai total : c'est ce qui
    distingue les deux transports. Le 60 s de la voie courte vit sur un AUTRE client, il ne peut pas
    déteindre ici."""
    import httpx
    import anthropic
    client = anthropic.Anthropic(api_key="x", timeout=httpx.Timeout(60.0, connect=10.0, write=10.0, pool=10.0))
    assert client.timeout.read == 60.0
    assert client.timeout.connect == 10.0


def test_la_decoupe_demande_le_mode_long(monkeypatch):
    """Le branchement lui-même : `decouper_texte` lit un référentiel entier, donc elle DOIT demander
    le mode long. Ce test tombe si quelqu'un le retire."""
    import backend.rag.analyse_amont as amont
    recu = {}

    def faux_generate(prompt, **kw):
        recu.update(kw)
        return '{"unites":[]}'

    # `generate_cached` et non `generate` : la découpe passe désormais par le cache disque (c'est
    # l'appel le plus cher du logiciel). Le bouchon se pose donc sur le nom RÉELLEMENT appelé —
    # sinon le test traverse jusqu'au vrai moteur et part au réseau.
    monkeypatch.setattr(amont, "generate_cached", faux_generate)
    monkeypatch.setattr(amont, "get_cle_texte", lambda db: "k")
    monkeypatch.setattr(amont, "get_ai_provider", lambda db: "anthropic")
    monkeypatch.setattr(amont, "get_ai_model", lambda db: "m")
    monkeypatch.setattr(amont, "get_max_tokens", lambda db, cle: 8000)
    # La fenêtre du modèle descend elle aussi depuis la base (ai_modeles.contexte_max) : même
    # motif que les autres résolutions, donc même bouchon ici. None = fenêtre inconnue.
    monkeypatch.setattr(amont, "get_contexte_max", lambda db: None)
    # La température descend elle aussi de la base depuis le 05/08/2026 (fiche du modèle :
    # Sonnet 5 la refuse). Même motif de bouchon que les autres résolutions, sinon `db=None`
    # traverse jusqu'à une vraie requête SQL.
    monkeypatch.setattr(amont, "get_temperature", lambda db: None)
    amont.decouper_texte("TEXTE", db=None, prompt="Découpe : {texte}")
    assert recu["appel_long"] is True
    assert recu["schema"] is amont._SCHEMA_DECOUPE
