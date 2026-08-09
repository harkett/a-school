"""Démonstration — le passage du prof vers le bac à sable de son niveau.

CE QUE C'EST. Une base de démonstration (`ciela_demo`…) est servie par une SECONDE instance de
l'application, branchée dessus, sur sa propre adresse. Le prof identifié voit dans son menu une
entrée « Démonstration » qui l'y emmène. Il y arrive AVEC SON IDENTITÉ : pas de compte partagé,
pas de mot de passe à faire circuler — on sait qui est venu, et chacun a son coin.

POURQUOI DEUX INSTANCES ET PAS UN AIGUILLAGE INTERNE. L'étanchéité ne repose alors sur aucune
astuce de code : ce sont deux processus, deux `DATABASE_URL`, deux bases. Rien de ce que le prof
touche en démonstration ne peut atteindre le réel, même si une route oubliait un filtre.

LE PASSAGE. L'instance réelle émet un JETON signé, valable cinq minutes, qui porte l'identité du
prof en CLAIR mais en NOMS (email, prénom, nom, matière, niveau) — jamais en identifiants : les
`matieres.id` et `niveaux.id` de la base de démonstration n'ont rien à voir avec ceux du réel.
L'instance de démonstration le vérifie, retrouve ou crée le compte, pose ses cookies.

LE SECRET. `DEMO_SECRET`, partagé par les deux instances. Il n'est PAS obligatoire au démarrage,
contrairement à `JWT_SECRET` : un serveur sans démonstration n'a aucune raison de le poser. Mais
sans lui, aucune des deux moitiés ne fonctionne — pas de repli, pas de valeur d'exemple.

LE CONTENU D'EXEMPLE. Un compte GABARIT, désigné par la clé `demo_gabarit_email` de `settings`,
porte les activités, séances et séquences d'exemple. Il ne se connecte plus (`is_active` faux) :
il n'est qu'un propriétaire. À sa première visite, un prof en reçoit une COPIE à son nom. Il la
modifie, il la casse, il la supprime — les autres visiteurs n'en savent rien.
"""

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.core.models_db import (
    Activite, Cycle, Demo, Matiere, Niveau, Referentiel, Seance, Sequence, Setting, User,
)
from backend.securite import comptes

router = APIRouter()

_ALGO = "HS256"
_TYPE_JETON = "passage_demo"
_VALIDITE = timedelta(minutes=5)

# Seules ces deux étapes ouvrent la porte. Une démonstration « fabriquée » n'est pas relue ; on
# n'y envoie personne. Même règle que partout : ce qui n'est pas vérifié n'est pas proposé.
_STATUTS_VISITABLES = ("teste", "valide")

# La clé de `settings` qui désigne le compte porteur du contenu d'exemple, dans la base de
# démonstration. En base et pas dans le code : le gabarit change d'une démonstration à l'autre.
_CLE_GABARIT = "demo_gabarit_email"


def _secret() -> str | None:
    """Le secret partagé, ou None s'il n'est pas posé. Pas de repli : sans secret, le passage
    n'existe pas — il ne se dégrade pas en passage non signé."""
    valeur = os.getenv("DEMO_SECRET") or ""
    return valeur.strip() or None


def mode_demo() -> bool:
    """Cette instance sert-elle une base de démonstration ? Décidé par l'environnement, jamais
    par la base : une base restaurée ailleurs ne doit pas emporter ce drapeau avec elle."""
    return (os.getenv("MODE_DEMO") or "").strip().lower() in ("1", "oui", "true")


# ---------------------------------------------------------------------------
# Côté instance RÉELLE — d'où part le prof
# ---------------------------------------------------------------------------

@router.get("/demo/pour-moi")
def demo_pour_moi(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """CE prof peut-il visiter une démonstration, et laquelle ? Sans jeton.

    Le jeton n'est PAS émis ici, à dessein : il ne vaut que cinq minutes, et le menu reste
    affiché bien plus longtemps que ça. Il naît au clic, dans `/demo/aller`. L'écran n'a besoin
    ici que de savoir s'il doit griser l'entrée, et de la raison à mettre dans sa bulle d'aide —
    une entrée grisée sans explication ne dit rien à personne."""
    if mode_demo():
        return {"ici": True, "disponible": False}

    niveau_id = user.travail_niveau_id or user.niveau_id
    if not niveau_id:
        return {"disponible": False, "raison": "Choisissez d’abord votre niveau dans Mon profil."}

    ligne = (
        db.query(Demo, Niveau.nom)
        .join(Referentiel, Referentiel.id == Demo.referentiel_id)
        .join(Niveau, Niveau.id == Referentiel.niveau_id)
        .filter(Niveau.id == niveau_id)
        .first()
    )
    if not ligne:
        return {"disponible": False,
                "raison": "Aucune démonstration n’existe encore pour votre niveau."}
    d, niveau_nom = ligne
    if d.statut not in _STATUTS_VISITABLES:
        return {"disponible": False,
                "raison": f"La démonstration de {niveau_nom} est en préparation."}
    if not d.url:
        return {"disponible": False,
                "raison": f"La démonstration de {niveau_nom} n’est pas encore en ligne."}
    if not _secret():
        return {"disponible": False,
                "raison": "La démonstration n’est pas configurée sur ce serveur."}
    return {"disponible": True, "niveau": niveau_nom}


@router.get("/demo/aller")
def demo_aller(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Le clic sur l'entrée du menu : fabrique le jeton MAINTENANT et redirige.

    Une vraie redirection, et pas une adresse rendue en JSON puis ouverte en JavaScript : le
    navigateur bloque les fenêtres ouvertes après un appel réseau. Ici l'entrée du menu est un
    lien ordinaire vers cette route, le navigateur suit, rien n'est bloqué — et le jeton est
    aussi frais que le clic."""
    etat = demo_pour_moi(user=user, db=db)
    if not etat.get("disponible"):
        raise HTTPException(409, etat.get("raison") or "Démonstration indisponible.")

    niveau_id = user.travail_niveau_id or user.niveau_id
    d = (db.query(Demo)
           .join(Referentiel, Referentiel.id == Demo.referentiel_id)
           .filter(Referentiel.niveau_id == niveau_id)
           .first())
    matiere_id = user.travail_matiere_id or user.subject_id
    return RedirectResponse(
        passage(d.url, user.email, user.prenom, user.nom,
                _nom(db, Matiere, matiere_id), _nom(db, Niveau, niveau_id)),
        status_code=307,
    )


def passage(url: str, email: str, prenom: str | None, nom: str | None,
            matiere: str | None, niveau: str | None) -> str:
    """L'adresse complète du passage : le jeton signé, fraîchement émis, accroché à l'adresse
    de la démonstration.

    PARTAGÉE (zéro copie) entre le passage du PROF — qui part vers la démonstration de son
    niveau — et celui de l'ADMIN, qui part vers n'importe laquelle depuis Admin → Démos. Une
    seule fabrique de jeton : le jour où sa charge change, les deux portes changent ensemble.
    Le secret doit être posé ; l'appelant s'en assure avant (il sait quel message rendre)."""
    charge = {
        "typ": _TYPE_JETON,
        "email": email,
        "prenom": prenom,
        "nom": nom,
        # Des NOMS, jamais des identifiants : l'autre base a ses propres clés.
        "matiere": matiere,
        "niveau": niveau,
        "exp": datetime.now(timezone.utc) + _VALIDITE,
    }
    return f"{url}/demo?jeton={jwt.encode(charge, _secret(), algorithm=_ALGO)}"


def secret_pose() -> bool:
    """`DEMO_SECRET` est-il posé sur ce serveur ? Lu ailleurs pour rendre un refus lisible
    plutôt que de laisser la fabrique du jeton échouer sans explication."""
    return _secret() is not None


def _nom(db: Session, modele, cle: int | None) -> str | None:
    if not cle:
        return None
    ligne = db.get(modele, cle)
    return ligne.nom if ligne else None


# ---------------------------------------------------------------------------
# Côté instance de DÉMONSTRATION — où le prof arrive
# ---------------------------------------------------------------------------

@router.get("/demo/etat")
def demo_etat(db: Session = Depends(get_db)):
    """Sans authentification, à dessein : l'écran doit savoir qu'il est en démonstration AVANT
    que quiconque soit connecté, sinon le bandeau n'apparaîtrait qu'après coup.

    Rend AUSSI le couple que cette base sert — « BTS · BTS CIEL Option A » —, pour que le bandeau
    ne dise pas seulement « vous êtes en démonstration » mais « en démonstration de QUOI ». Sans
    lui, un prof qui ouvre deux démonstrations dans deux onglets ne sait plus laquelle il regarde.

    Le couple se LIT, il ne se déclare pas : c'est celui des référentiels réellement découpés de
    cette base. Plusieurs référentiels y sont possibles ; on les nomme tous plutôt que d'en élire
    un au hasard. Aucun découpé : `couple` reste vide et le bandeau garde sa phrase seule.
    """
    if not mode_demo():
        return {"mode_demo": False, "couple": None}

    # Les colonnes de tri font PARTIE du SELECT : avec un DISTINCT, PostgreSQL refuse de trier
    # sur une colonne qu'il ne rend pas (« for SELECT DISTINCT, ORDER BY expressions must appear
    # in select list »). Sans elles, la route répondait 500 et l'écran de démonstration perdait
    # d'un coup son bandeau ET son filigrane — sans rien afficher qui l'explique.
    couples = [
        f"{cycle} · {niveau}"
        for cycle, niveau, _co, _no in db.query(Cycle.nom, Niveau.nom, Cycle.ordre, Niveau.ordre)
                                        .join(Niveau, Niveau.cycle_id == Cycle.id)
                                        .join(Referentiel, Referentiel.niveau_id == Niveau.id)
                                        .filter(Referentiel.decoupe_valide.is_(True))
                                        .order_by(Cycle.ordre, Niveau.ordre)
                                        .distinct()
                                        .all()
    ]
    return {"mode_demo": True, "couple": " / ".join(couples) or None}


class EntrerBody(BaseModel):
    jeton: str


@router.post("/demo/entrer")
def demo_entrer(body: EntrerBody, response: Response, request: Request,
                db: Session = Depends(get_db)):
    """Vérifie le jeton, retrouve ou crée le compte du prof, pose les cookies de session.

    Refusée hors mode démonstration : c'est une porte d'entrée sans mot de passe. Elle n'a de
    sens que là où toutes les données sont jetables, et nulle part ailleurs."""
    if not mode_demo():
        raise HTTPException(404, "Cette adresse n’existe pas sur ce serveur.")
    secret = _secret()
    if not secret:
        raise HTTPException(503, "La démonstration n’est pas configurée sur ce serveur.")
    try:
        charge = jwt.decode(body.jeton, secret, algorithms=[_ALGO])
    except ExpiredSignatureError:
        raise HTTPException(401, "Ce lien a expiré. Repartez de votre espace et recommencez.")
    except JWTError:
        raise HTTPException(401, "Lien de démonstration invalide.")
    if charge.get("typ") != _TYPE_JETON:
        raise HTTPException(401, "Lien de démonstration invalide.")
    email = (charge.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(401, "Lien de démonstration invalide.")

    user = db.query(User).filter(User.email == email).first()
    premiere_visite = user is None
    if premiere_visite:
        user = _creer_visiteur(db, email, charge)
    # LA COPIE SE DÉCIDE SUR L'ÉTAT, PAS SUR L'ANCIENNETÉ DU COMPTE. Elle ne se faisait qu'à la
    # création : un visiteur dont la copie avait échoué — ou dont le contenu avait disparu —
    # retrouvait une application vide à chaque visite, définitivement, sans aucun moyen de la
    # remplir. Constaté le 07/08/2026. On regarde donc ce qu'il A, pas ce qu'il est.
    #
    # Ce n'est pas une remise à zéro : dès qu'il possède UNE séquence, une séance ou une activité,
    # on ne touche à rien. Ce qu'il a fabriqué ou effacé lui appartient, y compris s'il a tout
    # supprimé exprès et gardé une seule ligne.
    if not _a_du_contenu(db, user):
        _copier_le_gabarit(db, user)
    user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    access = comptes.create_access_token(user.email)
    refresh = comptes.create_refresh_token(db, user.email)
    from backend.securite.auth import _set_cookies   # import local : évite un cycle au chargement
    _set_cookies(response, access, refresh)
    return {"status": "ok", "premiere_visite": premiere_visite,
            "prenom": user.prenom, "email": user.email}


def _a_du_contenu(db: Session, user: User) -> bool:
    """Ce visiteur a-t-il déjà quelque chose à lui dans le bac à sable ? Les trois tables, parce
    qu'une seule ne suffit pas : un prof peut n'avoir gardé que ses séquences."""
    return any(
        db.query(modele).filter(modele.user_id == user.id).first() is not None
        for modele in (Sequence, Seance, Activite)
    )


def _creer_visiteur(db: Session, email: str, charge: dict) -> User:
    """Le compte du prof DANS la base de démonstration. Vérifié et actif d'emblée : il vient
    d'une instance qui l'a déjà authentifié. Son mot de passe est tiré au hasard et jeté — la
    seule porte d'entrée ici est le jeton, il ne faut pas qu'une seconde existe."""
    import secrets as _secrets
    user = User(
        email=email,
        password_hash=comptes._hash_password(_secrets.token_urlsafe(32)),
        is_verified=True,
        is_active=True,
        prenom=charge.get("prenom"),
        nom=charge.get("nom"),
        subject_id=_id_par_nom(db, Matiere, charge.get("matiere")),
        niveau_id=_id_par_nom(db, Niveau, charge.get("niveau")),
    )
    db.add(user)
    db.flush()
    return user


def _id_par_nom(db: Session, modele, nom: str | None) -> int | None:
    """Le nom vient de l'autre base ; ici il peut ne correspondre à rien (une démonstration ne
    porte qu'un niveau et quelques matières). Absent = NULL, le prof choisira sur place."""
    if not nom:
        return None
    ligne = db.query(modele).filter(modele.nom == nom).first()
    return ligne.id if ligne else None


def _copier_le_gabarit(db: Session, user: User) -> None:
    """Recopie le contenu d'exemple au nom du visiteur : séquences, séances, activités, avec
    leurs liens et leurs positions.

    POURQUOI COPIER PLUTÔT QUE PARTAGER. Les écrans du prof ne montrent que ce qui lui
    appartient — c'est vrai à une trentaine d'endroits. Partager le contenu du gabarit voudrait
    dire ouvrir chacun de ces filtres, avec le risque d'en ouvrir un de trop. Copier ne touche à
    rien : le prof arrive chez lui, avec de quoi jouer, et personne ne voit ce qu'il en fait."""
    reglage = db.get(Setting, _CLE_GABARIT)
    if not reglage or not (reglage.value or "").strip():
        return
    gabarit = db.query(User).filter(User.email == reglage.value.strip().lower()).first()
    if not gabarit or gabarit.id == user.id:
        return

    sequences = db.query(Sequence).filter(Sequence.user_id == gabarit.id).all()
    seances = db.query(Seance).filter(Seance.user_id == gabarit.id).all()
    activites = db.query(Activite).filter(Activite.user_id == gabarit.id).all()

    # Ancien identifiant → nouveau : les liens séance→séquence et activité→séance doivent suivre
    # la copie, sinon le prof trouve des séances non rangées et des activités orphelines.
    corr_sequences: dict[int, int] = {}
    corr_seances: dict[int, int] = {}

    for s in sequences:
        neuve = Sequence(
            user_id=user.id, titre=s.titre, contexte=s.contexte, ampleur=s.ampleur,
            competences=s.competences, matiere=s.matiere, niveau=s.niveau,
        )
        db.add(neuve)
        db.flush()
        corr_sequences[s.id] = neuve.id

    for s in seances:
        neuve = Seance(
            user_id=user.id,
            sequence_id=corr_sequences.get(s.sequence_id) if s.sequence_id else None,
            position=s.position, titre=s.titre, description=s.description,
            matiere=s.matiere, niveau=s.niveau, duree_minutes=s.duree_minutes,
            mode=s.mode, competences=s.competences, materiel=s.materiel,
            esquisse=s.esquisse, contraintes=s.contraintes, style=s.style, resultat=s.resultat,
        )
        db.add(neuve)
        db.flush()
        corr_seances[s.id] = neuve.id

    for a in activites:
        db.add(Activite(
            user_id=user.id,
            seance_id=corr_seances.get(a.seance_id) if a.seance_id else None,
            position=a.position, activite_type_id=a.activite_type_id,
            activite_label=a.activite_label, sous_type=a.sous_type, nb=a.nb,
            avec_correction=a.avec_correction, objet=a.objet, matiere=a.matiere,
            niveau=a.niveau, ton=a.ton, texte_source=a.texte_source, resultat=a.resultat,
            statut=a.statut,
        ))
    db.flush()
