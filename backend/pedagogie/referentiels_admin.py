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
import unicodedata
import uuid
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models_db import ArbitrageDemande, Cycle, Niveau, Referentiel, ReferentielChunk, Matiere, MatiereNiveau, MatiereCandidate, Setting, User, Famille, FamilleCouple
from backend.systeme.admin import _require_admin, get_settings_dict
from backend.auth import send_custom_email

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
        # On remet à zéro ce qui découlait de l'ANCIEN PDF : prompt de découpe, verdict IA, chunks.
        existing.fichier = fichier_origine
        existing.source = (body.source.strip() if body.source else None)
        existing.date_doc = (body.date_doc.strip() if body.date_doc else None)
        existing.prompt_decoupe = None
        existing.prompt_decoupe_valide = False
        existing.doutes_ia = None
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


# ── Règle de découpe d'un référentiel : lire + valider/rejeter le statut ──
#    Objet à deux faces (explication_clair + critere_technique) porté EN BASE par la ligne
#    `referentiels` du COUPLE (colonnes regle_explication / regle_motif / regle_depose_par /
#    regle_valide) — une règle PAR référentiel, jamais partagée au niveau du cycle. Un niveau =
#    un référentiel = un document = sa règle (aucune exception crèche : le code voit 3 référentiels
#    distincts, donc 3 règles). L'admin ne fait que valider/rejeter le STATUT (regle_valide) ; il
#    ne modifie pas les deux faces.

def _ref_du_couple(db: Session, cycle_id: int, niveau: str) -> Referentiel | None:
    """Résout la ligne `referentiels` (matiere_id NULL) du COUPLE cycle+niveau — le porteur EN BASE
    de la règle de découpe et de l'arbitrage. Lève 404 si le cycle est inconnu, 422 si le niveau
    manque. Renvoie None si le niveau ou le référentiel du couple n'existe pas encore."""
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


def _ecrire_statut_regle(db: Session, cycle_id: int, niveau: str, valide: bool) -> dict:
    """Passe `regle_valide` du couple à la valeur voulue, EN BASE (les deux faces intactes). Lève
    404 si aucun référentiel ou aucune règle posée (motif vide) pour ce couple — jamais de statut
    fantôme."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None or not (ref.regle_motif or "").strip():
        raise HTTPException(404, "Aucune règle de découpe pour ce couple.")
    ref.regle_valide = valide
    ref.doutes_ia = None   # la règle change -> le verdict d'analyse amont est périmé : on le vide
    db.commit()            #   (il sera recalculé une fois, au prochain aperçu/ingestion)
    return {"ok": True, "valide": valide}


@router.get("/admin/referentiels/regle-decoupe", dependencies=[Depends(_require_admin)])
def lire_regle_decoupe(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Lit la règle de découpe du référentiel (lecture seule), EN BASE, résolue par COUPLE
    (cycle + niveau). `existe: false` si aucun référentiel pour ce couple ou aucune règle posée
    (motif vide) → l'écran n'affiche simplement pas la carte."""
    ref = _ref_du_couple(db, cycle_id, niveau)          # 404 cycle inconnu / 422 niveau manquant
    if ref is None or not (ref.regle_motif or "").strip():
        return {"existe": False}
    return {
        "existe": True,
        "explication_clair": ref.regle_explication or "",
        "critere_technique": ref.regle_motif or "",
        "depose_par": ref.regle_depose_par or "",
        "valide": bool(ref.regle_valide),
    }


class RegleStatutBody(BaseModel):
    cycle_id: int
    niveau: str                 # couple = cycle + niveau ; entre dans le chemin de la règle


@router.post("/admin/referentiels/regle-decoupe/valider", dependencies=[Depends(_require_admin)])
def valider_regle_decoupe(body: RegleStatutBody, db: Session = Depends(get_db)):
    """L'admin valide la règle : `valide` → true. Elle devient la règle retenue pour le
    découpage (le branchement effectif du moteur est une étape suivante)."""
    return _ecrire_statut_regle(db, body.cycle_id, body.niveau, True)


@router.post("/admin/referentiels/regle-decoupe/rejeter", dependencies=[Depends(_require_admin)])
def rejeter_regle_decoupe(body: RegleStatutBody, db: Session = Depends(get_db)):
    """L'admin rejette la règle : `valide` → false. Elle repart en proposition."""
    return _ecrire_statut_regle(db, body.cycle_id, body.niveau, False)


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


@router.post("/admin/referentiels/decoupe/valider", dependencies=[Depends(_require_admin)])
def valider_decoupe(body: RegleStatutBody, db: Session = Depends(get_db)):
    """Bouton FINAL : l'admin a contrôlé le résultat de la découpe et l'accepte → `decoupe_valide = true`.
    C'est LA dernière étape : elle seule fait passer la puce du menu au vert. Garde métier : on ne valide
    pas la découpe tant que le PROMPT n'est pas validé (la découpe en dépend)."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    if not ref.prompt_decoupe_valide:
        raise HTTPException(400, "Validez d'abord le prompt de découpe.")
    # LE VRAI PUT : découper + vectoriser + écrire les chunks en base (referentiel_chunks), pour que
    # l'IA des profs les trouve. On ingère AVANT de poser le drapeau : si l'ingestion échoue, le
    # référentiel ne passe PAS « complet » (la puce ne ment jamais).
    from backend.rag.pgvector_store import ingest_pgvector
    try:
        rapport = ingest_pgvector(ref.collection)
    except Exception as e:
        raise HTTPException(400, f"Ingestion de la découpe impossible : {e}")
    ref.decoupe_valide = True
    db.commit()
    return {"ok": True, "decoupe_valide": True, "chunks": rapport.get("total_chunks_PDF")}


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


# ── Aperçu du découpage : ce que la règle validée produit (lecture seule, aucune ingestion) ──

@router.get("/admin/referentiels/apercu-decoupage", dependencies=[Depends(_require_admin)])
def apercu_decoupage_couple(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Aperçu du découpage pour un couple : nombre d'unités, leurs titres, bandes d'âge, cas flous,
    et combien reviennent à ce niveau. LECTURE SEULE (aucune écriture, aucune ingestion, pas de
    vectorisation). L'admin VOIT le résultat de la règle qu'il a validée.
      - pas de règle pour ce cycle  -> {disponible:false, raison:"non_applicable"} (carte masquée) ;
      - règle non validée           -> {disponible:false, raison:"regle_non_validee"} (invite à valider) ;
      - sinon                       -> l'aperçu complet."""
    ref = _ref_du_couple(db, cycle_id, niveau)   # lève 404 cycle / 422 niveau
    if ref is None or not (ref.regle_motif or "").strip():
        return {"disponible": False, "raison": "non_applicable"}
    if not ref.regle_valide:
        return {"disponible": False, "raison": "regle_non_validee"}

    from backend.rag.pgvector_store import apercu_decoupage   # import paresseux (aucun coût au boot)
    try:
        apercu = apercu_decoupage(ref.collection)
    except Exception as e:
        return {"disponible": False, "raison": "erreur", "message": str(e)}
    return {"disponible": True, **apercu}


# ── Arbitrage des cas flous : l'admin tranche la tranche d'âge d'un libellé flou ──
#    Donnée du couple, EN BASE (colonne referentiels.arbitrage, JSON {label: [bandes]}), comme la
#    règle de découpe. La fiche lit cette colonne à l'ingestion (le flou n'est plus deviné).
#    Écrire = trancher ; bandes vides = dé-trancher. On valide les bandes contre celles de la FICHE
#    -> jamais une bande inconnue (qui rangerait l'unité dans aucune collection = trou muet).

@router.get("/admin/referentiels/arbitrage-flou", dependencies=[Depends(_require_admin)])
def lire_arbitrage_flou(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Lit l'arbitrage des cas flous du couple (lecture seule), EN BASE (referentiels.arbitrage).
    Aucun référentiel / aucun arbitrage -> {arbitrages: {}}. La LISTE des flous à trancher se lit
    dans l'aperçu (champ `arbitre`) — ici on sert les décisions."""
    ref = _ref_du_couple(db, cycle_id, niveau)   # 404 cycle inconnu / 422 niveau manquant
    if ref is None or not ref.arbitrage:
        return {"arbitrages": {}}
    try:
        data = json.loads(ref.arbitrage)
    except Exception as e:
        raise HTTPException(400, f"Arbitrage (referentiels.arbitrage) illisible : {e}")
    arb = data if isinstance(data, dict) else {}
    return {"arbitrages": {str(k): [str(b) for b in (v or [])] for k, v in arb.items()}}


class ArbitrageFlouBody(BaseModel):
    cycle_id: int
    niveau: str
    label: str                 # libellé d'âge flou exact (= age_label de l'aperçu)
    bandes: list[str]          # tranche(s) choisie(s) ; [] = retirer la décision (dé-trancher)


@router.post("/admin/referentiels/arbitrage-flou", dependencies=[Depends(_require_admin)])
def enregistrer_arbitrage_flou(body: ArbitrageFlouBody, db: Session = Depends(get_db)):
    """L'admin tranche un cas flou : écrit { label: [bandes] } dans referentiels.arbitrage (JSON).
    Valide les bandes contre celles de la FICHE (jamais une bande inconnue -> pas de trou muet).
    bandes vides = retire la décision. Préserve les autres entrées."""
    label = (body.label or "").strip()
    if not label:
        raise HTTPException(400, "Le libellé du cas flou est requis.")

    # Résoudre le couple -> référentiel -> collection -> fiche (pour ses bandes valides).
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple — rien à arbitrer.")
    from backend.rag.referentiels import get_fiche
    valides = getattr(get_fiche(ref.collection), "BANDES_VALIDES", None)
    if valides is None:
        raise HTTPException(400, "Ce référentiel n'a pas de tranches d'âge à arbitrer.")

    bandes = [str(b).strip() for b in (body.bandes or []) if str(b).strip()]
    hors = [b for b in bandes if b not in valides]
    if hors:
        raise HTTPException(400, f"Tranche(s) d'âge inconnue(s) : {hors}. Attendu : {sorted(valides)}.")

    # Lire l'existant (préserver les autres décisions), appliquer, réécrire EN BASE.
    arb = {}
    if ref.arbitrage:
        try:
            data = json.loads(ref.arbitrage)
            arb = data if isinstance(data, dict) else {}
        except Exception as e:
            raise HTTPException(400, f"Arbitrage (referentiels.arbitrage) illisible : {e}")
    if bandes:
        arb[label] = bandes
    else:
        arb.pop(label, None)               # bandes vides = dé-trancher
    ref.arbitrage = json.dumps(arb, ensure_ascii=False) if arb else None
    # TEMPS 2 : trancher un cas ferme la demande d'avis en attente (le cas sort de « en attente »).
    if bandes:
        db.query(ArbitrageDemande).filter(
            ArbitrageDemande.referentiel_id == ref.id, ArbitrageDemande.label == label
        ).delete()
    db.commit()
    return {"ok": True, "arbitrages": arb}


# ── TEMPS 2 : demander l'avis d'un professionnel quand l'admin ne sait pas trancher ──
#    L'admin envoie un mail (porte SMTP existante `send_custom_email`) et le cas passe « en attente »
#    (table `arbitrage_demandes`, EN BASE — cap « tout en base »). La réponse arrive dans la boîte de
#    l'admin (l'app ne reçoit pas encore : item 65) ; l'admin revient et tranche via arbitrage-flou,
#    ce qui ferme la demande. « en attente » = présence d'une ligne. PROVISOIRE : absorbé par l'item 65.

class DemandeAvisBody(BaseModel):
    cycle_id: int
    niveau: str
    label: str        # libellé flou exact (= age_label de l'aperçu)
    email: str        # adresse du professionnel sollicité
    message: str      # corps du mail, pré-rempli côté écran et éditable par l'admin


@router.post("/admin/referentiels/arbitrage-flou/demander", dependencies=[Depends(_require_admin)])
def demander_avis(body: DemandeAvisBody, db: Session = Depends(get_db)):
    """L'admin demande l'avis d'un professionnel par mail sur un cas flou → envoi via
    `send_custom_email` (aucune archi mail neuve) + le cas passe « en attente » (upsert EN BASE).
    Une demande par cas flou (référentiel + libellé) : redemander met à jour l'adresse, jamais un doublon."""
    label = (body.label or "").strip()
    email = (body.email or "").strip()
    message = (body.message or "").strip()
    if not label:
        raise HTTPException(400, "Le libellé du cas flou est requis.")
    if not email:
        raise HTTPException(400, "L'adresse du professionnel est requise.")
    if not message:
        raise HTTPException(400, "Le message à envoyer est requis.")

    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple — rien à arbitrer.")

    # Objet du mail = étiquette factuelle du COUPLE (cycle · niveau), composée EN BASE → toujours
    # exacte, jamais un couple faux ou oublié. Le corps, lui, reste éditable par l'admin. (Le nom du
    # produit « aSchool » reste en dur ici comme partout — chantier « nom en réglage admin » à part.)
    cycle = db.get(Cycle, body.cycle_id)
    couple = f"{cycle.nom} · {body.niveau.strip()}" if cycle else body.niveau.strip()
    objet = f"aSchool — {couple} : votre avis sur une activité"

    # Envoi via la porte SMTP unique (objet = couple ; corps éditable de l'admin).
    try:
        send_custom_email(email, None, objet, message)
    except Exception as e:
        raise HTTPException(502, f"L'email n'a pas pu être envoyé : {e}")

    # Upsert du statut « en attente » (une demande par cas flou : référentiel + libellé).
    row = (db.query(ArbitrageDemande)
             .filter(ArbitrageDemande.referentiel_id == ref.id, ArbitrageDemande.label == label).first())
    if row:
        row.destinataire = email
    else:
        db.add(ArbitrageDemande(referentiel_id=ref.id, label=label, destinataire=email))
    db.commit()
    return {"ok": True, "en_attente": True, "destinataire": email}


@router.get("/admin/referentiels/arbitrage-flou/en-attente", dependencies=[Depends(_require_admin)])
def lire_arbitrages_en_attente(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Libellés flous EN ATTENTE d'un avis pour ce couple (pour baliser les lignes de l'aperçu).
    Référentiel du couple absent → liste vide (jamais d'erreur bloquante en lecture)."""
    ref = _ref_du_couple(db, cycle_id, niveau)   # 404 cycle inconnu / 422 niveau manquant
    if ref is None:
        return {"en_attente": []}
    rows = db.query(ArbitrageDemande).filter(ArbitrageDemande.referentiel_id == ref.id).all()
    return {"en_attente": [{"label": r.label, "destinataire": r.destinataire} for r in rows]}


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
