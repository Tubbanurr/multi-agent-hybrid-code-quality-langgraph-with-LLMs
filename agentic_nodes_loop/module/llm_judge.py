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
                from module.ollama_client import check_ollama_available, get_ollama_models
                self.ollama_available = check_ollama_available()
                if self.ollama_available:
                    judge_model = get_ollama_models()["judge"]
                    print(f"  🤖 LLM Judge: {judge_model} (Ollama)")
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

    def get_model_name(self) -> str:
        """Return the current judge model name."""
        if self.ollama_available:
            from module.ollama_client import get_ollama_models
            return get_ollama_models()["judge"]
        return self.model
    
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
                    "identifier_clarity": 0-5,
                    "prompt_adherence": 0-10,
                    "naming_alignment": 0-5,
                    "test_reliability": 0-10
                },
                "reasoning": "Detailed explanation...",
                "chain_of_thought": "..." (only for DeepSeek-R1),
                "error": False
            }
        """
        # Clean the input code to remove conversational text and markdown formatting
        from module.advanced_judge import AdvancedCodeJudge
        judge_instance = AdvancedCodeJudge()
        clean = judge_instance.clean_code(code)

        # Pre-check: Detect garbage or non-code hallucinations
        from module.ollama_client import validate_code
        if not validate_code(clean):
            return {
                "semantic_score": 0,
                "breakdown": {
                    "identifier_clarity": 0,
                    "prompt_adherence": 0,
                    "naming_alignment": 0,
                    "test_reliability": 0
                },
                "reasoning": "Output detected as non-code/hallucination. Scoring zero.",
                "chain_of_thought": "",
                "error": False
            }
        
        # Use Ollama DeepSeek-R1 if available
        if self.use_ollama and self.ollama_available:
            return self._evaluate_with_ollama(clean, prompt)
        
        # Fallback to Groq
        return self._evaluate_with_groq(clean, prompt)
    
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
        
        system_prompt = """You are a highly critical Senior Python Architect and Code Reviewer. 
Your goal is to provide a TOUGH and UNBIASED evaluation. DO NOT give high scores unless the code is truly exceptional.

Evaluate the code based on these specific semantic criteria (Max 30 points total):

1. **Identifier Clarity** (0-5): 
   - 5: Perfect PEP8 naming, perfectly descriptive.
   - 3-4: Mostly clear but some vague names.
   - 1-2: Poor or generic names.
   - 0: Obfuscated or meaningless.

2. **Prompt Adherence** (0-10): 
   - 10: Implements ALL requirements perfectly, including edge cases.
   - 7-9: Implements core logic but misses a minor constraint.
   - 4-6: Significant missing features.
   - 0-3: Fails to understand the prompt.

3. **Naming Alignment** (0-5): 
   - 5: Uses domain-specific terminology perfectly.
   - 1-4: Inconsistent or generic terminology.

4. **Logic & Reliability** (0-10): 
   - 10: Robust, optimized, handles errors, high quality.
   - 0-9: Deduct points for inefficiency, lack of error handling, or bugs.

Deduct 1-2 points from `test_reliability` for:
- Hardcoded values
- Bad architectural choices or inefficiencies

Return ONLY a valid JSON object:
{
  "identifier_clarity": <number 0-5>,
  "prompt_adherence": <number 0-10>,
  "naming_alignment": <number 0-5>,
  "test_reliability": <number 0-10>,
  "reasoning": "<detailed explanation of score deductions IN TURKISH LANGUAGE>"
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
            
            breakdown = {
                "identifier_clarity": min(5, max(0, int(result.get("identifier_clarity", 0)))),
                "prompt_adherence": min(10, max(0, int(result.get("prompt_adherence", 0)))),
                "naming_alignment": min(5, max(0, int(result.get("naming_alignment", 0)))),
                "test_reliability": min(10, max(0, int(result.get("test_reliability", 0))))
            }
            
            semantic_score = sum(breakdown.values())
            
            return {
                "semantic_score": semantic_score,
                "breakdown": breakdown,
                "reasoning": result.get("reasoning", "Evaluated via Groq."),
                "chain_of_thought": "",
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
                "identifier_clarity": 0,
                "prompt_adherence": 0,
                "naming_alignment": 0,
                "test_reliability": 0
            },
            "reasoning": f"LLM evaluation unavailable: {error_message}",
            "chain_of_thought": "",
            "error": True
        }

    def get_model_name(self) -> str:
        """Return the name of the active LLM judge model."""
        if self.use_ollama and self.ollama_available:
            judge_model = os.getenv("OLLAMA_JUDGE_MODEL", "deepseek-r1:1.5b")
            return f"{judge_model} (Ollama)"
        elif self.groq_client:
            return "Llama 3.3 70B (Groq)"
        else:
            return "None (Fallback)"

