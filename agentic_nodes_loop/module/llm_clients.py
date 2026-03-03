import os
import requests
from groq import Groq
from dotenv import load_dotenv
import time

load_dotenv()

# --- Configuration ---
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"

# Initialize cloud clients (fallback)
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


# --- Ollama Functions (conditional import) ---
OLLAMA_MODEL_NAMES = {}
if USE_OLLAMA:
    try:
        from module.ollama_client import (
            call_qwen_coder,
            call_codellama_ollama,
            call_llama31,
            check_ollama_available,
            OLLAMA_MODELS
        )
        OLLAMA_AVAILABLE = check_ollama_available()
        if OLLAMA_AVAILABLE:
            OLLAMA_MODEL_NAMES = OLLAMA_MODELS
            print("✅ Ollama aktif - Yerel modeller kullanılacak")
        else:
            print("⚠️ Ollama servisi bulunamadı - Cloud API'lere fallback")
    except ImportError:
        OLLAMA_AVAILABLE = False
        print("⚠️ Ollama modülü bulunamadı - Cloud API'lere fallback")
else:
    OLLAMA_AVAILABLE = False


# --- Code Generation Functions ---

def call_codellama(prompt: str) -> str:
    """
    Generates code using the first model slot.
    
    - Ollama mode: Qwen2.5-Coder (best open-source code model)
    - Cloud mode: Llama 3.3 70B via Groq
    """
    if USE_OLLAMA and OLLAMA_AVAILABLE:
        print(f"  📡 {OLLAMA_MODEL_NAMES.get('coder_1', 'Coder 1')} (Ollama) kullanılıyor...")
        return call_qwen_coder(prompt)
    
    # Fallback to Groq
    if not groq_client:
        return "Groq API Key missing or client init failed."
        
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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
    """
    Generates code using the second model slot.
    
    - Ollama mode: CodeLlama (specialized code model)
    - Cloud mode: DeepSeek V3 via DeepSeek API
    """
    if USE_OLLAMA and OLLAMA_AVAILABLE:
        print(f"  📡 {OLLAMA_MODEL_NAMES.get('coder_2', 'Coder 2')} (Ollama) kullanılıyor...")
        return call_codellama_ollama(prompt)
    
    # Fallback to DeepSeek API
    if not deepseek_client:
        return "DeepSeek API Key missing or client init failed."
    
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
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
    """
    Generates code using the third model slot.
    
    - Ollama mode: Llama 3.1 (great instruction following)
    - Cloud mode: Gemini 2.0 Flash via Google API
    
    Includes retry with exponential backoff for 429 rate-limit errors.
    """
    if USE_OLLAMA and OLLAMA_AVAILABLE:
        print(f"  📡 {OLLAMA_MODEL_NAMES.get('coder_3', 'Coder 3')} (Ollama) kullanılıyor...")
        return call_llama31(prompt)
    
    # Fallback to Gemini API
    if not gemini_client:
        return "Gemini API Key missing or client init failed."

    max_retries = 3
    for attempt in range(max_retries):
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
            err_msg = str(e)
            if "429" in err_msg or "rate limit" in err_msg.lower():
                if attempt < max_retries - 1:
                    backoff = 2 ** attempt * 5
                    print(f"Gemini rate limit hit, sleeping {backoff}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(backoff)
                    continue
            return f"Gemini API Error: {err_msg}"
    return "Gemini API Error: exceeded retry attempts"


# --- Model Names for Display ---

def get_model_names() -> dict:
    """Return display names for the current model configuration (dynamically from .env)."""
    if USE_OLLAMA and OLLAMA_AVAILABLE:
        return {
            "model_1": f"{OLLAMA_MODEL_NAMES.get('coder_1', 'Coder 1')} (Ollama)",
            "model_2": f"{OLLAMA_MODEL_NAMES.get('coder_2', 'Coder 2')} (Ollama)",
            "model_3": f"{OLLAMA_MODEL_NAMES.get('coder_3', 'Coder 3')} (Ollama)"
        }
    else:
        return {
            "model_1": "Llama 3.3 70B (Groq)",
            "model_2": "DeepSeek V3",
            "model_3": "Gemini 2.0 Flash"
        }

