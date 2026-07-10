r"""Preuve — points 5 & 6 + BRIQUE 1a (arbitrage du flou par donnée) : le découpage crèche est
piloté par la RÈGLE VALIDÉE (motif lu EN BASE via charger_regle, plus de regex en dur ni de
fichier), le tag d'âge trie chaque niveau à l'ingestion, et les cas FLOUS ne sont plus devinés en
dur : leur tranche est lue dans l'ARBITRAGE (donnée du couple, colonne referentiels.arbitrage).
Flou non tranché -> ingestion REFUSÉE.

Ce que ce test PROUVE (chaîne réelle sur le VRAI PDF crèche, sans base) :
  1. Garde-fou règle (point 5) : charger_regle(ref non validé) LÈVE ; extract_pages sans règle
     chargée LÈVE (jamais un découpage sans règle validée).
  2. Motif validé (point 5) : 27 activités découpées, frontière venant de la règle en base.
  3. Filtre par niveau (étape 6) + arbitrage (1a) :
     - flou NON tranché  -> filtrer_chunks REFUSE (cap « n'invente rien », jamais un trou muet) ;
     - flou tranché 1-3  -> 18 / 27 / 27 (Bébés / Moyens / Grands), piloté par la DONNÉE ;
     - flou tranché 0-1+1-3 -> la DONNÉE décide : ce flou bascule aussi côté Bébés (19).
     - collection inconnue -> LÈVE (jamais un filtre muet).

Isolation : la règle + l'arbitrage sont fournis à la fiche via un FAUX `ref` (attributs regle_*),
comme le fait le socle depuis la ligne referentiels — plus aucun fichier lu.

Lancer : .\.venv\Scripts\python.exe -m pytest tests/test_decoupage_creche.py -q
"""
import json
import os
import sys
import types

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import pytest

import backend.rag.referentiels.creche_0_3_ans as creche
from backend.rag.chunker import build_chunks

PDF = os.path.join(ROOT, "REFERENTIELS", "CRECHE", "BEBES_0_1_AN", "referentiel.pdf")
MOTIF_REEL = r"^\s*-?\s*Âge\s*:\s*(.+)$"   # motif réel de la règle crèche (désormais EN BASE)

# Les 3 libellés flous réels du document (mesurés) : sans « 1-3 » explicite, donc à trancher.
FLOUS = ["dès ~2 ans", "tout-petits (dans notre bande)", "très jeunes enfants (dans notre bande)"]


def _ref(valide=True, motif=MOTIF_REEL, arbitrage=None):
    """Fausse ligne `referentiels` (attributs regle_*) — la fiche charge la règle DEPUIS cet objet,
    exactement comme le socle depuis la vraie ligne. `arbitrage` = dict {libellé: [bandes]} ou None."""
    return types.SimpleNamespace(
        regle_valide=valide,
        regle_motif=motif,
        arbitrage=(json.dumps(arbitrage, ensure_ascii=False) if arbitrage is not None else None),
    )


def _charger(valide=True, motif=MOTIF_REEL, arbitrage=None):
    """Charge la règle + l'arbitrage dans la fiche (pose _MOTIF et _ARBITRAGE), comme le socle."""
    creche._MOTIF = None
    creche.charger_regle(_ref(valide=valide, motif=motif, arbitrage=arbitrage))


def _decouper(arbitrage=None):
    _charger(valide=True, arbitrage=(arbitrage if arbitrage is not None else {}))
    pages = creche.extract_pages(PDF)   # utilise le motif chargé (base), plus aucun fichier
    return build_chunks(
        pages, max_chars=creche.MAX_CHARS, min_chars=creche.MIN_CHARS,
        overlap_chars=creche.OVERLAP_CHARS, is_boundary=creche.section_boundary,
        chunk_metadata=creche.chunk_metadata, dedup_key=creche.dedup_key,
    )


# ── Garde-fous règle (point 5) ────────────────────────────────────────────────

def test_gate_regle_non_validee_leve():
    creche._MOTIF = None
    with pytest.raises(RuntimeError, match="NON validée"):
        creche.charger_regle(_ref(valide=False))


def test_extract_sans_regle_chargee_leve():
    creche._MOTIF = None
    with pytest.raises(RuntimeError, match="sans règle chargée"):
        creche.extract_pages(PDF)


def test_charger_regle_motif_vide_leve():
    creche._MOTIF = None
    with pytest.raises(RuntimeError, match="vide"):
        creche.charger_regle(_ref(valide=True, motif="   "))


# ── Découpage (point 5) : 27 activités, quel que soit l'arbitrage ─────────────

def test_decoupage_pilote_par_motif_valide():
    chunks = _decouper({})   # peu importe l'arbitrage : le découpage n'en dépend pas
    assert len(chunks) == 27, f"attendu 27 activités, obtenu {len(chunks)}"


# ── BRIQUE 1a : le flou est piloté par la DONNÉE ─────────────────────────────

def test_flou_non_tranche_refuse_ingestion():
    """Sens 1 : sans arbitrage, les 3 flous n'ont pas de bande -> filtrer_chunks REFUSE."""
    chunks = _decouper({})            # aucun flou tranché
    with pytest.raises(RuntimeError, match="NON tranché"):
        creche.filtrer_chunks(chunks, "moyens_1_2_ans")
    # et les 3 flous sont bien sans bande (non devinés)
    assert sum(1 for c in chunks if not c["meta"]["age"]) == 3


def test_flou_tranche_1_3_passe_18_27_27():
    """Sens 2 : les 3 flous tranchés « 1-3 » par l'admin -> ingestion passe, 18 / 27 / 27."""
    chunks = _decouper({lbl: ["1-3"] for lbl in FLOUS})
    assert len(creche.filtrer_chunks(chunks, "bebes_0_1_an")) == 18
    assert len(creche.filtrer_chunks(chunks, "moyens_1_2_ans")) == 27
    assert len(creche.filtrer_chunks(chunks, "grands_2_3_ans")) == 27


def test_la_donnee_decide_flou_0_1_bascule_bebes():
    """Preuve que c'est la DONNÉE qui décide (pas un guess figé) : un flou tranché « 0-1 + 1-3 »
    par l'admin bascule cette activité aussi côté Bébés -> Bébés passe de 18 à 19."""
    mapping = {lbl: ["1-3"] for lbl in FLOUS}
    mapping[FLOUS[0]] = ["0-1", "1-3"]               # l'admin tranche CE flou dans les deux bandes
    chunks = _decouper(mapping)
    assert len(creche.filtrer_chunks(chunks, "bebes_0_1_an")) == 19
    assert len(creche.filtrer_chunks(chunks, "moyens_1_2_ans")) == 27


def test_filtre_collection_inconnue_leve():
    with pytest.raises(RuntimeError, match="inconnue"):
        creche.filtrer_chunks([], "collection-bidon")


def test_backstop_bande_inconnue_refuse():
    """Backstop anti-trou-muet : un arbitrage avec une bande INCONNUE (« 9-9 ») rangerait l'unité
    dans aucune collection -> filtrer_chunks REFUSE (jamais un trou)."""
    chunks = _decouper({lbl: ["9-9"] for lbl in FLOUS})   # bande hors {0-1, 1-3}
    with pytest.raises(RuntimeError, match="inconnue"):
        creche.filtrer_chunks(chunks, "moyens_1_2_ans")


# ── Aperçu admin : signale le flou + son état d'arbitrage ────────────────────

def test_apercu_flou_non_tranche_signale():
    """Sans arbitrage : les 3 flous sont signalés flou=True, arbitre=False, bandes vides ;
    les unités nettes restent arbitre=True avec leurs bandes."""
    ap = creche.apercu_unites(_decouper({}), "moyens_1_2_ans")
    assert ap["total"] == 27
    flous = [u for u in ap["unites"] if u["flou"]]
    assert len(flous) == 3
    assert all(u["arbitre"] is False and u["bandes"] == [] for u in flous)   # à trancher
    nets = [u for u in ap["unites"] if not u["flou"]]
    assert all(u["arbitre"] is True and u["bandes"] for u in nets)


def test_apercu_flou_tranche_arbitre_true():
    """Avec arbitrage 1-3 : les flous passent arbitre=True, bandes non vides, et Moyens
    récupère tout le niveau (27)."""
    ap = creche.apercu_unites(_decouper({lbl: ["1-3"] for lbl in FLOUS}), "moyens_1_2_ans")
    assert ap["total_niveau"] == 27
    assert all(u["arbitre"] is True for u in ap["unites"])
    assert all(u["bandes"] for u in ap["unites"])


def test_apercu_expose_les_options_darbitrage():
    """BRIQUE 1c : l'aperçu porte les options que l'admin peut choisir pour trancher un flou —
    elles viennent de la FICHE (BANDES_VALIDES), jamais écrites en dur dans l'écran. Même source
    que le validateur du POST -> le front ne peut proposer que des options que le POST accepte."""
    ap = creche.apercu_unites(_decouper({}), "moyens_1_2_ans")
    assert ap["options_arbitrage"] == sorted(creche.BANDES_VALIDES) == ["0-1", "1-3"]


def test_apercu_doute_ia_rend_une_unite_nette_floue():
    """Branchement de l'IA (pas 2) : même une unité NETTE (bandes présentes) devient flou=True si le
    verdict de l'IA (`doutes[i]`) la juge douteuse — c'est bien l'IA qui décide, plus le code en dur.
    Sans `doutes`, la même unité reste nette (repli sûr = bandes vides seules)."""
    chunks = _decouper({})                              # 27 unités : 3 flous (bandes vides), le reste net
    idx = next(i for i, c in enumerate(chunks) if c["meta"].get("age"))   # 1re unité NETTE (a des bandes)
    doutes = [False] * len(chunks)
    doutes[idx] = True                                  # l'IA doute de cette unité pourtant nette

    ap = creche.apercu_unites(chunks, "moyens_1_2_ans", doutes=doutes)
    assert ap["unites"][idx]["bandes"]                  # elle a bien des bandes (nette au parsing)
    assert ap["unites"][idx]["flou"] is True            # ... mais l'IA la rend floue
    assert ap["unites"][idx]["arbitre"] is False        # donc à trancher par l'admin

    ap0 = creche.apercu_unites(chunks, "moyens_1_2_ans")   # sans verdict IA
    assert ap0["unites"][idx]["flou"] is False          # la même unité redevient nette


# ── Cohérence aperçu ↔ ingestion : le doute de l'IA vaut des deux côtés (pas 2, bout 2b) ──

def test_age_bands_arbitrage_prime_sur_le_parsing():
    """L'arbitrage de l'admin PRIME sur le parsing en dur : un libellé qui matcherait « 1-3 » suit
    quand même la décision arbitrée (0-1). Sans arbitrage, il retomberait sur le parsing net."""
    creche._ARBITRAGE = {"dès ~2 ans (dans notre bande 1-3)": ["0-1"]}
    try:
        assert creche._age_bands("dès ~2 ans (dans notre bande 1-3)") == frozenset({"0-1"})  # arbitrage
        creche._ARBITRAGE = {}
        assert creche._age_bands("dès ~2 ans (dans notre bande 1-3)") == frozenset({"1-3"})  # parsing net
    finally:
        creche._ARBITRAGE = {}


def test_ingestion_refuse_un_doute_ia_non_tranche():
    """Miroir de l'aperçu : une unité jugée douteuse par l'IA et NON tranchée fait REFUSER
    filtrer_chunks — même verdict que l'aperçu (arbitre=False). Même une unité NETTE au parsing."""
    chunks = _decouper({})                                      # aucun arbitrage
    idx = next(i for i, c in enumerate(chunks) if c["meta"].get("age"))   # unité NETTE (a des bandes)
    doutes = [False] * len(chunks)
    doutes[idx] = True                                          # l'IA doute de cette unité
    with pytest.raises(RuntimeError, match="douteux"):
        creche.filtrer_chunks(chunks, "moyens_1_2_ans", doutes)


def test_ingestion_accepte_un_doute_ia_une_fois_tranche():
    """Le même doute, une fois TRANCHÉ par l'admin, ne fait plus refuser l'ingestion."""
    base = _decouper({})
    idx = next(i for i, c in enumerate(base) if c["meta"].get("age"))
    m = creche._MOTIF.match(base[idx]["text"].split("\n")[0])
    label = (m.group(1) if m.groups() else m.group(0)).strip()   # libellé d'âge de cette unité
    arb = {lbl: ["1-3"] for lbl in FLOUS}    # tranche les 3 vrais flous (sinon bandes vides = refus)
    arb[label] = ["1-3"]                     # + le libellé de l'unité que l'IA juge douteuse
    chunks = _decouper(arb)
    doutes = [False] * len(chunks)
    doutes[idx] = True
    kept = creche.filtrer_chunks(chunks, "moyens_1_2_ans", doutes)   # ne doit PAS lever
    assert len(kept) >= 1


# ── Verdict IA calculé UNE fois (libellés) puis reconstitué (bout 2b : persistance) ──

def test_libelles_douteux_renvoie_les_libelles_juges_douteux(monkeypatch):
    """libelles_douteux : l'IA (moquée) juge une unité douteuse -> son LIBELLÉ d'âge remonte
    (c'est cette liste de libellés, clé stable, qu'on persiste puis relit des deux côtés)."""
    import backend.rag.analyse_amont as aamod
    chunks = _decouper({})
    idx = next(i for i, c in enumerate(chunks) if c["meta"].get("age"))   # une unité nette

    def fake(unites, *, db):
        return {"regle": "x", "unites": [
            {"index": i, "classe": [], "doute": (i == idx)} for i in range(len(unites))
        ]}
    monkeypatch.setattr(aamod, "analyser_unites", fake)

    labels = creche.libelles_douteux(chunks, db=None)
    assert labels == [creche._label_age(chunks[idx])]


def test_doutes_depuis_labels_reconstitue_le_verdict_sans_ia():
    """doutes_depuis_labels : PUR (aucune IA). Une unité est douteuse ssi son libellé figure dans la
    liste persistée — même verdict que celui qui a servi à écrire la liste."""
    chunks = _decouper({})
    idx = next(i for i, c in enumerate(chunks) if c["meta"].get("age"))
    label = creche._label_age(chunks[idx])
    doutes = creche.doutes_depuis_labels(chunks, [label])
    assert doutes[idx] is True
    for i, c in enumerate(chunks):                       # clé = libellé : toutes les unités du même libellé
        assert doutes[i] == (creche._label_age(c) == label)


# ── Cohérence cartouche « Résultat du filtre » ↔ vrai filtre (étape 8, garde-fou modale) ──
#    La cartouche affiche filtre.ok ; la modale s'appuie sur le compte « âge à confirmer » de l'aperçu.
#    On PROUVE que les deux s'accordent : des cas « à confirmer » ⟺ filtrer_chunks REFUSE (jamais l'un
#    sans l'autre — sinon la cartouche mentirait sur l'état réel).

def test_apercu_signale_ssi_filtre_refuse_sans_arbitrage():
    """Aucun flou tranché : l'aperçu signale des cas « âge à confirmer » ET le filtre REFUSE
    (cartouche ROUGE + modale) — les deux d'accord."""
    chunks = _decouper({})                                    # aucun arbitrage
    ap = creche.apercu_unites(chunks, "bebes_0_1_an", doutes=None)
    a_confirmer = [u for u in ap["unites"] if u["flou"] and not u["arbitre"]]
    assert len(a_confirmer) > 0                               # l'aperçu signale
    with pytest.raises(RuntimeError):                         # et le filtre refuse
        creche.filtrer_chunks(chunks, "bebes_0_1_an", doutes=None)


def test_apercu_muet_ssi_filtre_passe_avec_arbitrage():
    """Les 3 flous tranchés : l'aperçu ne signale plus rien ET le filtre PASSE
    (cartouche VERTE, pas de modale) — les deux d'accord."""
    arb = {f: ["0-1"] for f in FLOUS}                         # les 3 vrais flous tranchés
    chunks = _decouper(arb)
    ap = creche.apercu_unites(chunks, "bebes_0_1_an", doutes=None)
    a_confirmer = [u for u in ap["unites"] if u["flou"] and not u["arbitre"]]
    assert len(a_confirmer) == 0                              # plus rien à confirmer
    kept = creche.filtrer_chunks(chunks, "bebes_0_1_an", doutes=None)   # filtre passe
    assert len(kept) >= 1
