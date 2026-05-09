# Logos — aSchool frontend

> Règle : pour changer un logo, on écrase le fichier. On ne touche jamais au code.

---

## 3 fichiers, 3 rôles

| Fichier | Fond | Texte | Utilisé dans |
|---|---|---|---|
| `Logo_aSchool.png` | Transparent | Foncé | Sidebar dépliée, Footer, APropos, cartes auth (Login, Signup, ForgotPassword, ResetPassword, VerifyEmail) |
| `Logo_aSchool_blanc.png` | Transparent | Blanc | Header principal, headers des pages auth, MentionsLegales |
| `icon.png` | Transparent | — | Sidebar repliée, Feedback, Notation, AdminLogin |

---

## TAILLES FIXES — NE JAMAIS MODIFIER

### Tous les headers (Header.jsx + Login, Signup, ForgotPassword, ResetPassword, VerifyEmail, MentionsLegales)
- **Header** : `height: 65px`, `overflow: hidden` — NE PAS CHANGER
- **Logo** : `height: 140px` — NE PAS CHANGER
- Le logo est plus grand que le header : les marges transparentes du PNG sont rognées par overflow:hidden, ce qui rend le logo visible plus grand sans agrandir le header.

---

## Statut

| Fichier | Statut |
|---|---|
| `Logo_aSchool.png` | Validé ✓ |
| `Logo_aSchool_blanc.png` | Validé ✓ |
| `icon.png` | Validé ✓ |
