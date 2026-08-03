"""Étape 1 du chantier « Référentiel → matières + chunks ».

RÉCEPTION d'un référentiel officiel fourni par l'admin — par LIEN ou par DÉPÔT —,
POINT DE CONTRÔLE (aperçu pour que l'admin valide que c'est le bon document), puis
RANGEMENT + EXTRACTION du texte + ENREGISTREMENT de la provenance (table referentiels).

Périmètre étape 1 UNIQUEMENT : pas d'extraction de matières (étape 2), pas de chunks
(étape 6), pas de recherche web automatique (palier suivant, branché « devant » plus tard).
On reçoit un PDF que l'admin fournit, on le lui montre, on le range et on trace sa provenance.
"""
import hashlib
import json
import logging
import shutil
import threading
import time
import uuid
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.database import get_db, SessionLocal
# Règle de nommage des dossiers (« Bébés (0-1 an) » → « BEBES_0_1_AN ») : UNE seule source,
# elle était recopiée mot pour mot ici, dans pgvector_store et dans profil.py.
from backend.core.nommage import dossier_cle as _dossier_cle
from backend.core.models_db import Cycle, Niveau, Referentiel, ReferentielChunk, ReferentielDepot, Matiere, User, ActiviteType, ReferentielActiviteType, ReferentielTypePrecision
# SETTING_DEFAULTS n'est plus importé : le gabarit des prompts de type était son dernier
# usage ici, et il se lit désormais EN BASE par `get_prompt` (registre, clé `gabarit_type`).
from backend.core.llm_prompts import PROMPTS
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
    sont ajoutées. Anti-doublon par nom, insensible à la casse, DANS ce référentiel."""
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
    """Nettoyage de la zone d'attente — fichier ET ligne partent ENSEMBLE (constat du 24/07 :
    33 aperçus abandonnés, 202 Mo depuis le 13/07 — rien ne les effaçait jamais).

    Le dépôt est désormais inscrit en base (`referentiel_depots`) : le balayage ne se fait plus
    à l'aveugle sur le dossier, il part des LIGNES et traite les trois cas possibles —
      · ligne + fichier trop vieux (> TTL)  → les deux partent, l'abandon est consommé ;
      · ligne SANS fichier                  → la ligne part tout de suite (rien à garder :
        le fichier a été validé, déplacé ou effacé à la main) ;
      · fichier SANS ligne                  → héritage d'avant la table (ou dépôt interrompu
        avant son commit) : effacé une fois périmé, jamais tant qu'il est récent — un dépôt
        en cours ne doit pas se faire faucher son PDF par le dépôt du voisin.

    L'âge se lit sur le fichier (`st_mtime`), pas sur `created_at` : c'est la même horloge que
    l'objet qu'on supprime, alors que `created_at` vient de celle du serveur de base. TTL
    réglable en base (`staging_ttl_heures`, défaut 24), lu comme `depot_max_pages`.
    Best-effort : un raté de suppression ne bloque jamais le dépôt en cours."""
    try:
        ttl_h = float(get_settings_dict(db).get("staging_ttl_heures", 24))
    except (TypeError, ValueError):
        ttl_h = 24.0
    seuil = time.time() - ttl_h * 3600

    connus: set[str] = set()          # les fichiers qu'une ligne référence — les autres sont orphelins
    a_effacer: list[ReferentielDepot] = []
    for depot in db.query(ReferentielDepot).all():
        f = _ROOT / depot.chemin
        connus.add(f.name)
        if not f.exists():
            a_effacer.append(depot)
            logger.info("Zone d'attente : ligne sans fichier supprimée (%s)", depot.token)
            continue
        try:
            if f.stat().st_mtime < seuil:
                f.unlink()
                a_effacer.append(depot)
                logger.info("Zone d'attente : dépôt abandonné supprimé (%s — %s)",
                            depot.token, depot.fichier_origine)
        except OSError:
            logger.warning("Zone d'attente : suppression impossible de %s", f.name)
    for depot in a_effacer:
        db.delete(depot)
    if a_effacer:
        db.commit()

    for f in STAGING_DIR.glob("*.pdf"):
        if f.name in connus:
            continue
        try:
            if f.stat().st_mtime < seuil:
                f.unlink()
                logger.info("Zone d'attente : fichier sans ligne supprimé (%s)", f.name)
        except OSError:
            logger.warning("Zone d'attente : suppression impossible de %s", f.name)


def _oublier_depot(db: Session, token: str) -> None:
    """Retire la ligne de zone d'attente d'un jeton — le fichier, lui, est déjà parti (déplacé
    par la validation, ou disparu). Sans effet si aucune ligne ne porte ce jeton (dépôt d'avant
    la table, jeton inventé) : effacer ce qui n'existe pas ne doit jamais faire échouer un geste
    qui, par ailleurs, a réussi."""
    n = db.query(ReferentielDepot).filter(ReferentielDepot.token == token).delete()
    if n:
        db.commit()
        logger.info("Zone d'attente : dépôt %s sorti (fichier validé ou disparu)", token)


def _deja_connu(db: Session, empreinte: str) -> dict | None:
    """Ce document est-il DÉJÀ connu ? Recherche par empreinte du contenu, jamais par le nom.

    Deux endroits où il peut être déjà passé, dans cet ordre de proximité :
      · la zone d'attente — un dépôt du même document attend déjà d'être validé ;
      · un référentiel validé — ce PDF est déjà LE référentiel d'un couple.
    Rend de quoi le DIRE à l'admin ({ou, …}) ou None. Ne bloque rien, n'écrit rien : la décision
    reste à l'admin, qui peut parfaitement vouloir redéposer le même document."""
    depot = (db.query(ReferentielDepot)
               .filter(ReferentielDepot.empreinte == empreinte)
               .order_by(ReferentielDepot.created_at.desc()).first())
    if depot is not None:
        return {"ou": "attente", "fichier": depot.fichier_origine,
                "depose_le": depot.created_at.isoformat(timespec="minutes")}
    ligne = (db.query(Referentiel, Niveau, Cycle)
               .join(Niveau, Niveau.id == Referentiel.niveau_id)
               .join(Cycle, Cycle.id == Niveau.cycle_id)
               .filter(Referentiel.empreinte == empreinte).first())
    if ligne is not None:
        ref, niveau, cycle = ligne
        return {"ou": "valide", "fichier": ref.fichier,
                "cycle": cycle.nom, "niveau": niveau.nom}
    return None


def _stage(content: bytes, filename: str, db: Session, source: str, url: str | None = None) -> dict:
    """Valide que c'est un PDF, le range en zone d'attente, l'INSCRIT EN BASE, renvoie l'aperçu.

    Porte unique des deux dépôts (fichier et lien) : c'est donc ici, et ici seulement, que la
    ligne `referentiel_depots` naît — le jeton ne vivait jusqu'à présent que dans l'état de
    l'écran, et un rechargement de page laissait le PDF orphelin sur le disque. `source` dit par
    quelle porte il est entré ('depot' | 'lien'), `url` n'accompagne que la seconde.

    La ligne est écrite EN DERNIER, quand le document a passé tous les contrôles : un PDF refusé
    (trop gros, illisible, trop long) n'en laisse aucune. Et si l'écriture en base échoue, le
    fichier est retiré du disque — les deux vivent et meurent ensemble, jamais l'un sans l'autre."""
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
    taille_ko = round(len(content) / 1024)
    # Reconnaissance du document : empreinte du CONTENU, cherchée AVANT d'inscrire la nouvelle
    # ligne (sinon elle se reconnaîtrait elle-même). Le résultat est rendu à l'écran pour
    # information — le dépôt aboutit normalement dans tous les cas.
    empreinte = hashlib.sha256(content).hexdigest()
    deja = _deja_connu(db, empreinte)
    if deja:
        logger.info("Dépôt : document déjà connu (%s) — empreinte %s", deja["ou"], empreinte[:12])
    # Le document existe maintenant EN BASE : nom d'origine, mesures, emplacement, aperçu. Si ce
    # commit échoue, le PDF ne doit pas rester seul sur le disque — on le retire avant de rendre
    # la main. (`chemin` en séparateurs POSIX : c'est une donnée, pas un chemin Windows.)
    db.add(ReferentielDepot(
        token=token,
        empreinte=empreinte,
        fichier_origine=filename,
        chemin=staged.relative_to(_ROOT).as_posix(),
        taille_ko=taille_ko,
        pages=n_pages,
        source=source,
        url_source=url,
        apercu=apercu,
    ))
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        staged.unlink(missing_ok=True)
        logger.exception("Dépôt : inscription en base impossible (%s)", filename)
        raise HTTPException(500, f"Enregistrement du dépôt impossible : {e}")
    return {
        "token": token,
        "filename": filename,
        "taille_ko": taille_ko,
        "pages": n_pages,
        "apercu": apercu,
        # `deja` : null (document inconnu) ou ce qu'on a reconnu. Clé AJOUTÉE — les écrans qui
        # l'ignorent continuent de fonctionner à l'identique.
        "deja": deja,
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
    return _stage(r.content, filename, db, source="lien", url=url)


@router.post("/admin/referentiels/preparer-depot", dependencies=[Depends(_require_admin)])
async def preparer_depot(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    return _stage(content, file.filename or "referentiel.pdf", db, source="depot")


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

    C'est la lecture UNIQUE de la page « Programmes & contenu ». Elle lisait avant deux endpoints
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

    # Types d'activité liés par référentiel, puis précisions par lien (couple × type).
    liens_par_ref: dict[int, list] = {}
    for lien, t in (db.query(ReferentielActiviteType, ActiviteType)
                      .join(ActiviteType, ActiviteType.id == ReferentielActiviteType.activite_type_id)
                      .order_by(ActiviteType.ordre, ActiviteType.id).all()):
        liens_par_ref.setdefault(lien.referentiel_id, []).append((lien, t))
    precs_par_lien: dict[int, list[str]] = {}
    for p in (db.query(ReferentielTypePrecision)
                .order_by(ReferentielTypePrecision.ordre, ReferentielTypePrecision.id).all()):
        precs_par_lien.setdefault(p.referentiel_activite_type_id, []).append(p.libelle)

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
                    {"id": t.id, "label": t.label, "source": lien.source, "origine": t.origine,
                     "precisions": precs_par_lien.get(lien.id, [])}
                    for lien, t in liens_par_ref.get(ref.id, [])],
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


class VerifierDepotBody(BaseModel):
    token: str
    cycle_id: int
    niveau_id: int


@router.post("/admin/referentiels/verifier-depot", dependencies=[Depends(_require_admin)])
def verifier_depot(body: VerifierDepotBody, db: Session = Depends(get_db)):
    """Vérification au dépôt (LECTURE SEULE), avant de proposer la validation : la vérif n°1
    (couple) — l'IA lit le couple visé par le PDF et le compare au couple cycle → niveau déclaré.
    L'écran n'affiche le document à valider que si elle passe (ou sur forçage motivé)."""
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

    return {"couple": couple}


class DetecterCoupleBody(BaseModel):
    token: str


@router.post("/admin/referentiels/detecter-couple", dependencies=[Depends(_require_admin)])
def detecter_couple_depot(body: DetecterCoupleBody, db: Session = Depends(get_db)):
    """Dépôt « PDF d'abord » (LECTURE SEULE — aucune écriture) : l'IA lit le début du document en
    zone d'attente et propose le cycle + le niveau (nom exact du diplôme). Le SERVEUR fait ensuite
    la CORRESPONDANCE en dur avec les tables cycles/niveaux (insensible à la casse) — l'IA lit,
    la base tranche. `cycle`/`niveau` valent null si rien ne correspond : l'écran propose alors
    « Ajouter ce niveau » (porte unique POST /admin/niveaux, sur clic de l'admin) ou renvoie vers
    Programmes pour un cycle inconnu. Ne crée JAMAIS rien ici."""
    texte = _texte_staged(body.token)
    if not texte:
        raise HTTPException(400, "PDF sans texte lisible : détection impossible.")
    from backend.rag.analyse_amont import detecter_couple
    try:
        lu = detecter_couple(texte[:4000], db=db)
    except Exception:
        logger.exception("detecter_couple : échec de la lecture du couple par l'IA")
        raise HTTPException(400, "La détection du cycle par l'IA a échoué. Réessayez.")
    cycle = None
    if lu["cycle_lu"]:
        cycle = db.query(Cycle).filter(func.lower(Cycle.nom) == lu["cycle_lu"].lower()).first()
    niveau = None
    if cycle is not None and lu["niveau_lu"]:
        niveau = (db.query(Niveau)
                    .filter(Niveau.cycle_id == cycle.id,
                            func.lower(Niveau.nom) == lu["niveau_lu"].lower()).first())
    return {
        "cycle": {"id": cycle.id, "nom": cycle.nom} if cycle else None,
        "niveau": {"id": niveau.id, "nom": niveau.nom} if niveau else None,
        "cycle_lu": lu["cycle_lu"], "niveau_lu": lu["niveau_lu"],
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


@router.post("/admin/referentiels/valider", dependencies=[Depends(_require_admin)])
def valider(body: ValiderBody, db: Session = Depends(get_db)):
    staged = STAGING_DIR / f"{body.token}.pdf"
    if not staged.exists():
        # Plus de fichier → plus de ligne : le dépôt n'existe plus, sa trace en zone d'attente
        # non plus (elle serait exactement l'orphelin que la table sert à empêcher).
        _oublier_depot(db, body.token)
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
            return {
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
            }
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
    # Le document vient de QUITTER la zone d'attente : sa ligne de dépôt n'a plus d'objet. Effacée
    # ici, dans la foulée du déplacement — et pas en fin de fonction : ce qui suit (épuration,
    # matières IA) peut échouer, la ligne resterait alors à désigner un fichier absent.
    _oublier_depot(db, body.token)

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
    # Empreinte du PDF retenu : même calcul qu'au dépôt, sur le fichier qui vient d'être rangé.
    # C'est elle qui fera reconnaître ce document s'il est redéposé un jour.
    empreinte = hashlib.sha256(pdf_final.read_bytes()).hexdigest()

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
        existing.texte_epure = texte_epure   # le NOUVEAU PDF impose SON texte de travail
        existing.empreinte = empreinte       # …et SON empreinte (l'ancienne ne vaut plus)
        db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == existing.id).delete()
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
            texte_epure=texte_epure,
            empreinte=empreinte,
        )
        db.add(ref)
        db.commit()

    # Détection IA des matières PROPOSÉES à partir du NOUVEAU PDF. Elle ne retient jamais une
    # matière d'office : elle les écrit sur le référentiel avec `validee=false` — l'admin coche
    # ce qu'il garde. Best-effort : une panne IA ne casse pas la validation du référentiel (une
    # proposition n'est qu'une aide au remplissage, jamais une donnée figée).
    try:
        from backend.rag.analyse_amont import detecter_matieres
        if texte_epure.strip():                     # le texte de travail qui vient d'être figé (get)
            _ecrire_matieres_proposees(db, ref.id, detecter_matieres(texte_epure, db=db))
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
             "forcage_motif": ref.forcage_motif, "verif_couple": ref.verif_couple}
            if ref else None
        ),
        "matieres": matieres,
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


@router.get("/admin/referentiels/depot-pdf", dependencies=[Depends(_require_admin)])
def voir_pdf_depot(token: str, db: Session = Depends(get_db)):
    """Sert le PDF qui est EN ZONE D'ATTENTE, désigné par son jeton — l'admin doit pouvoir
    regarder le document qu'il vient de déposer, avant toute validation.

    Même geste que `voir_pdf` juste au-dessus (lecture seule, inline, visionneuse du navigateur),
    mais l'adresse du fichier ne vient pas du couple — il n'est pas encore connu : elle vient de
    la ligne de dépôt (`referentiel_depots.chemin`). Ligne sans fichier : l'invariant de la zone
    d'attente veut qu'aucune des deux ne survive seule, la ligne part et on répond 404."""
    depot = db.query(ReferentielDepot).filter(ReferentielDepot.token == token).first()
    if depot is None:
        raise HTTPException(404, "Aucun document en attente pour ce jeton.")
    pdf = _ROOT / depot.chemin
    if not pdf.exists():
        _oublier_depot(db, token)
        raise HTTPException(404, "Le document en attente n'existe plus.")
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
    texte = _texte_du_couple(db, ref)   # le texte de travail figé au dépôt (get en base)
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
    texte = _texte_du_couple(db, ref)   # le texte de travail figé au dépôt (get en base)
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
    texte = _texte_du_couple(db, ref)   # le texte de travail figé au dépôt (get en base)
    from backend.rag.pgvector_store import _decouper_ia
    try:
        chunks = _decouper_ia(texte, ref.prompt_decoupe or "")
    except Exception as e:
        raise HTTPException(400, f"Découpe par l'IA impossible : {e}")
    # On garde ce résultat (avec le prompt qui l'a produit) : la validation écrira EXACTEMENT
    # cette découpe — celle que l'admin voit — au lieu de refaire l'appel IA.
    with _DECOUPES_LOCK:
        _DECOUPES_APERCU[ref.collection] = {"prompt": ref.prompt_decoupe or "", "chunks": chunks}
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


# ── Découpe (ingestion) en TÂCHE DE FOND : l'écriture des chunks + embeddings prend ~2 min, bien
#    plus long qu'une requête HTTP ne peut tenir. Le bouton LANCE l'ingestion et rend la main tout de
#    suite ; l'écran SURVEILLE ensuite l'aboutissement via /decoupe/statut. `_INGESTIONS` = état
#    d'orchestration RUNTIME (en cours / échec), PAS une donnée métier : l'unique vérité d'aboutissement
#    reste `referentiels.decoupe_valide` + les chunks EN BASE. Perdu au redémarrage serveur (l'admin
#    relance le bouton) — acceptable.
_INGESTIONS: dict[str, dict] = {}
_INGESTIONS_LOCK = threading.Lock()

# Découpe de l'APERÇU en attente de validation : {collection: {"prompt", "chunks"}}. État
# d'orchestration RUNTIME (comme _INGESTIONS, perdu au redémarrage — l'ingestion redécoupe alors
# elle-même) : la vérité métier reste les chunks EN BASE, posés à la validation. Sert à écrire
# EXACTEMENT ce que l'admin a vu et accepté, sans refaire l'appel IA — réutilisé seulement si le
# prompt n'a pas bougé entre l'aperçu et la validation (garde dans ingest_pgvector).
_DECOUPES_APERCU: dict[str, dict] = {}
_DECOUPES_LOCK = threading.Lock()


def _ingest_en_fond(collection: str) -> None:
    """Tâche de fond : découpe IA + embeddings + écriture des chunks, puis pose `decoupe_valide=true`
    EN BASE (le VRAI PUT). Met à jour l'état d'orchestration `_INGESTIONS` (running/done/error +
    avancement réel pour la jauge de l'écran). Session dédiée (le thread ne partage pas celle de
    la requête, déjà fermée)."""
    def _progression(etape: str, fait: int, total: int) -> None:
        # Avancement RÉEL remonté par l'ingestion (état runtime, pas une donnée métier).
        with _INGESTIONS_LOCK:
            job = _INGESTIONS.get(collection)
            if job is not None:
                job["progress"] = {"etape": etape, "fait": fait, "total": total}
    try:
        from backend.rag.pgvector_store import ingest_pgvector
        with _DECOUPES_LOCK:
            decoupe_prete = _DECOUPES_APERCU.get(collection)
        rapport = ingest_pgvector(collection, on_progress=_progression, decoupe_prete=decoupe_prete)
        with _DECOUPES_LOCK:
            _DECOUPES_APERCU.pop(collection, None)   # consommée : la vérité est en base désormais
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
            _INGESTIONS[collection] = {"status": "running", "chunks": None, "message": None,
                                       "progress": {"etape": "decoupe", "fait": 0, "total": 0}}
    if not deja:   # jamais deux ingestions en parallèle pour le même couple (idempotent)
        threading.Thread(target=_ingest_en_fond, args=(collection,), daemon=True).start()
    return {"ok": True, "status": "running"}


@router.get("/admin/referentiels/decoupe/statut", dependencies=[Depends(_require_admin)])
def statut_decoupe(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """État de l'ingestion d'un couple (surveillance après « Valider le découpage »).

    LE TRAVAIL EN COURS L'EMPORTE SUR LE DRAPEAU, et l'ordre inverse a coûté onze minutes de
    mensonge (mesurées le 02/08/2026, sur la réingestion du BTS CIEL). Le docstring d'avant
    annonçait « la VÉRITÉ d'aboutissement = `decoupe_valide` + nombre de chunks », et c'est cette
    phrase qui a produit l'ordre fautif : elle est vraie pour une PREMIÈRE ingestion, fausse pour
    une REPRISE. `decoupe_valide` reste posé depuis la fois d'avant ; testé en premier, il gagnait
    contre le travail réellement en cours. L'écran affichait donc `done` avec `chunks: 46` — les
    anciens, pas encore purgés — pendant que la vectorisation était à 0/44. Un admin qui réingère
    croyait que c'était fini avant que ça n'ait commencé.

    LA RÈGLE : `_INGESTIONS` porte l'ÉTAT COURANT, `decoupe_valide` porte l'HISTOIRE. Quand il y
    a un job, il est forcément plus récent que le drapeau — on le lit d'abord, quel que soit son
    état. Sans job, le drapeau reprend la main : c'est lui qui distingue « déjà ingéré » de
    « jamais ingéré ». Le garde de `valider_decoupe` (plus haut) lisait déjà `_INGESTIONS` de
    cette façon ; il était juste, c'est cette route qui le contredisait.

    CE QUE ÇA ÉLARGIT, au-delà des onze minutes : une réingestion qui ÉCHOUE rendait elle aussi
    `done` (même cause, drapeau d'abord). Elle rend désormais `error`, avec son message. C'est
    le même défaut, pas un second.

    LA LIMITE, VUE ET LAISSÉE (décision du 02/08). `_INGESTIONS` est de l'état RUNTIME : il
    disparaît au redémarrage du processus — et le conteneur de développement recharge à chaque
    modification de fichier (`--reload`). Une ingestion en cours au moment d'un rechargement
    redevient donc invisible aux DEUX sources : le job est perdu, le drapeau n'est pas encore
    posé, et la route rend `idle` alors que rien ne tourne plus. Corriger l'ordre règle le cas
    mesuré ; ça ne rend pas le statut fiable à travers un redémarrage. Le rendre fiable
    demanderait un drapeau EN BASE (« ingestion en cours depuis … »), c'est-à-dire un autre
    sujet : le cas est rare, et sans perte de données (la sauvegarde avant purge tient, et
    `outils_bdd/restaurer_chunks.py` sait rejouer). On l'a vu, on ne le tait pas, on le laisse."""
    ref = _ref_du_couple(db, cycle_id, niveau)
    if ref is None:
        return {"status": "absent", "decoupe_valide": False, "chunks": 0, "message": None}
    n = db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == ref.id).count()
    with _INGESTIONS_LOCK:
        job = _INGESTIONS.get(ref.collection)
    if job is not None:
        status = job["status"]          # running / done / error — plus récent que le drapeau
    elif ref.decoupe_valide:
        status = "done"                 # pas de job : l'histoire répond
    else:
        status = "idle"
    return {"status": status, "decoupe_valide": bool(ref.decoupe_valide), "chunks": n,
            "message": (job or {}).get("message"), "progress": (job or {}).get("progress")}


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
    """Retire une matière du programme = `actif=False` sur SA ligne (historique conservé, JAMAIS
    de suppression dure). Garde : la matière doit bien appartenir au référentiel de ce couple —
    on ne retire pas la matière d'un autre diplôme depuis cet écran. Signale, sans rien casser,
    combien de profs l'ont encore à leur profil.

    Le comptage des « référentiels qui utilisent cette matière » a disparu avec la colonne
    `referentiels.matiere_id` : le référentiel ne pointe plus vers une matière, il la POSSÈDE —
    il y en a donc exactement un, celui du couple affiché, et le dire n'apprend rien."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    mat = db.get(Matiere, body.matiere_id)
    if not mat or mat.referentiel_id != ref.id:
        raise HTTPException(404, "Cette matière n'appartient pas au référentiel de ce couple.")
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

def _profs_lies(db: Session, referentiel_id: int) -> list[User]:
    """Les professeurs rattachés à une matière de ce référentiel — NOMMÉMENT, pas un nombre.
    L'admin doit savoir QUI il met en attente avant de le faire. Les deux rattachements comptent :
    la matière du profil et celle du couple de travail."""
    return (db.query(User)
              .join(Matiere, (Matiere.id == User.subject_id) | (Matiere.id == User.travail_matiere_id))
              .filter(Matiere.referentiel_id == referentiel_id)
              .order_by(User.nom, User.prenom, User.email).distinct().all())


def _profs_du_referentiel(db: Session, referentiel_id: int) -> int:
    """Combien de professeurs travaillent sur une matière de ce référentiel — LA règle qui décide
    du refus de suppression, à UN SEUL endroit.

    Les deux rattachements comptent : la matière du profil (`subject_id`) et celle du couple de
    TRAVAIL (`travail_matiere_id`) — n'en compter qu'un sous-estimerait, et un prof perdrait sa
    matière sans figurer dans le nombre annoncé.

    Écrite une fois parce qu'elle est lue deux fois : le bilan l'ANNONCE avant le clic, la
    suppression l'APPLIQUE. Recopiée, elle dériverait — le bilan dirait « 0 professeur » et la
    suppression refuserait quand même."""
    return (db.query(User)
              .join(Matiere, (Matiere.id == User.subject_id) | (Matiere.id == User.travail_matiere_id))
              .filter(Matiere.referentiel_id == referentiel_id).count())


@router.get("/admin/referentiels/supprimer-bilan", dependencies=[Depends(_require_admin)])
def bilan_suppression(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """CE QUI PARTIRA si on supprime le référentiel de ce couple — compté EN BASE, jamais estimé.

    L'admin doit LIRE ce qu'il perd avant de décider, pas le deviner : matières, unités de
    découpe, types d'activité et leurs précisions, et le PDF sur disque. `profs` dit combien de
    professeurs travaillent sur une matière de ce référentiel : au-dessus de zéro, la suppression
    sera refusée (409) — autant l'annoncer avant plutôt que de le découvrir au clic.

    Lecture seule, aucune écriture. `existe` faux = rien à supprimer, tous les comptes à zéro."""
    ref = _ref_du_couple(db, cycle_id, niveau)             # 404 cycle / 422 niveau
    if ref is None:
        return {"existe": False, "matieres": 0, "unites": 0, "types": 0, "precisions": 0,
                "pdf": False, "profs": 0, "profs_liste": [], "fichier": None}
    liens = db.query(ReferentielActiviteType).filter(ReferentielActiviteType.referentiel_id == ref.id)
    ids_liens = [l.id for l in liens.all()]
    # Les profs NOMMÉMENT : c'est eux que l'admin s'apprête à mettre en attente. La matière
    # affichée est celle qui les rattache À CE référentiel (profil, sinon couple de travail).
    noms_matieres = {m.id: m.nom for m in db.query(Matiere).filter(Matiere.referentiel_id == ref.id).all()}
    profs_liste = [{
        "id": u.id, "prenom": u.prenom, "nom": u.nom, "email": u.email,
        "matiere": noms_matieres.get(u.subject_id) or noms_matieres.get(u.travail_matiere_id),
    } for u in _profs_lies(db, ref.id)]
    return {
        "existe": True,
        "fichier": ref.fichier,
        "matieres": db.query(Matiere).filter(Matiere.referentiel_id == ref.id).count(),
        "unites": db.query(ReferentielChunk).filter(ReferentielChunk.referentiel_id == ref.id).count(),
        "types": len(ids_liens),
        "precisions": (db.query(ReferentielTypePrecision)
                         .filter(ReferentielTypePrecision.referentiel_activite_type_id.in_(ids_liens))
                         .count() if ids_liens else 0),
        "pdf": _pdf_du_couple(db, cycle_id, niveau).exists(),
        "profs": _profs_du_referentiel(db, ref.id),
        "profs_liste": profs_liste,
    }


class SupprimerRefBody(BaseModel):
    cycle_id: int
    niveau: str
    # Le geste ASSUMÉ de l'admin : il a vu les profs nommément et confirmé deux fois. C'est le
    # SEUL chemin qui contourne le refus 409 — une suppression appelée autrement reste refusée.
    bloquer_profs: bool = False


def _avis_maj(db: Session, user: User, slug: str, suite: str = "") -> None:
    """Envoie au prof l'avis de début ou de fin de mise à jour. Le texte vient de la BASE
    (`email_templates`, semés en migration) : l'admin le corrige dans Admin → Email sans nous,
    et aucun texte de repli n'est inventé ici. Ne lève jamais — un serveur de mail muet ne doit
    pas faire échouer une suppression déjà commitée ; l'échec est tracé, et le prof lira de
    toute façon le même message à l'écran."""
    from backend.securite import comptes
    from backend.systeme.admin import record_email_envoi
    from backend.core.models_db import EmailTemplate
    modele = db.query(EmailTemplate).filter(EmailTemplate.slug == slug).first()
    if modele is None:
        logger.error("Avis de mise à jour : modèle '%s' absent de la base.", slug)
        return
    statut, erreur = "envoye", None
    try:
        comptes.send_custom_email(user.email, user.prenom, modele.objet,
                                  modele.corps.replace("{suite}", suite))
    except Exception as e:
        statut, erreur = "echec", f"{type(e).__name__}: {e}"
        logger.error("Avis de mise à jour non envoyé à %s : %s", user.email, erreur)
    record_email_envoi(db, modele_slug=modele.slug, modele_nom=modele.nom,
                       destinataire=user.email, objet=modele.objet, statut=statut, erreur=erreur)


def _bloquer_et_detacher(db: Session, ref: Referentiel, niveau_id: int) -> list[User]:
    """Met les profs de ce référentiel en attente et DÉTACHE leurs matières — c'est ce
    détachement, et lui seul, qui rend la suppression possible : `fk_users_subject_id` est en
    NO ACTION, une matière encore pointée fait ÉCHOUER l'écriture (pas un refus poli).

    La ligne mémorise les NOMS avant de vider les clés : les identifiants meurent avec le
    référentiel, les noms se re-résolvent dans le suivant.

    LES DEUX COLONNES DU COUPLE DE TRAVAIL SONT VIDÉES ENSEMBLE. `couple_de_travail` exige les
    deux : n'en vider qu'une la ferait retomber SILENCIEUSEMENT sur le couple du profil — un
    autre niveau, non bloqué, sur lequel le prof n'a jamais demandé à travailler.

    N'écrit rien d'autre : la suppression et le commit sont à l'appelant, dans la même
    transaction. Renvoie les profs concernés, pour les prévenir APRÈS le commit."""
    from backend.core.models_db import ProfBloqueMaj
    profs = _profs_lies(db, ref.id)
    noms = {m.id: m.nom for m in db.query(Matiere).filter(Matiere.referentiel_id == ref.id).all()}
    for u in profs:
        ligne = (db.query(ProfBloqueMaj)
                   .filter(ProfBloqueMaj.user_id == u.id, ProfBloqueMaj.niveau_id == niveau_id)
                   .first())
        if ligne is None:
            ligne = ProfBloqueMaj(user_id=u.id, niveau_id=niveau_id)
            db.add(ligne)
        ligne.etat, ligne.resultat, ligne.debloque_le = "bloque", None, None
        if u.subject_id in noms:                 # sa matière de PROFIL part avec le référentiel
            ligne.matiere_nom = noms[u.subject_id]
            u.subject_id = None
        if u.travail_matiere_id in noms:         # son couple de TRAVAIL visait ce référentiel
            ligne.travail_matiere_nom = noms[u.travail_matiere_id]
            ligne.travail_niveau_id = u.travail_niveau_id
            u.travail_matiere_id = None
            u.travail_niveau_id = None           # LES DEUX, jamais une seule
    return profs


@router.post("/admin/referentiels/supprimer", dependencies=[Depends(_require_admin)])
def supprimer_referentiel(body: SupprimerRefBody, db: Session = Depends(get_db)):
    """Supprime le référentiel d'un couple — refusé (409) tant qu'un prof est rattaché à l'une de
    ses matières. Efface la ligne `referentiels` + le PDF sur disque. Ses matières, ses unités,
    ses types d'activité et leurs précisions partent avec lui (CASCADE) : rien de tout cela
    n'existe sans le document qui le nomme.

    Le refus « déjà ingéré : n unité(s) » A ÉTÉ RETIRÉ. Il protégeait la mauvaise chose : les
    unités ne sont pas du travail humain, elles se RECALCULENT à partir du PDF. Ce qu'il
    verrouillait, en revanche, c'était le catalogue — un référentiel mené au bout de la procédure
    ne pouvait plus jamais être retiré, alors que c'est exactement ce qu'il faut faire quand
    l'Éducation nationale publie une nouvelle version : tout supprimer et refaire la procédure.
    Le seul refus qui reste est celui qui protège du VRAI monde : des profs au travail."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    # DELETE encadré : ses matières tombent avec lui, or un prof peut en avoir une à son profil ou à
    # son couple de travail. On refuse AVANT d'écrire, avec un message qui dit quoi faire. MÊME
    # comptage que celui annoncé par le bilan — une seule source, sinon les deux chiffres dérivent.
    profs = _profs_du_referentiel(db, ref.id)
    bloques: list[User] = []
    if profs > 0 and not body.bloquer_profs:
        raise HTTPException(409, f"{profs} professeur(s) travaillent sur une matière de ce référentiel — "
                                 "suppression impossible. Changez d'abord leur matière.")
    if profs > 0:
        # Geste assumé : mise en attente + détachement, DANS la même transaction que la
        # suppression. Ni l'un ni l'autre ne peut exister seul — sinon on aurait des profs
        # bloqués devant un référentiel toujours là.
        bloques = _bloquer_et_detacher(db, ref, ref.niveau_id)
    db.delete(ref)
    db.commit()

    # APRÈS le commit, et seulement après : ce qui ne s'annule pas. Le PDF effacé ne revient pas,
    # un e-mail parti ne se rappelle pas — les mettre dans la transaction, c'est risquer des
    # profs prévenus d'une mise à jour qui n'a pas eu lieu. (Le PDF était effacé AVANT le commit
    # jusqu'ici : un commit en échec laissait le document perdu et la fiche en place.)
    _pdf_du_couple(db, body.cycle_id, body.niveau).unlink(missing_ok=True)
    for u in bloques:
        _avis_maj(db, u, "referentiel_maj_debut")
    return {"ok": True, "profs_bloques": len(bloques)}


class DebloquerBody(BaseModel):
    cycle_id: int
    niveau: str


@router.get("/admin/referentiels/blocages", dependencies=[Depends(_require_admin)])
def blocages_du_couple(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Qui est en attente sur ce niveau, nommément, et où il en est. Sert au bouton de déblocage
    (visible tant qu'il reste des lignes) et à la liste que l'admin relit après coup — la boîte
    affichée au moment du déblocage ne doit pas être la seule trace."""
    from backend.core.models_db import ProfBloqueMaj
    niv = (db.query(Niveau).filter(Niveau.nom == (niveau or "").strip(),
                                   Niveau.cycle_id == cycle_id).first())
    if not niv:
        return {"niveau_id": None, "bloques": 0, "a_informer": 0, "profs": []}
    lignes = (db.query(ProfBloqueMaj, User).join(User, User.id == ProfBloqueMaj.user_id)
                .filter(ProfBloqueMaj.niveau_id == niv.id)
                .order_by(User.nom, User.prenom, User.email).all())
    return {
        "niveau_id": niv.id,
        "bloques": sum(1 for l, _ in lignes if l.etat == "bloque"),
        "a_informer": sum(1 for l, _ in lignes if l.etat == "a_informer"),
        "profs": [{"id": u.id, "prenom": u.prenom, "nom": u.nom, "email": u.email,
                   "matiere": l.matiere_nom, "etat": l.etat, "resultat": l.resultat}
                  for l, u in lignes],
    }


@router.post("/admin/referentiels/debloquer", dependencies=[Depends(_require_admin)])
def debloquer_profs(body: DebloquerBody, db: Session = Depends(get_db)):
    """Geste EXPLICITE de l'admin : la nouvelle procédure est en place, les profs reprennent.
    Jamais déclenché tout seul par la fin de la découpe — l'admin seul sait si c'est prêt.

    Rebranche chaque prof PAR LE NOM de sa matière, dans le NOUVEAU référentiel du niveau
    (`matiere_id_du_nom`, la règle maison). Deux issues, toutes deux assumées : retrouvée, il
    reprend là où il était ; absente du nouveau document, on n'invente rien — il est libéré, le
    message NOMME sa matière disparue et l'envoie à son profil, et l'admin lit ici la liste
    nominative de ceux qui n'ont pas pu être rebranchés.

    La ligne n'est PAS effacée : elle passe à `a_informer` et attend que le prof ait lu. Les
    e-mails partent après le commit — ils ne s'annulent pas."""
    from backend.core.models_db import ProfBloqueMaj
    from backend.core.resolution_couple import matiere_id_du_nom
    from backend.prof.profil import message_de_fin
    niv = (db.query(Niveau).filter(Niveau.nom == (body.niveau or "").strip(),
                                   Niveau.cycle_id == body.cycle_id).first())
    if not niv:
        raise HTTPException(404, "Niveau inconnu pour ce cycle.")
    lignes = (db.query(ProfBloqueMaj).filter(ProfBloqueMaj.niveau_id == niv.id,
                                             ProfBloqueMaj.etat == "bloque").all())
    rebranches, perdus, avis = [], [], []
    for ligne in lignes:
        u = db.get(User, ligne.user_id)
        matiere_id = matiere_id_du_nom(db, ligne.matiere_nom, niv.id)
        if matiere_id and u is not None:
            u.subject_id = matiere_id
            ligne.resultat = "rebranche"
            rebranches.append(u)
        else:
            ligne.resultat = "matiere_disparue"
            if u is not None:
                perdus.append(u)
        # Le couple de TRAVAIL se rebranche pareil, par le nom, dans SON niveau — et les deux
        # colonnes repartent ensemble ou pas du tout.
        if ligne.travail_matiere_nom and ligne.travail_niveau_id and u is not None:
            tid = matiere_id_du_nom(db, ligne.travail_matiere_nom, ligne.travail_niveau_id)
            if tid:
                u.travail_matiere_id, u.travail_niveau_id = tid, ligne.travail_niveau_id
        ligne.etat, ligne.debloque_le = "a_informer", func.now()
        avis.append((u, ligne))
    db.commit()

    for u, ligne in avis:                      # après le commit : un e-mail ne se rappelle pas
        if u is not None:
            _avis_maj(db, u, "referentiel_maj_fin", suite=message_de_fin(ligne).split("\n\n", 1)[-1])
    fiche = lambda u: {"prenom": u.prenom, "nom": u.nom, "email": u.email}
    return {"ok": True,
            "rebranches": [fiche(u) for u in rebranches],
            "non_rebranches": [fiche(u) for u in perdus]}


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
        {"id": t.id, "label": t.label, "is_default": bool(t.is_default), "origine": t.origine}
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


def _generer_prompt_type(db: Session, label: str, niveau: str) -> str:
    """Prompt de génération d'un type d'activité POUR CE couple, produit AUTOMATIQUEMENT au coche.

    Le GABARIT vit EN BASE (réglage `prompt_gabarit_type`) — il était écrit en dur ici alors que
    tous les autres prompts du produit sont administrables (méta-prompt de découpe en Setting,
    prompt du couple en colonne) : le retoucher demandait un redéploiement. Deux emplacements
    sont remplis ici, {label} et {niveau} (le type et le niveau du couple) ; deux autres sont
    laissés INTACTS pour la génération : {texte} (l'idée du prof, elle mène) et {referentiel}
    (le programme officiel). D'où le remplacement ciblé plutôt qu'un format() global, qui
    consommerait aussi les emplacements de la génération.

    Le résultat, lui, est stocké sur la ligne de liaison ; l'admin peut le relire et le corriger
    via ✎ Prompt — retoucher le gabarit ne réécrit donc jamais les prompts déjà posés.

    LU PAR `get_prompt` DEPUIS LE 02/08/2026, donc EN BASE et sans repli code. Le gabarit est
    entré au registre (clé `gabarit_type`, mode « replace ») : il se règle enfin depuis l'écran
    Prompts, et `valider_prompt` le garde à l'écriture. Avant, il n'avait aucune porte — ni
    route, ni écran — et un gabarit fautif faisait tomber la faute chez le PROF, à la
    génération, alors que l'auteur du texte est l'admin.

    ET ON CONTRÔLE CE QU'ON PRODUIT. Le garde-fou d'écriture ne couvre pas une valeur posée
    directement en base (Adminer est là, sur ce poste). Le prompt fabriqué ici est donc relu
    par la MÊME fonction que ✎ Prompt : si le gabarit produit un prompt invalide, l'admin
    l'apprend en cochant le type, avec un message qui nomme le défaut — jamais le prof au
    milieu d'une génération."""
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


class BasculerTypeBody(BaseModel):
    cycle_id: int
    niveau: str
    activite_type_id: int               # LE type basculé (un seul)
    actif: bool                         # True = cocher (lien actif), False = décocher (lien inactif)


@router.put("/admin/referentiels/types-activite", dependencies=[Depends(_require_admin)])
def basculer_type_activite(body: BasculerTypeBody, db: Session = Depends(get_db)):
    """Écrit DIRECTEMENT en base l'état d'UN type pour le couple — modèle SIMPLE (décision admin) :
    un type retenu = une ligne de lien, rien d'autre. `actif=True` → get-or-create du lien (à la
    création : `source` = origine du type, prompt gabarit posé). `actif=False` → le lien est
    SUPPRIMÉ, vraiment (ses précisions partent avec lui — CASCADE) : supprimé = plus en base, on
    n'en parle plus ; une future détection le recréera si l'IA relit le type dans le document.
    Idempotent. 404 si le couple n'a pas de référentiel ; 400 si le type n'existe pas au catalogue."""
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
    if body.actif:
        if l is None:                        # retenir un type sans lien → on crée le lien (source = origine)
            # Génération AUTO du prompt de ce type POUR CE couple, dès la création du lien (zéro copie).
            db.add(ReferentielActiviteType(referentiel_id=ref.id, activite_type_id=body.activite_type_id,
                                           actif=True, source=t.origine,
                                           prompt=_generer_prompt_type(db, t.label, body.niveau)))
        elif not (l.prompt or "").strip():   # lien déjà là mais sans prompt (ancien) → on le pose
            l.prompt = _generer_prompt_type(db, t.label, body.niveau)
    elif l is not None:
        db.delete(l)                         # retirer = SUPPRIMER le lien (précisions en cascade)
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
        ref = db.get(Referentiel, lien.referentiel_id)
        texte = _texte_du_couple(db, ref)   # le texte de travail figé au dépôt (get en base)
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
    # Garde-fou d'écriture — il manquait ICI, et seulement ici, de tout le produit : ce prompt
    # part ensuite dans `modele.format(...)` (api_generate), qui n'attrape que KeyError. Un
    # prompt sans {texte} ignorait l'idée du prof en silence ; une accolade seule rendait un
    # 500 nu au premier clic d'un enseignant. On refuse AVANT d'écrire, avec un message humain.
    from backend.contenu.activites import valider_prompt_couple   # import local : pas de cycle
    err = valider_prompt_couple(body.prompt)
    if err:
        raise HTTPException(400, err)
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
    cycle_id: int | None = None    # couple fourni → le type est aussi COCHÉ pour ce couple
    niveau: str | None = None
    suggestion_ia: bool = False    # True = l'ajout vient d'une SUGGESTION IA (badge 'ia' sur le lien)


@router.post("/admin/referentiels/types-activite/catalogue", dependencies=[Depends(_require_admin)])
def ajouter_type_catalogue(body: AjouterTypeCatalogueBody, db: Session = Depends(get_db)):
    """Ajoute un type au CATALOGUE GLOBAL (Create encadré) ET le COCHE pour le couple si le couple
    est fourni. Anti-doublon par LIBELLÉ insensible à la casse — la clé métier du catalogue, comme
    `matieres.nom` : un libellé déjà connu RÉUTILISE le type existant (jamais deux types de même
    libellé). Renvoie le type (créé ou réutilisé) + `deja_present`.

    ORIGINE (badge) : `suggestion_ia=True` = l'ajout vient d'une suggestion de la détection → type
    créé `origine='ia'`, lien coché `source='ia'`. Sinon (saisie manuelle de l'admin) → 'admin'.
    Le coche est un get-or-create encadré : lien déjà présent → rien, jamais de doublon."""
    label = (body.label or "").strip()
    if not label:
        raise HTTPException(400, "Le libellé du type d'activité est requis.")
    origine = "ia" if body.suggestion_ia else "admin"
    t = db.query(ActiviteType).filter(func.lower(ActiviteType.label) == label.lower()).first()
    deja_present = t is not None
    if t is None:
        maxo = db.query(func.max(ActiviteType.ordre)).scalar()
        t = ActiviteType(label=label, ordre=(maxo or 0) + 1, actif=True, origine=origine)
        db.add(t); db.commit(); db.refresh(t)

    # Couple fourni → coller le type au couple (coche = lien actif), avec la bonne origine.
    coche = False
    if body.cycle_id is not None and (body.niveau or "").strip():
        ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
        if ref is not None:
            l = (db.query(ReferentielActiviteType)
                   .filter(ReferentielActiviteType.referentiel_id == ref.id,
                           ReferentielActiviteType.activite_type_id == t.id).first())
            if l is None:
                db.add(ReferentielActiviteType(referentiel_id=ref.id, activite_type_id=t.id,
                                               actif=True, source=origine,
                                               prompt=_generer_prompt_type(db, t.label, body.niveau)))
                coche = True
            db.commit()

    return {"id": t.id, "label": t.label, "deja_present": deja_present, "coche_ia": coche}


@router.post("/admin/referentiels/types-activite/detecter", dependencies=[Depends(_require_admin)])
def detecter_types_activite_couple(body: RegleStatutBody, db: Session = Depends(get_db)):
    """L'IA LIT le document épuré du couple AVEC le catalogue des types sous les yeux
    (`detecter_types_activite`), et TOUT ce qu'elle retient est collé au couple (liaison
    `source='ia'`, prompt gabarit posé) : un libellé qui correspond au catalogue réutilise le type
    existant (badge Système · IA à l'écran) ; un libellé NOUVEAU est créé au catalogue
    (`origine='ia'`) dans le même geste — plus d'étape « suggestions » (décision admin : tout est
    déjà une proposition d'IA, l'admin fait le ménage sur la liste avec ✕).

    Modèle SIMPLE (décision admin) : un type retenu = une ligne de lien, le ✕ la SUPPRIME pour de
    vrai. La détection n'a donc qu'une règle : type lu AVEC un lien → rien à faire ; type lu SANS
    lien → lien créé. Un type retiré puis relu dans le document revient naturellement (sa ligne se
    recrée) ; un type retiré que l'IA ne lit plus reste dehors.

    CREATE encadré : type réutilisé par libellé (anti-doublon, insensible à la casse) ; une liaison
    n'est créée que si elle n'existe pas ENCORE — jamais de doublon."""
    ref = _ref_du_couple(db, body.cycle_id, body.niveau)   # 404 cycle / 422 niveau
    if ref is None:
        raise HTTPException(404, "Aucun référentiel pour ce couple.")
    texte = _texte_du_couple(db, ref)   # le texte de travail figé au dépôt (get en base)
    if not texte.strip():
        raise HTTPException(400, "Document sans texte lisible : détection impossible.")

    from backend.rag.analyse_amont import detecter_types_activite
    try:
        detectes = detecter_types_activite(texte, db=db)
    except Exception as e:
        raise HTTPException(400, f"Détection des types par l'IA impossible : {e}")

    # Liaisons EXISTANTES du couple, indexées par type — pour ne jamais doublonner.
    liaisons = {l.activite_type_id
                for l in (db.query(ReferentielActiviteType.activite_type_id)
                            .filter(ReferentielActiviteType.referentiel_id == ref.id).all())}

    coches_ia, deja_lies, crees = [], [], []
    vus: set[str] = set()
    for label in detectes:
        label = label.strip()
        cle = label.lower()                # matching par LIBELLÉ, comme les matières
        if not cle or cle in vus:          # même libellé (à la casse près) : une seule fois
            continue
        vus.add(cle)
        # Recherche par LIBELLÉ SEUL, sans filtrer sur `actif` — comme `ajouter_type_catalogue`.
        # Avec le filtre, un type que l'admin avait DÉSACTIVÉ devenait invisible ici, et la
        # détection en recréait un second portant le MÊME libellé : exactement le doublon que le
        # catalogue interdit (models_db.py:696), et que rien n'empêche en base (aucun unique sur
        # `label`). Un type désactivé reste désactivé : on ne le ressuscite pas en douce, on
        # passe simplement notre tour.
        t = (db.query(ActiviteType)
               .filter(func.lower(ActiviteType.label) == cle).first())
        if t is not None and not t.actif:
            continue                          # désactivé par l'admin : sa décision tient
        if t is None:
            # Type NOUVEAU : créé au catalogue (origine='ia') puis collé au couple, même geste.
            maxo = db.query(func.max(ActiviteType.ordre)).scalar()
            t = ActiviteType(label=label, ordre=(maxo or 0) + 1, actif=True, origine="ia")
            db.add(t); db.flush()
            crees.append({"id": t.id, "label": t.label})
        elif t.id in liaisons:
            deja_lies.append({"id": t.id, "label": t.label})   # déjà retenu : rien à faire
            continue
        # Prompt gabarit posé dès la création du lien : un type collé au couple est opérationnel
        # tout de suite, jamais « prompt vide ».
        db.add(ReferentielActiviteType(referentiel_id=ref.id, activite_type_id=t.id,
                                       actif=True, source="ia",
                                       prompt=_generer_prompt_type(db, t.label, body.niveau)))
        coches_ia.append({"id": t.id, "label": t.label})
    db.commit()
    return {"detectes": detectes, "coches_ia": coches_ia,
            "deja_lies": deja_lies, "crees": crees}
