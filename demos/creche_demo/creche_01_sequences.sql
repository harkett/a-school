-- ============================================================================
-- creche_demo — LE CONTENU PÉDAGOGIQUE, partie 1/3 : les 5 séquences
--
-- Une séquence par matière du référentiel d'éveil 0-3 ans (Crèche · Moyens-Grands 1-3 ans).
-- Rédigé à la main, aucun appel à un fournisseur d'IA.
--
-- CE QUI CHANGE PAR RAPPORT AUX DÉMONSTRATIONS DE BTS. Le public, ce sont des
-- professionnels de la petite enfance, et les enfants n'ont pas d'épreuve à
-- passer. Aucun barème, aucun devoir, aucune note : ce qu'on écrit ici, c'est
-- ce que l'adulte prépare, propose et observe. Le vocabulaire est celui du
-- référentiel lui-même — « jeu avec un jouet », « rituel collectif »,
-- « échange individuel ».
--
-- Le titre d'une séquence EST son objectif général (colonne `titre`, en Text) :
-- c'est ce que le professionnel saisit dans la zone d'apport de l'écran
-- Séquence. `competences` est une liste JSON de chaînes, comme partout ailleurs
-- — ici ce sont les acquisitions visées chez l'enfant, pas des compétences
-- d'examen.
-- ============================================================================

INSERT INTO sequences (user_id, titre, contexte, ampleur, competences, matiere, niveau, created_at, updated_at) VALUES

-- 1. Motricité et coordination
((SELECT id FROM users WHERE email='demo.creche@aschool.fr'),
 'Conquérir ses appuis et affiner son geste, du ramper aux premiers pas assurés',
 'Section des moyens, douze enfants de 12 à 30 mois, deux professionnelles. La salle dispose d''un tapis d''évolution, d''un petit module de mousse et d''un coin calme séparé par une étagère basse. Trois enfants marchent depuis peu, deux se déplacent encore à quatre pattes, les autres sont assurés. Le groupe est mélangé volontairement : les plus petits imitent, les plus grands ralentissent.',
 'Une dizaine de propositions étalées sur six semaines, en petits groupes de quatre, toujours sur le temps du matin où les enfants sont les plus disponibles.',
 '["Se déplacer avec de plus en plus d''assurance, en variant les appuis","Attraper, tenir, lâcher volontairement un objet","Coordonner son regard et sa main sur une cible précise","Oser un déplacement nouveau en présence sécurisante d''un adulte","Retrouver son calme après un temps de grande dépense"]',
 'Motricité et coordination', 'Moyens-Grands (1-3 ans)', now(), now()),

-- 2. Réflexion, raisonnement et repérage de l'environnement
((SELECT id FROM users WHERE email='demo.creche@aschool.fr'),
 'Comprendre que les choses tiennent ensemble : trier, ranger, retrouver, anticiper',
 'Section des grands, dix enfants de 24 à 36 mois. Le matériel de manipulation est rangé à hauteur d''enfant, sur une étagère à trois niveaux, chaque bac portant la photo de son contenu. Les enfants vont le chercher seuls : la séquence s''appuie sur ce libre accès plutôt que de le remplacer.',
 'Huit propositions sur deux mois, en groupe de trois ou quatre autour d''une table basse, jamais plus de vingt minutes.',
 '["Associer deux objets qui vont ensemble, et dire pourquoi","Trier selon un seul critère : la couleur, puis la taille","Reconstituer un ensemble à partir de ses parties","Retrouver un objet caché, puis anticiper où il se trouve","Nommer ce que l''on vient de faire, avec ses mots"]',
 'Réflexion, raisonnement et repérage de l''environnement', 'Moyens-Grands (1-3 ans)', now(), now()),

-- 3. Langage
((SELECT id FROM users WHERE email='demo.creche@aschool.fr'),
 'Donner envie de parler : accueillir le son, nommer le monde, entrer dans l''histoire',
 'Groupe d''âges mêlés, huit enfants de 10 à 32 mois, dont trois entendent une autre langue à la maison et deux ne produisent encore que des syllabes redoublées. Le coin lecture est installé au sol, avec des coussins, à l''écart du passage. Les livres sont laissés à disposition toute la journée, jamais rangés en hauteur.',
 'Un rendez-vous quotidien court — dix minutes — plus deux propositions plus longues par semaine, sur toute la période entre les vacances d''automne et Noël.',
 '["Répondre à une sollicitation vocale par un son, un geste, un regard","Comprendre une consigne simple donnée sans geste d''accompagnement","Nommer les objets et les personnes de son quotidien","Écouter une histoire courte jusqu''au bout, réclamer la suivante","Prendre la parole dans un échange à deux, et attendre son tour"]',
 'Langage', 'Moyens-Grands (1-3 ans)', now(), now()),

-- 4. Créativité, imagination et expression
((SELECT id FROM users WHERE email='demo.creche@aschool.fr'),
 'Laisser une trace, faire semblant, se faire entendre : les premières formes d''expression',
 'Section des moyens et des grands réunie, quatorze enfants de 18 à 36 mois, deux professionnelles et un espace atelier avec sol lavable. Les blouses sont accessibles aux enfants. Le principe posé en équipe : on n''écrit jamais sur la production d''un enfant, on écrit à côté, et on ne retouche rien.',
 'Six ateliers sur six semaines, par groupes de six, plus un temps d''expression sonore chaque vendredi avec le groupe entier.',
 '["Laisser une trace volontaire et la regarder","Explorer une matière avec les mains avant d''en faire quelque chose","Prêter une voix et une intention à un objet","Produire un son avec son corps, puis avec un objet","Montrer ce qu''on a fait, et accepter que ce soit vu"]',
 'Créativité, imagination et expression', 'Moyens-Grands (1-3 ans)', now(), now()),

-- 5. Aptitudes sociales, confiance et sécurité affective
((SELECT id FROM users WHERE email='demo.creche@aschool.fr'),
 'Se sentir attendu, se séparer sans se perdre, et faire une place à l''autre',
 'Section des petits, neuf enfants de 8 à 20 mois, dont quatre arrivés depuis moins d''un mois. Deux professionnelles référentes se partagent le groupe, chacune suivant les mêmes enfants au repas, au change et à l''endormissement. Les doudous sont accessibles à tout moment, dans un bac ouvert à hauteur d''enfant, jamais confisqués.',
 'Une séquence de fond, tenue sur tout le premier trimestre : ce sont les mêmes rituels répétés qui font le travail, pas la nouveauté.',
 '["Reconnaître les temps de la journée et les anticiper","Se séparer de son parent en s''appuyant sur un objet et une personne connus","Exprimer une émotion forte et se laisser apaiser","Repérer un autre enfant, le regarder, l''imiter","Attendre son tour dans un temps collectif court"]',
 'Aptitudes sociales, confiance et sécurité affective', 'Moyens-Grands (1-3 ans)', now(), now());
