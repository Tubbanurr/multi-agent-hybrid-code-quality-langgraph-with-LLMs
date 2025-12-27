class BaseAgent:
    name: str

    def run(self, state):
        raise NotImplementedError
    
# 	Tüm ajanlar için ortak sözleşme (interface)
# 		Agent’lar standardize edilir
#		LangGraph node’ları hep aynı tip fonksiyon alır
#		Akademik olarak: Agent abstraction