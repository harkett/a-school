# Liste de priorités — Fonctionnalités futures A-SCHOOL

> **Bannière "Bientôt disponible" dans la sidebar prof** : la liste affichée aux profs est dans `frontend/src/components/Sidebar.jsx`, bloc `{!collapsed && ...}` en bas du fichier. Mettre à jour manuellement quand les fonctionnalités évoluent.

## Niveau 0 — Quick Wins (à réaliser avant les premiers pilotes)

Ces fonctionnalités nécessitent peu d'efforts et peuvent générer du bouche-à-oreille dès le premier export.

| #  | Fonctionnalité                                                   | Effort | Pourquoi maintenant                                                                          |
|----|------------------------------------------------------------------|--------|---------------------------------------------------------------------------------------------|
| 1  | Pied de page dans les exports .docx "Activité générée avec A-SCHOOL — school.afia.fr" | 2h     | Chaque document distribué à des élèves ou collègues représente une publicité gratuite. La spécification est dans PLAN_LANCEMENT. |
| 2  | Pied de page à l'impression (CSS @media print)                  | 1h     | Même effet. La feuille imprimée distribuée en classe expose l'outil.                      |
| 3  | Signature dans le mailto:                                        | 30min  | Le collègue qui reçoit l'activité voit d'où elle provient.                                |
| 4  | Compteur "X activités créées" (Mes activités)                   | 3h     | SQL COUNT + affichage React. Favorise la rétention et la fierté. Un prof avec 50 activités sauvegardées ne repart pas. |
| 5  | Page `/contact` (formulaire ou adresse cliquable)               | 2h     | Les footers affichent actuellement `contact@aschool.fr` en texte brut. Une page dédiée évite d'exposer l'adresse dans le HTML, réduit le spam, et centralise le point de contact. |
| 6  | Civilité (M. / Mme) dans le profil et l'en-tête                 | 2h     | Demande d'ajouter un champ `civilite` en BDD (User), dans le formulaire d'inscription, la page Mon profil, et l'en-tête de l'app. Actuellement l'en-tête affiche "Prénom Nom" sans civilité. |

---

## Niveau 1 — Court Terme (1 à 3 jours, pendant la phase pilote)

| #  | Fonctionnalité                                                   | Effort | Pourquoi                                                                                     |
|----|------------------------------------------------------------------|--------|---------------------------------------------------------------------------------------------|
| 5  | Séquence onboarding email J+2 / J+7 / J+14                      | 2-3 jours | APScheduler est déjà installé. Ajouter des jobs a un impact direct sur la rétention. Le J+0 (welcome) existe déjà. |
| 6  | Bouton "Partagez avec vos collègues"                             | 1-2 jours | 1 route FastAPI + 1 composant React. La spécification est déjà écrite dans DECISIONS_TECHNIQUES.md. Levier d'acquisition par chaîne. |
| 7  | Analyse IA des notations (Groq)                                 | 1 jour | Groq est intégré, les notations sont en BDD. Un prompt + un bloc dans AdminFeedbacks. Utile dès 15-20 retours. |

---

## Niveau 2 — Moyen Terme (1 à 2 semaines, Phase 2 juin 2026)

| #  | Fonctionnalité                                                   | Effort   | Pourquoi                                                                                     |
|----|------------------------------------------------------------------|----------|---------------------------------------------------------------------------------------------|
| 8  | ~~Export PDF~~                                                  | ✅ Livré  | Impression via `window.print()` dans ZoneResultat.jsx — le navigateur propose "Enregistrer en PDF". |
| 9  | Aide spécifique par matière                                      | 3-5 jours | Infrastructure prête (subject en BDD). Textes d'aide adaptés à la matière du prof. Pas de backend à créer, juste de la logique React + contenu. |
| 10 | Support niveau Supérieur (activités BTS/prépa/licence)         | 1-2 semaines | Travail de prompts et d'activités. Ouvre un nouveau segment (formateurs, BTS...). |

---

## Niveau 3 — Long Terme (2 à 4 semaines, Phase 3)

| #  | Fonctionnalité                                                   | Effort   | Remarque                                                                                     |
|----|------------------------------------------------------------------|----------|---------------------------------------------------------------------------------------------|
| 11 | Application mobile (PWA)                                        | 2-4 semaines | Voir analyse détaillée ci-dessous.                                                          |
| 12 | Google OAuth                                                    | 2-3 semaines | Réduit la friction d'inscription, mais crée une dépendance Google. À faire après validation des pilotes. |
| 13 | Partage d'activités entre collègues                              | 3-4 semaines | Nécessite un modèle de partage, une page de découverte, et des règles de visibilité. À concevoir avec les retours pilotes. |

---

## Niveau 4 — Hors Scope Actuel (à ne pas toucher)

| #  | Fonctionnalité                                                   | Pourquoi attendre                                                                      |
|----|------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| 14 | Intégration ENT (Pronote)                                       | API propriétaires, accords institutionnels, homologations. Des mois de travail, blocages hors de ton contrôle. |
| 15 | Tableau de bord multi-profs établissement                        | Nécessite un concept "établissement" en BDD + rôles (directeur/prof). Phase 4 minimum. |
| 16 | Migration SQLite → PostgreSQL                                    | Uniquement si charge réelle. SQLite tient largement jusqu'à 500 utilisateurs actifs quotidiens. Ne pas migrer par anticipation. |

---

## Sur la question du mobile

La PWA est la bonne approche : pas d'app native, pas de Play Store/App Store, pas de revue Apple/Google, et pas de 30% de commission. L'app s'installe depuis le navigateur, et le code React existant est réutilisé.

### Ce que ça demande :
- `manifest.json + icônes` → 2-3h
- `Service worker basique` → 1 jour
- `Interface responsive mobile` → c'est le gros morceau (2-3 semaines si l'UI actuelle n'est pas mobile-first — sidebar, formulaires, zone résultat, tout à revoir pour petit écran)
- `Tests iOS + Android` → 2-3 jours

### Conseil sur le timing :
Attendre le retour des pilotes avant de commencer le mobile. Les profs préparent leurs cours sur leur ordinateur, pas sur leur téléphone. Le mobile sera un usage secondaire. Commencer par les Niveaux 0 et 1, collecter des retours, et si les pilotes demandent le mobile, prioriser la PWA en Phase 2.

---

## Ordre logique pour "finir" le projet :

1. Niveau 0 (4 items, 1 journée)
2. Onboarding emails + Partager + Analyse notations
3. Export PDF
4. PWA mobile
5. Google OAuth
6. Partage entre collègues