r"""Preuve de raccordement — Phase 5 : régulation de concurrence des appels LLM.

Ce que le test PROUVE (le plafond agit RÉELLEMENT, pas « le code existe ») :
  1. Sous charge, le pic de simultanéité mesuré ne dépasse JAMAIS la limite — et l'atteint
     (le sémaphore plafonne ET laisse passer le maximum autorisé, il ne bloque pas tout).
  2. Aucun appel n'est perdu : les N appels finissent tous (les surnuméraires attendent un créneau).
  3. Créneau indisponible dans le délai -> erreur honnête (RuntimeError), requête jamais pendante,
     aucun appel réseau tenté.

Lancer : .\.venv\Scripts\python.exe -m pytest test_llm_concurrence.py -q
"""
import os
import sys
import threading
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from unittest.mock import MagicMock, patch

import pytest

import backend.llm.generator as gen


def _fake_groq_lent(concurrence, lock):
    """Faux Groq qui dort : mesure la simultanéité réelle pendant l'appel."""
    def _post(*args, **kwargs):
        with lock:
            concurrence["now"] += 1
            concurrence["max"] = max(concurrence["max"], concurrence["now"])
        time.sleep(0.15)
        with lock:
            concurrence["now"] -= 1
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        return resp
    return _post


def test_le_plafond_agit_sous_charge():
    gen._llm_semaphore = threading.BoundedSemaphore(2)  # limite forcée à 2
    concurrence = {"now": 0, "max": 0}
    lock = threading.Lock()
    resultats = []

    def _appel():
        resultats.append(gen.generate("p", provider="groq"))

    with patch.object(gen, "AI_PROVIDER", "groq"), \
         patch.object(gen, "GROQ_API_KEY", "cle-de-test-fictive"), \
         patch("requests.post", side_effect=_fake_groq_lent(concurrence, lock)):
        threads = [threading.Thread(target=_appel) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    assert concurrence["max"] <= 2          # jamais plus de 2 en vol -> le plafond agit
    assert concurrence["max"] == 2          # et il est bien atteint (ne bloque pas tout)
    assert len(resultats) == 8              # aucun appel perdu : tous finissent


def test_creneau_indisponible_erreur_honnete():
    gen._llm_semaphore = threading.BoundedSemaphore(1)
    gen.AI_SLOT_TIMEOUT = 0.1               # délai d'attente court pour le test
    gen._llm_semaphore.acquire()            # on occupe le seul créneau
    try:
        with patch.object(gen, "AI_PROVIDER", "groq"), \
             patch("requests.post") as post:
            with pytest.raises(RuntimeError, match="simultan"):
                gen.generate("p", provider="groq")
            post.assert_not_called()        # aucun appel réseau tenté faute de créneau
    finally:
        gen._llm_semaphore.release()
