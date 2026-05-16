# Spécification technique — Intégration Deepgram STT

> **Version 1.1 — Mai 2026**  
> Mise à jour : intégration des décisions Phase 1 après revue technique

---

## 0. Étape préalable obligatoire (avant tout code)

**Avant de coder l'abstraction, valider la connexion brute à Deepgram.**

Objectif : s'assurer que la clé fonctionne, que Nova-3 transcrit correctement le français pédagogique, et que le format audio choisi (Opus 16 kHz) est bien accepté en streaming.

### 0.1 Test wscat ou script Python minimal

Avec un script de ~20 lignes en dehors de la codebase (script jetable) :
- Ouvrir une WebSocket vers `wss://api.deepgram.com/v1/listen` avec les paramètres prévus
- Envoyer un fichier audio FR contenant du vocabulaire pédagogique ("polynôme", "Lavoisier", "hypoténuse")
- Vérifier que les transcripts arrivent en streaming, que la qualité est conforme aux attentes
- Tester la latence first-token réelle depuis le VPS (depuis la France métropolitaine vers la région `us`)

### 0.2 Critères de validation

- [ ] Connexion WebSocket établie sans erreur d'auth
- [ ] Transcripts `is_final: false` reçus pendant l'envoi audio (vrai streaming)
- [ ] Transcripts `is_final: true` reçus en fin de phrase
- [ ] Vocabulaire pédagogique transcrit correctement (polynôme, Lavoisier, etc.)
- [ ] Latence first-token mesurée < 500 ms depuis le VPS France

Si tout est OK → passer au §1. Sinon → debug avant d'investir dans l'abstraction.

---

## 1. Vue d'ensemble fonctionnelle

### 1.1 Objectif

Remplacer la dictée vocale actuelle (`webkitSpeechRecognition`) par une intégration **Deepgram Nova-3** en streaming temps réel.

### 1.2 Besoin utilisateur (prof)

- Le prof clique sur le bouton micro
- Il parle naturellement
- Le texte transcrit s'écrit en direct dans le champ (streaming)
- Quand il clique stop, le texte final est inséré
- Aucun paramétrage technique exposé au prof

### 1.3 Pourquoi Deepgram

| Critère | Décision |
|---|---|
| Mode | **Streaming WebSocket temps réel** (pas batch) |
| Modèle | **Nova-3** (multilingue, qualité FR validée) |
| Phase de validation | $200 de crédits gratuits |
| Évolution future | Architecture extensible vers Azure France / Speechmatics / OVHcloud |

---

## 2. Architecture cible

### 2.1 Principe

```
[Prof navigateur]
     |
     | (WebSocket : audio Opus chunks + transcripts JSON)
     v
[Backend FastAPI]
     |
     | (WebSocket Deepgram + clé API)
     v
[Deepgram Nova-3]
```

**La clé Deepgram reste côté serveur. Jamais exposée au frontend.**

### 2.2 Structure dossier backend

```
backend/
└── stt/
    ├── __init__.py          # factory get_stt_provider()
    ├── base.py              # ABC STTProvider + STTSession + dataclasses + exceptions
    ├── deepgram_provider.py # implémentation Deepgram Nova-3
    └── session_tracker.py   # compteur sessions concurrentes (lock async)
```

---

## 3. Configuration

### 3.1 Variables d'environnement (`.env`)

```bash
# Provider STT actif
STT_PROVIDER=deepgram

# Identifiants Deepgram (JAMAIS en clair dans le code)
DEEPGRAM_API_KEY=[DEEPGRAM_API_KEY]
DEEPGRAM_PROJECT_ID=[DEEPGRAM_PROJECT_ID]

# Modèle et région
DEEPGRAM_MODEL=nova-3
DEEPGRAM_REGION=us  # Phase 1 — voir §3.4 conditions strictes

# Limites concurrence
STT_MAX_CONCURRENT_SESSIONS=40
STT_SESSION_IDLE_TIMEOUT_SECONDS=30
STT_SESSION_MAX_DURATION_SECONDS=300

# Monitoring crédit
STT_INITIAL_CREDIT_USD=200
STT_CREDIT_ALERT_THRESHOLD_PCT=10

# Sécurité — date d'expiration de la clé API (rappel admin)
DEEPGRAM_API_KEY_EXPIRES_AT=2026-08-15

# Paramètres Deepgram (MVP : en .env ; V2 : éditables en admin)
DEEPGRAM_LANGUAGE=fr
DEEPGRAM_SMART_FORMAT=true
DEEPGRAM_INTERIM_RESULTS=true
DEEPGRAM_ENDPOINTING_MS=800
DEEPGRAM_DICTATION=false
DEEPGRAM_PUNCTUATE=true

# Mode des messages utilisateur (neutral en Phase 1)
STT_MESSAGE_MODE=neutral  # 'neutral' | 'volume'
```

### 3.2 Paramètres Deepgram appliqués par défaut

| Paramètre | Valeur Phase 1 | Description |
|---|---|---|
| `language` | `fr` | Langue de transcription |
| `model` | `nova-3` | Modèle Deepgram |
| `smart_format` | `true` | Ponctuation automatique selon intonations |
| `interim_results` | `true` | Résultats partiels en streaming |
| `endpointing` | `800` | Fin de phrase (ms) — augmenté de 500 à 800 pour tolérer les pauses de réflexion |
| `dictation` | `false` | Le prof ne dit pas "point" / "virgule" (option utilisateur V2) |
| `punctuate` | `true` | Ajouter la ponctuation |
| `keyterm` | liste transversale | Voir §3.3 |

### 3.3 Keyterms — stratégie par paliers

**Phase 1 MVP — liste transversale unique (~80 termes)**

Vocabulaire pédagogique universel, couvrant les principales matières :

```
# Vocabulaire pédagogique universel
exercice, consigne, énoncé, question, réponse, justifier, démontrer, calculer,
élève, professeur, classe, leçon, chapitre, devoir, contrôle, évaluation,

# Mathématiques
polynôme, hypoténuse, théorème, équation, fonction affine, dérivée,
intégrale, racine carrée, fraction, numérateur, dénominateur, périmètre,
aire, volume, parallélogramme, isocèle, équilatéral,

# Sciences (physique-chimie / SVT)
Lavoisier, Avogadro, Newton, Einstein, Curie, Pasteur, Darwin,
ADN, ARN, mitochondrie, photosynthèse, molécule, atome, électron,
proton, neutron, oxygène, hydrogène, dioxyde, carbone,

# Lettres / Philosophie
Baudelaire, Hugo, Molière, Rousseau, Voltaire, Camus, Sartre, Proust,
métaphore, allégorie, oxymore, alexandrin, sonnet, tragédie, comédie,
épistémologie, ontologie, dialectique,

# Histoire-Géographie
Charlemagne, Napoléon, Robespierre, Clemenceau, de Gaulle, Mitterrand,
Renaissance, Révolution, Industrialisation, Mondialisation,

# Arts / EPS / Langues / Technique
Picasso, Monet, Vinci, basket-ball, handball, athlétisme,
PISA, QCM, PDF, Wi-Fi, PowerPoint, brevet, baccalauréat
```

**Phase 2 — injection adaptative par matière**

Structure BDD à préparer dès le MVP (sans la logique) :

```sql
-- À créer dès Phase 1, mais on ne lit que keyterms_global au début
CREATE TABLE stt_keyterms_global (
    id SERIAL PRIMARY KEY,
    term VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE stt_keyterms_by_subject (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(50) NOT NULL,  -- 'maths', 'svt', 'philo', 'histoire-geo', etc.
    term VARCHAR(100) NOT NULL,
    UNIQUE(subject, term)
);
```

En Phase 2, le `DeepgramProvider` lira la matière du prof depuis son profil et concaténera 80 transversaux + 20 spécifiques (max 100 keyterms par requête Deepgram).

### 3.4 Région `us` Phase 1 — conditions strictes

L'utilisation de la région `us` est **temporaire et conditionnelle** :

- Mention obligatoire dans les CGU et la politique de confidentialité
- Profs pilotes informés explicitement du contexte
- **Tâche bloquante avant ouverture au-delà de 50 profs** :
  - Soit vérifier la maturité Deepgram région `eu` pour Nova-3 et basculer
  - Soit déclencher la migration vers un provider EU (cf §13)
- À inscrire comme alerte en haut du dashboard admin :
  > *"Phase 1 — région Deepgram US active. Migration EU à planifier avant scale."*

---

## 4. Interface `STTProvider` (backend)

### 4.1 Fichier `backend/stt/base.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional

@dataclass
class Transcript:
    text: str
    is_final: bool
    confidence: float
    start_seconds: float
    end_seconds: float

@dataclass
class STTSessionConfig:
    language: str = "fr"
    sample_rate: int = 16000
    encoding: str = "opus"
    interim_results: bool = True
    smart_format: bool = True
    endpointing_ms: int = 800
    dictation: bool = False
    keyterms: list[str] = field(default_factory=list)

class STTSession(ABC):
    @abstractmethod
    async def send_audio(self, chunk: bytes) -> None: ...
    
    @abstractmethod
    async def receive_transcripts(self) -> AsyncIterator[Transcript]: ...
    
    @abstractmethod
    async def close(self) -> None: ...
    
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

class STTProvider(ABC):
    @abstractmethod
    async def create_session(
        self, config: Optional[STTSessionConfig] = None
    ) -> STTSession: ...

# Exceptions métier
class STTRateLimitError(Exception):
    """Quota STT simultané atteint."""

class STTServiceUnavailableError(Exception):
    """Service STT indisponible (panne provider, etc.)."""

class STTCreditExhaustedError(STTServiceUnavailableError):
    """Crédit Deepgram épuisé spécifiquement."""

class STTSessionTimeoutError(Exception):
    """Session timeout (idle ou durée max)."""
```

### 4.2 Fichier `backend/stt/__init__.py`

```python
import os
from .base import STTProvider
from .deepgram_provider import DeepgramProvider

def get_stt_provider() -> STTProvider:
    name = os.getenv("STT_PROVIDER", "deepgram")
    if name == "deepgram":
        return DeepgramProvider()
    raise ValueError(f"Unknown STT_PROVIDER: {name}")
```

---

## 5. Endpoint WebSocket

### 5.1 Route

```
WS /api/transcribe/stream
```

### 5.2 Authentification

JWT prof via cookie httpOnly. **Vérification AVANT `accept()`** — rejet propre si non authentifié.

### 5.3 Protocole

**Client → Serveur** : frames binaires audio (Opus chunks ~250ms via `MediaRecorder`)

**Serveur → Client** : frames JSON
```json
{
  "type": "transcript",
  "text": "Soit P de x égal à deux",
  "is_final": false,
  "confidence": 0.94
}
```

Messages serveur additionnels :
```json
{ "type": "session_warning", "code": "EXPIRING_SOON", "remaining_seconds": 60 }
```

### 5.4 Codes de fermeture WebSocket

| Code | Raison | Action frontend |
|---|---|---|
| `1000` | Fermeture normale | Aucune |
| `4401` | Non authentifié | Redirection login |
| `4429` | Saturation | Toast saturation |
| `4402` | Crédit épuisé | Message indisponibilité |
| `4502` | Provider down | Message indisponibilité |
| `4408` | Timeout idle ou durée max | Toast info, finaliser le texte reçu |
| `1011` | Erreur interne | Erreur générique |

### 5.5 Implémentation — pattern correct (race condition corrigée)

**Point critique** : l'acquisition du slot doit être atomique avec le check. Pas de `is_available()` puis `track()` séparés.

```python
@router.websocket("/api/transcribe/stream")
async def stt_stream(websocket: WebSocket):
    # 1. Auth AVANT accept
    user = await authenticate_ws(websocket)
    if not user:
        await websocket.close(code=4401)
        return
    
    tracker = get_session_tracker()
    
    # 2. Acquisition atomique (raise si saturé, AVANT accept)
    try:
        async with tracker.acquire():
            await websocket.accept()
            await _run_stt_session(websocket, user)
    except STTRateLimitError:
        await websocket.close(code=4429, reason="HIGH_LOAD")
    except STTCreditExhaustedError:
        await websocket.close(code=4402, reason="CREDIT_EXHAUSTED")
    except STTServiceUnavailableError:
        await websocket.close(code=4502, reason="SERVICE_DOWN")
    except STTSessionTimeoutError:
        await websocket.close(code=4408, reason="SESSION_TIMEOUT")
    except Exception:
        await websocket.close(code=1011)


async def _run_stt_session(websocket: WebSocket, user):
    """Boucle de session. La fermeture de la session Deepgram
    est centralisée ici dans le finally — pas de double close."""
    provider = get_stt_provider()
    config = load_session_config(user)  # avec keyterms transversaux Phase 1
    session = await provider.create_session(config)
    
    idle_timeout = int(os.getenv("STT_SESSION_IDLE_TIMEOUT_SECONDS", "30"))
    max_duration = int(os.getenv("STT_SESSION_MAX_DURATION_SECONDS", "300"))
    warning_at = max_duration - 60  # alerte à 1min de la fin
    started_at = time.monotonic()
    warning_sent = False
    
    try:
        async def audio_pump():
            """Reçoit l'audio du client et le forwarde au provider.
            Ne ferme PAS la session Deepgram (centralisé en finally)."""
            nonlocal warning_sent
            while True:
                # Durée max session
                elapsed = time.monotonic() - started_at
                if elapsed >= max_duration:
                    raise STTSessionTimeoutError("Max session duration")
                
                # Alerte 1 min avant expiration
                if not warning_sent and elapsed >= warning_at:
                    await websocket.send_json({
                        "type": "session_warning",
                        "code": "EXPIRING_SOON",
                        "remaining_seconds": int(max_duration - elapsed)
                    })
                    warning_sent = True
                
                # Timeout idle sur réception audio
                try:
                    chunk = await asyncio.wait_for(
                        websocket.receive_bytes(),
                        timeout=idle_timeout
                    )
                except asyncio.TimeoutError:
                    raise STTSessionTimeoutError("Idle timeout")
                
                await session.send_audio(chunk)
        
        async def transcript_pump():
            async for t in session.receive_transcripts():
                await websocket.send_json({
                    "type": "transcript",
                    "text": t.text,
                    "is_final": t.is_final,
                    "confidence": t.confidence,
                })
        
        await asyncio.gather(audio_pump(), transcript_pump())
    
    except WebSocketDisconnect:
        pass  # client a fermé, on sort proprement
    finally:
        # FERMETURE CENTRALISÉE — un seul endroit
        await session.close()
```

**Notes** :
- L'acquisition du slot via `tracker.acquire()` est atomique (lock interne au tracker)
- Le `accept()` n'a lieu qu'après acquisition réussie → pas de close après accept sur 4429
- `session.close()` est appelé **une seule fois** dans le `finally` de `_run_stt_session` → pas de double close
- `WebSocketDisconnect` est attrapé pour finaliser proprement la session Deepgram

---

## 6. Compteur de sessions concurrentes

### 6.1 Principe

Compteur **séparé** du compteur HTTP `UserSession` existant (qui mesure la présence globale prof, reste inchangé).

Le compteur STT mesure uniquement les WebSockets STT actives.

### 6.2 Fichier `backend/stt/session_tracker.py`

**Pattern corrigé : un seul context manager atomique, pas de check séparé.**

```python
import asyncio
import os
from contextlib import asynccontextmanager
from .base import STTRateLimitError

class STTSessionTracker:
    def __init__(self, max_concurrent: int):
        self._active = 0
        self._max = max_concurrent
        self._lock = asyncio.Lock()
    
    # Lecture seule — pour l'admin dashboard uniquement
    async def get_active_count(self) -> int:
        return self._active
    
    async def get_max(self) -> int:
        return self._max
    
    @asynccontextmanager
    async def acquire(self):
        """Acquisition atomique d'un slot. Raise si saturé.
        À utiliser AVANT websocket.accept()."""
        async with self._lock:
            if self._active >= self._max:
                raise STTRateLimitError(
                    f"Max concurrent sessions reached ({self._max})"
                )
            self._active += 1
        try:
            yield
        finally:
            async with self._lock:
                self._active -= 1

_tracker = STTSessionTracker(
    max_concurrent=int(os.getenv("STT_MAX_CONCURRENT_SESSIONS", "40"))
)

def get_session_tracker() -> STTSessionTracker:
    return _tracker
```

**Important** : `get_active_count()` ne doit **jamais** être utilisé comme gate avant `acquire()`. C'est uniquement de la lecture pour affichage. La seule façon d'acquérir un slot, c'est `acquire()` — qui est atomique.

**Note multi-instance** : compteur en mémoire = OK pour mono-instance Docker actuel. Migration Redis si passage en multi-worker.

---

## 7. Monitoring du crédit Deepgram

### 7.1 Job périodique

Tâche planifiée (cron horaire) :

```
GET https://api.deepgram.com/v1/projects/{DEEPGRAM_PROJECT_ID}/balances
Authorization: Token {DEEPGRAM_API_KEY}
```

### 7.2 Logique

```python
def check_deepgram_credit():
    balance = fetch_deepgram_balance()
    
    # Source de vérité : table stt_credit_history (modifiable via admin V2)
    # avec fallback sur l'env var STT_INITIAL_CREDIT_USD
    total = get_current_credit_total_from_db() or float(
        os.getenv("STT_INITIAL_CREDIT_USD", "200")
    )
    threshold_pct = int(os.getenv("STT_CREDIT_ALERT_THRESHOLD_PCT", "10"))
    
    remaining_pct = (balance / total) * 100
    
    save_credit_snapshot(balance, remaining_pct)
    
    if remaining_pct <= threshold_pct and not already_alerted_today():
        send_admin_alert_email(balance, remaining_pct)
        # Active le mode "service en sursis" (bannière préventive)
        activate_preventive_user_message()
    
    if balance <= 0:
        activate_service_unavailable_mode()
```

### 7.3 Gestion des recharges (Phase 1 admin lecture seule, mais on prévoit la BDD)

Table `stt_credit_history` :
```sql
CREATE TABLE stt_credit_history (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(20) NOT NULL,  -- 'snapshot' | 'recharge' | 'reset'
    balance_usd DECIMAL(10,2),         -- pour les snapshots
    new_total_usd DECIMAL(10,2),       -- pour les recharges
    note TEXT,                         -- libre, ex: "recharge 500$ le 15/08/2026"
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id)  -- admin qui a fait l'action
);
```

**Phase 1** : seuls les snapshots horaires sont écrits automatiquement.
**Phase 2 admin V2** : bouton "Recharger crédit total" qui insère un événement `recharge`.

---

## 8. Interface admin — découpage MVP vs V2

### 8.1 MVP Phase 1 : page admin LECTURE SEULE

Une seule page `/admin/stt-status` accessible aux admins.

**Affichage** :
- Crédit Deepgram restant (montant + barre de progression %)
- Nombre de sessions STT actives (temps réel, rafraîchissement 5s)
- Nombre max de sessions configuré
- Jours restants avant expiration de la clé API
- Compteur transcriptions (jour / semaine / mois)
- Statut région (`us` en Phase 1, avec bannière d'alerte si pas encore migré)
- Historique des snapshots crédit (graphique simple sur 30 jours)

**Toute la configuration est dans `.env`** — pas d'édition en MVP.

### 8.2 V2 (post-pilotes) : édition admin

Quand le besoin sera prouvé par l'usage :

- Édition WYSIWYG des messages utilisateur
- Toggle entre mode `neutral` et mode `volume` (cf §9)
- Override des paramètres Deepgram (model, endpointing, dictation, etc.)
- Édition de la liste keyterms transversaux
- Gestion des keyterms par matière (logique adaptative §3.3)
- Bouton "Recharger crédit total" + saisie nouveau montant
- Bouton "Marquer clé API comme renouvelée" + nouvelle date

### 8.3 Alertes admin automatiques

**Dans le dashboard admin principal**, widgets d'alerte :

**Expiration clé API** :
- J-30 : info bleue
- J-15 : warning orange
- J-7 : alerte rouge + email quotidien automatique
- J-0 : alerte rouge bloquante + email quotidien

**Crédit Deepgram** :
- Seuil atteint (≤ 10% par défaut) : alerte rouge + email

**Région US active** (Phase 1) :
- Bannière permanente : *"Phase 1 — région Deepgram US active. Migration EU à planifier avant scale."*

---

## 9. Messages utilisateur

### 9.1 Stratégie deux modes

Stockés en BDD avec un toggle admin (cf §8.2). Deux jeux complets de messages :

**Mode `neutral`** : Phase 1 (5-20 profs pilotes). Pas de mention "forte affluence" — ce serait mensonger et contre-productif.

**Mode `volume`** : Phase 2+ (>100 profs actifs). Valorise la popularité de la plateforme.

Le mode actif est défini par la variable d'env `STT_MESSAGE_MODE=neutral` en Phase 1.

### 9.2 Mode `neutral` — Phase 1

**Message préventif** (crédit bientôt épuisé) :
> *"Information : le service de dictée vocale fera l'objet d'une intervention technique dans les prochains jours et pourrait être temporairement indisponible. Vous pouvez continuer à utiliser toutes les fonctionnalités normalement et saisir vos textes au clavier en attendant. Merci de votre compréhension."*

**Message d'indisponibilité** (crédit épuisé ou panne) :
> *"La dictée vocale est momentanément indisponible pour intervention technique. Vous pouvez continuer à préparer vos contenus en saisissant vos textes directement au clavier — toutes les autres fonctionnalités restent pleinement opérationnelles. Le service sera rétabli rapidement. Merci de votre compréhension."*

**Message de saturation ponctuelle** (max sessions atteint) :
> *"La dictée vocale est temporairement saturée. Veuillez patienter quelques instants et réessayer dans un moment, ou saisissez votre texte au clavier. Toutes les autres fonctionnalités restent disponibles."*

**Message expiration session** (timeout idle ou durée max) :
> *"Votre session de dictée a été interrompue après plusieurs minutes d'inactivité. Le texte déjà transcrit est conservé. Vous pouvez relancer une nouvelle dictée à tout moment."*

### 9.3 Mode `volume` — Phase 2+ (en réserve BDD)

**Message préventif** :
> *"Information : la dictée vocale rencontre actuellement une forte affluence en raison du grand nombre d'enseignants qui l'utilisent simultanément sur la plateforme. Le service pourrait être temporairement indisponible dans les prochains jours, le temps que nos équipes techniques augmentent la capacité d'accueil. Vous pouvez continuer à utiliser toutes les fonctionnalités normalement et saisir vos textes au clavier en attendant. Merci de votre patience et bonne continuation dans vos préparations."*

**Message d'indisponibilité** :
> *"La dictée vocale est momentanément indisponible en raison du grand nombre d'enseignants connectés actuellement sur la plateforme. Nos équipes techniques travaillent à augmenter la capacité pour que chacun puisse en profiter pleinement. En attendant, vous pouvez continuer à préparer vos contenus en saisissant vos textes directement au clavier — toutes les autres fonctionnalités restent pleinement opérationnelles. Le service de dictée sera rétabli rapidement. Merci de votre compréhension."*

**Message de saturation** :
> *"La dictée vocale est très sollicitée en ce moment par les nombreux enseignants connectés. Veuillez patienter quelques instants et réessayer dans une minute, ou saisissez votre texte directement au clavier. Toutes les autres fonctionnalités restent disponibles. Merci de votre compréhension."*

### 9.4 Schéma BDD

```sql
CREATE TABLE stt_messages (
    id SERIAL PRIMARY KEY,
    mode VARCHAR(20) NOT NULL,   -- 'neutral' | 'volume'
    code VARCHAR(50) NOT NULL,   -- 'preventive' | 'unavailable' | 'saturation' | 'session_expired'
    content TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(mode, code)
);
```

Le backend récupère le bon message selon `STT_MESSAGE_MODE` + le code de la situation.

---

## 10. Frontend — composant dictée

### 10.1 Remplacement de `webkitSpeechRecognition`

Composant existant entièrement remplacé.

### 10.2 Stack technique

- `MediaRecorder` API
- Format audio : Opus, 16 kHz, mono
- Chunks : `mediaRecorder.start(250)` (250ms)
- WebSocket vers `/api/transcribe/stream`

**⚠️ Compatibilité iOS PWA** (cf §15.2) : MediaRecorder Opus non garanti sur Safari iOS. Tester avant de cibler iOS. Fallback gracieux si non supporté : bouton micro grisé + tooltip *"Dictée vocale non disponible sur ce navigateur pour le moment."*

### 10.3 États du bouton micro

| État | Apparence | Action |
|---|---|---|
| Disponible | Icône micro normale | Démarre l'enregistrement |
| En cours | Icône stop + pulsation | Arrête l'enregistrement |
| Saturé (4429) | Grisé + tooltip | Toast saturation |
| Indisponible (4402/4502) | Grisé + tooltip | Message indisponibilité |
| Timeout (4408) | Reset à disponible | Toast info |
| Non supporté (iOS, etc.) | Grisé permanent | Tooltip explicatif |

### 10.4 Flux utilisateur

1. Clic micro → demande permission micro navigateur
2. Ouverture WebSocket `/api/transcribe/stream`
3. Si refus serveur : afficher message approprié selon code WS, abandon
4. Si OK : `MediaRecorder.start(250)`
5. `ondataavailable` → `ws.send(blob)`
6. Réception message JSON :
   - `type: "transcript"` → afficher dans champ texte (interim en gris/italique, final en noir)
   - `type: "session_warning"` → toast info "Votre session expire dans X secondes"
7. Clic stop : `MediaRecorder.stop()` → flush dernier chunk → close WS (1000)
8. Texte final inséré dans champ principal

### 10.5 Gestion des erreurs

Pas d'erreurs techniques 500 au prof. Tous les codes WS mappés vers messages user-friendly (§9). Logs détaillés backend pour debug admin.

---

## 11. Sécurité

### 11.1 Règles strictes

- Clé API uniquement côté serveur (variable d'env)
- Jamais dans frontend, code committé, logs
- Jamais dans screenshots, documents partagés, tickets
- Notation bracket dans toute documentation : `[DEEPGRAM_API_KEY]`, `[DEEPGRAM_PROJECT_ID]`
- `.env` chiffré sur VPS, `.gitignore` strict

### 11.2 Rotation de la clé API

**Politique** : tous les 90 jours.

**Procédure** :
1. Créer nouvelle clé sur dashboard Deepgram (rôle Default)
2. Mettre à jour `DEEPGRAM_API_KEY` dans `.env`
3. Mettre à jour `DEEPGRAM_API_KEY_EXPIRES_AT`
4. Redémarrer backend
5. Supprimer ancienne clé du dashboard Deepgram
6. (V2) Bouton admin "Marquer comme renouvelée"

**Rappels automatiques** : §8.3 (J-30, J-15, J-7, J-0).

### 11.3 Rôle clé

Toujours **Default** (permission minimale `usage:write`). Jamais Member, Admin ou Owner.

---

## 12. Tests

### 12.1 Étape 0 — Validation préalable (cf §0)

Tests wscat/script jetable AVANT codage de l'abstraction. Critères §0.2.

### 12.2 Tests fonctionnels manuels (après dev)

- [ ] Énoncé mathématique ("Soit P de x égal à...")
- [ ] Nom propre scientifique ("Lavoisier", "Avogadro")
- [ ] Consigne pédagogique ("Justifiez votre réponse")
- [ ] Coupure réseau pendant dictée
- [ ] Saturation (forcer `STT_MAX_CONCURRENT_SESSIONS=1`, ouvrir 2 sessions)
- [ ] Crédit épuisé (simuler via clé invalide ou mock)
- [ ] Timeout idle (clic micro + attendre 30s sans parler)
- [ ] Durée max session (forcer `STT_SESSION_MAX_DURATION_SECONDS=10` et parler longtemps)
- [ ] Alerte "session expire bientôt" reçue côté client
- [ ] États visuels bouton micro corrects dans chaque cas
- [ ] Messages mode `neutral` affichés correctement
- [ ] iOS PWA — détection support MediaRecorder Opus + fallback grisé

### 12.3 Tests admin

- [ ] Affichage page `/admin/stt-status` correct
- [ ] Compteur sessions actives temps réel
- [ ] Affichage rappels J-30 / J-15 / J-7 / J-0 (forcer date d'expiration)
- [ ] Alerte région US visible

---

## 13. Évolutions futures (hors scope Phase 1)

### 13.1 V2 admin — édition

Cf §8.2 — édition WYSIWYG messages, override paramètres, gestion keyterms.

### 13.2 Keyterms adaptatifs par matière

Cf §3.3 — basculer de la liste transversale unique vers l'injection adaptative selon la matière du prof. Structure BDD déjà prête.

### 13.3 Option utilisateur "Mode dictée ponctuation"

Champ booléen dans `user_preferences` :
- ☐ Je dicte la ponctuation à voix haute
- ☑ Le système ajoute la ponctuation automatiquement

Lu à la création de session pour surcharger `dictation`.

### 13.4 Multi-provider et fallback

Implémenter `AzureProvider` (région France), `SpeechmaticsProvider`, `OVHcloudProvider` quand :
- Exigence RGPD/EU d'un client
- Plainte qualité Deepgram
- Marketing souveraineté

Système de fallback automatique : si provider principal échoue → secondaire (config admin).

### 13.5 Benchmark formel

Spec déjà esquissée (corpus 30 échantillons, métriques WER + CTA). À activer quand décision provider scale à prendre.

### 13.6 Migration Redis

Si passage multi-instance backend → migrer le compteur de sessions vers Redis.

### 13.7 Bascule mode `volume` → `neutral`

Toggle admin pour passer du mode `neutral` (Phase 1) au mode `volume` quand le volume de profs le justifie (>100 actifs).

---

## 14. Ordre d'implémentation recommandé

0. **Étape 0 — validation préalable wscat/script jetable** (§0)
1. `backend/stt/base.py` — interfaces, dataclasses, exceptions
2. `backend/stt/session_tracker.py` — compteur avec `acquire()` atomique
3. `backend/stt/deepgram_provider.py` — wrapper Deepgram (SDK `deepgram-sdk`)
4. `backend/stt/__init__.py` — factory
5. `backend/routers/transcribe_stream.py` — endpoint WebSocket avec gestion timeouts
6. Schémas BDD : `stt_credit_history`, `stt_messages`, `stt_keyterms_global`, `stt_keyterms_by_subject`
7. Tests manuels backend via wscat
8. Frontend — remplacement composant dictée
9. Tests bout-en-bout dans Edge avec voix réelle
10. Test iOS PWA — détection MediaRecorder Opus + fallback
11. Page admin `/admin/stt-status` (lecture seule)
12. Job cron monitoring crédit Deepgram
13. Système rappels expiration clé API
14. Tests d'intégration admin

---

## 15. Annexes

### 15.1 Dépendances Python à ajouter

```
deepgram-sdk>=3.0
```

### 15.2 Compatibilité iOS / PWA

Le projet est installé en PWA iOS. Sur Safari iOS, `MediaRecorder` est supporté mais le codec Opus n'est pas garanti (souvent `mp4`/`aac` uniquement).

**Stratégie** : détection à l'initialisation du composant frontend.
```javascript
const supportsOpus = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                  || MediaRecorder.isTypeSupported('audio/ogg;codecs=opus');
```

Si non supporté → bouton micro désactivé permanent + tooltip explicatif. Pas de tentative de fallback codec en Phase 1 (Deepgram accepte d'autres codecs mais ça multiplie les chemins de test).

### 15.3 Documentation Deepgram

- API streaming : https://developers.deepgram.com/reference/streaming
- SDK Python : https://github.com/deepgram/deepgram-python-sdk
- Modèles : https://developers.deepgram.com/docs/models-languages-overview

### 15.4 Récap éléments configurables — Phase 1 vs V2

**Phase 1 MVP — uniquement via `.env`**
- Tous les paramètres Deepgram (model, language, smart_format, endpointing, dictation, etc.)
- Limites concurrence et timeouts
- Seuil d'alerte crédit
- Crédit initial total
- Mode messages (`neutral` / `volume`)
- Région Deepgram

**Phase 1 MVP — interface admin lecture seule**
- Vue d'ensemble crédit, sessions actives, expiration clé
- Historique snapshots crédit
- Alertes automatiques (expiration clé, seuil crédit, région US)

**V2 — édition admin**
- Messages utilisateur (WYSIWYG)
- Toggle mode messages
- Override paramètres Deepgram
- Édition keyterms transversaux
- Gestion keyterms par matière
- Recharge crédit + historique modifications
- Renouvellement clé API

---

## 16. Annexe — Alternative étudiée : Whisper auto-hébergé

### 16.1 Contexte

Une alternative à Deepgram a été évaluée : héberger un moteur STT **Whisper open source** directement sur le VPS, pour éliminer la dépendance cloud et la facturation à l'usage.

### 16.2 Technologies envisagées

- **whisper.cpp** : implémentation C++ optimisée CPU
- **faster-whisper** : implémentation Python optimisée (CTranslate2)
- **whisper-streaming / WhisperLive** : variantes pour pseudo-streaming temps réel

### 16.3 Limites identifiées

- Whisper entraîné sur segments de 30s : pas de vrai streaming natif, pseudo-streaming dégrade l'UX (latence 2-5s par bloc au lieu de <300ms first-token chez Deepgram)
- Charge CPU/RAM significative sur VPS partagé : `medium` ≈ 5 GB RAM et plafonne vers 30-50 profs simultanés sur CPU
- Pour performances proches de Deepgram, VPS GPU dédié nécessaire (~200€/mois)

### 16.4 Comparaison économique (hypothèse 1000 profs × 5 dictées/jour × 30s = 4 380h audio/an)

| Critère | Deepgram (cloud) | Whisper local CPU | Whisper local GPU |
|---|---|---|---|
| Coût annuel | ~1 050€ | ~360€ (VPS upgrade) | ~2 400€ (VPS GPU) |
| Latence | ★★★★★ | ★★ | ★★★★ |
| Qualité FR | ★★★★★ | ★★★★ | ★★★★★ |
| Maintenance | ★★★★★ | ★ | ★ |
| Scale automatique | ★★★★★ | ★★ | ★★ |
| RGPD souverain | ★★ | ★★★★★ | ★★★★★ |
| Temps d'implémentation | ~1 semaine | 3-4 semaines | 4-6 semaines |

### 16.5 Décision Phase 1

**Deepgram cloud retenu** :
- Économie locale illusoire (CPU = scale limité ; GPU = plus cher que Deepgram)
- 2-4 semaines de dev économisées et réinvesties sur le métier
- Maintenance déléguée
- L'abstraction `STTProvider` laisse la porte ouverte à un `WhisperLocalProvider` futur

### 16.6 Déclencheurs pour reconsidérer Whisper local

- Appel d'offres public exigeant hébergement souverain (et aucune API EU mature disponible)
- Volume mensuel Deepgram dépassant 500€ avec croissance continue
- Recrutement d'un ingé infra dédié
- Cas d'usage offline identifié

---

**Fin de la spécification — Version 1.1**
