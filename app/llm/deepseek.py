import requests
from app.config.settings import settings

def call_deepseek(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [{"role": "user", "content": prompt}]
    }

    res = requests.post(url, json=payload, headers=headers, timeout=40)
    return res.json()["choices"][0]["message"]["content"]