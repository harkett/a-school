"""Découpage d'une séance générée (markdown) en phases structurées.

Le prompt (llm_prompts) impose « ## Phase N — Nom (X min) » : on s'appuie sur CE contrat,
avec tolérance sur le tiret (—, –, -), la casse et une durée absente. Tout ce qui suit
l'en-tête d'une phase jusqu'à la suivante (ou le séparateur de fin) est son contenu,
conservé tel quel (markdown).

Un texte sans phase reconnaissable → liste vide : la séance garde son `resultat` complet
(seule source d'affichage), le découpage est un plus structurel — jamais un préalable.

PARTAGÉ (zéro copie) entre la sauvegarde à la génération (sequence.py) et l'import des
anciennes « séquences » en séances (migration alembic b4d8f0e2c6a3).
"""
import re

_RE_PHASE = re.compile(
    r"^##\s*Phase\s*(\d+)\s*[—–-]\s*(.+?)\s*(?:\((\d+)\s*min[^)]*\))?\s*$",
    re.IGNORECASE,
)


def decouper_phases(texte: str) -> list[dict]:
    """Retourne [{position, titre, duree_minutes, contenu}, …] dans l'ordre du texte."""
    phases = []
    courante = None       # phase en cours de remplissage
    lignes_contenu = []

    def clore():
        if courante is not None:
            courante["contenu"] = "\n".join(lignes_contenu).strip()
            phases.append(courante)

    for ligne in str(texte or "").replace("\r\n", "\n").split("\n"):
        m = _RE_PHASE.match(ligne.strip())
        if m:
            clore()
            courante = {
                "position": int(m.group(1)),
                "titre": m.group(2).strip()[:300],
                "duree_minutes": int(m.group(3)) if m.group(3) else None,
            }
            lignes_contenu = []
        elif courante is not None:
            # Le séparateur de fin (---) ou un nouveau titre de niveau 1/2 clôt la dernière phase.
            strip = ligne.strip()
            if re.match(r"^-{3,}$", strip) or strip.startswith("# ") or strip.startswith("## "):
                clore()
                courante = None
                lignes_contenu = []
            else:
                lignes_contenu.append(ligne)
    clore()

    # Positions dédoublonnées par ordre d'apparition (un LLM peut numéroter faux) :
    # l'ordre du TEXTE fait foi, la position est réécrite en séquence 1..n.
    for i, ph in enumerate(phases, start=1):
        ph["position"] = i
    return phases
