from src.config import AI_PROVIDER, AI_API_KEY, AI_MODEL


def generate(
    prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float | None = None,
    json_mode: bool = False,
) -> str:
    """Point d'entrée UNIQUE pour tout appel LLM texte.

    Les paramètres sont des INTENTIONS métier neutres (« combien de tokens »,
    « du JSON », « déterministe »), jamais des formats fournisseur. Chaque
    adaptateur les traduit dans la langue de son fournisseur — ou les ignore
    quand le fournisseur ne les accepte pas (ex. temperature chez Anthropic).

    `model` : modèle résolvé par l'appelant (côté backend, lu en base à chaud).
    `None` ⇒ repli sur AI_MODEL (config/.env) — rétro-compatible. generate() reste
    pur : il ne lit aucune base, il reçoit la chaîne déjà résolue.
    """
    if AI_PROVIDER == "gemini":
        return _gemini(prompt, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode)
    elif AI_PROVIDER == "groq":
        return _groq(prompt, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode)
    elif AI_PROVIDER == "anthropic":
        return _anthropic(prompt, model=model, max_tokens=max_tokens, temperature=temperature, json_mode=json_mode)
    else:
        raise ValueError(f"Fournisseur inconnu : {AI_PROVIDER}")


def _groq(
    prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float | None = None,
    json_mode: bool = False,
) -> str:
    import requests
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model or AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        body["temperature"] = temperature
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    response = requests.post(url, headers=headers, json=body, timeout=60)
    if not response.ok:
        raise RuntimeError(f"Erreur {response.status_code}: {response.text}")
    return response.json()["choices"][0]["message"]["content"]


def _gemini(
    prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float | None = None,
    json_mode: bool = False,
) -> str:
    import requests
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model or AI_MODEL}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": AI_API_KEY}
    generation_config: dict = {"maxOutputTokens": max_tokens}
    if temperature is not None:
        generation_config["temperature"] = temperature
    if json_mode:
        generation_config["responseMimeType"] = "application/json"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }
    response = requests.post(url, headers=headers, params=params, json=body, timeout=60)
    if not response.ok:
        raise RuntimeError(f"Erreur {response.status_code}: {response.text}")
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


def transcribe_audio(audio_bytes: bytes) -> str:
    import requests
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {AI_API_KEY}"}
    files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
    data = {"model": "whisper-large-v3", "language": "fr"}
    response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    if not response.ok:
        raise RuntimeError(f"Erreur transcription {response.status_code}: {response.text}")
    return response.json()["text"]


def transcribe_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    import base64
    import requests
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    body = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
                },
                {
                    "type": "text",
                    "text": "Extrais tout le texte visible sur ce document de façon fidèle, sans reformuler ni résumer. Retourne uniquement le texte brut.",
                },
            ],
        }],
        "max_tokens": 2048,
    }
    response = requests.post(url, headers=headers, json=body, timeout=60)
    if not response.ok:
        raise RuntimeError(f"Erreur OCR {response.status_code}: {response.text}")
    return response.json()["choices"][0]["message"]["content"]


def _anthropic(
    prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = 2048,
    temperature: float | None = None,
    json_mode: bool = False,
) -> str:
    import anthropic
    # temperature : volontairement IGNORÉE — les modèles Claude Opus 4.x la
    # rejettent (400). Le déterminisme se pilote par le prompt, pas par ce param.
    # json_mode : Claude n'a pas de response_format. Sans schéma JSON (le métier
    # parse en tolérant), on force le JSON par instruction système — jamais en
    # recopiant le dict response_format de Groq.
    kwargs = {
        "model": model or AI_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if json_mode:
        kwargs["system"] = "Réponds uniquement avec du JSON valide, sans aucun texte avant ni après."
    # timeout=60 s (secondes côté SDK Python) — voie propre du SDK, aligné sur les
    # autres branches LLM (requests timeout=60). Sans ça, le SDK attendrait 10 min.
    client = anthropic.Anthropic(api_key=AI_API_KEY, timeout=60)
    message = client.messages.create(**kwargs)
    return message.content[0].text
