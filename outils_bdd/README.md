# Filet de reproductibilité — cycles / niveaux

Deux fichiers, un seul but : **pouvoir reconstruire les tables `cycles` et
`niveaux` sur une base neuve**, à l'identique.

| Fichier | Rôle |
|---|---|
| `cycles_niveaux.json` | **Donnée** : snapshot fidèle des 11 cycles / 88 niveaux (ids figés). Source de vérité committée. |
| `rebuild_cycles_niveaux.py` | **Outil** : capture (base → JSON) et rejoue (JSON → base). Ne porte aucune donnée en dur. |

## Pourquoi ce filet existe

Les cycles et les niveaux sont une **décision humaine** (les 11 cycles, les 88
niveaux avec leurs 17 BTS, 15 Master, etc.), **pas** une donnée extraite d'un
référentiel officiel. Ils ne sont donc **pas** reconstructibles par
ré-ingestion RAG. Le script éphémère qui les avait remplis a été supprimé après
usage (doctrine « script éphémère ») — sans laisser de trace reproductible.
Ce filet répare ça : la donnée vit dans le JSON committé, l'outil sait la rejouer.

## RECONSTRUCTION, PAS CORRECTION

Le mode « rejouer » fait un **insert-si-absent** (par `id`) : il **n'écrase
jamais** une ligne existante.

- Sur une base **vide** → reconstruit fidèlement les 11 cycles / 88 niveaux.
- Sur une base **pleine** → tous les ids existent, tout est sauté, **zéro effet**.

Pour **corriger** une donnée existante (un libellé fautif, par exemple) : ce
n'est **pas** le rôle de cet outil. On passe par l'écran admin, ou par une base
neuve. C'est un choix assumé : l'outil est **inoffensif** dans les deux sens.

## Usage (depuis la racine du dépôt)

```bash
# base -> JSON : rafraîchir le snapshot après un ajout humain d'un cycle/niveau
python outils_bdd/rebuild_cycles_niveaux.py --export

# JSON -> base : rejouer sur une base neuve (idempotent, sans risque, mode par défaut)
python outils_bdd/rebuild_cycles_niveaux.py
```

Le script lit `DATABASE_URL` dans le `.env` (comme l'application) : il agit sur
la base pointée par ce fichier. **Vérifier `.env` avant de rejouer.**

## Détail technique

- Les `id` sont **figés** dans le JSON : d'autres tables (`matiere_niveaux`,
  `referentiels`, profs, chunks) référencent les niveaux par leur `id`. Si les
  ids bougeaient à la reconstruction, ces liens casseraient.
- Après un insert d'ids explicites, le script **recale les séquences**
  d'auto-increment (`cycles_id_seq`, `niveaux_id_seq`) sur `MAX(id)`, sinon le
  prochain insert automatique entrerait en collision.
