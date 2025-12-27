from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
# uygulamanın giriş noktası fastAPI' yi başlatır
app = FastAPI(
    title="Agentic Code Generation System",
    description="LangGraph tabanlı çok ajanlı kod üretim ve kalite analizi",
    version="1.0"
)

# API routes
app.include_router(router)

# Frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root → index.html
@app.get("/")
def root():
    return {"message": "Uygulama çalışıyor. /static/index.html aç."}