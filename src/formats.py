from datetime import date


def to_markdown(activite: str, niveau: str, contenu: str) -> str:
    titres = {
        "comprehension": "Questions de compréhension",
        "pistes": "Pistes de lecture",
        "reecriture": "Exercice de réécriture",
    }
    titre = titres.get(activite, activite.capitalize())
    today = date.today().strftime("%d/%m/%Y")

    return f"""# {titre}

**Niveau :** {niveau}
**Date :** {today}

---

{contenu}
"""


def save(content: str, path: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
