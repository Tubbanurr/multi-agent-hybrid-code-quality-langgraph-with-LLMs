from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import threading
import uuid
import logging
import os
from datetime import datetime

from module.llm_clients import call_codellama, call_deepseek, call_gemini
from module.agentic_workflow import run_hybrid_workflow

# /status/ polling isteklerini access log'dan gizle
class SuppressStatusLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/status/" not in record.getMessage()

logging.getLogger("uvicorn.access").addFilter(SuppressStatusLogs())


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

# --- In-memory Job Store ---
# {job_id: {"status": "pending"|"running"|"done"|"error", "result": ..., "error": ...}}
jobs: Dict[str, Dict[str, Any]] = {}
jobs_lock = threading.Lock()


class PromptRequest(BaseModel):
    prompt: str
    static_weight: float = 0.7
    llm_weight: float = 0.3
    metric_weights: Dict[str, int] = None


@app.get("/", response_class=HTMLResponse)
def serve_index():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        return file.read()


def run_workflow_background(job_id: str, req: PromptRequest):
    """Background thread'de workflow çalıştır, sonucu job store'a yaz."""
    with jobs_lock:
        jobs[job_id]["status"] = "running"
    try:
        result = run_hybrid_workflow(
            prompt=req.prompt,
            quality_threshold=85.0,
            max_iterations=10,
            static_weight=req.static_weight,
            llm_weight=req.llm_weight,
            metric_weights=req.metric_weights
        )
        with jobs_lock:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["result"] = result
    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)


@app.post("/generate")
async def generate_endpoint(req: PromptRequest) -> Dict:
    """
    İsteği anında kabul et, arka planda çalıştır, job_id döndür.
    Frontend /status/{job_id} ile sonucu sorgular (polling).
    """
    job_id = f"job_{uuid.uuid4().hex[:12]}"

    with jobs_lock:
        jobs[job_id] = {
            "status": "pending",
            "result": None,
            "error": None,
            "created_at": datetime.now().isoformat()
        }

    # Arka planda başlat — HTTP bağlantısı ANINDA kapanır
    thread = threading.Thread(
        target=run_workflow_background,
        args=(job_id, req),
        daemon=True
    )
    thread.start()

    return {"job_id": job_id, "status": "pending"}


@app.get("/status/{job_id}")
async def get_status(job_id: str) -> Dict:
    """
    Job durumunu sorgula.
    Returns: {"status": "pending"|"running"|"done"|"error", "result": {...}, "error": "..."}
    """
    with jobs_lock:
        job = jobs.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job bulunamadı: {job_id}")

    return {
        "status": job["status"],
        "result": job.get("result"),
        "error": job.get("error"),
    }