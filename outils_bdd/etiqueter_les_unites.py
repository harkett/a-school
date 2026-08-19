# -*- coding: utf-8 -*-
"""Écrit l'étiquetage d'un référentiel : la matière de chaque unité, ou sa portée `formation`.

    docker exec a-school-backend-1 python outils_bdd/etiqueter_les_unites.py <referentiel_id> <fichier.json>
    (ajouter --ecrire pour écrire ; sans lui, il contrôle et n'écrit rien)

D'OÙ VIENT LE FICHIER. D'un agent gratuit, à qui on a donné les matières du référentiel et les
titres de ses unités. Aucun appel payant dans ce chantier : le jugement se fait dehors, cet
outil ne fait que contrôler et poser.

IL CONTRÔLE AVANT D'ÉCRIRE, ET IL REFUSE TOUT EN BLOC. Un étiquetage à moitié posé est le pire
des états : la recherche filtrerait sur les unités liées et perdrait les autres, sans que rien
ne le dise. Les refus :
  - une unité du référentiel absente du fichier, ou une unité du fichier qui n'est pas de ce
    référentiel ;
  - un nom de matière qui n'existe pas dans ce référentiel (une matière inventée par l'agent) ;
  - une portée autre que `matiere` ou `formation` ;
  - une unité `matiere` sans aucune matière, ou une unité `formation` qui en porte ;
  - une matière du référentiel qu'AUCUNE unité ne sert. Ce n'est pas une faute de
    l'étiquetage, c'est une faute de la découpe : le programme de cette matière est dans
    le document, la découpe ne l'en a pas sorti. Étiqueter par-dessus mettrait au vert un
    référentiel amputé — mesuré le 19/08/2026 sur BTS CIEL A, cinq matières sur dix
    vides, et le contrôle « aucune unité sans liaison » passait quand même.

IL EST REJOUABLE. Les liaisons de ces unités sont remplacées, pas ajoutées : rejouer un fichier
corrigé donne exactement l'état du fichier, jamais un mélange des deux passages.
"""
import json
import sys
from pathlib import Path

from sqlalchemy import text

from backend.core.database import session_pour

PORTEES = ("matiere", "formation")


def charger(chemin: Path) -> list[dict]:
    contenu = json.loads(chemin.read_text(encoding="utf-8"))
    unites = contenu.get("unites") if isinstance(contenu, dict) else contenu
    if not isinstance(unites, list) or not unites:
        raise SystemExit(f"ARRET : {chemin.name} ne porte aucune unité.")
    return unites


def controler(db, referentiel_id: int, unites: list[dict]) -> dict[str, int]:
    en_base = {i for (i,) in db.execute(text(
        "SELECT id FROM referentiel_chunks WHERE referentiel_id = :r"), {"r": referentiel_id})}
    if not en_base:
        raise SystemExit(f"ARRET : le référentiel {referentiel_id} n'a aucune unité.")
    matieres = {nom: mid for nom, mid in db.execute(text(
        "SELECT nom, id FROM matieres WHERE referentiel_id = :r AND validee AND actif"),
        {"r": referentiel_id})}

    fautes: list[str] = []
    vus: set[int] = set()
    for u in unites:
        uid = u.get("id")
        if uid in vus:
            fautes.append(f"unité {uid} : deux fois dans le fichier")
        vus.add(uid)
        if uid not in en_base:
            fautes.append(f"unité {uid} : n'appartient pas au référentiel {referentiel_id}")
            continue
        portee = u.get("portee")
        noms = u.get("matieres") or []
        if portee not in PORTEES:
            fautes.append(f"unité {uid} : portée {portee!r} inconnue")
        if portee == "matiere" and not noms:
            fautes.append(f"unité {uid} : portée matiere sans aucune matière")
        if portee == "formation" and noms:
            fautes.append(f"unité {uid} : portée formation, mais {len(noms)} matière(s) posée(s)")
        for nom in noms:
            if nom not in matieres:
                fautes.append(f"unité {uid} : matière inconnue « {nom} »")

    servies = {nom for u in unites for nom in (u.get("matieres") or [])}
    orphelines = sorted(set(matieres) - servies)
    if orphelines:
        fautes.append(f"{len(orphelines)} matière(s) sans aucune unité — la découpe ne les a pas "
                      f"sorties du document : " + ", ".join(f"« {n} »" for n in orphelines))

    manquantes = sorted(en_base - vus)
    if manquantes:
        fautes.append(f"{len(manquantes)} unité(s) du référentiel absente(s) du fichier : "
                      f"{manquantes[:10]}{' …' if len(manquantes) > 10 else ''}")
    if fautes:
        raise SystemExit("ARRET : rien n'a été écrit.\n  - " + "\n  - ".join(fautes))
    return matieres


def ecrire(db, referentiel_id: int, unites: list[dict], matieres: dict[str, int]) -> None:
    ids = [u["id"] for u in unites]
    db.execute(text("DELETE FROM referentiel_chunk_matieres WHERE chunk_id = ANY(:ids)"),
               {"ids": ids})
    for u in unites:
        db.execute(text("UPDATE referentiel_chunks SET portee = :p WHERE id = :i"),
                   {"p": u["portee"], "i": u["id"]})
        for nom in u.get("matieres") or []:
            db.execute(text("INSERT INTO referentiel_chunk_matieres (chunk_id, matiere_id) "
                            "VALUES (:c, :m)"), {"c": u["id"], "m": matieres[nom]})
    db.commit()


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("Usage : etiqueter_les_unites.py <referentiel_id> <fichier.json> [--ecrire]")
    referentiel_id = int(sys.argv[1])
    chemin = Path(sys.argv[2])
    ecriture = "--ecrire" in sys.argv

    unites = charger(chemin)
    db = session_pour("public")
    try:
        matieres = controler(db, referentiel_id, unites)
        print(f"{len(unites)} unité(s) contrôlée(s), {len(matieres)} matière(s) au référentiel.")
        par_portee = {p: sum(1 for u in unites if u["portee"] == p) for p in PORTEES}
        print(f"  portées : {par_portee}")
        servies = {nom for u in unites for nom in (u.get("matieres") or [])}
        print(f"  matières servies : {len(servies)}/{len(matieres)}")
        if not ecriture:
            print("Contrôle seul : rien n'a été écrit (ajouter --ecrire).")
            return
        ecrire(db, referentiel_id, unites, matieres)
        reste = db.execute(text(
            "SELECT count(*) FROM referentiel_chunks c WHERE c.referentiel_id = :r "
            "AND c.portee = 'matiere' AND NOT EXISTS ("
            "  SELECT 1 FROM referentiel_chunk_matieres m WHERE m.chunk_id = c.id)"),
            {"r": referentiel_id}).scalar()
        print(f"Écrit. Unités en portée matiere sans liaison : {reste}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
