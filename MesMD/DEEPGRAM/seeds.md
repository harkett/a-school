# Seeds STT — Phase 1.2

> Données à insérer en BDD lors du seed initial.  
> Référencé par la procédure Phase 1.2 (migration BDD).

---

## 1. Messages neutres — table `stt_messages`

4 entrées, toutes en mode `neutral` (Phase 1).  
Les versions `volume` sont à insérer aussi en seed mais inactives (le mode actif est défini par `STT_MESSAGE_MODE=neutral` dans `.env`).

### 1.1 Mode `neutral` — Phase 1 (5-20 profs pilotes)

| `mode` | `code` | `content` |
|---|---|---|
| `neutral` | `preventive` | Information : le service de dictée vocale fera l'objet d'une intervention technique dans les prochains jours et pourrait être temporairement indisponible. Vous pouvez continuer à utiliser toutes les fonctionnalités normalement et saisir vos textes au clavier en attendant. Merci de votre compréhension. |
| `neutral` | `unavailable` | La dictée vocale est momentanément indisponible pour intervention technique. Vous pouvez continuer à préparer vos contenus en saisissant vos textes directement au clavier — toutes les autres fonctionnalités restent pleinement opérationnelles. Le service sera rétabli rapidement. Merci de votre compréhension. |
| `neutral` | `saturation` | La dictée vocale est temporairement saturée. Veuillez patienter quelques instants et réessayer dans un moment, ou saisissez votre texte au clavier. Toutes les autres fonctionnalités restent disponibles. |
| `neutral` | `session_expired` | Votre session de dictée a été interrompue après plusieurs minutes d'inactivité. Le texte déjà transcrit est conservé. Vous pouvez relancer une nouvelle dictée à tout moment. |

### 1.2 Mode `volume` — Phase 2+ (>100 profs actifs, en réserve)

| `mode` | `code` | `content` |
|---|---|---|
| `volume` | `preventive` | Information : la dictée vocale rencontre actuellement une forte affluence en raison du grand nombre d'enseignants qui l'utilisent simultanément sur la plateforme. Le service pourrait être temporairement indisponible dans les prochains jours, le temps que nos équipes techniques augmentent la capacité d'accueil. Vous pouvez continuer à utiliser toutes les fonctionnalités normalement et saisir vos textes au clavier en attendant. Merci de votre patience et bonne continuation dans vos préparations. |
| `volume` | `unavailable` | La dictée vocale est momentanément indisponible en raison du grand nombre d'enseignants connectés actuellement sur la plateforme. Nos équipes techniques travaillent à augmenter la capacité pour que chacun puisse en profiter pleinement. En attendant, vous pouvez continuer à préparer vos contenus en saisissant vos textes directement au clavier — toutes les autres fonctionnalités restent pleinement opérationnelles. Le service de dictée sera rétabli rapidement. Merci de votre compréhension. |
| `volume` | `saturation` | La dictée vocale est très sollicitée en ce moment par les nombreux enseignants connectés. Veuillez patienter quelques instants et réessayer dans une minute, ou saisissez votre texte directement au clavier. Toutes les autres fonctionnalités restent disponibles. Merci de votre compréhension. |
| `volume` | `session_expired` | Votre session de dictée a été interrompue après plusieurs minutes d'inactivité. Le texte déjà transcrit est conservé. Vous pouvez relancer une nouvelle dictée à tout moment. |

### 1.3 Script Python idempotent (extrait)

```python
SEED_MESSAGES = [
    # Mode neutral
    ("neutral", "preventive",       "Information : le service de dictée vocale..."),
    ("neutral", "unavailable",      "La dictée vocale est momentanément indisponible..."),
    ("neutral", "saturation",       "La dictée vocale est temporairement saturée..."),
    ("neutral", "session_expired",  "Votre session de dictée a été interrompue..."),
    # Mode volume
    ("volume",  "preventive",       "Information : la dictée vocale rencontre..."),
    ("volume",  "unavailable",      "La dictée vocale est momentanément indisponible..."),
    ("volume",  "saturation",       "La dictée vocale est très sollicitée..."),
    ("volume",  "session_expired",  "Votre session de dictée a été interrompue..."),
]

for mode, code, content in SEED_MESSAGES:
    # ON CONFLICT (mode, code) DO UPDATE — idempotent
    db.execute("""
        INSERT INTO stt_messages (mode, code, content)
        VALUES (?, ?, ?)
        ON CONFLICT(mode, code) DO UPDATE SET
            content = excluded.content,
            updated_at = CURRENT_TIMESTAMP
    """, (mode, code, content))
```

---

## 2. Keyterms transversaux — table `stt_keyterms_global`

80 termes universels, à seeder. La table `stt_keyterms_by_subject` reste vide en Phase 1 (préparée pour Phase 2 adaptative).

### 2.1 Liste par catégorie (80 termes)

#### Vocabulaire pédagogique universel (16)
```
exercice, consigne, énoncé, question, réponse,
justifier, démontrer, calculer, expliquer, rédiger,
élève, professeur, leçon, chapitre, contrôle, évaluation
```

#### Mathématiques (16)
```
polynôme, hypoténuse, théorème, équation, dérivée,
intégrale, fraction, numérateur, dénominateur, périmètre,
aire, volume, parallélogramme, isocèle, équilatéral, asymptote
```

#### Sciences — physique-chimie / SVT (16)
```
Lavoisier, Avogadro, Newton, Einstein, Curie, Pasteur, Darwin,
molécule, atome, électron, proton, neutron,
photosynthèse, mitochondrie, ADN, ARN
```

#### Lettres / Philosophie (12)
```
Baudelaire, Hugo, Molière, Rousseau, Voltaire, Camus,
métaphore, allégorie, oxymore, alexandrin, sonnet, dialectique
```

#### Histoire-Géographie (10)
```
Charlemagne, Napoléon, Robespierre, Clemenceau, de Gaulle,
Renaissance, Révolution, Industrialisation, Mondialisation, décolonisation
```

#### Arts / EPS / Langues / Technique (10)
```
Picasso, Monet, Vinci, basket-ball, handball,
athlétisme, PISA, QCM, baccalauréat, brevet
```

### 2.2 Liste à plat (pour copier-coller dans le seed)

```
exercice
consigne
énoncé
question
réponse
justifier
démontrer
calculer
expliquer
rédiger
élève
professeur
leçon
chapitre
contrôle
évaluation
polynôme
hypoténuse
théorème
équation
dérivée
intégrale
fraction
numérateur
dénominateur
périmètre
aire
volume
parallélogramme
isocèle
équilatéral
asymptote
Lavoisier
Avogadro
Newton
Einstein
Curie
Pasteur
Darwin
molécule
atome
électron
proton
neutron
photosynthèse
mitochondrie
ADN
ARN
Baudelaire
Hugo
Molière
Rousseau
Voltaire
Camus
métaphore
allégorie
oxymore
alexandrin
sonnet
dialectique
Charlemagne
Napoléon
Robespierre
Clemenceau
de Gaulle
Renaissance
Révolution
Industrialisation
Mondialisation
décolonisation
Picasso
Monet
Vinci
basket-ball
handball
athlétisme
PISA
QCM
baccalauréat
brevet
```

**Total : 80 termes exactement.**

### 2.3 Script Python idempotent (extrait)

```python
SEED_KEYTERMS = [
    "exercice", "consigne", "énoncé", "question", "réponse",
    "justifier", "démontrer", "calculer", "expliquer", "rédiger",
    # ... (80 termes complets)
]

for term in SEED_KEYTERMS:
    db.execute("""
        INSERT INTO stt_keyterms_global (term)
        VALUES (?)
        ON CONFLICT(term) DO NOTHING
    """, (term,))
```

---

## 3. Notes pour le développeur

### 3.1 Idempotence

Les deux seeds doivent être idempotents :
- `stt_messages` : `ON CONFLICT(mode, code) DO UPDATE` pour refresh du contenu si modifié
- `stt_keyterms_global` : `ON CONFLICT(term) DO NOTHING` (on ne touche pas un terme existant)

Le script `backend/seed_stt.py` doit pouvoir être rejoué N fois sans effet de bord.

### 3.2 Évolutions Phase 2

Quand on passera en injection adaptative par matière (§3.3 de la spec) :
- Garder les 80 termes transversaux dans `stt_keyterms_global`
- Remplir `stt_keyterms_by_subject` avec ~20 termes spécifiques par matière (12 matières × 20 = 240 termes)
- Logique provider : 80 transversaux + 20 spécifiques matière = 100 keyterms max envoyés à Deepgram par session

### 3.3 Édition admin V2

En V2 (cf §8.2 spec), l'admin pourra :
- Ajouter / retirer / modifier les keyterms globaux
- Gérer les keyterms par matière
- Éditer les messages (WYSIWYG)
- Basculer le mode `neutral` ↔ `volume`

Pour l'instant, toute modification se fait via rejouage du seed après édition de ce fichier.

---

**Fin du fichier seeds.**
