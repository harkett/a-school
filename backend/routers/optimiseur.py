import json
import re

from fastapi import APIRouter, Depends, HTTPException, Cookie
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import ToolUsageLog, User
from src.config import AI_MODEL, AI_PROVIDER
from backend.groq_client import call_groq

router = APIRouter()


class OptimiseRequest(BaseModel):
    sequence: str
    matiere: str
    niveau: str


class Probleme(BaseModel):
    type: str
    detail: str


class OptimiseResponse(BaseModel):
    sequence_optimisee: str
    problemes: list[Probleme]
    score: str
    avertissement: str | None = None


_PROMPT = """Tu es un expert en ingénierie pédagogique pour l'enseignement secondaire français (collège et lycée, 6e à Terminale).

Un enseignant de {matiere}, niveau {niveau}, te soumet une séquence pédagogique existante à optimiser.

Ta mission : analyser la séquence selon les 6 critères ci-dessous, identifier les problèmes présents, puis produire la version optimisée.

Les 6 critères d'analyse :
1. Rupture conceptuelle — une phase suppose une notion non encore construite dans la séquence
2. Surcharge cognitive — trop de notions nouvelles concentrées dans un temps trop court
3. Consigne ambiguë — formulation pouvant être mal interprétée par les élèves
4. Activité inefficace — exercice sans lien réel avec l'objectif pédagogique déclaré
5. Progression déséquilibrée — phases trop courtes ou trop longues, rythme inadapté
6. Ancrage mémoriel manquant — absence de consolidation avant la fin ou l'évaluation

Séquence soumise :
{sequence}

Format de réponse — JSON strict, rien d'autre autour :
{{
  "problemes": [
    {{"type": "Rupture conceptuelle", "detail": "description précise et concrète du problème détecté"}},
    {{"type": "Surcharge cognitive", "detail": "..."}}
  ],
  "sequence_optimisee": "# Séance : [titre]\n**Matière :** ... | **Niveau :** ... | **Durée :** ... min\n\n---\n\n## Phase 1 — [Nom] ([X] min)\n**Objectif :** ...\n**Déroulement :** ...\n**Organisation :** ...\n\n## Phase 2 — [Nom] ([X] min)\n...",
  "score": "Bon|Moyen|À revoir — X problème(s) détecté(s)",
  "avertissement": "Message optionnel si incohérence détectée — sinon ne pas inclure ce champ."
}}

Règles :
- N'inclure dans "problemes" que les critères réellement problématiques. Ignorer les critères sans problème.
- Si la séquence est déjà de bonne qualité, "problemes" est une liste vide [].
- La séquence optimisée conserve la structure générale du prof. Elle corrige les problèmes détectés sans tout réécrire de zéro.
- Le champ sequence_optimisee doit contenir le texte complet avec les vrais sauts de ligne (\\n) entre chaque phase — exactement le même format markdown que la séquence originale soumise.
- Si la séquence soumise ne correspond manifestement pas à la matière {matiere} (ex : contenu de Français soumis pour Mathématiques, exercice de sport soumis pour Philosophie), remplis le champ "avertissement" avec un message court et précis signalant l'incohérence. Sinon, n'inclus pas ce champ.
- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON."""


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


def _call_groq(prompt: str) -> str:
    return call_groq({
        "model": AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 6000,
        "temperature": 0,
        "response_format": {"type": "json_object"},
    })


def _parse_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    raise ValueError("Réponse non parseable en JSON")


@router.post("/optimize-sequence", response_model=OptimiseResponse)
def api_optimize(
    req: OptimiseRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    if not req.sequence.strip():
        raise HTTPException(400, "La séquence ne peut pas être vide.")

    prompt = _PROMPT.format(
        matiere=req.matiere,
        niveau=req.niveau,
        sequence=req.sequence.strip(),
    )

    try:
        if AI_PROVIDER == "groq":
            raw = _call_groq(prompt)
        else:
            from src.generator import generate
            raw = generate(prompt)
        data = _parse_json(raw)
    except ValueError:
        raise HTTPException(500, "Le modèle n'a pas retourné un résultat exploitable. Réessayez.")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    score_raw = data.get("score", "")
    score_label = score_raw.split(" — ")[0].strip() or None

    try:
        db.add(ToolUsageLog(user_email=email, user_id=db.query(User.id).filter(User.email == email).scalar(), tool="optimiseur", score_label=score_label))
        db.commit()
    except Exception:
        pass

    return OptimiseResponse(
        sequence_optimisee=data.get("sequence_optimisee", ""),
        problemes=[Probleme(**p) for p in data.get("problemes", [])],
        score=score_raw,
        avertissement=data.get("avertissement") or None,
    )
