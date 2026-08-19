"""« Mes évals → Grilles » — la grille d'évaluation critériée du professeur.

CE QU'ELLE EST. Un TABLEAU : des critères en lignes (`grille_criteres`), des niveaux de maîtrise
en colonnes (`grille_niveaux_maitrise`), et dans chaque case le descripteur qui dit ce qu'il faut
avoir fait pour obtenir ce niveau sur ce critère (`grille_cellules`). Elle appartient au
professeur, comme une activité : il la crée, la retouche, la duplique, la rouvre l'année
suivante, la supprime.

UNE GRILLE NAÎT D'UNE GÉNÉRATION, ET D'ELLE SEULE. Il n'y a pas de « créer une grille vide » :
un tableau nu à remplir case par case n'est pas un service, c'est un tableur — le professeur en a
déjà un. Ce qu'il vient chercher ici, c'est que la grille soit ÉCRITE, sur son programme.

ELLE S'ÉCRIT AU GESTE, ET C'EST UNE DÉCISION. « Mes contenus » range son résultat dans une
colonne de texte réécrite en entier à chaque enregistrement (`activites.resultat`) ; une grille
éclatée en quatre tables ne peut pas se réécrire ainsi. Deux voies étaient possibles : un
brouillon JSON à côté des tables, figé en lignes à la validation, ou l'écriture immédiate de
chaque geste. C'est la seconde — un brouillon et des tables, ce sont DEUX VÉRITÉS POUR LA MÊME
DONNÉE, et la première qui diverge est un défaut que rien ne signale.

Concrètement : la génération écrit la grille entière en une transaction (règle 0, comme
l'activité qui naît en base à sa première génération), puis chaque retouche est un appel ciblé —
un critère ajouté, une case écrite, une colonne renommée.

CE QUI N'EST PAS ICI. La grille officielle du CCF (elle ne s'écrit pas, elle se référence) et
l'évaluation d'un élève (elle référence une grille, et le chef-d'œuvre en bac pro lui demande
plusieurs évaluateurs). Ni l'une ni l'autre n'entre dans ce module : ce sont d'autres objets,
avec d'autres cycles de vie.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.analyse.commun import json_du_modele
from backend.core.database import get_db, schema_de_session
from backend.core.deps import get_current_user
from backend.core.models_db import (
    Grille, GrilleCellule, GrilleCritere, GrilleNiveauMaitrise, User,
)
from backend.llm.generator import generate, LLMRateLimitError
from backend.llm.prompts import (
    ajouter_cahier_au_prompt, build_grille_idee_prompt, build_grille_prompt,
)
from backend.pedagogie.exemple_referentiel import _resolve_collection
from backend.prof.profil import couple_de_travail, texte_cahier_du_profil
from backend.rag.pgvector_store import retrieve_pg
from backend.systeme.admin import (
    get_ai_model, get_ai_provider, get_cle_texte, get_max_tokens, get_rag_top_k, get_retry_max,
    get_retry_wait_max, get_temperature, liste_fournisseurs,
)

router = APIRouter()

# Ce que le modèle a le droit de rendre. Au-delà, ce n'est plus une grille : personne ne coche
# douze lignes par copie, et une échelle de dix colonnes ne tient sur aucune feuille. Le prompt
# le demande déjà — ces bornes sont ce qui arrive quand il n'est pas suivi.
MAX_CRITERES = 12
MAX_NIVEAUX = 8

# Ce que « Propose-moi une idée » répond quand le programme officiel ne dit rien sur le thème
# demandé. Deux silences différents, deux messages : l'un dit qu'il n'y a pas de document, l'autre
# que le document n'a rien d'assez proche — et celui-là s'adresse à un professeur qui peut agir,
# donc il lui dit quoi faire. Ils s'affichent DANS la fenêtre, qui reste ouverte.
_AUCUN_REFERENTIEL_POUR_IDEE = (
    "Aucun référentiel officiel n'est encore en place pour votre niveau : aSchool ne peut pas "
    "proposer d'idée ancrée sur le programme. Écrivez votre demande directement dans la zone."
)
_AUCUN_EXTRAIT_POUR_IDEE = (
    "aSchool n'a rien trouvé sur ce thème dans le référentiel officiel de votre niveau. "
    "Reformulez-le avec des termes plus proches du programme — ou fermez cette fenêtre et "
    "écrivez votre demande vous-même."
)


# ---------------------------------------------------------------------------
# Corps de requête
# ---------------------------------------------------------------------------

class GrilleGeneration(BaseModel):
    """La demande du professeur, et rien d'autre : le couple est résolu EN BASE."""
    texte: str


class GrilleIdee(BaseModel):
    """Le THÈME tapé dans la fenêtre « Propose-moi une idée » — deux mots suffisent (« les
    réseaux »). Le couple, lui, est résolu en base comme partout ailleurs."""
    theme: str


class GrilleIdeeReponse(BaseModel):
    """La réponse du bouton — même forme que son frère des activités (`ProposerIdeeResponse`).

    `available=False` n'est PAS une erreur : c'est la réponse honnête quand le référentiel n'a
    rien d'assez proche du thème. Elle n'est pas rendue en 4xx justement pour que la fenêtre
    reste ouverte et affiche `message` — le professeur reformule sur place. Ce cas coûte zéro :
    on s'arrête après la recherche, avant le modèle."""
    available: bool
    texte: str | None = None
    message: str | None = None


class GrilleEntete(BaseModel):
    titre: str = ""
    contexte: str = ""


class CritereCorps(BaseModel):
    libelle: str = ""
    poids: float = 1.0
    ordre: int | None = None


class NiveauCorps(BaseModel):
    libelle: str = ""
    points: float = 0.0
    ordre: int | None = None


class CelluleCorps(BaseModel):
    critere_id: int
    niveau_maitrise_id: int
    descripteur: str = ""


# ---------------------------------------------------------------------------
# Accès — rien ne se lit ni ne s'écrit sans passer par ici
# ---------------------------------------------------------------------------

def _grille_de(user: User, grille_id: int, db: Session) -> Grille:
    grille = (db.query(Grille)
                .filter(Grille.id == grille_id, Grille.user_id == user.id)
                .first())
    if not grille:
        raise HTTPException(404, "Grille introuvable.")
    return grille


def _critere_de(user: User, critere_id: int, db: Session) -> GrilleCritere:
    """Le critère ET la preuve qu'il est dans une grille du professeur connecté — la jointure
    est la vérification. Interroger `grille_criteres` seul rendrait la ligne de n'importe qui."""
    critere = (db.query(GrilleCritere)
                 .join(Grille, Grille.id == GrilleCritere.grille_id)
                 .filter(GrilleCritere.id == critere_id, Grille.user_id == user.id)
                 .first())
    if not critere:
        raise HTTPException(404, "Critère introuvable.")
    return critere


def _niveau_de(user: User, niveau_id: int, db: Session) -> GrilleNiveauMaitrise:
    niveau = (db.query(GrilleNiveauMaitrise)
                .join(Grille, Grille.id == GrilleNiveauMaitrise.grille_id)
                .filter(GrilleNiveauMaitrise.id == niveau_id, Grille.user_id == user.id)
                .first())
    if not niveau:
        raise HTTPException(404, "Niveau de maîtrise introuvable.")
    return niveau


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

def _tableau(grille: Grille, db: Session) -> dict:
    """La grille ENTIÈRE, telle que l'écran la dessine : les colonnes, les lignes, et les cases.

    Les descripteurs sont rendus indexés par l'ID de leur colonne, pas par son libellé : un
    libellé se renomme, un identifiant non. L'écran qui a la grille en main a déjà les deux."""
    niveaux = (db.query(GrilleNiveauMaitrise)
                 .filter(GrilleNiveauMaitrise.grille_id == grille.id)
                 .order_by(GrilleNiveauMaitrise.ordre, GrilleNiveauMaitrise.id)
                 .all())
    criteres = (db.query(GrilleCritere)
                  .filter(GrilleCritere.grille_id == grille.id)
                  .order_by(GrilleCritere.ordre, GrilleCritere.id)
                  .all())
    ids_criteres = [c.id for c in criteres]
    cases: dict[int, dict[str, str]] = {cid: {} for cid in ids_criteres}
    if ids_criteres:
        for cellule in (db.query(GrilleCellule)
                          .filter(GrilleCellule.critere_id.in_(ids_criteres))
                          .all()):
            cases[cellule.critere_id][str(cellule.niveau_maitrise_id)] = cellule.descripteur

    return {
        "id": grille.id,
        "titre": grille.titre,
        "contexte": grille.contexte,
        "matiere": grille.matiere,
        "niveau": grille.niveau,
        "niveaux_maitrise": [
            {"id": n.id, "libelle": n.libelle, "points": n.points, "ordre": n.ordre}
            for n in niveaux
        ],
        "criteres": [
            {"id": c.id, "libelle": c.libelle, "poids": c.poids, "ordre": c.ordre,
             "descripteurs": cases.get(c.id, {})}
            for c in criteres
        ],
    }


@router.get("/contenus/grilles")
def lister_grilles(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """La liste, sans les cases : une liste n'a pas besoin de charger trente descripteurs par
    ligne pour afficher un titre et une date. Les compteurs se comptent, ils ne se stockent pas."""
    grilles = (db.query(Grille)
                 .filter(Grille.user_id == user.id)
                 .order_by(Grille.updated_at.desc())
                 .all())
    if not grilles:
        return []
    ids = [g.id for g in grilles]
    nb_criteres: dict[int, int] = {gid: 0 for gid in ids}
    for gid, in db.query(GrilleCritere.grille_id).filter(GrilleCritere.grille_id.in_(ids)).all():
        nb_criteres[gid] += 1
    nb_niveaux: dict[int, int] = {gid: 0 for gid in ids}
    for gid, in (db.query(GrilleNiveauMaitrise.grille_id)
                   .filter(GrilleNiveauMaitrise.grille_id.in_(ids)).all()):
        nb_niveaux[gid] += 1

    return [
        {"id": g.id, "titre": g.titre, "matiere": g.matiere, "niveau": g.niveau,
         "nb_criteres": nb_criteres[g.id], "nb_niveaux": nb_niveaux[g.id],
         "created_at": g.created_at.isoformat() if g.created_at else None,
         "updated_at": g.updated_at.isoformat() if g.updated_at else None}
        for g in grilles
    ]


@router.get("/contenus/grilles/{grille_id}")
def lire_grille(
    grille_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _tableau(_grille_de(user, grille_id, db), db)


# ---------------------------------------------------------------------------
# Génération — le modèle écrit, le serveur range
# ---------------------------------------------------------------------------

def _lignes_du_modele(data: dict) -> tuple[str, list[dict], list[dict]]:
    """Le JSON du modèle, relu et ramené à ce qui est écrivable. Rien n'est cru sur parole.

    CE QUE LE SERVEUR REFUSE : une grille sans critère ou sans niveau de maîtrise (ce n'est pas
    une grille), et les débordements au-delà des bornes. CE QU'IL ÉCARTE EN SILENCE : un
    descripteur dont la clé ne correspond à aucun niveau déclaré. Le prompt exige que les clés
    reprennent les libellés, mais une consigne n'est pas une garantie — le modèle peut traduire
    ou abréger. Une case dont on ne sait pas de quelle colonne elle parle ne s'écrit pas : le
    professeur la remplira, et c'est mieux qu'une case posée dans la mauvaise colonne.

    LES DOUBLONS DE LIBELLÉ SONT FUSIONNÉS et non refusés : la table les interdit (contrainte
    d'unicité), et faire échouer toute une génération sur deux colonnes homonymes coûterait au
    professeur un appel qu'il a déjà payé."""
    titre = str(data.get("titre") or "").strip()

    niveaux: list[dict] = []
    vus: set[str] = set()
    for brut in data.get("niveaux_maitrise") or []:
        if not isinstance(brut, dict):
            continue
        libelle = str(brut.get("libelle") or "").strip()[:64]
        if not libelle or libelle.casefold() in vus:
            continue
        vus.add(libelle.casefold())
        try:
            points = float(brut.get("points") or 0)
        except (TypeError, ValueError):
            points = 0.0
        niveaux.append({"libelle": libelle, "points": points})
        if len(niveaux) >= MAX_NIVEAUX:
            break

    connus = {n["libelle"].casefold(): n["libelle"] for n in niveaux}

    criteres: list[dict] = []
    for brut in data.get("criteres") or []:
        if not isinstance(brut, dict):
            continue
        libelle = str(brut.get("libelle") or "").strip()
        if not libelle:
            continue
        try:
            poids = float(brut.get("poids") or 1)
        except (TypeError, ValueError):
            poids = 1.0
        descripteurs: dict[str, str] = {}
        source = brut.get("descripteurs")
        if isinstance(source, dict):
            for cle, texte in source.items():
                vrai = connus.get(str(cle).strip().casefold())
                if vrai is None:
                    continue          # colonne inconnue : la case n'est pas écrite
                texte = str(texte or "").strip()
                if texte:
                    descripteurs[vrai] = texte
        criteres.append({"libelle": libelle, "poids": poids, "descripteurs": descripteurs})
        if len(criteres) >= MAX_CRITERES:
            break

    if not niveaux or not criteres:
        raise ValueError("grille sans critère ou sans niveau de maîtrise")
    return titre, niveaux, criteres


def _ecrire_grille(db: Session, user: User, matiere: str | None, niveau: str,
                   demande: str, titre: str, niveaux: list[dict],
                   criteres: list[dict]) -> Grille:
    """La grille entière, écrite en UNE transaction. Une grille à moitié écrite — des colonnes
    sans lignes, des lignes sans cases — n'est pas un état que le professeur doit pouvoir voir."""
    grille = Grille(
        user_id=user.id,
        titre=titre or demande[:120],
        contexte=demande,
        matiere=matiere or None,
        niveau=niveau,
    )
    db.add(grille)
    db.flush()

    par_libelle: dict[str, int] = {}
    for rang, n in enumerate(niveaux):
        ligne = GrilleNiveauMaitrise(grille_id=grille.id, libelle=n["libelle"],
                                     points=n["points"], ordre=rang)
        db.add(ligne)
        db.flush()
        par_libelle[n["libelle"]] = ligne.id

    for rang, c in enumerate(criteres):
        critere = GrilleCritere(grille_id=grille.id, libelle=c["libelle"],
                                poids=c["poids"], ordre=rang)
        db.add(critere)
        db.flush()
        for libelle, texte in c["descripteurs"].items():
            db.add(GrilleCellule(critere_id=critere.id,
                                 niveau_maitrise_id=par_libelle[libelle],
                                 descripteur=texte))

    db.commit()
    return grille


@router.post("/contenus/grilles/proposer-idee", response_model=GrilleIdeeReponse)
def proposer_idee_grille(
    req: GrilleIdee,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """« Propose-moi une idée » — le professeur ne sait pas quoi évaluer : il tape un thème dans
    la fenêtre, aSchool lui rend la DEMANDE qu'il aurait écrite lui-même. Elle s'affiche dans la
    zone de l'écran, il la relit, la modifie, puis « Générer la grille » fait le reste. Ce bouton
    ne rend AUCUNE grille : il amorce la zone, rien de plus.

    LE THÈME SERT DEUX FOIS, et c'est tout le dispositif : il est la requête envoyée au
    référentiel (sans lui, les extraits seraient pris au hasard du document entier et l'idée
    serait quelconque), puis il entre dans le prompt pour que l'idée porte sur ce thème.

    RÈGLE D'OR, la même que `generer_grille` : rien d'assez pertinent au seuil du référentiel
    (`referentiels.score_min`) → on n'invente RIEN et `generate` n'est pas appelé. La différence
    est la FORME de la réponse — `available:false` avec son message, pas une erreur : la fenêtre
    reste ouverte, le professeur reformule son thème et relance autant qu'il veut. Ces essais ne
    coûtent rien, ils s'arrêtent après la recherche."""
    theme = req.theme.strip()
    if not theme:
        raise HTTPException(400, "Dites en deux mots sur quoi porte l'évaluation.")

    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    resolu = _resolve_collection(db, niveau)
    if resolu is None:
        return GrilleIdeeReponse(available=False, message=_AUCUN_REFERENTIEL_POUR_IDEE)
    collection, filtres, seuil = resolu

    chunks = retrieve_pg(collection, theme, filters=filtres, top_k=get_rag_top_k(db),
                         schema=schema_de_session(db), annee=niveau, matiere=matiere)
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        return GrilleIdeeReponse(available=False, message=_AUCUN_EXTRAIT_POUR_IDEE)

    prompt = build_grille_idee_prompt(db, chunks, matiere=matiere or "", niveau=niveau,
                                      demande=theme)
    # Les règles de l'établissement s'appliquent par-dessus le programme officiel, ici comme dans
    # toute génération — l'idée proposée ne peut pas ignorer ce que l'école impose.
    prompt = ajouter_cahier_au_prompt(db, prompt, texte_cahier_du_profil(db, user))

    try:
        texte = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db),
                         voies_fournisseurs=liste_fournisseurs(db), model=get_ai_model(db),
                         max_tokens=get_max_tokens(db, "grille_idee"),
                         temperature=get_temperature(db), retry_max=get_retry_max(db),
                         retry_wait_max=get_retry_wait_max(db), outil="grille_idee")
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))   # surchargé : transitoire, pas une panne
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    texte = (texte or "").strip()
    if not texte:
        raise HTTPException(500, "Le modèle n'a rien retourné. Réessayez.")
    return GrilleIdeeReponse(available=True, texte=texte)


@router.post("/contenus/grilles/generer")
def generer_grille(
    req: GrilleGeneration,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """« Générer la grille » — le modèle écrit, le serveur range, la grille NAÎT en base.

    PAS DE STREAMING, contrairement à la séance. Le flux sert à voir un texte s'écrire ; ici la
    réponse est un JSON dont rien n'est affichable tant qu'il n'est pas complet. Une barre
    d'attente dit la même chose sans prétendre montrer ce qui n'existe pas encore.

    RÈGLE D'OR, celle de tout ce qui s'ancre sur le programme : pas de référentiel pour ce
    couple, ou rien d'assez pertinent au seuil (`referentiels.score_min`) → on le DIT, et
    `generate` n'est pas appelé (rien n'est payé pour une génération qu'on sait hors sol)."""
    demande = req.texte.strip()
    if not demande:
        raise HTTPException(400, "Dites ce que la grille doit évaluer.")

    # Couple résolu EN BASE : l'écran n'envoie pas matière/niveau, le serveur ne fait pas
    # confiance au corps de la requête.
    matiere, niveau, _ = couple_de_travail(db, user)
    if not niveau:
        raise HTTPException(400, "Complétez d'abord votre profil (matière et niveau).")

    resolu = _resolve_collection(db, niveau)
    if resolu is None:
        raise HTTPException(400, "Aucun référentiel officiel n'est encore en place pour votre "
                                 "niveau : la grille ne peut pas s'appuyer sur le programme.")
    collection, filtres, seuil = resolu

    chunks = retrieve_pg(collection, demande, filters=filtres, top_k=get_rag_top_k(db),
                         schema=schema_de_session(db), annee=niveau, matiere=matiere)
    chunks = [c for c in chunks if c.get("score") is not None and c["score"] >= seuil]
    if not chunks:
        raise HTTPException(400, "aSchool n'a pas trouvé, dans le référentiel officiel, de "
                                 "passage assez pertinent. Reformulez votre demande avec des "
                                 "termes plus proches du programme.")

    prompt = build_grille_prompt(db, chunks, matiere=matiere or "", niveau=niveau, texte=demande)
    # Les règles de l'établissement s'appliquent PAR-DESSUS le programme officiel, ici comme
    # dans toutes les générations de contenu.
    prompt = ajouter_cahier_au_prompt(db, prompt, texte_cahier_du_profil(db, user))

    try:
        brut = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db),
                        voies_fournisseurs=liste_fournisseurs(db), model=get_ai_model(db),
                        max_tokens=get_max_tokens(db, "grille_generation"),
                        temperature=get_temperature(db), retry_max=get_retry_max(db),
                        retry_wait_max=get_retry_wait_max(db), outil="grille_generation")
        titre, niveaux, criteres = _lignes_du_modele(json_du_modele(brut))
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))   # surchargé : transitoire, pas une panne
    except ValueError:
        raise HTTPException(500, "Le modèle n'a pas retourné une grille exploitable. Réessayez.")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    grille = _ecrire_grille(db, user, matiere, niveau, demande, titre, niveaux, criteres)
    return _tableau(grille, db)


# ---------------------------------------------------------------------------
# Écriture au geste
# ---------------------------------------------------------------------------

# LES ROUTES LITTÉRALES PASSENT AVANT LES ROUTES À PARAMÈTRE, et ce n'est pas une question de
# style : FastAPI essaie les chemins DANS L'ORDRE DE DÉCLARATION. `/contenus/grilles/{grille_id}`
# déclarée d'abord attrape « cellules » comme identifiant, échoue à le convertir en entier, et
# rend 422 — sans jamais essayer la route suivante. Ne pas remettre ce bloc plus bas.

@router.put("/contenus/grilles/cellules")
def ecrire_cellule(
    corps: CelluleCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Le descripteur d'UNE case — le geste le plus fréquent de l'écran.

    Le critère ET la colonne sont vérifiés comme appartenant au professeur, et comme étant de la
    MÊME grille : sans ce second contrôle, on pourrait écrire au croisement de deux grilles
    différentes, c'est-à-dire nulle part.

    DESCRIPTEUR VIDÉ = LIGNE SUPPRIMÉE. Une case vide n'a pas de ligne (l'absence est le vide) :
    garder une ligne à texte vide ferait deux façons de dire « rien », et la lecture devrait
    connaître les deux."""
    critere = _critere_de(user, corps.critere_id, db)
    niveau = _niveau_de(user, corps.niveau_maitrise_id, db)
    if critere.grille_id != niveau.grille_id:
        raise HTTPException(400, "Ce critère et ce niveau de maîtrise ne sont pas dans la même grille.")

    texte = corps.descripteur.strip()
    cellule = (db.query(GrilleCellule)
                 .filter(GrilleCellule.critere_id == critere.id,
                         GrilleCellule.niveau_maitrise_id == niveau.id)
                 .first())
    if not texte:
        if cellule:
            db.delete(cellule)
            db.commit()
        return {"ok": True}
    if cellule:
        cellule.descripteur = texte
    else:
        db.add(GrilleCellule(critere_id=critere.id, niveau_maitrise_id=niveau.id,
                             descripteur=texte))
    db.commit()
    return {"ok": True}

@router.put("/contenus/grilles/{grille_id}")
def modifier_entete(
    grille_id: int,
    corps: GrilleEntete,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    grille = _grille_de(user, grille_id, db)
    titre = corps.titre.strip()
    if not titre:
        raise HTTPException(400, "Le titre ne peut pas être vide.")
    grille.titre = titre
    grille.contexte = corps.contexte.strip()
    db.commit()
    return {"ok": True}


@router.delete("/contenus/grilles/{grille_id}")
def supprimer_grille(
    grille_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SUPPRIMER VEUT DIRE SUPPRIMER : un vrai DELETE, jamais un drapeau caché. Les critères,
    les colonnes et les cases suivent par CASCADE."""
    db.delete(_grille_de(user, grille_id, db))
    db.commit()
    return {"ok": True}


@router.post("/contenus/grilles/{grille_id}/dupliquer")
def dupliquer_grille(
    grille_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """La même grille, pour une autre classe. COPIE COMPLÈTE et indépendante : les deux vivront
    leur vie, et retoucher l'une ne doit pas toucher l'autre."""
    source = _grille_de(user, grille_id, db)
    copie = Grille(user_id=user.id, titre=f"{source.titre} (copie)", contexte=source.contexte,
                   matiere=source.matiere, niveau=source.niveau)
    db.add(copie)
    db.flush()

    # Les colonnes d'abord : les cases ont besoin de leurs nouveaux identifiants.
    correspondance: dict[int, int] = {}
    for n in (db.query(GrilleNiveauMaitrise)
                .filter(GrilleNiveauMaitrise.grille_id == source.id)
                .order_by(GrilleNiveauMaitrise.ordre, GrilleNiveauMaitrise.id).all()):
        neuf = GrilleNiveauMaitrise(grille_id=copie.id, libelle=n.libelle,
                                    points=n.points, ordre=n.ordre)
        db.add(neuf)
        db.flush()
        correspondance[n.id] = neuf.id

    for c in (db.query(GrilleCritere)
                .filter(GrilleCritere.grille_id == source.id)
                .order_by(GrilleCritere.ordre, GrilleCritere.id).all()):
        neuf = GrilleCritere(grille_id=copie.id, libelle=c.libelle, poids=c.poids, ordre=c.ordre)
        db.add(neuf)
        db.flush()
        for cellule in db.query(GrilleCellule).filter(GrilleCellule.critere_id == c.id).all():
            cible = correspondance.get(cellule.niveau_maitrise_id)
            if cible is not None:
                db.add(GrilleCellule(critere_id=neuf.id, niveau_maitrise_id=cible,
                                     descripteur=cellule.descripteur))

    db.commit()
    return _tableau(copie, db)


def _rang_suivant(db: Session, modele, grille_id: int) -> int:
    rangs = [r for r, in db.query(modele.ordre).filter(modele.grille_id == grille_id).all()]
    return (max(rangs) + 1) if rangs else 0


@router.post("/contenus/grilles/{grille_id}/criteres")
def ajouter_critere(
    grille_id: int,
    corps: CritereCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    grille = _grille_de(user, grille_id, db)
    critere = GrilleCritere(
        grille_id=grille.id,
        libelle=corps.libelle.strip(),
        poids=corps.poids,
        ordre=corps.ordre if corps.ordre is not None else _rang_suivant(db, GrilleCritere, grille.id),
    )
    db.add(critere)
    db.commit()
    return {"id": critere.id}


@router.put("/contenus/grilles/criteres/{critere_id}")
def modifier_critere(
    critere_id: int,
    corps: CritereCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    critere = _critere_de(user, critere_id, db)
    critere.libelle = corps.libelle.strip()
    critere.poids = corps.poids
    if corps.ordre is not None:
        critere.ordre = corps.ordre
    db.commit()
    return {"ok": True}


@router.delete("/contenus/grilles/criteres/{critere_id}")
def supprimer_critere(
    critere_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """La ligne s'en va, ses cases avec elle (CASCADE) : une case sans critère ne veut rien dire."""
    db.delete(_critere_de(user, critere_id, db))
    db.commit()
    return {"ok": True}


@router.post("/contenus/grilles/{grille_id}/niveaux")
def ajouter_niveau(
    grille_id: int,
    corps: NiveauCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    grille = _grille_de(user, grille_id, db)
    libelle = corps.libelle.strip()
    if not libelle:
        raise HTTPException(400, "Donnez un nom à ce niveau de maîtrise.")
    # L'unicité est en base ; on la dit ici avec les mots du professeur plutôt que de le laisser
    # recevoir une erreur de contrainte.
    deja = (db.query(GrilleNiveauMaitrise)
              .filter(GrilleNiveauMaitrise.grille_id == grille.id,
                      GrilleNiveauMaitrise.libelle == libelle)
              .first())
    if deja:
        raise HTTPException(400, f"« {libelle} » existe déjà dans cette grille.")
    niveau = GrilleNiveauMaitrise(
        grille_id=grille.id, libelle=libelle, points=corps.points,
        ordre=corps.ordre if corps.ordre is not None else _rang_suivant(db, GrilleNiveauMaitrise, grille.id),
    )
    db.add(niveau)
    db.commit()
    return {"id": niveau.id}


@router.put("/contenus/grilles/niveaux/{niveau_id}")
def modifier_niveau(
    niveau_id: int,
    corps: NiveauCorps,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    niveau = _niveau_de(user, niveau_id, db)
    libelle = corps.libelle.strip()
    if not libelle:
        raise HTTPException(400, "Le nom d'un niveau de maîtrise ne peut pas être vide.")
    deja = (db.query(GrilleNiveauMaitrise)
              .filter(GrilleNiveauMaitrise.grille_id == niveau.grille_id,
                      GrilleNiveauMaitrise.libelle == libelle,
                      GrilleNiveauMaitrise.id != niveau.id)
              .first())
    if deja:
        raise HTTPException(400, f"« {libelle} » existe déjà dans cette grille.")
    niveau.libelle = libelle
    niveau.points = corps.points
    if corps.ordre is not None:
        niveau.ordre = corps.ordre
    db.commit()
    return {"ok": True}


@router.delete("/contenus/grilles/niveaux/{niveau_id}")
def supprimer_niveau(
    niveau_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """La colonne s'en va, la case de chaque critère avec elle (CASCADE)."""
    db.delete(_niveau_de(user, niveau_id, db))
    db.commit()
    return {"ok": True}
