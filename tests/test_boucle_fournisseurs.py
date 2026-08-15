r"""LA BOUCLE — quand un fournisseur refuse, on essaie le suivant.

CE QUI CHANGE. `generate()` appelait UN fournisseur : s'il refusait, le professeur voyait un échec
et devait recliquer, alors que deux autres fournisseurs raccordés attendaient avec leurs clés. Il
reçoit maintenant une LISTE (`secours`) et la descend jusqu'au premier qui répond.

CE QUI NE CHANGE PAS, ET C'EST L'ESSENTIEL. Sans `secours`, le comportement est celui d'hier — un
appel, un fournisseur, la même erreur au même moment. C'est ce que vérifie le premier test, et
c'est le seul qui protège les vingt-six sites d'appel qui n'ont rien demandé à personne.

CE QU'ELLE NE FAIT PAS. Aucun compteur de quota, aucune lecture d'en-tête, aucune mémoire d'un
appel à l'autre : chaque appel repart du premier. Le refus est le seul signal.

Lancer : docker compose exec backend python -m pytest tests/test_boucle_fournisseurs.py -q
"""
import pytest

from backend.llm import generator as gen
from backend.llm.generator import (
    LLMCleRefuseeError, LLMDemandeInvalideError, LLMIndisponibleError,
    LLMRateLimitError, generate,
)

VOIES = [
    {"provider": "groq", "cle": "k1", "model": "m1", "contexte_max": 131072},
    {"provider": "anthropic", "cle": "k2", "model": "claude-sonnet-5", "contexte_max": 1000000},
    {"provider": "infomaniak", "cle": "k3", "model": "mistral3", "max_tokens": 5000,
     "contexte_max": 100000},
]


@pytest.fixture
def essais(monkeypatch):
    """Le mouchard sans aucun refus : tout réussit du premier coup."""
    return _mouchard(monkeypatch)


def _refuse(*erreurs):
    """Fabrique un `_appeler` qui lève l'erreur prévue pour chaque tentative, dans l'ordre.
    `None` = cette tentative-là réussit."""
    suite = list(erreurs)

    def faux(prompt, *, cle, fournisseur, model, max_tokens, **reste):
        e = suite.pop(0) if suite else None
        if e is not None:
            raise e
        return f"réponse de {fournisseur}"
    return faux


def _mouchard(monkeypatch, *issues):
    """Un `_appeler` qui NOTE chaque tentative avant de rendre l'issue prévue (`None` = succès).
    Rend la liste des tentatives : fournisseur, clé, modèle, plafond de sortie et rang."""
    vus, suite = [], list(issues)

    def faux(prompt, *, cle, fournisseur, model, max_tokens, **reste):
        vus.append({"fournisseur": fournisseur, "cle": cle, "model": model,
                    "max_tokens": max_tokens, "rang": gen._rang_courant.get()})
        e = suite.pop(0) if suite else None
        if e is not None:
            raise e
        return f"réponse de {fournisseur}"

    monkeypatch.setattr(gen, "_appeler", faux)
    return vus


def test_sans_secours_le_comportement_est_celui_d_hier(essais):
    """LE GARDE-FOU. Vingt-six sites d'appel ne passent pas de liste : ils doivent recevoir
    exactement ce qu'ils recevaient — un seul appel, et pas de rang inventé au journal."""
    texte = generate("bonjour", cle="k1", provider="groq", model="m1", max_tokens=100)
    assert texte == "réponse de groq"
    assert len(essais) == 1, "un fournisseur sans secours ne doit être appelé qu'une fois"
    assert essais[0]["rang"] is None, (
        "sans liste, le rang doit rester vide : écrire « 1 » inventerait une cascade qui n'a pas eu lieu"
    )


def test_le_premier_qui_repond_arrete_la_boucle(essais):
    """Le rang 1 répond : les suivants ne sont jamais appelés — ni facturés."""
    generate("bonjour", cle="k1", provider="groq", model="m1", max_tokens=100, voies_fournisseurs=VOIES)
    assert [e["fournisseur"] for e in essais] == ["groq"]


def test_un_refus_fait_passer_au_suivant(monkeypatch):
    """429 chez le premier : le second répond, et c'est SA réponse que reçoit le professeur."""
    monkeypatch.setattr(gen, "_appeler", _refuse(LLMRateLimitError("quota")))
    texte = generate("bonjour", cle="k1", provider="groq", model="m1", max_tokens=100,
                     voies_fournisseurs=VOIES)
    assert texte == "réponse de anthropic"


def test_le_secours_appelle_SON_modele_avec_SA_cle(monkeypatch):
    """`mistral3` n'existe pas chez Anthropic, et la clé d'Anthropic n'ouvre pas Infomaniak :
    chaque voie porte les siens. Reprendre ceux du premier ferait échouer tous les secours."""
    vus = _mouchard(monkeypatch, LLMRateLimitError("quota"), None)
    generate("bonjour", cle="k1", provider="groq", model="m1", max_tokens=100, voies_fournisseurs=VOIES)
    assert vus[1]["fournisseur"] == "anthropic"
    assert vus[1]["cle"] == "k2", "le secours doit être appelé avec SA clé"
    assert vus[1]["model"] == "claude-sonnet-5", "le secours doit être appelé avec SON modèle"


def test_le_rang_est_ecrit_pour_chaque_tentative(monkeypatch):
    """C'est lui qui permettra de compter ce que la boucle a rattrapé : une réponse de rang 2 est
    une génération que l'ancienne version aurait perdue."""
    rangs = []

    def faux(prompt, *, cle, fournisseur, model, max_tokens, **reste):
        rangs.append(gen._rang_courant.get())
        if len(rangs) < 3:
            raise LLMIndisponibleError("panne")
        return "ok"

    monkeypatch.setattr(gen, "_appeler", faux)
    generate("bonjour", cle="k1", provider="groq", model="m1", max_tokens=100, voies_fournisseurs=VOIES)
    assert rangs == [1, 2, 3]


def test_une_demande_mal_formee_arrete_tout_de_suite(monkeypatch):
    """Elle ne vient pas du fournisseur mais de nous : les autres recevraient la même demande et
    répondraient la même chose. Insister brûlerait la liste en facturant chaque essai."""
    appels = []

    def faux(prompt, *, cle, fournisseur, model, max_tokens, **reste):
        appels.append(fournisseur)
        raise LLMDemandeInvalideError("mal formée")

    monkeypatch.setattr(gen, "_appeler", faux)
    with pytest.raises(LLMDemandeInvalideError):
        generate("bonjour", cle="k1", provider="groq", model="m1", max_tokens=100, voies_fournisseurs=VOIES)
    assert appels == ["groq"], "un défaut de notre demande ne doit pas faire le tour des fournisseurs"


def test_tous_refusent_le_prof_voit_la_derniere_erreur(monkeypatch):
    """Ni erreur inventée, ni message plus alarmant : ce qu'il aurait vu sans la liste."""
    monkeypatch.setattr(gen, "_appeler", _refuse(
        LLMRateLimitError("quota"), LLMIndisponibleError("panne"), LLMCleRefuseeError("clé morte")))
    with pytest.raises(LLMCleRefuseeError):
        generate("bonjour", cle="k1", provider="groq", model="m1", max_tokens=100, voies_fournisseurs=VOIES)


def test_la_cle_morte_d_un_fournisseur_ne_perd_pas_la_generation(monkeypatch):
    """Une clé révoquée est un problème d'exploitation, pas une raison de refuser le travail du
    professeur tant qu'un autre fournisseur répond."""
    monkeypatch.setattr(gen, "_appeler", _refuse(LLMCleRefuseeError("401")))
    assert generate("bonjour", cle="k1", provider="groq", model="m1", max_tokens=100,
                    voies_fournisseurs=VOIES) == "réponse de anthropic"


# ── Le SDK d'Anthropic ne doit plus réessayer tout seul ─────────────────────────────────────────

def test_le_client_anthropic_ne_retente_pas_de_lui_meme():
    """Par défaut, le SDK retente DEUX fois avant de rendre la main. Avec une liste de fournisseurs,
    c'est trois appels et plusieurs secondes perdus avant même de savoir qu'il faut passer au
    suivant — la jauge tourne pendant ce temps devant le professeur.

    Lu dans le code des deux voies (flux et hors flux) : un client construit sans ce réglage
    réintroduirait l'attente sans que rien ne le signale."""
    import inspect
    for fn in (gen._anthropic, gen._anthropic_stream):
        src = inspect.getsource(fn)
        debut = src.index("anthropic.Anthropic(")
        appel = src[debut:debut + 400]
        assert "max_retries=0" in appel, (
            f"{fn.__name__} construit son client sans max_retries=0 : le SDK réessaiera deux fois "
            "avant de laisser la liste avancer."
        )


# ── La liste sort du CATALOGUE, pas d'un élu ────────────────────────────────────────────────────
#
# CE QUI ÉTAIT FAUX. La première version construisait la liste autour de `settings.ai_provider` :
# l'élu en tête, le catalogue derrière. L'ordre du catalogue ne décidait donc de rien, et le
# 15/08/2026 cela plaçait Infomaniak (payant) AVANT Groq (gratuit) — l'exact contraire du but du
# chantier. Ces deux tests tiennent la règle : le gratuit d'abord, parce qu'il est premier au
# catalogue, et pour aucune autre raison.

def test_la_liste_suit_l_ordre_du_catalogue(monkeypatch):
    """Et non un réglage séparé. L'administrateur range le catalogue ; il ne sacre personne."""
    from backend.systeme.admin import liste_fournisseurs
    from backend.core.database import SessionLocal
    from backend.core.models_db import AiFournisseur

    db = SessionLocal()
    try:
        attendu = [f.code for f in db.query(AiFournisseur)
                     .filter(AiFournisseur.actif.is_(True))
                     .order_by(AiFournisseur.ordre.asc(), AiFournisseur.code.asc()).all()]
        obtenu = [v["provider"] for v in liste_fournisseurs(db)]
        # Un fournisseur sans clé ou sans modèle est écarté : l'obtenu est un SOUS-ENSEMBLE de
        # l'attendu, mais dans le même ordre.
        assert obtenu == [c for c in attendu if c in obtenu], (
            f"la liste {obtenu} ne suit pas l'ordre du catalogue {attendu}"
        )
    finally:
        db.close()


def test_chaque_entree_porte_son_modele_et_sa_cle(monkeypatch):
    """Reprendre le modèle du premier pour appeler le second, c'est le faire échouer à coup sûr :
    `mistral3` n'existe pas chez Anthropic. Le test sème ses propres fournisseurs — la base de test
    est vide, et dépendre d'un catalogue qu'on n'a pas posé rend le test muet le jour où il
    change."""
    from backend.systeme.admin import liste_fournisseurs
    from backend.core.database import SessionLocal
    from backend.core.models_db import AiFournisseur, AiModele

    monkeypatch.setenv("CLE_A", "aaa")
    monkeypatch.setenv("CLE_B", "bbb")
    db = SessionLocal()
    try:
        db.query(AiModele).filter(AiModele.fournisseur.in_(("zz_a", "zz_b", "zz_c"))).delete()
        db.query(AiFournisseur).filter(AiFournisseur.code.in_(("zz_a", "zz_b", "zz_c"))).delete()
        db.add_all([
            AiFournisseur(code="zz_a", label="A", actif=True, ordre=1, cle_env="CLE_A"),
            AiFournisseur(code="zz_b", label="B", actif=True, ordre=2, cle_env="CLE_B",
                          max_tokens=5000),
            # Sans clé dans le .env : doit être écarté en silence, pas faire échouer la liste.
            AiFournisseur(code="zz_c", label="C", actif=True, ordre=3, cle_env="CLE_ABSENTE"),
        ])
        db.add_all([
            AiModele(fournisseur="zz_a", modele="mod-a", label="A", actif=True, recommande=True,
                     contexte_max=100000),
            AiModele(fournisseur="zz_b", modele="mod-b", label="B", actif=True, recommande=True),
        ])
        db.commit()

        voies = {v["provider"]: v for v in liste_fournisseurs(db) if v["provider"].startswith("zz_")}
        assert list(voies) == ["zz_a", "zz_b"], "l'ordre du catalogue n'est pas respecté, ou le fournisseur sans clé n'a pas été écarté"
        assert voies["zz_a"]["cle"] == "aaa" and voies["zz_a"]["model"] == "mod-a"
        assert voies["zz_b"]["cle"] == "bbb" and voies["zz_b"]["model"] == "mod-b"
        # Faute de plafond sur le modèle, celui du fournisseur s'applique — les 5 000 d'Infomaniak.
        assert voies["zz_b"]["max_tokens"] == 5000
    finally:
        db.query(AiModele).filter(AiModele.fournisseur.in_(("zz_a", "zz_b", "zz_c"))).delete()
        db.query(AiFournisseur).filter(AiFournisseur.code.in_(("zz_a", "zz_b", "zz_c"))).delete()
        db.commit()
        db.close()


def test_sans_liste_le_moteur_appelle_ce_qu_on_lui_donne(monkeypatch):
    """Le mode long de la découpe appelle sans base : il passe son fournisseur tout résolu, et le
    moteur doit l'appeler tel quel plutôt que de chercher une liste qui n'existe pas."""
    vus = _mouchard(monkeypatch)
    generate("x", cle="kk", provider="infomaniak", model="mistral3", max_tokens=10,
             voies_fournisseurs=[])
    assert [v["fournisseur"] for v in vus] == ["infomaniak"]
    assert vus[0]["cle"] == "kk"


# ── Le plafond de sortie : on BORNE, on ne remplace pas ─────────────────────────────────────────

def test_le_plafond_du_fournisseur_ne_devient_pas_une_consigne(monkeypatch):
    """CE QUI ÉTAIT FAUX. La voie portait le plafond du fournisseur (5 000 chez Infomaniak) et il
    ÉCRASAIT la demande de l'outil. Un outil réglé sur 300 tokens en recevait 5 000 dès que la
    boucle passait chez lui : la borne du fournisseur devenait une consigne, et les réglages de
    longueur de l'admin étaient ignorés sans que rien ne le dise."""
    vus = _mouchard(monkeypatch, LLMRateLimitError("q"), LLMRateLimitError("q"), None)
    generate("x", cle="k1", provider="groq", model="m1", max_tokens=300,
             voies_fournisseurs=VOIES)
    chez_infomaniak = vus[2]
    assert chez_infomaniak["fournisseur"] == "infomaniak"
    assert chez_infomaniak["max_tokens"] == 300, (
        f"{chez_infomaniak['max_tokens']} envoyé alors que l'outil en demandait 300 : le plafond "
        "du fournisseur a écrasé la demande au lieu de la borner."
    )


def test_la_demande_reste_bornee_par_le_fournisseur(monkeypatch):
    """L'inverse doit rester vrai : demander 60 000 à Infomaniak le ferait refuser (422)."""
    vus = _mouchard(monkeypatch, LLMRateLimitError("q"), LLMRateLimitError("q"), None)
    generate("x", cle="k1", provider="groq", model="m1", max_tokens=60000,
             voies_fournisseurs=VOIES)
    assert vus[2]["max_tokens"] == 5000
