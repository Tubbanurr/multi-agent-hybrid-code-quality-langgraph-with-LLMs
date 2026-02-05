"""
LLM-based Semantic Code Judge
Uses LLM to evaluate code quality semantically (algorithm correctness, logic, best practices)

Supports:
- DeepSeek-R1 via Ollama (local, with Chain-of-Thought)
- Llama 3.3 70B via Groq (cloud fallback)
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Configuration
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"


class LLMJudge:
    """
    LLM-based semantic code quality judge.
    
    - Ollama mode: DeepSeek-R1 (with CoT reasoning)
    - Cloud mode: Llama 3.3 70B via Groq
    """
    
    def __init__(self):
        """Initialize judge with appropriate backend."""
        self.use_ollama = USE_OLLAMA
        self.ollama_available = False
        
        # Try Ollama first if enabled
        if self.use_ollama:
            try:
                from module.ollama_client import check_ollama_available
                self.ollama_available = check_ollama_available()
                if self.ollama_available:
                    print("  🤖 LLM Judge: DeepSeek-R1 (Ollama)")
            except ImportError:
                pass
        
        # Initialize Groq as fallback
        if not self.ollama_available:
            try:
                from groq import Groq
                self.groq_api_key = os.getenv("GROQ_API_KEY")
                if self.groq_api_key:
                    self.groq_client = Groq(api_key=self.groq_api_key)
                    print("  🤖 LLM Judge: Llama 3.3 70B (Groq)")
                else:
                    self.groq_client = None
            except ImportError:
                self.groq_client = None
        else:
            self.groq_client = None
        
        self.model = "llama-3.3-70b-versatile"
    
    def evaluate_code(self, code: str, prompt: str) -> Dict[str, Any]:
        """
        Evaluates code semantically using LLM.
        
        Args:
            code: The Python code to evaluate
            prompt: The original user request/prompt
        
        Returns:
            {
                "semantic_score": 0-100,
                "breakdown": {
                    "algorithm_correctness": 0-25,
                    "code_logic": 0-25,
                    "best_practices": 0-25,
                    "readability": 0-25
                },
                "reasoning": "Detailed explanation...",
                "chain_of_thought": "..." (only for DeepSeek-R1),
                "error": False
            }
        """
        
        # Use Ollama DeepSeek-R1 if available
        if self.use_ollama and self.ollama_available:
            return self._evaluate_with_ollama(code, prompt)
        
        # Fallback to Groq
        return self._evaluate_with_groq(code, prompt)
    
    def _evaluate_with_ollama(self, code: str, prompt: str) -> Dict[str, Any]:
        """Evaluate code using DeepSeek-R1 via Ollama."""
        try:
            from module.ollama_client import call_deepseek_r1_judge
            result = call_deepseek_r1_judge(code, prompt)
            return result
        except Exception as e:
            return self._get_fallback_result(f"Ollama evaluation failed: {str(e)}")
    
    def _evaluate_with_groq(self, code: str, prompt: str) -> Dict[str, Any]:
        """Evaluate code using Llama 3.3 70B via Groq."""
        if not self.groq_client:
            return self._get_fallback_result("GROQ_API_KEY not configured")
        
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
        
        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_completion_tokens=512,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Validate and extract scores
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
                "chain_of_thought": "",  # No CoT for Groq
                "error": False
            }
            
        except json.JSONDecodeError as e:
            return self._get_fallback_result(f"JSON decode error: {str(e)}")
        except Exception as e:
            return self._get_fallback_result(f"LLM evaluation failed: {str(e)}")
    
    def _get_fallback_result(self, error_message: str) -> Dict[str, Any]:
        """Return fallback result when LLM evaluation fails."""
        return {
            "semantic_score": 0,
            "breakdown": {
                "algorithm_correctness": 0,
                "code_logic": 0,
                "best_practices": 0,
                "readability": 0
            },
            "reasoning": f"LLM evaluation unavailable: {error_message}",
            "chain_of_thought": "",
            "error": True
        }

