"""
Ollama LLM Client Module
Provides unified interface for local LLM models via Ollama.
"""

import os
import requests
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Model configurations (optimized for 24GB RAM)
OLLAMA_MODELS = {
    "judge": os.getenv("OLLAMA_JUDGE_MODEL", "deepseek-r1:14b"),
    "coder_1": os.getenv("OLLAMA_CODER_MODEL_1", "qwen2.5-coder:7b"),
    "coder_2": os.getenv("OLLAMA_CODER_MODEL_2", "codellama:7b"),
    "coder_3": os.getenv("OLLAMA_CODER_MODEL_3", "llama3.1:8b"),
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

def call_deepseek_r1_judge(code: str, prompt: str) -> Dict[str, Any]:
    """
    Evaluate code using DeepSeek-R1 with Chain-of-Thought reasoning.
    
    DeepSeek-R1 outputs reasoning in <think>...</think> blocks.
    We parse this to extract both the reasoning and the final JSON scores.
    
    Returns:
        {
            "semantic_score": 0-100,
            "breakdown": {
                "algorithm_correctness": 0-25,
                "code_logic": 0-25,
                "best_practices": 0-25,
                "readability": 0-25
            },
            "reasoning": "...",
            "chain_of_thought": "...",  # Raw CoT from <think> block
            "error": False
        }
    """
    system_prompt = """You are an expert Python code reviewer with deep knowledge of algorithms, design patterns, and best practices.

Evaluate the given code based on these 4 criteria (each 0-25 points):

1. **Algorithm Correctness** (0-25): Does the code correctly solve the stated problem? Are there bugs or edge cases not handled?

2. **Code Logic** (0-25): Is the logic sound and efficient? Are there better algorithmic approaches? Is it optimized?

3. **Best Practices** (0-25): Does it follow Python best practices? (PEP8, naming, error handling, modularity, etc.)

4. **Readability** (0-25): Is the code clear and easy to understand? Good variable names? Comments where needed?

Return ONLY a valid JSON object with this exact structure (no markdown, no code blocks):
{
  "algorithm_correctness": <number 0-25>,
  "code_logic": <number 0-25>,
  "best_practices": <number 0-25>,
  "readability": <number 0-25>,
  "reasoning": "<brief 1-2 sentence explanation of the scores>"
}"""

    user_prompt = f"""Original Request: {prompt}

Generated Code:
```python
{code}
```

Evaluate this code and return JSON scores."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Call DeepSeek-R1 with JSON format
    response = call_ollama_chat(
        model=OLLAMA_MODELS["judge"],
        messages=messages,
        temperature=0.1,
        max_tokens=1024,
        timeout=180,  # Longer timeout for CoT reasoning
        format_json=True
    )
    
    # Check for errors
    if response.startswith("Ollama Error:"):
        return {
            "semantic_score": 0,
            "breakdown": {
                "algorithm_correctness": 0,
                "code_logic": 0,
                "best_practices": 0,
                "readability": 0
            },
            "reasoning": response,
            "chain_of_thought": "",
            "error": True
        }
    
    # Parse Chain-of-Thought if present
    chain_of_thought = ""
    json_response = response
    
    # DeepSeek-R1 may include <think>...</think> blocks
    if "<think>" in response and "</think>" in response:
        import re
        think_match = re.search(r"<think>(.*?)</think>", response, re.DOTALL)
        if think_match:
            chain_of_thought = think_match.group(1).strip()
            # Remove think block from response to get JSON
            json_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
    
    # Parse JSON
    try:
        result = json.loads(json_response)
        
        algorithm_correctness = min(25, max(0, result.get("algorithm_correctness", 0)))
        code_logic = min(25, max(0, result.get("code_logic", 0)))
        best_practices = min(25, max(0, result.get("best_practices", 0)))
        readability = min(25, max(0, result.get("readability", 0)))
        
        semantic_score = algorithm_correctness + code_logic + best_practices + readability
        
        return {
            "semantic_score": semantic_score,
            "breakdown": {
                "algorithm_correctness": algorithm_correctness,
                "code_logic": code_logic,
                "best_practices": best_practices,
                "readability": readability
            },
            "reasoning": result.get("reasoning", "No reasoning provided"),
            "chain_of_thought": chain_of_thought,
            "error": False
        }
        
    except json.JSONDecodeError as e:
        return {
            "semantic_score": 0,
            "breakdown": {
                "algorithm_correctness": 0,
                "code_logic": 0,
                "best_practices": 0,
                "readability": 0
            },
            "reasoning": f"JSON parse error: {str(e)}",
            "chain_of_thought": chain_of_thought,
            "error": True
        }
