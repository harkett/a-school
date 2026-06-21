"""Découpeur générique de référentiel — brique neutre du moteur RAG.

Ne connaît AUCUN référentiel : ni regex de section, ni notion d'option A/B, ni
quel champ de métadonnée existe. La fiche du référentiel lui fournit tout :
  - max_chars / min_chars : tailles de chunk ;
  - overlap_chars : recouvrement repris d'un chunk au suivant sur une coupe de
    TAILLE (0 = aucun recouvrement = comportement historique) ;
  - is_boundary(line) -> marqueur opaque | None : signale une frontière de chunk ;
  - chunk_metadata(marker, page) -> dict : métadonnées à attacher au chunk ;
  - dedup_key(text, meta) -> clé hashable | None : 2 chunks de MÊME clé sont des
    doublons (on garde le 1er). None (défaut) = aucune déduplication = historique.
    La dédup porte sur le CHUNK ENTIER ; un segment d'overlap n'étant jamais un
    chunk entier, le recouvrement volontaire n'est jamais supprimé.

Le découpeur trimballe le « marqueur courant » tel que la fiche le lui a donné et
ne l'interprète JAMAIS (il teste seulement « non-None ⇒ frontière »). Toute la
sémantique (qu'est-ce qu'un en-tête, que signifie-t-il) vit dans la fiche.

Critère d'archi : ajouter un référentiel = écrire une fiche, zéro ligne touchée ici.
"""
from __future__ import annotations

from typing import Any, Callable, Optional


def _tail_lines(lines: list[str], budget: int) -> list[str]:
    """Suffixe maximal de `lines` dont la longueur cumulée (len+1 par ligne) ≤ budget.
    Granularité ligne : on ne coupe jamais au milieu d'une ligne. Si la dernière ligne
    dépasse à elle seule le budget, renvoie [] (aucun recouvrement, coupe nette)."""
    out: list[str] = []
    total = 0
    for line in reversed(lines):
        add = len(line) + 1
        if total + add > budget:
            break
        out.append(line)
        total += add
    out.reverse()
    return out


def build_chunks(
    pages: list[tuple[int, str]],
    *,
    max_chars: int,
    min_chars: int,
    overlap_chars: int = 0,
    is_boundary: Callable[[str], Optional[Any]],
    chunk_metadata: Callable[[Optional[Any], int], dict],
    dedup_key: Optional[Callable[[str, dict], Any]] = None,
) -> list[dict]:
    """Découpe en chunks (≤ max_chars), une seule page par chunk, métadonnées posées
    par la fiche. Le marqueur de frontière traverse les pages et bascule aux en-têtes
    signalés par la fiche ; le découpeur ne sait pas ce qu'il représente.

    Recouvrement (overlap) : sur une coupe de TAILLE uniquement, le chunk suivant
    reprend la fin du précédent (≤ overlap_chars, à la ligne près) → une idée à cheval
    sur la coupe n'est plus perdue. JAMAIS sur une frontière ni en fin de page (ce sont
    de vraies ruptures ; y déborder ferait fuir le marqueur/le tag dans le mauvais chunk).
    overlap_chars=0 ⇒ sortie strictement identique au comportement historique.

    Renvoie une liste de dicts {"text", "page", "meta"} — `meta` est le dict opaque
    rendu par chunk_metadata (le découpeur n'en lit aucune clé)."""
    chunks: list[dict] = []
    marker: Optional[Any] = None  # marqueur courant, fourni par la fiche — jamais interprété ici
    for page_no, text in pages:
        buf: list[str] = []
        buf_len = 0
        n_carry = 0  # nb de lignes en tête de buf reprises du chunk précédent (overlap)

        def emit(carry_overlap: bool) -> None:
            nonlocal buf, buf_len, n_carry
            content = "\n".join(buf).strip()
            # n'émet QUE s'il y a du contenu nouveau au-delà du recouvrement repris
            # (sinon on créerait un chunk purement dupliqué du précédent).
            if len(buf) > n_carry and len(content) >= min_chars:
                chunks.append({
                    "text": content,
                    "page": page_no,
                    "meta": chunk_metadata(marker, page_no),
                })
            if carry_overlap and overlap_chars > 0:
                tail = _tail_lines(buf, overlap_chars)
                buf = list(tail)
                buf_len = sum(len(l) + 1 for l in buf)
                n_carry = len(buf)
            else:
                buf, buf_len, n_carry = [], 0, 0

        for line in text.splitlines():
            m = is_boundary(line)
            if m is not None:
                emit(carry_overlap=False)  # frontière : vraie rupture, pas de recouvrement…
                marker = m                 # …et nouveau marqueur courant (opaque)
            buf.append(line)
            buf_len += len(line) + 1
            if buf_len >= max_chars:
                emit(carry_overlap=True)   # coupe de taille : on reprend la fin dans le suivant
        emit(carry_overlap=False)          # fin de page : pas de recouvrement inter-pages

    # Déduplication post-découpage : on garde la PREMIÈRE occurrence de chaque clé
    # (ordre document). Clé fournie par la fiche, opaque pour le découpeur. Au chunk
    # entier uniquement → ne touche jamais au recouvrement de l'overlap.
    if dedup_key is not None:
        seen: set = set()
        deduped: list[dict] = []
        for c in chunks:
            k = dedup_key(c["text"], c["meta"])
            if k in seen:
                continue
            seen.add(k)
            deduped.append(c)
        chunks = deduped
    return chunks
