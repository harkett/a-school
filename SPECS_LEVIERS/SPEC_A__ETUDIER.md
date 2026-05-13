# Spécification à étudier — Générateur d'activités pédagogiques IA

> Document de synthèse stratégique pour la conception d'un générateur d'activités pédagogiques basé sur LLM, destiné aux enseignants de la maternelle au supérieur.

---

## 1. Positionnement (parti pris fondateur)

- **Outil prof-only** — aucun compte élève, aucune interface élève. Vente B2B (établissement / prof / collectivité).
- **Le prof reste maître** — l'IA propose, le prof valide systématiquement avant export. Responsabilité juridique transférée au prof-auteur.
- **Le support est extrait** — tout livrable doit pouvoir vivre sans la plateforme (PDF, DOCX, PPTX, lien lecture seule).
- **De la maternelle au supérieur** — l'outil s'adapte au niveau enseigné.

> 💡 **Pourquoi ce cadrage est stratégique** : pas de compte élève = surface RGPD massivement réduite, pas de consentement parental, pas d'auth mineurs. C'est une arme de différenciation face aux concurrents qui s'enlisent dans le RGPD scolaire.

---

## 2. Synthèse visuelle de priorisation

| # | Feature | Valeur | Faisabilité | Priorité |
|---|---|---|---|---|
| 1 | Séquence complète + adaptation/réutilisation | ★★★★★ | ★★★★★ | ✅ Cœur |
| 2 | Plan depuis référentiel officiel (RAG) | ★★★★★ | ★★★★ | ✅ Cœur |
| 3 | Correction pédagogique + fiches d'aide à la compréhension | ★★★★★ | ★★★★ | ✅ Cœur |
| 4 | Recherche & résumé de sources fiables (RAG) | ★★★★ | ★★★★ | ✅ Cœur |
| 5 | Fiches de révision multi-format | ★★★★ | ★★★★★ | ✅ Cœur |
| 6 | Visuels vectoriels (Mermaid / SVG / LaTeX) | ★★★★ | ★★★★ | ✅ Prioritaire |
| 7 | Anticipation des erreurs élèves ⭐ | ★★★★ | ★★★★★ | ✅ Prioritaire |
| 8 | Différenciation auto (DYS / FLE / approfondissement) ⭐ | ★★★★ | ★★★★ | ✅ Prioritaire |
| 9 | Mode T1 / prof expérimenté ⭐ | ★★★ | ★★★★ | ✅ Prioritaire |
| 10 | Newsletter & communication parents | ★★★ | ★★★★★ | ✅ Prioritaire |
| 11 | Supports déclencheurs de créativité élève | ★★★ | ★★★★ | ✅ Prioritaire |
| 12 | Escape games pédagogiques | ★★★ | ★★★★ | 🟡 Secondaire |
| 13 | Images illustratives génératives (cadrées) | ★★★ | ★★★ | 🟡 Secondaire |
| 14 | Variantes graphiques d'un même contenu ⭐ | ★★★ | ★★★★ | 🟡 Secondaire |
| 15 | Script vidéo adapté au rythme du prof | ★★★ | ★★★★ | 🟡 Plus tard |
| 16 | Capsules animées (slides + voix off TTS) | ★★★ | ★★ | 🟡 Plus tard |
| 17 | Vidéo full-IA depuis texte | ★★ | ★ | ❌ R&D |
| 18 | Simulations & expériences virtuelles | ★★ | ★ | ❌ Hors scope |
| 19 | Avatar animé d'onboarding | ★ | ★★★ | ❌ Éviter |

⭐ = levier ajouté à la liste initiale, fort potentiel différenciant.

---

## 3. Détail des features avec conseils

### 🟢 Cœur — sans ces 5, pas de produit

**1. Séquence complète & adaptation**
Plan de séquence, fiche enseignant, fiche élève, supports, évaluation finale.

> 💡 **Le vrai différenciant n'est pas de générer, c'est de réutiliser/adapter.** Tout LLM sait générer une séquence ; peu savent dire "reprends ma séquence de l'an dernier et adapte-la au nouveau programme / à une 4ᵉ au lieu d'une 3ᵉ". Investir sur le **versioning** et la fonction "transposer".

**2. Plan de cours / révision depuis référentiel**

> 💡 **Les LLM connaissent mal les programmes officiels français.** Indexation maison (RAG) sur BO, socle commun, référentiels BTS / Bac Pro / LMD = le vrai moat. Sans ça, on est un wrapper ChatGPT.

**3. Correction d'exercice pédagogique + fiches d'aide**
Pas la bonne réponse seule : **le raisonnement explicité**, à niveaux de détail variables (élève en difficulté / élève rapide).

> ⚠️ Risque hallucination en maths/sciences → mode **vérification calculatoire** par Python sandbox sur les disciplines à risque numérique. Sinon la crédibilité s'effondre au premier exercice faux distribué en classe.

**4. Recherche & résumé de sources**
RAG sur Éduscol, BO, manuels partenaires, articles vulgarisés.

> ⚠️ **Citations vérifiables obligatoires, jamais inventées.** Une source hallucinée et on perd le prof à vie. La fiabilité prime sur l'exhaustivité.

**5. Fiches de révision multi-format**

> 💡 Sortie naturelle des points 1 à 4 → coût d'implémentation faible une fois le reste en place. Mais soigner les formats : recto, mémo flash, carte mentale, audio.

### 🟢 Prioritaire — gros effet de levier dès qu'on en a les moyens

**6. Visuels vectoriels (Mermaid / SVG / LaTeX TikZ / draw.io)**

> 💡 **Distinction cruciale : pas besoin d'IA générative d'image pour ça.** Générer du Mermaid / SVG / LaTeX depuis un texte → rendu propre, éditable, imprimable. Bien plus utile qu'une image bitmap qu'on ne peut pas retoucher. **C'est ici qu'un LLM brille vraiment.**

**7. Anticipation des erreurs élèves** ⭐
"Voici les 5 conceptions erronées fréquentes sur cette notion + comment les déconstruire."

> 💡 **Énorme valeur didactique, peu de concurrents le proposent.** C'est un levier de réputation auprès des profs expérimentés qui reconnaîtront tout de suite la pertinence pédagogique.

**8. Différenciation automatique en 3 versions** ⭐
À partir d'un même support : version DYS (police OpenDyslexic, interlignage), version FLE/allophones (langage simplifié), version approfondissement.

> 💡 **Répond à une douleur quotidienne.** Un prof gère en moyenne 3 à 5 profils différents dans sa classe ; aujourd'hui il duplique tout à la main.

**9. Mode T1 vs prof expérimenté** ⭐
Le générateur ajuste le niveau de détail : scripts d'oralisation et conseils de gestion de classe pour les jeunes profs, raccourcis pour les titulaires.

> 💡 **Levier d'acquisition fort pour conquérir les T1**, qui sont les plus en demande d'aide et les plus à l'aise avec l'IA.

**10. Newsletter & communication**
Newsletter parents, mot dans le carnet, mail type, compte-rendu de réunion, **rédaction d'appréciations bulletins**.

> 💡 Les appréciations bulletins seules valent l'abonnement annuel pour beaucoup de profs (4 conseils de classe × 30 élèves = 120 appréciations à rédiger × 3 trimestres).

**11. Supports déclencheurs de créativité élève** *(reformulé)*
Amorces d'écriture, situations-problèmes ouvertes, défis disciplinaires, cartes d'inspiration imprimables, canevas BD vierges, sujets de débat.

> 💡 La reformulation "le prof génère le support, l'élève consomme" préserve le cadrage **prof-only et prof maître**.

### 🟡 Secondaire — utile mais ponctuel ou plus risqué

**12. Escape games pédagogiques**

> 💡 **Usage réel : 1-2 fois par trimestre.** Mais énorme effet "wow" en démo commerciale → utile pour l'**acquisition** même si l'usage récurrent est faible.

**13. Images illustratives génératives** (cadrées)

> ⚠️ **Uniquement pour l'illustratif décoratif.** Les modèles génératifs sont mauvais sur : formules math, schémas techniques précis (circuits, anatomie), cartes géographiques exactes, texte intégré. Si le prof veut un schéma scientifique → renvoyer vers le point 6 (vectoriel).

**14. Variantes graphiques d'un même contenu** ⭐
Habillage sobre / BD / manga / rétro / scientifique selon la classe.

> 💡 **L'acte créatif d'appropriation par le prof** : il personnalise avant de distribuer. Renforce le sentiment de maîtrise — exactement le positionnement "prof maître". Très bon ratio valeur / coût technique.

### 🟡 Plus tard — bonne valeur mais lourd techniquement

**15. Script vidéo adapté au rythme du prof**

> 💡 Idée intéressante : le prof enregistre 30 sec de sa voix → l'IA analyse son rythme/registre et adapte ses scripts à son style. Faisable, différenciant, mais usage moins fréquent.

**16. Capsules animées (slides + voix off TTS)**

> ⚠️ **Niveau d'ambition à calibrer.** Diaporama animé + TTS + musique libre = 80% de la valeur perçue pour 20% du coût (style Powtoon/Lumen5). Animation narrative synchronisée vraie = 5× plus cher pour 10% de valeur en plus. **Commencer par le niveau 1.**

### ❌ À ne pas faire (ou très tard)

**17. Vidéo full-IA depuis texte**

> ⚠️ **Pas mature en 2026.** Sora/Veo/Runway : visuel bluffant mais incohérence narrative au-delà de 10 sec, hallucinations visuelles (mains, texte, anatomie), coût élevé, latence longue. À garder en R&D, pas en feature commerciale.

**18. Simulations & expériences virtuelles**

> ⚠️ **Sort du cadre LLM.** C'est un produit à part entière (style PhET, Algodoo, GeoGebra), pas une feature parmi d'autres. Si on veut y aller un jour, c'est une roadmap séparée avec une équipe dédiée.

**19. Avatar animé d'onboarding**

> ⚠️ **Mauvaise idée pour ce public.** Les profs sont des pros pressés ; un avatar qui parle = friction + effet "gadget IA" qui décrédibilise. Remplacer par tooltips contextuels + 1 vidéo courte par feature.
>
> **Exception** : si l'avatar va dans les **supports élèves** (mascotte de classe personnalisable), alors c'est un atout pédagogique → basculer dans la feature 14 (variantes graphiques).

---

## 4. Principes produit transversaux

- **Export multi-format au cœur du produit** — PDF imprimable, DOCX/ODT modifiable, PPTX éditable, PNG/SVG, lien partageable lecture seule (ENT, Pronote). *Règle d'or : tout ce qui sort doit pouvoir vivre sans l'outil.*
- **Validation humaine avant export** — boutons "modifier", "régénérer cette partie" (partielle, pas tout), "exporter" grisé tant que pas validé une fois.
- **RAG sur référentiels officiels = le vrai moat** — pas l'IA, le RAG.
- **Vérification calculatoire en sciences** — Python sandbox sur les exos à risque numérique.

---

## 5. Conseils stratégiques à retenir

1. **Mieux vaut 5 features excellentes que 15 médiocres.** L'erreur classique d'un projet IA edtech : tout vouloir faire dès le début → 18 mois de dev, budget cramé, produit moyen partout. Être **excellent sur le Cœur** avant de toucher au reste.

2. **Le vrai moat n'est pas l'IA, c'est le RAG sur les référentiels officiels français.** N'importe qui peut wrapper un LLM ; nous garantissons l'alignement programmes officiels avec citations vérifiables. C'est ce qui justifie le prix face à ChatGPT gratuit.

3. **L'export est aussi important que la génération.** Un support qui ne sort pas proprement de l'outil ne sera pas utilisé. Soigner PDF/DOCX/PPTX dès le départ.

4. **L'IA propose, le prof dispose.** Cette posture résout simultanément la responsabilité juridique (hallucinations) **et** l'acceptabilité (un prof n'aime pas être remplacé, mais adore être assisté).

5. **Pas de compte élève = simplicité maximale.** Garder ce cadrage strict, c'est une arme de différenciation face à tous les concurrents qui s'enlisent dans le RGPD scolaire.

6. **Éviter les gadgets IA visibles** (avatar parlant, vidéo full-IA). Public professionnel pressé. Le "wow effect" doit venir de la **pertinence pédagogique**, pas de l'esbroufe technique.

7. **Anticiper la rétention, pas juste l'acquisition.** Versioning des séquences, bibliothèque partagée d'équipe, réutilisation année après année : c'est ce qui transforme un usage ponctuel en abonnement pérenne. Sans ça, le prof essaie une fois et oublie.

8. **Les escape games sont un piège de communication.** Très demandés en démo, peu utilisés en vrai. Bons pour la **vente**, pas pour mesurer la **valeur réelle** du produit. Ne pas se laisser guider par le marketing pour prioriser le produit.

9. **Le "wow" pédagogique le moins cher = l'anticipation des erreurs élèves.** Quasi personne ne le propose, valeur immédiate visible par tout prof expérimenté, faisabilité maximale avec un LLM. **À ne pas oublier.**

10. **La force d'un outil prof, c'est qu'il fait gagner du temps sur les tâches répétitives à faible valeur ajoutée** (appréciations, mails parents, fiches de révision dérivées). Ne pas sous-estimer ces features "ennuyeuses" : elles déclenchent le réabonnement plus que les escape games.
