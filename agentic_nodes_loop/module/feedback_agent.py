"""
Chain-of-Thought Feedback Agent

DeepSeek-R1'in CoT yeteneğini kullanarak dinamik, bağlama özgü
kod iyileştirme önerileri üretir.
"""

import os
import json
import re
from typing import Dict, Any, List
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"


def generate_cot_feedback(
    code: str,
    original_prompt: str,
    static_analysis: Dict[str, Any],
    llm_evaluation: Dict[str, Any],
    previous_score: float = 0,
    current_score: float = 0
) -> Dict[str, Any]:
    """
    Chain-of-Thought kullanarak dinamik feedback ve öneriler üretir.
    """
    
    # Statik analiz breakdown'ını hazırla
    breakdown = static_analysis.get("breakdown", {})
    # Hybrid skor breakdown (categories)
    hybrid_categories = llm_evaluation.get("categories", {})
    llm_reasoning = llm_evaluation.get("reasoning", "")
    
    # Context bilgisi oluştur
    context = f"""## Kod Analiz Sonuçları

### Skorlar
- Hybrid Skor: {current_score}/100 (Önceki: {previous_score}/100)
- Statik Analiz (Temel): {static_analysis.get('static_total', 0):.1f}/100

### 6 Kategori Detaylı Skorları
- 1. Kod Kalitesi: {hybrid_categories.get('1_Kod_Kalitesi', 0)}/25
- 2. Teknik Borç: {hybrid_categories.get('2_Teknik_Borc', 0)}/20
- 3. Test & Build: {hybrid_categories.get('3_Test_Build', 0)}/15
- 4. Stil & Standart: {hybrid_categories.get('4_Stil_Standart', 0)}/15
- 5. Semantic Alignment: {hybrid_categories.get('5_Semantic_Alignment', 0)}/15
- 6. Robustness & Safety: {hybrid_categories.get('6_Robustness_Safety', 0)}/10

### Statik Metrik Detayları
- AST Yapısı: Functions: {breakdown.get('syntax', {}).get('functions', 0)}, Classes: {breakdown.get('syntax', {}).get('classes', 0)}, Docstrings: {breakdown.get('syntax', {}).get('docstrings', 0)}
- Pylint: {breakdown.get('pylint', {}).get('raw_score', 0):.1f}/10
- Karmaşıklık: {breakdown.get('complexity', {}).get('average_complexity', 0):.1f}
- Güvenlik: {breakdown.get('security', {}).get('issues_count', 0)} açık
- Stil (PEP8): {breakdown.get('style', {}).get('violations', 0)} ihlal
- Yorum Yoğunluğu: {breakdown.get('comments', {}).get('density', 0)*100:.1f}%

### LLM Semantic Değerlendirmesi
- Reasoning: {llm_reasoning}"""

    system_prompt = """Sen uzman bir Python kod reviewer'ısın. Sana verilen kod analiz sonuçlarını değerlendirip, ÖNCELİKLİ ve SPESİFİK iyileştirme önerileri üreteceksin.

Chain-of-Thought (adım adım düşünme) yöntemiyle analiz yap:
1. Önce en kritik sorunları tespit et
2. Sorunları etkiye göre önceliklendir (1=en yüksek, 3=düşük)
3. Her sorun için somut çözüm öner
4. Mümkünse kod örneği ver

SADECE aşağıdaki JSON formatında yanıt ver (markdown veya açıklama YOOOK):
{
  "suggestions": [
    {
      "priority": 1,
      "area": "Error Handling|Documentation|Security|Complexity|Naming",
      "issue": "<issue description>",
      "action": "<specific recovery action>",
      "code_example": "optional code snippet"
    }
  ],
  "summary": "1-2 cümlelik genel özet"
}"""

    user_prompt = f"""Orijinal İstek: {original_prompt}

Kod:
```python
{code}
```

{context}

Bu kodu iyileştirmek için öncelikli önerilerini JSON formatında ver."""

    # Ollama veya Groq kullan
    if USE_OLLAMA:
        result = _call_ollama_cot(system_prompt, user_prompt)
    else:
        result = _call_groq_cot(system_prompt, user_prompt)
    
    # Fallback
    if result.get("error") or not result.get("suggestions"):
        smart_suggestions = _generate_smart_fallback_suggestions(
            static_analysis=static_analysis,
            llm_evaluation=llm_evaluation,
            code=code
        )
        if smart_suggestions:
            result["suggestions"] = smart_suggestions
            result["summary"] = "Statik analize dayalı öneriler üretildi."
    
    return result


def _generate_smart_fallback_suggestions(static_analysis, llm_evaluation, code):
    suggestions = []
    breakdown = static_analysis.get("breakdown", {})
    
    if breakdown.get("comments", {}).get("density", 0) < 0.1:
        suggestions.append({
            "priority": 2,
            "area": "Documentation",
            "issue": "Yorum yoğunluğu çok düşük",
            "action": "Kodun anlaşılırlığını artırmak için docstring ve yorum ekle"
        })
    if breakdown.get("style", {}).get("violations", 0) > 5:
        suggestions.append({
            "priority": 2,
            "area": "Style",
            "issue": "Çok sayıda PEP8 ihlali var",
            "action": "Kod stilini PEP8 standartlarına göre düzelt"
        })
    if "try" not in code and len(code) > 100:
        suggestions.append({
            "priority": 1,
            "area": "Robustness",
            "issue": "Hata yönetimi blokları (try-except) eksik",
            "action": "Kritik operasyonlar için hata yakalama mekanizması ekle"
        })
    return suggestions[:3]


def _call_ollama_cot(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    try:
        from module.ollama_client import call_ollama_chat, OLLAMA_MODELS
        response = call_ollama_chat(
            model=OLLAMA_MODELS.get("judge", "deepseek-r1:7b"),
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            format_json=True
        )
        return _parse_cot_response(response)
    except Exception as e:
        return {"error": True, "suggestions": [], "summary": str(e)}


def _call_groq_cot(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.2
        )
        return _parse_cot_response(response.choices[0].message.content)
    except Exception as e:
        return {"error": True, "suggestions": [], "summary": str(e)}


def _parse_cot_response(response: str) -> Dict[str, Any]:
    chain_of_thought = ""
    json_response = response
    if "<think>" in response and "</think>" in response:
        think_match = re.search(r"<think>(.*?)</think>", response, re.DOTALL)
        if think_match:
            chain_of_thought = think_match.group(1).strip()
            json_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
    try:
        if "```json" in json_response:
            json_response = re.search(r"```json\s*(.*?)\s*```", json_response, re.DOTALL).group(1)
        result = json.loads(json_response)
        return {
            "suggestions": result.get("suggestions", []),
            "chain_of_thought": chain_of_thought,
            "summary": result.get("summary", ""),
            "error": False
        }
    except:
        return {"error": True, "suggestions": [], "chain_of_thought": chain_of_thought, "summary": "JSON parse error"}


def format_suggestions_for_prompt(suggestions: List[Dict]) -> str:
    if not suggestions: return "Genel kod kalitesini artır."
    lines = []
    for s in suggestions:
        lines.append(f"- [{s.get('area', 'Genel')}]: {s.get('issue', '')} -> {s.get('action', '')}")
    return "\n".join(lines)
