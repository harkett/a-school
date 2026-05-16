"""
Seed initial STT — Phase 1.2
Source : MesMD/DEEPGRAM/seeds.md
Appelé au démarrage du backend depuis backend/main.py (idempotent).

Contient :
- 8 messages utilisateur (4 mode neutral actif Phase 1 + 4 mode volume en réserve)
- 80 keyterms transversaux (Phase 1 — vocabulaire pédagogique universel)
"""

from datetime import datetime

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from backend.models_db import STTMessage, STTKeytermGlobal


# ============================================================
# 1. Messages utilisateur — 8 entrées (4 neutral + 4 volume)
# ============================================================

SEED_MESSAGES = [
    # --- Mode neutral (Phase 1 — actif) ---
    ("neutral", "preventive",
     "Information : le service de dictée vocale fera l'objet d'une intervention "
     "technique dans les prochains jours et pourrait être temporairement "
     "indisponible. Vous pouvez continuer à utiliser toutes les fonctionnalités "
     "normalement et saisir vos textes au clavier en attendant. Merci de votre "
     "compréhension."),

    ("neutral", "unavailable",
     "La dictée vocale est momentanément indisponible pour intervention "
     "technique. Vous pouvez continuer à préparer vos contenus en saisissant "
     "vos textes directement au clavier — toutes les autres fonctionnalités "
     "restent pleinement opérationnelles. Le service sera rétabli rapidement. "
     "Merci de votre compréhension."),

    ("neutral", "saturation",
     "La dictée vocale est temporairement saturée. Veuillez patienter quelques "
     "instants et réessayer dans un moment, ou saisissez votre texte au "
     "clavier. Toutes les autres fonctionnalités restent disponibles."),

    ("neutral", "session_expired",
     "Votre session de dictée a été interrompue après plusieurs minutes "
     "d'inactivité. Le texte déjà transcrit est conservé. Vous pouvez relancer "
     "une nouvelle dictée à tout moment."),

    # --- Mode volume (Phase 2+ — en réserve, inactif) ---
    ("volume", "preventive",
     "Information : la dictée vocale rencontre actuellement une forte affluence "
     "en raison du grand nombre d'enseignants qui l'utilisent simultanément sur "
     "la plateforme. Le service pourrait être temporairement indisponible dans "
     "les prochains jours, le temps que nos équipes techniques augmentent la "
     "capacité d'accueil. Vous pouvez continuer à utiliser toutes les "
     "fonctionnalités normalement et saisir vos textes au clavier en attendant. "
     "Merci de votre patience et bonne continuation dans vos préparations."),

    ("volume", "unavailable",
     "La dictée vocale est momentanément indisponible en raison du grand "
     "nombre d'enseignants connectés actuellement sur la plateforme. Nos "
     "équipes techniques travaillent à augmenter la capacité pour que chacun "
     "puisse en profiter pleinement. En attendant, vous pouvez continuer à "
     "préparer vos contenus en saisissant vos textes directement au clavier — "
     "toutes les autres fonctionnalités restent pleinement opérationnelles. "
     "Le service de dictée sera rétabli rapidement. Merci de votre compréhension."),

    ("volume", "saturation",
     "La dictée vocale est très sollicitée en ce moment par les nombreux "
     "enseignants connectés. Veuillez patienter quelques instants et réessayer "
     "dans une minute, ou saisissez votre texte directement au clavier. Toutes "
     "les autres fonctionnalités restent disponibles. Merci de votre compréhension."),

    ("volume", "session_expired",
     "Votre session de dictée a été interrompue après plusieurs minutes "
     "d'inactivité. Le texte déjà transcrit est conservé. Vous pouvez relancer "
     "une nouvelle dictée à tout moment."),
]


# ============================================================
# 2. Keyterms transversaux — 80 termes (Phase 1)
# ============================================================

SEED_KEYTERMS = [
    # Vocabulaire pédagogique universel (16)
    "exercice", "consigne", "énoncé", "question", "réponse",
    "justifier", "démontrer", "calculer", "expliquer", "rédiger",
    "élève", "professeur", "leçon", "chapitre", "contrôle", "évaluation",
    # Mathématiques (16)
    "polynôme", "hypoténuse", "théorème", "équation", "dérivée",
    "intégrale", "fraction", "numérateur", "dénominateur", "périmètre",
    "aire", "volume", "parallélogramme", "isocèle", "équilatéral", "asymptote",
    # Sciences — physique-chimie / SVT (16)
    "Lavoisier", "Avogadro", "Newton", "Einstein", "Curie", "Pasteur", "Darwin",
    "molécule", "atome", "électron", "proton", "neutron",
    "photosynthèse", "mitochondrie", "ADN", "ARN",
    # Lettres / Philosophie (12)
    "Baudelaire", "Hugo", "Molière", "Rousseau", "Voltaire", "Camus",
    "métaphore", "allégorie", "oxymore", "alexandrin", "sonnet", "dialectique",
    # Histoire-Géographie (10)
    "Charlemagne", "Napoléon", "Robespierre", "Clemenceau", "de Gaulle",
    "Renaissance", "Révolution", "Industrialisation", "Mondialisation", "décolonisation",
    # Arts / EPS / Langues / Technique (10)
    "Picasso", "Monet", "Vinci", "basket-ball", "handball",
    "athlétisme", "PISA", "QCM", "baccalauréat", "brevet",
]

assert len(SEED_KEYTERMS) == 80, f"Expected 80 keyterms, got {len(SEED_KEYTERMS)}"


# ============================================================
# Logique de seed (idempotent)
# ============================================================

def _seed_messages(db: Session) -> int:
    """Upsert des 8 messages. Met à jour content + updated_at si déjà présent."""
    now = datetime.utcnow()
    for mode, code, content in SEED_MESSAGES:
        stmt = sqlite_insert(STTMessage).values(
            mode=mode, code=code, content=content, updated_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["mode", "code"],
            set_={"content": content, "updated_at": now},
        )
        db.execute(stmt)
    db.commit()
    return len(SEED_MESSAGES)


def _seed_keyterms(db: Session) -> int:
    """Insert idempotent des 80 keyterms. Ignore si déjà présent.

    Compte via SELECT before/after car result.rowcount n'est pas fiable
    sur SQLite avec on_conflict_do_nothing.
    """
    before = db.query(STTKeytermGlobal).count()
    for term in SEED_KEYTERMS:
        stmt = sqlite_insert(STTKeytermGlobal).values(term=term)
        stmt = stmt.on_conflict_do_nothing(index_elements=["term"])
        db.execute(stmt)
    db.commit()
    after = db.query(STTKeytermGlobal).count()
    return after - before


def run_seed(db: Session) -> None:
    n_msgs = _seed_messages(db)
    n_kts = _seed_keyterms(db)
    print(f"[seed_stt] {n_msgs} messages upsertés, {n_kts} nouveaux keyterms (sur 80 attendus)")
