r"""Preuve de raccordement — Sonde CPU : la mesure est une VRAIE part de temps processeur,
soutenue sur l'intervalle de surveillance, et non un load average déguisé en pourcentage.

Deux sondes ont échoué avant celle-ci, chacune laissant son cas réel :

  1. `cpu_percent(interval=1)` ne lisait qu'une seconde — 23/06 : « 100 % » annoncé sur une
     machine au repos (~0,3 % réel).
  2. `getloadavg()[1] / cœurs` — 07/08 : douze mails « CPU critique » à 91-104 %, alors que le
     conteneur consommait 17,4 % de CPU. Le load compte aussi les tâches en attente de DISQUE et
     peut dépasser le nombre de cœurs : ce n'est pas un pourcentage.

Ce que le test PROUVE (décision réelle de check_cpu_alert, create_alert capturée) :
  - le pourcentage vient du delta des compteurs `/proc/stat` entre deux contrôles ;
  - une charge réellement élevée alerte, une machine au repos non ;
  - un load average élevé n'alerte PLUS tant que le processeur, lui, ne travaille pas ;
  - le premier passage n'invente rien (rien à comparer, donc pas d'alerte).

Lancer : docker compose exec backend python -m pytest tests/test_cpu_alert_soutenue.py -q
"""
import collections

import backend.supervision.alerts as alerts

# Compteurs cumulés à la manière de /proc/stat sous Linux.
_Temps = collections.namedtuple(
    "_Temps", "user nice system idle iowait irq softirq steal guest guest_nice"
)


def _temps(occupe, idle, iowait=0.0):
    return _Temps(occupe, 0.0, 0.0, idle, iowait, 0.0, 0.0, 0.0, 0.0, 0.0)


def _sonde(monkeypatch, *releves):
    """Fait lire les relevés donnés, dans l'ordre, à chaque appel de psutil.cpu_times()."""
    suite = iter(releves)
    monkeypatch.setattr(alerts, "_dernier_cpu", None)      # fenêtre remise à zéro
    monkeypatch.setattr(alerts.psutil, "cpu_times", lambda: next(suite))


def _capture(monkeypatch):
    """Remplace create_alert pour capturer les appels sans toucher la BDD/SMTP."""
    calls = []
    monkeypatch.setattr(
        alerts, "create_alert",
        lambda level, title, message, sujet_detail="", **k: calls.append((level, title, message)),
    )
    return calls


def test_charge_soutenue_elevee_declenche_alerte(monkeypatch):
    calls = _capture(monkeypatch)
    # Entre les deux contrôles : 570 s de temps occupé pour 30 s d'inactivité = 95 %.
    _sonde(monkeypatch, _temps(1000.0, 4000.0), _temps(1570.0, 4030.0))
    alerts.check_cpu_alert()      # premier passage : amorce la fenêtre
    alerts.check_cpu_alert()      # second : c'est lui qui mesure

    assert len(calls) == 1
    level, title, message = calls[0]
    assert level == "critical"
    # La valeur est dans le MESSAGE, pas dans le titre : le titre est la clé anti-flood et doit
    # rester stable d'un relevé à l'autre (voir tests/test_alertes_flood_et_mail_dev.py).
    assert "95.0" in message
    assert title == "CPU critique"


def test_charge_basse_ne_declenche_pas__cas_23_06(monkeypatch):
    # Machine au repos : 0,5 s de travail pour 599,5 s d'inactivité.
    calls = _capture(monkeypatch)
    _sonde(monkeypatch, _temps(1000.0, 4000.0), _temps(1000.5, 4599.5))
    alerts.check_cpu_alert()
    alerts.check_cpu_alert()
    assert calls == []


def test_un_load_average_eleve_n_alerte_plus__cas_07_08(monkeypatch):
    """LE cas des douze mails : load à 7,5 sur 8 cœurs (l'ancienne formule annonçait 94 %) alors
    que le processeur travaille à 29 %. La sonde ne doit plus rien déclencher."""
    calls = _capture(monkeypatch)
    monkeypatch.setattr(alerts.psutil, "cpu_count", lambda: 8)
    monkeypatch.setattr(alerts.psutil, "getloadavg", lambda: (7.2, 7.5, 7.8))
    # 29 % de CPU réel, le reste en attente (dont disque : iowait, que le load compte et pas nous).
    _sonde(monkeypatch,
           _temps(1000.0, 4000.0, iowait=100.0),
           _temps(1290.0, 4610.0, iowait=200.0))
    alerts.check_cpu_alert()
    alerts.check_cpu_alert()
    assert calls == [], "le load average décide encore de l'alerte"


def test_le_premier_passage_n_invente_pas_de_mesure(monkeypatch):
    """Rien à comparer au démarrage : un contrôle sauté vaut mieux qu'un chiffre inventé."""
    calls = _capture(monkeypatch)
    _sonde(monkeypatch, _temps(9999.0, 10.0))     # compteurs très chargés depuis le boot
    alerts.check_cpu_alert()
    assert calls == []


def test_le_pourcentage_est_bien_une_part_du_temps_ecoule(monkeypatch):
    # 300 s occupées sur 600 s écoulées = 50 % -> sous le seuil, aucune alerte.
    calls = _capture(monkeypatch)
    _sonde(monkeypatch, _temps(1000.0, 4000.0), _temps(1300.0, 4300.0))
    alerts.check_cpu_alert()
    alerts.check_cpu_alert()
    assert calls == []
