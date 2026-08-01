"""Lecture du référentiel des programmes pour le frontend (matières + niveaux).

Lecture seule. Source de vérité = les tables cycles/niveaux/referentiels/matieres.
Une matière appartient au RÉFÉRENTIEL d'un niveau : le programme d'un niveau, ce sont les
matières de son référentiel, retenues par l'admin (`validee`) et actives. Ne renvoie que les
niveaux UTILISABLES (au moins une matière) → un niveau sans référentiel, ou dont le référentiel
n'a encore aucune matière validée, n'apparaît pas dans les menus du prof.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models_db import Cycle, LangueLv, Niveau, Matiere, Referentiel, ReferentielChunk
from backend.systeme.admin import _require_admin

router = APIRouter()


def _matiere(m: Matiere) -> dict:
    """La matière telle que les écrans la reçoivent. `demande_langue` accompagne chaque matière :
    c'est LUI qui décide d'afficher le choix de la langue au profil — plus une comparaison de
    libellé côté écran, qu'un renommage de matière casserait en silence."""
    return {"id": m.id, "nom": m.nom, "demande_langue": m.demande_langue}


def _matieres_du_programme(db: Session):
    """(niveau_id, cycle_id, Matiere) pour TOUTE matière réellement au programme : validée par
    l'admin, active, portée par le référentiel d'un niveau. LA lecture de base des menus du prof
    — une seule jointure, faite une fois, réutilisée par les trois vues de /programmes."""
    return (db.query(Referentiel.niveau_id, Niveau.cycle_id, Matiere)
              .join(Matiere, Matiere.referentiel_id == Referentiel.id)
              .join(Niveau, Niveau.id == Referentiel.niveau_id)
              .filter(Matiere.validee.is_(True), Matiere.actif.is_(True))
              .order_by(Matiere.ordre, Matiere.id)
              .all())


def _langues_lv(db: Session) -> list[LangueLv]:
    """Catalogue des langues vivantes, lu EN BASE. Valeurs initiales SEMÉES par migration :
    table vide = erreur explicite, jamais un repli silencieux sur une liste en dur."""
    lignes = (db.query(LangueLv).filter(LangueLv.actif.is_(True))
                .order_by(LangueLv.ordre, LangueLv.id).all())
    if not lignes:
        raise HTTPException(500, "Catalogue « langues vivantes » vide en base (migration non appliquée ?).")
    return lignes


@router.get("/programmes")
def get_programmes(db: Session = Depends(get_db)):
    programme = _matieres_du_programme(db)

    # Toutes les matières au programme, tous référentiels confondus. Deux référentiels peuvent
    # nommer chacun leur « Mathématiques » : ce sont DEUX lignes distinctes, jamais fusionnées.
    matieres = [_matiere(m) for _, _, m in programme]

    niveau_ids_utiles = {niveau_id for niveau_id, _, _ in programme}

    # Matières utilisables PAR CYCLE → menu matière du profil, scopé sur le cycle du niveau choisi.
    cycle_matieres: dict[int, list] = {}
    for _, cycle_id, m in programme:
        cycle_matieres.setdefault(cycle_id, []).append(m)

    # refDisponible = DÉRIVÉ, jamais stocké : un niveau a un référentiel réellement ingéré
    # (au moins 1 chunk). Source unique de vérité = les référentiels eux-mêmes.
    niveaux_ref_disponible = {
        row[0]
        for row in db.query(Referentiel.niveau_id)
                     .join(ReferentielChunk, ReferentielChunk.referentiel_id == Referentiel.id)
                     .distinct().all()
    }

    niveaux_par_cycle = []
    matieres_par_cycle = []
    for c in db.query(Cycle).order_by(Cycle.ordre).all():
        nivs = [
            {"id": n.id, "nom": n.nom, "refDisponible": n.id in niveaux_ref_disponible}
            for n in db.query(Niveau).filter(Niveau.cycle_id == c.id)
                       .order_by(Niveau.ordre).all()
            if n.id in niveau_ids_utiles
        ]
        if nivs:
            niveaux_par_cycle.append({"cycle": c.nom, "niveaux": nivs})

        mats = [_matiere(m) for m in cycle_matieres.get(c.id, [])]
        if mats:
            matieres_par_cycle.append({"cycle": c.nom, "matieres": mats})

    # Matières PAR NIVEAU (scope fin = le programme du diplôme/niveau, via son référentiel).
    # C'est ce que lit le menu matière du profil : un niveau ne propose QUE les matières de SON
    # référentiel (deux diplômes d'un même cycle ont des matières différentes — ex. BTS CIEL ≠
    # Master). Clé = nom du niveau (unique dans le référentiel actuel).
    noms_niveaux = dict(db.query(Niveau.id, Niveau.nom).all())
    par_niveau = {}
    for niveau_id, _, m in programme:
        par_niveau.setdefault(noms_niveaux.get(niveau_id, ""), []).append(_matiere(m))
    matieres_par_niveau = [{"niveau": k, "matieres": v} for k, v in par_niveau.items() if k]

    return {
        "matieres": matieres,
        "niveaux_par_cycle": niveaux_par_cycle,
        "matieres_par_cycle": matieres_par_cycle,
        "matieres_par_niveau": matieres_par_niveau,
        # Les langues offertes au prof dont la matière porte une langue : catalogue EN BASE
        # (`langues_lv`), plus de liste écrite dans l'écran du profil.
        "langues_lv": [l.label for l in _langues_lv(db)],
    }


@router.get("/matieres")
def get_matieres(niveau_id: int | None = None, db: Session = Depends(get_db)):
    """Les matières au programme, LUES EN BASE. Deux questions, deux réponses :

    • `?niveau_id=` → les matières du RÉFÉRENTIEL de ce niveau (le vrai programme d'un diplôme).
      Chaque ligne porte son `id` : dans ce cadre, une matière est identifiée sans ambiguïté.
    • sans argument → les NOMS distincts de toutes les matières au programme, tous référentiels
      confondus. C'est ce que lisent les trois filtres admin (Analytique, Profils, Communication),
      qui trient de l'historique rangé par NOM. Pas d'`id` ici : deux référentiels peuvent nommer
      chacun leur « Mathématiques », le nom seul ne désigne donc plus une ligne.

    Dans les deux cas : matières retenues par l'admin (`validee`) et actives, jamais une
    proposition de la détection. Liste vide si le niveau n'a pas de référentiel."""
    q = (db.query(Matiere)
           .join(Referentiel, Referentiel.id == Matiere.referentiel_id)
           .filter(Matiere.validee.is_(True), Matiere.actif.is_(True)))
    if niveau_id is not None:
        rows = q.filter(Referentiel.niveau_id == niveau_id).order_by(Matiere.ordre, Matiere.id).all()
        return [_matiere(m) for m in rows]
    noms = [nom for (nom,) in
            q.with_entities(Matiere.nom).distinct().order_by(Matiere.nom).all()]
    return [{"nom": n} for n in noms]


# RETIRÉ le 31/07 (ménage) : GET /referentiel-disponible répondait « ce couple a-t-il un
# référentiel ? ». Personne ne l'appelait : la réponse voyage déjà dans /programmes, où chaque
# niveau porte son `refDisponible` — l'écran l'a par la même lecture que ses menus, sans second
# appel. Trois vérifications faites : aucun import, aucun appelant (hors ses propres tests, partis
# avec lui), aucun seed en migration.


@router.get("/programmes/couverture")
def get_couverture(db: Session = Depends(get_db)):
    """Vitrine « Programmes couverts » (page À propos du prof) : TOUS les cycles et niveaux qui
    existent en base, Y COMPRIS ceux sans matière encore rattachée (BTS, BUT, Master, Doctorat…),
    pour montrer l'ampleur de la couverture. `refDisponible` = DÉRIVÉ (le niveau a un référentiel
    réellement ingéré, ≥1 chunk), jamais stocké — source unique = les référentiels. Lecture seule,
    zéro copie. À NE PAS confondre avec /programmes, qui ne renvoie QUE les niveaux utilisables par
    un prof (filtrés sur la matière) : ici on ne filtre pas, c'est une vitrine, pas un menu."""
    dispo = {
        row[0]
        for row in db.query(Referentiel.niveau_id)
                     .join(ReferentielChunk, ReferentielChunk.referentiel_id == Referentiel.id)
                     .distinct().all()
    }
    cycles = []
    for c in db.query(Cycle).order_by(Cycle.ordre).all():
        nivs = [
            {"id": n.id, "nom": n.nom, "refDisponible": n.id in dispo}
            for n in db.query(Niveau).filter(Niveau.cycle_id == c.id)
                       .order_by(Niveau.ordre).all()
        ]
        if nivs:   # un cycle sans aucun niveau n'a rien à montrer
            cycles.append({"cycle": c.nom, "niveaux": nivs})
    return {"cycles": cycles}


# ───────────────────────────────────────────────────────────────────────────
# Admin — édition des programmes (garde admin, JAMAIS de DELETE sur une
# entrée de référence : on bascule `actif`, l'historique reste valide).
# ───────────────────────────────────────────────────────────────────────────

@router.get("/admin/programmes", dependencies=[Depends(_require_admin)])
def admin_programmes(db: Session = Depends(get_db)):
    """Arbre COMPLET pour l'écran admin : tous les cycles (même sans niveau), tous leurs niveaux,
    et pour chaque niveau les matières de SON référentiel — inactives et non validées INCLUSES
    (l'admin voit ce que le prof ne voit pas encore, c'est là qu'il coche).

    Le catalogue global de matières et la liste des paires ont disparu de cette réponse : ils
    n'existent plus. Un niveau sans référentiel n'a aucune matière et le dit (`referentiel_id`
    à null) — l'écran affiche « aucun référentiel déposé » au lieu d'une grille de cases vides."""
    refs = {r.niveau_id: r.id for r in db.query(Referentiel).all()}
    mat_par_ref: dict[int, list] = {}
    for m in db.query(Matiere).order_by(Matiere.ordre, Matiere.id).all():
        mat_par_ref.setdefault(m.referentiel_id, []).append(m)

    cycles = []
    for c in db.query(Cycle).order_by(Cycle.ordre).all():
        niveaux = []
        for n in db.query(Niveau).filter(Niveau.cycle_id == c.id).order_by(Niveau.ordre).all():
            ref_id = refs.get(n.id)
            niveaux.append({
                "id": n.id, "nom": n.nom, "ordre": n.ordre,
                "referentiel_id": ref_id,
                "matieres": [
                    {"id": m.id, "nom": m.nom, "ordre": m.ordre,
                     "actif": m.actif, "validee": m.validee, "demande_langue": m.demande_langue}
                    for m in mat_par_ref.get(ref_id, [])
                ],
            })
        cycles.append({"id": c.id, "nom": c.nom, "ordre": c.ordre, "niveaux": niveaux})
    return {"cycles": cycles}


# RETIRÉ (chantier Matière) : PATCH /admin/programmes/paire basculait une paire matière×niveau.
# La paire n'existe plus — une matière appartient à un référentiel, donc à un niveau, et rien
# d'autre ne les relie. Le geste équivalent est « activer/désactiver une matière du référentiel » :
# PATCH /admin/matieres/actif, juste en dessous, qui existait déjà.


# ── Création de cycle / niveau — la SEULE place où l'on crée ces entrées (boutons
# « + Cycle / + Niveau » de la page Programmes & contenu). Le dépôt de référentiel ne
# crée JAMAIS de niveau : il ne propose que l'existant, en cascade cycle → niveau.

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


class CreerNiveauBody(BaseModel):
    cycle_id: int
    nom: str


@router.post("/admin/niveaux", dependencies=[Depends(_require_admin)])
def creer_niveau(body: CreerNiveauBody, db: Session = Depends(get_db)):
    """Crée un niveau dans un cycle (Create encadré : nom non vide, unique DANS le cycle).
    `ordre` = max+1 du cycle."""
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


# ── La maison des matières : créer DANS un référentiel + activer/désactiver. Une matière naît
# soit ici (l'admin l'ajoute à la main au référentiel), soit à la détection du dépôt (proposée,
# `validee=false`). Create encadré, bascule `actif`, JAMAIS de DELETE (l'historique reste).

class CreerMatiereBody(BaseModel):
    referentiel_id: int
    nom: str


@router.post("/admin/matieres", dependencies=[Depends(_require_admin)])
def creer_matiere(body: CreerMatiereBody, db: Session = Depends(get_db)):
    """Crée une matière DANS un référentiel (Create encadré : référentiel existant, nom non vide,
    borné par la colonne, unique DANS CE référentiel, insensible à la casse). `ordre` = max+1 du
    référentiel, active et VALIDÉE d'emblée — l'admin qui la saisit la retient par ce geste même.
    Une matière déjà là mais inactive ne se recrée pas : on la réactive par PATCH
    /admin/matieres/actif. Le même nom dans un AUTRE référentiel est normal, et accepté."""
    nom = (body.nom or "").strip()
    if not nom:
        raise HTTPException(400, "Le nom de la matière est requis.")
    ref = db.get(Referentiel, body.referentiel_id)
    if not ref:
        raise HTTPException(404, "Référentiel inconnu : déposez d'abord son document.")
    max_nom = Matiere.__table__.c.nom.type.length
    if len(nom) > max_nom:
        raise HTTPException(422, f"Le nom de matière est trop long ({len(nom)} caractères, "
                                 f"maximum {max_nom}). Raccourcissez-le.")
    if (db.query(Matiere)
          .filter(Matiere.referentiel_id == ref.id, func.lower(Matiere.nom) == nom.lower())
          .first()):
        raise HTTPException(409, f"La matière « {nom} » existe déjà dans ce référentiel.")
    maxo = (db.query(func.max(Matiere.ordre))
              .filter(Matiere.referentiel_id == ref.id).scalar())
    m = Matiere(referentiel_id=ref.id, nom=nom, ordre=(maxo or 0) + 1, actif=True, validee=True)
    db.add(m); db.commit(); db.refresh(m)
    return {"id": m.id, "nom": m.nom, "ordre": m.ordre, "actif": m.actif, "validee": m.validee,
            "referentiel_id": m.referentiel_id}


class MatiereActifBody(BaseModel):
    matiere_id: int
    actif: bool


@router.patch("/admin/matieres/actif", dependencies=[Depends(_require_admin)])
def admin_toggle_matiere(body: MatiereActifBody, db: Session = Depends(get_db)):
    """Active/désactive une matière de son référentiel — JAMAIS de DELETE. Désactivée : elle
    disparaît des menus prof (les GET publics filtrent sur `actif`) mais reste sur son
    référentiel avec son historique ; la réactiver la remet telle quelle."""
    m = db.get(Matiere, body.matiere_id)
    if not m:
        raise HTTPException(404, "Matière inconnue.")
    m.actif = body.actif
    db.commit()
    return {"id": m.id, "nom": m.nom, "actif": m.actif}


class MatiereLangueBody(BaseModel):
    matiere_id: int
    demande_langue: bool


@router.patch("/admin/matieres/demande-langue", dependencies=[Depends(_require_admin)])
def admin_matiere_demande_langue(body: MatiereLangueBody, db: Session = Depends(get_db)):
    """« Cette matière porte une langue » — l'indicateur qui décide si le prof choisit une langue
    à son profil et si la génération l'injecte dans le prompt. Il vit sur la ligne matière : la
    migration l'a posé au mieux sur les intitulés connus, l'admin corrige ici (une matière créée
    au dépôt d'un référentiel arrive forcément à false)."""
    m = db.get(Matiere, body.matiere_id)
    if not m:
        raise HTTPException(404, "Matière inconnue.")
    m.demande_langue = body.demande_langue
    db.commit()
    return {"id": m.id, "nom": m.nom, "demande_langue": m.demande_langue}
