"""
Test d'intégration DeepgramProvider — clôt Phase 0.2 + valide Phase 1.5.

Ce script :
1. Crée un DeepgramProvider (lit DEEPGRAM_API_KEY depuis .env)
2. Ouvre une session streaming réelle vers Deepgram
3. Envoie un fichier audio FR (test_audio.wav, 16 kHz mono linear16)
4. Affiche les transcripts reçus en streaming
5. Vérifie les termes critiques (polynôme, Lavoisier, hypoténuse)

Usage :
    1. Avoir un test_audio.wav (16 kHz mono PCM 16-bit) contenant la phrase :
       "Soit P de x égal à deux x au carré moins cinq, déterminez les racines
        du polynôme. L'hypoténuse du triangle est égale à cinq. Lavoisier
        disait : rien ne se perd, rien ne se crée."
    2. python test_deepgram_provider.py

Critères de succès :
    - 3 termes critiques transcrits → Phase 0.2 + 1.5 VALIDÉES
    - 2/3 → partiel, investiguer le manquant
    - <2/3 → ÉCHEC, revoir le provider
"""

import asyncio
import logging
import sys
from pathlib import Path

# Permet d'importer backend.* depuis la racine
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from backend.stt.base import STTSessionConfig
from backend.stt.deepgram_provider import DeepgramProvider

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s : %(message)s")

AUDIO_FILE = Path(__file__).parent / "test_audio.wav"
CHUNK_SIZE = 8000  # ~250ms à 16 kHz mono 16-bit (16000 * 2 * 0.25 = 8000)
WAV_HEADER_SIZE = 44

CRITICAL_TERMS = ["polynôme", "Lavoisier", "hypoténuse"]


async def main() -> int:
    if not AUDIO_FILE.exists():
        print(f"[FAIL] Fichier audio manquant : {AUDIO_FILE}")
        print("   Crée un WAV 16 kHz mono 16-bit PCM avec la phrase de test (cf. docstring).")
        return 1

    print("=" * 60)
    print("  Test d'intégration DeepgramProvider")
    print("=" * 60)
    print(f"  Audio : {AUDIO_FILE.name}")
    print(f"  Modèle : nova-3 (config par défaut)")
    print()

    provider = DeepgramProvider()
    config = STTSessionConfig(
        language="fr",
        sample_rate=16000,
        encoding="linear16",
        interim_results=True,
        smart_format=True,
        endpointing_ms=800,
        dictation=False,
        # keyterms : chargés automatiquement depuis BDD par le provider
    )

    try:
        session = await provider.create_session(config)
    except Exception as e:
        print(f"[FAIL] Échec ouverture session : {e}")
        return 1

    transcripts_final: list[str] = []
    transcripts_interim: list[str] = []

    async def receive_loop() -> None:
        async for t in session.receive_transcripts():
            if t.is_final:
                transcripts_final.append(t.text)
                print(f"  [FINAL]   {t.text}")
            else:
                transcripts_interim.append(t.text)
                print(f"  [interim] {t.text}")

    async def send_loop() -> None:
        with open(AUDIO_FILE, "rb") as f:
            f.read(WAV_HEADER_SIZE)  # skip WAV header
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                await session.send_audio(chunk)
                await asyncio.sleep(0.25)  # simule streaming temps réel
        # Attente courte pour laisser Deepgram envoyer les derniers transcripts
        await asyncio.sleep(2.0)
        await session.close()

    # Lance les 2 boucles en parallèle (receive d'abord, send ensuite via gather)
    try:
        await asyncio.gather(receive_loop(), send_loop())
    except Exception as e:
        print(f"\n[FAIL] Erreur pendant le streaming : {e}")
        return 1

    # Vérification finale
    full_text = " ".join(transcripts_final).lower()
    print()
    print("=" * 60)
    print(f"  Transcript final concaténé : {full_text}")
    print("=" * 60)
    print()

    found = {term: term.lower() in full_text for term in CRITICAL_TERMS}
    success_count = sum(found.values())

    print("  Vérification termes critiques :")
    for term, ok in found.items():
        status = "[OK]" if ok else "[FAIL]"
        print(f"    {status} {term}")
    print()

    if success_count == 3:
        print("  [PASS] Phase 0.2 + Phase 1.5 VALIDÉES")
        print("     → DeepgramProvider fonctionnel, vocabulaire pédagogique OK")
        return 0
    elif success_count >= 2:
        print(f"  [WARN] Partiel ({success_count}/3) — investiguer le terme manquant")
        return 0
    else:
        print(f"  [FAIL] ÉCHEC ({success_count}/3) — debug avant de continuer")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
