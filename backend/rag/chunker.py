"""Découpeur générique de référentiel — brique neutre du moteur RAG.

Ne connaît AUCUN référentiel : ni regex de section, ni notion d'option A/B, ni
quel champ de métadonnée existe. La fiche du référentiel lui fournit tout :
  - max_chars / min_chars : tailles de chunk ;
  - is_boundary(line) -> marqueur opaque | None : signale une frontière de chunk ;
  - chunk_metadata(marker, page) -> dict : métadonnées à attacher au chunk.

Le découpeur trimballe le « marqueur courant » tel que la fiche le lui a donné et
ne l'interprète JAMAIS (il teste seulement « non-None ⇒ frontière »). Toute la
sémantique (qu'est-ce qu'un en-tête, que signifie-t-il) vit dans la fiche.

Critère d'archi : ajouter un référentiel = écrire une fiche, zéro ligne touchée ici.
"""
from __future__ import annotations

from typing import Any, Callable, Optional


def build_chunks(
    pages: list[tuple[int, str]],
    *,
    max_chars: int,
    min_chars: int,
    is_boundary: Callable[[str], Optional[Any]],
    chunk_metadata: Callable[[Optional[Any], int], dict],
) -> list[dict]:
    """Découpe en chunks (≤ max_chars), une seule page par chunk, métadonnées posées
    par la fiche. Le marqueur de frontière traverse les pages et bascule aux en-têtes
    signalés par la fiche ; le découpeur ne sait pas ce qu'il représente.

    Renvoie une liste de dicts {"text", "page", "meta"} — `meta` est le dict opaque
    rendu par chunk_metadata (le découpeur n'en lit aucune clé)."""
    chunks: list[dict] = []
    marker: Optional[Any] = None  # marqueur courant, fourni par la fiche — jamais interprété ici
    for page_no, text in pages:
        buf: list[str] = []
        buf_len = 0

        def flush() -> None:
            nonlocal buf, buf_len
            content = "\n".join(buf).strip()
            if len(content) >= min_chars:
                chunks.append({
                    "text": content,
                    "page": page_no,
                    "meta": chunk_metadata(marker, page_no),
                })
            buf, buf_len = [], 0

        for line in text.splitlines():
            m = is_boundary(line)
            if m is not None:
                flush()      # un nouvel en-tête ferme le chunk courant…
                marker = m   # …et devient le marqueur courant (opaque)
            buf.append(line)
            buf_len += len(line) + 1
            if buf_len >= max_chars:
                flush()
        flush()
    return chunks
