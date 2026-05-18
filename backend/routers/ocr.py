import io
from fastapi import APIRouter, HTTPException, UploadFile

from src.generator import transcribe_image

router = APIRouter()


@router.post("/ocr")
async def ocr(file: UploadFile):
    content_type = file.content_type or ""
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    data = await file.read()

    if content_type.startswith("image/") or ext in ("jpg", "jpeg", "png"):
        mime = "image/png" if ext == "png" else "image/jpeg"
        try:
            texte = transcribe_image(data, mime)
        except Exception as e:
            raise HTTPException(500, f"Erreur OCR image : {e}")
        return {"texte": texte}

    elif content_type == "application/pdf" or ext == "pdf":
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
            texte = "\n\n".join(p for p in pages if p.strip())
        except Exception as e:
            raise HTTPException(500, f"Erreur lecture PDF : {e}")

        if len(texte.strip()) < 50:
            raise HTTPException(
                422,
                "Ce PDF a été scanné en choisissant l'option PDF — même s'il contient du texte "
                "à vos yeux lisible, ce rendu de scanner reste une photo, une image, donc non "
                "exploitable comme un PDF numérique généré par un outil PDF.\n\n"
                "Pour ce genre de document, scannez-le au format image puis utilisez plutôt "
                "le bouton « Image / Scan »."
            )
        return {"texte": texte}

    raise HTTPException(400, "Type de fichier non supporté.")
