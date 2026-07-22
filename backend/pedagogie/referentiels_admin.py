"""Étape 1 du chantier « Référentiel → matières + chunks ».

RÉCEPTION d'un référentiel officiel fourni par l'admin — par LIEN ou par DÉPÔT —,
POINT DE CONTRÔLE (aperçu pour que l'admin valide que c'est le bon document), puis
RANGEMENT + EXTRACTION du texte + ENREGISTREMENT de la provenance (table referentiels).

Périmètre étape 1 UNIQUEMENT : pas d'extraction de matières (étape 2), pas de chunks
(étape 6), pas de recherche web automatique (palier suivant, branché « devant » plus tard).
On reçoit un PDF que l'admin fournit, on le lui montre, on le range et on trace sa provenance.
"""
import json
import logging
import re
import shutil
import threading
import unicodedata
import uuid
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.database import get_db, SessionLocal
from backend.core.models_db import Cycle, Niveau, Referentiel, ReferentielChunk, Matiere, MatiereNiveau, MatiereCandidate, Setting, User, Famille, FamilleCouple, ActiviteType, ReferentielActiviteType, ActiviteSauvegardee, FewShotMilestone, TypePrecision, ReferentielTypePrecision
from backend.systeme.admin import _require_admin, get_settings_dict

router = APIRouter()
logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[2]                 # racine du projet (d:\A-SCHOOL)
REFERENTIELS_DIR = _ROOT / "REFERENTIELS"
STAGING_DIR = _ROOT / "data" / "referentiels_staging"       # PDF récupéré, en attente de validation
STAGING_DIR.mkdir(parents=True, exist_ok=True)

MAX_PDF_BYTES = 30 * 1024 * 1024   # 30 Mo : un référentiel officiel peut être lourd (BTS CIEL = 88 p.)
APERCU_LIGNES = 25                 # lignes de texte montrées à l'admin pour le contrôle


def _dossier_cle(nom: str) -> str:
    """Nom de niveau → nom de dossier-clé lisible : accents enlevés, MAJUSCULES, tout
    caractère non alphanumérique remplacé par « _ ». Ex. « Bébés (0-1 an) » →
    « BEBES_0_1_AN ». L'identifiant interne (nom_fixe) en est la version minuscule."""
    s = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()
    return s or "REFERENTIEL"


def _lire_candidates(db: Session, niveau_id: int) -> list[str]:
    """Liste des matières candidates du couple, lue EN BASE (table `matieres_candidates`,
    une ligne par niveau). L'app ne calcule JAMAIS cette liste : elle la lit. [] si aucune
    ligne pour ce niveau (ou contenu illisible). Plus de fichier matieres-candidates.json."""
    row = (db.query(MatiereCandidate)
             .filter(MatiereCandidate.niveau_id == niveau_id).first())
    if not row:
        return []
    try:
        data = json.loads(row.matieres)
    except Exception:
        return []
    return [str(m).strip() for m in (data or []) if str(m).strip()]


def _ecrire_candidates(db: Session, niveau_id: int, noms: list[str]) -> None:
    """PENDANT écriture de `_lire_candidates` : ÉCRIT les matières candidates d'un niveau EN BASE
    (table `matieres_candidates`, une ligne par niveau — `niveau_id` unique). get-or-create sur le
    niveau, `matieres` = tableau JSON de noms. Le nouveau PDF ÉCRASE la proposition précédente. La
    donnée vit à un seul endroit : get pour lire, put pour écrire, zéro copie."""
    charge = json.dumps(noms, ensure_ascii=False)
    row = db.query(MatiereCandidate).filter(MatiereCandidate.niveau_id == niveau_id).first()
    if row:
        row.matieres = charge
    else:
        db.add(MatiereCandidate(niveau_id=niveau_id, matieres=charge))
    db.commit()


def _apercu(pdf_path: Path) -> tuple[int, str]:
    """(nombre de pages, premières lignes de texte) — la matière du point de contrôle admin."""
    import pdfplumber  # import paresseux : ne pas alourdir le démarrage du serveur
    with pdfplumber.open(str(pdf_path)) as pdf:
        n_pages = len(pdf.pages)
        premier = (pdf.pages[0].extract_text() or "") if n_pages else ""
    lignes = [l for l in premier.splitlines() if l.strip()][:APERCU_LIGNES]
    return n_pages, "\n".join(lignes)


def _stage(content: bytes, filename: str, db: Session) -> dict:
    """Valide que c'est un PDF, le range en zone d'attente, renvoie l'aperçu pour le contrôle."""
    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(400, "PDF trop volumineux (maximum 30 Mo).")
    if content[:5] != b"%PDF-":
        raise HTTPException(400, "Le document récupéré n'est pas un PDF valide.")
    token = uuid.uuid4().hex
    staged = STAGING_DIR / f"{token}.pdf"
    staged.write_bytes(content)
    try:
        n_pages, apercu = _apercu(staged)
    except Exception as e:
        staged.unlink(missing_ok=True)
        raise HTTPException(400, f"Lecture du PDF impossible : {e}")
    # Plafond de pages (réglage EN BASE `depot_max_pages`, défaut 150), lu ici, au dépôt. Un document
    # trop long (ex. le Bulletin officiel entier, ~967 p.) n'est pas un référentiel de couple : on le
    # refuse AVANT tout traitement lourd — donc plus d'extraction longue, plus de timeout, plus
    # d'incohérence écran/serveur. Le comptage `n_pages` est déjà fait par _apercu (rapide).
    try:
        max_pages = int(get_settings_dict(db).get("depot_max_pages", 150))
    except (TypeError, ValueError):
        max_pages = 150
    if n_pages > max_pages:
        staged.unlink(missing_ok=True)
        raise HTTPException(
            400,
            f"Document trop long : {n_pages} pages. Veuillez déposer un document de {max_pages} pages maximum.",
        )
    return {
        "token": token,
        "filename": filename,
        "taille_ko": round(len(content) / 1024),
        "pages": n_pages,
        "apercu": apercu,
    }


# ── Récupération (lien OU dépôt) → aperçu pour le point de contrôle admin ──────

class PreparerLienBody(BaseModel):
    url: str


@router.post("/admin/referentiels/preparer-lien", dependencies=[Depends(_require_admin)])
def preparer_lien(body: PreparerLienBody, db: Session = Depends(get_db)):
    url = body.url.strip()
    if not url:
        raise HTTPException(400, "Lien vide.")
    try:
        r = httpx.get(url, follow_redirects=True, timeout=30.0)
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(400, f"Téléchargement depuis le lien impossible : {e}")
    filename = (url.rsplit("/", 1)[-1].split("?")[0]) or "referentiel.pdf"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    return _stage(r.content, filename, db)


@router.post("/admin/referentiels/preparer-depot", dependencies=[Depends(_require_admin)])
async def preparer_depot(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    return _stage(content, file.filename or "referentiel.pdf", db)


# ── Validation : range + extrait le texte + enregistre la provenance ──────────

@router.get("/admin/familles", dependencies=[Depends(_require_admin)])
def lister_familles(db: Session = Depends(get_db)):
    """Les familles de structure, lues EN BASE (aucune liste en dur)."""
    fam = db.query(Famille).order_by(Famille.id).all()
    return {"familles": [{"id": f.id, "nom": f.nom, "description": f.description, "rejet": f.rejet} for f in fam]}


@router.get("/admin/fc-autorisees", dependencies=[Depends(_require_admin)])
def lister_fc_autorisees(db: Session = Depends(get_db)):
    """Catalogue des couples (famille + niveau) lu EN BASE dans `famille_couples` (get direct, lecture
    seule) — la liste qui alimente le choix « Couple » de la procédure. Les noms famille + cycle/niveau
    ET le cycle_id sont résolus par jointure AU MOMENT DE LA LECTURE (aucune donnée recopiée). Jointures
    INTERNES : les clés étrangères de `famille_couples` garantissent que famille et niveau existent, donc
    aucune ligne orpheline à gérer. Le `cycle_id` n'est pas stocké (dérivé du niveau) : on le LIT ici."""
    rows = (db.query(FamilleCouple, Famille.nom, Cycle.id, Cycle.nom, Niveau.nom)
              .join(Famille, Famille.id == FamilleCouple.famille_id)
              .join(Niveau, Niveau.id == FamilleCouple.niveau_id)
              .join(Cycle, Cycle.id == Niveau.cycle_id)
              .order_by(Cycle.ordre, Niveau.ordre).all())
    couples = [
        {"id": fc.id, "famille_id": fc.famille_id, "niveau_id": fc.niveau_id,
         "cycle_id": cyc_id, "famille": fam_nom, "cycle": cyc_nom, "niveau": niv_nom}
        for fc, fam_nom, cyc_id, cyc_nom, niv_nom in rows
    ]
    return {"total": len(couples), "couples": couples}


@router.get("/admin/referentiels/liste", dependencies=[Depends(_require_admin)])
def lister_referentiels(db: Session = Depends(get_db)):
    """Liste des référentiels déposés (get direct, lecture seule) — pour la page « Consulter ».
    La famille se lit par jointure sur `famille_couples` via le niveau (aucune colonne famille
    sur le référentiel). Vide tant qu'aucun dépôt."""
    rows = (db.query(Referentiel, Cycle.nom, Niveau.nom, Famille.nom, Cycle.id)
              .join(Niveau, Niveau.id == Referentiel.niveau_id)
              .join(Cycle, Cycle.id == Niveau.cycle_id)
              .outerjoin(FamilleCouple, FamilleCouple.niveau_id == Referentiel.niveau_id)
              .outerjoin(Famille, Famille.id == FamilleCouple.famille_id)
              .order_by(Cycle.ordre, Niveau.ordre).all())

    # `complet` = puce de synthèse du menu Catalogues. REFLET lu en base (get), jamais recopié. Vert =
    # la procédure est ARRIVÉE AU BOUT = `decoupe_valide` (le bouton final « Valider le découpage »).
    # C'est ce booléen, et lui seul, qui pilote le vert — les étapes intermédiaires (matières, prompt)
    # se valident au fur et à mesure mais ne suffisent PAS à déclarer le référentiel complet.
    refs = [
        {"id": r.id, "cycle": cyc, "cycle_id": cyc_id, "niveau": niv, "famille": fam,
         "fichier": r.fichier, "source": r.source, "forcage_motif": r.forcage_motif,
         "complet": bool(r.decoupe_valide)}
        for r, cyc, niv, fam, cyc_id in rows
    ]
    return {"total": len(refs), "referentiels": refs}


@router.get("/admin/cycles", dependencies=[Depends(_require_admin)])
def lister_cycles_table(db: Session = Depends(get_db)):
    """Contenu de la table `cycles` (get direct, lecture seule) — fenêtre de contrôle admin."""
    cy = db.query(Cycle).order_by(Cycle.ordre).all()
    return {"total": len(cy), "cycles": [{"id": c.id, "nom": c.nom, "ordre": c.ordre} for c in cy]}


@router.get("/admin/matieres", dependencies=[Depends(_require_admin)])
def lister_matieres_table(db: Session = Depends(get_db)):
    """Contenu de la table `matieres` (get direct, lecture seule) — fenêtre de contrôle admin."""
    ma = db.query(Matiere).order_by(Matiere.ordre).all()
    return {"total": len(ma), "matieres": [{"id": m.id, "nom": m.nom, "ordre": m.ordre, "actif": m.actif} for m in ma]}


@router.get("/admin/activite-types", dependencies=[Depends(_require_admin)])
def lister_activite_types_table(db: Session = Depends(get_db)):
    """Contenu de la table `types_activite` (get direct, lecture seule) — fenêtre de contrôle admin.
    Ajoute par type `usage` (nb de références VIVANTES) + `supprimable`, CALCULÉS À LA VOLÉE (zéro copie,
    rien n'est stocké) : un type est référencé par sa CLÉ dans `activites_sauvegardees` et
    `few_shot_milestones`. supprimable = 0 usage → le front sait quel bouton poubelle griser."""
    ta = db.query(ActiviteType).order_by(ActiviteType.ordre, ActiviteType.id).all()
    usage: dict[int, int] = {}
    for tid, n in db.query(ActiviteSauvegardee.activite_type_id, func.count()).group_by(ActiviteSauvegardee.activite_type_id).all():
        usage[tid] = usage.get(tid, 0) + n
    for tid, n in db.query(FewShotMilestone.activite_type_id, func.count()).group_by(FewShotMilestone.activite_type_id).all():
        usage[tid] = usage.get(tid, 0) + n
    return {"total": len(ta), "types": [
        {"id": t.id, "label": t.label, "is_default": t.is_default, "actif": t.actif, "ordre": t.ordre,
         "origine": t.origine, "usage": usage.get(t.id, 0), "supprimable": usage.get(t.id, 0) == 0}
        for t in ta]}


@router.delete("/admin/activite-types/{type_id}", dependencies=[Depends(_require_admin)])
def supprimer_activite_type(type_id: int, db: Session = Depends(get_db)):
    """Supprime un type du catalogue `types_activite`. CONTRÔLE DELETE (règle 4) — refuse si le type est
    encore UTILISÉ, c.-à-d. référencé par sa CLÉ dans une activité sauvegardée ou un jalon few-shot. Les
    coches référentiel cascadent (FK ondelete=CASCADE) : elles ne bloquent pas. 404 si absent, 409 si utilisé."""
    t = db.get(ActiviteType, type_id)
    if t is None:
        raise HTTPException(404, "Type d'activité introuvable.")
    n_act = db.query(func.count()).select_from(ActiviteSauvegardee).filter(ActiviteSauvegardee.activite_type_id == t.id).scalar()
    n_few = db.query(func.count()).select_from(FewShotMilestone).filter(FewShotMilestone.activite_type_id == t.id).scalar()
    if n_act or n_few:
        raise HTTPException(409, f"Type utilisé ({n_act} activité(s) sauvegardée(s), {n_few} jalon(s) few-shot) : suppression impossible.")
    db.delete(t)
    db.commit()
    logger.info("Type d'activité supprimé : id=%s label=%s", type_id, t.label)
    return {"ok": True, "id": type_id}


@router.get("/admin/activite-types/{type_id}/precisions", dependencies=[Depends(_require_admin)])
def lister_precisions_type(type_id: int, db: Session = Depends(get_db)):
    """Précisions d'un type — get direct dans `type_precisions`, ordonné (ordre, id). Lecture seule :
    la cartouche « Précisions » de l'admin AFFICHE cette liste, jamais recopiée (règle 4). 404 si le type
    n'existe pas. L'ajout/suppression (put) viendra à l'étape B, mêmes contrôles que le catalogue."""
    if db.get(ActiviteType, type_id) is None:
        raise HTTPException(404, "Type d'activité introuvable.")
    precs = (db.query(TypePrecision)
               .filter(TypePrecision.type_activite_id == type_id)
               .order_by(TypePrecision.ordre, TypePrecision.id).all())
    return {"type_id": type_id, "precisions": [
        {"id": p.id, "libelle": p.libelle, "ordre": p.ordre, "source": p.source} for p in precs]}


class PrecisionIn(BaseModel):
    libelle: str


@router.post("/admin/activite-types/{type_id}/precisions", dependencies=[Depends(_require_admin)])
def creer_precision_type(type_id: int, body: PrecisionIn, db: Session = Depends(get_db)):
    """Ajoute une précision au type (table `type_precisions`). CONTRÔLE CREATE (règle 4) : type existe
    (404), libellé non vide (400), et REFUS DU DOUBLON par libellé insensible à la casse dans CE type
    (comme le catalogue) → on renvoie l'existante avec `deja_present=True` plutôt que d'en refaire une.
    Sinon crée avec `source='admin'` (saisie manuelle) et `ordre = max(ordre)+1` (ajout en fin)."""
    if db.get(ActiviteType, type_id) is None:
        raise HTTPException(404, "Type d'activité introuvable.")
    libelle = (body.libelle or "").strip()
    if not libelle:
        raise HTTPException(400, "Indiquez un libellé pour la précision.")
    existante = (db.query(TypePrecision)
                   .filter(TypePrecision.type_activite_id == type_id,
                           func.lower(TypePrecision.libelle) == libelle.lower()).first())
    if existante is not None:
        return {"id": existante.id, "libelle": existante.libelle, "deja_present": True}
    ordre_max = (db.query(func.coalesce(func.max(TypePrecision.ordre), -1))
                   .filter(TypePrecision.type_activite_id == type_id).scalar())
    p = TypePrecision(type_activite_id=type_id, libelle=libelle, ordre=ordre_max + 1, source="admin")
    db.add(p)
    db.commit()
    db.refresh(p)
    logger.info("Précision ajoutée : type_id=%s id=%s libelle=%s", type_id, p.id, p.libelle)
    return {"id": p.id, "libelle": p.libelle, "deja_present": False}


@router.delete("/admin/activite-types/{type_id}/precisions/{prec_id}", dependencies=[Depends(_require_admin)])
def supprimer_precision_type(type_id: int, prec_id: int, db: Session = Depends(get_db)):
    """Supprime une précision. CONTRÔLE DELETE (règle 4) : la précision doit exister ET appartenir à CE
    type (404 sinon). Aucun grisage : rien ne référence une précision par clé étrangère — la précision
    choisie par le prof est un instantané TEXTE dans `activites_sauvegardees.sous_type`, pas un lien —
    donc la suppression est toujours sûre et n'oriente aucune activité déjà sauvegardée."""
    p = db.get(TypePrecision, prec_id)
    if p is None or p.type_activite_id != type_id:
        raise HTTPException(404, "Précision introuvable pour ce type.")
    db.delete(p)
    db.commit()
    logger.info("Précision supprimée : type_id=%s id=%s libelle=%s", type_id, prec_id, p.libelle)
    return {"ok": True, "id": prec_id}


def _texte_staged(token: str, max_pages: int = 6) -> str:
    """Texte des premières pages du PDF en attente (staging) — la structure se lit sur le début ;
    on n'envoie pas tout le PDF à l'IA. Lève si le document a expiré."""
    staged = STAGING_DIR / f"{token}.pdf"
    if not staged.exists():
        raise HTTPException(400, "Document introuvable (aperçu expiré ?). Recommencez.")
    import pdfplumber  # import paresseux
    with pdfplumber.open(str(staged)) as pdf:
        pages = [(p.extract_text() or "") for p in pdf.pages[:max_pages]]
    return "\n".join(pages).strip()


def _famille_dict(f: Famille) -> dict:
    """Fiche d'une famille pour le front : classification pure (id, nom, description)."""
    return {"id": f.id, "nom": f.nom, "description": f.description}


def famille_couple_existe(db: Session, famille_id: int, niveau_id: int) -> bool:
    """Vérif n°2 au dépôt : cette famille a-t-elle sa place à ce niveau ? Lit `famille_couples`
    (le couple famille_id + niveau_id, décidé par l'humain, jamais par l'IA). True si la ligne
    existe, False sinon. Requête base pure (aucune IA), testable seule."""
    return db.query(FamilleCouple).filter(
        FamilleCouple.famille_id == famille_id,
        FamilleCouple.niveau_id == niveau_id,
    ).first() is not None


class DetecterFamilleBody(BaseModel):
    token: str


@router.post("/admin/referentiels/detecter-famille", dependencies=[Depends(_require_admin)])
def detecter_famille_endpoint(body: DetecterFamilleBody, db: Session = Depends(get_db)):
    """L'IA classe le PDF en attente parmi les familles classables (rejet=false) EN BASE.
    Deux réponses possibles :
      - {"scenario": "match", "famille": {id, nom, description}} — une famille existante convient ;
      - {"scenario": "candidate", "candidate": {nom, description}} — aucune ne convient, l'IA propose une famille.
    L'IA ne prononce jamais le rejet. Générique : texte + familles de la base, aucun cas particulier."""
    from backend.rag.analyse_amont import classer_famille
    familles = [{"id": f.id, "nom": f.nom, "description": f.description}
                for f in db.query(Famille).filter(Famille.rejet == False).order_by(Famille.id).all()]
    if not familles:
        raise HTTPException(400, "Aucune famille classable en base.")
    texte = _texte_staged(body.token)
    if not texte:
        raise HTTPException(400, "PDF sans texte lisible : classement impossible.")
    res = classer_famille(texte, familles, db=db)
    if res["scenario"] == "match":
        return {"scenario": "match", "famille": _famille_dict(db.get(Famille, res["famille_id"]))}
    return {"scenario": "candidate", "candidate": res["candidate"]}


class CreerFamilleBody(BaseModel):
    nom: str
    description: str


@router.post("/admin/referentiels/familles", dependencies=[Depends(_require_admin)])
def creer_famille(body: CreerFamilleBody, db: Session = Depends(get_db)):
    """Crée une famille validée par l'admin (proposée par l'IA, éventuellement éditée). `rejet=false`.
    `nom` et `description` non vides ; `nom` unique. Donnée runtime — la migration ne sème que les
    familles initiales (familles est une table métier vivante)."""
    nom = (body.nom or "").strip()
    description = (body.description or "").strip()
    if not nom or not description:
        raise HTTPException(400, "Champs obligatoires vides : nom et description.")
    if db.query(Famille).filter(Famille.nom == nom).first():
        raise HTTPException(409, f"Une famille porte déjà le nom « {nom} ». Renomme-la.")
    fam = Famille(nom=nom, description=description, rejet=False)
    db.add(fam); db.commit(); db.refresh(fam)
    return _famille_dict(fam)


class ModifierDescriptionBody(BaseModel):
    description: str


@router.put("/admin/familles/{famille_id}/description", dependencies=[Depends(_require_admin)])
def modifier_description_famille(famille_id: int, body: ModifierDescriptionBody, db: Session = Depends(get_db)):
    """Update encadré : modifie UNIQUEMENT la description d'une famille (jamais le nom). 404 si la famille
    n'existe pas, 400 si la description est vide. Put direct en base (règle get/put, zéro copie)."""
    description = (body.description or "").strip()
    if not description:
        raise HTTPException(400, "La description ne peut pas être vide.")
    fam = db.query(Famille).filter(Famille.id == famille_id).first()
    if not fam:
        raise HTTPException(404, "Famille introuvable.")
    fam.description = description
    db.commit(); db.refresh(fam)
    return _famille_dict(fam)


# ── Construction d'une famille : choisir/ajouter le cycle, cocher/ajouter les niveaux, relier au couple.
#    Tout via l'admin (get/put, zéro seed sauf obligation). Trois briques neuves + creer_famille (ci-dessus).

class CreerCycleBody(BaseModel):
    nom: str


@router.post("/admin/cycles", dependencies=[Depends(_require_admin)])
def creer_cycle(body: CreerCycleBody, db: Session = Depends(get_db)):
    """Crée un cycle (Create encadré : nom non vide, unique insensible à la casse). `ordre` = max+1."""
    nom = (body.nom or "").strip()
    if not nom:
        raise HTTPException(400, "Le nom du cycle est requis.")
    if db.query(Cycle).filter(func.lower(Cycle.nom) == nom.lower()).first():
        raise HTTPException(409, f"Le cycle « {nom} » existe déjà.")
    maxo = db.query(func.max(Cycle.ordre)).scalar()
    c = Cycle(nom=nom, ordre=(maxo or 0) + 1)
    db.add(c); db.commit(); db.refresh(c)
    return {"id": c.id, "nom": c.nom, "ordre": c.ordre}


@router.post("/admin/familles/{famille_id}/suggerer-cycles", dependencies=[Depends(_require_admin)])
def suggerer_cycles_famille(famille_id: int, db: Session = Depends(get_db)):
    """L'IA PROPOSE les cycles sur lesquels s'appuie la famille (aide au remplissage, jamais une
    écriture). Chaque proposition est marquée `existant` (avec son `cycle_id`) si un cycle du même nom
    est déjà en base, sinon `à créer` (`cycle_id` null → l'admin l'ajoute en 1 clic via POST /admin/cycles).
    Lecture seule ici : l'IA suggère, le code apparie aux cycles réels, l'admin décide (règle 4)."""
    from backend.rag.analyse_amont import suggerer_cycles as ia_suggerer_cycles
    fam = db.query(Famille).filter(Famille.id == famille_id).first()
    if not fam:
        raise HTTPException(404, "Famille introuvable.")
    cycles = db.query(Cycle).order_by(Cycle.ordre, Cycle.id).all()
    par_nom = {c.nom.strip().lower(): c for c in cycles}
    try:
        noms = ia_suggerer_cycles(
            {"nom": fam.nom, "description": fam.description},
            [{"id": c.id, "nom": c.nom} for c in cycles],
            db=db,
        )
    except Exception:
        logger.exception("suggerer_cycles : appel IA échoué (famille %s)", famille_id)
        raise HTTPException(502, "L'IA n'a pas pu proposer de cycles. Réessaie.")
    propositions = []
    for nom in noms:
        c = par_nom.get(nom.strip().lower())
        propositions.append({
            "nom": (c.nom if c else nom.strip()),
            "cycle_id": (c.id if c else None),
            "existant": c is not None,
        })
    return {"propositions": propositions}


@router.post("/admin/familles/{famille_id}/cycles/{cycle_id}/suggerer-niveaux", dependencies=[Depends(_require_admin)])
def suggerer_niveaux_famille(famille_id: int, cycle_id: int, db: Session = Depends(get_db)):
    """L'IA PROPOSE les niveaux d'un cycle pertinents pour la famille (aide au remplissage, jamais une
    écriture). Chaque proposition est marquée `existant` (avec `niveau_id` + `lie` = déjà relié à la
    famille) ou `à créer` (`niveau_id` null). Lecture seule : l'IA suggère, le code apparie aux niveaux
    réels du cycle + lit les liens, l'admin coche/crée (règle 4)."""
    from backend.rag.analyse_amont import suggerer_niveaux as ia_suggerer_niveaux
    fam = db.query(Famille).filter(Famille.id == famille_id).first()
    if not fam:
        raise HTTPException(404, "Famille introuvable.")
    cyc = db.get(Cycle, cycle_id)
    if not cyc:
        raise HTTPException(404, "Cycle inconnu.")
    niveaux = db.query(Niveau).filter(Niveau.cycle_id == cycle_id).order_by(Niveau.ordre, Niveau.id).all()
    par_nom = {n.nom.strip().lower(): n for n in niveaux}
    lies = {r.niveau_id for r in (db.query(FamilleCouple.niveau_id)
                                    .filter(FamilleCouple.famille_id == famille_id).all())}
    try:
        noms = ia_suggerer_niveaux(
            {"nom": fam.nom, "description": fam.description},
            cyc.nom,
            [{"id": n.id, "nom": n.nom} for n in niveaux],
            db=db,
        )
    except Exception:
        logger.exception("suggerer_niveaux : appel IA échoué (famille %s cycle %s)", famille_id, cycle_id)
        raise HTTPException(502, "L'IA n'a pas pu proposer de niveaux. Réessaie.")
    propositions = []
    for nom in noms:
        n = par_nom.get(nom.strip().lower())
        propositions.append({
            "nom": (n.nom if n else nom.strip()),
            "niveau_id": (n.id if n else None),
            "existant": n is not None,
            "lie": (n.id in lies if n else False),
        })
    return {"propositions": propositions}


class CreerNiveauBody(BaseModel):
    cycle_id: int
    nom: str


@router.post("/admin/niveaux", dependencies=[Depends(_require_admin)])
def creer_niveau(body: CreerNiveauBody, db: Session = Depends(get_db)):
    """Crée un niveau dans un cycle (Create encadré : nom non vide, unique DANS le cycle). `ordre` = max+1
    du cycle. Même geste que le get-or-create du dépôt de référentiel, mais explicite et à la demande."""
    nom = (body.nom or "").strip()
    if not nom:
        raise HTTPException(400, "Le nom du niveau est requis.")
    cycle = db.get(Cycle, body.cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle inconnu.")
    if db.query(Niveau).filter(Niveau.cycle_id == cycle.id, func.lower(Niveau.nom) == nom.lower()).first():
        raise HTTPException(409, f"Le niveau « {nom} » existe déjà dans ce cycle.")
    maxo = db.query(func.max(Niveau.ordre)).filter(Niveau.cycle_id == cycle.id).scalar()
    n = Niveau(cycle_id=cycle.id, nom=nom, ordre=(maxo or 0) + 1)
    db.add(n); db.commit(); db.refresh(n)
    return {"id": n.id, "nom": n.nom, "cycle_id": n.cycle_id}


@router.get("/admin/familles/niveaux", dependencies=[Depends(_require_admin)])
def lister_niveaux_pour_famille(famille_id: int, cycle_id: int, db: Session = Depends(get_db)):
    """Fenêtre de l'écran : les niveaux d'un cycle + lesquels sont DÉJÀ reliés à la famille (get, zéro copie).
    `lie` = présence d'une ligne dans `famille_couples` (famille_id, niveau_id)."""
    lies = {r.niveau_id for r in (db.query(FamilleCouple.niveau_id)
                                    .filter(FamilleCouple.famille_id == famille_id).all())}
    nivs = (db.query(Niveau).filter(Niveau.cycle_id == cycle_id)
              .order_by(Niveau.ordre, Niveau.id).all())
    return {"niveaux": [{"id": n.id, "nom": n.nom, "lie": n.id in lies} for n in nivs]}


@router.get("/admin/familles/{famille_id}/matrice", dependencies=[Depends(_require_admin)])
def matrice_famille(famille_id: int, db: Session = Depends(get_db)):
    """Détail (GET pur) de la famille : les cycles auxquels elle est reliée + les niveaux reliés,
    groupés par cycle et triés. Sert à afficher l'état COURANT à l'ouverture de la famille (avant toute
    proposition IA). Lecture seule, zéro écriture, zéro copie."""
    fam = db.query(Famille).filter(Famille.id == famille_id).first()
    if not fam:
        raise HTTPException(404, "Famille introuvable.")
    ids = [r.niveau_id for r in (db.query(FamilleCouple.niveau_id)
                                   .filter(FamilleCouple.famille_id == famille_id).all())]
    if not ids:
        return {"cycles": []}
    niveaux = db.query(Niveau).filter(Niveau.id.in_(ids)).all()
    par_cycle = {}
    for n in niveaux:
        par_cycle.setdefault(n.cycle_id, []).append(n)
    cycles = (db.query(Cycle).filter(Cycle.id.in_(list(par_cycle.keys())))
                .order_by(Cycle.ordre, Cycle.id).all())
    out = []
    for c in cycles:
        nivs = sorted(par_cycle[c.id], key=lambda x: (x.ordre or 0, x.id))
        out.append({"cycle_id": c.id, "nom": c.nom,
                    "niveaux": [{"niveau_id": n.id, "nom": n.nom, "lie": True} for n in nivs]})
    return {"cycles": out}


class BasculerFamilleCoupleBody(BaseModel):
    famille_id: int
    niveau_id: int
    actif: bool               # True = relier (créer le couple), False = délier (supprimer le couple)


@router.put("/admin/familles/couple", dependencies=[Depends(_require_admin)])
def basculer_famille_couple(body: BasculerFamilleCoupleBody, db: Session = Depends(get_db)):
    """La case EST le put : cocher un niveau = créer le couple famille↔niveau, décocher = le supprimer.
    Écriture directe au clic. CREATE encadré : l'UNIQUE(famille_id, niveau_id) empêche le doublon.
    DELETE encadré : on REFUSE de délier si un référentiel est déposé sur ce niveau (le couple sert)."""
    fam = db.get(Famille, body.famille_id)
    if not fam:
        raise HTTPException(404, "Famille inconnue.")
    niv = db.get(Niveau, body.niveau_id)
    if not niv:
        raise HTTPException(404, "Niveau inconnu.")
    lien = (db.query(FamilleCouple)
              .filter(FamilleCouple.famille_id == fam.id, FamilleCouple.niveau_id == niv.id).first())
    if body.actif:
        if lien is None:
            db.add(FamilleCouple(famille_id=fam.id, niveau_id=niv.id)); db.commit()
    else:
        if lien is not None:
            if db.query(Referentiel).filter(Referentiel.niveau_id == niv.id).first():
                raise HTTPException(409, "Impossible de délier : un référentiel est déposé sur ce niveau.")
            db.delete(lien); db.commit()
    return {"ok": True, "famille_id": fam.id, "niveau_id": niv.id, "actif": body.actif}


class VerifierDepotBody(BaseModel):
    token: str
    cycle_id: int
    niveau_id: int
    famille_id: int


@router.post("/admin/referentiels/verifier-depot", dependencies=[Depends(_require_admin)])
def verifier_depot(body: VerifierDepotBody, db: Session = Depends(get_db)):
    """Vérification au dépôt (LECTURE SEULE), avant de proposer la validation. Lance les deux
    contrôles et renvoie les deux verdicts :
      - n°1 (couple) : l'IA lit le couple visé par le PDF et le compare au couple déclaré ;
      - n°2 (famille) : le couple (famille, niveau) est-il présent dans famille_couples ?
    L'écran n'affiche le document à valider que si les deux passent."""
    cycle = db.get(Cycle, body.cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle inconnu.")
    niv = db.get(Niveau, body.niveau_id)
    if not niv or niv.cycle_id != cycle.id:
        raise HTTPException(404, "Niveau inconnu pour ce cycle.")

    texte = _texte_staged(body.token)
    if not texte:
        raise HTTPException(400, "PDF sans texte lisible : vérification impossible.")

    from backend.rag.analyse_amont import verifier_couple
    try:
        couple = verifier_couple(texte[:4000], cycle.nom, niv.nom, db=db)
    except Exception:
        logger.exception("verifier_depot : échec de la vérification du couple par l'IA")
        raise HTTPException(400, "Vérification du couple impossible.")

    famille = {"existe": famille_couple_existe(db, body.famille_id, niv.id)}
    return {"couple": couple, "famille": famille}


class AbandonnerBody(BaseModel):
    token: str


@router.post("/admin/referentiels/abandonner", dependencies=[Depends(_require_admin)])
def abandonner(body: AbandonnerBody):
    """L'admin jette le PDF en attente (Scénario candidate). Efface le staging. Aucun écrit en base."""
    (STAGING_DIR / f"{body.token}.pdf").unlink(missing_ok=True)
    return {"ok": True}


class ValiderBody(BaseModel):
    token: str
    cycle_id: int
    niveau: str
    famille_id: int | None = None        # famille de structure choisie par l'admin (une des 5)
    fichier_origine: str | None = None   # vrai nom du PDF déposé/téléchargé — gardé en base comme trace
    source: str | None = None
    date_doc: str | None = None
    forcage_motif: str | None = None     # motif si l'admin FORCE malgré une alerte (couple/famille) ; NULL sinon
    verif_couple: dict | None = None     # verdict IA du couple {correspond, niveau_lu, raison} — figé à la validation


@router.post("/admin/referentiels/valider", dependencies=[Depends(_require_admin)])
def valider(body: ValiderBody, db: Session = Depends(get_db)):
    staged = STAGING_DIR / f"{body.token}.pdf"
    if not staged.exists():
        raise HTTPException(400, "Document à valider introuvable (aperçu expiré ?). Recommencez.")

    niveau_nom = body.niveau.strip()
    if not niveau_nom:
        raise HTTPException(400, "Le niveau est requis.")
    cycle = db.get(Cycle, body.cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle inconnu.")

    # get-or-create du niveau. Créé sans référentiel : il n'est donc pas « disponible »
    # (refDisponible est dérivé = le niveau a un référentiel ingéré). La mise à disposition
    # au prof reste l'affaire du garde-fou, APRÈS validation complète (étape 4).
    niveau = (db.query(Niveau)
                .filter(Niveau.nom == niveau_nom, Niveau.cycle_id == cycle.id).first())
    if not niveau:
        maxo = db.query(func.max(Niveau.ordre)).filter(Niveau.cycle_id == cycle.id).scalar()
        niveau = Niveau(cycle_id=cycle.id, nom=niveau_nom, ordre=(maxo or 0) + 1)
        db.add(niveau)
        db.flush()

    # Un référentiel par niveau (matiere_id NULL = tout le niveau). S'il existe déjà pour ce couple
    # → MISE À JOUR (le nouveau PDF remplace l'ancien, on refait texte/prompt/découpe). Sinon → création.
    existing = db.query(Referentiel).filter(Referentiel.niveau_id == niveau.id,
                                            Referentiel.matiere_id.is_(None)).first()
    nom_fixe = _dossier_cle(niveau_nom).lower()
    # Contrôle d'unicité du nom_fixe seulement pour une CRÉATION (en MAJ, c'est le même couple).
    if existing is None and db.query(Referentiel).filter(Referentiel.nom_fixe == nom_fixe).first():
        raise HTTPException(409, f"Identifiant de référentiel déjà utilisé : {nom_fixe}.")

    # Rangement CYCLE / NIVEAU : le chemin complet (cycle + niveau) identifie le référentiel
    # de façon unique (deux niveaux de même nom dans deux cycles ne se télescopent jamais).
    dossier = REFERENTIELS_DIR / _dossier_cle(cycle.nom) / _dossier_cle(niveau_nom)
    dossier.mkdir(parents=True, exist_ok=True)
    pdf_final = dossier / "referentiel.pdf"
    shutil.move(str(staged), str(pdf_final))

    # On NE fait PAS l'extraction du texte ici : c'est le travail lourd (≈0,18 s/page → ~3 min pour
    # un gros PDF, ce qui figeait l'écran et déclenchait un faux « échec réseau ») et il est INUTILE
    # à ce stade — le fichier produit n'était relu par personne, et le découpage/ingestion ré-extrait
    # déjà du PDF (pgvector_store._decouper_ia). On se contente de COMPTER les pages (rapide) pour le
    # retour. Le plafond au dépôt (depot_max_pages) garantit en amont un PDF de taille raisonnable.
    try:
        import pdfplumber  # import paresseux
        with pdfplumber.open(str(pdf_final)) as pdf:
            n_pages = len(pdf.pages)
    except Exception as e:
        raise HTTPException(400, f"Lecture du PDF impossible : {e}")

    # Disque = nom fixe `referentiel.pdf` (le code ne dépend jamais du nom mouvant de l'EN).
    # Base = `fichier` garde le VRAI nom d'origine (trace, affiché à l'admin), sans contrainte
    # de système de fichiers (c'est du texte). Repli sur le nom de disque si non fourni.
    fichier_origine = (body.fichier_origine.strip() if body.fichier_origine else "") or "referentiel.pdf"
    # Motif de forçage (l'admin valide malgré une alerte des vérifications au dépôt). None = pas de
    # forçage. Tracé EN BASE (colonne forcage_motif) + log si présent.
    forcage_motif = (body.forcage_motif.strip() if body.forcage_motif else "") or None
    if forcage_motif:
        logger.warning("valider : FORÇAGE de la validation (%s / %s) — motif : %s",
                       cycle.nom, niveau_nom, forcage_motif)
    # Verdict IA du couple (le {correspond, niveau_lu, raison} calculé au dépôt et affiché à l'écran).
    # C'est une donnée NEUVE (n'existe nulle part ailleurs) : on la FIGE ici en JSON. Réécrit sur les
    # deux branches → une mise à jour de PDF ne laisse jamais traîner l'ancien verdict. None = non fourni.
    verif_couple_json = json.dumps(body.verif_couple, ensure_ascii=False) if body.verif_couple else None
    # PUT du couple (famille + niveau) dans `famille_couples` : cette table relationnelle est la
    # SEULE source de vérité du lien famille↔niveau. Valider un référentiel FAIT exister le couple.
    # Idempotent : on LIT d'abord (famille_couple_existe), on n'écrit que s'il manque — la contrainte
    # UNIQUE(famille_id, niveau_id) garantit qu'on n'aura jamais de doublon.
    if body.famille_id is not None and not famille_couple_existe(db, body.famille_id, niveau.id):
        db.add(FamilleCouple(famille_id=body.famille_id, niveau_id=niveau.id))
        db.flush()

    if existing is not None:
        # MISE À JOUR : même ligne (id/collection/niveau stables → liens et MATIÈRES intacts).
        # On remet à zéro ce qui découlait de l'ANCIEN PDF : prompt de découpe, chunks.
        existing.fichier = fichier_origine
        existing.source = (body.source.strip() if body.source else None)
        existing.date_doc = (body.date_doc.strip() if body.date_doc else None)
        existing.prompt_decoupe = None
        existing.prompt_decoupe_valide = False
        existing.forcage_motif = forcage_motif
        existing.verif_couple = verif_couple_json
        db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == existing.id).delete()
        # Candidates issues de l'ANCIEN PDF : effacées ici (elles seront refaites par le nouveau juste
        # après). Ainsi, si la détection échoue, on reste sur une proposition VIDE, jamais périmée.
        # Les matières VALIDÉES (paires matière×niveau) ne sont PAS touchées : c'est le travail de l'admin.
        db.query(MatiereCandidate).filter(MatiereCandidate.niveau_id == niveau.id).delete()
        db.commit()
        ref = existing
    else:
        ref = Referentiel(
            niveau_id=niveau.id, matiere_id=None,
            nom_fixe=nom_fixe, collection=nom_fixe, filtres=None,
            fichier=fichier_origine,
            source=(body.source.strip() if body.source else None),
            date_doc=(body.date_doc.strip() if body.date_doc else None),
            forcage_motif=forcage_motif,
            verif_couple=verif_couple_json,
        )
        db.add(ref)
        db.commit()

    # Détection IA des matières PROPOSÉES à partir du NOUVEAU PDF. Elle ne crée jamais une matière
    # validée (paire matière×niveau, travail de l'admin) : elle remplit seulement `matieres_candidates`
    # — les propositions que l'admin cochera. Le nouveau PDF ÉCRASE les anciennes candidates (déjà
    # effacées ci-dessus en mise à jour). Best-effort : une panne IA ne casse pas la validation du
    # référentiel (les candidates ne sont qu'une aide au remplissage, jamais une donnée figée).
    try:
        from backend.rag.analyse_amont import detecter_matieres
        texte_pdf = _texte_du_pdf(pdf_final)        # TOUT le PDF (toutes les pages), pas les 6 premières
        if texte_pdf.strip():
            _ecrire_candidates(db, niveau.id, detecter_matieres(texte_pdf, db=db))
    except Exception:
        logger.exception("valider : détection des matières échouée (%s / %s)", cycle.nom, niveau_nom)

    return {
        "ok": True,
        "cycle": cycle.nom,
        "niveau": niveau_nom,
        "dossier": f"{_dossier_cle(cycle.nom)}/{_dossier_cle(niveau_nom)}",
        "fichier_disque": "referentiel.pdf",   # nom physique sur le disque (chemin du message)
        "fichier_origine": fichier_origine,     # vrai nom conservé en base
        "nom_fixe": nom_fixe,
        "pages": n_pages,
    }


# ── État d'un couple : le référentiel est-il DÉJÀ enregistré ? nom réel + matières ──

@router.get("/admin/referentiels/etat", dependencies=[Depends(_require_admin)])
def etat_couple(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """À la sélection d'un couple (cycle + niveau) sur l'écran admin : dire si un
    référentiel est DÉJÀ enregistré (« déjà traité »), avec son VRAI nom d'origine
    (colonne `fichier`) + la source, et la liste des matières déjà reliées à ce niveau.

    Lecture seule (aucune écriture). Sert à l'écran à afficher l'état « déjà téléchargé,
    déjà traité » + les matières existantes, et à griser la zone de dépôt. Le couple est
    INDÉPENDANT : chaque niveau a sa propre ligne `referentiels` et ses propres paires.
    """
    niveau_nom = (niveau or "").strip()
    niv = (db.query(Niveau)
             .filter(Niveau.nom == niveau_nom, Niveau.cycle_id == cycle_id).first())
    if not niv:
        # Pas de niveau en base → pas de candidates (elles sont clés par niveau_id).
        return {"existe_referentiel": False, "referentiel": None, "matieres": [], "candidates": [],
                "prompt_decoupe_valide": False, "decoupe_valide": False}
    candidates = _lire_candidates(db, niv.id)

    # Référentiel du niveau entier (matiere_id NULL) — même clé qu'à la validation.
    ref = (db.query(Referentiel)
             .filter(Referentiel.niveau_id == niv.id, Referentiel.matiere_id.is_(None))
             .first())

    # Matières déjà reliées à ce niveau (paires actives + matière active).
    matieres = [
        {"id": mid, "nom": mnom}
        for mid, mnom in (
            db.query(Matiere.id, Matiere.nom)
              .join(MatiereNiveau, MatiereNiveau.matiere_id == Matiere.id)
              .filter(MatiereNiveau.niveau_id == niv.id,
                      MatiereNiveau.actif == True, Matiere.actif == True)
              .order_by(Matiere.ordre).all()
        )
    ]

    return {
        "existe_referentiel": ref is not None,
        "referentiel": (
            {"fichier": ref.fichier, "source": ref.source, "date_doc": ref.date_doc,
             "forcage_motif": ref.forcage_motif, "verif_couple": ref.verif_couple}
            if ref else None
        ),
        "matieres": matieres,
        "candidates": candidates,
        # Drapeaux de validation lus sur la MÊME ligne `ref` (get) — la table front les lit via etat.
        "prompt_decoupe_valide": bool(ref.prompt_decoupe_valide) if ref else False,
        "decoupe_valide": bool(ref.decoupe_valide) if ref else False,
    }


# ── Relecture : servir le PDF d'origine d'un couple déjà enregistré (lecture seule) ──

@router.get("/admin/referentiels/pdf", dependencies=[Depends(_require_admin)])
def voir_pdf(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Sert le PDF d'origine (referentiel.pdf) d'un couple déjà enregistré, pour relecture.
    Lecture seule : ne range rien, ne modifie rien. Affiché inline (visionneuse du navigateur)."""
    cycle = db.get(Cycle, cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle inconnu.")
    pdf = REFERENTIELS_DIR / _dossier_cle(cycle.nom) / _dossier_cle(niveau.strip()) / "referentiel.pdf"
    if not pdf.exists():
        raise HTTPException(404, "Aucun référentiel enregistré pour ce couple.")
    return FileResponse(str(pdf), media_type="application/pdf",
                        headers={"Content-Disposition": "inline; filename=referentiel.pdf"})


# ── Résolution du référentiel d'un couple (cycle + niveau) — porteur EN BASE des données du couple ──

def _ref_du_couple(db: Session, cycle_id: int, niveau: str) -> Referentiel | None:
    """Résout la ligne `referentiels` (matiere_id NULL) du COUPLE cycle+niveau — le porteur EN BASE
    des données du couple (prompt de découpe, PDF…). Lève 404 si le cycle est inconnu, 422 si le
    niveau manque. Renvoie None si le niveau ou le référentiel du couple n'existe pas encore."""
    cycle = db.get(Cycle, cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle inconnu.")
    niveau_nom = (niveau or "").strip()
    if not niveau_nom:
        raise HTTPException(422, "Niveau manquant pour résoudre le couple.")
    niv = (db.query(Niveau)
             .filter(Niveau.nom == niveau_nom, Niveau.cycle_id == cycle_id).first())
    if not niv:
        return None
    return (db.query(Referentiel)
              .filter(Referentiel.niveau_id == niv.id, Referentiel.matiere_id.is_(None)).first())


class RegleStatutBody(BaseModel):
    cycle_id: int
    niveau: str                 # couple = cycle + niveau ; entre dans le chemin de la découpe


# ── Prompt de découpe du couple — GÉNÉRÉ PAR L'IA (méta-prompt en base), affiché/corrigé/validé ──
#    par l'admin. Aucun prompt écrit en dur : le méta-prompt vit en base (Setting), le prompt du
#    couple aussi (colonnes referentiels.prompt_decoupe / prompt_decoupe_valide). La découpe refuse
#    de tourner tant que le prompt du couple n'est pas validé (garde-fou, cap « aSchool n'invente rien »).

def _pdf_du_couple(db: Session, cycle_id: int, niveau: str) -> Path:
    """Chemin du PDF déposé pour le couple (REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf)."""
    cycle = db.get(Cycle, cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle inconnu.")
    return REFERENTIELS_DIR / _dossier_cle(cycle.nom) / _dossier_cle((niveau or "").strip()) / "referentiel.pdf"


def _texte_du_pdf(pdf: Path) -> str:
    """Texte brut du PDF (même extraction que la découpe). 404 si le PDF n'existe pas."""
    if not pdf.exists():
        raise HTTPException(404, "Aucun PDF déposé pour ce couple.")
    import pdfplumber
    with pdfplumber.open(str(pdf)) as p:
        return "\n".join((pg.extract_text() or "") for pg in p.pages)


class PromptDecoupeBody(BaseModel):
    cycle_id: int
    niveau: str
    prompt: str


@router.get("/admin/referentiels/prompt-decoupe", dependencies=[Depends(_require_admin)])
def lire_prompt_decoupe(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Lit le prompt de découpe du couple (EN BASE) + son statut de validation. `existe:false` si
    aucun référentiel pour ce couple."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None:
        return {"existe": False}
    return {"existe": True, "prompt": ref.prompt_decoupe or "", "valide": bool(ref.prompt_decoupe_valide),
            "decoupe_valide": bool(ref.decoupe_valide)}


@router.post("/admin/referentiels/prompt-decoupe/generer", dependencies=[Depends(_require_admin)])
def generer_prompt_decoupe_couple(body: RegleStatutBody, db: Session = Depends(get_db)):
    """L'IA GÉNÈRE le prompt de découpe adapté à CE document (méta-prompt lu EN BASE + texte du PDF).
    Stocké sur le couple, `valide=false` (l'admin doit le relire puis valider). Renvoie le prompt."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    texte = _texte_du_pdf(_pdf_du_couple(db, body.cycle_id, body.niveau))
    from backend.rag.analyse_amont import generer_prompt_decoupe
    try:
        prompt = generer_prompt_decoupe(texte, db=db)
    except Exception as e:
        raise HTTPException(400, f"Génération du prompt par l'IA impossible : {e}")
    ref.prompt_decoupe = prompt
    ref.prompt_decoupe_valide = False
    db.commit()
    return {"ok": True, "prompt": prompt, "valide": False}


class RegenererPromptBody(BaseModel):
    cycle_id: int
    niveau: str
    prompt_actuel: str
    remarques: str


@router.post("/admin/referentiels/prompt-decoupe/regenerer", dependencies=[Depends(_require_admin)])
def regenerer_prompt_decoupe_couple(body: RegenererPromptBody, db: Session = Depends(get_db)):
    """L'IA CORRIGE le prompt de découpe à partir des REMARQUES de l'admin (français clair). Reprend
    le prompt actuel + les remarques, produit un NOUVEAU prompt qui en tient compte, le stocke sur le
    couple avec `valide=false` (l'admin relit puis valide). Répétable à volonté. N'efface rien."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    texte = _texte_du_pdf(_pdf_du_couple(db, body.cycle_id, body.niveau))
    from backend.rag.analyse_amont import regenerer_prompt_decoupe
    try:
        prompt = regenerer_prompt_decoupe(
            texte, prompt_actuel=body.prompt_actuel, remarques=body.remarques, db=db)
    except Exception as e:
        raise HTTPException(400, f"Régénération du prompt par l'IA impossible : {e}")
    ref.prompt_decoupe = prompt
    ref.prompt_decoupe_valide = False
    db.commit()
    return {"ok": True, "prompt": prompt, "valide": False}


@router.post("/admin/referentiels/prompt-decoupe/valider", dependencies=[Depends(_require_admin)])
def valider_prompt_decoupe_couple(body: PromptDecoupeBody, db: Session = Depends(get_db)):
    """L'admin enregistre le prompt (éventuellement corrigé à la main) et le VALIDE (`valide=true`)
    → la découpe pourra tourner. Prompt vide refusé."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    if not (body.prompt or "").strip():
        raise HTTPException(422, "Le prompt de découpe est vide.")
    ref.prompt_decoupe = body.prompt
    ref.prompt_decoupe_valide = True
    db.commit()
    return {"ok": True, "valide": True}


@router.post("/admin/referentiels/prompt-decoupe/decouper", dependencies=[Depends(_require_admin)])
def decouper_couple(body: RegleStatutBody, db: Session = Depends(get_db)):
    """Déclenche la découpe (LECTURE SEULE, aucune ingestion) avec le prompt VALIDÉ du couple, et
    renvoie les unités produites par l'IA (titre + taille). Refuse si le prompt n'est pas validé."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    if not ref.prompt_decoupe_valide:
        raise HTTPException(400, "Prompt de découpe non validé : validez-le avant de découper.")
    pdf = _pdf_du_couple(db, body.cycle_id, body.niveau)
    if not pdf.exists():
        raise HTTPException(404, "Aucun PDF déposé pour ce couple.")
    from backend.rag.pgvector_store import _decouper_ia
    try:
        chunks = _decouper_ia(pdf, ref.prompt_decoupe or "")
    except Exception as e:
        raise HTTPException(400, f"Découpe par l'IA impossible : {e}")
    unites = [{"titre": c["text"].split("\n")[0].strip(), "taille": len(c["text"])} for c in chunks]
    return {"ok": True, "total": len(unites), "unites": unites}


@router.get("/admin/referentiels/decoupe", dependencies=[Depends(_require_admin)])
def lire_decoupe(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Lit les unités du découpage DÉJÀ en base (referentiel_chunks) pour ce couple — get, aucun
    recalcul. Même forme {titre, taille} que la découpe en direct, pour réafficher à l'ouverture ce
    qui est réellement stocké. Liste vide si rien n'est ingéré."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None:
        return {"unites": []}
    chunks = (db.query(ReferentielChunk)
              .filter(ReferentielChunk.referentiel_id == ref.id)
              .order_by(ReferentielChunk.option_ab, ReferentielChunk.chunk_index)
              .all())
    unites = [{"titre": c.texte.split("\n")[0].strip(), "taille": len(c.texte)} for c in chunks]
    return {"unites": unites}


# ── Découpe (ingestion) en TÂCHE DE FOND : l'écriture des chunks + embeddings prend ~2 min, bien
#    plus long qu'une requête HTTP ne peut tenir. Le bouton LANCE l'ingestion et rend la main tout de
#    suite ; l'écran SURVEILLE ensuite l'aboutissement via /decoupe/statut. `_INGESTIONS` = état
#    d'orchestration RUNTIME (en cours / échec), PAS une donnée métier : l'unique vérité d'aboutissement
#    reste `referentiels.decoupe_valide` + les chunks EN BASE. Perdu au redémarrage serveur (l'admin
#    relance le bouton) — acceptable.
_INGESTIONS: dict[str, dict] = {}
_INGESTIONS_LOCK = threading.Lock()


def _ingest_en_fond(collection: str) -> None:
    """Tâche de fond : découpe IA + embeddings + écriture des chunks, puis pose `decoupe_valide=true`
    EN BASE (le VRAI PUT). Met à jour l'état d'orchestration `_INGESTIONS` (done / error). Session
    dédiée (le thread ne partage pas celle de la requête, déjà fermée)."""
    try:
        from backend.rag.pgvector_store import ingest_pgvector
        rapport = ingest_pgvector(collection)
        db = SessionLocal()
        try:
            ref = db.query(Referentiel).filter(Referentiel.collection == collection).first()
            if ref is not None:
                ref.decoupe_valide = True   # drapeau posé UNIQUEMENT après l'ingestion réussie
                db.commit()
        finally:
            db.close()
        with _INGESTIONS_LOCK:
            _INGESTIONS[collection] = {"status": "done", "chunks": rapport.get("inseres_en_base"), "message": None}
    except Exception as e:
        logger.exception("Ingestion de la découpe échouée (collection=%s)", collection)
        with _INGESTIONS_LOCK:
            _INGESTIONS[collection] = {"status": "error", "chunks": None, "message": str(e)}


@router.post("/admin/referentiels/decoupe/valider", dependencies=[Depends(_require_admin)])
def valider_decoupe(body: RegleStatutBody, db: Session = Depends(get_db)):
    """Bouton FINAL : l'admin accepte la découpe. LANCE l'ingestion (découpe + embeddings + chunks
    EN BASE, puis `decoupe_valide=true`) en TÂCHE DE FOND et rend la main aussitôt — l'opération est
    trop longue pour tenir dans une requête HTTP. L'écran surveille ensuite via /decoupe/statut.
    Garde métier : on ne valide pas la découpe tant que le PROMPT n'est pas validé (elle en dépend)."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    if not ref.prompt_decoupe_valide:
        raise HTTPException(400, "Validez d'abord le prompt de découpe.")
    collection = ref.collection
    with _INGESTIONS_LOCK:
        deja = _INGESTIONS.get(collection, {}).get("status") == "running"
        if not deja:
            _INGESTIONS[collection] = {"status": "running", "chunks": None, "message": None}
    if not deja:   # jamais deux ingestions en parallèle pour le même couple (idempotent)
        threading.Thread(target=_ingest_en_fond, args=(collection,), daemon=True).start()
    return {"ok": True, "status": "running"}


@router.get("/admin/referentiels/decoupe/statut", dependencies=[Depends(_require_admin)])
def statut_decoupe(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """État de l'ingestion d'un couple (surveillance après « Valider le découpage »). La VÉRITÉ
    d'aboutissement = `decoupe_valide` + nombre de chunks EN BASE (get) ; `status` d'orchestration
    (running / error) lu dans `_INGESTIONS` (runtime). idle = rien en cours et pas encore validé."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None:
        return {"status": "absent", "decoupe_valide": False, "chunks": 0, "message": None}
    n = db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == ref.id).count()
    with _INGESTIONS_LOCK:
        job = _INGESTIONS.get(ref.collection)
    if ref.decoupe_valide:
        status = "done"
    elif job is not None:
        status = job["status"]
    else:
        status = "idle"
    return {"status": status, "decoupe_valide": bool(ref.decoupe_valide), "chunks": n,
            "message": (job or {}).get("message")}


# ── Méta-prompt (générique) : EN BASE (Setting 'prompt_meta_decoupe'), lu par le code, éditable ──

class MetaPromptBody(BaseModel):
    texte: str


@router.get("/admin/referentiels/meta-prompt", dependencies=[Depends(_require_admin)])
def lire_meta_prompt(db: Session = Depends(get_db)):
    """Lit le méta-prompt (EN BASE). Vide si pas encore renseigné."""
    from backend.systeme.admin import get_settings_dict
    return {"texte": get_settings_dict(db).get("prompt_meta_decoupe", "")}


@router.put("/admin/referentiels/meta-prompt", dependencies=[Depends(_require_admin)])
def ecrire_meta_prompt(body: MetaPromptBody, db: Session = Depends(get_db)):
    """Enregistre le méta-prompt EN BASE. Vide refusé."""
    if not (body.texte or "").strip():
        raise HTTPException(422, "Le méta-prompt est vide.")
    row = db.query(Setting).filter(Setting.key == "prompt_meta_decoupe").first()
    if row:
        row.value = body.texte
    else:
        db.add(Setting(key="prompt_meta_decoupe", value=body.texte))
    db.commit()
    return {"ok": True}


# ── Enregistrement des matières d'un couple : get-or-create + paire (idempotent) ──

class EnregistrerMatieresBody(BaseModel):
    cycle_id: int
    niveau: str
    matieres: list[str]


@router.post("/admin/referentiels/matieres", dependencies=[Depends(_require_admin)])
def enregistrer_matieres(body: EnregistrerMatieresBody, db: Session = Depends(get_db)):
    """Enregistre en base les matières d'un couple (cycle + niveau) : pour chaque nom, on
    RÉUTILISE la matière existante (get-or-create par nom, insensible à la casse — jamais de
    doublon) et on crée/réactive la paire matière×niveau. Idempotent : relancer ne crée rien
    en double. Renvoie un bilan (ajoutées / déjà présentes). Ne supprime JAMAIS rien."""
    niveau_nom = (body.niveau or "").strip()
    niv = (db.query(Niveau)
             .filter(Niveau.nom == niveau_nom, Niveau.cycle_id == body.cycle_id).first())
    if not niv:
        raise HTTPException(404, "Niveau inconnu pour ce cycle.")

    # Dédoublonnage des noms reçus (insensible à la casse), 1er libellé vu conservé.
    noms, vus = [], set()
    for raw in body.matieres:
        nom = (raw or "").strip()
        if nom and nom.lower() not in vus:
            vus.add(nom.lower()); noms.append(nom)

    ajoutees, deja = [], []
    for nom in noms:
        mat = db.query(Matiere).filter(func.lower(Matiere.nom) == nom.lower()).first()
        if not mat:
            maxo = db.query(func.max(Matiere.ordre)).scalar()
            mat = Matiere(nom=nom, ordre=(maxo or 0) + 1, actif=True)
            db.add(mat); db.flush()
        paire = (db.query(MatiereNiveau)
                   .filter(MatiereNiveau.matiere_id == mat.id, MatiereNiveau.niveau_id == niv.id)
                   .first())
        if paire and paire.actif:
            deja.append(nom)
        elif paire:
            paire.actif = True
            ajoutees.append(nom)
        else:
            db.add(MatiereNiveau(matiere_id=mat.id, niveau_id=niv.id, actif=True))
            ajoutees.append(nom)
    db.commit()
    return {"ajoutees": ajoutees, "deja_presentes": deja,
            "nb_ajoutees": len(ajoutees), "nb_deja": len(deja)}


# ── Renommer une matière PAR SON ID (garde l'id → aucun lien cassé) ──

class RenommerMatiereBody(BaseModel):
    matiere_id: int
    nouveau_nom: str


@router.patch("/admin/referentiels/matiere", dependencies=[Depends(_require_admin)])
def renommer_matiere(body: RenommerMatiereBody, db: Session = Depends(get_db)):
    """Renomme une matière par son id : garde l'identifiant, donc aucun lien (paire, prof,
    référentiel) n'est cassé. Le libellé change PARTOUT où la matière est partagée entre
    niveaux. Refuse un nom vide ou déjà porté par une AUTRE matière (anti-doublon)."""
    nom = (body.nouveau_nom or "").strip()
    if not nom:
        raise HTTPException(400, "Le nouveau nom est requis.")
    mat = db.get(Matiere, body.matiere_id)
    if not mat:
        raise HTTPException(404, "Matière inconnue.")
    autre = (db.query(Matiere)
               .filter(func.lower(Matiere.nom) == nom.lower(), Matiere.id != mat.id).first())
    if autre:
        raise HTTPException(409, f"Une autre matière porte déjà le nom « {nom} ».")
    ancien = mat.nom
    mat.nom = nom
    db.commit()
    return {"ok": True, "id": mat.id, "ancien_nom": ancien, "nouveau_nom": nom}


# ── Retirer une matière d'un niveau = DÉSACTIVER la paire (jamais de suppression dure) ──

class RetirerMatiereBody(BaseModel):
    cycle_id: int
    niveau: str
    matiere_id: int


@router.post("/admin/referentiels/retirer-matiere", dependencies=[Depends(_require_admin)])
def retirer_matiere(body: RetirerMatiereBody, db: Session = Depends(get_db)):
    """Retire une matière d'un niveau = met la paire `actif=False` (historique conservé,
    JAMAIS de suppression dure). Signale, sans rien casser, si la matière est encore utilisée
    par un prof (profil) ou par un référentiel de matière."""
    niveau_nom = (body.niveau or "").strip()
    niv = (db.query(Niveau)
             .filter(Niveau.nom == niveau_nom, Niveau.cycle_id == body.cycle_id).first())
    if not niv:
        raise HTTPException(404, "Niveau inconnu pour ce cycle.")
    mat = db.get(Matiere, body.matiere_id)
    if not mat:
        raise HTTPException(404, "Matière inconnue.")
    paire = (db.query(MatiereNiveau)
               .filter(MatiereNiveau.matiere_id == mat.id, MatiereNiveau.niveau_id == niv.id).first())
    if not paire or not paire.actif:
        return {"ok": True, "deja_absente": True, "matiere": mat.nom, "profs": 0, "referentiels": 0}
    profs = db.query(User).filter(func.lower(User.subject) == mat.nom.lower()).count()
    refs = db.query(Referentiel).filter(Referentiel.matiere_id == mat.id).count()
    paire.actif = False
    db.commit()
    return {"ok": True, "deja_absente": False, "matiere": mat.nom, "profs": profs, "referentiels": refs}


# ── CRUD référentiel : écrire UN champ (put au coup par coup) + supprimer (gardé) ──

class ModifierChampBody(BaseModel):
    cycle_id: int
    niveau: str
    champ: str                 # colonne libre autorisée : 'source' | 'date_doc'
    valeur: str | None = None


@router.patch("/admin/referentiels/champ", dependencies=[Depends(_require_admin)])
def modifier_champ(body: ModifierChampBody, db: Session = Depends(get_db)):
    """Écrit UN champ scalaire du référentiel du couple (put direct, zéro copie). Réservé aux
    colonnes de saisie libre (source, date_doc). Valeur vide → NULL. 404 si aucun référentiel."""
    CHAMPS = {"source", "date_doc"}
    if body.champ not in CHAMPS:
        raise HTTPException(400, f"Champ non modifiable : {body.champ}.")
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    setattr(ref, body.champ, (body.valeur or "").strip() or None)
    db.commit()
    return {"ok": True, "champ": body.champ, "valeur": getattr(ref, body.champ)}


class SupprimerRefBody(BaseModel):
    cycle_id: int
    niveau: str


@router.post("/admin/referentiels/supprimer", dependencies=[Depends(_require_admin)])
def supprimer_referentiel(body: SupprimerRefBody, db: Session = Depends(get_db)):
    """Supprime le référentiel d'un couple — UNIQUEMENT s'il n'a JAMAIS servi (aucun chunk ingéré) ;
    sinon refus (409). Efface la ligne `referentiels` + le PDF sur disque. Ne touche NI `famille_couples`
    (le couple garde le droit d'exister) NI les matières (données du couple, pas du document)."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    n = db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == ref.id).count()
    if n > 0:
        raise HTTPException(409, f"Référentiel utilisé (déjà ingéré : {n} unité(s)) — suppression impossible.")
    _pdf_du_couple(db, body.cycle_id, body.niveau).unlink(missing_ok=True)
    db.delete(ref)
    db.commit()
    return {"ok": True}


# ── Types d'activité d'un couple : CATALOGUE global (types_activite) coché/décoché via la LIAISON
#    (referentiel_types_activite). Exact calque du patron matières (catalogue partagé + paire N-N),
#    mais ici le référentiel ne fait que COCHER des lignes d'un catalogue global — il ne les possède
#    pas. get pour lire (l'écran), put pour écrire (le coché), zéro donnée en dur.


@router.get("/admin/referentiels/types-activite", dependencies=[Depends(_require_admin)])
def lire_types_activite(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Fenêtre de l'écran (lecture seule) : le CATALOGUE global des types actifs + lesquels sont COCHÉS
    (liaison `actif`) pour le référentiel de CE couple. L'écran rend une case par type du catalogue,
    cochée si son id est dans `coches`. `coches` vide si le couple n'a pas encore de référentiel (rien
    à cocher) — 404/422 seulement pour cycle inconnu / niveau manquant (via `_ref_du_couple`)."""
    ref = _ref_du_couple(db, cycle_id, niveau)   # 404 cycle / 422 niveau ; None si pas de référentiel
    catalogue = [
        {"id": t.id, "label": t.label, "is_default": bool(t.is_default)}
        for t in (db.query(ActiviteType)
                    .filter(ActiviteType.actif.is_(True))
                    .order_by(ActiviteType.ordre, ActiviteType.id).all())
    ]
    coches = []
    if ref is not None:
        liens = (db.query(ReferentielActiviteType)
                   .filter(ReferentielActiviteType.referentiel_id == ref.id,
                           ReferentielActiviteType.actif.is_(True))
                   .order_by(ReferentielActiviteType.ordre, ReferentielActiviteType.id).all())
        # Comptage RÉEL des précisions par lien (get, zéro copie) : un count groupé, pas de N+1.
        nb_par_lien = dict(
            db.query(ReferentielTypePrecision.referentiel_activite_type_id, func.count())
              .filter(ReferentielTypePrecision.referentiel_activite_type_id.in_([l.id for l in liens]))
              .group_by(ReferentielTypePrecision.referentiel_activite_type_id).all()
        ) if liens else {}
        coches = [
            {"activite_type_id": l.activite_type_id, "source": l.source, "prompt": l.prompt or "",
             "nb_precisions": int(nb_par_lien.get(l.id, 0))}
            for l in liens
        ]
    return {"catalogue": catalogue, "coches": coches}


def _generer_prompt_type(label: str, niveau: str) -> str:
    """Prompt de génération d'un type d'activité POUR CE couple, produit AUTOMATIQUEMENT au coche.
    Deux emplacements laissés à remplir à la génération : {texte} (l'idée du prof, elle mène) et
    {referentiel} (le programme officiel, pour cadrer et enrichir). {niveau} est fixé ici (le niveau
    du couple). Résultat stocké sur la ligne de liaison ; l'admin peut le relire/corriger via ✎ Prompt."""
    return (
        "Tu es un enseignant expérimenté.\n"
        f"Conçois une activité du type « {label} » adaptée à des élèves de {niveau}.\n\n"
        "Pars de l'idée du professeur ci-dessous — garde son intention et son style, c'est elle qui mène :\n"
        "{texte}\n\n"
        "Appuie-toi sur le programme officiel ci-dessous pour cadrer et enrichir l'activité, sans t'en écarter :\n"
        "{referentiel}\n\n"
        "Rends une activité claire et directement exploitable (objectif, consigne, déroulé)."
    )


class BasculerTypeBody(BaseModel):
    cycle_id: int
    niveau: str
    activite_type_id: int               # LE type basculé (un seul)
    actif: bool                         # True = cocher (lien actif), False = décocher (lien inactif)


@router.put("/admin/referentiels/types-activite", dependencies=[Depends(_require_admin)])
def basculer_type_activite(body: BasculerTypeBody, db: Session = Depends(get_db)):
    """La case EST le put : un clic écrit DIRECTEMENT en base l'état d'UN type pour le couple (pas de
    bouton Valider, pas de tampon). `actif=True` → liaison `actif=True` (get-or-create ; à la création
    `source` = l'ORIGINE du type : 'systeme' | 'admin' | 'ia' — le badge reflète d'où vient le type, pas
    qui a coché ; source CONSERVÉE si la liaison existait déjà — ex. une détection IA). `actif=False` →
    liaison `actif=False` (jamais de suppression dure : historique + source restent). Idempotent.
    404 si le couple n'a pas de référentiel ; 400 si le type n'existe pas au catalogue (FK)."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")

    # Origine + libellé du type (→ source du lien + génération du prompt). Contrôle d'existence AVANT écriture.
    t = (db.query(ActiviteType.id, ActiviteType.origine, ActiviteType.label)
           .filter(ActiviteType.id == body.activite_type_id).first())
    if t is None:
        raise HTTPException(400, f"Type d'activité inconnu au catalogue : {body.activite_type_id}.")

    l = (db.query(ReferentielActiviteType)
           .filter(ReferentielActiviteType.referentiel_id == ref.id,
                   ReferentielActiviteType.activite_type_id == body.activite_type_id).first())
    if l is None:
        if body.actif:                       # cocher un type jamais lié → on crée le lien (source = origine)
            # Génération AUTO du prompt de ce type POUR CE couple, dès la création du lien (zéro copie).
            db.add(ReferentielActiviteType(referentiel_id=ref.id, activite_type_id=body.activite_type_id,
                                           actif=True, source=t.origine,
                                           prompt=_generer_prompt_type(t.label, body.niveau)))
    else:
        l.actif = body.actif                 # bascule le lien existant (source d'origine conservée)
        # Recoche d'un lien sans prompt (ex. lien posé avant cette fonctionnalité) → on génère à ce moment.
        if body.actif and not (l.prompt or "").strip():
            l.prompt = _generer_prompt_type(t.label, body.niveau)
    # Le coche reste INSTANTANÉ (prompt = gabarit, aucun appel IA) — sinon « Tout sélectionner » (boucle de
    # coches, timeout court) casse. Les PRÉCISIONS ne sont PAS touchées ici : à l'ouverture du panneau
    # ✎ Précisions le front LIT (GET) ; si la lecture est vide, il appelle `…/precisions/generer` (l'IA écrit).
    db.commit()
    return {"ok": True, "activite_type_id": body.activite_type_id, "actif": body.actif}


def _generer_precisions_ia(db: Session, lien: ReferentielActiviteType, label: str, cycle_id: int, niveau: str) -> None:
    """Écrit les précisions IA du type POUR CE COUPLE dans `referentiel_type_precisions` (source='ia'), au
    coche. IDEMPOTENT : ne fait rien si la liaison a déjà des précisions (recocher ne réécrase pas, et
    n'écrase JAMAIS les précisions 'admin' saisies à la main). Toute panne (PDF absent, IA down) est
    ABSORBÉE (loggée) — la coche réussit quoi qu'il arrive."""
    deja = (db.query(ReferentielTypePrecision.id)
              .filter(ReferentielTypePrecision.referentiel_activite_type_id == lien.id).first())
    if deja is not None:
        return
    try:
        texte = _texte_du_pdf(_pdf_du_couple(db, cycle_id, niveau))
        if not texte.strip():
            return
        from backend.rag.analyse_amont import suggerer_precisions_type
        libelles = suggerer_precisions_type(label, niveau, texte, db=db)
    except Exception as e:
        logger.warning("Précisions IA non générées (coche non bloquée) lien=%s : %s", lien.id, e)
        return
    for i, lib in enumerate(libelles):
        lib = (lib or "").strip()
        if not lib:
            continue
        existe = (db.query(ReferentielTypePrecision.id)
                    .filter(ReferentielTypePrecision.referentiel_activite_type_id == lien.id,
                            func.lower(ReferentielTypePrecision.libelle) == lib.lower()).first())
        if existe is None:
            db.add(ReferentielTypePrecision(referentiel_activite_type_id=lien.id, libelle=lib, ordre=i, source="ia"))


class PromptLienBody(BaseModel):
    cycle_id: int
    niveau: str
    activite_type_id: int
    prompt: str


@router.put("/admin/referentiels/types-activite/prompt", dependencies=[Depends(_require_admin)])
def ecrire_prompt_type_couple(body: PromptLienBody, db: Session = Depends(get_db)):
    """UPDATE (règle 4) du prompt d'un type POUR CE couple — réécrit la colonne `prompt` de la ligne de
    liaison (une seule place, zéro copie). Contrôles : 404 si le couple n'a pas de référentiel ou si le
    type n'est pas lié à ce couple ; 422 si le prompt est vide (un prompt vide = type non opérationnel)."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    l = (db.query(ReferentielActiviteType)
           .filter(ReferentielActiviteType.referentiel_id == ref.id,
                   ReferentielActiviteType.activite_type_id == body.activite_type_id).first())
    if l is None:
        raise HTTPException(404, "Ce type n'est pas coché pour ce couple.")
    if not (body.prompt or "").strip():
        raise HTTPException(422, "Le prompt est vide.")
    l.prompt = body.prompt
    db.commit()
    return {"ok": True, "activite_type_id": body.activite_type_id}


def _lien_couple_type(db: Session, cycle_id: int, niveau: str, activite_type_id: int) -> ReferentielActiviteType:
    """Résout la ligne de liaison (couple × type) — le SEUL endroit où vit ce qui est propre au couple
    (prompt, et désormais précisions). 404 si le couple n'a pas de référentiel ou si le type n'y est pas lié."""
    ref = _ref_du_couple(db, cycle_id, niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    l = (db.query(ReferentielActiviteType)
           .filter(ReferentielActiviteType.referentiel_id == ref.id,
                   ReferentielActiviteType.activite_type_id == activite_type_id).first())
    if l is None:
        raise HTTPException(404, "Ce type n'est pas coché pour ce couple.")
    return l


@router.get("/admin/referentiels/types-activite/precisions", dependencies=[Depends(_require_admin)])
def lister_precisions_couple(cycle_id: int, niveau: str, activite_type_id: int, db: Session = Depends(get_db)):
    """Précisions d'un type POUR CE COUPLE — get direct dans `referentiel_type_precisions`, ordonné
    (ordre, id). Lecture seule : la liste est LUE, jamais recopiée (règle 4). Clé = la liaison couple×type."""
    l = _lien_couple_type(db, cycle_id, niveau, activite_type_id)
    precs = (db.query(ReferentielTypePrecision)
               .filter(ReferentielTypePrecision.referentiel_activite_type_id == l.id)
               .order_by(ReferentielTypePrecision.ordre, ReferentielTypePrecision.id).all())
    return {"precisions": [
        {"id": p.id, "libelle": p.libelle, "ordre": p.ordre, "source": p.source} for p in precs]}


class PrecisionCoupleIn(BaseModel):
    cycle_id: int
    niveau: str
    activite_type_id: int
    libelle: str


@router.post("/admin/referentiels/types-activite/precisions", dependencies=[Depends(_require_admin)])
def creer_precision_couple(body: PrecisionCoupleIn, db: Session = Depends(get_db)):
    """Ajoute une précision au type POUR CE COUPLE (`referentiel_type_precisions`). CREATE encadré
    (règle 4) : couple×type valide (404), libellé non vide (400), REFUS DU DOUBLON par libellé insensible
    à la casse DANS CE couple×type → renvoie l'existante (`deja_present`). Sinon crée `source='admin'`,
    `ordre = max(ordre)+1`. Rien de global : c'est propre au couple, jamais partagé avec un autre niveau."""
    l = _lien_couple_type(db, body.cycle_id, body.niveau, body.activite_type_id)
    libelle = (body.libelle or "").strip()
    if not libelle:
        raise HTTPException(400, "Indiquez un libellé pour la précision.")
    existante = (db.query(ReferentielTypePrecision)
                   .filter(ReferentielTypePrecision.referentiel_activite_type_id == l.id,
                           func.lower(ReferentielTypePrecision.libelle) == libelle.lower()).first())
    if existante is not None:
        return {"id": existante.id, "libelle": existante.libelle, "deja_present": True}
    ordre_max = (db.query(func.coalesce(func.max(ReferentielTypePrecision.ordre), -1))
                   .filter(ReferentielTypePrecision.referentiel_activite_type_id == l.id).scalar())
    p = ReferentielTypePrecision(referentiel_activite_type_id=l.id, libelle=libelle, ordre=ordre_max + 1, source="admin")
    db.add(p)
    db.commit()
    db.refresh(p)
    logger.info("Précision couple ajoutée : lien=%s id=%s libelle=%s", l.id, p.id, p.libelle)
    return {"id": p.id, "libelle": p.libelle, "deja_present": False}


@router.delete("/admin/referentiels/types-activite/precisions/{prec_id}", dependencies=[Depends(_require_admin)])
def supprimer_precision_couple(prec_id: int, cycle_id: int, niveau: str, activite_type_id: int,
                               db: Session = Depends(get_db)):
    """Supprime une précision d'un couple×type. DELETE encadré : la précision doit exister ET appartenir
    au bon couple×type (404 sinon). CASCADE côté base si la liaison disparaît ; ici suppression unitaire."""
    l = _lien_couple_type(db, cycle_id, niveau, activite_type_id)
    p = db.get(ReferentielTypePrecision, prec_id)
    if p is None or p.referentiel_activite_type_id != l.id:
        raise HTTPException(404, "Précision introuvable pour ce couple.")
    db.delete(p)
    db.commit()
    logger.info("Précision couple supprimée : lien=%s id=%s libelle=%s", l.id, prec_id, p.libelle)
    return {"ok": True, "id": prec_id}


class CoupleTypeRef(BaseModel):
    cycle_id: int
    niveau: str
    activite_type_id: int


@router.post("/admin/referentiels/types-activite/precisions/generer", dependencies=[Depends(_require_admin)])
def generer_precisions_couple(body: CoupleTypeRef, db: Session = Depends(get_db)):
    """ÉCRITURE : l'IA génère les précisions du couple×type et les enregistre (`source='ia'`), puis renvoie
    la liste. Appelé par le front UNIQUEMENT quand la LECTURE (GET) est revenue vide — jamais autrement.
    Garde-fou : si la liaison a déjà des précisions, le helper ne régénère pas. Pannes IA absorbées."""
    l = _lien_couple_type(db, body.cycle_id, body.niveau, body.activite_type_id)
    t = db.get(ActiviteType, body.activite_type_id)
    _generer_precisions_ia(db, l, t.label if t else "", body.cycle_id, body.niveau)
    db.commit()
    precs = (db.query(ReferentielTypePrecision)
               .filter(ReferentielTypePrecision.referentiel_activite_type_id == l.id)
               .order_by(ReferentielTypePrecision.ordre, ReferentielTypePrecision.id).all())
    return {"precisions": [
        {"id": p.id, "libelle": p.libelle, "ordre": p.ordre, "source": p.source} for p in precs]}


class AjouterTypeCatalogueBody(BaseModel):
    label: str
    cycle_id: int | None = None   # fournis SEULEMENT quand l'ajout vient d'une SUGGESTION IA : on coche
    niveau: str | None = None     # alors le type pour ce couple avec source='ia' (origine IA tracée).


@router.post("/admin/referentiels/types-activite/catalogue", dependencies=[Depends(_require_admin)])
def ajouter_type_catalogue(body: AjouterTypeCatalogueBody, db: Session = Depends(get_db)):
    """Ajoute un type au CATALOGUE GLOBAL (Create encadré). Anti-doublon par LIBELLÉ insensible à la
    casse — la clé métier du catalogue, exactement comme `matieres.nom` (jamais deux types de même
    libellé). Le type est identifié par son `id` (plus de slug `key`). Renvoie le type (créé ou
    réutilisé) + `deja_present`.

    ORIGINE (badge) : si `cycle_id`+`niveau` sont fournis, l'ajout vient d'une SUGGESTION IA → on COCHE
    aussi le type pour ce couple avec `source='ia'` (get-or-create encadré). Ainsi l'origine IA est
    tracée sur le LIEN même si c'est l'admin qui a cliqué « + ». Sans couple (saisie manuelle), on
    n'ajoute qu'au catalogue : l'origine deviendra 'admin' quand l'admin cochera via le put."""
    label = (body.label or "").strip()
    if not label:
        raise HTTPException(400, "Le libellé du type d'activité est requis.")
    # Origine du type : ajout depuis une SUGGESTION IA (couple fourni) → 'ia' ; saisie MANUELLE → 'admin'.
    from_suggestion = body.cycle_id is not None and bool((body.niveau or "").strip())
    t = db.query(ActiviteType).filter(func.lower(ActiviteType.label) == label.lower()).first()
    deja_present = t is not None
    if t is None:
        maxo = db.query(func.max(ActiviteType.ordre)).scalar()
        t = ActiviteType(label=label, ordre=(maxo or 0) + 1, actif=True,
                         origine=("ia" if from_suggestion else "admin"))
        db.add(t); db.commit(); db.refresh(t)

    # Suggestion IA acceptée → on coche le type pour le couple avec source='ia' (get-or-create encadré).
    coche_ia = False
    if from_suggestion:
        ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
        if ref is not None:
            l = (db.query(ReferentielActiviteType)
                   .filter(ReferentielActiviteType.referentiel_id == ref.id,
                           ReferentielActiviteType.activite_type_id == t.id).first())
            if l is None:
                db.add(ReferentielActiviteType(referentiel_id=ref.id, activite_type_id=t.id,
                                               actif=True, source="ia"))
                coche_ia = True
            elif not l.actif:
                l.actif = True                     # réactivé ; source d'origine conservée
                coche_ia = True
            db.commit()

    return {"id": t.id, "label": t.label, "deja_present": deja_present, "coche_ia": coche_ia}


@router.post("/admin/referentiels/types-activite/detecter", dependencies=[Depends(_require_admin)])
def detecter_types_activite_couple(body: RegleStatutBody, db: Session = Depends(get_db)):
    """L'IA LIT le référentiel du couple et COCHE automatiquement les types déjà au CATALOGUE (liaison
    `source='ia'`). Calque de la détection matières : même source (le TEXTE du PDF déposé, lu à la volée,
    zéro copie) + la brique `detecter_types_activite`. Elle ne crée JAMAIS de type au catalogue : les
    libellés détectés ABSENTS du catalogue remontent en `suggestions` (l'admin les ajoute puis coche).

    CREATE encadré : une liaison n'est créée que si elle n'existe pas ENCORE (contrôle avant écriture)
    → jamais de doublon, et une liaison déjà posée (par l'admin ou une détection précédente, cochée OU
    décochée) est LAISSÉE TELLE QUELLE — l'IA ne se bat pas contre la décision de l'admin."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    texte = _texte_du_pdf(_pdf_du_couple(db, body.cycle_id, body.niveau))   # 404 si pas de PDF
    if not texte.strip():
        raise HTTPException(400, "PDF sans texte lisible : détection impossible.")

    from backend.rag.analyse_amont import detecter_types_activite
    try:
        detectes = detecter_types_activite(texte, db=db)
    except Exception as e:
        raise HTTPException(400, f"Détection des types par l'IA impossible : {e}")

    # Liaisons EXISTANTES du couple, indexées par type — pour ne jamais recréer ni écraser.
    liaisons = {l.activite_type_id
                for l in (db.query(ReferentielActiviteType.activite_type_id)
                            .filter(ReferentielActiviteType.referentiel_id == ref.id).all())}

    coches_ia, deja_lies, suggestions = [], [], []
    vus: set[str] = set()
    for label in detectes:
        cle = label.strip().lower()        # matching par LIBELLÉ, comme les matières
        if not cle or cle in vus:          # même libellé (à la casse près) : une seule fois
            continue
        vus.add(cle)
        t = (db.query(ActiviteType)
               .filter(func.lower(ActiviteType.label) == cle, ActiviteType.actif.is_(True)).first())
        if t is None:
            suggestions.append(label)      # hors catalogue : rien écrit, proposé à l'admin
        elif t.id in liaisons:
            deja_lies.append({"id": t.id, "label": t.label})   # laissé tel quel
        else:
            db.add(ReferentielActiviteType(referentiel_id=ref.id, activite_type_id=t.id,
                                           actif=True, source="ia"))
            coches_ia.append({"id": t.id, "label": t.label})
    db.commit()
    return {"detectes": detectes, "coches_ia": coches_ia,
            "deja_lies": deja_lies, "suggestions": suggestions}
