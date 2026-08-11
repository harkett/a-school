import json
import re

from fastapi import APIRouter, Depends, HTTPException, Cookie
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.securite import comptes
from backend.core.catalogues import catalogue
from backend.core.database import get_db
from backend.core.models_db import AmbiguiteCritere, AmbiguiteExemple, ToolUsageLog, User
from backend.prof.profil import couple_de_travail
from backend.systeme.admin import (get_ai_model, get_ai_provider, get_cle_texte, get_max_tokens,
                                   get_retry_max, get_retry_wait_max, get_temperature, get_prompt)
from backend.llm.generator import generate, LLMRateLimitError

router = APIRouter()

# Le code du critère « à moi » : la SEULE valeur du catalogue dont le serveur connaisse le
# comportement (elle ouvre le champ de texte libre). Les six autres sont de la donnée pure —
# les renommer, les réordonner ou en ajouter un septième ne touche pas à ce fichier.
CODE_CRITERE_LIBRE = "autre"

# Le critère écrit par le prof est le seul endroit de l'écran où un utilisateur écrit DANS le
# prompt. Il y entre comme une donnée citée, jamais comme une consigne : borné en longueur
# (motif maison, cf. communication/feedback.py), ramené sur une ligne, et privé des guillemets
# qui lui permettraient de sortir de sa délimitation. Le cadrage du prompt dit le reste.
CRITERE_LIBRE_MAX = 200


class AmbigsRequest(BaseModel):
    texte: str
    criteres: list[str] = Field(default_factory=list)
    critere_libre: str | None = Field(default=None, max_length=CRITERE_LIBRE_MAX)


class Ambiguite(BaseModel):
    extrait: str
    type: str
    risque: str
    reformulation: str


class AmbigsResponse(BaseModel):
    ambiguites: list[Ambiguite]
    verdict: str


class CritereItem(BaseModel):
    code: str
    label: str
    description: str


def criteres_ambiguite(db: Session) -> list[AmbiguiteCritere]:
    return catalogue(db, AmbiguiteCritere, "critères d'ambiguïté")


def _aplatir(texte: str) -> str:
    """Le critère du prof, ramené à une donnée d'une seule ligne."""
    return " ".join(texte.replace('"', "").split())


@router.get("/ambiguites/criteres", response_model=list[CritereItem])
def api_criteres_ambiguite(
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Les critères proposés au prof — la MÊME source que celle sur laquelle le serveur
    refusera ou acceptera plus bas. L'écran ne connaît aucun de ces libellés."""
    _get_email(aschool_access)
    return [CritereItem(code=c.code, label=c.label, description=c.description)
            for c in criteres_ambiguite(db)]


# Prompt déplacé dans backend/core/llm_prompts.py (administrable en base, lu via get_prompt).


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = comptes.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


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


@router.get("/ambiguites/exemple")
def api_exemple_ambiguites(
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """L'énoncé d'exemple du couple du prof — écrit d'avance par l'admin, JAMAIS généré ici.

    `disponible: false` quand ce couple n'a pas encore le sien : l'écran cache alors son bouton
    plutôt que d'en proposer un qui répondrait « pas d'exemple ». On n'invente rien."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")

    # Le couple de travail s'il est posé, sinon le profil — même règle que l'analyse, mais on a
    # besoin de la CLÉ ici, pas du libellé.
    matiere_id = (user.travail_matiere_id
                  if (user.travail_matiere_id and user.travail_niveau_id)
                  else user.subject_id)
    if not matiere_id:
        return {"disponible": False, "texte": ""}

    ligne = (db.query(AmbiguiteExemple)
               .filter(AmbiguiteExemple.matiere_id == matiere_id,
                       AmbiguiteExemple.actif.is_(True)).first())
    if not ligne or not ligne.texte.strip():
        return {"disponible": False, "texte": ""}
    return {"disponible": True, "texte": ligne.texte}


@router.post("/detect-ambiguites", response_model=AmbigsResponse)
def api_detect_ambiguites(
    req: AmbigsRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    if not req.texte.strip():
        raise HTTPException(400, "L'énoncé ne peut pas être vide.")

    # Couple résolu EN BASE (couple_de_travail, décision 25/07) — l'écran n'envoie plus
    # matière/niveau, le serveur ne fait plus confiance au corps de la requête.
    matiere, niveau, _ajuste = couple_de_travail(db, user)
    if not matiere or not niveau:
        raise HTTPException(400, "Votre profil n'a pas encore de matière et de niveau — complétez Mon profil avant de lancer l'analyse.")

    # Ce que le prof a coché — validé CONTRE LA TABLE, pas contre une liste écrite ici. L'écran
    # grise déjà son bouton tant que rien n'est coché ; le serveur ne s'appuie pas là-dessus.
    connus = {c.code: c for c in criteres_ambiguite(db)}
    demandes = [connus[code] for code in dict.fromkeys(req.criteres) if code in connus]
    if not demandes:
        raise HTTPException(400, "Cochez au moins un type d'ambiguïté à rechercher.")
    inconnus = [c for c in req.criteres if c not in connus]
    if inconnus:
        raise HTTPException(400, "Un des types demandés n'existe pas (ou n'est plus proposé). Rechargez la page.")

    libre = _aplatir(req.critere_libre or "")
    if any(c.code == CODE_CRITERE_LIBRE for c in demandes) and not libre:
        raise HTTPException(400, "Vous avez coché « Autre » : écrivez ce qu'aSchool doit vérifier, ou décochez la case.")
    if not any(c.code == CODE_CRITERE_LIBRE for c in demandes):
        libre = ""   # texte laissé dans le formulaire mais case décochée : il n'est pas injecté

    # Chaque type part avec SA vérification (colonne `verification`) : le libellé seul laissait
    # le modèle choisir où chercher, et il prenait le plus visible.
    predefinis = [c for c in demandes if c.code != CODE_CRITERE_LIBRE]
    labels = [c.label for c in predefinis]
    lignes = []
    for c in predefinis:
        lignes.append(f"- {c.label}")
        if c.verification.strip():
            lignes.append(f"  Vérification : {c.verification.strip()}")

    prompt = get_prompt(db, "ambiguites").format(
        matiere=matiere,
        niveau=niveau,
        texte=req.texte.strip(),
        criteres="\n".join(lignes) or "- (aucun type prédéfini)",
        critere_libre=libre or "aucun",
    )

    try:
        # retry_max / retry_wait_max : la politique de rattrapage sur 429, LUE EN BASE comme
        # partout ailleurs. Elle manquait ici — l'outil rendait donc 429 au prof dès la première
        # limite du fournisseur, pendant que la séance et l'activité re-tentaient. Le réglage
        # `ai_retry_max` de l'admin ne s'appliquait pas à cet écran, sans que rien ne le dise.
        raw = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), model=get_ai_model(db),
                       max_tokens=get_max_tokens(db, "ambiguites"), temperature=get_temperature(db),
                       retry_max=get_retry_max(db), retry_wait_max=get_retry_wait_max(db),
                       outil="ambiguites")
        data = _parse_json(raw)
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    except ValueError:
        raise HTTPException(500, "Le modèle n'a pas retourné un résultat exploitable. Réessayez.")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    nb = len(data.get("ambiguites", []))

    # Une statistique ne casse JAMAIS l'outil du prof : si le journal d'usage ne s'écrit pas,
    # l'analyse est rendue quand même. L'intention était bonne, il manquait le rollback.
    #
    # Après un commit() qui échoue, la session reste EN ÉTAT D'ÉCHEC : toute requête suivante
    # sur cette même session échoue à son tour, avec une erreur qui ne parle pas de statistiques.
    # Ici la requête se termine juste après et get_db referme — le risque est donc faible
    # aujourd'hui. Mais le motif se recopie, et le prochain qui le posera au milieu d'une
    # fonction plus longue héritera d'une session morte sans le savoir.
    #
    # Motif déjà correct ailleurs : core/middleware.py, supervision/alerts.py, systeme/admin.py.
    try:
        db.add(ToolUsageLog(user_id=user.id, tool="ambiguites", score_label=str(nb)))
        db.commit()
    except Exception:
        db.rollback()

    # Le `type` rendu est RECOLLÉ sur ce qui a été coché. La consigne du prompt n'est pas une
    # garantie : le modèle peut inventer un intitulé, traduire le libellé ou en signaler un que
    # le prof n'a pas demandé. Un type hors liste devient « Autre » — la carte reste affichée,
    # mais aucun intitulé fantôme n'atteint l'écran.
    libelle_autre = connus[CODE_CRITERE_LIBRE].label if CODE_CRITERE_LIBRE in connus else "Autre"
    attendus = {label.casefold(): label for label in labels}
    attendus[libelle_autre.casefold()] = libelle_autre

    cartes = []
    for a in data.get("ambiguites", []):
        carte = dict(a)
        carte["type"] = attendus.get(str(carte.get("type", "")).strip().casefold(), libelle_autre)
        cartes.append(Ambiguite(**carte))

    return AmbigsResponse(ambiguites=cartes, verdict=data.get("verdict", ""))
