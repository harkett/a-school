# aSchool — TRACKER

> **Vue de pilotage de l'utilisateur.** Une ligne par tâche, lisible d'un coup d'œil.
> Le détail (score, description, synergies, audits, RAG, journal FAIT) vit dans [TABLEAU-DE-BORD.md](TABLEAU-DE-BORD.md).
>
> **Règle de tenue :** Statut / ordre / dépendance → ce TRACKER fait foi. Détail / score / journal FAIT → le TABLEAU fait foi.
> Le statut est mis à jour ICI, dans la même réponse où l'on démarre ou finit une tâche.

**Statut :** ☐ à faire · 🔄 en cours · ⏸️ en pause · ✅ fait
**Prio :** P1 / P2 / P3 — *remplie par l'utilisateur*

---

| Statut | Prio | Tâche | Dépend de | Fiche |
|---|---|---|---|---|
| 🔄 |  | Consolidation du cœur (filet de tests + suspect sous filet) | rien de bloquant | [D16](BOUSSOLE/D16.md) |
| ⏸️ |  | Affinage interactif de séquence *(= item 37)* | câblage de la route à faire — code dormant, parké | [D07](BOUSSOLE/D07.md) |
| 🔄 |  | PROD-BUSINESS — Activité 100% fonctionnel | rien de bloquant | [D12](BOUSSOLE/D12.md) |
| ☐ |  | PROD-BUSINESS — Séquences 100% fonctionnel | attend la fin de l'Affinage séquence (D07) | [D13](BOUSSOLE/D13.md) |
| 🔄 |  | INFRA-RAG — Pile RAG mutualisée | attend décision hébergement chroma_db (VPS) | [INFRA-RAG](RAG/INFRA-RAG.md) |
| 🔄 |  | Corpus Programmes MEN (producteur RAG) *(= item 36)* | attend INFRA-RAG en place | [D24](BOUSSOLE/D24.md) |

---

> **Pour ajouter une tâche :** quand tu décides d'attaquer un item du réservoir, tu le fais remonter ici (une ligne). Les 40 autres items du réservoir restent dans le [TABLEAU-DE-BORD.md](TABLEAU-DE-BORD.md) tant que tu ne les pilotes pas.
