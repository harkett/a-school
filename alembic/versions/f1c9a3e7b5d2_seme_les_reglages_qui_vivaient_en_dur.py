"""Seme les 14 reglages qui n'existaient QUE dans le code (`SETTING_DEFAULTS`).

10/08/2026. LE CONSTAT. `get_settings_dict()` partait du dictionnaire `SETTING_DEFAULTS` puis
ecrasait avec la base. Sur ses 18 cles, 16 n'avaient AUCUNE ligne en `settings` : c'etait donc le
code qui gagnait, en silence, pendant que chaque ecran et chaque docstring affirment que la base
est la source unique. Un admin ouvrant `settings` ne voyait pas ces reglages ; il ne pouvait ni
les lire, ni les changer, ni meme savoir qu'ils existaient.

CE QUE FAIT CETTE MIGRATION : elle ECRIT en base les 14 cles reellement lues par le code, avec
EXACTEMENT la valeur qui s'appliquait deja. Rien ne change de comportement — ce qui change, c'est
qu'elles existent enfin la ou on les cherche.

  ai_temperature, rag_top_k, stats_minutes_par_activite, ocr_model, depot_max_pages, depot_max_mo,
  stream_silence_timeout, ai_retry_max, ai_retry_wait_max, staging_ttl_heures,
  alerte_cpu_pct, alerte_disque_pct, alerte_tentatives_1h, alerte_anti_flood_h

LES QUATRE QUI NE SONT PAS SEMEES, ET POURQUOI :
  • `ai_model`, `ai_provider` — deja en base (semees a l'installation).
  • `max_tokens_default` — MORTE : son ecran a disparu le meme jour (migration e2b6d4a8f7c1).
    Elle quitte le dictionnaire sans etre semee : semer une valeur que rien ne lit recreerait
    le defaut qu'on repare.
  • `prompt_gabarit_type` — deja en base, et `get_prompt` doit LEVER si la ligne manque. Le
    doublon en dur annulait ce filet : une base incomplete passait inapercue.
  • `welcome_email_subject` / `welcome_email_body` RESTENT dans le code, seuls. Ce n'est pas un
    reglage mais un FILET : si la ligne 'welcome' d'`email_templates` manque, le mail de
    bienvenue part quand meme (`_WelcomeFallback`). Un inscrit sans mail ne peut pas valider son
    compte — la, le repli est le bon choix, et il est le seul qui reste.

Revision ID: f1c9a3e7b5d2
Revises: e2b6d4a8f7c1
Create Date: 2026-08-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1c9a3e7b5d2'
down_revision: Union[str, Sequence[str], None] = 'e2b6d4a8f7c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Valeurs RECOPIEES de SETTING_DEFAULTS au 10/08/2026 : ce qui s'appliquait deja.
REGLAGES = {
    # Generation
    "ai_temperature": "",            # vide = defaut du fournisseur (non reglee)
    "rag_top_k": "4",
    "stream_silence_timeout": "30",  # secondes de silence avant coupure du flux
    "ai_retry_max": "2",
    "ai_retry_wait_max": "10",
    "ocr_model": "meta-llama/llama-4-scout-17b-16e-instruct",
    # Depot de referentiel
    "depot_max_pages": "150",
    "depot_max_mo": "30",
    "staging_ttl_heures": "24",
    # Statistiques
    "stats_minutes_par_activite": "15",
    # Surveillance
    "alerte_cpu_pct": "90",
    "alerte_disque_pct": "85",
    "alerte_tentatives_1h": "10",
    "alerte_anti_flood_h": "2",
}


def upgrade() -> None:
    conn = op.get_bind()
    for cle, valeur in REGLAGES.items():
        conn.execute(
            sa.text("INSERT INTO settings (key, value) VALUES (:k, :v) "
                    "ON CONFLICT (key) DO NOTHING"),
            {"k": cle, "v": valeur},
        )


def downgrade() -> None:
    """Retire les 14 lignes. Le code, lui, ne les retrouvera pas : le dictionnaire en dur a ete
    vide dans le meme geste. Un downgrade sans revenir sur le code laisse donc une base a qui il
    manque des reglages — c'est voulu, et c'est visible : les lecteurs levent avec un message
    clair au lieu d'appliquer un chiffre que personne n'a choisi."""
    conn = op.get_bind()
    for cle in REGLAGES:
        conn.execute(sa.text("DELETE FROM settings WHERE key = :k"), {"k": cle})
