# CLAUDE.md — Règles permanentes A-SCHOOL

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
- `SMTP_FROM` = `A-SCHOOL <contact@aschool.fr>` (emails vers les profs)
- `FEEDBACK_FROM` = `A-SCHOOL Feedback <feedback@aschool.fr>` (notifications admin)
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
| A-SCHOOL | `/var/www/a-school/` | `/var/www/a-school/.env` |
| AFIA-FR | `/home/ubuntu/AFIA-FR/` ⚠️ | `/home/ubuntu/AFIA-FR/backend/.env` ⚠️ à migrer |

Ne jamais suggérer `/home/ubuntu/` pour un nouveau déploiement — toujours `/var/www/`.

---

## Dossier interdit

Ne jamais lire `D:\A-SCHOOL\MesRessources\` — dossier personnel hors projet.

---

## Workflow obligatoire

Proposer → valider → coder → tester. Ne jamais coder sans validation explicite de l'utilisateur.
