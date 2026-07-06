from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, DateTime, Index, Text, ForeignKey, UniqueConstraint, Identity, func
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from backend.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    subject: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prenom: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nom: Mapped[str | None] = mapped_column(String(64), nullable=True)
    niveau: Mapped[str | None] = mapped_column(String(16), nullable=True)
    langue_lv: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1', nullable=False)


class EmailToken(Base):
    __tablename__ = "email_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(86), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)  # NULLABLE : NULL si l'email n'est pas (encore) un user (journal)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)  # verify_email | reset_password
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ConnexionLog(Base):
    __tablename__ = "connexion_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)  # NULLABLE : NULL si l'email n'est pas un user (journal)
    action: Mapped[str] = mapped_column(String(16), nullable=False)  # signup | login
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="feedback")  # feedback | notation
    message: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    statut: Mapped[str] = mapped_column(String(16), nullable=False, default="nouveau")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    attachment_path: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")


class EmailTemplate(Base):
    """Modèle d'email administrable. Remplace les 2 clés plates
    `welcome_email_subject/body` de `settings` par une collection de modèles
    (liste maître-détail côté admin). Deux natures d'envoi :
      - `mode_envoi = 'auto'`   : parti tout seul sur un événement (ex. bienvenue à
                                  la vérification d'email). Non supprimable.
      - `mode_envoi = 'manuel'` : envoyé à la demande vers une adresse saisie
                                  (ex. UNICEF), via send_custom_email().
    `slug` = clé stable non renommable (ex. 'welcome') ; `nom` = libellé affiché."""
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    nom: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="", server_default="")  # a quoi sert ce mail (hors contenu)
    objet: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    corps: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mode_envoi: Mapped[str] = mapped_column(String(16), nullable=False, default="manuel")  # 'auto' | 'manuel'
    supprimable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class EmailEnvoi(Base):
    """Journal des envois d'email (onglet « Suivi » de la page Email). Une ligne par
    envoi reel : mail manuel (ex. UNICEF) ET mail de bienvenue automatique. Structure
    ce que l'Audit ne porte qu'en texte libre — date, destinataire, statut triables."""
    __tablename__ = "email_envois"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    modele_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    modele_nom: Mapped[str] = mapped_column(String(128), nullable=False)
    destinataire: Mapped[str] = mapped_column(String(255), nullable=False)
    objet: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    statut: Mapped[str] = mapped_column(String(16), nullable=False)  # 'envoye' | 'echec'
    erreur: Mapped[str | None] = mapped_column(Text, nullable=True)
    envoye_le: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class SequenceSauvegardee(Base):
    __tablename__ = "sequences_sauvegardees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    matiere: Mapped[str] = mapped_column(String(64), nullable=False)
    niveau: Mapped[str] = mapped_column(String(32), nullable=False)
    theme: Mapped[str] = mapped_column(String(300), nullable=False)
    duree: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")
    description_classe: Mapped[str] = mapped_column(Text, nullable=False, default="")
    resultat: Mapped[str] = mapped_column(Text, nullable=False)
    partagee: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='0')
    anonyme: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='0')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ActiviteSauvegardee(Base):
    """Activité générée et sauvegardée — INSTANTANÉ FIGÉ (snapshot).

    À la génération, `niveau` et `matiere` sont RECOPIÉS depuis l'état effectif
    (profil par défaut, ou valeur ajustée via « Ajuster pour cette activité »,
    Parametres.jsx) dans les colonnes de cette table. L'affichage relit CES
    colonnes (MesActivites.jsx), jamais le profil.
    Chaîne : référentiel (cycles/niveaux/matieres) -> profil -> [ajustable à la
    génération] -> activité (immuable). Conséquence : modifier le profil ne
    réécrit AUCUNE activité passée.
    """
    __tablename__ = "activites_sauvegardees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activite_key: Mapped[str] = mapped_column(String(64), nullable=False)
    activite_label: Mapped[str] = mapped_column(String(128), nullable=False)
    niveau: Mapped[str] = mapped_column(String(32), nullable=False)
    sous_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avec_correction: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    matiere: Mapped[str | None] = mapped_column(String(64), nullable=True)
    objet: Mapped[str | None] = mapped_column(String(150), nullable=True)
    partagee: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='0')
    anonyme: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='0')
    texte_source: Mapped[str] = mapped_column(Text, nullable=False)
    resultat: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)


# ---------------------------------------------------------------------------
# Admin backoffice — Phase 0
# ---------------------------------------------------------------------------

class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(100), nullable=True)
    os: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    login_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def is_online(self) -> bool:
        delta = datetime.now(timezone.utc) - self.last_seen.replace(tzinfo=timezone.utc)
        return self.is_active and delta.total_seconds() < 90


class FailedLoginAttempt(Base):
    __tablename__ = "failed_login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    attempt_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AdminAlert(Base):
    __tablename__ = "admin_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class FeatureVote(Base):
    __tablename__ = "feature_votes"
    __table_args__ = (Index("ix_feature_votes_unique", "user_id", "feature_key", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    feature_key: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class FicheMatiere(Base):
    __tablename__ = "fiches_matieres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    matiere_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    statut: Mapped[str] = mapped_column(String(16), nullable=False, default="brouillon")  # brouillon | publie | a_reviser
    accroche: Mapped[str | None] = mapped_column(Text, nullable=True)
    pour_qui: Mapped[str | None] = mapped_column(Text, nullable=True)
    ameliorations: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ToolUsageLog(Base):
    __tablename__ = "tool_usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tool: Mapped[str] = mapped_column(String(32), nullable=False)  # sequence | optimiseur
    score_label: Mapped[str | None] = mapped_column(String(32), nullable=True)  # Bon | Moyen | À revoir
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class FewShotMilestone(Base):
    # Jalon « aSchool reconnaît votre façon de travailler » : posé UNE fois par couple
    # (prof, type d'activité) au franchissement du seuil few-shot. L'unique garantit le
    # one-shot durable (jamais rejoué, même si le compte retombe puis repasse le seuil).
    # Table neuve et vide → créée par create_all au démarrage, l'existant n'est pas touché.
    __tablename__ = "few_shot_milestones"
    __table_args__ = (Index("ix_few_shot_milestones_unique", "user_id", "activite_key", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activite_key: Mapped[str] = mapped_column(String(64), nullable=False)
    reached_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Refonte programmes — référentiel niveaux/matières (programme officiel)
# ---------------------------------------------------------------------------

class Cycle(Base):
    __tablename__ = "cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False)


class Niveau(Base):
    __tablename__ = "niveaux"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_id: Mapped[int] = mapped_column(Integer, ForeignKey("cycles.id"), nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(64), nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False)
    # true = niveau ayant reçu son VRAI référentiel (sélectionnable au profil) ;
    # false = pas encore traité (affiché « en cours », sélection bloquée par une modale).
    traite: Mapped[bool] = mapped_column(Boolean, default=False, server_default='0', nullable=False)


class Matiere(Base):
    __tablename__ = "matieres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(64), nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1', nullable=False)  # false = retirée du programme (historique conservé)


class MatiereNiveau(Base):
    """Programme officiel : quelle matière à quel niveau (paire valide)."""
    __tablename__ = "matiere_niveaux"
    __table_args__ = (Index("ix_matiere_niveaux_unique", "matiere_id", "niveau_id", "variante", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    matiere_id: Mapped[int] = mapped_column(Integer, ForeignKey("matieres.id"), nullable=False, index=True)
    niveau_id: Mapped[int] = mapped_column(Integer, ForeignKey("niveaux.id"), nullable=False, index=True)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1', nullable=False)  # false = paire retirée du programme (historique conservé)
    # '' = pas de variante ; sinon 'A' / 'B'… — même matière déclinée au même niveau (cf. règle
    # « Matière, variante, spécialité »). NOT NULL default '' : l'unique protège partout sans piège NULL.
    variante: Mapped[str] = mapped_column(String(32), nullable=False, server_default='', default='')


class UserEnseignement(Base):
    """Ce que CE prof enseigne : un sous-ensemble du programme (paire valide)."""
    __tablename__ = "user_enseignements"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    matiere_niveau_id: Mapped[int] = mapped_column(Integer, ForeignKey("matiere_niveaux.id"), primary_key=True)


class Referentiel(Base):
    """Référentiel officiel d'un couple → collection ChromaDB + filtres de retrieval.

    Schéma PostgreSQL : id en IDENTITY, created_at DateTime/func.now().
    Clé d'identification = le COUPLE (niveau_id, matiere_id), jamais niveau_id seul.
    matiere_id NULL = le référentiel couvre TOUT le niveau (toutes ses matières)."""
    __tablename__ = "referentiels"
    __table_args__ = (UniqueConstraint("niveau_id", "matiere_id"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    niveau_id: Mapped[int] = mapped_column(Integer, ForeignKey("niveaux.id"), nullable=False)
    matiere_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("matieres.id"), nullable=True)
    nom_fixe: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    collection: Mapped[str] = mapped_column(Text, nullable=False)
    filtres: Mapped[str | None] = mapped_column(Text, nullable=True)
    fichier: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_doc: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class ReferentielChunk(Base):
    """Chunk d'un référentiel + son embedding (RAG sur PostgreSQL/pgvector — remplace ChromaDB).

    niveau/source NON dupliqués : récupérés par jointure via referentiel_id (cap relationnel).
    embedding_model = garde-fou : interdit de comparer un jour des vecteurs de modèles différents.
    Dimension 1024 (embeddings BGE-M3). Migration Alembic 384->1024 encore à écrire pour la
    vraie base / environnements neufs : le modèle est ici en avance sur les migrations commitées."""
    __tablename__ = "referentiel_chunks"
    __table_args__ = (
        Index("ix_referentiel_chunks_referentiel_id", "referentiel_id"),
        Index("ix_referentiel_chunks_ref_option", "referentiel_id", "option_ab"),
        Index("ix_referentiel_chunks_embedding_hnsw", "embedding",
              postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"}),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    referentiel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    option_ab: Mapped[str] = mapped_column(Text, nullable=False)
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    texte: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1024), nullable=False)
    embedding_model: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
