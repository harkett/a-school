from fastapi import APIRouter, Cookie, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.securite import comptes
from backend.core.database import get_db
from backend.core.models_db import FeatureVotable, FeatureVote, User
from backend.systeme.admin import _require_admin

router = APIRouter()


def catalogue_features(db: Session, actives_seulement: bool = True) -> list[FeatureVotable]:
    """Catalogue des fonctionnalités votables, lu EN BASE (table `features_votables`).
    Aucune liste en dur : l'écran prof, la validation du vote et l'admin passent tous ici.
    Table vide = migration non appliquée -> on lève (erreur claire) plutôt que de retomber
    sur du dur caché. `actif=false` retire la carte de l'écran sans perdre les votes."""
    rows = db.query(FeatureVotable).order_by(FeatureVotable.ordre, FeatureVotable.id).all()
    if not rows:
        raise HTTPException(500, "Fonctionnalités votables absentes en base (migration non appliquée ?).")
    # UNE FONCTIONNALITÉ LIVRÉE N'EST PLUS « BIENTÔT ». Elle quitte l'écran du professeur sans
    # que personne ait à décocher `actif` : on ne fait pas voter pour ce qui existe déjà. Ses
    # votes restent — ils disent ce qui était attendu. L'administration, elle, voit tout.
    return [r for r in rows if r.actif and not r.livree] if actives_seulement else rows


def _email_ou_401(aschool_access: str | None) -> str:
    if not aschool_access:
        raise HTTPException(401, "Connexion requise.")
    email = comptes.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


@router.get("/feature-votes")
def get_votes(
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    email = _email_ou_401(aschool_access)

    rows = db.query(FeatureVote.feature_key, func.count(FeatureVote.id)).group_by(FeatureVote.feature_key).all()
    votes = {row[0]: row[1] for row in rows}

    mes_votes = [v.feature_key for v in db.query(FeatureVote).filter(FeatureVote.user_id == db.query(User.id).filter(User.email == email).scalar()).all()]

    features = [
        {
            "key":         f.code,
            "label":       f.label,
            "description": f.description,
            "categorie":   f.categorie,
            "icone":       f.icone,
            "count":       votes.get(f.code, 0),
        }
        for f in catalogue_features(db)
    ]
    return {"features": features, "mes_votes": mes_votes}


@router.get("/nouveautes")
def get_nouveautes(
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    """Ce qui vient d'arriver, pour le bandeau d'accueil : les fonctionnalités LIVRÉES que
    l'administration a choisi d'annoncer. Deux conditions, jamais une seule — une ligne cochée
    « nouveauté » mais pas livrée ne s'affiche pas, l'écran d'administration l'interdit déjà."""
    _email_ou_401(aschool_access)
    rows = (
        db.query(FeatureVotable)
        .filter(FeatureVotable.livree.is_(True), FeatureVotable.nouveaute.is_(True))
        .order_by(FeatureVotable.ordre, FeatureVotable.id)
        .all()
    )
    return [
        {"key": f.code, "label": f.label, "description": f.description,
         "icone": f.icone, "page": f.page}
        for f in rows
    ]


class VoteBody(BaseModel):
    feature_key: str


@router.post("/feature-vote")
def toggle_vote(
    body: VoteBody,
    db: Session = Depends(get_db),
    aschool_access: str | None = Cookie(default=None),
):
    email = _email_ou_401(aschool_access)
    if body.feature_key not in {f.code for f in catalogue_features(db)}:
        raise HTTPException(400, "Cette fonctionnalité n'est pas (ou plus) ouverte au vote.")

    existing = db.query(FeatureVote).filter(
        FeatureVote.user_id == db.query(User.id).filter(User.email == email).scalar(),
        FeatureVote.feature_key == body.feature_key,
    ).first()

    if existing:
        db.delete(existing)
        voted = False
    else:
        db.add(FeatureVote(user_id=db.query(User.id).filter(User.email == email).scalar(), feature_key=body.feature_key))
        voted = True

    db.commit()

    count = db.query(func.count(FeatureVote.id)).filter(
        FeatureVote.feature_key == body.feature_key
    ).scalar()

    return {"voted": voted, "count": count}


@router.get("/admin/feature-votes")
def admin_get_votes(
    db: Session = Depends(get_db),
    _=Depends(_require_admin),
):
    rows = db.query(FeatureVote.feature_key, func.count(FeatureVote.id)).group_by(FeatureVote.feature_key).all()
    votes = {row[0]: row[1] for row in rows}

    # Toutes les lignes, y compris inactives : les votes recueillis restent visibles de
    # l'admin même quand la carte a quitté l'écran prof.
    # LA FICHE ENTIERE, PAS SEULEMENT LE COMPTEUR (16/08/2026). L'ecran « Bientot disponible »
    # de l'administration montre ce que le professeur lit : le texte de la carte et sa famille.
    # Le classement des votes s'en sert toujours — il ignore simplement les champs en plus.
    result = [
        {"key": f.code, "label": f.label, "description": f.description,
         "categorie": f.categorie, "actif": f.actif, "ordre": f.ordre,
         "livree": f.livree, "nouveaute": f.nouveaute, "page": f.page,
         "count": votes.get(f.code, 0)}
        for f in catalogue_features(db, actives_seulement=False)
    ]
    result.sort(key=lambda x: -x["count"])
    return result


class EtatFeatureBody(BaseModel):
    livree: bool
    nouveaute: bool


@router.patch("/admin/feature-votes/{code}")
def admin_etat_feature(
    code: str,
    body: EtatFeatureBody,
    db: Session = Depends(get_db),
    _=Depends(_require_admin),
):
    """Les deux cases de l'écran « Bientôt disponible » de l'administration.

    LA RÈGLE EST TENUE ICI, PAS SEULEMENT À L'ÉCRAN : annoncer en nouveauté ce qui n'est pas
    livré n'a pas de sens, et un appel direct au serveur contournerait la case grisée. Décocher
    « livrée » retire donc aussi « nouveauté »."""
    ligne = db.query(FeatureVotable).filter(FeatureVotable.code == code).first()
    if not ligne:
        raise HTTPException(404, "Fonctionnalité inconnue.")

    ligne.livree = body.livree
    ligne.nouveaute = body.nouveaute and body.livree

    # UNE SEULE NOUVEAUTÉ À LA FOIS. Annoncer trois choses, c'est n'en annoncer aucune : le
    # bandeau du professeur porte UN titre, celui qu'on a choisi de mettre en avant. Cocher une
    # ligne décoche donc la précédente — l'administration n'a rien à décocher à la main, et
    # deux écrans ne peuvent pas en allumer deux chacun de son côté.
    if ligne.nouveaute:
        (db.query(FeatureVotable)
           .filter(FeatureVotable.code != ligne.code, FeatureVotable.nouveaute.is_(True))
           .update({FeatureVotable.nouveaute: False}, synchronize_session=False))

    db.commit()
    return {"key": ligne.code, "livree": ligne.livree, "nouveaute": ligne.nouveaute}
