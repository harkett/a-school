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


def build_proposer_idee_prompt(chunks: list[dict], type_label: str, precision: str | None, niveau: str) -> str:
    """Prompt — propose UNE idée d'activité, formulée comme la DEMANDE COURTE que le prof
    écrirait lui-même dans la zone texte (c'est là qu'elle atterrit : le prof la relit, la
    modifie, puis « Générer » la réalise). Donc : PAS l'activité complète, PAS de mise en
    forme (la zone n'affiche que du texte brut) — la seule aération permise est la ligne
    vide entre 2-3 petits paragraphes (matériel → déroulement → objectif), pour que la
    demande se relise d'un coup d'œil. La réponse s'ouvre sur UNE ligne « Objet : titre
    court » que le serveur détache (_extraire_objet) pour remplir le champ Objet de
    l'écran. Ancré sur les extraits du référentiel du niveau."""
    refs = []
    for c in chunks:
        page = c.get("page", "?")
        refs.append(f"[Référentiel {niveau}, p.{page}]\n{(c.get('text') or '').strip()}")
    bloc = "\n\n".join(refs)
    quoi = f"« {type_label} »" + (f" (précision : {precision})" if precision else "")
    return (
        f"Tu es enseignant·e pour le niveau « {niveau} ».\n\n"
        f"Un professeur a choisi le type d'activité {quoi} et cherche une idée de départ.\n"
        f"À partir des EXTRAITS du référentiel officiel ci-dessous, propose UNE idée d'activité "
        f"pour ce type d'activité, écrite comme la demande que le professeur taperait lui-même : "
        f"2 à 4 phrases concrètes (thème, support ou matériel, intention pédagogique), à la "
        f"première personne ou à l'infinitif.\n"
        f"Présentation : commence par UNE première ligne « Objet : » suivie d'un titre très court "
        f"(3 à 8 mots) pour retrouver l'activité facilement, puis une ligne vide, puis la demande "
        f"aérée en 2 ou 3 petits paragraphes séparés par une ligne vide — d'abord le matériel ou "
        f"le support, puis le déroulement, puis l'objectif pédagogique.\n"
        f"Contraintes : reste dans le périmètre du référentiel ; ne rédige PAS l'activité complète ; "
        f"AUCUN titre, AUCUNE liste, AUCUNE autre mise en forme que ces lignes vides — uniquement "
        f"le texte de la demande.\n\n"
        f"## Extraits du référentiel officiel — {niveau}\n\n{bloc}\n\n"
        f"## Idée d'activité à proposer\n"
    )
