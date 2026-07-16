def build_exemple_referentiel_prompt(chunks: list[dict], matiere: str, niveau: str) -> str:
    """Prompt — génère un TEXTE SOURCE ancré sur le référentiel officiel du couple
    matière+niveau, destiné à servir de point de départ d'activité (PAS une liste de
    compétences recopiée).

    Le prompt CONTIENT les extraits du référentiel + le niveau : c'est précisément
    ce qui garantit — et ce que le test prouve — que la génération est ancrée sur le
    bon couple, pas inventée hors-sujet."""
    refs = []
    for c in chunks:
        page = c.get("page", "?")
        refs.append(f"[Référentiel {niveau}, p.{page}]\n{(c.get('text') or '').strip()}")
    bloc = "\n\n".join(refs)
    return (
        f"Tu es enseignant·e en {matiere} pour le niveau « {niveau} ».\n\n"
        f"À partir des EXTRAITS du référentiel officiel ci-dessous, rédige un TEXTE SOURCE "
        f"court et concret (énoncé, situation professionnelle, document de travail) "
        f"directement exploitable comme point de départ d'une activité pour ce niveau.\n"
        f"Contraintes : reste dans le périmètre du référentiel ; ne recopie PAS la liste de "
        f"compétences ; produis un vrai contenu (contexte, données, consigne), pas un sommaire.\n\n"
        f"## Extraits du référentiel officiel — {matiere}, {niveau}\n\n{bloc}\n\n"
        f"## Texte source à rédiger\n"
    )
