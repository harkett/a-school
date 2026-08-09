-- ============================================================================
-- ergo_demo — LE CONTENU PÉDAGOGIQUE, partie 1/6 : les 6 séquences
--
-- Licence Ergothérapie (arrêté du 5 juillet 2010, annexes IV et V). Rédigé à
-- la main, aucun appel à un fournisseur d'IA.
--
-- POURQUOI 6 ET NON DAVANTAGE. Le référentiel porte six matières, et ces six
-- matières SONT les six domaines d'unités d'enseignement du diplôme (UE 1.x à
-- UE 6.x). Chacune a un programme propre : aucune n'est un enseignement
-- d'appui. Une séquence par matière, donc, et pas une de plus.
--
-- LE VOCABULAIRE EST CELUI DE CE DIPLÔME, pas celui d'un BTS. Ici on parle
-- d'unités d'enseignement, de semestres S1 à S6, de crédits ECTS, de CM, de TD
-- et de travail personnel, de compétences 1 à 10, de stages cliniques et
-- d'unités d'intégration. Aucun coefficient, aucune épreuve E4 : ce diplôme ne
-- valide pas ainsi.
--
-- Le titre d'une séquence EST son objectif général (colonne `titre`, en Text) :
-- c'est ce que le prof saisit dans la zone d'apport de l'écran Séquence.
-- `competences` est une liste JSON de chaînes, comme partout ailleurs.
-- Matière et niveau se reprennent MOT POUR MOT du référentiel : ce qui n'en
-- vient pas ne se rattache à rien, et l'écran affiche une liste vide.
-- ============================================================================

INSERT INTO sequences (user_id, titre, contexte, ampleur, competences, matiere, niveau, created_at, updated_at) VALUES

-- 1. Sciences humaines, sociales et droit — UE 1.1 à 1.7, compétences 6, 7 et 9
((SELECT id FROM users WHERE email='demo.ergo@aschool.fr'),
 'Situer l''exercice de l''ergothérapeute dans son cadre légal, institutionnel et social',
 'Les UE 1.3 et 1.5 se donnent au semestre 1, l''UE 1.7 au semestre 2, l''UE 1.1 au semestre 5. Promotion de 32 étudiants, majoritairement issus d''une première année de santé ou d''une licence de sciences. Ils arrivent avec l''idée que le droit est un décor administratif ; la séquence part chaque fois d''une situation où la règle décide de ce qu''on a le droit de faire au lit du patient.',
 'Une quinzaine de séances réparties sur les semestres 1, 2 et 5, en cours magistral pour les apports et en travaux dirigés pour les situations. Évaluation écrite en fin de semestre 5.',
 '["Citer le décret d''actes et de compétences de l''ergothérapeute et en délimiter le champ","Distinguer secret professionnel, discrétion et partage d''informations dans une équipe","Repérer les acteurs institutionnels d''un parcours de soin et de compensation","Analyser une situation où l''intérêt de la personne et la règle ne coïncident pas","Argumenter une position éthique sans la confondre avec une préférence personnelle"]',
 'Sciences humaines, sociales et droit', 'Licence Ergothérapie', now(), now()),

-- 2. Sciences médicales — UE 2.1 à 2.6, compétences 1 et 3
((SELECT id FROM users WHERE email='demo.ergo@aschool.fr'),
 'Relier une atteinte anatomique ou physiologique aux incapacités qu''elle produit dans l''activité',
 'Semestres 1 à 4, promotion entière pour les cours magistraux, demi-groupes de 16 pour les travaux dirigés en salle de bilan. Le laboratoire dispose de squelettes articulés, de goniomètres, d''un dynamomètre Jamar et de deux mannequins de positionnement. La difficulté propre à ces UE est connue : les étudiants apprennent l''anatomie comme une nomenclature et ne savent pas encore en déduire ce qu''une personne ne peut plus faire. Chaque séance repart donc de l''activité empêchée pour remonter à la lésion.',
 'Une trentaine de séances sur les quatre premiers semestres, adossées aux UE 2.1 S1 et S2, 2.3 S1, 2.4 S2, 2.5 S3 et 2.6 S4. Évaluation écrite en fin de chaque semestre concerné.',
 '["Nommer les structures anatomiques du membre supérieur et leurs fonctions organiques","Mesurer une amplitude articulaire et une force segmentaire avec l''outil adapté","Déduire d''un territoire lésionnel neurologique les incapacités attendues dans l''activité","Repérer les manifestations d''un dysfonctionnement cognitif dans une tâche quotidienne","Rendre compte par écrit d''une observation clinique, en séparant le constat de l''interprétation"]',
 'Sciences médicales', 'Licence Ergothérapie', now(), now()),

-- 3. Fondements et processus de l'ergothérapie — UE 3.1 à 3.6, compétences 1, 2 et 6
((SELECT id FROM users WHERE email='demo.ergo@aschool.fr'),
 'S''approprier les modèles conceptuels de l''ergothérapie et conduire un diagnostic ergothérapique',
 'Semestres 1 à 3, cœur de l''identité professionnelle. Groupes de 16, salle modulable avec tables mobiles. C''est la séquence qui déstabilise le plus : les étudiants attendent des techniques et reçoivent des cadres de pensée. L''UE 3.1 S1 leur demande de se percevoir eux-mêmes comme des êtres d''activité avant de considérer l''impact d''une pathologie — ce détour paraît long, et c''est pourtant lui qui rend le diagnostic ergothérapique possible.',
 'Une vingtaine de séances sur les semestres 1 à 3. Le travail écrit de fin de semestre 1 est commun aux UE 3.1 S1 et 3.5 S1 : une partie sur la science de l''activité humaine, l''autre sur le diagnostic et le processus d''intervention.',
 '["Définir l''ergothérapie, son champ d''exercice et ses valeurs professionnelles","Distinguer activité signifiante et activité significative sur un cas réel","Mobiliser un modèle conceptuel pour organiser un recueil de données","Formuler un diagnostic ergothérapique qui nomme la situation de handicap, non la pathologie","Poser un cadre thérapeutique et en repérer les ruptures"]',
 'Fondements et processus de l''ergothérapie', 'Licence Ergothérapie', now(), now()),

-- 4. Méthodes, techniques et outils d'intervention de l'ergothérapeute — UE 4.1 à 4.10, compétences 3, 4 et 5
((SELECT id FROM users WHERE email='demo.ergo@aschool.fr'),
 'Conduire une intervention : évaluer, rééduquer, appareiller, aménager, éduquer',
 'Semestres 1 à 5, la matière la plus lourde du diplôme en volume horaire. Travaux pratiques en demi-groupes de 16 dans l''atelier d''appareillage — bacs thermoformables, pistolets à air chaud, matériel de sangles, établis — et en salle d''activités. Les étudiants manipulent dès le semestre 1 ; l''erreur fréquente est de choisir une technique avant d''avoir posé l''objectif, et l''atelier la rend visible immédiatement : une orthèse faite sans objectif ne tient sur rien.',
 'Une quarantaine de séances sur cinq semestres, avec une épreuve pratique d''appareillage au semestre 4 et un dossier d''aménagement au semestre 2.',
 '["Choisir et conduire un bilan adapté à la situation et à la personne","Concevoir, réaliser et adapter une orthèse provisoire à visée fonctionnelle","Sélectionner une aide technique et en assurer l''essai et le réglage","Élaborer un projet d''aménagement de l''environnement et en argumenter les choix","Conduire une séance d''éducation thérapeutique auprès d''une personne ou d''un aidant"]',
 'Méthodes, techniques et outils d''intervention de l''ergothérapeute', 'Licence Ergothérapie', now(), now()),

-- 5. Méthodes de travail — UE 5.1 à 5.6, compétences 7 et 8
((SELECT id FROM users WHERE email='demo.ergo@aschool.fr'),
 'Chercher, traiter et écrire : de la recherche documentaire au mémoire d''initiation à la recherche',
 'Semestres 1 à 6, en salle informatique puis en tutorat. Les étudiants savent chercher, ils ne savent pas encore trier : la première séance de recherche documentaire produit invariablement une bibliographie de sites commerciaux d''aides techniques. Le fil de la séquence est le mémoire d''initiation à la démarche de recherche des UE 5.4 S5 et S6, préparé dès le semestre 1 par les méthodes de travail et l''anglais professionnel.',
 'Une vingtaine de séances sur les six semestres, avec deux jalons de tutorat individuel au semestre 5 et la soutenance du mémoire au semestre 6.',
 '["Construire une équation de recherche et interroger une base de données scientifique","Évaluer la fiabilité d''une source et citer selon une norme constante","Rédiger une synthèse de plusieurs articles sans les juxtaposer","Formuler une question de recherche opérationnelle et délimitée","Conduire un projet écrit sur deux semestres en tenant un calendrier"]',
 'Méthodes de travail', 'Licence Ergothérapie', now(), now()),

-- 6. Intégration des savoirs et posture professionnelle de l'ergothérapeute — UE 6.1 à 6.6 et stages, compétences 1 à 10
((SELECT id FROM users WHERE email='demo.ergo@aschool.fr'),
 'Faire tenir ensemble les savoirs sur une situation réelle, et construire sa posture professionnelle',
 'Semestres 2 à 6, autour des stages cliniques et des unités d''intégration. Groupes d''analyse de pratique de 8 étudiants, animés par un formateur et, deux fois par an, par un ergothérapeute de terrain. C''est ici que se règle ce qu''aucune UE théorique ne règle : ce qu''on fait quand la personne ne veut pas, quand l''équipe n''est pas d''accord, quand on s''est trompé. Les stages représentent soixante semaines sur les trois années.',
 'Une quinzaine de séances réparties sur les semestres 2 à 6, en amont et en aval de chaque stage, plus les entretiens individualisés de suivi pédagogique.',
 '["Mobiliser sur une situation unique des savoirs venus de plusieurs unités d''enseignement","Analyser une situation professionnelle vécue en stage, sans se justifier ni s''accuser","Repérer ce qui, dans sa propre pratique, relève de la technique et ce qui relève de la posture","Rendre compte de son parcours de formation et en identifier les manques","Recevoir un désaccord d''équipe et y répondre professionnellement"]',
 'Intégration des savoirs et posture professionnelle de l''ergothérapeute', 'Licence Ergothérapie', now(), now());
