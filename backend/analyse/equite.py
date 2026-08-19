"""« Équité d'une évaluation » — le troisième frère d'Ambiguïtés et de Consigne.

MÊME MOULE QUE LES AMBIGUÏTÉS, et pour la même raison : ce que l'outil cherche est une LISTE,
le prof coche ce qu'il veut faire relire, et décocher un biais ne fait que retirer des cartes du
rapport. (La consigne, elle, impose ses cinq axes parce qu'elle rend une réécriture : un axe mis
de côté produirait une version « corrigée » qui laisse passer un défaut connu. Ici, rien n'est
réécrit à la place du prof.)

CE QUE CET OUTIL NE FAIT PAS, et il faut le savoir avant de lire une ligne. Les biais du
CORRECTEUR — effet de halo, écart entre deux correcteurs, sévérité qui dérive au fil du paquet,
influence d'une copie sur la suivante — sont les mieux établis de la recherche française
(Cnesco, « Limites et biais de l'évaluation »). Ils demandent plusieurs copies, plusieurs
correcteurs ou de la durée : un énoncé collé seul n'en montre AUCUN. L'outil ne les cherche pas
et le prompt lui interdit d'en parler. Ils sont expliqués dans l'aide de l'écran, avec cette
raison — un prof qui vient y chercher « effet de halo » doit trouver une réponse, pas un blanc.

Restent les biais DU SUJET, tous de la même forme : l'évaluation demande quelque chose EN PLUS
de la compétence visée, et ce quelque chose n'est pas également disponible à tous les élèves.
"""
from fastapi import APIRouter, Depends, HTTPException, Cookie
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.analyse.commun import email_de_session, json_du_modele
from backend.core.catalogues import catalogue
from backend.core.database import get_db, schema_de_session
from backend.core.models import ExempleReferentielResponse
from backend.core.models_db import EquiteCritere, ToolUsageLog, User
from backend.pedagogie.exemple_referentiel import (AUCUN_EXTRAIT_PERTINENT, REQUETE_GABARIT,
                                                   _resolve_collection)
from backend.prof.profil import couple_de_travail
from backend.rag.pgvector_store import retrieve_pg
from backend.systeme.admin import (get_ai_model, get_ai_provider, liste_fournisseurs, get_cle_texte, get_max_tokens,
                                   get_rag_top_k, get_retry_max, get_retry_wait_max,
                                   get_temperature, get_prompt)
from backend.llm.generator import generate, LLMRateLimitError
from backend.llm.prompts import build_equite_exemple_prompt

router = APIRouter()

# Ce que le prompt reçoit quand le prof n'a pas collé de barème. Une phrase, pas un vide : sans
# elle, le repère `{bareme}` arriverait au modèle avec du blanc dessous, et il inventerait une
# répartition de points pour avoir quelque chose à juger.
AUCUN_BAREME = "(aucun barème fourni — ne rien supposer sur la répartition des points)"

# LE DROIT DE NE PAS ÉCRIRE, pour le prompt d'exemple : quand les extraits du référentiel ne
# suffisent pas à savoir ce que la matière recouvre à ce niveau, le modèle répond par ce marqueur
# au lieu de deviner une évaluation plausible. Une évaluation inventée hors du programme serait
# pire qu'une absence d'exemple — le prof la croirait tirée de SA formation.
#
# Le marqueur est une CONVENTION DU TEXTE, administrable comme lui : on le reconnaît, mais on ne
# tombe pas si l'admin le retire du prompt (le modèle rendrait alors une évaluation, cas normal).
MARQUEUR_PAS_D_EXEMPLE = "=== PAS D'EXEMPLE ==="


class EquiteRequest(BaseModel):
    texte: str
    # Facultatif, et c'est le sujet : trois des neuf biais portent sur le barème (barème absent
    # ou décalé, double peine, question qui verrouille). L'analyse tourne sans lui et le dit.
    bareme: str | None = None
    criteres: list[str] = Field(default_factory=list)


class Biais(BaseModel):
    # Vide quand le défaut porte sur l'ensemble de l'évaluation et non sur un passage : « temps
    # insuffisant » et « barème absent » n'ont pas d'extrait à citer. L'écran affiche alors la
    # carte sans citation, plutôt qu'une citation fabriquée.
    extrait: str = ""
    critere: str
    consequence: str
    correction: str


class EquiteResponse(BaseModel):
    biais: list[Biais]
    verdict: str


class CritereItem(BaseModel):
    code: str
    label: str
    description: str


def criteres_equite(db: Session) -> list[EquiteCritere]:
    return catalogue(db, EquiteCritere, "critères d'équité")


@router.get("/equite/criteres", response_model=list[CritereItem])
def api_criteres_equite(
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Les biais proposés au prof — la MÊME source que celle sur laquelle le serveur refusera ou
    acceptera plus bas. L'écran ne connaît aucun de ces libellés."""
    email_de_session(aschool_access)
    return [CritereItem(code=c.code, label=c.label, description=c.description)
            for c in criteres_equite(db)]


def bloc_biais(db: Session) -> str:
    """Les biais tels qu'un RÉDACTEUR d'exemple doit les lire : un tiret par biais, et ce qui doit
    être repérable dessous.

    Un seul endroit : l'analyse et l'exemple décrivent les MÊMES biais, puisqu'ils les lisent au
    même catalogue. Une liste recopiée dans le prompt d'exemple aurait divergé au premier
    renommage — et l'outil aurait alors cherché autre chose que ce qu'il fait écrire."""
    lignes = []
    for c in criteres_equite(db):
        lignes.append(f"- {c.label}")
        if c.verification.strip():
            lignes.append(f"  Ce qui doit être repérable : {c.verification.strip()}")
    return "\n".join(lignes)


def _refus_ou_texte(brut: str) -> ExempleReferentielResponse:
    """La réponse du modèle, rangée : soit une évaluation à poser dans la zone, soit un refus
    motivé à montrer au prof. Rien ne part dans la zone tant que le marqueur y est."""
    texte = (brut or "").strip()
    if MARQUEUR_PAS_D_EXEMPLE not in texte:
        return ExempleReferentielResponse(available=True, texte=texte)

    # Ce qui suit le marqueur est la raison écrite par le modèle. On la nettoie de son étiquette
    # (« Raison : ») pour ne pas la montrer telle quelle au prof, et on retombe sur le message
    # commun si elle est vide — un refus sans motif n'apprend rien.
    reste = texte.split(MARQUEUR_PAS_D_EXEMPLE, 1)[1].strip()
    if reste.lower().startswith("raison"):
        reste = reste.split(":", 1)[-1].strip() if ":" in reste else ""
    return ExempleReferentielResponse(available=False, message=reste or AUCUN_EXTRAIT_PERTINENT)


@router.post("/equite/exemple-genere", response_model=ExempleReferentielResponse)
def api_exemple_equite_genere(
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """« Propose-moi un exemple » : l'évaluation de démonstration ÉCRITE À LA DEMANDE du prof,
    pour SON couple, ancrée sur les extraits de son référentiel.

    Le MÊME geste que chez ses deux frères : un clic, un appel, un texte posé dans la zone — rien
    n'est rangé en base. Une évaluation de démonstration n'a aucune raison d'être la même deux
    fois, et l'ancrage vient d'où il doit venir : le référentiel du couple, jamais l'intuition du
    modèle sur un nom de matière.

    Règle d'or, celle de `exemple_referentiel` dont il reprend la résolution : pas de référentiel
    pour ce couple, ou rien d'assez pertinent au seuil (`referentiels.score_min`) →
    available:false. On n'invente RIEN — et le modèle lui-même garde le droit de refuser."""
    email = email_de_session(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    matiere, niveau, _ = couple_de_travail(db, user)
    if not matiere or not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    resolu = _resolve_collection(db, niveau)
    if resolu is None:
        return ExempleReferentielResponse(available=False)
    collection, filtres, seuil = resolu

    chunks = retrieve_pg(collection, REQUETE_GABARIT.format(matiere=matiere, niveau=niveau),
                         filters=filtres, top_k=get_rag_top_k(db),
                         schema=schema_de_session(db), annee=niveau, matiere=matiere)
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        # Rien d'assez pertinent : on le dit au prof, et `generate` n'est PAS appelé (rien payé).
        return ExempleReferentielResponse(available=False, message=AUCUN_EXTRAIT_PERTINENT)

    prompt = build_equite_exemple_prompt(db, chunks, matiere=matiere, niveau=niveau,
                                         criteres=bloc_biais(db))
    # Pas de cahier des charges de l'établissement ici, contrairement aux prompts de génération :
    # ses règles servent à rendre un contenu PROPRE, et cette évaluation-ci doit être bancale.
    try:
        brut = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
                        model=get_ai_model(db),
                        max_tokens=get_max_tokens(db, "equite_exemple_genere"),
                        temperature=get_temperature(db), retry_max=get_retry_max(db),
                        retry_wait_max=get_retry_wait_max(db), outil="equite_exemple_genere")
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))   # surchargé/trop de demandes : transitoire, pas une panne
    return _refus_ou_texte(brut)


@router.post("/detect-equite", response_model=EquiteResponse)
def api_detect_equite(
    req: EquiteRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    email = email_de_session(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    if not req.texte.strip():
        raise HTTPException(400, "L'évaluation ne peut pas être vide.")

    # Couple résolu EN BASE (couple_de_travail, décision 25/07) — l'écran n'envoie pas
    # matière/niveau, le serveur ne fait pas confiance au corps de la requête.
    matiere, niveau, _ajuste = couple_de_travail(db, user)
    if not matiere or not niveau:
        raise HTTPException(400, "Votre profil n'a pas encore de matière et de niveau — complétez Mon profil avant de lancer l'analyse.")

    # Ce que le prof a coché — validé CONTRE LA TABLE, pas contre une liste écrite ici. L'écran
    # grise déjà son bouton tant que rien n'est coché ; le serveur ne s'appuie pas là-dessus.
    connus = {c.code: c for c in criteres_equite(db)}
    demandes = [connus[code] for code in dict.fromkeys(req.criteres) if code in connus]
    if not demandes:
        raise HTTPException(400, "Cochez au moins un biais à rechercher.")
    inconnus = [c for c in req.criteres if c not in connus]
    if inconnus:
        raise HTTPException(400, "Un des biais demandés n'existe pas (ou n'est plus proposé). Rechargez la page.")

    # Chaque biais part avec SA vérification (colonne `verification`) : le libellé seul laisse le
    # modèle choisir où chercher, et il prend le plus visible.
    lignes = []
    for c in demandes:
        lignes.append(f"- {c.label}")
        if c.verification.strip():
            lignes.append(f"  Vérification : {c.verification.strip()}")

    prompt = get_prompt(db, "equite").format(
        matiere=matiere,
        niveau=niveau,
        texte=req.texte.strip(),
        bareme=(req.bareme or "").strip() or AUCUN_BAREME,
        criteres="\n".join(lignes),
    )

    try:
        raw = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), voies_fournisseurs=liste_fournisseurs(db),
                       model=get_ai_model(db), max_tokens=get_max_tokens(db, "equite"),
                       temperature=get_temperature(db), retry_max=get_retry_max(db),
                       retry_wait_max=get_retry_wait_max(db), outil="equite")
        data = json_du_modele(raw)
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    except ValueError:
        raise HTTPException(500, "Le modèle n'a pas retourné un résultat exploitable. Réessayez.")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    trouves = data.get("biais", [])

    # Une statistique ne casse JAMAIS l'outil du prof : si le journal d'usage ne s'écrit pas,
    # l'analyse est rendue quand même (motif de `ambiguites.py`, rollback compris).
    try:
        db.add(ToolUsageLog(user_id=user.id, tool="equite", score_label=str(len(trouves)),
                            matiere=matiere, niveau=niveau))
        db.commit()
    except Exception:
        db.rollback()

    # Le `critere` rendu est RECOLLÉ sur ce qui a été coché. La consigne du prompt n'est pas une
    # garantie : le modèle peut inventer un intitulé, traduire un libellé, ou signaler un biais
    # que le prof n'a pas demandé. Ici, PAS de repli « Autre » comme chez les ambiguïtés — cette
    # liste n'en a pas, et une carte dont on ne sait pas de quel biais elle parle ne s'affiche
    # pas : elle est écartée. Un rapport plus court vaut mieux qu'un rapport douteux.
    attendus = {c.label.casefold(): c.label for c in demandes}
    cartes = []
    for b in trouves:
        carte = dict(b)
        label = attendus.get(str(carte.get("critere", "")).strip().casefold())
        if label is None:
            continue
        carte["critere"] = label
        carte["extrait"] = str(carte.get("extrait") or "").strip()
        cartes.append(Biais(**carte))

    return EquiteResponse(biais=cartes, verdict=data.get("verdict", ""))
