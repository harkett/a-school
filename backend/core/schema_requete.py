"""Quel schéma PostgreSQL cette requête doit-elle lire ? — la résolution `Host` → schéma.

CE QUE ÇA REMPLACE. Une démonstration était un PROCESS entier : son propre uvicorn, sa propre
`DATABASE_URL`, sa propre base. Cinq démonstrations, cinq process, 800 Mo chacun. L'étanchéité
ne coûtait aucune ligne de code, mais quatre gigaoctets de mémoire.

CE QUE ÇA DEVIENT. Un seul process pour les cinq, une base à elles seules, un SCHÉMA par
démonstration. Le sous-domaine dit lequel : `demo-crsa.aschool.fr` sert le schéma `crsa`.
L'APPLICATION RÉELLE RESTE DEHORS — son service, son process et SA BASE sont séparés. Ce
process-ci n'a donc pas le réel sous la main : il ne peut pas l'atteindre, même par erreur.

LA LISTE BLANCHE, C'EST LA BASE. Il n'y a ni table de routage à tenir à jour, ni fichier de
configuration à recopier : le schéma existe dans `information_schema.schemata`, on sert ; il
n'existe pas, c'est 404. Un sous-domaine inventé ne peut donc pas produire une erreur SQL, et
créer une démonstration ne demande rien d'autre que créer son schéma.

PAS DE CACHE, à dessein. Un schéma retiré doit cesser de répondre tout de suite, et un schéma
tout juste versé doit répondre sans redémarrage. La vérification est un `SELECT 1` sur un
catalogue que PostgreSQL garde en mémoire — c'est moins cher que le cache d'invalidation qu'il
faudrait écrire pour l'éviter.
"""
import re

from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.core import database as _db
from backend.core.database import SCHEMA_REEL

# `demo-crsa.aschool.fr` → `crsa`. Le port (`:8000` en local) ne fait pas partie du nom d'hôte
# utile et se retire avant. Le jeu de caractères est celui d'un nom de schéma PostgreSQL non
# quoté : ce qui n'y entre pas ne peut pas être un schéma, donc pas la peine d'aller le demander.
_MOTIF_HOTE = re.compile(r"^demo-([a-z0-9_]{1,55})\.aschool\.fr$", re.IGNORECASE)


def schema_du_host(host: str | None) -> str | None:
    """Le schéma demandé par cet en-tête `Host`, ou None si ce n'est pas un sous-domaine démo.

    None n'est pas une erreur : c'est le cas ordinaire du réel et du poste de développement
    (`localhost:5173`). L'appelant en fait `SCHEMA_REEL`."""
    hote = (host or "").split(",")[0].strip().split(":")[0]
    trouve = _MOTIF_HOTE.match(hote)
    return trouve.group(1).lower() if trouve else None


def schema_existe(nom: str) -> bool:
    """Ce schéma est-il réellement dans la base ? La question se pose au catalogue, pas à une
    liste que quelqu'un aurait à tenir à jour.

    `pg_namespace` ET PAS `information_schema.schemata` : la seconde est filtrée par les droits
    de l'utilisateur connecté. Un schéma versé par `pg_dump` appartient à l'utilisateur SYSTÈME
    qui a lancé le versement ; l'application, connectée sous un autre rôle, ne le voyait pas et
    rendait 404 sur une démonstration parfaitement présente. Constaté en production le
    11/08/2026, sur les cinq à la fois."""
    with _db.engine.connect() as conn:
        return conn.execute(
            text("SELECT 1 FROM pg_namespace WHERE nspname = :nom"),
            {"nom": nom},
        ).first() is not None


def schema_de(request: Request) -> str:
    """Le schéma de CETTE requête. Le repli sur le réel vaut pour tout ce qui n'est pas passé
    par le middleware — un test qui fabrique une requête à la main, par exemple. Le réel est le
    seul repli sûr : se tromper vers une démonstration ferait écrire un prof dans un bac à sable
    sans qu'aucune erreur ne le signale."""
    return getattr(request.state, "schema_db", SCHEMA_REEL)


class SchemaRequeteMiddleware(BaseHTTPMiddleware):
    """Pose `request.state.schema_db` avant que quoi que ce soit touche la base.

    IL DOIT S'EXÉCUTER AVANT `UserSessionMiddleware`, qui ouvre une session dès la phase 1 pour
    vérifier la session du prof : sans schéma résolu, cette lecture partirait sur le réel. Dans
    Starlette, le DERNIER middleware ajouté est le plus EXTERNE — celui-ci est donc ajouté après
    `UserSessionMiddleware` dans `main.py`, ce qui le fait tourner avant lui."""

    async def dispatch(self, request: Request, call_next):
        demande = schema_du_host(request.headers.get("host"))
        if demande is not None:
            if not schema_existe(demande):
                # 404 et pas 500 : un sous-domaine sans schéma est une adresse qui n'existe pas,
                # exactement comme une URL inconnue. Aucune erreur SQL ne doit remonter au
                # visiteur — elle nommerait la base et ne lui apprendrait rien.
                return JSONResponse(
                    {"detail": "Cette adresse n’existe pas sur ce serveur."}, status_code=404
                )
            request.state.schema_db = demande
        else:
            request.state.schema_db = SCHEMA_REEL
        return await call_next(request)
