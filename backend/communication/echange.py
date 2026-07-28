"""Échange sur un retour : la réponse de l'administration, puis la suite.

UNE SEULE PLACE pour la règle. Les deux écrans — « Mes retours » côté prof et
« Retours utilisateurs » côté admin — lisent et écrivent par ici : même validation, même
avis par mail, même journal. Rien n'est réécrit d'un côté ou de l'autre.

Ce que ce module NE fait PAS : toucher au message d'ouverture. `feedbacks.message` reste
la première prise de parole du prof, modifiable par lui tant que `feedback_statuts.modifiable`
l'autorise. Ici on ne gère que ce qui vient APRÈS.

L'avis par mail ne porte JAMAIS le contenu du message : il dit qu'il y a quelque chose à lire,
le contenu reste dans aSchool (la base est la source unique). Son texte vit en base
(`email_templates`, slugs semés par migration) — aucun repli en dur : si le modèle manque,
le message est quand même enregistré et l'échec est tracé dans le journal des envois.
"""
import logging
import os

from sqlalchemy.orm import Session

from backend.core.models_db import EmailTemplate, Feedback, FeedbackMessage, User

logger = logging.getLogger(__name__)

CORPS_MAX = 2000

# Slugs des deux sens de l'avis, semés en base par la migration f1e2d3c4b5a6.
SLUG_VERS_PROF = "reponse_feedback"
SLUG_VERS_ADMIN = "reponse_prof"


class CorpsInvalide(ValueError):
    """Message vide ou trop long — remonté à l'écran en langage humain (RÈGLE 23)."""


# ── Lecture ────────────────────────────────────────────────────────────────

def messages_par_feedback(db: Session, feedback_ids: list[int]) -> dict[int, list[FeedbackMessage]]:
    """Les échanges de PLUSIEURS retours en UNE requête (les deux écrans affichent des listes ;
    une requête par carte ferait autant d'allers-retours que de retours affichés)."""
    if not feedback_ids:
        return {}
    rows = (
        db.query(FeedbackMessage)
        .filter(FeedbackMessage.feedback_id.in_(feedback_ids))
        .order_by(FeedbackMessage.feedback_id, FeedbackMessage.created_at)
        .all()
    )
    par_feedback: dict[int, list[FeedbackMessage]] = {}
    for m in rows:
        par_feedback.setdefault(m.feedback_id, []).append(m)
    return par_feedback


def serialiser(messages: list[FeedbackMessage], *, vu_par_admin: bool,
               email_prof: str | None = None) -> list[dict]:
    """Met l'échange en forme POUR CELUI QUI REGARDE.

    Le nom affiché n'est pas une donnée rangée en base : il se déduit du côté d'où vient le
    message et du côté d'où on le lit. Calculé ici plutôt que dans chaque écran, pour que les
    deux disent la même chose — et pour que l'administration s'appelle toujours « aSchool »
    devant un prof (jamais « IA », jamais « admin »)."""
    sortie = []
    for m in messages or []:
        de_moi = (m.auteur_est_admin == vu_par_admin)
        if de_moi:
            auteur = "Vous"
        elif m.auteur_est_admin:
            auteur = "aSchool"
        else:
            auteur = email_prof or "Le professeur"
        sortie.append({
            "id": m.id,
            "corps": m.corps,
            "de_l_administration": m.auteur_est_admin,
            "de_moi": de_moi,
            "auteur": auteur,
            "date": m.created_at.strftime("%d/%m/%Y %H:%M") if m.created_at else "—",
        })
    return sortie


# ── Écriture ───────────────────────────────────────────────────────────────

def _avis_par_mail(db: Session, feedback: Feedback, *, est_admin: bool) -> tuple[str, str | None]:
    """Envoie l'avis « il y a quelque chose à lire » et le trace dans le journal des envois.

    Ne lève jamais : le message est déjà en base, un serveur de mail muet ne doit pas le perdre.
    Renvoie (statut, erreur) — 'envoye' ou 'echec' — pour que l'écran dise la vérité."""
    from backend import auth as auth_lib
    from backend.systeme.admin import record_email_envoi

    slug = SLUG_VERS_PROF if est_admin else SLUG_VERS_ADMIN
    modele = db.query(EmailTemplate).filter(EmailTemplate.slug == slug).first()

    if est_admin:
        prof = db.query(User).filter(User.id == feedback.user_id).first()
        destinataire = prof.email if prof else ""
        prenom = prof.prenom if prof else None
    else:
        destinataire = os.getenv("FEEDBACK_NOTIFY_EMAIL", "")
        prenom = None

    # Base = source unique : aucun texte de repli en dur. Un modèle absent est une ERREUR de
    # configuration, tracée telle quelle — pas un mail fantôme envoyé avec un texte inventé.
    if modele is None:
        erreur = f"Modèle d'email '{slug}' absent de la base (migration non appliquée ?)."
        record_email_envoi(db, modele_slug=slug, modele_nom=slug, destinataire=destinataire,
                           objet="", statut="echec", erreur=erreur)
        logger.error(erreur)
        return "echec", erreur

    if not destinataire:
        erreur = ("Aucun destinataire pour l'avis : "
                  + ("le prof n'a plus de compte." if est_admin
                     else "FEEDBACK_NOTIFY_EMAIL n'est pas configurée."))
        record_email_envoi(db, modele_slug=modele.slug, modele_nom=modele.nom,
                           destinataire="", objet=modele.objet, statut="echec", erreur=erreur)
        logger.error(erreur)
        return "echec", erreur

    statut, erreur = "envoye", None
    try:
        auth_lib.send_custom_email(destinataire, prenom, modele.objet, modele.corps)
    except Exception as e:
        statut, erreur = "echec", f"{type(e).__name__}: {e}"
        logger.error("Avis d'échange non envoyé à %s : %s", destinataire, erreur)

    record_email_envoi(db, modele_slug=modele.slug, modele_nom=modele.nom,
                       destinataire=destinataire, objet=modele.objet,
                       statut=statut, erreur=erreur)
    return statut, erreur


def ajouter_message(db: Session, feedback: Feedback, corps: str, *,
                    est_admin: bool) -> tuple[FeedbackMessage, str, str | None]:
    """Écrit un message dans l'échange, puis prévient l'autre côté.

    Le message est enregistré AVANT l'envoi de l'avis : si le mail échoue, la réponse existe
    quand même et se lit dans l'application. Renvoie (message, statut_avis, erreur_avis)."""
    corps = (corps or "").strip()
    if not corps:
        raise CorpsInvalide("Votre message est vide.")
    if len(corps) > CORPS_MAX:
        raise CorpsInvalide(f"Votre message dépasse {CORPS_MAX} caractères.")

    message = FeedbackMessage(
        feedback_id=feedback.id, auteur_est_admin=est_admin, corps=corps,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    statut_avis, erreur_avis = _avis_par_mail(db, feedback, est_admin=est_admin)
    return message, statut_avis, erreur_avis
