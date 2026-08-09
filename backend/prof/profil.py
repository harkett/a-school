import unicodedata
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Cookie, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.securite import comptes
from backend.core.database import get_db
from backend.core.models_db import CahierProf, Cycle, Matiere, Niveau, Referentiel, User
from backend.core.nommage import dossier_cle as _dossier_cle
from backend.systeme.admin import _reglage_entier
from backend.core.resolution_couple import matiere_id_du_nom, matiere_nom_de_id, niveau_id_du_nom, niveau_nom_de_id

router = APIRouter()

# Dossier des référentiels déposés — même convention de rangement que le dépôt admin
# (REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf). La règle de nommage vient de
# `backend.core.nommage` : module neutre (aucune dépendance), donc l'importer ne couple
# toujours pas le routeur du profil au module RAG — et la règle n'a plus qu'une seule source.
_ROOT = Path(__file__).resolve().parents[2]
REFERENTIELS_DIR = _ROOT / "REFERENTIELS"
# Cahier des charges depose par le PROF (1 PDF/prof) : hors depot (data/ est gitignore), persiste
# sur le serveur. Nom de disque fixe (cahier.pdf) par dossier prop, comme le referentiel admin.
UPLOADS_CAHIERS_DIR = _ROOT / "data" / "uploads" / "cahiers"


# ── Mise à jour d'un référentiel : ce qui a été RETIRÉ le 07/08/2026 ─────────────────────────
#
# Il existait ici un mécanisme de « blocage » : quand l'admin supprimait le référentiel d'un
# niveau, le serveur détachait lui-même la matière des profs concernés (`users.subject_id` remis
# à NULL) pour que la suppression passe, mémorisait le nom perdu dans `profs_bloques_maj`, et
# refusait toute génération tant que la ligne existait.
#
# POURQUOI IL EST PARTI. La base refusait DÉJÀ la suppression : `fk_users_subject_id` est en
# NO ACTION, une matière portée par un prof ne peut pas disparaître. Le code contournait sa
# propre garde d'intégrité pour recréer, en Python, une protection que PostgreSQL assurait
# gratuitement — et cette protection-là, elle, ne se levait pas toute seule. Une ligne posée le
# 03/08/2026 par une suppression qui n'a jamais abouti a laissé un compte incapable de générer
# pendant quatre jours, avec un référentiel intact et une matière valide.
#
# CE QUI TIENT LA PLACE. Rien de neuf : le refus 409 « n professeur(s) travaillent sur une
# matière de ce référentiel » reste la règle, à l'admin de changer leur matière d'abord. Un prof
# sans matière est un profil incomplet — l'écran l'envoie la choisir, comme pour tout compte neuf.


def couple_de_travail(db: Session, user: User) -> tuple[str | None, str | None, bool]:
    """Le couple sur lequel le prof TRAVAILLE, résolu depuis la base — LA seule règle,
    à UN seul endroit : le couple de travail s'il est posé (les deux clés non NULL),
    sinon le couple du profil. Renvoie (matiere, niveau, ajuste) ; ajuste=True quand le
    prof travaille hors de son profil. Le nom se relit par get sur `matieres`/`niveaux`
    (zéro copie). Lu par /auth/me ET par les actions (génération, idée, exemple).

    Ne refuse RIEN : cette fonction résout un couple, elle ne juge pas le droit de travailler.
    Elle a porté un refus 409 « mise à jour en cours » jusqu'au 07/08/2026 — voir le bloc retiré
    plus haut."""
    if user.travail_matiere_id and user.travail_niveau_id:
        return matiere_nom_de_id(db, user.travail_matiere_id), niveau_nom_de_id(db, user.travail_niveau_id), True
    return matiere_nom_de_id(db, user.subject_id), niveau_nom_de_id(db, user.niveau_id), False


def matiere_demande_langue(db: Session, user: User) -> bool:
    """La matière du COUPLE DE TRAVAIL porte-t-elle une langue (→ le prof choisit sa langue au
    profil, la génération l'injecte dans le prompt) ? Lu sur l'INDICATEUR `matieres.demande_langue`,
    jamais sur le libellé : la matière est déjà rangée par clé (`subject_id`), il n'y a aucune
    raison de la reconnaître à son nom — un nom, ça se renomme."""
    matiere_id = user.travail_matiere_id if (user.travail_matiere_id and user.travail_niveau_id) else user.subject_id
    if not matiere_id:
        return False
    return bool(db.query(Matiere.demande_langue).filter(Matiere.id == matiere_id).scalar())


def couple_est_au_programme(db: Session, matiere: str, niveau: str) -> bool:
    """Cette matière est-elle au programme de ce niveau ? = le référentiel du niveau la nomme-t-il,
    retenue par l'admin et active ? C'est EXACTEMENT la question que résout `matiere_id_du_nom` :
    le contrôle et la résolution disent donc la même chose, à un seul endroit. Un niveau sans
    référentiel n'a aucune matière — le couple est refusé, et c'est juste.

    PUBLIQUE depuis le 02/08/2026 (elle s'appelait `_couple_est_au_programme`). Elle ne servait
    qu'À L'ÉCRITURE, pour refuser un couple qu'on pose. Elle sert désormais aussi À LA LECTURE :
    /auth/me s'en sert pour dire si le profil DÉJÀ ENREGISTRÉ tient toujours debout — un profil
    accepté hier peut avoir cessé d'être au programme depuis (référentiel remplacé, matière
    retirée, niveau renommé), et rien ne le relisait.
    Le `_` partait : elle sort de son module. La règle, elle, reste ici et nulle part ailleurs."""
    return matiere_id_du_nom(db, matiere, niveau_id_du_nom(db, niveau)) is not None


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = comptes.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


class ProfileBody(BaseModel):
    prenom: str = ""
    nom: str = ""
    subject: str = ""
    niveau: str = ""
    langue_lv: str = ""
    mobile: str = ""


@router.get("/user/profile")
def get_profile(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    return {
        "email":     user.email,
        "prenom":    user.prenom    or "",
        "nom":       user.nom       or "",
        "subject":   matiere_nom_de_id(db, user.subject_id) or "",
        "niveau":    niveau_nom_de_id(db, user.niveau_id) or "",
        "langue_lv": user.langue_lv or "",
        "mobile":    user.mobile    or "",
    }


@router.patch("/user/profile")
def update_profile(body: ProfileBody, aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    # Contrôle métier AVANT d'écrire — même règle que « Changer niveau et/ou matière » : la
    # matière doit être au programme du niveau, le front seul ne suffit pas. Un profil encore
    # VIDE (ni matière ni niveau) reste enregistrable tel quel : c'est l'état normal d'un compte
    # qui vient de naître. Une matière SANS niveau, en revanche, ne se range nulle part — elle
    # n'existe que dans le référentiel d'un niveau : on le dit, plutôt que de l'effacer en silence.
    matiere, niveau = (body.subject or "").strip(), (body.niveau or "").strip()
    if matiere and not niveau:
        raise HTTPException(400, "Choisissez d'abord votre niveau : les matières proposées dépendent de son programme.")
    if matiere and niveau and not couple_est_au_programme(db, matiere, niveau):
        raise HTTPException(400, "Cette matière n'est pas enseignée à ce niveau dans les programmes. Choisissez une matière proposée pour ce niveau.")
    niveau_id       = niveau_id_du_nom(db, niveau or None)
    user.prenom     = body.prenom    or None
    user.nom        = body.nom       or None
    # Matière rangée UNIQUEMENT par clé (put) : elle se résout DANS le référentiel du niveau
    # choisi — le nom seul ne désigne plus rien (plusieurs « Mathématiques » coexistent en base).
    user.subject_id = matiere_id_du_nom(db, matiere or None, niveau_id)
    user.niveau_id  = niveau_id
    user.langue_lv  = body.langue_lv or None
    user.mobile     = body.mobile    or None
    db.commit()
    return {"status": "ok"}


class CoupleTravailBody(BaseModel):
    matiere: str
    niveau: str


@router.put("/user/couple-travail")
def put_couple_travail(body: CoupleTravailBody, aschool_access: str = Cookie(default=None),
                       db: Session = Depends(get_db)):
    """Valider de « Changer niveau et/ou matière » = PUT : le couple de travail s'écrit EN BASE
    (il survit au rechargement de la page et à un changement d'appareil — c'est LUI que le
    serveur lit pour générer). Contrôle métier avant d'écrire : la paire doit exister au
    programme officiel. Choisir son propre couple de profil = revenir au profil (efface
    l'écart, on ne stocke jamais une copie du profil)."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    matiere, niveau = body.matiere.strip(), body.niveau.strip()
    if not matiere or not niveau:
        raise HTTPException(400, "Choisissez un niveau et une matière avant de valider.")
    if not couple_est_au_programme(db, matiere, niveau):
        raise HTTPException(400, "Cette matière n'est pas enseignée à ce niveau dans les programmes. Choisissez une matière proposée pour ce niveau.")
    profil_matiere = matiere_nom_de_id(db, user.subject_id) or ""
    profil_niveau = niveau_nom_de_id(db, user.niveau_id) or ""
    if matiere == profil_matiere and niveau == profil_niveau:
        user.travail_matiere_id = None   # même couple que le profil → aucun écart à stocker
        user.travail_niveau_id = None
    else:
        # Couple de travail rangé UNIQUEMENT par clé (put), matière résolue DANS le référentiel
        # du niveau visé.
        travail_niveau_id = niveau_id_du_nom(db, niveau)
        user.travail_matiere_id = matiere_id_du_nom(db, matiere, travail_niveau_id)
        user.travail_niveau_id = travail_niveau_id
    db.commit()
    # Relecture APRÈS le commit, pour construire la réponse.
    tm, tn, ajuste = couple_de_travail(db, user)
    return {"status": "ok", "travail_matiere": tm, "travail_niveau": tn, "couple_ajuste": ajuste}


@router.put("/user/guide-creer-vu")
def put_guide_creer_vu(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """La visite guidée de l'écran Créer vient d'être terminée (ou passée) : on le note EN
    BASE pour ne plus la lancer automatiquement — sur cet appareil comme sur les autres.
    Idempotent : re-noter un guide déjà vu ne change rien."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    user.guide_creer_vu = True
    db.commit()
    return {"status": "ok", "guide_creer_vu": True}


@router.delete("/user/couple-travail")
def delete_couple_travail(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """« Revenir à mon profil » = effacement de l'écart : le couple de travail redevient
    celui du profil (les deux colonnes repassent à NULL). Aucun contrôle à faire : on
    supprime une donnée que seul son propriétaire référence."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    user.travail_matiere_id = None
    user.travail_niveau_id = None
    db.commit()
    # Relecture APRÈS le commit, pour construire la réponse.
    tm, tn, ajuste = couple_de_travail(db, user)
    return {"status": "ok", "travail_matiere": tm, "travail_niveau": tn, "couple_ajuste": ajuste}


# ── Programme officiel du prof : voir, depuis son profil, le référentiel déposé par l'admin ──
#    LECTURE SEULE (le prof consulte, il n'écrit rien → aucun Valider/Annuler). Zéro nouvelle
#    donnée : le nom EXACT déposé vit déjà en base (referentiels.fichier) et le PDF sur disque.

def _referentiel_du_profil(db: Session, user: User) -> Referentiel | None:
    """Le référentiel officiel du NIVEAU de profil du prof, lu PAR SA CLÉ (users.niveau_id →
    referentiels.niveau_id). La clé lève toute ambiguïté — un niveau = une ligne, l'unicité de
    la base le garantit — donc plus de correspondance par nom ni de garde « len == 1 ».
    None si le prof n'a pas de niveau (niveau_id NULL) ou si ce niveau n'a pas de référentiel :
    la carte du profil affiche alors « indisponible »."""
    if not user.niveau_id:
        return None
    return db.query(Referentiel).filter(Referentiel.niveau_id == user.niveau_id).first()


@router.get("/user/referentiel")
def get_mon_referentiel(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """Le programme officiel du niveau du prof : { disponible, fichier }. `fichier` = le NOM EXACT
    du document déposé par l'admin (colonne referentiels.fichier, get — pas le nom de disque figé
    « referentiel.pdf »). disponible=false s'il n'y a pas encore de référentiel pour son niveau."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    ref = _referentiel_du_profil(db, user)
    if ref is None:
        return {"disponible": False, "fichier": None}
    return {"disponible": True, "fichier": ref.fichier or "referentiel.pdf"}


# RETIRÉ le 31/07 (ménage) : GET /user/referentiel/texte servait le programme officiel en texte
# épuré. Aucun écran ne l'appelait — le prof lit son programme dans le PDF d'origine
# (/user/referentiel/pdf, celui-là bien branché). Trois vérifications faites avant de le retirer :
# aucun import, aucun appelant (hors ses propres tests, partis avec lui), aucun seed en migration.
# `referentiels.texte_epure` reste évidemment en base : c'est LUI que la génération lit.


@router.get("/user/referentiel/pdf")
def get_mon_referentiel_pdf(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """Le PDF D'ORIGINE du niveau du prof — le fichier déposé par l'admin, servi TEL QUEL et affiché
    dans la visionneuse du navigateur (inline). get pur, aucune écriture. VERROUILLÉ sur SON niveau
    (users.niveau_id, comme les deux endpoints ci-dessus). Chemin sur disque : même convention que le
    dépôt admin — REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf. Le nom montré au navigateur est le
    VRAI nom déposé (referentiels.fichier), pas le nom de disque figé. 404 si rien à servir."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    ref = _referentiel_du_profil(db, user)
    if ref is None:
        raise HTTPException(404, "Aucun programme officiel n'est disponible pour votre niveau.")
    niveau = db.get(Niveau, ref.niveau_id)
    cycle = db.get(Cycle, niveau.cycle_id) if niveau else None
    if not niveau or not cycle:
        raise HTTPException(404, "Aucun programme officiel n'est disponible pour votre niveau.")
    pdf = REFERENTIELS_DIR / _dossier_cle(cycle.nom) / _dossier_cle(niveau.nom) / "referentiel.pdf"
    if not pdf.exists():
        raise HTTPException(404, "Aucun programme officiel n'est disponible pour votre niveau.")
    # Nom affiché = le vrai nom déposé ; en-tête sûr même avec accents (ASCII + filename* RFC 5987).
    nom = ref.fichier or "referentiel.pdf"
    ascii_nom = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode() or "referentiel.pdf"
    cd = f"inline; filename=\"{ascii_nom}\"; filename*=UTF-8''{quote(nom)}"
    return FileResponse(str(pdf), media_type="application/pdf", headers={"Content-Disposition": cd})


# ── Cahier des charges du PROF — document interne à son école/structure, déposé par LUI ──
#    (1 PDF par prof ; re-déposer remplace). Le pourquoi et l'extraction du texte viendront plus
#    tard. Écran = fenêtre sur la table cahiers_prof : get (état/PDF), put (dépôt). Auth inchangée.

def _cahier_du_profil(db: Session, user: User) -> CahierProf | None:
    return db.query(CahierProf).filter(CahierProf.user_id == user.id).first()


def texte_cahier_du_profil(db: Session, user: User) -> str:
    """Le TEXTE de travail du cahier des charges du prof (cahiers_prof.texte_epure), lu EN BASE
    au moment de générer (get, zéro copie). Chaîne VIDE s'il n'a pas déposé de cahier (ou texte
    non exploitable) : la génération se fait alors sans cahier, à l'identique. Lu par la génération
    (et, plus tard, exemple / idée) pour appliquer les règles de l'école par-dessus le programme."""
    cahier = _cahier_du_profil(db, user)
    return (cahier.texte_epure or "").strip() if cahier else ""


def _cahier_pdf_path(user: User) -> Path:
    return UPLOADS_CAHIERS_DIR / str(user.id) / "cahier.pdf"


@router.get("/user/cahier")
def get_mon_cahier(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """État du cahier des charges du prof : { present, fichier }. get pur, aucune écriture."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    cahier = _cahier_du_profil(db, user)
    if cahier is None:
        return {"present": False, "fichier": None}
    return {"present": True, "fichier": cahier.fichier}


@router.post("/user/cahier")
async def deposer_mon_cahier(file: UploadFile = File(...), aschool_access: str = Cookie(default=None),
                             db: Session = Depends(get_db)):
    """Dépôt du cahier des charges du prof (PDF) — CREATE si absent, UPDATE sinon (re-déposer
    remplace : 1 par prof). Le PDF est écrit sur disque (nom fixe cahier.pdf, dossier du prof) et
    la ligne cahiers_prof porte le nom d'origine. Messages d'erreur humains (règle des 2 publics)."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    nom = (file.filename or "cahier.pdf").strip()
    if not nom.lower().endswith(".pdf"):
        raise HTTPException(422, "Le fichier doit être un PDF (extension .pdf).")
    content = await file.read()
    if not content:
        raise HTTPException(422, "Le fichier est vide.")
    if not content[:4] == b"%PDF":
        raise HTTPException(422, "Ce fichier n'est pas un vrai PDF.")
    # Plafond de taille du cahier des charges : réglage EN BASE (semé par migration), plus un
    # nombre écrit ici. Le prof ne voit ce plafond que dans ce message — d'où le libellé calculé.
    max_mo = _reglage_entier(db, "cahier_max_mo", 1)
    if len(content) > max_mo * 1024 * 1024:
        raise HTTPException(413, f"Le PDF dépasse {max_mo} Mo — merci d'en déposer un plus léger.")
    dossier = _cahier_pdf_path(user).parent
    dossier.mkdir(parents=True, exist_ok=True)
    _cahier_pdf_path(user).write_bytes(content)
    # LE texte de travail du cahier : extrait UNE fois ici (porte unique rag.extraction, comme le
    # référentiel officiel) et figé en base — c'est LUI que la génération lira (get, zéro copie).
    try:
        from backend.rag.extraction import extraire_texte   # import paresseux (pdfplumber)
        texte_epure = extraire_texte(_cahier_pdf_path(user))
    except Exception:
        raise HTTPException(400, "Impossible de lire le contenu de ce PDF — merci d'en déposer un autre.")
    cahier = _cahier_du_profil(db, user)
    if cahier is None:
        db.add(CahierProf(user_id=user.id, fichier=nom, texte_epure=texte_epure))   # CREATE (aucun cahier encore)
    else:
        cahier.fichier = nom                               # UPDATE (re-dépôt = remplacement)
        cahier.texte_epure = texte_epure                   # le NOUVEAU PDF impose SON texte de travail
    db.commit()
    return {"present": True, "fichier": nom}


@router.get("/user/cahier/pdf")
def get_mon_cahier_pdf(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """Sert le cahier des charges déposé par le prof, affiché dans la visionneuse du navigateur
    (inline), avec le vrai nom d'origine. get pur, verrouillé sur SON dépôt. 404 si rien."""
    email = _get_email(aschool_access)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    cahier = _cahier_du_profil(db, user)
    pdf = _cahier_pdf_path(user)
    if cahier is None or not pdf.exists():
        raise HTTPException(404, "Aucun cahier des charges déposé.")
    nom = cahier.fichier or "cahier.pdf"
    ascii_nom = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode() or "cahier.pdf"
    cd = f"inline; filename=\"{ascii_nom}\"; filename*=UTF-8''{quote(nom)}"
    return FileResponse(str(pdf), media_type="application/pdf", headers={"Content-Disposition": cd})
