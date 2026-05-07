# Pack légal complet — A‑SCHOOL / AFIA Services

> Document de référence interne — synthèse des 4 pages légales du site.
> Dernière mise à jour : mai 2026
>
> **Placeholders à remplacer avant publication :**
> - `[À COMPLÉTER — forme juridique]` → ex. SASU, SARL, Auto-entrepreneur
> - `[À COMPLÉTER — SIRET]` → numéro à 14 chiffres
> - `[À COMPLÉTER — capital social]` → ex. 1 000 € (non requis pour auto-entrepreneur)
> - `[À COMPLÉTER — adresse du siège]` → adresse officielle
> - `[À COMPLÉTER — nom du dirigeant]` → prénom et nom du responsable de la publication
> - `[À COMPLÉTER — ville siège]` → pour la juridiction compétente dans les CGU

---

## Plan de site légal

Structure des pages légales accessibles depuis le footer :

- `/mentions-legales`
- `/politique-de-confidentialite`
- `/conditions-generales-utilisation`
- `/cookies`

---

## 1. Mentions légales

### Éditeur du site

- **Raison sociale :** AFIA Services
- **Forme juridique :** [À COMPLÉTER — forme juridique]
- **Capital social :** [À COMPLÉTER — capital social]
- **SIRET :** [À COMPLÉTER — SIRET]
- **Siège social :** [À COMPLÉTER — adresse du siège]
- **Responsable de la publication :** [À COMPLÉTER — nom du dirigeant]
- **Contact :** contact@afia.fr
- **Site web :** https://school.afia.fr

### Hébergement

Serveur privé virtuel (VPS) administré par AFIA Services, localisé dans l'Union Européenne.

La génération IA est assurée par **Groq Cloud Inc.** (USA), encadrée par des Clauses Contractuelles Types conformes au RGPD.

### Propriété intellectuelle

© 2026 — AFIA Services. Tous droits réservés.
Toute reproduction non autorisée est interdite.

### Responsabilité

AFIA Services ne peut être tenue responsable d'une mauvaise utilisation, d'une interruption de service ou des contenus générés par les utilisateurs.

---

## 2. Politique de confidentialité (RGPD)

### Responsable du traitement

AFIA Services — contact@afia.fr

### Données collectées

- Données d'inscription : e‑mail, prénom, nom, matière, niveau
- Données d'usage : contenus générés, préférences
- Données techniques : session, logs, IP (sécurité)

Aucune donnée sensible (art. 9 RGPD).

### Finalités

Fonctionnement du service, gestion du compte, amélioration, sécurité.
Aucun usage commercial ou publicitaire.

### Base légale

- Exécution du service (art. 6.1.b)
- Consentement (art. 6.1.a)
- Intérêt légitime — sécurité (art. 6.1.f)

### Sous-traitants

| Sous-traitant | Rôle | Localisation | Garanties |
|---|---|---|---|
| AFIA Services (VPS) | Hébergement | UE | Interne |
| Groq Cloud Inc. | Génération IA | États-Unis | CCT (décision 2021/914) |

### Durée de conservation

- Compte actif : données conservées tant que le compte est actif
- Inactivité : suppression après **36 mois**
- Sauvegardes techniques : max **30 jours**

### Droits des utilisateurs

Accès, rectification, effacement, limitation, opposition, portabilité.
Contact : contact@afia.fr — réponse sous 30 jours.
Recours possible auprès de la CNIL (cnil.fr).

### Sécurité

HTTPS, VPS sécurisé UE, accès restreint, journalisation, sauvegardes.

---

## 3. Conditions Générales d'Utilisation

### Accès

Réservé aux professionnels de l'enseignement. Nécessite un compte valide.

### Obligations de l'utilisateur

Usage légal et pédagogique. Interdiction de contourner la sécurité ou d'accéder aux données d'autrui.

### Contenus générés

L'utilisateur est responsable des contenus générés et de leur diffusion.
Les contenus IA peuvent comporter des erreurs — relecture obligatoire avant usage.

### Bibliothèque partagée

Le partage d'une activité implique l'autorisation de diffusion à tous les utilisateurs inscrits.

### Propriété intellectuelle

© 2026 AFIA Services — tous éléments de l'application protégés.

### Limitation de responsabilité IA

AFIA Services n'est pas responsable des erreurs dans les contenus générés par l'IA.

### Résiliation

Par l'utilisateur : demande à contact@afia.fr.
Par AFIA Services : en cas de violation des CGU, fraude ou inactivité prolongée.

### Modifications des CGU

Modifications notifiées par e‑mail. Poursuite de l'utilisation = acceptation.

### Droit applicable

Droit français. Juridiction : tribunaux de [À COMPLÉTER — ville siège].

---

## 4. Cookies

### Cookies utilisés

| Cookie | Finalité | Durée |
|---|---|---|
| `aschool_token` | Session utilisateur (JWT httpOnly) | Session / 7 jours |
| `aschool_refresh` | Renouvellement de session | 7 jours |

### Pas de bandeau requis

Cookies techniques uniquement → aucun consentement requis (CNIL, délibération 17/09/2020).

### Aucun cookie tiers

Ni publicitaire, ni analytique, ni réseau social.

---

## 5. Points à traiter avant publication

- [ ] Remplacer tous les placeholders `[À COMPLÉTER]`
- [ ] Vérifier que `contact@afia.fr` est opérationnelle (ou mettre à jour avec `contact@aschool.fr`)
- [ ] Intégrer les 4 pages dans le site (routes React + liens dans le footer)
- [ ] Ajouter les liens footer sur toutes les pages de l'application
- [ ] Vérifier la conformité avec l'avocat ou le DPO si nécessaire
