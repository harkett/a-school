-- ============================================================================
-- college4e — 5e, partie 1/3 : les 13 séquences
--
-- Le référentiel 21 dessert 5e, 4e et 3e. La démonstration doit donc porter du
-- contenu pour chacune des trois années : un professeur de 5e qui n'y trouve
-- que du programme de 4e ne s'y reconnaît pas.
--
-- CE QUI EST PROPRE À LA 5e vient des unités datées du référentiel :
--   Français       — les cinq questionnements de l'année (unités 27 à 31)
--   Histoire       — chrétientés et islam, l'occident féodal, XVIe-XVIIe (101-103)
--   Géographie     — démographie, ressources, environnement (110-112)
-- Les onze autres disciplines ont un programme de CYCLE : le contenu retenu
-- suit la progression usuelle de l'année, sans sortir du cycle 4.
--
-- Les identifiants continuent la numérotation du 4e : séquences 14 à 26.
-- ============================================================================

INSERT INTO sequences (user_id, titre, contexte, ampleur, competences, matiere, niveau, created_at, updated_at) VALUES

-- 14. Français — « Le voyage et l'aventure : pourquoi aller vers l'inconnu ? »
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Lire des récits d''aventure et comprendre ce qu''on va chercher en partant',
 'Classe de 5e, 28 élèves, quatre heures et demie hebdomadaires. Premier questionnement de l''année. Le groupe lit peu en dehors de la classe ; les récits d''aventure sont l''entrée qui fonctionne, à condition de ne pas s''arrêter au résumé des péripéties.',
 'Huit séances sur cinq semaines, autour d''un roman d''aventure lu en œuvre intégrale et d''un corpus de récits de voyage authentiques.',
 '["Lire une œuvre intégrale et en rendre compte","Distinguer le récit d''aventure fictif du récit de voyage réel","Repérer ce qui pousse un personnage à partir","Écrire un épisode d''aventure qui tient sur un obstacle","Employer les temps du récit au passé"]',
 'Français', '5e', now(), now()),

-- 15. Langues vivantes
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Décrire son quotidien et celui des autres, en continu',
 'Classe de 5e, anglais LV1, 28 élèves, trois heures hebdomadaires. Niveau visé A2. Les élèves connaissent le vocabulaire du quotidien mais l''emploient au coup par coup ; l''enjeu de l''année est d''enchaîner deux ou trois phrases sans s''arrêter.',
 'Sept séances sur quatre semaines, autour de la journée type et des habitudes, en France et dans un pays anglophone.',
 '["Comprendre une description orale simple du quotidien","Distinguer le présent simple du présent progressif","Décrire sa journée en continu pendant quarante secondes","Lire à haute voix un texte court préparé","Rendre compte de ce qu''un camarade a dit"]',
 'Langues vivantes (étrangères ou régionales)', '5e', now(), now()),

-- 16. Arts plastiques
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Faire tenir un espace en trois dimensions sur une feuille plate',
 'Classe de 5e, 28 élèves, une heure hebdomadaire. La question de l''espace est celle de l''année : les élèves dessinent ce qu''ils savent d''un objet plutôt que ce qu''ils en voient, et la perspective leur paraît une astuce plutôt qu''un problème.',
 'Six séances d''une heure, une production par séance, et un accrochage comparatif en fin de séquence.',
 '["Représenter la profondeur par des moyens choisis","Employer le point de vue comme une décision","Distinguer ce qu''on voit de ce qu''on sait","Parler d''une production avec un vocabulaire précis","Réinvestir une référence artistique dans son travail"]',
 'Arts plastiques', '5e', now(), now()),

-- 17. Éducation musicale
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Sentir la pulsation, la tenir, puis jouer avec elle',
 'Classe de 5e, 28 élèves, une heure hebdomadaire. Salle équipée de percussions et d''un clavier. Le groupe chante volontiers et accélère systématiquement : la pulsation est le chantier de l''année.',
 'Six séances : deux d''installation rythmique, deux d''écoute comparée, deux de réalisation collective.',
 '["Tenir une pulsation régulière en groupe","Décrire un rythme avec un vocabulaire technique","Repérer un décalage rythmique volontaire dans une musique","Chanter en respectant la mise en place","Justifier un choix d''écoute devant la classe"]',
 'Éducation musicale', '5e', now(), now()),

-- 18. Histoire des arts
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Regarder ce que les images du Moyen Âge et de la Renaissance donnent à croire',
 'Classe de 5e, 28 élèves, une heure tous les quinze jours, en co-intervention avec l''histoire-géographie. La séquence accompagne le programme d''histoire de l''année : chrétientés et islam, puis l''ouverture du XVIe siècle.',
 'Cinq séances de deux heures sur le trimestre, autour d''œuvres religieuses et de portraits de commanditaires.',
 '["Décrire une œuvre avant de l''interpréter","Situer une œuvre dans son contexte de commande","Comparer deux œuvres de deux aires culturelles","Se repérer dans une collection en ligne","Présenter une œuvre à l''oral"]',
 'Histoire des arts', '5e', now(), now()),

-- 19. Éducation physique et sportive
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Construire une figure collective où chacun tient sa place',
 'Classe de 5e, 28 élèves, deux séances hebdomadaires dont une de deux heures, en gymnase. L''acrosport est retenu parce qu''il met tout le monde en réussite et qu''il oblige à la sécurité mutuelle : personne ne monte si personne ne tient.',
 'Six séances d''acrosport, par groupes de quatre, avec un enchaînement présenté en fin de séquence.',
 '["Assurer la sécurité d''un camarade dans une figure","Construire un enchaînement à quatre","Observer une figure et signaler ce qui n''est pas sûr","Tenir un rôle de porteur, de voltigeur ou de pareur","Présenter un enchaînement devant les autres"]',
 'Éducation physique et sportive', '5e', now(), now()),

-- 20. Enseignement moral et civique
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Comprendre à quoi sert une règle, et ce qui se passe quand elle manque',
 'Classe de 5e, 28 élèves, une heure hebdomadaire. La classe conteste les règles sans les connaître : la séquence part donc du règlement intérieur réel, article par article, avant toute discussion morale.',
 'Six séances : deux sur le règlement, trois sur des cas de la vie du collège, une sur la production collective.',
 '["Chercher ce que dit la règle avant de dire ce qu''on ressent","Distinguer une règle, une habitude et un ordre","Écouter un avis contraire jusqu''au bout","Formuler une proposition de modification argumentée","Rendre compte par écrit d''une discussion"]',
 'Enseignement moral et civique', '5e', now(), now()),

-- 21. Histoire et géographie
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Comprendre comment trois mondes se sont rencontrés autour de la Méditerranée',
 'Classe de 5e, 28 élèves, trois heures hebdomadaires. Premier thème d''histoire de l''année. La difficulté est de faire tenir ensemble trois ensembles — Byzance, l''Europe carolingienne, le monde musulman — sans les traiter l''un après l''autre comme trois chapitres étanches.',
 'Sept séances appuyées sur des cartes, deux récits de voyageurs et l''étude d''une ville de contact.',
 '["Situer dans le temps et l''espace trois ensembles politiques","Lire une carte historique et en tirer une information","Confronter deux documents sur un même échange","Réaliser un croquis simple de contacts","Rédiger un développement construit d''une quinzaine de lignes"]',
 'Histoire et géographie', '5e', now(), now()),

-- 22. Physique-Chimie
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Séparer ce qui est mélangé, et dire ce qu''on a séparé',
 'Classe de 5e, 28 élèves, une heure et demie hebdomadaire dont une heure en demi-groupe. Premier contact avec le laboratoire pour la plupart. La séquence installe autant les gestes et la sécurité que les notions.',
 'Six séances dont quatre expérimentales, autour des mélanges, des solutions et des techniques de séparation.',
 '["Distinguer un mélange homogène d''un mélange hétérogène","Choisir une technique de séparation adaptée","Manipuler en respectant les consignes de sécurité","Rédiger un compte rendu qui permette de refaire l''expérience","Schématiser un montage aux normes"]',
 'Physique-Chimie', '5e', now(), now()),

-- 23. Sciences de la vie et de la Terre
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Suivre ce que devient un aliment, de la bouche jusqu''au sang',
 'Classe de 5e, 28 élèves, une heure et demie hebdomadaire dont une heure en demi-groupe. Le sujet touche au corps des élèves : il faut le traiter avec précision et sans gêne, en évitant toute allusion aux régimes ou aux corps des uns et des autres.',
 'Sept séances : trois de manipulation, deux de modélisation, deux de synthèse.',
 '["Suivre le trajet d''un aliment dans le tube digestif","Distinguer digestion mécanique et digestion chimique","Concevoir une expérience qui met une hypothèse à l''épreuve","Distinguer un modèle de la réalité qu''il représente","Relier un besoin de l''organisme à un apport alimentaire"]',
 'Sciences de la vie et de la Terre', '5e', now(), now()),

-- 24. Technologie
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Comprendre à quoi répond un objet, avant de vouloir l''améliorer',
 'Classe de 5e, 28 élèves, une heure et demie hebdomadaire. Les élèves arrivent avec l''idée qu''un objet technique est un objet compliqué. La séquence part d''objets banals — une trottinette, un parapluie, une bouilloire — pour installer la notion de fonction.',
 'Huit séances, par équipes de quatre, avec une étude d''objet et une amélioration prototypée.',
 '["Décrire un objet par les fonctions qu''il assure","Repérer les solutions techniques retenues","Comparer deux objets qui remplissent la même fonction","Représenter une amélioration par un croquis coté","Rendre compte de l''avancement devant une autre équipe"]',
 'Technologie', '5e', now(), now()),

-- 25. Mathématiques
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Reconnaître une situation de proportionnalité — et savoir quand il n''y en a pas',
 'Classe de 5e, 28 élèves, quatre heures et demie hebdomadaires. Les élèves appliquent le produit en croix partout, y compris là où il n''a rien à faire. La séquence travaille donc autant la reconnaissance que la technique.',
 'Neuf séances, dont deux consacrées à des situations qui ne sont PAS proportionnelles.',
 '["Reconnaître une situation de proportionnalité","Justifier qu''une situation ne l''est pas","Employer le coefficient de proportionnalité","Traiter un pourcentage comme une proportion","Représenter une situation par un tableau ou un graphique"]',
 'Mathématiques', '5e', now(), now()),

-- 26. Éducation aux médias et à l'information
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Comprendre ce qu''un moteur de recherche répond, et à quelle question',
 'Classe de 5e, 28 élèves, une heure par quinzaine au CDI avec la professeure documentaliste. Les élèves tapent une question entière dans la barre de recherche et prennent le premier résultat. Le tri des résultats est le contenu de la séquence.',
 'Six séances au CDI, chacune partant d''une recherche réellement demandée dans une autre matière.',
 '["Formuler une requête avec des mots-clés","Distinguer un résultat sponsorisé d''un résultat ordinaire","Identifier qui publie un site et pourquoi","Comparer deux sources sur une même question","Citer ses sources dans un travail rendu"]',
 'Éducation aux médias et à l’information', '5e', now(), now());
