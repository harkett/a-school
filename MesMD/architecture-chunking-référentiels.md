# L'architecture du chunking des référentiels

Cette note explique comment aSchool transforme un référentiel officiel (un PDF) en extraits — les *chunks* — exploitables par la recherche augmentée (le RAG). Elle vaut pour tous les référentiels, présents et à venir.

## La règle d'entrée : une extraction propre avant tout découpage

Avant de découper un PDF en chunks, on en produit d'abord une extraction propre. Sans exception, quel que soit le référentiel.

Un PDF mal extrait donne des chunks mélangés : colonnes entremêlées, en-têtes de page répétés au milieu du texte, encarts injectés en plein milieu des phrases. Un RAG construit sur ce texte est de mauvaise qualité. On ne découpe donc jamais sur une extraction sale.

## L'architecture : un moteur commun, une procédure par référentiel

Le système repose sur deux briques.

- **Un moteur générique** qui ne connaît aucun référentiel en particulier : `backend/rag/chunker.py`. On n'y touche jamais quand on ajoute un référentiel.
- **Une procédure propre à chaque référentiel**, appelée une « fiche ». Exemple : `backend/rag/referentiels/bts_ciel_option_a.py`. La fiche porte tout ce qui est spécifique à ce référentiel : où lire le PDF, comment l'extraire proprement, comment le découper, comment étiqueter les chunks.

Ajouter un nouveau référentiel revient à écrire une nouvelle fiche, sans modifier le moteur.

## La règle de réutilisation : même forme, même procédure

Deux référentiels qui se ressemblent partagent la même procédure. Quand un référentiel a une forme inédite, il reçoit sa propre procédure. Exemples :

- **BTS option B** : c'est le même PDF que l'option A. Il utilise donc la même fiche, qui gère déjà la distinction option A / option B et étiquette les chunks en conséquence. Rien à réécrire.
- **Crèche Bébés, Moyens et Grands** : c'est le même document 0-3 ans pour les trois. Une seule procédure crèche suffit, et les trois couples pointent dessus.
- **Collège** : un programme scolaire est une forme différente. Il demandera une nouvelle fiche.

## L'extraction fait partie de la procédure, pas seulement la découpe

Au départ, seule la découpe était propre à chaque fiche ; l'extraction du PDF restait commune et sommaire (`backend/rag/pgvector_store.py`). Le cas de la crèche a montré la limite : son PDF est en plusieurs colonnes, et une extraction qui lit en travers mélange les phrases.

La conclusion : l'extraction aussi doit vivre dans la fiche. Chaque PDF peut exiger sa propre façon d'être lu — un document sur plusieurs colonnes ne se lit pas comme un document sur une seule colonne. La règle « une procédure par référentiel » vaut donc autant pour l'extraction que pour la découpe.

## La qualité prime, la vitesse est secondaire

L'extraction et le découpage sont un geste d'administration, réalisé une seule fois, hors ligne. Qu'il prenne une minute ou dix n'a aucune importance : il suffit d'en informer l'administrateur. La seule exigence est la qualité du résultat.

## Les méthodes d'extraction déjà écrites

- **Crèche (document 0-3 ans, mise en page magazine multi-colonnes).** La méthode coupe chaque double-page en deux pages imprimées, sépare leurs colonnes, garde entières les lignes pleine largeur (titres, encadrés « À retenir »), retire le mobilier répété (en-têtes, numéros de page, encart « Ce référentiel est le vôtre… ») et recolle les mots coupés en fin de ligne. Elle sert les trois couples Bébés, Moyens et Grands, qui partagent le même document.

---

*Note née le 04/07/2026, à partir du cas crèche : un PDF en colonnes dont l'extraction naïve mélangeait les phrases.*
