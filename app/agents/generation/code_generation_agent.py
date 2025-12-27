from app.agents.base_agent import BaseAgent
from app.llm.codellama import call_codellama
from app.llm.deepseek import call_deepseek
from app.llm.gemini import call_gemini
# 	Kod üretiminden tek başına sorumlu ajan
#    3 LLM’i çağırır 
#    State içine codes yazar
class CodeGenerationAgent(BaseAgent):
    name = "code_generation"

    def run(self, state):
        prompt = state["prompt"]

        return {
            **state,
            "codes": {
                "LLaMA3": call_codellama(prompt),
                "DeepSeek": call_deepseek(prompt),
                "Gemini": call_gemini(prompt)
            }
        }