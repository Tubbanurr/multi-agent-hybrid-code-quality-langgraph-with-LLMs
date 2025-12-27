from app.agents.base_agent import BaseAgent
from app.metrics.code_quality import compare_models
#		İlk ve temel kalite ajanı
#       Mevcut CodeQualityAnalyzer’ı kullanır
#		Skorları metrics içine koyar
#		Kazanan modeli belirler#
class CodeQualityAgent(BaseAgent):
    name = "code_quality"

    def run(self, state):
        result = compare_models(
            state["codes"]["LLaMA3"],
            state["codes"]["DeepSeek"],
            state["codes"]["Gemini"]
        )

        state["metrics"]["code_quality"] = result["scores"]
        state["winner"] = result["winner"]

        return state