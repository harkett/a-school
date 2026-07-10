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

from backend.systeme.admin import get_ai_model, get_ai_provider, get_max_tokens, get_prompt
from src.generator import generate

_CLE_PROMPT = "analyse_amont"


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
