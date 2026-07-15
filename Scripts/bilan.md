# `bilan.ps1` — Bilan des commits (assisté par Claude Code)

Outil pour **faire le point sur ce qu'il y a à committer**, puis — sur demande —
**créer les commits** regroupés par thème. L'intelligence du découpage est déléguée
à **Claude Code en mode non-interactif** (`claude -p`), parce qu'un script de chemins
ne sait pas trier par *sens* un working tree où plusieurs chantiers sont mélangés.

Fichier : [`Scripts/bilan.ps1`](./bilan.ps1)

---

## Pourquoi cet outil

Le dépôt est **partagé par 3 sessions de travail** : les changements de plusieurs
chantiers cohabitent dans le working tree. Committer « tout d'un bloc » mélangerait
les sujets. `bilan.ps1` demande à Claude de **lire l'état réel** et de proposer (ou
d'exécuter) un **découpage par thème** : un commit = un sujet.

---

## Les deux modes

| Mode | Commande | Ce que fait Claude | Écrit dans git ? |
|------|----------|--------------------|------------------|
| **PLAN** (défaut) | `.\bilan.ps1` | Lit le working tree et **propose** un plan de commits (fichiers exacts + messages). | ❌ Non — outils git restreints à la **lecture** |
| **EXÉCUTION** | `.\bilan.ps1 -Go` | **Crée** les commits thématiques (`git add` chemins précis + `git commit`), un à la fois. | ✅ `add` + `commit` — **pas** de push |
| **EXÉCUTION + PUSH** | `.\bilan.ps1 -Go -Push` | Idem, puis `git push` à la fin. | ✅ `add` + `commit` + `push` |

> `-Push` seul (sans `-Go`) n'a aucun sens : le script s'arrête avec un message.

---

## Utilisation

```powershell
cd D:\A-SCHOOL\Scripts

.\bilan.ps1              # Bilan (lecture seule) — le point de départ recommandé
.\bilan.ps1 -Go         # Crée les commits par thème (ne pousse pas)
.\bilan.ps1 -Go -Push   # Crée les commits, puis pousse
```

Le script résout tout seul la racine du dépôt (le dossier **parent** de `Scripts/`),
donc les commandes ci-dessus marchent quel que soit le contenu du dépôt.

---

## Comportement attendu de Claude

1. Lit l'état réel : `git status`, `git diff`, `git diff --staged`, et `git log`
   (pour **reprendre le style des messages** du dépôt : `type(scope): sujet`, en français).
2. **Regroupe par thème** — un commit = un seul sujet cohérent.
3. Pour chaque commit : la **liste exacte** des fichiers à stager + le message.
4. Tout changement qu'il ne peut **pas** rattacher avec certitude à un chantier est
   **mis de côté** sous une rubrique « À vérifier / ne pas committer » — jamais commité au hasard.

---

## Sécurité (mode headless = personne ne rattrape à la main)

Deux garde-fous, l'un **mécanique**, l'autre **textuel** :

### 1. Liste blanche d'outils (`--allowedTools`) — le garde-fou dur

Claude ne peut appeler **que** les commandes git autorisées pour le mode courant :

| Commandes git | PLAN | `-Go` | `-Go -Push` |
|---------------|:----:|:-----:|:-----------:|
| `status`, `diff`, `log`, `show`, `branch`, `remote` (lecture) | ✅ | ✅ | ✅ |
| `add`, `commit` | ❌ | ✅ | ✅ |
| `push` | ❌ | ❌ | ✅ |
| `reset`, `clean`, `rm`, `checkout`, … (destructif) | ❌ | ❌ | ❌ |

Conséquence : en mode PLAN, écrire dans git est **physiquement impossible** ; et
`git push` ne peut **jamais** partir sans `-Push` — ce n'est pas qu'une consigne.

### 2. Consignes du prompt — le garde-fou métier

- Jamais `git add -A` ni `git add .` → chemins **précis**, sujet par sujet.
- Jamais un commit fourre-tout.
- **Secrets** : ne jamais stager/committer `.env`, `.env.*`, `*.key`, `*.pem`, tokens,
  mots de passe, identifiants ; respecter `.gitignore` ; un fichier sensible non ignoré
  est mis sous « À vérifier », jamais commité, jamais affiché en clair.
- Jamais de commit vide (`--allow-empty` interdit).

---

## Contrôles d'entrée (avant tout appel)

Le script s'arrête proprement si :

- `-Push` est passé **sans** `-Go` ;
- la racine n'est **pas** un dépôt git (`.git` introuvable) ;
- `git status` **échoue** (on ne prend pas une sortie vide pour « rien à committer ») ;

et sort en succès sans rien faire si le **working tree est propre**.

---

## Prérequis

- **Claude Code CLI** installée. Le script la cherche dans le `PATH`, sinon sous
  `%APPDATA%\Claude\claude-code\<version>\claude.exe` (la version n'est pas figée).
- **git** dans le `PATH`.
- **PowerShell** (Windows).

---

## Détails d'implémentation

- Modèle utilisé : `opus` (`--model opus`).
- Le prompt est envoyé à Claude via **STDIN** (et non en argument) pour éviter que
  la liste variadique `--allowedTools` n'« avale » le texte du prompt.
- Le code de retour de Claude est vérifié en fin de script : un échec (réseau, quota…)
  est signalé et propagé (`exit`), au lieu d'être silencieux.

---

## Limites connues

- Claude voit le **mélange des 3 chantiers**. Il regroupe par thème, mais ne peut pas
  toujours deviner à quel chantier appartient un bout **inachevé** : ces cas partent
  dans « À vérifier / ne pas committer », à toi de trancher.
- En mode `-Go`, les commits sont créés **sans nouvelle confirmation** : c'est le rôle
  du mode PLAN (par défaut) de te laisser vérifier **avant** de lancer `-Go`.
