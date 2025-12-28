from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from dotenv import load_dotenv
import json
import ast
import re

# Load env variables
load_dotenv()

# --- Clients ---
# 1. Llama via Groq
llama_llm = ChatGroq(
    temperature=0.1, 
    model_name="llama-3.3-70b-versatile", 
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# 2. DeepSeek via Groq (or OpenRouter if preferred, using Groq mostly for speed/convenience if available)
# Since the user had DeepSeek key, let's stick to standard requests for DeepSeek if library support is thin,
# BUT for LangGraph uniformity, wrapping it in a simple function or Using consistent clients is better.
# For this demo, let's use the explicit `call_deepseek` logic from `llm_clients` inside the node
# to avoid complex custom LangChain wrapper implementation.
from module.llm_clients import call_deepseek

# 3. Gemini Integ
gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.1
)

# --- State ---
class AgentState(TypedDict):
    prompt: str
    code_llama: str
    code_deepseek: str
    code_gemini: str
    judge_result: Dict[str, Any] # stores "winner", "reasoning", "scores"

# --- Nodes ---

def generate_competitors(state: AgentState) -> AgentState:
    """Generates code from all 3 models in parallel (conceptually)."""
    # If codes are already provided (e.g. from UI manual input), skip generation
    if state.get("code_llama") and state.get("code_deepseek") and state.get("code_gemini"):
        return {}

    prompt = state["prompt"]
    
    # 1. Llama (using LangChain wrapper)
    try:
        msg = [
            SystemMessage(content="You are an expert Python programmer. Output ONLY code."),
            HumanMessage(content=prompt)
        ]
        res = llama_llm.invoke(msg)
        llama_code = res.content
    except Exception as e:
        llama_code = f"Error: {e}"

    # 2. DeepSeek (using our specific function)
    deepseek_code = call_deepseek(prompt)

    # 3. Gemini (using LangChain wrapper)
    try:
        msg = [
            SystemMessage(content="You are an expert Python programmer. Output ONLY code."),
            HumanMessage(content=prompt)
        ]
        res = gemini_llm.invoke(msg)
        gemini_code = res.content
    except Exception as e:
        gemini_code = f"Error: {e}"

    return {
        "code_llama": llama_code,
        "code_deepseek": deepseek_code,
        "code_gemini": gemini_code
    }

def judge_solutions(state: AgentState) -> AgentState:
    """Evaluating the 3 solutions using Gemini Pro as a Judge."""
    
    llama = state["code_llama"]
    deepseek = state["code_deepseek"]
    gemini = state["code_gemini"]
    prompt = state["prompt"]

    judge_prompt = f"""
    You are an expert Senior Software Architect and Code Reviewer.
    
    User Request: {prompt}

    Option 1 (Llama):
    {llama}

    Option 2 (DeepSeek):
    {deepseek}

    Option 3 (Gemini):
    {gemini}

    Evaluate these 3 snippets based on:
    1. Correctness (Does it solve the user request?)
    2. Efficiency (Big O, resource usage)
    3. Style (Cleanliness, comments, naming conventions)
    4. Safety (No vulnerabilities)

    Output JSON ONLY in this format:
    {{
        "winner": "CodeLlama" | "DeepSeek-V3" | "Gemini 2.5",
        "reasoning": "A short paragraph explaining why the winner was chosen and comparison of others.",
        "scores": {{
            "CodeLlama": {{ "syntax": 20, "cleanliness": 0-15, "oop": 0-20, "complexity": 0-20, "total": 0-100 }},
            "DeepSeek-V3": {{ "syntax": 20, "cleanliness": 0-15, "oop": 0-20, "complexity": 0-20, "total": 0-100 }},
            "Gemini 2.5": {{ "syntax": 20, "cleanliness": 0-15, "oop": 0-20, "complexity": 0-20, "total": 0-100 }}
        }}
    }}
    """

    try:
        # Use Llama 3 (Groq) for Judging because Gemini hit Rate Limit
        # Llama 3 is a very capable judge as well.
        res = llama_llm.invoke([
            SystemMessage(content="You are a strict JSON-only outputting machine. No markdown, no preambles."),
            HumanMessage(content=judge_prompt)
        ])
        content = res.content
        
        # Clean markdown json
        content = content.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(content)
        
        # --- Normalization Block ---
        # Map common aliases to standard keys
        normalization_map = {
            "Llama": "CodeLlama", "Llama 3": "CodeLlama", "LLaMA3": "CodeLlama", "CodeLlama": "CodeLlama",
            "DeepSeek": "DeepSeek-V3", "DeepSeek V3": "DeepSeek-V3", "DeepSeek-V3": "DeepSeek-V3",
            "Gemini": "Gemini 2.5", "Gemini 2.5": "Gemini 2.5", "Gemini Pro": "Gemini 2.5"
        }
        
        # Normalize Winner
        raw_winner = result_json.get("winner", "CodeLlama")
        normalized_winner = normalization_map.get(raw_winner, raw_winner)
        # If still not in expected keys, pick the one with max score manually? 
        # For now, just trust map or fallback.
        if normalized_winner not in ["CodeLlama", "DeepSeek-V3", "Gemini 2.5"]:
             normalized_winner = "CodeLlama" # Safe fallback
        
        result_json["winner"] = normalized_winner
        
        # Normalize Scores Keys (The LLM might have messed up keys in the dict too)
        new_scores = {}
        for k, v in result_json.get("scores", {}).items():
            norm_k = normalization_map.get(k, k)
            if norm_k in ["CodeLlama", "DeepSeek-V3", "Gemini 2.5"]:
                new_scores[norm_k] = v
        
        # Fill missing keys with 0
        for key in ["CodeLlama", "DeepSeek-V3", "Gemini 2.5"]:
            if key not in new_scores:
                new_scores[key] = {"total": 0, "syntax": 0, "cleanliness": 0, "oop": 0, "complexity": 0}
                
        result_json["scores"] = new_scores
        # ---------------------------

    except Exception as e:
        # Fallback if judge fails
        result_json = {
            "winner": "CodeLlama", # Use a valid key so JS doesn't crash on .total access
            "reasoning": f"Analiz sırasında hata oluştu: {e}. Lütfen tekrar deneyin.",
            "scores": {
                "CodeLlama": {"total": 0, "syntax": 0},
                "DeepSeek-V3": {"total": 0, "syntax": 0},
                "Gemini 2.5": {"total": 0, "syntax": 0}
            }
        }

    return {"judge_result": result_json}


# --- Graph Construction ---
workflow = StateGraph(AgentState)

workflow.add_node("generate_competitors", generate_competitors)
workflow.add_node("judge_solutions", judge_solutions)

workflow.set_entry_point("generate_competitors")
workflow.add_edge("generate_competitors", "judge_solutions")
workflow.add_edge("judge_solutions", END)

app_graph = workflow.compile()

# Public interface
def run_agent(prompt: str, code_llama: str = "", code_deepseek: str = "", code_gemini: str = ""):
    inputs = {
        "prompt": prompt, 
        "code_llama": code_llama, 
        "code_deepseek": code_deepseek, 
        "code_gemini": code_gemini,
        "judge_result": {}
    }
    result = app_graph.invoke(inputs)
    return result
