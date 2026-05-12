from fastapi import APIRouter, Depends, HTTPException, Cookie
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.database import get_db
from backend.models_db import ToolUsageLog
from src.config import AI_API_KEY, AI_MODEL, AI_PROVIDER

router = APIRouter()

DUREES_VALIDES = {30, 45, 50, 55, 60, 90, 120}
MODES_VALIDES  = {"standard", "remediation"}


class SequenceRequest(BaseModel):
    theme: str
    matiere: str
    niveau: str
    duree: int
    mode: str = "standard"
    description_classe: str = ""


class SequenceResponse(BaseModel):
    resultat: str


_PROMPT_STANDARD = """Tu es un expert en ingénierie pédagogique pour l'enseignement secondaire français (collège et lycée, 6e à Terminale).

Un enseignant de {matiere}, niveau {niveau}, prépare une séance de {duree} minutes sur :
"{theme}"

Génère une séance pédagogique complète, cohérente et directement utilisable en classe.

Structure attendue : 5 à 6 phases couvrant exactement {duree} minutes.
Progression conseillée : Activation → Exploration/Découverte → Structuration/Formalisation → Entraînement → Ancrage/Consolidation.

Format de réponse — markdown strict :

# Séance : [titre court reprenant le thème]
**Matière :** {matiere} | **Niveau :** {niveau} | **Durée :** {duree} min

---

## Phase 1 — [Nom] ([X] min)
**Objectif :** [Ce que les élèves construisent ou réalisent]
**Déroulement :** [Description concrète — ce que fait le prof, ce que font les élèves]
**Organisation :** [Individuel / Binôme / Groupe / Collectif]

## Phase 2 — [Nom] ([X] min)
**Objectif :** ...
**Déroulement :** ...
**Organisation :** ...

[…continuer jusqu'à la dernière phase]

---

> *Séance générée par aSchool*

Règles absolues :
- La somme des durées des phases = exactement {duree} minutes
- Chaque phase a un rôle clair et distinct dans la progression
- Le déroulement est concret, précis et directement applicable en classe
- Le contenu est adapté au niveau {niveau} et à la matière {matiere}
- Aucune phase sans lien direct avec le thème "{theme}"
- Répondre uniquement en markdown, rien d'autre avant ni après le markdown"""


_PROMPT_REMEDIATION = """Tu es un expert en ingénierie pédagogique pour l'enseignement secondaire français.

Un enseignant de {matiere}, niveau {niveau}, décrit la situation de sa classe :
"{description_classe}"

La notion à retravailler est : "{theme}"
Durée disponible : {duree} minutes

Génère un scénario de remédiation créatif qui :
1. Exploite la situation décrite (difficultés, contexte, centres d'intérêt) comme point d'accroche
2. Cible précisément la notion à consolider
3. Propose une approche différente de la présentation initiale, plus engageante
4. Alterne entre phases courtes pour maintenir l'attention

Format de réponse — markdown strict :

# Remédiation : [titre court lié à la notion et au contexte]
**Matière :** {matiere} | **Niveau :** {niveau} | **Durée :** {duree} min

---

## Phase 1 — [Nom] ([X] min)
**Objectif :** ...
**Déroulement :** ...
**Organisation :** ...

[…continuer jusqu'à la dernière phase]

---

> *Séance de remédiation générée par aSchool*

Règles absolues :
- La somme des durées des phases = exactement {duree} minutes
- Le scénario exploite concrètement la situation décrite par l'enseignant
- Chaque phase a un rôle clair dans la reconsolidation de la notion "{theme}"
- Le contenu est adapté au niveau {niveau}
- Répondre uniquement en markdown, rien d'autre avant ni après le markdown"""


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


def _call_groq(prompt: str) -> str:
    import requests
    headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers, json=body, timeout=90,
    )
    if not r.ok:
        raise RuntimeError(f"Erreur Groq {r.status_code}: {r.text}")
    return r.json()["choices"][0]["message"]["content"]


@router.post("/generate-sequence", response_model=SequenceResponse)
def api_generate_sequence(
    req: SequenceRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)

    if not req.theme.strip():
        raise HTTPException(400, "Le thème ne peut pas être vide.")
    if req.duree not in DUREES_VALIDES:
        raise HTTPException(400, "Durée invalide.")
    if req.mode not in MODES_VALIDES:
        raise HTTPException(400, "Mode invalide.")
    if req.mode == "remediation" and not req.description_classe.strip():
        raise HTTPException(400, "La description de la classe est requise pour le mode remédiation.")

    try:
        if req.mode == "remediation":
            prompt = _PROMPT_REMEDIATION.format(
                matiere=req.matiere,
                niveau=req.niveau,
                duree=req.duree,
                theme=req.theme.strip(),
                description_classe=req.description_classe.strip(),
            )
        else:
            prompt = _PROMPT_STANDARD.format(
                matiere=req.matiere,
                niveau=req.niveau,
                duree=req.duree,
                theme=req.theme.strip(),
            )

        if AI_PROVIDER == "groq":
            resultat = _call_groq(prompt)
        else:
            from src.generator import generate
            resultat = generate(prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

    try:
        db.add(ToolUsageLog(user_email=email, tool="sequence"))
        db.commit()
    except Exception:
        pass

    return SequenceResponse(resultat=resultat)
