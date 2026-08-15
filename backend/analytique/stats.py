from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import Integer, func

from backend.core.database import get_db
from backend.core.models_db import (
    Activite, AiFournisseur, AiModele, ConnexionLog, OutilLlm, Seance, Sequence, UsageLlm, User,
)
from backend.securite import comptes
from backend.systeme.admin import _require_admin, get_minutes_par_activite, get_few_shot_seuil
from backend.core.horloge import maintenant_utc

router = APIRouter()


def _get_email(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = comptes.verify_access_token(aschool_access)
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

    debut_mois = maintenant_utc().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
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

    today = maintenant_utc().date()
    depuis_7j = maintenant_utc() - timedelta(days=7)

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
    today = maintenant_utc().date()
    depuis_7j = maintenant_utc() - timedelta(days=7)

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


# ---------------------------------------------------------------------------
# IA › Statistiques — ce que l'IA a consommé, et ce que ça coûte.
# ---------------------------------------------------------------------------

def _tarifs(db: Session) -> dict:
    """Grille de prix par modèle, telle qu'elle est EN BASE (`ai_modeles`). Un modèle sans tarif
    n'est pas une erreur : ses tokens se comptent, son montant reste inconnu — l'écran le dit."""
    return {
        m.modele: (
            float(m.cout_entree_million) if m.cout_entree_million is not None else None,
            float(m.cout_sortie_million) if m.cout_sortie_million is not None else None,
        )
        for m in db.query(AiModele).all()
    }


# Cache de prompt du fournisseur : ce que coûtent ses tokens, en multiple du tarif d'ENTRÉE.
# Faire garder un préambule se paie un peu plus cher qu'un envoi normal (1,25×) ; le relire ensuite
# ne coûte qu'un dixième (0,10×). C'est tout l'intérêt de la mécanique, et c'est pourquoi les deux
# ne peuvent pas être additionnés avant d'être multipliés.
_CACHE_ECRITURE = 1.25
_CACHE_LECTURE = 0.10


def _cout(tarifs: dict, modele: str, entree: int, sortie: int,
          cache_ecriture: int = 0, cache_lecture: int = 0):
    """Montant estimé en dollars, ou None si le modèle n'a pas de tarif renseigné.

    None n'est PAS zéro, et l'écran ne doit pas les confondre : zéro veut dire « n'a rien coûté »,
    None veut dire « on ne sait pas encore ». Les additionner donnerait un total faussement bas.

    Les tokens de cache s'ajoutent à l'entrée, à leurs propres multiplicateurs. Les oublier ne
    rendrait pas le total « approximatif » : Anthropic les sort de `input_tokens`, donc un appel
    servi par le cache paraîtrait presque gratuit alors qu'il a lu un référentiel entier."""
    entree_prix, sortie_prix = tarifs.get(modele, (None, None))
    if entree_prix is None and sortie_prix is None:
        return None
    prix_entree = entree_prix or 0
    return round(((entree or 0)
                  + (cache_ecriture or 0) * _CACHE_ECRITURE
                  + (cache_lecture or 0) * _CACHE_LECTURE) / 1_000_000 * prix_entree
                 + (sortie or 0) / 1_000_000 * (sortie_prix or 0), 4)


@router.get("/admin/ia/usage")
def admin_ia_usage(jours: int = Query(30, ge=1, le=365),
                   db: Session = Depends(get_db), _=Depends(_require_admin)):
    """Consommation LLM sur les N derniers jours, vue sous les trois angles de l'écran.

    Une seule route pour les trois onglets : les trois regroupent LES MÊMES lignes, et trois
    requêtes séparées feraient trois fois le même filtre pour des totaux qui doivent rester
    cohérents entre eux. `jours` borne la fenêtre — sans borne, l'écran ralentirait avec l'âge de
    l'installation, et personne ne lit « depuis toujours »."""
    depuis = maintenant_utc() - timedelta(days=jours)
    tarifs = _tarifs(db)

    # LES REFUS SONT ÉCARTÉS DE CET ÉCRAN. Depuis que `usage_llm` porte les tentatives et non plus
    # les seuls appels aboutis, une ligne peut être un refus : aucun token, aucun coût, mais elle
    # se compterait dans « appels » et écraserait les moyennes. La consommation, c'est ce qui a été
    # consommé. Les refus se regardent au Journal, un par un, qui est fait pour ça.
    #
    # `coupe` RESTE compté : une réponse tronquée a bien été produite et se facture. La masquer
    # ferait disparaître une dépense réelle — et c'est justement la dépense qu'on veut voir.
    _abouti = UsageLlm.resultat != "refus"

    somme_entree = func.coalesce(func.sum(UsageLlm.tokens_entree), 0)
    somme_sortie = func.coalesce(func.sum(UsageLlm.tokens_sortie), 0)
    # Appels REJOUÉS par le cache disque : comptés à part, pas retirés. Un rejeu n'a rien envoyé et
    # rien coûté, mais il a bien eu lieu — le soustraire ferait disparaître le travail du cache de
    # l'écran, alors que c'est précisément ce qu'on veut voir.
    somme_cache = func.coalesce(func.sum(func.cast(UsageLlm.depuis_cache, Integer)), 0)
    # Tokens du cache de PROMPT (fournisseur) : comptés à part parce qu'ils se paient à un autre
    # tarif — et parce qu'Anthropic les sort de `input_tokens`, donc les ignorer sous-estimerait
    # la facture d'un facteur dix sur les appels qui relisent un référentiel.
    somme_cache_ecriture = func.coalesce(func.sum(UsageLlm.tokens_cache_ecriture), 0)
    somme_cache_lecture = func.coalesce(func.sum(UsageLlm.tokens_cache_lecture), 0)

    # Libellés lisibles des outils : « detecter_matieres » n'est pas un mot d'écran.
    libelles = {o.outil: o.libelle for o in db.query(OutilLlm).all()}

    def _lignes(colonne, nommer):
        lignes = []
        for r in (db.query(colonne.label("cle"), somme_entree.label("entree"),
                           somme_sortie.label("sortie"),
                           somme_cache_ecriture.label("cache_ecriture"),
                           somme_cache_lecture.label("cache_lecture"),
                           func.count(UsageLlm.id).label("appels"))
                    .filter(UsageLlm.created_at >= depuis, _abouti)
                    .group_by(colonne).all()):
            # Cache compris, comme dans « par modèle » : les trois onglets doivent donner le même
            # volume pour les mêmes appels, sinon l'un des trois passe pour cassé.
            entree = int(r.entree) + int(r.cache_ecriture) + int(r.cache_lecture)
            sortie = int(r.sortie)
            lignes.append({
                "cle": r.cle, "libelle": nommer(r.cle), "appels": r.appels,
                "tokens_entree": entree, "tokens_sortie": sortie,
                # Le coût se calcule TOUJOURS par modèle, jamais sur un agrégat multi-modèles :
                # additionner des tokens de modèles à prix différents puis multiplier donnerait
                # un montant inventé. D'où le calcul par ligne quand la clé est le modèle, et
                # l'absence de montant sur les regroupements qui mélangent les modèles.
                "cout_usd": None,
            })
        return sorted(lignes, key=lambda l: l["tokens_entree"] + l["tokens_sortie"], reverse=True)

    # « Par modèle » croise le MODÈLE et L'ORIGINE (l'outil qui a déclenché l'appel). Regroupé sur
    # le seul modèle, le tableau répondait « claude-sonnet-5 : 210 000 tokens, 0,85 $ » sans dire
    # QUI avait dépensé — la question que l'admin pose en premier devant un montant. Le croisement
    # la met sur la même ligne, sans changer d'onglet.
    #
    # Le coût reste calculable ligne par ligne : chacune ne porte qu'UN modèle, donc un seul tarif.
    # Et les totaux du haut ne bougent pas — un découpage plus fin couvre exactement les mêmes
    # appels ; c'est une partition, pas un filtre.
    par_modele = []
    for r in (db.query(UsageLlm.modele.label("modele"), UsageLlm.outil.label("outil"),
                       somme_entree.label("entree"), somme_sortie.label("sortie"),
                       somme_cache.label("cache"), somme_cache_ecriture.label("cache_ecriture"),
                       somme_cache_lecture.label("cache_lecture"),
                       func.count(UsageLlm.id).label("appels"))
                .filter(UsageLlm.created_at >= depuis, _abouti)
                .group_by(UsageLlm.modele, UsageLlm.outil).all()):
        entree, sortie = int(r.entree), int(r.sortie)
        cache_e, cache_l = int(r.cache_ecriture), int(r.cache_lecture)
        par_modele.append({
            "cle": r.modele, "libelle": r.modele or "—",
            # Combien de ces appels ont été rejoués gratuitement (cache disque, dev).
            "appels_cache": int(r.cache),
            # Tokens confiés au cache de prompt du fournisseur, et tokens relus depuis lui.
            "tokens_cache_ecriture": cache_e, "tokens_cache_lecture": cache_l,
            # `outil` = le mot du code (`outils_llm.outil`) ; `origine` = ce que l'admin lit.
            # Un appel non nommé garde sa ligne et se dit « Non précisé » : le faire disparaître
            # amputerait la facture de la dépense qu'on cherche justement à identifier.
            "outil": r.outil,
            "origine": libelles.get(r.outil) or r.outil or "Non précisé",
            # `tokens_entree` = TOUT ce qui est parti chez le fournisseur, cache compris.
            # Anthropic sort les tokens de cache de son `input_tokens` : les laisser dehors ferait
            # afficher « 42 tokens envoyés » pour un appel qui vient de lire 7 800 tokens de
            # référentiel. L'écran dirait vrai sur la facture et faux sur le volume.
            "appels": r.appels, "tokens_entree": entree + cache_e + cache_l,
            "tokens_sortie": sortie,
            "cout_usd": _cout(tarifs, r.modele, entree, sortie, cache_e, cache_l),
        })
    par_modele.sort(key=lambda l: l["tokens_entree"] + l["tokens_sortie"], reverse=True)

    par_outil = _lignes(UsageLlm.outil, lambda c: libelles.get(c) or c or "Non précisé")
    par_jour = _lignes(func.date(UsageLlm.created_at), lambda c: str(c))
    par_jour.sort(key=lambda l: str(l["cle"]))

    # Total : la somme des seuls modèles TARIFÉS. `cout_partiel` prévient l'écran qu'une part de la
    # consommation n'est pas chiffrée — un total muet sur ce point se lirait comme une facture.
    total_cout = sum(l["cout_usd"] for l in par_modele if l["cout_usd"] is not None)

    # ── CE QUE LA LISTE DE FOURNISSEURS A RATTRAPÉ ────────────────────────────────────────────
    #
    # Une réponse obtenue au rang 2 ou plus est une génération que l'ancienne version aurait
    # PERDUE : le premier fournisseur avait refusé, et il n'y avait personne derrière lui — le
    # professeur voyait un échec et devait recliquer.
    #
    # C'est la seule mesure honnête de ce qu'apporte la liste. Compter les refus ne dirait rien
    # (un refus rattrapé n'a coûté que quelques secondes) ; compter les succès non plus (ils
    # existaient avant). Ce qui compte, c'est le croisement des deux.
    #
    # `rang > 1` et pas `rang is not null` : le rang 1 est un succès du premier appelé, exactement
    # ce qui se passait avant. Il n'y a rien à en dire.
    rattrapees = (db.query(func.count(UsageLlm.id))
                    .filter(UsageLlm.created_at >= depuis, UsageLlm.resultat == "ok",
                            UsageLlm.rang.isnot(None), UsageLlm.rang > 1)
                    .scalar()) or 0

    return {
        "jours": jours,
        "appels": sum(l["appels"] for l in par_modele),
        # Générations obtenues chez un fournisseur de rang 2 ou plus : perdues, sans la liste.
        "appels_rattrapes": int(rattrapees),
        # Sur ces appels, ceux que le cache disque a rejoués sans rien envoyer ni payer.
        "appels_cache": sum(l["appels_cache"] for l in par_modele),
        # Et, chez le fournisseur, ce qui a été confié au cache de prompt puis relu à 10 %.
        "tokens_cache_ecriture": sum(l["tokens_cache_ecriture"] for l in par_modele),
        "tokens_cache_lecture": sum(l["tokens_cache_lecture"] for l in par_modele),
        "tokens_entree": sum(l["tokens_entree"] for l in par_modele),
        "tokens_sortie": sum(l["tokens_sortie"] for l in par_modele),
        "cout_usd": round(total_cout, 4),
        "cout_partiel": any(l["cout_usd"] is None for l in par_modele),
        "par_modele": par_modele,
        "par_outil": par_outil,
        "par_jour": par_jour,
    }


@router.get("/admin/ia/journal")
def admin_ia_journal(jours: int = Query(30, ge=1, le=365),
                     limite: int = Query(100, ge=1, le=500),
                     page: int = Query(1, ge=1),
                     fournisseur: str = Query(""),
                     db: Session = Depends(get_db), _=Depends(_require_admin)):
    """Le JOURNAL : un appel par ligne, le plus récent en haut.

    Pendant de `/admin/ia/usage`, qui ne rend que des cumuls. Les cumuls répondent « qu'a coûté la
    semaine ? » ; ils ne répondent pas « que s'est-il passé sur CET appel de 14 h 03 ? ». Jusqu'ici
    la seule façon de le voir était `docker logs` — c'est-à-dire pas depuis l'application.

    Les lignes sont les MÊMES que celles des statistiques (table `usage_llm`) : aucun recomptage,
    aucune autre source. Le coût est estimé ligne à ligne avec la grille du jour, comme ailleurs.
    Pagination obligatoire : un journal grandit sans fin, et une page qui charge tout finit par ne
    plus s'ouvrir du tout.

    `fournisseur` : filtre facultatif, vide = tous. La liste des choix N'EST PAS écrite dans le
    code — elle sort des lignes elles-mêmes (avec le libellé du catalogue `ai_fournisseurs` quand
    il existe). Un fournisseur raccordé demain apparaît donc dans le filtre dès son premier appel,
    sans une ligne à modifier. Et les compteurs sont comptés À LA LECTURE : un compteur tenu en
    base coûterait une écriture à chaque appel IA pour une lecture rare, et dériverait dès qu'une
    de ces écritures échoue — or celles d'usage échouent en silence, par construction."""
    depuis = maintenant_utc() - timedelta(days=jours)
    tarifs = _tarifs(db)
    libelles = {o.outil: o.libelle for o in db.query(OutilLlm).all()}

    # Compté SANS le filtre : les nombres de la liste déroulante doivent rester ceux de tous les
    # fournisseurs, sinon choisir l'un d'eux mettrait tous les autres à zéro.
    labels = {f.code: f.label for f in db.query(AiFournisseur).all()}
    repartition = (db.query(UsageLlm.fournisseur.label("code"), func.count(UsageLlm.id).label("appels"))
                     .filter(UsageLlm.created_at >= depuis)
                     .group_by(UsageLlm.fournisseur).all())
    fournisseurs = sorted(
        [{"code": r.code, "libelle": labels.get(r.code) or r.code, "appels": r.appels}
         for r in repartition],
        key=lambda f: f["appels"], reverse=True)

    conditions = [UsageLlm.created_at >= depuis]
    if fournisseur:
        conditions.append(UsageLlm.fournisseur == fournisseur)

    base = db.query(UsageLlm).filter(*conditions)
    total = base.count()
    lignes = (base.order_by(UsageLlm.created_at.desc(), UsageLlm.id.desc())
                  .offset((page - 1) * limite).limit(limite).all())

    # COÛT TOTAL DU FILTRE — toutes pages confondues, pas seulement celle qu'on regarde. Additionner
    # les seules lignes affichées donnerait un montant qui change en tournant les pages, c'est-à-dire
    # un chiffre qui ne répond à aucune question.
    #
    # Groupé par MODÈLE parce qu'un tarif appartient à un modèle : mélanger les tokens de plusieurs
    # modèles avant de multiplier inventerait le montant. Les rejeux du cache disque sont écartés —
    # rien n'est parti chez le fournisseur, rien n'a été facturé.
    cout_total, cout_partiel = 0.0, False
    for r in (db.query(UsageLlm.modele.label("modele"),
                       func.coalesce(func.sum(UsageLlm.tokens_entree), 0).label("entree"),
                       func.coalesce(func.sum(UsageLlm.tokens_sortie), 0).label("sortie"),
                       func.coalesce(func.sum(UsageLlm.tokens_cache_ecriture), 0).label("cache_e"),
                       func.coalesce(func.sum(UsageLlm.tokens_cache_lecture), 0).label("cache_l"))
                .filter(*conditions, UsageLlm.depuis_cache.is_(False),
                        UsageLlm.resultat != "refus")
                .group_by(UsageLlm.modele).all()):
        montant = _cout(tarifs, r.modele, int(r.entree), int(r.sortie), int(r.cache_e), int(r.cache_l))
        if montant is None:
            # Modèle sans tarif : ses appels existent, leur prix est inconnu. L'écran le dit — un
            # total muet là-dessus se lirait comme une facture complète.
            cout_partiel = True
        else:
            cout_total += montant

    return {
        "jours": jours, "page": page, "limite": limite, "total": total,
        "fournisseur": fournisseur,
        "cout_usd": round(cout_total, 4),
        "cout_partiel": cout_partiel,
        # « Tous » se compte ici plutôt qu'à l'écran : c'est la même période et la même table, et
        # `total` ne peut pas servir puisqu'il est déjà filtré.
        "total_tous": sum(f["appels"] for f in fournisseurs),
        "fournisseurs": fournisseurs,
        "lignes": [{
            "id": u.id,
            "quand": u.created_at.isoformat() if u.created_at else None,
            "fournisseur": u.fournisseur,
            "modele": u.modele,
            "outil": u.outil,
            "origine": libelles.get(u.outil) or u.outil or "Non précisé",
            # Pourquoi le modèle s'est arrêté. « max_tokens » = réponse COUPÉE : c'est la seule
            # colonne qui explique une génération incomplète, et c'est pour elle que cet écran existe.
            "motif_arret": u.motif_arret,
            # Ce qu'est devenue la tentative. `refus` = le fournisseur n'a rien produit ; `coupe` =
            # il a produit mais s'est arrêté sur sa limite de sortie ; `ok` = complet. Sans ce mot,
            # un refus se lisait comme un appel à zéro token, c'est-à-dire comme un appel gratuit.
            "resultat": u.resultat,
            # Ce que le fournisseur a répondu (429, 402, 500…), vide quand il a répondu normalement.
            # C'est lui qui distingue « plus de quota » de « en panne » : deux refus, deux gestes.
            "code_http": u.code_http,
            # La place du fournisseur dans la liste au moment de l'essai. Vide tant qu'il n'y a pas
            # de liste — écrire « 1 » inventerait une cascade qui n'existe pas encore.
            "rang": u.rang,
            "tokens_entree": (u.tokens_entree or 0) + (u.tokens_cache_ecriture or 0) + (u.tokens_cache_lecture or 0),
            "tokens_sortie": u.tokens_sortie or 0,
            "tokens_cache_ecriture": u.tokens_cache_ecriture or 0,
            "tokens_cache_lecture": u.tokens_cache_lecture or 0,
            "duree_ms": u.duree_ms,
            "depuis_cache": bool(u.depuis_cache),
            # Un rejeu du cache disque n'a rien envoyé : lui compter un prix ferait payer deux fois
            # le même appel à l'écran, alors que la deuxième fois n'a rien coûté.
            # Ni les rejeux du cache, ni les refus n'ont coûté quoi que ce soit : leur donner
            # un prix ferait payer à l'écran ce qui n'a jamais été facturé.
            "cout_usd": None if (u.depuis_cache or u.resultat == "refus") else _cout(
                tarifs, u.modele, u.tokens_entree, u.tokens_sortie,
                u.tokens_cache_ecriture, u.tokens_cache_lecture),
        } for u in lignes],
    }
