-- ============================================================================
-- crsa_demo — LE CONTENU PÉDAGOGIQUE, partie 1/6 : les 12 séquences
--
-- BTS CRSA — Conception et Réalisation de Systèmes Automatiques. Rédigé à la
-- main, aucun appel à un fournisseur d'IA.
--
-- POURQUOI 12 ET NON 15. Le référentiel porte quinze matières. Trois sont des
-- enseignements d'appui sans programme propre — langue vivante facultative,
-- accompagnement personnalisé, enseignement complémentaire de culture générale.
-- Elles n'ont pas de séquence ; l'accompagnement personnalisé reste visible en
-- tant que TYPE d'activité, ce qui est sa vraie place.
--
-- Le titre d'une séquence EST son objectif général (colonne `titre`, en Text) :
-- c'est ce que le prof saisit dans la zone d'apport de l'écran Séquence.
-- `competences` est une liste JSON de chaînes, comme partout ailleurs.
-- Matière et niveau se reprennent MOT POUR MOT du référentiel : ce qui n'en
-- vient pas ne se rattache à rien, et l'écran affiche une liste vide.
-- ============================================================================

INSERT INTO sequences (user_id, titre, contexte, ampleur, competences, matiere, niveau, created_at, updated_at) VALUES

-- 1. Culture générale et expression — épreuve E1, coefficient 2
((SELECT id FROM users WHERE email='demo.btscrsa@aschool.fr'),
 'Lire un dossier, en dégager les thèses, et prendre position par écrit',
 'Première et deuxième années, classe entière de 24 étudiants, deux heures hebdomadaires. La promotion vient majoritairement de baccalauréats technologiques STI2D et de baccalauréats professionnels : la lecture longue est peu pratiquée, l''écrit argumenté encore moins. Chaque séance part de documents courts et va vers le dossier complet de l''épreuve.',
 'Une douzaine de séances sur l''année, dont deux épreuves blanches dans les conditions de l''examen : quatre heures, coefficient 2.',
 '["Dégager la thèse et les arguments d''un document","Confronter plusieurs documents de nature différente sur une même question","Rédiger une synthèse objective, organisée et sans opinion personnelle","Construire une écriture personnelle argumentée et référencée","Distinguer l''opinion de l''argument"]',
 'Culture générale et expression', 'BTS CRSA', now(), now()),

-- 2. Langue vivante : anglais — épreuve E2, coefficient 2
((SELECT id FROM users WHERE email='demo.btscrsa@aschool.fr'),
 'Travailler en anglais dans un contexte industriel : comprendre une documentation, expliquer un choix technique',
 'Groupes de 12, salle équipée d''un laboratoire de langues et de postes connectés. Niveau très hétérogène, de A2 à B2. La documentation des constituants d''automatisme — variateurs, automates, capteurs — est presque toujours en anglais : chaque séance s''appuie sur un document professionnel authentique plutôt que sur un texte de manuel.',
 'Sur les deux années, en parallèle des enseignements techniques, avec un entraînement régulier à la prise de parole en continu et à l''interaction.',
 '["Comprendre une documentation technique écrite en anglais","Rendre compte oralement du contenu d''un document","Expliquer et justifier un choix technique à l''oral","Interagir dans une situation professionnelle simulée","Rédiger un courriel professionnel clair et bref"]',
 'Langue vivante : anglais', 'BTS CRSA', now(), now()),

-- 3. Mathématiques — sous-épreuve E31, coefficient 2
((SELECT id FROM users WHERE email='demo.btscrsa@aschool.fr'),
 'Mobiliser les outils mathématiques du comportement des systèmes et de la fiabilité',
 'Classe entière pour les apports, demi-groupe pour les travaux dirigés. Beaucoup d''étudiants ont un rapport difficile aux mathématiques et ne voient pas ce qu''elles font là : chaque notion est introduite par une situation technique — une réponse de vérin, un relevé de panne — avant d''être formalisée.',
 'Une trentaine de séances sur les deux années, adossées aux besoins des enseignements techniques, avec deux devoirs surveillés par trimestre.',
 '["Résoudre une équation différentielle du premier ordre et interpréter sa solution","Identifier une constante de temps sur un relevé expérimental","Exploiter une loi de probabilité dans un contexte de fiabilité","Estimer une grandeur et donner un intervalle de confiance","Justifier un choix technique par un calcul écrit"]',
 'Mathématiques', 'BTS CRSA', now(), now()),

-- 4. Sciences physiques et chimiques appliquées — sous-épreuve E32, coefficient 2
((SELECT id FROM users WHERE email='demo.btscrsa@aschool.fr'),
 'Comprendre la chaîne d''énergie d''un système automatique, de la conversion aux nuisances qu''elle produit',
 'Laboratoire de physique appliquée équipé de bancs de mesure de puissance, d''un motoréducteur instrumenté, d''un sonomètre de classe 2 et d''une caméra thermique. Les étudiants découvrent la plupart des grandeurs : chaque séance part d''une mesure réelle avant tout modèle.',
 'Une vingtaine de séances sur les deux années, systématiquement adossées à une manipulation, avec des situations d''évaluation en contrôle en cours de formation.',
 '["Établir le bilan de puissance d''une chaîne électromécanique","Mesurer un rendement en charge et interpréter les écarts","Caractériser un signal issu d''un capteur","Évaluer une nuisance — bruit, échauffement, corrosion — et proposer une parade","Rendre compte d''une mesure avec son incertitude"]',
 'Sciences physiques et chimiques appliquées', 'BTS CRSA', now(), now()),

-- 5. La communication technique — compétences C1 à C5
((SELECT id FROM users WHERE email='demo.btscrsa@aschool.fr'),
 'Chercher, structurer et transmettre une information technique — à l''écrit, en réunion, devant une commission',
 'Demi-groupes, salle modulable avec table de réunion et vidéoprojecteur. Les étudiants savent chercher sur internet mais ne savent pas encore citer une source, dater une information, ni distinguer une notice constructeur d''un avis d''utilisateur. Le fil de la séquence est le dossier documentaire du projet de deuxième année.',
 'Une dizaine de séances réparties sur les deux années, avec un oral blanc filmé au deuxième trimestre.',
 '["Rechercher, analyser, structurer et synthétiser des informations","Rédiger et mettre en forme un document technique","Organiser et animer une réunion de travail","Échanger avec un interlocuteur en choisissant le moyen adapté","Présenter un travail personnel ou d''équipe et transmettre un savoir-faire"]',
 'La communication technique', 'BTS CRSA', now(), now()),

-- 6. Le besoin — compétences C6 et C7
((SELECT id FROM users WHERE email='demo.btscrsa@aschool.fr'),
 'Décoder un cahier des charges, reformuler un besoin, analyser un existant',
 'Demi-groupes, avec accès à une ligne de conditionnement pédagogique installée en atelier — une machine réelle, ancienne, qui tombe en panne pour de vraies raisons. Le commanditaire fictif est une conserverie de 80 salariés qui veut fiabiliser sa ligne sans la remplacer.',
 'Huit à dix séances au premier trimestre de première année, en amont de la séquence d''avant-projet.',
 '["Décoder un cahier des charges fonctionnel","Distinguer une exigence vérifiable d''une préférence","Reformuler un besoin exprimé en langage courant","Analyser un existant : relever, mesurer, hiérarchiser les défaillances","Proposer des améliorations argumentées et chiffrées"]',
 'Le besoin', 'BTS CRSA', now(), now()),

-- 7. L'avant-projet — compétences C8 à C11, épreuve E4
((SELECT id FROM users WHERE email='demo.btscrsa@aschool.fr'),
 'Conduire un avant-projet : choisir un procédé, comparer des architectures, chiffrer une offre',
 'Deuxième année, demi-groupes, salle de projet équipée de postes de CAO et d''un accès aux catalogues constructeurs. Les étudiants ont traité le besoin au premier trimestre de première année ; ils reprennent le même dossier de conserverie, cette fois pour proposer une solution complète.',
 'Une quinzaine de séances sur le premier trimestre de deuxième année, conclues par une épreuve E4 blanche de quatre heures trente.',
 '["Choisir et justifier un procédé et un processus technique","Organiser les fonctions opératives et comparer des architectures","Définir et organiser les chaînes fonctionnelles et leurs technologies","Évaluer les coûts et les délais, estimer une enveloppe budgétaire","Rédiger une offre commerciale tenant en trois pages"]',
 'L''avant-projet', 'BTS CRSA', now(), now()),

-- 8. Les chaînes fonctionnelles — compétences C12 et C13, sous-épreuve E51
((SELECT id FROM users WHERE email='demo.btscrsa@aschool.fr'),
 'Dimensionner une chaîne fonctionnelle et vérifier son comportement par la simulation puis par la mesure',
 'Demi-groupes en salle de CAO et au laboratoire d''automatismes. Bancs disponibles : axe linéaire à vis à billes motorisé, vérin pneumatique instrumenté, table indexée. Les étudiants disposent des catalogues constructeurs réels ; le dimensionnement se pose à la main avant toute vérification logicielle.',
 'Une quinzaine de séances sur l''année de deuxième année, avec deux situations d''évaluation en contrôle en cours de formation (3 h puis 4 h).',
 '["Dimensionner et choisir les constituants d''une chaîne fonctionnelle","Élaborer et modifier un schéma cinématique","Vérifier une résistance et un comportement statique","Définir le comportement d''une chaîne et le vérifier par simulation","Confronter un résultat de simulation à une mesure"]',
 'Les chaînes fonctionnelles', 'BTS CRSA', now(), now()),

-- 9. Le système — compétences C14 à C16, sous-épreuve E52
((SELECT id FROM users WHERE email='demo.btscrsa@aschool.fr'),
 'Intégrer les chaînes fonctionnelles en un système : interfaces, sécurité, dialogue, comportement d''ensemble',
 'Deuxième année, demi-groupes, salle de CAO et plateau technique. Le système support est un poste de palettisation à trois axes, doté d''un pupitre et d''un réseau de terrain. C''est ici que les étudiants découvrent qu''un système n''est pas la somme de ses chaînes : ce sont les interfaces qui coûtent.',
 'Une quinzaine de séances au deuxième trimestre de deuxième année, avec deux situations d''évaluation en contrôle en cours de formation.',
 '["Définir les interfaces entre chaînes fonctionnelles","Prendre en compte l''ergonomie et la sécurité des personnes","Choisir les constituants de commande, de dialogue et de communication","Définir les structures porteuses, armoires et carters","Vérifier par simulation le comportement spatial et temporel du système"]',
 'Le système', 'BTS CRSA', now(), now()),

-- 10. La réalisation, la mise en service — compétences C17 à C19
((SELECT id FROM users WHERE email='demo.btscrsa@aschool.fr'),
 'Passer du dossier à la machine : réaliser, câbler, configurer, mettre en service et prouver la conformité',
 'Atelier et plateau d''automatismes, équipes de trois, quatre heures d''affilée. Armoires vides, goulottes, borniers, automate, variateur, îlot pneumatique. La consigne qui structure toute la séquence : rien ne se modifie sans sauvegarde préalable, et rien n''est déclaré conforme sans procès-verbal.',
 'Une douzaine de séances longues sur le deuxième trimestre de deuxième année, en parallèle du projet.',
 '["Élaborer un dossier de réalisation et un dossier de tests","Câbler et raccorder d''après un schéma, dans les règles de l''art","Configurer un constituant d''automatisme et sauvegarder sa configuration","Mettre en service une solution et valider sa conformité au cahier des charges","Rédiger un procès-verbal de mise en service, y compris ce qui n''a pas été testé"]',
 'La réalisation, la mise en service', 'BTS CRSA', now(), now()),

-- 11. Le projet — compétences C20 et C21
((SELECT id FROM users WHERE email='demo.btscrsa@aschool.fr'),
 'Piloter un projet : jalons, charges, risques, sécurité et développement durable',
 'Deuxième année, équipes de trois à quatre, une demi-journée hebdomadaire réservée au projet. Chaque équipe a un commanditaire réel — entreprise partenaire ou service technique du lycée — et un budget plafonné. Les revues de jalon se tiennent devant le commanditaire, pas devant le professeur seul.',
 'Sur les deux tiers de l''année de deuxième année, rythmée par trois revues de jalon.',
 '["Mettre en œuvre les outils de la conduite de projet","Découper un projet en tâches, estimer des charges, tenir un planning","Identifier les risques et décider des parades","Rendre compte des dispositions prises en matière de sécurité","Rendre compte des dispositions prises en matière de développement durable"]',
 'Le projet', 'BTS CRSA', now(), now()),

-- 12. Conduite et réalisation d'un projet — sous-épreuves E61 (coef. 2) et E62 (coef. 6)
((SELECT id FROM users WHERE email='demo.btscrsa@aschool.fr'),
 'Le stage, le rapport d''activité et la soutenance : préparer les deux sous-épreuves E61 et E62',
 'Deuxième année, dernier trimestre. Les étudiants reviennent de six semaines de stage en entreprise et achèvent leur projet. Deux échéances distinctes qu''ils confondent souvent : le rapport d''activité en entreprise, coefficient 2, et la conduite et réalisation d''un projet, coefficient 6 — la plus lourde du diplôme.',
 'Six à huit séances au dernier trimestre, dont deux oraux blancs devant une commission composée d''un professeur et d''un professionnel.',
 '["Rédiger un rapport d''activité en entreprise conforme aux attentes","Préparer et tenir un exposé suivi d''un entretien","Soutenir un projet devant une commission d''interrogation","Répondre à une question imprévue sans perdre le fil","Rendre compte honnêtement de ce qui n''a pas fonctionné"]',
 'Conduite et réalisation d''un projet', 'BTS CRSA', now(), now());
