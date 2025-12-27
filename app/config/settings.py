from dotenv import load_dotenv
import os
#		API anahtarlarının tek merkezi
#		.env dosyasını okur
load_dotenv()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    def has_groq(self) -> bool:
        return bool(self.GROQ_API_KEY)

    def has_deepseek(self) -> bool:
        return bool(self.DEEPSEEK_API_KEY)

    def has_gemini(self) -> bool:
        return bool(self.GEMINI_API_KEY)

settings = Settings()