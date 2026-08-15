r"""Un appel d'IA qui RATE doit laisser une trace qui s'additionne — pas seulement un log.

CE QUE CES TESTS PROUVENT, et pourquoi ils existent. Jusqu'au 14/08, `usage_llm` ne recevait une
ligne qu'après une réponse reçue. Un refus (quota épuisé, clé morte, service en panne) ne laissait
qu'un `log.warning` : un journal défile et s'efface, il ne s'additionne pas. La question « qu'est-ce
qui refuse, et à quelle fréquence ? » n'avait donc aucune réponse — alors que c'est exactement
celle qu'il faut trancher avant de décider dans quel ordre essayer plusieurs fournisseurs.

Trois choses sont vérifiées ici :
  1. le refus écrit sa ligne, avec le code du fournisseur, et SANS tokens (rien n'a été facturé) ;
  2. la réponse coupée ne se compte plus comme un succès : elle a coûté, elle n'a rien produit ;
  3. les refus que la traduction ignorait (401, 402, 403, 400 inexpliqué) arrivent à l'admin en
     français, chacun avec SON geste — une clé morte ne se répare pas en attendant.

Ce que ces tests garantissent AUSSI : mesurer ne change pas ce que l'appelant reçoit. Sur une
panne réseau, l'erreur d'origine repart telle quelle.

Lancer : docker compose exec backend python -m pytest tests/test_trace_des_refus.py -q
"""
from unittest.mock import MagicMock, patch

import pytest
import requests

import backend.analytique.usage as usage_mod
import backend.llm.generator as gen
from backend.llm.generator import (
    detail_admin,
    LLMCleRefuseeError,
    LLMDemandeInvalideError,
    LLMModeleIncompatibleError,
    LLMSoldeEpuiseError,
    _traduire_echec_fournisseur,
)


@pytest.fixture
def lignes(monkeypatch):
    """Intercepte ce qui PARTIRAIT en base : les tests portent sur le contenu de la ligne, pas sur
    la mécanique d'écriture (déjà éprouvée ailleurs)."""
    posees = []
    monkeypatch.setattr(usage_mod, "enregistrer_usage", lambda **kw: posees.append(kw))
    return posees


def _reponse(statut, texte="refus du fournisseur"):
    resp = MagicMock()
    resp.status_code = statut
    resp.ok = False
    resp.text = texte
    return resp


# ===================== 1. Le refus laisse sa ligne =====================

def test_un_refus_ecrit_sa_ligne_avec_le_code_du_fournisseur(lignes):
    gen._journal_echec("groq", "llama-3.3-70b", 429, debut=0.0, outil="decoupe")
    assert len(lignes) == 1
    ligne = lignes[0]
    assert ligne["resultat"] == "refus"
    assert ligne["code_http"] == 429
    assert ligne["fournisseur"] == "groq"
    assert ligne["outil"] == "decoupe"


def test_un_refus_ne_porte_aucun_token(lignes):
    """Un appel refusé n'a rien produit et ne se facture pas. Des zéros s'additionneraient et
    feraient croire à des appels gratuits ; l'absence, elle, ne ment pas."""
    gen._journal_echec("anthropic", "claude-sonnet-5", 500, debut=0.0)
    ligne = lignes[0]
    assert ligne.get("tokens_entree") is None
    assert ligne.get("tokens_sortie") is None


def test_sans_reponse_du_tout_le_code_reste_vide(lignes):
    """Délai dépassé, connexion perdue : le fournisseur n'a rien dit. Le distinguer d'un refus
    ANNONCÉ est précisément l'intérêt de la colonne."""
    gen._journal_echec("infomaniak", "mistral3", None, debut=0.0)
    assert lignes[0]["code_http"] is None
    assert lignes[0]["resultat"] == "refus"


# ===================== 2. La réponse coupée n'est pas un succès =====================

def test_la_reponse_coupee_se_declare_coupee(lignes):
    for motif in ("length", "max_tokens"):
        lignes.clear()
        gen._journal_appel("groq", "m", motif, 100, 50, 0.0)
        assert lignes[0]["resultat"] == "coupe", motif


def test_un_arret_normal_reste_un_succes(lignes):
    for motif in ("stop", "end_turn", None):
        lignes.clear()
        gen._journal_appel("groq", "m", motif, 100, 50, 0.0)
        assert lignes[0]["resultat"] == "ok", motif


# ===================== 3. Les refus qui n'étaient pas traduits =====================

def test_la_cle_refusee_dit_de_verifier_la_cle_et_non_d_attendre():
    for statut in (401, 403):
        with pytest.raises(LLMCleRefuseeError) as e:
            _traduire_echec_fournisseur(statut, "unauthorized", "m", "groq")
        message = str(e.value)
        # QUELLE clé est morte : dans le DÉTAIL TECHNIQUE, pas dans le message. Le message est lu
        # par un professeur, à qui le nom « groq » ne dit rien et ne fait rien faire ; le détail
        # est lu par l'administrateur, à qui il dit exactement quelle variable revoir.
        assert "groq" in detail_admin(e.value)
        assert "réessayez" not in message.lower()   # attendre ne répare pas une clé


def test_le_solde_epuise_ne_se_confond_pas_avec_une_saturation():
    with pytest.raises(LLMSoldeEpuiseError) as e:
        _traduire_echec_fournisseur(402, "payment required", "m", "deepseek")
    assert "crédit" in str(e.value).lower()


def test_un_400_inexplique_est_dit_de_notre_cote():
    """Aucun autre fournisseur ne répondrait mieux : ils recevraient la même demande."""
    with pytest.raises(LLMDemandeInvalideError):
        _traduire_echec_fournisseur(400, '{"error":{"message":"unknown field foo"}}', "m", "groq")


def test_le_prompt_trop_long_d_anthropic_reste_un_probleme_de_modele():
    """Anthropic ne dit pas « must be < » mais « prompt is too long ». Ne reconnaître que la
    formule de Groq rangerait ce refus parmi les demandes mal formées — c'est-à-dire à l'endroit
    d'où l'on ne pense pas à changer de modèle."""
    corps = '{"type":"error","error":{"message":"prompt is too long: 208000 tokens > 200000 maximum"}}'
    with pytest.raises(LLMModeleIncompatibleError):
        _traduire_echec_fournisseur(400, corps, "claude-sonnet-5", "anthropic")


# ===================== 4. Le raccordement réel, par la voie d'appel =====================

def test_un_401_du_fournisseur_ecrit_la_ligne_avant_de_lever(lignes):
    with patch("requests.post", return_value=_reponse(401, "invalid api key")):
        with pytest.raises(LLMCleRefuseeError):
            gen._groq("bonjour", cle="fausse", model="llama-3.3-70b", fournisseur="groq")
    assert [(l["resultat"], l["code_http"]) for l in lignes] == [("refus", 401)]


def test_une_panne_reseau_est_tracee_et_l_erreur_repart_telle_quelle(lignes):
    """Mesurer ne doit RIEN changer à ce que reçoit l'appelant : l'exception de la bibliothèque
    remonte intacte, comme avant."""
    with patch("requests.post", side_effect=requests.exceptions.ConnectTimeout("delai")):
        with pytest.raises(requests.exceptions.ConnectTimeout):
            gen._groq("bonjour", cle="k", model="m", fournisseur="groq")
    assert [(l["resultat"], l["code_http"]) for l in lignes] == [("refus", None)]


def test_un_appel_reussi_ecrit_toujours_la_meme_ligne_qu_avant(lignes):
    """Le garde-fou du « sans rien casser » : sur le chemin normal, la ligne est celle d'hier —
    `resultat` vaut « ok » et le refus n'apparaît nulle part."""
    reponse = MagicMock()
    reponse.ok = True
    reponse.status_code = 200
    reponse.json.return_value = {
        "choices": [{"message": {"content": "voilà"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 3},
    }
    with patch("requests.post", return_value=reponse):
        assert gen._groq("bonjour", cle="k", model="m", fournisseur="groq") == "voilà"
    assert len(lignes) == 1
    assert lignes[0]["resultat"] == "ok"
    assert lignes[0]["tokens_entree"] == 12


# ── Le raccordement à l'écran — trois erreurs qui repartaient en 500 ────────────────────────────
#
# POURQUOI CE TEST. Les trois classes nées avec la trace des refus (clé refusée, solde épuisé,
# demande mal formée) n'étaient déclarées dans AUCUN gestionnaire : leur message était écrit pour
# un humain, mais il arrivait au professeur habillé d'un « 500 erreur interne » — le code qui dit
# « le serveur a planté ». Un test par classe, pour que la prochaine ne s'oublie pas non plus.

def test_les_erreurs_de_l_ia_ont_toutes_leur_code_http():
    """Une classe d'erreur LLM sans code déclaré repart en 500 : l'écran le plus alarmant, pour
    des situations qui n'ont rien d'un plantage."""
    from backend.main import _CODES_LLM
    from backend.llm import generator as g

    declarees = {classe for classe, _ in _CODES_LLM}
    toutes = {v for nom, v in vars(g).items()
              if nom.startswith("LLM") and isinstance(v, type) and issubclass(v, RuntimeError)}
    oubliees = sorted(c.__name__ for c in toutes - declarees)
    assert not oubliees, (
        "Ces erreurs d'IA n'ont aucun code HTTP déclaré dans main._CODES_LLM et repartiront "
        f"en 500 : {', '.join(oubliees)}"
    )


def test_le_professeur_n_est_pas_envoye_dans_un_ecran_qu_il_ne_peut_pas_ouvrir():
    """Les messages sont lus par des PROFESSEURS. « Paramètres → Génération » et « le fichier de
    configuration du serveur » sont des endroits d'administrateur : les nommer envoie chercher ce
    qu'on ne peut pas atteindre, ce qui est pire qu'un message vague."""
    for statut, classe in ((401, gen.LLMCleRefuseeError), (402, gen.LLMSoldeEpuiseError),
                           (400, gen.LLMDemandeInvalideError)):
        try:
            gen._traduire_echec_fournisseur(statut, "{}", "m", "groq")
        except classe as e:
            texte = str(e)
        else:
            raise AssertionError(f"{statut} ne lève pas {classe.__name__}")
        assert "Paramètres → Génération" not in texte, f"{classe.__name__} renvoie le prof à un écran d'admin"
        assert "fichier de configuration" not in texte, f"{classe.__name__} parle du serveur au prof"
        assert "administrateur" in texte, f"{classe.__name__} ne dit pas à qui s'adresser"
