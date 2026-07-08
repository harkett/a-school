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
Le tag d'âge est MULTI-VALUÉ ; il est porté dans meta["age"] (liste de bandes). Le FILTRE par
niveau se fait À L'INGESTION, structurellement : filtrer_chunks(chunks, collection) ne garde que
les activités de la tranche d'âge de la collection (Bébés -> 0-1 ; Moyens/Grands -> 1-3). AUCUNE
colonne en base, AUCUN filtre à la recherche (cf. immuabilité de la structure). option = "" partout.

Pas d'option A/B ici (le document n'en a pas) : chaque chunk est tagué option = "".
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

# --- Découpe : 1 ACTIVITÉ = 1 CHUNK (frontière = titre d'activité, pas taille fixe) ---
MAX_CHARS = 4000      # plafond de sécurité (une activité n'atteint jamais cette taille, ~800 max mesuré)
MIN_CHARS = 60        # en dessous, pas de chunk isolé (bruit : titres orphelins)
OVERLAP_CHARS = 150   # recouvrement — ne joue que sur une coupe de TAILLE (jamais atteinte ici)
SCORE_MIN = 0.30      # seuil de pertinence (1 - distance cosinus) — PROVISOIRE, à calibrer sur le
                      # corpus crèche une fois les 3 niveaux ingérés (étape « seuil »).

# --- Repères de structure (sur le TEXTE extrait du PDF) ---
# La frontière d'unité (la ligne « Âge ») N'EST PLUS un regex en dur : elle vient de la RÈGLE
# VALIDÉE par l'admin, rangée À CÔTÉ DU PDF du couple traité
# (REFERENTIELS/<CYCLE>/<NIVEAU>/regle-decoupe.json, champ critere_technique). Une règle PAR
# référentiel : le code voit 3 référentiels crèche distincts (Bébés, Moyens, Grands) → 3 règles,
# chacune dans son dossier, à côté de son PDF. Pas de règle validée -> pas de découpage
# (cap « aSchool n'invente rien »).
_DOMAINE_RE = re.compile(r"^\s*DOMAINE\s+\d")           # en-tête « DOMAINE n — … » (borne, pas activité)
_TAIL_RE    = re.compile(r"^\s*(À VALIDER|Sources\s*&\s*attribution|Sources\s+et\s+attribution)")
_RENVOI_RE  = re.compile(r"\(renvoi\)\s*$")             # ligne « … (renvoi) » (pointeur, pas activité)

# Motif de frontière courant : (re)chargé par extract_pages à CHAQUE ingestion (depuis la règle
# du couple, à côté du PDF traité), réutilisé par section_boundary sans relire le fichier.
_MOTIF: Optional[re.Pattern] = None


def _regle_path_for(pdf_path) -> Path:
    """Chemin de la règle de découpe du couple : le regle-decoupe.json rangé DANS LE MÊME
    DOSSIER que le PDF traité (REFERENTIELS/<CYCLE>/<NIVEAU>/). Seul point qui localise la
    règle — dérivé du PDF, donc automatiquement le bon couple, sans passer le niveau en
    paramètre. (Point de couture pour les tests : monkeypatchable.)"""
    return Path(pdf_path).parent / "regle-decoupe.json"


def _charger_motif_valide(regle_path: Path) -> re.Pattern:
    """Lit la règle de découpe validée (à côté du PDF) et compile son critère technique en motif
    de frontière. Refuse (lève) si la règle est absente, NON validée, ou sans critère : pas de
    découpage tant que l'admin n'a pas validé (cap « aSchool n'invente rien »)."""
    if not regle_path.exists():
        raise RuntimeError(
            f"Règle de découpe absente ({regle_path}). "
            "Découpage refusé : l'admin doit d'abord déposer et valider la règle du couple."
        )
    try:
        data = json.loads(regle_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Règle de découpe illisible ({regle_path}) : {e}")
    if not data.get("valide"):
        raise RuntimeError(
            "Règle de découpe NON validée par l'admin. Découpage refusé "
            "(aSchool n'invente rien : la règle doit être validée avant d'ingérer)."
        )
    motif = (data.get("critere_technique") or "").strip()
    if not motif:
        raise RuntimeError("Règle de découpe : critère technique vide. Découpage refusé.")
    return re.compile(motif)


def _motif_courant(pdf_path) -> re.Pattern:
    """Recharge le motif validé (règle du couple, à côté du PDF) et le mémorise pour la passe de
    découpage en cours (extract_pages tourne toujours avant section_boundary, qui réutilise ce motif)."""
    global _MOTIF
    _MOTIF = _charger_motif_valide(_regle_path_for(pdf_path))
    return _MOTIF

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
    jamais de base trouée en silence). Lève AUSSI si la règle de découpe n'est pas validée."""
    rx = _motif_courant(pdf_path)   # frontière = règle VALIDÉE du couple (lève AVANT lecture si non validée)
    import pdfplumber  # import paresseux

    raw: list[tuple[int, str]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            for ln in (page.extract_text() or "").split("\n"):
                raw.append((i, ln))
    lines = [ln for _, ln in raw]
    page_of = [pg for pg, _ in raw]

    age_idx = [i for i, ln in enumerate(lines) if rx.match(ln)]
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
    c'est chunk_metadata qui le pose sur le chunk. Le motif vient de la règle validée du couple,
    mémorisé par extract_pages (qui tourne TOUJOURS avant). Appelé sans motif chargé -> lève
    (jamais un découpage sans règle validée)."""
    if _MOTIF is None:
        raise RuntimeError(
            "section_boundary appelé sans motif chargé : extract_pages doit tourner d'abord "
            "(c'est lui qui charge la règle validée du couple, à côté du PDF)."
        )
    m = _MOTIF.match(line)
    if not m:
        return None
    valeur = m.group(1) if m.groups() else m.group(0)
    return _age_bands(valeur)


def chunk_metadata(marker: Optional[Any], page: int) -> dict[str, Any]:
    """Métadonnées d'un chunk. `marker` = bandes d'âge de l'activité (via section_boundary).
    - option = "" : pas d'option A/B (clé attendue par l'ingestion, gardée telle quelle) ;
    - age    = liste triée des bandes (le tag d'âge du chunk).
    Niveau et source ne sont PAS posés ici (jointure via referentiel_id). Le tag `age` sert au
    FILTRE par niveau à l'ingestion (filtrer_chunks) ; il n'est pas persisté en colonne."""
    bandes = sorted(marker) if marker else []
    return {"option": "", "age": bandes, "page": page}


def dedup_key(text: str, meta: dict) -> tuple:
    """Deux chunks de texte identique sont des doublons (on garde le 1er). Filet."""
    return (text,)


# --- Filtrage par niveau À L'INGESTION (structurel) : chaque collection ne garde que les
#     activités de SA tranche d'âge. C'est la règle « quel contenu pour quel niveau », qui vit
#     dans le CODE de la fiche (jamais une colonne en base) — cf. immuabilité de la structure.
_COLLECTION_BANDE = {
    "bebes_0_1_an":   _BANDE_BEBES,   # Bébés  -> bande 0-1
    "moyens_1_2_ans": _BANDE_1_3,     # Moyens -> bande 1-3
    "grands_2_3_ans": _BANDE_1_3,     # Grands -> bande 1-3
}


def filtrer_chunks(chunks: list[dict], collection: str) -> list[dict]:
    """Ne garde que les chunks dont la tranche d'âge inclut celle de la collection (Bébés -> 0-1 ;
    Moyens et Grands -> 1-3). Lève si la collection est inconnue — jamais un filtre muet qui
    laisserait passer tout le corpus dans le mauvais niveau."""
    bande = _COLLECTION_BANDE.get(collection)
    if bande is None:
        raise RuntimeError(
            f"Collection crèche inconnue pour le filtre d'âge : {collection!r}. "
            f"Attendu l'une de {sorted(_COLLECTION_BANDE)}."
        )
    return [c for c in chunks if bande in c["meta"].get("age", [])]


def _age_est_flou(valeur_age: str) -> bool:
    """Vrai si l'étiquette d'âge n'a matché AUCUN motif net et est tombée dans le repli de
    _age_bands (« dès ~2 ans », « tout-petits »…) → cas à faire confirmer par l'admin.
    Miroir exact des branches de _age_bands (mêmes tests, mêmes sous-chaînes)."""
    s = valeur_age.lower()
    if "0-1" in s and "1-3" in s:
        return False
    if "bébés-3" in s or "bebes-3" in s:
        return False
    if "1-3" in s:
        return False
    return True


def apercu_unites(chunks: list[dict], collection: str) -> dict:
    """Aperçu LISIBLE du découpage pour l'écran admin (aucun calcul métier neuf : on relit ce que
    le moteur a déjà produit). Par unité : titre (2e ligne du chunk), étiquette d'âge brute (1re
    ligne), bandes (tag meta["age"]), flou (âge à confirmer), et appartenance au niveau demandé.
    Plus les totaux : nombre d'unités, et combien reviennent à ce niveau (même règle que
    filtrer_chunks). `collection` inconnue -> bande None -> total_niveau = 0 (aucune fausse info)."""
    bande_niveau = _COLLECTION_BANDE.get(collection)
    if _MOTIF is None:
        raise RuntimeError(
            "apercu_unites appelé sans motif chargé : extract_pages doit tourner d'abord "
            "(il charge la règle validée du couple)."
        )
    rx = _MOTIF
    unites: list[dict] = []
    for c in chunks:
        lignes = c["text"].split("\n")
        m = rx.match(lignes[0]) if lignes else None
        valeur = (m.group(1) if (m and m.groups()) else (m.group(0) if m else "")).strip()
        titre = lignes[1].strip() if len(lignes) > 1 and lignes[1].strip() else "(sans titre)"
        bandes = c["meta"].get("age", [])
        unites.append({
            "titre": titre,
            "age_label": valeur,
            "bandes": bandes,
            "flou": _age_est_flou(valeur),
            "dans_niveau": bool(bande_niveau) and bande_niveau in bandes,
        })
    return {
        "total": len(unites),
        "bande_niveau": bande_niveau,
        "total_niveau": sum(1 for u in unites if u["dans_niveau"]),
        "unites": unites,
    }
