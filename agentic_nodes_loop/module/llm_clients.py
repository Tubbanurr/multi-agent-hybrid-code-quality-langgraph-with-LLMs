"""
LLM Client Module — Ollama Only

Kod üretimi için sadece yerel Ollama modelleri kullanır.
Slot 1: Qwen2.5-Coder
Slot 2: CodeLlama
Slot 3: Llama 3.1
"""

from module.ollama_client import (
    call_qwen_coder,
    call_codellama_ollama,
    call_llama31,
    check_ollama_available,
)


# Başlangıçta Ollama durumunu kontrol et
if check_ollama_available():
    print("✅ Ollama aktif - Yerel modeller kullanılacak")
else:
    print("⚠️ Ollama servisi bulunamadı. Lütfen 'ollama serve' komutunu çalıştırın.")


# --- Code Generation Functions ---

def call_codellama(prompt: str) -> str:
    """
    Slot 1: Qwen2.5-Coder (Ollama) ile kod üretir.
    """
    print("  📡 Qwen2.5-Coder (Ollama) kullanılıyor...")
    return call_qwen_coder(prompt)


def call_deepseek(prompt: str) -> str:
    """
    Slot 2: CodeLlama (Ollama) ile kod üretir.
    """
    print("  📡 CodeLlama (Ollama) kullanılıyor...")
    return call_codellama_ollama(prompt)


def call_gemini(prompt: str) -> str:
    """
    Slot 3: Llama 3.1 (Ollama) ile kod üretir.
    """
    print("  📡 Llama 3.1 (Ollama) kullanılıyor...")
    return call_llama31(prompt)


# --- Model Names for Display ---

def get_model_names() -> dict:
    """Aktif model isimlerini döndürür."""
    return {
        "model_1": "Qwen2.5-Coder (Ollama)",
        "model_2": "CodeLlama (Ollama)",
        "model_3": "Llama 3.1 (Ollama)"
    }
