"""
Chain-of-Thought Feedback Agent

DeepSeek-R1'in CoT yeteneğini kullanarak dinamik, bağlama özgü
kod iyileştirme önerileri üretir.
"""

import json
import re
from typing import Dict, Any, List


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
    
    Args:
        code: Değerlendirilecek kod
        original_prompt: Kullanıcının orijinal isteği
        static_analysis: Statik analiz sonuçları (4_categories, breakdown)
        llm_evaluation: LLM semantic değerlendirme sonuçları
        previous_score: Önceki iterasyonun skoru
        current_score: Mevcut skor
    
    Returns:
        {
            "suggestions": [
                {
                    "priority": 1-3 (1=highest),
                    "area": "Error Handling",
                    "issue": "Fonksiyon exception handling içermiyor",
                    "action": "try-except bloğu ekle",
                    "code_example": "try:\n    ..."
                },
                ...
            ],
            "chain_of_thought": "...",  # Raw CoT reasoning
            "summary": "...",  # Kısa özet
            "error": False
        }
    """
    
    # Statik analiz breakdown'ını hazırla
    breakdown = static_analysis.get("breakdown", {})
    categories = static_analysis.get("4_categories", {})
    
    # LLM reasoning
    llm_reasoning = llm_evaluation.get("reasoning", "")
    llm_breakdown = llm_evaluation.get("breakdown", {})
    
    # Context bilgisi oluştur
    context = f"""## Kod Analiz Sonuçları

### Skorlar
- Hybrid Skor: {current_score}/100 (Önceki: {previous_score}/100)
- Statik Skor: {static_analysis.get('total_score', 0)}/100
- LLM Semantic Skor: {llm_evaluation.get('semantic_score', 0)}/100

### Statik Analiz Kategorileri
- Güvenilirlik (Reliability): {categories.get('reliability', 0)}/35
- Sürdürülebilirlik (Maintainability): {categories.get('maintainability', 0)}/45
- Kod Tekrarı (Duplications): {categories.get('duplications', 0)}/10
- Karmaşıklık (Complexity): {categories.get('complexity', 0)}/20

### Detaylı Analiz
- AST Yapısı: {breakdown.get('ast_structure', {}).get('score', 0)}/20
  - Syntax Valid: {breakdown.get('ast_structure', {}).get('syntax_valid', False)}
  - Functions: {breakdown.get('ast_structure', {}).get('functions', 0)}
  - Classes: {breakdown.get('ast_structure', {}).get('classes', 0)}
  - Docstrings: {breakdown.get('ast_structure', {}).get('docstrings', 0)}
- Pylint Kalitesi: {breakdown.get('pylint_quality', {}).get('scaled_score', 0)}/25
- Karmaşıklık: {breakdown.get('complexity', {}).get('score', 0)}/20 (Avg: {breakdown.get('complexity', {}).get('average_complexity', 0)})
- Güvenlik: {breakdown.get('security', {}).get('score', 0)}/15 ({breakdown.get('security', {}).get('issues_count', 0)} açık)
- Stil (PEP8): {breakdown.get('style', {}).get('score', 0)}/10 ({breakdown.get('style', {}).get('violations', 0)} ihlal)
- Type Hints: {breakdown.get('type_hints', {}).get('score', 0)}/10

### LLM Semantic Değerlendirmesi
- Algorithm Correctness: {llm_breakdown.get('algorithm_correctness', 0)}/25
- Code Logic: {llm_breakdown.get('code_logic', 0)}/25
- Best Practices: {llm_breakdown.get('best_practices', 0)}/25
- Readability: {llm_breakdown.get('readability', 0)}/25
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
      "area": "String (örn: Error Handling, Documentation, Security)",
      "issue": "Tespit edilen sorun",
      "action": "Yapılması gereken aksiyon",
      "code_example": "Varsa kod örneği (opsiyonel)"
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

    # Ollama ile CoT feedback üret
    result = _call_ollama_cot(system_prompt, user_prompt)
    
    # Eğer hata varsa veya öneri yoksa, statik analize dayalı akıllı fallback kullan
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


def _generate_smart_fallback_suggestions(
    static_analysis: Dict[str, Any],
    llm_evaluation: Dict[str, Any],
    code: str
) -> List[Dict]:
    """
    Statik analiz sonuçlarına dayalı akıllı fallback önerileri üret.
    JSON parse hatası olsa bile gerçek sorunları tespit eder.
    """
    suggestions = []
    breakdown = static_analysis.get("breakdown", {})
    categories = static_analysis.get("4_categories", {})
    llm_breakdown = llm_evaluation.get("breakdown", {})
    
    # 1. Docstring eksikliği kontrolü
    ast_info = breakdown.get("ast_structure", {})
    functions = ast_info.get("functions", 0)
    classes = ast_info.get("classes", 0)
    docstrings = ast_info.get("docstrings", 0)
    
    if (functions + classes) > 0 and docstrings == 0:
        suggestions.append({
            "priority": 1,
            "area": "Documentation",
            "issue": f"{functions} fonksiyon ve {classes} sınıf var ama docstring yok",
            "action": "Her fonksiyon ve sınıfa docstring ekle",
            "code_example": '''def fonksiyon(param: str) -> str:
    """
    Fonksiyonun kısa açıklaması.
    
    Args:
        param: Parametre açıklaması
        
    Returns:
        Dönüş değeri açıklaması
    """
    pass'''
        })
    
    # 2. Type hints eksikliği
    type_hints_score = breakdown.get("type_hints", {}).get("score", 0)
    if type_hints_score < 5 and functions > 0:
        suggestions.append({
            "priority": 1,
            "area": "Type Safety",
            "issue": "Type hints eksik veya yetersiz",
            "action": "Tüm fonksiyon parametrelerine ve dönüş değerlerine type hint ekle",
            "code_example": "def hesapla(x: int, y: int) -> int:"
        })
    
    # 3. Güvenlik sorunları
    security_issues = breakdown.get("security", {}).get("issues_count", 0)
    if security_issues > 0:
        suggestions.append({
            "priority": 1,
            "area": "Security",
            "issue": f"{security_issues} güvenlik açığı tespit edildi",
            "action": "Güvenlik açıklarını düzelt: hardcoded credentials, SQL injection, vb.",
            "code_example": ""
        })
    
    # 4. Yüksek karmaşıklık
    complexity_score = breakdown.get("complexity", {}).get("score", 20)
    avg_complexity = breakdown.get("complexity", {}).get("average_complexity", 0)
    if avg_complexity > 10:
        suggestions.append({
            "priority": 2,
            "area": "Complexity",
            "issue": f"Ortalama karmaşıklık çok yüksek: {avg_complexity}",
            "action": "Büyük fonksiyonları küçük parçalara böl, nested if'leri azalt",
            "code_example": ""
        })
    
    # 5. PEP8 ihlalleri
    style_violations = breakdown.get("style", {}).get("violations", 0)
    if style_violations > 3:
        suggestions.append({
            "priority": 2,
            "area": "Style",
            "issue": f"{style_violations} PEP8 stil ihlali",
            "action": "Satır uzunluğunu 79 karaktere sınırla, uygun boşluk kullan",
            "code_example": ""
        })
    
    # 6. Error handling eksikliği (kodda try-except var mı?)
    if "try" not in code and "except" not in code and len(code) > 100:
        suggestions.append({
            "priority": 2,
            "area": "Error Handling",
            "issue": "Exception handling eksik",
            "action": "Potansiyel hata noktalarına try-except bloğu ekle",
            "code_example": """try:
    result = risky_operation()
except Exception as e:
    print(f"Hata: {e}")
    return None"""
        })
    
    # 7. LLM semantik değerlendirmesine dayalı öneriler
    if llm_breakdown.get("algorithm_correctness", 25) < 15:
        suggestions.append({
            "priority": 1,
            "area": "Algorithm",
            "issue": "Algoritma doğruluğu düşük",
            "action": "Algoritmanın edge case'lerini kontrol et ve mantık hatalarını düzelt",
            "code_example": ""
        })
    
    if llm_breakdown.get("readability", 25) < 15:
        suggestions.append({
            "priority": 2,
            "area": "Readability",
            "issue": "Kod okunabilirliği düşük",
            "action": "Değişken isimlerini anlamlı yap, kodu mantıksal bloklara ayır",
            "code_example": "# Kötü: x, y, z  |  İyi: total_count, user_name, is_valid"
        })
    
    # Önceliklere göre sırala
    suggestions.sort(key=lambda x: x.get("priority", 3))
    
    # Maksimum 5 öneri döndür
    return suggestions[:5]


def _call_ollama_cot(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Ollama üzerinden DeepSeek-R1 ile CoT feedback üret."""
    try:
        from module.ollama_client import call_ollama_chat, OLLAMA_MODELS
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = call_ollama_chat(
            model=OLLAMA_MODELS.get("judge", "deepseek-r1:7b"),
            messages=messages,
            temperature=0.2,
            max_tokens=2048,
            timeout=120,
            format_json=True
        )
        
        return _parse_cot_response(response)
        
    except Exception as e:
        return {
            "suggestions": [],
            "chain_of_thought": "",
            "summary": f"Ollama CoT Error: {str(e)}",
            "error": True
        }




def _parse_cot_response(response: str) -> Dict[str, Any]:
    """
    CoT yanıtını parse et.
    DeepSeek-R1 <think>...</think> blokları kullanabilir.
    """
    chain_of_thought = ""
    json_response = response
    
    # <think> bloğunu ayıkla
    if "<think>" in response and "</think>" in response:
        think_match = re.search(r"<think>(.*?)</think>", response, re.DOTALL)
        if think_match:
            chain_of_thought = think_match.group(1).strip()
            json_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
    
    # JSON parse et
    try:
        # Markdown code block'u temizle
        if "```json" in json_response:
            json_match = re.search(r"```json\s*(.*?)\s*```", json_response, re.DOTALL)
            if json_match:
                json_response = json_match.group(1)
        elif "```" in json_response:
            json_match = re.search(r"```\s*(.*?)\s*```", json_response, re.DOTALL)
            if json_match:
                json_response = json_match.group(1)
        
        result = json.loads(json_response)
        
        return {
            "suggestions": result.get("suggestions", []),
            "chain_of_thought": chain_of_thought,
            "summary": result.get("summary", ""),
            "error": False
        }
        
    except json.JSONDecodeError as e:
        # JSON parse edilemezse basit öneriler döndür
        return {
            "suggestions": [{
                "priority": 2,
                "area": "Genel",
                "issue": "Kod kalitesi iyileştirilmeli",
                "action": "Docstring ekle, error handling ekle, PEP8 standartlarına uy",
                "code_example": ""
            }],
            "chain_of_thought": chain_of_thought,
            "summary": f"JSON parse error, fallback öneriler kullanıldı: {str(e)}",
            "error": True
        }


def format_suggestions_for_prompt(suggestions: List[Dict]) -> str:
    """
    Önerileri prompt'a eklenecek formata dönüştür.
    """
    if not suggestions:
        return "Genel kod kalitesini artır."
    
    lines = []
    priority_labels = {1: "🔴 KRİTİK", 2: "🟡 ÖNEMLİ", 3: "🟢 DÜŞÜK"}
    
    for s in suggestions:
        priority = s.get("priority", 2)
        label = priority_labels.get(priority, "⚪ GENEL")
        
        line = f"{label} [{s.get('area', 'Genel')}]: {s.get('issue', '')} → {s.get('action', '')}"
        if s.get("code_example"):
            line += f"\n   Örnek: {s['code_example'][:100]}..."
        
        lines.append(line)
    
    return "\n".join(lines)


# Test için
if __name__ == "__main__":
    test_code = '''
def calc(x):
    return x * 2
'''
    
    test_static = {
        "total_score": 45,
        "4_categories": {
            "reliability": 15,
            "maintainability": 10,
            "duplications": 10,
            "complexity": 20
        },
        "breakdown": {
            "ast_structure": {"score": 10, "syntax_valid": True, "functions": 1, "docstrings": 0},
            "pylint_quality": {"scaled_score": 5},
            "complexity": {"score": 20, "average_complexity": 1},
            "security": {"score": 15, "issues_count": 0},
            "style": {"score": 5, "violations": 3},
            "type_hints": {"score": 0}
        }
    }
    
    test_llm = {
        "semantic_score": 60,
        "breakdown": {
            "algorithm_correctness": 20,
            "code_logic": 15,
            "best_practices": 10,
            "readability": 15
        },
        "reasoning": "Fonksiyon çalışıyor ama docstring ve type hints eksik."
    }
    
    result = generate_cot_feedback(
        code=test_code,
        original_prompt="2 ile çarp",
        static_analysis=test_static,
        llm_evaluation=test_llm,
        previous_score=40,
        current_score=50
    )
    
    print("CoT Feedback Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
