"""Helper de test — créer un prof dont le profil pointe (matière × niveau) PAR CLÉ.

Le profil `users` est rangé UNIQUEMENT par clé (subject_id / niveau_id) : le nom seul ne suffit
pas, la matière et le niveau doivent EXISTER en base. Et depuis le chantier Matière, une matière
n'existe QUE dans le référentiel d'un niveau : la créer, c'est donc créer le niveau, son
référentiel, puis SA matière. Ce helper fait cette chaîne en get-or-create idempotent (réutilise
ce qui est déjà semé) et renvoie un objet User prêt à `db.add(...)`.
Préfixé « _ » → non collecté par pytest.
"""
from backend.core.models_db import (ActiviteType, Cycle, Matiere, Niveau, Referentiel,
                                    ReferentielActiviteType, User)


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


def referentiel_id(db, niveau_nom):
    """Le référentiel DU niveau (get-or-create) — la maison des matières. Un seul par niveau."""
    niv_id = niveau_id(db, niveau_nom)
    if not niv_id:
        return None
    ref = db.query(Referentiel).filter(Referentiel.niveau_id == niv_id).first()
    if not ref:
        cle = f"ref_{niveau_nom}".lower().replace(" ", "_")
        ref = Referentiel(niveau_id=niv_id, nom_fixe=cle, collection=cle, filtres=None,
                          fichier="doc.pdf", texte_epure="TEXTE")
        db.add(ref)
        db.flush()
    return ref.id


def matiere_id(db, nom, niveau_nom="6e", validee=True):
    """La matière `nom` DANS le référentiel du niveau (get-or-create). `validee` par défaut :
    c'est l'état d'une matière retenue par l'admin, la seule qu'un profil puisse porter."""
    if not nom:
        return None
    ref_id = referentiel_id(db, niveau_nom)
    m = (db.query(Matiere)
           .filter(Matiere.referentiel_id == ref_id, Matiere.nom == nom).first())
    if not m:
        m = Matiere(referentiel_id=ref_id, nom=nom, ordre=0, actif=True, validee=validee)
        db.add(m)
        db.flush()
    return m.id


def user_couple(db, email, subject=None, niveau=None, **kw):
    """User(...) avec le couple de profil posé PAR CLÉ. La matière est créée DANS le référentiel
    du niveau demandé — sans niveau, elle n'aurait nulle part où exister."""
    return User(
        email=email,
        subject_id=matiere_id(db, subject, niveau) if (subject and niveau) else None,
        niveau_id=niveau_id(db, niveau),
        **kw,
    )


def type_pret(db, niveau_nom, label="Compréhension", prompt="Texte : {texte}\n{referentiel}"):
    """Un type d'activité RÉELLEMENT utilisable pour un niveau — la précondition que le serveur
    exige désormais À L'ÉCRITURE comme à la génération (`type_du_couple_verifie`) :

      1. le niveau a un référentiel officiel (`referentiels`) ;
      2. le type existe au catalogue et y est actif ;
      3. il est COCHÉ pour ce référentiel, avec un prompt non vide.

    Un type créé seul (sans référentiel ni liaison) n'a jamais existé dans la vraie vie : c'est
    ce raccourci de test que les contrôles de l'étape 8 ont mis en évidence. Get-or-create
    idempotent, renvoie l'id du type.
    """
    ref_id = referentiel_id(db, niveau_nom)
    t = db.query(ActiviteType).filter(ActiviteType.label == label).first()
    if not t:
        t = ActiviteType(label=label, ordre=1, actif=True, origine="systeme")
        db.add(t)
        db.flush()
    lien = (db.query(ReferentielActiviteType)
              .filter(ReferentielActiviteType.referentiel_id == ref_id,
                      ReferentielActiviteType.activite_type_id == t.id).first())
    if not lien:
        db.add(ReferentielActiviteType(referentiel_id=ref_id, activite_type_id=t.id,
                                       actif=True, source="admin", prompt=prompt, ordre=1))
    db.flush()
    return t.id
