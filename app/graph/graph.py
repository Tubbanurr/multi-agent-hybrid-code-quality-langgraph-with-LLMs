from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.agents.generation.code_generation_agent import CodeGenerationAgent
from app.agents.quality.code_quality_agent import CodeQualityAgent
#	 	LangGraph akışını tanımlar
#       Hangi agent, hangi sırayla çalışacak → burada
def build_graph():
    graph = StateGraph(AgentState)

    gen = CodeGenerationAgent()
    quality = CodeQualityAgent()

    graph.add_node("generate", gen.run)
    graph.add_node("code_quality", quality.run)

    graph.set_entry_point("generate")
    graph.add_edge("generate", "code_quality")
    graph.add_edge("code_quality", END)

    return graph.compile()