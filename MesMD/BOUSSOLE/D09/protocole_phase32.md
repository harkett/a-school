# Protocole Phase 3.2 — Tests bout-en-bout dictée Deepgram

> Phase 3.2 = pivots paramètres Deepgram (endpointing_ms, smart_format, keyterms)
> sur vraie voix Edge MediaRecorder Opus + vocabulaire pédagogique réel.
> Plumbing code = commit C1 `0ec0cde` (17/05/2026) câblant DEEPGRAM_ENDPOINTING_MS
> + DEEPGRAM_SMART_FORMAT. Câblage DEEPGRAM_KEYTERMS_ENABLED à venir dans commit dédié (cf. §3.1).
> Date d'ouverture protocole : 17/05/2026.

---

## 1. Énoncés étalons (figés)

7 énoncés × 3 takes par énoncé = 21 takes par run. Prononcer textuellement,
naturellement, sans accentuation artificielle. Chaque take = un cycle complet
mic ON → énoncé → mic OFF.

| # | Type | Énoncé à prononcer |
|---|---|---|
| E1 | Math — keyterm "hypoténuse" | L'hypoténuse d'un triangle rectangle est le côté opposé à l'angle droit. |
| E2 | Math — notation symbolique | Soit f la fonction définie par f de x égal deux x au carré moins trois x plus un. |
| E3 | Physique — formule | L'accélération est égale au quotient de la vitesse par le temps. |
| E4 | Français — ponctuation + chiffre romain | Au dix-neuvième siècle, le naturalisme prolonge le réalisme. |
| E5 | Histoire-géo — nombre en lettres | Charlemagne a été couronné empereur en l'an huit cents. |
| E6 | Consigne mono-phrase multi-clauses | Soit ABC un triangle rectangle en A, dans lequel AB mesure six centimètres et BC mesure dix centimètres ; calculez la longueur du côté AC en appliquant le théorème de Pythagore. |
| E7 | Nom propre rare + date en lettres | Saint-Exupéry a écrit Le Petit Prince en mille neuf cent quarante-trois. |

---

## 2. Critères de validation par pivot

### 2.1 Endpointing (R1/R2/R3 vs R0)

- **Sémantique des events finaux Deepgram** (figée le 17/05/2026, suite au smoke C1.5) :
  - `is_final` *intermédiaire* : Deepgram clôt un segment par décision interne
    (prosodie, fin de phrase détectée) AVANT expiration du timer endpointing.
    Mesure latence de décision Deepgram, **indépendante d'`endpointing_ms`**.
    Loggué pour traçabilité, **exclu de l'agrégation latence**.
  - `speech_final` : Deepgram clôt par expiration du timer endpointing
    après silence prolongé. Mesure cible des pivots R1-R6.
    **Seul event utilisé pour calculer médianes et seuils.**

- **Latence d'endpointing** : médiane sur 21 takes du `delta_interim_ms`
  capturé par l'instrumentation backend (log `STT_MEASURE`, cf. C1.5),
  filtrée sur événements `event=speech_final` uniquement. Mesure
  automatique, précision ±5-20 ms (timestamps Python `time.monotonic()`).

- **Intégrité mid-clause** sur E6 : **kill binaire** si segmentation (apparition
  d'un `is_final` intermédiaire) AVANT le point final unique. Une segmentation
  sur la virgule avant "dans lequel", ou sur le point-virgule avant "calculez",
  invalide la valeur d'endpointing.

- **Outillage extract (C1.6)** : le script
  `MesMD/DEEPGRAM/extract_measurements.py` filtre `event=speech_final` pour
  alimenter les colonnes "latence" de la grille §4. Les `is_final`
  intermédiaires sont préservés en log mais n'apparaissent pas dans les
  médianes/agrégations.

- **Décision** : valeur d'endpointing retenue = la plus basse qui passe les deux
  critères. Reportée comme `<X retenu>` dans R4/R5/R6.

**Observation pré-R0 (smoke C1.5, 17/05/2026)** : à endpointing=800 (baseline
R0), une phrase de 7s ("Aujourd'hui je teste la dictée vocale du système.")
a été segmentée par Deepgram en 2 segments. Implications : R1 (500), R2 (400),
R3 (300) vont segmenter plus → critère "intégrité mid-clause" pourrait
s'enclencher tôt sur des phrases sans point-virgule. À garder en tête pendant R0.

### 2.2 Smart_format (R4/R5)

- **Count erreurs réécriture** sur les 15 takes non-keyterm (E2-E6, 5 énoncés ×
  3 takes — E1 et E7 exclus car keyterm/orthographe spécifiques traités ailleurs).
- Une "erreur" = réécriture incorrecte qu'un prof devrait corriger à la main :
  - Comparer les réécritures observées entre R0 (ON) et R4 (OFF) sur E2, E4, E5
  - Identifier celle qui nécessite le moins de corrections manuelles côté prof
  - Critères secondaires : ponctuation aberrante, nombre cassé, espace manquant
- **Décision** : ON ou OFF retenu = celui avec le plus faible count d'erreurs.
  Reporté comme `<Y retenu>` dans R6.

### 2.3 Keyterms (R6 vs R0)

- **Critère principal** : sur E1, "hypoténuse" correctement transcrit ≥ 2/3 takes
  avec keyterms ON (R0 réutilisé), vs comportement avec keyterms OFF (R6).
  Si keyterms OFF rend "hypothèse" ou autre substitution sur ≥ 2/3 takes,
  validation positive de l'utilité du keyterm boost.
- **Critère secondaire (observation)** : faux positif keyterm — keyterms ON force
  un keyterm là où il n'a rien à faire. Noter en marge si observé sur E2-E7.
  N'invalide pas le pivot mais documenté.

---

## 3. Plan des runs

7 runs au total. Entre chaque run : modifier `.env` + restart uvicorn.

| ID | endpointing | smart_format | keyterms | Pivot testé | Prérequis |
|---|---|---|---|---|---|
| R0 | 800 | true | ON | Baseline defaults dataclass | C1 livré ✅ (0ec0cde) |
| R1 | 500 | true | ON | Endpointing -300ms | C1 |
| R2 | 400 | true | ON | Endpointing -400ms | C1 |
| R3 | 300 | true | ON | Endpointing seuil bas | C1 |
| R4 | `<X retenu>` | **false** | ON | Smart format OFF | C1 |
| R5 | `<X>` | `<Y retenu après R4>` | ON | Réconfirmation valeur smart_format retenue (R5 = run de contrôle, peut être skippé si R4 vs R0 est concluant) | C1 |
| R6 | `<X>` | `<Y>` | **OFF** | Keyterms désactivés | **Câblage `KEYTERMS_ENABLED`** |

### 3.1 Prérequis env var `DEEPGRAM_KEYTERMS_ENABLED` (avant R6)

R6 nécessite un mécanisme pour désactiver les keyterms côté provider sans
toucher la BDD. **Câbler env var `DEEPGRAM_KEYTERMS_ENABLED` (default `true`)** :
- Ajouter champ `keyterms_enabled: bool = True` au dataclass `STTSessionConfig`
  (cohérence single source of truth avec `endpointing_ms`/`smart_format` câblés
  en C1 via `_defaults = STTSessionConfig()`). La dette Phase 1.1 résiduelle
  reste celle des 4 vars non câblées (LANGUAGE, INTERIM_RESULTS, DICTATION,
  PUNCTUATE) — `keyterms_enabled` rejoint le groupe "câblé Phase 3.2".
- Pattern identique C1 (lecture dans `backend/routers/transcribe.py`, parsing (b))
- Provider `deepgram_provider.py` : si `cfg.keyterms_enabled=False`, ne pas
  charger les keyterms BDD ni les injecter dans `LiveOptions`
- Filet `test_phase22.py` 7/7 avant ET après le commit de câblage (réflexe Phase 2.2 maintenu)
- Commit séparé `feat(stt): câbler DEEPGRAM_KEYTERMS_ENABLED (Phase 3.2 prérequis R6)`

### 3.2 Workflow pivot inter-run

1. Modifier `.env` (changer la/les vars du run suivant)
2. Tuer puis relancer uvicorn (env vars figées au lancement du process)
3. Vérifier au 1er WS test : log INFO `STT encoding=opus — user=...` dans la
   console uvicorn (cf. `backend/routers/transcribe.py:129`)
4. Dicter les 7 énoncés × 3 takes dans Edge, depuis la page TexteSource
5. Reporter résultats dans la grille §4 (run correspondant)
6. Conclure verdict du run AVANT de passer au suivant (latence médiane,
   count erreurs, hypoténuse OK/KO)

---

## 4. Grille de mesure (à remplir)

### Run R0 — baseline (endpointing=800, smart_format=true, keyterms=ON)

| Énoncé | Take | Transcrit (final concaténé) | Latence is_final (s) | Verdict |
|---|---|---|---|---|
| E1 | 1 |  |  |  |
| E1 | 2 |  |  |  |
| E1 | 3 |  |  |  |
| E2 | 1 |  |  |  |
| E2 | 2 |  |  |  |
| E2 | 3 |  |  |  |
| E3 | 1 |  |  |  |
| E3 | 2 |  |  |  |
| E3 | 3 |  |  |  |
| E4 | 1 |  |  |  |
| E4 | 2 |  |  |  |
| E4 | 3 |  |  |  |
| E5 | 1 |  |  |  |
| E5 | 2 |  |  |  |
| E5 | 3 |  |  |  |
| E6 | 1 |  |  |  |
| E6 | 2 |  |  |  |
| E6 | 3 |  |  |  |
| E7 | 1 |  |  |  |
| E7 | 2 |  |  |  |
| E7 | 3 |  |  |  |

**Latence médiane** : ___ s
**Intégrité E6** : OK / KILL (segmentation observée : ___)
**Hypoténuse E1** : ___/3 takes OK
**Erreurs smart_format E2-E6** : ___ sur 15 takes
**Verdict pivot baseline** : NA (référence)

---

### Run R1 — endpointing=500, smart_format=true, keyterms=ON

(grille identique R0)

**Latence médiane** : ___ s
**Intégrité E6** : OK / KILL
**Hypoténuse E1** : ___/3
**Erreurs smart_format E2-E6** : ___/15
**Verdict pivot endpointing=500** : RETENU / REJETÉ — raison :

---

### Run R2 — endpointing=400, smart_format=true, keyterms=ON

(grille identique R0)

**Verdict pivot endpointing=400** : RETENU / REJETÉ — raison :

---

### Run R3 — endpointing=300, smart_format=true, keyterms=ON

(grille identique R0)

**Verdict pivot endpointing=300** : RETENU / REJETÉ — raison :

---

### Synthèse endpointing (R0-R3)

| Run | endpointing | Latence médiane | Intégrité E6 | Verdict |
|---|---|---|---|---|
| R0 | 800 |  |  | référence |
| R1 | 500 |  |  |  |
| R2 | 400 |  |  |  |
| R3 | 300 |  |  |  |

**Valeur retenue X** : ___

---

### Run R4 — endpointing=X, smart_format=**false**, keyterms=ON

(grille identique R0)

**Verdict pivot smart_format=false** : RETENU / REJETÉ — raison :

---

### Run R5 (optionnel) — confirmation Y retenu après R4

À skipper si R0 vs R4 est concluant sur smart_format.

---

### Run R6 — endpointing=X, smart_format=Y, keyterms=**OFF**

⚠️ Prérequis : commit dédié de câblage `DEEPGRAM_KEYTERMS_ENABLED`.

(grille identique R0, focus E1 + observations E2-E7)

**Hypoténuse E1 OFF** : ___/3
**Faux positifs observés E2-E7** : ___
**Verdict pivot keyterms** : UTILE / NEUTRE / NUISIBLE — raison :

---

## 5. Synthèse finale Phase 3.2

À remplir en clôture Phase 3.2, juste avant commit C2 :

| Paramètre | Valeur retenue | Justification |
|---|---|---|
| `DEEPGRAM_ENDPOINTING_MS` | ___ | ___ |
| `DEEPGRAM_SMART_FORMAT` | ___ | ___ |
| `DEEPGRAM_KEYTERMS_ENABLED` | ___ | ___ |

Defaults dataclass `STTSessionConfig` à mettre à jour en C2 :
- `endpointing_ms = <X retenu>`
- `smart_format = <Y retenu>`
- `keyterms_enabled = <bool retenu>`

Synchroniser `.env.example` avec les nouvelles valeurs.
