# CLAUDE.md — Règles permanentes aSchool

> Ce fichier est lu automatiquement à chaque session. Ces règles s'appliquent sans exception.

---

## Streamlit est MORT — depuis le 24/04/2026

Streamlit a été abandonné définitivement le 24/04/2026. Le projet tourne sur **FastAPI + React**.

**Fichiers morts supprimés :**
- `app.py` — ancienne UI Streamlit (supprimé)
- `src/auth.py` — ancienne auth Streamlit avec magic links (supprimé)
- `.streamlit/secrets.toml` — config Streamlit (supprimé)

**Ce qui n'existe plus :**
- Magic links (remplacé par email token 60 min + JWT httpOnly cookies)
- `st.secrets` (remplacé par `os.getenv()`)
- `send_magic_link()` / `notify_admin_connexion()` (supprimées)
- `streamlit_cookies_controller`, `streamlit_mic_recorder` (supprimés)

**Règle absolue :** toute référence à Streamlit, magic link, `st.secrets`, `send_magic_link`, `notify_admin_connexion` trouvée dans le code ou la doc est du **code mort à supprimer immédiatement**, sans demander.

---

## SMTP — Règles absolues

- Ne jamais changer de fournisseur SMTP sans demande explicite
- `SMTP_FROM` = `aSchool <contact@aschool.fr>` (emails vers les profs)
- `FEEDBACK_FROM` = `aSchool Feedback <feedback@aschool.fr>` (notifications admin)
- Tout le code SMTP passe par `_smtp_send()` dans `backend/auth.py` — ne jamais créer de connexion SMTP ailleurs
- `feedback_client.py` est deprecated — ne jamais réutiliser
- Voir `MesMD/EMAILS.md` avant toute modification email

---

## Auth — Ne pas toucher

L'auth JWT (bcrypt + python-jose, httpOnly cookies) fonctionne parfaitement depuis le 25/04/2026. Ne jamais modifier `backend/auth.py` ni `backend/routers/auth.py` sans demande explicite.

---

## Déploiement VPS — Convention obligatoire

Toutes les applications web sont dans `/var/www/<nom-app>/` — standard Linux FHS, suivi par Nginx et tous les hébergeurs professionnels.

| Application | Chemin | .env |
|---|---|---|
| aSchool | `/var/www/aSchool/` | `/var/www/aSchool/.env` |
| AFIA-FR | `/home/ubuntu/AFIA-FR/` ⚠️ | `/home/ubuntu/AFIA-FR/backend/.env` ⚠️ à migrer |

Ne jamais suggérer `/home/ubuntu/` pour un nouveau déploiement — toujours `/var/www/`.

---

## Renommage — Règle de cascade obligatoire

Dès qu'un nom UI change (page, section, composant, route), produire dans la même réponse la liste complète des impacts : fichiers frontend, page IDs dans App.jsx, composants, routes backend, noms de fichiers. Demander si on traite maintenant ou si on note dans TRACKER sous "En attente de cascade". Ne jamais clore la session sans que chaque impact soit traité ou noté.

---

## Workflow obligatoire

Proposer → valider → coder → tester. Ne jamais coder sans validation explicite de l'utilisateur.

---

## Nom du produit — aSchool

Le nom affiché dans toute l'interface, les textes, les boutons et les messages est **aSchool** (a minuscule, S majuscule). Jamais "aSchool", jamais "IA".

---

## Bulles d'aide — Règle absolue

Tout bouton, lien d'action ou icône cliquable doit avoir un attribut `title="..."` décrivant ce qu'il fait. Sans exception. Vérifier également que le texte est lisible : `color: white !important` sur tout fond foncé.

---

## TRACKER.md — Source unique de vérité

`MesMD/TRACKER.md` est le seul endroit où sont tracés statut, idées et avancement. Règles :
- Toute idée mentionnée en session → notée dans TRACKER.md **immédiatement**, dans la même réponse. Pas en fin de session.
- Jamais de cases ☐/☑ dans un autre document (specs, dashboard, mémoire).
- En fin de session : synchroniser TRACKER.md (cocher les livrés, ajouter les nouvelles idées).

---

## Règles UI permanentes

- **Profil = source unique** pour matière et niveau. Jamais de `<select>` matière/niveau dans les features — toujours lire depuis le profil.
- **Bouton d'action principale** = classe `btn-primary` + icône SVG + `title=` tooltip + positionné en bas à droite. Référence : bouton "Générer l'activité" dans `Parametres.jsx`.
- **Header** : `height: 65px`, `overflow: hidden`. **Logo** : `height: 140px`. INTOUCHABLES.
- **Tagline** "Générateur d'activités pédagogiques" = `<span>` HTML blanc dans le header, toujours présent, jamais dans le PNG seul.

---

## Responsive mobile — Règle PWA

Toute adaptation mobile utilise `const isMobile = window.innerWidth < 768` défini localement dans chaque composant. Ne jamais casser le layout desktop (> 768px). Patterns établis :
- Sidebar : `useState(() => window.innerWidth < 768)` → repliée par défaut sur mobile
- Header : tagline masquée, matière sous le nom, bouton "Déconnecter" raccourci
- Grilles `1fr Xpx` → `1fr` sur mobile
- Boutons hover-only → toujours visibles sur mobile (`isMobile || hovered`)
- Longs blocs tutoriel/aide → masqués sur mobile (`!isMobile`)

---

## Fournisseur IA — Règle absolue

Groq (`llama-3.3-70b-versatile`) par défaut. Google Gemini banni — compte Workspace afia.fr incompatible avec le free tier.

---

## Aide — Règle absolue

Dès qu'une fonctionnalité est livrée, sa section Aide est rédigée dans la **même session** — à chaud, pendant que c'est frais. Jamais en retard. Jamais reporté à "plus tard".

---

## Secrets — Règle absolue

Ne jamais afficher mots de passe, clés API ou tokens en clair dans la discussion, même si l'utilisateur le demande.
