from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Float, Numeric, DateTime, Index, Text, ForeignKey, UniqueConstraint, Identity, func, text
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from backend.core.database import Base
from backend.core.horloge import maintenant_utc


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    subject_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("matieres.id"), nullable=True)   # RÈGLE 4 : matière rangée UNIQUEMENT par CLÉ (le nom vit dans `matieres`, get)
    prenom: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nom: Mapped[str | None] = mapped_column(String(64), nullable=True)
    niveau_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("niveaux.id"), nullable=True)   # RÈGLE 4 : niveau rangé UNIQUEMENT par CLÉ (le nom vit dans `niveaux`, get)
    langue_lv: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1', nullable=False)
    # Couple de TRAVAIL (écran Créer, « Changer niveau et/ou matière ») — NULL = couple du profil.
    # C'est LA donnée que le serveur lit pour générer ; rangé UNIQUEMENT par CLÉ (get sur
    # matieres/niveaux pour le nom), jamais recopié côté écran ni en texte.
    travail_matiere_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("matieres.id"), nullable=True)
    travail_niveau_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("niveaux.id"), nullable=True)
    # Visite guidée de l'écran Créer déjà montrée ? En base (pas dans le navigateur) :
    # un autre appareil doit le savoir aussi. False → elle se lance toute seule une fois.
    guide_creer_vu: Mapped[bool] = mapped_column(Boolean, default=False, server_default='0', nullable=False)


class CahierProf(Base):
    """Cahier des charges INTERNE d'un prof (PDF déposé par lui, propre à son école/structure).
    UN seul par prof pour l'instant (user_id unique) : re-déposer REMPLACE. Le PDF vit sur disque
    (data/uploads/cahiers/<user_id>/cahier.pdf) ; ici on garde le NOM d'origine (affiché au prof)
    + la date + le TEXTE ÉPURÉ (le texte de travail lu par la génération)."""
    __tablename__ = "cahiers_prof"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    fichier: Mapped[str] = mapped_column(String(255), nullable=False)   # nom d'origine du PDF déposé (affiché au prof)
    # Texte ÉPURÉ du cahier — LE texte de travail. Extrait UNE SEULE FOIS au dépôt (porte unique
    # rag.extraction, comme referentiels.texte_epure) puis FIGÉ ici : la génération le LIT (get,
    # zéro copie) pour appliquer les règles de l'école par-dessus le programme officiel. NULL =
    # rien d'exploitable (ancien dépôt / PDF illisible) → la génération se fait sans cahier.
    texte_epure: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="feedback")  # feedback | notation
    message: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    statut: Mapped[str] = mapped_column(String(16), ForeignKey("feedback_statuts.code"), nullable=False, default="nouveau")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    attachment_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # D'où le feedback est parti (« Écran Créer une activité · Français × 6e ») — fait
    # d'événement figé à l'envoi, jamais retouché à l'édition.
    contexte: Mapped[str | None] = mapped_column(String(160), nullable=True)


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
    # La phrase qui explique le statut au prof (écran d'aide) : elle appartient au statut,
    # pas à l'écran — sinon elle se recopie et diverge.
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class FeedbackMessage(Base):
    """Un message de l'ÉCHANGE qui suit un retour — la réponse de l'admin, puis la suite.

    `feedbacks.message` reste le message d'OUVERTURE (celui que le prof écrit et peut encore
    modifier selon `feedback_statuts.modifiable`) : il n'est pas recopié ici. Cette table ne
    porte que ce qui vient APRÈS, dans l'ordre de `created_at`.

    `auteur_est_admin` est un booléen et non une clé vers `users` : l'administrateur n'a pas
    de compte dans l'application (circuit de connexion séparé, aucune ligne dans `users`), et
    un échange n'a que deux côtés. Le nom affiché — « Vous », « aSchool », l'e-mail du prof —
    se calcule à la lecture selon qui regarde : c'est de la présentation, pas une donnée à
    ranger. Le prof est déjà identifié par `feedbacks.user_id` (get, zéro copie).
    """
    __tablename__ = "feedback_messages"
    __table_args__ = (
        Index("ix_feedback_messages_feedback_id_created_at", "feedback_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feedback_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("feedbacks.id", ondelete="CASCADE"), nullable=False,
    )
    auteur_est_admin: Mapped[bool] = mapped_column(Boolean, nullable=False)
    corps: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)


class Incident(Base):
    """Incident TECHNIQUE de génération (échec côté IA) — capturé automatiquement au plantage, que le
    prof le signale ou non. L'admin y lit CE QUI a réellement échoué (erreur, endpoint, fournisseur,
    paramètres tentés), là où l'écran du prof ne montre qu'un message humain (RÈGLE 23). Les champs
    métier (matiere/niveau/type/consigne) sont un INSTANTANÉ figé de la tentative — journal historique,
    même logique que feedbacks.contexte, jamais une copie vivante qui divergerait. `feedback_id` relie
    l'incident au message du prof s'il clique « signaler » (sinon NULL : l'incident existe quand même)."""
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ref: Mapped[str] = mapped_column(String(24), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)
    endpoint: Mapped[str] = mapped_column(String(120), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error: Mapped[str] = mapped_column(Text, nullable=False)
    matiere: Mapped[str | None] = mapped_column(String(120), nullable=True)
    niveau: Mapped[str | None] = mapped_column(String(120), nullable=True)
    type_activite: Mapped[str | None] = mapped_column(String(120), nullable=True)
    consigne: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # SET NULL : l'incident TECHNIQUE survit à la disparition du feedback (et donc du compte) —
    # il perd son lien, pas son existence. Sans ça, supprimer un prof dont un feedback porte un
    # incident échouait en violation de clé étrangère.
    feedback_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("feedbacks.id", ondelete="SET NULL"), nullable=True, index=True)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)


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
    envoye_le: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False, index=True)


# (ActiviteSauvegardee et SequenceSauvegardee — l'ancien monde — ont été DROPPÉES le
# 30/07/2026, migration du démantèlement : Mes contenus est LE produit, comptage et
# affichage vivent sur les tables neuves ci-dessous.)


# ---------------------------------------------------------------------------
# « Mes contenus » — le modèle playlist à 3 niveaux : séquence ⊃ séances ⊃ activités.
# Le parent est TOUJOURS nullable : une séance ou une activité peut vivre seule
# (« Non rangée »).
# ---------------------------------------------------------------------------

class Sequence(Base):
    """Séquence — le conteneur du haut. Contient des séances ordonnées (Seance.position).
    Le « résultat » d'une séquence N'EST PAS un texte : c'est SES SÉANCES (le plan généré
    devient des lignes `seances` rattachées) — donc pas de colonne resultat ni de table de
    versions. Rien de dérivable n'est stocké : la durée totale se calcule depuis les
    séances, leur nombre se compte (zéro copie)."""
    __tablename__ = "sequences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # Titre = l'OBJECTIF GÉNÉRAL saisi par le prof (zone d'apport complète, comme le thème
    # de la séance) → Text, jamais borné (leçon du bug de troncature des titres de séance).
    titre: Mapped[str] = mapped_column(Text, nullable=False)
    # Le FORMULAIRE de l'écran Séquence, en entier : chaque champ vit en base (reprise
    # complète, même moule que Seance).
    contexte: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    ampleur: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")      # ampleur souhaitée, libre : « une dizaine de séances », « sur deux ans »…
    competences: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")  # liste JSON de chaînes
    matiere: Mapped[str | None] = mapped_column(String(64), nullable=True)
    niveau: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, onupdate=maintenant_utc, nullable=False)


class SeanceMode(Base):
    """Les modes de séance offerts au prof (donnée de référence, EN BASE). Source unique : le
    serveur valide sur cette table, l'écran Séance affiche ces lignes, la liste « Mes séances »
    y lit ses libellés — plus de troisième copie qui diverge.

    `code` EST la clé du prompt (`seance_<code>` dans le registre) : renommer le `label` ne
    touche à rien. `description` = la phrase affichée sous le libellé, dans le choix du mode."""
    __tablename__ = "seance_modes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1', nullable=False)


class SeanceStyle(Base):
    """Les styles de production d'une séance (même moule que SeanceMode). `code` EST la clé du
    prompt de la couche de style (`seance_style_<code>`)."""
    __tablename__ = "seance_styles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1', nullable=False)


class LangueLv(Base):
    """Les langues vivantes proposées au prof dont la matière `demande_langue`. `label` est ce
    qui s'écrit dans `users.langue_lv` (colonne texte) : le catalogue sert des libellés, aucune
    donnée existante n'est à réécrire. `code` est là pour la clé étrangère du jour où."""
    __tablename__ = "langues_lv"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1', nullable=False)


class Seance(Base):
    """Séance — le niveau du milieu. `sequence_id` nullable = séance libre ; SET NULL à la
    suppression de la séquence : les séances redeviennent « non rangées », jamais détruites."""
    __tablename__ = "seances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sequence_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sequences.id", ondelete="SET NULL"), nullable=True, index=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)  # ordre dans la séquence
    # Titre = le THÈME saisi par le prof (zone libre : dictée, import, « Propose-moi un
    # thème »…) → Text, jamais borné (un thème réel dépasse facilement 300 caractères).
    titre: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    matiere: Mapped[str | None] = mapped_column(String(64), nullable=True)
    niveau: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duree_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Le FORMULAIRE de l'écran Séance, en entier : chaque champ vit en base (reprise complète).
    mode: Mapped[str | None] = mapped_column(String(32), nullable=True)        # standard / remediation / approfondissement / autonomie
    competences: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")  # liste JSON de chaînes
    materiel: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    esquisse: Mapped[str] = mapped_column(Text, nullable=False, default="{}", server_default="{}")     # JSON {a, b, c} — l'esquisse A/B/C du prof
    contraintes: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    style: Mapped[str | None] = mapped_column(String(32), nullable=True)       # classique / ludique / structure / concis
    resultat: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, onupdate=maintenant_utc, nullable=False)


class SeanceVersion(Base):
    """Version restaurable d'une séance (règle 0, même moule qu'`activite_versions`) : chaque
    génération EMPILE une photo — on n'écrase jamais. CASCADE : les versions suivent leur séance."""
    __tablename__ = "seance_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seance_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("seances.id", ondelete="CASCADE"), nullable=False, index=True)
    # Mêmes deux jalons que l'activité — 'generation' et 'restauration', et pas de troisième :
    # le déroulé d'une séance ne s'édite pas davantage dans l'application. Le pourquoi est
    # écrit une seule fois, sur `ActiviteVersion.jalon` juste en dessous.
    jalon: Mapped[str] = mapped_column(String(32), nullable=False, default="generation", server_default="generation")
    style: Mapped[str | None] = mapped_column(String(32), nullable=True)
    resultat: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)


class Activite(Base):
    """Activité du monde « Mes contenus » — la brique de base du modèle playlist.

    Table NEUVE, règle 0 NATIVE : l'activité est écrite en base à la génération même
    (auto-save), chaque jalon fige une version dans `activite_versions`. `seance_id`
    nullable = activité libre (« non rangée ») ; SET NULL si sa séance disparaît.
    Ne pas confondre avec `activites_sauvegardees` (l'ancien monde, qui vit sa vie
    dans Mes outils jusqu'à sa suppression finale)."""
    __tablename__ = "activites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    seance_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("seances.id", ondelete="SET NULL"), nullable=True, index=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Type référencé par son id au catalogue (types_activite) + libellé FIGÉ (instantané).
    activite_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("types_activite.id"), nullable=False, index=True)
    activite_label: Mapped[str] = mapped_column(String(128), nullable=False)
    sous_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avec_correction: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='0')
    objet: Mapped[str | None] = mapped_column(String(150), nullable=True)
    matiere: Mapped[str | None] = mapped_column(String(64), nullable=True)
    niveau: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ton: Mapped[str | None] = mapped_column(String(32), nullable=True)
    texte_source: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    resultat: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")   # ÉTAT COURANT (auto-save)
    statut: Mapped[str] = mapped_column(String(32), nullable=False, default="brouillon", server_default="brouillon")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, onupdate=maintenant_utc, nullable=False)


class ActiviteVersion(Base):
    """Version (photo restaurable) d'une activité du monde neuf — un jalon = une version,
    l'historique S'EMPILE, on n'écrase jamais (règle 0). CASCADE : les versions suivent
    leur activité."""
    __tablename__ = "activite_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activite_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("activites.id", ondelete="CASCADE"), nullable=False, index=True)
    # DEUX JALONS, ET DEUX SEULEMENT :
    #   'generation'    le prof a (re)généré — POST à la première, PUT aux suivantes.
    #   'restauration'  le prof est revenu à une version précédente ; ce retour s'empile à son
    #                   tour, d'où la possibilité de revenir en arrière d'un retour en arrière.
    #
    # IL N'Y A PAS DE TROISIÈME JALON, et ce n'est pas un manque : le résultat NE S'ÉDITE PAS
    # dans l'application. C'est un choix produit, déjà annoncé au prof dans l'aide de l'écran
    # Créer (frontend/src/utils/aideCreer.js) — pour retoucher une question ou corriger une
    # coquille, il télécharge l'activité en .txt ou Word et la modifie dans son traitement de
    # texte. Aucun écran n'offre d'édition, aucun code n'écrit un autre jalon.
    #
    # Ce commentaire annonçait « (puis 'edition', 'restauration'…) » et JALON_LABELS portait un
    # libellé « Modification à la main » pour un jalon que rien n'écrivait. Le libellé est parti
    # le 02/08/2026. La raison est écrite ici pour qu'on ne le remette pas : ouvrir l'édition
    # sans toucher au PUT de régénération étiquetterait la retouche « Génération » — un mensonge
    # inscrit dans l'historique du prof, pire que l'absence.
    jalon: Mapped[str] = mapped_column(String(32), nullable=False)
    ton: Mapped[str | None] = mapped_column(String(32), nullable=True)
    resultat: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)


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
    login_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)
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
    attempt_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)


class AdminAlert(Base):
    __tablename__ = "admin_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class FeatureVotable(Base):
    """Catalogue des fonctionnalités votables de l'écran « Bientôt disponible » (donnée de
    référence, EN BASE). Source unique : l'écran, le serveur et l'admin lisent CETTE table —
    plus aucune liste en dur. `actif=false` retire la carte de l'écran sans perdre les votes.
    `icone` = nom d'un pictogramme du mapping front (le dessin SVG reste de l'affichage).
    `feature_votes.feature_key` a une FK vers `code` : la base est l'autorité."""
    __tablename__ = "features_votables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    categorie: Mapped[str] = mapped_column(String(32), nullable=False)
    icone: Mapped[str] = mapped_column(String(32), nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FeatureVote(Base):
    __tablename__ = "feature_votes"
    __table_args__ = (Index("ix_feature_votes_unique", "user_id", "feature_key", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # CASCADE : un vote n'a aucune vie sans son prof (voir migration e4b8c2d6a1f7).
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_key: Mapped[str] = mapped_column(String(64), ForeignKey("features_votables.code"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)


class ToolUsageLog(Base):
    __tablename__ = "tool_usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # CASCADE : le journal d'usage disparaît avec son prof (voir migration e4b8c2d6a1f7).
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tool: Mapped[str] = mapped_column(String(32), nullable=False)  # consigne | ambiguites
    score_label: Mapped[str | None] = mapped_column(String(32), nullable=True)  # Bon | Moyen | À revoir
    created_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)


class FewShotMilestone(Base):
    # Jalon « aSchool reconnaît votre façon de travailler » : posé UNE fois par couple
    # (prof, type d'activité) au franchissement du seuil few-shot. L'unique garantit le
    # one-shot durable (jamais rejoué, même si le compte retombe puis repasse le seuil).
    # Table neuve et vide → créée par create_all au démarrage, l'existant n'est pas touché.
    __tablename__ = "few_shot_milestones"
    __table_args__ = (Index("ix_few_shot_milestones_unique", "user_id", "activite_type_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # CASCADE : le jalon n'a aucune vie sans son prof (voir migration e4b8c2d6a1f7).
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activite_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("types_activite.id"), nullable=False)
    reached_at: Mapped[datetime] = mapped_column(DateTime, default=maintenant_utc, nullable=False)


# ---------------------------------------------------------------------------
# Refonte programmes — référentiel niveaux/matières (programme officiel)
# ---------------------------------------------------------------------------

class Cycle(Base):
    __tablename__ = "cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False)
    # Prompt de lecture des MATIÈRES, propre à ce cycle. Écrit par l'IA à partir d'un référentiel
    # du cycle (méta-prompt `prompt_meta_matieres`), relu et validé par l'admin, puis réutilisé par
    # TOUS les référentiels du cycle : un cycle = une famille de documents bâtis pareil (tous les
    # BTS ont la même architecture, tous les programmes de collège aussi). NULL = pas encore écrit,
    # la détection retombe alors sur le prompt général `detecter_matieres`. DONNÉE MÉTIER EN BASE.
    prompt_matieres: Mapped[str | None] = mapped_column(Text, nullable=True)
    # false = prompt écrit mais pas encore relu par l'admin → il ne sert PAS (on reste sur le
    # prompt général). Seul un prompt VALIDÉ remplace le prompt général.
    prompt_matieres_valide: Mapped[bool] = mapped_column(Boolean, nullable=False,
                                                         server_default="0", default=False)
    # Prompt de DÉCOUPE du cycle — même raisonnement, même geste : l'ossature d'un référentiel
    # (activités, compétences, unités certificatives, ce qu'on écarte) est celle de toute la
    # famille ; seuls les identifiants changent d'un document à l'autre. Écrit par l'IA à partir
    # du premier référentiel du cycle (méta-prompt `prompt_meta_decoupe`), puis réutilisé par tous.
    # NULL = pas encore écrit. DONNÉE MÉTIER EN BASE.
    prompt_decoupe: Mapped[str | None] = mapped_column(Text, nullable=True)
    # false = écrit par l'IA, pas encore relu par l'admin. Comme pour les matières, le prompt SERT
    # dès qu'il existe : ce drapeau dit seulement s'il a été relu.
    prompt_decoupe_valide: Mapped[bool] = mapped_column(Boolean, nullable=False,
                                                        server_default="0", default=False)
    # Prompt de lecture des TYPES D'ACTIVITÉ, propre à ce cycle (05/08/2026). MÊME RÈGLE que les
    # deux précédents : la DONNÉE (le type) appartient au référentiel, la RECETTE (le prompt qui la
    # lit) appartient au cycle — une famille de documents bâtis pareil se lit avec la même recette.
    # Écrit par l'IA au premier référentiel du cycle (méta-prompt `prompt_meta_types`). NULL = pas
    # encore écrit, la détection retombe sur le prompt général `detecter_types_activite`.
    prompt_types: Mapped[str | None] = mapped_column(Text, nullable=True)
    # false = écrit par l'IA, pas encore relu par l'admin. Le prompt SERT dès qu'il existe.
    prompt_types_valide: Mapped[bool] = mapped_column(Boolean, nullable=False,
                                                      server_default="0", default=False)


class Niveau(Base):
    __tablename__ = "niveaux"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_id: Mapped[int] = mapped_column(Integer, ForeignKey("cycles.id"), nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(64), nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False)


class Matiere(Base):
    """Une matière DU référentiel qui la nomme — jamais un catalogue partagé entre diplômes.

    Le BTS CIEL a ses matières, la Terminale a les siennes, avec l'orthographe de LEUR document :
    deux « Mathématiques » dans deux référentiels sont deux matières distinctes, et elles ne se
    comparent jamais. D'où l'unicité sur (referentiel_id, nom) — et non sur le nom seul. La
    disparition du référentiel emporte ses matières (CASCADE) : une matière sans document qui la
    nomme n'a pas de sens.

    Les paires matière×niveau (table `matiere_niveaux`) n'existent plus : le référentiel connaît
    déjà son niveau, la paire faisait doublon. Sa `variante` (LV A/B) non plus — un document qui
    distingue LV1 et LV2 donne désormais deux matières."""
    __tablename__ = "matieres"
    __table_args__ = (UniqueConstraint("referentiel_id", "nom", name="uq_matieres_referentiel_nom"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referentiel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False, index=True)
    # 255 : les intitulés officiels dépassent 64 (cas réel : 70 car. dans le référentiel
    # ergothérapie). Cette colonne EST la limite — les gardes la lisent ici (zéro copie).
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1', nullable=False)  # false = retirée du programme (historique conservé)
    # PROPOSÉE par la détection au dépôt du PDF (false) vs RETENUE par l'admin (true). Le prof ne
    # voit QUE les matières validées : une proposition d'IA n'entre jamais dans ses menus toute
    # seule. Remplace la table `matieres_candidates`, qui doublait la liste à côté de celle-ci.
    validee: Mapped[bool] = mapped_column(Boolean, default=False, server_default='0', nullable=False)
    # « Cette matière porte une langue » : le prof choisit sa langue dans son profil, et la
    # génération l'injecte dans le prompt ({langue}). Un INDICATEUR, pas un libellé : jusqu'ici
    # le code comparait le nom à « Langues Vivantes (LV) » — la matière réelle s'appelant
    # « Langue vivante », le test était faux en silence. Renommer la matière ne casse plus rien.
    demande_langue: Mapped[bool] = mapped_column(Boolean, default=False, server_default='0', nullable=False)


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
    # Ce que CE modèle peut ÉCRIRE au plus (tokens) — le paramètre `max_tokens` envoyé tel quel au
    # fournisseur, d'où son nom : c'est le mot de l'API, celui des erreurs (« max_tokens=5000 ») et
    # celui de l'écran. NULL = pas de valeur propre, celle du fournisseur s'applique. Ce n'est pas
    # un réglage de confort : Infomaniak REFUSE la requête (422) au-delà de 5 000, sans rien
    # générer — cf. get_max_tokens_modele.
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Fenêtre TOTALE du modèle (entrée + sortie). Deux bornes distinctes, qu'on a confondues une
    # fois : `max_tokens` limite ce que le modèle ÉCRIT, `contexte_max` ce qu'il peut TENIR. Un
    # référentiel entier pèse ~46 000 tokens — au-delà de la fenêtre, le fournisseur refuse en 400
    # après avoir fait attendre. NULL = fenêtre inconnue, aucun contrôle en amont.
    contexte_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Sortie contrainte (json_schema / output_config) et flux. Vrais pour les trois fournisseurs
    # d'aujourd'hui — vérifiés en appelant chacun ; la colonne existe pour le modèle qui ne saura pas.
    supporte_schema: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    supporte_stream: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    # `temperature` : les Claude Opus 4.x et les modèles 5 la REJETTENT (400). C'était écrit en dur
    # dans le moteur, deux fois, au nom du fournisseur entier — donc invisible pour l'admin, qui
    # réglait une valeur silencieusement jetée. La contrainte tient au MODÈLE : elle se déclare ici.
    supporte_temperature: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    # Tarifs $/million de tokens, pour l'estimation de coût de l'écran statistiques. VIDES tant
    # qu'ils n'ont pas été relevés : un tarif inventé serait pire qu'un tarif absent.
    cout_entree_million: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    cout_sortie_million: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


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
    # « anthropic » (SDK natif) ou « openai_compat » (chat/completions). C'est CE champ qui doit
    # remplacer le `if fournisseur == ...` du moteur : un fournisseur de plus devient une ligne,
    # pas une modification de code.
    type_api: Mapped[str] = mapped_column(String(30), nullable=False, server_default="openai_compat", default="openai_compat")
    # Adresse d'appel. Celle d'Infomaniak porte le NUMÉRO DE PRODUIT du compte, propre à chaque
    # installation : elle est stockée avec le marqueur `{produit}`, substitué depuis l'env.
    base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # `max_tokens` du FOURNISSEUR, dont ses modèles héritent faute de valeur propre. Les 5 000
    # tokens d'Infomaniak ne tiennent pas au modèle : les trois du produit les partagent. Même nom
    # que sur le modèle, parce que c'est la même valeur — seule la portée diffère.
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class OutilLlm(Base):
    """LES OUTILS DU LOGICIEL QUI APPELLENT L'IA — un par ligne, pour que l'écran admin
    « Longueur des réponses » les montre TOUS sans qu'on les recopie dans l'écran.

    POURQUOI CETTE TABLE. L'écran ne réglait que 3 outils sur 17, parce que ces 3 clés étaient
    écrites à la main dans le backend et dans le front. Les 14 autres prenaient le défaut global
    en silence : l'admin ne pouvait ni les voir ni les changer, et `max_tokens_referentiel_fusion`
    (12 000, semé par migration d3b7f5c9e1a2) existait en base sans aucun écran pour l'afficher.
    Taper les 17 dans l'écran n'aurait fait que remplacer 3 valeurs en dur par 17 : le 18e outil
    serait redevenu invisible. L'écran lit donc CETTE table — une ligne = un champ.

    QUI ÉCRIT ICI. Le développeur, par migration, le jour où il crée un outil qui appelle
    `get_max_tokens(db, "<outil>")`. JAMAIS l'admin : un outil n'existe que si du code l'utilise,
    il n'y a donc pas de bouton « Ajouter un outil ». L'admin règle les valeurs, c'est tout.
    `tests/test_outils_llm_en_base.py` relit le code et tombe si un appel n'a pas sa ligne.

    OÙ EST LA VALEUR. Pas ici : dans `settings`, sous `max_tokens_<outil>`, comme avant — c'est
    ce que `get_max_tokens` lit, et sa lecture était déjà générique. Cette table ne porte que
    l'IDENTITÉ de l'outil (nom technique, libellé lisible, phrase d'aide). Pas de ligne
    `max_tokens_<outil>` = l'outil suit le défaut global : l'absence est le réglage."""
    __tablename__ = "outils_llm"
    __table_args__ = (
        UniqueConstraint("outil", name="uq_outils_llm_outil"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    outil: Mapped[str] = mapped_column(String(50), nullable=False)    # le mot passé à get_max_tokens()
    libelle: Mapped[str] = mapped_column(String(150), nullable=False)  # affichage admin
    aide: Mapped[str] = mapped_column(Text, nullable=False, server_default="", default="")
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)


class UsageLlm(Base):
    """UNE LIGNE PAR APPEL LLM RÉUSSI — ce que l'écran « IA › Statistiques » compte.

    POURQUOI CETTE TABLE. Les tokens consommés étaient calculés à chaque appel puis écrits dans
    le journal applicatif (`log.info`), c'est-à-dire perdus : un journal défile et s'efface, il ne
    s'additionne pas. L'écran de statistiques existait donc en disant « rien n'est encore mesuré »,
    faute d'un endroit où lire. Poser la trace ICI est la seule chose qui manquait.

    CE QU'ON GARDE. Les tokens, PAS le coût : le prix vit dans `ai_modeles` et peut être corrigé
    (un tarif se relève, un fournisseur change sa grille). Figer un montant obligerait à réécrire
    l'historique à chaque correction ; multiplier à la lecture donne toujours le chiffre cohérent
    avec la grille du jour. C'est une ESTIMATION affichée, pas une facture.

    CE QU'ON NE GARDE PAS. Le prompt et la réponse — jamais. Cette table sert à compter, pas à
    relire : y stocker du contenu de prof en ferait un second entrepôt de données personnelles,
    et le volume la rendrait inexploitable. Pour diagnostiquer un appel, c'est `incidents`.

    ÉCHECS. Seuls les appels RÉUSSIS sont ici — un appel refusé ne consomme rien de facturable et
    laisse déjà sa trace dans `incidents`. Un appel COUPÉ (`motif_arret = "max_tokens"`), lui, est
    bien enregistré : il a été payé, et le voir est précisément ce qui explique une facture."""
    __tablename__ = "usage_llm"
    __table_args__ = (
        Index("ix_usage_llm_created_at", "created_at"),
        Index("ix_usage_llm_modele", "modele"),
        Index("ix_usage_llm_outil", "outil"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)
    fournisseur: Mapped[str] = mapped_column(String(50), nullable=False)   # "groq" / "anthropic" / "infomaniak"
    modele: Mapped[str] = mapped_column(String(100), nullable=False)       # id API exact, rapproché de ai_modeles.modele
    # L'outil du logiciel qui a déclenché l'appel (cf. `outils_llm.outil`). NULLABLE, et sans clé
    # étrangère : une statistique ne doit JAMAIS refuser une ligne. Un appel dont l'outil n'est pas
    # encore nommé se compte quand même — il apparaît sous « non précisé » plutôt que de disparaître.
    outil: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Tokens tels que RENVOYÉS PAR LE FOURNISSEUR — jamais l'estimation maison de `_tokens_estimes`
    # (3,5 caractères/token), qui n'est qu'un garde-fou d'envoi. NULL = le fournisseur ne les a pas
    # donnés : on garde la ligne (l'appel a bien eu lieu) sans inventer de chiffre.
    tokens_entree: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_sortie: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # CACHE DE PROMPT DU FOURNISSEUR (à ne pas confondre avec `depuis_cache`, qui est notre cache
    # disque de développement). Six outils envoient le même référentiel : le premier le fait garder
    # (écriture), les suivants le relisent (lecture) à 10 % du prix.
    #
    # CES DEUX COLONNES NE SONT PAS UN LUXE STATISTIQUE. Anthropic SORT ces tokens de
    # `input_tokens` : sans elles, un appel qui relit 70 000 tokens en cache s'afficherait comme un
    # appel de 200 tokens, et la facture estimée serait dix fois trop basse. On les compte à part
    # parce qu'ils ne se paient pas au même prix — écriture 1,25×, relecture 0,10× du tarif d'entrée.
    tokens_cache_ecriture: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_cache_lecture: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duree_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Pourquoi le modèle s'est arrêté ("end_turn", "max_tokens", "stop"…). Le même champ que le
    # journal : devant une découpe qui ne rend que deux unités, c'est lui qui dit si le modèle a
    # fini ou s'il a été coupé.
    motif_arret: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # L'appel a été SERVI PAR LE CACHE DISQUE (dev) : rien n'a été envoyé, rien n'a été payé, d'où
    # tokens et coût à 0. La ligne existe quand même, sinon l'écran afficherait 3 appels pour 10
    # lancés et le cache travaillerait invisible. Une COLONNE, et non un faux fournisseur « cache » :
    # le modèle et l'outil restent les vrais — c'est justement ce qu'on veut lire (« la découpe sur
    # Sonnet 5 a été rejouée »). Faux par défaut : tout l'historique d'avant est de vrais appels.
    depuis_cache: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", default=False)


class ReferentielDocument(Base):
    """UN PDF fourni pour un couple — un MORCEAU du référentiel, pas le référentiel.

    Pourquoi cette table. Un niveau n'a pas toujours un document unique : au collège et à l'école,
    le programme complet du cycle tient en un PDF ; au lycée, il n'existe qu'éclaté, un fichier par
    matière et par série. Un couple doit donc pouvoir recevoir PLUSIEURS documents, les garder,
    les ordonner, en retirer un — puis les fusionner en un seul `referentiel.pdf`.

    LA BASE DIT CE QUI EXISTE, LE DISQUE NE PORTE QUE LES OCTETS. Chaque ligne est la trace d'un
    fichier rangé dans le dossier du couple (REFERENTIELS/<CYCLE>/<NIVEAU>/) : son vrai nom, celui
    qu'il porte sur le disque, ce qu'on a mesuré, et son rang dans la fusion. Rien ne se déduit du
    contenu d'un dossier — un écran quitté puis rouvert retrouve tout en relisant la base.

    DEUX LIENS, ET C'EST VOULU :
      • `niveau_id` — le couple, posé DÈS le dépôt. À ce moment la ligne `referentiels` n'existe
        pas encore (elle naît à la fusion) : sans ce lien, un document déposé ne pointerait rien.
        La créer plus tôt serait pire — `profil.py` lit `referentiels` par `niveau_id` pour dire
        si un prof a un référentiel, et le côté prof croirait le niveau servi alors qu'il n'y a
        rien à lire.
      • `referentiel_id` — vide au dépôt, REMPLI À LA FUSION. C'est lui qui dit ensuite de quoi
        le `referentiel.pdf` est fait : les morceaux survivent au montage, on peut en retirer un
        et refusionner sans tout redéposer.

    Remplace `referentiel_depots` (zone d'attente à jeton), morte depuis que le couple est demandé
    avant le document : la destination étant connue d'entrée, plus rien n'attend."""
    __tablename__ = "referentiel_documents"
    __table_args__ = (
        UniqueConstraint("niveau_id", "fichier_disque", name="uq_ref_documents_fichier"),
        Index("ix_ref_documents_niveau", "niveau_id"),
        Index("ix_ref_documents_referentiel", "referentiel_id"),
        Index("ix_ref_documents_empreinte", "empreinte"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    niveau_id: Mapped[int] = mapped_column(Integer, ForeignKey("niveaux.id", ondelete="CASCADE"),
                                           nullable=False)
    # Rempli à la fusion seulement. ondelete=CASCADE : supprimer le référentiel emporte la trace de
    # ses morceaux — comme ses matières et ses unités, ils n'existent pas sans lui.
    referentiel_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=True)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    fichier_origine: Mapped[str] = mapped_column(Text, nullable=False)   # le nom donné par l'admin
    # Le nom sur le disque, DANS le dossier du couple. Distinct du nom d'origine : deux documents
    # peuvent porter le même nom, et un nom fourni n'est jamais un nom de fichier sûr.
    fichier_disque: Mapped[str] = mapped_column(Text, nullable=False)
    # Empreinte SHA-256 du CONTENU du morceau (64 caractères hexadécimaux) — jamais le nom : le
    # même PDF téléchargé deux fois porte souvent deux noms. Sert à reconnaître un morceau déjà
    # déposé pour ce couple. Le doublon entre COUPLES, lui, se juge sur le fusionné.
    empreinte: Mapped[str] = mapped_column(String(64), nullable=False)
    taille_ko: Mapped[int] = mapped_column(Integer, nullable=False)
    pages: Mapped[int] = mapped_column(Integer, nullable=False)
    # Par où il est entré : 'depot' (fichier) | 'lien'. `url_source` n'est rempli que pour 'lien'.
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    url_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    apercu: Mapped[str | None] = mapped_column(Text, nullable=True)      # 25 premières lignes, page 1
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class Referentiel(Base):
    """Référentiel officiel d'un NIVEAU → collection de recherche + filtres de retrieval.

    Schéma PostgreSQL : id en IDENTITY, created_at DateTime/func.now().
    Clé d'identification = le NIVEAU, un seul référentiel par niveau (unique sur `niveau_id`).
    Il POSSÈDE ses matières (`matieres.referentiel_id`) : la colonne `matiere_id` qui pointait
    en sens inverse a disparu — elle était NULL partout et la boucle n'avait pas de sens."""
    __tablename__ = "referentiels"
    __table_args__ = (UniqueConstraint("niveau_id", name="uq_referentiels_niveau"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    niveau_id: Mapped[int] = mapped_column(Integer, ForeignKey("niveaux.id"), nullable=False)
    nom_fixe: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    collection: Mapped[str] = mapped_column(Text, nullable=False)
    filtres: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Seuil de pertinence RAG (1 - distance cosinus) par référentiel — un chunk sous ce seuil
    # n'ancre jamais une génération. Donnée métier EN BASE (plus de constante SCORE_MIN en dur).
    score_min: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.30")
    fichier: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_doc: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Empreinte SHA-256 du PDF retenu pour ce couple — écrite à la validation, même calcul que
    # `referentiel_depots.empreinte`. Elle permet de reconnaître, AU DÉPÔT, un document déjà
    # validé quelque part (« ce PDF est déjà le référentiel de BTS · CIEL Option A »). NULL =
    # référentiel dont le fichier n'était plus lisible au moment du rétro-remplissage.
    empreinte: Mapped[str | None] = mapped_column(String(64), nullable=True)
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
    # CONTRÔLE N°1, celui qui autorise le dépôt : le document NOMME-T-IL le niveau du couple ?
    # Recherche de texte, SANS IA, faite au moment où l'admin choisit le fichier, puis FIGÉE ici à
    # la validation : JSON {niveau: str, trouve: bool, manquants: [str]}. C'est une PREUVE de
    # contrôle — sans elle, plus moyen de dire sur quoi on s'est appuyé pour accepter ce document,
    # et elle ne se recalcule pas (elle porte sur le texte du PDF et le nom du niveau de CE
    # moment-là). Donnée NEUVE → EN BASE, comme forcage_motif et verif_couple. NULL = ancien dépôt.
    controle_niveau: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    Dimension 1024 (embeddings BGE-M3). La migration 384->1024 EXISTE :
    alembic/versions/e2f3a4b5c6d7_embedding_1024.py — le modèle et les migrations sont alignés.
    (Ce commentaire annonçait la migration « encore à écrire » longtemps après qu'elle l'ait
    été : un texte qui promet un travail déjà fait le fait refaire, ou pire, croire absent.)"""
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
    """Un type d'activité DU référentiel qui le met en œuvre — jamais un catalogue partagé.

    MÊME PATRON QUE `Matiere` (05/08/2026). Un type d'activité est une donnée LUE DANS LE DOCUMENT,
    au même titre qu'une matière : le référentiel dit quels formats il met en œuvre. Il appartient
    donc au référentiel, avec l'unicité sur (referentiel_id, label) — deux « Projet » dans deux
    diplômes sont deux types distincts, et ils ne se comparent jamais. CASCADE : la disparition du
    référentiel emporte ses types.

    CE QUE ÇA REMPLACE. Il y avait ici un CATALOGUE GLOBAL (crèche → doctorat) semé en dur par la
    migration `a1b2c3d4e5f6` (13 familles + un défaut), plus une table de liaison N–N
    `referentiel_types_activite` qui disait quels types un couple avait cochés. Ce catalogue était
    le vestige du temps où la liste précédait les référentiels : tout ce qui avait du sens métier
    l'avait déjà quitté (le prompt vivait sur la liaison ; les précisions avaient déjà migré depuis
    l'ancien catalogue global `type_precisions`, supprimé). Le seed était ce qui forçait le reste
    du montage — liaison N–N, `is_default`, et surtout la création automatique d'un type dans la
    table PARTAGÉE dès que l'IA en lisait un nouveau dans UN référentiel.

    `validee` = le point de fond, repris de `Matiere` : la détection PROPOSE (false), l'admin
    RETIENT (true). Le prof ne voit que les types validés — une lecture d'IA n'entre jamais dans
    ses menus toute seule. `actif` = retiré du programme (historique conservé), comme une matière.
    `origine` = qui a nommé ce type : 'ia' (lu dans le document) | 'admin' (ajouté à la main) ;
    c'est le badge affiché, jamais « qui a coché ».

    `is_default` a disparu avec le catalogue : le repli « Activité d'apprentissage » servi au prof
    quand un couple n'a aucun type est désormais UN LIBELLÉ DE SECOURS EN DUR (backend.contenu.
    activites). Il ne perd rien : le type par défaut n'avait de prompt pour aucun couple, donc il
    n'était déjà pas générable — il ne servait que d'affichage.

    Le `prompt` (génération de CE type pour CE référentiel) est descendu de la liaison sur la ligne,
    à un seul endroit. Les besoins de saisie ne sont PAS stockés : ils se lisent des trous du prompt,
    à l'instant."""
    __tablename__ = "types_activite"
    __table_args__ = (UniqueConstraint("referentiel_id", "label", name="uq_types_activite_referentiel_label"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    referentiel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    # PROPOSÉ par la détection (false) vs RETENU par l'admin (true) — comme `matieres.validee`.
    validee: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", default=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    # Qui a nommé ce type : 'ia' (lu dans le document) | 'admin' (ajouté à la main).
    origine: Mapped[str] = mapped_column(String(16), nullable=False, server_default="ia", default="ia")
    # Prompt de génération de CE type POUR CE référentiel — descendu de l'ancienne liaison, une
    # seule place, zéro copie. Écrit automatiquement à la création (gabarit en base), réécrit à
    # l'édition. Porte les deux emplacements {texte} (idée du prof) et {referentiel} (programme
    # officiel). Vide = pas encore généré.
    prompt: Mapped[str] = mapped_column(Text, nullable=False, server_default="", default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class ReferentielTypePrecision(Base):
    """Précision d'un type d'activité — fille de `types_activite`, donc PROPRE au référentiel.

    « exploration sensorielle » n'existe que pour le référentiel qui l'a nommée : le doctorat
    n'hérite pas du vocabulaire crèche. Elle pendait sur la liaison N–N ; la liaison ayant disparu
    (le type appartient désormais au référentiel), elle pend directement sur le type — même portée,
    un intermédiaire en moins. `source` = 'admin' (saisie manuelle) | 'ia' (proposée). CASCADE :
    supprimer le type retire ses précisions. UNIQUE (type_activite_id, libelle) : pas de doublon
    dans un type."""
    __tablename__ = "referentiel_type_precisions"
    __table_args__ = (
        UniqueConstraint("type_activite_id", "libelle", name="uq_ref_type_precisions_type_libelle"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    type_activite_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("types_activite.id", ondelete="CASCADE"), nullable=False, index=True)
    libelle: Mapped[str] = mapped_column(String(128), nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    source: Mapped[str] = mapped_column(String(16), nullable=False, server_default="admin", default="admin")



class ProfBloqueMaj(Base):
    """Un prof mis en attente pendant la mise à jour du référentiel d'un niveau — et la MÉMOIRE
    de ce qu'il faudra lui rebrancher ensuite.

    UNE LIGNE PAR PROF ET PAR NIVEAU : le profil d'un prof peut être sur un niveau et son couple
    de travail sur un autre, les deux peuvent être mis à jour l'un après l'autre. Une ligne par
    prof aurait fait échouer la seconde mise à jour.

    ELLE SURVIT À LA SUPPRESSION DU RÉFÉRENTIEL — c'est sa raison d'être. Le niveau, lui, ne
    bouge pas ; le référentiel disparaît et emporte ses matières (CASCADE), donc la mémoire ne
    peut pas être un identifiant de matière : on garde le NOM. Au déblocage, `matiere_id_du_nom`
    (resolution_couple.py) le résout dans le NOUVEAU référentiel — la règle maison, déjà écrite.

    TROIS QUESTIONS DIFFÉRENTES SE LISENT ICI, et elles n'ont pas la même réponse :
      · peut-il générer ?          → une ligne `etat='bloque'` pour (lui, le niveau du couple
                                     qu'il s'apprête à utiliser) ;
      · doit-on lui demander de    → une ligne existe pour (lui, le niveau de son PROFIL), quel
        compléter son profil ?       que soit son état : c'est NOUS qui avons vidé sa matière ;
      · a-t-il à lire ?            → `etat='a_informer'`, où qu'il travaille.

    La ligne ne meurt pas au déblocage : elle passe à `a_informer` et porte dans `resultat` de
    quoi composer le second message. Elle n'est effacée que lorsque le prof en a accusé
    réception — sinon un prof absent ce jour-là ne saurait jamais que sa matière a disparu."""
    __tablename__ = "profs_bloques_maj"
    __table_args__ = (
        UniqueConstraint("user_id", "niveau_id", name="uq_profs_bloques_maj_user_niveau"),
        Index("ix_profs_bloques_maj_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    niveau_id: Mapped[int] = mapped_column(Integer, ForeignKey("niveaux.id"), nullable=False)
    # La mémoire : les NOMS, seuls rescapés de la suppression. `matiere_nom` = la matière du
    # PROFIL détachée ; le couple de TRAVAIL n'est mémorisé que s'il visait ce référentiel.
    matiere_nom: Mapped[str | None] = mapped_column(Text, nullable=True)
    travail_niveau_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    travail_matiere_nom: Mapped[str | None] = mapped_column(Text, nullable=True)
    etat: Mapped[str] = mapped_column(String(12), nullable=False, server_default="bloque", default="bloque")
    # Écrit au déblocage : 'rebranche' (le nouveau document porte le MÊME nom) | 'remplace' (l'admin
    # a désigné celle qui prend sa place — `remplacee_par` la nomme) | 'matiere_disparue' (elle s'en
    # va pour de bon, et seulement si PLUS AUCUN prof ne l'attendait). NULL tant que bloqué.
    resultat: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # La matière qui a PRIS LA PLACE de `matiere_nom`, par son NOM (même raison : ce que le prof
    # lira doit survivre à la prochaine suppression). NULL = rien n'a été remplacé.
    remplacee_par: Mapped[str | None] = mapped_column(Text, nullable=True)
    bloque_le: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    debloque_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
