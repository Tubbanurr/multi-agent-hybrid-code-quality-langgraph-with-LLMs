"""
Ollama LLM Client Module
Provides unified interface for local LLM models via Ollama.
"""

import os
import requests
import json
import re
from typing import Optional, Dict, Any
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Model configurations (optimized for 24GB RAM)
OLLAMA_MODELS = {
    "judge": os.getenv("OLLAMA_JUDGE_MODEL", "deepseek-r1:7b"),
    "coder_1": os.getenv("OLLAMA_CODER_MODEL_1", "qwen2.5-coder:7b"),
    "coder_2": os.getenv("OLLAMA_CODER_MODEL_2", "codellama:7b"),
    "coder_3": os.getenv("OLLAMA_CODER_MODEL_3", "deepseek-r1:1.5b"),
}


def check_ollama_available() -> bool:
    """Check if Ollama service is running."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/version", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def list_ollama_models() -> list:
    """List available models in Ollama."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        return []
    except requests.RequestException:
        return []


def call_ollama(
    model: str,
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.1,
    max_tokens: int = 2048,
    timeout: int = 120
) -> str:
    """
    Generic Ollama API call.
    
    Args:
        model: Model name (e.g., 'qwen2.5-coder:7b')
        prompt: User prompt
        system_prompt: System instruction
        temperature: Generation temperature (0-1)
        max_tokens: Maximum tokens to generate
        timeout: Request timeout in seconds
    
    Returns:
        Generated text or error message
    """
    if not check_ollama_available():
        return "Ollama Error: Service not available. Please start Ollama."
    
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            return f"Ollama Error: HTTP {response.status_code}"
            
    except requests.Timeout:
        return f"Ollama Error: Request timeout ({timeout}s)"
    except requests.RequestException as e:
        return f"Ollama Error: {str(e)}"


def call_ollama_chat(
    model: str,
    messages: list,
    temperature: float = 0.1,
    max_tokens: int = 2048,
    timeout: int = 120,
    format_json: bool = False
) -> str:
    """
    Ollama chat API call (for multi-turn conversations).
    
    Args:
        model: Model name
        messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
        temperature: Generation temperature
        max_tokens: Maximum tokens
        timeout: Request timeout
        format_json: Force JSON output format
    
    Returns:
        Generated text or error message
    """
    if not check_ollama_available():
        return "Ollama Error: Service not available. Please start Ollama."
    
    try:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if format_json:
            payload["format"] = "json"
        
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json=payload,
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("message", {}).get("content", "")
        else:
            return f"Ollama Error: HTTP {response.status_code}"
            
    except requests.Timeout:
        return f"Ollama Error: Request timeout ({timeout}s)"
    except requests.RequestException as e:
        return f"Ollama Error: {str(e)}"


# --- Code Generation Functions ---

def call_qwen_coder(prompt: str) -> str:
    """
    Generate code using Qwen2.5-Coder via Ollama.
    Best for: Code generation, bug fixing, code understanding.
    """
    system_prompt = (
        "You are an expert Python programmer. Write clean, efficient code. "
        "Output ONLY the code or markdown with code blocks. Do not be conversational."
    )
    return call_ollama(
        model=OLLAMA_MODELS["coder_1"],
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.1,
        max_tokens=2048
    )


def call_codellama_ollama(prompt: str) -> str:
    """
    Generate code using CodeLlama via Ollama.
    Best for: Pure code generation, code completion.
    """
    system_prompt = (
        "You are an expert Python programmer. Write clean, efficient code. "
        "Output ONLY the code."
    )
    return call_ollama(
        model=OLLAMA_MODELS["coder_2"],
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.1,
        max_tokens=2048
    )


def call_llama31(prompt: str) -> str:
    """
    Generate code using Llama 3.1 via Ollama.
    Best for: Complex prompt understanding, instruction following.
    """
    system_prompt = (
        "You are an expert Python programmer. Write clean, efficient code. "
        "Output ONLY the code."
    )
    return call_ollama(
        model=OLLAMA_MODELS["coder_3"],
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.1,
        max_tokens=2048
    )


# --- DeepSeek R1 Judge Function ---

def call_ollama_judge(code: str, prompt: str) -> Dict[str, Any]:
    """
    Evaluate code using the configured Ollama judge model.
    Supports CoT reasoning (like DeepSeek-R1) and standard models (like Phi-4).
    """
    system_prompt = """You are an expert Python code reviewer.
Evaluate the code on 4 criteria (0-25 points each):
1. Algorithm Correctness
2. Code Logic
3. Best Practices
4. Readability

Return ONLY a JSON object:
{
  "algorithm_correctness": <0-25>,
  "code_logic": <0-25>,
  "best_practices": <0-25>,
  "readability": <0-25>,
  "reasoning": "<1-2 sentence explanation>"
}"""

    user_prompt = f"""EVALUATION TASK:
Please evaluate the following Python code based on the original user prompt.

[ORIGINAL USER PROMPT]:
{prompt}

[CODE TO EVALUATE]:
{code}

---
Remember: Your response must be in strict JSON format as specified in the system instructions."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Determine if we should force JSON format
    # For R1 series, we want False to capture <think> blocks via raw text
    # For others (phi4, codellama, etc.), True is much safer.
    judge_model = OLLAMA_MODELS["judge"].lower()
    is_r1 = "r1" in judge_model
    force_json = not is_r1
    
    response = call_ollama_chat(
        model=OLLAMA_MODELS["judge"],
        messages=messages,
        temperature=0.1,
        max_tokens=1024,
        timeout=240,
        format_json=force_json
    )
    
    # Error check
    if response.startswith("Ollama Error:"):
        return _get_error_result(response)
    
    # Parse Chain-of-Thought
    chain_of_thought = ""
    try:
        # JSON extraction logic
        # 1. Handle CoT
        if "<think>" in response:
            think_match = re.search(r"<think>(.*?)</think>", response, re.DOTALL)
            if think_match:
                chain_of_thought = think_match.group(1).strip()
            response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
        
        # 2. Extract JSON from potential markdown/conversational text
        # Use a more robust regex that finds the first { and last }
        json_match = re.search(r"(\{.*\})", response, re.DOTALL)
        if json_match:
            json_payload = json_match.group(1).strip()
        else:
            json_payload = response.strip()

        try:
            result = json.loads(json_payload)
        except json.JSONDecodeError:
            # Fallback: Try regex extraction of scores if JSON fails
            print(f"  ⚠️  JSON parse failed, attempting regex fallback for scores...")
            ac_match = re.search(r'"algorithm_correctness":\s*(\d+)', response)
            cl_match = re.search(r'"code_logic":\s*(\d+)', response)
            bp_match = re.search(r'"best_practices":\s*(\d+)', response)
            rd_match = re.search(r'"readability":\s*(\d+)', response)
            
            if ac_match and cl_match and bp_match and rd_match:
                result = {
                    "algorithm_correctness": int(ac_match.group(1)),
                    "code_logic": int(cl_match.group(1)),
                    "best_practices": int(bp_match.group(1)),
                    "readability": int(rd_match.group(1)),
                    "reasoning": "Extracted via regex fallback"
                }
            else:
                raise ValueError("Could not extract scores via regex fallback")

        # Scores
        ac = min(25, max(0, int(result.get("algorithm_correctness", 0))))
        cl = min(25, max(0, int(result.get("code_logic", 0))))
        bp = min(25, max(0, int(result.get("best_practices", 0))))
        rd = min(25, max(0, int(result.get("readability", 0))))
        total = ac + cl + bp + rd
        
        # Reasoning
        reasoning = result.get("reasoning", "")
        if not reasoning or reasoning == "No reasoning provided":
            reasoning = generate_auto_reasoning(ac, cl, bp, rd)
            
        return {
            "semantic_score": total,
            "breakdown": {
                "algorithm_correctness": ac,
                "code_logic": cl,
                "best_practices": bp,
                "readability": rd
            },
            "reasoning": reasoning,
            "chain_of_thought": chain_of_thought,
            "error": False
        }
        
    except (json.JSONDecodeError, ValueError, TypeError, Exception) as e:
        return _get_error_result(f"Judge error: {str(e)} | Raw snippet: {response[:100]}...", chain_of_thought)


def generate_auto_reasoning(ac, cl, bp, rd) -> str:
    """Generate a readable reasoning string from scores."""
    parts = []
    if ac >= 20: parts.append("Algoritma doğru")
    elif ac >= 10: parts.append("Algoritma kısmen doğru")
    else: parts.append("Algoritmada ciddi hatalar var")
    
    if cl >= 20: parts.append("mantık sağlam")
    elif cl >= 10: parts.append("mantık geliştirilebilir")
    
    if bp >= 20: parts.append("en iyi pratiklere uygun")
    elif bp >= 10: parts.append("pratiklerde eksikler var")
    
    if rd >= 20: parts.append("okunabilirlik yüksek")
    
    return f"Hibrid Değerlendirme (Skor {ac+cl+bp+rd}/100): " + ", ".join(parts) + "."


def _get_error_result(msg: str, cot: str = "") -> Dict[str, Any]:
    return {
        "semantic_score": 0,
        "breakdown": {"algorithm_correctness": 0, "code_logic": 0, "best_practices": 0, "readability": 0},
        "reasoning": msg,
        "chain_of_thought": cot,
        "error": True
    }

