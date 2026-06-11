# aSchool — Base de données & outillage de visualisation

> **Doc interne (admin).** Jamais visible par les profs. Sert à travailler sur la base
> et à visualiser son schéma en 2D.

---

## La base

- **SQLite**, fichier **`data/aschool.db`** (local + VPS).
- **20 tables**, pivot central **`users.email`** (UNIQUE) : les comptes profs vivent dans `users`,
  presque toutes les autres tables s'y rattachent par une colonne `user_email` (ou `email`).
- L'**admin est externe** (variable d'environnement `ADMIN_EMAIL`) : il n'a pas de ligne dans
  `users`, donc les colonnes `admin_email` / `read_by` / `updated_by` ne sont pas des relations.

---

## Deux outils, complémentaires

| Outil | À quoi il sert | Ce qu'il ne fait pas |
|---|---|---|
| **DB Browser for SQLite** (sqlitebrowser.org, gratuit / open source) | Ouvrir la **vraie base** `data/aschool.db` : voir tables, colonnes, **données**, structure ; lancer du SQL ; éditer. | Aucun diagramme de relations. |
| **dbdiagram.io** | Dessiner le **diagramme relationnel 2D** (tables reliées), propre et **imprimable** (export PDF/PNG). Vue d'ensemble du modèle. | Ne touche pas aux données. |

**En clair :** DB Browser pour *travailler sur la base réelle*, dbdiagram.io pour *voir le modèle*.

---

## Le pont entre les deux

1. Export du SQL de structure (`CREATE TABLE`) depuis DB Browser…
2. …collé dans dbdiagram.io (langage **DBML**), qui en génère le diagramme.

**Raccourci déjà en place :** le schéma réel est **déjà traduit en DBML** dans
**`data/aschool.dbml`** (généré le 11/06/2026 depuis `aschool.db`). Il suffit de :
coller son contenu dans **dbdiagram.io** → **Export → PDF**.

---

## ⚠️ Réserve importante (les relations)

dbdiagram.io (et les outils auto en général) ne tracent les liens entre tables **que si les
`FOREIGN KEY` sont déclarées** dans la base. **Ici, elles ne le sont pas** : les relations sont
**implicites** (`user_email` → `users.email`).

→ Conséquence : un import **brut** du SQL sortirait les tables **sans les liens**.
C'est pourquoi, dans `data/aschool.dbml`, les **9 relations réelles ont été écrites à la main**
(lignes `Ref:`) pour qu'elles apparaissent au diagramme.

---

## Note de modèle (à garder en tête)

`niveau` est une **simple colonne texte libre** (`users`, `activites_sauvegardees`,
`sequences_sauvegardees`) — **pas une entité, pas une relation**. C'est l'incohérence
structurelle repérée sur la liste des niveaux, à repenser.
