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
import time
import unicodedata
import uuid
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.database import get_db, session_pour, SCHEMA_REEL
# Règle de nommage des dossiers (« BMG_0-3 » → « BMG_0_3 ») : UNE seule source,
# elle était recopiée mot pour mot ici, dans pgvector_store et dans profil.py.
from backend.core.nommage import dossier_cle as _dossier_cle
from backend.core.resolution_couple import recalculer_nom_affichage
from backend.core.models_db import (
    Activite, Cycle, Niveau, Referentiel, ReferentielChunk, Matiere, User, ActiviteType,
    ReferentielTypePrecision,
)
# SETTING_DEFAULTS n'est plus importé : le gabarit des prompts de type était son dernier
# usage ici, et il se lit désormais EN BASE par `get_prompt` (registre, clé `gabarit_type`).
from backend.core.llm_prompts import PROMPTS
# `detail_admin` : le corps brut renvoyé par le fournisseur (avec son nom et le modèle), collé au
# message d'erreur. Cet écran est un écran d'ADMINISTRATION — celui qui le lit est celui qui doit
# corriger. Renvoyer « le détail est dans les journaux du serveur » l'envoyait chercher ailleurs
# ce que l'application tenait déjà en main.
from backend.llm.generator import detail_admin
from backend.systeme.admin import _require_admin, get_prompt, get_settings_dict

router = APIRouter()
logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[2]                 # racine du depot
REFERENTIELS_DIR = _ROOT / "REFERENTIELS"
STAGING_DIR = _ROOT / "data" / "referentiels_staging"       # PDF récupéré, en attente de validation
STAGING_DIR.mkdir(parents=True, exist_ok=True)

APERCU_LIGNES = 25                 # lignes de texte montrées à l'admin pour le contrôle


# (L'identifiant interne `nom_fixe` est la version minuscule de `_dossier_cle`.)


def _ecrire_matieres_proposees(db: Session, referentiel_id: int, noms: list[str]) -> None:
    """Range les matières LUES par la détection dans le référentiel lui-même (`matieres`,
    `validee=false`) — l'admin cochera celles qu'il retient.

    Plus de table `matieres_candidates` à côté : la proposition et la matière retenue sont la
    MÊME ligne, cocher ne fait que basculer `validee`. Rien n'est écrasé ni supprimé : une
    matière déjà là (retenue ou non) est laissée telle quelle, seules les vraiment nouvelles
    sont ajoutées. Anti-doublon par nom, insensible à la casse, DANS ce référentiel.

    Ménage préalable : les PROPOSITIONS désactivées d'avant (`validee=false`, `actif=false`) sont
    effacées ici. Vestiges d'un temps où écarter ne faisait que désactiver, elles n'apparaissaient
    plus à l'écran mais bloquaient encore l'anti-doublon — une liste vidée puis relue revenait
    presque vide, la lecture étant refusée nom par nom. Une matière RETENUE désactivée, elle, n'est
    jamais touchée : c'est un retrait de programme, décidé par l'admin."""
    (db.query(Matiere)
       .filter(Matiere.referentiel_id == referentiel_id,
               Matiere.validee.is_(False), Matiere.actif.is_(False))
       .delete(synchronize_session=False))
    db.commit()
    deja = {nom.lower(): True for (nom,) in
            db.query(Matiere.nom).filter(Matiere.referentiel_id == referentiel_id).all()}
    maxo = (db.query(func.max(Matiere.ordre))
              .filter(Matiere.referentiel_id == referentiel_id).scalar()) or 0
    max_nom = Matiere.__table__.c.nom.type.length
    for nom in noms:
        nom = (nom or "").strip()
        if not nom or len(nom) > max_nom or nom.lower() in deja:
            continue
        deja[nom.lower()] = True
        maxo += 1
        db.add(Matiere(referentiel_id=referentiel_id, nom=nom, ordre=maxo,
                       actif=True, validee=False))
    db.commit()


def _apercu(pdf_path: Path) -> tuple[int, str]:
    """(nombre de pages, premières lignes de texte) — la matière du point de contrôle admin."""
    import pdfplumber  # import paresseux : ne pas alourdir le démarrage du serveur
    with pdfplumber.open(str(pdf_path)) as pdf:
        n_pages = len(pdf.pages)
        premier = (pdf.pages[0].extract_text() or "") if n_pages else ""
    lignes = [l for l in premier.splitlines() if l.strip()][:APERCU_LIGNES]
    return n_pages, "\n".join(lignes)


def _nettoyer_staging(db: Session) -> None:
    """Nettoyage paresseux de la zone d'attente (constat du 24/07 : 33 aperçus abandonnés,
    202 Mo depuis le 13/07 — rien ne les effaçait jamais). Un fichier plus vieux que le TTL
    n'est plus référencé par personne : le jeton ne vit que le temps d'un aperçu ouvert à
    l'écran, et aucune table en base ne le retient. TTL réglable en base (`staging_ttl_heures`,
    défaut 24), lu comme `depot_max_pages`. Best-effort : un raté de suppression ne bloque
    jamais le dépôt en cours."""
    try:
        ttl_h = float(get_settings_dict(db).get("staging_ttl_heures", 24))
    except (TypeError, ValueError):
        ttl_h = 24.0
    seuil = time.time() - ttl_h * 3600
    for f in STAGING_DIR.glob("*.pdf"):
        try:
            if f.stat().st_mtime < seuil:
                f.unlink()
                logger.info("Zone d'attente : aperçu abandonné supprimé (%s)", f.name)
        except OSError:
            logger.warning("Zone d'attente : suppression impossible de %s", f.name)


def _stage(content: bytes, filename: str, db: Session) -> dict:
    """Valide que c'est un PDF, le range en zone d'attente, renvoie l'aperçu pour le contrôle."""
    _nettoyer_staging(db)   # zone transitoire : chaque dépôt balaie les aperçus abandonnés
    # Plafond de TAILLE (réglage EN BASE `depot_max_mo`, défaut 30) — il était en dur alors que
    # ses deux voisins du même geste (pages, TTL) se réglaient déjà en base.
    try:
        max_mo = float(get_settings_dict(db).get("depot_max_mo", 30))
    except (TypeError, ValueError):
        max_mo = 30.0
    if len(content) > max_mo * 1024 * 1024:
        raise HTTPException(400, f"PDF trop volumineux (maximum {max_mo:g} Mo).")
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

@router.get("/admin/referentiels/liste", dependencies=[Depends(_require_admin)])
def lister_referentiels(db: Session = Depends(get_db)):
    """Liste des référentiels déposés (get direct, lecture seule) — pour la page « Consulter ».
    Une ligne par référentiel, identifié par son couple cycle → niveau. Vide tant qu'aucun dépôt."""
    rows = (db.query(Referentiel, Cycle.nom, Niveau.nom, Cycle.id)
              .join(Niveau, Niveau.id == Referentiel.niveau_id)
              .join(Cycle, Cycle.id == Niveau.cycle_id)
              .order_by(Cycle.ordre, Niveau.ordre).all())

    # `complet` = puce de synthèse du menu Catalogues. REFLET lu en base (get), jamais recopié. Vert =
    # la procédure est ARRIVÉE AU BOUT = `decoupe_valide` (le bouton final « Valider le découpage »).
    # C'est ce booléen, et lui seul, qui pilote le vert — les étapes intermédiaires (matières, prompt)
    # se valident au fur et à mesure mais ne suffisent PAS à déclarer le référentiel complet.
    refs = [
        {"id": r.id, "cycle": cyc, "cycle_id": cyc_id, "niveau": niv, "niveau_id": r.niveau_id,
         # Ce que l'écran AFFICHE : tous les niveaux desservis. `niveau` reste le niveau PORTEUR,
         # qui sert à ouvrir la fiche du couple — le remplacer casserait la navigation.
         "nom_affichage": r.nom_affichage or niv,
         "fichier": r.fichier, "source": r.source, "forcage_motif": r.forcage_motif,
         "complet": bool(r.decoupe_valide)}
        for r, cyc, niv, cyc_id in rows
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


@router.get("/admin/contenu", dependencies=[Depends(_require_admin)])
def lire_contenu(db: Session = Depends(get_db)):
    """Page « Contenu » : TOUT le contenu pédagogique en UN SEUL arbre (get direct, lecture seule).
    Cycle → niveau (le couple) → son référentiel (PDF, texte épuré, découpe, unités), les matières
    de CE référentiel avec leur état, ses types d'activité (avec les précisions du couple). Chaque
    bloc est LU dans sa table — aucune écriture, aucune copie, l'écran n'est qu'une fenêtre sur la
    base. Un niveau sans référentiel apparaît quand même (referentiel et referentiel_id à null) :
    l'admin voit ce qui reste à remplir.

    C'est la lecture UNIQUE de la page « Formations ». Elle lisait avant deux endpoints
    et les recollait — un arbre d'un côté, un catalogue global de matières et des paires
    matière × niveau de l'autre. Ni le catalogue global ni les paires n'existent : les matières
    d'un niveau sont celles de son référentiel, elles sont donc déjà dans l'arbre."""
    cycles = db.query(Cycle).order_by(Cycle.ordre, Cycle.id).all()
    niveaux = db.query(Niveau).order_by(Niveau.ordre, Niveau.id).all()

    # Référentiel du niveau (un seul par niveau, l'unicité de la base le garantit).
    refs = {r.niveau_id: r for r in db.query(Referentiel).all()}

    # Nombre d'unités (chunks) par référentiel — comptage à la volée, rien de stocké.
    nb_unites = dict(db.query(ReferentielChunk.referentiel_id, func.count())
                       .group_by(ReferentielChunk.referentiel_id).all())

    # Matières par RÉFÉRENTIEL, dans leur ordre — TOUTES, sans filtrer : cet arbre est la page où
    # l'admin les gère, il doit donc voir aussi celles que le prof ne voit pas (désactivées, ou
    # seulement proposées par la lecture du document). Chaque ligne porte son état, l'écran tranche.
    mat_par_ref: dict[int, list] = {}
    for m in db.query(Matiere).order_by(Matiere.ordre, Matiere.id).all():
        mat_par_ref.setdefault(m.referentiel_id, []).append(m)

    # Types d'activité par RÉFÉRENTIEL (ils lui appartiennent, comme les matières), puis leurs
    # précisions. TOUS, sans filtrer : même raison que les matières ci-dessus — l'admin gère ici,
    # il doit voir aussi ce que le prof ne voit pas (proposé, pas encore retenu).
    types_par_ref: dict[int, list] = {}
    for t in (db.query(ActiviteType)
                .order_by(ActiviteType.ordre, ActiviteType.id).all()):
        types_par_ref.setdefault(t.referentiel_id, []).append(t)
    precs_par_type: dict[int, list[str]] = {}
    for p in (db.query(ReferentielTypePrecision)
                .order_by(ReferentielTypePrecision.ordre, ReferentielTypePrecision.id).all()):
        precs_par_type.setdefault(p.type_activite_id, []).append(p.libelle)

    arbre = []
    for c in cycles:
        blocs_niveaux = []
        for n in (x for x in niveaux if x.cycle_id == c.id):
            ref = refs.get(n.id)
            blocs_niveaux.append({
                "id": n.id,
                "nom": n.nom,
                # L'id du référentiel voyage à part : c'est lui qu'on adresse pour créer une
                # matière (elle naît DANS un référentiel). À null, le niveau n'a rien reçu.
                "referentiel_id": None if ref is None else ref.id,
                "referentiel": None if ref is None else {
                    "fichier": ref.fichier,
                    "source": ref.source,
                    "date_doc": ref.date_doc,
                    "epure": bool((ref.texte_epure or "").strip()),
                    "decoupe_valide": bool(ref.decoupe_valide),
                    "nb_unites": nb_unites.get(ref.id, 0),
                },
                "matieres": [{"id": m.id, "nom": m.nom, "validee": m.validee, "actif": m.actif,
                              "demande_langue": m.demande_langue}
                             for m in (mat_par_ref.get(ref.id, []) if ref else [])],
                "types": [] if ref is None else [
                    {"id": t.id, "label": t.label, "validee": t.validee, "actif": t.actif,
                     "origine": t.origine, "precisions": precs_par_type.get(t.id, [])}
                    for t in types_par_ref.get(ref.id, [])],
            })
        arbre.append({"id": c.id, "nom": c.nom, "niveaux": blocs_niveaux})
    return {"cycles": arbre}


def _texte_staged(token: str, max_pages: int = 6) -> str:
    """Texte ÉPURÉ des premières pages du PDF en attente (staging) — la structure se lit sur le
    début ; on n'envoie pas tout le PDF à l'IA. Porte d'extraction UNIQUE (rag.extraction) :
    texte vertical des marges + numéros de page écartés. Lève si le document a expiré."""
    staged = STAGING_DIR / f"{token}.pdf"
    if not staged.exists():
        raise HTTPException(400, "Document introuvable (aperçu expiré ?). Recommencez.")
    from backend.rag.extraction import extraire_texte
    return extraire_texte(staged, max_pages=max_pages)


def _texte_cherchable(s: str) -> str:
    """Texte rendu COMPARABLE : accents retirés, minuscules, tout ce qui n'est ni lettre ni
    chiffre devient une espace, espaces réduits à un seul. « Option  B », « OPTION-B » et
    « option b » deviennent alors la même chaîne."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


class ControleCoupleBody(BaseModel):
    token: str
    cycle_id: int
    niveau_id: int


@router.post("/admin/referentiels/controle-couple", dependencies=[Depends(_require_admin)])
def controle_couple(body: ControleCoupleBody, db: Session = Depends(get_db)):
    """CONTRÔLE N°1, au dépôt du document et SANS IA : le document NOMME-T-IL le NIVEAU du couple
    choisi ? Simple recherche de texte (accents, casse et ponctuation ignorés), aucun appel
    extérieur, aucune interprétation.

    C'est le NIVEAU qui décide, pas le cycle : « BTS » se trouve dans les 164 référentiels de BTS
    et ne prouve donc rien. Et on cherche les MOTS du niveau, pas la phrase entière — aucun
    document officiel n'écrit son titre comme nous (« BTS CIEL Option B » y devient « Brevet de
    technicien supérieur Cybersécurité… option B »). Le cycle est cherché en plus, seulement pour
    que le message d'erreur puisse dire ce qui a été trouvé.

    Le document est lu ENTIER, d'un seul tenant. Il l'était déjà, mais après une première passe
    sur six pages : cette avance n'en était pas une — un titre trouvé tôt faisait gagner trois
    secondes, un titre absent faisait payer la lecture DEUX fois. Or c'est précisément quand le
    niveau ne se lit pas dès le titre que le contrôle a besoin d'être court : un programme de
    cycle ne nomme ses années qu'au fil de ses pages. Lecture seule : ne range rien, n'écrit rien."""
    cycle = db.get(Cycle, body.cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle inconnu.")
    niv = db.get(Niveau, body.niveau_id)
    if not niv or niv.cycle_id != cycle.id:
        raise HTTPException(404, "Niveau inconnu pour ce cycle.")

    cible_cycle = _texte_cherchable(cycle.nom)
    mots_niveau = list(dict.fromkeys(_texte_cherchable(niv.nom).split()))   # sans doublon, ordre gardé
    texte = _texte_cherchable(_texte_staged(body.token, max_pages=None))
    trouve_cycle = bool(cible_cycle) and re.search(rf"\b{re.escape(cible_cycle)}\b", texte) is not None
    manquants = [m for m in mots_niveau if not re.search(rf"\b{re.escape(m)}\b", texte)]

    trouve_niveau = bool(mots_niveau) and not manquants
    return {
        "trouve": trouve_niveau,          # le niveau, et lui seul, autorise le dépôt
        "cycle": cycle.nom, "cycle_trouve": trouve_cycle,
        "niveau": niv.nom, "niveau_trouve": trouve_niveau,
        "manquants": manquants,           # les mots du niveau absents du document (pour le message)
    }


class ValiderBody(BaseModel):
    token: str
    cycle_id: int
    niveau_id: int                       # niveau EXISTANT choisi en cascade — créé UNIQUEMENT via Programmes
    fichier_origine: str | None = None   # vrai nom du PDF déposé/téléchargé — gardé en base comme trace
    source: str | None = None
    date_doc: str | None = None
    forcage_motif: str | None = None     # motif si l'admin FORCE malgré une alerte du couple ; NULL sinon
    verif_couple: dict | None = None     # verdict IA du couple {correspond, niveau_lu, raison} — figé à la validation
    controle_niveau: dict | None = None  # PREUVE du contrôle n°1 {niveau, trouve, manquants} — figée à la validation


def _nom_origine_sur_disque(nom: str | None) -> str:
    """Nom d'origine rendu SÛR pour le disque : on ne garde que le nom de fichier (jamais un
    chemin), les caractères interdits deviennent « _ », et l'extension .pdf est forcée. Chaîne
    vide si rien d'exploitable — dans ce cas on ne dépose pas de copie."""
    base = Path((nom or "").strip()).name
    base = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", base).strip(" .")
    if not base:
        return ""
    return base if base.lower().endswith(".pdf") else f"{base}.pdf"


# Les TROIS tâches du bouton « Valider le référentiel », dans leur ordre d'exécution. UNE seule
# source : le serveur les fait ET les annonce (première ligne du flux), l'écran ne fait que les
# afficher — il n'en garde aucune copie en dur. Une tâche de plus = une ligne de plus ici.
TACHES_VALIDATION = [
    {"id": "rangement", "libelle": "Rangement du document"},
    {"id": "lecture",   "libelle": "Lecture du document"},
    {"id": "base",      "libelle": "Enregistrement en base"},
]


def _etapes_enregistrement(body: "ValiderBody", db: Session):
    """LE dépôt proprement dit, SANS AUCUN APPEL IA (bouton « Valider le référentiel »), raconté
    TÂCHE PAR TÂCHE : le document est rangé, son texte est extrait, nettoyé et figé, et la ligne
    du référentiel est écrite.

    Générateur : il émet ("tache", id) dès qu'une tâche des `TACHES_VALIDATION` est TERMINÉE —
    l'écran la coche à cet instant, pas à la fin —, puis ("fin", (réponse, id du référentiel,
    texte épuré)). L'id vaut None quand le jeton était déjà consommé (rien n'a été refait) :
    l'appelant n'a alors aucune suite à donner."""
    staged = STAGING_DIR / f"{body.token}.pdf"
    if not staged.exists():
        # Jeton déjà CONSOMMÉ : le PDF a été rangé par une validation précédente qui a ABOUTI.
        # Cas réel du 24/07 : la validation travaille plusieurs minutes (épuration + matières IA),
        # l'écran perdait patience à 45 s et l'admin recliquait — le reclic recevait un mensonge
        # (« aperçu expiré ? » alors que rien n'expire). Si le référentiel du couple EXISTE, la
        # seule réponse vraie est : déjà validé → succès, l'écran se resynchronise sur la base.
        deja = db.query(Referentiel).filter(Referentiel.niveau_id == body.niveau_id).first()
        if deja is not None:
            cycle_deja = db.get(Cycle, body.cycle_id)
            niveau_deja = db.get(Niveau, body.niveau_id)
            pages_deja = None
            pdf_deja = (REFERENTIELS_DIR / _dossier_cle(cycle_deja.nom) / _dossier_cle(niveau_deja.nom)
                        / "referentiel.pdf") if (cycle_deja and niveau_deja) else None
            if pdf_deja and pdf_deja.exists():
                try:
                    import pdfplumber
                    with pdfplumber.open(str(pdf_deja)) as pdf:
                        pages_deja = len(pdf.pages)
                except Exception:
                    pages_deja = None
            yield ("fin", ({
                "ok": True,
                "deja_valide": True,
                "cycle": cycle_deja.nom if cycle_deja else "",
                "niveau": niveau_deja.nom if niveau_deja else "",
                "dossier": (f"{_dossier_cle(cycle_deja.nom)}/{_dossier_cle(niveau_deja.nom)}"
                            if (cycle_deja and niveau_deja) else ""),
                "fichier_disque": "referentiel.pdf",
                "fichier_origine": deja.fichier or "referentiel.pdf",
                "nom_fixe": deja.nom_fixe,
                "pages": pages_deja,
            }, None, ""))
            return
        raise HTTPException(400, "Le document en attente n'existe plus. Recommencez le dépôt (nouveau lien ou nouveau fichier).")

    cycle = db.get(Cycle, body.cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle inconnu.")

    # Le niveau EXISTE forcément déjà (une seule place pour créer un niveau : l'écran
    # Programmes, bouton « + Niveau »). Le dépôt ne crée JAMAIS de niveau — 404 sinon.
    niveau = db.get(Niveau, body.niveau_id)
    if not niveau or niveau.cycle_id != cycle.id:
        raise HTTPException(404, "Niveau inconnu pour ce cycle.")
    niveau_nom = niveau.nom

    # Un référentiel par niveau (l'unicité de la base le garantit). S'il existe déjà pour ce couple
    # → MISE À JOUR (le nouveau PDF remplace l'ancien, on refait texte/prompt/découpe). Sinon → création.
    existing = db.query(Referentiel).filter(Referentiel.niveau_id == niveau.id).first()
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

    # Le document est AUSSI posé sous SON NOM D'ORIGINE, à côté : en ouvrant le dossier on voit
    # tout de suite quel document a été téléchargé, sans avoir à consulter la base. Un
    # remplacement laisse l'original précédent en place (l'historique du dossier reste lisible).
    # Une copie qui échoue ne fait jamais échouer le dépôt : c'est un confort, pas la pièce maîtresse.
    nom_origine = _nom_origine_sur_disque(body.fichier_origine)
    if nom_origine and nom_origine.lower() != "referentiel.pdf":
        try:
            shutil.copy2(str(pdf_final), str(dossier / nom_origine))
        except OSError:
            logger.exception("depot : copie sous le nom d'origine impossible (%s)", nom_origine)

    yield ("tache", "rangement")   # le document est à sa place définitive

    # LE moment de l'épuration : le texte de travail est extrait UNE SEULE FOIS ici, épuré avec
    # les règles du jour (porte unique rag.extraction), puis FIGÉ en base (texte_epure). Toutes
    # les étapes suivantes (matières, prompt, découpe, re-découpe) LISENT cette colonne — plus
    # aucune ré-extraction du PDF après la validation, et une règle d'épuration ajoutée plus tard
    # ne touche jamais ce dépôt. Le plafond depot_max_pages (contrôlé au dépôt) garde le geste court.
    try:
        import pdfplumber  # import paresseux
        with pdfplumber.open(str(pdf_final)) as pdf:
            n_pages = len(pdf.pages)
        from backend.rag.extraction import extraire_texte
        texte_epure = extraire_texte(pdf_final)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Lecture du PDF impossible : {e}")

    yield ("tache", "lecture")     # pages comptées, texte extrait et épuré

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
    # PREUVE du contrôle n°1 ({niveau, trouve, manquants}), celui qui a AUTORISÉ ce dépôt. Il ne se
    # recalcule pas (texte du PDF + nom du niveau du jour du dépôt) : on le fige, comme au-dessus.
    controle_niveau_json = json.dumps(body.controle_niveau, ensure_ascii=False) if body.controle_niveau else None

    if existing is not None:
        # MISE À JOUR : même ligne (id/collection/niveau stables → liens et MATIÈRES intacts).
        # On remet à zéro ce qui découlait de l'ANCIEN PDF : les chunks. Les PROMPTS du référentiel,
        # eux, ne bougent pas : ils décrivent l'ossature du DIPLÔME, pas celle d'un fichier — un
        # nouveau PDF du même référentiel se découpe et se lit pareil.
        existing.fichier = fichier_origine
        existing.source = (body.source.strip() if body.source else None)
        existing.date_doc = (body.date_doc.strip() if body.date_doc else None)
        existing.forcage_motif = forcage_motif
        existing.verif_couple = verif_couple_json
        existing.controle_niveau = controle_niveau_json   # le NOUVEAU document a son propre contrôle
        existing.texte_epure = texte_epure   # le NOUVEAU PDF impose SON texte de travail
        db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == existing.id).delete()
        # Les unités de l'ANCIEN document viennent de partir : l'étape « Découpe » n'a plus rien à
        # montrer, son drapeau ne peut pas rester levé. Il restait vrai — la cartouche s'affichait
        # verte sans une seule unité en base, et « Découper » restait grisé sans moyen d'en sortir.
        existing.decoupe_valide = False
        # Matières PROPOSÉES par l'ANCIEN PDF et jamais retenues : effacées ici (le nouveau document
        # refera sa propre proposition juste après). Si la détection échoue, on reste sur une liste
        # sans proposition périmée. Les matières RETENUES par l'admin (`validee`) ne sont PAS
        # touchées : c'est son travail, et des profs y sont peut-être déjà rattachés.
        db.query(Matiere).filter(Matiere.referentiel_id == existing.id,
                                 Matiere.validee.is_(False)).delete()
        db.commit()
        ref = existing
    else:
        ref = Referentiel(
            niveau_id=niveau.id,
            nom_fixe=nom_fixe, collection=nom_fixe, filtres=None,
            fichier=fichier_origine,
            source=(body.source.strip() if body.source else None),
            date_doc=(body.date_doc.strip() if body.date_doc else None),
            forcage_motif=forcage_motif,
            verif_couple=verif_couple_json,
            controle_niveau=controle_niveau_json,
            texte_epure=texte_epure,
        )
        db.add(ref)
        # Le rattachement à son niveau porteur part avec la création, tenu par le modèle
        # (`_referentiel_dessert_au_moins_son_niveau_porteur`) : rien à écrire ici.
        db.flush()
        # Le nom d'affichage se calcule APRÈS le rattachement, puisqu'il en dérive. Même
        # transaction : un référentiel ne peut pas exister sans le nom sous lequel il se montre.
        recalculer_nom_affichage(db, ref.id)
        db.commit()

    # AUCUN méta-prompt n'est posé ici, et c'est voulu. Un référentiel neuf arrive avec ses
    # quatre colonnes VIDES : c'est son état normal, pas une panne. La recopie automatique d'un
    # gabarit, essayée le 14/08/2026, a été retirée le jour même — elle remplissait Collège · 4e
    # avec les méta-prompts d'un BTS, qui parlent d'options, de règlement d'examen et de codes
    # d'unités. Un texte faux qui a l'air juste est PIRE qu'une colonne vide : vide, l'écran dit
    # ce qu'il faut charger ; rempli, personne ne va compter les mots pour s'apercevoir qu'il
    # décrit un autre diplôme. C'est la même faute que le repli commun retiré le 08/08/2026
    # (il faisait chercher une grille d'horaires dans un programme de crèche), refaite sous un
    # autre nom. Chaque méta-prompt se charge à la main, dans la cartouche de son étape.

    yield ("tache", "base")        # la fiche du référentiel est écrite (commit fait)

    yield ("fin", ({
        "ok": True,
        "cycle": cycle.nom,
        "niveau": niveau_nom,
        "dossier": f"{_dossier_cle(cycle.nom)}/{_dossier_cle(niveau_nom)}",
        "fichier_disque": "referentiel.pdf",   # nom physique sur le disque (chemin du message)
        "fichier_origine": fichier_origine,     # vrai nom conservé en base
        "fichier_copie": nom_origine,           # le document sous son nom d'origine, à côté
        "nom_fixe": nom_fixe,
        "pages": n_pages,
    }, ref.id, texte_epure))


def _enregistrer_referentiel(body: "ValiderBody", db: Session) -> tuple[dict, int | None, str]:
    """Le même dépôt, déroulé d'un trait : les tâches défilent sans être racontées et seule la
    réponse finale sort. C'est la porte des appels qui veulent UN résultat (endpoints classiques) ;
    le flux, lui, égrène les mêmes tâches. Un seul code, deux façons de le lire."""
    for genre, charge in _etapes_enregistrement(body, db):
        if genre == "fin":
            return charge
    raise HTTPException(500, "Dépôt interrompu avant son terme.")   # inatteignable : le générateur finit toujours par ("fin", …)


@router.post("/admin/referentiels/valider-flux", dependencies=[Depends(_require_admin)])
def valider_flux(body: ValiderBody):
    """Bouton « Valider le référentiel » : le MÊME dépôt que /verifier, mais raconté TÂCHE PAR
    TÂCHE. Une ligne JSON par événement (NDJSON) :

        {"taches": [...]}        les tâches annoncées, dans l'ordre — l'écran dresse sa liste
        {"faite": "rangement"}   … puis une ligne par tâche TERMINÉE, au fil du travail
        {"fin": {…}}             le résultat, identique à celui de /verifier
        {"erreur": "…"}          un échec en cours de route (rien de plus ne suivra)

    L'écran coche donc au fur et à mesure et n'a plus de raison de perdre patience : chaque ligne
    reçue prouve que le serveur travaille (le cas du 24/07 — reclic après 45 s de silence).

    La session est ouverte ICI, et non par `Depends(get_db)` : depuis FastAPI 0.106 une dépendance
    à `yield` est refermée AVANT que le corps streamé ne soit produit — la session serait déjà
    close à la première tâche."""
    def flux():
        db = session_pour(SCHEMA_REEL)
        try:
            yield json.dumps({"taches": TACHES_VALIDATION}, ensure_ascii=False) + "\n"
            for genre, charge in _etapes_enregistrement(body, db):
                if genre == "tache":
                    yield json.dumps({"faite": charge}, ensure_ascii=False) + "\n"
                else:
                    yield json.dumps({"fin": charge[0]}, ensure_ascii=False) + "\n"
        except HTTPException as e:
            yield json.dumps({"erreur": e.detail}, ensure_ascii=False) + "\n"
        except Exception:
            logger.exception("valider-flux : dépôt interrompu")
            yield json.dumps({"erreur": "Validation impossible : le dépôt a été interrompu."},
                             ensure_ascii=False) + "\n"
        finally:
            db.close()
    # `X-Accel-Buffering: no` : sans lui un proxy (nginx) garderait les lignes en réserve et les
    # livrerait toutes à la fin — l'affichage progressif n'aurait plus rien de progressif.
    return StreamingResponse(flux(), media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


class MatieresProposerBody(BaseModel):
    cycle_id: int
    niveau: str


def _prompt_matieres_du_referentiel(db: Session, ref: Referentiel, texte: str) -> str | None:
    """LE prompt qui lit les matières de CE référentiel — le couple cycle+niveau, pas le cycle.

    Rangé sur le référentiel depuis le 06/08/2026. Il était sur le cycle, et c'était faux : le
    cycle « BTS » porte dix-huit niveaux, et le prompt écrit sur le premier déposé était ensuite
    servi à tous les autres — il ne dit rien des dix-sept qui suivent. Une famille
    de diplômes n'est pas une famille de documents.

    S'il n'existe pas encore, il est ÉCRIT ICI, tout de suite, par l'IA (méta-prompt en base + ce
    référentiel comme exemple) : le geste de l'admin reste UN clic sur « Proposer les matières ».

    Le prompt SERT dès qu'il existe. `prompt_matieres_valide` ne commande pas son usage : il dit
    seulement si l'admin l'a relu — il peut l'ouvrir, le corriger et le valider quand il veut.

    None si la rédaction échoue : la détection retombe alors sur le prompt général, sans casser le
    geste (une panne de l'IA ne doit pas empêcher de proposer des matières)."""
    deja = (ref.prompt_matieres or "").strip()
    if deja:
        return deja
    from backend.rag.analyse_amont import generer_prompt_matieres
    try:
        # Le méta-prompt DU NIVEAU passe devant le réglage général (même règle que la découpe).
        prompt = generer_prompt_matieres(texte, db=db,
                                         meta_referentiel=ref.prompt_meta_matieres).strip()
    except Exception:
        logger.exception("matieres : rédaction du prompt du référentiel impossible (id=%s)", ref.id)
        return None
    if not prompt:
        return None
    ref.prompt_matieres = prompt
    ref.prompt_matieres_valide = False   # écrit par l'IA, pas encore relu par l'admin
    db.commit()
    logger.info("matieres : prompt du référentiel id=%s rédigé par l'IA (%d caractères)",
                ref.id, len(prompt))
    return prompt


def _prompt_precisions_du_referentiel(db: Session, ref: Referentiel, texte: str) -> str | None:
    """LE prompt qui lit les PRÉCISIONS d'un type dans CE référentiel — jumeau exact de
    `_prompt_types_du_referentiel`.

    S'il n'existe pas encore, il est ÉCRIT ICI par l'IA (méta-prompt en base + ce référentiel comme
    exemple). Le prompt SERT dès qu'il existe ; `prompt_precisions_valide` dit seulement si l'admin
    l'a relu.

    None si la rédaction échoue : les précisions retombent alors sur le prompt général, sans casser
    le geste — elles sont une aide au remplissage, leur échec ne doit rien faire tomber."""
    deja = (ref.prompt_precisions or "").strip()
    if deja:
        return deja
    from backend.rag.analyse_amont import generer_prompt_precisions
    try:
        prompt = generer_prompt_precisions(texte, db=db,
                                           meta_referentiel=ref.prompt_meta_precisions).strip()
    except Exception:
        logger.exception("precisions : rédaction du prompt du référentiel impossible (id=%s)", ref.id)
        return None
    if not prompt:
        return None
    ref.prompt_precisions = prompt
    ref.prompt_precisions_valide = False   # écrit par l'IA, pas encore relu par l'admin
    db.commit()
    logger.info("precisions : prompt du référentiel id=%s rédigé par l'IA (%d caractères)",
                ref.id, len(prompt))
    return prompt


@router.post("/admin/referentiels/matieres-proposer", dependencies=[Depends(_require_admin)])
def matieres_proposer(body: MatieresProposerBody, db: Session = Depends(get_db)):
    """Bouton « Proposer les matières » — UN seul clic, deux temps chez le serveur :

    1. le prompt de CE référentiel : déjà en base, sinon écrit à l'instant par l'IA à partir du
       document lui-même — un prompt taillé pour ce diplôme lit ce qu'un prompt passe-partout
       laisse tomber, et il ne sert qu'à lui ;
    2. la lecture des matières avec ce prompt-là, sur le texte DÉJÀ figé en base (aucune
       ré-extraction du PDF). Elles sont écrites non cochées — l'admin coche ce qu'il retient."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel enregistré pour ce couple : vérifiez d'abord le document.")
    texte = ref.texte_epure or ""
    if not texte.strip():
        raise HTTPException(400, "Le texte de travail de ce référentiel est vide : rien à lire.")
    from backend.rag.analyse_amont import detecter_matieres
    try:
        noms = detecter_matieres(texte, db=db,
                                 prompt_referentiel=_prompt_matieres_du_referentiel(db, ref, texte))
    except Exception:
        logger.exception("matieres_proposer : détection des matières échouée (%s)", body.niveau)
        raise HTTPException(400, "La proposition des matières par l'IA a échoué.")
    _ecrire_matieres_proposees(db, ref.id, noms)
    return {"ok": True, "proposees": len(noms)}


# ── Écran Prompts → Référentiels : les prompts du niveau, par COUPLES ────────────────
#
# Deux couples, quatre textes, et le même geste dans les deux :
#   - matières : `prompt_meta_matieres` (repère {document}) écrit `prompt_matieres` (repère {texte}) ;
#   - découpe  : `prompt_meta_decoupe`  (repère {document}) écrit `prompt_decoupe`  (repère {texte}).
# Saisis À LA MAIN par l'admin, donc gratuits — c'est tout l'intérêt de cet écran : doter un
# référentiel sans le moindre appel facturé. Une seule lecture pour toute la liste (pas de N+1).
# La route garde son nom d'origine (`prompts-matieres`) : elle sert le même écran, renommer une
# porte déjà appelée ne change rien à ce qu'elle rend.

@router.get("/admin/referentiels/prompts-matieres", dependencies=[Depends(_require_admin)])
def lister_prompts_matieres(db: Session = Depends(get_db)):
    """Un niveau par ligne, avec ses huit textes tels qu'ils sont EN BASE (get, zéro copie).

    `nb_types` / `nb_types_prompt` (08/08/2026) : le NEUVIÈME prompt d'un référentiel n'est pas une
    colonne d'ici mais une ligne par type (`types_activite.prompt`) — celui qui GÉNÈRE ce que le
    professeur reçoit. Sans ces deux comptes, la liste de l'écran Prompts affichait quatre couples
    complets et taisait le seul qui décide de la sortie. Comptés en base, en une requête groupée
    (pas de N+1) : un nombre réel, jamais un nombre stocké à côté qui finirait par mentir."""
    rows = (db.query(Referentiel, Cycle.nom, Cycle.id, Niveau.nom)
              .join(Niveau, Niveau.id == Referentiel.niveau_id)
              .join(Cycle, Cycle.id == Niveau.cycle_id)
              .order_by(Cycle.ordre, Niveau.ordre).all())
    # Types actifs par référentiel, et parmi eux ceux qui portent un prompt de génération.
    comptes: dict[int, tuple[int, int]] = {}
    for rid, total, dotes in db.query(
            ActiviteType.referentiel_id,
            func.count(),
            func.count().filter(func.length(func.trim(ActiviteType.prompt)) > 0),
    ).filter(ActiviteType.actif.is_(True)).group_by(ActiviteType.referentiel_id).all():
        comptes[rid] = (int(total), int(dotes))
    return {"referentiels": [
        {"id": r.id, "cycle": cyc, "cycle_id": cid, "niveau": niv,
         "meta": r.prompt_meta_matieres or "",
         "lecture": r.prompt_matieres or "",
         "lecture_valide": bool(r.prompt_matieres_valide),
         "meta_decoupe": r.prompt_meta_decoupe or "",
         "decoupe": r.prompt_decoupe or "",
         # `decoupe_relue` et non `decoupe_valide` : ce booléen dit que l'admin a RELU le prompt
         # de découpe, pas que le découpage lui-même est validé (`referentiels.decoupe_valide`).
         "decoupe_relue": bool(r.prompt_decoupe_valide),
         "meta_types": r.prompt_meta_types or "",
         "types": r.prompt_types or "",
         "types_relu": bool(r.prompt_types_valide),
         "meta_precisions": r.prompt_meta_precisions or "",
         "precisions": r.prompt_precisions or "",
         "precisions_relu": bool(r.prompt_precisions_valide),
         "nb_types": comptes.get(r.id, (0, 0))[0],
         "nb_types_prompt": comptes.get(r.id, (0, 0))[1]}
        for r, cyc, cid, niv in rows
    ]}


class PromptMetaMatieresBody(BaseModel):
    cycle_id: int
    niveau: str
    prompt: str


@router.get("/admin/referentiels/prompt-meta-matieres", dependencies=[Depends(_require_admin)])
def lire_prompt_meta_matieres(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Le méta-prompt des matières de ce couple. `source` vaut 'referentiel' ou 'aucun'.

    Le repli sur un réglage général a été retiré le 08/08/2026, ici comme dans le moteur : cette
    porte rendait un texte qui n'était PAS celui du niveau regardé, en laissant croire que la
    génération partirait de là."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    propre = (ref.prompt_meta_matieres or "").strip() if ref is not None else ""
    return {"prompt": propre, "source": "referentiel" if propre else "aucun"}


@router.post("/admin/referentiels/prompt-meta-matieres", dependencies=[Depends(_require_admin)])
def enregistrer_prompt_meta_matieres(body: PromptMetaMatieresBody, db: Session = Depends(get_db)):
    """Écrit le MÉTA-prompt des matières de ce niveau. AUCUNE IA : c'est de la saisie.

    Le repère exigé est {document}, et non {texte} : ce texte-ci reçoit le DOCUMENT et rend un
    prompt ; c'est le prompt rendu qui recevra ensuite le texte. Se tromper de repère donne une
    consigne qui ne s'exécutera jamais.

    Vider le champ est permis, mais plus rien ne prend le relais : la génération d'un prompt de
    matières lèvera tant que cette case est vide (repli général retiré le 08/08/2026)."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce niveau : déposez d'abord un document.")
    prompt = (body.prompt or "").strip()
    if prompt and "{document}" not in prompt:
        raise HTTPException(422, "Le méta-prompt doit contenir le marqueur {document} : c'est là "
                                 "que le référentiel sera inséré.")
    ref.prompt_meta_matieres = prompt or None
    db.commit()
    return {"ok": True, "longueur": len(prompt)}


# ── Le MÉTA-prompt de la DÉCOUPE, propre au référentiel (06/08/2026) ─────────────────
#
# Jumeau exact du précédent. Deux portes seulement : on le LIT depuis l'écran du couple (bouton
# « Méta-prompt » de la cartouche Découpe) et on l'ÉCRIT depuis Prompts → Référentiels. La lecture
# dit d'où vient le texte affiché — la case du niveau, ou le réglage général quand elle est vide.

class PromptMetaDecoupeBody(BaseModel):
    cycle_id: int
    niveau: str
    prompt: str


@router.get("/admin/referentiels/prompt-meta-decoupe", dependencies=[Depends(_require_admin)])
def lire_prompt_meta_decoupe(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Le méta-prompt de découpe de ce couple. `source` vaut 'referentiel' ou 'aucun'.

    'aucun' veut dire que l'IA ne peut rédiger aucun prompt de découpe pour ce référentiel : le
    dire ici évite de l'apprendre au moment de payer. Repli général retiré le 08/08/2026."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    propre = (ref.prompt_meta_decoupe or "").strip() if ref is not None else ""
    return {"prompt": propre, "source": "referentiel" if propre else "aucun"}


@router.post("/admin/referentiels/prompt-meta-decoupe", dependencies=[Depends(_require_admin)])
def enregistrer_prompt_meta_decoupe(body: PromptMetaDecoupeBody, db: Session = Depends(get_db)):
    """Écrit le MÉTA-prompt de découpe de ce niveau. AUCUNE IA : c'est de la saisie.

    Le repère exigé est {document}, et non {texte} : ce texte-ci reçoit le DOCUMENT et rend un
    prompt ; c'est le prompt rendu qui recevra ensuite le texte.

    Vider le champ est permis, mais plus rien ne prend le relais : la génération d'un prompt de
    découpe lèvera tant que cette case est vide (repli général retiré le 08/08/2026)."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce niveau : déposez d'abord un document.")
    prompt = (body.prompt or "").strip()
    if prompt and "{document}" not in prompt:
        raise HTTPException(422, "Le méta-prompt doit contenir le marqueur {document} : c'est là "
                                 "que le référentiel sera inséré.")
    ref.prompt_meta_decoupe = prompt or None
    db.commit()
    return {"ok": True, "longueur": len(prompt)}


# ── Le prompt de MATIÈRES du RÉFÉRENTIEL : lu et écrit sur le couple cycle+niveau ────
#
# C'est la porte qui compte : le prompt appartient au référentiel, un par couple. L'écran du couple
# le lit ici et l'enregistre ici — un seul endroit, pas deux éditeurs sur la même colonne.

class PromptMatieresCoupleBody(BaseModel):
    cycle_id: int
    niveau: str
    prompt: str


@router.get("/admin/referentiels/prompt-matieres", dependencies=[Depends(_require_admin)])
def lire_prompt_matieres_couple(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Lit le prompt de matières de CE couple (EN BASE) + son statut de validation.
    `existe:false` si aucun référentiel n'est encore enregistré pour ce couple."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None:
        return {"existe": False, "prompt": "", "valide": False}
    return {"existe": True, "prompt": ref.prompt_matieres or "",
            "valide": bool(ref.prompt_matieres_valide)}


@router.post("/admin/referentiels/prompt-matieres/valider", dependencies=[Depends(_require_admin)])
def valider_prompt_matieres_couple(body: PromptMatieresCoupleBody, db: Session = Depends(get_db)):
    """L'admin écrit (ou corrige) le prompt de CE référentiel et le VALIDE. C'est aussi le moyen de
    le remplir SANS appel IA : un prompt déposé à la main coûte zéro, et évite que le premier clic
    sur « Proposer les matières » en fasse d'abord écrire un. Prompt vide refusé ; sans le marqueur
    {texte}, refusé aussi : sans lui, le document ne serait jamais inséré dedans."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple : déposez d'abord un document.")
    prompt = (body.prompt or "").strip()
    if not prompt:
        raise HTTPException(422, "Le prompt des matières est vide.")
    if "{texte}" not in prompt:
        raise HTTPException(422, "Le prompt doit contenir le marqueur {texte} : c'est là que le "
                                 "document sera inséré.")
    ref.prompt_matieres = prompt
    ref.prompt_matieres_valide = True
    db.commit()
    return {"ok": True, "valide": True}


class PromptDecoupeCoupleBody(BaseModel):
    cycle_id: int
    niveau: str
    prompt: str


@router.post("/admin/referentiels/prompt-decoupe/valider", dependencies=[Depends(_require_admin)])
def valider_prompt_decoupe_couple(body: PromptDecoupeCoupleBody, db: Session = Depends(get_db)):
    """L'admin écrit, corrige ou EFFACE le prompt de découpe de CE référentiel. C'est aussi le
    moyen de le remplir SANS appel IA : un prompt déposé à la main coûte zéro, et évite que le
    premier « Découper » en fasse d'abord écrire un. Sans le marqueur {texte}, refusé : sans lui,
    le document ne serait jamais inséré dedans.

    LE VIDE EST ACCEPTÉ (08/08/2026). Il était refusé, et il n'existait aucune autre porte
    d'écriture : un prompt écrit pour un document qui a changé depuis restait donc en base,
    marqué relu, et servait à la découpe suivante. Refuser l'effacement ne protégeait rien — ça
    enfermait. Un prompt effacé perd sa validation (`prompt_decoupe_valide` à faux) : on ne
    marque pas « relu » une case vide. L'écran avertit AVANT si des unités déjà découpées en
    dépendent, et rappelle qu'un « Découper » sans prompt en fait d'abord rédiger un (payant).

    Les deux portes du CYCLE (lire / valider) ont été retirées le 06/08/2026 avec la colonne
    `cycles.prompt_decoupe` : un cycle porte des diplômes qui ne se découpent pas pareil."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple : déposez d'abord un document.")
    prompt = (body.prompt or "").strip()
    if prompt and "{texte}" not in prompt:
        raise HTTPException(422, "Le prompt doit contenir le marqueur {texte} : c'est là que le "
                                 "document sera inséré.")
    ref.prompt_decoupe = prompt
    ref.prompt_decoupe_valide = bool(prompt)
    db.commit()
    return {"ok": True, "valide": bool(prompt)}


# Les trois portes qui lisaient et écrivaient `cycles.prompt_matieres` (lire / generer / valider)
# ont été retirées le 06/08/2026 avec la colonne elle-même : le prompt des matières appartient au
# RÉFÉRENTIEL, un par couple cycle+niveau. Un cycle « BTS » porte dix-huit diplômes qui ne se lisent
# pas avec les mêmes repères — le prompt écrit sur l'un d'eux n'apprenait rien sur ses voisins.


# ── État d'un couple : le référentiel est-il DÉJÀ enregistré ? nom réel + matières ──

@router.get("/admin/referentiels/etat", dependencies=[Depends(_require_admin)])
def etat_couple(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """À la sélection d'un couple (cycle + niveau) sur l'écran admin : dire si un
    référentiel est DÉJÀ enregistré (« déjà traité »), avec son VRAI nom d'origine
    (colonne `fichier`) + la source, et les matières que ce référentiel porte.

    Lecture seule (aucune écriture). Sert à l'écran à afficher l'état « déjà téléchargé,
    déjà traité » + les matières, et à griser la zone de dépôt. Chaque niveau a sa propre
    ligne `referentiels`, qui possède ses propres matières.

    `matieres` = UNE seule liste, celle du référentiel, chaque ligne portant son état : `validee`
    vrai = retenue par l'admin (elle est au programme du prof), faux = proposée par la détection
    et pas encore cochée. L'écran affiche cette liste telle quelle — il n'a plus à recoller deux
    sources, et deux matières de même nom ne peuvent plus s'y masquer l'une l'autre.
    """
    niveau_nom = (niveau or "").strip()
    niv = (db.query(Niveau)
             .filter(Niveau.nom == niveau_nom, Niveau.cycle_id == cycle_id).first())
    if not niv:
        return {"existe_referentiel": False, "referentiel": None, "matieres": [],
                "prompt_decoupe_valide": False, "decoupe_valide": False}

    # Référentiel du niveau — même clé qu'à la validation.
    ref = db.query(Referentiel).filter(Referentiel.niveau_id == niv.id).first()

    matieres = []
    if ref is not None:
        matieres = [
            {"id": m.id, "nom": m.nom, "validee": m.validee}
            for m in (db.query(Matiere)
                        .filter(Matiere.referentiel_id == ref.id, Matiere.actif == True)  # noqa: E712
                        .order_by(Matiere.ordre, Matiere.id).all())
        ]

    return {
        "existe_referentiel": ref is not None,
        "referentiel": (
            {"fichier": ref.fichier, "source": ref.source, "date_doc": ref.date_doc,
             "forcage_motif": ref.forcage_motif, "verif_couple": ref.verif_couple,
             # La preuve du contrôle n°1, telle qu'elle a été figée au dépôt (get, zéro copie).
             "controle_niveau": ref.controle_niveau}
            if ref else None
        ),
        "matieres": matieres,
        # Le prompt de découpe qui SERT est celui du RÉFÉRENTIEL : c'est SON drapeau qu'on renvoie.
        "prompt_decoupe_valide": bool(ref.prompt_decoupe_valide) if ref else False,
        "decoupe_valide": bool(ref.decoupe_valide) if ref else False,
    }


# ── Relecture : servir le PDF d'origine d'un couple déjà enregistré (lecture seule) ──

@router.get("/admin/referentiels/depot-pdf", dependencies=[Depends(_require_admin)])
def voir_depot_pdf(token: str):
    """Sert le PDF EN ATTENTE (zone de dépôt), pour que l'admin l'OUVRE avant de valider —
    « Voir » dans la liste des documents déposés. Lecture seule : ne range rien, ne modifie rien.
    Le jeton est un uuid4 hexadécimal ; toute autre forme est refusée, donc aucun chemin ne peut
    être fabriqué depuis l'extérieur."""
    jeton = (token or "").strip().lower()
    if len(jeton) != 32 or any(c not in "0123456789abcdef" for c in jeton):
        raise HTTPException(400, "Jeton de document invalide.")
    staged = STAGING_DIR / f"{jeton}.pdf"
    if not staged.exists():
        raise HTTPException(404, "Document introuvable (aperçu expiré ?). Recommencez le dépôt.")
    return FileResponse(str(staged), media_type="application/pdf",
                        headers={"Content-Disposition": "inline; filename=document.pdf"})


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
    """Résout la ligne `referentiels` du COUPLE cycle+niveau — le porteur EN BASE des données du
    couple (prompt de découpe, PDF, matières…). Lève 404 si le cycle est inconnu, 422 si le
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
    return db.query(Referentiel).filter(Referentiel.niveau_id == niv.id).first()


class RegleStatutBody(BaseModel):
    cycle_id: int
    niveau: str                 # couple = cycle + niveau ; entre dans le chemin de la découpe


# ── Prompt de découpe — GÉNÉRÉ PAR L'IA (méta-prompt en base) et rangé sur le RÉFÉRENTIEL ──────
#    depuis le 06/08/2026 (referentiels.prompt_decoupe) : un par couple cycle+niveau. Il a vécu une
#    journée sur le cycle ; c'était faux — le cycle « BTS » porte dix-huit diplômes qui n'ont pas la
#    même ossature. Aucun prompt écrit en dur : le méta-prompt vit en base (Setting), celui du
#    référentiel aussi. Il se lit ET s'écrit sur l'écran Référentiel, cartouche Découpe.

def _pdf_du_couple(db: Session, cycle_id: int, niveau: str) -> Path:
    """Chemin du PDF déposé pour le couple (REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf)."""
    cycle = db.get(Cycle, cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle inconnu.")
    return REFERENTIELS_DIR / _dossier_cle(cycle.nom) / _dossier_cle((niveau or "").strip()) / "referentiel.pdf"


def _texte_du_couple(db: Session, ref: Referentiel) -> str:
    """LE texte de travail du référentiel — get pur de la colonne `texte_epure`, FIGÉE à la
    validation du dépôt avec les règles d'épuration de ce jour-là. Aucun recalcul en lecture.
    Filet pour un dépôt antérieur à la colonne (NULL) : calculé UNE fois depuis le PDF d'origine
    (porte unique rag.extraction) puis ÉCRIT en base — la donnée vit ensuite à sa place."""
    if (ref.texte_epure or "").strip():
        return ref.texte_epure
    niv = db.get(Niveau, ref.niveau_id)
    cycle = db.get(Cycle, niv.cycle_id) if niv else None
    pdf = (REFERENTIELS_DIR / _dossier_cle(cycle.nom) / _dossier_cle(niv.nom) / "referentiel.pdf"
           if cycle else None)
    if pdf is None or not pdf.exists():
        raise HTTPException(404, "Aucun texte de travail pour ce couple (PDF d'origine introuvable).")
    from backend.rag.extraction import extraire_texte
    ref.texte_epure = extraire_texte(pdf)
    db.commit()
    return ref.texte_epure


def _prompt_decoupe_du_referentiel(db: Session, ref: Referentiel, texte: str) -> str:
    """LE prompt qui découpe CE référentiel. Même geste que `_prompt_matieres_du_referentiel` :
    s'il n'existe pas encore, il est ÉCRIT ICI, tout de suite, par l'IA (méta-prompt en base + le
    document lui-même), puis rangé sur le référentiel — le geste de l'admin reste UN clic.

    Le prompt SERT dès qu'il existe. `prompt_decoupe_valide` ne commande pas son usage : il dit
    seulement si l'admin l'a relu — il peut l'ouvrir, le corriger et le valider quand il veut.

    Lève si la rédaction échoue : sans prompt, il n'y a pas de découpe possible (contrairement aux
    matières, aucun prompt général ne peut prendre le relais)."""
    deja = (ref.prompt_decoupe or "").strip()
    if deja:
        return deja
    from backend.rag.analyse_amont import generer_prompt_decoupe
    try:
        # Le méta-prompt du niveau passe devant le réglage général quand il est renseigné.
        prompt = generer_prompt_decoupe(texte, db=db,
                                        meta_referentiel=ref.prompt_meta_decoupe).strip()
    except Exception as e:
        logger.exception("decoupe : rédaction du prompt du référentiel impossible (id=%s)", ref.id)
        raise HTTPException(400, f"Génération du prompt de découpe par l'IA impossible : {e}{detail_admin(e)}")
    if not prompt:
        raise HTTPException(400, "L'IA n'a rendu aucun prompt de découpe.")
    ref.prompt_decoupe = prompt
    ref.prompt_decoupe_valide = False   # écrit par l'IA, pas encore relu par l'admin
    db.commit()
    logger.info("decoupe : prompt du référentiel id=%s rédigé par l'IA (%d caractères)",
                ref.id, len(prompt))
    return prompt


@router.get("/admin/referentiels/prompt-decoupe", dependencies=[Depends(_require_admin)])
def lire_prompt_decoupe(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Lit le prompt de découpe de CE couple (EN BASE) + son statut de validation.
    `existe:false` si aucun référentiel pour ce couple. `decoupe_valide` dit, lui, si SON découpage
    a été ingéré."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None:
        return {"existe": False}
    return {"existe": True, "prompt": ref.prompt_decoupe or "",
            "valide": bool(ref.prompt_decoupe_valide),
            "decoupe_valide": bool(ref.decoupe_valide)}


@router.post("/admin/referentiels/prompt-decoupe/decouper", dependencies=[Depends(_require_admin)])
def decouper_couple(body: RegleStatutBody, db: Session = Depends(get_db)):
    """Déclenche la découpe (LECTURE SEULE, aucune ingestion) avec le prompt DE CE RÉFÉRENTIEL, et
    renvoie les unités produites par l'IA (titre + taille). S'il n'en a pas encore, l'IA l'écrit à
    ce moment-là : le geste de l'admin reste UN clic. Il SERT dès qu'il existe — `valide` dit
    seulement s'il a été relu."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    texte = _texte_du_couple(db, ref)   # le texte de travail figé au dépôt (get en base)
    prompt = _prompt_decoupe_du_referentiel(db, ref, texte)
    from backend.rag.pgvector_store import _decouper_ia
    try:
        chunks = _decouper_ia(texte, prompt)
    except Exception as e:
        raise HTTPException(400, f"Découpe par l'IA impossible : {e}{detail_admin(e)}")
    # LES UNITÉS SONT ÉCRITES ICI, dans le geste qui les a produites (08/08/2026). L'aperçu ne
    # vit plus nulle part entre les deux boutons : ni en mémoire du serveur — un redémarrage le
    # perdait, et la validation repartait alors en appel IA — ni dans une colonne d'attente.
    # Ce qui est affiché est ce qui est en base, et le bouton du bas n'a plus qu'à le valider.
    from backend.rag.pgvector_store import ingest_pgvector
    try:
        ingest_pgvector(ref.collection, decoupe_prete={"prompt": prompt, "chunks": chunks})
    except Exception as e:
        raise HTTPException(400, f"Écriture des unités impossible : {e}{detail_admin(e)}")
    # Une découpe neuve n'est pas une découpe validée : l'admin doit la relire et cliquer.
    ref.decoupe_valide = False
    db.commit()
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
    unites = [{"id": c.id, "titre": c.texte.split("\n")[0].strip(), "taille": len(c.texte)} for c in chunks]
    return {"unites": unites}


@router.get("/admin/referentiels/decoupe/unite", dependencies=[Depends(_require_admin)])
def lire_unite(cycle_id: int, niveau: str, unite_id: int, db: Session = Depends(get_db)):
    """Texte COMPLET d'UNE unité de la découpe (lecture seule, get pur, à la demande du clic).
    C'est exactement la matière première que l'IA des profs reçoit — l'admin la consulte pour
    juger la découpe et mieux cibler. Garde : l'unité doit appartenir au référentiel DU couple."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    chunk = (db.query(ReferentielChunk)
             .filter(ReferentielChunk.id == unite_id,
                     ReferentielChunk.referentiel_id == ref.id).first())
    if chunk is None:
        raise HTTPException(404, "Cette unité n'existe pas pour ce couple.")
    return {"id": chunk.id, "texte": chunk.texte}


@router.get("/admin/referentiels/epuration", dependencies=[Depends(_require_admin)])
def lire_regles_epuration():
    """Consultation PURE des règles d'épuration appliquées à chaque PDF déposé. La liste est lue
    directement dans le module d'épuration (une seule source, l'affichage ne peut pas mentir) :
    l'admin voit, ne modifie pas — une nouvelle règle se fabrique avec le DEV."""
    from backend.rag.extraction import REGLES_EPURATION
    return {"regles": REGLES_EPURATION}


@router.get("/admin/referentiels/epure", dependencies=[Depends(_require_admin)])
def lire_texte_epure(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Le DOCUMENT ÉPURÉ du couple — get pur de la colonne `texte_epure`, figée à la validation
    du dépôt avec les règles de ce jour-là. C'est EXACTEMENT le texte de travail que toutes les
    étapes IA lisent (matières, prompt, découpe). Aucun recalcul à l'affichage."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    return {"texte": _texte_du_couple(db, ref)}


class ModifierUniteBody(BaseModel):
    cycle_id: int
    niveau: str
    unite_id: int
    texte: str


@router.put("/admin/referentiels/decoupe/unite", dependencies=[Depends(_require_admin)])
def modifier_unite(body: ModifierUniteBody, db: Session = Depends(get_db)):
    """UPDATE encadré d'UNE unité : geste de NETTOYAGE (numéro de page collé, coquille
    d'extraction) — jamais une réécriture du référentiel officiel. Le put écrit le texte ET
    recalcule l'empreinte dans le MÊME geste : l'empreinte est une donnée CALCULÉE à partir du
    texte — quand la source change, le calcul se refait, sinon la recherche des profs retrouve
    l'unité sur un texte qui n'existe plus. Garde : l'unité doit appartenir au référentiel du couple."""
    texte = (body.texte or "").strip()
    if not texte:
        raise HTTPException(400, "Le texte de l'unité ne peut pas être vide.")
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    chunk = (db.query(ReferentielChunk)
             .filter(ReferentielChunk.id == body.unite_id,
                     ReferentielChunk.referentiel_id == ref.id).first())
    if chunk is None:
        raise HTTPException(404, "Cette unité n'existe pas pour ce couple.")
    from backend.rag.embeddings import embed_texts
    vec = embed_texts([texte])[0]   # AVANT l'écriture : si le calcul échoue, rien n'est modifié
    chunk.texte = texte
    chunk.embedding = vec
    db.commit()
    return {"ok": True, "id": chunk.id, "taille": len(texte)}






@router.post("/admin/referentiels/decoupe/valider", dependencies=[Depends(_require_admin)])
def valider_decoupe(body: RegleStatutBody, db: Session = Depends(get_db)):
    """Bouton FINAL : l'admin a relu les unités affichées et les accepte. C'est un PUT sur un
    drapeau, et RIEN D'AUTRE — il ne découpe pas, il n'appelle pas l'IA, il ne recalcule aucun
    vecteur, il ne réécrit pas ce qui est déjà là. Les unités ont été écrites par « Découper »,
    le geste qui les a produites ; celui-ci ne fait que dire « je les valide ».

    POURQUOI C'EST ÉCRIT EN GRAS (08/08/2026). Ce bouton lançait toute la chaîne d'ingestion, et
    redécoupait PAR L'IA quand l'aperçu manquait — en silence, sur le document entier. Le
    fournisseur a fini par refuser la requête, et un référentiel dont les 61 unités étaient déjà
    en base est devenu impossible à valider. Un bouton de validation valide ; il ne fabrique rien.

    Le seul refus possible : il n'y a aucune unité à valider."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    combien = (db.query(func.count(ReferentielChunk.id))
               .filter(ReferentielChunk.referentiel_id == ref.id).scalar() or 0)
    if combien == 0:
        raise HTTPException(400, "Aucune unité à valider pour ce référentiel : lancez d'abord "
                                 "« Découper », c'est lui qui lit le document et écrit les unités.")
    ref.decoupe_valide = True
    db.commit()
    return {"ok": True, "status": "done", "chunks": combien}


@router.get("/admin/referentiels/decoupe/statut", dependencies=[Depends(_require_admin)])
def statut_decoupe(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """État de l'ingestion d'un couple (surveillance après « Valider le découpage »).

    Depuis le 08/08/2026, plus rien ne tourne en tâche de fond : « Valider » ne fait qu'un put.
    Cette route lit donc la base et rien d'autre — `decoupe_valide` et le nombre d'unités."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None:
        return {"status": "absent", "decoupe_valide": False, "chunks": 0, "message": None}
    n = db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == ref.id).count()
    # Plus rien ne tourne en tâche de fond depuis que « Valider » ne fait qu'un put (08/08/2026) :
    # l'état d'orchestration a disparu avec elle. La base répond seule, et elle ne ment pas.
    return {"status": "done" if ref.decoupe_valide else "idle",
            "decoupe_valide": bool(ref.decoupe_valide), "chunks": n,
            "message": None, "progress": None}


# ── Méta-prompt de découpe : PLUS DE PORTE ICI (retirée le 02/08/2026) ───────────────────
#
# Il y avait a cet endroit un GET et un PUT `/admin/referentiels/meta-prompt` qui lisaient et
# ecrivaient `Setting['prompt_meta_decoupe']`. Aucun ecran ne les appelait — ni le frontend,
# ni un script, ni un test. Et le PUT ecrivait CETTE MEME LIGNE sans passer par
# `valider_prompt` : il ne verifiait que « non vide ». Un texte sans `{document}` y passait,
# et le meta-prompt ne recevait alors plus jamais le document a decouper. C'etait une seconde
# porte, non gardee, sur une serrure deja posee.
#
# La porte qui reste est PUT /api/admin/prompts (backend/systeme/admin.py) : meme ligne en
# base (`prompt_` + la cle du registre), mais precedee de `valider_prompt`, qui refuse en 400
# tout texte ou `{document}` a disparu. La cle `meta_decoupe` est au registre
# (llm_prompts.py, categorie « admin », mode « replace ») donc l'ecran Prompts — Admin
# l'affiche et l'edite comme les autres.

# ── L'admin RETIENT les matières d'un référentiel : cocher = `validee=true` (idempotent) ──

class EnregistrerMatieresBody(BaseModel):
    cycle_id: int
    niveau: str
    matieres: list[str]


@router.post("/admin/referentiels/matieres", dependencies=[Depends(_require_admin)])
def enregistrer_matieres(body: EnregistrerMatieresBody, db: Session = Depends(get_db)):
    """L'admin RETIENT des matières pour le référentiel de ce couple. Pour chaque nom : la matière
    du référentiel qui le porte est VALIDÉE (et réactivée si elle était retirée) ; un nom que le
    référentiel ne porte pas encore est créé, validé d'emblée — c'est une saisie de l'admin, donc
    un choix. Le même nom dans un AUTRE référentiel n'est jamais réutilisé : chaque référentiel a
    les siennes. Idempotent : relancer ne crée rien en double. Ne supprime JAMAIS rien."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple : déposez d'abord son document.")

    # Dédoublonnage des noms reçus (insensible à la casse), 1er libellé vu conservé.
    # Garde de longueur AVANT toute écriture : la limite est LUE sur la colonne (zéro copie),
    # et le refus est un message humain — jamais un 500 brut à l'écran (cas réel du 24/07).
    max_nom = Matiere.__table__.c.nom.type.length
    noms, vus = [], set()
    for raw in body.matieres:
        nom = (raw or "").strip()
        if len(nom) > max_nom:
            raise HTTPException(422, f"Le nom de matière « {nom[:60]}… » est trop long "
                                     f"({len(nom)} caractères, maximum {max_nom}). "
                                     "Raccourcissez-le puis relancez « Récupérer ».")
        if nom and nom.lower() not in vus:
            vus.add(nom.lower()); noms.append(nom)

    # Les matières DE CE RÉFÉRENTIEL, indexées par nom en minuscules (une seule lecture).
    du_ref = {m.nom.lower(): m for m in
              db.query(Matiere).filter(Matiere.referentiel_id == ref.id).all()}
    maxo = (db.query(func.max(Matiere.ordre))
              .filter(Matiere.referentiel_id == ref.id).scalar()) or 0

    ajoutees, deja = [], []
    for nom in noms:
        mat = du_ref.get(nom.lower())
        if mat is not None and mat.validee and mat.actif:
            deja.append(nom)
            continue
        if mat is not None:
            mat.validee = True
            mat.actif = True
        else:
            maxo += 1
            db.add(Matiere(referentiel_id=ref.id, nom=nom, ordre=maxo, actif=True, validee=True))
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
    """Renomme une matière par son id : garde l'identifiant, donc aucun lien (prof, historique)
    n'est cassé. Le renommage ne touche QUE cette matière-là : une matière de même nom dans un
    autre référentiel est une autre matière, elle ne bouge pas. Refuse un nom vide ou déjà porté
    par une AUTRE matière DU MÊME référentiel (anti-doublon, comme l'unique en base)."""
    nom = (body.nouveau_nom or "").strip()
    if not nom:
        raise HTTPException(400, "Le nouveau nom est requis.")
    max_nom = Matiere.__table__.c.nom.type.length   # même garde qu'à l'enregistrement (zéro copie)
    if len(nom) > max_nom:
        raise HTTPException(422, f"Ce nom est trop long ({len(nom)} caractères, "
                                 f"maximum {max_nom}). Raccourcissez-le puis revalidez.")
    mat = db.get(Matiere, body.matiere_id)
    if not mat:
        raise HTTPException(404, "Matière inconnue.")
    autre = (db.query(Matiere)
               .filter(Matiere.referentiel_id == mat.referentiel_id,
                       func.lower(Matiere.nom) == nom.lower(), Matiere.id != mat.id).first())
    if autre:
        raise HTTPException(409, f"Une autre matière de ce référentiel porte déjà le nom « {nom} ».")
    ancien = mat.nom
    mat.nom = nom
    db.commit()
    return {"ok": True, "id": mat.id, "ancien_nom": ancien, "nouveau_nom": nom}


# ── Retirer une matière du programme = la DÉSACTIVER (jamais de suppression dure) ──

class RetirerMatiereBody(BaseModel):
    cycle_id: int
    niveau: str
    matiere_id: int


@router.post("/admin/referentiels/retirer-matiere", dependencies=[Depends(_require_admin)])
def retirer_matiere(body: RetirerMatiereBody, db: Session = Depends(get_db)):
    """Deux gestes, selon ce qu'est la ligne — et c'est la seule différence qui compte :

    • une PROPOSITION (`validee=false`) : elle n'est JAMAIS entrée au programme, aucun prof ne la
      voit. Elle est SUPPRIMÉE, vraiment (DELETE). La désactiver serait pire qu'inutile : la ligne
      resterait en base et l'anti-doublon de la lecture suivante refuserait de la reproposer — le
      document semblait alors ne plus rien contenir (constat du 04/08 : une liste vidée puis relue
      revenait avec UNE matière).
    • une matière RETENUE (`validee=true`) : elle est au programme, des profs peuvent y être
      rattachés. Elle est DÉSACTIVÉE (`actif=False`), historique conservé, retrait réversible.

    Garde commune : la matière doit appartenir au référentiel de ce couple — on ne touche pas à
    la matière d'un autre diplôme depuis cet écran. Signale, sans rien casser, combien de profs
    l'ont encore à leur profil."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    mat = db.get(Matiere, body.matiere_id)
    if not mat or mat.referentiel_id != ref.id:
        raise HTTPException(404, "Cette matière n'appartient pas au référentiel de ce couple.")
    if not mat.validee:
        nom = mat.nom
        db.delete(mat)
        db.commit()
        return {"ok": True, "supprimee": True, "matiere": nom, "profs": 0}
    if not mat.actif:
        return {"ok": True, "deja_absente": True, "matiere": mat.nom, "profs": 0}
    # Comptage PAR CLÉ, sur les DEUX rattachements — comme le fait la suppression du référentiel
    # vingt lignes plus bas. Ne compter que `subject_id` sous-estimait : un prof dont c'est le
    # couple de TRAVAIL perdait sa matière sans figurer dans le nombre annoncé à l'admin.
    profs = (db.query(User)
               .filter((User.subject_id == mat.id) | (User.travail_matiere_id == mat.id))
               .count())
    mat.actif = False
    db.commit()
    return {"ok": True, "deja_absente": False, "matiere": mat.nom, "profs": profs}


# ── CRUD référentiel : supprimer ────────────────────────────────────────────

class SupprimerRefBody(BaseModel):
    cycle_id: int
    niveau: str


@router.post("/admin/referentiels/supprimer", dependencies=[Depends(_require_admin)])
def supprimer_referentiel(body: SupprimerRefBody, db: Session = Depends(get_db)):
    """Supprime le référentiel d'un couple — UNIQUEMENT s'il n'a JAMAIS servi (aucun chunk ingéré)
    et si aucun prof n'est rattaché à l'une de ses matières ; sinon refus (409). Efface la ligne
    `referentiels` + le PDF sur disque. Ses matières partent avec lui (CASCADE) : une matière
    n'existe pas sans le document qui la nomme."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    n = db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == ref.id).count()
    if n > 0:
        raise HTTPException(409, f"Référentiel utilisé (déjà ingéré : {n} unité(s)) — suppression impossible.")
    # DELETE encadré : ses matières tombent avec lui, or un prof peut en avoir une à son
    # profil ou à son couple de travail. On refuse AVANT d'écrire, avec un message qui dit quoi faire.
    profs = (db.query(User)
               .join(Matiere, (Matiere.id == User.subject_id) | (Matiere.id == User.travail_matiere_id))
               .filter(Matiere.referentiel_id == ref.id).count())
    if profs > 0:
        raise HTTPException(409, f"{profs} professeur(s) travaillent sur une matière de ce référentiel — "
                                 "suppression impossible. Changez d'abord leur matière.")
    _pdf_du_couple(db, body.cycle_id, body.niveau).unlink(missing_ok=True)
    db.delete(ref)
    db.commit()
    return {"ok": True}


# ── Types d'activité D'UN RÉFÉRENTIEL — exact calque du patron MATIÈRES (05/08/2026) ─────────
#
# Un type d'activité est une donnée LUE DANS LE DOCUMENT, au même titre qu'une matière : le
# référentiel dit quels formats de travail il met en œuvre. Il lui appartient donc (table
# `types_activite`, colonne `referentiel_id`), et le geste est celui des matières :
#
#   la détection PROPOSE (validee=false) → l'admin RETIENT (validee=true) → le prof voit.
#
# CE QUE ÇA REMPLACE. Il y avait ici un CATALOGUE GLOBAL coché/décoché par une liaison N–N. Ce
# catalogue était le vestige d'un seed en dur (migration a1b2c3d4e5f6, 13 familles) : la liste
# précédait les référentiels, il fallait donc un moyen de s'y raccrocher. Sa conséquence était
# qu'un type lu dans UN document était créé dans la table PARTAGÉE par tous les couples, sans
# clic et sans retour possible — et que son libellé repartait ensuite comme vocabulaire dans le
# prompt de détection de tous les autres. Voir la migration e4a7c2b9d5f8.
#
# get pour lire, put/post/delete pour écrire, zéro donnée en dur.


def _type_du_couple(db: Session, cycle_id: int, niveau: str, type_id: int) -> ActiviteType:
    """Résout LE type d'activité du référentiel de ce couple. Remplace `_lien_couple_type` : il n'y
    a plus de liaison à traverser, le type porte lui-même son référentiel. 404 si le couple n'a pas
    de référentiel, ou si ce type n'est pas le sien (garde de portée : un id d'un autre référentiel
    ne donne jamais accès à ses précisions)."""
    ref = _ref_du_couple(db, cycle_id, niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    t = (db.query(ActiviteType)
           .filter(ActiviteType.id == type_id, ActiviteType.referentiel_id == ref.id).first())
    if t is None:
        raise HTTPException(404, "Ce type d'activité n'appartient pas à ce référentiel.")
    return t


@router.get("/admin/referentiels/types-activite", dependencies=[Depends(_require_admin)])
def lire_types_activite(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Les types d'activité DU référentiel de ce couple (lecture seule, get pur). Une seule liste :
    propositions et types retenus s'y côtoient, `validee` les distingue — comme la table des
    matières. Liste vide si le couple n'a pas encore de référentiel (rien à montrer) ; 404/422
    seulement pour cycle inconnu / niveau manquant (via `_ref_du_couple`).

    `nb_precisions` est COMPTÉ en base (un count groupé, pas de N+1) : l'écran affiche un nombre
    réel, jamais un nombre stocké à côté qui finirait par mentir."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None:
        return {"types": []}
    types = (db.query(ActiviteType)
               .filter(ActiviteType.referentiel_id == ref.id, ActiviteType.actif.is_(True))
               .order_by(ActiviteType.ordre, ActiviteType.id).all())
    nb_par_type = dict(
        db.query(ReferentielTypePrecision.type_activite_id, func.count())
          .filter(ReferentielTypePrecision.type_activite_id.in_([t.id for t in types]))
          .group_by(ReferentielTypePrecision.type_activite_id).all()
    ) if types else {}
    return {"types": [
        {"id": t.id, "label": t.label, "validee": bool(t.validee), "origine": t.origine,
         "prompt": t.prompt or "", "nb_precisions": int(nb_par_type.get(t.id, 0))}
        for t in types
    ]}


def _generer_prompt_type(db: Session, label: str, niveau: str) -> str:
    """Prompt de génération d'un type d'activité POUR CE référentiel, produit AUTOMATIQUEMENT à la
    création du type (détection ou ajout manuel).

    Le GABARIT vit EN BASE (réglage `prompt_gabarit_type`) — il était écrit en dur ici alors que
    tous les autres prompts du produit sont administrables : le retoucher demandait un
    redéploiement. Deux emplacements sont remplis ici, {label} et {niveau} ; deux autres sont
    laissés INTACTS pour la génération : {texte} (l'idée du prof, elle mène) et {referentiel} (le
    programme officiel). D'où le remplacement ciblé plutôt qu'un format() global, qui consommerait
    aussi les emplacements de la génération.

    Le résultat est stocké sur la ligne du type ; l'admin peut le relire et le corriger via
    ✎ Prompt — retoucher le gabarit ne réécrit donc jamais les prompts déjà posés.

    ET ON CONTRÔLE CE QU'ON PRODUIT. Le garde-fou d'écriture ne couvre pas une valeur posée
    directement en base (Adminer est là, sur ce poste). Le prompt fabriqué ici est donc relu par
    la MÊME fonction que ✎ Prompt : si le gabarit produit un prompt invalide, l'admin l'apprend en
    créant le type, avec un message qui nomme le défaut — jamais le prof au milieu d'une
    génération."""
    from backend.contenu.activites import valider_prompt_couple   # import local : pas de cycle
    gabarit = get_prompt(db, "gabarit_type")
    prompt = gabarit.replace("{label}", label).replace("{niveau}", niveau)
    err = valider_prompt_couple(prompt)
    if err:
        raise HTTPException(
            400,
            f"Le gabarit des prompts de type (écran Prompts → « {PROMPTS['gabarit_type']['label']} ») "
            f"produit un prompt inutilisable : {err}"
        )
    return prompt


def _creer_type(db: Session, ref: Referentiel, label: str, niveau: str, *,
                origine: str, validee: bool) -> ActiviteType:
    """CREATE encadré d'un type POUR CE référentiel. Anti-doublon par LIBELLÉ insensible à la casse
    DANS CE référentiel (la clé métier, comme `matieres.nom`) : un libellé déjà présent renvoie la
    ligne existante au lieu d'en créer une seconde. Prompt gabarit posé dès la création — un type
    du référentiel est opérationnel tout de suite, jamais « prompt vide »."""
    existant = (db.query(ActiviteType)
                  .filter(ActiviteType.referentiel_id == ref.id,
                          func.lower(ActiviteType.label) == label.lower()).first())
    if existant is not None:
        return existant
    ordre_max = (db.query(func.coalesce(func.max(ActiviteType.ordre), -1))
                   .filter(ActiviteType.referentiel_id == ref.id).scalar())
    t = ActiviteType(referentiel_id=ref.id, label=label, ordre=ordre_max + 1,
                     origine=origine, validee=validee, actif=True,
                     prompt=_generer_prompt_type(db, label, niveau))
    db.add(t)
    db.flush()
    return t


class RetenirTypeBody(BaseModel):
    cycle_id: int
    niveau: str
    type_id: int
    validee: bool                       # True = retenu (le prof le voit) · False = remis en proposition


@router.put("/admin/referentiels/types-activite", dependencies=[Depends(_require_admin)])
def retenir_type_activite(body: RetenirTypeBody, db: Session = Depends(get_db)):
    """RETENIR (ou remettre en proposition) UN type du référentiel — LE geste de l'admin, écrit
    direct en base au clic. `validee=true` : le type entre au programme, le prof le voit.
    `validee=false` : il redevient une proposition, invisible du prof, mais il reste à l'écran.

    C'est ici que se joue la règle : une lecture d'IA n'entre jamais dans les menus d'un
    professeur toute seule. Idempotent."""
    t = _type_du_couple(db, body.cycle_id, body.niveau, body.type_id)
    t.validee = body.validee
    db.commit()
    return {"ok": True, "type_id": t.id, "validee": t.validee}


class AjouterTypeBody(BaseModel):
    cycle_id: int
    niveau: str
    label: str


@router.post("/admin/referentiels/types-activite", dependencies=[Depends(_require_admin)])
def ajouter_type_activite(body: AjouterTypeBody, db: Session = Depends(get_db)):
    """Ajout MANUEL d'un type à CE référentiel (l'admin le nomme lui-même) : `origine='admin'` et
    RETENU d'emblée — il n'a pas à se proposer à lui-même ce qu'il vient d'écrire. Anti-doublon par
    libellé dans ce référentiel (`deja_present`). Rien de global : ce type n'existe que pour ce
    document."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    label = (body.label or "").strip()
    if not label:
        raise HTTPException(400, "Le libellé du type d'activité est requis.")
    deja = (db.query(ActiviteType)
              .filter(ActiviteType.referentiel_id == ref.id,
                      func.lower(ActiviteType.label) == label.lower()).first())
    t = _creer_type(db, ref, label, body.niveau, origine="admin", validee=True)
    if deja is None:
        db.commit()
        db.refresh(t)
    else:
        db.rollback()
    return {"id": t.id, "label": t.label, "deja_present": deja is not None}


@router.delete("/admin/referentiels/types-activite/{type_id}", dependencies=[Depends(_require_admin)])
def supprimer_type_activite(type_id: int, cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """DELETE encadré d'un type du référentiel : un VRAI delete (ses précisions partent avec lui,
    CASCADE), jamais un `actif=false` caché — le mot du bouton dit le geste.

    REFUS (409) si des activités déjà générées s'appuient sur ce type : elles y sont rattachées par
    clé étrangère, l'effacer casserait l'historique d'un professeur. Le message dit combien, comme
    pour la suppression d'un référentiel. Une future détection recréera le type si le document le
    nomme encore."""
    t = _type_du_couple(db, cycle_id, niveau, type_id)
    faites = db.query(Activite).filter(Activite.activite_type_id == t.id).count()
    if faites > 0:
        raise HTTPException(409, f"{faites} activité(s) déjà générée(s) s'appuient sur « {t.label} » — "
                                 "suppression impossible. L'historique des professeurs y est rattaché.")
    db.delete(t)
    db.commit()
    logger.info("Type d'activité supprimé : id=%s label=%s", type_id, t.label)
    return {"ok": True, "id": type_id}


def _generer_precisions_ia(db: Session, t: ActiviteType, niveau: str) -> None:
    """Écrit les précisions IA d'un type (source='ia'). IDEMPOTENT : ne fait rien si le type en a
    déjà (relancer ne réécrase pas, et n'écrase JAMAIS les précisions 'admin' saisies à la main).
    Toute panne (texte absent, IA down) est ABSORBÉE (loggée) : les précisions sont une aide au
    remplissage, leur échec ne doit pas faire tomber le geste qui les a demandées."""
    deja = (db.query(ReferentielTypePrecision.id)
              .filter(ReferentielTypePrecision.type_activite_id == t.id).first())
    if deja is not None:
        return
    try:
        ref = db.get(Referentiel, t.referentiel_id)
        texte = _texte_du_couple(db, ref)   # le texte de travail figé au dépôt (get en base)
        if not texte.strip():
            return
        from backend.rag.analyse_amont import suggerer_precisions_type
        # Le prompt DU RÉFÉRENTIEL passe devant le prompt général (même règle que les types).
        libelles = suggerer_precisions_type(
            t.label, niveau, texte, db=db,
            prompt_referentiel=_prompt_precisions_du_referentiel(db, ref, texte))
    except Exception as e:
        logger.warning("Précisions IA non générées (geste non bloqué) type=%s : %s", t.id, e)
        return
    for i, lib in enumerate(libelles):
        lib = (lib or "").strip()
        if not lib:
            continue
        existe = (db.query(ReferentielTypePrecision.id)
                    .filter(ReferentielTypePrecision.type_activite_id == t.id,
                            func.lower(ReferentielTypePrecision.libelle) == lib.lower()).first())
        if existe is None:
            db.add(ReferentielTypePrecision(type_activite_id=t.id, libelle=lib, ordre=i, source="ia"))


class PromptTypeBody(BaseModel):
    cycle_id: int
    niveau: str
    type_id: int
    prompt: str


@router.put("/admin/referentiels/types-activite/prompt", dependencies=[Depends(_require_admin)])
def ecrire_prompt_type(body: PromptTypeBody, db: Session = Depends(get_db)):
    """UPDATE du prompt d'un type — réécrit la colonne `prompt` de sa ligne (une seule place, zéro
    copie). Contrôles : type du référentiel (404), prompt non vide (422), et le MÊME garde-fou
    d'écriture que partout : ce prompt part ensuite dans `modele.format(...)` (api_generate), qui
    n'attrape que KeyError. Un prompt sans {texte} ignorerait l'idée du prof en silence ; une
    accolade seule rendrait un 500 nu au premier clic d'un enseignant. On refuse AVANT d'écrire."""
    t = _type_du_couple(db, body.cycle_id, body.niveau, body.type_id)
    if not (body.prompt or "").strip():
        raise HTTPException(422, "Le prompt est vide.")
    from backend.contenu.activites import valider_prompt_couple   # import local : pas de cycle
    err = valider_prompt_couple(body.prompt)
    if err:
        raise HTTPException(400, err)
    t.prompt = body.prompt
    db.commit()
    return {"ok": True, "type_id": t.id}


@router.get("/admin/referentiels/types-activite/precisions", dependencies=[Depends(_require_admin)])
def lister_precisions_type(cycle_id: int, niveau: str, type_id: int, db: Session = Depends(get_db)):
    """Précisions d'un type — get direct dans `referentiel_type_precisions`, ordonné (ordre, id).
    Lecture seule : la liste est LUE, jamais recopiée. Elles pendent sur le type, donc sur le
    référentiel : « exploration sensorielle » n'existe que pour le document qui l'a nommée."""
    t = _type_du_couple(db, cycle_id, niveau, type_id)
    precs = (db.query(ReferentielTypePrecision)
               .filter(ReferentielTypePrecision.type_activite_id == t.id)
               .order_by(ReferentielTypePrecision.ordre, ReferentielTypePrecision.id).all())
    return {"precisions": [
        {"id": p.id, "libelle": p.libelle, "ordre": p.ordre, "source": p.source} for p in precs]}


class PrecisionTypeIn(BaseModel):
    cycle_id: int
    niveau: str
    type_id: int
    libelle: str


@router.post("/admin/referentiels/types-activite/precisions", dependencies=[Depends(_require_admin)])
def creer_precision_type(body: PrecisionTypeIn, db: Session = Depends(get_db)):
    """Ajoute une précision à un type. CREATE encadré : type du référentiel (404), libellé non vide
    (400), REFUS DU DOUBLON par libellé insensible à la casse DANS CE type → renvoie l'existante
    (`deja_present`). Sinon crée `source='admin'`, `ordre = max(ordre)+1`."""
    t = _type_du_couple(db, body.cycle_id, body.niveau, body.type_id)
    libelle = (body.libelle or "").strip()
    if not libelle:
        raise HTTPException(400, "Indiquez un libellé pour la précision.")
    existante = (db.query(ReferentielTypePrecision)
                   .filter(ReferentielTypePrecision.type_activite_id == t.id,
                           func.lower(ReferentielTypePrecision.libelle) == libelle.lower()).first())
    if existante is not None:
        return {"id": existante.id, "libelle": existante.libelle, "deja_present": True}
    ordre_max = (db.query(func.coalesce(func.max(ReferentielTypePrecision.ordre), -1))
                   .filter(ReferentielTypePrecision.type_activite_id == t.id).scalar())
    p = ReferentielTypePrecision(type_activite_id=t.id, libelle=libelle,
                                 ordre=ordre_max + 1, source="admin")
    db.add(p)
    db.commit()
    db.refresh(p)
    logger.info("Précision ajoutée : type=%s id=%s libelle=%s", t.id, p.id, p.libelle)
    return {"id": p.id, "libelle": p.libelle, "deja_present": False}


@router.delete("/admin/referentiels/types-activite/precisions/{prec_id}", dependencies=[Depends(_require_admin)])
def supprimer_precision_type(prec_id: int, cycle_id: int, niveau: str, type_id: int,
                             db: Session = Depends(get_db)):
    """Supprime une précision d'un type. DELETE encadré : la précision doit exister ET appartenir
    au bon type (404 sinon)."""
    t = _type_du_couple(db, cycle_id, niveau, type_id)
    p = db.get(ReferentielTypePrecision, prec_id)
    if p is None or p.type_activite_id != t.id:
        raise HTTPException(404, "Précision introuvable pour ce type.")
    db.delete(p)
    db.commit()
    logger.info("Précision supprimée : type=%s id=%s libelle=%s", t.id, prec_id, p.libelle)
    return {"ok": True, "id": prec_id}


class TypeRef(BaseModel):
    cycle_id: int
    niveau: str
    type_id: int


@router.post("/admin/referentiels/types-activite/precisions/generer", dependencies=[Depends(_require_admin)])
def generer_precisions_type(body: TypeRef, db: Session = Depends(get_db)):
    """ÉCRITURE : l'IA génère les précisions d'un type et les enregistre (`source='ia'`), puis
    renvoie la liste.

    RÉSERVÉ AUX TYPES RETENUS (422 sinon). On ne dépense l'IA que sur ce que l'admin a gardé : une
    proposition qu'il n'a pas retenue n'a pas à coûter un appel — c'est la même règle que les
    matières, où rien ne se travaille avant d'être au programme. Garde-fou : un type qui a déjà des
    précisions n'est jamais réécrasé. Pannes IA absorbées."""
    t = _type_du_couple(db, body.cycle_id, body.niveau, body.type_id)
    if not t.validee:
        raise HTTPException(422, "Retenez d'abord ce type d'activité : les précisions ne se "
                                 "génèrent que pour les types au programme.")
    _generer_precisions_ia(db, t, body.niveau)
    db.commit()
    precs = (db.query(ReferentielTypePrecision)
               .filter(ReferentielTypePrecision.type_activite_id == t.id)
               .order_by(ReferentielTypePrecision.ordre, ReferentielTypePrecision.id).all())
    return {"precisions": [
        {"id": p.id, "libelle": p.libelle, "ordre": p.ordre, "source": p.source} for p in precs]}


def _prompt_types_du_referentiel(db: Session, ref: Referentiel, texte: str) -> str | None:
    """LE prompt qui lit les types d'activité de CE référentiel. Troisième exemplaire du geste de
    `_prompt_matieres_du_referentiel` et `_prompt_decoupe_du_referentiel` : s'il n'existe pas
    encore, il est ÉCRIT ICI, tout de suite, par l'IA (méta-prompt en base + le document lui-même),
    puis rangé sur le référentiel — le geste de l'admin reste UN clic.

    Le prompt SERT dès qu'il existe. `prompt_types_valide` ne commande pas son usage : il dit
    seulement si l'admin l'a relu.

    None si la rédaction échoue : la détection retombe alors sur le prompt général, sans casser le
    geste (une panne de l'IA ne doit pas empêcher de proposer des types)."""
    deja = (ref.prompt_types or "").strip()
    if deja:
        return deja
    from backend.rag.analyse_amont import generer_prompt_types
    try:
        # Le méta-prompt DU NIVEAU passe devant le réglage général (même règle que la découpe).
        prompt = generer_prompt_types(texte, db=db,
                                      meta_referentiel=ref.prompt_meta_types).strip()
    except Exception:
        logger.exception("types : rédaction du prompt du référentiel impossible (id=%s)", ref.id)
        return None
    if not prompt:
        return None
    ref.prompt_types = prompt
    ref.prompt_types_valide = False   # écrit par l'IA, pas encore relu par l'admin
    db.commit()
    logger.info("types : prompt du référentiel id=%s rédigé par l'IA (%d caractères)",
                ref.id, len(prompt))
    return prompt


class PromptTypesCoupleBody(BaseModel):
    cycle_id: int
    niveau: str
    prompt: str


# ── Le MÉTA-prompt des TYPES D'ACTIVITÉ, propre au référentiel (06/08/2026) ─────────
#
# Troisième jumeau. Deux portes : on le LIT depuis l'écran du couple (bouton « Méta-prompt » de la
# cartouche Types) et on l'ÉCRIT depuis Prompts → Référentiels. La lecture dit d'où vient le texte
# affiché — la case du niveau, ou le réglage général quand elle est vide.

class PromptMetaTypesBody(BaseModel):
    cycle_id: int
    niveau: str
    prompt: str


@router.get("/admin/referentiels/prompt-meta-types", dependencies=[Depends(_require_admin)])
def lire_prompt_meta_types(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Le méta-prompt des types qui sert VRAIMENT à ce couple, et la provenance du texte rendu.

    `source` vaut 'referentiel' ou 'aucun'. Repli général retiré le 08/08/2026."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    propre = (ref.prompt_meta_types or "").strip() if ref is not None else ""
    return {"prompt": propre, "source": "referentiel" if propre else "aucun"}


@router.post("/admin/referentiels/prompt-meta-types", dependencies=[Depends(_require_admin)])
def enregistrer_prompt_meta_types(body: PromptMetaTypesBody, db: Session = Depends(get_db)):
    """Écrit le MÉTA-prompt des types de ce niveau. AUCUNE IA : c'est de la saisie.

    Le repère exigé est {document}, et non {texte} : ce texte-ci reçoit le DOCUMENT et rend un
    prompt ; c'est le prompt rendu qui recevra ensuite le texte.

    Vider le champ est permis, mais plus rien ne prend le relais : la génération d'un prompt de
    types lèvera tant que cette case est vide (repli général retiré le 08/08/2026)."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce niveau : déposez d'abord un document.")
    prompt = (body.prompt or "").strip()
    if prompt and "{document}" not in prompt:
        raise HTTPException(422, "Le méta-prompt doit contenir le marqueur {document} : c'est là "
                                 "que le référentiel sera inséré.")
    ref.prompt_meta_types = prompt or None
    db.commit()
    return {"ok": True, "longueur": len(prompt)}


# ── Les prompts des PRÉCISIONS, propres au référentiel (07/08/2026) ─────────────────
#
# Quatrième couple, mêmes portes que les trois autres. Deux repères dans le prompt de travail, et
# non un : {texte} (le document) et {label} (le type dont on veut les précisions) — les deux sont
# exigés, sans eux le prompt ne recevrait ni l'un ni l'autre.

class PromptMetaPrecisionsBody(BaseModel):
    cycle_id: int
    niveau: str
    prompt: str


class PromptPrecisionsCoupleBody(BaseModel):
    cycle_id: int
    niveau: str
    prompt: str


@router.get("/admin/referentiels/prompt-meta-precisions", dependencies=[Depends(_require_admin)])
def lire_prompt_meta_precisions(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Le méta-prompt des précisions de ce couple. `source` vaut 'referentiel' ou 'aucun'."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    propre = (ref.prompt_meta_precisions or "").strip() if ref is not None else ""
    return {"prompt": propre, "source": "referentiel" if propre else "aucun"}


@router.post("/admin/referentiels/prompt-meta-precisions", dependencies=[Depends(_require_admin)])
def enregistrer_prompt_meta_precisions(body: PromptMetaPrecisionsBody, db: Session = Depends(get_db)):
    """Écrit le MÉTA-prompt des précisions de ce niveau. AUCUNE IA : c'est de la saisie.

    Vider le champ est permis, mais plus rien ne prend le relais : la génération d'un prompt de
    précisions lèvera tant que cette case est vide (repli général retiré le 08/08/2026)."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce niveau : déposez d'abord un document.")
    prompt = (body.prompt or "").strip()
    if prompt and "{document}" not in prompt:
        raise HTTPException(422, "Le méta-prompt doit contenir le marqueur {document} : c'est là "
                                 "que le référentiel sera inséré.")
    ref.prompt_meta_precisions = prompt or None
    db.commit()
    return {"ok": True, "longueur": len(prompt)}


@router.get("/admin/referentiels/prompt-precisions", dependencies=[Depends(_require_admin)])
def lire_prompt_precisions_couple(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Le prompt des précisions de CE couple, tel qu'il est en base (get, zéro copie)."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None:
        return {"existe": False, "prompt": "", "valide": False}
    return {"existe": True, "prompt": ref.prompt_precisions or "",
            "valide": bool(ref.prompt_precisions_valide)}


@router.post("/admin/referentiels/prompt-precisions/valider", dependencies=[Depends(_require_admin)])
def valider_prompt_precisions_couple(body: PromptPrecisionsCoupleBody, db: Session = Depends(get_db)):
    """L'admin écrit (ou corrige) le prompt des précisions de CE référentiel et le VALIDE. Écrit à
    la main, il coûte zéro. Prompt vide refusé ; les DEUX marqueurs sont exigés — sans {texte} le
    document ne serait jamais inséré, sans {label} l'IA ne saurait pas de quel type il s'agit."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple : déposez d'abord un document.")
    prompt = (body.prompt or "").strip()
    if not prompt:
        raise HTTPException(422, "Le prompt des précisions est vide.")
    manquants = [m for m in ("{texte}", "{label}") if m not in prompt]
    if manquants:
        raise HTTPException(422, f"Le prompt doit contenir {' et '.join(manquants)} : "
                                 "{texte} reçoit le document, {label} le nom du type d'activité.")
    ref.prompt_precisions = prompt
    ref.prompt_precisions_valide = True
    db.commit()
    return {"ok": True, "valide": True}


@router.get("/admin/referentiels/prompt-types", dependencies=[Depends(_require_admin)])
def lire_prompt_types_couple(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Lit le prompt des types d'activité de CE couple (EN BASE) + son statut de validation."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None:
        return {"existe": False, "prompt": "", "valide": False}
    return {"existe": True, "prompt": ref.prompt_types or "",
            "valide": bool(ref.prompt_types_valide)}


@router.post("/admin/referentiels/prompt-types/valider", dependencies=[Depends(_require_admin)])
def valider_prompt_types_couple(body: PromptTypesCoupleBody, db: Session = Depends(get_db)):
    """L'admin écrit (ou corrige) le prompt des types de CE référentiel et le VALIDE. Écrit à la
    main, il coûte zéro et évite que le premier « Détecter les types » en fasse d'abord écrire un.
    Prompt vide refusé ; sans le marqueur {texte}, refusé aussi."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple : déposez d'abord un document.")
    prompt = (body.prompt or "").strip()
    if not prompt:
        raise HTTPException(422, "Le prompt des types d'activité est vide.")
    if "{texte}" not in prompt:
        raise HTTPException(422, "Le prompt doit contenir le marqueur {texte} : c'est là que le "
                                 "document sera inséré.")
    ref.prompt_types = prompt
    ref.prompt_types_valide = True
    db.commit()
    return {"ok": True, "valide": True}


@router.post("/admin/referentiels/types-activite/detecter", dependencies=[Depends(_require_admin)])
def detecter_types_activite_couple(body: RegleStatutBody, db: Session = Depends(get_db)):
    """Bouton « Détecter les types » — UN seul clic, deux temps chez le serveur, exactement comme
    « Proposer les matières » :

    1. le prompt de CE référentiel : déjà en base, sinon écrit à l'instant par l'IA à partir du
       document lui-même — la recette appartient au couple qui la porte ;
    2. la lecture des types avec ce prompt-là, sur le texte DÉJÀ figé en base (aucune
       ré-extraction du PDF).

    Les types lus sont écrits NON RETENUS (`validee=false`) : ce sont des propositions, l'admin
    garde ce qu'il veut. Un type déjà présent (même libellé, casse ignorée) est laissé tel quel —
    une nouvelle détection ne déretient jamais ce que l'admin avait retenu, et ne crée pas de
    doublon. Rien n'est écrit hors de ce référentiel."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    texte = _texte_du_couple(db, ref)   # le texte de travail figé au dépôt (get en base)
    if not texte.strip():
        raise HTTPException(400, "Document sans texte lisible : détection impossible.")

    from backend.rag.analyse_amont import detecter_types_activite
    try:
        detectes = detecter_types_activite(
            texte, db=db, prompt_referentiel=_prompt_types_du_referentiel(db, ref, texte))
    except Exception as e:
        raise HTTPException(400, f"Détection des types par l'IA impossible : {e}{detail_admin(e)}")

    proposes, deja = [], []
    vus: set[str] = set()
    for label in detectes:
        label = label.strip()
        cle = label.lower()                # matching par LIBELLÉ, comme les matières
        if not cle or cle in vus:          # même libellé (à la casse près) : une seule fois
            continue
        vus.add(cle)
        existant = (db.query(ActiviteType)
                      .filter(ActiviteType.referentiel_id == ref.id,
                              func.lower(ActiviteType.label) == cle).first())
        if existant is not None:
            deja.append({"id": existant.id, "label": existant.label})
            continue
        t = _creer_type(db, ref, label, body.niveau, origine="ia", validee=False)
        proposes.append({"id": t.id, "label": t.label})
    db.commit()
    return {"detectes": detectes, "proposes": proposes, "deja_presents": deja}


