"""Preuve de raccordement — Une alerte admin laisse une trace dans le JOURNAL, pas seulement
en base et dans la boîte mail.

Ce que le test PROUVE (vrai `create_alert`, base et SMTP neutralisés, journal capturé) :
  1. Une alerte écrite en base émet AUSSI une ligne de log — sinon elle est invisible pour tout
     outil de supervision qui lit `journalctl` / `docker logs`.
  2. La sévérité de l'alerte devient la sévérité de la ligne : critical -> CRITICAL,
     warning -> WARNING, info -> INFO, niveau inconnu -> WARNING (jamais perdu).
  3. La ligne se suffit à elle-même : titre, message et horodatage UTC, de quoi lire l'événement
     sans ouvrir la base.
  4. La base et le mail restent servis — la journalisation s'ajoute, elle ne remplace rien.
  5. Un doublon anti-flood ne journalise pas (sinon le journal reflood à chaque cycle).

Lancer : docker compose exec backend python -m pytest tests/test_alerte_journalisee.py -q
"""
import logging

import backend.supervision.alerts as alerts


class _SessionFactice:
    """Session BDD de façade : retient ce qui est ajouté/commité, ne touche à rien."""
    def __init__(self, journal):
        self.journal = journal

    def add(self, objet):
        self.journal["ajoutes"].append(objet)

    def commit(self):
        self.journal["commits"] += 1

    def rollback(self):
        self.journal["rollbacks"] += 1

    def close(self):
        pass


def _brancher(monkeypatch, *, deja_alerte=False):
    """Isole create_alert : pas de BDD, pas de SMTP. Rend le journal des effets observés."""
    effets = {"ajoutes": [], "commits": 0, "rollbacks": 0, "mails": []}
    monkeypatch.setattr(alerts, "session_pour", lambda _schema: _SessionFactice(effets))
    monkeypatch.setattr(alerts, "_already_alerted", lambda db, title: deja_alerte)
    monkeypatch.setattr(
        alerts, "_send_alert_email",
        lambda level, title, message, sujet_detail="": effets["mails"].append((level, title, message)),
    )
    return effets


def test_une_alerte_critique_ecrit_une_ligne_critical(caplog):
    """Le cas qui motive tout : « CPU critique : 93% » doit se voir dans le journal."""
    with caplog.at_level(logging.DEBUG, logger=alerts.log.name):
        alerts._journaliser("critical", "CPU critique : 93%", "Le processeur dépasse 85 %.")

    lignes = [e for e in caplog.records if "CPU critique" in e.getMessage()]
    assert len(lignes) == 1, "l'alerte n'a laissé aucune trace dans le journal"
    assert lignes[0].levelno == logging.CRITICAL


def test_la_severite_de_l_alerte_devient_celle_de_la_ligne(caplog):
    attendu = {
        "critical": logging.CRITICAL,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "farfelu": logging.WARNING,   # niveau inconnu : classé, jamais perdu
    }
    for niveau, attendu_logging in attendu.items():
        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger=alerts.log.name):
            alerts._journaliser(niveau, f"Titre {niveau}", "Message.")
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == attendu_logging, f"niveau « {niveau} » mal classé"


def test_la_ligne_se_lit_sans_ouvrir_la_base(caplog):
    """Type d'alerte, valeur/seuil, message et horodatage : tout est dans la ligne."""
    with caplog.at_level(logging.DEBUG, logger=alerts.log.name):
        alerts._journaliser("warning", "Disque faible : 91% utilisé", "Il reste 4.2 Go libres.")

    texte = caplog.records[0].getMessage()
    assert caplog.records[0].levelname == "WARNING"  # la sévérité porte la ligne, pas le texte
    assert "Disque faible : 91% utilisé" in texte  # le type d'alerte et sa valeur
    assert "Il reste 4.2 Go libres." in texte     # le message
    assert "UTC" in texte                         # l'horodatage, recoupable avec le mail
    horodatage = alerts.maintenant_utc().strftime("%d/%m/%Y")
    assert horodatage in texte


def test_create_alert_journalise_SANS_rien_retirer(monkeypatch, caplog):
    """Contrainte de la tâche : la journalisation s'AJOUTE — base et mail restent servis."""
    effets = _brancher(monkeypatch)
    with caplog.at_level(logging.DEBUG, logger=alerts.log.name):
        alerts.create_alert("critical", "Tentatives d'intrusion : 42 en 1h", "Vérifier les IPs.")

    assert len(effets["ajoutes"]) == 1 and effets["commits"] == 1, "l'écriture en base a sauté"
    assert len(effets["mails"]) == 1, "l'envoi du mail a sauté"
    assert effets["rollbacks"] == 0
    lignes = [e for e in caplog.records if "Tentatives d'intrusion" in e.getMessage()]
    assert len(lignes) == 1 and lignes[0].levelno == logging.CRITICAL


def test_un_doublon_anti_flood_ne_journalise_pas(monkeypatch, caplog):
    """Même titre dans la fenêtre anti-flood : rien en base, rien par mail, rien au journal."""
    effets = _brancher(monkeypatch, deja_alerte=True)
    with caplog.at_level(logging.DEBUG, logger=alerts.log.name):
        alerts.create_alert("critical", "CPU critique : 93%", "Le processeur dépasse 85 %.")

    assert effets["ajoutes"] == [] and effets["mails"] == []
    assert caplog.records == [], "le doublon a refloodé le journal"


def test_le_journal_ne_peut_pas_casser_l_alerte(monkeypatch):
    """Un journal en panne ne doit faire perdre ni la base ni le mail."""
    effets = _brancher(monkeypatch)

    def log_en_panne(*a, **k):
        raise RuntimeError("handler de log cassé")

    monkeypatch.setattr(alerts.log, "log", log_en_panne)
    alerts.create_alert("warning", "Disque faible : 91% utilisé", "Il reste 4.2 Go libres.")

    assert effets["commits"] == 1 and len(effets["mails"]) == 1
    assert effets["rollbacks"] == 0
