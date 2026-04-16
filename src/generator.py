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


def _anthropic(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=AI_API_KEY)
    message = client.messages.create(
        model=AI_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
