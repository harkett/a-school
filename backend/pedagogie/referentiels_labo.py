"""LABO — le back de la procédure « Référentiels » en cours de reconstruction.

CE FICHIER EST LE BACK DU LABO, ET RIEN D'AUTRE. Il vit à côté de `referentiels_admin.py`
(l'écran historique), qui n'est plus jamais modifié : chaque étape de la procédure est REFAITE
ici, avec ses propres routes (`/api/admin/labo/referentiels/…`) et ses propres règles. Rien n'est
importé de l'ancien module — sinon une correction faite ici changerait l'écran d'à côté, ce qui
est exactement ce qu'on refuse. Quand toutes les étapes seront là, l'ancien disparaît et le labo
prend sa place.

LE COUPLE D'ABORD, LE PDF ENSUITE. L'admin choisit cycle · niveau, puis dépose le document : il
sait ce qu'il dépose, et il répond de leur cohérence. La détection du couple par l'IA est
abandonnée — on ne devine plus ce que quelqu'un sait déjà.

D'où la disparition de la ZONE D'ATTENTE du labo (jeton, `referentiel_depots`, ménage, route de
relecture par jeton). Elle n'existait que parce que la destination du fichier était inconnue tant
que le couple n'était pas deviné. Le couple étant donné d'entrée, la destination l'est aussi : les
PDF vont directement dans REFERENTIELS/<CYCLE>/<NIVEAU>/. Rien n'attend, donc rien n'est à balayer.

UN RÉFÉRENTIEL N'EST PAS TOUJOURS UN FICHIER. Au collège et à l'école, le programme complet du
cycle tient en un PDF ; au lycée il n'existe qu'éclaté, un par matière et par série. Le couple
reçoit donc plusieurs documents (`referentiel_documents`, une ligne par morceau), qu'on ordonne et
qu'on retire, et c'est CONSTITUER qui clôture : elle fabrique `referentiel.pdf`, crée la fiche
`referentiels` avec l'empreinte du produit, et lui rattache les morceaux. La base dit ce qui
existe, le disque ne porte que les octets.

CONSTITUER N'EST PAS TOUJOURS FUSIONNER, et c'est le point qu'on avait manqué. Un seul document
EST le référentiel : il est officiel, il est complet, on le prend TEL QUEL — pas d'IA, pas de
réécriture, pas un jeton dépensé. La fusion ne sert qu'à partir de DEUX documents, là où il y a
vraiment des redites à supprimer. Une seule route décide, côté serveur ; l'écran ne fait que
nommer le bouton d'après ce qu'il voit.

Ce qui est déjà là — le choix du couple, le dépôt des documents (fichier ou lien), la recherche du
lien officiel, la reconnaissance d'un document déjà connu, la constitution du référentiel, la
suppression, et la mise à jour d'un référentiel en service (mise en attente des profs, déblocage).
"""
import hashlib
import logging
import os
import re
import shutil
from pathlib import Path
from urllib.parse import unquote
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.nommage import dossier_cle as _dossier_cle
from backend.core.models_db import (Cycle, Niveau, Referentiel, ReferentielChunk,
                                    ReferentielDocument, Matiere, User,
                                    ReferentielActiviteType, ReferentielTypePrecision)
from backend.systeme.admin import (_require_admin, get_settings_dict, get_prompt, get_cle_texte,
                                   get_ai_provider, get_ai_model, get_max_tokens, get_temperature,
                                   get_retry_max, get_retry_wait_max)
from backend.llm.generator import generate, LLMRateLimitError

logger = logging.getLogger("aschool.referentiels_labo")

router = APIRouter()

_ROOT = Path(__file__).resolve().parents[2]                       # racine du dépôt
REFERENTIELS_DIR = _ROOT / "REFERENTIELS"

APERCU_LIGNES = 25                 # lignes de texte montrées à l'admin pour le contrôle


# ── Résolution du couple (cycle + niveau) ─────────────────────────────────────

def _ref_du_couple(db: Session, cycle_id: int, niveau: str) -> Referentiel | None:
    """Résout la ligne `referentiels` du COUPLE cycle+niveau. Lève 404 si le cycle est inconnu,
    422 si le niveau manque. Renvoie None si le niveau ou le référentiel n'existe pas encore."""
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


def _pdf_du_couple(db: Session, cycle_id: int, niveau: str) -> Path:
    """Chemin du PDF rangé pour le couple (REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf)."""
    cycle = db.get(Cycle, cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle inconnu.")
    return REFERENTIELS_DIR / _dossier_cle(cycle.nom) / _dossier_cle((niveau or "").strip()) / "referentiel.pdf"


# ── Étape 1 — LE COUPLE : cycle puis niveau ───────────────────────────
#
# L'écran lit l'arbre cycles → niveaux par `/admin/programmes` (programmes.py) — la même source
# que l'écran existant, et la seule : les cycles et les niveaux se créent à UNE place, l'écran
# Programmes. Le labo n'en crée jamais, il ne fait que choisir ; il n'a donc pas de route à lui
# pour ça — une seconde lecture du même arbre serait une copie de plus à tenir à jour.


# ── Étape 2 — LES DOCUMENTS : on empile, puis on constitue ───────────────────
#
# Le couple étant connu, la place des fichiers l'est aussi : plus de zone d'attente, plus de jeton.
# Ils vont directement dans REFERENTIELS/<CYCLE>/<NIVEAU>/. La détection du couple par l'IA
# n'existe plus : l'admin sait ce qu'il dépose, et il en répond.
#
# UN RÉFÉRENTIEL N'EST PAS TOUJOURS UN FICHIER. Au collège et à l'école, le programme complet du
# cycle tient en un PDF ; au lycée il n'existe qu'éclaté, un fichier par matière et par série. Le
# couple reçoit donc PLUSIEURS documents, dans l'ordre qu'on veut, et c'est CONSTITUER qui clôture :
#
#   dépôt(s)    → une ligne `referentiel_documents` par morceau, le fichier rangé sous son nom de
#                 disque. Rien d'autre. Le couple n'a pas encore de référentiel.
#   constituer  → `referentiel.pdf` est écrit et c'est LÀ que la ligne `referentiels` naît, avec
#                 l'empreinte du produit. UN morceau : il est copié tel quel, sans IA — il EST le
#                 référentiel. PLUSIEURS : l'IA les lit et n'écrit qu'une fois chaque chose.
#                 Les morceaux survivent dans les deux cas, rattachés à la fiche.
#
# La base dit ce qui existe, le disque ne porte que les octets : un écran quitté puis rouvert
# retrouve tout en relisant `referentiel_documents`. Rien ne se devine du contenu d'un dossier.

def _apercu(pdf_path: Path) -> tuple[int, str]:
    """(nombre de pages, premières lignes de texte) — la matière du point de contrôle admin."""
    import pdfplumber  # import paresseux : ne pas alourdir le démarrage du serveur
    with pdfplumber.open(str(pdf_path)) as pdf:
        n_pages = len(pdf.pages)
        premier = (pdf.pages[0].extract_text() or "") if n_pages else ""
    lignes = [l for l in premier.splitlines() if l.strip()][:APERCU_LIGNES]
    return n_pages, "\n".join(lignes)


def _deja_connu(db: Session, empreinte: str, sauf_niveau_id: int | None = None) -> dict | None:
    """Ce document a-t-il DÉJÀ été fourni pour un autre couple ? Recherche par empreinte du
    CONTENU, jamais par le nom : le même document téléchargé deux fois porte souvent deux noms, et
    deux documents différents portent parfois le même.

    On regarde les DOCUMENTS, pas les référentiels. Depuis que le référentiel est un fusionné, son
    empreinte n'est plus celle d'aucun morceau : comparer un dépôt aux référentiels ne trouverait
    plus jamais rien. Ce qui se compare à un morceau, c'est un morceau.

    Le couple visé est exclu : y redéposer le même document est un doublon interne, pas une
    ressemblance avec un autre niveau — et il se voit tout seul dans la liste.

    Rend de quoi le DIRE à l'admin, ou None. Ne bloque rien, n'écrit rien : c'est un
    avertissement, pas un refus — le même programme peut légitimement servir deux niveaux."""
    q = (db.query(ReferentielDocument, Niveau, Cycle)
           .join(Niveau, Niveau.id == ReferentielDocument.niveau_id)
           .join(Cycle, Cycle.id == Niveau.cycle_id)
           .filter(ReferentielDocument.empreinte == empreinte))
    if sauf_niveau_id is not None:
        q = q.filter(ReferentielDocument.niveau_id != sauf_niveau_id)
    ligne = q.order_by(ReferentielDocument.id).first()
    if ligne is None:
        return None
    doc, niveau, cycle = ligne
    return {"ou": "valide" if doc.referentiel_id else "en_cours",
            "fichier": doc.fichier_origine, "cycle": cycle.nom, "niveau": niveau.nom}


def _deja_fusionne(db: Session, empreinte: str) -> dict | None:
    """Le document FUSIONNÉ est-il, à l'octet près, le référentiel d'un autre couple ? Même
    principe, mais à l'autre bout de la procédure : ici on compare un référentiel à un référentiel."""
    ligne = (db.query(Referentiel, Niveau, Cycle)
               .join(Niveau, Niveau.id == Referentiel.niveau_id)
               .join(Cycle, Cycle.id == Niveau.cycle_id)
               .filter(Referentiel.empreinte == empreinte).first())
    if ligne is None:
        return None
    ref, niveau, cycle = ligne
    return {"ou": "valide", "fichier": ref.fichier, "cycle": cycle.nom, "niveau": niveau.nom}


def _couple_libre(db: Session, cycle_id: int, niveau_id: int) -> tuple[Cycle, Niveau]:
    """Le couple visé par le dépôt : il doit EXISTER et n'avoir pas encore de référentiel.

    Le labo ne crée jamais un niveau (une seule place pour ça : l'écran Programmes) → 404. Et un
    couple déjà servi n'est pas mis à jour en douce : un nouveau document, c'est une nouvelle
    procédure, donc on supprime d'abord — le message le dit."""
    cycle = db.get(Cycle, cycle_id)
    if not cycle:
        raise HTTPException(404, "Cycle inconnu.")
    niveau = db.get(Niveau, niveau_id)
    if not niveau or niveau.cycle_id != cycle.id:
        raise HTTPException(404, "Niveau inconnu pour ce cycle.")
    if db.query(Referentiel).filter(Referentiel.niveau_id == niveau.id).first() is not None:
        raise HTTPException(409, f"« {cycle.nom} · {niveau.nom} » a déjà un référentiel. "
                                 "Supprimez-le d'abord, puis refaites la procédure avec le "
                                 "nouveau document.")
    return cycle, niveau


def _dossier_du_couple(cycle: Cycle, niveau: Niveau) -> Path:
    return REFERENTIELS_DIR / _dossier_cle(cycle.nom) / _dossier_cle(niveau.nom)


def _plafonds(db: Session) -> tuple[float, int]:
    """(Mo par document déposé, pages du référentiel PRODUIT) — réglages lus EN BASE.

    Deux plafonds, deux moments, et ils ne parlent plus de la même chose :
      • `depot_max_mo` borne CHAQUE morceau déposé — un fichier de 300 Mo n'a pas à s'écrire sur
        le disque avant d'être refusé ;
      • `fusion_max_pages` borne ce que l'IA PRODUIT. Les documents d'entrée, eux, ne sont plus
        plafonnés en pages : c'est normal qu'ils soient longs (139 + 64 pages vus en vrai), c'est
        même la raison d'être de la fusion. L'ancien `depot_max_pages` ne s'applique donc plus
        ici ; il reste au service de l'écran historique."""
    reglages = get_settings_dict(db)
    try:
        max_mo = float(reglages.get("depot_max_mo", 30))
    except (TypeError, ValueError):
        max_mo = 30.0
    try:
        max_pages = int(reglages.get("fusion_max_pages", 15))
    except (TypeError, ValueError):
        max_pages = 15
    return max_mo, max_pages


def _documents_du_couple(db: Session, niveau_id: int) -> list[ReferentielDocument]:
    return (db.query(ReferentielDocument)
              .filter(ReferentielDocument.niveau_id == niveau_id)
              .order_by(ReferentielDocument.ordre, ReferentielDocument.id).all())


def _vue_document(d: ReferentielDocument) -> dict:
    """Ce qu'un document montre à l'écran. L'aperçu n'y est pas : 25 lignes par document
    alourdiraient la liste pour rien — il se demande document par document."""
    return {"id": d.id, "ordre": d.ordre, "fichier": d.fichier_origine, "pages": d.pages,
            "taille_ko": d.taille_ko, "source": d.source,
            "constitue": d.referentiel_id is not None}


def _deposer(content: bytes, filename: str, db: Session, source: str,
             cycle_id: int, niveau_id: int, url_source: str | None = None) -> dict:
    """Contrôle UN document, le range dans le dossier du couple, écrit sa ligne. C'est tout.

    Ce dépôt ne clôture RIEN : ni `referentiel.pdf`, ni fiche `referentiels`. Il empile un
    morceau de plus, dans l'ordre d'arrivée. La fusion s'occupe du reste.

    Ce qui est vérifié ici, morceau par morceau :
      • le couple est libre (pas déjà de référentiel) — sinon rien n'est écrit nulle part ;
      • c'est bien un PDF, et il n'est pas à lui seul plus gros que le plafond : un fichier de
        300 Mo n'a pas à s'écrire sur le disque avant d'être refusé ;
      • il se lit (pdfplumber) — un PDF chiffré ou abîmé échoue ICI, pas au moment de la fusion.
    Le NOMBRE DE PAGES n'est pas jugé ici : le plafond porte sur le total fusionné.

    Le fichier est écrit sous un nom de travail puis renommé (renommage atomique) : un refus ne
    laisse rien, et un dépôt à moitié écrit n'existe jamais sous son nom définitif. Si le commit
    échoue, le fichier est retiré — la ligne et le fichier vivent et meurent ensemble."""
    cycle, niveau = _couple_libre(db, cycle_id, niveau_id)
    max_mo, _ = _plafonds(db)
    if len(content) > max_mo * 1024 * 1024:
        raise HTTPException(400, f"PDF trop volumineux (maximum {max_mo:g} Mo).")
    if content[:5] != b"%PDF-":
        raise HTTPException(400, "Le document récupéré n'est pas un PDF valide.")

    dossier = _dossier_du_couple(cycle, niveau)
    dossier.mkdir(parents=True, exist_ok=True)
    # Un nom de disque À LUI. Deux documents peuvent porter le même nom d'origine, et un nom fourni
    # n'est jamais un nom de fichier sûr. `referentiel.pdf` reste réservé au fusionné.
    nom_disque = f"doc-{uuid4().hex[:12]}.pdf"
    final = dossier / nom_disque
    travail = dossier / f"{nom_disque}.depot"
    travail.write_bytes(content)
    try:
        n_pages, apercu = _apercu(travail)
    except Exception as e:
        travail.unlink(missing_ok=True)
        raise HTTPException(400, f"Lecture du PDF impossible : {e}")

    empreinte = hashlib.sha256(content).hexdigest()
    # LE MÊME DOCUMENT DEUX FOIS SUR LE MÊME COUPLE : refusé, et c'est le seul refus de doublon.
    # Il passait sans un mot — deux lignes, les pages comptées deux fois, et l'IA payée pour lire
    # deux fois la même chose. Ailleurs (autre couple), le même document reste légitime : un même
    # programme peut servir deux niveaux ; là, on se contente de prévenir (`deja`).
    jumeau = next((d for d in _documents_du_couple(db, niveau.id) if d.empreinte == empreinte), None)
    if jumeau is not None:
        travail.unlink(missing_ok=True)
        raise HTTPException(409, f"Ce document est déjà dans la liste de « {cycle.nom} · "
                                 f"{niveau.nom} », sous le nom « {jumeau.fichier_origine} ». "
                                 "C'est le même fichier, quel que soit son nom.")

    deja = _deja_connu(db, empreinte, sauf_niveau_id=niveau.id)
    os.replace(travail, final)                      # il prend sa place, d'un seul geste
    rang = len(_documents_du_couple(db, niveau.id))
    doc = ReferentielDocument(
        niveau_id=niveau.id, referentiel_id=None, ordre=rang,
        fichier_origine=filename, fichier_disque=nom_disque, empreinte=empreinte,
        taille_ko=round(len(content) / 1024), pages=n_pages,
        source=source, url_source=url_source, apercu=apercu)
    db.add(doc)
    try:
        db.commit()
        db.refresh(doc)
    except Exception as e:
        db.rollback()
        final.unlink(missing_ok=True)
        logger.exception("Dépôt : écriture du document impossible (%s · %s)", cycle.nom, niveau.nom)
        raise HTTPException(500, f"Enregistrement du document impossible : {e}")
    logger.info("Dépôt : %s · %s ← %s (%d pages, rang %d)",
                cycle.nom, niveau.nom, filename, n_pages, rang)
    documents = _documents_du_couple(db, niveau.id)
    return {
        "cycle_id": cycle.id, "cycle": cycle.nom,
        "niveau_id": niveau.id, "niveau": niveau.nom,
        "document_id": doc.id,
        "filename": filename,
        "taille_ko": doc.taille_ko,
        "pages": n_pages,
        "apercu": apercu,
        # `deja` : null (document inconnu) ou le couple qu'il sert déjà. On prévient, on ne bloque pas.
        "deja": deja,
        # La liste complète repart avec le dépôt : l'écran n'a pas à la redemander.
        "documents": [_vue_document(d) for d in documents],
        "total_pages": sum(d.pages for d in documents),
        "total_ko": sum(d.taille_ko for d in documents),
    }


# ── Étape 2 bis — TROUVER LE LIEN (aide facultative) ─────────────────────────
#
# Le champ « Par lien » attend une adresse que l'admin va chercher lui-même, dans un autre onglet.
# Cette route la lui PROPOSE : elle passe SA question à un moteur de recherche et rend ce que le
# moteur a trouvé. Elle ne télécharge rien, n'écrit rien, ne dépose rien — elle remplit un champ.
# Le geste qui engage reste « Récupérer », et il est à l'admin.
#
# LA QUESTION EST À L'ADMIN, PAS À MOI. L'écran l'affiche AVANT de chercher, pré-remplie avec le
# cycle et le niveau, et il la corrige comme il veut. On ne filtre rien, on ne reclasse rien : les
# résultats reviennent dans l'ordre du moteur. C'est volontaire — la version précédente jugeait à
# sa place (domaines autorisés, mots interdits, millésime lu dans le document) avec des règles
# réglées sur quatre couples de la scolarité obligatoire, et elles ne valaient que pour eux.
#
# UN MOTEUR, PAS UN MODÈLE. Un modèle sans accès au web répondrait de mémoire et INVENTERAIT une
# adresse plausible (le nôtre est appelé sans outil : backend/llm/generator.py n'envoie jamais de
# `tools`). Ici les liens sortent d'un index : ils existent. Que ce soit LE bon document, c'est
# l'admin qui en juge — d'où le bouton « Voir », et les contrôles de `_deposer` derrière.
#
# La clé vit dans le .env, jamais en base — la règle des clés LLM (cf. AiFournisseur.cle_env :
# « la valeur — le secret — reste dans le .env »). Sans clé, la fonction se déclare indisponible
# et l'écran cache le bouton : rien ne casse, la saisie à la main est inchangée.

TAVILY_URL = "https://api.tavily.com/search"
TAVILY_CLE_ENV = "TAVILY_API_KEY_FIND"
RECHERCHE_MAX = 12          # résultats demandés au moteur


def _question_par_defaut(cycle: str, niveau: str) -> str:
    """La question PROPOSÉE — le point de départ, pas une règle. L'écran l'affiche et l'admin la
    réécrit avant de chercher. Le cycle et le niveau, et rien d'autre : ce sont les deux seules
    choses qu'on sache à coup sûr du document cherché."""
    return f"{cycle} {niveau}".strip()


def _cle_tavily() -> str:
    return (os.getenv(TAVILY_CLE_ENV) or "").strip()


@router.get("/admin/labo/referentiels/recherche-dispo", dependencies=[Depends(_require_admin)])
def recherche_dispo():
    """La recherche de lien est-elle branchée ? L'écran s'en sert pour afficher ou non son bouton :
    une fonction sans clé ne doit pas s'offrir comme si elle marchait."""
    return {"disponible": bool(_cle_tavily())}


class ChercherLienBody(BaseModel):
    cycle_id: int
    niveau_id: int
    # Ce que l'admin a écrit dans le champ. Vide ou absent → la proposition par défaut.
    question: str | None = None


@router.post("/admin/labo/referentiels/chercher-lien", dependencies=[Depends(_require_admin)])
def chercher_lien(body: ChercherLienBody, db: Session = Depends(get_db)):
    """Ce que l'admin a écrit part chez Tavily, et ce que Tavily rend revient. Rien entre les deux.

    AUCUNE RÈGLE ICI, ET C'EST VOULU. La version précédente filtrait sur trois listes de mots
    écrites en dur (domaines autorisés, « ce n'est qu'un projet », « ce n'est qu'une matière ») et
    reclassait sur le millésime lu dans le document. Ces règles avaient été réglées sur quatre
    couples de la scolarité obligatoire (GS, CM1, 4e, Seconde) et ne valaient que pour eux : sur un
    BTS, elles jetaient tout — le bon PDF compris, quand il vit sur un domaine que je n'avais pas
    prévu. Deviner à la place de l'admin coûtait plus que ça ne servait.

    Donc : la question est À LUI. On la propose (cycle + niveau), il la corrige, elle part telle
    quelle. On affichera les résultats bruts, dans l'ordre du moteur, et on affinera EN VOYANT
    ce qui sort — pas en imaginant ce qui devrait sortir."""
    cle = _cle_tavily()
    if not cle:
        raise HTTPException(503, "La recherche du lien officiel n'est pas configurée "
                                 f"(clé {TAVILY_CLE_ENV} absente du .env).")
    # Le même couple que le dépôt, avec la même exigence : inutile de proposer un lien pour un
    # couple déjà servi, il serait refusé au dépôt.
    cycle, niveau = _couple_libre(db, body.cycle_id, body.niveau_id)
    # Ce que l'écran a envoyé, ou la proposition par défaut s'il n'a rien envoyé.
    question = (body.question or "").strip() or _question_par_defaut(cycle.nom, niveau.nom)
    try:
        r = httpx.post(TAVILY_URL, timeout=40.0,
                       headers={"Authorization": f"Bearer {cle}"},
                       json={"query": question, "search_depth": "advanced",
                             "max_results": RECHERCHE_MAX})
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning("Recherche de lien impossible (%s · %s) : %s", cycle.nom, niveau.nom, e)
        raise HTTPException(502, f"Recherche du lien impossible : {e}")

    pistes, vus = [], set()
    for res in (data.get("results") or []):
        url = (res.get("url") or "").strip()
        if not url or url in vus:
            continue
        vus.add(url)
        pistes.append({"url": url, "titre": (res.get("title") or url).strip(),
                       # `pdf` sert à l'affichage : l'admin voit d'un coup d'œil ce qui est
                       # téléchargeable tel quel. Ce n'est pas un filtre, rien n'est écarté.
                       "pdf": url.split("?")[0].lower().endswith(".pdf")})
    logger.info("Recherche de lien : %s · %s → %d résultat(s) pour « %s »",
                cycle.nom, niveau.nom, len(pistes), question)
    return {"cycle": cycle.nom, "niveau": niveau.nom, "question": question, "pistes": pistes}


class PreparerLienBody(BaseModel):
    cycle_id: int
    niveau_id: int
    url: str


@router.post("/admin/labo/referentiels/preparer-lien", dependencies=[Depends(_require_admin)])
def preparer_lien(body: PreparerLienBody, db: Session = Depends(get_db)):
    url = body.url.strip()
    if not url:
        raise HTTPException(400, "Lien vide.")
    _couple_libre(db, body.cycle_id, body.niveau_id)   # inutile de télécharger pour rien
    try:
        r = httpx.get(url, follow_redirects=True, timeout=30.0)
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(400, f"Téléchargement depuis le lien impossible : {e}")
    filename = (url.rsplit("/", 1)[-1].split("?")[0]) or "referentiel.pdf"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    return _deposer(r.content, filename, db, "lien", body.cycle_id, body.niveau_id, url_source=url)


@router.post("/admin/labo/referentiels/preparer-depot", dependencies=[Depends(_require_admin)])
async def preparer_depot(file: UploadFile = File(...), cycle_id: int = Form(...),
                         niveau_id: int = Form(...), db: Session = Depends(get_db)):
    content = await file.read()
    return _deposer(content, file.filename or "referentiel.pdf", db, "depot", cycle_id, niveau_id)


@router.get("/admin/labo/referentiels/pdf", dependencies=[Depends(_require_admin)])
def voir_pdf(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Le référentiel FUSIONNÉ du couple, relu depuis sa place — le couple suffit à le retrouver.
    Lecture seule, servi en ligne (visionneuse du navigateur). Avant la fusion il n'existe pas :
    ce sont les morceaux qu'on relit alors, un par un (route `document-pdf`)."""
    pdf = _pdf_du_couple(db, cycle_id, niveau)
    if not pdf.exists():
        raise HTTPException(404, "Aucun document pour ce couple.")
    return FileResponse(str(pdf), media_type="application/pdf",
                        headers={"Content-Disposition": "inline; filename=referentiel.pdf"})


# ── Les morceaux : lire, ordonner, retirer ───────────────────────────────────

def _document(db: Session, document_id: int) -> tuple[ReferentielDocument, Cycle, Niveau]:
    """Un document et son couple, ou 404. Le chemin du fichier se REFAIT depuis le couple : rien
    n'est stocké en dur, un dossier renommé ailleurs ne laisse pas de chemin mort en base."""
    doc = db.get(ReferentielDocument, document_id)
    if doc is None:
        raise HTTPException(404, "Document inconnu.")
    niveau = db.get(Niveau, doc.niveau_id)
    cycle = db.get(Cycle, niveau.cycle_id) if niveau else None
    if niveau is None or cycle is None:
        raise HTTPException(404, "Couple inconnu pour ce document.")
    return doc, cycle, niveau


@router.get("/admin/labo/referentiels/documents", dependencies=[Depends(_require_admin)])
def lister_documents(niveau_id: int, db: Session = Depends(get_db)):
    """Les morceaux fournis pour un couple, dans l'ordre, avec leurs totaux et les plafonds.

    C'est la source de la cartouche « Document PDF » : l'écran ne garde rien en mémoire, il relit.
    `max_pages` est celui du référentiel PRODUIT, pas des documents lus : ceux-ci peuvent être
    longs sans que ça pose problème — c'est justement ce que la fusion règle."""
    if db.get(Niveau, niveau_id) is None:
        raise HTTPException(404, "Niveau inconnu.")
    documents = _documents_du_couple(db, niveau_id)
    max_mo, max_pages = _plafonds(db)
    ref = db.query(Referentiel).filter(Referentiel.niveau_id == niveau_id).first()
    return {
        "documents": [_vue_document(d) for d in documents],
        "total_pages": sum(d.pages for d in documents),
        "total_ko": sum(d.taille_ko for d in documents),
        "max_pages": max_pages, "max_mo": max_mo,
        # Le couple est-il clôturé ? L'écran en dépend : une fois constitué, on n'empile plus.
        "constitue": ref is not None,
        "fichier": ref.fichier if ref else None,
    }


@router.get("/admin/labo/referentiels/document-pdf", dependencies=[Depends(_require_admin)])
def voir_document(document_id: int, db: Session = Depends(get_db)):
    """UN morceau, relu avant la fusion — c'est le bouton « Voir » de chaque ligne."""
    doc, cycle, niveau = _document(db, document_id)
    chemin = _dossier_du_couple(cycle, niveau) / doc.fichier_disque
    if not chemin.exists():
        raise HTTPException(404, "Le fichier de ce document est introuvable sur le disque.")
    return FileResponse(str(chemin), media_type="application/pdf",
                        headers={"Content-Disposition": "inline; filename=document.pdf"})


class OrdreBody(BaseModel):
    niveau_id: int
    # Les identifiants des documents dans l'ordre voulu. Tous, sans exception.
    documents: list[int]


@router.post("/admin/labo/referentiels/documents/ordre", dependencies=[Depends(_require_admin)])
def ordonner_documents(body: OrdreBody, db: Session = Depends(get_db)):
    """L'ordre de la fusion — c'est celui du référentiel final, donc une DONNÉE, pas un hasard.

    La liste envoyée doit être exactement celle du couple : ni oubli, ni intrus. Un ordre partiel
    laisserait des documents au rang de leur voisin, et la fusion suivante mélangerait tout.

    REFUSÉ une fois le référentiel constitué, comme le retrait : il est écrit, changer l'ordre en
    base annoncerait une composition que `referentiel.pdf` ne suit pas."""
    documents = _documents_du_couple(db, body.niveau_id)
    if not documents:
        raise HTTPException(404, "Aucun document pour ce couple.")
    if any(d.referentiel_id is not None for d in documents):
        raise HTTPException(409, "Le référentiel de ce couple est constitué : son ordre ne change "
                                 "plus. Supprimez-le pour reprendre la composition.")
    if sorted(body.documents) != sorted(d.id for d in documents):
        raise HTTPException(422, "L'ordre envoyé ne correspond pas aux documents de ce couple.")
    rangs = {doc_id: i for i, doc_id in enumerate(body.documents)}
    for d in documents:
        d.ordre = rangs[d.id]
    db.commit()
    return {"ok": True, "documents": [_vue_document(d)
                                      for d in _documents_du_couple(db, body.niveau_id)]}


class RetirerDocumentBody(BaseModel):
    document_id: int


@router.post("/admin/labo/referentiels/documents/retirer", dependencies=[Depends(_require_admin)])
def retirer_document(body: RetirerDocumentBody, db: Session = Depends(get_db)):
    """Retire UN morceau : sa ligne et son fichier partent ensemble.

    Refusé une fois le référentiel constitué (409) : les morceaux disent alors de quoi le
    `referentiel.pdf` est fait, en retirer un en douce serait un mensonge. Pour changer la
    composition, on supprime le référentiel et on refait la procédure."""
    doc, cycle, niveau = _document(db, body.document_id)
    if doc.referentiel_id is not None:
        raise HTTPException(409, f"Le référentiel de « {cycle.nom} · {niveau.nom} » est constitué. "
                                 "Supprimez-le pour reprendre la composition de ses documents.")
    chemin = _dossier_du_couple(cycle, niveau) / doc.fichier_disque
    db.delete(doc)
    db.commit()
    chemin.unlink(missing_ok=True)      # après le commit : ce qui ne s'annule pas vient en dernier
    # Les rangs se resserrent, sinon un trou grandit à chaque retrait.
    for i, d in enumerate(_documents_du_couple(db, niveau.id)):
        d.ordre = i
    db.commit()
    logger.info("Document retiré : %s · %s ← %s", cycle.nom, niveau.nom, doc.fichier_origine)
    return {"ok": True, "documents": [_vue_document(d)
                                      for d in _documents_du_couple(db, niveau.id)]}


# ── LA FUSION — c'est elle qui clôture l'étape ───────────────────────────────

POLICE_UNICODE = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
FUSION_CARACTERES_PAR_PAGE = 2600      # mesuré sur le rendu ci-dessous (11 pt, interligne 5,5 mm)
FUSION_SIGNES_PAR_JETON = 3.5          # français : ~3,5 caractères par jeton, ordre de grandeur
FUSION_TEXTE_MAX = 400_000             # ce qu'on accepte de donner à lire à l'IA, en caractères


def _texte_du_pdf(chemin: Path) -> str:
    """Le texte ENTIER d'un PDF, page après page. `_apercu` ne lit que la première page (elle
    sert au contrôle visuel) ; ici il faut tout, c'est la matière que l'IA va lire."""
    import pdfplumber                 # import paresseux : ne pas alourdir le démarrage
    with pdfplumber.open(str(chemin)) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def _ecrire_pdf(texte: str, destination: Path, titre: str) -> None:
    """Écrit un texte dans un PDF lisible. Titres « ## », puces « - », le reste au fil.

    fpdf2 pour écrire (pdfplumber et pypdfium2 ne savent que lire ou assembler), avec une police
    UNICODE : les polices de base d'un PDF sont limitées au latin-1, et un référentiel contient
    des tirets cadratins, des apostrophes typographiques, parfois des signes mathématiques — la
    génération tomberait dessus. Si la police manque (image non reconstruite), on retombe sur la
    police de base et on remplace ce qu'elle ne sait pas écrire : un référentiel un peu moins joli
    vaut mieux qu'un bouton qui ne marche pas."""
    from fpdf import FPDF             # import paresseux

    doc = FPDF(format="A4")
    doc.set_auto_page_break(auto=True, margin=15)
    doc.set_margins(18, 15, 18)
    unicode_ok = POLICE_UNICODE.exists()
    if unicode_ok:
        doc.add_font("ref", "", str(POLICE_UNICODE))
        doc.add_font("ref", "B", str(POLICE_UNICODE))   # pas de gras réel : même dessin, assumé
        famille = "ref"
    else:
        famille = "Helvetica"
        texte = (texte.replace("—", "-").replace("–", "-").replace("’", "'")
                      .replace("œ", "oe").replace("Œ", "OE").replace("…", "..."))
        texte = texte.encode("latin-1", "replace").decode("latin-1")
        titre = titre.encode("latin-1", "replace").decode("latin-1")

    doc.add_page()
    # Largeur DONNÉE, et retour à la marge gauche après chaque bloc. La largeur « 0 » (jusqu'à la
    # marge droite) semble équivalente, mais fpdf2 laisse le curseur COLLÉ à la marge droite après
    # un multi_cell : le bloc suivant se retrouvait alors avec une largeur nulle, et la génération
    # tombait sur « Not enough horizontal space » — vu en vrai, sur le programme du cycle 4.
    largeur = doc.w - doc.l_margin - doc.r_margin
    suite = {"new_x": "LMARGIN", "new_y": "NEXT"}

    doc.set_font(famille, "B", 15)
    doc.multi_cell(largeur, 8, titre, **suite)
    doc.ln(3)
    for ligne in texte.splitlines():
        nue = ligne.strip()
        if not nue:
            doc.ln(2.5)
            continue
        if nue.startswith("#"):                      # une matière
            doc.ln(2)
            doc.set_font(famille, "B", 12.5)
            doc.multi_cell(largeur, 6.5, nue.lstrip("# ").strip(), **suite)
            doc.ln(1)
            continue
        doc.set_font(famille, "", 10.5)
        if nue.startswith(("-", "•", "*")):
            nue = "• " + nue.lstrip("-•* ").strip()
        doc.multi_cell(largeur, 5.5, nue, **suite)
    doc.output(str(destination))


def _fusionner_par_ia(db: Session, cycle: Cycle, niveau: Niveau,
                      documents: list[tuple[str, Path]], max_pages: int, destination: Path) -> None:
    """Fait LIRE les documents à l'IA et écrit le référentiel qu'elle en tire.

    C'est ça, « fusionner » : pas empiler. Deux documents d'un même niveau se recouvrent presque
    toujours — un programme et son bulletin officiel disent la même chose, deux fichiers redisent
    la même matière. Les coller bout à bout additionnerait les redites (mesuré : 139 + 64 = 203
    pages pour un programme qui en fait 15). L'IA garde le meilleur, une seule fois.

    Les documents d'origine ne sont pas touchés : ils restent la preuve de ce qui a servi."""
    morceaux, budget, lu = [], FUSION_TEXTE_MAX, 0
    for nom, chemin in documents:
        texte = _texte_du_pdf(chemin)[:budget]
        budget -= len(texte)
        lu += len(texte.strip())
        morceaux.append(f"--- Document : {nom} ---\n{texte}")
        if budget <= 0:
            logger.warning("Fusion : texte tronqué à %d caractères (%s · %s)",
                           FUSION_TEXTE_MAX, cycle.nom, niveau.nom)
            break
    if lu == 0:
        # Aucun texte : ce sont des images. Le dire, plutôt que d'envoyer du vide à l'IA et de
        # rendre un référentiel inventé.
        raise HTTPException(400, "Aucun texte lisible dans ces documents — ce sont probablement "
                                 "des PDF scannés (images).")

    # LA LONGUEUR DEMANDÉE TIENT COMPTE DES DEUX BORNES. Le plafond de pages dit ce qu'on veut
    # lire ; `max_tokens` dit ce que le modèle peut écrire d'un coup. Demander 15 pages alors que
    # la réponse est coupée à 8 000 jetons rendrait un référentiel tronqué en pleine phrase — on
    # demande donc la plus petite des deux, et le texte est entier.
    max_tokens = get_max_tokens(db, "referentiel_fusion")
    signes = min(max_pages * FUSION_CARACTERES_PAR_PAGE, int(max_tokens * FUSION_SIGNES_PAR_JETON))
    prompt = get_prompt(db, "referentiel_fusion").format(
        cycle=cycle.nom, niveau=niveau.nom,
        documents="\n\n".join(morceaux),
        consigne_taille=f"Le texte entier doit tenir en {signes} caractères environ "
                        f"({max_pages} pages au maximum) : va à l'essentiel, sans rien perdre de "
                        f"ce qui définit le programme.")
    texte = generate(prompt, cle=get_cle_texte(db), provider=get_ai_provider(db),
                     model=get_ai_model(db), max_tokens=max_tokens,
                     temperature=get_temperature(db), retry_max=get_retry_max(db),
                     retry_wait_max=get_retry_wait_max(db)).strip()
    if not texte:
        raise HTTPException(502, "L'IA n'a rien produit à partir de ces documents. Réessayez.")
    _ecrire_pdf(texte, destination, f"Référentiel — {cycle.nom} · {niveau.nom}")


class ConstituerBody(BaseModel):
    cycle_id: int
    niveau_id: int


@router.post("/admin/labo/referentiels/constituer", dependencies=[Depends(_require_admin)])
def constituer(body: ConstituerBody, db: Session = Depends(get_db)):
    """Fabrique le `referentiel.pdf` du couple à partir de ses documents, et la fiche naît.

    DEUX CHEMINS, ET C'EST LE SERVEUR QUI CHOISIT — l'écran ne fait que nommer le bouton.

      • UN SEUL DOCUMENT : il EST le référentiel. Il est officiel, il est complet, il a déjà passé
        les contrôles du dépôt. On le COPIE tel quel. Aucune IA n'est appelée : la faire réécrire
        88 pages officielles en 15 ne « fusionne » rien, ça les abîme — et ça coûte des jetons pour
        détruire de l'information. Le plafond `fusion_max_pages` ne s'y applique pas non plus : il
        borne ce que l'IA PRODUIT, pas un document officiel qu'on reprend intact.

      • DEUX DOCUMENTS OU PLUS : là, il y a vraiment des redites (un programme et son bulletin
        officiel disent la même chose). L'IA lit tout et n'écrit qu'une fois chaque chose, dans la
        limite de `fusion_max_pages`.

    C'est le seul endroit où naît la ligne `referentiels` — avec l'empreinte du PRODUIT. Les
    morceaux, eux, restent : ils sont la preuve de ce qui a servi.

    En cas d'échec, le `referentiel.pdf` est retiré : pas de fichier sans fiche, jamais."""
    # DÉJÀ CONSTITUÉ : ce n'est pas un refus, c'est un constat. Le message générique du dépôt
    # (« supprimez-le d'abord ») serait faux ici : l'admin qui reclique après une attente trop
    # courte a réussi, il ne cherche pas à recommencer. On le lui dit, et l'écran rouvre le couple.
    cycle_vu = db.get(Cycle, body.cycle_id)
    niveau_vu = db.get(Niveau, body.niveau_id)
    if (cycle_vu and niveau_vu
            and db.query(Referentiel).filter(Referentiel.niveau_id == niveau_vu.id).first()):
        raise HTTPException(409, f"Le référentiel de « {cycle_vu.nom} · {niveau_vu.nom} » est déjà "
                                 "constitué. Rien à refaire.")
    cycle, niveau = _couple_libre(db, body.cycle_id, body.niveau_id)
    documents = _documents_du_couple(db, niveau.id)
    if not documents:
        raise HTTPException(409, "Aucun document pour ce couple.")

    dossier = _dossier_du_couple(cycle, niveau)
    chemins = [dossier / d.fichier_disque for d in documents]
    manquants = [d.fichier_origine for d, c in zip(documents, chemins) if not c.exists()]
    if manquants:
        raise HTTPException(409, "Document introuvable sur le disque : " + ", ".join(manquants))

    max_mo, max_pages = _plafonds(db)
    par_ia = len(documents) > 1
    final = dossier / "referentiel.pdf"
    travail = dossier / "referentiel.pdf.travail"
    try:
        if par_ia:
            _fusionner_par_ia(db, cycle, niveau,
                              [(d.fichier_origine, c) for d, c in zip(documents, chemins)],
                              max_pages, travail)
        else:
            # Copie, pas déplacement : le morceau reste à sa place, il est la preuve de l'origine.
            shutil.copyfile(chemins[0], travail)
    except HTTPException:
        travail.unlink(missing_ok=True)
        raise
    except LLMRateLimitError as e:
        travail.unlink(missing_ok=True)
        raise HTTPException(429, str(e))            # surcharge du fournisseur : transitoire
    except Exception as e:
        travail.unlink(missing_ok=True)
        logger.exception("Constitution impossible (%s · %s)", cycle.nom, niveau.nom)
        raise HTTPException(500, f"Constitution du référentiel impossible : {e}")

    contenu = travail.read_bytes()
    try:
        n_pages, apercu = _apercu(travail)
    except Exception as e:
        travail.unlink(missing_ok=True)
        raise HTTPException(400, f"Lecture du référentiel produit impossible : {e}")
    if par_ia and n_pages > max_pages:
        # L'IA a débordé la longueur demandée. On ne coupe pas un référentiel en deux : on le dit,
        # et l'admin relance — la génération n'est jamais deux fois identique. Le test ne vaut QUE
        # pour elle : un document unique repris tel quel fait la longueur qu'il fait.
        travail.unlink(missing_ok=True)
        raise HTTPException(502, f"Le référentiel produit fait {n_pages} pages (maximum "
                                 f"{max_pages}). Relancez la fusion, ou retirez un document.")
    if len(contenu) > max_mo * 1024 * 1024:
        travail.unlink(missing_ok=True)
        raise HTTPException(400, f"Référentiel produit trop volumineux "
                                 f"({round(len(contenu) / 1024 / 1024, 1):g} Mo, maximum {max_mo:g} Mo).")

    empreinte = hashlib.sha256(contenu).hexdigest()
    deja = _deja_fusionne(db, empreinte)            # AVANT la fiche : sinon elle se verrait
    os.replace(travail, final)
    nom_fixe = _dossier_cle(niveau.nom).lower()
    # Le nom montré à l'admin : celui du document quand il est seul, sinon ce qu'on a fabriqué.
    fichier = (documents[0].fichier_origine if not par_ia
               else f"referentiel.pdf ({len(documents)} documents)")
    source = documents[0].source if len({d.source for d in documents}) == 1 else "mixte"
    ref = Referentiel(niveau_id=niveau.id, nom_fixe=nom_fixe, collection=nom_fixe, filtres=None,
                      fichier=fichier, source=source, empreinte=empreinte)
    db.add(ref)
    try:
        db.flush()
        for d in documents:                         # les morceaux disent de quoi il est fait
            d.referentiel_id = ref.id
        db.commit()
    except Exception as e:
        db.rollback()
        final.unlink(missing_ok=True)
        logger.exception("Constitution : création de la fiche impossible (%s · %s)",
                         cycle.nom, niveau.nom)
        raise HTTPException(500, f"Enregistrement du référentiel impossible : {e}")
    logger.info("Référentiel constitué : %s · %s ← %d document(s) %s, %d pages",
                cycle.nom, niveau.nom, len(documents),
                "fusionnés par l'IA" if par_ia else "repris tel quel", n_pages)
    return {
        "cycle_id": cycle.id, "cycle": cycle.nom,
        "niveau_id": niveau.id, "niveau": niveau.nom,
        "filename": fichier,
        "documents": len(documents),
        # L'écran le dit à l'admin : son référentiel a-t-il été réécrit, ou repris intact ?
        "par_ia": par_ia,
        "taille_ko": round(len(contenu) / 1024),
        "pages": n_pages,
        "apercu": apercu,
        "deja": deja,
    }


# ── La colonne des catalogues — lecture seule ─────────────────────────────────

@router.get("/admin/labo/referentiels/liste", dependencies=[Depends(_require_admin)])
def lister_referentiels(db: Session = Depends(get_db)):
    """Liste de la colonne (get direct, lecture seule) : les référentiels EN PLACE, et les couples
    EN COURS de composition.

    Les couples en cours y sont parce que la base les connaît : depuis qu'un référentiel se
    construit en plusieurs documents, un couple peut avoir des morceaux sans avoir encore de
    fiche. Les taire ferait disparaître de l'écran un travail commencé — l'admin qui s'en va
    perdrait ses dépôts de vue. `en_cours` les distingue ; ils n'ont pas d'`id` de référentiel,
    puisqu'ils n'en ont pas encore."""
    rows = (db.query(Referentiel, Cycle.nom, Niveau.nom, Cycle.id)
              .join(Niveau, Niveau.id == Referentiel.niveau_id)
              .join(Cycle, Cycle.id == Niveau.cycle_id)
              .order_by(Cycle.ordre, Niveau.ordre).all())
    # `complet` = puce de synthèse de la colonne. REFLET lu en base, jamais recopié. Vert = la
    # procédure est ARRIVÉE AU BOUT = `decoupe_valide` (le bouton final « Valider le découpage »).
    refs = [
        {"id": r.id, "cycle": cyc, "cycle_id": cyc_id, "niveau": niv, "niveau_id": r.niveau_id,
         "fichier": r.fichier, "source": r.source, "forcage_motif": r.forcage_motif,
         "complet": bool(r.decoupe_valide), "en_cours": False, "documents": 0}
        for r, cyc, niv, cyc_id in rows
    ]
    # Les couples qui ont des documents mais pas encore de fiche : la composition est commencée.
    encours = (db.query(Niveau.id, Niveau.nom, Cycle.id, Cycle.nom, func.count(ReferentielDocument.id))
                 .join(ReferentielDocument, ReferentielDocument.niveau_id == Niveau.id)
                 .join(Cycle, Cycle.id == Niveau.cycle_id)
                 .filter(ReferentielDocument.referentiel_id.is_(None))
                 .group_by(Niveau.id, Niveau.nom, Cycle.id, Cycle.nom, Cycle.ordre, Niveau.ordre)
                 .order_by(Cycle.ordre, Niveau.ordre).all())
    refs += [
        {"id": None, "cycle": cyc_nom, "cycle_id": cyc_id, "niveau": niv_nom, "niveau_id": niv_id,
         "fichier": None, "source": None, "forcage_motif": None,
         "complet": False, "en_cours": True, "documents": n}
        for niv_id, niv_nom, cyc_id, cyc_nom, n in encours
    ]
    return {"total": len(refs), "referentiels": refs}


# ── Supprimer un référentiel, et la mise à jour d'un référentiel EN SERVICE ───

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


@router.get("/admin/labo/referentiels/supprimer-bilan", dependencies=[Depends(_require_admin)])
def bilan_suppression(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """CE QUI PARTIRA si on supprime le référentiel de ce couple — compté EN BASE, jamais estimé.

    L'admin doit LIRE ce qu'il perd avant de décider, pas le deviner : matières, unités de
    découpe, types d'activité et leurs précisions, et le PDF sur disque. `profs` dit combien de
    professeurs travaillent sur une matière de ce référentiel, et `profs_liste` dit QUI.

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


@router.post("/admin/labo/referentiels/supprimer", dependencies=[Depends(_require_admin)])
def supprimer_referentiel(body: SupprimerRefBody, db: Session = Depends(get_db)):
    """Supprime le référentiel d'un couple — refusé (409) tant qu'un prof est rattaché à l'une de
    ses matières, SAUF geste assumé de l'admin (`bloquer_profs`). Efface la ligne `referentiels`
    + le PDF sur disque. Ses matières, ses unités, ses types d'activité et leurs précisions
    partent avec lui (CASCADE) : rien de tout cela n'existe sans le document qui le nomme.

    Aucun refus « déjà ingéré : n unité(s) » : les unités ne sont pas du travail humain, elles se
    RECALCULENT à partir du PDF. Un tel refus verrouillerait le catalogue — un référentiel mené
    au bout ne pourrait plus jamais être retiré, alors que c'est exactement ce qu'il faut faire
    quand l'Éducation nationale publie une nouvelle version : tout supprimer et refaire la
    procédure. Le seul refus qui reste est celui qui protège du VRAI monde : des profs au travail."""
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
    # profs prévenus d'une mise à jour qui n'a pas eu lieu.
    #
    # LE DOSSIER ENTIER, pas le seul `referentiel.pdf` : les morceaux qui l'ont composé sont là
    # aussi, et leurs lignes viennent de partir avec la fiche (CASCADE). Un fichier que plus
    # aucune ligne ne réclame n'a rien à faire sur le disque.
    fin = _pdf_du_couple(db, body.cycle_id, body.niveau)
    shutil.rmtree(fin.parent, ignore_errors=True)
    for u in bloques:
        _avis_maj(db, u, "referentiel_maj_debut")
    return {"ok": True, "profs_bloques": len(bloques)}


class DebloquerBody(BaseModel):
    cycle_id: int
    niveau: str
    # Pour chaque matière ATTENDUE (son nom d'avant), la matière du NOUVEAU référentiel qui prend
    # sa place. `null` = elle s'en va pour de bon — accepté seulement si plus aucun prof ne
    # l'attend. Une matière attendue absente de ce dictionnaire fait refuser le déblocage.
    correspondances: dict[str, int | None] = {}


@router.get("/admin/labo/referentiels/blocages", dependencies=[Depends(_require_admin)])
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


# ── Le déblocage : REMPLACER la matière, jamais la perdre ────────────────────
#
# Une matière qu'un prof utilise ne disparaît pas : un programme qui change la RENOMME ou la
# FUSIONNE, il ne l'efface presque jamais. C'est la même règle que le Delete refusé sur une donnée
# référencée. Le rebranchement par le nom seul ne savait pas dire ça : nom retrouvé à l'identique,
# ou « matière disparue » — et cette seconde issue était sans retour (la ligne quitte l'état
# `bloque`, aucun second déblocage ne la reprend). L'admin DÉSIGNE donc la remplaçante.

def _lignes_bloquees(db: Session, niveau_id: int):
    from backend.core.models_db import ProfBloqueMaj
    return (db.query(ProfBloqueMaj).filter(ProfBloqueMaj.niveau_id == niveau_id,
                                           ProfBloqueMaj.etat == "bloque").all())


def _attendues(db: Session, niveau_id: int) -> list[dict]:
    """Les matières ATTENDUES sur ce niveau : celles que les lignes en attente mémorisent, avec
    le nombre de professeurs qui les attendent.

    Deux sources dans la même ligne — la matière du PROFIL (`matiere_nom`) et celle du couple de
    TRAVAIL (`travail_matiere_nom`), cette dernière seulement si le couple visait CE niveau : sinon
    elle appartient au référentiel d'un autre niveau, que cette mise à jour n'a pas touché.

    Un même professeur qui attend la même matière des deux côtés ne compte qu'une fois : c'est un
    nombre de gens, pas un nombre de rattachements — le bilan de suppression, lui, comptait les
    rattachements et annonçait « 4 professeur(s) » pour trois noms."""
    par_nom: dict[str, set[int]] = {}
    for l in _lignes_bloquees(db, niveau_id):
        for nom in (l.matiere_nom,
                    l.travail_matiere_nom if l.travail_niveau_id == niveau_id else None):
            if nom:
                par_nom.setdefault(nom, set()).add(l.user_id)
    return [{"nom": nom, "profs": len(qui)} for nom, qui in sorted(par_nom.items())]


def _matieres_retenues(db: Session, niveau_id: int) -> list[Matiere]:
    """Les matières du référentiel EN PLACE sur ce niveau que l'admin a retenues — les seules
    qu'un profil puisse porter, et donc les seules qui peuvent en remplacer une autre."""
    ref = db.query(Referentiel).filter(Referentiel.niveau_id == niveau_id).first()
    if ref is None:
        return []
    return (db.query(Matiere)
              .filter(Matiere.referentiel_id == ref.id,
                      Matiere.validee.is_(True), Matiere.actif.is_(True))
              .order_by(Matiere.ordre, Matiere.nom).all())


def _niveau_du_couple(db: Session, cycle_id: int, niveau: str) -> Niveau:
    niv = (db.query(Niveau).filter(Niveau.nom == (niveau or "").strip(),
                                   Niveau.cycle_id == cycle_id).first())
    if not niv:
        raise HTTPException(404, "Niveau inconnu pour ce cycle.")
    return niv


@router.get("/admin/labo/referentiels/correspondances", dependencies=[Depends(_require_admin)])
def correspondances_du_couple(cycle_id: int, niveau: str, db: Session = Depends(get_db)):
    """Ce que l'admin doit trancher avant de débloquer : à gauche les matières ATTENDUES, à droite
    les matières RETENUES du nouveau référentiel.

    `propose` = la remplaçante évidente, quand le nouveau document porte le MÊME nom : le cas de
    loin le plus fréquent, l'admin n'a alors qu'à valider. `peut_disparaitre` n'est vrai que si
    plus personne n'attend cette matière — on ne propose « elle disparaît vraiment » que là.

    `prete` dit si le déblocage est possible : un référentiel en place, des matières retenues, et
    une correspondance pour chaque attendue. `empechement` dit pourquoi, en français, quand non.
    Lecture seule."""
    niv = _niveau_du_couple(db, cycle_id, niveau)
    retenues = _matieres_retenues(db, niv.id)
    par_nom = {m.nom: m.id for m in retenues}
    attendues = [{**a, "propose": par_nom.get(a["nom"]), "peut_disparaitre": a["profs"] == 0}
                 for a in _attendues(db, niv.id)]
    ref = db.query(Referentiel).filter(Referentiel.niveau_id == niv.id).first()
    if ref is None:
        empechement = ("Aucun référentiel sur ce niveau : déposez le nouveau document et menez la "
                       "procédure jusqu’au bout avant de débloquer.")
    elif not retenues:
        empechement = ("Le nouveau référentiel ne compte aucune matière retenue : cochez les "
                       "matières du document avant de débloquer.")
    else:
        empechement = None
    return {
        "niveau_id": niv.id,
        "attendues": attendues,
        "matieres": [{"id": m.id, "nom": m.nom} for m in retenues],
        "prete": empechement is None,
        "empechement": empechement,
    }


@router.post("/admin/labo/referentiels/debloquer", dependencies=[Depends(_require_admin)])
def debloquer_profs(body: DebloquerBody, db: Session = Depends(get_db)):
    """Geste EXPLICITE de l'admin : la nouvelle procédure est en place, les profs reprennent.
    Jamais déclenché tout seul par la fin de la découpe — l'admin seul sait si c'est prêt.

    Chaque prof est rebranché sur la matière que l'admin a DÉSIGNÉE (`correspondances`), pas sur
    un nom deviné. Trois issues, toutes assumées et nommées : même nom (`rebranche`), nom
    différent (`remplace` — le message dit l'ancienne ET la nouvelle), ou disparition réelle
    (`matiere_disparue`), qui n'est acceptée que si plus aucun prof ne l'attendait.

    REFUSÉ (409) tant que le niveau n'a pas de référentiel avec des matières retenues, ou tant
    qu'une matière attendue n'a pas de correspondance : libérer les profs dans le vide, c'était
    les détacher pour de bon sans que personne l'ait décidé.

    La ligne n'est PAS effacée : elle passe à `a_informer` et attend que le prof ait lu. Les
    e-mails partent après le commit — ils ne s'annulent pas."""
    from backend.core.resolution_couple import matiere_id_du_nom
    from backend.prof.profil import message_de_fin
    niv = _niveau_du_couple(db, body.cycle_id, body.niveau)

    # Les trois refus, dans l'ordre où l'admin les rencontre.
    etat = correspondances_du_couple(body.cycle_id, body.niveau, db)
    if not etat["prete"]:
        raise HTTPException(409, etat["empechement"])
    retenues = {m["id"]: m["nom"] for m in etat["matieres"]}
    choix: dict[str, int | None] = {}
    manquantes, invalides, refusees = [], [], []
    for a in etat["attendues"]:
        if a["nom"] not in body.correspondances:
            manquantes.append(a["nom"])
            continue
        cible = body.correspondances[a["nom"]]
        if cible is None:
            if not a["peut_disparaitre"]:
                refusees.append(f"{a['nom']} ({a['profs']} professeur(s))")
            else:
                choix[a["nom"]] = None
        elif cible not in retenues:
            invalides.append(a["nom"])
        else:
            choix[a["nom"]] = cible
    if manquantes:
        raise HTTPException(409, "Désignez la matière qui remplace : "
                                 + ", ".join(f"« {n} »" for n in manquantes) + ".")
    if refusees:
        raise HTTPException(409, "Ces matières sont utilisées par des professeurs, elles ne "
                                 "peuvent pas disparaître : " + ", ".join(refusees) + ".")
    if invalides:
        raise HTTPException(422, "Matière de remplacement inconnue dans ce référentiel pour : "
                                 + ", ".join(f"« {n} »" for n in invalides) + ".")

    rebranches, remplaces, perdus, avis = [], [], [], []
    for ligne in _lignes_bloquees(db, niv.id):
        u = db.get(User, ligne.user_id)
        if u is None:
            ligne.etat, ligne.debloque_le = "a_informer", func.now()
            continue
        if ligne.matiere_nom:                     # une matière de PROFIL avait été détachée
            cible = choix.get(ligne.matiere_nom)
            if cible is None:
                ligne.resultat, ligne.remplacee_par = "matiere_disparue", None
                perdus.append(u)
            else:
                u.subject_id = cible
                nouveau = retenues[cible]
                ligne.remplacee_par = nouveau
                if nouveau == ligne.matiere_nom:
                    ligne.resultat = "rebranche"
                    rebranches.append(u)
                else:
                    ligne.resultat = "remplace"
                    remplaces.append((u, ligne.matiere_nom, nouveau))
        else:
            # Rien ne partait de son profil : il était rattaché par son seul couple de TRAVAIL.
            # Lui dire « votre matière ne figure plus au programme » serait faux.
            ligne.resultat, ligne.remplacee_par = "rebranche", None
            rebranches.append(u)
        # Le couple de TRAVAIL repart sur la matière désignée quand il visait CE niveau ; ailleurs,
        # son référentiel n'a pas bougé et le nom suffit. Les deux colonnes ensemble ou pas du tout.
        if ligne.travail_matiere_nom and ligne.travail_niveau_id:
            tid = (choix.get(ligne.travail_matiere_nom) if ligne.travail_niveau_id == niv.id
                   else matiere_id_du_nom(db, ligne.travail_matiere_nom, ligne.travail_niveau_id))
            if tid:
                u.travail_matiere_id, u.travail_niveau_id = tid, ligne.travail_niveau_id
        ligne.etat, ligne.debloque_le = "a_informer", func.now()
        avis.append((u, ligne))
    db.commit()

    for u, ligne in avis:                      # après le commit : un e-mail ne se rappelle pas
        if u is not None:
            # {suite} = CE QUI S'AJOUTE à la phrase que le modèle d'e-mail porte déjà (« La mise à
            # jour est terminée… »), c'est-à-dire le second paragraphe du message — et RIEN quand
            # il n'y en a pas. `partition` rend "" dans ce cas, là où `split(…)[-1]` recopiait la
            # phrase entière : le prof rattaché par son seul couple de travail, dont le message
            # tient en une phrase, la lisait deux fois dans son e-mail.
            _, _, suite = message_de_fin(ligne).partition("\n\n")
            _avis_maj(db, u, "referentiel_maj_fin", suite=suite)
    fiche = lambda u: {"prenom": u.prenom, "nom": u.nom, "email": u.email}
    return {"ok": True,
            "rebranches": [fiche(u) for u in rebranches],
            # Les remplacements, nommés des DEUX côtés : l'admin doit relire ce qu'il a décidé.
            "remplaces": [{**fiche(u), "avant": avant, "apres": apres}
                          for u, avant, apres in remplaces],
            "non_rebranches": [fiche(u) for u in perdus]}
