# Les démonstrations — comment ça marche

Écrit le 16/08/2026, point par point, chaque point validé avant le suivant.
Destiné à un lecteur humain, pas à un développeur. Servira au bouton « Comment ça marche ».

---

## 1. Ce qu'est une démonstration

C'est une deuxième application aSchool, à sa propre adresse (`demo-college4e.aschool.fr`),
remplie de contenus déjà prêts : des séquences, des séances et des activités, pour qu'un
visiteur voie l'outil en marche sans rien créer.

Ces contenus ne sont pas ceux du professeur — mais ils sont fabriqués à partir du **vrai
référentiel** et de ses unités découpées.

Un professeur qui y entre travaille dans un bac à sable : ce qu'il y fait n'atteint jamais ses
vrais contenus.

Il y en a six, une par niveau : CIEL A, CIEL B, CRSA, Ergothérapie, Crèche, Collège 4e.

## 2. Où vivent ces contenus

Les six démonstrations ne sont pas six applications installées : c'est le même programme qui les
sert toutes.

Ce qui change, c'est la base de données. Le vrai aSchool a la sienne. Les démonstrations en ont
une autre, à côté, découpée en six compartiments étanches — un par démonstration.

C'est l'adresse tapée dans le navigateur qui décide du compartiment servi.

---

## À retirer de l'écran — relevé au fil des tests (16/08/2026)

Constaté par l'administrateur en regardant l'écran, sans code écrit : noté ici, à traiter quand
on reprendra la page point par point.

- **Colonne « Testée »** (`demos.date_dernier_test`). Une date saisie à la main, le jour où l'on
  aurait relu la démonstration. Aucun code ne la lit, elle ne commande rien, et elle n'a jamais
  été remplie de bonne foi : « je n'ai jamais testé cette base ». Elle encombre le tableau.
  Même esprit que les cinq statuts supprimés le même jour — un rituel de validation qui ne
  correspond à aucune pratique réelle.
- **Colonne « Act. / Séq. / Séa. »** (`nb_activites`, `nb_sequences`, `nb_seances`). À RETIRER DE
  L'AFFICHAGE, pas de la base : la donnée reste, elle se consulte en ouvrant « Modifier ». Elle
  n'a rien à faire dans la vue d'ensemble.
- **Colonne « Fabriquée »** (`date_generation`) : GARDÉE. C'est la date de création de la
  démonstration — elle dit de quand date le contenu. Reste à revoir QUI la remplit : aujourd'hui
  elle se saisit à la main, or l'administrateur ne saisit rien à la main.
