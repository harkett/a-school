# Spec à travailler — aSchool, réalité du projet vs. vision

> Ce document reprend les 19 features de `SPEC_A__ETUDIER.md` et les confronte à ce qui existe réellement dans le code au 13/05/2026. Il ne copie pas la spec originale — il dit ce qui reste à faire, avec quoi, et à quel effort. C'est le document de travail opérationnel.

---

## 1. Positionnement — toujours valide

Le cadrage fondateur tient : outil prof-only, pas de compte élève, RGPD simplifié, le prof valide avant export. Ce n'est pas remis en question. La stack est FastAPI + React, Groq (llama-3.3-70b-versatile), SQLite en production sur aschool.fr.

Ce qui a changé depuis la spec originale : **trois leviers sont déjà en production** (L1 séquences, L2 ambiguïtés, L3 optimiseur). Ce sont des prompts Groq bien construits — efficaces, mais pas les "systèmes cognitifs propriétaires" décrits dans SPECS_LEVIERS. Cette nuance est importante pour estimer l'effort réel des prochains chantiers.

---

## 2. État réel des 19 features

| # | Feature | État | Priorité réelle |
|---|---|---|---|
| 1 | Séquence complète + adaptation/réutilisation | ✅ Livré (partiel — versioning manque) | Compléter |
| 2 | Plan depuis référentiel officiel (RAG) | ❌ Rien | Lourd — chantier futur |
| 3 | Correction pédagogique + fiches d'aide | ⚠️ Correction oui, sandbox non | Compléter |
| 4 | Recherche & résumé de sources fiables (RAG) | ❌ Rien | Lourd — même chantier que F2 |
| 5 | Fiches de révision multi-format | ⚠️ Un format (texte/Word) | Compléter |
| 6 | Visuels vectoriels (Mermaid / SVG / LaTeX) | ❌ Rien | Moyen — injection frontend |
| 7 | Anticipation des erreurs élèves | ⚠️ Détection oui, déconstruction non | Compléter |
| 8 | Différenciation auto (DYS / FLE / approfondissement) | ⚠️ Few-shot ≠ vraie différenciation | Compléter |
| 9 | Mode T1 / prof expérimenté | ❌ Rien | Facile — champ profil |
| 10 | Appréciations bulletins & communication | ❌ Rien | Facile — nouveaux prompts |
| 11 | Supports déclencheurs de créativité élève | ⚠️ Production écrite partielle | Compléter |
| 12 | Escape games pédagogiques | ❌ Rien | Lourd — dans TRACKER OPTIONNEL |
| 13 | Images illustratives génératives | ❌ Rien | Moyen — API externe |
| 14 | Variantes graphiques (BD / manga / rétro) | ❌ Rien | Lourd |
| 15 | Script vidéo adapté au rythme du prof | ❌ Rien | Facile en V1 (texte seul) |
| 16 | Capsules animées (slides + voix off TTS) | ❌ Rien | Très lourd |
| 17 | Vidéo full-IA depuis texte | ❌ Rien | Hors scope |
| 18 | Simulations & expériences virtuelles | ❌ Rien | Hors scope |
| 19 | Avatar animé d'onboarding | ❌ Rien | Hors scope |

---

## 3. Détail feature par feature

---

### ✅ F1 — Séquence complète

**Ce qui existe :** deux prompts Groq dans `backend/routers/sequence.py`. Mode standard (thème + matière + niveau + durée) et mode remédiation (notion bloquante + description libre de la classe). Sauvegarde BDD, historique, partage anonyme entre collègues, suppression. En production.

**Ce qui manque par rapport à la spec :**
- **Versioning** : un prof ne peut pas reprendre sa séquence de l'an dernier et l'adapter au nouveau programme ou à un autre niveau. C'est le vrai différenciant décrit dans la spec ("réutiliser/adapter") — il n'existe pas.
- **Transposition automatique** : "prends cette séquence de 3e et adapte-la pour une 4e" — absent.
- **Mode 3 (trajectoire multi-séances)** : planification d'un chapitre sur plusieurs semaines — documenté dans SPECS_LEVIERS comme extension future de L1, non codé.

> Ce qui reste à faire sur F1 est plus important stratégiquement que tout ce qui a été livré. La génération from scratch, tout LLM sait le faire. La réutilisation et l'adaptation, c'est le vrai moat.

---

### ⚠️ F3 — Correction pédagogique + fiches d'aide

**Ce qui existe :** flag `avec_correction` dans les prompts de génération d'activités. Quand activé, le résultat inclut une section correction textuelle. Disponible sur tous les types d'activités.

**Ce qui manque :**
- **Python sandbox** : vérification calculatoire automatique sur les exercices maths/sciences. Chantier lourd (isolation d'exécution, sécurité, timeout). À ne pas mettre en Cœur V1 — le risque de bug de sécurité est réel.
- **Fiches d'aide à niveaux variables** : une version pour l'élève rapide (raisonnement condensé), une pour l'élève en difficulté (étapes détaillées, analogies). Aujourd'hui la correction est unique pour tous.

> Le sandbox Python est souvent mentionné comme "évident" dans les specs edtech. En production, c'est un vrai chantier de sécurité. Ne pas le sous-estimer.

---

### ⚠️ F5 — Fiches de révision multi-format

**Ce qui existe :** type d'activité `fiche_revision` disponible dans les 12 matières. Sortie : texte structuré + export Word. Un seul format.

**Ce qui manque :**
- **Mémo flash** : format ultra-condensé recto, idéal pour une révision rapide avant un contrôle. Nouveau type d'activité à ajouter dans `MATRICE_ACTIVITES_ASCHOOL.md` — même moteur, nouveau prompt.
- **Carte mentale** : arborescence visuelle des notions clés. Faisable en Mermaid (voir F6) — dépend de l'implémentation de F6.
- **Audio** : lecture TTS de la fiche. Groq propose Whisper (voix→texte), pas TTS (texte→voix). API externe requise.

> Mémo flash = le plus rapide à livrer. Nouveau prompt dans la matrice, 1 session. À prioriser avant carte mentale et audio.

---

### ⚠️ F7 — Anticipation des erreurs élèves

**Ce qui existe :** L2 (`backend/routers/ambiguites.py`) — 1 prompt Groq qui analyse un énoncé et détecte 6 types d'ambiguïtés cognitives, avec reformulations corrigées. Opérationnel, interface complète (`Ambiguites.jsx`).

**Ce qui manque :**
- **Stratégie de déconstruction** : pour chaque ambiguïté détectée, proposer une stratégie pédagogique concrète — contre-exemple à utiliser, activité de remédiation suggérée, formulation alternative à tester. Aujourd'hui L2 dit "voilà le problème", mais pas "voilà comment le traiter en classe".
- C'est une extension du prompt L2 existant. Pas une nouvelle feature, pas un nouveau endpoint.

> Important : L2 ne s'appuie sur aucun graphe des notions. C'est Groq seul. La qualité est bonne mais elle dépend entièrement du modèle — pas d'une base de connaissances structurée propriétaire comme décrit dans SPECS_LEVIERS.

---

### ⚠️ F8 — Différenciation automatique (DYS / FLE / approfondissement)

**Ce qui existe :** few-shot adaptation — après 3 sauvegardes du même type d'activité, le style du prof est reconnu et intégré dans les prochaines générations. Livré le 30/04. Utile, mais ce n'est pas de la différenciation pédagogique — c'est une adaptation au style du prof.

**Ce qui manque :**
- **Version DYS** : syntaxe épurée (phrases courtes, structure simple), vocabulaire non ambigu, sans mise en page complexe. Police OpenDyslexic = côté frontend uniquement.
- **Version FLE/allophones** : vocabulaire simplifié, contextes culturels neutres, langage quotidien.
- **Version approfondissement** : nuances ajoutées, complexification, ouverture vers des notions connexes.

**Comment l'implémenter :** 3 boutons dans `ZoneResultat.jsx` après génération — "Version DYS", "Version FLE", "Version approfondissement". Même endpoint de génération, modificateur ajouté au prompt. Pas de nouveau backend, pas de nouvelle page.

---

### ⚠️ F11 — Supports déclencheurs de créativité élève

**Ce qui existe :** en Français, plusieurs types de production écrite (continuer un texte, décrire un personnage, imaginer la suite d'une scène, texte poétique). Partiellement couvert pour une matière.

**Ce qui manque :**
- **Amorces d'écriture** : phrase d'ouverture fournie, l'élève continue. Type dédié, pas encore dans la matrice.
- **Situations-problèmes ouvertes** : un obstacle, une contrainte, une décision à prendre. Utilisable dans toutes les matières (pas que le Français).
- **Défis structurés** : contraintes formelles créatives ("écrivez en 5 phrases sans le mot 'important'", "résoudre ce problème sans utiliser la multiplication").
- **Canevas BD** : structure narrative en cases. Nécessite F6 (Mermaid) pour être vraiment utile — sans visuels, c'est du texte décrivant une BD, pas une BD.

> Ces types d'activités s'ajoutent dans `MATRICE_ACTIVITES_ASCHOOL.md` et `src/prompts.py`. Même moteur de génération. Travail = rédiger des prompts adaptés.

---

### ❌ F2 + F4 — RAG sur référentiels officiels et sources fiables

**Ce qui existe :** rien. Groq génère à partir de sa connaissance brute, sans aucune source vérifiable, sans alignement garanti avec les programmes officiels.

**Ce que ça demande :**
- Extraction des programmes MEN (~96 documents : 12 matières × 8 niveaux) depuis eduscol.fr — travail mécanique mais long.
- Base vectorielle (ChromaDB, Qdrant, ou équivalent) pour indexer ces documents.
- Pipeline RAG : question du prof → recherche vectorielle → contexte injecté dans le prompt Groq → réponse citant les sources.
- Le L4 dans le TRACKER (OPTIONNEL / Difficile / 2-3 sessions) décrit exactement ce chantier en 3 étapes, mais aucune ligne de code n'existe.

**Pourquoi c'est le vrai moat :** tout LLM peut générer une séquence sur les fractions. Seul aSchool peut garantir que cette séquence est alignée avec le programme officiel de 5e du MEN, avec citation vérifiable. C'est ce qui justifie le prix face à ChatGPT gratuit.

> F2 et F4 partagent la même infrastructure RAG. Les concevoir et implémenter ensemble — pas l'un après l'autre.

---

### ❌ F6 — Visuels vectoriels (Mermaid / SVG / LaTeX)

**Ce qui existe :** rien. Toutes les sorties sont du texte (Markdown, Word, impression CSS).

**Comment l'implémenter :**
- Frontend : intégrer Mermaid.js dans `ZoneResultat.jsx`. La librairie détecte les blocs ` ```mermaid ` et les rend automatiquement en diagramme SVG. Légère, gratuite, bien documentée.
- Backend : quelques nouveaux prompts (diagramme de séquence, frise chronologique, carte conceptuelle, arbre de notions) qui demandent explicitement du code Mermaid en sortie.
- Pas d'infrastructure nouvelle. Pas d'API externe. Une librairie + des prompts.

> Distinction cruciale (rappel de la spec originale) : pas besoin d'IA générative d'images. Mermaid depuis texte → rendu propre, éditable, imprimable. C'est là qu'un LLM brille vraiment, et c'est faisable en 1 session.

---

### ❌ F9 — Mode T1 / prof expérimenté

**Ce qui existe :** rien. Tous les prompts génèrent au même niveau de détail pour tous les profs.

**Comment l'implémenter :**
- Ajouter un champ `experience` dans la table `User` (T1 / confirmé / expert).
- Afficher le champ dans la page "Mon profil" (composant existant).
- Passer ce paramètre dans les prompts existants comme modificateur : T1 → scripts d'oralisation, conseils de gestion de classe, étapes détaillées / expert → format condensé, raccourcis.
- Aucune nouvelle page, aucun nouveau composant. Un champ BDD + une variable dans les prompts.

> Ce n'est pas une feature à part entière — c'est un paramètre de profil qui traverse toutes les features. À traiter comme tel dans l'implémentation.

---

### ❌ F10 — Appréciations bulletins & communication

**Ce qui existe :** côté admin, un système de mail groupé admin→profs (`AdminCommunication`). Côté prof, rien pour générer des textes administratifs.

**Ce que c'est vraiment :** le prof génère des textes à destination des parents ou de l'administration — appréciations de bulletins, mails type, comptes-rendus de réunion. Ce n'est pas de la communication parents gérée par l'outil. Reste dans le cadre prof-only.

**Comment l'implémenter :** nouvelle section "Communication" dans "Mes Outils". Nouveaux prompts dédiés au registre administratif. Même moteur Groq. Le plus impactant : les appréciations bulletins (4 conseils de classe × 30 élèves × 3 trimestres = 360 appréciations/an — ce seul usage justifie l'abonnement pour beaucoup de profs).

> Non présent dans le TRACKER actuellement. À y ajouter.

---

### ❌ F12 — Escape games pédagogiques

**Ce qui existe :** rien. Dans le TRACKER sous OPTIONNEL / Difficile / 2-3 semaines.

**Ce que ça demande :** logique de jeu (scénario + énigmes numérotées + vérification des réponses + progression linéaire), moteur frontend dédié, export HTML imprimable avec énigmes. Pas juste un prompt — une architecture de jeu.

> Rappel de la spec originale : usage réel faible (1-2 fois par trimestre), mais fort effet "wow" en démo commerciale. Ne pas prioriser pour la rétention — prioriser si besoin d'un levier d'acquisition commercial.

---

### ❌ F13 — Images illustratives génératives

**Ce qui existe :** rien.

**Ce que ça demande :** branchement sur une API externe (DALL-E, Stable Diffusion). Coût récurrent par image générée. Uniquement pour l'illustratif décoratif — les modèles sont mauvais sur les schémas techniques, formules mathématiques, cartes géographiques précises. Pour tout ce qui est schéma scientifique ou visuel structuré → voir F6 (Mermaid).

---

### ❌ F14 — Variantes graphiques (BD / manga / rétro / sobre)

**Ce qui existe :** rien. Export actuel = texte brut + Word standard + impression CSS basique.

**Ce que ça demande :** templates CSS/HTML par style, parsing du contenu généré pour le mapper dans le template, tests d'imprimabilité pour chaque style. Chantier de design autant que de développement.

---

### ❌ F15 — Script vidéo adapté au rythme du prof

**Ce qui existe :** rien.

**V1 faisable rapidement :** un nouveau prompt qui génère un script structuré avec timecodes, indications de voix et transitions. Sortie = texte pur que le prof utilise avec son logiciel de montage. Pas d'infrastructure vidéo, pas d'API externe. Une session de travail.

**V2 (plus tard) :** analyse de 30 secondes de voix du prof → adaptation du rythme et du registre du script à son style. Nécessite Groq Whisper (déjà intégré) + analyse du débit. Faisable mais non prioritaire.

---

### ❌ F16 — Capsules animées (slides + voix off TTS)

**Ce qui existe :** Groq Whisper est intégré pour la dictée vocale (voix→texte). C'est l'inverse du besoin (texte→voix).

**Ce que ça demande :** API TTS externe (Google Cloud, Azure, ElevenLabs), générateur de slides automatique, moteur d'assemblage vidéo. Plusieurs mois de développement + coûts récurrents élevés. Pas pour maintenant.

---

### ❌ F17, F18, F19 — Hors scope

- **F17 Vidéo full-IA** : technologie pas mature en 2026. Hallucinations visuelles, incohérence narrative, coûts prohibitifs. Veille uniquement.
- **F18 Simulations** : produit à part entière (style PhET, GeoGebra). Nécessite une équipe et une roadmap dédiées.
- **F19 Avatar onboarding** : contre-productif pour des profs professionnels pressés. L'effet "gadget IA" décrédibilise. Remplacer par tooltips contextuels si besoin d'aide à la prise en main.

---

## 4. Ce qui est dans le TRACKER mais absent des 19 features

Deux leviers planifiés dans le TRACKER (section IMPORTANT) n'apparaissent pas dans `SPEC_A__ETUDIER.md`. Ils sont les prochains à livrer selon le TRACKER.

**L5 — Analyseur de qualité didactique des consignes** (Facile / 1 session)
Analyse chirurgicale d'une consigne isolée : clarté, charge cognitive, cohérence avec l'objectif pédagogique, erreurs typiques qu'elle provoque, version optimisée. Distinct du L2 (L2 analyse un exercice entier, L5 analyse une seule consigne — avant même de la distribuer aux élèves).

**L6 — Détecteur d'équité pédagogique** (Facile / 1 session)
Audit d'une évaluation sur 3 biais genuinement uniques (non couverts par L2/L3/L5) :
- Biais de contenu : l'évaluation mesure-t-elle vraiment ce qu'elle prétend mesurer ?
- Biais de difficulté : le niveau est-il adapté à la classe ?
- Biais émotionnel : les formulations sont-elles anxiogènes ou démotivantes ?

---

## 5. Niveau d'effort réel

> Une session = une séance de travail concentré (~2-3h). Les estimations tiennent compte du code existant, pas d'une base vierge.

| Feature | Sessions | Ce que ça implique concrètement |
|---|---|---|
| **L5** — Analyseur de consignes | **1** | Nouveau prompt Groq + composant React + route `/api/analyser-consigne` + entrée dans Mes Outils |
| **L6** — Détecteur d'équité | **1** | Nouveau prompt Groq + composant React + route `/api/equite-evaluation` + entrée dans Mes Outils |
| **F7** — Déconstruction erreurs (ext. L2) | **0,5** | Modifier le prompt L2 existant pour ajouter une stratégie par ambiguïté + ajuster `Ambiguites.jsx` pour l'afficher |
| **F9** — Mode T1 / expérimenté | **0,5** | 1 champ `experience` dans la table `User` + champ dans `MonProfil.jsx` + variable injectée dans tous les prompts |
| **F8** — DYS / FLE / approfondissement | **1** | 3 boutons dans `ZoneResultat.jsx` après génération + 3 modificateurs de prompt côté backend — aucun nouveau endpoint |
| **F10** — Appréciations bulletins | **1** | Nouvelle section dans Mes Outils + 4 prompts dédiés (appréciation bulletin, mail parents, CR réunion, appréciation libre) |
| **F6** — Mermaid / SVG | **1** | `npm install mermaid` + rendu auto dans `ZoneResultat.jsx` + 4 nouveaux prompts (frise, diagramme, carte conceptuelle, arbre de notions) |
| **F5** — Mémo flash (nouveau format révision) | **0,5** | 1 nouveau type dans `MATRICE_ACTIVITES_ASCHOOL.md` + prompt par matière concernée — même moteur de génération |
| **F11** — Supports créativité (complétion) | **1** | 3-4 nouveaux types dans la matrice (amorces, situations-problèmes, défis structurés) + prompts multi-matières |
| **F1** — Versioning / transposition séquences | **3** | Schéma BDD `sequence_versions` + UI copie/fork + 2 nouveaux prompts (transposer vers autre niveau, actualiser programme) |
| **F3** — Sandbox Python (correction calculatoire) | **5-8** | Isolation d'exécution (Docker ou subprocess sécurisé) + timeout + validation + tests exhaustifs — risque sécurité réel, ne pas sous-estimer |
| **F2 + F4** — RAG programmes officiels | **8-12** | Extraction ~96 docs MEN (eduscol.fr) + indexation vectorielle (ChromaDB ou Qdrant) + pipeline RAG + tests de qualité — projet dans le projet |
| **F14** — Variantes graphiques | **4-6** | Templates CSS/HTML × 4 styles + parsing du contenu généré + tests d'imprimabilité pour chaque style |
| **F15** — Script vidéo V1 | **0,5** | 1 nouveau prompt structuré (timecodes + transitions + indications voix) — sortie texte pur, aucune infrastructure |
| **F12** — Escape game pédagogique | **6-10** | Architecture de jeu complète : scénario + énigmes numérotées + vérification réponses + progression + export HTML imprimable |
| F13, F16, F17, F18, F19 | hors scope | API images externes / TTS / vidéo full-IA / simulations — ne pas planifier |

**Total chantiers planifiables (L5→F1) : ~11 sessions**, soit environ 5-6 semaines à raison de 2 sessions par semaine.

---

## 6. Ordre de travail recommandé

> La logique de cet ordre : d'abord les gains rapides qui prouvent la valeur aux profs pilotes, ensuite les features qui se débloquent les unes les autres, enfin le chantier structurant.

### Bloc 1 — Gains immédiats (sessions 1-3)

| # | Feature | Sessions | Pourquoi maintenant |
|---|---|---|---|
| 1 | L5 — Analyseur de consignes | 1 | Dans le TRACKER, estimé facile, valeur immédiate pour les profs |
| 2 | L6 — Détecteur d'équité | 1 | Idem — les deux leviers vont ensemble dans Mes Outils |
| 3 | F7 — Déconstruction erreurs | 0,5 | Extension du prompt L2 existant — 0 risque, gain direct |
| 4 | F9 — Mode T1 / expérimenté | 0,5 | Champ profil simple, traverse toutes les features — plus on attend, plus il manque partout |

### Bloc 2 — Impact rétention (sessions 3-5)

| # | Feature | Sessions | Pourquoi maintenant |
|---|---|---|---|
| 5 | F8 — DYS / FLE / approfondissement | 1 | 3 boutons + modificateurs prompt — impacte tous les types d'activité d'un coup |
| 6 | F10 — Appréciations bulletins | 1 | 360 appréciations/an par prof — le seul usage qui justifie l'abonnement à lui seul |

### Bloc 3 — Visuels et nouveaux formats (sessions 5-8)

| # | Feature | Sessions | Pourquoi maintenant |
|---|---|---|---|
| 7 | F6 — Mermaid / SVG | 1 | Débloque F5 et F11 — faire d'abord |
| 8 | F5 — Mémo flash | 0,5 | Bénéficie de F6 pour la carte mentale — rapide une fois F6 livré |
| 9 | F11 — Supports créativité | 1 | Bénéficie de F6 pour le canevas BD — nouveaux types dans la matrice |

### Bloc 4 — Différenciant stratégique (sessions 8-11)

| # | Feature | Sessions | Pourquoi maintenant |
|---|---|---|---|
| 10 | F1 — Versioning / transposition séquences | 3 | Le vrai moat : reprendre une séquence de l'an dernier et l'adapter — personne ne le fait bien |

### Bloc 5 — Chantier structurant (sessions 12+, après validation pilotes)

| # | Feature | Sessions | Condition préalable |
|---|---|---|---|
| 11 | F2 + F4 — RAG programmes officiels | 8-12 | Concevoir en session dédiée avant de coder — extraction docs MEN + infrastructure vectorielle |

### Ne pas faire maintenant
- **F3 sandbox Python** : risque sécurité élevé, valeur marginale — reporter sine die
- **F12-F16** : après profs pilotes validés et demande réelle confirmée
- **F17, F18, F19** : hors scope définitif
