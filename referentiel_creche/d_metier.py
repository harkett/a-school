# -*- coding: utf-8 -*-
"""Bloc 5 — LE MÉTIER AUTOUR DE L'ENFANT : parents, équipe, organisation.

Ce bloc CROISE deux sources qui ne se recouvrent pas : le cahier des charges EDE (Doc 4) énumère
les missions réelles du métier — transmettre aux parents, transmettre à l'équipe, planifier,
contribuer au projet pédagogique, se relire — mais ne porte aucun contenu ; les parties 2 et 3 du
Doc 3 portent le contenu de ces mêmes missions mais ne les nomment pas comme des missions.

Le référentiel précédent avait écarté ces deux parties. C'est ce qui manquait pour que le métier
soit couvert au-delà de la relation directe à l'enfant.
"""

METIER = [
 {"titre": "La place des parents dans le lieu d'accueil",
  "forme": "repère de conduite professionnelle · relation aux parents",
  "retenir": ["Accueillir un enfant, c'est aussi accueillir sa famille. L'implication des parents "
              "et la qualité de la relation entre parents et professionnels contribuent au "
              "bien-être et à la sécurité affective de l'enfant.",
              "Les parents peuvent accéder au lieu d'accueil, pour les moments de transmission "
              "comme pour des moments passés avec leur enfant."],
  "faire": ["Encourager la participation des parents à la vie du lieu d'accueil : sorties, "
            "activités, café des parents.",
            "Préciser les modalités de participation des parents à la gouvernance de "
            "l'établissement et au travail sur le projet.",
            "Établir une collaboration active avec les parents, sans jamais prendre leur place : "
            "les conseiller et les rassurer face à leurs inquiétudes.",
            "Accompagner un collègue lors d'un entretien avec les parents lorsque c'est nécessaire."],
  "source": "Doc 3, partie 2 · Doc 4, missions de l'EDE"},

 {"titre": "La communication et les transmissions aux parents",
  "forme": "transmission aux parents",
  "retenir": ["Les transmissions servent à faire part aux parents des épisodes marquants de la "
              "journée, des résultats des observations quand elles ont été conduites, et à "
              "échanger sur les besoins de l'enfant et sur son développement.",
              "Des discussions individuelles plus approfondies ont lieu plusieurs fois par an pour "
              "faire le point sur l'évolution de l'enfant."],
  "faire": ["Écouter et décoder les attentes des parents.",
            "S'informer des soins donnés à l'enfant chez lui, des attitudes et comportements qu'il "
            "y présente.",
            "Informer les parents des observations relatives à leur enfant : ses habitudes, ses "
            "goûts.",
            "Éclairer, conseiller et rassurer les parents sur les réactions de leur enfant.",
            "Organiser des réunions à l'intention des parents et y participer.",
            "S'appuyer sur l'observation professionnelle comme support premier de la communication."],
  "source": "Doc 3, partie 2 · Doc 4, fonction sociale et de communication"},

 {"titre": "Les demandes et les pratiques parentales",
  "forme": "repère de conduite professionnelle · relation aux parents",
  "retenir": ["Les professionnels cherchent autant que possible des accommodements raisonnables "
              "pour assurer la continuité avec les pratiques parentales. Lorsqu'ils ne peuvent pas "
              "appliquer certaines pratiques favorables à l'enfant, ils ne les découragent pas pour "
              "autant.",
              "Toute pratique parentale défavorable à l'enfant, ou contraire aux principes qui "
              "régissent l'accueil, fait l'objet d'une interpellation et d'un échange."],
  "faire": ["Chercher la continuité éducative dans le respect de l'autorité parentale, sans "
            "violence physique ou psychologique.",
            "Se rappeler que l'enfant n'appartient pas à ses parents : il est sujet de droit, et sa "
            "dépendance implique une responsabilité collective supérieure. Son intérêt prime sur le "
            "libre choix des parents lorsque ce choix remet en cause ses droits ou ses besoins."],
  "source": "Doc 3, partie 2"},

 {"titre": "Le jugement et le non-jugement",
  "forme": "repère de conduite professionnelle",
  "retenir": ["Il est inévitable de porter des jugements : la posture professionnelle de "
              "non-jugement est l'objet d'un travail et d'une construction spécifiques, pour éviter "
              "que des jugements spontanés interfèrent dans la relation avec la famille.",
              "Les temps et espaces de réflexivité permettent de verbaliser les jugements et les "
              "préjugés sur les familles, de les travailler et de les interroger."],
  "pasfaire": ["S'abstenir de toute remarque négative ou dévalorisante sur les parents en présence "
               "des parents ou des enfants."],
  "faire": ["Poser un regard critique sur son propre travail et son propre fonctionnement.",
            "Adopter un comportement intègre, fiable et réservé.",
            "Appliquer le droit au respect de la vie privée : ne communiquer que l'obligatoire et "
            "l'indispensable."],
  "source": "Doc 3, partie 2 · Doc 4, déontologie et auto-analyse"},

 {"titre": "L'allaitement",
  "forme": "accompagnement d'un temps du quotidien · relation aux parents",
  "retenir": ["Les modes d'accueil soutiennent les mères qui souhaitent poursuivre l'allaitement, "
              "de façon exclusive ou complémentaire. Ils ne demandent pas de sevrer le bébé avant "
              "l'accueil et ne refusent pas de donner du lait maternel.",
              "Les mères peuvent venir allaiter à tout moment de la journée : des espaces adaptés "
              "sont prévus à cet effet."],
  "source": "Doc 3, partie 2"},

 {"titre": "L'accompagnement à la parentalité",
  "forme": "transmission aux parents",
  "retenir": ["Les professionnels de l'accueil sont aussi des professionnels de l'accompagnement "
              "des parents : ils assurent un rôle d'information, d'accompagnement et de soutien.",
              "Ils encouragent la diffusion auprès de toutes les familles des principes qui guident "
              "l'accueil, notamment par de l'observation et de l'action conjointes."],
  "source": "Doc 3, partie 2"},

 {"titre": "L'inclusion de tous les enfants et de leurs familles",
  "forme": "repère de conduite professionnelle",
  "retenir": ["Les professionnels répondent à un principe d'inclusion et accueillent toutes les "
              "familles et tous les enfants sans distinction, sauf contre-indication médicale.",
              "Les règles qui guident cet accueil sont celles du droit commun ; une attention "
              "renforcée peut être nécessaire lorsque parents ou enfants présentent des besoins "
              "spécifiques.",
              "L'accueil part toujours des compétences des parents et des enfants — y compris en "
              "situation de handicap ou de maladie chronique — pour les renforcer, les soutenir et "
              "les valoriser."],
  "faire": ["Aller vers les familles en situation de précarité.",
            "S'adapter aux enfants qui présentent des besoins particuliers, et apprendre au groupe "
            "la tolérance envers eux.",
            "Adapter le comportement des autres enfants à ces enfants."],
  "source": "Doc 3, partie 2 · Doc 4, missions de l'EDE"},

 {"titre": "La prévention et le repérage de la maltraitance",
  "forme": "repère de conduite professionnelle",
  "retenir": ["Tous les lieux d'accueil formalisent la conduite à tenir en cas de suspicion de "
              "maltraitance. En accueil collectif, les protocoles couvrent la maltraitance "
              "intrafamiliale comme la maltraitance institutionnelle.",
              "Les professionnels connaissent les circuits — information préoccupante, signalement — "
              "et y ont recours lorsque les situations se présentent.",
              "La maltraitance institutionnelle fait l'objet d'un travail spécifique dans les "
              "dispositifs de réflexivité."],
  "faire": ["Être attentif à la communication non verbale de l'enfant : elle permet de détecter et "
            "de relayer les problèmes de santé, de motricité, de compréhension et de langage, de "
            "socialisation, de maltraitance.",
            "Signaler les cas de maltraitance."],
  "source": "Doc 3, partie 3 · Doc 4, missions de l'EDE"},

 {"titre": "La transmission à l'équipe et le travail pluridisciplinaire",
  "forme": "transmission à l'équipe",
  "retenir": ["Les démarches de réflexivité et de recul sur l'activité sont mises en place "
              "régulièrement, selon des modalités variées : réunions d'équipe ou de réseau, analyse "
              "de la pratique, supervision.",
              "La pluridisciplinarité est mise en œuvre dans les établissements, et proposée aux "
              "professionnels de l'accueil individuel par les animateurs de réseau."],
  "faire": ["Transmettre les informations nécessaires aux membres de l'équipe et à la direction.",
            "S'intégrer activement au travail d'une équipe pluridisciplinaire.",
            "Négocier l'organisation du travail avec les membres de l'équipe, le personnel de "
            "cuisine et d'entretien.",
            "Présenter la synthèse d'une formation continue qu'on a suivie.",
            "Diagnostiquer ses besoins en formation continue et se situer dans la structure "
            "professionnelle."],
  "source": "Doc 3, partie 3 · Doc 4, fonction sociale et de communication, auto-analyse"},

 {"titre": "L'organisation de la journée et la planification",
  "forme": "planification et organisation",
  "retenir": ["Les professionnels construisent une planification des journées a minima de façon "
              "quotidienne et hebdomadaire : temps de la journée, propositions faites aux enfants.",
              "L'organisation interne offre une visibilité sur les plannings, prévoit les modalités "
              "de remplacement des absences et les départs en formation."],
  "faire": ["Établir le planning des activités.",
            "Adapter son rythme de travail au planning et au rythme des enfants.",
            "Préparer le matériel en fonction du planning et organiser l'espace en conséquence.",
            "Gérer l'espace et le temps pour permettre à l'enfant d'exercer ses activités "
            "spontanées, ludiques et artistiques.",
            "Installer une routine régulière : les tout-petits sont rassurés par ce qui est "
            "prévisible.",
            "Réunir les enfants dans un lieu accueillant et sûr, en petits groupes par âge quand "
            "c'est possible.",
            "Noter les présences et les absences, tenir l'agenda, les feuilles journalières, le "
            "cahier d'information et les dossiers des enfants."],
  "source": "Doc 3, partie 3 · Doc 4, organiser et planifier, gestion et administration · Doc 2, "
            "comment utiliser ce kit"},

 {"titre": "Le projet pédagogique",
  "forme": "contribution au projet pédagogique",
  "retenir": ["Le professionnel est chargé de mettre en œuvre le projet pédagogique du lieu "
              "d'accueil et participe également à son évolution."],
  "faire": ["Participer, dans le cadre de sa profession, à l'élaboration du projet pédagogique et "
            "à son évolution.",
            "Préciser dans le projet d'accueil la façon dont l'observation professionnelle est "
            "conduite, et les dispositions prévues : rythme des réunions, journées pédagogiques, "
            "formations, analyse de la pratique.",
            "Travailler dans le projet d'accueil la notion de personne de référence et de "
            "personnes relais."],
  "source": "Doc 3, parties 1 et 3 · Doc 4, missions de l'EDE"},

 {"titre": "La santé, la prévention et les premiers soins",
  "forme": "accompagnement d'un temps du quotidien · fonction de soins",
  "retenir": ["La fonction de soin consiste à assurer les soins d'hygiène et de santé, à organiser "
              "les temps de repos et à veiller au bien-être de l'enfant en installant un "
              "environnement calme et sécurisé."],
  "faire": ["Repérer les premiers signes de maladie et les signes d'altération de la santé.",
            "Éviter les contagions.",
            "Administrer un médicament ou utiliser un aérosol selon les directives du médecin.",
            "Prévenir les accidents et assurer les premiers soins d'urgence.",
            "Repérer les premiers signes de fatigue, mettre au lit et surveiller la sieste.",
            "Donner le repas ou aider à la prise du repas, en tenant compte des besoins individuels "
            "de rythme et de quantité.",
            "Accompagner et encourager l'apprentissage de la propreté et celui de l'utilisation "
            "des couverts.",
            "Aider au dépistage précoce des problématiques particulières que peuvent rencontrer les "
            "enfants."],
  "source": "Doc 4, fonction de soins et de santé · Doc 3, partie 1"},

 {"titre": "La qualité de vie au travail et l'environnement",
  "forme": "repère de conduite professionnelle",
  "retenir": ["Les établissements s'engagent dans des démarches d'amélioration de la qualité de vie "
              "et des conditions de travail : prévention des troubles musculo-squelettiques et des "
              "risques psycho-sociaux, espaces de pause et de répit.",
              "Les lieux d'accueil s'engagent dans des démarches écologiques, avec un double "
              "objectif : s'inscrire dans la transition écologique et favoriser la santé globale de "
              "l'enfant."],
  "faire": ["Appliquer l'ensemble des recommandations des autorités nationales relatives à la santé "
            "de l'enfant et à la qualité de l'environnement.",
            "Former les personnes exerçant des fonctions de direction au management et aux "
            "connaissances métier sur le développement de l'enfant, à la prise de poste comme en "
            "formation continue."],
  "source": "Doc 3, partie 3"},
]
