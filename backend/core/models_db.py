from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Float, Numeric, DateTime, Index, JSON, Text, ForeignKey, UniqueConstraint, Identity, func, text
from sqlalchemy import event
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
    # signup | login | admin_login | inactivite_logout. Élargie de 16 à 32 le 10/08/2026 :
    # « inactivite_logout » fait 17 caractères et PostgreSQL refusait la ligne — la sortie
    # pour inactivité rendait une 500 au lieu de se journaliser (migration d5b1f8c3e604).
    action: Mapped[str] = mapped_column(String(32), nullable=False)
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
    matiere: Mapped[str | None] = mapped_column(String(80), nullable=True)
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


class AmbiguiteCritere(Base):
    """Les types d'ambiguïté que le prof coche avant de lancer une analyse (donnée de référence,
    EN BASE, même moule que `SeanceMode`). Source unique : le serveur valide les codes reçus sur
    cette table, l'écran dessine ses cases avec ces lignes, le prompt reçoit les `label` cochés
    et le `type` rendu par le modèle est recollé dessus — plus de liste recopiée qui diverge.

    `description` = la phrase de l'onglet « Comment ça marche » : elle appartient au critère,
    pas à l'écran. `code == "autre"` est la seule valeur dont le SERVEUR connaît le
    comportement (elle ouvre le champ de texte libre) ; tout le reste est de la donnée."""
    __tablename__ = "ambiguite_criteres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    # Le CONTRÔLE à effectuer pour ce type, envoyé au modèle sous le libellé. « Cherche les
    # consignes vagues » le laissait choisir où chercher : il prenait le plus facile à voir
    # (le vocabulaire) et sautait le reste. Ici on lui dit quoi vérifier, point par point.
    # C'est une donnée du critère, pas une phrase du prompt : muscler un contrôle ou en
    # ajouter un se fait en base.
    verification: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1', nullable=False)


class EquiteCritere(Base):
    """Les biais d'équité que le prof coche avant de lancer une analyse (donnée de référence,
    EN BASE, même moule que `AmbiguiteCritere` — écran jumeau, table jumelle).

    CE QUE CETTE LISTE NE CONTIENT PAS, et pourquoi. La recherche française sur l'équité
    (Cnesco, « Limites et biais de l'évaluation ») décrit surtout les biais du CORRECTEUR :
    effet de halo, écart entre deux correcteurs, dérive de sévérité au fil du paquet, effet de
    contraste d'une copie sur la suivante. Ils sont réels et bien établis, mais ils demandent
    plusieurs copies, plusieurs correcteurs ou de la durée : un énoncé collé seul n'en montre
    aucun. L'outil ne les promet donc pas — ils sont expliqués dans l'aide de l'écran, avec
    cette raison, pour le prof qui vient y chercher « effet de halo ».

    Restent les biais DU SUJET, écrits noir sur blanc dans le texte, et qui ont tous la même
    forme : quelque chose est demandé EN PLUS de la compétence visée, et ce quelque chose n'est
    pas également disponible à tous les élèves.

    Pas de ligne `autre` ici, à la différence des ambiguïtés : l'équité se juge sur des motifs
    connus, et un motif écrit à la main par le prof ne serait vérifiable par rien."""
    __tablename__ = "equite_criteres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    # Le CONTRÔLE à effectuer, envoyé au modèle sous le libellé — même raison que pour les
    # ambiguïtés : sans lui, le modèle choisit où chercher et prend le plus facile à voir.
    verification: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1', nullable=False)


class PromptFonctionnalite(Base):
    """LES FONCTIONNALITÉS DE L'ÉCRAN ADMIN « PROMPTS » — une ligne par outil du produit.

    Un prompt se cherche par CE QU'IL FAIT à l'écran du professeur. Le `label` est donc le CHEMIN
    dans son menu (« Mes contenus → Séance ») : c'est ainsi qu'on retrouve un texte quand on vient
    de voir le bouton qui le déclenche. L'écran admin était coupé en « Prof » et « Admin » — deux
    étiquettes qui ne triaient rien (l'admin est le seul à lire les 36 prompts, et tous servent le
    prof au bout du compte) et qui séparaient les jumeaux : l'analyse de consigne d'un côté, celle
    des ambiguïtés de l'autre.

    LE LIEN AVEC UN PROMPT tient dans `cle`, que le registre porte sur chaque prompt
    (`llm_prompts.PROMPTS[...]["fonctionnalite"]`). Une fonctionnalité sans prompt ne s'affiche
    pas : l'écran ne fabrique pas de ligne vide.

    Même moule que les autres catalogues (`code`/`label`/`ordre`/`actif`) : semé par migration,
    jamais écrit dans le code."""
    __tablename__ = "prompt_fonctionnalites"
    __table_args__ = (
        UniqueConstraint("code", name="uq_prompt_fonctionnalites_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)      # la clé portée par les prompts
    label: Mapped[str] = mapped_column(String(150), nullable=False)    # le chemin dans le menu du prof
    aide: Mapped[str] = mapped_column(Text, nullable=False, server_default="", default="")
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='true', default=True)


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
    matiere: Mapped[str | None] = mapped_column(String(80), nullable=True)
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
    matiere: Mapped[str | None] = mapped_column(String(80), nullable=True)
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
    # D'OÙ VIENT CETTE CONNEXION. L'adresse IP est là depuis toujours, mais elle ne dit rien à
    # personne : « 83.228.245.163 » ne permet pas de voir qu'un même compte est ouvert à Lille et
    # à Marseille en même temps. La ville est résolue UNE FOIS puis gardée ici — pas à chaque
    # affichage — et les coordonnées servent à mesurer l'écart entre deux sessions du même compte.
    localisation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
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
    """UNE ALERTE D'ADMINISTRATION — ce que la surveillance a trouvé, et de quoi elle parle.

    CE QU'ELLE ÉTAIT. Un niveau, un titre, une phrase. Tout le reste — de qui il s'agit, ce qui a
    été mesuré, où aller voir — vivait DANS la phrase. « 47 tentatives détectées, vérifier les IPs
    dans le panel admin » : le lecteur repart chercher lui-même, et rien n'est comptable. On ne
    peut ni regrouper, ni trier, ni suivre une évolution sur trois mois.

    LES QUATRE COLONNES AJOUTÉES le 15/08/2026, et à quoi chacune sert vraiment :
      - `code` : le GENRE d'alerte, stable dans le temps (« cpu », « compte_multi_postes »). C'est
        lui qui rend les statistiques possibles — un titre se réécrit, un code non ;
      - `user_id` / `user_email` : DE QUI l'alerte parle, quand elle parle de quelqu'un. Écrire le
        courriel à côté de l'identifiant est volontaire : un compte supprimé six mois plus tard ne
        doit pas rendre son alerte anonyme ;
      - `donnees` : les FAITS mesurés (nombre de postes, distance, villes). Relire une phrase pour
        en extraire un nombre est le meilleur moyen de se tromper ;
      - `lien` : OÙ aller voir. L'écran cesse d'être un cul-de-sac.

    SURVEILLER, PAS INTERDIRE. Aucune de ces colonnes ne déclenche quoi que ce soit : rien n'est
    bloqué, rien n'est fermé. Une alerte informe l'administrateur, qui décide."""
    __tablename__ = "admin_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    # Le genre d'alerte, stable — c'est la clé de tout regroupement et de toute statistique.
    # NULL pour les alertes écrites avant cette colonne : on ne leur invente pas un code.
    code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # De qui parle l'alerte. NULL quand elle parle de la machine (processeur, disque).
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Les faits, tels quels. Pas de format imposé : chaque genre d'alerte a les siens, et forcer
    # un schéma commun reviendrait à ne rien pouvoir y mettre.
    donnees: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Le chemin dans l'administration où l'on peut vérifier par soi-même.
    lien: Mapped[str | None] = mapped_column(String(300), nullable=True)
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


class Cycle(Base):
    __tablename__ = "cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False)
    # Le cycle ne porte PLUS AUCUN PROMPT depuis le 06/08/2026. Les trois (matières, découpe,
    # types) vivent sur le RÉFÉRENTIEL : `Referentiel.prompt_matieres`, `.prompt_decoupe`,
    # `.prompt_types` — un jeu par couple cycle+niveau. Ils étaient rangés ici parce qu'un cycle
    # ressemble à une famille de documents bâtis pareil ; c'est faux, et prouvé : le cycle « BTS »
    # porte dix-huit diplômes, et le prompt écrit sur l'un d'eux n'apprenait rien sur ses voisins.
    # Une famille de diplômes n'est pas une famille de documents.


class Niveau(Base):
    __tablename__ = "niveaux"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_id: Mapped[int] = mapped_column(Integer, ForeignKey("cycles.id"), nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(64), nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False)


class Matiere(Base):
    """Une matière DU référentiel qui la nomme — jamais un catalogue partagé entre diplômes.

    Chaque diplôme a ses matières, la Terminale a les siennes, avec l'orthographe de LEUR document :
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
    # Tarifs par million de tokens, pour l'estimation de coût de l'écran statistiques. VIDES tant
    # qu'ils n'ont pas été relevés : un tarif inventé serait pire qu'un tarif absent.
    #
    # DANS LA MONNAIE DU FOURNISSEUR, pas en dollars : Infomaniak publie en francs suisses, les
    # autres en dollars. Stocker tel qu'affiché sur leur page laisse l'admin vérifier d'un coup
    # d'œil ; convertir à l'écriture donnerait un montant faux dès le lendemain, et faux en
    # silence. L'euro se calcule à l'affichage (`backend/core/devises.py`).
    cout_entree_million: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    cout_sortie_million: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    devise: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD", default="USD")
    # LE NOM PUBLIC DU MODÈLE, quand il diffère de son nom d'appel. Infomaniak n'accepte que
    # « mistral3 » dans une requête, mais publie « mistralai/Ministral-3-14B-Instruct-2512 » dans sa
    # liste et sur sa grille tarifaire : sans les deux, retrouver ce qu'un modèle coûte se fait au
    # jugé. Vide = les deux noms sont le même (Anthropic, Groq).
    nom_fournisseur: Mapped[str | None] = mapped_column(String(200), nullable=True)
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
    # « gratuit » ou « payant » — DIT PAR L'ADMINISTRATEUR, jamais déduit. Ni le tarif des modèles ni
    # la présence d'une clé ne permettent de le savoir : un tarif à zéro peut vouloir dire « offert »
    # comme « pas encore relevé », et un plan gratuit devient payant sans qu'aucun chiffre ne bouge
    # chez nous. Sert à ranger l'écran en deux zones ; ne touche PAS l'ordre d'appel.
    tarification: Mapped[str] = mapped_column(String(10), nullable=False,
                                              server_default="payant", default="payant")
    # L'adresse de sa grille tarifaire publique. Sert au bouton « Relever les tarifs », qui va la
    # lire et remplit le prix de chaque modèle. Donnée du fournisseur, comme `base_url` : elle
    # change quand il refait son site, et seul l'administrateur peut la corriger.
    lien_tarifs: Mapped[str | None] = mapped_column(String(500), nullable=True)
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

    ÉCHECS — UNE LIGNE PAR TENTATIVE, ABOUTIE OU NON. Un appel refusé ne laissait qu'un
    `log.warning`, c'est-à-dire rien : impossible de dire ce qui refuse ni à quelle fréquence. Il
    écrit maintenant sa ligne, avec `resultat = "refus"` et le `code_http` du fournisseur. La
    conséquence est à connaître : compter la consommation demande désormais de filtrer sur
    `resultat`, un refus ne consommant rien de facturable."""
    __tablename__ = "usage_llm"
    __table_args__ = (
        Index("ix_usage_llm_created_at", "created_at"),
        Index("ix_usage_llm_modele", "modele"),
        Index("ix_usage_llm_outil", "outil"),
        Index("ix_usage_llm_resultat", "resultat"),
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
    # Ce qu'est devenue la tentative : "ok" · "refus" · "coupe". TROIS états et non deux — une
    # réponse coupée (le modèle a atteint sa limite de sortie) a été payée mais reste inutilisable ;
    # la ranger avec les succès masquerait une dépense sans contrepartie. Défaut "ok" : une ligne
    # écrite sans le préciser est un appel qui a abouti, un refus se déclare toujours.
    resultat: Mapped[str] = mapped_column(String(10), nullable=False, server_default="ok", default="ok")
    # Ce que le fournisseur a répondu (429, 402, 500…). NULL quand l'appel a abouti. C'est lui qui
    # sépare « plus de quota » de « service en panne » : deux refus, deux gestes différents.
    code_http: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # La place du fournisseur dans la liste au moment de la tentative. NULL tant qu'il n'y a pas de
    # liste — écrire « 1 » quand un seul fournisseur est appelé inventerait une cascade.
    rang: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ReferentielNiveau(Base):
    """LES NIVEAUX QU'UN RÉFÉRENTIEL DESSERT — la réponse à « quel référentiel pour ce prof ? ».

    POURQUOI ELLE EXISTE (15/08/2026). Un programme de CYCLE est un seul document pour plusieurs
    années : le cycle 4 tient la 5e, la 4e et la 3e. Tant que le référentiel n'était rattaché qu'à
    un niveau, deux défauts en découlaient — le prof de 4e recevait le contenu des deux autres
    années (réparé par `referentiel_chunks.annee`), et les profs de 5e et de 3e n'avaient AUCUN
    référentiel, donc aucune génération ancrée. Le second se répare ici.

    PAS UN RATTACHEMENT AU CYCLE. Le cycle « Collège » porte 6e, 5e, 4e ET 3e, alors que le cycle 4
    du BOEN ne couvre pas la 6e : rattacher au cycle donnerait le programme du cycle 4 aux profs de
    6e. La liste des niveaux desservis est donc EXPLICITE, jamais déduite.

    `UNIQUE(niveau_id)` : un niveau n'est desservi que par UN référentiel — c'est cette contrainte
    qui porte désormais l'invariant, et elle est plus forte que l'ancienne, qui ne regardait que le
    niveau porteur. CASCADE : la disparition du référentiel emporte ses rattachements.

    IL N'Y A AUCUN ÉCRAN pour remplir cette table (dette assumée le 15/08/2026, pour ne pas mêler
    une réparation de bug et une fonctionnalité neuve). Le prochain référentiel de cycle demandera
    soit une migration écrite à la main, soit ce geste dans Admin → Référentiels."""
    __tablename__ = "referentiel_niveaux"
    __table_args__ = (UniqueConstraint("niveau_id", name="uq_referentiel_niveaux_niveau"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    referentiel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False)
    niveau_id: Mapped[int] = mapped_column(Integer, ForeignKey("niveaux.id"), nullable=False)


class Referentiel(Base):
    """Référentiel officiel → collection de recherche + filtres de retrieval.

    Schéma PostgreSQL : id en IDENTITY, created_at DateTime/func.now().
    Il POSSÈDE ses matières (`matieres.referentiel_id`) : la colonne `matiere_id` qui pointait
    en sens inverse a disparu — elle était NULL partout et la boucle n'avait pas de sens.

    `niveau_id` EST LE NIVEAU PORTEUR, ET RIEN D'AUTRE (15/08/2026) : il donne le chemin du PDF
    (`REFERENTIELS/<CYCLE>/<NIVEAU>/`), le nom et la collection. Il ne répond PLUS à la question
    « quel référentiel pour ce prof ? » — c'est `referentiel_niveaux` qui répond, par la porte
    unique `referentiel_du_niveau()`. Deux sources pour une même question seraient pires que le
    défaut d'origine : elles se contrediraient un jour sans que rien ne le signale.

    `uq_referentiels_niveau` RESTE. Elle ne bloquait pas le service de plusieurs niveaux — c'est
    l'absence de table de liaison qui le bloquait. Elle garde son sens : deux référentiels ne
    peuvent pas se ranger dans le même dossier de PDF."""
    __tablename__ = "referentiels"
    __table_args__ = (UniqueConstraint("niveau_id", name="uq_referentiels_niveau"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    niveau_id: Mapped[int] = mapped_column(Integer, ForeignKey("niveaux.id"), nullable=False)
    nom_fixe: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    # Les niveaux DESSERVIS, écrits pour être lus : « 5e, 4e, 3e ». C'est ce que la liste des
    # référentiels affiche à la place du seul niveau porteur — sans quoi l'administrateur venu
    # modifier le programme de la 3e ne trouve aucune ligne pour la 3e et en dépose un second.
    # CALCULÉE, jamais saisie (`recalculer_nom_affichage`) : un libellé tapé à la main ment le
    # jour où un rattachement bouge, et rien ne permet de s'en apercevoir.
    nom_affichage: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    # validé quelque part (« ce PDF est déjà le référentiel d'un autre couple »). NULL =
    # référentiel dont le fichier n'était plus lisible au moment du rétro-remplissage.
    empreinte: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Prompt de découpe du couple — GÉNÉRÉ PAR L'IA (méta-prompt en base), puis affiché, corrigé et
    # validé par l'admin. DONNÉE MÉTIER EN BASE (aucun prompt écrit en dur dans le code).
    # `prompt_decoupe_valide` : la découpe REFUSE de tourner tant que False (garde-fou).
    prompt_decoupe: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_decoupe_valide: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0", default=False)
    # Prompts MATIÈRES et TYPES du couple (06/08/2026). Ils étaient rangés sur le CYCLE : une seule
    # case pour les 18 niveaux du BTS, remplie à partir du premier déposé — elle aurait lu les dix-sept
    # autres avec les repères de celui-là. Ils descendent ici, où vivent déjà le texte de travail et le prompt
    # de découpe, et où pointent les matières et les types qu'ils produisent.
    # `_valide` ne commande rien : le prompt sert dès qu'il existe, le booléen dit seulement que
    # l'admin l'a relu (même règle que sur le cycle).
    prompt_matieres: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_matieres_valide: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0", default=False)
    prompt_types: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_types_valide: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0", default=False)
    # Quatrième couple (07/08/2026) : le prompt qui lit les PRÉCISIONS d'un type. Il portait le
    # même défaut que les trois autres avant eux — un seul texte pour toute l'application, donc
    # des précisions plausibles mais inventées, jamais ancrées au document. Deux repères ici, et
    # non un : {texte} (le document) et {label} (le type dont on veut les précisions).
    prompt_precisions: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_precisions_valide: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0", default=False)
    # MÉTA-prompt des matières, propre à ce niveau (06/08/2026). Ce n'est PAS le prompt qui lit le
    # document : c'est la consigne qui sert à l'ÉCRIRE (elle reçoit le document dans {document} et
    # rend un prompt de lecture, lequel porte {texte}). Il en existait un seul pour toute
    # l'application. Ce repli a été RETIRÉ le 08/08/2026 : cette case est désormais la seule source.
    # Aucun drapeau `_valide` : ce texte est écrit à la main par l'admin, jamais par l'IA, il n'y a
    # donc rien à « relire ».
    prompt_meta_matieres: Mapped[str | None] = mapped_column(Text, nullable=True)
    # MÉTA-prompt de la DÉCOUPE, propre à ce niveau (06/08/2026) — le jumeau du précédent, et pour
    # la même raison : la recette qui fait écrire le prompt de découpe d'un BTS n'est pas celle
    # d'un programme de crèche. Case vide = rien ne prend la main, la génération lève (repli
    # général retiré le 08/08/2026). Aucun drapeau `_valide` : écrit à la main.
    prompt_meta_decoupe: Mapped[str | None] = mapped_column(Text, nullable=True)
    # MÉTA-prompt des TYPES D'ACTIVITÉ, propre à ce niveau (06/08/2026) — le troisième et dernier
    # des trois couples. Il était le seul à n'avoir aucune case par niveau : la recette qui fait
    # écrire le prompt des types d'un BTS partait aussi à la crèche. Repli identique aux deux
    # autres : case vide = rien ne prend la main, la génération lève. Aucun drapeau `_valide`.
    prompt_meta_types: Mapped[str | None] = mapped_column(Text, nullable=True)
    # MÉTA-prompt des PRÉCISIONS, propre à ce niveau (07/08/2026) — quatrième et dernier jumeau.
    # Case vide = rien ne prend la main : la génération lève (repli général retiré le 08/08/2026).
    prompt_meta_precisions: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    # L'annee du CYCLE a laquelle cette unite appartient ('5e'/'4e'/'3e'), NULL quand elle vaut
    # pour tout le cycle. NULL n'est pas « on ne sait pas », c'est « commune » : le filtre RAG
    # lit `annee IS NULL OR annee = <annee du prof>`, comme il lit deja l'option.
    annee: Mapped[str | None] = mapped_column(Text, nullable=True)
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    texte: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1024), nullable=False)
    embedding_model: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


@event.listens_for(Referentiel, "after_insert")
def _referentiel_dessert_au_moins_son_niveau_porteur(mapper, connection, target) -> None:
    """TOUT référentiel créé dessert d'emblée son niveau porteur.

    C'EST UN INVARIANT, PAS UNE COMMODITÉ. Un référentiel absent de `referentiel_niveaux` ne sert
    PERSONNE : `referentiel_du_niveau` rend None et l'application répond « available: false » sans
    qu'aucune erreur ne soit levée — le pire des défauts, celui qui se présente comme un état
    normal. Le tenir ici, dans le modèle, plutôt que dans les douze endroits qui créent un
    référentiel (l'écran admin, et onze semis de tests), c'est zéro occasion de l'oublier.

    Un document de CYCLE en dessert plusieurs : les rattachements SUPPLÉMENTAIRES s'ajoutent
    ensuite, par migration (il n'y a pas encore d'écran pour les dire — dette du 15/08/2026).
    Ils ne passent pas par ici, et c'est bien : cette fonction ne connaît que le niveau porteur.

    `connection.execute` et non une session : on est dans le flush en cours, sur la MÊME
    transaction et le MÊME schéma que l'insertion qui l'a déclenchée. Un échec ici annule donc
    aussi la création du référentiel — un référentiel sans rattachement ne peut pas exister."""
    connection.execute(
        ReferentielNiveau.__table__.insert().values(
            referentiel_id=target.id, niveau_id=target.niveau_id)
    )


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


class Demo(Base):
    """Le PILOTAGE des bases de démonstration — jamais leur contenu.

    Une démonstration, c'est une base PostgreSQL À PART qui contient un référentiel déjà fabriqué,
    un compte de démonstration et du contenu d'exemple : un enseignant qui découvre le produit y
    entre, explore et bidouille sans toucher au réel. Cette table-ci ne contient rien de tout
    cela ; elle vit dans la base réelle et se contente de dire, pour chaque niveau, OÙ est sa
    démonstration et OÙ elle en est.

    POURQUOI `nom_base` EST DU TEXTE ET NON UNE CLÉ ÉTRANGÈRE : PostgreSQL ne sait pas référencer
    une autre base. La démonstration est ailleurs, hors de portée du moteur — le lien ne peut donc
    être qu'un nom, et c'est à nous de le tenir juste. Convention retenue : `<option>_demo`
    (ciela_demo, cielb_demo, crsa_demo…), en minuscules et sans tiret, parce qu'un tiret obligerait
    à écrire le nom entre guillemets dans TOUTE commande SQL — et un oubli se lirait comme une
    soustraction.

    UNE SEULE DÉMONSTRATION PAR RÉFÉRENTIEL (`uq_demos_referentiel`) : deux démonstrations du même
    niveau n'auraient aucun sens et l'admin ne saurait pas laquelle est livrée.

    LES COMPTEURS SONT FIGÉS À DESSEIN. `nb_activites`, `nb_sequences` et `nb_seances` décrivent
    une base que cette connexion-ci NE PEUT PAS interroger. Ils sont écrits au moment de la
    fabrication et relus tels quels ; les rafraîchir demanderait d'ouvrir la base de démonstration.
    Ils peuvent donc mentir si quelqu'un modifie la démonstration sans repasser par ici — c'est le
    prix de la séparation, pas un oubli.

    `defauts_connus` est une MÉMOIRE, pas un journal d'incidents : ce qu'on a déjà trouvé sur cette
    démonstration et qu'il ne faut pas rechercher deux fois."""
    __tablename__ = "demos"
    __table_args__ = (
        UniqueConstraint("referentiel_id", name="uq_demos_referentiel"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    # CASCADE : le référentiel disparu, sa démonstration ne désigne plus rien. Même règle que
    # `matieres` et `types_activite`, qui tombent déjà avec lui.
    referentiel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("referentiels.id", ondelete="CASCADE"), nullable=False)
    nom_base: Mapped[str] = mapped_column(Text, nullable=False)
    # L'adresse de l'instance branchée sur cette base. NULL = pas encore montée, donc pas
    # visitable : l'entrée « Démonstration » du menu prof reste grisée tant qu'elle manque.
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # a_faire | en_cours | fait | teste | valide — la progression, du vide au livrable.
    statut: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="a_faire", default="a_faire")
    nb_activites: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"), default=0)
    nb_sequences: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"), default=0)
    nb_seances: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"), default=0)
    date_generation: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    date_dernier_test: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    defauts_connus: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Fonctionnalite(Base):
    """Ce que la plateforme sait faire, et où ça en est — la matière du tableau de bord.

    LA RAISON D'ÊTRE. L'écran d'état ne savait dire qu'une chose : la plomberie est branchée
    (clé IA, SMTP, un référentiel découpé, une activité générée). Il annonçait « tout est prêt »
    pendant que des pans entiers du produit n'existaient pas — « Mes évals » vide, l'équité
    jamais écrite. Vrai sur la plomberie, faux pour qui le lit. Cette table porte la moitié
    manquante : ce qui est livré, ce qui est commencé, ce qui reste à faire.

    ELLE N'EST PAS DÉRIVABLE. Les huit étapes techniques se lisent dans les vraies tables — une
    clé existe ou non. L'avancement d'une fonctionnalité, lui, ne se lit nulle part : aucune
    table ne sait qu'un bouton est posé mais inactif. Il se DÉCLARE, et la déclaration vit ici
    plutôt que dans le code, pour que l'écran la lise comme il lit le reste.

    QUI LA TIENT. La session qui code, par migration, à chaque fonctionnalité livrée — jamais
    l'administrateur, qui ne fait que consulter. C'est le motif déjà en place pour `outils_llm`.

    LA PREUVE. `note` dit POURQUOI l'état est celui-là — « bouton posé, inactif », « page vide ».
    Sans elle, une ligne « en cours » est une affirmation qu'on ne peut ni vérifier ni contester.
    """
    __tablename__ = "fonctionnalites"
    __table_args__ = (
        # Un même nom peut exister des deux côtés (« Feedbacks » chez l'admin ET chez le prof) :
        # c'est le couple qui identifie, pas le nom seul.
        UniqueConstraint("domaine", "ecran", "nom", name="uq_fonctionnalites_domaine_ecran_nom"),
        # Le seul tri de l'écran : par domaine, puis dans l'ordre de la liste.
        Index("ix_fonctionnalites_domaine_ordre", "domaine", "ordre"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    # « admin » | « prof » — de quel côté de l'application. La plomberie n'est PAS ici : elle
    # reste dérivée des vraies tables, c'est sa force.
    domaine: Mapped[str] = mapped_column(String(16), nullable=False)
    # L'écran qui la porte (« Mes contenus », « Supervision ») : c'est le groupe d'affichage.
    ecran: Mapped[str] = mapped_column(String(80), nullable=False)
    nom: Mapped[str] = mapped_column(String(120), nullable=False)
    # « fait » | « en_cours » | « a_venir ». Trois états, pas quatre : au-delà, plus personne
    # ne sait où placer une ligne, et le tableau cesse d'être lisible.
    etat: Mapped[str] = mapped_column(String(16), nullable=False, server_default="a_venir", default="a_venir")
    # La preuve, en quelques mots. Vide pour une fonctionnalité simplement faite.
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # LE FICHIER QUI REND CET ÉCRAN, chemin depuis `frontend/`. C'est ce qui rend la ligne
    # vérifiable : `test_tableau_de_bord_dit_vrai` exige qu'il existe pour toute ligne qui n'est
    # pas « à venir ». Sans lui, une fonctionnalité supprimée continue de s'annoncer « faite »
    # sans que rien ne tombe — c'est arrivé au Labo le 10/08/2026. NULL pour ce qui n'est pas
    # écrit : il n'y a pas de fichier à citer.
    composant: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"), default=0)


class TachePlanifiee(Base):
    """LES TRAVAUX QUE L'APPLICATION FAIT TOUTE SEULE — une ligne par tâche, réglée par l'admin.

    POURQUOI EN BASE. L'heure de la veille des tarifs et la cadence de la surveillance étaient
    écrites dans `main.py`. Passer un contrôle de 6 h à 22 h demandait un développeur et un
    redéploiement pour changer deux chiffres qui ne regardent que l'exploitation.

    CE QUI N'EST PAS ICI : la fonction exécutée. Elle vit dans le registre `TACHES` de
    `backend/systeme/planificateur.py`, où `code` la retrouve — on ne met pas du Python en base.

    LES TROIS DERNIÈRES COLONNES sont le compte rendu du dernier passage. Sans elles, une tâche
    silencieuse est indiscernable d'une tâche qui ne tourne plus : l'écran dirait « active » d'un
    travail mort depuis trois semaines."""
    __tablename__ = "taches_planifiees"
    __table_args__ = (UniqueConstraint("code", name="uq_taches_planifiees_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # L'identifiant technique, celui qui retrouve la fonction dans le registre du planificateur.
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", default=True)
    # « quotidien » (à telle heure) ou « intervalle » (toutes les N minutes). Deux façons, pas
    # cinq : une expression cron complète serait ingérable dans un écran d'administration, et
    # aucune des tâches connues n'en a besoin.
    type_planif: Mapped[str] = mapped_column(String(12), nullable=False,
                                             server_default="quotidien", default="quotidien")
    heure: Mapped[int | None] = mapped_column(Integer, nullable=True)     # 0–23, UTC
    minute: Mapped[int | None] = mapped_column(Integer, nullable=True)    # 0–59
    intervalle_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # À qui écrire. Vide = l'adresse d'administration du serveur (`ADMIN_EMAIL`) : on n'oblige pas
    # à recopier une adresse déjà connue, et une tâche ne devient pas muette parce qu'un champ est
    # resté vide.
    destinataire: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dernier_passage: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dernier_resultat: Mapped[str | None] = mapped_column(Text, nullable=True)
    dernier_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    derniere_duree_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TacheAFaire(Base):
    """LE CARNET DE L'ADMINISTRATEUR — les idées et les chantiers, notés avant d'être oubliés.

    POURQUOI CETTE TABLE. Les professeurs ont « Mes feedbacks » pour faire remonter une remarque,
    et l'administrateur a l'écran qui les reçoit. Lui n'avait rien. Une idée qui lui vient en
    pleine autre tâche — « alerter quand un compte tourne sur dix postes » — n'avait aucun endroit
    où atterrir : elle se disait, et elle se perdait.

    CE QUE CE N'EST PAS. Ni le planificateur (`taches_planifiees`), qui exécute des travaux à
    l'heure dite ; ni la carte des fonctionnalités (`fonctionnalites`), qui décrit ce qui existe.
    Ici, rien ne s'exécute et rien n'est vérifié : c'est un carnet, il ne contient que ce qu'on y
    écrit.

    DEUX ÉTATS, PAS TROIS. À faire, ou fait. « En cours » se raconte dans le détail de la ligne —
    un troisième état oblige à décider où ranger chaque note, et le carnet cesse d'être un carnet.
    """
    __tablename__ = "taches_a_faire"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titre: Mapped[str] = mapped_column(String(200), nullable=False)
    # Le détail, facultatif : le pourquoi, les pièges, ce qu'on avait décidé. C'est ce qui fait
    # qu'une note relue dans six mois veut encore dire quelque chose.
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    fait: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", default=False)
    # QUAND elle a été cochée. Sans cette date, une ligne faite hier et une ligne faite l'an
    # dernier se ressemblent, et le carnet ne se purge plus jamais.
    fait_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
