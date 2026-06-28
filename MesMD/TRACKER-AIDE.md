# Tracker Aide — système d'aide aSchool

> Préparation seule. Rien n'est appliqué au code tant que la session structure n'est pas finie.
> Spec : archivée hors projet (plus nécessaire à ce stade).
> À reprendre au code : 2 modifs déjà posées, non commitées — `Sidebar.jsx` (label « Centre d'aide ») + `Aide.jsx` (composants `OptionTabs`/`OptionPlaceholder` ajoutés, pas encore branchés). Elles font partie de l'Étape 1.

## Décisions actées
- [x] Aide à 3 niveaux : aide de page · aide contextuelle · Centre d'aide.
- [x] L'aide de page ouvre un panneau qui glisse à droite, sans cacher la page (pas un onglet).
- [x] La FAQ est écrite dans l'appli, pas modifiable en ligne pour l'instant.
- [x] L'entrée du menu « Aide » devient « Centre d'aide ».

## Étape 1 — Centre d'aide : la structure de la page
- [ ] Renommer le menu et le titre de page en « Centre d'aide ».
- [ ] Diviser la page en 3 choix : Aide · FAQ · Prise en main.
- [ ] Choix « Aide » = les fiches actuelles, inchangées.
- [ ] Choix « FAQ » = emplacement « bientôt » à l'Étape 1, rempli à l'Étape 2.
- [ ] Choix « Prise en main » = emplacement « bientôt » pour l'instant.
- [ ] La barre de recherche reste visible en haut quand on fait défiler.

## Étape 2 — FAQ et impression des fiches
- [ ] Écrire les questions/réponses de la FAQ.
- [ ] La recherche cherche aussi dans la FAQ.
- [ ] Un bouton « Imprimer / Télécharger » sur chaque fiche.

## Étape 3 — L'aide de chaque page
- [ ] Créer le panneau qui glisse à droite, commun à toute l'appli.
- [ ] « Comment ça marche » sur les pages à onglets.
- [ ] Bouton « Aide » sur les pages sans onglets.
- [ ] Y rebrancher les 4 « Comment ça marche » déjà écrits.
- [ ] Chaque aide de page renvoie vers sa fiche du Centre d'aide.

## Étape 4 — L'aide au clic droit
- [ ] Garder les bulles au survol (déjà là).
- [ ] Ajouter une explication au clic droit là où c'est utile.

## À traiter ailleurs (hors passe Aide)
- [ ] Réaligner le rangement des fiches sur Créer/Analyser/Améliorer/Adapter — plus tard.
- [ ] Header (et footer ?) figés sur toute l'appli — décision séparée.

## Contenu rédigé (rempli tâche par tâche)

- [x] FAQ — questions/réponses.
- [x] Aide au clic droit — textes courts par zone.
- [x] Renvois aide de page → fiche (table de l'Étape 3).
- [x] Fiche « Analyser une consigne » — rédigée (outil qui n'avait pas de fiche).
- [x] Fiche « Mes stats » — rédigée.
- [x] Fiches « Accueil » · « À propos » · « Bientôt disponible » — rédigées (zéro page sans fiche).
- [x] Prise en main — squelette (chantier distinct, non développé).
- [ ] Fiche « Équité » — à rédiger quand l'outil sera en service.

### FAQ

**Compte & connexion**
- **Je n'ai pas reçu l'email de vérification ?** Vérifiez vos spams ; sinon, cliquez sur « Renvoyer l'email de vérification » sur la page de connexion.
- **J'ai oublié mon mot de passe.** Cliquez sur « Mot de passe oublié ? » sur la page de connexion : un lien de réinitialisation vous est envoyé par email.
- **Comment changer ma matière ou mon niveau ?** Dans « Mon profil ». Pour un changement ponctuel, utilisez le sélecteur de matière dans les paramètres de génération.

**Créer une activité**
- **Comment générer ma première activité ?** Fournissez un texte (collez, dictez ou scannez), choisissez le type, cliquez sur « Générer ». → fiche *Première activité*
- **Comment obtenir aussi la correction ?** Cochez « Avec correction » avant de générer : le corrigé apparaît sous l'activité.
- **Le résultat ne me convient pas.** Cliquez sur « Régénérer », changez de type, ou clarifiez le texte source.
- **Comment dicter le texte au lieu de le taper ?** Cliquez sur « Dicter », autorisez le micro, parlez, puis arrêtez : le texte s'insère seul. → fiche *Dictée vocale*
- **Comment scanner un document papier ?** Cliquez sur l'icône appareil photo dans la zone de texte : le texte est extrait automatiquement. → fiche *Scanner un document*
- **Je n'ai pas de texte sous la main.** Cliquez sur « Tester un exemple » : un texte adapté à votre matière se remplit tout seul.
- **Quel texte donne les meilleurs résultats ?** Un texte en français, en paragraphes, de 200 à 1 000 mots. → fiche *Conseils pour un bon texte source*
- **À quoi sert le « sous-type » ?** Il cible la nature de l'exercice (inférence, lexique…) ; plus il est précis, mieux le résultat colle à votre besoin.
- **Comment exporter ou imprimer une activité ?** Depuis le résultat : Word (.docx), texte brut, impression ou envoi par email.

**Les autres outils**
- **Comment créer une séquence de cours ?** Dans « Séquence → Créer » : décrivez le thème, choisissez le nombre de phases et le mode. → fiche *Générateur de séquences*
- **Puis-je améliorer une séquence existante ?** Oui, avec l'Optimiseur : il l'analyse sur 6 critères et la réécrit corrigée. → fiche *Améliorer une séquence*
- **Comment vérifier qu'une consigne est claire ?** Collez-la dans le Détecteur d'ambiguïtés : il repère les zones à risque et propose une reformulation. → fiche *Détecter les ambiguïtés*

**Style, réseau, exemples**
- **aSchool s'adapte-t-il à ma façon de faire ?** Oui : dès la 3e activité du même type que vous sauvegardez, il génère dans votre style, sans rien régler. → fiche *aSchool apprend votre style*
- **Mes activités sont-elles enregistrées ?** Oui, automatiquement. Retrouvez-les dans « Activité → Historique ».
- **Où voir ce que mes collègues partagent ?** Dans « Mon réseau → Activités / Séquences ». → fiche *Mon réseau*
- **Y a-t-il des exemples tout faits ?** Oui, la Bibliothèque contient 24 activités d'exemple (2 par matière). → fiche *La Bibliothèque*

**Partage et retours**
- **Comment partager une activité avec un collègue ?** Depuis l'historique, cliquez sur « Partager » et choisissez d'afficher votre nom ou de rester anonyme. → fiche *Partager avec les collègues*
- **Mon prénom est-il visible quand je partage ?** Seulement si vous choisissez « Afficher mon nom » ; l'email n'est jamais montré.
- **Comment retirer un partage ?** Recliquez sur « Partager » : l'activité quitte Mon réseau mais reste dans votre historique.
- **Comment signaler un problème ou proposer une idée ?** Via « Mes feedbacks » : choisissez Problème, Suggestion ou Question, et suivez l'état de votre retour.
- **Comment joindre une capture d'écran à un feedback ?** Capturez avec Win+Maj+S, enregistrez l'image, puis joignez-la via « Parcourir ».
- **Puis-je modifier un feedback déjà envoyé ?** Oui, tant qu'il est « Nouveau » ou « En cours » : cliquez sur « Modifier ».
- **Comment noter aSchool ?** Via « Notez aSchool » dans le menu : 1 à 5 étoiles, avec un commentaire optionnel.

**Téléphone & hors-ligne**
- **Puis-je installer aSchool sur mon téléphone ou ma tablette ?** Oui : sur iPhone via Safari, sur Android via Chrome. → fiches *Installer sur iPhone / sur Android*
- **aSchool fonctionne-t-il sans connexion ?** La navigation reste possible, mais générer, sauvegarder et partager nécessitent internet. → fiche *Mode hors-ligne*
- **Une bannière annonce une mise à jour.** Rien à faire : la page se recharge seule au bout de 30 s, ou cliquez « Actualiser maintenant ». → fiche *Mise à jour automatique*

**Petits soucis**
- **Mes activités sortent incohérentes, pourquoi ?** Souvent à cause de la traduction automatique du navigateur. Dans Edge : « Plus » → « Ne jamais traduire ce site ».
- **Le bouton « Générer » est grisé.** La zone de texte source est vide : ajoutez un texte et le bouton s'active.
- **Le niveau Supérieur affiche un message de développement.** Les activités pour le Supérieur (BTS, prépa, licence) arrivent ; de la 6e à la Terminale, tout fonctionne.

### Aide au clic droit (textes par zone)

> Explication courte (3-5 lignes) au clic droit sur une zone. Pas chaque bouton (les bulles au survol couvrent ça) : seulement les zones utiles. Au moment du code, on décide zone par zone lesquelles brancher (la spec dit : pas systématique).

**Créer une activité**
- *Zone Texte source* — Le point de départ : collez un texte, dictez-le à la voix ou scannez un document. aSchool s'appuie dessus pour produire l'activité. Pas de texte ? Cliquez sur « Tester un exemple ».
- *Type et sous-type* — Le type fixe le genre d'exercice (compréhension, vocabulaire, résumé…), le sous-type le précise. Plus le choix est ciblé, plus le résultat colle à votre besoin.
- *Avec correction* — Cochez pour obtenir le corrigé complet sous l'activité — gain de temps pour préparer ou corriger.
- *Zone résultat* — L'activité générée. Vous pouvez la régénérer (chaque essai diffère), la télécharger (Word, texte), l'imprimer, l'envoyer par email, ou la sauvegarder dans Mes activités.

**Profil**
- *Matière et niveau* — Votre matière et votre niveau par défaut. Ils pré-remplissent chaque génération et filtrent Mes activités. Pour les changer durablement, passez par Mon profil.

**Séquence**
- *Zone thème + phases + mode* — Décrivez le thème, choisissez le nombre de phases et leur durée, puis le mode : Standard (progression classique) ou Remédiation (élèves en difficulté).

**Optimiseur**
- *Zone séquence à analyser* — Collez une séquence existante. aSchool l'examine sur 6 critères, donne un score, et la réécrit corrigée.

**Détecteur d'ambiguïtés**
- *Zone énoncé à vérifier* — Collez un exercice ou une consigne. aSchool repère ce qui peut être mal compris par les élèves et propose une reformulation claire.

**Mes activités**
- *Liste des activités* — Vos générations sauvegardées, filtrées par votre matière et niveau. Survolez une ligne pour la rouvrir (Reprendre), la partager ou la supprimer.

**Mon réseau**
- *Activités/séquences partagées* — Ce que vos collègues ont choisi de partager. Filtrez, ouvrez le détail, ou cliquez « Utiliser » pour repartir de leur contenu.

**Partage**
- *Bouton Partager* — Rend votre activité visible dans Mon réseau. Vous choisissez d'afficher votre nom ou de rester anonyme ; l'email n'est jamais montré.

**Mes feedbacks**
- *Espace feedbacks* — Signalez un problème, proposez une idée ou posez une question, puis suivez l'état de votre retour (Nouveau → En cours → Traité).

### Renvois aide de page → fiche (Étape 3)

> Chaque aide de page (panneau slide-over) finit par « Pour aller plus loin : voir la fiche dans le Centre d'aide » et pointe vers la/les fiche(s) ci-dessous.

| Écran | Aide de page | Renvoie vers |
|---|---|---|
| Accueil | bouton « Aide » | Accueil · Première activité |
| Créer une activité | onglet « Comment ça marche » | Créer une activité · Dictée · Scanner · Champs · Conseils texte source |
| Créer une séquence | onglet « Comment ça marche » | Générateur de séquences |
| Optimiseur | onglet « Comment ça marche » | Améliorer une séquence |
| Détecteur d'ambiguïtés | onglet « Comment ça marche » | Détecter les ambiguïtés |
| Consigne | onglet « Comment ça marche » | Analyser une consigne |
| Mes activités | bouton « Aide » | Historique des activités · Partager avec les collègues |
| Historique des séquences | bouton « Aide » | Historique des séquences |
| Mon réseau | bouton « Aide » | Mon réseau |
| Mon profil | bouton « Aide » | Compléter votre profil · Champs |
| Mes feedbacks | bouton « Aide » | Mes feedbacks |
| Mes stats | bouton « Aide » | Mes stats |
| Bibliothèque | bouton « Aide » | La Bibliothèque |
| À propos | bouton « Aide » | À propos |
| Bientôt disponible | bouton « Aide » | Bientôt disponible |

### Fiches manquantes à créer (zéro trou)

> Objectif : aucun outil/page sans fiche. Au moment du code, ces fiches rejoignent les fiches existantes du Centre d'aide.

#### Fiche — Analyser une consigne (catégorie Analyser)

L'Analyseur de consignes examine **une seule consigne** (l'instruction donnée à l'élève) et mesure sa qualité didactique, puis propose une version optimisée prête à coller.

**1. Collez une consigne isolée**
- Une consigne = une instruction adressée à l'élève, pas un exercice entier.
- Exemple : « Analysez le personnage en faisant référence au texte. »
- Pas de consigne sous la main ? « Tester un exemple » en remplit une, adaptée à votre matière.

**2. Lancez l'analyse**
- Cliquez sur « Analyser la consigne » : aSchool l'examine sur 5 axes didactiques.

**3. Lisez le rapport**
- Un verdict global sur la clarté de la consigne.
- Pour chaque point : l'extrait exact, le problème identifié, une suggestion concrète.
- Une **consigne optimisée**, prête à copier.

**Les 5 axes analysés**
- **Clarté linguistique** — formulations floues, vagues ou trop longues.
- **Précision didactique** — la consigne dit-elle exactement ce qu'elle évalue ?
- **Ambiguïté conceptuelle** — mots à double sens (« analyser », « simplifier », « produit »…).
- **Structure logique** — étapes implicites, tâches multiples, sauts logiques.
- **Risque d'erreurs typiques** — formulations qui provoquent des erreurs récurrentes.

**Différence avec le Détecteur d'ambiguïtés** — le Détecteur analyse un *exercice entier* (plusieurs questions) ; l'Analyseur de consignes se concentre sur *une seule consigne* et va plus loin sur la précision didactique, la charge cognitive et la structure.

*Conseil : utilisez-le avant de distribuer un contrôle — une consigne nette réduit les questions pendant l'épreuve.*

#### Fiche — Mes stats (catégorie Comprendre)

**Mes stats** vous montre, en un coup d'œil, votre activité sur aSchool et la vitalité de la communauté. Rien à configurer : tout se met à jour automatiquement.

**Votre activité**
- **Activités depuis votre début** — le total de vos générations, avec une estimation du temps gagné.
- **Mes séquences** — le nombre d'orchestrations que vous avez créées.
- **Partagées** — combien de vos contenus sont visibles par vos collègues.

**Vos repères personnels**
- **Votre type favori** — le type d'activité que vous générez le plus.
- **Activités ce mois-ci** — votre rythme du mois en cours.
- **« aSchool vous connaît à X % »** — à quel point l'outil a appris votre style. Il s'active après 3 activités sauvegardées du même type, puis monte à mesure que vous l'utilisez.

**La communauté aSchool**
- **Profs actifs** aujourd'hui et cette semaine.
- **Total des activités** créées sur la plateforme.
- **Partages** entre collègues.

*Ces chiffres sont indicatifs et évoluent en continu — un repère, pas une évaluation.*

#### Fiche — Accueil (catégorie Premiers pas)

L'Accueil est votre tableau de bord à la connexion : un coup d'œil sur vos dernières créations et un accès rapide à tout.
- Un **bandeau de bienvenue** rappelle votre matière, votre niveau et votre progression.
- **Mes dernières créations** — votre dernière activité et votre dernière séquence, rechargeables en un clic, plus des raccourcis vers les outils d'analyse.
- À droite : un bouton **Mes outils**, un accès à **Mes statistiques**, et une **astuce** qui change à chaque visite (flèches pour la parcourir).

#### Fiche — À propos (catégorie Comprendre)

La page À propos rassemble les informations sur l'application et votre compte.
- La **version** d'aSchool et l'environnement.
- L'**adresse du compte** connecté.
- La liste des **matières disponibles**.
- **Ma fiche aSchool** — un document de présentation à imprimer ou partager à vos collègues.
- Des accès directs pour **donner votre avis** ou **envoyer un retour**.

#### Fiche — Bientôt disponible (catégorie Comprendre)

La page Bientôt disponible montre ce qui arrive sur aSchool — et vous laisse peser sur les priorités.
- **Vous avez une idée ?** — proposez une fonctionnalité ; chaque suggestion est lue.
- **Nos idées à nous** — les fonctionnalités en préparation, classées par thème.
- Sur chacune, un bouton **« Je veux cette fonctionnalité »** : plus une idée est demandée, plus elle remonte dans nos priorités.

#### Fiche — Équité *(à rédiger le jour où l'outil entre en service)*

### Prise en main — squelette (chantier distinct, à développer plus tard)

**Principe :** un assistant **optionnel** qui guide le prof dans ses premiers pas, **à la demande** (jamais forcé — principe de non-intrusivité de la spec). Relançable à tout moment depuis le Centre d'aide.

**Les grandes étapes (ossature) :**
1. **Bienvenue** — ce qu'est aSchool en une phrase, et ce que l'assistant va montrer.
2. **Compléter son profil** — matière + niveau, et pourquoi ça compte.
3. **Générer sa première activité** — fournir un texte (ou « Tester un exemple ») → choisir le type → Générer.
4. **Récupérer le résultat** — exporter, imprimer ou sauvegarder.
5. **L'apprentissage du style** — sauvegarder pour qu'aSchool s'adapte à vous.
6. **Aller plus loin** — un mot sur les séquences, l'analyse, et le Centre d'aide.
7. **Fin** — « Vous êtes prêt » + accès direct à Mes outils.

**Cadrage pour le futur chantier :**
- Optionnel, passable et quittable à toute étape (pas de blocage).
- Chaque étape **renvoie vers la fiche correspondante** (réutilise les fiches existantes, pas de contenu dupliqué).
