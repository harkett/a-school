"""
Dépendances FastAPI partagées.

`get_current_user` : résout le prof courant à partir du cookie d'access (JWT).

Le JWT garde l'email comme identité (`sub`) — **non modifié**. Cette dépendance
ajoute seulement la résolution **email → objet `User`**, pour que les routes
disposent, depuis UN seul endroit, de :
  - `user.id`    → pour les liens entre tables (chantier user_email → user_id) ;
  - `user.email` → là où l'email sert vraiment (envoi de mail, affichage).

Additif et non cassant : n'altère aucun comportement d'auth existant. Reproduit
les mêmes 401 que les helpers `_get_email` actuels.
"""
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models_db import User
from backend import auth as auth_lib


def get_current_user(
    aschool_access: str = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = auth_lib.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(401, "Compte introuvable.")
    return user
