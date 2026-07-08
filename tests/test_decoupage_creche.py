r"""Preuve — points 5 & 6 : le découpage crèche est piloté par la RÈGLE VALIDÉE (motif lu du
fichier, plus de regex en dur) et le tag d'âge trie chaque niveau à l'ingestion.

Ce que ce test PROUVE (chaîne réelle sur le VRAI PDF crèche, sans base) :
  1. Garde-fou (point 5) : règle NON validée -> extract_pages LÈVE (aSchool n'invente rien).
     Règle absente -> LÈVE aussi.
  2. Motif validé (point 5) : avec une règle validée, extract_pages + build_chunks découpent
     27 activités, la frontière venant du fichier (pas d'un regex en dur).
  3. Filtre par niveau (étape 6) : filtrer_chunks garde 18 pour Bébés (bande 0-1) et 27 pour
     Moyens/Grands (bande 1-3). Collection inconnue -> LÈVE (jamais un filtre muet).

Isolation : _regle_path_for est monkeypatché pour renvoyer un fichier temporaire — les vrais
regle-decoupe.json committés (un par couple, à côté du PDF) ne sont jamais touchés.

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
# Motif réel, lu depuis la vraie règle committée du COUPLE (à côté du PDF) : on prouve QUE ce
# motif-là pilote le découpage.
MOTIF_REEL = json.loads(
    open(os.path.join(ROOT, "REFERENTIELS", "CRECHE", "BEBES_0_1_AN", "regle-decoupe.json"),
         encoding="utf-8").read()
)["critere_technique"]


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


def _decouper():
    pages = creche.extract_pages(PDF)
    return build_chunks(
        pages, max_chars=creche.MAX_CHARS, min_chars=creche.MIN_CHARS,
        overlap_chars=creche.OVERLAP_CHARS, is_boundary=creche.section_boundary,
        chunk_metadata=creche.chunk_metadata, dedup_key=creche.dedup_key,
    )


def test_gate_regle_non_validee_leve(tmp_path, monkeypatch):
    _regle(tmp_path, monkeypatch, valide=False)
    with pytest.raises(RuntimeError, match="NON validée"):
        creche.extract_pages(PDF)


def test_gate_regle_absente_leve(tmp_path, monkeypatch):
    monkeypatch.setattr(creche, "_regle_path_for", lambda _pdf: tmp_path / "pas-de-fichier.json")
    monkeypatch.setattr(creche, "_MOTIF", None)
    with pytest.raises(RuntimeError, match="absente"):
        creche.extract_pages(PDF)


def test_decoupage_pilote_par_motif_valide(tmp_path, monkeypatch):
    _regle(tmp_path, monkeypatch, valide=True)
    chunks = _decouper()
    assert len(chunks) == 27, f"attendu 27 activités, obtenu {len(chunks)}"


def test_filtre_par_bande_18_et_27(tmp_path, monkeypatch):
    _regle(tmp_path, monkeypatch, valide=True)
    chunks = _decouper()
    bebes = creche.filtrer_chunks(chunks, "bebes_0_1_an")
    moyens = creche.filtrer_chunks(chunks, "moyens_1_2_ans")
    grands = creche.filtrer_chunks(chunks, "grands_2_3_ans")
    assert len(bebes) == 18, f"Bébés : attendu 18, obtenu {len(bebes)}"
    assert len(moyens) == 27, f"Moyens : attendu 27, obtenu {len(moyens)}"
    assert len(grands) == 27, f"Grands : attendu 27, obtenu {len(grands)}"
    assert all("0-1" in c["meta"]["age"] for c in bebes)   # Bébés : que des activités bande 0-1
    assert all("1-3" in c["meta"]["age"] for c in moyens)  # Moyens : que des activités bande 1-3


def test_filtre_collection_inconnue_leve():
    with pytest.raises(RuntimeError, match="inconnue"):
        creche.filtrer_chunks([], "collection-bidon")


def test_apercu_unites_bebes_totaux_titres_flou(tmp_path, monkeypatch):
    _regle(tmp_path, monkeypatch, valide=True)
    ap = creche.apercu_unites(_decouper(), "bebes_0_1_an")
    assert ap["total"] == 27
    assert ap["total_niveau"] == 18            # Bébés = bande 0-1
    assert ap["bande_niveau"] == "0-1"
    assert len(ap["unites"]) == 27
    # Chaque unité a un vrai titre (jamais « (sans titre) ») et au moins une bande.
    assert all(u["titre"] and u["titre"] != "(sans titre)" for u in ap["unites"])
    assert all(u["bandes"] for u in ap["unites"])
    # Cohérence dans_niveau <-> total_niveau.
    assert sum(1 for u in ap["unites"] if u["dans_niveau"]) == 18
    # Cas flous signalés (dès ~2 ans / tout-petits / très jeunes enfants) : exactement 3.
    flous = [u["age_label"] for u in ap["unites"] if u["flou"]]
    assert len(flous) == 3, f"attendu 3 flous, obtenu {len(flous)} : {flous}"


def test_apercu_unites_moyens_tout_le_niveau(tmp_path, monkeypatch):
    _regle(tmp_path, monkeypatch, valide=True)
    ap = creche.apercu_unites(_decouper(), "moyens_1_2_ans")
    assert ap["total"] == 27
    assert ap["total_niveau"] == 27            # Moyens = bande 1-3 -> toutes les activités
    assert ap["bande_niveau"] == "1-3"
    assert all(u["dans_niveau"] for u in ap["unites"])
