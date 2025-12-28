import os
import requests
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Initialize Groq client
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Error initializing Groq client: {e}")

def call_codellama(prompt: str) -> str:
    """Generates code using Llama 3 via Groq."""
    if not groq_client:
        return "Groq API Key missing or client init failed."
        
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert Python programmer. Write clean, efficient code. Output ONLY the code or markdown with code blocks. Do not be conversational."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, # Lower temperature for better code
            max_completion_tokens=1024
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Groq API Error: {str(e)}"

def call_deepseek(prompt: str) -> str:
    """Generates code using DeepSeek via OpenRouter (or direct if applicable)."""
    if not DEEPSEEK_API_KEY:
        return "DeepSeek API Key missing."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
             {"role": "system", "content": "You are an expert Python programmer. Write clean, efficient code. Output ONLY the code or markdown with code blocks."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=60)
        if res.status_code != 200:
             return f"DeepSeek API Error: {res.status_code} - {res.text}"
        
        data = res.json()
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        
        return f"DeepSeek Unexpected Response: {data}"
    except Exception as e:
        return f"DeepSeek API Connection Error: {str(e)}"

def call_gemini(prompt: str) -> str:
    """Generates code using Gemini 2.0 Flash via REST API."""
    if not GEMINI_API_KEY:
        return "Gemini API Key missing."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{
            "parts": [{"text": f"You are an expert Python programmer. Write code for the following request. Output ONLY code.\nRequest: {prompt}"}]
        }]
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code != 200:
            return f"Gemini API Error: {response.status_code} - {response.text}"
            
        result = response.json()
        if "candidates" in result and len(result["candidates"]) > 0:
             return result["candidates"][0]["content"]["parts"][0]["text"]
        
        return f"Gemini Unexpected Response: {result}"
    except Exception as e:
        return f"Gemini API Connection Error: {str(e)}"
