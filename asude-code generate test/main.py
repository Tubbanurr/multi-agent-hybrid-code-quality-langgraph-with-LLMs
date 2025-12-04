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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCOdk8m7wR0gUCi5doI-53ZzCvDVhUEV_0")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "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")

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
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=40)
        data = res.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        return f"DeepSeek Yanıtı Beklenmeyen Format: {data}"
    except Exception as e:
        return f"DeepSeek API Hatası: {e}"

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
from module.code_quality import compare_models

@app.post("/analyze-results")
def analyze_results(payload: dict):
    llama = payload["llama"]
    deepseek = payload["deepseek"]
    gemini = payload["gemini"]

    return compare_models(llama, deepseek, gemini)