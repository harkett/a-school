-- ============================================================================
-- college4e — 3e, partie 1/3 : les 13 séquences
--
-- Troisième et dernière année du cycle 4. Le référentiel 21 la dessert comme
-- il dessert la 5e et la 4e.
--
-- CE QUI EST PROPRE À LA 3e vient des unités datées du référentiel :
--   Français   — se raconter, dénoncer, visions poétiques, agir dans la cité,
--                progrès et rêves scientifiques (unités 37 à 41)
--   Histoire   — les guerres totales, le monde depuis 1945, la République
--                repensée (107 à 109)
--   Géographie — dynamiques territoriales, aménager, la France et l'UE (116-118)
-- Les onze autres disciplines ont un programme de CYCLE : le contenu retenu
-- suit la progression usuelle de l'année de troisième.
--
-- Les identifiants continuent : séquences 27 à 39.
-- ============================================================================

INSERT INTO sequences (user_id, titre, contexte, ampleur, competences, matiere, niveau, created_at, updated_at) VALUES

-- 27. Français — « Se raconter, se représenter »
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Écrire sur soi sans se raconter d''histoires',
 'Classe de 3e, 26 élèves, quatre heures et demie hebdomadaires. Le questionnement de l''écriture de soi tombe au bon moment : les élèves ont quinze ans et une idée très arrêtée de ce qu''ils sont. La difficulté n''est pas de les faire écrire sur eux, c''est de leur faire voir qu''un souvenir se reconstruit.',
 'Huit séances sur cinq semaines, autour d''extraits autobiographiques et d''autoportraits, et d''un texte personnel repris deux fois.',
 '["Lire un texte autobiographique en repérant ce qui est reconstruit","Distinguer le narrateur adulte de l''enfant qu''il raconte","Écrire un souvenir en assumant le point de vue d''aujourd''hui","Reprendre son texte après une lecture critique","Employer les temps du récit et du commentaire"]',
 'Français', '3e', now(), now()),

-- 28. Langues vivantes
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Parler de ce qu''on veut faire, et de ce qu''on ne sait pas encore',
 'Classe de 3e, anglais LV1, 26 élèves, trois heures hebdomadaires. Niveau visé A2+ vers B1. Le stage d''observation vient d''avoir lieu : tout le monde a quelque chose à raconter, et c''est l''occasion de travailler le récit au passé et le projet au futur dans une même séquence.',
 'Sept séances sur quatre semaines, autour du stage, des métiers et de ce qu''on envisage après la troisième.',
 '["Comprendre un témoignage oral sur un métier","Employer les formes du futur et de l''intention","Présenter son stage en continu pendant deux minutes","Lire à haute voix un texte préparé","Rendre compte du projet d''un camarade"]',
 'Langues vivantes (étrangères ou régionales)', '3e', now(), now()),

-- 29. Arts plastiques
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Faire une œuvre pour un endroit précis, et pas pour un mur quelconque',
 'Classe de 3e, 26 élèves, une heure hebdomadaire. Les élèves conçoivent leurs productions comme des objets autonomes, à accrocher n''importe où. La séquence part du contraire : l''œuvre est faite pour un lieu du collège, et elle n''a plus de sens ailleurs.',
 'Six séances : repérage des lieux, projet, réalisation in situ, et documentation photographique.',
 '["Concevoir une production pour un lieu déterminé","Employer l''échelle et le point de vue comme moyens","Documenter une œuvre éphémère par la photographie","Parler de son travail avec un vocabulaire précis","Situer sa démarche par rapport à une référence artistique"]',
 'Arts plastiques', '3e', now(), now()),

-- 30. Éducation musicale
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Comprendre comment une musique prend parti',
 'Classe de 3e, 26 élèves, une heure hebdomadaire. Le groupe écoute beaucoup et sait dire ce qu''il aime. La séquence déplace la question : par quels moyens musicaux une chanson engagée agit-elle sur celui qui l''écoute ?',
 'Six séances : trois écoutes comparées d''œuvres engagées, un travail vocal, une réalisation en binômes.',
 '["Décrire les moyens musicaux d''une œuvre engagée","Distinguer le propos du texte et l''effet de la musique","Situer une œuvre dans son contexte historique","Chanter en groupe en respectant la mise en place","Justifier un choix devant la classe"]',
 'Éducation musicale', '3e', now(), now()),

-- 31. Histoire des arts
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Regarder des œuvres qui ont eu affaire au pouvoir',
 'Classe de 3e, 26 élèves, une heure tous les quinze jours, en co-intervention avec l''histoire-géographie. La séquence accompagne le programme de l''année : guerres totales, régimes totalitaires, engagement.',
 'Cinq séances de deux heures sur le trimestre, autour d''œuvres de commande, d''œuvres censurées et d''œuvres de témoignage.',
 '["Décrire une œuvre avant de l''interpréter","Distinguer une œuvre de commande d''une œuvre de témoignage","Comparer deux œuvres traitant du même événement","Se repérer dans une collection en ligne","Présenter une œuvre à l''oral en la situant"]',
 'Histoire des arts', '3e', now(), now()),

-- 32. Éducation physique et sportive
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Jouer sans arbitre : l''ultimate et la règle qu''on se donne',
 'Classe de 3e, 26 élèves, deux séances hebdomadaires dont une de deux heures. L''ultimate se joue sans arbitre, y compris en compétition : les joueurs signalent leurs propres fautes. C''est ce qui en fait un support d''EPS et pas seulement un sport de plus.',
 'Six séances d''ultimate en équipes stables, avec un temps de régulation collective à chaque séance.',
 '["Se déplacer et se démarquer dans un espace partagé","Signaler sa propre faute et accepter celle qu''on nous signale","Résoudre un désaccord de jeu sans arbitre extérieur","Observer une équipe et rendre compte de son organisation","Tenir un projet de jeu collectif sur une séance"]',
 'Éducation physique et sportive', '3e', now(), now()),

-- 33. Enseignement moral et civique
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Jusqu''où va une liberté quand elle rencontre celle des autres',
 'Classe de 3e, 26 élèves, une heure hebdomadaire. À quinze ans, la liberté d''expression est invoquée dans toutes les discussions et presque jamais définie. La séquence part de textes réels — la loi, la jurisprudence — plutôt que d''opinions.',
 'Six séances : deux sur les textes, trois sur des cas concrets, une sur la production collective.',
 '["Chercher ce que dit le droit avant de dire ce qu''on ressent","Distinguer une opinion, une information et une injure","Écouter un avis contraire jusqu''au bout","Argumenter une position en citant un texte","Rendre compte d''une discussion par écrit"]',
 'Enseignement moral et civique', '3e', now(), now()),

-- 34. Histoire et géographie
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Comprendre ce que veut dire « guerre totale »',
 'Classe de 3e, 26 élèves, trois heures et demie hebdomadaires. Premier thème de l''année. Les élèves connaissent les deux guerres par les commémorations et par les films ; l''enjeu est de passer de l''image à ce que le mot « totale » recouvre : les civils, l''économie, l''arrière, les colonies.',
 'Huit séances appuyées sur des lettres de soldats, des affiches de mobilisation économique et des données chiffrées.',
 '["Confronter des documents de nature différente","Distinguer le front et l''arrière dans une guerre totale","Exploiter des données chiffrées et en tirer une phrase","Réaliser un croquis de l''extension d''un conflit","Rédiger un développement construit d''une vingtaine de lignes"]',
 'Histoire et géographie', '3e', now(), now()),

-- 35. Physique-Chimie
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Suivre l''énergie d''un bout à l''autre d''une chaîne',
 'Classe de 3e, 26 élèves, une heure et demie hebdomadaire dont une heure en demi-groupe. Les élèves emploient le mot « énergie » tous les jours sans pouvoir dire ce qui se conserve et ce qui se perd. La séquence installe la chaîne énergétique comme outil de description.',
 'Sept séances dont quatre expérimentales, autour des conversions et du rendement.',
 '["Identifier les formes d''énergie en jeu dans une situation","Représenter une chaîne énergétique","Mesurer une puissance et calculer une énergie","Distinguer ce qui se conserve de ce qui se dégrade","Rédiger un compte rendu qui permette de refaire l''expérience"]',
 'Physique-Chimie', '3e', now(), now()),

-- 36. Sciences de la vie et de la Terre
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Comprendre pourquoi on ressemble à ses parents sans leur être identique',
 'Classe de 3e, 26 élèves, une heure et demie hebdomadaire dont une heure en demi-groupe. Le sujet touche aux familles : il se traite avec précision et sans jamais partir des ressemblances réelles des élèves de la classe.',
 'Sept séances : trois d''étude de documents, deux de modélisation, deux de synthèse.',
 '["Relier un caractère à l''information génétique","Distinguer un caractère héréditaire d''un caractère acquis","Exploiter un arbre généalogique simple","Distinguer un modèle de la réalité qu''il représente","Employer avec justesse gène, allèle, chromosome"]',
 'Sciences de la vie et de la Terre', '3e', now(), now()),

-- 37. Technologie
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Faire faire à un objet ce qu''on lui demande — et savoir ce qu''il enregistre',
 'Classe de 3e, 26 élèves, une heure et demie hebdomadaire. Le projet de l''année porte sur un objet programmable installé dans le collège. La question des données collectées n''est pas un supplément : elle est dans le cahier des charges.',
 'Huit séances en projet, par équipes de quatre, avec deux revues de projet et un prototype fonctionnel.',
 '["Décomposer un besoin en fonctions à programmer","Écrire et corriger un programme simple","Représenter une solution par un croquis et un algorithme","Réaliser un prototype fonctionnel et l''éprouver","Dire quelles données l''objet collecte, et pourquoi"]',
 'Technologie', '3e', now(), now()),

-- 38. Mathématiques
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Calculer une longueur qu''on ne peut pas mesurer',
 'Classe de 3e, 26 élèves, trois heures et demie hebdomadaires. Thalès et la trigonométrie arrivent ensemble dans la séquence, parce qu''ils répondent à la même question posée autrement. Les élèves cherchent d''abord à mesurer ; la séquence les met dans des situations où c''est impossible.',
 'Neuf séances, dont deux passées dehors à mesurer ce qui peut l''être pour calculer ce qui ne le peut pas.',
 '["Reconnaître une configuration de Thalès","Employer le cosinus, le sinus et la tangente à bon escient","Choisir entre Thalès et la trigonométrie selon les données","Rédiger un calcul en citant la propriété employée","Estimer la précision d''un résultat issu d''une mesure"]',
 'Mathématiques', '3e', now(), now()),

-- 39. Éducation aux médias et à l'information
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Comprendre ce qui décide de ce qu''on nous montre',
 'Classe de 3e, 26 élèves, une heure par quinzaine au CDI avec la professeure documentaliste. Les élèves savent qu''un algorithme choisit ce qu''ils voient ; ils l''expliquent par des théories approximatives. La séquence part de ce qu''on peut réellement observer et vérifier.',
 'Six séances au CDI, appuyées sur les paramètres réels des plateformes et sur des expériences menées en classe.',
 '["Expliquer ce qui décide de l''ordre d''un fil","Distinguer ce qu''on choisit de ce qui est choisi pour soi","Lire les paramètres de confidentialité d''un service","Vérifier une information avant de la partager","Produire un contenu qui cite ses sources"]',
 'Éducation aux médias et à l’information', '3e', now(), now());
