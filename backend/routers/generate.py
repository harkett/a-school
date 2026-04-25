from fastapi import APIRouter, HTTPException
from backend.models import GenerateRequest, GenerateResponse
from src.prompts import build_prompt
from src.generator import generate

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
def api_generate(req: GenerateRequest):
    try:
        kwargs = {"niveau": req.niveau}
        if req.sous_type:
            kwargs["sous_type"] = req.sous_type
        if req.nb:
            kwargs["nb"] = req.nb
        prompt = build_prompt(req.activite_key, req.texte, avec_correction=req.avec_correction, **kwargs)
        resultat = generate(prompt)
        return GenerateResponse(resultat=resultat)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
