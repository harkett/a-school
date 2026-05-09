import base64
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models_db import FicheMatiere
from backend.routers.admin import _require_admin
from src.activities import ACTIVITES_PAR_MATIERE
from src.generator import generate

router = APIRouter()

MATIERES = list(ACTIVITES_PAR_MATIERE.keys())

_LOGO_PATH = Path(__file__).resolve().parents[2] / "frontend" / "public" / "Logo_aSchool" / "Logo_aSchool.png"


def _logo_b64() -> str:
    try:
        data = _LOGO_PATH.read_bytes()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    except Exception:
        return ""


def _get_or_create(db: Session, matiere: str) -> FicheMatiere:
    fiche = db.query(FicheMatiere).filter_by(matiere_key=matiere).first()
    if not fiche:
        fiche = FicheMatiere(matiere_key=matiere, statut="brouillon")
        db.add(fiche)
        db.commit()
        db.refresh(fiche)
    return fiche


def _render_html(fiche: FicheMatiere, activites: dict) -> str:
    logo = _logo_b64()
    matiere = fiche.matiere_key
    nb = len(activites)

    accroche = fiche.accroche or (
        f"Vous enseignez {matiere} ? aSchool génère vos activités pédagogiques "
        f"en quelques secondes à partir de n'importe quel texte ou document."
    )

    pq_lines = [l.strip("- ").strip() for l in (fiche.pour_qui or "").split("\n") if l.strip()]
    if not pq_lines:
        pq_lines = [
            f"Professeurs de {matiere} du collège et du lycée",
            "Tout enseignant souhaitant gagner du temps sur la préparation",
            "Formateurs cherchant des supports calibrés par niveau",
        ]

    am_lines = [l.strip("- ").strip() for l in (fiche.ameliorations or "").split("\n") if l.strip()]
    if not am_lines:
        am_lines = [
            "Quiz interactifs à projeter en classe — les élèves répondent sur téléphone",
            "Partage d'activités entre collègues du même établissement",
            "Application mobile (PWA) pour accéder à aSchool sans navigateur",
        ]

    rows = ""
    for label, info in activites.items():
        sous = info.get("sous_types", [])
        if sous:
            detail = ", ".join(sous[:4])
            if len(sous) > 4:
                detail += "…"
        else:
            detail = "Activité complète générée d'un clic"
        rows += f"<tr><td><strong>{label}</strong></td><td>{detail}</td></tr>"

    pq_html = "".join(f"<li>{l}</li>" for l in pq_lines)
    am_html = "".join(f"<li>{l}</li>" for l in am_lines)
    logo_img = f'<img src="{logo}" alt="aSchool">' if logo else ""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>aSchool — {matiere}</title>
<style>
  @page {{ size: A4; margin: 18mm 18mm 18mm 18mm; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.5pt; color: #1e293b; line-height: 1.5; background: #fff; }}

  .doc-header {{ background: #1a3a6e; color: white; padding: 18px 22px; display: flex; align-items: center; gap: 18px; border-radius: 6px 6px 0 0; margin-bottom: 18px; }}
  .doc-header img {{ height: 48px; }}
  .doc-header h1 {{ font-size: 17pt; font-weight: 700; }}
  .doc-header p {{ font-size: 9.5pt; opacity: 0.75; margin-top: 3px; }}

  .accroche {{ background: #eff6ff; border-left: 4px solid #1a3a6e; padding: 12px 16px; margin-bottom: 20px; border-radius: 0 4px 4px 0; font-size: 11pt; color: #1e3a5f; }}

  h2 {{ font-size: 12pt; font-weight: 700; color: #1a3a6e; margin-bottom: 10px; padding-bottom: 5px; border-bottom: 2px solid #e2e8f0; }}

  .steps {{ display: flex; gap: 10px; margin-bottom: 20px; }}
  .step {{ flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; }}
  .step-num {{ width: 22px; height: 22px; background: #1a3a6e; color: white; border-radius: 50%; font-size: 10pt; font-weight: 700; display: flex; align-items: center; justify-content: center; margin-bottom: 7px; }}
  .step h3 {{ font-size: 9.5pt; font-weight: 700; margin-bottom: 3px; }}
  .step p {{ font-size: 9pt; color: #64748b; }}

  table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 9.5pt; }}
  th {{ background: #1a3a6e; color: white; padding: 7px 11px; text-align: left; font-weight: 600; }}
  tr:nth-child(even) {{ background: #f8fafc; }}
  td {{ padding: 6px 11px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
  td:first-child {{ width: 37%; font-weight: 600; color: #1e3a5f; }}

  .two-col {{ display: flex; gap: 16px; margin-bottom: 20px; }}
  .col {{ flex: 1; }}

  ul {{ list-style: none; padding: 0; }}
  ul li {{ padding: 5px 0 5px 18px; font-size: 10pt; color: #374151; position: relative; border-bottom: 1px solid #f1f5f9; }}
  ul li::before {{ content: "→"; position: absolute; left: 0; color: #1a3a6e; font-weight: 700; }}

  .avantages {{ display: flex; flex-direction: column; gap: 5px; }}
  .av {{ display: flex; gap: 8px; align-items: flex-start; }}
  .av strong {{ color: #1a3a6e; white-space: nowrap; min-width: 72px; font-size: 10pt; }}
  .av span {{ font-size: 9.5pt; color: #475569; }}

  .future {{ background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; }}
  .future h2 {{ border-bottom-color: #ddd6fe; color: #6b21a8; }}
  .future ul li::before {{ color: #7c3aed; }}
  .future ul li {{ color: #4c1d95; border-bottom-color: #f3e8ff; }}

  .doc-footer {{ background: #1a3a6e; color: white; padding: 12px 20px; border-radius: 0 0 6px 6px; display: flex; align-items: center; justify-content: space-between; margin-top: 20px; }}
  .doc-footer img {{ height: 28px; }}
  .doc-footer p {{ font-size: 9pt; opacity: 0.85; line-height: 1.5; }}
  .doc-footer a {{ color: #93c5fd; text-decoration: none; }}

  .badge {{ display: inline-block; background: #dbeafe; color: #1e40af; font-size: 8pt; font-weight: 700; padding: 1px 7px; border-radius: 99px; margin-left: 8px; vertical-align: middle; }}

  @media print {{
    body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}
</style>
</head>
<body>

<div class="doc-header">
  {logo_img}
  <div>
    <h1>aSchool — {matiere}</h1>
    <p>Générateur d'activités pédagogiques · school.afia.fr</p>
  </div>
</div>

<div class="accroche">{accroche}</div>

<h2>Comment ça marche ?</h2>
<div class="steps">
  <div class="step">
    <div class="step-num">1</div>
    <h3>Fournissez un texte</h3>
    <p>Collez un extrait, importez un .txt, photographiez un document (OCR) ou dictez à voix haute.</p>
  </div>
  <div class="step">
    <div class="step-num">2</div>
    <h3>Configurez l'activité</h3>
    <p>Niveau (6e → Terminale), type parmi {nb} disponibles, sous-type, nombre de questions, correction.</p>
  </div>
  <div class="step">
    <div class="step-num">3</div>
    <h3>Téléchargez</h3>
    <p>Prête en moins de 15 secondes. Export Word (.docx) ou PDF — imprimez directement.</p>
  </div>
</div>

<h2>Les {nb} activités disponibles <span class="badge">{matiere}</span></h2>
<table>
  <tr><th>Type d'activité</th><th>Ce que ça génère</th></tr>
  {rows}
</table>

<div class="two-col">
  <div class="col">
    <h2>Pour qui ?</h2>
    <ul>{pq_html}</ul>
  </div>
  <div class="col">
    <h2>Pourquoi aSchool ?</h2>
    <div class="avantages">
      <div class="av"><strong>Rapide</strong><span>Activité complète en moins de 15 secondes</span></div>
      <div class="av"><strong>Adapté</strong><span>Le contenu s'ajuste de la 6e à la Terminale</span></div>
      <div class="av"><strong>Prêt</strong><span>Export Word — imprimez sans mise en forme</span></div>
      <div class="av"><strong>Flexible</strong><span>{nb} types × plusieurs sous-types = des centaines de combinaisons</span></div>
      <div class="av"><strong>Gratuit</strong><span>Inscription libre sur school.afia.fr</span></div>
      <div class="av"><strong>Privé</strong><span>Vos textes ne sont ni stockés ni partagés</span></div>
    </div>
  </div>
</div>

<div class="future">
  <h2>Ce qui arrive bientôt</h2>
  <ul>{am_html}</ul>
</div>

<div class="doc-footer">
  {logo_img}
  <p>
    <strong>school.afia.fr</strong> · Inscription gratuite<br>
    <a href="mailto:contact@aschool.fr">contact@aschool.fr</a> · Développé par AFIA
  </p>
</div>

</body>
</html>"""


# ── Routes admin ─────────────────────────────────────────────────────────────

@router.get("/api/admin/fiches", dependencies=[Depends(_require_admin)])
def list_fiches(db: Session = Depends(get_db)):
    result = []
    for matiere in MATIERES:
        fiche = _get_or_create(db, matiere)
        nb_activites = len(ACTIVITES_PAR_MATIERE.get(matiere, {}))
        result.append({
            "matiere": matiere,
            "statut": fiche.statut,
            "nb_activites": nb_activites,
            "has_content": bool(fiche.accroche),
            "updated_at": fiche.updated_at.isoformat() if fiche.updated_at else None,
        })
    return result


@router.get("/api/admin/fiches/{matiere}", dependencies=[Depends(_require_admin)])
def get_fiche(matiere: str, db: Session = Depends(get_db)):
    matiere = unquote(matiere)
    if matiere not in MATIERES:
        raise HTTPException(404, "Matière inconnue")
    fiche = _get_or_create(db, matiere)
    return {
        "matiere": matiere,
        "statut": fiche.statut,
        "accroche": fiche.accroche or "",
        "pour_qui": fiche.pour_qui or "",
        "ameliorations": fiche.ameliorations or "",
        "updated_at": fiche.updated_at.isoformat() if fiche.updated_at else None,
        "nb_activites": len(ACTIVITES_PAR_MATIERE.get(matiere, {})),
    }


class FicheUpdate(BaseModel):
    statut: str | None = None
    accroche: str | None = None
    pour_qui: str | None = None
    ameliorations: str | None = None


@router.put("/api/admin/fiches/{matiere}", dependencies=[Depends(_require_admin)])
def update_fiche(matiere: str, body: FicheUpdate, db: Session = Depends(get_db)):
    matiere = unquote(matiere)
    if matiere not in MATIERES:
        raise HTTPException(404, "Matière inconnue")
    fiche = _get_or_create(db, matiere)
    if body.statut is not None:
        fiche.statut = body.statut
    if body.accroche is not None:
        fiche.accroche = body.accroche
    if body.pour_qui is not None:
        fiche.pour_qui = body.pour_qui
    if body.ameliorations is not None:
        fiche.ameliorations = body.ameliorations
    fiche.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@router.post("/api/admin/fiches/{matiere}/generer", dependencies=[Depends(_require_admin)])
def generer_fiche(matiere: str, db: Session = Depends(get_db)):
    matiere = unquote(matiere)
    if matiere not in MATIERES:
        raise HTTPException(404, "Matière inconnue")

    activites = ACTIVITES_PAR_MATIERE.get(matiere, {})
    activites_list = ", ".join(activites.keys())

    prompt = f"""Tu es un expert en communication éducative. Génère le contenu d'une fiche de présentation pour aSchool (générateur d'activités pédagogiques) ciblant les professeurs de {matiere} du secondaire français.

Activités disponibles pour {matiere} : {activites_list}

Génère exactement 3 sections au format JSON :
{{
  "accroche": "2-3 phrases percutantes en vouvoyement, spécifiques à {matiere}, montrant le gain de temps concret",
  "pour_qui": "ligne1\\nligne2\\nligne3\\nligne4",
  "ameliorations": "- amélioration 1 spécifique à {matiere}\\n- amélioration 2\\n- amélioration 3\\n- amélioration 4"
}}

Règles :
- pour_qui : 3-4 lignes, une par ligne, spécifiques au profil du prof de {matiere}
- ameliorations : 3-4 futures fonctionnalités utiles pour {matiere}
- Ton professionnel, direct, sans jargon technique
- Ne jamais mentionner "IA" — utiliser "aSchool" ou "génération automatique"
- Répondre uniquement avec le JSON, sans texte avant ou après"""

    try:
        raw = generate(prompt)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            raise ValueError("Réponse JSON introuvable")
        data = json.loads(match.group())
    except Exception as e:
        raise HTTPException(500, f"Erreur de génération : {e}")

    fiche = _get_or_create(db, matiere)
    fiche.accroche = data.get("accroche", "")
    fiche.pour_qui = data.get("pour_qui", "")
    fiche.ameliorations = data.get("ameliorations", "")
    fiche.statut = "brouillon"
    fiche.updated_at = datetime.utcnow()
    db.commit()

    return {
        "accroche": fiche.accroche,
        "pour_qui": fiche.pour_qui,
        "ameliorations": fiche.ameliorations,
    }


# ── Route publique ─────────────────────────────────────────────────────────────

@router.get("/api/fiches/{matiere}", response_class=HTMLResponse)
def get_fiche_html(matiere: str, db: Session = Depends(get_db)):
    matiere = unquote(matiere)
    if matiere not in MATIERES:
        raise HTTPException(404, "Matière inconnue")
    fiche = _get_or_create(db, matiere)
    activites = ACTIVITES_PAR_MATIERE.get(matiere, {})
    html = _render_html(fiche, activites)
    filename = matiere.lower().replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "")
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f'inline; filename="aSchool_{filename}.html"'},
    )
