import io
import streamlit as st
from pathlib import Path
from datetime import date

from src.prompts import build_prompt
from src.generator import generate, transcribe_audio
from src.formats import to_markdown, save
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="A-SCHOOL — Générateur pédagogique IA", page_icon="📚", layout="wide")

# ── Réduire le vide en haut ───────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    [data-testid="stFileUploader"] label { display: none; }
</style>
""", unsafe_allow_html=True)

st.title("📚 A-SCHOOL — Générateur d'activités pédagogiques")
st.caption("Collez un texte, choisissez une activité, générez en quelques secondes.")

# ── Configuration des activités ───────────────────────────────────────────────
ACTIVITES = {
    "Questions de compréhension": {
        "key": "comprehension",
        "sous_types": ["simples (repérage)", "inférence", "interprétation", "personnages", "décor / contexte", "émotions / intentions", "mélange"],
        "params": ["nb", "sous_type"],
    },
    "Pistes de lecture": {
        "key": "pistes",
        "sous_types": ["thématique", "narrateur", "réalisme", "point de vue", "registre"],
        "params": ["nb", "sous_type"],
    },
    "Résumés": {
        "key": "resume",
        "sous_types": ["court (5 lignes)", "structuré (début/milieu/fin)", "pour l'oral"],
        "params": ["sous_type"],
    },
    "Analyse de texte": {
        "key": "analyse",
        "sous_types": ["thème principal", "champs lexicaux", "procédés d'écriture", "passage difficile"],
        "params": ["sous_type"],
    },
    "Exercices de réécriture": {
        "key": "reecriture",
        "sous_types": [
            "style direct vers style indirect",
            "passé simple vers présent",
            "présent vers passé simple",
            "présent vers conditionnel présent",
            "1ère personne du singulier vers 1ère personne du pluriel",
            "3ème personne du singulier vers 1ère personne du pluriel",
            "changement de point de vue",
            "simplifier le vocabulaire",
            "enrichir le texte",
        ],
        "params": ["sous_type"],
    },
    "Étude de vocabulaire": {
        "key": "vocabulaire",
        "sous_types": ["mots difficiles + définitions", "synonymes / antonymes", "exercices à trous", "reformulation"],
        "params": ["sous_type"],
    },
    "Production d'écrit": {
        "key": "production_ecrit",
        "sous_types": ["paragraphe argumenté", "continuer le texte", "décrire un personnage", "imaginer la suite d'une scène", "texte poétique"],
        "params": ["sous_type"],
    },
    "Questions pour l'oral": {
        "key": "oral",
        "sous_types": ["débat", "exposé", "échange en classe"],
        "params": ["nb", "sous_type"],
    },
    "Fiche pédagogique": {
        "key": "fiche_pedagogique",
        "sous_types": [],
        "params": [],
    },
    "Exercices de grammaire": {
        "key": "grammaire",
        "sous_types": ["temps verbaux", "types de phrases", "transformer des phrases", "accords"],
        "params": ["sous_type"],
    },
    "Recherche de séquences": {
        "key": "recherche_sequences",
        "sous_types": [],
        "params": [],
    },
    "Séquence détaillée": {
        "key": "sequence_detaillee",
        "sous_types": [],
        "params": [],
    },
    "Questionnaire sur un roman": {
        "key": "questionnaire_roman",
        "sous_types": [],
        "params": [],
    },
    "Évaluation de grammaire": {
        "key": "evaluation_grammaire",
        "sous_types": [],
        "params": [],
    },
    "Évaluation d'orthographe": {
        "key": "evaluation_orthographe",
        "sous_types": [],
        "params": [],
    },
}


def to_docx(texte: str) -> bytes:
    from docx import Document
    from docx.shared import Pt
    doc = Document()
    doc.styles["Normal"].font.size = Pt(11)
    for ligne in texte.split("\n"):
        ligne = ligne.strip()
        if ligne.startswith("# "):
            doc.add_heading(ligne[2:], level=1)
        elif ligne.startswith("## "):
            doc.add_heading(ligne[3:], level=2)
        elif ligne.startswith("### "):
            doc.add_heading(ligne[4:], level=3)
        elif ligne:
            doc.add_paragraph(ligne)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ── Mise en page ──────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Texte")

    c_upload, c_micro = st.columns([1, 1])
    with c_upload:
        fichier = st.file_uploader(
            "Importer",
            type=["txt"],
            help="Importer un fichier texte (.txt)",
            label_visibility="collapsed",
        )
    with c_micro:
        audio = mic_recorder(
            start_prompt="Dicter",
            stop_prompt="Arrêter",
            key="micro",
            use_container_width=True,
        )

    if fichier:
        texte = fichier.read().decode("utf-8")
        st.success(f"Fichier chargé : {fichier.name}")
        st.text_area("Contenu", texte, height=250, disabled=True, label_visibility="collapsed")
    else:
        if audio:
            with st.spinner("Transcription en cours..."):
                try:
                    texte_dicte = transcribe_audio(audio["bytes"])
                    st.session_state["texte_dicte"] = texte_dicte
                    st.success("Transcription terminée.")
                except Exception as e:
                    st.error(f"Erreur transcription : {e}")

        texte = st.text_area(
            "Texte",
            value=st.session_state.get("texte_dicte", ""),
            height=300,
            placeholder="Collez un extrait de texte ici...",
            label_visibility="collapsed",
        )

with col2:
    st.subheader("Paramètres")

    niveau = st.selectbox("Niveau", ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale", "Supérieur"], index=2)

    activite_label = st.selectbox("Type d'activité", list(ACTIVITES.keys()))
    activite_cfg = ACTIVITES[activite_label]
    activite_key = activite_cfg["key"]

    sous_type = None
    nb = None

    if activite_cfg["sous_types"]:
        sous_type = st.selectbox("Sous-type", activite_cfg["sous_types"])

    if "nb" in activite_cfg["params"]:
        nb = st.slider("Nombre de questions", 2, 15, 5)

    st.divider()
    avec_correction = st.checkbox(
        "Inclure une proposition de correction",
        value=False,
        help="L'IA génère une réponse-type après chaque question, que le professeur adapte à sa classe.",
    )

# ── Génération ────────────────────────────────────────────────────────────────
st.divider()
generer = st.button("Générer l'activité", type="primary", use_container_width=True)

if generer:
    if not texte or not texte.strip():
        st.error("Veuillez coller un texte, importer un fichier ou utiliser la dictée.")
    else:
        with st.spinner("Génération en cours..."):
            try:
                kwargs = {"niveau": niveau}
                if sous_type:
                    kwargs["sous_type"] = sous_type
                if nb:
                    kwargs["nb"] = nb

                prompt = build_prompt(activite_key, texte, avec_correction=avec_correction, **kwargs)
                resultat = generate(prompt)
                md_content = to_markdown(activite_key, niveau, resultat)

                st.success("Activité générée !")
                st.subheader("Résultat")
                st.markdown(resultat)

                today = date.today().strftime("%Y%m%d")
                chemin = f"outputs/{activite_key}_{today}.md"
                Path("outputs").mkdir(exist_ok=True)
                save(md_content, chemin)

                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="Télécharger en Word (.docx)",
                        data=to_docx(resultat),
                        file_name=f"{activite_key}_{today}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                with col_dl2:
                    st.download_button(
                        label="Télécharger en texte (.txt)",
                        data=resultat.encode("utf-8"),
                        file_name=f"{activite_key}_{today}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

            except Exception as e:
                st.error(f"Erreur : {e}")
