r"""Preuve de la SURVEILLANCE DES CONNEXIONS — surveiller, ne pas interdire.

LE PRINCIPE, POSÉ LE 15/08/2026. Un professeur travaille sur l'ordinateur de sa salle, sur celui
de chez lui et sur son téléphone : c'est normal. Ce qu'on cherche, c'est le compte PARTAGÉ entre
plusieurs enseignants. Aucun de ces contrôles ne ferme quoi que ce soit — ils écrivent une alerte,
l'administrateur décide.

CE QUE CES TESTS PROTÈGENT :
  1. un usage normal ne déclenche RIEN — sinon l'alerte devient du bruit et plus personne ne la
     lit, ce qui revient à ne pas surveiller du tout ;
  2. on compte des APPAREILS, pas des sessions : trois onglets sur un même poste ne font pas trois
     postes ;
  3. deux villes trop éloignées au même moment sont signalées, et une session sans coordonnées
     n'est comparée à rien — surtout pas placée d'office quelque part ;
  4. l'alerte porte DE QUI elle parle, ce qui a été mesuré et où aller voir : c'est ce qui la rend
     exploitable, et comptable ;
  5. l'anti-flood ne confond pas deux professeurs — sans quoi le signalement du premier ferait
     taire celui du second pendant deux heures ;
  6. rien n'est fermé : les sessions restent actives après l'alerte.

Lancer : docker compose exec backend python -m pytest tests/test_surveillance_connexions.py -q
"""
from datetime import timedelta

import backend.supervision.alerts as alerts
import backend.systeme.localisation_ip as loc
import backend.core.database as dbmod
from backend.core.horloge import maintenant_utc
from backend.core.models_db import AdminAlert, User, UserSession
from conftest import resemer_reglages

LILLE = (50.63, 3.06)
MARSEILLE = (43.30, 5.37)


def _table_rase():
    db = dbmod.SessionLocal()
    try:
        db.query(AdminAlert).delete()
        db.query(UserSession).delete()
        db.commit()
    finally:
        db.close()


def _prof(email: str) -> int:
    db = dbmod.SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        if u is None:
            u = User(email=email, password_hash="x", is_verified=True)
            db.add(u)
            db.commit()
        return u.id
    finally:
        db.close()


def _session(user_id, cle, *, navigateur="Chrome 120", systeme="Windows 11",
             type_app="desktop", ip="83.228.245.163", lieu=None, coords=(None, None),
             minutes=1):
    db = dbmod.SessionLocal()
    try:
        db.add(UserSession(
            user_id=user_id, session_key=cle, ip_address=ip, browser=navigateur,
            os=systeme, device_type=type_app, localisation=lieu,
            latitude=coords[0], longitude=coords[1], is_active=True,
            last_seen=maintenant_utc() - timedelta(minutes=minutes),
        ))
        db.commit()
    finally:
        db.close()


def _alertes(code=None):
    db = dbmod.SessionLocal()
    try:
        q = db.query(AdminAlert)
        return q.filter(AdminAlert.code == code).all() if code else q.all()
    finally:
        db.close()


def _sessions_vivantes():
    db = dbmod.SessionLocal()
    try:
        return db.query(UserSession).filter(UserSession.is_active == True).count()  # noqa: E712
    finally:
        db.close()


def test_un_usage_normal_ne_declenche_rien():
    """LE POINT QUI COMPTE AUTANT QUE LA DÉTECTION. Salle de classe, domicile, téléphone : trois
    appareils légitimes. Une alerte ici ferait du bruit à chaque journée de travail, et une alerte
    qu'on n'ouvre plus ne surveille plus rien."""
    resemer_reglages()
    _table_rase()
    uid = _prof("normal@test.fr")
    _session(uid, "n-salle", navigateur="Chrome 120", systeme="Windows 11", ip="1.1.1.1")
    _session(uid, "n-maison", navigateur="Firefox 130", systeme="Windows 11", ip="2.2.2.2")
    _session(uid, "n-tel", navigateur="Safari 18", systeme="iOS 18", type_app="mobile", ip="3.3.3.3")

    alerts.check_comptes_multi_postes()
    assert _alertes("compte_multi_postes") == []


def test_trois_onglets_sur_un_poste_ne_font_pas_trois_postes():
    """Rouvrir son navigateur crée une session de plus, pas un appareil de plus. Compter les
    sessions signalerait un professeur qui n'a rien fait d'anormal."""
    resemer_reglages()
    _table_rase()
    uid = _prof("onglets@test.fr")
    for i in range(8):
        _session(uid, f"o-{i}", navigateur="Chrome 120", systeme="Windows 11", ip="4.4.4.4")

    alerts.check_comptes_multi_postes()
    assert _alertes("compte_multi_postes") == [], "huit sessions, un seul appareil"


def test_trop_d_appareils_declenche_une_alerte_exploitable():
    """Au-delà du seuil, l'alerte part — et elle porte tout ce qu'il faut pour décider : le
    professeur, le nombre mesuré, le seuil, et l'écran où vérifier."""
    resemer_reglages()
    _table_rase()
    uid = _prof("partage@test.fr")
    for i in range(6):
        _session(uid, f"p-{i}", navigateur=f"Chrome 12{i}", ip=f"5.5.5.{i}")

    alerts.check_comptes_multi_postes()
    lot = _alertes("compte_multi_postes")
    assert len(lot) == 1
    a = lot[0]
    assert a.user_id == uid and a.user_email == "partage@test.fr", "l'alerte doit dire DE QUI"
    assert a.donnees["appareils"] == 6 and a.donnees["seuil"] == 4
    assert a.lien == "/admin/sessions", "sans chemin, l'alerte est un cul-de-sac"
    assert a.level == "warning", "on signale, on n'annonce pas une panne"


def test_rien_n_est_ferme():
    """SURVEILLER, PAS INTERDIRE. Fermer la session de quelqu'un sur un soupçon coûte plus cher
    que le compte partagé qu'on cherchait."""
    resemer_reglages()
    _table_rase()
    uid = _prof("intact@test.fr")
    for i in range(6):
        _session(uid, f"i-{i}", navigateur=f"Chrome 13{i}", ip=f"6.6.6.{i}")

    alerts.check_comptes_multi_postes()
    assert _sessions_vivantes() == 6, "aucune session ne doit avoir été fermée"


def test_deux_villes_trop_eloignees_sont_signalees(monkeypatch):
    """Lille et Marseille dans la même demi-heure : ce n'est pas la même personne. C'est le
    signal le plus sûr d'un compte partagé."""
    resemer_reglages()
    _table_rase()
    monkeypatch.setattr(loc, "localiser", lambda ip: (None, None, None))
    uid = _prof("deux-villes@test.fr")
    _session(uid, "v-lille", ip="7.7.7.1", lieu="Lille, France", coords=LILLE)
    _session(uid, "v-marseille", ip="7.7.7.2", lieu="Marseille, France", coords=MARSEILLE)

    alerts.check_connexions_eloignees()
    lot = _alertes("connexion_eloignee")
    assert len(lot) == 1
    a = lot[0]
    assert a.user_email == "deux-villes@test.fr"
    assert 750 < a.donnees["distance_km"] < 850
    assert set(a.donnees["lieux"]) == {"Lille, France", "Marseille, France"}


def test_deux_sessions_de_la_meme_ville_ne_declenchent_rien(monkeypatch):
    """Le même professeur, au même endroit, sur deux appareils : c'est la normalité."""
    resemer_reglages()
    _table_rase()
    monkeypatch.setattr(loc, "localiser", lambda ip: (None, None, None))
    uid = _prof("meme-ville@test.fr")
    _session(uid, "m-1", ip="8.8.8.1", lieu="Lille, France", coords=LILLE)
    _session(uid, "m-2", ip="8.8.8.2", lieu="Lille, France", coords=(50.64, 3.07))

    alerts.check_connexions_eloignees()
    assert _alertes("connexion_eloignee") == []


def test_une_session_sans_coordonnees_n_est_comparee_a_rien(monkeypatch):
    """Réseau local, adresse que personne ne sait situer : on l'ignore. La placer d'office
    quelque part inventerait une distance, donc une alerte fausse."""
    resemer_reglages()
    _table_rase()
    monkeypatch.setattr(loc, "localiser", lambda ip: (None, None, None))
    uid = _prof("sans-lieu@test.fr")
    _session(uid, "s-1", ip="9.9.9.1", lieu="Lille, France", coords=LILLE)
    _session(uid, "s-2", ip="192.168.1.10", lieu="Réseau local", coords=(None, None))

    alerts.check_connexions_eloignees()
    assert _alertes("connexion_eloignee") == []


def test_la_surveillance_resout_les_lieux_elle_meme(monkeypatch):
    """Sans ça, la comparaison ne porterait que sur les sessions déjà regardées par
    l'administrateur — donc presque jamais sur celles qui comptent."""
    resemer_reglages()
    _table_rase()
    uid = _prof("resolution@test.fr")
    _session(uid, "r-1", ip="7.7.7.1")
    _session(uid, "r-2", ip="7.7.7.2")

    lieux = {"7.7.7.1": ("Lille, France", *LILLE), "7.7.7.2": ("Marseille, France", *MARSEILLE)}
    monkeypatch.setattr(loc, "localiser", lambda ip: lieux.get(ip, (None, None, None)))

    alerts.check_connexions_eloignees()
    assert len(_alertes("connexion_eloignee")) == 1, "les lieux devaient être résolus au passage"


def test_l_anti_flood_ne_confond_pas_deux_professeurs():
    """Le titre seul comme clé faisait taire le second signalement pendant deux heures : deux
    comptes partagés, une seule alerte, et le deuxième passait inaperçu."""
    resemer_reglages()
    _table_rase()
    for nom in ("flood-un@test.fr", "flood-deux@test.fr"):
        uid = _prof(nom)
        for i in range(6):
            _session(uid, f"{nom}-{i}", navigateur=f"Chrome 14{i}", ip=f"10.0.{uid}.{i}")

    alerts.check_comptes_multi_postes()
    lot = _alertes("compte_multi_postes")
    assert len(lot) == 2, "chaque professeur doit avoir son alerte"
    assert {a.user_email for a in lot} == {"flood-un@test.fr", "flood-deux@test.fr"}


def test_le_meme_professeur_n_est_pas_signale_deux_fois():
    """L'anti-flood tient toujours : deux passages de la surveillance à cinq minutes d'intervalle
    ne doivent pas produire deux fois la même alerte."""
    resemer_reglages()
    _table_rase()
    uid = _prof("repete@test.fr")
    for i in range(6):
        _session(uid, f"rp-{i}", navigateur=f"Chrome 15{i}", ip=f"11.0.0.{i}")

    alerts.check_comptes_multi_postes()
    alerts.check_comptes_multi_postes()
    assert len(_alertes("compte_multi_postes")) == 1
