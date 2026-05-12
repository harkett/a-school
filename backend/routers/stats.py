from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models_db import ActiviteSauvegardee, ToolUsageLog, User
from backend import auth as auth_lib
from backend.routers.admin import _require_admin

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
    _get_email(aschool_access)

    def _filter(q):
        if matiere:
            q = q.filter(ActiviteSauvegardee.matiere == matiere)
        if niveau:
            q = q.filter(ActiviteSauvegardee.niveau == niveau)
        return q

    total = _filter(db.query(func.count(ActiviteSauvegardee.id))).scalar() or 0

    nb_profs = (
        _filter(db.query(func.count(func.distinct(ActiviteSauvegardee.user_email))))
        .scalar() or 0
    )

    top_types = (
        _filter(
            db.query(ActiviteSauvegardee.activite_label, func.count().label("nb"))
        )
        .group_by(ActiviteSauvegardee.activite_label)
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
    email = _get_email(aschool_access)

    mes_activites = db.query(func.count(ActiviteSauvegardee.id)).filter(
        ActiviteSauvegardee.user_email == email
    ).scalar() or 0

    mes_partages = db.query(func.count(ActiviteSauvegardee.id)).filter(
        ActiviteSauvegardee.user_email == email,
        ActiviteSauvegardee.partagee == True,
    ).scalar() or 0

    communaute_total = db.query(func.count(ActiviteSauvegardee.id)).scalar() or 0
    communaute_profs = db.query(func.count(func.distinct(ActiviteSauvegardee.user_email))).scalar() or 0

    recentes = (
        db.query(ActiviteSauvegardee)
        .filter(ActiviteSauvegardee.user_email == email)
        .order_by(ActiviteSauvegardee.id.desc())
        .limit(3)
        .all()
    )

    return {
        "mes_activites": mes_activites,
        "mes_partages": mes_partages,
        "communaute_total": communaute_total,
        "communaute_profs": communaute_profs,
        "recentes": [
            {
                "id": a.id,
                "activite_key": a.activite_key,
                "activite_label": a.activite_label,
                "matiere": a.matiere,
                "niveau": a.niveau,
                "sous_type": a.sous_type,
                "nb": a.nb,
                "avec_correction": a.avec_correction,
                "objet": a.objet,
                "texte_source": a.texte_source,
                "resultat": a.resultat,
            }
            for a in recentes
        ],
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
    nb_profs = db.query(func.count(func.distinct(ActiviteSauvegardee.user_email))).scalar() or 0
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
    seq_profs = db.query(func.count(func.distinct(ToolUsageLog.user_email))).filter(ToolUsageLog.tool == "sequence").scalar() or 0
    opt_total = db.query(func.count(ToolUsageLog.id)).filter(ToolUsageLog.tool == "optimiseur").scalar() or 0
    opt_profs = db.query(func.count(func.distinct(ToolUsageLog.user_email))).filter(ToolUsageLog.tool == "optimiseur").scalar() or 0
    opt_scores = (
        db.query(ToolUsageLog.score_label, func.count().label("nb"))
        .filter(ToolUsageLog.tool == "optimiseur", ToolUsageLog.score_label.isnot(None))
        .group_by(ToolUsageLog.score_label)
        .all()
    )

    total_partages = db.query(func.count(ActiviteSauvegardee.id)).filter(ActiviteSauvegardee.partagee == True).scalar() or 0
    nb_contributeurs = db.query(func.count(func.distinct(ActiviteSauvegardee.user_email))).filter(ActiviteSauvegardee.partagee == True).scalar() or 0

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
        nb_profs = db.query(func.count(func.distinct(ToolUsageLog.user_email))).filter(ToolUsageLog.tool == tool_name).scalar() or 0
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
    nb_profs = db.query(func.count(func.distinct(ActiviteSauvegardee.user_email))).filter(ActiviteSauvegardee.partagee == True).scalar() or 0

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
        db.query(ActiviteSauvegardee.user_email, func.count().label("nb"))
        .filter(ActiviteSauvegardee.partagee == True)
        .group_by(ActiviteSauvegardee.user_email)
        .order_by(func.count().desc())
        .all()
    )

    contributeurs = []
    for email, nb in contributeurs_raw:
        u = db.query(User).filter(User.email == email).first()
        nom = " ".join(filter(None, [u.prenom, u.nom])) if u else ""
        contributeurs.append({"email": email, "nom": nom or email, "nb": nb})

    return {
        "total_partages": total,
        "nb_contributeurs": nb_profs,
        "par_matiere": [{"matiere": r[0], "nb": r[1]} for r in par_matiere],
        "par_type": [{"label": r[0], "nb": r[1]} for r in par_type],
        "contributeurs": contributeurs,
    }
