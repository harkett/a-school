"""Singleton sentence-transformers — modele d'embeddings multilingue charge une fois.

Modele : BAAI/bge-m3 (~2,2 Go, dim 1024). Charge au premier appel par la voie DIRECTE
sentence-transformers (sans ChromaDB), conserve en RAM pour tous les appels suivants.
C'est le modele utilise par le RAG pgvector (embed_texts), a l'ingestion ET a la recherche.
CHOIX ACTE : BGE-M3 est le meilleur modele multilingue qui tourne SANS GPU, et la prod n'en a
pas. Cible haut de gamme = Qwen3-Embedding-8B, le jour ou la prod aura un GPU.
Changer de modele n'est jamais anodin : la dimension du vecteur change avec lui, et des
vecteurs de modeles differents ne se comparent pas (d'ou le garde-fou `embedding_model`
sur chaque chunk, cf. backend/core/models_db.py ReferentielChunk).
"""
import logging
import os
import threading
from typing import Any

# ── HORS-LIGNE : le modele ne se telecharge JAMAIS tout seul ─────────────────────────────
#
# Ces deux lignes ne vivaient QUE dans backend/main.py, donc uniquement pour le serveur. Tout
# ce qui charge le modele sans passer par lui — la suite de tests, un script, un
# `docker exec python -c` — partait sans garde-fou. Constate le 02/08 : un appel direct a
# `retrieve_pg` repondait « You are sending unauthenticated requests to the HF Hub ». Rien
# n'avait casse parce que le cache etait la ; le jour ou il manque (machine neuve, hf-cache
# non recopie, volume perdu), le serveur echoue net et proprement tandis que la suite de
# tests part chercher 2,2 Go sans le dire.
#
# POURQUOI ICI, ET PAS DANS main.py NI DANS conftest.py. `huggingface_hub` fige la valeur dans
# une CONSTANTE, au premier chargement de son module `huggingface_hub.constants` — chargement
# PARESSEUX, donc pas forcement au premier `import huggingface_hub`. Une fois fige, plus rien ne
# le bouge. Mesure des deux cotes, sans les variables dans l'environnement :
#     constants charge d'abord, setdefault ensuite  ->  False, et False apres. Trop tard.
#     ordre reel du depot (ce module d'abord)       ->  True. `constants` n'etait pas charge.
# Il faut donc un endroit garanti d'etre execute AVANT ce chargement, et qu'aucun point d'entree
# ne puisse contourner. Ce module est cet endroit, et pour une raison precise : il est la SEULE porte du
# depot vers un modele HuggingFace (verifie : aucun autre fichier n'importe
# sentence_transformers ni n'appelle from_pretrained), et son propre import de
# `sentence_transformers` est PARESSEUX — il vit dans `get_st_model()`, pas ici. Ces lignes-ci
# tournent donc forcement avant lui. Un module d'amorcage separe aurait la faiblesse qu'on
# repare : un import a ne pas oublier. Celui-ci, on ne peut pas l'oublier — sans lui, pas de
# modele.
#
# `setdefault`, jamais `=` : docker-compose.yml pose deja les deux variables sur le service
# backend (avant meme que Python demarre, ceinture et bretelles) et une valeur venue de
# l'environnement doit gagner — c'est par la qu'on remplit le cache la premiere fois, en
# lancant une fois avec HF_HUB_OFFLINE=0.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "BAAI/bge-m3"

_st_model: Any = None
_lock = threading.Lock()  # le modele peut etre charge en parallele (prechauffe au boot + 1er clic)


def get_st_model() -> Any:
    """Singleton SentenceTransformer. Charge une fois, thread-safe (double-checked locking) :
    la prechauffe lancee au demarrage du serveur et une requete concurrente ne doivent
    jamais charger le modele deux fois."""
    global _st_model
    if _st_model is None:
        with _lock:
            if _st_model is None:
                from sentence_transformers import SentenceTransformer
                logger.info(f"[RAG] Chargement SentenceTransformer : {EMBEDDING_MODEL}")
                _st_model = SentenceTransformer(EMBEDDING_MODEL)
                logger.info("[RAG] Modele d'embedding pret")
    return _st_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeddings d'une liste de textes par la voie DIRECTE sentence-transformers, dim 1024."""
    model = get_st_model()
    vecs = model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=False)
    return [v.tolist() for v in vecs]
