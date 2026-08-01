r"""Le prompt d'un couple×type est contrôlé À L'ÉCRITURE, comme tous les autres prompts.

CE QUE CES TESTS PROUVENT, et pourquoi ils existent. Tous les prompts du produit passent par
`valider_prompt` (admin.py) avant d'être écrits — sauf UN : celui du couple×type, écrit par
✎ Prompt de l'écran Référentiels, qui n'exigeait que « non vide ». Il finit pourtant dans
`modele.format(...)` (activites.py, api_generate étape 5), qui n'attrape que KeyError.

Deux pannes en découlaient, toutes deux SILENCIEUSES jusqu'au clic d'un enseignant :

  1. ACCOLADES CASSÉES — un exemple JSON non doublé, une accolade seule : `.format()` lève
     ValueError ou IndexError, non attrapées. L'admin a un 200 ; le prof a un 500 nu, sans
     message et sans incident enregistré (l'erreur survient AVANT le flux, donc hors du
     `try` qui crée les incidents). Rien, nulle part, ne dit ce qui s'est passé.

  2. `{texte}` OUBLIÉ — la plus traître : rien ne tombe. La génération marche, elle ignore
     simplement l'idée que l'enseignant a écrite. Le produit repose sur « la zone de texte
     mène » ; sans ce repère, elle ne mène plus rien, et personne ne l'apprend.

`_trous_du_prompt` SAVAIT déjà que ce texte peut avoir des accolades cassées — son
`except ValueError: return []` rendait « aucun besoin » sans rien signaler. Le garde-fou
manquait à l'autre bout.

Lancer : docker exec a-school-backend-1 python -m pytest tests/test_prompt_du_couple_valide_a_l_ecriture.py -q
"""
import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from backend.contenu.activites import valider_prompt_couple


def test_un_prompt_correct_passe():
    ok = ("Conçois une activité pour {niveau}.\n"
          "Idée du professeur : {texte}\n"
          "Programme officiel : {referentiel}")
    assert valider_prompt_couple(ok) is None


def test_les_parametres_saisis_par_le_prof_sont_acceptes():
    """{nb}, {sous_type}, {langue} sont légitimes : l'écran les demande si le prompt les nomme."""
    assert valider_prompt_couple(
        "{texte} — {nb} questions de type {sous_type} en {langue}, niveau {niveau}") is None


def test_sans_texte_c_est_refuse():
    """LA panne muette : sans ce repère, l'idée du prof n'entre jamais dans le prompt."""
    err = valider_prompt_couple("Conçois une activité pour {niveau} à partir de {referentiel}.")
    assert err is not None
    assert "{texte}" in err


def test_une_accolade_seule_est_refusee():
    """Le 500 nu, première forme : `.format()` lève ValueError, qu'api_generate n'attrape pas."""
    err = valider_prompt_couple("{texte} — rends la réponse entre accolades }")
    assert err is not None
    assert "accolades" in err.lower()


def test_un_exemple_json_non_double_est_refuse():
    """Le 500 nu, deuxième forme — la plus probable dans la vraie vie : l'admin colle un exemple
    JSON. `.format()` prend `"unites"` pour un repère et lève KeyError, qu'api_generate re-lève
    (activites.py:405, « placeholder inconnu = bug du prompt »). Autre branche du garde-fou,
    même conclusion : refusé avant d'écrire, avec le nom du fautif."""
    err = valider_prompt_couple('{texte} — rends du JSON : {"unites": []}')
    assert err is not None
    assert '"unites"' in err


def test_un_repere_inconnu_est_nomme_dans_le_message():
    """L'admin doit savoir LEQUEL, pas seulement que « ça ne va pas »."""
    err = valider_prompt_couple("{texte} pour la classe de {professeur}")
    assert err is not None
    assert "professeur" in err


def test_le_message_liste_les_reperes_disponibles():
    err = valider_prompt_couple("{texte} et {inconnu}")
    for repere in ("{texte}", "{niveau}", "{referentiel}", "{nb}", "{sous_type}", "{langue}"):
        assert repere in err, f"Le message n'offre pas {repere} à l'admin."


def test_la_route_refuse_avant_d_ecrire():
    """Le raccordement : la validation est bien branchée sur ✎ Prompt, pas seulement écrite."""
    import inspect
    from backend.pedagogie import referentiels_admin
    source = inspect.getsource(referentiels_admin.ecrire_prompt_type_couple)
    assert "valider_prompt_couple" in source, (
        "PUT /admin/referentiels/types-activite/prompt n'appelle plus le garde-fou : "
        "un prompt cassé redeviendrait écrivable, et le prof aurait le 500."
    )
    assert source.index("valider_prompt_couple") < source.index("l.prompt = body.prompt"), (
        "Le contrôle doit passer AVANT l'écriture : sinon le mauvais prompt est déjà en base."
    )
