# A-SCHOOL — Interface PRO (validée 24/04/2026)

> Prototype HTML : `frontend/index.html` — base de la migration React

---

## Structure générale

```
┌─────────────────────────────────────────────────────┐
│  HEADER  [A-SCHOOL | slogan | matière | email | ⎋]  │
├──────────┬──────────────────────────────────────────┤
│          │  ZONE TEXTE SOURCE                       │
│ SIDEBAR  │  textarea + [Fichier] [Dicter]           │
│          │                                          │
│ Accueil  │  PARAMÈTRES                              │
│ Historique│  Activité / Niveau / Précision / Nb     │
│          │  Inclure correction                      │
│          │  [⚡ Générer l'activité]                 │
│ ──────── │                                          │
│ Aide     │  ZONE RÉSULTAT (si généré)               │
│ À propos │  [.txt] [Word] [Fermer]                  │
├──────────┴──────────────────────────────────────────┤
│  FOOTER  slogan centré | A-SCHOOL · mentions | v    │
└─────────────────────────────────────────────────────┘
```

---

## Composants

### HEADER
- Fond bleu `#1F6EEB`
- Logo : **A** (bordeaux `#A63045`) **-SCHOOL** (blanc)
- Slogan : "| Générateur d'activités pédagogiques" (blanc, opacité 65%)
- Navbar connecté : matière (bordeaux) | email (blanc discret) | [Se déconnecter]

### SIDEBAR
- Largeur 180px, rétractable (toggle hamburger avec chevron directionnel)
- Items haut : Accueil (actif bordeaux), Historique
- Items bas (séparateur) : Aide, À propos
- Chaque item : icône SVG + texte + bulle d'aide

### ZONE TEXTE SOURCE
- Textarea 8 lignes — placeholder liste les 3 modes de saisie
- Boutons `btn-action` (gris visible) : [Fichier .txt / scan JPG] [Dicter]

### PARAMÈTRES
- Activité (dropdown — labels exacts de `prompts.py`)
- Niveau (6e → Terminale + Supérieur)
- Précision / sous-type (conditionnel selon activité)
- Nombre de questions (conditionnel selon activité)
- Case "Inclure une proposition de correction" + texte d'aide
- Bouton primaire : [⚡ Générer l'activité]

### ZONE RÉSULTAT
- Bordure gauche bordeaux
- Boutons : [Télécharger .txt] [Télécharger Word] [Fermer]

### FOOTER
- Slogan centré italique : *"Plus le monde s'ouvre, plus nous avons besoin de proximité..."*
- Ligne infos : A-SCHOOL · Mentions légales (gauche) | version · contact (droite)

---

## Couleurs

| Rôle | Valeur |
|------|--------|
| Bordeaux (accent) | `#A63045` |
| Bordeaux foncé (hover) | `#832538` |
| Bleu primaire | `#1F6EEB` |
| Bleu foncé (hover) | `#1558C0` |

## Classes boutons (règle projet)

| Classe | Usage | Style |
|--------|-------|-------|
| `btn-primary` | Générer | Bleu, blanc, icône+texte |
| `btn-action` | Fichier, Dicter | Gris `#E5E7EB`, bordure, icône+texte |
| `btn-secondary` | Télécharger, Fermer | Blanc, bordure, icône+texte |

**Règle absolue :** tout bouton = icône SVG + texte + attribut `title=`

---

## Règles interface

- Pas de "IA" — utiliser "A-SCHOOL"
- Pas d'emojis
- Matière : définie à la connexion, affichée dans la navbar, pas dans le formulaire
- Selectbox : pas de saisie libre (dropdown uniquement)
