"""Règle de nommage des dossiers de référentiel — écrite UNE fois, pour tout le monde.

`dossier_cle` était recopiée à l'identique dans trois modules (dépôt admin, module RAG, routeur
du profil). La duplication était assumée pour ne pas coupler le profil au RAG : ce module neutre
lève l'objection — il ne dépend de rien (deux modules de la bibliothèque standard), personne ne
se couple à personne en l'important, et la règle n'a plus qu'un seul endroit où changer.

La convention de rangement qu'elle sert : REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf.
"""
import re
import unicodedata


def dossier_cle(nom: str) -> str:
    """Nom de cycle/niveau → nom de dossier-clé : accents enlevés, MAJUSCULES, non-alphanumérique
    remplacé par « _ ». Ex. « Crèche » → « CRECHE », « BMG_0-3 » → « BMG_0_3 ». Un nom qui ne laisse
    aucun caractère exploitable retombe sur « REFERENTIEL » (jamais de dossier au nom vide)."""
    s = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()
    return s or "REFERENTIEL"
