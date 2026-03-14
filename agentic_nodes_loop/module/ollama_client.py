"""
Ollama LLM Client Module
Provides unified interface for local LLM models via Ollama.
"""

import os
import requests
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Model configurations (re-read every time for dynamic updates)
def get_ollama_models() -> Dict[str, str]:
    """Dynamically read model configuration from environment."""
    load_dotenv(override=True)
    return {
        "judge": os.getenv("OLLAMA_JUDGE_MODEL", "deepseek-r1:1.5b"),
        "coder_1": os.getenv("OLLAMA_CODER_MODEL_1", "qwen2.5-coder:7b"),
        "coder_2": os.getenv("OLLAMA_CODER_MODEL_2", "qwen2.5-coder:3b"),
        "coder_3": os.getenv("OLLAMA_CODER_MODEL_3", "gemma2:2b"),
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
    timeout: int = 1800
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
    timeout: int = 1800,
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

def validate_code(code: str) -> bool:
    """
    Checks if the generated code is likely valid and not a hallucination.
    """
    if not code:
        return False
    
    clean_code = code.strip().lower()
    
    # Check for extremely short or common hallucination keywords
    if len(clean_code) < 10:
        # If it's just 'ipynb' or '.py' it's garbage
        hallucinations = ["ipynb", "untitled", ".py", "markdown", "python", "sure", "here"]
        if any(h == clean_code for h in hallucinations):
            return False
    
    # Check for conversational filler without code
    if clean_code.startswith("sure") and "def " not in code and "import " not in code:
        return False

    # A valid script MUST have at least one of these major structural markers
    major_markers = ["def ", "import ", " = ", "class ", "print("]
    clean_stripped = code.strip()
    has_major = any(m in clean_stripped for m in major_markers)
    
    # If the output is longer than 40 chars and has NO major markers, it's likely a paragraph/hallucination.
    if len(clean_stripped) > 40:
        return has_major
    # For short strings, must have a major marker
    return has_major


def call_coder_1(prompt: str) -> str:
    """
    Generate code using the model in OLLAMA_CODER_MODEL_1.
    """
    system_prompt = (
        "You are an expert Python programmer. Write a full, working Python implementation. "
        "Output ONLY the code. No markdown backticks, no markdown blocks, no 'Sure, here is...', no explanations. "
        "Just the code itself starting from imports or function definition."
    )
    code = call_ollama(
        model=get_ollama_models()["coder_1"],
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.1,
        max_tokens=2048
    )
    
    if not validate_code(code):
        coder_name = get_ollama_models()["coder_1"]
        print(f"⚠️ {coder_name} hallucination detected, retrying...")
        code = call_ollama(
            model=get_ollama_models()["coder_1"],
            prompt=f"CRITICAL: The previous output was incorrect. Write the actual Python code for: {prompt}",
            system_prompt=system_prompt + " START IMMEDIATELY WITH 'import' OR 'def'. DO NOT WRITE FILE NAMES.",
            temperature=0.3 # Slightly higher temperature for variety on retry
        )
    return code


def call_coder_2(prompt: str) -> str:
    """
    Generate code using the model in OLLAMA_CODER_MODEL_2.
    """
    system_prompt = (
        "You are an expert Python coder. Output raw Python code ONLY. "
        "STRICTLY FORBIDDEN: Do not write '.ipynb', do not write file names, do not write explanations. "
        "Start directly with 'import' or 'def'. No markdown backticks."
    )
    code = call_ollama(
        model=get_ollama_models()["coder_2"],
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.1,
        max_tokens=2048
    )
    
    # Specific check for common Codegemma hallucination
    if not validate_code(code) or ".ipynb" in code.lower():
        coder_name = get_ollama_models()["coder_2"]
        print(f"⚠️ {coder_name} hallucination detected (.ipynb or invalid), retrying...")
        code = call_ollama(
            model=get_ollama_models()["coder_2"],
            prompt=f"CRITICAL: DO NOT WRITE '.ipynb'. Write ACTUAL Python code for: {prompt}",
            system_prompt="PYTHON CODE ONLY. START WITH THE CODE. NO MARKDOWN.",
            temperature=0.3
        )
    return code


def call_coder_3(prompt: str) -> str:
    """
    Generate code using the model in OLLAMA_CODER_MODEL_3.
    """
    system_prompt = (
        "You are a STRICT Python code generator. Output raw Python code ONLY. "
        "NO markdown, NO explanations, NO conversational text, NO hashtags. "
        "If you cannot generate code, output 'print(\"Error\")'. "
        "Example start: import os"
    )
    code = call_ollama(
        model=get_ollama_models()["coder_3"],
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.1,
        max_tokens=2048
    )
    
    if not validate_code(code):
        coder_name = get_ollama_models()["coder_3"]
        print(f"⚠️ {coder_name} hallucination detected, retrying...")
        code = call_ollama(
            model=get_ollama_models()["coder_3"],
            prompt=f"ACTUAL PYTHON CODE ONLY: {prompt}",
            system_prompt=system_prompt,
            temperature=0.3
        )
    return code


# --- DeepSeek R1 Judge Function ---

def safe_int_extract(val: Any) -> int:
    """Extract an integer from various LLM output formats like '0-1', '5/10', or ' 8 '."""
    if isinstance(val, int):
        return val
    if not val:
        return 0
    
    s = str(val).strip()
    # Handle ranges like "0-1" -> take the higher value
    if '-' in s:
        parts = re.findall(r'\d+', s)
        if parts:
            return max(int(p) for p in parts)
    
    # Handle fractions like "8/10" -> take the numerator
    if '/' in s:
        parts = re.findall(r'\d+', s)
        if parts:
            return int(parts[0])
            
    # Default: find first number
    match = re.search(r'\d+', s)
    if match:
        return int(match.group())
        
    return 0

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
    system_prompt = """You are a highly critical Senior Python Architect and Code Reviewer. 
Your goal is to provide a TOUGH and UNBIASED evaluation. DO NOT give high scores unless the code is truly exceptional.

Evaluate the code based on these specific semantic criteria (Max 30 points total):

1. **Identifier Clarity** (0-5): 
   - 5: Perfect PEP8 naming, perfectly descriptive.
   - 3-4: Mostly clear but some vague names (e.g., 'data', 'temp').
   - 1-2: Poor names (e.g., 'a', 'b', 'list1').
   - 0: Obfuscated or completely meaningless.

2. **Prompt Adherence** (0-10): 
   - 10: Implements ALL requirements perfectly, including edge cases.
   - 7-9: Implements core logic but misses a minor constraint or edge case.
   - 4-6: Significant missing features or logic errors.
   - 0-3: Fails to understand the prompt or produces completely wrong algorithm.

3. **Naming Alignment** (0-5): 
   - 5: Uses domain-specific terminology perfectly.
   - 3-4: Acceptable domain names but generic in places.
   - 1-2: Inconsistent or wrong terminology for the requested domain.
   - 0: Completely random names.

4. **Logic & Reliability** (0-10): 
   - 10: Robust, optimized, handles errors, no race conditions, high quality.
   - 7-9: Logic is correct but could be more efficient or lacks advanced error handling.
   - 4-6: Works for simple cases but crashes on empty input or invalid types.
   - 0-3: Broken logic, infinite loops, or major bugs.

Deduct points for:
- Lack of docstrings (-1 or -2)
- Hardcoded values that should be parameters (-1)
- Redundant logic (-1)
- Lack of type hints (-1)

Return ONLY a valid JSON object:
{"identifier_clarity":<0-5>,"prompt_adherence":<0-10>,"naming_alignment":<0-5>,"test_reliability":<0-10>,"reasoning":"<detailed explanation of why points were deducted>"}"""

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
    
    response = call_ollama_chat(
        model=get_ollama_models()["judge"],
        messages=messages,
        temperature=0.1,
        max_tokens=1024,
        timeout=1800,
        format_json=True
    )
    
    if not response or response.strip() == "":
        return {
            "semantic_score": 0,
            "breakdown": {"identifier_clarity": 0, "prompt_adherence": 0, "naming_alignment": 0, "test_reliability": 0},
            "reasoning": "Ollama Error: Empty response.",
            "chain_of_thought": "",
            "error": True
        }
    
    chain_of_thought = ""
    import re
    
    # Extract JSON block more aggressively
    json_response = response
    if "<think>" in response and "</think>" in response:
        think_match = re.search(r"<think>(.*?)</think>", response, re.DOTALL)
        if think_match:
            chain_of_thought = think_match.group(1).strip()
            json_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
    
    # Find the outermost JSON object if model added conversational text
    json_match = re.search(r"(\{.*\})", json_response, re.DOTALL)
    if json_match:
        json_response = json_match.group(1)
    
    try:
        # Clean up common LLM oddities (line breaks inside strings, etc.)
        # but be careful not to break valid JSON
        result = json.loads(json_response)
        
        breakdown = {
            "identifier_clarity": min(5, max(0, safe_int_extract(result.get("identifier_clarity", 0)))),
            "prompt_adherence": min(10, max(0, safe_int_extract(result.get("prompt_adherence", 0)))),
            "naming_alignment": min(5, max(0, safe_int_extract(result.get("naming_alignment", 0)))),
            "test_reliability": min(10, max(0, safe_int_extract(result.get("test_reliability", 0))))
        }
        semantic_score = sum(breakdown.values())
        return {
            "semantic_score": semantic_score,
            "breakdown": breakdown,
            "reasoning": result.get("reasoning", "Evaluated."),
            "chain_of_thought": chain_of_thought,
            "error": False
        }
    except Exception as e:
        # Fallback parsing for common "Unterminated string" or minor formatting errors
        print(f"  ⚠️ JSON Parse Error: {e}. Attempting recovery...")
        
        # Simple regex-based field extraction as emergency fallback
        fallback_breakdown = {"identifier_clarity": 0, "prompt_adherence": 0, "naming_alignment": 0, "test_reliability": 0}
        
        for key in fallback_breakdown.keys():
            match = re.search(rf'"{key}"\s*:\s*"?([\d\-/]+)"?', json_response)
            if match:
                fallback_breakdown[key] = safe_int_extract(match.group(1))
        
        reasoning_match = re.search(r'"reasoning"\s*:\s*"(.*?)"', json_response)
        reasoning = reasoning_match.group(1) if reasoning_match else "Evaluation successful (recovered from partial response)."
        
        # If we got at least some scores, don't return error
        if sum(fallback_breakdown.values()) > 0:
            return {
                "semantic_score": sum(fallback_breakdown.values()),
                "breakdown": fallback_breakdown,
                "reasoning": reasoning,
                "chain_of_thought": chain_of_thought,
                "error": False
            }

        return {
            "semantic_score": 0,
            "breakdown": {"identifier_clarity": 0, "prompt_adherence": 0, "naming_alignment": 0, "test_reliability": 0},
            "reasoning": f"Parse error: {str(e)}",
            "chain_of_thought": chain_of_thought,
            "error": True
        }
