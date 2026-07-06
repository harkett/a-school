r"""Preuve de raccordement — Sonde CPU : alerte sur charge SOUTENUE (5 min), pas un flash d'1 s.

Ce que le test PROUVE (decision reelle de check_cpu_alert, create_alert capturee) :
  1. Charge soutenue elevee (3.8 sur 4 coeurs = 95%) -> l'alerte CRITIQUE part.
  2. Charge basse (cas reel du 23/06 : ~0.02 sur 4 coeurs) -> AUCUNE alerte
     (l'ancienne sonde « flash 1 s » alertait a tort ; la nouvelle ne doit pas).
  3. Le pourcentage est bien la charge 5 min normalisee par le nombre de coeurs.

Lancer : .\.venv\Scripts\python.exe -m pytest test_cpu_alert_soutenue.py -q
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import backend.alerts as alerts


def _capture(monkeypatch):
    """Remplace create_alert pour capturer les appels sans toucher la BDD/SMTP."""
    calls = []
    monkeypatch.setattr(
        alerts, "create_alert",
        lambda level, title, message: calls.append((level, title, message)),
    )
    return calls


def test_charge_soutenue_elevee_declenche_alerte(monkeypatch):
    calls = _capture(monkeypatch)
    monkeypatch.setattr(alerts.psutil, "cpu_count", lambda: 4)
    monkeypatch.setattr(alerts.psutil, "getloadavg", lambda: (3.9, 3.8, 3.7))  # 3.8/4 = 95%
    alerts.check_cpu_alert()
    assert len(calls) == 1
    level, title, _ = calls[0]
    assert level == "critical"
    assert "95.0%" in title


def test_charge_basse_ne_declenche_pas__cas_23_06(monkeypatch):
    # Cas reel du 23/06 : machine au repos. L'ancienne sonde (flash 1 s) alertait
    # a tort sur un pic isole ; la nouvelle, mesurant 5 min, ne doit rien declencher.
    calls = _capture(monkeypatch)
    monkeypatch.setattr(alerts.psutil, "cpu_count", lambda: 4)
    monkeypatch.setattr(alerts.psutil, "getloadavg", lambda: (0.06, 0.02, 0.0))
    alerts.check_cpu_alert()
    assert calls == []


def test_pourcentage_normalise_par_coeurs(monkeypatch):
    # 5min = 2.0 sur 4 coeurs = 50% -> sous le seuil, aucune alerte.
    calls = _capture(monkeypatch)
    monkeypatch.setattr(alerts.psutil, "cpu_count", lambda: 4)
    monkeypatch.setattr(alerts.psutil, "getloadavg", lambda: (2.0, 2.0, 2.0))
    alerts.check_cpu_alert()
    assert calls == []
