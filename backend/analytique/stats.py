from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.core.database import get_db
from backend.core.models_db import Activite, ActiviteSauvegardee, ConnexionLog, Seance, Sequence, SequenceSauvegardee, ToolUsageLog, User
from backend import auth as auth_lib
from backend.systeme.admin import _require_admin, get_minutes_par_activite

router = APIRouter()


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


@router.get("/stats/matiere")
def get_stats_matiere(
    matiere: str = Query(""),
    niveau: str = Query(""),
    aschool_access: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """Bandeau communauté de l'onglet Activités de Mes contenus. Compté sur la table NEUVE
    `activites` (monde neuf UNIQUEMENT — décision 30/07 : l'ancien monde disparaît, on ne
    l'additionne jamais)."""
    _get_email(aschool_access)

    def _filter(q):
        if matiere:
            q = q.filter(Activite.matiere == matiere)
        if niveau:
            q = q.filter(Activite.niveau == niveau)
        return q

    total = _filter(db.query(func.count(Activite.id))).scalar() or 0

    nb_profs = (
        _filter(db.query(func.count(func.distinct(Activite.user_id))))
        .scalar() or 0
    )

    top_types = (
        _filter(
            db.query(Activite.activite_label, func.count().label("nb"))
        )
        .group_by(Activite.activite_label)
        .order_by(func.count().desc())
        .limit(3)
        .all()
    )

    return {
        "total_plateforme": total,
        "nb_profs": nb_profs,
        "top_types": [{"label": t[0] or "—", "nb": t[1]} for t in top_types],
    }


@router.get("/dashboard")
def get_dashboard(
    aschool_access: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """Accueil du prof, compté sur le monde NEUF (tables `activites` / `seances` — décision
    30/07 : l'ancien monde disparaît, on ne le lit plus). L'écran rouvre les dernières
    créations via /api/mes-contenus (relecture en base, règle 0) : ici on ne renvoie que
    l'identité et de quoi afficher la carte, jamais le contenu complet."""
    email = _get_email(aschool_access)
    uid = db.query(User.id).filter(User.email == email).scalar()

    mes_activites = db.query(func.count(Activite.id)).filter(Activite.user_id == uid).scalar() or 0

    derniere_act = (
        db.query(Activite)
        .filter(Activite.user_id == uid)
        .order_by(Activite.id.desc())
        .first()
    )
    derniere_sea = (
        db.query(Seance)
        .filter(Seance.user_id == uid)
        .order_by(Seance.id.desc())
        .first()
    )

    return {
        "mes_activites": mes_activites,
        "derniere_activite": {
            "id": derniere_act.id,
            "titre": derniere_act.objet or derniere_act.activite_label,
            "matiere": derniere_act.matiere,
            "niveau": derniere_act.niveau,
        } if derniere_act else None,
        "derniere_seance": {
            "id": derniere_sea.id,
            "titre": derniere_sea.titre,
            "matiere": derniere_sea.matiere,
            "niveau": derniere_sea.niveau,
            "duree_minutes": derniere_sea.duree_minutes,
        } if derniere_sea else None,
    }


# ---------------------------------------------------------------------------
# Admin — Vue générale
# ---------------------------------------------------------------------------

@router.get("/admin/stats/general")
def admin_stats_general(
    db: Session = Depends(get_db),
    _=Depends(_require_admin),
):
    total_activites = db.query(func.count(ActiviteSauvegardee.id)).scalar() or 0
    nb_profs = db.query(func.count(func.distinct(ActiviteSauvegardee.user_id))).scalar() or 0
    top_mat = (
        db.query(ActiviteSauvegardee.matiere, func.count().label("nb"))
        .filter(ActiviteSauvegardee.matiere.isnot(None))
        .group_by(ActiviteSauvegardee.matiere)
        .order_by(func.count().desc())
        .first()
    )
    top_type = (
        db.query(ActiviteSauvegardee.activite_label, func.count().label("nb"))
        .group_by(ActiviteSauvegardee.activite_label)
        .order_by(func.count().desc())
        .first()
    )

    seq_total = db.query(func.count(ToolUsageLog.id)).filter(ToolUsageLog.tool == "sequence").scalar() or 0
    seq_profs = db.query(func.count(func.distinct(ToolUsageLog.user_id))).filter(ToolUsageLog.tool == "sequence").scalar() or 0
    opt_total = db.query(func.count(ToolUsageLog.id)).filter(ToolUsageLog.tool == "optimiseur").scalar() or 0
    opt_profs = db.query(func.count(func.distinct(ToolUsageLog.user_id))).filter(ToolUsageLog.tool == "optimiseur").scalar() or 0
    opt_scores = (
        db.query(ToolUsageLog.score_label, func.count().label("nb"))
        .filter(ToolUsageLog.tool == "optimiseur", ToolUsageLog.score_label.isnot(None))
        .group_by(ToolUsageLog.score_label)
        .all()
    )

    total_partages = db.query(func.count(ActiviteSauvegardee.id)).filter(ActiviteSauvegardee.partagee == True).scalar() or 0
    nb_contributeurs = db.query(func.count(func.distinct(ActiviteSauvegardee.user_id))).filter(ActiviteSauvegardee.partagee == True).scalar() or 0

    return {
        "activites": {
            "total": total_activites,
            "nb_profs": nb_profs,
            "top_matiere": top_mat[0] if top_mat else "—",
            "top_matiere_nb": top_mat[1] if top_mat else 0,
            "top_type": top_type[0] if top_type else "—",
            "top_type_nb": top_type[1] if top_type else 0,
        },
        "outils": {
            "sequence": {"total": seq_total, "nb_profs": seq_profs},
            "optimiseur": {
                "total": opt_total,
                "nb_profs": opt_profs,
                "scores": {row[0]: row[1] for row in opt_scores},
            },
        },
        "communaute": {
            "total_partages": total_partages,
            "nb_contributeurs": nb_contributeurs,
        },
    }


# ---------------------------------------------------------------------------
# Admin — Outils (Séquence + Optimiseur)
# ---------------------------------------------------------------------------

@router.get("/admin/tool-usage")
def admin_tool_usage(
    db: Session = Depends(get_db),
    _=Depends(_require_admin),
):
    depuis_30j = datetime.utcnow() - timedelta(days=30)

    def _stats(tool_name: str) -> dict:
        total = db.query(func.count(ToolUsageLog.id)).filter(ToolUsageLog.tool == tool_name).scalar() or 0
        nb_profs = db.query(func.count(func.distinct(ToolUsageLog.user_id))).filter(ToolUsageLog.tool == tool_name).scalar() or 0
        derniers_30j = db.query(func.count(ToolUsageLog.id)).filter(
            ToolUsageLog.tool == tool_name,
            ToolUsageLog.created_at >= depuis_30j,
        ).scalar() or 0
        return {"total": total, "nb_profs": nb_profs, "derniers_30j": derniers_30j}

    seq_stats = _stats("sequence")
    opt_stats = _stats("optimiseur")

    opt_scores = (
        db.query(ToolUsageLog.score_label, func.count().label("nb"))
        .filter(ToolUsageLog.tool == "optimiseur", ToolUsageLog.score_label.isnot(None))
        .group_by(ToolUsageLog.score_label)
        .all()
    )
    opt_stats["scores"] = {row[0]: row[1] for row in opt_scores}

    return {"sequence": seq_stats, "optimiseur": opt_stats}


# ---------------------------------------------------------------------------
# Admin — Communauté
# ---------------------------------------------------------------------------

@router.get("/admin/communaute-stats")
def admin_communaute_stats(
    db: Session = Depends(get_db),
    _=Depends(_require_admin),
):
    total = db.query(func.count(ActiviteSauvegardee.id)).filter(ActiviteSauvegardee.partagee == True).scalar() or 0
    nb_profs = db.query(func.count(func.distinct(ActiviteSauvegardee.user_id))).filter(ActiviteSauvegardee.partagee == True).scalar() or 0

    par_matiere = (
        db.query(ActiviteSauvegardee.matiere, func.count().label("nb"))
        .filter(ActiviteSauvegardee.partagee == True, ActiviteSauvegardee.matiere.isnot(None))
        .group_by(ActiviteSauvegardee.matiere)
        .order_by(func.count().desc())
        .all()
    )
    par_type = (
        db.query(ActiviteSauvegardee.activite_label, func.count().label("nb"))
        .filter(ActiviteSauvegardee.partagee == True)
        .group_by(ActiviteSauvegardee.activite_label)
        .order_by(func.count().desc())
        .limit(10)
        .all()
    )
    contributeurs_raw = (
        db.query(User.email, User.prenom, User.nom, func.count().label("nb"))
        .join(ActiviteSauvegardee, ActiviteSauvegardee.user_id == User.id)
        .filter(ActiviteSauvegardee.partagee == True)
        .group_by(ActiviteSauvegardee.user_id)
        .order_by(func.count().desc())
        .all()
    )

    contributeurs = []
    for email, prenom, nom, nb in contributeurs_raw:
        nom_complet = " ".join(filter(None, [prenom, nom]))
        contributeurs.append({"email": email, "nom": nom_complet or email, "nb": nb})

    return {
        "total_partages": total,
        "nb_contributeurs": nb_profs,
        "par_matiere": [{"matiere": r[0], "nb": r[1]} for r in par_matiere],
        "par_type": [{"label": r[0], "nb": r[1]} for r in par_type],
        "contributeurs": contributeurs,
    }


# ---------------------------------------------------------------------------
# Stats personnelles prof (B1)
# ---------------------------------------------------------------------------

@router.get("/stats/perso")
def stats_perso(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """Mes stats du prof, comptées sur le monde NEUF (activites / seances / sequences —
    décision 30/07). Minutes gagnées par activité : réglage EN BASE
    (stats_minutes_par_activite), plus de « 15 » en dur."""
    email = _get_email(aschool_access)
    uid = db.query(User.id).filter(User.email == email).scalar()

    total_sequences = db.query(func.count(Sequence.id)).filter(Sequence.user_id == uid).scalar() or 0
    total_seances = db.query(func.count(Seance.id)).filter(Seance.user_id == uid).scalar() or 0

    type_row = (
        db.query(Activite.activite_label, func.count().label("nb"))
        .filter(Activite.user_id == uid)
        .group_by(Activite.activite_label)
        .order_by(func.count().desc())
        .first()
    )
    type_favori = type_row[0] if type_row else None
    max_par_type = type_row[1] if type_row else 0
    score_adaptation = 0 if max_par_type == 0 else min(100, int(max_par_type / 3 * 100))

    total_activites = db.query(func.count(Activite.id)).filter(Activite.user_id == uid).scalar() or 0
    heures_gagnees = (total_activites * get_minutes_par_activite(db)) // 60

    debut_mois = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    activites_ce_mois = db.query(func.count(Activite.id)).filter(
        Activite.user_id == uid,
        Activite.created_at >= debut_mois,
    ).scalar() or 0

    return {
        "sequences": total_sequences,
        "seances": total_seances,
        "activites_total": total_activites,
        "activites_ce_mois": activites_ce_mois,
        "type_favori": type_favori,
        "heures_gagnees": heures_gagnees,
        "score_adaptation": score_adaptation,
    }


# ---------------------------------------------------------------------------
# Jauge communauté (B2) — profs
# ---------------------------------------------------------------------------

@router.get("/stats/communaute")
def stats_communaute(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    """Jauge communauté du prof, comptée sur le monde NEUF. Le partage n'existe pas (encore)
    dans le monde neuf : la tuile a quitté l'écran, on n'envoie pas un faux zéro d'ancien
    monde."""
    _get_email(aschool_access)

    today = datetime.utcnow().date()
    depuis_7j = datetime.utcnow() - timedelta(days=7)

    # Comparaison sur l'objet date (jamais str) : « date = varchar » est refusé par
    # PostgreSQL — ce 500 silencieux cachait la section communauté depuis l'origine.
    profs_actifs_aujourd_hui = db.query(func.count(func.distinct(ConnexionLog.user_id))).filter(
        ConnexionLog.action == "login",
        func.date(ConnexionLog.created_at) == today
    ).scalar() or 0

    profs_actifs_semaine = db.query(func.count(func.distinct(ConnexionLog.user_id))).filter(
        ConnexionLog.action == "login",
        ConnexionLog.created_at >= depuis_7j
    ).scalar() or 0

    activites_total = db.query(func.count(Activite.id)).scalar() or 0

    return {
        "profs_actifs_aujourd_hui": profs_actifs_aujourd_hui,
        "profs_actifs_semaine": profs_actifs_semaine,
        "activites_total": activites_total,
    }


# ---------------------------------------------------------------------------
# Vitalité communauté (B2) — admin
# ---------------------------------------------------------------------------

@router.get("/admin/stats/vitalite")
def admin_stats_vitalite(db: Session = Depends(get_db), _=Depends(_require_admin)):
    today = datetime.utcnow().date()
    depuis_7j = datetime.utcnow() - timedelta(days=7)

    profs_actifs_aujourd_hui = db.query(func.count(func.distinct(ConnexionLog.user_id))).filter(
        ConnexionLog.action == "login",
        func.date(ConnexionLog.created_at) == today   # objet date, jamais str (500 sinon)
    ).scalar() or 0

    profs_actifs_semaine = db.query(func.count(func.distinct(ConnexionLog.user_id))).filter(
        ConnexionLog.action == "login",
        ConnexionLog.created_at >= depuis_7j
    ).scalar() or 0

    activites_total = db.query(func.count(ActiviteSauvegardee.id)).scalar() or 0

    partages_total = db.query(func.count(ActiviteSauvegardee.id)).filter(
        ActiviteSauvegardee.partagee == True
    ).scalar() or 0

    sequences_total = db.query(func.count(SequenceSauvegardee.id)).scalar() or 0

    return {
        "profs_actifs_aujourd_hui": profs_actifs_aujourd_hui,
        "profs_actifs_semaine": profs_actifs_semaine,
        "activites_total": activites_total,
        "partages_total": partages_total,
        "sequences_total": sequences_total,
    }
