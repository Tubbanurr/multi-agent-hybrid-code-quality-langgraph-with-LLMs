"""
LLM-based Semantic Code Judge — Ollama Only

DeepSeek-R1 (Ollama) kullanarak kodu semantik olarak değerlendirir.
Chain-of-Thought desteğiyle derin analiz yapar.
"""

import json
from typing import Dict, Any

from module.ollama_client import call_deepseek_r1_judge


class LLMJudge:
    """
    LLM-tabanlı semantik kod kalite değerlendirici.
    Her zaman DeepSeek-R1 (Ollama) kullanır.
    """

    def __init__(self):
        print("  🤖 LLM Judge: DeepSeek-R1 (Ollama)")

    def evaluate_code(self, code: str, prompt: str) -> Dict[str, Any]:
        """
        Kodu semantik olarak değerlendirir.

        Args:
            code: Değerlendirilecek Python kodu
            prompt: Kullanıcının orijinal isteği

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
                "chain_of_thought": "...",
                "error": False
            }
        """
        return call_deepseek_r1_judge(code, prompt)

    def get_model_name(self) -> str:
        return "DeepSeek-R1 (Ollama)"
