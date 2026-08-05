r"""Preuve — le prompt des PRECISIONS d'un type vit EN BASE, comme les 38 autres.

Ce texte etait ecrit EN DUR dans backend/rag/analyse_amont.py, en f-string, au milieu de la
fonction qui l'envoie au modele : le seul vrai prompt du projet hors du registre. L'admin ne
pouvait ni le lire, ni le corriger, ni savoir qu'il existait.

CE FICHIER COMPTE PLUS QUE LA MOYENNE, pour une raison precise : le seul appelant
(pedagogie/referentiels_admin.py, `_generer_precisions_ia`) ABSORBE toute exception et se
contente d'un warning — « la coche reussit quoi qu'il arrive ». Casser ce chemin ne provoque
donc aucune erreur visible : le bouton repond « ok » et rend zero precision. Sans test, la
panne serait silencieuse des deux cotes.

Ce qui est tenu ici :

  1. Le texte envoye au modele vient de la BASE, pas du code : on modifie la ligne en base et
     l'appel suit.
  2. Les trois reperes sont bien remplaces — aucun {label}, {niveau} ou {texte} n'atteint le
     modele en clair.
  3. max_tokens est LU EN BASE (get_max_tokens) et non fige a 2000.
  4. Le prompt absent en base leve, au lieu de retomber en douce sur un texte du code.

Lancer : docker compose exec backend python -m pytest tests/test_prompt_precisions_type_en_base.py -q
"""
import pytest

# engine / SessionLocal rediriges vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod
import backend.rag.analyse_amont as amont
from backend.core.llm_prompts import PROMPTS
from backend.core.models_db import Setting

CLE = "suggerer_precisions_type"
LABEL = "Activités écrites"
NIVEAU = "6e"
TEXTE = "Extrait du référentiel officiel de sixième."


@pytest.fixture
def db():
    """Une session, et surtout REFERMEE. Laissee ouverte, elle garde sa transaction et le
    TRUNCATE de nettoyage de conftest l'attend jusqu'a son plafond — le test passe, et c'est
    le suivant qui tombe sur une erreur de verrou qui ne parle de rien."""
    session = dbmod.SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def espion(monkeypatch):
    """Capture ce qui part vers le modele, sans rien envoyer. On remplace `generate` DANS le
    module qui l'appelle : c'est la porte reelle, pas une copie."""
    vu = {}

    def faux_generate(prompt, **kwargs):
        vu["prompt"] = prompt
        vu.update(kwargs)
        return '{"precisions": ["copie", "dictée"]}'

    monkeypatch.setattr(amont, "generate", faux_generate)
    monkeypatch.setattr(amont, "get_cle_texte", lambda db: "cle-de-test")
    monkeypatch.setattr(amont, "get_ai_provider", lambda db: "groq")
    monkeypatch.setattr(amont, "get_ai_model", lambda db: "modele-de-test")
    return vu


# Ces deux aides ouvrent leur PROPRE session et la referment : la session du test, elle, doit
# rester celle qu'on passe a la fonction, sans transaction d'ecriture ouverte a cote.
def _ecrire_reglage(cle: str, valeur: str):
    session = dbmod.SessionLocal()
    session.query(Setting).filter(Setting.key == cle).delete()
    session.add(Setting(key=cle, value=valeur))
    session.commit()
    session.close()


def _retirer_reglage(cle: str):
    session = dbmod.SessionLocal()
    session.query(Setting).filter(Setting.key == cle).delete()
    session.commit()
    session.close()


def test_la_cle_est_declaree_au_registre_avec_ses_trois_reperes():
    """Sans cette declaration, l'ecran d'administration des prompts ne l'affiche pas — et le
    garde-fou d'ecriture ne protege pas ses reperes."""
    assert CLE in PROMPTS, "le prompt n'est pas au registre : l'admin ne peut pas le voir"
    assert set(PROMPTS[CLE]["placeholders"]) == {"label", "niveau", "texte"}
    assert PROMPTS[CLE]["categorie"] == "admin"


def test_le_texte_envoye_au_modele_vient_de_la_base(espion, db):
    """LA preuve du point : on change la ligne EN BASE, et c'est elle qui part au modele. Tant
    que le texte etait en dur, cette modification n'avait aucun effet."""
    _ecrire_reglage(f"prompt_{CLE}",
                    "TEXTE ADMIN RETOUCHE — type {label}, niveau {niveau}.\n{texte}")

    amont.suggerer_precisions_type(LABEL, NIVEAU, TEXTE, db=db)

    assert "TEXTE ADMIN RETOUCHE" in espion["prompt"], (
        "le prompt envoye ne vient pas de la base — le texte en dur est encore utilise")


def test_les_trois_reperes_sont_remplaces(espion, db):
    """Un repere oublie part EN CLAIR dans la consigne du modele : il lit « {niveau} » au lieu
    de « 6e ». Ca ne leve pas, ca degrade la reponse en silence."""
    amont.suggerer_precisions_type(LABEL, NIVEAU, TEXTE, db=db)

    envoye = espion["prompt"]
    for repere in ("{label}", "{niveau}", "{texte}"):
        assert repere not in envoye, f"{repere} est parti tel quel au modele"
    assert LABEL in envoye and NIVEAU in envoye and TEXTE in envoye


def test_max_tokens_est_lu_en_base_et_non_fige(espion, db):
    """`max_tokens=2000` etait ecrit en dur. La raison tenait (300 coupait la reponse), pas le
    nombre : il devient reglable, avec le meme moule que les autres outils."""
    _ecrire_reglage(f"max_tokens_{CLE}", "3333")

    amont.suggerer_precisions_type(LABEL, NIVEAU, TEXTE, db=db)

    assert espion["max_tokens"] == 3333, (
        "max_tokens ne suit pas la base : la valeur est restee figee dans le code")


def test_sans_surcharge_on_retombe_sur_le_defaut_global(espion, db):
    """Comportement par defaut apres la correction : aucune surcharge -> defaut global, donc
    au-dessus des 2000 d'avant. La marge qui motivait le nombre en dur est preservee. Le defaut
    n'est pas ecrit ici : il se lit dans SETTING_DEFAULTS, sinon ce test tombe chaque fois que
    l'admin ou une migration le change — ce qui est arrive le 05/08 (2048 -> 8000)."""
    from backend.systeme.admin import SETTING_DEFAULTS

    _retirer_reglage(f"max_tokens_{CLE}")

    amont.suggerer_precisions_type(LABEL, NIVEAU, TEXTE, db=db)

    assert espion["max_tokens"] == int(SETTING_DEFAULTS["max_tokens_default"])
    assert espion["max_tokens"] >= 2000


def test_prompt_absent_en_base_leve_au_lieu_de_se_rattraper(espion, db):
    """Regle maison : une base vide se dit, elle ne se rattrape pas en douce. Le repli code a
    ete supprime a l'etape 9 lot C — cette cle doit suivre la meme regle que les 38 autres."""
    _retirer_reglage(f"prompt_{CLE}")

    with pytest.raises(Exception) as exc:
        amont.suggerer_precisions_type(LABEL, NIVEAU, TEXTE, db=db)
    assert "suggerer_precisions_type" in str(exc.value) or "absent en base" in str(exc.value)
