# -*- coding: utf-8 -*-
"""Écrit les unités d'un référentiel À PARTIR D'UN JSON DE DÉCOUPE DÉJÀ RENDU — zéro appel IA.

    docker exec a-school-backend-1 python outils_bdd/ingerer_decoupe_json.py <collection> <fichier.json>
    (ajouter --ecrire pour écrire ; sans lui, il contrôle, tranche à blanc et n'écrit rien)

D'OÙ VIENT LE FICHIER. Du prompt de découpe du référentiel, exécuté dehors, sur un agent gratuit
— la voie qui ne coûte rien. Le JSON revient alors sous les yeux avant d'entrer : on le contrôle,
on corrige à la main les entrées fautives contre le document, et c'est CE fichier-là qui est posé.

POURQUOI CET OUTIL EXISTE. Le bouton « Découper » appelle forcément l'IA : il n'y a aucune porte
pour un JSON relu et corrigé. Or corriger deux entrées ne vaut pas de relancer tout le document —
la découpe n'est pas reproductible (`analyse_amont`, note du 05/08/2026), et relancer échangerait
des défauts connus et localisés contre un jeu d'unités inconnu. Le tranchage, lui, est PUR :
`_trancher_par_titres` ne touche ni l'IA ni la base. Rejouer un JSON corrigé est donc gratuit et
déterministe — c'est exactement ce que fait cet outil.

IL NE DÉCIDE RIEN. Il ne réécrit aucun titre, ne devine aucune option, n'invente aucune frontière :
il passe le JSON au tranchage réel du produit, puis à l'ingestion réelle du produit
(`ingest_pgvector`). Ce qu'il écrit est mot pour mot ce que le bouton « Découper » aurait écrit si
l'IA avait rendu ce JSON-là.

CE QU'IL CONTRÔLE AVANT D'ÉCRIRE :
  - le référentiel existe pour cette collection, et il a un texte de travail ;
  - le JSON porte les quatre champs, `garder` en VRAI booléen (une chaîne "false" passerait pour
    un `true` — `u.get("garder", True) is not False` ne compare que l'identité) ;
  - le tranchage rend au moins une unité (une découpe vide effacerait le référentiel).
Il REFUSE en bloc : une découpe à moitié posée est le pire des états.

IL DIT CE QU'IL PERD. Titres introuvables, titres hors ordre, tranches nues écartées, doublons
fondus : le journal du tranchage passe à l'écran, et le compte des caractères gardés est mis en
face du texte épuré. Sans ce rapport, une découpe qui garde 30 % du document a exactement la même
allure qu'une bonne.

IL EST REJOUABLE. `ingest_pgvector` sauvegarde les unités existantes avant de les remplacer, et ne
touche qu'au document courant du référentiel.
"""
import json
import logging
import sys
from pathlib import Path

# Racine du dépôt sur le sys.path : ce script vit dans outils_bdd/, on doit pouvoir importer
# le package backend (lancé par chemin, sys.path[0] = outils_bdd/, pas la racine).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.core.database import session_pour, SCHEMA_REEL
from backend.core.models_db import Referentiel
from backend.rag.analyse_amont import _trancher_par_titres
from backend.rag.pgvector_store import ingest_pgvector


def charger(chemin: Path) -> list[dict]:
    """Les entrées du JSON, contrôlées champ par champ. Lève sur la première faute."""
    data = json.loads(chemin.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("unites"), list):
        raise SystemExit(f"{chemin.name} : attendu un objet {{\"unites\": [...]}}.")
    entrees = data["unites"]
    if not entrees:
        raise SystemExit(f"{chemin.name} : aucune entrée.")
    for i, u in enumerate(entrees):
        if not isinstance(u, dict):
            raise SystemExit(f"entrée {i} : attendu un objet à quatre champs.")
        manquants = {"titre", "option", "annee", "garder"} - set(u)
        if manquants:
            raise SystemExit(f"entrée {i} : champ(s) absent(s) {sorted(manquants)}.")
        if not isinstance(u["garder"], bool):
            # Le tranchage teste l'IDENTITÉ à False : "false", 0 ou null passeraient pour un
            # `true` et la borne ne bornerait rien, en silence.
            raise SystemExit(f"entrée {i} : `garder` doit être un booléen JSON, "
                             f"reçu {u['garder']!r} ({type(u['garder']).__name__}).")
        if not (u.get("titre") or "").strip():
            raise SystemExit(f"entrée {i} : titre vide — elle serait jetée sans laisser de trace.")
    return entrees


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s", stream=sys.stdout)
    ecrire = "--ecrire" in argv
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 2
    collection, chemin = args[0], Path(args[1])
    if not chemin.exists():
        raise SystemExit(f"Fichier introuvable : {chemin}")

    entrees = charger(chemin)

    db = session_pour(SCHEMA_REEL)
    try:
        ref = db.query(Referentiel).filter(Referentiel.collection == collection).first()
        if ref is None:
            raise SystemExit(f"Aucun référentiel pour collection='{collection}'.")
        rid = ref.id
        texte = (ref.texte_epure or "").strip()
        prompt = ref.prompt_decoupe or ""
        nom = ref.nom_affichage or collection
    finally:
        db.close()
    if not texte:
        raise SystemExit(f"Le référentiel {rid} n'a pas de texte de travail (texte_epure vide).")

    print(f"Référentiel {rid} — {nom}")
    print(f"texte de travail : {len(texte)} caractères")
    print(f"{chemin.name} : {len(entrees)} entrées, "
          f"{sum(1 for e in entrees if e['garder'])} gardées, "
          f"{sum(1 for e in entrees if not e['garder'])} bornes")
    print("-" * 90)

    # LE TRANCHAGE RÉEL, celui du produit. Son journal (titres perdus, tranches nues, doublons
    # fondus) sort ici : c'est le seul endroit où l'on voit ce que la découpe laisse en route.
    unites = _trancher_par_titres(texte, entrees)
    if not unites:
        raise SystemExit("Le tranchage ne rend AUCUNE unité : rien ne sera écrit.")

    garde = sum(len(u["texte"]) for u in unites)
    print("-" * 90)
    print(f"=> {len(unites)} unités, {garde} caractères gardés "
          f"({100.0 * garde / len(texte):.1f} % du texte de travail)")
    for i, u in enumerate(unites):
        print(f"{i:3d} [{u['option'] or '·':^7}] {len(u['texte']):6d} car.  {u['titre'][:80]}")

    if not ecrire:
        print("\n(contrôle seul — rien n'a été écrit ; ajouter --ecrire pour poser)")
        return 0

    # Même forme que `_decouper_ia` : c'est ce que l'ingestion attend, et rien d'autre.
    chunks = [{"text": u["texte"], "page": 1,
               "meta": {"option": u.get("option", ""), "annee": u.get("annee", "")}}
              for u in unites]
    # `prompt` doit être MOT POUR MOT celui du référentiel : l'ingestion refuse une découpe qui
    # ne vient pas du prompt en base (elle ne peut pas savoir, autrement, ce qu'elle écrit).
    rapport = ingest_pgvector(collection, decoupe_prete={"prompt": prompt, "chunks": chunks})
    print("\n" + json.dumps(rapport, ensure_ascii=False, indent=2, default=str))

    # UNE DÉCOUPE NEUVE N'EST PAS UNE DÉCOUPE VALIDÉE — même règle que le bouton « Découper » :
    # l'admin relit les unités et clique. Laisser le drapeau à vrai ferait passer pour relu un
    # découpage que personne n'a vu.
    db = session_pour(SCHEMA_REEL)
    try:
        db.query(Referentiel).filter(Referentiel.id == rid).update({"decoupe_valide": False})
        db.commit()
    finally:
        db.close()
    print("\n`decoupe_valide` remis à faux : les unités sont à relire dans Admin → Référentiels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
