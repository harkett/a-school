"""GET /api/activites/{matiere} — les types d'activité d'un couple, LUS EN BASE.

Source UNIQUE : le CATALOGUE `types_activite` + la LIAISON `referentiel_types_activite` (le « coché »
du référentiel). Aucun type en dur, zéro copie.

Résolution du couple : par le NIVEAU (envoyé par le client, même patron qu'`exemple_referentiel`) →
le référentiel du niveau (matiere_id NULL). Repli : si le couple n'a aucun type coché (ou pas de
référentiel), on renvoie le type par DÉFAUT du catalogue (`is_default`) — « Activité d'apprentissage ».
"""
import json
import logging
from string import Formatter

from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend import auth as auth_lib
from backend.core.database import get_db
from backend.core.models import GenerateRequest, ProposerIdeeRequest, ProposerIdeeResponse
from backend.core.models_db import (
    Activite, Niveau, Referentiel, ActiviteType, ReferentielActiviteType, ReferentielTypePrecision,
    TypeParametre, User,
)
from backend.prof.profil import couple_de_travail, matiere_demande_langue, texte_cahier_du_profil
from backend.llm.generator import generate, generate_stream, acquire_llm_slot, release_llm_slot, LLMRateLimitError
from backend.llm.prompts import build_proposer_idee_prompt, ajouter_cahier_au_prompt
from backend.rag.pgvector_store import retrieve_pg
from backend.supervision.incidents import creer_incident
from backend.systeme.admin import (
    get_ai_model, get_ai_provider, get_cle_texte, get_max_tokens, get_temperature, get_rag_top_k,
    get_stream_silence_timeout, get_retry_max, get_retry_wait_max, get_prompt,
    get_few_shot_seuil, get_few_shot_extrait_max,
)

router = APIRouter()
log = logging.getLogger(__name__)

# Paramètres SAISIS par le prof qui peuvent légitimement manquer dans la requête (le front les
# retire s'ils sont vides). S'ils manquent alors que le prompt du type les exige, le .format()
# lève KeyError → faute client (400), jamais un 500. Tout AUTRE placeholder manquant = bug
# du prompt (template) → on re-lève (500), jamais masqué.
_USER_PARAMS = {
    "nb": "le nombre de questions / d'items",
    "sous_type": "le type d'exercice",
    "langue": "la langue vivante",
}


def type_du_couple_verifie(db: Session, niveau: str, activite_type_id: int):
    """LA porte unique de la question « ce type est-il utilisable pour ce couple ? ».

    Trois contrôles, dans l'ordre où ils comptent pour le prof :
      1. le NIVEAU a un référentiel officiel (sans lui, aucun prompt de couple n'existe) ;
      2. le TYPE existe au catalogue ET y est actif ;
      3. le type est COCHÉ pour ce référentiel, avec un prompt non vide (`referentiel_types_activite`).

    Renvoie (ref_id, type, prompt du couple). Lève un 400 au message écrit pour le prof sinon.

    Écrite une fois, appelée par les DEUX portes : la génération (/api/generate) et l'écriture
    en base (POST/PUT /contenus/activites). Deux copies auraient fini par dire des choses
    différentes — et c'est l'écriture qui décide de ce que « Mes stats » comptera.
    """
    ref_id = _referentiel_du_niveau(db, niveau)
    if ref_id is None:
        raise HTTPException(400, "Ce niveau n'a pas encore de référentiel officiel. La génération n'est pas encore possible ici.")

    t = (db.query(ActiviteType)
           .filter(ActiviteType.id == activite_type_id, ActiviteType.actif.is_(True))
           .first())
    if t is None:
        raise HTTPException(400, "Type d'activité inconnu.")

    # Le PROMPT du COUPLE × type, LU EN BASE sur la liaison (coché + non vide). Une seule source
    # par donnée, zéro prompt en dur, zéro repli sur un prompt global : le prompt est propre au couple.
    lien = (db.query(ReferentielActiviteType)
              .filter(ReferentielActiviteType.referentiel_id == ref_id,
                      ReferentielActiviteType.activite_type_id == t.id,
                      ReferentielActiviteType.actif.is_(True))
              .first())
    modele = lien.prompt if (lien and lien.prompt and lien.prompt.strip()) else None
    if modele is None:
        raise HTTPException(400, "Ce type d'activité n'est pas encore prêt pour ce niveau.")

    return ref_id, t, modele


def few_shot_du_prof(db: Session, user: User, activite_type_id: int,
                     matiere: str | None, niveau: str) -> str:
    """Le style du prof, tiré de SES activités précédentes — le « aSchool vous reconnaît » que
    l'application promet (astuce de l'Accueil, jauge de Mes stats).

    On ne prend que les activités du MÊME type et du MÊME couple (matière + niveau) : ses
    résumés n'influencent pas ses analyses, et son français de 6e n'influence pas sa 3e. En
    dessous du seuil (`few_shot_seuil`, en base — 3 aujourd'hui), on ne renvoie RIEN : deux
    exemples ne font pas un style, et le prof n'a encore rien vu se déclencher dans Mes stats.

    Renvoie la couche de prompt prête à coller, ou une chaîne vide (aucune couche ajoutée).
    """
    seuil = get_few_shot_seuil(db)
    precedentes = (
        db.query(Activite.resultat, Activite.activite_label)
        .filter(Activite.user_id == user.id,
                Activite.activite_type_id == activite_type_id,
                Activite.matiere == matiere,
                Activite.niveau == niveau,
                Activite.resultat != "")
        .order_by(Activite.created_at.desc())
        .limit(seuil)
        .all()
    )
    if len(precedentes) < seuil:
        return ""
    taille = get_few_shot_extrait_max(db)
    exemples = "\n\n".join(
        f"--- Exemple {i} ({label}) ---\n{(resultat or '')[:taille]}"
        for i, (resultat, label) in enumerate(precedentes, start=1)
    )
    return get_prompt(db, "few_shot").format(exemples=exemples)


def _trous_du_prompt(modele: str | None) -> list[str]:
    """Trous du prompt du couple×type saisis par le PROF ({texte} + _USER_PARAMS), dans l'ordre
    du prompt, sans doublon. Renvoyé à l'écran dans `besoins` : le champ « Nombre de questions »
    s'affiche si {nb} y figure — le besoin reste écrit à UNE seule place, le prompt. La zone
    TEXTE, elle, est TOUJOURS affichée et exigée (la demande de l'utilisateur est la base de
    tout — décision du 24/07). Les trous remplis par le serveur ({referentiel}…) n'y figurent pas."""
    if not modele:
        return []
    try:
        champs = [f for _, f, _, _ in Formatter().parse(modele) if f]
    except ValueError:  # prompt avec accolades cassées : aucun besoin lisible, jamais un 500
        return []
    prof = {"texte", *_USER_PARAMS}
    vus: set[str] = set()
    trous: list[str] = []
    for f in champs:
        if f in prof and f not in vus:
            vus.add(f)
            trous.append(f)
    return trous


def _referentiel_du_niveau(db: Session, niveau: str) -> int | None:
    """id du référentiel de ce niveau, ou None.

    None si niveau vide, aucun référentiel, ou ambiguïté (même nom de niveau dans deux cycles :
    on ne peut pas trancher sans le cycle). Dans tous ces cas on retombe sur le défaut — un GET
    d'affichage ne doit JAMAIS casser la page prof."""
    if not niveau:
        return None
    rows = (db.query(Referentiel.id)
              .join(Niveau, Niveau.id == Referentiel.niveau_id)
              .filter(Niveau.nom == niveau)
              .all())
    if len(rows) != 1:
        if len(rows) > 1:
            log.warning("[activites] ambiguïté niveau %r : %d référentiels → repli défaut", niveau, len(rows))
        return None
    return rows[0][0]


def types_du_couple(db: Session, niveau: str) -> list[dict]:
    """Types d'activité à afficher pour le couple, LUS EN BASE.

    1) types COCHÉS (`liaison.actif`) du référentiel du niveau, joints au catalogue (`actif`) ;
    2) si vide (pas de référentiel, ou rien de coché) → le type par DÉFAUT du catalogue.
    Précisions LUES PAR COUPLE (`referentiel_type_precisions`, ordonnées par `ordre`) et paramètres
    dans `type_parametres` — plus de blob JSON. Renvoie `[{label, key, sous_types:[...], params:[...]}]`
    (ordre liaison puis catalogue)."""
    ref_id = _referentiel_du_niveau(db, niveau)
    lignes = []
    if ref_id is not None:
        lignes = (db.query(ActiviteType)
                    .join(ReferentielActiviteType,
                          ReferentielActiviteType.activite_type_id == ActiviteType.id)
                    .filter(ReferentielActiviteType.referentiel_id == ref_id,
                            ReferentielActiviteType.actif.is_(True),
                            ActiviteType.actif.is_(True))
                    .order_by(ReferentielActiviteType.ordre, ActiviteType.ordre)
                    .all())
    if not lignes:
        lignes = (db.query(ActiviteType)
                    .filter(ActiviteType.is_default.is_(True), ActiviteType.actif.is_(True))
                    .order_by(ActiviteType.ordre)
                    .all())

    # Précisions / paramètres de chaque type, LUS dans leurs tables filles (une requête chacune,
    # groupée par type). Ordre des précisions = `ordre`. Zéro JSON, une donnée = une ligne.
    type_ids = [t.id for t in lignes]
    prec_par_type: dict[int, list[str]] = {}
    par_par_type: dict[int, list[str]] = {}
    besoins_par_type: dict[int, list[str]] = {}
    if type_ids:
        # Précisions PAR COUPLE (table fille de la liaison `referentiel_type_precisions`), comme le
        # prompt : chaque couple a SES précisions. On passe par les liaisons de CE référentiel — pas
        # de repli sur une table globale. Sans référentiel (types par défaut) : aucune précision.
        if ref_id is not None:
            type_par_lien = {}
            for tid, lien_id, prompt in (db.query(ReferentielActiviteType.activite_type_id,
                                                  ReferentielActiviteType.id,
                                                  ReferentielActiviteType.prompt)
                                           .filter(ReferentielActiviteType.referentiel_id == ref_id,
                                                   ReferentielActiviteType.actif.is_(True),
                                                   ReferentielActiviteType.activite_type_id.in_(type_ids))
                                           .all()):
                type_par_lien[lien_id] = tid
                # Les besoins du type = les trous de SON prompt (lu à l'instant, jamais stocké).
                besoins_par_type[tid] = _trous_du_prompt(prompt)
            if type_par_lien:
                for lien_id, libelle in (db.query(ReferentielTypePrecision.referentiel_activite_type_id,
                                                  ReferentielTypePrecision.libelle)
                                           .filter(ReferentielTypePrecision.referentiel_activite_type_id
                                                   .in_(list(type_par_lien.keys())))
                                           .order_by(ReferentielTypePrecision.referentiel_activite_type_id,
                                                     ReferentielTypePrecision.ordre)
                                           .all()):
                    prec_par_type.setdefault(type_par_lien[lien_id], []).append(libelle)
        for tid, cle in (db.query(TypeParametre.type_activite_id, TypeParametre.cle)
                           .filter(TypeParametre.type_activite_id.in_(type_ids))
                           .all()):
            par_par_type.setdefault(tid, []).append(cle)

    return [
        {"id": t.id, "label": t.label,
         "sous_types": prec_par_type.get(t.id, []), "params": par_par_type.get(t.id, []),
         "besoins": besoins_par_type.get(t.id, [])}
        for t in lignes
    ]


@router.get("/activites/{matiere}")
def get_activites(matiere: str, niveau: str = "", db: Session = Depends(get_db)):
    """Types d'activité du couple. `matiere` reste dans l'URL (compat front) mais n'entre PAS dans la
    résolution : le référentiel est résolu par NIVEAU (matiere_id NULL), même patron qu'`exemple_
    referentiel`. `niveau` = query envoyée par le front. Renvoie TOUJOURS un tableau (repli défaut) →
    la page prof ne casse jamais."""
    return types_du_couple(db, niveau)


def _prof_et_couple(db: Session, aschool_access: str | None) -> tuple[User, str, str]:
    """Le prof connecté et son couple de TRAVAIL, lus EN BASE au moment de l'action
    (décision du 25/07) : l'écran n'envoie plus matière/niveau — le serveur lit le couple
    que le prof a validé (« Changer niveau et/ou matière »), sinon son profil. Renvoie
    (user, matiere, niveau) ; profil incomplet → 400 humain, jamais une génération à vide."""
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(401, "Non connecté.")
    matiere, niveau, _ = couple_de_travail(db, user)
    if not matiere or not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau) — c'est lui qui guide la génération.")
    return user, matiere, niveau


# Message honnête au prof quand aucun extrait n'est assez pertinent (même contrat que
# « Tester un exemple » : on n'invente RIEN, on le dit).
_AUCUN_EXTRAIT_POUR_IDEE = (
    "aSchool n'a pas trouvé, dans le référentiel officiel, de passage assez pertinent "
    "pour proposer une idée fidèle. Essayez une autre précision — ou décrivez votre idée "
    "directement dans la zone de texte."
)

# Gabarit de requête RAG — UNIFORME pour tout couple, construit sur ce que le prof a
# RÉELLEMENT choisi (type d'activité + précision + niveau) ; jamais de formulation par matière en dur.
_REQUETE_IDEE_GABARIT = "Idée d'activité pour le type d'activité {type_label}{precision}, niveau {niveau}"


def _extraire_objet(texte: str | None) -> tuple[str | None, str]:
    """Détache la ligne « Objet : titre court » (1re ligne demandée à l'IA) du corps de l'idée.

    Renvoie (objet, texte_idee). DÉFENSIF : si l'IA n'a pas ouvert par une ligne Objet
    reconnaissable, on ne perd RIEN — objet None et le texte ENTIER part dans la zone.
    L'objet est plafonné à 150 caractères (la limite du champ Objet à l'écran)."""
    brut = (texte or "").strip()
    premiere, _, reste = brut.partition("\n")
    tete = premiere.strip()
    if tete.lower().startswith("objet") and ":" in tete:
        candidat = tete.split(":", 1)[1].strip()
        if candidat and reste.strip():
            return candidat[:150], reste.strip()
    return None, brut


@router.post("/proposer-idee", response_model=ProposerIdeeResponse)
def api_proposer_idee(
    req: ProposerIdeeRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Bouton « Propose-moi une idée » de la zone texte (même famille que « Tester un
    exemple ») : fabrique UNE idée de départ à partir des choix du prof (type + précision +
    niveau) et du référentiel officiel du niveau, et la renvoie pour être ÉCRITE DANS LA
    ZONE TEXTE. Le prof la relit, la modifie, puis « Générer » suit le circuit normal
    ({texte}) — la zone reste la base de tout, ce bouton ne fait que l'amorcer.

    Règle d'or : pas de référentiel → available:false ; rien d'assez pertinent au seuil
    (lu en base, `referentiels.score_min`) → available:false + message honnête. On
    n'invente RIEN hors du programme. Le couple (matière + niveau) est LU EN BASE
    (couple de travail du prof) — l'écran ne l'envoie plus (décision du 25/07)."""
    user, _matiere, niveau = _prof_et_couple(db, aschool_access)

    t = (db.query(ActiviteType)
           .filter(ActiviteType.id == req.activite_type_id, ActiviteType.actif.is_(True))
           .first())
    if t is None:
        raise HTTPException(400, "Type d'activité inconnu.")

    ref_id = _referentiel_du_niveau(db, niveau)
    if ref_id is None:
        return ProposerIdeeResponse(available=False)

    ref = (db.query(Referentiel.collection, Referentiel.filtres, Referentiel.score_min)
             .filter(Referentiel.id == ref_id).first())
    collection, filtres_json, seuil = ref
    filters = json.loads(filtres_json) if filtres_json else None
    requete = _REQUETE_IDEE_GABARIT.format(
        type_label=t.label,
        precision=f" ({req.sous_type})" if req.sous_type else "",
        niveau=niveau,
    )
    chunks = retrieve_pg(collection, requete, filters=filters, top_k=get_rag_top_k(db))
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        log.info("[proposer-idee] aucun chunk >= seuil %s (%s, type=%r) → available=false", seuil, collection, t.label)
        return ProposerIdeeResponse(available=False, message=_AUCUN_EXTRAIT_POUR_IDEE)

    prompt = build_proposer_idee_prompt(db, chunks, type_label=t.label, precision=req.sous_type, niveau=niveau)
    # Cahier des charges de l'établissement (get, zéro copie) ajouté par-dessus le programme officiel —
    # même geste que générer. Pas de cahier → prompt inchangé.
    prompt = ajouter_cahier_au_prompt(db, prompt, texte_cahier_du_profil(db, user))
    try:
        texte = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db), model=get_ai_model(db),
                         max_tokens=get_max_tokens(db, "idee"), temperature=get_temperature(db),
                         retry_max=get_retry_max(db), retry_wait_max=get_retry_wait_max(db))
    except LLMRateLimitError as e:
        log.warning("[proposer-idee] service très demandé : %s", e)
        raise HTTPException(429, "Le service est très demandé en ce moment. Réessayez dans un instant.")
    objet, texte_idee = _extraire_objet(texte)
    log.info("[proposer-idee] idée générée (%s, type=%r, %d chunks >= %s, objet=%r)",
             niveau, t.label, len(chunks), seuil, objet)
    return ProposerIdeeResponse(available=True, texte=texte_idee, objet=objet)


@router.post("/generate")
def api_generate(
    req: GenerateRequest,
    aschool_access: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Génère une activité EN STREAMING à partir du PROMPT du COUPLE × type, LU EN BASE sur la
    liaison `referentiel_types_activite` (une seule place, zéro copie) — PAS le catalogue global.
    Le couple est résolu par le NIVEAU (même patron que `types_du_couple`). Le prompt contient deux
    marqueurs : {texte} (l'idée du prof, elle mène) et {referentiel} (extraits du programme officiel
    du couple, récupérés par RAG sur l'idée du prof). Provider / modèle / max_tokens / température /
    coupure de silence lus EN BASE.

    Réponse : flux SSE (`text/event-stream`) — événements `delta` (morceau de texte), `error`
    (échec technique survenu APRÈS le début du flux) et `done` (fin normale). Les échecs MÉTIER
    (référentiel absent, type pas prêt, RAG vide, saturation) sont renvoyés AVANT le flux, en JSON
    HTTP classique (4xx/429) — l'écran affiche alors leur message tel quel.

    `avec_correction` : case cochée → la consigne du corrigé (registre des prompts admin, clé
    `correction`, modifiable à chaud) est AJOUTÉE à la fin du prompt du couple avant le flux —
    le corrigé sort dans le même document, sous l'activité. Décochée → prompt strictement
    identique. NB : le few-shot « aSchool vous reconnaît » reste DIFFÉRÉ. La sauvegarde côté
    prof (/api/mes-activites) reste inchangée (déclenchée par l'écran à la fin du flux).
    Le couple (matière + niveau) est LU EN BASE (couple de travail du prof, résolu par
    couple_de_travail) — l'écran ne l'envoie plus (décision du 25/07)."""
    user, matiere, niveau = _prof_et_couple(db, aschool_access)

    # 1 à 3. Le couple, le type et son prompt — LA porte unique (voir type_du_couple_verifie).
    ref_id, t, modele = type_du_couple_verifie(db, niveau, req.activite_type_id)

    # 4. Le {referentiel} : extraits du programme officiel du couple les plus proches de l'idée du prof
    # (RAG pgvector), filtrés au SEUIL du référentiel (lu en base). Rien d'assez pertinent → on n'invente
    # RIEN, on le dit au prof (règle 23). Même voie que « Tester un exemple ».
    ref = (db.query(Referentiel.collection, Referentiel.filtres, Referentiel.score_min)
             .filter(Referentiel.id == ref_id).first())
    collection, filtres_json, seuil = ref
    filters = json.loads(filtres_json) if filtres_json else None
    chunks = retrieve_pg(collection, req.texte, filters=filters, top_k=get_rag_top_k(db))
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        raise HTTPException(400, "aSchool n'a pas trouvé, dans le référentiel officiel, de passage assez pertinent. Reformulez votre idée avec des termes plus proches du programme.")
    referentiel_txt = "\n\n".join(c["text"] for c in chunks)

    # 5. Remplissage. Le texte source → {texte}, les extraits officiels → {referentiel}. Les autres
    # paramètres (niveau, sous_type, nb, langue) restent disponibles si l'admin les a mis dans le prompt.
    kwargs = {"niveau": niveau, "referentiel": referentiel_txt}
    if req.sous_type:
        kwargs["sous_type"] = req.sous_type
    if req.nb:
        kwargs["nb"] = req.nb
    # LV : la langue vient de la BASE (matière de travail qui PORTE une langue + langue du
    # profil) — plus aucune valeur envoyée par l'écran. La reconnaissance se fait sur
    # l'indicateur `matieres.demande_langue`, plus sur le libellé exact de la matière : celui-ci
    # se renomme (constaté : la matière réelle s'appelle « Langue vivante »), la clé ne bouge pas.
    if matiere_demande_langue(db, user) and user.langue_lv:
        kwargs["langue"] = user.langue_lv
    try:
        prompt = modele.format(texte=req.texte, **kwargs)
    except KeyError as e:
        manquant = str(e).strip("'")
        if manquant not in _USER_PARAMS:
            raise  # placeholder inconnu = bug du prompt → 500, jamais masqué
        raise HTTPException(400, f"Indiquez {_USER_PARAMS[manquant]} pour cette activité.") from e

    # 5 bis. Cahier des charges de l'établissement : s'il en a déposé un, son texte de travail
    # (cahiers_prof.texte_epure, get — zéro copie) est AJOUTÉ après le programme officiel — aSchool
    # applique les règles de l'école PAR-DESSUS le programme. Pas de cahier (ou texte vide) → prompt
    # inchangé (aucune régression). Même geste que « Document d'exemple » et « Propose-moi une idée ».
    prompt = ajouter_cahier_au_prompt(db, prompt, texte_cahier_du_profil(db, user))

    # 5 bis 2. FEW-SHOT « aSchool vous reconnaît » : à partir de `few_shot_seuil` activités du
    # même type ET du même couple, les précédentes sont données en exemple de SA manière (ton,
    # formulation, mise en page). En dessous du seuil, aucune couche — c'est exactement ce que
    # la jauge de Mes stats et l'astuce de l'Accueil annoncent au prof. Placé après le cahier
    # (le style s'applique par-dessus le fond) et avant le corrigé, le ton et le contrôle qualité.
    few_shot = few_shot_du_prof(db, user, t.id, matiere, niveau)
    if few_shot:
        prompt = prompt + "\n\n" + few_shot

    # 5 ter. Corrigé : case « Inclure une proposition de correction » cochée → la consigne du
    # corrigé (registre des prompts admin, lue en base à l'appel) s'ajoute à la FIN du prompt
    # du couple — le corrigé sort dans le même document, sous l'activité. Décochée → rien.
    if req.avec_correction:
        prompt = prompt + "\n\n" + get_prompt(db, "correction")

    # 5 quater. TON de rédaction : choisi PAR LE BOUTON de génération (« Générer — ton académique » /
    # « … opérationnel »). Deux valeurs seulement ('academique' / 'operationnel') → couche de style
    # ajoutée au prompt (texte en base, même mécanique que le corrigé). Absent ou valeur inconnue →
    # aucune couche (rétrocompatible). Placé AVANT le contrôle qualité pour qu'il relise dans le bon ton.
    if req.ton in ("academique", "operationnel"):
        prompt = prompt + "\n\n" + get_prompt(db, f"ton_{req.ton}")

    # 5 quinquies. Contrôle qualité INTÉGRÉ (remplace l'ancienne cartouche « Vérifier ») : dernière couche
    # du prompt, TOUJOURS ajoutée. Le modèle s'auto-relit sur les 5 axes et corrige avant de rendre —
    # un seul appel, aucun surcoût. Placée après le corrigé et le ton pour qu'elle les couvre. Texte en base.
    prompt = prompt + "\n\n" + get_prompt(db, "controle_qualite")

    # 6. Réglages LLM lus EN BASE, AVANT le flux (get) — passés en valeurs au flux (aucune lecture
    # de base pendant le streaming, la session de requête étant destinée à se fermer). `silence` =
    # coupure de silence admin en base (zéro délai en dur).
    provider = get_ai_provider(db)
    model = get_ai_model(db)
    cle = get_cle_texte(db)
    max_toks = get_max_tokens(db, "activite")
    temp = get_temperature(db)
    silence = get_stream_silence_timeout(db)
    retry_max = get_retry_max(db)
    retry_wait_max = get_retry_wait_max(db)

    # 7. Créneau LLM pris AVANT le flux : si saturation, message MÉTIER « service très demandé »
    # renvoyé en 429 pré-flux (jamais après le début du flux, où le statut 200 est déjà parti).
    try:
        acquire_llm_slot()
    except LLMRateLimitError as e:
        log.warning("/api/generate — service très demandé : %s", e)   # détail technique = logs
        raise HTTPException(429, "Le service est très demandé en ce moment. Réessayez dans un instant.")

    def flux():
        # Le créneau est RENDU dans le finally — donc dans TOUS les cas : fin normale, erreur
        # technique en cours de flux, ET déconnexion du prof (Starlette ferme ce générateur →
        # GeneratorExit remonte jusqu'au finally). GeneratorExit est une BaseException : le
        # `except Exception` ne l'attrape pas (pas de faux événement `error`), le finally, lui,
        # s'exécute toujours. Un créneau jamais rendu = perdu jusqu'au redémarrage : c'est le
        # piège à ne pas laisser passer.
        try:
            for morceau in generate_stream(
                prompt, cle=cle, provider=provider, model=model,
                max_tokens=max_toks, temperature=temp, read_timeout=silence,
                retry_max=retry_max, retry_wait_max=retry_wait_max,
            ):
                yield f"event: delta\ndata: {json.dumps({'text': morceau}, ensure_ascii=False)}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            # Détail technique = logs (règle 23) ; l'écran ne reçoit qu'un `error` neutre + une
            # RÉFÉRENCE d'incident. L'incident (erreur réelle + contexte technique) est enregistré
            # EN BASE via une session DÉDIÉE (la session de requête étant destinée à se fermer) →
            # l'admin voit ce qui a planté, le prof ne voit qu'un message humain.
            log.warning("/api/generate — flux interrompu : %s", e)
            ref = creer_incident(
                endpoint="/api/generate",
                error=f"{type(e).__name__}: {e}",
                provider=provider, model=model,
                matiere=matiere, niveau=niveau, type_activite=t.label,
                consigne=req.texte, user_email=user.email,
            )
            data = json.dumps({"ref": ref}, ensure_ascii=False) if ref else "{}"
            yield f"event: error\ndata: {data}\n\n"
        finally:
            release_llm_slot()

    return StreamingResponse(
        flux(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
