# aSchool — Interface PRO

> **Rôle : référence design et interface — à consulter avant de créer ou modifier un composant UI.**
>
> Ce document contient :
> - Le schéma ASCII du layout général (Header / Sidebar / Zone texte / Paramètres / Résultat / Footer)
> - La description détaillée de chaque composant React (Header, Sidebar, Zone texte source, Paramètres, Zone résultat, Footer)
> - Le système de couleurs officiel : bordeaux `#A63045`, bleu `#1F6EEB` et leurs variantes hover
> - Le système de classes boutons (`btn-primary`, `btn-action`, `btn-secondary`) avec leur usage et leur rendu visuel
> - Les règles d'interface absolues du projet
>
> **Règles critiques à ne jamais violer :**
> - Tout bouton = icône SVG + texte + attribut `title=` (tooltip obligatoire)
> - Pas d'emojis dans l'interface
> - Pas de "IA" — utiliser "aSchool"
> - Selectbox uniquement (pas de saisie libre)
> - La matière est définie à la connexion, affichée dans la navbar — pas dans le formulaire
>
> **Interface React opérationnelle depuis 24/04/2026.**
> **Vérifié le : 30/04/2026 — À mettre à jour si un composant ou une couleur change**

---

## Structure générale

```
┌─────────────────────────────────────────────────────┐
│  HEADER  [aSchool | slogan | matière | email | ⎋]  │
├──────────┬──────────────────────────────────────────┤
│          │  ZONE TEXTE SOURCE                       │
│ SIDEBAR  │  textarea + [Fichier] [Dicter]           │
│          │                                          │
│ Accueil  │  PARAMÈTRES                              │
│ Mes act. │  Activité / Niveau / Précision / Nb      │
│ Mon prof.│  Inclure correction                      │
│ Historiq.│  [⚡ Générer l'activité]                 │
│ ──────── │                                          │
│ Aide     │  ZONE RÉSULTAT (si généré)               │
│ Feedback │  [.txt] [Word] [Fermer]                  │
│ Avis     │                                          │
│ À propos │                                          │
├──────────┴──────────────────────────────────────────┤
│  FOOTER  slogan centré | aSchool · mentions | v    │
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
- Largeur 176px, rétractable (toggle hamburger avec chevron directionnel)
- Items haut : Accueil (actif bordeaux), Mes activités, Mon profil, Historique
- Items bas (séparateur) : Aide, Feedback (modale), Avis (modale), À propos
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
- Ligne infos : aSchool · Mentions légales (gauche) | version · contact (droite)

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

- Pas de "IA" — utiliser "aSchool"
- Pas d'emojis
- Matière : définie à la connexion, affichée dans la navbar, pas dans le formulaire
- Selectbox : pas de saisie libre (dropdown uniquement)
