# La boucle — procédure de mise en place

**Ouverte le 14/08/2026.** Une amélioration du système existant : au lieu d'appeler **un** fournisseur, le code appelle **une liste** et s'arrête au premier qui répond.

**Règle de déroulé.** Chaque étape est livrable seule, se vérifie seule, et ne casse rien si on s'arrête là. On ne passe à la suivante qu'une fois la précédente vue et validée.

**Les trois fournisseurs** : Groq, Anthropic, Infomaniak — ceux qui sont déjà en base. Aucun à créer.

---

## Étape 1 — la trace des échecs

**Ce qu'on fait.** Trois colonnes sur `usage_llm` :

| colonne | contenu |
|---|---|
| `resultat` | `ok` · `refus` · `coupe` |
| `code_http` | ce que le fournisseur a répondu (429, 500, 402…), vide si l'appel a réussi |
| `rang` | la place du fournisseur dans la liste au moment de la tentative |

Puis on écrit une ligne **aussi quand l'appel échoue** — ce qui n'est fait nulle part aujourd'hui.

**Ce qui ne change pas.** Le système appelle toujours un seul fournisseur. Aucun comportement modifié.

**Ce qu'on voit.** L'écran Journal montre enfin les refus. On sait, avant même d'avoir codé la boucle, ce qui rate et à quelle fréquence.

**Recette.** Provoquer un refus (clé fausse dans un fournisseur de test) et vérifier que la ligne apparaît au Journal avec son code.

---

## Étape 2 — la porte unique

**Ce qu'on fait.** Une fonction unique qui fait exactement ce que les **33 sites d'appel** font aujourd'hui : résoudre le fournisseur et le modèle, puis appeler. Les 33 appelants passent par elle au lieu de résoudre eux-mêmes.

**Ce qui ne change pas.** Rien, absolument rien. Même fournisseur, même modèle, même résultat. C'est un déplacement de code, pas une évolution.

**Pourquoi cette étape existe.** Sans elle, la boucle devrait être écrite 33 fois — et le 34ᵉ outil créé plus tard l'oublierait.

**Recette.** Les tests existants passent sans modification. C'est le seul critère.

---

## Étape 3 — la boucle

**Ce qu'on fait.** Dans cette fonction unique, remplacer « le fournisseur » par « la liste des fournisseurs actifs, dans l'ordre » :

```
pour chaque fournisseur de la liste, dans l'ordre :
    essayer d'appeler
    s'il répond          -> on rend la réponse, c'est fini
    s'il refuse          -> on écrit la ligne, on passe au suivant
tous ont refusé          -> on rend l'échec au professeur, comme aujourd'hui
```

**Ce qui déclenche le passage au suivant** — tout ce qui vient du fournisseur :

- `429` quota atteint
- `500 / 502 / 503 / 529` panne ou saturation
- `401 / 403` clé refusée
- `402` solde vide
- absence de réponse dans le délai
- réponse **coupée** — inutilisable, et le suivant écrit peut-être plus long
- prompt **trop gros pour ce modèle** — le suivant a peut-être une fenêtre plus large

**Ce qui arrête la boucle immédiatement** — tout ce qui vient de notre demande, parce que le suivant répondra la même chose :

- contenu refusé par la modération
- demande mal formée de notre côté

> **Le piège à ne pas rater.** « Prompt trop gros » et « demande mal formée » arrivent avec **le même code, 400**. Le code HTTP seul ne les sépare pas : il faut lire le message. Le moteur le fait déjà (`_traduire_echec_fournisseur` reconnaît « inputs tokens + max_tokens = … but must »), il ne reste qu'à s'en servir pour trancher.

**Recette.** Casser volontairement la clé du premier fournisseur : la génération doit aboutir quand même, et le Journal montrer deux lignes — un refus au rang 1, un succès au rang 2.

---

## Étape 4 — couper les re-tentatives d'Anthropic

**Ce qu'on fait.** Le SDK Anthropic réessaie **deux fois tout seul** avant de rendre la main (`generator.py:310` le dit déjà). Avec la boucle, c'est du temps perdu : on veut passer au suivant tout de suite. Mettre `max_retries` à zéro.

**Recette.** Un refus d'Anthropic doit rendre la main en une fois, pas en trois.

---

## Ce qu'on ne fait pas

Aucun compteur de quota. Aucune lecture d'en-têtes. Aucune table de capacités. Aucun système parallèle à côté de l'existant.

---

## Le modèle, à chaque rang

**Chaque fournisseur a son modèle recommandé, en base.** La boucle appelle Anthropic avec le modèle recommandé d'Anthropic, Infomaniak avec celui d'Infomaniak. Rien à décider, rien à écrire : `ai_modeles.recommande` porte déjà l'information pour les trois, et `admin.py:1195-1198` sait déjà le lire.
