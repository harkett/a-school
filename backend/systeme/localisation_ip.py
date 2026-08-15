# -*- coding: utf-8 -*-
"""D'OÙ VIENT UNE CONNEXION — la ville derrière l'adresse IP, sans clé et sans abonnement.

POURQUOI. L'écran des sessions affiche depuis toujours l'adresse IP. Elle ne dit rien : personne
ne reconnaît une ville dans « 83.228.245.163 ». Or c'est exactement ce qu'il faut voir pour
repérer un compte partagé — le même professeur ouvert à Lille et à Marseille en même temps n'est
pas le même professeur.

CE QUE ÇA COÛTE : rien. Le service interrogé (freeipapi.com) est gratuit, autorise l'usage
commercial et ne demande aucune clé — donc aucun secret à poser sur le serveur, aucun compte à
renouveler. Sa limite est de 60 appels par minute, très au-dessus de nos besoins : on résout UNE
FOIS par session, pas à chaque affichage, et le résultat est écrit dans la ligne de la session.

CE QU'ON NE FAIT PAS. Aucun appel pendant qu'un professeur travaille : la résolution se fait
quand l'administrateur regarde l'écran, ou quand une vérification tourne. Une page web ne doit
jamais attendre après un serveur tiers.

QUAND ÇA NE MARCHE PAS, ON NE MENT PAS. Service muet, adresse illisible, réseau coupé : la
fonction rend `None` et la session reste sans lieu. Une ville inventée serait pire que pas de
ville — on prendrait des décisions dessus.

LES ADRESSES PRIVÉES N'ONT PAS DE VILLE. En développement, derrière un pare-feu ou un proxy mal
réglé, l'adresse vue est celle du réseau local. Aucun service au monde ne peut la situer : on
répond « Réseau local » plutôt que d'aller le demander pour rien.
"""
import ipaddress
import json
import logging
import math
import urllib.request

log = logging.getLogger(__name__)

# Le service. Sans clé, gratuit, usage commercial autorisé (60 appels/minute).
SERVICE = "https://freeipapi.com/api/json/"

# Au-delà, on abandonne. L'administrateur attend devant son écran : mieux vaut une case vide
# tout de suite qu'une page qui tourne dix secondes.
DELAI = 4

# Ce que l'on répond pour une adresse qui n'existe que sur le réseau local.
RESEAU_LOCAL = "Réseau local"

# Le résultat, gardé pour la durée de vie du processus. Trente professeurs derrière le même
# établissement partagent une seule adresse publique : sans ce cache, ce serait trente appels
# identiques.
_cache: dict[str, tuple[str | None, float | None, float | None]] = {}


def _adresse_publique(ip: str) -> bool:
    """Vrai si l'adresse peut appartenir à quelqu'un, quelque part. Faux pour le réseau local."""
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (a.is_private or a.is_loopback or a.is_reserved or a.is_link_local)


def localiser(ip: str | None) -> tuple[str | None, float | None, float | None]:
    """Rend (lieu, latitude, longitude) pour une adresse IP.

    `lieu` est lisible par un humain — « Lyon, France ». Les coordonnées servent à mesurer
    l'écart entre deux connexions du même compte ; elles ne s'affichent pas."""
    if not ip:
        return None, None, None
    if not _adresse_publique(ip):
        return RESEAU_LOCAL, None, None
    if ip in _cache:
        return _cache[ip]

    resultat: tuple[str | None, float | None, float | None] = (None, None, None)
    try:
        requete = urllib.request.Request(
            SERVICE + ip,
            headers={"User-Agent": "aSchool/1.0", "Accept": "application/json"},
        )
        with urllib.request.urlopen(requete, timeout=DELAI) as reponse:
            donnees = json.loads(reponse.read(64 * 1024).decode("utf-8", "replace"))
        ville = (donnees.get("cityName") or "").strip()
        pays = (donnees.get("countryName") or "").strip()
        # Le service répond « - » quand il ne sait pas : ce n'est pas une ville.
        if ville == "-":
            ville = ""
        if pays == "-":
            pays = ""
        lieu = ", ".join(x for x in (ville, pays) if x) or None
        lat, lon = donnees.get("latitude"), donnees.get("longitude")
        lat = float(lat) if isinstance(lat, (int, float)) else None
        lon = float(lon) if isinstance(lon, (int, float)) else None
        resultat = ((lieu or None)[:120] if lieu else None, lat, lon)
    except Exception as e:
        # Un service tiers indisponible n'est pas une panne de l'application : la case reste vide.
        log.info("Localisation IP indisponible pour %s : %s", ip, e)
        return None, None, None

    _cache[ip] = resultat
    return resultat


def assurer_localisations(db, sessions) -> int:
    """Résout le lieu des sessions qui n'en ont pas encore, et l'écrit. Rend le nombre résolu.

    APPELÉE DE DEUX ENDROITS, et c'est le but : l'écran des sessions quand l'administrateur
    l'ouvre, et la surveillance des connexions quand elle passe. Tant qu'elle vivait dans l'écran,
    une alerte « connexions éloignées » n'aurait rien pu comparer — les coordonnées n'existaient
    que si quelqu'un avait regardé la page avant.

    Ne lève jamais : un service tiers en panne laisse la case vide et on réessaie plus tard. Ni
    l'écran des sessions — qui sert d'abord à déconnecter quelqu'un en urgence — ni la surveillance
    ne doivent tomber pour ça."""
    resolus = 0
    for s in sessions:
        if s.localisation or not s.ip_address:
            continue
        lieu, lat, lon = localiser(s.ip_address)
        if lieu is None:
            continue
        s.localisation, s.latitude, s.longitude = lieu, lat, lon
        resolus += 1
    if resolus:
        try:
            db.commit()
        except Exception:
            db.rollback()
            return 0
    return resolus


def distance_km(lat1, lon1, lat2, lon2) -> float | None:
    """Distance à vol d'oiseau entre deux points, en kilomètres.

    Sert à répondre à une seule question : ces deux sessions du même compte peuvent-elles être
    la même personne ? Deux villes à 800 km d'intervalle, à la même heure, non."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    rayon = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return rayon * 2 * math.asin(math.sqrt(a))
