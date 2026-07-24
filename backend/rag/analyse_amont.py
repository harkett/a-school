"""Analyse amont d'un référentiel — par l'IA.

Applique la règle de `CLAUDE.md` « L'ambiguïté d'un référentiel se détecte par l'IA » :
on donne à l'IA les unités DÉJÀ découpées d'un document ; elle en DÉDUIT la règle de
classement (l'axe qui structure le document) et, pour chaque unité, dit si le classement est
clair (dans quelle(s) classe(s)) ou s'il y a un VRAI doute. L'IA propose, l'admin valide
(cap « aSchool n'invente rien »).

GÉNÉRIQUE : aucun axe (âge, matière, compétence…) n'est fourni ni codé ici — l'IA le découvre
en lisant. C'est du SOCLE, pas une fiche : rien de propre à un document.

Porte IA unique : `generate()` (backend.llm.generator) ; provider / modèle / prompt résolus EN BASE,
comme les autres outils (cf. `backend/analyse/ambiguites.py`). JSON déterministe (température 0).

État : brique ISOLÉE et testable — PAS encore branchée sur le découpage / l'ingestion
(pas 1 du chantier TRACKER 67 ; le remplacement de `_age_est_flou` vient dans un pas suivant).
"""
import json
import re

from sqlalchemy.orm import Session

from backend.systeme.admin import (
    get_ai_model, get_ai_provider, get_max_tokens, get_prompt, get_settings_dict,
)
from backend.llm.generator import generate

_CLE_PROMPT = "analyse_amont"
_CLE_DECOUPE = "decoupe_amont"
# Clé EN BASE du méta-prompt (l'instruction générique qui demande à l'IA de GÉNÉRER le prompt de
# découpe d'un document). Aucun texte de prompt en dur : le code le LIT en base (Setting).
_CLE_META = "prompt_meta_decoupe"
# Clé EN BASE du méta-prompt de CRITIQUE : l'IA relit le prompt de découpe qu'elle vient de
# générer et le corrige s'il viole le contrat (titres verbatim, JSON exact, pas de contenu,
# exclusions) AVANT de l'afficher à l'admin. Aucun texte en dur : lu en base (Setting).
_CLE_VERIF = "prompt_verif_decoupe"

# Schéma STRICT de la découpe (Structured Outputs) : le modèle ne renvoie QUE des titres.
# `additionalProperties: false` interdit tout champ en trop (ex. « contenu ») → la génération est
# contrainte token par token, la réponse reste petite : ni troncature, ni dépassement de délai. On
# ne lit de toute façon que le titre (`_trancher_par_titres` tranche le texte réel) : le contenu que
# le modèle produisait était du poids mort. GÉNÉRIQUE : aucun axe métier ici, juste la forme.
_SCHEMA_DECOUPE = {
    "type": "object",
    "properties": {
        "unites": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"titre": {"type": "string"}},
                "required": ["titre"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["unites"],
    "additionalProperties": False,
}


def formater_unites(unites: list[dict]) -> str:
    """Rend les unités en texte numéroté pour le prompt : `[i] titre` puis le texte de l'unité.
    Pur (aucune IA, aucune base) → testable seul. `titre` est optionnel."""
    blocs = []
    for i, u in enumerate(unites):
        titre = (u.get("titre") or "").strip()
        texte = (u.get("texte") or "").strip()
        entete = f"[{i}] {titre}" if titre else f"[{i}]"
        blocs.append(f"{entete}\n{texte}".strip())
    return "\n\n".join(blocs)


def parser_reponse(raw: str) -> dict:
    """Extrait le JSON de la réponse du modèle : direct, dans un bloc ```json … ```, ou 1er objet
    `{...}` trouvé. Lève `ValueError` si rien d'exploitable. Même tolérance que les autres outils."""
    for candidat in _candidats_json(raw):
        try:
            data = json.loads(candidat)
        except Exception:
            continue
        if isinstance(data, dict):
            return data
    raise ValueError(f"Réponse non parseable en JSON (longueur : {len(raw)}).")


def _candidats_json(raw: str):
    yield raw
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if m:
        yield m.group(1)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        yield m.group(0)


def analyser_unites(unites: list[dict], *, db: Session) -> dict:
    """Analyse amont d'un document via l'IA. `unites` = `[{"titre","texte"}]` déjà découpées.

    Retour : `{"regle": str, "unites": [{"index", "classe": [...], "doute": bool, "raison"}]}`
    — la règle de classement que l'IA a déduite + son verdict par unité (clair vs vrai doute).

    Lève `ValueError` si l'IA ne rend pas un JSON exploitable. Laisse remonter
    `LLMRateLimitError` (surcharge transitoire) et `RuntimeError` (panne fournisseur) — l'appelant
    les traduit. Prompt / provider / modèle lus EN BASE ; température 0 (sortie déterministe)."""
    prompt = get_prompt(db, _CLE_PROMPT).format(unites=formater_unites(unites))
    raw = generate(
        prompt,
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, _CLE_PROMPT),
        temperature=0,
        json_mode=True,
    )
    return parser_reponse(raw)


# L'épuration vit à UNE seule place : backend/rag/extraction.py (porte d'extraction unique).
# Ré-exposée ici car le tranchage la ré-applique (défensif : idempotent sur un texte déjà propre).
from backend.rag.extraction import _sans_numeros_de_page


def _trancher_par_titres(texte: str, titres: list[str]) -> list[dict]:
    """Tranche le TEXTE RÉEL aux lignes de titre rendues par l'IA — jamais réécrit par l'IA
    (cap « aSchool n'invente rien »). Pur, sans IA, sans base : testable seul.
    Chaque unité = du titre trouvé jusqu'au titre suivant (recherche séquentielle, ordre du
    document). Un titre introuvable est ignoré (on ne fabrique pas de frontière). Les numéros
    de page (lignes-nombres) sont écartés avant tranchage. Renvoie `[{"titre","texte"}]`
    dans l'ordre."""
    lignes = _sans_numeros_de_page(texte).split("\n")
    debuts: list[int] = []
    curseur = 0
    for t in titres:
        for i in range(curseur, len(lignes)):
            ligne = lignes[i].strip()
            if ligne and (ligne == t or t in lignes[i]):
                debuts.append(i)
                curseur = i + 1
                break
    unites: list[dict] = []
    for k, i in enumerate(debuts):
        fin = debuts[k + 1] if k + 1 < len(debuts) else len(lignes)
        bloc = "\n".join(lignes[i:fin]).strip()
        unites.append({"titre": lignes[i].strip(), "texte": bloc})
    return unites


def generer_prompt_decoupe(texte: str, *, db: Session) -> str:
    """L'IA GÉNÈRE le prompt de découpe adapté à CE document. On lui donne le méta-prompt (lu EN
    BASE, `Setting[prompt_meta_decoupe]`) + le texte brut du PDF ; elle rend un prompt de découpe
    sur mesure (texte libre). SOCLE, générique : aucun prompt écrit en dur, aucun axe métier codé.
    Le résultat sera stocké en base par couple et validé par l'admin avant usage. Lève si le
    méta-prompt n'est pas en base (jamais de découpe silencieuse sans amorce). Laisse remonter les
    pannes IA."""
    meta = (get_settings_dict(db).get(_CLE_META) or "").strip()
    if not meta:
        raise RuntimeError(
            f"Méta-prompt absent en base (Setting '{_CLE_META}'). L'admin doit le renseigner "
            f"avant de générer un prompt de découpe (cap « tout en base »)."
        )
    # Le document s'injecte au marqueur {document} du méta-prompt (distinct de {texte}, que le
    # méta-prompt demande au prompt GÉNÉRÉ de contenir). Ajouté en fin si le marqueur est absent.
    prompt = meta.replace("{document}", texte) if "{document}" in meta else f"{meta}\n\n{texte}"
    prompt_genere = generate(
        prompt,
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, "meta_decoupe"),
        temperature=0,
    ).strip()
    # Passe d'auto-critique AVANT de renvoyer : l'IA relit son propre prompt et corrige les défauts
    # grossiers (titre paraphrasé, contenu demandé, JSON non conforme, exclusion oubliée).
    return verifier_prompt_decoupe(prompt_genere, db=db)


def verifier_prompt_decoupe(prompt_genere: str, *, db: Session) -> str:
    """L'IA RELIT le prompt de découpe qu'elle vient de générer et le CORRIGE s'il viole le contrat,
    AVANT affichage à l'admin (lui épargne un aller-retour sur les défauts grossiers). Méta-prompt de
    critique lu EN BASE (`Setting[prompt_verif_decoupe]`), jamais en dur ; on n'injecte QUE le prompt
    (`{prompt}`) — pas le document : on juge la FORMULATION du prompt, pas sa sortie. Renvoie le
    prompt corrigé (ou inchangé si rien à redire). Lève si le méta-prompt de critique est absent.
    N'est PAS appelée par `regenerer_prompt_decoupe` : après une remarque admin, la remarque fait foi."""
    meta = (get_settings_dict(db).get(_CLE_VERIF) or "").strip()
    if not meta:
        raise RuntimeError(
            f"Méta-prompt de critique absent en base (Setting '{_CLE_VERIF}'). L'admin doit le "
            f"renseigner avant la génération d'un prompt de découpe (cap « tout en base »)."
        )
    p = meta.replace("{prompt}", prompt_genere) if "{prompt}" in meta else f"{meta}\n\nPROMPT À VÉRIFIER :\n{prompt_genere}"
    return generate(
        p,
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, "meta_decoupe"),
        temperature=0,
    ).strip()


def regenerer_prompt_decoupe(texte: str, *, prompt_actuel: str, remarques: str, db: Session) -> str:
    """L'IA CORRIGE le prompt de découpe à partir des REMARQUES de l'admin (français clair). Même
    méta-prompt lu EN BASE (`Setting[prompt_meta_decoupe]`) + texte du PDF, auxquels on joint le
    prompt actuel et les remarques ; l'IA rend un prompt de découpe RÉVISÉ (texte libre). SOCLE,
    générique : aucun prompt écrit en dur, aucun axe métier codé. Répétable à volonté (l'admin relit,
    remet une remarque, régénère). Lève si le méta-prompt n'est pas en base. Laisse remonter les
    pannes IA."""
    meta = (get_settings_dict(db).get(_CLE_META) or "").strip()
    if not meta:
        raise RuntimeError(
            f"Méta-prompt absent en base (Setting '{_CLE_META}'). L'admin doit le renseigner "
            f"avant de régénérer un prompt de découpe (cap « tout en base »)."
        )
    base = meta.replace("{document}", texte) if "{document}" in meta else f"{meta}\n\n{texte}"
    prompt = (
        f"{base}\n\n"
        f"PROMPT DE DÉCOUPE ACTUEL (à corriger) :\n{prompt_actuel}\n\n"
        f"REMARQUES DE L'ADMIN (à prendre en compte pour produire un NOUVEAU prompt) :\n{remarques}\n\n"
        f"Produis le PROMPT DE DÉCOUPE RÉVISÉ, et RIEN d'autre."
    )
    return generate(
        prompt,
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, "meta_decoupe"),
        temperature=0,
    ).strip()


def decouper_texte(texte: str, *, db: Session, prompt: str) -> list[dict]:
    """Découpe GÉNÉRIQUE d'un référentiel PAR L'IA, pilotée par le PROMPT VALIDÉ DU COUPLE (`prompt`,
    lu en base par l'appelant — jamais écrit en dur). On injecte le texte brut à la place du marqueur
    `{texte}` (ajouté en fin si absent), l'IA rend la liste ordonnée des lignes de titre ; le texte de
    chaque unité est ensuite TRANCHÉ dans le texte réel (`_trancher_par_titres`), jamais réécrit par
    l'IA. SOCLE : aucun axe (âge, matière…) codé. Laisse remonter les pannes IA. Renvoie
    `[{"titre","texte"}]`."""
    p = prompt.replace("{texte}", texte) if "{texte}" in prompt else f"{prompt}\n\nTEXTE BRUT :\n{texte}"
    raw = generate(
        p,
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, _CLE_DECOUPE),
        temperature=0,
        json_mode=True,
        schema=_SCHEMA_DECOUPE,
    )
    data = parser_reponse(raw)
    titres: list[str] = []
    for u in data.get("unites", []):
        t = (u.get("titre") if isinstance(u, dict) else str(u)) or ""
        t = t.strip()
        if t:
            titres.append(t)
    return _trancher_par_titres(texte, titres)


# Clé EN BASE du prompt de vérification du couple (cycle + niveau) — vérif n°1 au dépôt.
_CLE_COUPLE = "verifier_couple"


def _schema_couple() -> dict:
    """Sortie structurée de la vérif n°1. `correspond` = le document vise-t-il bien le couple
    déclaré ; `niveau_lu` = ce que l'IA lit dans le document ; `raison` = une phrase."""
    return {
        "type": "object",
        "properties": {
            "correspond": {"type": "boolean"},
            "niveau_lu": {"type": "string"},
            "raison": {"type": "string"},
        },
        "required": ["correspond", "niveau_lu", "raison"],
        "additionalProperties": False,
    }


def verifier_couple(texte: str, cycle: str, niveau: str, *, db: Session) -> dict:
    """Vérif n°1 au dépôt : l'IA lit le couple (cycle + niveau) visé par le DOCUMENT et le compare
    au couple DÉCLARÉ par l'admin. L'IA fait la comparaison sémantique (pas de string-matching) —
    on lui donne le couple déclaré + le texte, elle renvoie son verdict.

    Retour : `{"correspond": bool, "niveau_lu": str, "raison": str}`.
    Prompt / provider / modèle lus EN BASE ; température 0. Laisse remonter les pannes IA
    (l'appelant traduit). Lève `ValueError` si l'IA ne rend pas un JSON exploitable."""
    prompt = (get_prompt(db, _CLE_COUPLE)
              .replace("{cycle}", cycle)
              .replace("{niveau}", niveau)
              .replace("{texte}", texte))
    raw = generate(
        prompt,
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, _CLE_COUPLE),
        temperature=0,
        json_mode=True,
        schema=_schema_couple(),
    )
    data = parser_reponse(raw)
    return {
        "correspond": bool(data.get("correspond")),
        "niveau_lu": (data.get("niveau_lu") or "").strip(),
        "raison": (data.get("raison") or "").strip(),
    }


# Clé EN BASE du prompt de détection des matières — proposées au dépôt du PDF (proposition, pas
# une matière validée : l'admin coche ce qu'il garde).
_CLE_MATIERES = "detecter_matieres"


def _schema_matieres() -> dict:
    """Sortie structurée de la détection : `matieres` = tableau de noms. `additionalProperties:
    false` interdit tout champ en trop (réponse contrainte, petite, ni troncature ni dépassement)."""
    return {
        "type": "object",
        "properties": {
            "matieres": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["matieres"],
        "additionalProperties": False,
    }


def detecter_matieres(texte: str, *, db: Session) -> list[str]:
    """L'IA LIT le texte d'un référentiel et PROPOSE la liste des matières (disciplines / domaines)
    qu'il structure. Proposition seulement : l'admin coche ce qu'il ajoute (jamais une matière écrite
    d'office). L'IA reçoit AUSSI la table des matières actives (get, zéro copie) pour faire
    CORRESPONDRE le document avec l'existant : orthographe exacte de la table, et un intitulé qui
    regroupe plusieurs matières connues (ex. « Mathématiques et physique-chimie ») est séparé.
    Prompt / provider / modèle lus EN BASE ; température 0 (sortie déterministe). Renvoie
    les noms nettoyés, sans doublon (insensible à la casse), dans l'ordre lu. Liste vide si l'IA n'en
    lit aucune. Lève `ValueError` si l'IA ne rend pas un JSON exploitable. Laisse remonter les pannes
    IA (l'appelant traduit / absorbe)."""
    from backend.core.models_db import Matiere
    existantes = [nom for (nom,) in (db.query(Matiere.nom)
                                       .filter(Matiere.actif == True)
                                       .order_by(Matiere.ordre, Matiere.id).all())]
    prompt = (get_prompt(db, _CLE_MATIERES)
              .replace("{matieres_existantes}",
                       "\n".join(f"- {n}" for n in existantes) or "(aucune pour le moment)")
              .replace("{texte}", texte))
    raw = generate(
        prompt,
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, _CLE_MATIERES),
        temperature=0,
        json_mode=True,
        schema=_schema_matieres(),
    )
    data = parser_reponse(raw)
    noms: list[str] = []
    vus: set[str] = set()
    for m in data.get("matieres", []):
        nom = (m if isinstance(m, str) else str(m)).strip()
        if nom and nom.lower() not in vus:
            vus.add(nom.lower())
            noms.append(nom)
    return noms


# Clé EN BASE du prompt de détection du COUPLE (cycle + niveau) — dépôt « PDF d'abord » :
# l'IA propose, le serveur fait la correspondance avec les tables, l'admin dispose.
_CLE_DETECTER_COUPLE = "detecter_couple"


def _schema_detecter_couple() -> dict:
    """Sortie structurée de la détection du couple : `cycle_lu` / `niveau_lu` = ce que le document
    vise, repris à l'ORTHOGRAPHE EXACTE de la liste fournie quand ça correspond (sinon le nom lu).
    Chaîne vide = le document ne permet pas de le dire."""
    return {
        "type": "object",
        "properties": {
            "cycle_lu": {"type": "string"},
            "niveau_lu": {"type": "string"},
        },
        "required": ["cycle_lu", "niveau_lu"],
        "additionalProperties": False,
    }


def detecter_couple(texte: str, *, db: Session) -> dict:
    """Dépôt « PDF d'abord » : l'IA LIT le début du document et PROPOSE le couple (cycle + niveau).
    Elle reçoit l'arbre des cycles → niveaux EXISTANTS (get, zéro copie) pour faire CORRESPONDRE
    le document avec les tables : orthographe exacte de la liste quand ça correspond, sinon le nom
    lu dans le document. La CORRESPONDANCE finale (ids) est faite par l'APPELANT contre la base —
    l'IA lit, la base tranche. Prompt / provider / modèle lus EN BASE ; température 0. Lève
    `ValueError` si l'IA ne rend pas un JSON exploitable ; laisse remonter les pannes IA."""
    from backend.core.models_db import Cycle, Niveau
    lignes = []
    for c in db.query(Cycle).order_by(Cycle.ordre, Cycle.id).all():
        niveaux = [n.nom for n in (db.query(Niveau).filter(Niveau.cycle_id == c.id)
                                     .order_by(Niveau.ordre, Niveau.id).all())]
        lignes.append(f"- {c.nom} : {', '.join(niveaux) if niveaux else '(aucun niveau)'}")
    prompt = (get_prompt(db, _CLE_DETECTER_COUPLE)
              .replace("{cycles_existants}", "\n".join(lignes) or "(aucun cycle pour le moment)")
              .replace("{texte}", texte))
    raw = generate(
        prompt,
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, _CLE_DETECTER_COUPLE),
        temperature=0,
        json_mode=True,
        schema=_schema_detecter_couple(),
    )
    data = parser_reponse(raw)
    return {
        "cycle_lu": (data.get("cycle_lu") or "").strip(),
        "niveau_lu": (data.get("niveau_lu") or "").strip(),
    }


# Clé EN BASE du prompt de détection des TYPES D'ACTIVITÉ — proposés à partir des chunks du couple
# (proposition, pas une liaison validée : l'admin coche ce qu'il garde). Même patron que les matières.
_CLE_TYPES_ACTIVITE = "detecter_types_activite"


def _schema_types_activite() -> dict:
    """Sortie structurée de la détection : `types` = tableau de noms. `additionalProperties: false`
    interdit tout champ en trop (réponse contrainte, petite, ni troncature ni dépassement)."""
    return {
        "type": "object",
        "properties": {
            "types": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["types"],
        "additionalProperties": False,
    }


def detecter_types_activite(texte: str, *, db: Session) -> list[str]:
    """L'IA LIT le texte d'un référentiel et PROPOSE la liste des TYPES D'ACTIVITÉ (formats /
    modalités pédagogiques) qu'il met en œuvre. Proposition seulement : l'admin coche ce qu'il garde
    (jamais un type coché d'office). L'IA reçoit AUSSI le catalogue des types actifs (get, zéro
    copie) pour faire CORRESPONDRE le document avec l'existant — libellé exact du catalogue quand ça
    correspond, libellé du document sinon (même patron que `detecter_matieres`). Prompt / provider /
    modèle lus EN BASE ; température 0 (sortie déterministe). Renvoie les noms nettoyés, sans doublon
    (insensible à la casse), dans l'ordre lu. Liste vide si l'IA n'en lit aucun. Lève `ValueError`
    si l'IA ne rend pas un JSON exploitable. Laisse remonter les pannes IA (l'appelant traduit)."""
    from backend.core.models_db import ActiviteType
    existants = [lbl for (lbl,) in (db.query(ActiviteType.label)
                                      .filter(ActiviteType.actif == True)
                                      .order_by(ActiviteType.ordre, ActiviteType.id).all())]
    prompt = (get_prompt(db, _CLE_TYPES_ACTIVITE)
              .replace("{types_existants}",
                       "\n".join(f"- {n}" for n in existants) or "(aucun pour le moment)")
              .replace("{texte}", texte))
    raw = generate(
        prompt,
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=get_max_tokens(db, _CLE_TYPES_ACTIVITE),
        temperature=0,
        json_mode=True,
        schema=_schema_types_activite(),
    )
    data = parser_reponse(raw)
    noms: list[str] = []
    vus: set[str] = set()
    for m in data.get("types", []):
        nom = (m if isinstance(m, str) else str(m)).strip()
        if nom and nom.lower() not in vus:
            vus.add(nom.lower())
            noms.append(nom)
    return noms


def _schema_precisions_type() -> dict:
    """Sortie structurée : `precisions` = tableau de libellés. `additionalProperties: false` interdit tout
    champ en trop (réponse contrainte, petite, ni troncature ni dépassement)."""
    return {
        "type": "object",
        "properties": {"precisions": {"type": "array", "items": {"type": "string"}}},
        "required": ["precisions"],
        "additionalProperties": False,
    }


def suggerer_precisions_type(label: str, niveau: str, texte: str, *, db: Session) -> list[str]:
    """L'IA PROPOSE les PRÉCISIONS d'un type d'activité POUR CE NIVEAU, ancrées au référentiel. Une
    précision = une déclinaison concrète du type, RÉELLEMENT adaptée au niveau (ex. « Activités écrites » :
    « copie », « dictée » en primaire ; « dissertation », « mémoire » dans le supérieur). Même plomberie
    que `detecter_types_activite` : provider / modèle lus EN BASE, température 0 (déterministe), JSON
    contraint. Renvoie des libellés nettoyés, sans doublon (insensible à la casse), dans l'ordre rendu.
    Lève `ValueError` si l'IA ne rend pas un JSON exploitable (l'appelant absorbe)."""
    prompt = (
        f"Tu es un concepteur pédagogique.\n"
        f"Pour le type d'activité « {label} » enseigné au niveau « {niveau} », propose 3 à 6 PRÉCISIONS : "
        f"des déclinaisons concrètes de ce type, réellement adaptées à ce niveau (ni trop enfantines, ni "
        f"trop avancées).\n"
        f"Appuie-toi sur le référentiel officiel ci-dessous pour rester dans le programme :\n{texte}\n\n"
        f"Rends UNIQUEMENT des libellés courts (2 à 4 mots), en minuscules."
    )
    raw = generate(
        prompt,
        provider=get_ai_provider(db),
        model=get_ai_model(db),
        max_tokens=2000,   # marge large : 300 coupait la réponse (JSON tronqué → erreur → 0 précision)
        temperature=0,
        json_mode=True,
        schema=_schema_precisions_type(),
    )
    data = parser_reponse(raw)
    noms: list[str] = []
    vus: set[str] = set()
    for m in data.get("precisions", []):
        nom = (m if isinstance(m, str) else str(m)).strip()
        if nom and nom.lower() not in vus:
            vus.add(nom.lower())
            noms.append(nom)
    return noms


