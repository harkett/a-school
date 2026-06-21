"""Fiche de réglages — BTS CIEL option A. PREMIÈRE fiche, PAS un gabarit universel.

Tout ce qui est propre à CIEL vit ici : où est le PDF, comment on découpe, comment on
tague les chunks. Le moteur (chunker générique + retrieve) n'en sait rien. Ajouter un
autre référentiel = écrire une autre fiche comme celle-ci, ZÉRO ligne touchée au moteur.

Découpage option A / B : seules 3 sections du référentiel sont spécifiques à l'option B
(II.2.3, III.1.3, III.2.2). Tout le reste (présentation, activités/compétences option A,
et surtout les enseignements généraux III.3 — Maths, Anglais, Français…) s'applique à
l'option A → tagué 'A'. Le détecteur se cale sur le NUMÉRO de section (ASCII, robuste à
l'encodage), en ignorant le sommaire.

Non négociable : le `niveau` est posé sur CHAQUE chunk dès l'ingestion — c'est le défaut
de `maths_cycle4` (pas de niveau) qu'on ne reproduit PAS ici.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

# --- Source : BTS CIEL option A ---
_ROOT = Path(__file__).resolve().parents[3]
PDF_PATH = _ROOT / "REFERENTIELS" / "BTS-CIEL-option-A" / "15324-ref-bts-ciel-vpub-v01.pdf"
EXTRACTION_TXT = PDF_PATH.parent / "extraction-texte.txt"

COLLECTION = "bts_ciel_optionA"
NIVEAU = "BTS CIEL option A"          # non négociable — posé sur CHAQUE chunk
CYCLE = "Supérieur"
SOURCE = "REF-BTS-CIEL-2023"
LABEL = "Référentiel BTS CIEL — éduscol STI, rénovation 2023"

MAX_CHARS = 900   # taille cible d'un chunk
MIN_CHARS = 60    # en dessous, on ne crée pas un chunk isolé (bruit : n° de page, titres orphelins)

# Sections SPÉCIFIQUES à l'option B → tag 'B'. Tout autre en-tête reconnu → 'A'.
OPTION_B_SECTIONS = {"II.2.3", "III.1.3", "III.2.2"}
# En-tête de section = « ANNEXE <romain> » OU un numéro « <romain>.<n>[.<n>[.<n>]] ».
SECTION_RE = re.compile(r"^(ANNEXE\s+[IVX]+|[IVX]+\.\d+(?:\.\d+){0,2})\b")
TOC_RE = re.compile(r"\.{4,}")  # lignes du sommaire (pointillés de table des matières)


def section_boundary(line: str) -> Optional[str]:
    """Marqueur de frontière : numéro de section si `line` est un en-tête (hors sommaire),
    sinon None. Donné tel quel au découpeur générique, qui le traite comme opaque.
    (Ex-_section_number de ingest_referentiel.py.)"""
    s = line.strip()
    if not s or TOC_RE.search(s):
        return None
    m = SECTION_RE.match(s)
    return m.group(0) if m else None


def chunk_metadata(marker: Optional[str], page: int) -> dict[str, Any]:
    """Métadonnées posées sur chaque chunk. La décision option A/B vit ICI : un chunk
    relève de l'option B si sa section courante est l'une des sections spécifiques B ;
    sinon 'A' (commun + option A). `marker` None (avant tout en-tête) ⇒ 'A'."""
    option = "B" if marker in OPTION_B_SECTIONS else "A"
    return {
        "source": SOURCE,
        "label": LABEL,
        "cycle": CYCLE,
        "niveau": NIVEAU,        # <-- non négociable, sur CHAQUE chunk
        "option": option,
        "page": page,
    }
