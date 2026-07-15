from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Float, DateTime, Index, Text, ForeignKey, UniqueConstraint, Identity, func
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
    statut: Mapped[str] = mapped_column(String(16), ForeignKey("feedback_statuts.code"), nullable=False, default="nouveau")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    attachment_path: Mapped[str | None] = mapped_column(String(500), nullable=True)


class FeedbackStatut(Base):
    """Catalogue des statuts de feedback (donnée de référence, EN BASE). Source unique :
    les codes ASSIGNABLES = toutes les lignes ; la colonne `modifiable` porte la notion
    SOURCE (statut dans lequel l'auteur peut encore éditer son feedback), distincte des
    statuts assignables. `feedbacks.statut` a une FK vers `code` : la base est l'autorité."""
    __tablename__ = "feedback_statuts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    modifiable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Setting(Base):
    """Table de configuration du projet (paramètres clé / valeur), équivalent-en-base d'un
    fichier de config. Consultée depuis l'écran admin « Paramètres »."""
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


class MatiereCandidate(Base):
    """Matières candidates d'un couple (cycle+niveau) — proposition à valider par l'admin.

    Liste de noms de matières proposée (aujourd'hui préparée en DEV, cible = app via Groq) et
    affichée dans la table de l'écran Référentiels : l'admin coche celles à ajouter → crée les
    paires MatiereNiveau. DONNÉE MÉTIER → elle vit EN BASE (plus de fichier matieres-candidates.json).
    Une ligne par niveau (le niveau implique son cycle) ; `matieres` = tableau JSON de noms."""
    __tablename__ = "matieres_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    niveau_id: Mapped[int] = mapped_column(Integer, ForeignKey("niveaux.id"), nullable=False, unique=True, index=True)
    matieres: Mapped[str] = mapped_column(Text, nullable=False, server_default="[]", default="[]")  # JSON array de noms


class AiModele(Base):
    """Modèles LLM texte offerts à l'admin, rattachés à leur fournisseur. DONNÉE MÉTIER → EN BASE
    (plus de liste `SUPPORTED_AI_MODELS` en dur). Une ligne = un modèle d'un fournisseur ; l'écran
    admin propose, pour le fournisseur choisi, ses modèles `actif`, le `recommande` en premier.
    `modele` = l'id exact de l'API (ex. « claude-sonnet-5 »)."""
    __tablename__ = "ai_modeles"
    __table_args__ = (
        UniqueConstraint("fournisseur", "modele", name="uq_ai_modeles_fournisseur_modele"),
        Index("ix_ai_modeles_fournisseur", "fournisseur"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Lien base : un modèle appartient à un fournisseur connu (FK -> ai_fournisseurs.code).
    fournisseur: Mapped[str] = mapped_column(String(50), ForeignKey("ai_fournisseurs.code"), nullable=False)  # "groq" / "anthropic"
    modele: Mapped[str] = mapped_column(String(100), nullable=False)        # id API exact
    label: Mapped[str] = mapped_column(String(150), nullable=False)         # affichage admin
    recommande: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", default=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)


class AiFournisseur(Base):
    """Fournisseurs LLM offerts à l'admin. DONNÉE MÉTIER → EN BASE (plus de listes
    `SUPPORTED_AI_PROVIDERS` / `ALL_AI_PROVIDERS` en dur). Une ligne = un fournisseur ;
    l'écran admin propose ceux qui sont `actif` (opérationnels), les autres apparaissent
    grisés « pas encore disponible ». `code` = l'identifiant technique du moteur
    (« groq »/« anthropic ») ; `cle_env` = le NOM de la variable d'env de sa clé TEXTE
    (la valeur — le secret — reste dans le .env, jamais en base)."""
    __tablename__ = "ai_fournisseurs"
    __table_args__ = (
        UniqueConstraint("code", name="uq_ai_fournisseurs_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)          # "groq" / "anthropic"
    label: Mapped[str] = mapped_column(String(150), nullable=False)        # affichage admin
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    cle_env: Mapped[str] = mapped_column(String(100), nullable=False, server_default="", default="")  # nom var env clé texte


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
    # Seuil de pertinence RAG (1 - distance cosinus) par référentiel — un chunk sous ce seuil
    # n'ancre jamais une génération. Donnée métier EN BASE (plus de constante SCORE_MIN en dur).
    score_min: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.30")
    fichier: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_doc: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Règle de découpe du couple (objet à deux faces) — DONNÉE MÉTIER EN BASE (plus de fichier
    # regle-decoupe.json). L'admin valide sur `regle_explication` (face claire, sans code) ; la fiche
    # exécute `regle_motif` (regex) à l'ingestion. `regle_valide` : découpage REFUSÉ tant que False.
    regle_explication: Mapped[str | None] = mapped_column(Text, nullable=True)
    regle_motif: Mapped[str | None] = mapped_column(Text, nullable=True)
    regle_depose_par: Mapped[str | None] = mapped_column(Text, nullable=True)   # 'dev' | 'admin'
    regle_valide: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0", default=False)
    # Arbitrage des cas flous du couple : JSON {libellé d'âge flou: [bandes]} — DONNÉE MÉTIER EN BASE
    # (plus de fichier arbitrage-flou.json). NULL/absent = aucun cas flou tranché.
    arbitrage: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Verdict d'analyse amont de l'IA, calculé UNE fois puis relu (aperçu ET ingestion lisent le
    # MÊME verdict → jamais deux appels IA divergents) : JSON = liste des libellés jugés douteux.
    # NULL = pas encore analysé (calculé au 1er besoin) ; vidé quand la règle du couple change.
    doutes_ia: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Prompt de découpe du couple — GÉNÉRÉ PAR L'IA (méta-prompt en base), puis affiché, corrigé et
    # validé par l'admin. DONNÉE MÉTIER EN BASE (aucun prompt écrit en dur dans le code).
    # `prompt_decoupe_valide` : la découpe REFUSE de tourner tant que False (garde-fou).
    prompt_decoupe: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_decoupe_valide: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0", default=False)
    # « Découpe validée » : l'admin a CONTRÔLÉ le résultat de la découpe et l'a accepté = le référentiel
    # est ARRIVÉ AU BOUT de la procédure. C'est ce booléen (et lui seul) qui fait passer la puce du menu
    # au VERT. Écrit par le bouton final « Valider le découpage ». Donnée NEUVE (n'existe nulle part
    # ailleurs) → EN BASE, sur la ligne du document. false = pas encore validée (puce rouge).
    decoupe_valide: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0", default=False)
    # Motif de FORÇAGE d'une validation malgré une alerte des vérifications au dépôt (couple lu par
    # l'IA ≠ couple déclaré, ou famille absente de famille_couples). NULL = validation normale (aucun
    # forçage). Renseigné = l'admin a passé outre, motif tracé EN BASE (+ log). DONNÉE MÉTIER EN BASE.
    forcage_motif: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Verdict de l'IA sur le couple, rendu AU DÉPÔT (verifier_couple) et FIGÉ à la validation : JSON
    # {correspond: bool, niveau_lu: str, raison: str}. Sans lui, l'analyse de l'IA (« le document est
    # intitulé Cycle 4 · 5e… ») serait perdue. Donnée NEUVE (n'existe nulle part ailleurs) → EN BASE,
    # sur la ligne du document, comme forcage_motif. NULL = non renseigné (ancien dépôt / non transmis).
    verif_couple: Mapped[str | None] = mapped_column(Text, nullable=True)
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


class ArbitrageDemande(Base):
    """TEMPS 2 de l'arbitrage : cas flou où l'admin a demandé l'avis d'un pro par mail et ATTEND la
    réponse. La DÉCISION d'arbitrage vit en base (`referentiels.arbitrage`) ; ici on ne stocke QUE le
    statut « en attente » — donnée saisie via l'app, cap « tout en base ». Une ligne = un cas flou
    (référentiel + libellé) en attente ; « en attente » = présence de la ligne. La ligne est supprimée
    quand l'admin tranche le cas (endpoint arbitrage-flou). Ancrée au MÊME référentiel que la décision
    (referentiel_id), jamais au niveau — un seul point d'ancrage. PROVISOIRE : absorbé plus tard par la
    gestion unifiée des mails (item 65)."""
    __tablename__ = "arbitrage_demandes"
    __table_args__ = (UniqueConstraint("referentiel_id", "label", name="uq_arbitrage_demandes_ref_label"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    referentiel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)                 # libellé d'âge flou (= age_label de l'aperçu)
    destinataire: Mapped[str] = mapped_column(String(255), nullable=False)   # adresse du pro sollicité
    demande_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class Famille(Base):
    """Famille de structure d'un référentiel (6 types) : ce que le document EST.
    Classification pure — ne pilote pas la découpe. DONNÉE MÉTIER → EN BASE."""
    __tablename__ = "familles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # État interne (jamais renvoyé par l'IA) : la famille de rejet, à exclure de la classification.
    # Le code ne connaît QUE ce drapeau, jamais le nom/id de la ligne (cap « aucun cas particulier »).
    rejet: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='false', default=False)


class FamilleCouple(Base):
    """Couple (niveau) rattaché à une famille de structure — décidé par l'humain (admin/dev),
    jamais écrit par l'IA. Le cycle se déduit du niveau (niveaux.cycle_id), donc pas stocké ici
    (zéro redondance). UNIQUE (famille_id, niveau_id) : un niveau ne s'inscrit qu'une fois par famille."""
    __tablename__ = "famille_couples"
    __table_args__ = (UniqueConstraint("famille_id", "niveau_id", name="uq_famille_couples_famille_niveau"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    famille_id: Mapped[int] = mapped_column(Integer, ForeignKey("familles.id"), nullable=False, index=True)
    niveau_id: Mapped[int] = mapped_column(Integer, ForeignKey("niveaux.id"), nullable=False, index=True)
