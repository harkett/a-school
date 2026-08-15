# -*- coding: utf-8 -*-
"""RELEVER LES TARIFS SUR LA PAGE DU FOURNISSEUR — sans IA, sans clé, sans abonnement.

POURQUOI CE MODULE. Les tarifs se saisissaient à la main, modèle par modèle, en lisant la page du
fournisseur dans un autre onglet. Deux défauts : c'est long, et surtout ça vieillit — un prix
changé chez lui reste faux chez nous jusqu'à ce que quelqu'un s'en aperçoive. Le fournisseur
publie ses prix ; il suffit d'aller les lire.

CE QU'ON NE FAIT PAS : appeler une IA pour lire une page web. Les grilles tarifaires sont des
tableaux — un nom de modèle, deux montants — et un tableau se lit avec une expression régulière.
Payer un modèle de langage pour extraire deux nombres serait absurde, et le résultat moins fiable :
une IA peut inventer un chiffre, pas un `findall`.

COMMENT ON RETROUVE LA BONNE LIGNE. Par le NOM PUBLIC du modèle (`ai_modeles.nom_fournisseur`),
celui qui figure sur la grille — pas par son nom d'appel. Chez Infomaniak les deux diffèrent :
on appelle « mistral3 », la grille dit « mistralai/Ministral-3-14B-Instruct-2512 ». Un modèle sans
nom public est cherché sous son nom d'appel, ce qui suffit chez Anthropic et Groq où les deux sont
le même.

CE QU'ON RELÈVE, ET DANS QUEL ORDRE. Dans le texte qui suit le nom du modèle, les deux premiers
montants : l'ENTRÉE puis la SORTIE. C'est l'ordre de toutes les grilles observées, et c'est celui
qui a un sens — on écrit avant de lire la réponse. Un troisième montant (cache, image, minute) est
ignoré : il ne correspond à rien de ce qu'on stocke.

QUAND ON N'ÉCRIT PAS. Nom introuvable sur la page, un seul montant, montant aberrant : le modèle
est laissé tel quel et signalé. Un tarif faux coûte plus cher qu'un tarif absent — l'absence se
voit à l'écran (« non relevé »), l'erreur non.
"""
import logging
import re
import urllib.request

from backend.core.devises import DEVISES

log = logging.getLogger(__name__)

# Ce qu'on accepte d'ouvrir. L'adresse vient de l'administrateur, mais rien n'oblige à suivre un
# `file://` ou un `ftp://` qui n'a rien à faire ici.
SCHEMAS = ("http://", "https://")

# Au-delà, ce n'est plus une grille tarifaire. Garde-fou contre une page qui servirait un flux
# sans fin — on lit ce qu'il faut et on s'arrête.
TAILLE_MAX = 8 * 1024 * 1024

# Combien de texte on regarde APRÈS le nom d'un modèle pour y trouver ses deux prix. Assez pour
# couvrir un bloc « entrée / sortie », trop peu pour déborder sur le modèle suivant et lui voler
# ses montants.
FENETRE = 400

# Les symboles qu'on rencontre à la place du code à trois lettres.
SYMBOLES = {"$": "USD", "€": "EUR", "£": "GBP", "Fr.": "CHF"}

# Un montant : « CHF 0.30 », « 0.30 CHF », « $3 », « 2,50 € ». Le séparateur décimal peut être un
# point ou une virgule — les pages françaises écrivent « 0,30 ».
_DEVISE = "|".join(list(DEVISES) + [re.escape(s) for s in SYMBOLES])
# Le `[\s|]*` entre la devise et le montant n'est pas un détail : après réduction du HTML, une
# cellule de tableau devient « CHF | 0.30 ». Exiger un simple espace ne trouvait RIEN sur une page
# pourtant parfaitement lisible.
_MONTANT = re.compile(
    rf"(?:(?P<d1>{_DEVISE})[\s|]*(?P<m1>\d+(?:[.,]\d+)?)|(?P<m2>\d+(?:[.,]\d+)?)[\s|]*(?P<d2>{_DEVISE}))",
    re.IGNORECASE,
)


def _texte(html: str) -> str:
    """Le HTML réduit à son texte, balises remplacées par un séparateur.

    Le séparateur compte : sans lui, « <td>0.30</td><td>0.40</td> » deviendrait « 0.300.40 »."""
    sans_script = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    brut = re.sub(r"<[^>]+>", " | ", sans_script)
    brut = (brut.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'"))
    return re.sub(r"(\s*\|\s*)+", " | ", brut)


def lire_page(url: str) -> str:
    """Télécharge la page et rend son texte. Lève `ValueError` avec un message pour l'admin."""
    if not url or not url.lower().startswith(SCHEMAS):
        raise ValueError("L'adresse doit commencer par http:// ou https://.")
    try:
        # `User-Agent` explicite : plusieurs sites répondent 403 à l'agent par défaut de Python —
        # le même piège que chez Groq et à la Banque centrale européenne.
        requete = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; aSchool/1.0)",
            "Accept-Language": "fr,en;q=0.8",
        })
        with urllib.request.urlopen(requete, timeout=25) as r:
            brut = r.read(TAILLE_MAX)
    except Exception as e:
        raise ValueError(f"Page injoignable ({type(e).__name__}). Vérifiez l'adresse.") from e
    return _texte(brut.decode("utf-8", "replace"))


def _montants(fenetre: str) -> list[tuple[float, str | None]]:
    """Les montants trouvés dans l'ordre, avec leur devise quand elle est écrite."""
    trouves = []
    for m in _MONTANT.finditer(fenetre):
        brut = m.group("m1") or m.group("m2")
        dev = (m.group("d1") or m.group("d2") or "").strip()
        trouves.append((float(brut.replace(",", ".")), SYMBOLES.get(dev, dev.upper()) or None))
    return trouves


# Ce qui NE PEUT PAS toucher un nom de modèle sans en faire un autre. « qwen3 » ne doit pas se
# reconnaître dans « Qwen/Qwen3.5-122B-A10B-FP8 » : ce sont deux modèles, à deux prix différents
# (0,40 contre 3,20 CHF en sortie). Sans cette frontière, le relevé recopie sur l'un le tarif de
# l'autre — et rien à l'écran ne le dirait.
_COLLE = re.compile(r"[0-9a-z./_-]", re.IGNORECASE)


def _trouver(texte: str, minuscule: str, nom: str) -> int:
    """L'index du nom dans la page, à condition qu'il y soit ENTIER. -1 sinon."""
    cible = nom.lower()
    depart = 0
    while True:
        i = minuscule.find(cible, depart)
        if i < 0:
            return -1
        avant = texte[i - 1] if i > 0 else " "
        apres_i = i + len(cible)
        apres = texte[apres_i] if apres_i < len(texte) else " "
        if not _COLLE.match(avant) and not _COLLE.match(apres):
            return i
        depart = i + 1


def relever(texte: str, noms: list[str]) -> dict[str, dict]:
    """Pour chaque nom cherché, ce que la page en dit.

    Rend `{nom: {"entree": float, "sortie": float, "devise": str|None}}`. Un nom absent de la page,
    ou suivi de moins de deux montants, n'a pas d'entrée dans le résultat : on ne devine pas."""
    resultat = {}
    minuscule = texte.lower()
    for nom in noms:
        if not nom:
            continue
        i = _trouver(texte, minuscule, nom)
        if i < 0:
            continue
        prix = _montants(texte[i + len(nom): i + len(nom) + FENETRE])
        if len(prix) < 2:
            continue
        (entree, dev_e), (sortie, dev_s) = prix[0], prix[1]
        resultat[nom] = {
            "entree": entree,
            "sortie": sortie,
            # La devise des deux montants doit être la même : une grille qui annoncerait l'entrée
            # en francs et la sortie en dollars n'existe pas, et si elle existait il vaudrait mieux
            # ne rien conclure.
            "devise": dev_e if dev_e and dev_e == dev_s else None,
        }
    return resultat
