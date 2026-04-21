import io
import streamlit as st
from pathlib import Path
from datetime import date

from src.prompts import build_prompt
from src.generator import generate, transcribe_audio, transcribe_image
from src.formats import to_markdown, save
from src.auth import (generate_magic_token, verify_magic_token,
                      send_magic_link, get_current_user, notify_admin_connexion,
                      create_session, get_session, delete_session)
from streamlit_cookies_controller import CookieController
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="A-SCHOOL — Générateur pédagogique IA", page_icon="📚", layout="wide")


def _get_webmail_url(email: str) -> str | None:
    domain = email.split("@")[-1].lower()
    if domain == "gmail.com":
        return "https://mail.google.com"
    if domain in ("outlook.fr", "outlook.com", "hotmail.com", "hotmail.fr", "live.fr", "live.com"):
        return "https://outlook.live.com/mail/inbox"
    if domain in ("yahoo.fr", "yahoo.com"):
        return "https://mail.yahoo.com"
    if domain == "laposte.net":
        return "https://www.laposte.net/accueil"
    if domain == "orange.fr":
        return "https://messagerie.orange.fr"
    return None

# ── 1. Token Magic link — vérifié AVANT le CookieController ─────────────────
params = st.query_params
if "token" in params and not st.session_state.get("user_email"):
    result = verify_magic_token(params["token"])
    if result:
        st.session_state["user_email"] = result["email"]
        st.session_state["matiere"] = result["matiere"]
        _tok = create_session(result["email"], result["matiere"])
        st.session_state["session_token"] = _tok
        st.session_state["_pending_cookie"] = _tok
        st.query_params.clear()
        try:
            notify_admin_connexion(result["email"], "A-SCHOOL : Générateur d'activités pédagogiques")
        except Exception as e:
            st.session_state["notif_error"] = str(e)
        st.rerun()
    else:
        st.error("Lien invalide ou expiré. Demandez un nouveau lien.")
        st.stop()

# ── 2. CookieController — initialisé après le token check ───────────────────
_cookies = CookieController()

# ── 3. Poser le cookie si un token vient d'être validé ──────────────────────
if st.session_state.get("_pending_cookie"):
    _cookies.set("aschool_session", st.session_state.pop("_pending_cookie"), max_age=30 * 24 * 3600)

# ── 4. Restauration session depuis cookie ────────────────────────────────────
if not st.session_state.get("user_email"):
    try:
        _session_token = _cookies.get("aschool_session")
    except Exception:
        _session_token = None
    if _session_token:
        _session_data = get_session(_session_token)
        if _session_data:
            st.session_state["user_email"] = _session_data["email"]
            st.session_state["matiere"] = _session_data["matiere"]
            st.session_state["session_token"] = _session_token

# ── 5. Logout via URL ────────────────────────────────────────────────────────
if "logout" in st.query_params:
    _token = st.session_state.pop("session_token", None)
    if _token:
        delete_session(_token)
        _cookies.remove("aschool_session")
    st.session_state.pop("user_email", None)
    st.session_state.pop("user_name", None)
    st.query_params.clear()
    st.rerun()

# ── Page de connexion ─────────────────────────────────────────────────────────
user = get_current_user()

# Notification admin à la première connexion Google de la session
if user and user["method"] == "google" and not st.session_state.get("google_notified"):
    try:
        notify_admin_connexion(user["email"], "google")
        st.session_state["google_notified"] = True
    except Exception:
        pass

if not user:
    st.markdown("""
    <style>
        .block-container { padding-top: 5rem; max-width: 480px; }
        #MainMenu, header, [data-testid="stToolbar"],
        [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
        .aschool-navbar {
            position: fixed;
            top: 0; left: 0; right: 0;
            z-index: 1000;
            background: #1e2d4d;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 2rem;
            height: 56px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        .aschool-navbar-logo { font-size:1.1rem; font-weight:700; color:white; letter-spacing:-0.3px; }
        .aschool-navbar-logo span { color:#f97316; }
        .aschool-navbar-btn {
            color: white !important;
            text-decoration: none !important;
            border: 1px solid rgba(255,255,255,0.35);
            border-radius: 6px;
            padding: 0.3rem 1rem;
            font-size: 0.875rem;
            font-weight: 500;
        }
        .aschool-navbar-btn:hover { background: rgba(255,255,255,0.1); }
    </style>
    <nav class="aschool-navbar">
        <div class="aschool-navbar-logo">A-<span>SCHOOL</span></div>
        <a href="#" class="aschool-navbar-btn" title="Entrez votre email pour recevoir un lien de connexion">Connexion</a>
    </nav>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:linear-gradient(135deg,#1e3a8a,#2563eb);
                border-radius:12px; padding:2rem; text-align:center; margin-bottom:2rem;
                max-width:420px; margin-left:auto; margin-right:auto;">
        <h1 style="color:white; margin:0; font-size:2rem;">A-SCHOOL</h1>
        <p style="color:rgba(255,255,255,0.85); margin:0.5rem 0 0 0;">
            Générateur d'activités pédagogiques
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("Entrez votre email pour recevoir un lien de connexion :")

    with st.form("magic_link_form"):
        email_input = st.text_input("Votre adresse email professionnelle",
                                    placeholder="prenom.nom@ac-bordeaux.fr")
        matiere_input = st.selectbox("Vous enseignez quelle matière ?",
                                     ["Français", "Histoire-Géographie"])
        envoyer = st.form_submit_button("Recevoir un lien de connexion",
                                        use_container_width=True)

    if envoyer:
        if not email_input or "@" not in email_input:
            st.error("Entrez une adresse email valide.")
        else:
            with st.spinner("Envoi en cours..."):
                try:
                    token = generate_magic_token(email_input, matiere_input)
                    send_magic_link(email_input, token)
                    webmail = _get_webmail_url(email_input)
                    email_display = f'<a href="{webmail}" target="_blank">{email_input}</a>' if webmail else email_input
                    st.markdown(
                        f'<div class="stAlert" style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:0.75rem 1rem;color:#166534;">'
                        f'Lien envoyé à {email_display} — vérifiez votre boîte mail (valable 15 min).</div>',
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"Erreur d'envoi : {e}")
    st.stop()

# ── Styles ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Layout général */
    .block-container { padding-top: 5rem; padding-bottom: 2rem; max-width: 1200px; }
    #MainMenu, header, [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* Navbar */
    .aschool-navbar {
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 1000;
        background: #1e2d4d;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 2rem;
        height: 56px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .aschool-navbar-logo {
        font-size: 1.1rem;
        font-weight: 700;
        color: white;
        letter-spacing: -0.3px;
    }
    .aschool-navbar-logo span {
        color: #f97316;
    }
    .aschool-navbar-right {
        display: flex;
        align-items: center;
        gap: 1.5rem;
        font-size: 0.875rem;
    }
    .aschool-navbar-email {
        color: rgba(255,255,255,0.6);
    }
    .aschool-navbar-logout {
        color: white !important;
        text-decoration: none !important;
        border: 1px solid rgba(255,255,255,0.35);
        border-radius: 6px;
        padding: 0.3rem 1rem;
        font-weight: 500;
        transition: background 0.15s;
    }
    .aschool-navbar-logout:hover {
        background: rgba(255,255,255,0.1);
    }

    /* Header custom */
    .aschool-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }
    .aschool-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: white !important;
    }
    .aschool-header p {
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
        opacity: 0.85;
        color: white !important;
    }
    .aschool-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        color: white;
        font-size: 0.75rem;
        padding: 0.15rem 0.6rem;
        border-radius: 20px;
        margin-bottom: 0.6rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    /* Cartes panneaux */
    .aschool-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
    }
    .aschool-card h3 {
        margin: 0 0 1rem 0;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #64748b;
    }

    /* Résultat */
    .aschool-result {
        background: #f8faff;
        border: 1px solid #bfdbfe;
        border-left: 4px solid #1e3a8a;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
    }

    /* Widgets */
    [data-testid="stFileUploader"] label { display: none; }
    [data-testid="stSelectbox"] input { pointer-events: none !important; caret-color: transparent !important; }
    [data-testid="stSelectbox"] > div { cursor: pointer !important; }
    [data-testid="stSelectbox"] > div > div { cursor: pointer !important; }

    /* Sélects et sliders */
    [data-testid="stSelectbox"] > div > div {
        border-radius: 8px !important;
        border-color: #cbd5e1 !important;
    }

    /* Zone micro */
    [data-testid="stColumn"]:has(audio) [data-testid="stVerticalBlock"] {
        background-color: #f0f4f8;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        min-height: 88px;
    }
    [data-testid="stColumn"]:has(audio) button {
        background-color: white !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
        padding: 0.25rem 0.75rem !important;
        font-size: 0.875rem !important;
        font-weight: 400 !important;
        box-shadow: none !important;
    }

    /* Bouton générer */
    [data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #1e3a8a, #2563eb) !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px !important;
        padding: 0.6rem 1.5rem !important;
        box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
        transition: all 0.2s ease !important;
    }

    /* Boutons téléchargement */
    [data-testid="stDownloadButton"] > button {
        border-radius: 8px !important;
        border-color: #1e3a8a !important;
        color: #1e3a8a !important;
        font-weight: 500 !important;
    }

    /* Séparateurs */
    hr { border-color: #e2e8f0 !important; margin: 1.25rem 0 !important; }

    /* Captions */
    [data-testid="stCaptionContainer"] { color: #94a3b8 !important; font-size: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)

# Navbar fixe
st.markdown(f"""
<nav class="aschool-navbar">
    <div class="aschool-navbar-logo">A-<span>SCHOOL</span></div>
    <div class="aschool-navbar-right">
        <span style="color:rgba(255,255,255,0.45); font-size:0.8rem;">|</span>
        <span style="color:#f97316; font-size:0.85rem; font-weight:600;">{st.session_state.get('matiere', 'Français')}</span>
        <span style="color:rgba(255,255,255,0.45); font-size:0.8rem;">|</span>
        <span class="aschool-navbar-email">{user['email']}</span>
        <a href="?logout=1" class="aschool-navbar-logout" title="Fermer votre session et revenir à la page de connexion">Se déconnecter</a>
    </div>
</nav>
""", unsafe_allow_html=True)

# Header page
st.markdown("""
<div class="aschool-header">
    <h1>Générateur d'activités pédagogiques</h1>
    <p>Collez un texte, choisissez une activité, générez en quelques secondes.</p>
</div>
""", unsafe_allow_html=True)

# ── Configuration des activités ───────────────────────────────────────────────
ACTIVITES_PAR_MATIERE = {}

ACTIVITES_PAR_MATIERE["Français"] = {
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

ACTIVITES_PAR_MATIERE["Histoire-Géographie"] = {
    "Questions sur un document": {
        "key": "hg_comprehension",
        "sous_types": ["identification", "contexte", "analyse", "mise en relation", "mélange"],
        "params": ["nb", "sous_type"],
    },
    "Analyse de source": {
        "key": "hg_analyse_source",
        "sous_types": [],
        "params": [],
    },
    "Questions de cours": {
        "key": "hg_questions_cours",
        "sous_types": ["connaissances", "définitions", "explication", "mélange"],
        "params": ["nb", "sous_type"],
    },
    "Frise chronologique": {
        "key": "hg_frise",
        "sous_types": [],
        "params": [],
    },
    "Paragraphe argumenté": {
        "key": "hg_paragraphe",
        "sous_types": ["réponse organisée", "SEUL", "bilan de séquence"],
        "params": ["sous_type"],
    },
    "Fiche de révision": {
        "key": "hg_fiche_revision",
        "sous_types": [],
        "params": [],
    },
    "Composition / Dissertation": {
        "key": "hg_composition",
        "sous_types": ["introduction seule", "plan détaillé", "développement complet", "plan avec transitions"],
        "params": ["sous_type"],
    },
    "Lecture de carte / Croquis": {
        "key": "hg_carte",
        "sous_types": ["décrire et expliquer une carte", "questions sur un croquis", "légende à compléter"],
        "params": ["sous_type"],
    },
    "Étude d'un document iconographique": {
        "key": "hg_iconographie",
        "sous_types": ["affiche de propagande", "dessin de presse", "photographie historique", "œuvre d'art"],
        "params": ["sous_type"],
    },
    "Exercice de repères": {
        "key": "hg_reperes",
        "sous_types": ["QCM de repères", "définir des notions clés", "placer des événements sur une frise", "situer des lieux"],
        "params": ["nb", "sous_type"],
    },
    "Mise en relation de documents": {
        "key": "hg_mise_en_relation",
        "sous_types": ["confronter deux sources", "dégager complémentarité / contradiction", "synthèse de documents"],
        "params": ["sous_type"],
    },
    "Préparation à l'oral": {
        "key": "hg_oral",
        "sous_types": ["exposé", "débat", "Grand Oral Terminale", "échange en classe"],
        "params": ["nb", "sous_type"],
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
            type=["txt", "jpg", "jpeg", "png"],
            label_visibility="collapsed",
            help="Fichier texte (.txt) ou image scannée (JPG/PNG) — le texte sera extrait automatiquement",
        )
        st.caption("Texte .txt ou scan JPG/PNG")
    with c_micro:
        audio = mic_recorder(
            start_prompt="🎤  Dicter",
            stop_prompt="⏹  Arrêter",
            key="micro",
            use_container_width=False,
        )
        st.caption("Cliquez puis parlez — arrêtez quand vous avez terminé")

    if fichier:
        ext = fichier.name.lower().split(".")[-1]
        if ext == "txt":
            st.session_state["texte_dicte"] = fichier.read().decode("utf-8")
            st.session_state["last_image_name"] = None
        elif fichier.name != st.session_state.get("last_image_name"):
            st.session_state["last_image_name"] = fichier.name
            with st.spinner("Lecture du document en cours..."):
                try:
                    mime = "image/png" if ext == "png" else "image/jpeg"
                    st.session_state["texte_dicte"] = transcribe_image(fichier.getvalue(), mime)
                    st.success(f"Texte extrait de {fichier.name}")
                except Exception as e:
                    st.error(f"Erreur extraction : {e}")
    else:
        if audio:
            with st.spinner("Transcription en cours..."):
                try:
                    st.session_state["texte_dicte"] = transcribe_audio(audio["bytes"])
                    st.success("Transcription terminée.")
                except Exception as e:
                    st.error(f"Erreur transcription : {e}")

    texte = st.text_area(
        "Texte",
        value=st.session_state.get("texte_dicte", ""),
        height=270,
        placeholder="Collez un extrait de texte ici\n— ou téléchargez un fichier .txt\n— ou dictez avec le micro\n— ou importez un scan JPG/PNG",
        label_visibility="collapsed",
    )

with col2:
    st.subheader("Paramètres")

    niveau = st.selectbox("Niveau de la classe", ["6e", "5e", "4e", "3e", "2nde", "1ère", "Terminale", "Supérieur"], index=2)

    matiere = st.session_state.get("matiere", "Français")
    ACTIVITES = ACTIVITES_PAR_MATIERE.get(matiere, ACTIVITES_PAR_MATIERE["Français"])

    activite_label = st.selectbox("Type d'activité", list(ACTIVITES.keys()))
    activite_cfg = ACTIVITES[activite_label]
    activite_key = activite_cfg["key"]

    sous_type = None
    nb = None

    if activite_cfg["sous_types"]:
        sous_type = st.selectbox("Précision", activite_cfg["sous_types"])

    if "nb" in activite_cfg["params"]:
        nb = st.number_input("Nombre de questions", min_value=1, value=5, step=1)

    st.divider()
    avec_correction = st.checkbox(
        "Inclure une proposition de correction",
        value=False,
        help="L'IA génère une réponse-type après chaque question, que le professeur adapte à sa classe.",
    )

# ── Génération ────────────────────────────────────────────────────────────────
st.divider()
generer = st.button("Générer l'activité", type="primary", use_container_width=True,
                    help="Cliquez pour générer l'activité pédagogique avec l'IA")

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
                today = date.today().strftime("%Y%m%d")

                Path("outputs").mkdir(exist_ok=True)
                save(md_content, f"outputs/{activite_key}_{today}.md")

                st.session_state["resultat"] = resultat
                st.session_state["resultat_key"] = activite_key
                st.session_state["resultat_today"] = today

            except Exception as e:
                st.error(f"Erreur : {e}")

# ── Affichage du résultat (persiste jusqu'à fermeture) ────────────────────────
if st.session_state.get("resultat"):
    resultat = st.session_state["resultat"]
    activite_key_dl = st.session_state["resultat_key"]
    today_dl = st.session_state["resultat_today"]

    st.divider()
    col_titre, col_fermer = st.columns([5, 1])
    with col_titre:
        st.markdown("### Résultat généré")
    with col_fermer:
        if st.button("Fermer", use_container_width=True):
            st.session_state["resultat"] = None
            st.rerun()

    st.markdown(f'<div class="aschool-result">{resultat}</div>', unsafe_allow_html=True)

    st.divider()
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="Télécharger en Word (.docx)",
            data=to_docx(resultat),
            file_name=f"{activite_key_dl}_{today_dl}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    with col_dl2:
        st.download_button(
            label="Télécharger en texte (.txt)",
            data=resultat.encode("utf-8"),
            file_name=f"{activite_key_dl}_{today_dl}.txt",
            mime="text/plain",
            use_container_width=True,
        )
