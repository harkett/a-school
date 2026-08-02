# A-SCHOOL — passer d'une machine à l'autre

**Une commande sur chaque poste. Rien d'autre.**

| | |
|---|---|
| sur la machine que vous **quittez** | `.\Scripts\je_pars.ps1` |
| sur la machine où vous **arrivez** | `.\Scripts\j_arrive.ps1` |

Rien à fermer, rien à rouvrir, rien à attendre, rien à glisser dans
l'explorateur. Si un programme doit être fermé, le script le ferme ; s'il doit
être ouvert, le script l'ouvre.

Ci-dessous, le sens portable → fixe. Dans l'autre sens, échangez les deux noms :
le rituel est identique.

---

## La procédure

1. **Sur le portable —** ouvrez une fenêtre PowerShell, placez-vous dans le
   dossier (`cd C:\A-SCHOOL`) et lancez `.\Scripts\je_pars.ps1`.

   Il travaille seul : ouvre le moteur s'il dort, enregistre et envoie votre
   code, ferme VS Code, sort votre base dans `Bagage\`, relève la carte des
   liens du modèle, ferme l'application, puis dépose une valise
   `A-SCHOOL-a-emporter` et relit chaque fichier des deux côtés.

   La **première fois seulement**, il demande où déposer : répondez `\\FIXE\D$`
   (en UNC, jamais une lettre mappée). Ensuite il s'en souvient — Entrée suffit.

   À la moindre anomalie il s'arrête en disant « Rien n'a été modifié ».

2. **Sur le fixe —** ouvrez une fenêtre PowerShell, placez-vous dans le dossier
   (`cd D:\A-SCHOOL`) et lancez `.\Scripts\j_arrive.ps1`.

   Il travaille seul : ouvre le moteur s'il dort, ferme l'application, trouve la
   valise, en sort ce qui ne voyage pas par le code (votre base, les
   référentiels, `.env`, le modèle) en vérifiant chaque fichier, récupère le
   code, compare les dates, installe, redémarre, remet les liens du modèle en
   place, et jette la valise.

   Une seule question, et seulement si elle a lieu d'être : ce poste
   contient-il du travail **plus récent** que ce que vous apportez ? Si oui, il
   s'arrête et réclame le mot `remplacer`. Entrée seule : rien n'est touché.

   Il finit par <http://localhost:5173>.

---

## Les gestes qui restent, et pourquoi

Il en restait six. Il en reste **un, fait deux fois** : ouvrir une fenêtre
PowerShell et lancer la commande, sur chaque poste.

C'est la règle elle-même — « l'utilisateur lance une commande, sur chaque poste,
et rien d'autre » — et il n'y a pas de septième chose à savoir : ni programme à
fermer, ni programme à rouvrir, ni état à surveiller, ni chemin à retaper.

Les cinq autres ont disparu le 02/08/2026, et voici lesquels :

| geste supprimé | comment |
|---|---|
| fermer Docker Desktop sur le fixe | plus nécessaire : la valise est déposée **à côté**, le dossier vivant d'en face n'est plus touché |
| fermer VS Code sur le fixe | même raison |
| confirmer que Docker est bien fermé en face | la question n'a plus d'objet, elle est retirée |
| rouvrir Docker Desktop et attendre le vert | `j_arrive` ouvre le moteur lui-même et attend qu'il réponde |
| retaper « où copier » à chaque bascule | demandé une seule fois, puis retenu (hors du dossier, pour que la réponse ne voyage pas) |

Un piège a disparu avec eux : `je_pars` lancé depuis le terminal intégré de
VS Code se coupait lui-même en fermant VS Code. Il se relance désormais tout
seul dans une fenêtre à part.

---

## Pourquoi une valise, et pas le dossier directement

C'est le changement qui vaut les quatre premiers gestes du tableau.

Le départ écrivait droit dans le dossier `A-SCHOOL` de l'autre poste, et
l'effaçait pour le remplacer. Or à cet instant **rien ne tourne là-bas** pour se
protéger : c'était donc à vous d'y aller à la main fermer l'application, fermer
VS Code, puis revenir les rouvrir. Quatre allers-retours sur une machine à
laquelle vous n'aviez rien à demander, et dont l'oubli faisait échouer la copie
sur un fichier tenu ouvert.

Déposée à côté, la valise ne touche à rien. Le dossier d'en face peut tourner,
être ouvert, être utilisé. C'est `j_arrive`, qui tourne **là-bas**, qui installe
— et un script qui tourne sur une machine sait fermer et rouvrir ses propres
programmes.

**Place disque :** la valise pèse le poids du dossier (6,5 Go, modèle compris),
et coexiste avec le dossier vivant le temps de la bascule. Prévoir 13 Go libres
à l'arrivée. `j_arrive` la jette une fois l'installation vérifiée **et**
l'application redémarrée — pas avant : tant que l'un des deux n'est pas acquis,
elle reste le seul exemplaire complet de ce que vous apportiez.

---

## Ce qui voyage

| | |
|---|---|
| `Bagage\` | la base de données, la date du départ, la carte des liens du modèle |
| `REFERENTIELS\` | les PDF déposés — hors dépôt, irremplaçables |
| `.env` | hors dépôt, identique sur les deux machines |
| `.git` | l'historique. Sans lui, plus de dépôt là-bas, et `j_arrive` s'arrête à 3/6 |
| `docker\hf-cache` | 4,3 Go, le modèle qui lit les référentiels |
| le code | et tout le reste du dossier |

Le modèle **ne se retéléchargera pas de lui-même** : `HF_HUB_OFFLINE=1` est posé
partout — `docker-compose.yml` pour tout ce qui tourne dans la boîte, et
`backend/rag/embeddings.py` pour le reste. Sans ce dossier, l'autre poste ne génère plus rien — ni
activité, ni séance, ni thème, ni idée, ni exemple.

## Ce qui ne voyage pas

Parce que ça se refabrique vraiment sur place :

| | |
|---|---|
| `node_modules` | refait par le conteneur (15 300 fichiers) |
| `docker\pgdata` | un reste : la base vit dans le volume nommé `pgdata_dev` |
| `__pycache__`, `.pytest_cache` | caches de Python |

**`.venv` n'existe plus** — abandonné le 02/08/2026. Un environnement qui ne
survit pas à une bascule et qui exige internet pour renaître n'est pas un outil,
c'est une charge. Le seul Python du projet est celui du conteneur : c'est lui
qui fait tourner l'application, et désormais lui aussi qui lance les tests. Les
65 fichiers de `tests\` portent la même ligne, et elle est vraie sur un poste
fraîchement basculé :

```
docker compose exec backend python -m pytest tests/<le fichier>.py -q
```

Les deux scripts retirent encore un `.venv` s'ils en trouvent un : c'est un
reste, pas quelque chose qui renaîtra.

**La copie ne se fait pas dans l'explorateur Windows** : il emporte les fichiers
inutiles, échoue sur les liens du cache du modèle, et saute `.git` parce qu'il
est caché.

---

## Si un script s'arrête

Il s'arrête plutôt que de deviner, et dit « Rien n'a été modifié » quand c'est
le cas. **Relancer un script interrompu est toujours sans danger.**

Une seule chose n'est jamais faite à votre place : trancher un conflit sur le
code. C'est le seul endroit où du travail peut se perdre pour de bon. Comme vous
ne travaillez jamais sur les deux postes à la fois, le cas ne devrait pas
survenir : `je_pars` envoie tout avant de partir, et `j_arrive` refuse
d'avancer si le poste d'arrivée a gardé du travail à lui. S'il survient quand
même, c'est le signe qu'un départ a été sauté quelque part.

---

## Ailleurs qu'entre ces deux postes

« Où déposer » accepte n'importe quel endroit atteignable des deux machines : un
chemin réseau (`\\FIXE\D$`), une clé USB, un disque externe, un dossier
synchronisé. `j_arrive` cherche la valise tout seul sur les disques du poste.
