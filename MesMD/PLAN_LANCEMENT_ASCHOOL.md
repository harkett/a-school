# Plan de lancement — A-SCHOOL (school.afia.fr)

> Feuille de route du lancement — phases, actions concrètes et règles de communication.
> Version 3 — Ancrée sur les fonctionnalités réelles du produit.
> **Vérifié le : 30/04/2026 — Statut : VPS opérationnel, outil en production**

---

## 1. Ce qu'est A-SCHOOL

A-SCHOOL est un **générateur automatique d'activités pédagogiques** destiné aux enseignants de la 6e à la Terminale.

L'enseignant colle un texte, choisit le type d'activité et le niveau de classe — il obtient en moins de 10 secondes une activité complète, avec correction, prête à imprimer ou distribuer en Word.

**État actuel (avril 2026) :** Français et Histoire-Géographie disponibles pour les niveaux 6e à Terminale, toutes les autres matières en cours de développement.
**Vision complète :** toutes les matières, tous les enseignants de la 6e à la Terminale.
**Évolutions futures :** maternelle/primaire et enseignement supérieur, en options complémentaires.

**Ce que l'outil n'est pas :**
- Pas un outil pour les élèves ou les parents
- Pas un ENT (pas de gestion de classe, de notes, d'élèves)
- Pas un chatbot généraliste — contrairement à ChatGPT ou Copilot, il n'exige aucun prompt à rédiger et connaît les programmes français de la 6e à la Terminale
- **Pas un substitut à l'enseignant.** A-SCHOOL ne remplace pas le prof — il lui fait gagner du temps sur la partie mécanique. L'exercice généré est une base de travail : le prof peut modifier les questions, en supprimer, en ajouter, reformuler les consignes, ajuster le niveau. Le résultat final reste entièrement le sien.

> **"A-SCHOOL prépare. Vous décidez."**

---

## 2. Positionnement

**En une phrase :**
> "Vous avez le texte. A-SCHOOL fait l'exercice."

**Positionnement étendu :**
> A-SCHOOL est fait pour les enseignants de la 6e à la Terminale qui passent des heures chaque semaine à concevoir des exercices à partir de documents. Collez un extrait, choisissez le type d'activité et le niveau — vous avez votre exercice en 10 secondes, prêt à imprimer ou à distribuer en Word. Pas besoin de rédiger un prompt, de reformater le résultat, ni de recommencer à zéro à chaque session : vos activités sont sauvegardées et retrouvables à tout moment.

> "A-SCHOOL retient vos préférences. Et bientôt, après quelques utilisations, il s'adapte à votre façon de formuler les exercices."

**Ce qu'il ne faut jamais dire :**

| À éviter | Pourquoi | À dire à la place |
|---|---|---|
| "Intelligence artificielle" | Méfiance des profs, terme flou | "Génération automatique en 10 secondes" |
| "Révolution de l'enseignement" | Pas crédible | Gain de temps concret et mesurable |
| "Plateforme complète" | Pas d'ENT, pas de gestion élèves | "Générateur d'activités pédagogiques" |
| "Toutes les matières disponibles" | Pas encore le cas | "Français et Histoire-Géo aujourd'hui, toutes les matières bientôt" |
| "Pour les parents" | Hors cible totalement | Ne pas mentionner |

---

## 3. Cibles

### Priorité 1 — Les enseignants de la 6e à la Terminale (cible unique et principale)

Tous les niveaux sont traités à égalité — pas de distinction entre collège et lycée.

| Persona | Profil | Levier d'entrée |
|---|---|---|
| **Prof de français** | Travaille avec des extraits de textes au programme (6e → Terminale), a peut-être essayé ChatGPT mais trouvé les résultats trop génériques ou mal calibrés | "Donne-moi ton extrait. Voilà les questions de compréhension en 10 secondes — calées sur le bon niveau." |
| **Prof d'histoire-géo** | Prépare analyses de documents, frises chronologiques, dissertations, exercices brevet et bac | "Analyse de source automatique, calibrée pour ton niveau." |
| **Prof en surcharge (REP+, polyvalent)** | Manque de temps structurel, ressources insuffisantes | "Je gagne du temps sur toutes mes préparations." |
| **Prof d'autres matières** *(cible à venir)* | Attend l'arrivée de sa matière sur la plateforme | À cibler dès qu'une nouvelle matière est disponible |

### Priorité 2 — Les prescripteurs (pas utilisateurs directs)

- **Formateurs INSPE** → touchent les futurs profs avant qu'ils démarrent leur carrière
- **Associations disciplinaires** (AFEF, APHG, APMEP...) → crédibilité et relais auprès des pairs
- **Inspecteurs académiques** → légitimation institutionnelle

**Règle absolue : ni les élèves, ni les parents ne sont une cible.**

---

## 4. Messages clés

| Message | Formulation | Ancrage produit |
|---|---|---|
| **Gain de temps** | "Ce qui prenait 45 minutes prend maintenant 10 secondes." | Génération < 10 sec, export direct, aucune mise en forme — là où ChatGPT exige encore de reformuler, reformater et recommencer |
| **Spécificité métier** | "Pas un chatbot. Un outil calé sur les programmes de la 6e à la Terminale." | 28 types d'activités calés sur les référentiels brevet, bac, BO — pas de prompt à rédiger, pas de résultat générique |
| **Utilisable immédiatement** | "Téléchargez en Word ou TXT. Imprimez. Distribuez. C'est tout." | Export `.docx`, `.txt`, impression directe, envoi par e-mail |
| **Bibliothèque personnelle** | "Toutes vos activités sont sauvegardées. Retrouvez, réutilisez, adaptez en un clic." | Historique "Mes activités" — là où ChatGPT repart de zéro à chaque session, A-SCHOOL construit votre capital pédagogique |
| **Données privées** | "Vos textes, vos activités, votre compte. Rien n'est partagé." | Compte individuel, historique privé — vos documents ne servent pas à entraîner un modèle tiers |
| **Produit qui évolue avec vous** | "Vous signalez ce qui ne va pas. On corrige." | Feedback intégré, réponse sous 48h |
| **Un outil qui devient plus précieux avec le temps** | "Plus vous l'utilisez, plus il vous connaît. Un prof qui a généré 50 activités avec son style appris ne repart pas chez un concurrent." | Adaptation au style via l'historique — promesse marketing et réalité technique parfaitement alignées |

---

## 5. Leviers viraux intégrés au logiciel

Ces leviers fonctionnent **sans pub**, souvent **sans action consciente du prof**.

### Levier 1 — Pied de page dans le fichier Word (viral passif)
Le prof télécharge un `.docx` et le distribue à ses élèves ou envoie à un collègue.
**Action :** Ajouter un pied de page discret : *"Activité générée avec A-SCHOOL — school.afia.fr"*
**Impact :** chaque document distribué expose l'outil à d'autres profs sans effort.

### Levier 2 — Signature dans les e-mails (viral passif)
Le bouton `mailto:` ouvre le client mail avec l'activité prête. Si envoyée à un collègue, ce collègue voit comment c'est généré.
**Action :** Ajouter en bas du corps du mail : *"Généré avec A-SCHOOL — school.afia.fr — Créez votre compte gratuit"*

### Levier 3 — Pied de page à l'impression (exposition physique)
Le prof imprime et distribue en classe. Si "A-SCHOOL" apparaît en bas de la feuille, d'autres profs qui voient la copie posent la question.
**Action :** Ajouter automatiquement un pied de page sur toutes les impressions : *"Généré avec A-SCHOOL — school.afia.fr"* — visible sur la feuille papier distribuée en classe.

### Levier 4 — Compteur "Mes activités" (rétention + fierté)
Le prof retrouve toutes ses activités en un clic. Plus il utilise, moins il repart — et plus il en parle. C'est l'inverse de ChatGPT, qui repart de zéro à chaque session et ne conserve rien de structuré.
**Action :** Afficher un compteur visible "Vous avez créé X activités". Les gens aiment voir leur propre production — et un prof avec 50 activités sauvegardées ne repart pas chez un concurrent.

### Levier 5 — Feedback → ambassadeur
Le formulaire de feedback crée un lien direct entre le prof et l'équipe.
**Action :** Répondre à chaque feedback sous 48h. Un prof écouté dès le départ devient le meilleur ambassadeur de l'outil.

### Levier 6 — Spécialisation visible sur la page d'accueil
Un outil générique (ChatGPT) ne peut pas dire "je suis fait pour toi". A-SCHOOL si.
**Action :** Afficher clairement les matières disponibles avec des exemples concrets de sorties générées, dès la page d'accueil.

### Levier 7 — Kit de démonstration (activation du bouche-à-oreille)
Préparer 3 exemples réels d'activités générées — une par matière et par niveau — prêts à partager sans avoir à ouvrir l'outil. Un prof peut montrer le résultat à un collègue en salle des profs, par message ou par email, sans démonstration live.
**Action :** Produire et mettre à disposition ces exemples dès la phase pilote (Word + capture écran).
**Impact :** réduit la friction du bouche-à-oreille — le collègue voit le résultat avant même de s'inscrire.

### Levier 8 — Bouton "Partagez avec vos collègues" sur afia.fr (bouche-à-oreille numérique direct)
Un visiteur sur la page School d'afia.fr peut envoyer une invitation à ses collègues sans quitter la page — sans copier-coller une URL, sans ouvrir sa messagerie.
**Où :** bouton discret sous "Vous avez déjà un compte ? Connectez-vous" dans le hero et dans le CTA final de la page `/school` sur afia.fr.
**Mécanisme :** une modale s'ouvre — le visiteur saisit son nom (facultatif) et jusqu'à 5 adresses e-mail séparées par des virgules. Le backend Django (`POST /api/vitrine/recommander/`) valide les adresses et envoie un e-mail d'invitation à chaque destinataire avec le lien school.afia.fr.
**Anti-spam :** limité à 5 adresses par envoi, 5 envois par IP et par jour.
**Corps du mail envoyé :**
```
[Prénom Nom] vous recommande A-SCHOOL, l'outil gratuit pour les enseignants.
Collez un texte, choisissez le type d'activité et le niveau — exercice complet en 10 s.
→ Créez votre compte gratuit sur school.afia.fr
```
**Impact :** chaque prof qui découvre l'outil peut déclencher une chaîne dans son établissement en 30 secondes, sans sortir de la page.

---

## 6. Canaux de communication

### Canal 1 — Bouche-à-oreille entre profs (priorité absolue)
Les profs font confiance à leurs pairs. Un outil recommandé par un collègue vaut 10 publicités.

**Actions :**
1. Identifier et chouchouter les 2 à 3 profs pilotes actuels
2. Leur demander de montrer l'outil à 1 ou 2 collègues dans leur établissement
3. Répondre à tous leurs feedbacks en moins de 48h

### Canal 2 — Groupes Facebook de profs (acquisition organique)

**Groupes cibles :**
- "Profs de français" (> 50 000 membres)
- "Profs d'histoire-géo" (> 30 000 membres)
- "Ressources pédagogiques lycée / collège"
- Groupes académiques régionaux

**Format de post :**
```
J'ai testé A-SCHOOL cette semaine pour mes 4e.
J'ai collé un extrait de Maupassant, choisi "exercices de réécriture",
et j'avais mes consignes + correction en 10 secondes.
Le .docx est directement utilisable — sans reformater, sans copier-coller.

J'avais essayé ChatGPT pour ça. Le résultat était trop générique,
pas calé sur le niveau. Là, c'est fait pour nous.

Voilà ce que ça donne : [capture écran]
Gratuit pour l'instant → school.afia.fr
```
**Règle :** toujours un exemple réel en capture d'écran. Jamais de publicité abstraite.

### Canal 3 — LinkedIn (crédibilité institutionnelle)
**Cible :** formateurs INSPE, inspecteurs académiques, directeurs, journalistes éducation
**Format :** données d'usage + témoignage prof + exemple concret. Pas de jargon tech.

### Canal 4 — Associations disciplinaires
- **AFEF** (Association Française des Enseignants de Français)
- **APHG** (Association des Professeurs d'Histoire-Géographie)
- Élargir aux autres associations au fur et à mesure des nouvelles matières disponibles

**Action :** proposer une démo de 20 min lors d'une réunion ou webinaire. Un seul contact peut débloquer des dizaines d'inscriptions qualifiées.

### Canal 5 — INSPE (acquisition amont)
Présenter A-SCHOOL aux futurs enseignants en formation initiale → adoption dès le début de carrière, avant que les réflexes avec des outils généralistes (ChatGPT, Copilot) ne soient installés.

### Canal 6 — SEO / Contenu (trafic organique durable)
**Articles à produire :**
1. "10 exemples d'exercices de réécriture pour la 4e générés en 10 secondes"
2. "Comment créer une fiche de révision brevet à partir d'un document Histoire-Géographie"
3. "Comment préparer un exercice sur document historique en 10 secondes ?"
4. "ChatGPT ou A-SCHOOL : lequel choisir pour préparer ses cours ?" *(article comparatif — fort potentiel SEO)*

**Règle :** chaque article contient un exemple réel de sortie de l'outil.

---

## 7. Séquence e-mail onboarding

| Email | Timing | Contenu |
|---|---|---|
| Bienvenue | J+0 (vérification compte) | "Votre compte est actif. Voici comment faire votre première activité." |
| Premier usage | J+2 | "Avez-vous essayé les exercices de réécriture ? Voilà un exemple." |
| Rétention | J+7 | "X activités générées cette semaine par vos collègues." |
| Feedback | J+14 | "Qu'est-ce qui manque ? Répondez directement." |

---

## 8. Calendrier de lancement

### Phase 0 — Amorçage pilote (Avril 2026)

**Email ciblé de présentation — profs sélectionnés**

Envoi d'un email de présentation à une sélection de profs identifiés manuellement (contacts directs, réseau proche). Objectif : recruter les 2-3 premiers profs pilotes fondateurs avant l'ouverture progressive de mai.

*À détailler — tâche du 30 avril 2026*

---

### Phase 1 — Consolidation pilote (Mai 2026)

| Semaine | Action |
|---|---|
| S0 | **Déploiement VPS — school.afia.fr opérationnel** |
| S1 | Ajouter pied de page A-SCHOOL dans les exports `.docx` et `@media print` |
| S1 | Ajouter signature dans le corps du mail `mailto:` |
| S2 | Entretien structuré avec les profs pilotes (20 min, retours concrets) — les encourager à générer un maximum d'activités d'un même type pour amorcer l'adaptation au style (cold start) |
| S3 | Créer 3 captures d'écran d'exemples à partager (une par matière et niveau) |
| S4 | Premier post dans 1 groupe Facebook de profs (exemple réel) |

### Phase 2 — Ouverture progressive (Juin 2026)

| Semaine | Action |
|---|---|
| S1-S2 | Implémenter séquence e-mail onboarding (4 mails) |
| S2 | Ajouter compteur "X activités créées" dans "Mes activités" |
| S3 | Post LinkedIn avec données pilote + témoignage prof |
| S4 | Contacter AFEF ou APHG pour présentation |

### Phase 3 — Expansion matières (avant fin juin 2026)

À chaque nouvelle matière disponible, relancer une campagne ciblée sur les profs de cette discipline (6e à Terminale) :
- Contacter l'association disciplinaire correspondante
- Post ciblé dans le groupe Facebook de la matière
- Nouveau persona activé dans la communication

### Phase 4 — Avant rentrée (Août-Septembre 2026)

La rentrée est le moment clé : les profs préparent leurs séquences.

| Action | Timing |
|---|---|
| Post Facebook "préparez vos séquences de rentrée avec A-SCHOOL" | 25 août |
| Article blog "10 activités de rentrée prêtes en 2 minutes" | 28 août |
| Campagne e-mail vers inscrits inactifs | 1er septembre |
| **Objectif :** 50 profs actifs | Rentrée 2026 |

---

## 9. Indicateurs de performance

| Métrique | Objectif Mai 2026 | Objectif Rentrée 2026 |
|---|---|---|
| Inscrits vérifiés | 10 | 50 |
| Activités générées | 100 | 500 |
| Rétention J+7 | 40% | 50% |
| Feedbacks reçus | 10 | 30 |
| Note moyenne feedback | > 3,5 / 5 | > 4,0 / 5 |

---

## 10. État des fonctionnalités

| Fonctionnalité | Statut |
|---|---|
| Dictée vocale | ✅ Disponible |
| Lecture et interprétation de documents scannés (OCR) | ✅ Disponible |
| Autres matières (Maths, SVT, Philo, Langues...) | En cours de développement |
| Partage d'activités entre collègues | Prévu |
| Export PDF | Prévu |
| Application mobile (PWA) | Prévu |
| Google OAuth | Prévu |
| Intégration ENT (Pronote...) | Prévu |
| Tableau de bord multi-profs établissement | Prévu |

---

## 11. Amélioration future : Preuve sociale, avis et témoignages

Aujourd'hui, la fonctionnalité "Donner votre avis" permet de recueillir des retours utilisateurs simples.

**Pour renforcer la crédibilité et l'adoption, il est recommandé d'aller plus loin :**

- Collecter et afficher des témoignages clients détaillés (texte, vidéo)
- Mettre en avant des études de cas concrètes (avant/après, impact réel)
- Publier des chiffres d'usage (nombre d'activités créées, taux de satisfaction)
- Ajouter une section dédiée sur le site/app pour valoriser ces preuves sociales
- Utiliser ces éléments dans la communication (posts, e-mails, webinaires)

**Objectif :** Passer d'un simple recueil d'avis à une stratégie de preuve sociale approfondie, pour rassurer et convaincre les nouveaux utilisateurs et prescripteurs.

---

*Document — school.afia.fr — Version 3, 30 avril 2026*
