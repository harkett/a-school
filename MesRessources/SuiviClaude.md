## Dire à Claude Code
Projet à jour. Fichiers modifiés :

README.md — stack cible, structure projet, règles de dev
ROADMAP.md — décisions du 24/04, règles interface, étapes migration
SchemaUI.md — documentation complète de l'interface validée (composants, couleurs, classes boutons, règles)

On attaque l'adaptation de l'existant à la nouvelle interface.


## 21/04/2026 - 13h Dire à Claude Code - 
Pour reprendre, dis simplement :

"On reprend A-SCHOOL. Backend FastAPI + React validés visuellement. Prochaine étape : tester la génération end-to-end (texte → API → résultat), puis la page de login."

Ce que tu retrouveras au démarrage : .\run.ps1 lance tout, et on attaque les tests + l'auth.

## 21/04/2026 - 19:30 Dire à Claude Code 

## 1 - Test
Tout est en place. Avant de tester, il me faut deux infos :

SMTP_PASSWORD — le mot de passe du compte noreply@afia.fr (à renseigner dans .env)
SMTP_HOST — mail.afia.fr est-il correct, ou c'est un autre serveur (ex: smtp.afia.fr) ?
Une fois le .env complet, tu relances .\run.ps1 et tu testes avec ton email.


### 25/04/2026 Demander à Claude
"Reprends A-SCHOOL — l'auth fonctionne, on continue."

- Menu retractable l'incone si retractation l'icone De l'option qui était au préalable sélectionné Disparaît (remplacé par un POINT)Et sa bulle d'aide aussi 
- Créer une aide Pro avec aides communes et des options d'aides spécifique par prof
- Compléter la page de l'option A propos
- allimenter l'historique et ajouter un bouton a coté de dicté Depuis l'historique (bulle aide approriée)
- allimenter les mentions legales
- Pour eviter les confusions le bouton Générer l'acivité doit etre grisé tant que tous les champs ne sont renseignés


### 25/04/2026 - 158:14 Dire à Claude Code
"On reprend A-SCHOOL. Consulte ta mémoire pour le contexte."

# 1-Refonte page Aide (accordéon basique à rendre pro)
# 2- Système de feedback utilisateur (remplace "Signaler un problème")
# 3- Aide spécifique par matière (nécessite d'abord persister subject en BDD)
# 4- Déploiement VPS school.afia.fr
    Déploiement VPS — porter la nouvelle stack FastAPI + React sur school.afia.fr (remplace l'ancien Streamlit). Nginx + PM2 ou Uvicorn en service systemd.
    Ces deux étapes ensemble = la prof de Francais et le prof d'histoiore géo, profs pilotes,  peuvent se connecter et utiliser l'outil depuis n'importe quel navigateur.


### 25/04/2026 - 21:31 Dire à Claude Code
Prochaines étapes disponibles :

Modifier ses identifiants admin depuis le panneau (tu avais validé, pas encore codé)
Système de feedback utilisateur (en attente VPS — c'est fait maintenant)
Aide spécifique par matière (nécessite subject en BDD)
Mot de passe oublié (flow reset_password)

# 5- Mot de passe oublié (flow reset_password)
# 6- L'historique et la base de données viennent après (Phase 3), une fois que le pilote tourne.


### 27/04/2026 - 14:45 Dire à Claude Code
## Priorité de la prochaine session
Commencer par les 3 tâches de visibilité — pas par le few-shot.

Pourquoi ce choix
Le few-shot a besoin que les profs pilotes aient déjà généré 3+ activités du même type pour fonctionner. En ce moment leur historique est encore mince. Si tu codes le few-shot maintenant, il ne sera testable que dans 2 semaines.

Les tâches de visibilité, elles, sont utiles dès la prochaine impression.

Ordre exact pour la prochaine session
# Bloc 1 — ½ journée max (impact immédiat)

1- Pied de page à l'impression — "Généré avec A-SCHOOL — school.afia.fr" — visible sur papier, invisible à l'écran
2- Même pied de page dans les exports .docx
Signature dans les mails envoyés depuis l'app
Ces 3 tâches sont du code simple, chacune 1 à 2 heures. Dès que les profs impriment ou partagent un fichier, l'outil se diffuse tout seul.

# Bloc 2 — dans la même session si le temps le permet

Auth JWT sur /api/generate — c'est un bug sécurité, 30 minutes, et c'est le prérequis obligatoire du few-shot
# Bloc 3 — session suivante

Few-shot adaptation au style du prof — une fois que les profs pilotes ont suffisamment d'historique et que l'auth est en place
En résumé : les tâches rapides et à fort impact de diffusion d'abord, pendant que les profs accumulent l'historique nécessaire au few-shot. Les deux fronts avancent en parallèle sans se bloquer.



Je ne changerais rien à ton architecture. mais je te propse quelques ajustements dans la détection des activités et des matières, pour éviter les bugs de parsing et les clés instables :
Je changerais juste 3 lignes :

✔️ 1. Détection des matières : if line.startswith('# '):
✔️ 2. Détection du début de la section sous‑types : idx = text.lower().find("sous-types")
✔️ 3. Normalisation des activités (optionnel) : current_activite = current_activite.replace(" / ", " - ")
on peut ajouter : current_activite = current_activite.replace(" / ", " - ")
Pour éviter les clés instables.



### 28/04/2026 - 17:00 Dire à Claude Code
La prod est déployée, on est exactement là où on voulait être. La prochaine session, c'est le few-shot — la fonctionnalité qui fait qu'A-SCHOOL s'adapte au style du prof.

3 étapes dans l'ordre, 2-3h de travail :

1. Sécuriser /api/generate (petit bug de sécurité)
Ajouter la lecture du cookie JWT dans backend/routers/generate.py — même pattern que mes_activites.py ligne 24. Sans ça, n'importe qui peut appeler l'API sans être connecté.

2. Requête few-shot en base
Après une génération, chercher les 2 dernières activités du même type pour ce prof dans activites_sauvegardees. Si le prof en a moins de 3 pour ce type → génération normale, rien ne change pour lui.

3. Injection dans le prompt
Dans src/prompts.py, injecter les 2 exemples du prof avant la consigne : "Voici comment ce professeur formule ses exercices… Génère dans le même style."

Après ça : laisser les pilotes générer quelques activités, observer si le style s'adapte, puis préparer les assets de communication (captures d'écran, vidéo 60s) — mais seulement une fois le few-shot validé avec les pilotes.


