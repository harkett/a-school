from src.config import AI_PROVIDER, AI_API_KEY, AI_MODEL


def generate(prompt: str) -> str:
    if AI_PROVIDER == "gemini":
        return _gemini(prompt)
    elif AI_PROVIDER == "groq":
        return _groq(prompt)
    elif AI_PROVIDER == "anthropic":
        return _anthropic(prompt)
    else:
        raise ValueError(f"Fournisseur inconnu : {AI_PROVIDER}")


def _groq(prompt: str) -> str:
    import requests
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
    }
    response = requests.post(url, headers=headers, json=body, timeout=60)
    if not response.ok:
        raise RuntimeError(f"Erreur {response.status_code}: {response.text}")
    return response.json()["choices"][0]["message"]["content"]


def _gemini(prompt: str) -> str:
    import requests
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{AI_MODEL}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": AI_API_KEY}
    body = {"contents": [{"parts": [{"text": prompt}]}]}
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


def _anthropic(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=AI_API_KEY)
    message = client.messages.create(
        model=AI_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
