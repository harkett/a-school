"""Extract Deepgram STT_MEASURE metrics from uvicorn logs (Phase 3.2).

Usage:
    python extract_measurements.py [logfile]
    # ou via stdin :
    Get-Content uvicorn.log | python extract_measurements.py

Filtre les events `speech_final` (cf. BOUSSOLE/D09/protocole_phase32.md §2.1),
exclut les `is_final` intermédiaires de l'agrégation latence d'endpointing.
"""
import re
import statistics
import sys

STT_RE = re.compile(
    r"STT_MEASURE event=(?P<event>\w+) "
    r"delta_audio_ms=(?P<audio>\S+) "
    r"delta_interim_ms=(?P<interim>\S+) "
    r"text=(?P<text>.+?) last_interim="
)


def parse_lines(lines):
    speech_finals = []
    is_finals = []
    for line in lines:
        m = STT_RE.search(line)
        if not m:
            continue
        event = m.group("event")
        interim_raw = m.group("interim")
        text = m.group("text").strip("'\"")
        try:
            interim_ms = int(interim_raw)
        except ValueError:
            interim_ms = None
        entry = {"interim_ms": interim_ms, "text": text}
        if event == "speech_final":
            speech_finals.append(entry)
        elif event == "is_final":
            is_finals.append(entry)
    return speech_finals, is_finals


def report(speech_finals, is_finals):
    print(f"speech_final count                  : {len(speech_finals)}")
    print(f"is_final intermediaires (exclus)    : {len(is_finals)}")

    deltas = [e["interim_ms"] for e in speech_finals if e["interim_ms"] is not None]
    if not deltas:
        print("\nAucune mesure delta_interim_ms exploitable.")
        return

    print(f"\nDelta_interim_ms (speech_finals uniquement) :")
    print(f"  count   : {len(deltas)}")
    print(f"  min     : {min(deltas)}")
    print(f"  median  : {statistics.median(deltas):.0f}")
    print(f"  mean    : {statistics.mean(deltas):.0f}")
    print(f"  max     : {max(deltas)}")
    if len(deltas) >= 4:
        print(f"  stdev   : {statistics.stdev(deltas):.0f}")

    print(f"\n-> Mediane retenue pour verdict pivot endpointing : {statistics.median(deltas):.0f} ms")

    print(f"\nListe complète des speech_finals (ordre log) :")
    for i, e in enumerate(speech_finals, 1):
        delta = f"{e['interim_ms']:>5} ms" if e["interim_ms"] is not None else "  n/a"
        print(f"  [{i:2}] {delta} — {e['text']}")


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()
    speech_finals, is_finals = parse_lines(lines)
    report(speech_finals, is_finals)


if __name__ == "__main__":
    main()
