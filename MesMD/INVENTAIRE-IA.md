# Inventaire IA — aSchool

> Où l'IA est utilisée dans aSchool : ce qui l'utilise aujourd'hui, ce qui l'utilisera par la suite.
> Vérifié le 10/07/2026 sur le code réel. Source de vérité = le code (ce document dérive).
>
> **Destiné à l'aide admin.** Ce document alimentera l'aide de l'administrateur (`AdminAide.jsx`, rubrique « Génération LLM ») : au fil de son enrichissement, son contenu sera repris dans l'aide que lit l'admin. Le code reste la source de vérité ; ce document en est le résumé lisible.

## Porte unique

Tout appel au LLM texte passe par **une seule fonction** : `generate()` ([src/generator.py:34](../src/generator.py#L34)).
Fournisseur/modèle par défaut : **Groq / `llama-3.3-70b-versatile`**, administrables en base et basculables à chaud vers **Claude** ([admin.py:49](../backend/systeme/admin.py#L49), [:54](../backend/systeme/admin.py#L54)).

## Ce qui utilise l'IA aujourd'hui

### LLM texte (via `generate()`)

| Fonction | Où |
|---|---|
| Créer une activité | [generate.py:70](../backend/activite/generate.py#L70) |
| Générer une fiche | [fiches.py:306](../backend/contenu/fiches.py#L306) |
| Générer une séquence | [sequence.py:78](../backend/sequence/sequence.py#L78) |
| Optimiseur de séquences | [optimiseur.py:84](../backend/sequence/optimiseur.py#L84) |
| Détecteur d'ambiguïtés (consigne prof) | [ambiguites.py:84](../backend/analyse/ambiguites.py#L84) |
| Analyse de consigne | [consigne.py:86](../backend/analyse/consigne.py#L86) |
| Tester un exemple de référentiel | [exemple_referentiel.py:115](../backend/pedagogie/exemple_referentiel.py#L115) |

Les prompts de ces outils vivent en base, administrables (`get_prompt`, [admin.py:237](../backend/systeme/admin.py#L237)).

### Autres briques IA

| Fonction | Modèle / brique | Où |
|---|---|---|
| Dictée vocale | Groq Whisper `whisper-large-v3` | [groq_client.py:7](../backend/core/groq_client.py#L7) |
| OCR image | Groq vision (`transcribe_image`) | [ocr.py:18](../backend/dictee/ocr.py#L18) |
| Embeddings du RAG | BGE-M3 (1024 dim) | [embeddings.py](../backend/rag/embeddings.py) |

> L'OCR d'un **PDF numérique** est une simple extraction de texte (`pdfplumber`) — pas d'IA, et c'est voulu : le texte est déjà dans le fichier.

## Ce qui utilisera l'IA par la suite

### Préparation d'un référentiel (cible : l'IA propose, l'admin valide)

| Étape | Cible |
|---|---|
| Détection des cas ambigus au découpage | l'IA lit le document, en tire la règle de classement, ne remonte que les vrais doutes (règle « L'ambiguïté se détecte par l'IA » dans `CLAUDE.md` ; chantier TRACKER 67) |
| Règle de découpe | proposée par l'IA (aujourd'hui par le dev) |
| Matières candidates d'un niveau | extraites par l'IA (aujourd'hui par le dev) |

### Futures fonctionnalités (au TRACKER)

Consommateurs RAG : Détecteur d'équité (04), Différenciation DYS / FLE (30), Cohérence curriculaire (25), Appréciations bulletins & parents (31).
Autres : Visuels Mermaid / SVG (32), Mémo flash (33), Supports de créativité (34), Validation du texte source par LLM (27), Bouton « Par IA » — recherche web de la source officielle (64).

> Principe permanent (cap « aSchool n'invente rien ») : chacune de ces fonctions devra naître **avec** l'IA, et l'IA **propose** — l'admin ou le prof **valide**.
