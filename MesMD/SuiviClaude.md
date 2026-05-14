## Dire à Claude Code
# ** A chaque nouvelle session, il est impératif de faire lire à Claude les documents suivants avant toute autre action :

Session du [date]
Objectif : L5 — Analyseur de consignes
En attente de cascade : rien

# ** A chaque fermeture de  session, il est impératif de faire lire à Claude les documents suivants avant toute autre action :

Et surtout ne rien coder avant d'avoir lu ces 4 fichiers.


## Dans cette cession :
# PROF_PILOTE/Recrute_Prof_Pilote.md — pour reprendre les canaux Discord, LinkedIn, INSPÉ, Café Pédagogique, DANE
FeedBack Capture d'écran , joindre un document chaque profs peut afficher les feedbacks qu'i à envoyer pour surtout voir l'etat



# [ ] FB2 — Email admin → prof | Facile | 2h
Bouton “Contacter” dans AdminFeedbacks. 3 templates : Traité / Demande de précision / Remerciement. Admin peut modifier le corps avant envoi. Endpoint POST /api/admin/feedbacks/{id}/email. Trace en BDD : email_sent_at + email_type.


# L5, L6 — Leviers pédagogiques (L5= Consigne, L=6Équité)
Voici l'état exact :
Levier	Statut	Complexité
L5 — Analyseur de consignes	⬜ Stub "en cours de développement"	Facile · 1 session
L6 — Détecteur d'équité	⬜ Stub "en cours de développement"	Facile · 1 session

# Session dette technique — alignement noms, code mort, documentation



Lis CLAUDE.md en premier. Nous venons de terminer une session de nettoyage documentaire complète (suppression de ~14 fichiers .md obsolètes, fusions dans CLAUDE.md).

L'objectif de cette session est un nettoyage technique du code : code mort, fichiers inutilisés, imports orphelins, variables non utilisées, commentaires obsolètes, doublons.

Commence par un audit complet avant de toucher quoi que ce soit :

Backend — fichiers Python inutilisés, routes mortes, imports orphelins, variables non utilisées
Frontend — composants jamais importés, imports inutilisés, fichiers CSS/assets orphelins
Fichiers .env — vérifier que toutes les variables déclarées sont réellement utilisées dans le code
Racine du projet — fichiers de config, scripts, fichiers temporaires qui n'ont plus de raison d'être
Règle absolue : proposer → valider → supprimer. Ne rien supprimer sans validation explicite. Présenter l'audit d'abord, on décide ensemble.
