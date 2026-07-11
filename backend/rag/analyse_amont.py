"""Analyse amont d'un référentiel — par l'IA.

Applique la règle de `CLAUDE.md` « L'ambiguïté d'un référentiel se détecte par l'IA » :
on donne à l'IA les unités DÉJÀ découpées d'un document ; elle en DÉDUIT la règle de
classement (l'axe qui structure le document) et, pour chaque unité, dit si le classement est
clair (dans quelle(s) classe(s)) ou s'il y a un VRAI doute. L'IA propose, l'admin valide
(cap « aSchool n'invente rien »).

GÉNÉRIQUE : aucun axe (âge, matière, compétence…) n'est fourni ni codé ici — l'IA le découvre
en lisant. C'est du SOCLE, pas une fiche : rien de propre à un document.

Porte IA unique : `generate()` (src.generator) ; provider / modèle / prompt résolus EN BASE,
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
from src.generator import generate

_CLE_PROMPT = "analyse_amont"
_CLE_DECOUPE = "decoupe_amont"
# Clé EN BASE du méta-prompt (l'instruction générique qui demande à l'IA de GÉNÉRER le prompt de
# découpe d'un document). Aucun texte de prompt en dur : le code le LIT en base (Setting).
_CLE_META = "prompt_meta_decoupe"


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
    raise ValueError("Réponse non parseable en JSON")


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


def _trancher_par_titres(texte: str, titres: list[str]) -> list[dict]:
    """Tranche le TEXTE RÉEL aux lignes de titre rendues par l'IA — jamais réécrit par l'IA
    (cap « aSchool n'invente rien »). Pur, sans IA, sans base : testable seul.
    Chaque unité = du titre trouvé jusqu'au titre suivant (recherche séquentielle, ordre du
    document). Un titre introuvable est ignoré (on ne fabrique pas de frontière). Renvoie
    `[{"titre","texte"}]` dans l'ordre."""
    lignes = texte.split("\n")
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
    return generate(
        prompt,
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
    )
    data = parser_reponse(raw)
    titres: list[str] = []
    for u in data.get("unites", []):
        t = (u.get("titre") if isinstance(u, dict) else str(u)) or ""
        t = t.strip()
        if t:
            titres.append(t)
    return _trancher_par_titres(texte, titres)
