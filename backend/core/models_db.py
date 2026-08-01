from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Float, DateTime, Index, Text, ForeignKey, UniqueConstraint, Identity, func, text
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
    jalon: Mapped[str] = mapped_column(String(32), nullable=False)   # 'generation' (puis 'edition', 'restauration'…)
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
    Les précisions vivent PAR COUPLE sur la liaison (`referentiel_type_precisions`). Les besoins de
    saisie du type ne sont PAS stockés : ils se lisent des trous de son prompt, à l'instant."""
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

    Contrairement à l'ancien catalogue GLOBAL `type_precisions` (supprimé — même valeur crèche→doctorat), ici la précision
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

