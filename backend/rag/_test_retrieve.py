"""Test manuel de la pile RAG. Jetable une fois Phase 1 validee.

Usage : depuis la racine du projet
    python -m backend.rag._test_retrieve
"""
import logging

from backend.rag import retrieve

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")


def main() -> None:
    question = "Que doit-on enseigner sur les identites remarquables en 3e ?"
    chunks = retrieve("maths_cycle4", question, top_k=3)

    print()
    print("=" * 70)
    print(f"QUESTION : {question}")
    print(f"CHUNKS   : {len(chunks)}")
    print("=" * 70)
    for i, c in enumerate(chunks, start=1):
        page = c["page"]
        prog = c["programme"]
        score = c["score"]
        text = c["text"]
        print(f"\n--- chunk {i} (page {page} / programme {prog} / score {score}) ---")
        print(text[:300] + ("..." if len(text) > 300 else ""))


if __name__ == "__main__":
    main()
