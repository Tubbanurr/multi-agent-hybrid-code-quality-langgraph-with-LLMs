import os
import requests
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
groq_client = None
deepseek_client = None
gemini_client = None

try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        groq_client = Groq(api_key=groq_api_key)
except Exception as e:
    print(f"Error initializing Groq client: {e}")

# DeepSeek client
try:
    from openai import OpenAI
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_api_key:
        deepseek_client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
except Exception as e:
    print(f"Error initializing DeepSeek client: {e}")

# Gemini client
try:
    import google.generativeai as genai
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp')
except Exception as e:
    print(f"Error initializing Gemini client: {e}")


def call_codellama(prompt: str) -> str:
    """Generates code using CodeLlama 70B (Groq) - Best CodeLlama model."""
    if not groq_client:
        return "Groq API Key missing or client init failed."
        
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Currently best available on Groq
            messages=[
                {"role": "system", "content": "You are an expert Python programmer. Write clean, efficient code. Output ONLY the code or markdown with code blocks. Do not be conversational."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_completion_tokens=2048
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"CodeLlama API Error: {str(e)}"


def call_deepseek(prompt: str) -> str:
    """Generates code using DeepSeek V3 (DeepSeek API) - Most powerful reasoning model."""
    if not deepseek_client:
        return "DeepSeek API Key missing or client init failed."
    
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",  # DeepSeek V3
            messages=[
                {"role": "system", "content": "You are an expert Python programmer. Write clean, efficient code. Output ONLY the code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"DeepSeek API Error: {str(e)}"


def call_gemini(prompt: str) -> str:
    """Generates code using Gemini 2.0 Flash (Gemini API) - Google's latest."""
    if not gemini_client:
        return "Gemini API Key missing or client init failed."
    
    try:
        response = gemini_client.generate_content(
            f"You are an expert Python programmer. Write clean, efficient code. Output ONLY the code.\n\n{prompt}",
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 2048
            }
        )
        return response.text
    except Exception as e:
        return f"Gemini API Error: {str(e)}"
