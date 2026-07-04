"""Fiche de réglages — Crèche (Référentiel national de la qualité d'accueil du jeune enfant, 0-3 ans).

Deuxième fiche, après CIEL. Elle sert les TROIS couples de la crèche — Bébés (0-1 an),
Moyens (1-2 ans), Grands (2-3 ans) — qui partagent le MÊME document 0-3 ans. Le moteur
(chunker générique + retrieve) n'en sait rien ; toute la spécificité crèche vit ici.

Spécificité de CE PDF : mise en page « magazine ». Chaque page du PDF est une DOUBLE-PAGE
(deux pages imprimées côte à côte, largeur ~1191), et chaque page imprimée a DEUX colonnes.
Une extraction naïve (lecture en travers) mélange les colonnes et injecte le mobilier de page
au milieu des phrases. La méthode ci-dessous :
  1. coupe la double-page en deux pages imprimées (au milieu),
  2. détecte les 2 colonnes de chaque page imprimée et les lit dans l'ordre,
  3. garde ENTIÈRES les lignes pleine largeur (titres, encadrés « À retenir »),
  4. retire le mobilier répété (en-tête courant, numéros de page, encart « Ce référentiel est le vôtre… »),
  5. recolle les mots coupés en fin de ligne (césure du texte justifié).

Pas d'option A/B ici (le document n'en a pas) : chaque chunk est tagué option = "".
"""
from __future__ import annotations

import re
from typing import Any, Optional

# --- Découpe (mêmes ordres de grandeur que CIEL, calibrage neutre) ---
MAX_CHARS = 900       # taille cible d'un chunk
MIN_CHARS = 60        # en dessous, on ne crée pas un chunk isolé (bruit : titres orphelins)
OVERLAP_CHARS = 150   # recouvrement repris sur une coupe de TAILLE (~17 % de MAX_CHARS)
SCORE_MIN = 0.30      # seuil de pertinence (1 - distance cosinus) — PROVISOIRE, à calibrer sur le
                      # corpus crèche quand on branchera « Tester un exemple » (épisode 4).

# --- Mobilier de page à retirer, par CONTENU (robuste à la position) ---
_FURNITURE_EXACT = {
    "Référentiel national de la qualité d’accueil",
    "du jeune enfant",
    "Avril 2025",
    "Ce référentiel est le vôtre !",
    "Complétez cette fiche et remontez",
    "vos idées, bonnes pratiques, exemples",
    "d’activités, de cas pratiques et de situations",
    "type à l’adresse nationale du service public",
    "de la petite enfance, sppe@sante.gouv.fr,",
    "pour enrichir les ressources mises à disposition",
    "de tous les professionnels de France.",
}
_PAGENUM_RE = re.compile(r"^\d{1,3}(\s+\d{1,3})*$")
_GUTTER_GAP = 25.0     # gap horizontal (px) au-delà duquel on voit une gouttière entre colonnes
_DOUBLE_PAGE_MIN_WIDTH = 800.0  # au-delà, la page PDF est une double-page (2 pages imprimées)


# ----------------------------------------------------------------------------
# Extraction colonne-par-colonne (le cœur de la méthode crèche)
# ----------------------------------------------------------------------------
def _rows(words: list[dict], y_tol: float = 3.0) -> list[list[dict]]:
    """Groupe les mots en lignes visuelles (par 'top'), chaque ligne triée gauche->droite."""
    words = sorted(words, key=lambda w: (w["top"], w["x0"]))
    rows: list[list[dict]] = []
    cur: list[dict] = []
    cur_top: Optional[float] = None
    for w in words:
        if cur_top is None or abs(w["top"] - cur_top) <= y_tol:
            cur.append(w)
            cur_top = w["top"] if cur_top is None else cur_top
        else:
            rows.append(sorted(cur, key=lambda x: x["x0"]))
            cur, cur_top = [w], w["top"]
    if cur:
        rows.append(sorted(cur, key=lambda x: x["x0"]))
    return rows


def _detect_boundary(words: list[dict], lo: float, hi: float) -> Optional[float]:
    """Cherche la gouttière entre 2 colonnes dans [lo,hi] : le x où le moins de mots
    chevauchent une bande verticale. None si pas de vrai creux (page à une seule colonne)."""
    span = hi - lo
    cand_lo, cand_hi = lo + 0.35 * span, lo + 0.62 * span
    best_x, best_cov = None, 10**9
    x = cand_lo
    while x <= cand_hi:
        cov = sum(1 for w in words if w["x0"] <= x + 3 and w["x1"] >= x - 3)
        if cov < best_cov:
            best_cov, best_x = cov, x
        x += 4
    total = sum(1 for w in words if lo <= (w["x0"] + w["x1"]) / 2 <= hi)
    if total and best_cov <= max(1, 0.06 * total):
        return best_x
    return None


def _row_text(row: list[dict]) -> str:
    return " ".join(w["text"] for w in row)


def _printed_page_lines(words: list[dict], left: float, right: float) -> list[str]:
    """Une page imprimée [left,right] -> lignes de texte dans l'ordre de lecture.
    Les lignes pleine largeur (titres, « À retenir ») sont gardées entières et intercalées
    entre les blocs 2-colonnes (méthode XY-cut)."""
    body = [w for w in words if left <= (w["x0"] + w["x1"]) / 2 < right]
    if not body:
        return []
    b = _detect_boundary(body, left, right)
    if b is None:
        return [_row_text(r) for r in _rows(body)]

    out: list[str] = []
    buf_l: list[list[dict]] = []
    buf_r: list[list[dict]] = []

    def flush() -> None:
        for r in buf_l:
            out.append(_row_text(r))
        for r in buf_r:
            out.append(_row_text(r))
        buf_l.clear()
        buf_r.clear()

    for row in _rows(body):
        has_left = any((w["x0"] + w["x1"]) / 2 < b for w in row)
        has_right = any((w["x0"] + w["x1"]) / 2 >= b for w in row)
        if has_left and has_right:
            gap_straddles = any(
                w1["x1"] < b <= w2["x0"] and (w2["x0"] - w1["x1"]) >= _GUTTER_GAP
                for w1, w2 in zip(row, row[1:])
            )
            if gap_straddles:                       # vraie gouttière : 2 colonnes sur cette ligne
                buf_l.append([w for w in row if (w["x0"] + w["x1"]) / 2 < b])
                buf_r.append([w for w in row if (w["x0"] + w["x1"]) / 2 >= b])
            else:                                   # ligne PLEINE LARGEUR
                flush()
                out.append(_row_text(row))
        else:
            (buf_l if has_left else buf_r).append(row)
    flush()
    return out


def _clean(lines: list[str]) -> list[str]:
    out = []
    for ln in lines:
        s = ln.strip()
        if not s or s in _FURNITURE_EXACT or _PAGENUM_RE.match(s):
            continue
        out.append(s)
    return out


def _dehyphenate(lines: list[str]) -> list[str]:
    """Recolle les mots coupés en fin de ligne : une ligne finissant par '-' suivie d'un
    mot en minuscule -> les deux morceaux réunis sans le tiret ('en-'/'fants' -> 'enfants')."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i]
        while s.endswith("-") and i + 1 < len(lines) and lines[i + 1][:1].islower():
            s = s[:-1] + lines[i + 1]
            i += 1
        out.append(s)
        i += 1
    return out


def extract_pages(pdf_path) -> list[tuple[int, str]]:
    """(n° page depuis 1, texte propre) — extraction colonne-par-colonne + retrait du mobilier.
    C'est la méthode crèche ; elle remplace l'extraction naïve pour ce PDF multi-colonnes."""
    import pdfplumber  # import paresseux (ne pas alourdir le démarrage)
    pages: list[tuple[int, str]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(use_text_flow=False)
            if not words:
                pages.append((i, ""))
                continue
            mid = page.width / 2
            if page.width > _DOUBLE_PAGE_MIN_WIDTH:  # double-page : gauche puis droite
                lines = _printed_page_lines(words, 0, mid) + _printed_page_lines(words, mid, page.width)
            else:                                    # page simple (couverture)
                lines = _printed_page_lines(words, 0, page.width)
            pages.append((i, "\n".join(_dehyphenate(_clean(lines)))))
    return pages


# ----------------------------------------------------------------------------
# Interface attendue par le chunker générique
# ----------------------------------------------------------------------------
def section_boundary(line: str) -> Optional[str]:
    """Le document crèche n'a pas de sections numérotées ni d'option A/B : on découpe par
    TAILLE uniquement. Aucune frontière signalée -> le découpeur coupe sur MAX_CHARS + overlap."""
    return None


def chunk_metadata(marker: Optional[str], page: int) -> dict[str, Any]:
    """Métadonnées d'un chunk. Pas d'option A/B ici -> option = "". Le niveau et la source
    ne sont PAS posés ici : ils sont récupérés par jointure via referentiel_id (cap relationnel)."""
    return {"option": "", "page": page}


def dedup_key(text: str, meta: dict) -> tuple:
    """Deux chunks de texte identique sont des doublons (on garde le 1er). Filet contre un
    éventuel passage répété à l'identique."""
    return (text,)
