from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import os

from module.llm_clients import call_codellama, call_deepseek, call_gemini
from module.agentic_workflow import run_hybrid_workflow  # NEW: Hybrid workflow

app = FastAPI(title="HAVELSAN Hybrid Code Generator")

# Static files setup
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str

@app.get("/", response_class=HTMLResponse)
def serve_index():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        return file.read()

@app.post("/generate")
def generate_endpoint(req: PromptRequest) -> Dict:
    """
    YENİ: Hybrid Workflow Endpoint
    
    1. İlk tur: 3 model (Llama, DeepSeek, Gemini) kod üretir
    2. 4 metrikle analiz → Kazanan seçilir  
    3. Eşik kontrolü:
       - >= 70 → Direkt çıktı
       - < 70 → Feedback döngüsü (sadece kazananla)
    """
    result = run_hybrid_workflow(
        prompt=req.prompt,
        quality_threshold=70.0,
        max_iterations=3
    )
    return result