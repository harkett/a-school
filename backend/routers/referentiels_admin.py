"""Étape 1 du chantier « Référentiel → matières + chunks ».

RÉCEPTION d'un référentiel officiel fourni par l'admin — par LIEN ou par DÉPÔT —,
POINT DE CONTRÔLE (aperçu pour que l'admin valide que c'est le bon document), puis
RANGEMENT + EXTRACTION du texte + ENREGISTREMENT de la provenance (table referentiels).

Périmètre étape 1 UNIQUEMENT : pas d'extraction de matières (étape 2), pas de chunks
(étape 6), pas de recherche web automatique (palier suivant, branché « devant » plus tard).
On reçoit un PDF que l'admin fournit, on le lui montre, on le range et on trace sa provenance.
"""
import re
import shutil
import unicodedata
import uuid
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models_db import Cycle, Niveau, Referentiel
from backend.routers.admin import _require_admin

router = APIRouter()

_ROOT = Path(__file__).resolve().parents[2]                 # racine du projet (d:\A-SCHOOL)
REFERENTIELS_DIR = _ROOT / "REFERENTIELS"
STAGING_DIR = _ROOT / "data" / "referentiels_staging"       # PDF récupéré, en attente de validation
STAGING_DIR.mkdir(parents=True, exist_ok=True)

MAX_PDF_BYTES = 30 * 1024 * 1024   # 30 Mo : un référentiel officiel peut être lourd (BTS CIEL = 88 p.)
APERCU_LIGNES = 25                 # lignes de texte montrées à l'admin pour le contrôle


def _dossier_cle(nom: str) -> str:
    """Nom de niveau → nom de dossier-clé lisible : accents enlevés, MAJUSCULES, tout
    caractère non alphanumérique remplacé par « _ ». Ex. « BTS CIEL Option A » →
    « BTS_CIEL_OPTION_A ». L'identifiant interne (nom_fixe) en est la version minuscule."""
    s = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()
    return s or "REFERENTIEL"


def _apercu(pdf_path: Path) -> tuple[int, str]:
    """(nombre de pages, premières lignes de texte) — la matière du point de contrôle admin."""
    import pdfplumber  # import paresseux : ne pas alourdir le démarrage du serveur
    with pdfplumber.open(str(pdf_path)) as pdf:
        n_pages = len(pdf.pages)
        premier = (pdf.pages[0].extract_text() or "") if n_pages else ""
    lignes = [l for l in premier.splitlines() if l.strip()][:APERCU_LIGNES]
    return n_pages, "\n".join(lignes)


def _stage(content: bytes, filename: str) -> dict:
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
def preparer_lien(body: PreparerLienBody):
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
    return _stage(r.content, filename)


@router.post("/admin/referentiels/preparer-depot", dependencies=[Depends(_require_admin)])
async def preparer_depot(file: UploadFile = File(...)):
    content = await file.read()
    return _stage(content, file.filename or "referentiel.pdf")


# ── Validation : range + extrait le texte + enregistre la provenance ──────────

class ValiderBody(BaseModel):
    token: str
    cycle_id: int
    niveau: str
    fichier_origine: str | None = None   # vrai nom du PDF déposé/téléchargé — gardé en base comme trace
    source: str | None = None
    date_doc: str | None = None


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

    # get-or-create du niveau. Créé « en construction » (traite=False) : la mise à
    # disposition au prof reste l'affaire du garde-fou, APRÈS validation complète (étape 4).
    niveau = (db.query(Niveau)
                .filter(Niveau.nom == niveau_nom, Niveau.cycle_id == cycle.id).first())
    if not niveau:
        maxo = db.query(func.max(Niveau.ordre)).filter(Niveau.cycle_id == cycle.id).scalar()
        niveau = Niveau(cycle_id=cycle.id, nom=niveau_nom, ordre=(maxo or 0) + 1, traite=False)
        db.add(niveau)
        db.flush()

    # Un seul référentiel par niveau (matiere_id NULL = tout le niveau) à ce stade.
    # La mise à jour d'un référentiel existant est un autre geste (palier ultérieur).
    if db.query(Referentiel).filter(Referentiel.niveau_id == niveau.id,
                                    Referentiel.matiere_id.is_(None)).first():
        raise HTTPException(409, f"Un référentiel existe déjà pour « {niveau_nom} ».")

    nom_fixe = _dossier_cle(niveau_nom).lower()
    if db.query(Referentiel).filter(Referentiel.nom_fixe == nom_fixe).first():
        raise HTTPException(409, f"Identifiant de référentiel déjà utilisé : {nom_fixe}.")

    dossier = REFERENTIELS_DIR / _dossier_cle(niveau_nom)
    dossier.mkdir(parents=True, exist_ok=True)
    pdf_final = dossier / "referentiel.pdf"
    shutil.move(str(staged), str(pdf_final))

    # Extraction du texte complet → extraction-texte.txt (UTF-8), même brique que l'ingestion.
    try:
        import pdfplumber  # import paresseux
        with pdfplumber.open(str(pdf_final)) as pdf:
            pages = [(p.extract_text() or "") for p in pdf.pages]
        texte = "\n".join(pages)
        (dossier / "extraction-texte.txt").write_text(texte, encoding="utf-8")
    except Exception as e:
        raise HTTPException(400, f"Extraction du texte impossible : {e}")

    # Disque = nom fixe `referentiel.pdf` (le code ne dépend jamais du nom mouvant de l'EN).
    # Base = `fichier` garde le VRAI nom d'origine (trace, affiché à l'admin), sans contrainte
    # de système de fichiers (c'est du texte). Repli sur le nom de disque si non fourni.
    fichier_origine = (body.fichier_origine.strip() if body.fichier_origine else "") or "referentiel.pdf"
    ref = Referentiel(
        niveau_id=niveau.id, matiere_id=None,
        nom_fixe=nom_fixe, collection=nom_fixe, filtres=None,
        fichier=fichier_origine,
        source=(body.source.strip() if body.source else None),
        date_doc=(body.date_doc.strip() if body.date_doc else None),
    )
    db.add(ref)
    db.commit()

    return {
        "ok": True,
        "cycle": cycle.nom,
        "niveau": niveau_nom,
        "dossier": _dossier_cle(niveau_nom),
        "fichier_disque": "referentiel.pdf",   # nom physique sur le disque (chemin du message)
        "fichier_origine": fichier_origine,     # vrai nom conservé en base
        "nom_fixe": nom_fixe,
        "pages": len(pages),
        "caracteres_extraits": len(texte),
    }
