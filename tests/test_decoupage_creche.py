r"""Preuve — points 5 & 6 + BRIQUE 1a (arbitrage du flou par donnée) : le découpage crèche est
piloté par la RÈGLE VALIDÉE (motif lu du fichier, plus de regex en dur), le tag d'âge trie chaque
niveau à l'ingestion, et les cas FLOUS ne sont plus devinés en dur : leur tranche est lue dans
l'ARBITRAGE (donnée par couple, arbitrage-flou.json). Flou non tranché -> ingestion REFUSÉE.

Ce que ce test PROUVE (chaîne réelle sur le VRAI PDF crèche, sans base) :
  1. Garde-fou règle (point 5) : règle NON validée / absente -> extract_pages LÈVE.
  2. Motif validé (point 5) : 27 activités découpées, frontière venant du fichier (pas d'un regex en dur).
  3. Filtre par niveau (étape 6) + arbitrage (1a) :
     - flou NON tranché  -> filtrer_chunks REFUSE (cap « n'invente rien », jamais un trou muet) ;
     - flou tranché 1-3  -> 18 / 27 / 27 (Bébés / Moyens / Grands), piloté par la DONNÉE ;
     - flou tranché 0-1+1-3 -> la DONNÉE décide : ce flou bascule aussi côté Bébés (19).
     - collection inconnue -> LÈVE (jamais un filtre muet).

Isolation : _regle_path_for ET _arbitrage_path_for sont monkeypatchés vers des fichiers temporaires
— les vrais regle-decoupe.json / arbitrage-flou.json committés (par couple, à côté du PDF) ne sont
jamais touchés.

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_decoupage_creche.py -q
"""
import json
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import pytest

import backend.rag.referentiels.creche_0_3_ans as creche
from backend.rag.chunker import build_chunks

PDF = os.path.join(ROOT, "REFERENTIELS", "CRECHE", "BEBES_0_1_AN", "referentiel.pdf")
MOTIF_REEL = json.loads(
    open(os.path.join(ROOT, "REFERENTIELS", "CRECHE", "BEBES_0_1_AN", "regle-decoupe.json"),
         encoding="utf-8").read()
)["critere_technique"]

# Les 3 libellés flous réels du document (mesurés) : sans « 1-3 » explicite, donc à trancher.
FLOUS = ["dès ~2 ans", "tout-petits (dans notre bande)", "très jeunes enfants (dans notre bande)"]


def _regle(tmp_path, monkeypatch, valide, motif=MOTIF_REEL):
    """Pose une règle temporaire et fait pointer la fiche dessus (via _regle_path_for), quel que
    soit le PDF passé — isole du vrai regle-decoupe.json du couple."""
    f = tmp_path / "regle-decoupe.json"
    f.write_text(json.dumps({
        "explication_clair": "Une unité = une activité (ligne d'âge).",
        "critere_technique": motif, "depose_par": "dev", "valide": valide,
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(creche, "_regle_path_for", lambda _pdf: f)
    monkeypatch.setattr(creche, "_MOTIF", None)
    return f


def _arbitrage(tmp_path, monkeypatch, mapping):
    """Pose un arbitrage-flou.json temporaire et fait pointer la fiche dessus (via
    _arbitrage_path_for) — isole du vrai arbitrage committé. `mapping` = { libellé : [bandes] }.
    Ne rien passer (mapping vide) = aucun arbitrage (cas flou non tranché)."""
    f = tmp_path / "arbitrage-flou.json"
    f.write_text(json.dumps({"arbitrages": mapping}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(creche, "_arbitrage_path_for", lambda _pdf: f)
    return f


def _decouper():
    pages = creche.extract_pages(PDF)   # (re)charge motif + arbitrage depuis les chemins (monkeypatchés)
    return build_chunks(
        pages, max_chars=creche.MAX_CHARS, min_chars=creche.MIN_CHARS,
        overlap_chars=creche.OVERLAP_CHARS, is_boundary=creche.section_boundary,
        chunk_metadata=creche.chunk_metadata, dedup_key=creche.dedup_key,
    )


# ── Garde-fous règle (point 5) ────────────────────────────────────────────────

def test_gate_regle_non_validee_leve(tmp_path, monkeypatch):
    _regle(tmp_path, monkeypatch, valide=False)
    with pytest.raises(RuntimeError, match="NON validée"):
        creche.extract_pages(PDF)


def test_gate_regle_absente_leve(tmp_path, monkeypatch):
    monkeypatch.setattr(creche, "_regle_path_for", lambda _pdf: tmp_path / "pas-de-fichier.json")
    monkeypatch.setattr(creche, "_MOTIF", None)
    with pytest.raises(RuntimeError, match="absente"):
        creche.extract_pages(PDF)


# ── Découpage (point 5) : 27 activités, quel que soit l'arbitrage ─────────────

def test_decoupage_pilote_par_motif_valide(tmp_path, monkeypatch):
    _regle(tmp_path, monkeypatch, valide=True)
    _arbitrage(tmp_path, monkeypatch, {})   # peu importe : le découpage ne dépend pas de l'arbitrage
    chunks = _decouper()
    assert len(chunks) == 27, f"attendu 27 activités, obtenu {len(chunks)}"


# ── BRIQUE 1a : le flou est piloté par la DONNÉE ─────────────────────────────

def test_flou_non_tranche_refuse_ingestion(tmp_path, monkeypatch):
    """Sens 1 : sans arbitrage, les 3 flous n'ont pas de bande -> filtrer_chunks REFUSE."""
    _regle(tmp_path, monkeypatch, valide=True)
    _arbitrage(tmp_path, monkeypatch, {})            # aucun flou tranché
    chunks = _decouper()
    with pytest.raises(RuntimeError, match="NON tranché"):
        creche.filtrer_chunks(chunks, "moyens_1_2_ans")
    # et les 3 flous sont bien sans bande (non devinés)
    assert sum(1 for c in chunks if not c["meta"]["age"]) == 3


def test_flou_tranche_1_3_passe_18_27_27(tmp_path, monkeypatch):
    """Sens 2 : les 3 flous tranchés « 1-3 » par l'admin -> ingestion passe, 18 / 27 / 27."""
    _regle(tmp_path, monkeypatch, valide=True)
    _arbitrage(tmp_path, monkeypatch, {lbl: ["1-3"] for lbl in FLOUS})
    chunks = _decouper()
    assert len(creche.filtrer_chunks(chunks, "bebes_0_1_an")) == 18
    assert len(creche.filtrer_chunks(chunks, "moyens_1_2_ans")) == 27
    assert len(creche.filtrer_chunks(chunks, "grands_2_3_ans")) == 27


def test_la_donnee_decide_flou_0_1_bascule_bebes(tmp_path, monkeypatch):
    """Preuve que c'est la DONNÉE qui décide (pas un guess figé) : un flou tranché « 0-1 + 1-3 »
    par l'admin bascule cette activité aussi côté Bébés -> Bébés passe de 18 à 19."""
    _regle(tmp_path, monkeypatch, valide=True)
    mapping = {lbl: ["1-3"] for lbl in FLOUS}
    mapping[FLOUS[0]] = ["0-1", "1-3"]               # l'admin tranche CE flou dans les deux bandes
    _arbitrage(tmp_path, monkeypatch, mapping)
    chunks = _decouper()
    assert len(creche.filtrer_chunks(chunks, "bebes_0_1_an")) == 19
    assert len(creche.filtrer_chunks(chunks, "moyens_1_2_ans")) == 27


def test_filtre_collection_inconnue_leve():
    with pytest.raises(RuntimeError, match="inconnue"):
        creche.filtrer_chunks([], "collection-bidon")


def test_backstop_bande_inconnue_refuse(tmp_path, monkeypatch):
    """Backstop anti-trou-muet : un arbitrage-flou.json édité à la main avec une bande INCONNUE
    (« 9-9 ») rangerait l'unité dans aucune collection -> filtrer_chunks REFUSE (jamais un trou)."""
    _regle(tmp_path, monkeypatch, valide=True)
    _arbitrage(tmp_path, monkeypatch, {lbl: ["9-9"] for lbl in FLOUS})   # bande hors {0-1, 1-3}
    chunks = _decouper()
    with pytest.raises(RuntimeError, match="inconnue"):
        creche.filtrer_chunks(chunks, "moyens_1_2_ans")


# ── Aperçu admin : signale le flou + son état d'arbitrage ────────────────────

def test_apercu_flou_non_tranche_signale(tmp_path, monkeypatch):
    """Sans arbitrage : les 3 flous sont signalés flou=True, arbitre=False, bandes vides ;
    les unités nettes restent arbitre=True avec leurs bandes."""
    _regle(tmp_path, monkeypatch, valide=True)
    _arbitrage(tmp_path, monkeypatch, {})
    ap = creche.apercu_unites(_decouper(), "moyens_1_2_ans")
    assert ap["total"] == 27
    flous = [u for u in ap["unites"] if u["flou"]]
    assert len(flous) == 3
    assert all(u["arbitre"] is False and u["bandes"] == [] for u in flous)   # à trancher
    nets = [u for u in ap["unites"] if not u["flou"]]
    assert all(u["arbitre"] is True and u["bandes"] for u in nets)


def test_apercu_flou_tranche_arbitre_true(tmp_path, monkeypatch):
    """Avec arbitrage 1-3 : les flous passent arbitre=True, bandes non vides, et Moyens
    récupère tout le niveau (27)."""
    _regle(tmp_path, monkeypatch, valide=True)
    _arbitrage(tmp_path, monkeypatch, {lbl: ["1-3"] for lbl in FLOUS})
    ap = creche.apercu_unites(_decouper(), "moyens_1_2_ans")
    assert ap["total_niveau"] == 27
    assert all(u["arbitre"] is True for u in ap["unites"])
    assert all(u["bandes"] for u in ap["unites"])


def test_apercu_expose_les_options_darbitrage(tmp_path, monkeypatch):
    """BRIQUE 1c : l'aperçu porte les options que l'admin peut choisir pour trancher un flou —
    elles viennent de la FICHE (BANDES_VALIDES), jamais écrites en dur dans l'écran. Même source
    que le validateur du POST -> le front ne peut proposer que des options que le POST accepte."""
    _regle(tmp_path, monkeypatch, valide=True)
    _arbitrage(tmp_path, monkeypatch, {})
    ap = creche.apercu_unites(_decouper(), "moyens_1_2_ans")
    assert ap["options_arbitrage"] == sorted(creche.BANDES_VALIDES) == ["0-1", "1-3"]
