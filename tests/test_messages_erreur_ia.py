r"""Un échec du fournisseur d'IA doit arriver à l'admin en FRANÇAIS, pas en JSON d'API.

CE QUE CES TESTS PROUVENT, et pourquoi ils existent. Le 05/08, un admin a vu s'afficher :

    Découpe par l'IA impossible : {'type': 'error', 'error': {'details': None,
    'type': 'overloaded_error', 'message': 'Overloaded'}, 'request_id': 'req_011Cdj...'}

Ce texte ne dit pas ce qui s'est passé, ne dit pas quoi faire, et fait porter à l'admin un
vocabulaire qui n'est pas le sien. Pire : il confond deux situations qui n'appellent PAS le même
geste — le service saturé (attendre) et le modèle incompatible (changer un réglage). Devant
« réessayez plus tard », un admin attend une panne qui n'existe pas.

La traduction se fait à la SOURCE (`_traduire_echec_fournisseur`), pas dans chaque écran : les
appelants font tous `f"... impossible : {e}"`, donc le bon message leur arrive sans qu'ils en
sachent rien — et un nouvel appelant en hérite le jour où il est écrit.

Lancer : docker compose exec backend python -m pytest tests/test_messages_erreur_ia.py -q
"""
import pytest

from backend.llm.generator import (
    LLMIndisponibleError,
    LLMModeleIncompatibleError,
    LLMQuotaCompteError,
    LLMRateLimitError,
    _traduire_echec_fournisseur,
)

_OVERLOADED = '{"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}'
_FORMAT_REFUSE = '{"error":{"message":"This model does not support response format `json_schema`"}}'


def test_service_sature_dit_attendre_et_non_changer_de_reglage():
    with pytest.raises(LLMIndisponibleError) as e:
        _traduire_echec_fournisseur(529, _OVERLOADED, "claude-sonnet-5")
    message = str(e.value)
    assert "overloaded" not in message.lower()   # le JSON du fournisseur ne va pas à l'écran
    assert "réessayez" in message.lower()


def test_modele_incompatible_nomme_le_modele_et_le_geste():
    """Le message doit nommer le coupable ET dire où le changer : sans ça, l'admin cherche une
    panne. C'est la distinction qui manquait le 05/08."""
    with pytest.raises(LLMModeleIncompatibleError) as e:
        _traduire_echec_fournisseur(400, _FORMAT_REFUSE, "llama-3.3-70b-versatile")
    message = str(e.value)
    assert "llama-3.3-70b-versatile" in message
    assert "Paramètres" in message
    assert "json_schema" not in message


def test_document_trop_gros_pour_le_palier_du_compte():
    """Mesuré le 05/08 : la découpe d'un référentiel réclame ~49 000 tokens, l'offre gratuite de
    Groq en autorise 8 000 par minute → HTTP 413. Ni panne, ni mauvais modèle : réessayer et changer
    de modèle sont tous deux inutiles, le message doit donc conseiller autre chose."""
    corps = ('{"error":{"message":"Request too large ... tokens per minute (TPM): '
             'Limit 8000, Requested 49175","code":"rate_limit_exceeded"}}')
    with pytest.raises(LLMQuotaCompteError) as e:
        _traduire_echec_fournisseur(413, corps, "openai/gpt-oss-120b")
    message = str(e.value)
    assert "réessayez" not in message.lower()
    assert "fournisseur" in message.lower() or "abonnement" in message.lower()
    assert "TPM" not in message and "rate_limit" not in message


def test_trop_de_demandes_reste_un_429_metier():
    with pytest.raises(LLMRateLimitError):
        _traduire_echec_fournisseur(429, "rate limit exceeded", "peu importe")


def test_une_panne_serveur_est_traitee_comme_une_indisponibilite():
    for statut in (500, 502, 503):
        with pytest.raises(LLMIndisponibleError):
            _traduire_echec_fournisseur(statut, "gateway", "peu importe")


def test_un_statut_non_repertorie_n_est_pas_maquille():
    """On ne traduit QUE ce qu'on sait nommer. Un 404 ou un 401 ne doit pas devenir « service
    saturé » : un message rassurant mais faux est pire qu'un message technique."""
    assert _traduire_echec_fournisseur(404, "not found", "m") is None
    assert _traduire_echec_fournisseur(401, "unauthorized", "m") is None


def test_les_deux_situations_ne_donnent_pas_le_meme_conseil():
    """Le fond du sujet : saturé ≠ incompatible. Si les deux messages se ressemblaient, l'admin
    referait le même geste inutile."""
    with pytest.raises(LLMIndisponibleError) as sature:
        _traduire_echec_fournisseur(529, _OVERLOADED, "m")
    with pytest.raises(LLMModeleIncompatibleError) as incompatible:
        _traduire_echec_fournisseur(400, _FORMAT_REFUSE, "m")
    assert str(sature.value) != str(incompatible.value)
    assert "réessayez" in str(sature.value).lower()
    assert "réessayez" not in str(incompatible.value).lower()  # ici, réessayer ne sert à rien
