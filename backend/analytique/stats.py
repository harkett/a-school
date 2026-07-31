from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.core.database import get_db
from backend.core.models_db import Activite, ConnexionLog, Seance, Sequence, User
from backend import auth as auth_lib
from backend.systeme.admin import _require_admin, get_minutes_par_activite, get_few_shot_seuil

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
    """Vue générale admin, comptée sur le monde NEUF (table activites — décision 30/07).
    Les sections « outils » (Séquence/Optimiseur, démolis) et « communauté » (partages,
    ancien monde) ont disparu avec l'ancien monde."""
    total_activites = db.query(func.count(Activite.id)).scalar() or 0
    nb_profs = db.query(func.count(func.distinct(Activite.user_id))).scalar() or 0
    top_mat = (
        db.query(Activite.matiere, func.count().label("nb"))
        .filter(Activite.matiere.isnot(None))
        .group_by(Activite.matiere)
        .order_by(func.count().desc())
        .first()
    )
    top_type = (
        db.query(Activite.activite_label, func.count().label("nb"))
        .group_by(Activite.activite_label)
        .order_by(func.count().desc())
        .first()
    )

    return {
        "activites": {
            "total": total_activites,
            "nb_profs": nb_profs,
            "top_matiere": top_mat[0] if top_mat else "—",
            "top_matiere_nb": top_mat[1] if top_mat else 0,
            "top_type": top_type[0] if top_type else "—",
            "top_type_nb": top_type[1] if top_type else 0,
        },
    }


# ---------------------------------------------------------------------------
# Admin — Outils (Séquence + Optimiseur)
# ---------------------------------------------------------------------------

# (/admin/tool-usage supprimé le 30/07 : il ne comptait que Séquence et Optimiseur,
# deux outils démolis avec l'ancien monde. La table tool_usage_logs reste — les analyses
# Ambiguïtés/Consigne y écrivent toujours.)


# ---------------------------------------------------------------------------
# Admin — Communauté
# ---------------------------------------------------------------------------

# (/admin/communaute-stats supprimé le 30/07 : les partages étaient l'ancien monde ;
# le partage du monde neuf sera conçu avec le nouveau Mon réseau.)


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

    # « aSchool vous connaît à X% » : la jauge suit EXACTEMENT ce qui déclenche le few-shot à
    # la génération (activites.few_shot_du_prof), c'est-à-dire le meilleur groupe type × couple
    # — et non le type toutes classes confondues. Sinon la jauge annoncerait « style reconnu »
    # alors que rien ne s'appliquerait. Le seuil est EN BASE (few_shot_seuil), plus de « 3 » en dur.
    seuil = get_few_shot_seuil(db)
    meilleur_groupe = (
        db.query(func.count().label("nb"))
        .filter(Activite.user_id == uid, Activite.resultat != "")
        .group_by(Activite.activite_type_id, Activite.matiere, Activite.niveau)
        .order_by(func.count().desc())
        .first()
    )
    max_par_type = meilleur_groupe[0] if meilleur_groupe else 0
    score_adaptation = min(100, int(max_par_type / seuil * 100))

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
        # Le seuil part à l'écran : la phrase sous la jauge (« Créez N activités du même
        # type… ») le lit au lieu de le recopier en dur.
        "few_shot_seuil": seuil,
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

    # Monde NEUF (décision 30/07) ; plus de partages_total — le partage neuf n'existe pas encore.
    activites_total = db.query(func.count(Activite.id)).scalar() or 0
    seances_total = db.query(func.count(Seance.id)).scalar() or 0
    sequences_total = db.query(func.count(Sequence.id)).scalar() or 0

    return {
        "profs_actifs_aujourd_hui": profs_actifs_aujourd_hui,
        "profs_actifs_semaine": profs_actifs_semaine,
        "activites_total": activites_total,
        "seances_total": seances_total,
        "sequences_total": sequences_total,
    }
