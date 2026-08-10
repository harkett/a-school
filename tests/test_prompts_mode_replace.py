r"""Le registre dit COMMENT chaque prompt est consommé — et la validation en tient compte.

CE QUE CES TESTS PROUVENT, et pourquoi ils existent. Trois prompts vivaient HORS du registre :

  - `prompt_meta_decoupe` — lu à chaque génération d'un prompt de découpe ; ses seules portes
    étaient GET/PUT /admin/referentiels/meta-prompt, qu'AUCUN écran n'appelait — et dont le PUT
    écrivait la ligne SANS valider (supprimées le 02/08, cf. les deux derniers tests) ;
  - `prompt_verif_decoupe` — lu à chaque découpe lui aussi, et AUCUNE route ne permettait de le
    corriger. Ni écran, ni endpoint : semé une fois, puis intouchable ;
  - `prompt_gabarit_type` — il FABRIQUE le prompt de chaque couple×type au coche, et il n'avait
    même pas de ligne en base (seulement un repli code). S'il était mauvais, la faute tombait
    chez le PROF au moment de générer, alors que l'auteur du texte est l'admin.

Hors registre, ils échappaient à tout : l'écran Prompts ne les voyait pas, `valider_prompt` ne
les gardait pas, et rien ne vérifiait qu'une base neuve les contenait.

CE QUI A CHANGÉ DEPUIS (08 puis 10/08/2026). Les QUATRE méta-prompts — découpe, matières, types,
précisions — ont quitté `settings` ET le registre : ils vivent maintenant SUR LE RÉFÉRENTIEL, un
texte par diplôme (`referentiels.prompt_meta_*`, migration d9e4b7a2c6f1). Un méta-prompt lit un
document pour écrire le prompt qui le lira ; un gabarit commun à tous les diplômes n'a pas de
sens. Leur garde-fou n'a pas disparu, il a déménagé avec eux : les routes
`POST /admin/referentiels/prompt-meta-*` refusent un texte sans {document} (dernier test).
Restent ici les deux prompts réellement GÉNÉRIQUES : `verif_decoupe` et `gabarit_type`.

Ils ne pouvaient pas y entrer tels quels : leur texte CASSE `.format()` — c'est mesuré, pas
supposé (`test_leur_texte_reel_casse_bien_format` ci-dessous). C'est normal : ils DÉCRIVENT un
autre prompt, donc leurs accolades sont du texte à préserver. D'où le champ `mode` : en
« replace », on vérifie la PRÉSENCE des repères et on n'appelle jamais `.format()`.

Lancer : docker compose exec backend python -m pytest tests/test_prompts_mode_replace.py -q
"""
import pytest

# engine / SessionLocal redirigés vers PostgreSQL (aschool_test) par conftest.py — JAMAIS SQLite
import backend.core.database as dbmod

from backend.core.llm_prompts import PROMPTS
from backend.core.models_db import Setting
from backend.main import app
from backend.systeme.admin import _make_admin_token, get_prompts_settings, valider_prompt
from fastapi.testclient import TestClient

# Les prompts du REGISTRE en mode « replace ». Les quatre méta-prompts en sont sortis le
# 10/08/2026 avec leur entrée au registre : ils sont portés par chaque référentiel, et leur
# repère {document} est exigé par la route qui les écrit, pas par `valider_prompt`.
EN_REPLACE = ("verif_decoupe", "gabarit_type")


def _admin():
    c = TestClient(app)
    c.cookies.set("aschool_admin", _make_admin_token())
    return c


# ── Le champ lui-même ────────────────────────────────────────────────────────────────────

def test_le_mode_declare_est_toujours_l_un_des_deux_connus():
    """Un mode inventé passerait silencieusement pour « format » (c'est le défaut du `.get`) :
    le prompt serait alors validé par une règle qui n'est pas la sienne."""
    inconnus = {cle: meta["mode"] for cle, meta in PROMPTS.items()
                if meta.get("mode", "format") not in ("format", "replace")}
    assert not inconnus, f"Modes inconnus au registre : {inconnus}"


def test_seuls_ces_prompts_sont_en_replace():
    """Liste GELÉE. Passer un prompt en « replace » lui retire le contrôle `.format()` : ça se
    décide, ça ne se glisse pas. Ce test tombe dans les deux sens."""
    reels = tuple(sorted(cle for cle, meta in PROMPTS.items()
                         if meta.get("mode") == "replace"))
    assert reels == tuple(sorted(EN_REPLACE))


# ── Le fait mesuré qui justifie tout le reste ────────────────────────────────────────────

def test_le_prompt_de_critique_casse_vraiment_format():
    """Première raison d'être du mode, et la plus nette : son texte réel LÈVE. `verif_decoupe`
    fait relire à l'IA le prompt qu'elle vient d'écrire, et impose la sortie {"unites":[…]} :
    `.format()` prend ces accolades pour des repères — mesuré, pas supposé. La règle « format »
    refuserait donc son texte LÉGITIME."""
    meta = PROMPTS["verif_decoupe"]
    with pytest.raises((KeyError, IndexError, ValueError)):
        meta["default"].format(**{ph: "x" for ph in meta["placeholders"]})


def test_le_gabarit_a_besoin_du_mode_pour_une_AUTRE_raison():
    """Le gabarit, lui, ne casse pas `.format()` : ses quatre accolades sont ses quatre repères.
    Son mode ne vient pas de la validation mais de la CONSOMMATION — au coche d'un type, on ne
    remplit QUE {label} et {niveau} ; {texte} et {referentiel} doivent rester intacts pour la
    génération du prof. Un `.format()` global les mangerait ; un `.format()` partiel lève.
    C'est exactement pourquoi `_generer_prompt_type` procède par `replace` ciblés."""
    gabarit = PROMPTS["gabarit_type"]["default"]

    # Formater les quatre « marche » — et c'est bien le problème : les deux derniers repères,
    # que le prof doit encore remplir, ont disparu du texte produit.
    tout_rempli = gabarit.format(label="x", niveau="y", texte="z", referentiel="w")
    assert "{texte}" not in tout_rempli and "{referentiel}" not in tout_rempli

    # Et n'en formater que deux est impossible : `.format()` exige tous les repères.
    with pytest.raises(KeyError):
        gabarit.format(label="x", niveau="y")

    # La voie réellement utilisée garde les deux autres pour la génération.
    produit = gabarit.replace("{label}", "Compréhension").replace("{niveau}", "6e")
    assert "{texte}" in produit and "{referentiel}" in produit
    assert "{label}" not in produit and "{niveau}" not in produit


def test_leur_texte_reel_passe_la_validation():
    """Le corollaire : la règle « format » les refuserait, la règle « replace » les accepte.
    Un garde-fou qui refuse le texte légitime ne garde rien, il bloque."""
    for cle in EN_REPLACE:
        assert valider_prompt(cle, PROMPTS[cle]["default"]) is None, (
            f"Le texte réel de « {cle} » est refusé par son propre garde-fou."
        )


# ── Ce que le mode replace garde quand même ─────────────────────────────────────────────

def test_un_repere_manquant_reste_refuse_en_mode_replace():
    """« replace » n'est pas « on ne vérifie plus rien » : le repère est la seule garantie que
    la valeur atteindra le modèle. Sans {prompt}, l'IA relirait le vide."""
    err = valider_prompt("verif_decoupe", "Relis ce prompt et dis ce qui cloche.")
    assert err is not None and "{prompt}" in err


def test_le_gabarit_exige_ses_quatre_reperes():
    """{label} et {niveau} sont remplis au coche ; {texte} et {referentiel} doivent SURVIVRE
    jusqu'à la génération du prof. Il manque l'un des quatre = le prompt produit est cassé."""
    complet = "Type « {label} » en {niveau}. Idée : {texte}. Programme : {referentiel}"
    assert valider_prompt("gabarit_type", complet) is None
    for absent in ("{label}", "{niveau}", "{texte}", "{referentiel}"):
        err = valider_prompt("gabarit_type", complet.replace(absent, "…"))
        assert err is not None and absent in err, f"{absent} manquant n'est pas refusé."


def test_un_prompt_en_mode_format_garde_son_controle_d_accolades():
    """L'autre bord : le mode replace ne doit pas avoir relâché les prompts normaux."""
    err = valider_prompt("decoupe_amont", '{texte} — rends {"unites": []}')
    assert err is not None and "accolades" in err.lower()


# ── Le raccordement : ils sont VRAIMENT administrables maintenant ────────────────────────

def test_l_ecran_prompts_les_affiche():
    """La panne de départ : `prompt_verif_decoupe` était lu à chaque découpe et modifiable par
    rien. Il doit désormais apparaître dans la liste de l'écran, avec sa ligne en base."""
    with dbmod.SessionLocal() as db:
        rendu = get_prompts_settings(db=db, _=None)
    par_cle = {p["key"]: p for p in rendu["prompts"]}
    for cle in EN_REPLACE:
        assert cle in par_cle, f"« {cle} » n'est toujours pas dans l'écran Prompts."
        assert par_cle[cle]["en_base"], f"« {cle} » est au registre mais absent de la base."
        assert par_cle[cle]["categorie"] == "admin"


def test_ils_s_enregistrent_par_la_route_commune():
    """Le bout du bout : l'admin peut réellement les CORRIGER, et le garde-fou les tient."""
    c = _admin()
    bon = PROMPTS["verif_decoupe"]["default"] + "\n\n(Relecture affinée.)"
    r = c.put("/api/admin/prompts", json={"key": "verif_decoupe", "text": bon})
    assert r.status_code == 200, r.text
    with dbmod.SessionLocal() as db:
        assert db.query(Setting).filter(
            Setting.key == "prompt_verif_decoupe").one().value == bon

    # Et le repère reste obligatoire, même par cette porte-là.
    r = c.put("/api/admin/prompts",
              json={"key": "verif_decoupe", "text": "Relis ce prompt, merci."})
    assert r.status_code == 400
    assert "{prompt}" in r.json()["detail"]

    # On remet le texte de référence : les autres tests lisent cette base.
    c.put("/api/admin/prompts",
          json={"key": "verif_decoupe", "text": PROMPTS["verif_decoupe"]["default"]})


def test_le_gabarit_de_type_est_lu_en_base_pas_dans_le_code():
    """`_generer_prompt_type` lisait SETTING_DEFAULTS en repli : la base n'était donc pas la
    source, et le texte n'avait aucune porte. Il passe maintenant par `get_prompt`."""
    import inspect
    from backend.pedagogie import referentiels_admin
    source = inspect.getsource(referentiels_admin._generer_prompt_type)
    assert 'get_prompt(db, "gabarit_type")' in source
    assert "SETTING_DEFAULTS" not in source, (
        "Le repli code est revenu : la base cesse d'être la source, et l'écran Prompts ment."
    )


# ── La seconde porte, retirée le 02/08 ───────────────────────────────────────────────────

def test_l_ancienne_porte_non_gardee_du_meta_prompt_n_existe_plus():
    """`prompt_meta_decoupe` avait DEUX portes vers la même ligne de base.

    La seconde — GET/PUT /admin/referentiels/meta-prompt — n'avait aucun appelant et
    n'appelait pas `valider_prompt` : elle ne vérifiait que « non vide ». Un texte sans
    {document} y passait, et le méta-prompt ne recevait alors plus jamais le document à
    découper — exactement la panne que `valider_prompt` existe pour empêcher.

    On interroge en ADMIN authentifié exprès : un 403 dirait « la route est là, mais fermée ».
    C'est 404 qu'on veut — la route n'existe plus."""
    c = _admin()
    assert c.get("/api/admin/referentiels/meta-prompt").status_code == 404
    assert c.put("/api/admin/referentiels/meta-prompt",
                 json={"texte": "un texte sans le moindre repère"}).status_code == 404


def test_la_porte_du_referentiel_refuse_un_meta_prompt_sans_document():
    """Le corollaire, et la raison pour laquelle rien n'est perdu : le garde-fou a SUIVI les
    méta-prompts sur le référentiel, et il travaille AU NIVEAU HTTP — pas seulement dans
    `valider_prompt` pris à part. Rien n'est écrit, et la colonne reste telle qu'elle était.

    Cette porte a remplacé les deux précédentes : le réglage global (retiré le 08/08, migration
    d9e4b7a2c6f1) et l'entrée du registre (retirée le 10/08). C'est la seule aujourd'hui."""
    from backend.core.models_db import Cycle, Niveau, Referentiel

    with dbmod.SessionLocal() as db:
        cy = Cycle(nom="MP-Cycle", ordre=95)
        db.add(cy); db.commit(); db.refresh(cy)
        niv = Niveau(cycle_id=cy.id, nom="MP-Niveau", ordre=95)
        db.add(niv); db.commit(); db.refresh(niv)
        db.add(Referentiel(niveau_id=niv.id, nom_fixe="mp_ref", collection="mp_ref",
                           filtres=None, prompt_meta_decoupe="Lis {document} et rends un prompt."))
        db.commit()
        cycle_id, niveau_nom = cy.id, niv.nom

    r = _admin().post("/api/admin/referentiels/prompt-meta-decoupe",
                      json={"cycle_id": cycle_id, "niveau": niveau_nom,
                            "prompt": "Rédige un prompt de découpe, sans plus."})
    assert r.status_code == 422, r.text
    assert "{document}" in r.json()["detail"]

    with dbmod.SessionLocal() as db:
        ref = db.query(Referentiel).filter(Referentiel.niveau_id == niv.id).one()
        assert ref.prompt_meta_decoupe == "Lis {document} et rends un prompt.", (
            "un texte refusé a quand même été écrit sur le référentiel"
        )
