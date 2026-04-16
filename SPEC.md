# Spécification fonctionnelle et technique  
## Outil Python sous VS Code pour générer des activités de français (IA)

---

## 1. Objectif général

**But :**  
Permettre à un professeur de français (niveau collège, par ex. 4ᵉ) de générer en quelques minutes un ensemble d’activités pédagogiques à partir d’un texte littéraire (ex. *Les Misérables*, séquence sur la nouvelle réaliste), en s’appuyant sur une IA.

**Résultat attendu :**

- **Entrée :**  
  - Un texte (copié-collé ou fichier)  
  - Quelques paramètres (niveau, type d’activités, nombre de questions, etc.)
- **Sortie :**  
  - Un ensemble d’activités générées (questions de compréhension, pistes de lecture, exercices de réécriture, etc.)  
  - Exportable (Markdown, texte brut, éventuellement .docx plus tard)

---

## 2. Cas d’usage / User stories

1. **US1 – Questions de compréhension**
   - **En tant que** professeur de français de 4ᵉ  
   - **Je veux** obtenir 10 questions de compréhension sur un extrait des *Misérables*  
   - **Afin de** gagner du temps dans la préparation de ma séquence.

2. **US2 – Pistes de lecture / pistes de départ**
   - **En tant que** professeur  
   - **Je veux** obtenir 3 pistes de lecture / axes de réflexion sur un texte réaliste  
   - **Afin de** structurer rapidement mon cours et mes échanges oraux avec la classe.

3. **US3 – Exercice de réécriture (style indirect, etc.)**
   - **En tant que** professeur  
   - **Je veux** générer un exercice de réécriture (par ex. transformer un passage du style direct au style indirect)  
   - **Afin de** proposer un entraînement ciblé sur une compétence grammaticale.

4. **US4 – Personnalisation rapide**
   - **En tant que** professeur  
   - **Je veux** récupérer les activités dans un format simple (Markdown / texte)  
   - **Afin de** les modifier facilement avant impression ou mise en ligne.

5. **US5 – Simplicité d’usage**
   - **En tant que** utilisateur non technique  
   - **Je veux** lancer l’outil via une commande simple ou une interface minimale  
   - **Afin de** ne pas avoir à manipuler du code.

---

## 3. Environnement et technologies

- **Langage :** Python 3.11+  
- **IDE cible :** Visual Studio Code  
- **Gestion d’environnement :**  
  - `venv` ou `uv` / `poetry` (à choisir, mais prévoir dans la spec)  
- **Dépendances principales :**
  - Client API IA (par ex. OpenAI, Azure OpenAI, ou autre fournisseur compatible)  
  - `python-dotenv` pour gérer les clés API via `.env`  
- **Format de sortie :**
  - Markdown (`.md`) par défaut  
  - Texte brut (`.txt`) possible  
- **Interface :**
  - Phase 1 : CLI (ligne de commande)  
  - Phase 2 (optionnelle) : petite interface locale (ex. `typer`/`rich` ou mini GUI plus tard)

---

## 4. Fonctionnalités détaillées

### 4.1. Types d’activités supportés (v1)

1. **Questions de compréhension**
   - Paramètres :
     - **Nombre de questions** (par défaut : 10)
     - **Niveau** (ex. 5ᵉ, 4ᵉ, 3ᵉ)
     - **Type de questions** (ouvertes, QCM, mélange)
   - Sortie :
     - Liste numérotée de questions
     - Option : propositions de corrigé (v1.1 ou v2)

2. **Pistes de lecture / pistes de départ**
   - Paramètres :
     - **Nombre de pistes** (par défaut : 3)
     - **Angle** (thématique, stylistique, narratif, personnages, etc.)
   - Sortie :
     - 3 à 5 axes de réflexion, formulés clairement pour un usage en classe.

3. **Exercice de réécriture**
   - Paramètres :
     - **Type de transformation** (ex. direct → indirect, passé simple → présent, changement de focalisation, etc.)
     - **Consigne** (niveau de détail)
   - Sortie :
     - Consigne claire pour l’élève
     - Passage à transformer (repris du texte ou généré à partir de celui-ci)
     - Option : exemple de correction (v1.1 ou v2)

---

## 5. Architecture logique

### 5.1. Structure de projet (proposition)

```text
projet-activites-francais-ia/
├─ src/
│  ├─ main.py                # Point d’entrée CLI
│  ├─ config.py              # Gestion config (API key, modèle, etc.)
│  ├─ prompts.py             # Templates de prompts IA
│  ├─ generator.py           # Logique de génération (appel IA)
│  ├─ formats.py             # Mise en forme des sorties (Markdown, texte)
│  └─ cli.py                 # Interface ligne de commande (Typer/argparse)
├─ tests/
│  ├─ test_prompts.py
│  ├─ test_generator.py
│  └─ test_formats.py
├─ .env.example
├─ requirements.txt (ou pyproject.toml)
├─ README.md
└─ LICENSE (optionnel)
