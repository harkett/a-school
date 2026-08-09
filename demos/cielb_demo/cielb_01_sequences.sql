-- ============================================================================
-- cielb_demo — LE CONTENU PÉDAGOGIQUE, partie 1/3 : les 11 séquences
--
-- Une séquence par matière du référentiel BTS CIEL Option B (Informatique et
-- Réseaux). Rédigé à la main, aucun appel à un fournisseur d'IA.
--
-- Le titre d'une séquence EST son objectif général (colonne `titre`, en Text) :
-- c'est ce que le prof saisit dans la zone d'apport de l'écran Séquence.
-- `competences` est une liste JSON de chaînes, comme partout ailleurs.
-- ============================================================================

\set gabarit '(SELECT id FROM users WHERE email = ''demo.btscielb@aschool.fr'')'

INSERT INTO sequences (user_id, titre, contexte, ampleur, competences, matiere, niveau, created_at, updated_at) VALUES

-- 1. Sciences et techniques industrielles (STI) — le cœur de l'option B
((SELECT id FROM users WHERE email='demo.btscielb@aschool.fr'),
 'Concevoir, déployer et sécuriser l''infrastructure réseau d''une PME multi-sites',
 'Deuxième année, groupe de 18 étudiants, laboratoire équipé de commutateurs administrables, de routeurs et de deux baies de brassage. Les étudiants ont vu l''adressage IPv4 et le modèle en couches en première année. L''entreprise support est une PME de 60 salariés répartie sur deux sites reliés par une liaison opérateur.',
 'Une douzaine de séances sur le premier trimestre, en alternance division entière et travaux pratiques en demi-groupe.',
 '["Analyser un besoin client et le traduire en cahier des charges technique","Concevoir un plan d''adressage et un schéma de VLAN","Configurer commutateurs et routeurs, valider par des tests","Sécuriser les accès et journaliser les événements","Documenter et présenter la solution retenue"]',
 'Sciences et techniques industrielles (STI)', 'BTS CIEL Option B', now(), now()),

-- 2. Enseignements professionnel et généraux associés
((SELECT id FROM users WHERE email='demo.btscielb@aschool.fr'),
 'Développer une application métier communicante, de l''expression du besoin au déploiement',
 'Deuxième année, salle informatique, un poste par étudiant, dépôt Git commun. Les étudiants maîtrisent les bases de la programmation objet et l''interrogation d''une base relationnelle. Le commanditaire fictif est un atelier de maintenance qui veut suivre ses interventions depuis une tablette.',
 'Une dizaine de séances, en projet filé, avec deux revues intermédiaires.',
 '["Formaliser un besoin en spécifications exploitables","Concevoir un modèle de données et une interface de programmation","Développer par incréments et versionner son travail","Tester, corriger, et rendre compte de ce qui reste ouvert","Déployer sur un environnement proche du réel"]',
 'Enseignements professionnel et généraux associés', 'BTS CIEL Option B', now(), now()),

-- 3. Mathématiques
((SELECT id FROM users WHERE email='demo.btscielb@aschool.fr'),
 'Mobiliser les outils mathématiques du traitement du signal numérique et de la fiabilité',
 'Première et deuxième années confondues pour la partie révisions, classe entière. Beaucoup d''étudiants viennent de baccalauréats professionnels et ont un rapport difficile aux mathématiques : chaque notion est introduite par une situation technique avant d''être formalisée.',
 'Huit à dix séances, réparties sur l''année, adossées aux besoins des enseignements techniques.',
 '["Représenter et exploiter un signal échantillonné","Manipuler les nombres complexes appliqués aux régimes sinusoïdaux","Interpréter une loi de probabilité dans un contexte de fiabilité","Estimer une grandeur et donner un intervalle de confiance","Justifier un choix technique par un calcul"]',
 'Mathématiques', 'BTS CIEL Option B', now(), now()),

-- 4. Physique
((SELECT id FROM users WHERE email='demo.btscielb@aschool.fr'),
 'Comprendre la transmission de l''information, du signal électrique à la fibre optique',
 'Première année, laboratoire de physique appliquée équipé d''oscilloscopes numériques, de générateurs de fonctions et d''un banc de mesure sur fibre. Les étudiants découvrent la plupart des grandeurs : chaque séance part d''une mesure avant tout modèle.',
 'Une dizaine de séances sur l''année, systématiquement adossées à une manipulation.',
 '["Mesurer et caractériser un signal périodique","Relier bande passante, débit et qualité de transmission","Évaluer l''atténuation d''une liaison et son bilan de puissance","Distinguer les supports de transmission et leurs limites","Rendre compte d''une mesure avec son incertitude"]',
 'Physique', 'BTS CIEL Option B', now(), now()),

-- 5. Culture générale et expression
((SELECT id FROM users WHERE email='demo.btscielb@aschool.fr'),
 'Interroger la place du numérique dans nos vies : lire, confronter, écrire, soutenir un point de vue',
 'Classe entière, deux heures hebdomadaires. Le thème au programme sert de fil : les étudiants lisent des textes de nature différente (essai, article de presse, témoignage, image) et apprennent à ne pas confondre l''opinion et l''argument.',
 'Une douzaine de séances, avec deux évaluations blanches dans les conditions de l''examen.',
 '["Dégager la thèse et les arguments d''un document","Confronter plusieurs documents sur une même question","Rédiger une synthèse objective et organisée","Construire une écriture personnelle argumentée","S''exprimer à l''oral de façon claire et nuancée"]',
 'Culture générale et expression', 'BTS CIEL Option B', now(), now()),

-- 6. Langue vivante étrangère : anglais
((SELECT id FROM users WHERE email='demo.btscielb@aschool.fr'),
 'Travailler en anglais dans un contexte technique : comprendre, expliquer, échanger',
 'Groupes de 15, salle équipée d''un laboratoire de langues. Niveau très hétérogène, de A2 à B2. La documentation technique du métier étant majoritairement en anglais, chaque séance s''appuie sur un document professionnel authentique.',
 'Sur l''année, en parallèle des enseignements techniques, avec un entraînement régulier à l''oral.',
 '["Comprendre une documentation technique écrite","Suivre un échange oral professionnel","Expliquer un dysfonctionnement et proposer une solution","Rédiger un compte rendu bref et exact","Participer à une réunion de projet en anglais"]',
 'Langue vivante étrangère : anglais', 'BTS CIEL Option B', now(), now()),

-- 7. Langue vivante 2
((SELECT id FROM users WHERE email='demo.btscielb@aschool.fr'),
 'Acquérir une seconde langue vivante utile au contexte professionnel européen',
 'Enseignement facultatif, petit groupe de 8 étudiants de niveaux très inégaux, certains grands débutants. L''objectif reste modeste et concret : se présenter, décrire son travail, comprendre l''essentiel d''un échange simple.',
 'Une heure hebdomadaire sur les deux années.',
 '["Se présenter et présenter son parcours","Décrire son environnement de travail","Comprendre les informations essentielles d''un message simple","Échanger dans des situations courantes","Découvrir la culture professionnelle du pays"]',
 'Langue vivante 2', 'BTS CIEL Option B', now(), now()),

-- 8. STI en co-enseignement avec anglais
((SELECT id FROM users WHERE email='demo.btscielb@aschool.fr'),
 'Rédiger et soutenir en anglais la documentation d''une solution technique',
 'Co-animation : le professeur d''anglais et le professeur de STI sont présents ensemble. Les étudiants travaillent sur leur propre projet technique — ce n''est pas un exercice de langue plaqué, c''est leur dossier qu''ils doivent rendre lisible pour un interlocuteur anglophone.',
 'Six séances de deux heures, réparties sur le trimestre du projet.',
 '["Structurer un document technique en anglais","Employer le lexique exact du domaine","Décrire une architecture et justifier un choix","Répondre à des questions techniques imprévues","Adapter son propos à un interlocuteur non francophone"]',
 'STI en co-enseignement avec anglais', 'BTS CIEL Option B', now(), now()),

-- 9. STI en co-enseignement avec mathématiques
((SELECT id FROM users WHERE email='demo.btscielb@aschool.fr'),
 'Dimensionner et justifier par le calcul les choix d''une architecture réseau',
 'Co-animation mathématiques et STI. L''enjeu est de faire tomber la cloison : les étudiants calculent des débits, des files d''attente et des taux de disponibilité sur LEUR maquette, pas sur un énoncé abstrait.',
 'Cinq séances de deux heures, adossées à la séquence d''infrastructure.',
 '["Traduire une contrainte technique en modèle mathématique","Calculer un débit utile et un temps de réponse","Estimer une disponibilité et un taux de panne","Comparer deux solutions par le calcul","Présenter un résultat avec ses hypothèses"]',
 'STI en co-enseignement avec mathématiques', 'BTS CIEL Option B', now(), now()),

-- 10. STI en co-enseignement avec physique
((SELECT id FROM users WHERE email='demo.btscielb@aschool.fr'),
 'Diagnostiquer une liaison défaillante en croisant mesure physique et analyse réseau',
 'Co-animation physique et STI, en laboratoire. Une liaison est volontairement dégradée (atténuation, réflexion, brouillage) : les étudiants doivent décider si la cause est physique ou logique, et le prouver.',
 'Cinq séances de deux heures, en demi-groupe.',
 '["Mesurer les caractéristiques physiques d''une liaison","Lire et interpréter une capture de trames","Distinguer une cause physique d''une cause de configuration","Construire une démarche de diagnostic ordonnée","Rédiger un rapport d''intervention exploitable"]',
 'STI en co-enseignement avec physique', 'BTS CIEL Option B', now(), now()),

-- 11. Accompagnement personnalisé
((SELECT id FROM users WHERE email='demo.btscielb@aschool.fr'),
 'Consolider ses méthodes de travail et construire son projet après le BTS',
 'Groupes à effectif variable, constitués selon les besoins repérés au conseil de classe. Certains étudiants ont besoin de reprendre des bases, d''autres préparent une poursuite d''études en licence professionnelle ou en école d''ingénieurs.',
 'Une heure hebdomadaire, avec des groupes qui se recomposent toutes les six semaines.',
 '["Identifier ses points d''appui et ses fragilités","Organiser son travail personnel dans la durée","Reprendre une notion non acquise avec une autre entrée","Préparer un dossier de poursuite d''études","Se présenter en entretien"]',
 'Accompagnement personnalisé', 'BTS CIEL Option B', now(), now());
