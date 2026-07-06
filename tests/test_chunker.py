"""Preuve unitaire — overlap du découpeur générique (Phase 3, point 2).

Entrées SYNTHÉTIQUES (pas de PDF, pas de ChromaDB) : on prouve le mécanisme, pas
« le code existe ». Ce que les tests garantissent :
  1. overlap_chars=0 ⇒ AUCUN recouvrement (coupe nette) — rétro-compatibilité.
  2. overlap_chars>0 ⇒ deux chunks issus d'une coupe de TAILLE partagent un segment
     (queue de l'un = tête de l'autre).
  3. Une FRONTIÈRE ne reprend jamais de recouvrement (vraie rupture).
  4. Pas de recouvrement INTER-PAGES.
  5. Cas limite : une ligne unique plus longue que overlap_chars ⇒ aucun recouvrement.
  6. Le marqueur (donc le tag option) ne change pas sur une coupe de taille.

Lancer : .venv/Scripts/python.exe -m pytest test_chunker.py -q
"""
from backend.rag.chunker import build_chunks

# fiche-jouet : frontière = ligne « ## », marqueur = la ligne elle-même.
def _is_boundary(line):
    return line if line.startswith("##") else None

def _meta(marker, page):
    return {"marker": marker, "page": page}

# 20 lignes de 50 chars → ~1020 chars sur une page : force au moins une coupe de taille.
_LINES = [f"ligne-{i:02d}-" + "x" * 40 for i in range(20)]
_PAGE_TEXT = "\n".join(_LINES)


def _chunks(overlap, pages=None, max_chars=300, min_chars=10):
    return build_chunks(
        pages if pages is not None else [(1, _PAGE_TEXT)],
        max_chars=max_chars,
        min_chars=min_chars,
        overlap_chars=overlap,
        is_boundary=_is_boundary,
        chunk_metadata=_meta,
    )


def _shared_tail_head(a: str, b: str) -> bool:
    """Vrai si une fin de `a` (≥ 1 ligne) est exactement un début de `b`."""
    a_lines = a.split("\n")
    b_lines = b.split("\n")
    for k in range(len(a_lines), 0, -1):
        if a_lines[-k:] == b_lines[:k]:
            return True
    return False


def test_overlap_zero_coupe_nette():
    chunks = _chunks(overlap=0)
    assert len(chunks) >= 2  # 1020 chars / 300 → plusieurs chunks
    # Aucun couple voisin ne partage de segment : coupe nette.
    assert all(
        not _shared_tail_head(chunks[i]["text"], chunks[i + 1]["text"])
        for i in range(len(chunks) - 1)
    )


def test_overlap_positif_partage_un_segment():
    chunks = _chunks(overlap=120)
    assert len(chunks) >= 2
    # Au moins un couple voisin partage un segment (queue de l'un = tête de l'autre).
    assert any(
        _shared_tail_head(chunks[i]["text"], chunks[i + 1]["text"])
        for i in range(len(chunks) - 1)
    )
    # Et le recouvrement repris ne dépasse jamais le budget demandé.
    for i in range(len(chunks) - 1):
        a_lines, b_lines = chunks[i]["text"].split("\n"), chunks[i + 1]["text"].split("\n")
        for k in range(len(a_lines), 0, -1):
            if a_lines[-k:] == b_lines[:k]:
                assert len("\n".join(b_lines[:k])) <= 120
                break


def test_frontiere_ne_reprend_pas_doverlap():
    # Bloc A long (force coupe taille) puis frontière puis bloc B.
    a = "\n".join(f"A{i:02d}-" + "x" * 40 for i in range(20))
    b = "\n".join(f"B{i:02d}-" + "y" * 40 for i in range(8))
    text = a + "\n## SECTION 2\n" + b
    chunks = _chunks(overlap=120, pages=[(1, text)])
    # Le 1er chunk après la frontière commence par la frontière, jamais par du contenu A.
    after = [c for c in chunks if c["meta"]["marker"] == "## SECTION 2"]
    assert after, "la frontière n'a pas produit de chunk"
    assert after[0]["text"].lstrip().startswith("## SECTION 2")
    assert "A19" not in after[0]["text"].split("\n")[0]  # pas de fuite de la fin du bloc A


def test_pas_doverlap_inter_pages():
    p1 = "\n".join(f"P1-{i:02d}-" + "x" * 40 for i in range(20))
    p2 = "\n".join(f"P2-{i:02d}-" + "y" * 40 for i in range(20))
    chunks = _chunks(overlap=120, pages=[(1, p1), (2, p2)])
    # Le 1er chunk de la page 2 ne reprend rien de la page 1.
    page2 = [c for c in chunks if c["page"] == 2]
    assert page2
    assert "P1-" not in page2[0]["text"]


def test_ligne_unique_plus_longue_que_overlap_pas_de_reprise():
    # Lignes DISTINCTES, chacune plus longue que overlap (et que max_chars) :
    # aucun suffixe ne tient dans overlap → coupe nette, et les chunks diffèrent.
    text = "\n".join(f"L{i}-" + "z" * 250 for i in range(4))  # force des coupes de taille
    chunks = _chunks(overlap=60, pages=[(1, text)], max_chars=200, min_chars=10)
    assert len(chunks) >= 2
    # Aucune ligne ne fait < 60 chars → _tail_lines renvoie [] → coupe nette partout.
    assert all(
        not _shared_tail_head(chunks[i]["text"], chunks[i + 1]["text"])
        for i in range(len(chunks) - 1)
    )


def test_marqueur_constant_sur_coupe_de_taille():
    # Tout le contenu est sous un même marqueur ; une coupe de taille ne doit pas le changer.
    text = "## SECTION 1\n" + "\n".join(f"l{i:02d}-" + "x" * 40 for i in range(20))
    chunks = _chunks(overlap=120, pages=[(1, text)])
    markers = {c["meta"]["marker"] for c in chunks}
    assert markers == {"## SECTION 1"}  # jamais de bascule de marqueur sur une coupe de taille


# --- Déduplication (point 3) ---------------------------------------------------

# clé (text, option) comme la fiche CIEL, et helper de construction paramétrable.
def _build(pages, *, overlap=0, dedup=None, chunk_metadata=None, max_chars=900, min_chars=10):
    return build_chunks(
        pages,
        max_chars=max_chars,
        min_chars=min_chars,
        overlap_chars=overlap,
        is_boundary=_is_boundary,
        chunk_metadata=chunk_metadata or _meta,
        dedup_key=dedup,
    )

_KEY_TEXT = lambda text, meta: text                       # clé texte seul
_KEY_TEXT_OPT = lambda text, meta: (text, meta["option"])  # clé CIEL : (text, option)

_BODY = "Contenu identique repete tel quel sur deux pages distinctes du referentiel."


def test_dedup_off_retrocompatible():
    # Même corpus, dédup absente (None) → AUCUNE suppression : les 2 chunks restent.
    chunks = _build([(1, _BODY), (2, _BODY)], dedup=None)
    assert len(chunks) == 2
    assert all(c["text"] == _BODY for c in chunks)


def test_dedup_supprime_doublon_chunk_entier():
    # Même texte sur p.1 et p.2 → un seul chunk après dédup (clé texte seul).
    chunks = _build([(1, _BODY), (2, _BODY)], dedup=_KEY_TEXT)
    assert len(chunks) == 1


def test_dedup_garde_premiere_occurrence():
    # On garde la page la plus basse (1), pas la 2.
    chunks = _build([(1, _BODY), (2, _BODY)], dedup=_KEY_TEXT)
    assert len(chunks) == 1
    assert chunks[0]["page"] == 1


def test_dedup_ne_fusionne_pas_A_et_B():
    # Texte IDENTIQUE mais option différente (A en p.1, B en p.2) → clé (text, option)
    # diffère → les DEUX sont conservés (protège la partition A/B).
    chunks = build_chunks(
        [(1, _BODY), (2, _BODY)],
        max_chars=900, min_chars=10, overlap_chars=0,
        is_boundary=_is_boundary,
        chunk_metadata=lambda marker, page: {"page": page, "option": "A" if page == 1 else "B"},
        dedup_key=_KEY_TEXT_OPT,
    )
    assert len(chunks) == 2
    assert {c["meta"]["option"] for c in chunks} == {"A", "B"}


def test_dedup_ne_mange_pas_loverlap():
    # Lignes distinctes + overlap : les chunks partagent un segment mais diffèrent en
    # ENTIER → la dédup (clé texte) n'en supprime aucun. Le recouvrement survit.
    pages = [(1, _PAGE_TEXT)]
    sans = _build(pages, overlap=120, dedup=None, max_chars=300)
    avec = _build(pages, overlap=120, dedup=_KEY_TEXT, max_chars=300)
    assert len(avec) == len(sans)  # aucune suppression
    # et un segment partagé existe toujours entre voisins
    assert any(
        _shared_tail_head(avec[i]["text"], avec[i + 1]["text"])
        for i in range(len(avec) - 1)
    )
