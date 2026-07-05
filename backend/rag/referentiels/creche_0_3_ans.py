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

# --- Découpe : 1 FICHE = 1 CHUNK (frontière de fiche, pas taille fixe) ---
# On ne coupe plus par taille aveugle (qui collait la queue d'une fiche sur la tête de la
# suivante → contamination). L'extraction reconstruit chaque fiche en une « page » autonome
# (cf. _split_into_fiches) ; le chunker générique en fait alors UN chunk par fiche.
# MAX_CHARS n'est plus une taille cible : c'est un plafond de sécurité, très au-dessus de la
# plus grande fiche (mesurée ~850 car.). Il n'agit que comme FILET : si une fiche dépassait ce
# plafond, la coupe de taille jouerait à l'intérieur de CETTE fiche uniquement, jamais entre deux.
MAX_CHARS = 4000      # plafond de sécurité (une fiche n'atteint jamais cette taille)
MIN_CHARS = 60        # en dessous, on ne crée pas un chunk isolé (bruit : titres orphelins)
OVERLAP_CHARS = 150   # recouvrement — ne s'applique qu'à une coupe de TAILLE (filet fiche géante)
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


# ----------------------------------------------------------------------------
# Découpe par FICHE : 1 fiche = 1 chunk (méthode EN VIGUEUR — cf. CLAUDE.md)
# ----------------------------------------------------------------------------
# Document (1 activité = 1 matière, sans « développe aussi ») : chaque fiche est
#     <titre>
#     Matière : <X>                                            <- ligne qui OUVRE la fiche (18 en tout)
#     Objectifs / Matériel / Déroulé / À observer / Sécurité   <- corps
# La ligne « Matière : … » (en début de ligne) est le repère de fiche ; son titre est TOUJOURS
# la ligne juste avant. On reconstruit chaque fiche en une « page » autonome COMMENÇANT par sa
# ligne « Matière : … » (titre reporté en 2e ligne). L'intro (avant la 1re fiche) et la queue
# méta (note « Hygiène… » vide, bloc « Sources & attribution ») ne sont pas des fiches et ne sont
# pas vectorisées : la zone des fiches s'arrête au 1er marqueur de queue. Si aucune fiche, on LÈVE
# (jamais de base trouée en silence). Le chunker générique fait alors un chunk par fiche.
_MATIERE_RE = re.compile(r"^Matière\s*:")          # ligne qui ouvre une fiche (début de ligne)
_TAIL_MARKERS = ("Hygiène et premiers gestes d'autonomie", "Sources & attribution")


def _split_into_fiches(pages: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Reconstruit les fiches depuis le texte extrait : UNE entrée (n° page, texte) PAR FICHE,
    chaque texte COMMENÇANT par sa ligne « Matière : … ».
    - une fiche s'ouvre par une ligne qui COMMENCE par « Matière : » ;
    - son titre est la ligne juste avant ; on réordonne : Matière, titre, corps ;
    - la zone des fiches s'arrête au 1er marqueur de queue (_TAIL_MARKERS) : l'intro d'avant la
      1re fiche et la méta d'après (Hygiène vide, Sources) ne sont pas vectorisées.
    Lève si aucune fiche, ou si une fiche n'a pas de titre devant elle."""
    flat: list[tuple[int, str]] = []
    for pg, t in pages:
        for ln in t.splitlines():
            s = ln.strip()
            if s:
                flat.append((pg, s))
    lines = [s for _, s in flat]
    pgs = [pg for pg, _ in flat]

    # fin de zone : 1re ligne portant un marqueur de queue méta (Hygiène/Sources)
    meta = next((i for i, s in enumerate(lines) if any(m in s for m in _TAIL_MARKERS)), len(lines))

    anchors = [i for i in range(meta) if _MATIERE_RE.match(lines[i])]
    if not anchors:
        raise RuntimeError(
            "Découpe crèche : aucune ligne de fiche « Matière : … » avant la zone méta. "
            "Extraction refusée (structure du référentiel inattendue)."
        )
    # chaque fiche doit avoir une ligne de titre juste avant sa ligne « Matière : »
    for a in anchors:
        if a == 0 or _MATIERE_RE.match(lines[a - 1]):
            raise RuntimeError(
                f"Découpe crèche : fiche « Matière : » sans titre devant elle (ligne {a}). "
                "Extraction refusée pour ne pas produire un chunk sans son titre."
            )

    starts = [a - 1 for a in anchors]          # chaque fiche commence à son titre
    ends = starts[1:] + [meta]                 # ... et finit au début de la suivante / à la méta
    out: list[tuple[int, str]] = []
    for st, en in zip(starts, ends):
        block = lines[st:en]
        mi = next(j for j, l in enumerate(block) if _MATIERE_RE.match(l))   # ligne « Matière : … »
        reordered = [block[mi]] + block[:mi] + block[mi + 1:]               # Matière, titre(s), corps
        out.append((pgs[st], "\n".join(reordered)))
    return out


def extract_pages(pdf_path) -> list[tuple[int, str]]:
    """(n° page depuis 1, texte propre) — extraction colonne-par-colonne + retrait du mobilier,
    PUIS reconstruction par fiche (_split_into_fiches, qui écarte aussi l'intro et la queue méta) :
    renvoie UNE entrée par fiche, chacune commençant par « Matière : … ».
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
    return _split_into_fiches(pages)                          # l'intro et la méta sont écartées dans _split_into_fiches


# ----------------------------------------------------------------------------
# Interface attendue par le chunker générique
# ----------------------------------------------------------------------------
def section_boundary(line: str) -> Optional[str]:
    """Plus de frontière signalée ligne par ligne : le découpage par fiche est fait EN AMONT,
    à l'extraction (_split_into_fiches renvoie une « page » par fiche). Le chunker produit donc
    un chunk par page = un chunk par fiche. On renvoie None (aucune coupe de structure ici) ;
    seul le filet de TAILLE (MAX_CHARS) jouerait, à l'intérieur d'une fiche géante."""
    return None


def chunk_metadata(marker: Optional[str], page: int) -> dict[str, Any]:
    """Métadonnées d'un chunk. Pas d'option A/B ici -> option = "". Le niveau et la source
    ne sont PAS posés ici : ils sont récupérés par jointure via referentiel_id (cap relationnel)."""
    return {"option": "", "page": page}


def dedup_key(text: str, meta: dict) -> tuple:
    """Deux chunks de texte identique sont des doublons (on garde le 1er). Filet contre un
    éventuel passage répété à l'identique."""
    return (text,)
