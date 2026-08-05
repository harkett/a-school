# -*- coding: utf-8 -*-
r"""Le document doit rester EN TETE des prompts qui lisent un referentiel entier.

POURQUOI CA COMPTE. Six outils envoient le meme referentiel (~70 000 tokens) pour rendre trois
lignes. Anthropic ne facture que 10 % d'un PREFIXE deja vu — mais un prefixe, c'est le DEBUT de la
requete, au caractere pres. Tant que `{texte}` est en premiere position, les six outils partagent
le meme debut et cinq d'entre eux paient un dixieme. Qu'une seule phrase repasse devant, et le
prefixe commun disparait : la facture reprend son plein tarif, EN SILENCE.

C'est le genre de regression qu'aucun test fonctionnel n'attrape. Les reponses restent bonnes,
l'ecran affiche les memes resultats, les prompts se lisent aussi bien — seule la facture change,
et personne ne la regarde au moment ou l'on modifie un prompt.

CE FICHIER LIT LE REGISTRE, pas la base : `conftest` seme la base de test depuis le registre, donc
la base ne prouverait rien. Le registre est ce qu'une installation neuve recevra, et c'est aussi
ce que restaure le bouton « revenir au defaut » de l'ecran admin — un defaut qui remettrait
l'ancien ordre casserait le cache sans que rien ne le dise.

Ce test ne dit rien des prompts GENERES (le prompt de decoupe d'un couple, le prompt de matieres
d'un cycle) : ceux-la sont ecrits par l'IA puis valides par l'admin, et le moteur se protege
autrement — `_contenu_utilisateur` verifie que le prompt commence bien par le document et renonce
au cache sinon, sans jamais faire echouer la generation.

Lancer : docker compose exec backend python -m pytest tests/test_document_en_tete_des_prompts.py -q
"""
import inspect

import pytest

from backend.core.llm_prompts import PROMPTS
from backend.llm.generator import _contenu_utilisateur


# Les six outils qui envoient un referentiel ENTIER. La liste est courte et explicite : ajouter un
# outil qui lit un document complet demande de venir l'inscrire ici, donc d'y penser.
PROMPTS_A_DOCUMENT = (
    "decoupe_amont",
    "detecter_matieres",
    "detecter_types_activite",
    "verifier_couple",
    "detecter_couple",
    "suggerer_precisions_type",
)


@pytest.mark.parametrize("cle", PROMPTS_A_DOCUMENT)
def test_le_document_est_en_premiere_position(cle):
    texte = PROMPTS[cle]["default"]
    assert texte.startswith("{texte}"), (
        f"Le prompt « {cle} » ne commence plus par {{texte}} : le document n'est plus le préfixe "
        f"commun aux six outils, et le cache de prompt du fournisseur ne rapportera plus rien. "
        f"La facture d'un dépôt de référentiel repasse au plein tarif, sans que rien ne le dise.\n"
        f"Début actuel : {texte[:120]!r}"
    )


@pytest.mark.parametrize("cle", PROMPTS_A_DOCUMENT)
def test_aucune_variable_ne_passe_devant_le_document(cle):
    """Une variable placee avant le document serait pire qu'une phrase fixe : son contenu change a
    chaque appel, donc le prefixe ne se repeterait meme pas d'un appel a l'autre du MEME outil.
    C'etait le cas de {cycle}, {niveau}, {cycles_existants} et {label} avant le 05/08/2026."""
    texte = PROMPTS[cle]["default"]
    avant = texte[:texte.index("{texte}")]
    assert "{" not in avant, (
        f"Le prompt « {cle} » place une variable AVANT le document : {avant!r}. "
        f"Son contenu changeant à chaque appel, le préfixe ne se répète jamais et le cache du "
        f"fournisseur ne peut rien garder."
    )


# ---------------------------------------------------------------------------
# Le garde-fou du moteur : il renonce au cache, il ne casse jamais l'appel.
# ---------------------------------------------------------------------------

def test_deux_blocs_quand_le_prompt_commence_par_le_document():
    contenu = _contenu_utilisateur("DOCUMENT\n\nfais ceci", "DOCUMENT")
    assert isinstance(contenu, list) and len(contenu) == 2
    assert contenu[0]["text"] == "DOCUMENT"
    assert contenu[0]["cache_control"] == {"type": "ephemeral"}
    assert contenu[1]["text"] == "\n\nfais ceci"
    assert "cache_control" not in contenu[1], "Seul le préfixe se met en cache, pas la question."


def test_un_prompt_qui_ne_commence_pas_par_le_document_part_entier():
    """Le cas d'un prompt GENERE, ou modifie par l'admin : on perd l'economie, jamais l'appel."""
    contenu = _contenu_utilisateur("Lis ceci :\nDOCUMENT", "DOCUMENT")
    assert contenu == "Lis ceci :\nDOCUMENT"


def test_sans_prefixe_le_contenu_ne_change_pas():
    assert _contenu_utilisateur("un prompt", None) == "un prompt"
    assert _contenu_utilisateur("un prompt", "") == "un prompt"


def test_un_prompt_reduit_au_document_ne_se_coupe_pas():
    """Un bloc de texte vide est refuse par l'API : mieux vaut renoncer au cache que lever."""
    assert _contenu_utilisateur("DOCUMENT", "DOCUMENT") == "DOCUMENT"
    assert _contenu_utilisateur("DOCUMENT   \n", "DOCUMENT") == "DOCUMENT   \n"


def test_les_quatre_entrees_du_moteur_acceptent_le_prefixe():
    """`prefixe_cache` doit traverser TOUTES les portes, sinon l'economie depend de la voie prise
    (flux ou non) — une difference invisible a la lecture de l'appelant."""
    from backend.llm import generator
    for nom in ("generate", "generate_cached", "generate_stream"):
        params = inspect.signature(getattr(generator, nom)).parameters
        assert "prefixe_cache" in params, f"{nom}() ne transmet pas prefixe_cache."
