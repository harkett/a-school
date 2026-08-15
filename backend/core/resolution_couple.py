"""Résolution NOM → ID du couple du prof (matière, niveau) — une seule règle, un seul endroit.

Le profil range matière et niveau UNIQUEMENT par CLÉ (users.subject_id / niveau_id / travail_*_id) :
le nom vit dans `matieres`/`niveaux` et se relit par get, jamais recopié ailleurs. Deux sens ici :
nom → id à l'écriture, id → nom à la lecture (matiere_nom_de_id / niveau_nom_de_id).

UNE MATIÈRE SE RÉSOUT DANS UN RÉFÉRENTIEL, JAMAIS GLOBALEMENT. Depuis que chaque référentiel
possède ses matières, plusieurs « Mathématiques » coexistent en base — une par diplôme qui en
nomme une. Chercher par le nom seul ne pouvait donc plus rendre qu'un doublon ambigu, c'est-à-dire
rien. `matiere_id_du_nom` demande le NIVEAU : il donne le référentiel, le référentiel donne SA
matière. Le niveau, lui, reste unique par son nom (cf. `niveau_id_du_nom`).

ET LE NIVEAU DONNE SON RÉFÉRENTIEL PAR `referentiel_du_niveau` (15/08/2026), jamais en filtrant
`referentiels.niveau_id` : depuis qu'un programme de cycle sert plusieurs années, cette colonne ne
dit plus que le niveau porteur du document.
"""
from sqlalchemy.orm import Session

from backend.core.models_db import Matiere, Niveau, Referentiel, ReferentielNiveau


def referentiel_du_niveau(db: Session, niveau_id: int | None) -> int | None:
    """LA réponse à « quel référentiel sert ce niveau ? » — id, ou None.

    UNE SEULE PORTE (15/08/2026). Huit endroits posaient cette question à la main, chacun en
    filtrant `referentiels.niveau_id`. Cette colonne ne répond plus : elle dit le niveau PORTEUR
    (le dossier du PDF, le nom, la collection), pas les niveaux servis. Un programme de CYCLE en
    sert plusieurs — le cycle 4 tient la 5e, la 4e et la 3e — et huit lectures directes, c'est
    huit occasions d'en oublier une : celle-là continuerait de répondre « aucun référentiel » à un
    prof de 5e, sans erreur, juste une page vide.

    `UNIQUE(referentiel_niveaux.niveau_id)` garantit qu'il n'y a jamais deux réponses possibles :
    pas de garde « len == 1 » à écrire ici, la base la porte."""
    if not niveau_id:
        return None
    return (db.query(ReferentielNiveau.referentiel_id)
              .filter(ReferentielNiveau.niveau_id == niveau_id)
              .scalar())


def recalculer_nom_affichage(db: Session, referentiel_id: int) -> str:
    """Réécrit `referentiels.nom_affichage` depuis les niveaux réellement desservis, et le rend.

    « 5e, 4e, 3e » pour un document de cycle, « BTS CRSA » pour un document d'un seul niveau.
    L'ordre est celui du cycle (`niveaux.ordre`), celui que l'administrateur a sous les yeux dans
    ses menus — pas l'ordre d'insertion des rattachements, qui ne veut rien dire pour un lecteur.

    À APPELER PARTOUT OÙ UN RATTACHEMENT CHANGE. La colonne est une copie : elle ne se corrige pas
    toute seule, et un libellé faux est pire qu'un libellé absent — il affirme. Aujourd'hui un seul
    appelant (la création d'un référentiel) ; le jour où un écran permettra de rattacher un niveau,
    il devra appeler ceci dans le même geste.

    Ne commit pas : l'appelant décide quand écrire, dans SA transaction."""
    noms = [n for (n,) in db.query(Niveau.nom)
                            .join(ReferentielNiveau, ReferentielNiveau.niveau_id == Niveau.id)
                            .filter(ReferentielNiveau.referentiel_id == referentiel_id)
                            .order_by(Niveau.ordre).all()]
    nom = ", ".join(noms)
    db.query(Referentiel).filter(Referentiel.id == referentiel_id).update(
        {"nom_affichage": nom or None}, synchronize_session=False)
    return nom


def referentiel_du_niveau_nomme(db: Session, nom: str | None) -> int | None:
    """Même question, posée avec le NOM du niveau — pour les appelants qui tiennent le couple du
    prof en clair (`couple_de_travail` rend des noms). Passe par `niveau_id_du_nom`, donc None
    aussi quand le nom désigne deux niveaux de deux cycles : on ne devine pas lequel."""
    return referentiel_du_niveau(db, niveau_id_du_nom(db, nom))


def matiere_id_du_nom(db: Session, nom: str | None, niveau_id: int | None) -> int | None:
    """id de LA matière de ce nom DANS le référentiel de ce niveau, sinon None.

    None si le nom ou le niveau manque, si le niveau n'a pas de référentiel, ou si son
    référentiel ne nomme pas cette matière. Seules les matières RETENUES par l'admin (`validee`)
    et actives sont résolues : une proposition de la détection n'entre jamais dans un profil.
    L'unicité (referentiel_id, nom) garantit qu'il n'y a jamais deux réponses possibles."""
    if not nom or not niveau_id:
        return None
    rid = referentiel_du_niveau(db, niveau_id)
    if rid is None:
        return None
    return (db.query(Matiere.id)
              .filter(Matiere.referentiel_id == rid,
                      Matiere.nom == nom,
                      Matiere.validee.is_(True),
                      Matiere.actif.is_(True))
              .scalar())


def niveau_id_du_nom(db: Session, nom: str | None) -> int | None:
    """id du niveau dont le nom == `nom`, si et seulement s'il y en a exactement un ; sinon None."""
    if not nom:
        return None
    rows = db.query(Niveau.id).filter(Niveau.nom == nom).all()
    return rows[0][0] if len(rows) == 1 else None


def matiere_nom_de_id(db: Session, matiere_id: int | None) -> str | None:
    """Nom de la matière pour cet id — get pur (le nom vit dans `matieres`, jamais recopié)."""
    if not matiere_id:
        return None
    return db.query(Matiere.nom).filter(Matiere.id == matiere_id).scalar()


def niveau_nom_de_id(db: Session, niveau_id: int | None) -> str | None:
    """Nom du niveau pour cet id — get pur (le nom vit dans `niveaux`, jamais recopié)."""
    if not niveau_id:
        return None
    return db.query(Niveau.nom).filter(Niveau.id == niveau_id).scalar()
