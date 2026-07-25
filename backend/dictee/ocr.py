import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.systeme.admin import get_cle_api, get_ocr_model, get_max_tokens
from backend.llm.generator import transcribe_image, LLMRateLimitError

router = APIRouter()

# PDF scanné (sans couche texte) → OCR page par page. pypdfium2 (déjà présent, dépendance de
# pdfplumber) rend chaque page en image ; transcribe_image applique la MÊME OCR que le bouton
# « Image / Scan ». scale 2.0 ≈ 144 dpi (net pour l'OCR). Plafond : une OCR = un appel modèle/page.
_PDF_OCR_MAX_PAGES = 15


def _ocr_pdf_scanne(data: bytes, db: Session) -> str:
    """Lit un PDF SCANNÉ : rend chaque page en image et la passe dans l'OCR image (transcribe_image,
    modèle lu EN BASE). Renvoie le texte recollé. Messages HUMAINS (RÈGLE 23), jamais techniques."""
    import pypdfium2 as pdfium
    try:
        doc = pdfium.PdfDocument(data)
    except Exception as e:
        raise HTTPException(500, f"Erreur ouverture PDF : {e}")
    try:
        nb_pages = len(doc)
        if nb_pages > _PDF_OCR_MAX_PAGES:
            raise HTTPException(
                422,
                f"Ce document scanné fait {nb_pages} pages : c'est trop pour une seule lecture "
                f"(maximum {_PDF_OCR_MAX_PAGES}). Découpez-le et envoyez-le en plusieurs fois."
            )
        api_key = get_cle_api(db, "cle_env_ocr")   # nom en base, clé au .env ; erreur claire si absent
        model = get_ocr_model(db)                   # modèle OCR résolu EN BASE (rien en dur)
        max_tokens = get_max_tokens(db, "ocr")
        morceaux: list[str] = []
        for i in range(nb_pages):
            buf = io.BytesIO()
            doc[i].render(scale=2.0).to_pil().save(buf, format="PNG")
            try:
                morceaux.append(transcribe_image(
                    buf.getvalue(), "image/png",
                    api_key=api_key, model=model, max_tokens=max_tokens,
                ))
            except LLMRateLimitError as e:
                raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
    finally:
        doc.close()
    texte = "\n\n".join(m for m in morceaux if m and m.strip())
    if not texte.strip():
        raise HTTPException(
            422,
            "Ce PDF n'a pas pu être lu : aucune écriture n'a été détectée sur les pages. "
            "Vérifiez que le document est bien net, puis réessayez."
        )
    return texte


@router.post("/ocr")
async def ocr(file: UploadFile, db: Session = Depends(get_db)):
    content_type = file.content_type or ""
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    data = await file.read()

    if content_type.startswith("image/") or ext in ("jpg", "jpeg", "png"):
        mime = "image/png" if ext == "png" else "image/jpeg"
        api_key = get_cle_api(db, "cle_env_ocr")  # nom en base, clé au .env ; erreur claire si absent
        try:
            texte = transcribe_image(
                data, mime,
                api_key=api_key,
                model=get_ocr_model(db),          # modèle OCR résolu EN BASE (plus rien en dur dans src)
                max_tokens=get_max_tokens(db, "ocr"),
            )
        except LLMRateLimitError as e:
            raise HTTPException(429, str(e))  # surchargé/trop de demandes : transitoire, pas une panne
        except Exception as e:
            raise HTTPException(500, f"Erreur OCR image : {e}")
        return {"texte": texte}

    elif content_type == "application/pdf" or ext == "pdf":
        # 1) PDF NUMÉRIQUE : couche texte présente → extraction directe (instantané, gratuit).
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
            texte = "\n\n".join(p for p in pages if p.strip())
        except Exception as e:
            raise HTTPException(500, f"Erreur lecture PDF : {e}")
        if len(texte.strip()) >= 50:
            return {"texte": texte}

        # 2) PDF SCANNÉ (pas de couche texte) : on ne rejette plus, on le LIT. Chaque page est
        #    rendue en image et passée dans la même OCR que « Image / Scan ».
        return {"texte": _ocr_pdf_scanne(data, db)}

    raise HTTPException(400, "Type de fichier non supporté.")
