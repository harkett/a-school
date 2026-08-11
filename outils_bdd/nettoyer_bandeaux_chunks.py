"""Retire les en-têtes et pieds de page des unités DÉJÀ découpées et rangées en base.

L'extraction collait la bande répétée de chaque page au fil du texte, et le saut de page tombe
souvent AU MILIEU d'une phrase : « Référentiel maison aSchool — en service, sans valeur
institutionnelle » s'est ainsi retrouvé planté au beau milieu d'une fiche d'activité du
référentiel crèche, où le modèle le lit comme du contenu pédagogique.

L'extraction est corrigée (règle « En-têtes et pieds de page », backend/rag/extraction.py) — mais
les documents DÉJÀ ingérés portent le défaut dans leurs unités. Les redécouper coûterait un appel
d'IA par référentiel pour un défaut qui n'a rien à voir avec la découpe. Cet outil les nettoie sur
place : il relit le PDF pour savoir QUELLES lignes sont des bandeaux, les retire des unités, et
recalcule leur vecteur — le modèle d'embedding tourne sur la machine, rien n'est facturé.

Lancer :  docker compose exec backend python outils_bdd/nettoyer_bandeaux_chunks.py [--ecrire]
Sans --ecrire, le script ne fait que dire ce qu'il ferait.
"""
import sys
from pathlib import Path

sys.path.insert(0, "/app")

import backend.core.database as dbmod                                        # noqa: E402
from backend.core.models_db import Cycle, Niveau, Referentiel, ReferentielChunk  # noqa: E402
from backend.core.nommage import dossier_cle                                 # noqa: E402
from backend.rag import pgvector_store                                       # noqa: E402
from backend.rag.extraction import (est_une_ligne_de_bandeau, extraire_texte,  # noqa: E402
                                    lignes_de_bandeau)

REFERENTIELS = Path("/app/REFERENTIELS")


def pdf_du_referentiel(db, ref: Referentiel) -> Path:
    """Même convention de rangement que le dépôt admin : <CYCLE>/<NIVEAU>/referentiel.pdf."""
    niveau = db.get(Niveau, ref.niveau_id)
    cycle = db.get(Cycle, niveau.cycle_id)
    return REFERENTIELS / dossier_cle(cycle.nom) / dossier_cle(niveau.nom) / "referentiel.pdf"


def sans_bandeaux(texte: str, bandeaux: set[str]) -> str:
    return "\n".join(l for l in texte.split("\n") if not est_une_ligne_de_bandeau(l, bandeaux))


def main() -> int:
    ecrire = "--ecrire" in sys.argv[1:]

    with dbmod.SessionLocal() as db:
        for ref in db.query(Referentiel).order_by(Referentiel.id).all():
            niveau = db.get(Niveau, ref.niveau_id)
            pdf = pdf_du_referentiel(db, ref)
            if not pdf.exists():
                print(f"— {niveau.nom} : PDF introuvable ({pdf}), passé")
                continue

            bandeaux = lignes_de_bandeau(pdf)
            if not bandeaux:
                print(f"— {niveau.nom} : aucun bandeau repéré")
                continue

            chunks = (db.query(ReferentielChunk)
                        .filter(ReferentielChunk.referentiel_id == ref.id)
                        .order_by(ReferentielChunk.chunk_index).all())
            sales = [c for c in chunks if sans_bandeaux(c.texte, bandeaux) != c.texte]
            epure_sale = ref.texte_epure and sans_bandeaux(ref.texte_epure, bandeaux) != ref.texte_epure

            print(f"— {niveau.nom} : {len(sales)}/{len(chunks)} unité(s) à nettoyer"
                  f"{', + le texte de travail' if epure_sale else ''}")
            for b in sorted(bandeaux):
                print(f"     bandeau : {b[:80]!r}")
            if not ecrire or (not sales and not epure_sale):
                continue

            if epure_sale:
                # Le texte de travail est FIGÉ au dépôt : c'est lui que relisent toutes les étapes
                # IA. Le laisser sale ferait revenir le bandeau à la première relecture.
                ref.texte_epure = extraire_texte(pdf)

            if sales:
                # Règle maison : on ne touche pas aux unités sans sauvegarde horodatée d'abord.
                # La fonction relit ce qu'elle a écrit et lève si le compte n'y est pas — le
                # nettoyage ci-dessous n'est donc jamais atteint sans filet.
                trace = pgvector_store._sauvegarder_chunks_avant_purge(db, ref.id)
                print(f"     sauvegarde : {trace.get('sauvegarde')} ({trace.get('lignes')} unités)")

                from backend.rag.embeddings import embed_texts
                propres = [sans_bandeaux(c.texte, bandeaux).strip() for c in sales]
                # Le texte change, donc le vecteur aussi : le laisser tel quel ferait chercher
                # l'unité sur des mots qu'elle ne contient plus.
                vecteurs = embed_texts(propres)
                for chunk, texte, vecteur in zip(sales, propres, vecteurs):
                    chunk.texte, chunk.embedding = texte, vecteur

            db.commit()
            print(f"     nettoyé : {len(sales)} unité(s)"
                  f"{', texte de travail réécrit' if epure_sale else ''}")

    if not ecrire:
        print("\nRelancez avec --ecrire pour appliquer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
