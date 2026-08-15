-- ============================================================================
-- college4e — LE CONTENU PÉDAGOGIQUE, partie 1/6 : les 13 séquences
--
-- Collège · 4e — programme du cycle des approfondissements (cycle 4), annexe 3
-- du BOEN n° 31 du 30 juillet 2020. Rédigé à la main, aucun appel à un
-- fournisseur d'IA.
--
-- UNE SÉQUENCE PAR MATIÈRE, les treize disciplines du référentiel. Aucune n'est
-- écartée : contrairement au BTS CRSA, ce programme ne porte pas d'enseignement
-- d'appui sans contenu propre.
--
-- Le titre d'une séquence EST son objectif général (colonne `titre`, en Text) :
-- c'est ce que le prof saisit dans la zone d'apport de l'écran Séquence.
-- `competences` est une liste JSON de chaînes, comme partout ailleurs.
-- Matière et niveau se reprennent MOT POUR MOT du référentiel : la matière
-- telle qu'elle est écrite dans `matieres.nom` (apostrophe typographique dans
-- « Éducation aux médias et à l'information »), et le niveau seul — `4e`, pas
-- « Collège · 4e », qui est un libellé fabriqué par l'écran et jamais stocké.
--
-- LE TON DU CYCLE 4. Ni épreuve, ni coefficient, ni barème d'examen : un
-- programme de collège n'en porte pas. Les repères d'évaluation sont formulés
-- en attendus de fin de cycle et en degrés de maîtrise, comme le fait le socle.
-- ============================================================================

INSERT INTO sequences (user_id, titre, contexte, ampleur, competences, matiere, niveau, created_at, updated_at) VALUES

-- 1. Français
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Lire une nouvelle réaliste jusque dans ses non-dits, et écrire à son tour',
 'Classe de 4e, 27 élèves, quatre heures et demie hebdomadaires. Trois élèves bénéficient d''un PAP, dont deux pour un trouble du langage écrit : les textes longs leur sont donnés en amont et en version aérée. Le groupe lit volontiers à voix haute mais bute sur l''implicite — ce que le texte laisse entendre sans le dire reste invisible pour la moitié de la classe.',
 'Huit séances sur cinq semaines, autour de trois nouvelles de Maupassant et d''un corpus de fins ouvertes. La séquence s''achève sur une nouvelle écrite par chaque élève, retravaillée deux fois.',
 '["Lire et comprendre un texte littéraire en repérant ce qu''il ne dit pas","Interpréter une fin ouverte et défendre son interprétation devant les autres","Écrire un récit bref qui tient sur une chute","Reprendre son propre texte après une lecture critique","Maîtriser l''accord du participe passé employé avec avoir"]',
 'Français', '4e', now(), now()),

-- 2. Langues vivantes (étrangères ou régionales)
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Raconter un souvenir au passé, à l''écrit puis devant les autres',
 'Classe de 4e, anglais LV1, 27 élèves, trois heures hebdomadaires en groupe entier. Niveau visé A2 confirmé, quelques élèves en B1 sur la compréhension orale. La prise de parole en continu est le point faible : les élèves écrivent correctement et se taisent dès qu''il faut parler sans lire.',
 'Sept séances sur quatre semaines. Le fil est un récit personnel court, travaillé d''abord à l''écrit, puis dit sans notes, puis enregistré.',
 '["Comprendre un récit oral simple au passé","Employer le prétérit simple et le passé progressif à bon escient","Raconter un événement personnel en continu pendant une minute","Lire à haute voix un texte préparé avec une intonation juste","Rendre compte brièvement d''un document écouté"]',
 'Langues vivantes (étrangères ou régionales)', '4e', now(), now()),

-- 3. Arts plastiques
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Fabriquer une image qui raconte autre chose que ce qu''elle montre',
 'Classe de 4e, 27 élèves, une heure hebdomadaire en salle d''arts plastiques. Matériel disponible : papiers, encres, six tablettes, un appareil photo numérique. Les élèves associent encore « réussir » à « ressembler » : le travail de l''année porte justement sur l''écart entre ce qu''on montre et ce qu''on fait comprendre.',
 'Six séances d''une heure, une production par élève à chaque séance, et un accrochage collectif en fin de séquence.',
 '["Choisir un cadrage et un point de vue pour orienter la lecture d''une image","Employer le montage et le collage comme moyens de récit","Distinguer ce qu''une image montre de ce qu''elle suggère","Parler de son travail et de celui des autres avec un vocabulaire précis","Réinvestir une référence artistique dans sa propre production"]',
 'Arts plastiques', '4e', now(), now()),

-- 4. Éducation musicale
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Comprendre comment un même thème change de sens quand il change d''habillage',
 'Classe de 4e, 27 élèves, une heure hebdomadaire. Salle équipée d''un clavier, de percussions et de six postes d''écoute. Le groupe chante sans réticence mais qualifie tout ce qu''il entend par « j''aime / j''aime pas » : l''objectif de la séquence est de remplacer le jugement par la description.',
 'Six séances : trois écoutes comparées, un travail vocal filé, et une réalisation numérique par binômes.',
 '["Décrire une musique avec un vocabulaire technique plutôt qu''un jugement","Repérer un même thème sous des arrangements différents","Chanter en respectant la justesse et la mise en place collective","Réaliser un court montage sonore qui transforme un thème donné","Justifier un choix d''écoute devant la classe"]',
 'Éducation musicale', '4e', now(), now()),

-- 5. Histoire des arts
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Regarder deux œuvres qui traitent du même sujet à deux siècles d''écart',
 'Classe de 4e, 27 élèves, l''enseignement est pris en charge alternativement par le professeur d''histoire-géographie et celui d''arts plastiques, une heure tous les quinze jours. Aucun musée à moins d''une heure de car : les visites se font en ligne, ce que la séquence assume au lieu de le subir.',
 'Cinq séances de deux heures réparties sur le trimestre, autour du couple œuvre ancienne / œuvre contemporaine sur le thème du travail.',
 '["Décrire une œuvre avant de l''interpréter","Situer une œuvre dans son époque et dans son contexte de production","Comparer deux œuvres sans les hiérarchiser","Se repérer dans une collection en ligne et y prélever ce qui sert son propos","Présenter une œuvre à l''oral devant la classe"]',
 'Histoire des arts', '4e', now(), now()),

-- 6. Éducation physique et sportive
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Construire un projet de course en demi-fond, et le tenir jusqu''au bout',
 'Classe de 4e, 27 élèves, deux séances hebdomadaires dont une de deux heures. Piste de 200 mètres et gymnase. Deux élèves dispensés partiels tiennent les rôles d''observateur et de chronométreur, ce qui est une place réelle dans la séquence et non un pis-aller.',
 'Six séances de demi-fond, avec un contrat de course individuel révisé à mi-parcours.',
 '["Établir une allure de course et la tenir sur une durée annoncée","Observer un camarade et lui rendre compte avec précision","Adapter son projet après une performance décevante","Expliquer l''effet de l''échauffement sur l''effort qui suit","Assumer un rôle d''arbitre ou d''observateur avec rigueur"]',
 'Éducation physique et sportive', '4e', now(), now()),

-- 7. Enseignement moral et civique
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Prendre la parole dans un désaccord sans chercher à avoir le dernier mot',
 'Classe de 4e, 27 élèves, une heure hebdomadaire. La classe est vive et les discussions y tournent vite au concours de répliques : la séquence installe des règles de prise de parole, et c''est son premier objet avant tout contenu.',
 'Six séances : deux sur les règles de la discussion, trois sur des cas concrets tirés de la vie du collège, une sur l''affichage produit par la classe.',
 '["Écouter un avis contraire jusqu''au bout avant de répondre","Distinguer un argument d''une opinion et d''une insulte","Reformuler la position de l''autre avant de la discuter","Chercher ce que dit la règle avant de dire ce qu''on ressent","Rendre compte d''une discussion collective par écrit"]',
 'Enseignement moral et civique', '4e', now(), now()),

-- 8. Histoire et géographie
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Comprendre ce que le commerce du XVIIIe siècle a construit, et sur quoi il reposait',
 'Classe de 4e, 27 élèves, trois heures hebdomadaires. Le chapitre sur la traite atlantique arrive après l''étude des bourgeoisies marchandes : les élèves connaissent l''enrichissement des ports avant d''en connaître le prix humain, et c''est ce raccord qui fait la difficulté de la séquence.',
 'Sept séances, appuyées sur les archives portuaires de Nantes et de Bordeaux et sur deux récits de captifs.',
 '["Lire et confronter des documents de nature différente sur un même fait","Situer dans le temps et dans l''espace un commerce à trois continents","Distinguer ce qu''un document dit de ce qu''il tait","Réaliser un croquis de flux à partir d''un texte","Rédiger un développement construit d''une vingtaine de lignes"]',
 'Histoire et géographie', '4e', now(), now()),

-- 9. Physique-Chimie
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Suivre ce qui se conserve quand la matière change d''état',
 'Classe de 4e, 27 élèves, une heure et demie hebdomadaire dont une heure en demi-groupe au laboratoire. Balances au centigramme, ballons, thermomètres. La conception spontanée à faire tomber est tenace : pour beaucoup d''élèves, ce qui s''évapore « disparaît ».',
 'Six séances dont quatre expérimentales, autour de la masse, du volume et de la température lors des changements d''état.',
 '["Formuler une hypothèse et concevoir l''expérience qui la met à l''épreuve","Mesurer une masse et un volume avec l''incertitude qui va avec","Distinguer masse et volume dans un changement d''état","Rédiger un compte rendu d''expérience qui permette de la refaire","Confronter un résultat inattendu au protocole plutôt qu''au hasard"]',
 'Physique-Chimie', '4e', now(), now()),

-- 10. Sciences de la vie et de la Terre
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Comprendre pourquoi la Terre tremble ici plutôt qu''ailleurs',
 'Classe de 4e, 27 élèves, une heure et demie hebdomadaire dont une heure en demi-groupe. Accès aux données sismiques publiques en ligne. La séquence part d''un séisme récent choisi avec la classe, ce qui donne au chapitre une actualité que le manuel n''a pas.',
 'Sept séances : trois de recueil et de traitement de données, deux de modélisation, deux de synthèse et de prévention.',
 '["Localiser les séismes et les volcans à l''échelle du globe","Relier la répartition des séismes aux limites de plaques","Exploiter un jeu de données réelles pour établir une corrélation","Distinguer un modèle de la réalité qu''il représente","Expliquer une consigne de sécurité par le phénomène qui la justifie"]',
 'Sciences de la vie et de la Terre', '4e', now(), now()),

-- 11. Technologie
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Concevoir un objet qui répond à un besoin réel, du croquis au prototype',
 'Classe de 4e, 27 élèves, une heure et demie hebdomadaire en salle de technologie. Deux imprimantes 3D, une découpeuse vinyle, six ordinateurs de CAO. Le besoin retenu vient du collège lui-même : le local à vélos est inutilisable les jours de pluie, et les élèves le savent mieux que quiconque.',
 'Huit séances en projet, par équipes de quatre, avec deux revues de projet imposées et un prototype par équipe.',
 '["Formuler un besoin sous forme de fonctions à assurer","Proposer plusieurs solutions et les comparer sur des critères annoncés","Représenter une solution par un croquis coté puis par un modèle numérique","Réaliser un prototype rapide et en tirer les conséquences","Rendre compte de l''avancement d''un projet devant un tiers"]',
 'Technologie', '4e', now(), now()),

-- 12. Mathématiques
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Démontrer, c''est-à-dire convaincre avec des raisons et non avec un dessin',
 'Classe de 4e, 27 élèves, trois heures et demie hebdomadaires. Le passage de la constatation à la démonstration est le seuil de l''année : les élèves mesurent sur la figure, concluent, et considèrent l''affaire réglée. La séquence attaque ce réflexe de front, sur le théorème de Pythagore et sa réciproque.',
 'Neuf séances, dont deux consacrées uniquement à la rédaction d''une démonstration et une à l''erreur comme objet d''étude.',
 '["Distinguer constater sur une figure et démontrer","Rédiger une démonstration en citant la propriété utilisée","Employer le théorème de Pythagore et sa réciproque à bon escient","Repérer l''endroit exact où un raisonnement se casse","Chercher un contre-exemple pour réfuter une affirmation"]',
 'Mathématiques', '4e', now(), now()),

-- 13. Éducation aux médias et à l'information
((SELECT id FROM users WHERE email='demo.college4e@aschool.fr'),
 'Savoir d''où vient une information avant de la partager',
 'Classe de 4e, 27 élèves, l''enseignement est conduit avec la professeure documentaliste au CDI, une heure par quinzaine. Tous les élèves ont un téléphone, la plupart sont sur au moins deux réseaux, et l''information leur arrive par des comptes dont ils ignorent qui les tient.',
 'Six séances au CDI, chacune partant d''un contenu réellement circulé dans le collège la semaine précédente.',
 '["Retrouver la source première d''une information reprise en ligne","Distinguer un fait, une opinion et une publicité déguisée","Vérifier une image par sa provenance et par sa date","Expliquer pourquoi un contenu apparaît dans son fil","Produire à son tour un contenu qui cite ses sources"]',
 'Éducation aux médias et à l’information', '4e', now(), now());
