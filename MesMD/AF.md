# A-SCHOOL — À Faire

> **Vérifié le : 21/04/2026 — État : à jour** — déploiement automatisé coché, 3 tâches stratégiques ajoutées

---

## Phase 2 — Ce qui a été fait

- [x] Déploiement VPS complet (Nginx, HTTPS Let's Encrypt, DNS Infomaniak)
- [x] App accessible sur https://school.afia.fr
- [x] Dictée vocale via Groq Whisper API
- [x] Export Word (.docx) et texte (.txt)
- [x] Résultat persistant avec bouton Fermer
- [x] Saisie libre désactivée dans les combos
- [x] Interface nettoyée (emojis supprimés, zones Upload/Micro côte à côte)

---

## Outils provisoires (à remplacer)

| Outil actuel | Remplacé par | Quand | Raison |
|---|---|---|---|
| Groq Whisper API (dictée) | faster-whisper local sur VPS | Phase 2b | Confidentialité données élèves, gratuit illimité |
| Streamlit | React ou Vue.js | Phase 4 | Limites UI, scalabilité |
| SQLite | PostgreSQL | Phase 3 | Multi-utilisateurs, robustesse |
| Fichiers `.env` | Variables d'environnement Docker | Phase 3 | Sécurité, déploiement propre |

---

## À faire — Court terme (Phase 2 / 2b)

- [ ] **Tester massivement avec de vrais profs** — HAUTE / Faible — Minimum 5 profs, 3 matières différentes pour découvrir ce qui manque vraiment
- [ ] **Tester la dictée avec la prof pilote** — HAUTE / Faible — Valider avant de continuer
- [ ] **Zone micro visuellement identique à Upload** — MOYENNE / Haute — Limite Streamlit, nécessite composant React (Phase 4)
- [ ] **Basculer dictée sur faster-whisper local** — MOYENNE / Moyenne — Installer sur VPS, modèle medium français (~1.5 Go)
- [ ] **Sélecteur de microphone dans l'interface** — BASSE / Moyenne — Utile si plusieurs micros disponibles
- [ ] **Export PDF** — BASSE / Moyenne — Ajouter après validation prof pilote

---

## À faire — Moyen terme (Phase 3)

- [ ] **Ajouter d'autres matières (histoire, maths, SVT...)** — HAUTE / Faible — Juste des prompts en BDD, pas de code — c'est là que l'outil devient une plateforme
- [ ] **Compte utilisateur minimal** — HAUTE / Moyenne — Email + mot de passe pour retrouver ses activités passées, créer de la fidélité
- [ ] **Backend FastAPI** — HAUTE / Haute — Remplace Streamlit comme moteur
- [ ] **Base de données SQLite (puis PostgreSQL)** — HAUTE / Moyenne — Stockage prompts, activités, historique
- [ ] **Interface admin web** — HAUTE / Haute — Ajouter/modifier activités sans code
- [ ] **Authentification enseignants** — HAUTE / Moyenne — Login/mot de passe par établissement
- [ ] **Historique des activités par prof** — MOYENNE / Moyenne — Retrouver ses activités passées
- [ ] **Docker (backend + frontend + BDD)** — MOYENNE / Haute — Isolation, déploiement propre
- [x] **Procédure de mise à jour automatisée** — `push.ps1` gère push GitHub + restart VPS en une seule commande

---

## À faire — Long terme (Phase 4)

- [ ] **Frontend React/Vue** — HAUTE / Très haute — Remplace Streamlit, UI pro
- [ ] **Partage d'activités entre collègues** — MOYENNE / Haute
- [ ] **Tableau de bord par établissement** — MOYENNE / Haute
- [ ] **Toutes matières (maths, histoire...)** — MOYENNE / Moyenne — Ajouter prompts en BDD via admin
- [ ] **Import PDF (extraits de manuels)** — BASSE / Haute — OCR + parsing
- [ ] **Application mobile (PWA)** — BASSE / Haute
- [ ] **Intégration ENT (Pronote...)** — BASSE / Très haute
- [ ] **Gestion abonnements (freemium)** — BASSE / Très haute

---

## Limite connue Streamlit (pour info)

Streamlit ne permet pas d'envelopper un composant externe (comme le micro) dans un `<div>` HTML personnalisé. La zone "Dicter" ne peut pas être rendue visuellement identique à la zone "Upload" sans un composant React custom. Ce sera résolu en Phase 4 avec le frontend React.

---

## Prochaine session recommandée

1. **Test prof pilote** — faire tester school.afia.fr à la professeure de français 4e
2. **Recueillir les retours** — noter ce qui manque, ce qui gêne
3. **Décider** : corriger les retours pilote OU démarrer Phase 2b (dictée locale)
