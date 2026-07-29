"""« Mes contenus » — la bibliothèque à plat du prof (modèle playlist : séquence ⊃ séances ⊃ activités).

Brique 1 (socle) : UNE lecture qui mélange les trois niveaux dans une seule liste, avec pour
chaque ligne son type, son état de rangement (parent ou « non rangée ») et de quoi afficher
l'aperçu HTML. Les activités viennent de la table EXISTANTE `activites_sauvegardees` (zéro
copie, zéro doublon — leur lien de rangement arrivera à la brique rattachement) ; séquences et
séances viennent des tables neuves du socle. Les anciennes « séquences »
(`sequences_sauvegardees`) n'apparaissent PAS ici : ce sont des séances en réalité, elles
seront IMPORTÉES à la brique suivante — jamais deux sources pour la même chose.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.core.models_db import ActiviteSauvegardee, Seance, Sequence, User

router = APIRouter()


def _iso(dt: datetime | None) -> str | None:
    return dt.replace(tzinfo=timezone.utc).isoformat() if dt else None


@router.get("/mes-contenus")
def lister(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sequences = db.query(Sequence).filter(Sequence.user_id == user.id).all()
    seances = db.query(Seance).filter(Seance.user_id == user.id).all()
    activites = db.query(ActiviteSauvegardee).filter(ActiviteSauvegardee.user_id == user.id).all()
    # DÉCISION utilisateur (29/07) : les séances de la bibliothèque viennent UNIQUEMENT de la
    # table NEUVE `seances` — jamais de `sequences_sauvegardees` (l'ancien monde reste à part).
    # L'onglet Séances se remplit par le « Générer » de l'écran Séance, qui écrit dans `seances`.

    titres_sequences = {s.id: s.titre for s in sequences}
    nb_seances_par_sequence: dict[int, int] = {}
    for s in seances:
        if s.sequence_id is not None:
            nb_seances_par_sequence[s.sequence_id] = nb_seances_par_sequence.get(s.sequence_id, 0) + 1

    contenus = []
    for s in sequences:
        contenus.append({
            "type": "sequence",
            "id": s.id,
            "titre": s.titre,
            "matiere": s.matiere,
            "niveau": s.niveau,
            "parent": None,                       # une séquence est le sommet : jamais rangée
            "nb_seances": nb_seances_par_sequence.get(s.id, 0),
            "resultat": None,
            "created_at": _iso(s.created_at),
            "updated_at": _iso(s.updated_at),
        })
    for s in seances:
        parent = None
        if s.sequence_id is not None:
            parent = {"type": "sequence", "id": s.sequence_id,
                      "titre": titres_sequences.get(s.sequence_id, "")}
        contenus.append({
            "type": "seance",
            "id": s.id,
            "titre": s.titre,
            "matiere": s.matiere,
            "niveau": s.niveau,
            "parent": parent,
            "nb_seances": None,
            "duree": s.duree_minutes,
            "mode": None,
            "contexte": s.description,
            "resultat": s.resultat,
            "created_at": _iso(s.created_at),
            "updated_at": _iso(s.updated_at),
        })
    for a in activites:
        contenus.append({
            "type": "activite",
            "id": a.id,
            "titre": a.objet or a.activite_label,
            "matiere": a.matiere,
            "niveau": a.niveau,
            "parent": None,                       # lien de rangement : brique rattachement
            "nb_seances": None,
            "resultat": a.resultat,
            "created_at": _iso(a.created_at),
            "updated_at": None,
        })

    # Plus récent en haut, tous types mélangés (dernière modification, sinon création).
    contenus.sort(key=lambda c: c["updated_at"] or c["created_at"] or "", reverse=True)

    return {
        "contenus": contenus,
        "compteurs": {
            "tout": len(contenus),
            "sequences": len(sequences),
            "seances": len(seances),
            "activites": len(activites),
        },
    }
