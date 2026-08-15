"""Preuve de raccordement — Les alertes admin ne floodent plus la boîte, et une pile de
développement n'y écrit plus du tout.

Cas réel du 07/08/2026 : douze mails « CPU critique » en quelques heures, émis par la pile Docker
LOCALE, avec le sujet d'une alerte de production. Deux défauts distincts, tous deux couverts ici :

  1. Le TITRE embarquait la valeur mesurée (« CPU critique : 94.4% », puis 100.0%, puis 101.1%).
     Comme le dédoublonnage anti-flood compare les titres, chaque relevé portait un titre neuf et
     la fenêtre de 2 h n'attrapait jamais rien : une alerte partait à chaque cycle de
     l'ordonnanceur, soit toutes les 5 minutes. Le défaut valait pour les TROIS contrôles.
  2. Le MAIL partait quel que soit l'environnement. Le corps disait « machine de développement »,
     mais le sujet — seul élément visible dans la liste des mails — était indiscernable d'une
     alerte du VPS.

La règle sur le mail est FAIL-SAFE : une variable ENV absente ou vide laisse passer le mail, pour
qu'un serveur dont le réglage a été oublié reste bavard plutôt que muet.

Lancer : docker compose exec backend python -m pytest tests/test_alertes_flood_et_mail_dev.py -q
"""
import collections

import backend.supervision.alerts as alerts

# Compteurs cumulés à la manière de /proc/stat : la sonde CPU compare deux relevés successifs.
_Temps = collections.namedtuple(
    "_Temps", "user nice system idle iowait irq softirq steal guest guest_nice"
)


def _temps(occupe, idle):
    return _Temps(occupe, 0.0, 0.0, idle, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def _sonde_cpu(monkeypatch, *releves):
    suite = iter(releves)
    monkeypatch.setattr(alerts, "_dernier_cpu", None)
    monkeypatch.setattr(alerts.psutil, "cpu_times", lambda: next(suite))


def _titres(monkeypatch):
    """Capture les titres passés à create_alert, sans toucher BDD ni SMTP."""
    titres = []
    monkeypatch.setattr(
        alerts, "create_alert",
        lambda level, title, message, sujet_detail="", **k: titres.append(title),
    )
    return titres


# --------------------------------------------------------------------------------------------
# 1. Le titre ne bouge plus quand la valeur bouge — l'anti-flood redevient opérant
# --------------------------------------------------------------------------------------------

def test_cpu_deux_valeurs_differentes_donnent_le_meme_titre(monkeypatch):
    """94.4 % puis 100.0 % : deux relevés distincts, UN SEUL titre — donc un seul mail."""
    titres = _titres(monkeypatch)
    _sonde_cpu(monkeypatch,
               _temps(1000.0, 4000.0),    # amorce
               _temps(1944.0, 4056.0),    # 944 s occupées sur 1000 s = 94.4 %
               _temps(2944.0, 4056.0))    # 1000 s occupées sur 1000 s = 100.0 %
    alerts.check_cpu_alert()
    alerts.check_cpu_alert()
    alerts.check_cpu_alert()

    assert titres == ["CPU critique", "CPU critique"], "le titre suit encore la valeur mesurée"


def test_disque_deux_valeurs_differentes_donnent_le_meme_titre(monkeypatch):
    titres = _titres(monkeypatch)

    class _Usage:
        def __init__(self, percent):
            self.percent, self.total, self.used = percent, 500 * 1024**3, 460 * 1024**3

    monkeypatch.setattr(alerts.psutil, "disk_usage", lambda _: _Usage(91.3))
    alerts.check_disk_alert()
    monkeypatch.setattr(alerts.psutil, "disk_usage", lambda _: _Usage(92.7))
    alerts.check_disk_alert()

    assert titres == ["Disque faible", "Disque faible"]


def test_la_valeur_reste_lisible_dans_le_message(monkeypatch):
    """Sortir la valeur du titre ne doit pas la faire disparaître : le message la porte."""
    messages = []
    monkeypatch.setattr(
        alerts, "create_alert",
        lambda level, title, message, sujet_detail="", **k: messages.append(message),
    )
    _sonde_cpu(monkeypatch, _temps(1000.0, 4000.0), _temps(1570.0, 4030.0))   # 95.0 %
    alerts.check_cpu_alert()
    alerts.check_cpu_alert()

    assert "95.0" in messages[0], "la valeur mesurée n'est plus lisible nulle part"


# --------------------------------------------------------------------------------------------
# 2. Le mail ne part qu'en production — mais une ENV absente reste bavarde (fail-safe)
# --------------------------------------------------------------------------------------------

def _mails(monkeypatch):
    """Capture les envois SMTP réels tentés par _send_alert_email."""
    envois = []
    from backend.securite import comptes
    monkeypatch.setattr(comptes, "_smtp_send", lambda msg: envois.append(msg))
    monkeypatch.setenv("ADMIN_EMAIL", "admin@aschool.fr")
    return envois


def test_pile_de_developpement_n_envoie_aucun_mail(monkeypatch):
    """Le cas qui motive tout : ENV=development, la boîte de l'admin reste tranquille."""
    envois = _mails(monkeypatch)
    monkeypatch.setenv("ENV", "development")
    alerts._send_alert_email("critical", "CPU critique", "Charge à 94.4 %.")
    assert envois == [], "la pile de développement écrit encore dans la boîte de l'admin"


def test_production_envoie_toujours(monkeypatch):
    envois = _mails(monkeypatch)
    monkeypatch.setenv("ENV", "production")
    alerts._send_alert_email("critical", "CPU critique", "Charge à 94.4 %.")
    assert len(envois) == 1, "la production ne prévient plus personne"


def test_env_absente_ou_vide_laisse_passer_le_mail(monkeypatch):
    """FAIL-SAFE : un VPS dont le réglage a été oublié doit rester bavard, jamais muet."""
    for valeur in (None, "", "   "):
        envois = _mails(monkeypatch)
        if valeur is None:
            monkeypatch.delenv("ENV", raising=False)
        else:
            monkeypatch.setenv("ENV", valeur)
        alerts._send_alert_email("critical", "CPU critique", "Charge à 94.4 %.")
        assert len(envois) == 1, f"ENV={valeur!r} a rendu la surveillance muette"


# --------------------------------------------------------------------------------------------
# 3. Le SUJET dit d'où vient la mesure — et garde la valeur, que le titre n'a plus
# --------------------------------------------------------------------------------------------

def _sujet(monkeypatch, env, sujet_detail="94.4 %"):
    """Rend le sujet du mail réellement construit pour l'environnement donné."""
    captures = []
    from backend.securite import comptes
    monkeypatch.setattr(comptes, "_smtp_send", lambda msg: captures.append(msg["Subject"]))
    monkeypatch.setenv("ADMIN_EMAIL", "admin@aschool.fr")
    if env is None:
        monkeypatch.delenv("ENV", raising=False)
    else:
        monkeypatch.setenv("ENV", env)
    alerts._send_alert_email("critical", "CPU critique", "Charge à 94.4 %.", sujet_detail)
    return captures[0] if captures else None


def test_le_sujet_de_production_est_marque_PROD(monkeypatch):
    assert "aSchool PROD" in _sujet(monkeypatch, "production")


def test_un_environnement_non_renseigne_ne_se_fait_pas_passer_pour_la_production(monkeypatch):
    """Le mail fail-safe part quand même, mais son sujet ne ment pas sur son origine."""
    sujet = _sujet(monkeypatch, None)
    assert "ORIGINE INCONNUE" in sujet
    assert "PROD" not in sujet


def test_la_valeur_mesuree_reste_dans_le_sujet(monkeypatch):
    """Le titre en base est stable (anti-flood) ; la valeur revient par le sujet, pour rester
    lisible dans la liste des mails sans ouvrir l'alerte."""
    sujet = _sujet(monkeypatch, "production", sujet_detail="104.8 %")
    assert "CPU critique : 104.8 %" in sujet
