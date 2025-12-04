from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
import requests
import os
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from groq import Groq
client = Groq(api_key="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")

# -------------------------------------------------
# FastAPI instance (⚠️ Uvicorn app burada!)
# -------------------------------------------------
app = FastAPI()

app.mount("/static", StaticFiles(directory="."), name="static")

# -------------------------------------------------
# MODEL API ANAHTARLARI
# -------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "*AIzaSyCOdk8m7wR0gUCi5doI-53ZzCvDVhUEV_0*")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-6745ce2c1b7743d9a3d74b9079e3b9ff")

class PromptRequest(BaseModel):
    prompt: str

# -------------------------------------------------
# MODELLER
# -------------------------------------------------
def call_codellama(prompt: str):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=1,
            max_completion_tokens=1024
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Groq API Hatası: {e}"

def call_deepseek(prompt: str):
    # DeepSeek geçici olarak devre dışı bırakıldı; HF izinleri yok.
    return "DeepSeek şu anda pasif (HF izin sorunu)."

def call_gemini(prompt: str):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(url, json=payload, timeout=40)
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Gemini API Hatası: {e}"

# -------------------------------------------------
# TEST ENDPOINT — API ÇALIŞIYOR MU?
# -------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def serve_index():
    with open("index.html", "r", encoding="utf-8") as file:
        return file.read()

# -------------------------------------------------
# ANA ENDPOINT — MODEL SONUÇLARI
# -------------------------------------------------
@app.post("/generate-code")
def generate_code(req: PromptRequest) -> Dict:
    prompt = req.prompt

    return {
        "prompt": prompt,
        "models": {
            "CodeLlama": call_codellama(prompt),
            "DeepSeek-V3": call_deepseek(prompt),
            "Gemini 2.5": call_gemini(prompt)
        }
    }
