"""Assemblage des prompts qui ne sont pas de simples gabarits.

Les TEXTES vivent en base (registre `llm_prompts.PROMPTS`, semés par migration, lus par
`get_prompt`) — plus aucune consigne rédigée ici. Ce fichier ne garde que le GESTE : mettre en
forme les extraits ramenés par le RAG, composer la partie conditionnelle d'une phrase, coller le
cahier des charges à la fin d'un prompt. C'est de l'assemblage, pas de la rédaction.
"""
from sqlalchemy.orm import Session

from backend.systeme.admin import get_prompt


def _bloc_referentiel(chunks: list[dict], niveau: str) -> str:
    """Les extraits du programme officiel, mis en forme pour être collés dans un prompt : un
    bloc par extrait, précédé de sa provenance (niveau + page) pour que le modèle sache d'où
    vient ce qu'il lit. Mise en forme, pas consigne — d'où le maintien dans le code."""
    refs = []
    for c in chunks:
        page = c.get("page", "?")
        refs.append(f"[Référentiel {niveau}, p.{page}]\n{(c.get('text') or '').strip()}")
    return "\n\n".join(refs)


def ajouter_cahier_au_prompt(db: Session, prompt: str, cahier_txt: str) -> str:
    """Ajoute le texte du cahier des charges du prof à la FIN d'un prompt de génération, sous un
    intitulé clair — les règles de l'école s'appliquent PAR-DESSUS le programme officiel. Texte de
    cahier VIDE (ou pas de cahier) → prompt renvoyé INCHANGÉ, génération strictement identique. UN
    seul endroit pour ce geste : générer, « Document d'exemple » et « Propose-moi une idée » l'appellent
    tous. Concaténation (pas de .format) : le cahier est une VALEUR, ses accolades ne sont jamais parsées.

    L'intitulé est LU EN BASE (`entete_cahier`) : il porte la décision de priorité entre les
    règles de l'école et le programme officiel, elle n'a pas à vivre dans une constante Python."""
    cahier_txt = (cahier_txt or "").strip()
    if not cahier_txt:
        return prompt
    return prompt + "\n\n" + get_prompt(db, "entete_cahier") + "\n" + cahier_txt


def build_exemple_referentiel_prompt(db: Session, chunks: list[dict], matiere: str, niveau: str) -> str:
    """Prompt — génère un TEXTE SOURCE ancré sur le référentiel officiel du couple
    matière+niveau, destiné à servir de point de départ d'activité (PAS une liste de
    compétences recopiée).

    Le prompt CONTIENT les extraits du référentiel + le niveau : c'est précisément
    ce qui garantit — et ce que le test prouve — que la génération est ancrée sur le
    bon couple, pas inventée hors-sujet."""
    return get_prompt(db, "exemple_referentiel").format(
        matiere=matiere, niveau=niveau, referentiel=_bloc_referentiel(chunks, niveau),
    )


def build_ambiguite_exemple_prompt(db: Session, chunks: list[dict], matiere: str, niveau: str,
                                  criteres: str) -> str:
    """Prompt — écrit à la demande du prof UN énoncé d'exemple VOLONTAIREMENT IMPARFAIT pour son
    couple, ancré sur les extraits de son référentiel.

    Même geste que `build_exemple_referentiel_prompt` : les extraits entrent dans le prompt, et
    c'est précisément ce qui empêche l'énoncé de partir dans une autre discipline que celle du
    couple. `criteres` est composé par l'appelant (catalogue lu en base, critère libre écarté).
    """
    return get_prompt(db, "ambiguite_exemple_genere").format(
        matiere=matiere, niveau=niveau, criteres=criteres,
        referentiel=_bloc_referentiel(chunks, niveau),
    )


def build_proposer_idee_prompt(db: Session, chunks: list[dict], type_label: str,
                               precision: str | None, niveau: str) -> str:
    """Prompt — propose UNE idée d'activité, formulée comme la DEMANDE COURTE que le prof
    écrirait lui-même dans la zone texte (c'est là qu'elle atterrit : le prof la relit, la
    modifie, puis « Générer » la réalise). Donc : PAS l'activité complète, PAS de mise en
    forme (la zone n'affiche que du texte brut) — la seule aération permise est la ligne
    vide entre 2-3 petits paragraphes (matériel → déroulement → objectif), pour que la
    demande se relise d'un coup d'œil. La réponse s'ouvre sur UNE ligne « Objet : titre
    court » que le serveur détache (_extraire_objet) pour remplir le champ Objet de
    l'écran. Ancré sur les extraits du référentiel du niveau.

    `quoi` est composé ici parce qu'il est CONDITIONNEL (la précision n'existe pas toujours) :
    un gabarit ne sait pas dire « seulement si le prof a rempli ce champ »."""
    quoi = f"« {type_label} »" + (f" (précision : {precision})" if precision else "")
    return get_prompt(db, "proposer_idee").format(
        quoi=quoi, niveau=niveau, referentiel=_bloc_referentiel(chunks, niveau),
    )
