from app.agents.base_agent import BaseAgent

class ReliabilityAgent(BaseAgent):
    name = "reliability"

    def run(self, state):
        state["metrics"]["reliability"] = {}
        return state