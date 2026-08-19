# -*- coding: utf-8 -*-
"""TRANSPORTER UN RÉFÉRENTIEL D'UNE INSTALLATION À L'AUTRE — export d'un côté, import de l'autre.

POURQUOI CE MODULE EXISTE. Un référentiel se construit sur le poste de développement : la
procédure est longue, elle se reprend en plusieurs fois, et on ne la refait pas en production.
Or un déploiement porte le CODE et la STRUCTURE de la base — jamais son contenu. Le référentiel
restait donc là où il était né. Constaté le 16/08/2026 : le référentiel Collège (5e, 4e, 3e)
absent du serveur après un déploiement pourtant complet.

LES DEUX BASES NE SE PARLENT PAS, ET C'EST VOULU. L'export produit un fichier, l'import le lit.
Personne n'ouvre de connexion vers l'autre monde : rien ne part sans qu'on l'ait porté soi-même.

CE QUI VOYAGE, et rien d'autre :
  - la ligne du référentiel (le document, ses prompts, ses drapeaux de validation) ;
  - les niveaux qu'il dessert ;
  - ses matières, ses types d'activité et les précisions de ces types ;
  - ses unités découpées, AVEC leurs vecteurs — c'est ce qui rend l'opération gratuite : rien
    n'est recalculé, donc aucun appel d'IA.

CE QUI NE VOYAGE PAS : les niveaux et les cycles eux-mêmes. Ils viennent des migrations et
portent les mêmes identifiants des deux côtés (vérifié le 16/08/2026 : Collège = 6, 7, 8, 9 ici
comme sur le serveur). Le PDF non plus — il vit dans `REFERENTIELS/`, hors base et hors dépôt.

LES IDENTIFIANTS SONT RÉATTRIBUÉS À L'ARRIVÉE. Le référentiel 21 du poste peut être le 34 en
production : rien ne garantit qu'un numéro soit libre. Seuls les `niveau_id` sont conservés, pour
la raison ci-dessus.

TOUT OU RIEN. L'import se fait dans une seule transaction : une erreur au milieu et la base n'a
pas bougé. On ne laisse jamais un référentiel à moitié posé — c'est l'état le plus cher à
diagnostiquer, parce que l'application répond quand même.
"""
import json
from datetime import datetime, date, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.models_db import (ActiviteType, Matiere, ReferentielChunk,
                                    ReferentielChunkMatiere, ReferentielDocument,
                                    ReferentielNiveau, ReferentielTypePrecision)

# Le numéro de format du fichier. Il changera le jour où une table s'ajoute au voyage : un
# fichier ancien doit être refusé clairement, pas importé à moitié.
FORMAT = 2

# L'ORDRE COMPTE — c'est celui des dépendances. `referentiel_type_precisions` vient après
# `types_activite` parce qu'elle le désigne ; les documents avant les unités, qui les désignent ;
# la liaison unité <-> matière en dernier, elle désigne les deux.
#
# LES NOMS SE LISENT DANS LES MODÈLES, ils ne sont pas recopiés : une table renommée un jour
# entraînerait ce module avec elle, au lieu de le laisser chercher un nom qui n'existe plus.
TABLES = tuple(m.__tablename__ for m in (
    ReferentielNiveau, Matiere, ActiviteType, ReferentielTypePrecision,
    ReferentielDocument, ReferentielChunk, ReferentielChunkMatiere,
))


def _lisible(valeur):
    """Ce que JSON ne sait pas écrire, traduit sans rien perdre.

    Les vecteurs de pgvector arrivent en tableau numpy : `tolist()` les rend en nombres ordinaires,
    et c'est exactement ce que la colonne réaccepte à l'arrivée."""
    if isinstance(valeur, (datetime, date)):
        return {"__type__": "datetime", "valeur": valeur.isoformat()}
    if hasattr(valeur, "tolist"):
        return valeur.tolist()
    return valeur


def _relu(valeur):
    if isinstance(valeur, dict) and valeur.get("__type__") == "datetime":
        return datetime.fromisoformat(valeur["valeur"])
    return valeur


def _lignes(db: Session, table: str, condition: str, params: dict) -> list[dict]:
    rows = db.execute(text(f"SELECT * FROM {table} WHERE {condition}"), params).mappings().all()
    return [{c: _lisible(v) for c, v in r.items()} for r in rows]


def exporter(db: Session, referentiel_id: int) -> dict:
    """Rassemble un référentiel et tout ce qui pend dessous. Ne modifie rien."""
    ref = db.execute(text("SELECT * FROM referentiels WHERE id = :id"),
                     {"id": referentiel_id}).mappings().first()
    if ref is None:
        raise ValueError(f"Aucun référentiel n° {referentiel_id}.")

    # Le nom du niveau porteur voyage à titre d'ÉTIQUETTE : il ne sert pas à l'import (qui suit
    # les identifiants), mais il permet de savoir ce que contient un fichier sans l'ouvrir.
    etiquette = db.execute(
        text("""SELECT c.nom || ' · ' || n.nom FROM niveaux n
                JOIN cycles c ON c.id = n.cycle_id WHERE n.id = :nid"""),
        {"nid": ref["niveau_id"]}).scalar()

    contenu = {
        "format": FORMAT,
        "exporte_le": datetime.now(timezone.utc).isoformat(),
        "etiquette": etiquette or "",
        "referentiel": {c: _lisible(v) for c, v in ref.items()},
        "tables": {},
    }
    # CE QUI NE SE RATTACHE PAS DIRECTEMENT AU RÉFÉRENTIEL. Ces tables-là ne portent pas de
    # `referentiel_id` : elles pendent d'une autre table qui, elle, en porte un. Déclarées ICI,
    # dans leur unique lectrice, comme le veut le filet « rien en dur ».
    par_ricochet = {
        "referentiel_type_precisions":
            "type_activite_id IN (SELECT id FROM types_activite WHERE referentiel_id = :id)",
        "referentiel_chunk_matieres":
            "chunk_id IN (SELECT id FROM referentiel_chunks WHERE referentiel_id = :id)",
    }
    for table in TABLES:
        condition = par_ricochet.get(table, "referentiel_id = :id")
        contenu["tables"][table] = _lignes(db, table, condition, {"id": referentiel_id})
    return contenu


def _inserer(db: Session, table: str, ligne: dict) -> int | None:
    """Insère une ligne SANS son identifiant d'origine, et rend celui que la base attribue.

    None pour une table de liaison, qui n'a pas d'identifiant à rendre — et personne ne le lui
    demande : rien ne la désigne."""
    valeurs = {c: _relu(v) for c, v in ligne.items() if c != "id"}
    colonnes = ", ".join(valeurs)
    reperes = ", ".join(f":{c}" for c in valeurs)
    requete = f"INSERT INTO {table} ({colonnes}) VALUES ({reperes})"
    # Les tables SANS colonne `id` : l'insertion ne peut rien rendre, et rien n'a besoin de les
    # désigner. `referentiel_chunk_matieres` est une liaison pure — sa clé, ce sont ses deux côtés.
    sans_id = {"referentiel_chunk_matieres"}
    if table in sans_id:
        db.execute(text(requete), valeurs)
        return None
    return db.execute(text(requete + " RETURNING id"), valeurs).scalar()


def resume(contenu: dict) -> dict:
    """Ce que le fichier contient, pour l'annoncer avant de l'installer."""
    return {
        "etiquette": contenu.get("etiquette", ""),
        "exporte_le": contenu.get("exporte_le", ""),
        "compte": {t: len(contenu.get("tables", {}).get(t, [])) for t in TABLES},
    }


def importer(db: Session, contenu: dict) -> dict:
    """Pose le référentiel dans CETTE base. Tout ou rien : l'appelant valide ou annule.

    NE VALIDE PAS LUI-MÊME : c'est la route qui décide, et c'est ce qui permet de tout défaire
    si un contrôle échoue plus loin."""
    if contenu.get("format") != FORMAT:
        raise ValueError(
            f"Fichier au format {contenu.get('format')}, attendu {FORMAT}. "
            "Il vient d'une version différente de l'application — réexportez-le.")

    ref = dict(contenu["referentiel"])
    niveau_id = _relu(ref.get("niveau_id"))

    # LE REFUS QUI PROTÈGE. `referentiel_niveaux` porte une contrainte d'unicité sur le niveau :
    # un second référentiel visant la même classe serait rejeté par la base, mais avec un message
    # de contrainte que personne ne comprend. On le dit ici, en français, avant d'écrire.
    vises = [_relu(l["niveau_id"]) for l in contenu["tables"].get("referentiel_niveaux", [])]
    for nid in set(vises) | {niveau_id}:
        occupant = db.execute(
            text("""SELECT n.nom FROM referentiel_niveaux rn JOIN niveaux n ON n.id = rn.niveau_id
                    WHERE rn.niveau_id = :nid"""), {"nid": nid}).scalar()
        if occupant:
            raise ValueError(
                f"Un référentiel dessert déjà « {occupant} » dans cette base. "
                "Supprimez-le avant d'importer celui-ci — rien n'a été modifié.")

    # `nom_fixe` est unique lui aussi, et il ne se déduit pas des niveaux : un référentiel peut
    # occuper le nom sans desservir aucune classe. Sans ce contrôle, l'import tombait sur une
    # violation de contrainte — un message que personne ne peut lire.
    if db.execute(text("SELECT 1 FROM referentiels WHERE nom_fixe = :n"),
                  {"n": ref.get("nom_fixe")}).scalar():
        raise ValueError(
            f"Un référentiel nommé « {ref.get('nom_fixe')} » existe déjà dans cette base. "
            "Supprimez-le avant d'importer celui-ci — rien n'a été modifié.")

    nouvel_id = _inserer(db, "referentiels", ref)

    # ANCIEN IDENTIFIANT -> NOUVEAU, table par table. Les types, les documents, les unités et les
    # matières sont tous désignés par quelqu'un : la correspondance se tient pour toutes, et
    # `_REDIRECTIONS` dit qui suit qui. Une seule mécanique, plus un cas particulier par table.
    # LES IDENTIFIANTS CHANGENT À L'ARRIVÉE : une ligne qui en désigne une autre doit suivre le
    # NOUVEAU, sinon elle pointe sur une ligne d'un autre référentiel — ou sur rien.
    # {table : {colonne qui désigne : table désignée}}
    redirections = {
        "referentiel_type_precisions": {"type_activite_id": "types_activite"},
        "referentiel_chunks": {"document_id": "referentiel_documents"},
        "referentiel_chunk_matieres": {"chunk_id": "referentiel_chunks",
                                       "matiere_id": "matieres"},
    }
    correspondances: dict[str, dict[int, int]] = {t: {} for t in TABLES}
    compte: dict[str, int] = {}

    for table in TABLES:
        pose = 0
        for ligne in contenu["tables"].get(table, []):
            ligne = dict(ligne)
            ancien = ligne.get("id")
            if "referentiel_id" in ligne:
                ligne["referentiel_id"] = nouvel_id
            for colonne, visee in redirections.get(table, {}).items():
                ligne[colonne] = correspondances[visee][_relu(ligne[colonne])]
            neuf = _inserer(db, table, ligne)
            if neuf is not None and ancien is not None:
                correspondances[table][ancien] = neuf
            pose += 1
        compte[table] = pose

    return {"referentiel_id": nouvel_id, "compte": compte,
            "etiquette": contenu.get("etiquette", "")}
