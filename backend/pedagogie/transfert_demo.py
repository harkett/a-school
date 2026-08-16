# -*- coding: utf-8 -*-
"""TRANSPORTER LA FICHE D'UNE DÉMONSTRATION D'UNE INSTALLATION À L'AUTRE.

POURQUOI CE MODULE EXISTE, ET SÉPARÉMENT DU RÉFÉRENTIEL. Constaté le 16/08/2026 : la
démonstration du Collège tournait en production — son adresse répondait, son compartiment de
données était en place — mais aucun professeur ne la voyait. Sa FICHE, elle, était restée sur le
poste de développement. Le déploiement porte le code, jamais les données saisies.

Un référentiel et une démonstration ne vivent pas au même rythme : le premier se dépose une fois
et bouge rarement, la seconde se refait, se corrige, se remplace. Les mêler obligerait à
retransporter tout un référentiel pour rétablir une vitrine. Deux objets, deux transferts.

CE QUI VOYAGE : le nom du compartiment de données, les trois compteurs, la date de fabrication,
les défauts connus et les notes.

CE QUI NE VOYAGE PAS, ET C'EST VOULU :
  - L'ADRESSE. Elle est propre à l'installation — `localhost:8096` ici, `demo-college4e.aschool.fr`
    là-bas — et c'est ELLE qui ouvre la porte au professeur. Importer l'adresse du poste de
    développement en production ouvrirait une entrée de menu vers une machine qui n'existe pas.
    Elle se renseigne à l'arrivée, une fois qu'on sait où la démonstration est montée.
  - LE CONTENU du compartiment (séquences, séances, activités). C'est une base entière ; elle se
    verse avec les outils de base de données, pas par un fichier d'écran.

LE RATTACHEMENT SE FAIT PAR LE NOM DU RÉFÉRENTIEL, jamais par son numéro : le référentiel 21 du
poste peut être le 34 en production. Si le référentiel n'est pas là, on refuse en le disant —
une fiche orpheline ne montrerait rien à personne.

REMPLACER EST POSSIBLE, MAIS DEMANDÉ. Une fiche déjà présente n'est jamais écrasée en silence :
l'import refuse et dit qu'il faut confirmer. C'est l'écran qui pose les deux questions.
"""
import json
from datetime import datetime, date, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.models_db import Demo

# Le numéro de format du fichier. Il changera le jour où un champ s'ajoute au voyage : un fichier
# ancien doit être refusé clairement, pas importé à moitié.
FORMAT = 1

# LES CHAMPS SE LISENT DANS LE MODÈLE, aucun n'est recopié ici : une colonne ajoutée un jour à la
# fiche voyagera d'elle-même, et une colonne renommée entraînera ce module avec elle au lieu de le
# laisser chercher un nom qui n'existe plus.
#
# CE QUI RESTE À QUAI, et pourquoi ça se lit dans le modèle plutôt qu'ici : la clé primaire et la
# clé étrangère sont réattribuées à l'arrivée (le référentiel 21 du poste peut être le 34 en
# production) ; les autres portent `info={"voyage": False}` sur leur colonne — la règle vit avec
# la donnée, à un seul endroit, et non dans une liste de noms qui se périme en silence.
CHAMPS = tuple(
    c.name for c in Demo.__table__.columns
    if not c.primary_key and not c.foreign_keys and c.info.get("voyage", True)
)


def _lisible(valeur):
    if isinstance(valeur, (datetime, date)):
        return {"__type__": "datetime", "valeur": valeur.isoformat()}
    return valeur


def _relu(valeur):
    if isinstance(valeur, dict) and valeur.get("__type__") == "datetime":
        return datetime.fromisoformat(valeur["valeur"])
    return valeur


def exporter(db: Session, demo_id: int) -> dict:
    """Rassemble la fiche d'une démonstration. Ne modifie rien."""
    fiche = db.execute(text("SELECT * FROM demos WHERE id = :id"),
                       {"id": demo_id}).mappings().first()
    if fiche is None:
        raise ValueError(f"Aucune démonstration n° {demo_id}.")

    # Le nom du référentiel est LA clé du rattachement à l'arrivée. Son libellé lisible et le
    # niveau porteur voyagent en plus, comme étiquette : on sait ce que contient un fichier sans
    # avoir à l'ouvrir.
    ref = db.execute(
        text("""SELECT r.nom_fixe, r.nom_affichage, c.nom AS cycle, n.nom AS niveau
                FROM referentiels r
                JOIN niveaux n ON n.id = r.niveau_id
                JOIN cycles  c ON c.id = n.cycle_id
                WHERE r.id = :id"""), {"id": fiche["referentiel_id"]}).mappings().first()
    if ref is None:
        raise ValueError("Cette démonstration ne désigne aucun référentiel — fiche inutilisable.")

    return {
        "format": FORMAT,
        "exporte_le": datetime.now(timezone.utc).isoformat(),
        "referentiel_nom_fixe": ref["nom_fixe"],
        "etiquette": f"{ref['cycle']} · {ref['niveau']}",
        "referentiel_affichage": ref["nom_affichage"] or "",
        "fiche": {c: _lisible(fiche[c]) for c in CHAMPS},
    }


def resume(contenu: dict) -> dict:
    """Ce que le fichier contient, pour l'annoncer avant de l'installer."""
    fiche = contenu.get("fiche", {})
    return {
        "etiquette": contenu.get("etiquette", ""),
        "referentiel": contenu.get("referentiel_affichage", ""),
        "exporte_le": contenu.get("exporte_le", ""),
        "nom_base": fiche.get("nom_base", ""),
        "compte": {
            "activites": fiche.get("nb_activites", 0),
            "sequences": fiche.get("nb_sequences", 0),
            "seances": fiche.get("nb_seances", 0),
        },
    }


def importer(db: Session, contenu: dict, remplacer: bool = False) -> dict:
    """Pose la fiche dans CETTE base. Tout ou rien : l'appelant valide ou annule.

    NE VALIDE PAS LUI-MÊME : c'est la route qui décide, et c'est ce qui permet de tout défaire si
    un contrôle échoue plus loin."""
    if contenu.get("format") != FORMAT:
        raise ValueError(
            f"Fichier au format {contenu.get('format')}, attendu {FORMAT}. "
            "Il vient d'une version différente de l'application — réexportez-le.")

    nom_fixe = contenu.get("referentiel_nom_fixe")
    if not nom_fixe:
        raise ValueError("Ce fichier ne dit pas à quel référentiel la démonstration se rattache.")

    # LE RATTACHEMENT PAR LE NOM. Sans le référentiel, la fiche ne montrerait rien : le menu du
    # professeur part de SON niveau, remonte au référentiel qui le sert, et cherche la
    # démonstration de ce référentiel-là.
    referentiel_id = db.execute(text("SELECT id FROM referentiels WHERE nom_fixe = :n"),
                                {"n": nom_fixe}).scalar()
    if not referentiel_id:
        raise ValueError(
            f"Le référentiel « {nom_fixe} » n'existe pas dans cette base. "
            "Importez-le d'abord (Admin → Référentiel), puis reprenez ce fichier — "
            "rien n'a été modifié.")

    fiche = {c: _relu(contenu.get("fiche", {}).get(c)) for c in CHAMPS}
    if not fiche.get("nom_base"):
        raise ValueError("Ce fichier ne porte pas le nom de la base de démonstration.")

    # UNE SEULE DÉMONSTRATION PAR RÉFÉRENTIEL (contrainte `uq_demos_referentiel`). Une fiche déjà
    # là n'est jamais écrasée en silence : on refuse, et c'est l'écran qui demande confirmation.
    existante = db.execute(text("SELECT id, url FROM demos WHERE referentiel_id = :r"),
                           {"r": referentiel_id}).mappings().first()
    if existante and not remplacer:
        raise ValueError(
            f"Une démonstration existe déjà pour « {contenu.get('referentiel_affichage') or nom_fixe} ». "
            "Confirmez le remplacement pour l'écraser — rien n'a été modifié.")

    if existante:
        # L'ADRESSE DÉJÀ EN PLACE SURVIT AU REMPLACEMENT. Elle décrit CETTE installation, pas le
        # fichier : l'écraser fermerait la porte aux professeurs sans que personne l'ait demandé.
        affectations = ", ".join(f"{c} = :{c}" for c in CHAMPS)
        db.execute(text(f"UPDATE demos SET {affectations} WHERE id = :id"),
                   {**fiche, "id": existante["id"]})
        return {"demo_id": existante["id"], "remplacee": True,
                "url": existante["url"],
                "etiquette": contenu.get("etiquette", "")}

    colonnes = ", ".join(("referentiel_id",) + CHAMPS)
    reperes = ", ".join(f":{c}" for c in ("referentiel_id",) + CHAMPS)
    nouvel_id = db.execute(
        text(f"INSERT INTO demos ({colonnes}) VALUES ({reperes}) RETURNING id"),
        {**fiche, "referentiel_id": referentiel_id}).scalar()
    return {"demo_id": nouvel_id, "remplacee": False, "url": None,
            "etiquette": contenu.get("etiquette", "")}


def lire_fichier(octets: bytes) -> dict:
    """Le contenu déposé, ou un refus qui dit ce qu'on a vu.

    Les messages sont écrits pour quelqu'un qui vient de déposer un fichier et ne sait pas
    pourquoi ça n'a pas marché — jamais « JSON invalide » tout court."""
    if not octets:
        raise ValueError("Le fichier est vide.")
    try:
        contenu = json.loads(octets.decode("utf-8"))
    except UnicodeDecodeError:
        raise ValueError("Ce fichier n'est pas lisible : ce n'est pas du texte. "
                         "Déposez le fichier .json produit par « Exporter ».")
    except json.JSONDecodeError as e:
        raise ValueError(f"Ce fichier n'est pas un export valide (ligne {e.lineno}). "
                         "Déposez le fichier .json produit par « Exporter », sans le modifier.")
    if not isinstance(contenu, dict) or "fiche" not in contenu:
        raise ValueError("Ce fichier ne contient pas de démonstration. "
                         "Déposez le fichier .json produit par « Exporter ».")
    return contenu
