from groq import Groq
from app.config.settings import settings

client = Groq(api_key=settings.GROQ_API_KEY)

def call_codellama(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
        max_completion_tokens=1024
    )
    return completion.choices[0].message.content