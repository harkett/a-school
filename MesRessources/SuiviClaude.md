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


