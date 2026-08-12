"""Ce que les trois écrans d'analyse font de la même façon.

Ambiguïtés, Consigne et Équité sont des frères : même geste (le prof colle un texte, aSchool le
relit), donc mêmes deux besognes d'entrée et de sortie — savoir QUI demande, et tirer un JSON
d'une réponse qui n'en est pas toujours un.

Ces deux fonctions vivaient en double, recopiées à l'identique dans `ambiguites.py` et
`consigne.py`. Le troisième frère en aurait fait une troisième copie : c'est le moment où une
tolérance devient un défaut. Elles sont ici, écrites une fois.
"""
import json
import re

from fastapi import HTTPException

from backend.securite import comptes


def email_de_session(aschool_access: str | None) -> str:
    """Le compte derrière le cookie, ou 401. Aucun écran d'analyse ne travaille sans lui."""
    if not aschool_access:
        raise HTTPException(401, "Non connecté.")
    email = comptes.verify_access_token(aschool_access)
    if not email:
        raise HTTPException(401, "Session expirée.")
    return email


def json_du_modele(raw: str) -> dict:
    """Le JSON d'une réponse de modèle, quel que soit ce qu'il a mis autour.

    Trois tentatives, de la plus stricte à la plus tolérante : la réponse entière, un bloc
    ```json``` , puis la première accolade jusqu'à la dernière. Un modèle qui préface son JSON
    d'une phrase de politesse ne doit pas coûter une analyse au professeur.

    Lève `ValueError` si rien n'est exploitable — l'appelant en fait un message clair."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    raise ValueError("Réponse non parseable en JSON")
