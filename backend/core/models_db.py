from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Float, DateTime, Index, Text, ForeignKey, UniqueConstraint, Identity, func, text
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
    # Type d'activité référencé par sa CLÉ ÉTRANGÈRE (l'id), jamais par une chaîne recopiée (règle 4).
    activite_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("types_activite.id"), nullable=False, index=True)
    activite_label: Mapped[str] = mapped_column(String(128), nullable=False)  # libellé FIGÉ (instantané d'historique)
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
    __table_args__ = (Index("ix_few_shot_milestones_unique", "user_id", "activite_type_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activite_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("types_activite.id"), nullable=False)
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
    # 255 : les intitulés officiels dépassent 64 (cas réel : 70 car. dans le référentiel
    # ergothérapie). Cette colonne EST la limite — les gardes la lisent ici (zéro copie).
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
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
    # Motif de FORÇAGE d'une validation malgré une alerte de la vérification au dépôt (couple lu par
    # l'IA ≠ couple déclaré). NULL = validation normale (aucun forçage). Renseigné = l'admin a passé
    # outre, motif tracé EN BASE (+ log). DONNÉE MÉTIER EN BASE.
    forcage_motif: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Verdict de l'IA sur le couple, rendu AU DÉPÔT (verifier_couple) et FIGÉ à la validation : JSON
    # {correspond: bool, niveau_lu: str, raison: str}. Sans lui, l'analyse de l'IA (« le document est
    # intitulé Cycle 4 · 5e… ») serait perdue. Donnée NEUVE (n'existe nulle part ailleurs) → EN BASE,
    # sur la ligne du document, comme forcage_motif. NULL = non renseigné (ancien dépôt / non transmis).
    verif_couple: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Texte ÉPURÉ du document — LE texte de travail. Calculé UNE SEULE FOIS à la validation du
    # dépôt (porte rag.extraction, règles d'épuration du jour) puis FIGÉ ici : toutes les étapes
    # suivantes le LISENT (matières, prompt de découpe, découpe, re-découpe). Plus aucune
    # ré-extraction du PDF après la validation — une règle d'épuration ajoutée plus tard ne
    # touche donc JAMAIS un dépôt passé. Le PDF sur disque reste la pièce d'origine intacte.
    texte_epure: Mapped[str | None] = mapped_column(Text, nullable=True)
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


class ActiviteType(Base):
    """Catalogue GLOBAL des types d'activité — défini UNE seule fois, partagé (crèche → doctorat).

    Un type d'activité N'APPARTIENT PAS à un référentiel : il vit dans ce catalogue. Le référentiel
    (PDF d'un couple) ne fait que COCHER/DÉCOCHER quels types s'appliquent, via la table de liaison
    `referentiel_types_activite` (relation N–N). Le PROMPT n'est PAS ici : il est SPÉCIFIQUE au couple
    (référentiel × type) et vit sur la liaison `referentiel_types_activite.prompt`, à un seul endroit
    — un type seul ne porte aucun prompt. Le type est identifié par son `id` (plus de slug `key`) ;
    l'anti-doublon du catalogue se fait par `label` (insensible à la casse), comme `matieres.nom`.
    `is_default` = le type de repli « Activité d'apprentissage », affiché quand un couple n'a coché
    aucun type (ou n'a pas de référentiel) ; UN SEUL défaut garanti par l'index partiel `ux_default`.
    Précisions et paramètres du type vivent dans leurs tables filles `type_precisions` /
    `type_parametres` (une ligne par valeur), plus dans un blob JSON."""
    __tablename__ = "types_activite"
    __table_args__ = (
        Index("ux_default", "is_default", unique=True, postgresql_where=text("is_default")),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", default=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    # Origine du type dans le catalogue : 'systeme' (fourni par aSchool, pré-rempli) | 'admin' (ajouté
    # à la main via « Ajouter ») | 'ia' (issu d'une suggestion IA). Sert de source du LIEN quand l'admin
    # COCHE le type — le badge affiché = l'origine, jamais « qui a coché ».
    origine: Mapped[str] = mapped_column(String(16), nullable=False, server_default="systeme", default="systeme")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class ReferentielActiviteType(Base):
    """Liaison référentiel ↔ type d'activité (N–N) : LE « coché / décoché ».

    Le référentiel (PDF d'un couple) active/désactive des types du catalogue `types_activite` :
    une ligne = « ce type est proposé pour ce couple ». `actif` = coché ou non (l'admin décoche sans
    supprimer). `source` = origine de la coche : 'ia' (détectée dans le PDF) ou 'admin' (ajout manuel).
    CASCADE des DEUX côtés : supprimer le référentiel OU le type retire les liaisons. Unicité
    (referentiel_id, activite_type_id) : un type ne peut être coché qu'une fois par référentiel."""
    __tablename__ = "referentiel_types_activite"
    __table_args__ = (
        UniqueConstraint("referentiel_id", "activite_type_id", name="uq_ref_activite_type"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    referentiel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False, index=True)
    activite_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("types_activite.id", ondelete="CASCADE"), nullable=False, index=True)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    source: Mapped[str] = mapped_column(String(16), nullable=False)   # origine du LIEN : 'ia' | 'admin' | 'systeme'
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    # Prompt de génération de CE type POUR CE couple (référentiel × type) — une seule place, zéro copie.
    # Écrit automatiquement au coche (généré), réécrit à l'édition. Le décoche ne le touche pas (il reste).
    # Contient les deux emplacements {texte} (idée du prof) et {referentiel} (programme officiel). Vide = pas encore généré.
    prompt: Mapped[str] = mapped_column(Text, nullable=False, server_default="", default="")


class ReferentielTypePrecision(Base):
    """Précision d'un type d'activité POUR UN COUPLE — fille de la liaison `referentiel_types_activite`.

    Contrairement à `type_precisions` (catalogue GLOBAL, même valeur crèche→doctorat), ici la précision
    est PROPRE AU COUPLE × TYPE : elle pend sur la ligne de liaison (comme le `prompt`), donc « exploration
    sensorielle » n'existe que pour le couple qui l'a saisie — le doctorat n'hérite plus du vocabulaire
    crèche. `source` = 'admin' (saisie manuelle) | 'ia' (proposée). CASCADE : supprimer la liaison retire
    ses précisions. UNIQUE (referentiel_activite_type_id, libelle) : pas de doublon dans un couple×type."""
    __tablename__ = "referentiel_type_precisions"
    __table_args__ = (
        UniqueConstraint("referentiel_activite_type_id", "libelle", name="uq_ref_type_precisions_lien_libelle"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    referentiel_activite_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("referentiel_types_activite.id", ondelete="CASCADE"), nullable=False, index=True)
    libelle: Mapped[str] = mapped_column(String(128), nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    source: Mapped[str] = mapped_column(String(16), nullable=False, server_default="admin", default="admin")


class TypePrecision(Base):
    """Précision d'un type d'activité — UNE ligne par choix offert au prof (ex. « dictée »).

    Remplace l'ancien blob JSON `types_activite.sous_types` : une donnée = une ligne, en base, avec
    contrôle (règle 4). Un type a 0..N précisions ; à la génération, le prof en choisit une (menu
    « Précision »). `source` = provenance de la ligne ('systeme' pré-rempli | 'admin' saisie manuelle |
    'ia' proposée par l'analyse), même logique que `ReferentielActiviteType.source`. CASCADE : supprimer
    le type retire ses précisions. UNIQUE (type_activite_id, libelle) : pas de doublon dans un type."""
    __tablename__ = "type_precisions"
    __table_args__ = (
        UniqueConstraint("type_activite_id", "libelle", name="uq_type_precisions_type_libelle"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    type_activite_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("types_activite.id", ondelete="CASCADE"), nullable=False, index=True)
    libelle: Mapped[str] = mapped_column(String(128), nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    source: Mapped[str] = mapped_column(String(16), nullable=False, server_default="systeme", default="systeme")


class TypeParametre(Base):
    """Paramètre saisi qu'un type d'activité réclame — UNE ligne par paramètre (ex. « nb » = nombre
    de questions).

    Remplace l'ancien blob JSON `types_activite.params` : une donnée = une ligne, en base, avec contrôle
    (règle 4). Un type a 0..N paramètres ; leur présence déclenche un champ de saisie côté prof (ex. `nb`
    → champ « Nombre de questions »). `source` = provenance ('systeme' | 'admin' | 'ia'). CASCADE :
    supprimer le type retire ses paramètres. UNIQUE (type_activite_id, cle) : pas de doublon dans un type."""
    __tablename__ = "type_parametres"
    __table_args__ = (
        UniqueConstraint("type_activite_id", "cle", name="uq_type_parametres_type_cle"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    type_activite_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("types_activite.id", ondelete="CASCADE"), nullable=False, index=True)
    cle: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False, server_default="systeme", default="systeme")
