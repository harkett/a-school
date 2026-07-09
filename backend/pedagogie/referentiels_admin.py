"""Étape 1 du chantier « Référentiel → matières + chunks ».

RÉCEPTION d'un référentiel officiel fourni par l'admin — par LIEN ou par DÉPÔT —,
POINT DE CONTRÔLE (aperçu pour que l'admin valide que c'est le bon document), puis
RANGEMENT + EXTRACTION du texte + ENREGISTREMENT de la provenance (table referentiels).

Périmètre étape 1 UNIQUEMENT : pas d'extraction de matières (étape 2), pas de chunks
(étape 6), pas de recherche web automatique (palier suivant, branché « devant » plus tard).
On reçoit un PDF que l'admin fournit, on le lui montre, on le range et on trace sa provenance.
"""
import json
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
from backend.core.models_db import Cycle, Niveau, Referentiel, Matiere, MatiereNiveau, MatiereCandidate, User
from backend.systeme.admin import _require_admin

router = APIRouter()

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

    # Un seul référentiel par niveau (matiere_id NULL = tout le niveau) à ce stade.
    # La mise à jour d'un référentiel existant est un autre geste (palier ultérieur).
    if db.query(Referentiel).filter(Referentiel.niveau_id == niveau.id,
                                    Referentiel.matiere_id.is_(None)).first():
        raise HTTPException(409, f"Un référentiel existe déjà pour « {niveau_nom} ».")

    nom_fixe = _dossier_cle(niveau_nom).lower()
    if db.query(Referentiel).filter(Referentiel.nom_fixe == nom_fixe).first():
        raise HTTPException(409, f"Identifiant de référentiel déjà utilisé : {nom_fixe}.")

    # Rangement CYCLE / NIVEAU : le chemin complet (cycle + niveau) identifie le référentiel
    # de façon unique (deux niveaux de même nom dans deux cycles ne se télescopent jamais).
    dossier = REFERENTIELS_DIR / _dossier_cle(cycle.nom) / _dossier_cle(niveau_nom)
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
        "dossier": f"{_dossier_cle(cycle.nom)}/{_dossier_cle(niveau_nom)}",
        "fichier_disque": "referentiel.pdf",   # nom physique sur le disque (chemin du message)
        "fichier_origine": fichier_origine,     # vrai nom conservé en base
        "nom_fixe": nom_fixe,
        "pages": len(pages),
        "caracteres_extraits": len(texte),
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
        return {"existe_referentiel": False, "referentiel": None, "matieres": [], "candidates": []}
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
            {"fichier": ref.fichier, "source": ref.source, "date_doc": ref.date_doc}
            if ref else None
        ),
        "matieres": matieres,
        "candidates": candidates,
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
    db.commit()
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
    db.commit()
    return {"ok": True, "arbitrages": arb}


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
