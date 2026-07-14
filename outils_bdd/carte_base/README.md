# Carte visuelle de la base

Un seul but : **voir la base d'un coup d'œil** — toutes les tables, leurs colonnes,
et les relations qui les relient. La carte se régénère **sur l'état réel de la
base**, jamais sur une supposition.

| Fichier | Rôle |
|---|---|
| `carte.py` (ici) | **Outil** : lit la structure réelle (`information_schema`) → régénère le HTML → l'ouvre dans Edge. Aucune donnée en dur. |
| `..\..\carte.ps1` (racine) | **Lanceur** : appelle `carte.py` avec le venv du projet. Vit à la racine du dépôt (`D:\A-SCHOOL\carte.ps1`). |
| `vendor/mermaid.min.js` | **Moteur de dessin** embarqué (Mermaid). Inclus dans le HTML → les schémas se dessinent **hors ligne**, sans CDN ni claude.ai. Versionné. |
| `carte_base.html` | **Sortie** : la carte régénérée (~3,3 Mo, moteur inclus). Fichier produit, **ignoré de git** (on le régénère, on ne le versionne pas). |

## Usage (depuis la racine du dépôt, venv actif)

```powershell
.\carte.ps1                                       # régénère + ouvre Edge

# ou directement en Python :
python outils_bdd\carte_base\carte.py            # régénère + ouvre Edge
python outils_bdd\carte_base\carte.py --no-open  # régénère seulement (pas d'ouverture)
```

Le script lit `DATABASE_URL` dans le `.env` (comme l'application) : il lit la base
pointée par ce fichier. **Il ne lit que la structure et le nombre de lignes — aucune
donnée métier.**

## Comment la faire évoluer avec le développement

À chaque évolution de la base (nouvelle table, nouvelle colonne, remplissage) :
relancer le script. La carte se **redessine sur l'état exact** de la base au moment
du lancement. C'est une **photo à la demande**, pas un flux temps réel.

Une **nouvelle table** apparaît toujours sur la carte : si elle n'est encore rangée
dans aucun des 5 domaines, elle tombe par défaut dans « système » et elle est
**signalée en pied de page** — jamais un oubli muet. Pour la classer proprement,
ajouter son nom dans le domaine voulu, au dictionnaire `DOMAINS` de `carte.py`.

## Le lien partagé (claude.ai) — à ne pas confondre

Ce script régénère le **fichier HTML local** et l'ouvre dans Edge : c'est autonome,
sans dépendance.

Le **lien claude.ai** (la version partagée, envoyable) est une autre chose : il ne
se met à jour que via l'outil de publication de Claude Code, pas par ce script. Pour
le rafraîchir, le demander en session.
