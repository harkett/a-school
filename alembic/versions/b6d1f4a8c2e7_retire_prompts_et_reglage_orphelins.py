# -*- coding: utf-8 -*-
"""retire les 3 prompts et le reglage max_tokens de l'outil demoli le 30/07

CE QUI PART, ET POURQUOI. Le monde « sequences » d'avant a ete demoli le 30/07/2026. Trois
prompts et un reglage lui ont survecu, sans consommateur : releve fait sur TOUS les appels a
`get_prompt` et `get_max_tokens` du backend.

    prompt_sequence_standard      aucun appelant
    prompt_sequence_remediation   aucun appelant
    prompt_optimiseur             aucun appelant
    max_tokens_optimiseur         aucun appelant

Ce n'etait pas seulement du poids mort. L'ecran admin proposait un champ « Surcharge —
Optimiseur de sequences » : l'admin y saisissait une valeur, elle s'enregistrait, elle ne
servait a rien. Un reglage qui ment est pire qu'un reglage absent — il donne l'impression
d'agir.

ATTENTION AUX HOMONYMES, c'est le piege de ce menage : `sequence_generer_plan`,
`sequence_proposer_objectif`, `sequence_proposer_competences` et le reglage
`max_tokens_sequence` (2 appelants reels, backend/contenu/mes_contenus.py) sont VIVANTS. Le
prefixe `sequence` ne dit rien ; seul le releve des appels le dit.

CE QUE FAIT LE DOWNGRADE, ET CE QU'IL NE PEUT PAS FAIRE. Il remet les quatre lignes : les
trois textes GELES ci-dessous (recopies verbatim de b8e5f2a1c9d7, jamais importes du registre
— une migration doit dire ce qui etait vrai le jour ou elle a ete ecrite) et
`max_tokens_optimiseur` a sa valeur de semis, "6000".

Ce qu'il ne rend pas : les RETOUCHES. Si un admin avait reecrit l'un de ces prompts ou change
le nombre de tokens, l'upgrade a supprime sa version et rien ne peut l'inventer. Le downgrade
rend l'etat d'ORIGINE, pas l'etat d'avant l'upgrade. C'est irreversible par nature, et c'est
assume : ces valeurs ne servaient a rien, personne ne les lisait, et les garder au cas ou
aurait fige indefiniment un mensonge dans l'ecran admin.

Revision ID: b6d1f4a8c2e7
Revises: a5e9c3b7f1d2
Create Date: 2026-08-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b6d1f4a8c2e7"
down_revision: Union[str, Sequence[str], None] = "a5e9c3b7f1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Lu par tests/test_prompts_en_base.py, qui rejoue la chaine des migrations pour verifier que
# le registre et la base disent la meme chose. `PROMPTS_MAJ` annonce des textes ajoutes ou
# modifies ; `PROMPTS_RETIRES` annonce des cles qui SORTENT — sans quoi le test signalerait
# comme « semees mais absentes du registre » trois lignes qu'on vient justement d'enlever.
PROMPTS_RETIRES = ["sequence_standard", "sequence_remediation", "optimiseur"]

# Textes GELES au 02/08/2026, recopies de b8e5f2a1c9d7 (verifie identiques au registre avant
# retrait). Ils ne servent QU'AU DOWNGRADE.
TEXTES_ORIGINE = {
    # l'ancien generateur de sequences, mode standard
    'sequence_standard': 'Tu es un expert en ingénierie pédagogique pour l\'enseignement secondaire français (collège et lycée, 6e à Terminale).\n\nUn enseignant de {matiere}, niveau {niveau}, prépare une séance de {duree} minutes sur :\n"{theme}"\n\nGénère une séance pédagogique complète, cohérente et directement utilisable en classe.\n\nStructure attendue : 5 à 6 phases couvrant exactement {duree} minutes.\nProgression conseillée : Activation → Exploration/Découverte → Structuration/Formalisation → Entraînement → Ancrage/Consolidation.\n\nFormat de réponse — markdown strict :\n\n# Séance : [titre court reprenant le thème]\n**Matière :** {matiere} | **Niveau :** {niveau} | **Durée :** {duree} min\n\n---\n\n## Phase 1 — [Nom] ([X] min)\n**Objectif :** [Ce que les élèves construisent ou réalisent]\n**Déroulement :** [Description concrète — ce que fait le prof, ce que font les élèves]\n**Organisation :** [Individuel / Binôme / Groupe / Collectif]\n\n## Phase 2 — [Nom] ([X] min)\n**Objectif :** ...\n**Déroulement :** ...\n**Organisation :** ...\n\n[…continuer jusqu\'à la dernière phase]\n\n---\n\n> *Séance générée par aSchool*\n\nRègles absolues :\n- La somme des durées des phases = exactement {duree} minutes\n- Chaque phase a un rôle clair et distinct dans la progression\n- Le déroulement est concret, précis et directement applicable en classe\n- Le contenu est adapté au niveau {niveau} et à la matière {matiere}\n- Aucune phase sans lien direct avec le thème "{theme}"\n- Répondre uniquement en markdown, rien d\'autre avant ni après le markdown',

    # l'ancien generateur de sequences, mode remediation
    'sequence_remediation': 'Tu es un expert en ingénierie pédagogique pour l\'enseignement secondaire français.\n\nUn enseignant de {matiere}, niveau {niveau}, décrit la situation de sa classe :\n"{description_classe}"\n\nLa notion à retravailler est : "{theme}"\nDurée disponible : {duree} minutes\n\nGénère un scénario de remédiation créatif qui :\n1. Exploite la situation décrite (difficultés, contexte, centres d\'intérêt) comme point d\'accroche\n2. Cible précisément la notion à consolider\n3. Propose une approche différente de la présentation initiale, plus engageante\n4. Alterne entre phases courtes pour maintenir l\'attention\n\nFormat de réponse — markdown strict :\n\n# Remédiation : [titre court lié à la notion et au contexte]\n**Matière :** {matiere} | **Niveau :** {niveau} | **Durée :** {duree} min\n\n---\n\n## Phase 1 — [Nom] ([X] min)\n**Objectif :** ...\n**Déroulement :** ...\n**Organisation :** ...\n\n[…continuer jusqu\'à la dernière phase]\n\n---\n\n> *Séance de remédiation générée par aSchool*\n\nRègles absolues :\n- La somme des durées des phases = exactement {duree} minutes\n- Le scénario exploite concrètement la situation décrite par l\'enseignant\n- Chaque phase a un rôle clair dans la reconsolidation de la notion "{theme}"\n- Le contenu est adapté au niveau {niveau}\n- Répondre uniquement en markdown, rien d\'autre avant ni après le markdown',

    # l'ancien optimiseur de sequences
    'optimiseur': 'Tu es un expert en ingénierie pédagogique pour l\'enseignement secondaire français (collège et lycée, 6e à Terminale).\n\nUn enseignant de {matiere}, niveau {niveau}, te soumet une séquence pédagogique existante à optimiser.\n\nTa mission : analyser la séquence selon les 6 critères ci-dessous, identifier les problèmes présents, puis produire la version optimisée.\n\nLes 6 critères d\'analyse :\n1. Rupture conceptuelle — une phase suppose une notion non encore construite dans la séquence\n2. Surcharge cognitive — trop de notions nouvelles concentrées dans un temps trop court\n3. Consigne ambiguë — formulation pouvant être mal interprétée par les élèves\n4. Activité inefficace — exercice sans lien réel avec l\'objectif pédagogique déclaré\n5. Progression déséquilibrée — phases trop courtes ou trop longues, rythme inadapté\n6. Ancrage mémoriel manquant — absence de consolidation avant la fin ou l\'évaluation\n\nSéquence soumise :\n{sequence}\n\nFormat de réponse — JSON strict, rien d\'autre autour :\n{{\n  "problemes": [\n    {{"type": "Rupture conceptuelle", "detail": "description précise et concrète du problème détecté"}},\n    {{"type": "Surcharge cognitive", "detail": "..."}}\n  ],\n  "sequence_optimisee": "# Séance : [titre]\n**Matière :** ... | **Niveau :** ... | **Durée :** ... min\n\n---\n\n## Phase 1 — [Nom] ([X] min)\n**Objectif :** ...\n**Déroulement :** ...\n**Organisation :** ...\n\n## Phase 2 — [Nom] ([X] min)\n...",\n  "score": "Bon|Moyen|À revoir — X problème(s) détecté(s)",\n  "avertissement": "Message optionnel si incohérence détectée — sinon ne pas inclure ce champ."\n}}\n\nRègles :\n- N\'inclure dans "problemes" que les critères réellement problématiques. Ignorer les critères sans problème.\n- Si la séquence est déjà de bonne qualité, "problemes" est une liste vide [].\n- La séquence optimisée conserve la structure générale du prof. Elle corrige les problèmes détectés sans tout réécrire de zéro.\n- Le champ sequence_optimisee doit contenir le texte complet avec les vrais sauts de ligne (\\n) entre chaque phase — exactement le même format markdown que la séquence originale soumise.\n- Si la séquence soumise ne correspond manifestement pas à la matière {matiere} (ex : contenu de Français soumis pour Mathématiques, exercice de sport soumis pour Philosophie), remplis le champ "avertissement" avec un message court et précis signalant l\'incohérence. Sinon, n\'inclus pas ce champ.\n- Réponds uniquement en JSON valide. Aucun texte avant ou après le JSON.',
}

REGLAGE_RETIRE = "max_tokens_optimiseur"
REGLAGE_ORIGINE = "6000"


def upgrade() -> None:
    cles = [f"prompt_{c}" for c in PROMPTS_RETIRES] + [REGLAGE_RETIRE]
    op.execute(
        sa.text("DELETE FROM settings WHERE key = ANY(:cles)").bindparams(
            sa.bindparam("cles", value=cles, type_=sa.ARRAY(sa.String()))
        )
    )


def downgrade() -> None:
    """Remet l'etat d'ORIGINE (cf. docstring) — pas les retouches de l'admin, perdues."""
    conn = op.get_bind()
    for cle, texte in TEXTES_ORIGINE.items():
        conn.execute(
            sa.text("INSERT INTO settings (key, value) VALUES (:k, :v) "
                    "ON CONFLICT (key) DO NOTHING"),
            {"k": f"prompt_{cle}", "v": texte},
        )
    conn.execute(
        sa.text("INSERT INTO settings (key, value) VALUES (:k, :v) "
                "ON CONFLICT (key) DO NOTHING"),
        {"k": REGLAGE_RETIRE, "v": REGLAGE_ORIGINE},
    )
