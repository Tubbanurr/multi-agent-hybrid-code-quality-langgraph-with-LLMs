from fastapi import APIRouter
from app.schemas.requests import PromptRequest
from app.graph.graph import build_graph

router = APIRouter()
graph = build_graph()

@router.post("/generate-code")
def generate_code(req: PromptRequest):
    result = graph.invoke({
        "prompt": req.prompt,
        "codes": {},
        "metrics": {},
        "winner": ""
    })

    return {
        "models": result["codes"],
        "metrics": result["metrics"],
        "winner": result["winner"]
    }