"""Fiche de réglages — Crèche, éveil 0-3 ans (compilation aSchool de 2 sources UNICEF).

Deuxième fiche, après CIEL. Elle sert les TROIS couples de la crèche — Bébés (0-1 an),
Moyens (1-2 ans), Grands (2-3 ans) — qui partagent le MÊME document 0-3 ans. Le moteur
(chunker générique + retrieve) n'en sait rien ; toute la spécificité crèche vit ici.

Structure de CE document (PDF simple, une colonne) : rangé par ACTIVITÉ, groupées sous 4 grands
DOMAINES de développement. Chaque activité s'ouvre par son titre, suivi de sa ligne « - Âge : … »
puis de ses champs (Matériel, Objectifs, Déroulé, À observer, Sécurité). PAS de ligne « Matière : »
(la matière est trouvée par le SENS à la recherche, pas taguée).

Découpe : 1 ACTIVITÉ = 1 CHUNK. Frontière = le titre d'activité (la ligne juste au-dessus d'une
ligne « Âge »). extract_pages reconstruit chaque activité en une « page » autonome, la ligne « Âge »
remontée en tête (pour servir de marqueur de frontière au chunker) ; le chunker en fait 1 chunk chacune.

Critère de tri du document = l'ÂGE. Décisions figées le 06/07/2026 :
  - « Bébés (0-1) · 1-3 ans » et « Bébés-3 ans »   -> les 3 niveaux (bandes 0-1 ET 1-3)
  - « 1-3 ans »                                     -> Moyens + Grands (bande 1-3)
  - âges flous (« dès ~2 ans », « tout-petits »…)  -> Moyens + Grands (doute -> inclusif, le prof tranche)
Le tag d'âge est MULTI-VALUÉ ; il est porté dans meta["age"] (liste de bandes). ATTENTION : sa
PERSISTANCE en base et le FILTRE d'appartenance à la recherche ne sont PAS branchés ici — étape
séparée (colonne + retrieve), à décider. En l'état option = "" : l'ingestion actuelle est inchangée.

Pas d'option A/B ici (le document n'en a pas) : chaque chunk est tagué option = "".
"""
from __future__ import annotations

import re
from typing import Any, Optional

# --- Découpe : 1 ACTIVITÉ = 1 CHUNK (frontière = titre d'activité, pas taille fixe) ---
MAX_CHARS = 4000      # plafond de sécurité (une activité n'atteint jamais cette taille, ~800 max mesuré)
MIN_CHARS = 60        # en dessous, pas de chunk isolé (bruit : titres orphelins)
OVERLAP_CHARS = 150   # recouvrement — ne joue que sur une coupe de TAILLE (jamais atteinte ici)
SCORE_MIN = 0.30      # seuil de pertinence (1 - distance cosinus) — PROVISOIRE, à calibrer sur le
                      # corpus crèche une fois les 3 niveaux ingérés (étape « seuil »).

# --- Repères de structure (sur le TEXTE extrait du PDF) ---
_AGE_RE     = re.compile(r"^\s*-?\s*Âge\s*:\s*(.+)$")   # ligne « - Âge : … »
_DOMAINE_RE = re.compile(r"^\s*DOMAINE\s+\d")           # en-tête « DOMAINE n — … » (borne, pas activité)
_TAIL_RE    = re.compile(r"^\s*(À VALIDER|Sources\s*&\s*attribution|Sources\s+et\s+attribution)")
_RENVOI_RE  = re.compile(r"\(renvoi\)\s*$")             # ligne « … (renvoi) » (pointeur, pas activité)

# --- Bandes d'âge (le tag) : « 0-1 » (Bébés) et « 1-3 » (Moyens + Grands) ---
_BANDE_BEBES = "0-1"
_BANDE_1_3   = "1-3"   # 1-3 ans = Moyens (1-2) + Grands (2-3)


# PROVISOIRE — donnée métier à sortir en base (chantier analyse amont, cf. D60).
# La correspondance « libellé d'âge -> niveaux » est de la DONNÉE, pas du code (cap : rien de métier
# en dur). Figée ici le temps du prototype, comme SCORE_MIN. À déplacer en base/config au moment où
# l'analyse amont devient data-driven ; l'arbitration des libellés flous doit y vivre, pas dans ce .py.
def _age_bands(valeur_age: str) -> frozenset[str]:
    """Valeur d'une ligne « Âge : … » -> bandes d'âge (décisions figées 06/07/2026). Le « · » du
    document ressort en « - » à l'extraction ; on teste des sous-chaînes robustes."""
    s = valeur_age.lower()
    if "0-1" in s and "1-3" in s:          # « Bébés (0-1) - 1-3 ans »
        return frozenset({_BANDE_BEBES, _BANDE_1_3})
    if "bébés-3" in s or "bebes-3" in s:   # « Bébés-3 ans »
        return frozenset({_BANDE_BEBES, _BANDE_1_3})
    if "1-3" in s:                         # « 1-3 ans » (et « dès ~2 ans (dans notre bande 1-3) »)
        return frozenset({_BANDE_1_3})
    return frozenset({_BANDE_1_3})         # flous restants (« dès ~2 ans », « tout-petits »…) -> Moyens + Grands


def extract_pages(pdf_path) -> list[tuple[int, str]]:
    """(n° page depuis 1, texte) — UNE entrée par ACTIVITÉ (1 activité = 1 chunk).
    Extraction directe (pdfplumber, page.extract_text : PDF une colonne), puis :
      - repère chaque activité par sa ligne « Âge » ; son titre = la ligne juste au-dessus ;
      - borne chaque activité au prochain repère (titre suivant, DOMAINE, queue, renvoi) ;
      - remonte la ligne « Âge » en tête du bloc (marqueur de frontière pour le chunker).
    Lève si aucune activité, ou si une activité n'a pas de titre propre (jamais de chunk sans titre,
    jamais de base trouée en silence)."""
    import pdfplumber  # import paresseux

    raw: list[tuple[int, str]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            for ln in (page.extract_text() or "").split("\n"):
                raw.append((i, ln))
    lines = [ln for _, ln in raw]
    page_of = [pg for pg, _ in raw]

    age_idx = [i for i, ln in enumerate(lines) if _AGE_RE.match(ln)]
    if not age_idx:
        raise RuntimeError(
            "Découpe crèche 0-3 : aucune ligne « Âge : » trouvée. "
            "Extraction refusée (structure du référentiel inattendue)."
        )

    def _titre_au_dessus(i: int) -> Optional[int]:
        j = i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        return j if j >= 0 else None

    titre_idx: list[int] = []
    for a in age_idx:
        t = _titre_au_dessus(a)
        titre = lines[t].strip() if t is not None else ""
        if (t is None or not titre or titre.startswith("-")
                or _DOMAINE_RE.match(titre) or _TAIL_RE.match(titre)):
            raise RuntimeError(
                f"Découpe crèche 0-3 : activité sans titre propre devant sa ligne « Âge » "
                f"(ligne {a} : {lines[a]!r}). Extraction refusée."
            )
        titre_idx.append(t)

    # bornes = titres d'activité + en-têtes DOMAINE + début de queue + renvois
    bornes = set(titre_idx)
    for i, ln in enumerate(lines):
        if _DOMAINE_RE.match(ln) or _TAIL_RE.match(ln) or _RENVOI_RE.search(ln):
            bornes.add(i)
    bornes = sorted(bornes)

    out: list[tuple[int, str]] = []
    for a, t in zip(age_idx, titre_idx):
        fin = next((b for b in bornes if b > t), len(lines))     # jusqu'au prochain repère
        corps = [lines[k].strip() for k in range(t, fin)
                 if k not in (a, t) and lines[k].strip()]         # champs, sans titre ni ligne Âge
        bloc = [lines[a].strip(), lines[t].strip()] + corps       # Âge en tête, puis titre, puis corps
        out.append((page_of[t], "\n".join(bloc)))
    return out


def section_boundary(line: str) -> Optional[Any]:
    """Marqueur de frontière = le tag d'âge, renvoyé sur la ligne « Âge » (remontée en tête de chaque
    activité par extract_pages). Toute autre ligne -> None. Marqueur opaque pour le chunker ;
    c'est chunk_metadata qui le pose sur le chunk."""
    m = _AGE_RE.match(line)
    if not m:
        return None
    return _age_bands(m.group(1))


def chunk_metadata(marker: Optional[Any], page: int) -> dict[str, Any]:
    """Métadonnées d'un chunk. `marker` = bandes d'âge de l'activité (via section_boundary).
    - option = "" : pas d'option A/B (clé attendue par l'ingestion, gardée telle quelle) ;
    - age    = liste triée des bandes (le tag d'âge du chunk).
    Niveau et source ne sont PAS posés ici (jointure via referentiel_id). NB : persistance de `age`
    + filtre d'appartenance = étape séparée, non branchée ici."""
    bandes = sorted(marker) if marker else []
    return {"option": "", "age": bandes, "page": page}


def dedup_key(text: str, meta: dict) -> tuple:
    """Deux chunks de texte identique sont des doublons (on garde le 1er). Filet."""
    return (text,)
