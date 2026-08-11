"""Les énoncés d'exemple de l'écran « Détecter les ambiguïtés » — côté ADMIN.

Un exemple par couple, écrit d'avance et rangé en base (table `ambiguite_exemples`). Il n'est
JAMAIS généré par l'application : l'admin copie ici le prompt rempli pour un couple, l'exécute
hors de l'application, et recolle le résultat. L'application ne paie donc aucun appel pour un
texte qui ne change pas, et le prof retrouve le même énoncé à chaque fois.

Le couple tient dans `matiere_id` seul : une matière appartient au référentiel d'un niveau
(voir `Matiere`), le niveau est déjà dedans.

Le prompt rendu par `/admin/ambiguite-exemples/{matiere_id}/prompt` porte les mêmes types
d'ambiguïté ET les mêmes vérifications que l'analyse elle-même, lus dans le même catalogue :
l'exemple contient donc exactement ce que l'outil sait chercher.
"""
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.analyse.ambiguites import CODE_CRITERE_LIBRE, criteres_ambiguite
from backend.core.database import get_db
from backend.core.models_db import (AmbiguiteExemple, Matiere, Niveau, Referentiel,
                                    ReferentielChunk)
from backend.llm.generator import generate, LLMRateLimitError
from backend.systeme.admin import (_require_admin, get_ai_model, get_ai_provider,
                                   get_cle_texte, get_max_tokens, get_prompt,
                                   get_retry_max, get_retry_wait_max, get_temperature)

router = APIRouter()

# Les deux blocs que le prompt impose à sa sortie. Le résultat se recolle d'un bloc : le
# serveur le découpe, l'admin n'a pas à séparer les deux champs à la main.
_BLOC_ENONCE = "=== ENONCE ==="
_BLOC_DEFAUTS = "=== DEFAUTS ==="
# Le bloc où le rédacteur DÉCLARE les matières qu'il n'a pas su traiter, au lieu de deviner.
# Il ne porte aucun énoncé : on l'enlève avant de découper, et on en lit les noms pour le
# compte rendu.
_BLOC_NON_TRAITEES = "=== NON TRAITEES ==="


class ExempleLigne(BaseModel):
    matiere_id: int
    matiere: str
    niveau: str
    texte: str
    defauts: str
    # Trois états à l'écran, et non deux : écrit / désactivé / manquant. Un exemple désactivé
    # a bien un texte — c'est le professeur qui ne le reçoit plus.
    actif: bool = True


class ExempleEcriture(BaseModel):
    texte: str = Field(min_length=1)
    defauts: str = ""


class ColleBrut(BaseModel):
    brut: str = Field(min_length=1)


def _couples(db: Session):
    """Tous les couples du programme : une matière active, avec le niveau de son référentiel."""
    return (db.query(Matiere, Niveau)
              .join(Referentiel, Referentiel.id == Matiere.referentiel_id)
              .join(Niveau, Niveau.id == Referentiel.niveau_id)
              .filter(Matiere.actif.is_(True))
              .order_by(Niveau.ordre, Niveau.nom, Matiere.ordre, Matiere.nom)
              .all())


def _couple(db: Session, matiere_id: int):
    ligne = (db.query(Matiere, Niveau)
               .join(Referentiel, Referentiel.id == Matiere.referentiel_id)
               .join(Niveau, Niveau.id == Referentiel.niveau_id)
               .filter(Matiere.id == matiere_id)
               .first())
    if not ligne:
        raise HTTPException(404, "Cette matière n'existe pas (ou n'a pas de référentiel).")
    return ligne


def decouper_colle(brut: str) -> tuple[str, str]:
    """Le collé de l'admin, coupé en (énoncé, défauts) sur les deux marqueurs du prompt.

    Sans marqueur, on ne devine pas : tout part dans l'énoncé et les défauts restent vides —
    un texte tronqué au mauvais endroit serait pire qu'un champ vide que l'admin voit."""
    if _BLOC_ENONCE not in brut:
        return brut.strip(), ""
    apres = brut.split(_BLOC_ENONCE, 1)[1]
    if _BLOC_DEFAUTS not in apres:
        return apres.strip(), ""
    enonce, defauts = apres.split(_BLOC_DEFAUTS, 1)
    return enonce.strip(), defauts.strip()


@router.get("/admin/ambiguite-exemples", response_model=list[ExempleLigne])
def liste_exemples(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """TOUS les couples, avec ou sans exemple — c'est l'écran qui montre ce qui manque. Une
    liste des seuls exemples écrits cacherait précisément le travail restant."""
    ecrits = {e.matiere_id: e for e in db.query(AmbiguiteExemple).all()}
    return [
        ExempleLigne(
            matiere_id=matiere.id,
            matiere=matiere.nom,
            niveau=niveau.nom,
            texte=ecrits[matiere.id].texte if matiere.id in ecrits else "",
            defauts=ecrits[matiere.id].defauts if matiere.id in ecrits else "",
            actif=ecrits[matiere.id].actif if matiere.id in ecrits else True,
        )
        for matiere, niveau in _couples(db)
    ]


@router.get("/admin/ambiguite-exemples/{matiere_id}/prompt")
def prompt_exemple(matiere_id: int, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Le prompt PRÊT À COPIER pour ce couple : plus qu'à l'exécuter et recoller la réponse."""
    matiere, niveau = _couple(db, matiere_id)

    lignes = []
    for c in criteres_ambiguite(db):
        if c.code == CODE_CRITERE_LIBRE:
            continue    # le critère libre appartient au prof, il n'a rien à faire dans un exemple
        lignes.append(f"- {c.label}")
        if c.verification.strip():
            lignes.append(f"  Ce qui doit être repérable : {c.verification.strip()}")

    return {
        "matiere": matiere.nom,
        "niveau": niveau.nom,
        "prompt": get_prompt(db, "ambiguite_exemple").format(
            matiere=matiere.nom, niveau=niveau.nom, criteres="\n".join(lignes),
        ),
    }


@router.put("/admin/ambiguite-exemples/{matiere_id}", response_model=ExempleLigne)
def enregistrer_exemple(matiere_id: int, corps: ExempleEcriture,
                        db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    matiere, niveau = _couple(db, matiere_id)
    ligne = db.query(AmbiguiteExemple).filter(AmbiguiteExemple.matiere_id == matiere_id).first()
    if ligne:
        ligne.texte = corps.texte.strip()
        ligne.defauts = corps.defauts.strip()
        # Réécrire un exemple désactivé, c'est dire « voilà le bon ». Le laisser éteint le rendrait
        # invisible sans raison, et l'admin chercherait longtemps pourquoi le prof ne le voit pas.
        ligne.actif = True
    else:
        ligne = AmbiguiteExemple(matiere_id=matiere_id, texte=corps.texte.strip(),
                                 defauts=corps.defauts.strip())
        db.add(ligne)
    db.commit()
    return ExempleLigne(matiere_id=matiere_id, matiere=matiere.nom, niveau=niveau.nom,
                        texte=ligne.texte, defauts=ligne.defauts, actif=ligne.actif)


@router.post("/admin/ambiguite-exemples/{matiere_id}/coller", response_model=ExempleLigne)
def coller_exemple(matiere_id: int, corps: ColleBrut,
                   db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """La réponse du modèle collée d'un bloc, découpée ici sur les marqueurs du prompt."""
    texte, defauts = decouper_colle(corps.brut)
    if not texte:
        raise HTTPException(400, "Le texte collé ne contient aucun énoncé.")
    return enregistrer_exemple(matiere_id, ExempleEcriture(texte=texte, defauts=defauts), db, None)


class Bascule(BaseModel):
    actif: bool


@router.put("/admin/ambiguite-exemples/{matiere_id}/actif", response_model=ExempleLigne)
def basculer_exemple(matiere_id: int, corps: Bascule,
                     db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Allume ou éteint un exemple. Le texte ne bouge pas — c'est tout l'intérêt.

    Découvrir qu'un exemple est faux imposait jusqu'ici de le supprimer, donc de perdre ce qu'il
    fallait corriger. On l'éteint, le professeur cesse de le voir, et on le reprend quand on a
    le temps. Le DELETE existe toujours, pour de bon."""
    matiere, niveau = _couple(db, matiere_id)
    ligne = db.query(AmbiguiteExemple).filter(AmbiguiteExemple.matiere_id == matiere_id).first()
    if not ligne:
        raise HTTPException(404, "Ce couple n'a pas d'exemple.")
    ligne.actif = corps.actif
    db.commit()
    return ExempleLigne(matiere_id=matiere_id, matiere=matiere.nom, niveau=niveau.nom,
                        texte=ligne.texte, defauts=ligne.defauts, actif=ligne.actif)


@router.delete("/admin/ambiguite-exemples/{matiere_id}")
def supprimer_exemple(matiere_id: int, db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    """Supprimer veut dire supprimer : la ligne part, le couple redevient sans exemple."""
    ligne = db.query(AmbiguiteExemple).filter(AmbiguiteExemple.matiere_id == matiere_id).first()
    if not ligne:
        raise HTTPException(404, "Ce couple n'a pas d'exemple.")
    db.delete(ligne)
    db.commit()
    return {"supprime": True}


# ── Tout un référentiel d'un coup ───────────────────────────────────────────────────────────
#
# 47 couples, c'était 47 aller-retours. La cartouche « Ambiguïtés » de la procédure Référentiel
# en fait UN par référentiel : elle donne le prompt de toutes ses matières, et elle avale le
# résultat entier.

def _cle(texte: str) -> str:
    """De quoi rapprocher « Langue vivante étrangère : anglais » de sa jumelle en base malgré un
    accent, une majuscule ou une espace de plus. On ne rapproche pas plus loin que ça : au-delà,
    ce n'est plus un rapprochement, c'est une devinette."""
    sans_accent = "".join(c for c in unicodedata.normalize("NFD", texte)
                          if unicodedata.category(c) != "Mn")
    return " ".join(sans_accent.lower().replace("\u2019", "'").split())


def decouper_referentiel(brut: str) -> tuple[list[tuple[str, str, str]], list[str]]:
    """Le collé de tout un référentiel → ([(matière, énoncé, défauts)], [matières déclarées non traitées]).

    Le nom de matière est lu sur les lignes « ### … » ; un « ## niveau » de tête et une éventuelle
    numérotation « 3. » sont ignorés — le référentiel est déjà connu, c'est la cartouche ouverte."""
    texte = brut.replace("\r\n", "\n")

    non_traitees: list[str] = []
    if _BLOC_NON_TRAITEES in texte:
        texte, fin = texte.split(_BLOC_NON_TRAITEES, 1)
        for ligne in fin.split("\n"):
            nom = ligne.strip().lstrip("-").strip()
            if not nom:
                continue
            # « Nom — ce qui manquait » : seul le nom sert à rapprocher.
            non_traitees.append(re.split(r"\s+[\u2014-]\s+", nom, maxsplit=1)[0].strip())

    blocs: list[tuple[str, str, str]] = []
    matiere, courant = None, []
    for ligne in texte.split("\n"):
        if ligne.startswith("### "):
            if matiere:
                blocs.append((matiere, *decouper_colle("\n".join(courant))))
            matiere = re.sub(r"^\d+\.\s*", "", ligne[4:]).strip()
            courant = []
        elif matiere is not None:
            courant.append(ligne)
    if matiere:
        blocs.append((matiere, *decouper_colle("\n".join(courant))))
    return blocs, non_traitees


class ColleReferentiel(BaseModel):
    cycle_id: int
    niveau: str
    brut: str = Field(min_length=1)


def _referentiel(db: Session, cycle_id: int, niveau: str):
    """Le référentiel du couple ouvert à l'écran, avec ses matières au programme."""
    niv = (db.query(Niveau)
             .filter(Niveau.nom == (niveau or "").strip(), Niveau.cycle_id == cycle_id).first())
    ref = db.query(Referentiel).filter(Referentiel.niveau_id == niv.id).first() if niv else None
    if not ref:
        raise HTTPException(404, "Ce couple n'a pas encore de référentiel.")
    matieres = (db.query(Matiere)
                  .filter(Matiere.referentiel_id == ref.id, Matiere.actif.is_(True))
                  .order_by(Matiere.ordre, Matiere.id).all())
    return niv, ref, matieres


@router.get("/admin/referentiels/ambiguites/etat", dependencies=[Depends(_require_admin)])
def etat_exemples_referentiel(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Ce que la cartouche affiche sans rien demander : combien de matières ont leur exemple."""
    _niv, _ref, matieres = _referentiel(db, cycle_id, niveau)
    # « Écrit » veut dire SERVI au professeur : un exemple éteint ne fait pas avancer le compte,
    # sinon la pastille verte annoncerait un travail que le prof ne voit pas.
    ecrits = {e.matiere_id for e in db.query(AmbiguiteExemple).all() if e.texte.strip() and e.actif}
    return {
        "total": len(matieres),
        "ecrits": sum(1 for m in matieres if m.id in ecrits),
        "matieres": [{"id": m.id, "nom": m.nom, "ecrit": m.id in ecrits} for m in matieres],
    }


# Combien d'extraits du référentiel accompagnent chaque matière, et jusqu'où on les cite.
# Trois suffisent à dire de quoi parle la matière ; au-delà on noie l'intitulé au lieu de
# l'éclairer, et le prompt devient illisible pour l'admin qui le relit.
_EXTRAITS_PAR_MATIERE = 3
_EXTRAIT_MAX = 700


def contexte_des_matieres(db: Session, ref: Referentiel, matieres: list[Matiere]):
    """Pour chaque matière : les passages du référentiel qui la décrivent → (avec, sans).

    Le nom seul ne suffit pas. « Langage » en petite enfance a été compris « langage de
    programmation », et l'exercice en C est entré en base sans que personne le voie. Les unités
    découpées du référentiel, elles, disent ce que la matière recouvre : on les cherche par
    proximité de sens (le même moteur que le RAG du prof, embeddings locaux — aucun appel payé).

    Une matière dont rien ne ressort au-dessus du seuil du référentiel (`score_min`) part dans
    `sans` : elle n'entrera PAS dans le prompt, et son couple restera vide. Vide plutôt que faux —
    un couple faux est invisible, le professeur le lirait sans jamais savoir."""
    from backend.rag.embeddings import embed_texts        # import tardif : charge le modèle local

    if not matieres:
        return [], []
    if not db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == ref.id).first():
        raise HTTPException(400, "Ce référentiel n'a pas encore été découpé — les extraits qui "
                                 "décrivent chaque matière viennent de sa découpe.")

    seuil = float(ref.score_min or 0)
    vecteurs = embed_texts([m.nom for m in matieres])

    avec, sans = [], []
    for matiere, vecteur in zip(matieres, vecteurs):
        distance = ReferentielChunk.embedding.cosine_distance(vecteur).label("d")
        lignes = (db.query(ReferentielChunk.texte, distance)
                    .filter(ReferentielChunk.referentiel_id == ref.id)
                    .order_by(distance).limit(_EXTRAITS_PAR_MATIERE).all())
        extraits = [t.strip()[:_EXTRAIT_MAX] for t, d in lignes if d is not None and (1 - d) >= seuil]
        if extraits:
            avec.append((matiere, extraits))
        else:
            sans.append(matiere)
    return avec, sans


def _prompt_du_referentiel(db: Session, cycle_id: int, niveau: str) -> dict:
    """Le prompt de TOUT le référentiel — LE MÊME pour les deux voies.

    Gratuite (l'admin l'exécute chez lui) ou payante (l'application appelle) : c'est le même
    texte, sinon les deux voies ne rendraient pas la même chose et la seconde deviendrait la
    vraie, l'autre un pis-aller."""
    niv, ref, matieres = _referentiel(db, cycle_id, niveau)
    if not matieres:
        raise HTTPException(400, "Ce référentiel n'a encore aucune matière au programme.")

    avec, sans = contexte_des_matieres(db, ref, matieres)
    if not avec:
        raise HTTPException(400, "Aucune matière de ce référentiel n'est décrite par sa découpe — "
                                 "il n'y a rien sur quoi écrire un exemple.")

    types = []
    for c in criteres_ambiguite(db):
        if c.code == CODE_CRITERE_LIBRE:
            continue    # le critère libre appartient au prof, il n'a rien à faire dans un exemple
        types.append(f"- {c.label}")
        if c.verification.strip():
            types.append(f"  Ce qui doit être repérable : {c.verification.strip()}")

    blocs = []
    for matiere, extraits in avec:
        blocs.append(f"- {matiere.nom}")
        for extrait in extraits:
            # Les extraits sont indentés sous leur matière : le modèle voit d'un coup d'œil ce qui
            # appartient à laquelle, et l'admin qui relit le prompt aussi.
            blocs.append("  · " + extrait.replace("\n", " "))

    return {
        "niveau": niv.nom,
        "total": len(matieres),
        # Ce que le prompt NE demande pas : le référentiel n'en dit rien, leur couple restera vide.
        "sans_contexte": [m.nom for m in sans],
        "prompt": get_prompt(db, "ambiguite_exemples_referentiel").format(
            niveau=niv.nom,
            matieres="\n".join(blocs),
            criteres="\n".join(types),
        ),
    }


@router.get("/admin/referentiels/ambiguites/prompt", dependencies=[Depends(_require_admin)])
def prompt_exemples_referentiel(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Le prompt prêt à copier — la VOIE GRATUITE : l'admin l'exécute hors de l'application."""
    return _prompt_du_referentiel(db, cycle_id, niveau)


class GenererReferentiel(BaseModel):
    cycle_id: int
    niveau: str


@router.post("/admin/referentiels/ambiguites/generer", dependencies=[Depends(_require_admin)])
def generer_exemples_referentiel(corps: GenererReferentiel, db: Session = Depends(get_db)):
    """LA VOIE PAYANTE : l'application appelle le moteur elle-même, et écrit le résultat.

    Même prompt, même découpage, même règle qu'au collage — un seul nom de matière non reconnu
    et RIEN n'est écrit. L'appel a beau être payé, il ne s'autorise pas à deviner : un exemple
    posé sur la mauvaise matière serait invisible, et l'aurait été pour de l'argent."""
    _niv, _ref, matieres = _referentiel(db, corps.cycle_id, corps.niveau)
    prompt = _prompt_du_referentiel(db, corps.cycle_id, corps.niveau)["prompt"]

    try:
        # Même politique de rattrapage sur 429 qu'ailleurs, lue en base (`ai_retry_max`).
        brut = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db),
                        model=get_ai_model(db), max_tokens=get_max_tokens(db, "ambiguite_exemples"),
                        temperature=get_temperature(db), retry_max=get_retry_max(db),
                        retry_wait_max=get_retry_wait_max(db), outil="ambiguite_exemples")
    except LLMRateLimitError as e:
        raise HTTPException(429, str(e))   # surchargé/trop de demandes : transitoire, pas une panne
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    compte = _repartir(db, matieres, brut)
    if compte["blocs"] == 0:
        raise HTTPException(500, "Le moteur n'a rendu aucun bloc « ### matière ». "
                                 "Réessayez, ou passez par la voie gratuite pour voir sa réponse.")
    # L'appel est payé : sa réponse ne se perd pas parce qu'un nom est mal orthographié. Elle
    # revient à l'écran, l'admin la corrige et la recolle — sinon il repaierait pour la ravoir.
    compte["brut"] = "" if compte["applique"] else brut
    return compte


@router.post("/admin/referentiels/ambiguites/coller", dependencies=[Depends(_require_admin)])
def coller_exemples_referentiel(corps: ColleReferentiel, db: Session = Depends(get_db)):
    """Le résultat entier, collé d'un bloc et réparti sur les matières du référentiel ouvert.

    RIEN n'est écrit tant qu'un bloc n'a pas trouvé sa matière : un exemple posé sur la mauvaise
    matière serait invisible, le professeur le lirait sans jamais savoir qu'il n'est pas le sien.
    L'admin corrige le nom et recolle — c'est un geste, pas une perte."""
    _niv, _ref, matieres = _referentiel(db, corps.cycle_id, corps.niveau)
    compte = _repartir(db, matieres, corps.brut)
    if compte["blocs"] == 0:
        raise HTTPException(400, "Le texte collé ne contient aucun bloc « ### matière ».")
    return compte


def _repartir(db: Session, matieres: list[Matiere], brut: str) -> dict:
    """Le texte rendu → les lignes en base, quelle que soit la voie qui l'a produit."""
    index = {_cle(m.nom): m for m in matieres}

    blocs, non_traitees = decouper_referentiel(brut)

    a_ecrire, orphelins, vides = [], [], []
    for nom, enonce, defauts in blocs:
        m = index.get(_cle(nom))
        if m is None:
            orphelins.append(nom)
        elif not enonce.strip():
            vides.append(nom)
        else:
            a_ecrire.append((m, enonce.strip(), defauts.strip()))

    compte = {
        # `blocs` : combien de « ### matière » le texte portait. Zéro = ce n'est pas le bon
        # format, ce n'est pas « rien à faire » — les deux voies le traitent différemment.
        "blocs": len(blocs),
        "applique": False, "ecrits": 0, "remplaces": 0,
        "orphelins": orphelins, "vides": vides,
        "non_traitees": [n for n in non_traitees],
        # Les matières du référentiel dont le collé ne parlait pas : elles gardent ce qu'elles ont.
        "absentes": [m.nom for m in matieres
                     if all(m.id != x[0].id for x in a_ecrire)
                     and _cle(m.nom) not in {_cle(n) for n in non_traitees}],
    }
    if not blocs or orphelins or vides:
        return compte

    deja = {e.matiere_id: e for e in db.query(AmbiguiteExemple).all()}
    for m, enonce, defauts in a_ecrire:
        ligne = deja.get(m.id)
        if ligne:
            ligne.texte, ligne.defauts = enonce, defauts
            compte["remplaces"] += 1
        else:
            db.add(AmbiguiteExemple(matiere_id=m.id, texte=enonce, defauts=defauts))
            compte["ecrits"] += 1
    db.commit()
    compte["applique"] = True
    return compte
