# Générateur d'activités pédagogiques

Outil CLI pour générer des activités de français (collège/lycée) par IA.

## Installation

```bash
cd d:\A-SCHOOL
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Copier `.env.example` en `.env` et coller ta clé API :

```bash
copy .env.example .env
```

Puis éditer `.env` :

```
AI_PROVIDER=gemini
AI_API_KEY=COLLE_TA_CLE_ICI
AI_MODEL=gemini-1.5-flash
```

## Utilisation

### Questions de compréhension
```bash
python -m src.main comprehension --texte monfichier.txt --niveau 4e --nb-questions 10
```

### Pistes de lecture
```bash
python -m src.main pistes --texte monfichier.txt --niveau 4e --nb-pistes 3 --angle thématique
```

### Exercice de réécriture
```bash
python -m src.main reecriture --texte monfichier.txt --niveau 4e --transformation "direct vers indirect"
```

## Passer à l'API Anthropic (Claude)

Dans `.env`, changer simplement :
```
AI_PROVIDER=anthropic
AI_API_KEY=ta_clé_anthropic
AI_MODEL=claude-sonnet-4-6
```
