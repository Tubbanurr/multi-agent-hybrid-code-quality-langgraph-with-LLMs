from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import os

from module.llm_clients import call_codellama, call_deepseek, call_gemini
from module.agent_graph import run_agent
# from module.code_quality import compare_models # Old regex based
from module.advanced_judge import advanced_judge  # NEW: Static analysis based

app = FastAPI(title="HAVELSAN Code Generator")

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

class AnalysisRequest(BaseModel):
    llama: str
    deepseek: str
    gemini: str
    prompt: str = "Analyze these codes" # Optional prompt context

@app.get("/", response_class=HTMLResponse)
def serve_index():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        return file.read()

@app.post("/generate-code")
def generate_code_endpoint(req: PromptRequest) -> Dict:
    prompt = req.prompt
    # We keep the direct calls here for speed, or we COULD use the graph 'generate_competitors' node.
    # For now, let's keep it fast.
    return {
        "prompt": prompt,
        "models": {
            "CodeLlama": call_codellama(prompt),
            "DeepSeek-V3": call_deepseek(prompt),
            "Gemini 2.5": call_gemini(prompt)
        }
    }

@app.post("/analyze-results")
def analyze_results_endpoint(payload: AnalysisRequest):
    # Use the LangGraph Agent to judge
    result = run_agent(
        prompt=payload.prompt,
        code_llama=payload.llama,
        code_deepseek=payload.deepseek,
        code_gemini=payload.gemini
    )
    
    # The result['judge_result'] contains {winner, reasoning, scores}
    return result["judge_result"]

@app.post("/analyze-advanced")
def analyze_advanced_endpoint(payload: AnalysisRequest):
    """
    Advanced static analysis using Pylint, Radon, Bandit, Flake8, AST.
    More objective and deterministic than LLM-based judging.
    Returns detailed breakdown with 6-layer analysis.
    """
    result = advanced_judge(
        code_llama=payload.llama,
        code_deepseek=payload.deepseek,
        code_gemini=payload.gemini
    )
    return result