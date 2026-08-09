# -*- coding: utf-8 -*-
"""Génère le PDF de la deuxième partie du référentiel d'éveil 0-3 : les temps du quotidien.

Source unique du contenu : Référentiel national de la qualité d'accueil du jeune enfant,
avril 2025 (ministère du Travail, de la Santé, des Solidarités et des Familles / IGAS).
Le texte est condensé, jamais inventé.
"""
from fpdf import FPDF

POLICE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
POLICE_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ---------------------------------------------------------------------------------------------
# Le contenu. ("H1"|"H2"|"RET"|"SUB"|"P"|"LI"|"NOTE", texte)
# ---------------------------------------------------------------------------------------------
BLOCS = [
("H1", "DEUXIÈME PARTIE — Les temps du quotidien"),

("P", "Les activités de la première partie ne se déroulent pas dans le vide. Elles s'insèrent dans "
      "une journée faite de repas, de siestes, de changes, de pleurs, d'arrivées et de départs — et "
      "c'est là que se joue l'essentiel du métier."),
("P", "Cette partie ne contient pas d'activités à animer. Elle donne le **cadre de conduite "
      "professionnelle** dans lequel toute activité prend place. Elle est de nature différente de la "
      "première partie et doit être lue comme telle : des principes et des pratiques, pas des déroulés."),

("NOTE", "SOURCE DE CETTE PARTIE. Référentiel national de la qualité d'accueil du jeune enfant, "
         "avril 2025, ministère du Travail, de la Santé, des Solidarités et des Familles — travaux "
         "pilotés par l'IGAS (Dr Nicole Bohic, Jean-Baptiste Frossard), 7 groupes de travail, "
         "2 000 professionnels consultés. Document public de l'État français, librement réutilisable, "
         "dont le ministère demande lui-même la diffusion et l'enrichissement. Statut différent des "
         "deux publications UNICEF de la première partie. Les 12 fiches retenues sont celles de sa "
         "partie 1 qui touchent au métier d'éveil ; ses parties 2 (relation aux parents) et "
         "3 (organisation, management, locaux) sont écartées. Rien n'est ajouté au texte officiel."),

("SUB", "Deux règles traversent tout le document officiel et valent pour chaque fiche"),
("LI", "**Aucune pratique de forçage.** Ni pour manger, ni pour dormir, ni pour la continence. Le "
       "forçage — par la voix intimidante comme par le geste — est qualifié de pratique maltraitante."),
("LI", "**Aucune punition.** Paroles dévalorisantes, coin, isolement : proscrits par la loi, et "
       "contre-productifs. Le professionnel peut se mettre à l'écart **avec** l'enfant pour l'apaiser ; "
       "il ne met jamais l'enfant à l'écart seul."),

# ------------------------------------------------------------------- 1
("H2", "Fiche 1 — Le jeu et l'exploration"),
("RET", "L'exploration de l'enfant est favorisée et encouragée en toute circonstance. Les interdits "
        "liés au danger sont systématiquement interrogés : s'agit-il d'un danger réel, ou d'une peur "
        "de l'adulte ?"),
("P", "L'enfant a besoin d'explorer librement : toucher, manipuler, flairer, goûter, déchirer, "
      "soulever, renverser, escalader. Il se tache et se salit — c'est le signe que ça fonctionne. "
      "L'enfant ne se développe pas par sphères cloisonnées (sensoriel, moteur, cognitif, langagier) "
      "mais globalement, en synergie : une activité de motricité développe l'ensemble."),
("SUB", "Ce que fait le professionnel"),
("LI", "Il laisse l'enfant circuler et explorer ; il joue avec lui, reste à proximité et attentif."),
("LI", "Il propose du matériel « bon à tout faire » (boîtes, tubes, contenants vides, tissus) qui "
       "permet de nombreuses combinaisons, et accepte le détournement des objets du quotidien."),
("LI", "Quand l'exploration entre en conflit avec la sécurité ou le collectif, il **réoriente** "
       "l'enfant vers autre chose plutôt que d'interdire ou d'arrêter."),
("LI", "Il distingue le **danger** (dont l'enfant doit être protégé) du **risque** (occasion "
       "d'exploration accompagnée). Si le lieu présente un danger réel, c'est au lieu de s'adapter."),
("LI", "**Quand il se surprend à dire « non » trop souvent, il s'interroge sur l'aménagement de "
       "l'espace**, pas sur l'enfant."),
("LI", "Il est vigilant aux stéréotypes de genre dans le choix des jeux et déguisements, et accepte "
       "toutes les formes de jeu sans distinction."),

# ------------------------------------------------------------------- 2
("H2", "Fiche 2 — Le langage"),
("RET", "Le professionnel s'adresse à l'enfant quel que soit son âge et prend le temps de "
        "l'interaction, qu'elle soit verbale ou pré-verbale."),
("P", "Le langage s'acquiert dans l'interaction. À 2 ans, un enfant peut avoir 50 mots quand un "
      "autre en produit 500 — l'écart tient à la qualité du bain langagier depuis la naissance."),
("SUB", "Ce que fait le professionnel"),
("LI", "Il parle à l'enfant à tous les âges : il explique les soins qu'il prodigue, décrit l'action, "
       "raconte, pose des questions au bébé et laisse le temps de la réponse non verbale."),
("LI", "Il emploie un langage riche, précis, construit ; il n'utilise pas de langage enfantin et ne "
       "parle jamais de l'enfant à la troisième personne devant lui."),
("LI", "Il parle **individuellement**, en regardant l'enfant dans les yeux, et évite les paroles "
       "adressées au groupe, surtout pour les plus petits."),
("LI", "Il ne l'interrompt pas quand il s'exprime, verbalement ou non."),
("LI", "Il porte une attention particulière aux enfants « discrets », qui parlent peu ou ne "
       "sollicitent pas l'adulte."),
("LI", "Il nomme les émotions des personnages quand il raconte une histoire, et demande aux plus "
       "grands ce qu'ils ressentent."),
("LI", "**Pas de musique de fond en continu** : elle freine la perception des sons et les "
       "interactions langagières."),
("LI", "Il encourage le contact avec plusieurs langues, dont la langue d'origine des familles "
       "allophones."),

# ------------------------------------------------------------------- 3
("H2", "Fiche 3 — Les émotions de l'enfant"),
("RET", "L'expression des émotions est favorisée, jamais empêchée. Lors d'émotions fortes, le "
        "professionnel accompagne et sécurise sans chercher à faire cesser."),
("P", "Le jeune enfant ne peut pas réguler seul ses émotions : son cerveau est immature, il ne peut "
      "pas « se raisonner ». L'adulte est le principal régulateur. La régulation viendra "
      "progressivement, par imitation de l'adulte."),
("SUB", "Ce que fait le professionnel"),
("LI", "Il nomme les émotions — celles de l'enfant comme les siennes."),
("LI", "Il ne dit pas « calme-toi », ne minimise pas (« ce n'est pas grave »), ne gronde pas parce "
       "que l'enfant crie."),
("LI", "Il émet des hypothèses à voix haute, **y compris pour un enfant qui ne parle pas encore** : "
       "« es-tu triste, en colère, as-tu peur ? »"),
("LI", "Il apaise par le regard, le contact, le portage, la parole. Si l'enfant rejette la "
       "proximité, il reste à distance **en gardant le lien visuel**."),
("LI", "Il accueille toutes les émotions avec la même bienveillance, sans distinction de genre — la "
       "colère chez les filles autant que la tristesse chez les garçons."),
("LI", "Si le comportement menace la sécurité, il peut tenir l'enfant **en lui expliquant qu'il le "
       "tient pour le protéger**."),
("LI", "Une fois l'enfant calme, il revient avec lui sur ce qui s'est passé, et s'interroge sur ce "
       "qui aurait pu l'éviter."),

# ------------------------------------------------------------------- 4
("H2", "Fiche 4 — Les pleurs"),
("RET", "Le professionnel accompagne et sécurise l'enfant qui pleure, cherche le besoin insatisfait "
        "— sans avoir pour objectif premier de faire cesser les pleurs."),
("P", "Les pleurs sont une alarme qui signale un besoin non satisfait, même quand l'adulte ne "
      "l'identifie pas. Les pleurs ne sont jamais des caprices ni des tentatives de manipulation. "
      "Consoler ne veut pas dire faire taire."),
("SUB", "Ce que fait le professionnel"),
("LI", "Il demande à l'enfant ce qu'il ressent."),
("LI", "Il le prend dans les bras, dans un climat apaisé et s'il l'accepte, **sans craindre qu'il "
       "« s'habitue aux bras »**."),
("LI", "Il ne cherche pas à interrompre les pleurs avec une tétine ou un doudou : ces objets ne "
       "remplacent pas la présence de l'adulte."),
("LI", "Quand les pleurs sont intenses et répétés, il cherche la cause du côté du lieu d'accueil "
       "autant que de l'enfant : bruit, lumière, ruptures dans le planning, manque de disponibilité, "
       "tension dans l'équipe."),

# ------------------------------------------------------------------- 5
("H2", "Fiche 5 — Les interactions entre enfants"),
("RET", "Les conflits ne se règlent pas de façon punitive. Pas de reproche à l'enfant qui initie le "
        "conflit : le professionnel se place en médiateur."),
("P", "Chez les tout-petits, le conflit autour d'un jouet et l'imitation joyeuse sont le même "
      "processus : découvrir l'autre en s'identifiant à lui. Un conflit, c'est de « l'imitation "
      "empêchée », pas de l'agressivité. L'enfant n'est ni égoïste ni méchant : il ne comprend pas "
      "encore les désirs de l'autre."),
("SUB", "Ce que fait le professionnel"),
("LI", "Il prévoit **plusieurs jeux identiques** (même forme, même couleur) : cela facilite "
       "l'imitation et diminue les conflits."),
("LI", "Il ne dit pas « tu n'es pas gentil » ; il explique et cherche une solution : « je vois que "
       "tu veux faire comme lui, mais il a encore envie de jouer, on va chercher comment faire »."),
("LI", "Il rappelle la règle calmement, montre comment agir autrement, nomme l'émotion."),
("LI", "Il relève et encourage le comportement adapté quand il apparaît (demander le jouet au lieu "
       "de l'arracher)."),

# ------------------------------------------------------------------- 6
("H2", "Fiche 6 — Le cadre, les repères et les interdits"),
("RET", "Le cadre n'a pas pour fonction de discipliner mais de sécuriser. Le professionnel fait "
        "régulièrement le compte des interdits qu'il formule, et se demande s'ils répondent aux "
        "besoins de l'enfant ou aux attentes de l'adulte."),
("P", "L'enfant a besoin d'entendre la même règle de tous les adultes. Lorsqu'une limite est posée, "
      "il lui faut un délai pour l'intégrer et l'appliquer. L'enfant ne fait pas de caprices : dans "
      "sa colère il exprime un besoin frustré et une incapacité, à ce stade, à contrôler sa "
      "frustration."),
("SUB", "Ce que fait le professionnel"),
("LI", "Il formule l'interdit **de façon affirmative** : « descends de la table » plutôt que « ne "
       "monte pas sur la table » — la forme négative est plus difficile à comprendre."),
("LI", "Il explique les raisons des interdits **en dehors** des moments où ils sont franchis."),
("LI", "Il compte ses interdits, particulièrement ceux qui touchent à la motricité (ne pas courir, "
       "ne pas grimper, ne pas jeter), et cherche à les réduire."),
("LI", "Il ne pose pas comme objectif la discipline, la « maîtrise » ou le calme : ces objectifs ne "
       "correspondent ni aux besoins ni aux capacités d'un enfant de moins de 3 ans."),
("LI", "**L'expression des émotions ne fait jamais l'objet d'un interdit** : la colère peut "
       "s'exprimer, le professionnel propose seulement une façon de le faire sans casser ni blesser."),
("LI", "Les moments de repas, change et sommeil ne donnent pas lieu à des règles rigides."),

# ------------------------------------------------------------------- 7
("H2", "Fiche 7 — Le sommeil"),
("RET", "L'enfant n'est jamais forcé à aller au lit, mais on le lui propose chaque jour. La sieste "
        "peut se faire à l'extérieur ou dans la salle de vie. On ne demande pas aux parents qui "
        "endorment leur enfant dans les bras de cesser cette pratique."),
("P", "Les espaces de sommeil ne sont pas dans l'obscurité totale, mais à la lumière du jour "
      "tamisée. Le sommeil se prépare par des rituels quotidiens : temps calmes, comptines, voix "
      "basse, respiration, musique lente, massage du visage, histoire redondante lue en chuchotant."),
("P", "**Repères de durée.** 15 à 17 h par 24 h à la naissance · 12 à 15 h entre 4 et 11 mois · "
      "11 à 14 h entre 1 et 2 ans · 10 à 12 h à 3 ans."),
("SUB", "Ce que fait le professionnel"),
("LI", "Il ne réveille pas un bébé qui dort. Au-delà de 2 ans, si une sieste trop tardive (après "
       "16 h) ou trop longue gêne la nuit, le réveil peut être induit, au cas par cas avec les parents."),
("LI", "Il propose le lit chaque jour sans forcer. **Maintenir un enfant au lit de force, par la "
       "voix ou par le geste, est une pratique maltraitante.**"),
("LI", "Pour l'enfant qui ne parvient pas à dormir, il renforce la sécurisation affective : temps "
       "individuel, câlins, échanges."),
("LI", "Il installe les enfants au sommeil léger contre un mur, dans un coin, avec vue sur la porte "
       "— jamais au milieu de la pièce."),
("LI", "Il reste disponible pour ceux qui ne dorment pas."),

# ------------------------------------------------------------------- 8
("H2", "Fiche 8 — L'alimentation"),
("RET", "On ne pousse pas l'enfant à finir son assiette ni à goûter ; on lui repropose "
        "régulièrement, en manifestant le plaisir qu'on a soi-même à manger. L'enfant touche, goûte, "
        "mélange — sans interdit systématique ni réprimande."),
("P", "Le repas est un moment de relation, et le plaisir de manger mobilise les cinq sens. C'est "
      "aussi un lieu privilégié d'autonomie : se servir, passer le plat, débarrasser."),
("SUB", "Ce que fait le professionnel"),
("LI", "Il laisse manger avec les mains et découvrir les textures avec les doigts."),
("LI", "Il ne demande pas de « respecter la nourriture » : un enfant de moins de 3 ans ne peut pas "
       "le comprendre."),
("LI", "Il présente chaque **nouvel aliment séparément**, sans le mélanger, et le repropose "
       "plusieurs fois sur des repas distincts."),
("LI", "Il ne fait pas de chantage : **ni « encore une petite cuillère pour me faire plaisir », ni "
       "« si tu finis ton assiette, tu auras un dessert »**."),
("LI", "Il accepte l'appréhension de certains aliments, normale surtout vers 2 ans."),
("LI", "Il autorise l'enfant à se lever pendant le repas : rester assis est fatigant à cet âge."),
("LI", "Il nomme et parle des aliments."),
("LI", "L'organisation permet à chacun de manger à son rythme."),

# ------------------------------------------------------------------- 9
("H2", "Fiche 9 — Le change et la continence"),
("RET", "Le change est un moment de soin intime, mis à profit pour un échange individuel. Il est "
        "fait dès que l'enfant manifeste une gêne. L'enfant n'est jamais contraint dans "
        "l'acquisition de la continence."),
("P", "La continence relève d'un processus naturel de maturation : on n'apprend pas à un enfant à "
      "être continent. Le rythme varie d'un enfant à l'autre et n'est pas linéaire — les régressions "
      "font partie du processus. Le respect du développement de l'enfant prime sur les attentes "
      "sociétales ou scolaires."),
("SUB", "Ce que fait le professionnel"),
("LI", "Il ne laisse jamais un enfant avec une couche souillée, et ne réprime pas celui qui demande "
       "à aller aux toilettes — **même en pleine activité**."),
("LI", "Il verbalise les soins qu'il prodigue et ce que fait l'enfant."),
("LI", "Il fait du change un moment de relation : regard, parole, jeux, sourires, rires."),
("LI", "Il favorise l'autonomie selon l'âge — change debout, lever la jambe, tenir la couche, avoir "
       "son propre gant — **sans en faire un objectif** : un enfant peut ne pas en avoir envie ce "
       "jour-là."),
("LI", "Il laisse l'enfant participer et regarder (jeter la couche, vider le pot) et répond à ses "
       "questions."),
("LI", "Il ne gronde jamais en cas d'accident."),

# ------------------------------------------------------------------- 10
("H2", "Fiche 10 — Les sorties quotidiennes en extérieur"),
("RET", "Les enfants sortent chaque jour, quel que soit le temps, hors alerte météo. Les enfants ne "
        "restent pas dans les poussettes pendant les moments de loisirs."),
("SUB", "Ce que fait le professionnel"),
("LI", "Il demande aux parents des vêtements adaptés à toutes les saisons : combinaison chaude, "
       "bottes de pluie, chapeau."),
("LI", "En forte chaleur, il sort tôt le matin ou dans des espaces ombragés et aérés."),
("LI", "Il favorise la découverte de milieux naturels variés."),
("LI", "**Il ne laisse pas un enfant assis ou allongé plus d'une heure d'affilée** en dehors du "
       "sommeil et de la sieste."),

# ------------------------------------------------------------------- 11
("H2", "Fiche 11 — Les arts et les cultures"),
("RET", "L'éveil artistique passe par la pratique de l'enfant. Dans tous les espaces de vie, des "
        "livres adaptés sont en libre accès, à hauteur d'enfant."),
("SUB", "Le livre et la lecture"),
("P", "Le professionnel laisse l'enfant s'approprier le livre par l'observation et le toucher, lit à "
      "voix haute, met en chanson. Il relit plusieurs fois le même livre — l'enfant a du plaisir à "
      "anticiper la suite. **Les livres ne sont pas rangés hors de portée par crainte qu'ils soient "
      "abîmés.**"),
("SUB", "Les arts plastiques"),
("P", "Peinture, modelage, collage, pliage, construction, avec des matières variées (lisses, "
      "rugueuses, brillantes, mates). Ateliers « fait maison » à base de produits naturels et "
      "biodégradables — pâte à modeler alimentaire, peintures végétales — reproductibles à la "
      "maison, ce qui associe les familles. L'espace est protégé (bâche, tissu) plutôt que "
      "l'activité empêchée ; elle peut se faire dehors."),
("SUB", "La musique"),
("P", "De la musicalité tout au long de la journée — chansons, comptines, jeux de doigts — selon le "
      "besoin du moment : calmer des pleurs, ouvrir un temps collectif, accompagner l'endormissement. "
      "Instruments acoustiques plutôt qu'électroniques, avec un souci de qualité sonore. Musiques "
      "d'autres cultures et d'autres langues, en invitant les parents à partager la leur."),

# ------------------------------------------------------------------- 12
("H2", "Fiche 12 — L'arrivée : familiarisation, doudous et tétines"),
("RET", "Le mot familiarisation est préféré à « adaptation » : il dit qu'on prend le temps de faire "
        "connaissance — l'enfant, les parents et le professionnel."),
("SUB", "La familiarisation"),
("LI", "On préfère **la répétition de situations semblables** (même lieu, même personne, même heure) "
       "à une progression par étapes (une heure, puis un repas). La répétition rend l'environnement "
       "prévisible, et c'est ce qui sécurise."),
("LI", "La présence des parents est prolongée, plusieurs heures sur plusieurs jours, et le parent y "
       "est acteur auprès de son enfant."),
("LI", "Pas de protocole rigide : les modalités s'ajustent à chaque enfant et à chaque famille."),
("LI", "Même un enfant déjà accueilli ailleurs recommence **une nouvelle familiarisation**."),
("LI", "Les temps de présence commune ne s'arrêtent pas à la familiarisation."),
("SUB", "Les doudous et les tétines"),
("LI", "Les doudous sont **à libre disposition**, accessibles seuls ; ils sont donnés aux plus "
       "petits dès qu'ils en manifestent l'envie."),
("LI", "Le doudou **voyage** entre la maison et le lieu d'accueil : il fait le lien entre deux mondes."),
("LI", "Tous les enfants n'ont pas de doudou — cela n'existe pas dans toutes les familles ni dans "
       "toutes les cultures. On n'insiste pas pour que les parents en fournissent un."),
("LI", "La tétine est découragée pendant les temps de veille, surtout en situation de communication : "
       "elle altère l'expression verbale et non verbale."),
("LI", "**Ces objets ne servent jamais à faire taire une émotion.** L'émotion est un signal social "
       "qui appelle d'abord une réponse humaine : l'adulte console par sa présence avant de proposer "
       "un objet."),

# -------------------------------------------------------------------
("H2", "Sources & attribution de la deuxième partie"),
("P", "Référentiel national de la qualité d'accueil du jeune enfant, avril 2025. Ministère du "
      "Travail, de la Santé, des Solidarités et des Familles. Élaboration pilotée par l'Inspection "
      "générale des affaires sociales (Dr Nicole Bohic, inspectrice générale des affaires sociales, "
      "et Jean-Baptiste Frossard, directeur de projet à l'IGAS). Base légale : article L214-1-1 du "
      "code de l'action sociale et des familles, qui prévoit que les principes de la charte "
      "nationale pour l'accueil du jeune enfant sont déclinés dans des référentiels nationaux."),
("P", "Document public de l'État français, librement réutilisable. Le ministère invite explicitement "
      "les professionnels à le diffuser, à le compléter et à faire remonter leurs pratiques "
      "(sppe@sante.gouv.fr). Ce statut diffère de celui des deux publications UNICEF de la première "
      "partie, dont les droits de réutilisation restent à traiter au moment du déploiement."),
("P", "Le texte ci-dessus condense les fiches de la partie 1 du document officiel. Aucune pratique "
      "n'y a été ajoutée, aucune n'a été élargie au-delà de ce que la source énonce."),
]


class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("D", "", 7.5)
        self.set_text_color(150)
        self.cell(0, 6, "Référentiel d'éveil 0-3 ans — aSchool · Deuxième partie : les temps du quotidien",
                  align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(220)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-13)
        self.set_font("D", "", 7.5)
        self.set_text_color(150)
        self.cell(0, 6, str(self.page_no()), align="C")


def construire(sortie: str) -> None:
    pdf = PDF(format="A4", unit="mm")
    pdf.set_margins(20, 16, 20)
    pdf.set_auto_page_break(True, margin=18)
    pdf.add_font("D", "", POLICE)
    pdf.add_font("D", "B", POLICE_B)
    pdf.add_page()

    for genre, texte in BLOCS:
        if genre == "H1":
            pdf.set_font("D", "B", 17)
            pdf.set_text_color(30, 41, 59)
            pdf.multi_cell(0, 8.5, texte, new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(109, 40, 217)
            pdf.set_line_width(0.8)
            y = pdf.get_y() + 1.5
            pdf.line(pdf.l_margin, y, pdf.l_margin + 55, y)
            pdf.set_line_width(0.2)
            pdf.ln(6)

        elif genre == "H2":
            if pdf.get_y() > pdf.h - 65:
                pdf.add_page()
            else:
                pdf.ln(4)
            pdf.set_font("D", "B", 12.5)
            pdf.set_text_color(109, 40, 217)
            pdf.multi_cell(0, 6.5, texte, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        elif genre == "RET":
            pdf.set_fill_color(245, 243, 255)
            pdf.set_draw_color(196, 181, 253)
            pdf.set_text_color(49, 46, 129)
            pdf.set_font("D", "B", 8.5)
            depart = pdf.get_y()
            pdf.set_x(pdf.l_margin + 3)
            pdf.multi_cell(pdf.epw - 6, 4.6, "À RETENIR", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("D", "", 9.5)
            pdf.set_x(pdf.l_margin + 3)
            pdf.multi_cell(pdf.epw - 6, 5, texte, new_x="LMARGIN", new_y="NEXT", markdown=True)
            fin = pdf.get_y()
            pdf.rect(pdf.l_margin, depart - 1.5, pdf.epw, fin - depart + 3)
            pdf.ln(5)

        elif genre == "NOTE":
            pdf.set_font("D", "", 8.5)
            pdf.set_text_color(100, 116, 139)
            pdf.set_fill_color(248, 250, 252)
            pdf.multi_cell(0, 4.6, texte, new_x="LMARGIN", new_y="NEXT", fill=True, markdown=True)
            pdf.ln(4)

        elif genre == "SUB":
            pdf.set_font("D", "B", 10.5)
            pdf.set_text_color(30, 41, 59)
            pdf.multi_cell(0, 5.5, texte, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1.5)

        elif genre == "P":
            pdf.set_font("D", "", 10)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(0, 5.2, texte, new_x="LMARGIN", new_y="NEXT", markdown=True)
            pdf.ln(2.5)

        elif genre == "LI":
            pdf.set_font("D", "", 10)
            pdf.set_text_color(15, 23, 42)
            gauche = pdf.l_margin
            pdf.set_x(gauche + 2)
            pdf.cell(4, 5.2, "•")
            pdf.set_x(gauche + 6)
            pdf.multi_cell(pdf.epw - 6, 5.2, texte, new_x="LMARGIN", new_y="NEXT", markdown=True)
            pdf.ln(1.2)

    pdf.output(sortie)
    print(f"OK — {sortie} · {pdf.page_no()} pages")


if __name__ == "__main__":
    import sys
    construire(sys.argv[1] if len(sys.argv) > 1 else "/tmp/partie2.pdf")
