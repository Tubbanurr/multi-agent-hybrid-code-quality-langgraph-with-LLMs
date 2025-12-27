from typing import TypedDict, Dict, Any
# 	Tüm ajanların ortak konuşma dilidir
#   LangGraph’in taşıdığı hafızayı tanımlar
class AgentState(TypedDict):
    prompt: str
    codes: Dict[str, str]
    metrics: Dict[str, Any]
    winner: str