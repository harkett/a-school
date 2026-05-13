from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models_db import ActiviteSauvegardee, ConnexionLog, SequenceSauvegardee, ToolUsageLog, User
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

    derniere_seq = (
        db.query(SequenceSauvegardee)
        .filter(SequenceSauvegardee.user_email == email)
        .order_by(SequenceSauvegardee.id.desc())
        .first()
    )

    return {
        "mes_activites": mes_activites,
        "mes_partages": mes_partages,
        "communaute_total": communaute_total,
        "communaute_profs": communaute_profs,
        "derniere_sequence": {
            "id": derniere_seq.id,
            "theme": derniere_seq.theme,
            "matiere": derniere_seq.matiere,
            "niveau": derniere_seq.niveau,
            "duree": derniere_seq.duree,
            "mode": derniere_seq.mode,
            "description_classe": derniere_seq.description_classe,
            "resultat": derniere_seq.resultat,
        } if derniere_seq else None,
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


# ---------------------------------------------------------------------------
# Stats personnelles prof (B1)
# ---------------------------------------------------------------------------

@router.get("/stats/perso")
def stats_perso(aschool_access: str = Cookie(default=None), db: Session = Depends(get_db)):
    email = _get_email(aschool_access)

    total_sequences = db.query(func.count(SequenceSauvegardee.id)).filter(
        SequenceSauvegardee.user_email == email
    ).scalar() or 0

    type_row = (
        db.query(ActiviteSauvegardee.activite_label, func.count().label("nb"))
        .filter(ActiviteSauvegardee.user_email == email)
        .group_by(ActiviteSauvegardee.activite_label)
        .order_by(func.count().desc())
        .first()
    )
    type_favori = type_row[0] if type_row else None
    max_par_type = type_row[1] if type_row else 0
    score_adaptation = 0 if max_par_type == 0 else min(100, int(max_par_type / 3 * 100))

    total_activites = db.query(func.count(ActiviteSauvegardee.id)).filter(
        ActiviteSauvegardee.user_email == email
    ).scalar() or 0
    heures_gagnees = (total_activites * 15) // 60

    debut_mois = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    activites_ce_mois = db.query(func.count(ActiviteSauvegardee.id)).filter(
        ActiviteSauvegardee.user_email == email,
        ActiviteSauvegardee.created_at >= debut_mois,
    ).scalar() or 0

    login_dates_raw = (
        db.query(func.date(ConnexionLog.created_at).label("day"))
        .filter(ConnexionLog.email == email, ConnexionLog.action == "login")
        .distinct()
        .all()
    )
    login_dates = {str(r.day) for r in login_dates_raw}
    streak = 0
    check = datetime.utcnow().date()
    for _ in range(365):
        if str(check) in login_dates:
            streak += 1
            check -= timedelta(days=1)
        else:
            break

    return {
        "sequences": total_sequences,
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
    _get_email(aschool_access)

    today = datetime.utcnow().date()
    depuis_7j = datetime.utcnow() - timedelta(days=7)

    profs_actifs_aujourd_hui = db.query(func.count(func.distinct(ConnexionLog.email))).filter(
        ConnexionLog.action == "login",
        func.date(ConnexionLog.created_at) == str(today)
    ).scalar() or 0

    profs_actifs_semaine = db.query(func.count(func.distinct(ConnexionLog.email))).filter(
        ConnexionLog.action == "login",
        ConnexionLog.created_at >= depuis_7j
    ).scalar() or 0

    activites_total = db.query(func.count(ActiviteSauvegardee.id)).scalar() or 0

    partages_total = db.query(func.count(ActiviteSauvegardee.id)).filter(
        ActiviteSauvegardee.partagee == True
    ).scalar() or 0

    return {
        "profs_actifs_aujourd_hui": profs_actifs_aujourd_hui,
        "profs_actifs_semaine": profs_actifs_semaine,
        "activites_total": activites_total,
        "partages_total": partages_total,
    }


# ---------------------------------------------------------------------------
# Vitalité communauté (B2) — admin
# ---------------------------------------------------------------------------

@router.get("/admin/stats/vitalite")
def admin_stats_vitalite(db: Session = Depends(get_db), _=Depends(_require_admin)):
    today = datetime.utcnow().date()
    depuis_7j = datetime.utcnow() - timedelta(days=7)

    profs_actifs_aujourd_hui = db.query(func.count(func.distinct(ConnexionLog.email))).filter(
        ConnexionLog.action == "login",
        func.date(ConnexionLog.created_at) == str(today)
    ).scalar() or 0

    profs_actifs_semaine = db.query(func.count(func.distinct(ConnexionLog.email))).filter(
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
