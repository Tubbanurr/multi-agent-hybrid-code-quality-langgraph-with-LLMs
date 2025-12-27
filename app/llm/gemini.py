import requests
from app.config.settings import settings


def call_gemini(prompt: str) -> str:
    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/gemini-2.0-flash:generateContent"
        f"?key={settings.GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        res = requests.post(url, json=payload, timeout=40)
        data = res.json()

        # 🔍 Güvenli kontrol
        if "candidates" not in data:
            return f"[Gemini Error] Unexpected response: {data}"

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"[Gemini Exception] {str(e)}"