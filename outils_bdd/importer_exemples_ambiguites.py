"""Injecte en base les énoncés d'exemple de l'écran « Détecter les ambiguïtés ».

Ces exemples ne sont JAMAIS générés par l'application : ils sont écrits hors de l'app (coût
zéro), rassemblés dans un seul fichier Markdown, puis recollés en base. L'écran admin fait
déjà ce travail couple par couple ; ce script le fait pour un fichier entier — même découpage
(`decouper_colle`), même table, même règle.

Format attendu du fichier :

    ## <niveau>                     ← le niveau, tel qu'il est écrit en base (le « (n) » final est ignoré)
    ### <k>. <matière>              ← la matière, telle qu'elle est écrite en base
    === ENONCE ===
    …
    === DEFAUTS ===
    …

Le rapprochement est STRICT : un couple du fichier qui ne se retrouve pas en base n'est pas
« deviné », il est signalé et RIEN n'est écrit. Un exemple posé sur la mauvaise matière serait
invisible — le prof le verrait sans jamais savoir qu'il n'est pas le sien.

Lancer :  docker compose exec backend python outils_bdd/importer_exemples_ambiguites.py <fichier.md> [--ecrire]
Sans --ecrire, le script ne fait que dire ce qu'il ferait.
"""
import re
import sys
import unicodedata

sys.path.insert(0, "/app")

import backend.core.database as dbmod                                    # noqa: E402
from backend.core.models_db import AmbiguiteExemple, Matiere, Niveau, Referentiel  # noqa: E402
from backend.pedagogie.ambiguite_exemples import decouper_colle          # noqa: E402


def cle(texte: str) -> str:
    """De quoi rapprocher « Langue vivante étrangère : anglais » de sa jumelle en base malgré
    un accent, une majuscule ou une espace de plus. On ne rapproche pas plus loin que ça."""
    sans_accent = "".join(c for c in unicodedata.normalize("NFD", texte)
                          if unicodedata.category(c) != "Mn")
    return " ".join(sans_accent.lower().replace("’", "'").split())


def sans_notes_de_relecture(defauts: str) -> str:
    """Les « *(NB : … )* » que le rédacteur laisse pour lui-même ne sont pas des défauts de
    l'énoncé : ils parlent du texte, pas du sujet. Ils n'ont rien à faire dans la colonne que
    l'admin relit pour savoir ce qui a été glissé dedans."""
    gardees = [l for l in defauts.splitlines() if not l.lstrip().startswith("*(NB")]
    return "\n".join(gardees).strip()


def lire_blocs(chemin: str) -> list[tuple[str, str, str]]:
    """(niveau, matière, collé) pour chaque `###` du fichier, dans l'ordre."""
    with open(chemin, encoding="utf-8") as f:
        lignes = f.read().replace("\r\n", "\n").split("\n")

    blocs, niveau, matiere, courant = [], None, None, []
    for ligne in lignes:
        if ligne.startswith("## ") and not ligne.startswith("### "):
            if matiere:
                blocs.append((niveau, matiere, "\n".join(courant)))
                matiere, courant = None, []
            niveau = re.sub(r"\s*\(\d+\)\s*$", "", ligne[3:]).strip()
        elif ligne.startswith("### "):
            if matiere:
                blocs.append((niveau, matiere, "\n".join(courant)))
            matiere = re.sub(r"^\d+\.\s*", "", ligne[4:]).strip()
            courant = []
        elif matiere is not None:
            courant.append(ligne)
    if matiere:
        blocs.append((niveau, matiere, "\n".join(courant)))
    return blocs


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    chemin, ecrire = sys.argv[1], "--ecrire" in sys.argv[2:]

    blocs = lire_blocs(chemin)
    print(f"{len(blocs)} bloc(s) lu(s) dans {chemin}")

    with dbmod.SessionLocal() as db:
        couples = (db.query(Matiere, Niveau)
                     .join(Referentiel, Referentiel.id == Matiere.referentiel_id)
                     .join(Niveau, Niveau.id == Referentiel.niveau_id)
                     .filter(Matiere.actif.is_(True)).all())
        index = {(cle(n.nom), cle(m.nom)): m for m, n in couples}

        a_ecrire, manquants, vides = [], [], []
        for niveau, matiere, colle in blocs:
            m = index.get((cle(niveau or ""), cle(matiere)))
            if m is None:
                manquants.append(f"{niveau} · {matiere}")
                continue
            texte, defauts = decouper_colle(colle)
            defauts = sans_notes_de_relecture(defauts)
            if not texte:
                vides.append(f"{niveau} · {matiere}")
                continue
            a_ecrire.append((m, texte, defauts))

        for quoi, liste in (("sans couple en base", manquants), ("sans énoncé", vides)):
            if liste:
                print(f"\n{len(liste)} bloc(s) {quoi} :")
                for x in liste:
                    print(f"  - {x}")

        if manquants or vides:
            print("\nRien n'est écrit tant qu'un bloc n'a pas trouvé sa matière.")
            return 1

        print(f"\n{len(a_ecrire)} exemple(s) prêts à écrire.")
        if not ecrire:
            print("Relancez avec --ecrire pour les poser en base.")
            return 0

        deja = {e.matiere_id: e for e in db.query(AmbiguiteExemple).all()}
        neufs = remplaces = 0
        for m, texte, defauts in a_ecrire:
            ligne = deja.get(m.id)
            if ligne:
                ligne.texte, ligne.defauts = texte, defauts
                remplaces += 1
            else:
                db.add(AmbiguiteExemple(matiere_id=m.id, texte=texte, defauts=defauts))
                neufs += 1
        db.commit()
        total = db.query(AmbiguiteExemple).count()
        print(f"{neufs} ajouté(s), {remplaces} remplacé(s) — {total} exemple(s) en base.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
