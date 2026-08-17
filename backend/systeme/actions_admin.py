# -*- coding: utf-8 -*-
"""LE CENTRE D'ACTIONS DE L'ADMINISTRATION — ce qui attend un geste humain.

UNE SEULE SOURCE, et c'est tout l'intérêt de ce fichier. L'encart « À traiter » du tableau de
bord l'affiche, la pastille du menu la compte : deux calculs séparés finiraient par dire deux
choses différentes le jour où une règle change d'un côté seulement.

CE QU'EST UNE ACTION : quelque chose que le logiciel ne peut PAS décider seul, et qui attend
donc quelqu'un. Pas un état à surveiller, pas une statistique — un geste. D'où trois propriétés
qui ne se négocient pas :

  · elle DISPARAÎT dès que le geste est fait, parce qu'elle se déduit de la base et ne se marque
    nulle part à la main : rien à cocher, rien à oublier de décocher ;
  · elle dit CE QUI EST ATTENDU, en français, pas l'état constaté ;
  · elle mène à L'ÉCRAN où le geste se fait, en un clic.

LA LISTE EST OUVERTE. Une source = une fonction qui rend des dictionnaires au même moule, et son
nom entre dans `_SOURCES`. Les prochaines sont déjà nommées dans la procédure du 16/08/2026 :
référentiels en attente, démonstrations, retours sans réponse.

Le moule d'une action :
    code   — identifiant stable, pour dédoublonner et pour les tests
    titre  — la phrase du geste attendu
    detail — ce qu'il faut savoir avant de le faire (facultatif)
    page   — l'adresse de l'écran où il se fait
    ecran  — la clé de l'entrée de menu concernée, pour la pastille
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models_db import FeatureVotable
from backend.systeme.admin import _require_admin

router = APIRouter()


# La clé d'écran sert à la PASTILLE : elle dit sur quelle entrée du menu poser le compteur.
# Un mot, pas une adresse — l'adresse est déjà dans `page`, et le menu, lui, range par entrée.
ECRAN_BIENTOT_DISPONIBLE = "bientot-disponible"


def _annonces_en_attente(db: Session) -> list[dict]:
    """Les fonctionnalités LIVRÉES que personne n'a encore annoncées aux professeurs.

    C'est la seule décision qui reste à un humain une fois la livraison faite : le code sait
    qu'une fonctionnalité existe (la migration pose `livree`), il ne sait pas s'il faut la
    mettre en avant. La ligne s'efface d'elle-même quand la case « Nouveauté » est cochée —
    ou quand une autre annonce prend la place, puisqu'il n'y en a qu'une à la fois.
    """
    lignes = (
        db.query(FeatureVotable)
        .filter(FeatureVotable.livree.is_(True), FeatureVotable.nouveaute.is_(False))
        .order_by(FeatureVotable.ordre, FeatureVotable.id)
        .all()
    )
    return [
        {
            "code":   f"annonce:{f.code}",
            "titre":  f"« {f.label} » est livrée : l’annoncer aux professeurs ?",
            "detail": "Cochez « Nouveauté » sur sa ligne. Une seule annonce à la fois : "
                      "celle qui est en place sera remplacée.",
            "page":   "/admin/bientot-disponible",
            "ecran":  ECRAN_BIENTOT_DISPONIBLE,
        }
        for f in lignes
    ]


# Les sources, dans l'ordre où elles s'affichent. Ajouter une source = ajouter une fonction
# ci-dessus et son nom ici — l'encart, la pastille et les tests suivent sans être touchés.
_SOURCES = [
    _annonces_en_attente,
]


def actions_en_attente(db: Session) -> list[dict]:
    """Tout ce qui attend un geste, toutes sources confondues.

    Une source qui échoue ne doit pas emporter l'encart entier : le tableau de bord afficherait
    une page vide là où il devrait montrer trois actions. Elle est passée, les autres restent.
    """
    actions: list[dict] = []
    for source in _SOURCES:
        try:
            actions.extend(source(db))
        except Exception:  # noqa: BLE001 — une source muette vaut mieux qu'un écran mort
            continue
    return actions


@router.get("/admin/actions", dependencies=[Depends(_require_admin)])
def get_actions(db: Session = Depends(get_db)):
    """Ce qui attend un geste, pour l'encart « À traiter » ET pour la pastille du menu.

    `par_ecran` épargne à l'écran de recompter : la pastille d'une entrée de menu lit sa clé,
    elle n'applique pas une seconde fois les règles du serveur."""
    actions = actions_en_attente(db)
    par_ecran: dict[str, int] = {}
    for a in actions:
        par_ecran[a["ecran"]] = par_ecran.get(a["ecran"], 0) + 1
    return {"total": len(actions), "actions": actions, "par_ecran": par_ecran}
