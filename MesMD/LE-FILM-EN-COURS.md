# LE FILM EN COURS — refonte du référentiel Bébés (0-1 an)

> Récap vivant, à suivre à deux — **mis à jour au fil du travail** (pas seulement quand on s'en souvient).
> Statut global : couple Bébés travaillé sur le **miroir** (TEST). La vraie base n'a pas été touchée, **rien n'est committé**.

## 0. Repartir propre ✅

- Trancher la gouvernance : matières (les tiennes) vs domaines UNICEF → décidé = tes matières
- Comprendre la dérive de CC (il avait rangé par domaines)

## 1. Le référentiel Bébés ✅

- Valider les 10 matières du socle Bébés
- (parenthèse Moyens : apostrophe [à confirmer] + lien affectif décidé/laissé ON → fermée) ✅
- Ranger les 18 activités sous les 10 matières (tableau validé)
- Reconstruire le document par matières + le vérifier
- Générer le PDF + vérifier les accents

## 2. Première mise en moteur de recherche ✅

- Ingestion des chunks sur le miroir (1re fois)
- Test des scores → Motricité globale échouait (0,276) → c'est ce qui a déclenché le travail sur les acteurs (section 3)

## 3. Les acteurs du score

Objectif : meilleure activité en rang 1, meilleur score, moins d'intrusions. On les traite **UN PAR UN**.

- **Modèle** : MiniLM (384) → BGE-M3 (1024) — ✅
- **PDF**, en deux temps :
  - (a) **Découpage** : 900 caractères aveugle → 1 fiche = 1 chunk — ✅
  - (b) **Contenu des fiches** (leviers : densifier le vocabulaire de la matière, retirer « développe aussi », recentrer les fiches hors-piste) — ✅ 18 fiches réécrites, code aligné, PDF régénéré, ré-ingéré + **re-testé sur miroir**. Résultat mesuré : **intrusions nettement réduites, marges élargies** (la bonne fiche plus clairement en rang 1) ; **scores bruts ~stables** (quelques-uns en légère baisse). → gain de **précision**, pas de score.
- **Requête** — ✅ **tranché = T2** (`« Activité d'éveil pour développer {matiere} chez un enfant de {niveau} »`, gabarit uniforme). Prouvé sur miroir avec la **chaîne réelle de l'endpoint** : moy rang 1 **0,700** vs **0,655** au nom seul (**+0,045**), **9/9** bonne fiche en rang 1. Branché dans `exemple_referentiel.py` (constante `REQUETE_GABARIT`). Le préfixe d'instruction BGE-M3 (T3) testé et **écarté** (dégrade : doc + mesure d'accord). NB : formulation calibrée crèche, à réexaminer au 1er couple non-crèche.
- **Seuil (0,30)** — ☐ pas encore traité (dernier acteur)

> Règle actée : la **méthode en vigueur** (1 fiche = 1 chunk, 1 activité = 1 matière, embeddings BGE-M3) est écrite dans **CLAUDE.md** ; l'ancienne méthode est morte.

## 4. Résultat Bébés — où on en est

- **Après modèle + découpage** : 5/5 matières passent, bonne fiche en rang 1, affectif réglé (prouvé sur miroir).
- **Après réécriture du contenu (re-test fait)** : 9/9 matières remontent leur propre fiche en rang 1 ; **intrusions réduites et marges élargies** (précision) ; scores bruts ~stables. Le couple Bébés est propre sur le miroir.
- **Après requête T2 (tranché + branché)** : score brut relevé (+0,045 vs nom seul), 9/9 bonne fiche en rang 1, sur miroir. Le code (`exemple_referentiel.py`) porte le gabarit uniforme.
- **Reste** (dernier acteur) : **seuil** (recalibrer 0,30 maintenant que requête est fixée). Puis vraie base, CIEL, Grands/Moyens, migration Alembic, commit : plus tard.
