"""Helper de test — créer un prof dont le profil pointe (matière × niveau) PAR CLÉ.

Le profil `users` est désormais rangé UNIQUEMENT par clé (subject_id / niveau_id) : le nom seul
ne suffit plus, la matière et le niveau doivent EXISTER dans `matieres` / `niveaux`. Ce helper
fait un get-or-create idempotent (réutilise la ligne si elle est déjà semée, sinon la crée) et
renvoie un objet User prêt à `db.add(...)`. Préfixé « _ » → non collecté par pytest.
"""
from backend.core.models_db import Cycle, Matiere, Niveau, User


def matiere_id(db, nom):
    if not nom:
        return None
    m = db.query(Matiere).filter(Matiere.nom == nom).first()
    if not m:
        m = Matiere(nom=nom, ordre=0)
        db.add(m)
        db.flush()
    return m.id


def niveau_id(db, nom):
    if not nom:
        return None
    n = db.query(Niveau).filter(Niveau.nom == nom).first()
    if not n:
        cyc = db.query(Cycle).first()
        if not cyc:
            cyc = Cycle(nom="Cycle-test", ordre=0)
            db.add(cyc)
            db.flush()
        n = Niveau(cycle_id=cyc.id, nom=nom, ordre=0)
        db.add(n)
        db.flush()
    return n.id


def user_couple(db, email, subject=None, niveau=None, **kw):
    """User(...) avec le couple de profil posé PAR CLÉ (get-or-create matière/niveau)."""
    return User(
        email=email,
        subject_id=matiere_id(db, subject),
        niveau_id=niveau_id(db, niveau),
        **kw,
    )
