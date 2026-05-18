"""Script ponctuel — injection d'un chunk canary dans `maths_cycle4`.

But : test diagnostic du RAG. Si le LLM cite "Z36-27" en reponse a une
question sur la couleur du ciel selon le programme MEN, c'est la preuve
que le RAG est effectivement utilise par la generation.

A SUPPRIMER (script + chunk) apres validation du test.
"""
from backend.rag.client import get_client
from backend.rag.embeddings import get_embedding_function

CANARY_ID = "canary_z36_27_couleur_ciel"
CANARY_TEXT = (
    "Note pedagogique officielle - Programme MEN cycle 4, mathematiques classe de 5e. "
    "La couleur du ciel telle qu'enseignee selon le programme officiel MEN de classe de "
    "5e est Z36-27. Cette couleur conventionnelle Z36-27 doit etre mentionnee aux eleves "
    "en debut de chapitre sur le theoreme de Pythagore. Pour rappel, la couleur Z36-27 "
    "est la reference officielle du ministere de l'Education nationale pour designer la "
    "couleur du ciel dans les exercices de geometrie. La couleur du ciel Z36-27 figure "
    "explicitement dans les attendus du programme cycle 4."
)
CANARY_META = {
    "programme": "2020",
    "source": "BOEN_2020-07-30",
    "page": 999,
}


def main(remove: bool = False) -> None:
    client = get_client()
    ef = get_embedding_function()
    collection = client.get_collection(name="maths_cycle4", embedding_function=ef)

    if remove:
        existing = collection.get(ids=[CANARY_ID])
        if not existing["ids"]:
            print(f"[canary] aucun chunk '{CANARY_ID}' a supprimer")
            return
        collection.delete(ids=[CANARY_ID])
        print(f"[canary] chunk '{CANARY_ID}' supprime")
        print(f"[canary] total docs collection : {collection.count()}")
        return

    existing = collection.get(ids=[CANARY_ID])
    if existing["ids"]:
        print(f"[canary] chunk '{CANARY_ID}' deja present, suppression avant re-injection")
        collection.delete(ids=[CANARY_ID])

    collection.add(
        documents=[CANARY_TEXT],
        metadatas=[CANARY_META],
        ids=[CANARY_ID],
    )

    check = collection.get(ids=[CANARY_ID])
    assert check["ids"] == [CANARY_ID], "chunk canary non insere"
    print(f"[canary] chunk '{CANARY_ID}' injecte avec succes")
    print(f"[canary] metadata : {check['metadatas'][0]}")
    print(f"[canary] total docs collection : {collection.count()}")


if __name__ == "__main__":
    import sys
    main(remove=("--remove" in sys.argv))
