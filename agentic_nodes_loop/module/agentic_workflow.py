"""
Hybrid Agentic Workflow
İlk tur: 3 model yarışması → Kazanan seçimi
İkinci tur: Kazanan < eşik ise feedback döngüsü
"""

from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
import os
import csv
import json # Added json import
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Mevcut modüllerden import
from module.llm_clients import call_codellama, call_deepseek, call_gemini, get_model_names
from module.advanced_judge import AdvancedCodeJudge

# Env variables
load_dotenv()

# --- CSV Logging Utility ---
def log_request_to_csv(
    request_id: str,
    user_prompt: str,
    model_names: Dict[str, str],
    judge_model: str,
    static_weight: float,
    llm_weight: float,
    model_scores: Dict[str, float],
    initial_winner: str,
    iteration_count: int,
    final_score: float,
    status: str,
    generated_code: str,
    judge_reasoning: str,
    feedback_iterations: List[Dict[str, Any]] = None,
    log_file: str = "logs/workflow_log.csv"
):
    """
    Append workflow summary to CSV file.
    İterasyon bilgileri Score_Progression ve Iteration_Notes kolonlarında özet olarak tutulur.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_exists = os.path.isfile(log_file)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # --- İterasyon özeti oluştur ---
    feedback_iterations = feedback_iterations or []

    # Skor akışı: başlangıç skoru → iter1 → iter2 ...
    if feedback_iterations:
        initial_score = feedback_iterations[0].get("previous_score", 0)
        score_steps = [f"{initial_score:.1f}"]
        for it in feedback_iterations:
            score_steps.append(f"{it.get('new_score', 0):.1f}")
        score_progression = " → ".join(score_steps)
    else:
        score_progression = f"{final_score:.1f}" if not feedback_iterations else ""

    # Iterasyon notları: her tur için [N] Δskor | öneriler
    iter_notes_parts = []
    for it in feedback_iterations:
        n = it.get("iteration", "?")
        delta = it.get("score_improvement", 0)
        rollback = " [ROLLBACK]" if it.get("new_score", 0) < it.get("previous_score", 0) - 2 else ""
        top_suggestions = ", ".join(
            s.get("area", "") for s in it.get("suggestions", [])[:3]
        )
        iter_notes_parts.append(f"[{n}] {delta:+.1f}{rollback} ({top_suggestions})")
    iteration_notes = " | ".join(iter_notes_parts) if iter_notes_parts else "-"

    row_data = [
        request_id,
        user_prompt[:500].replace("\n", " "),
        model_names.get("model_1", "Model 1"),
        model_names.get("model_2", "Model 2"),
        model_names.get("model_3", "Model 3"),
        judge_model,
        f"{static_weight:.2f}",
        f"{llm_weight:.2f}",
        f"{model_scores.get('model_1_static', 0):.1f}",
        f"{model_scores.get('model_1_llm', 0):.1f}",
        f"{model_scores.get('model_1_hybrid', 0):.1f}",
        f"{model_scores.get('model_2_static', 0):.1f}",
        f"{model_scores.get('model_2_llm', 0):.1f}",
        f"{model_scores.get('model_2_hybrid', 0):.1f}",
        f"{model_scores.get('model_3_static', 0):.1f}",
        f"{model_scores.get('model_3_llm', 0):.1f}",
        f"{model_scores.get('model_3_hybrid', 0):.1f}",
        initial_winner,
        iteration_count,
        score_progression,      # YENİ
        iteration_notes,         # YENİ
        f"{final_score:.1f}",
        status,
        timestamp,
        generated_code,
        judge_reasoning
    ]

    with open(log_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)  # Tüm alanları quote'la
        if not file_exists:
            writer.writerow([
                "Request_ID",
                "User_Prompt",
                "Model_1_Name",
                "Model_2_Name",
                "Model_3_Name",
                "Judge_Model",
                "Static_Weight",
                "LLM_Weight",
                "Model_1_Static_Score",
                "Model_1_LLM_Score",
                "Model_1_Hybrid_Score",
                "Model_2_Static_Score",
                "Model_2_LLM_Score",
                "Model_2_Hybrid_Score",
                "Model_3_Static_Score",
                "Model_3_LLM_Score",
                "Model_3_Hybrid_Score",
                "Initial_Winner",
                "Iteration_Count",
                "Score_Progression",
                "Iteration_Notes",
                "Final_Score",
                "Status",
                "Timestamp",
                "Generated_Code",
                "Judge_Reasoning"
            ])
        writer.writerow(row_data)



# --- Dynamic Threshold Utility ---
def calculate_dynamic_threshold(prompt: str) -> float:
    """
    Prompt karmaşıklığına göre dinamik kalite eşiği hesapla.
    
    Basit işlemler (aritmetik, tek satırlık) için düşük eşik,
    karmaşık algoritmalar için yüksek eşik.
    
    Returns:
        float: 55.0 - 75.0 arası threshold değeri
    """
    prompt_lower = prompt.lower()
    
    # Token sayısı (basit yaklaşım)
    word_count = len(prompt.split())
    
    # Karmaşıklık göstergeleri
    complexity_keywords = [
        'algorithm', 'algoritma', 'sort', 'search', 'binary', 'tree',
        'graph', 'recursive', 'dynamic', 'fibonacci', 'linked list',
        'hash', 'queue', 'stack', 'class', 'oop', 'design pattern',
        'api', 'database', 'async', 'thread', 'parallel'
    ]
    
    # Basitlik göstergeleri
    simple_keywords = [
        'topla', 'çıkar', 'çarp', 'böl', 'hesapla', 'yaz', 'print',
        '+', '-', '*', '/', 'kare', 'küp', 'katları', 'hello',
        'merhaba', 'basit', 'simple', 'basic'
    ]
    
    # Skor hesapla
    complexity_score = 0
    
    # Karmaşıklık keyword kontrolü
    for keyword in complexity_keywords:
        if keyword in prompt_lower:
            complexity_score += 10
    
    # Basitlik keyword kontrolü
    for keyword in simple_keywords:
        if keyword in prompt_lower:
            complexity_score -= 8
    
    # Word count bazlı ayarlama
    if word_count <= 5:
        complexity_score -= 10
    elif word_count >= 15:
        complexity_score += 5
    
    # Threshold hesapla (55-75 arası)
    base_threshold = 65.0
    threshold = base_threshold + (complexity_score / 5)
    
    # Sınırla
    threshold = max(55.0, min(75.0, threshold))
    
    print(f"📊 Dinamik Threshold: {threshold:.1f} (prompt karmaşıklık skoru: {complexity_score})")
    
    return threshold

# --- State Definition ---
class HybridState(TypedDict):
    """Hybrid workflow state"""
    prompt: str
    iteration_count: int
    max_iterations: int
    quality_threshold: float
    
    # Configuration (NEW)
    static_weight: float
    llm_weight: float
    metric_weights: Optional[Dict[str, int]]
    
    # Round 1 Data
    round1_codes: Dict[str, str]
    round1_scores: Dict[str, Any]
    
    # Recursive Loop State
    current_code: str
    current_score: float
    previous_code_snapshot: str  # Önceki iterasyonun kodu (generator çalışmadan önce)
    previous_categories: Dict[str, float]  # Önceki 4_categories
    winner_model: str
    final_quality_score: float # Ajanlardan gelen skorların ağırlıklı ortalaması
    
    # Separate Analysis Results (NEW)
    static_analysis_result: Dict[str, Any]  # Static analyzer çıktısı
    llm_evaluation_result: Dict[str, Any]   # LLM judge çıktısı
    hybrid_score: float                      # Birleştirilmiş skor
    
    # Feedback
    quality_profile: str
    feedback_iterations: List[Dict[str, Any]]
    
    # Results
    final_code: str
    final_score: float
    status: str  # "direct_output" | "improved_via_feedback"
    judge_reasoning: str # Final reasoning for logs
    request_id: str      # Unique ID shared between summary + iteration logs


# --- Helper: HYBRID Analysis (Static + LLM) ---
def analyze_with_4_metrics(code: str, prompt: str = "", 
                          static_weight: float = 0.7, 
                          llm_weight: float = 0.3,
                          metric_weights: Dict[str, int] = None) -> Dict[str, Any]:
    """Perform static + LLM analysis and return hybrid result including LLM reasoning."""
    """
    HYBRID ANALYSIS: Static + LLM Semantic (Dynamic Weights)
    
    Returns full hybrid analysis with both static and LLM scores.
    """
    from module.advanced_judge import AdvancedCodeJudge
    from module.llm_judge import LLMJudge
    
    # Check if code is actually an API error message
    if "API Error" in code or "Error code:" in code or len(code.strip()) < 20:
        return {
            "hybrid_score": 0,
            "total_score": 0,  # For backwards compatibility
            "static_score": 0,
            "llm_score": 0,
            "weights": {"static": static_weight, "llm": llm_weight},
            "breakdown": {
                "static_analysis": {
                    "total_score": 0,
                    "breakdown": {
                        "ast_structure": {"score": 0, "error": "API Error or empty code"},
                        "pylint_quality": {"scaled_score": 0},
                        "complexity": {"score": 0},
                        "security": {"score": 0, "issues_count": 0},
                        "style": {"score": 0, "violations": 0},
                        "type_hints": {"score": 0},
                        "duplications": {"score": 0, "duplication_ratio": 0}
                    },
                    "4_categories": {
                        "reliability": 0,
                        "maintainability": 0,
                        "duplications": 0,
                        "complexity": 0
                    }
                },
                "llm_evaluation": {
                    "semantic_score": 0,
                    "breakdown": {
                        "algorithm_correctness": 0,
                        "code_logic": 0,
                        "best_practices": 0,
                        "readability": 0
                    },
                    "reasoning": "API Error - no evaluation",
                    "error": True
                }
            },
            "is_error": True
        }
    
    # 1. Static Analysis (existing)
    judge = AdvancedCodeJudge(metric_weights=metric_weights)
    static_analysis = judge.score_code(code)
    
    # 2. LLM Semantic Evaluation (new)
    llm_judge = LLMJudge()
    llm_evaluation = llm_judge.evaluate_code(code, prompt)
    
    # 3. Combine into Hybrid Score
    hybrid_result = judge.get_hybrid_score(static_analysis, llm_evaluation, 
                                          static_weight=static_weight, 
                                          llm_weight=llm_weight)
    
    # Add total_score for backwards compatibility
    hybrid_result["total_score"] = hybrid_result["hybrid_score"]
    hybrid_result["is_error"] = False
    
    # Preserve 4_categories from static analysis
    hybrid_result["4_categories"] = static_analysis.get("4_categories", {})
    
    return hybrid_result


# --- Node 1: Generator Node (Kod Oluşturma) ---
def generator_node(state: HybridState) -> HybridState:
    """
    Düğüm 1: Kod oluşturma düğümü. 
    İlk turda 3 model kullanır, sonraki turlarda kazananla devam eder.
    """
    prompt = state["prompt"]
    iteration = state.get("iteration_count", 0)
    
    if iteration == 0:
        print(f"\n{'='*60}")
        print(f"🏁 DÜĞÜM 1: İLK KOD OLUŞTURMA (3 MODEL)")
        print(f"{'='*60}\n")
        
        # Model isimlerini dinamik al (Ollama veya Cloud)
        model_names = get_model_names()
        
        codes = {
            model_names["model_1"]: call_codellama(prompt),
            model_names["model_2"]: call_deepseek(prompt),
            model_names["model_3"]: call_gemini(prompt)
        }
        return {"round1_codes": codes}
    else:
        print(f"\n{'='*60}")
        print(f"🔄 DÜĞÜM 1: KOD İYİLEŞTİRME (İterasyon {iteration})")
        print(f"{'='*60}\n")
        
        # Geliştirilmiş ve daha direktif prompt oluştur
        quality_profile = state.get('quality_profile', '')
        current_code = state.get('current_code', '')
        
        enhanced_prompt = f"""# KOD İYİLEŞTİRME GÖREVİ

## Orijinal İstek
{prompt}

## Mevcut Kod
```python
{current_code}
```

## ZORUNLU İYİLEŞTİRMELER
{quality_profile}

## TALİMATLAR
1. Yukarıdaki ÖNCELİKLİ önerileri MUTLAKA uygula
2. Docstring ekle (fonksiyon/class varsa)
3. Type hints ekle (parametreler ve dönüş değeri)
4. Error handling ekle (try-except)
5. Değişken isimlerini anlamlı yap

⚠️ ÖNEMLİ: SADECE Python kodu üret, açıklama yazma!
⚠️ Mevcut işlevselliği KORU, sadece kaliteyi artır!"""
        
        winner_model = state["winner_model"]
        
        # Model seçimi - Ollama model isimlerini de kontrol et
        if "CodeLlama" in winner_model or "Qwen" in winner_model:
            new_code = call_codellama(enhanced_prompt)
        elif "DeepSeek" in winner_model:
            new_code = call_deepseek(enhanced_prompt)
        else:
            new_code = call_gemini(enhanced_prompt)
            
        # Yeni kodu kaydet VE önceki kodu snapshot olarak sakla
        return {
            "previous_code_snapshot": state["current_code"],  # Generator çalışmadan ÖNCEKİ kod
            "current_code": new_code
        }

# --- Node 2: Static Analyzer Node (Statik Analiz Düğümü) ---
def static_analyzer_node(state: HybridState) -> HybridState:
    """
    Düğüm 2: Statik analiz düğümü (AST, Pylint, Radon, Bandit, Flake8).
    """
    prompt = state["prompt"]
    iteration = state.get("iteration_count", 0)
    metric_weights = state.get("metric_weights", None)
    
    print(f"\n{'='*60}")
    print(f"🔍 DÜĞÜM 2: STATİK ANALİZ")
    print(f"{'='*60}\n")
    
    from module.advanced_judge import AdvancedCodeJudge
    judge = AdvancedCodeJudge(metric_weights=metric_weights)
    
    if iteration == 0:
        # İLK TUR: 3 modeli analiz et
        round1_codes = state["round1_codes"]
        static_results = {}
        
        for model, code in round1_codes.items():
            result = judge.score_code(code)
            static_results[model] = result
            print(f"📊 {model} Statik Skor: {result['total_score']}/100")
        
        return {"static_analysis_result": static_results}
    else:
        # FEEDBACK TURU: İyileştirilen kodu analiz et
        new_code = state["current_code"]
        result = judge.score_code(new_code)
        print(f"📊 Statik Analiz Skoru: {result['total_score']}/100")
        
        return {"static_analysis_result": result}


# --- Node 3: LLM Judge Node (LLM Değerlendirme Düğümü) ---
def llm_judge_node(state: HybridState) -> HybridState:
    """
    Düğüm 3: LLM semantic değerlendirme düğümü.
    """
    prompt = state["prompt"]
    iteration = state.get("iteration_count", 0)
    
    print(f"\n{'='*60}")
    print(f"🤖 DÜĞÜM 3: LLM SEMANTIC DEĞERLENDİRME")
    print(f"{'='*60}\n")
    
    from module.llm_judge import LLMJudge
    llm_judge = LLMJudge()
    
    if iteration == 0:
        # İLK TUR: 3 modeli değerlendir
        round1_codes = state["round1_codes"]
        llm_results = {}
        
        for model, code in round1_codes.items():
            result = llm_judge.evaluate_code(code, prompt)
            llm_results[model] = result
            print(f"📊 {model} LLM Skor: {result['semantic_score']}/100")
        
        return {"llm_evaluation_result": llm_results}
    else:
        # FEEDBACK TURU: İyileştirilen kodu değerlendir
        new_code = state["current_code"]
        result = llm_judge.evaluate_code(new_code, prompt)
        print(f"📊 LLM Semantic Skor: {result['semantic_score']}/100")
        
        return {"llm_evaluation_result": result}


# --- Node 4: Hybrid Scorer Node (Hibrit Skor Birleştirme Düğümü) ---
def hybrid_scorer_node(state: HybridState) -> HybridState:
    """
    Düğüm 4: Static ve LLM sonuçlarını birleştirip hybrid skor hesapla.
    """
    iteration = state.get("iteration_count", 0)
    static_weight = state.get("static_weight", 0.7)
    llm_weight = state.get("llm_weight", 0.3)
    metric_weights = state.get("metric_weights", None)
    
    print(f"\n{'='*60}")
    print(f"⚖️  DÜĞÜM 4: HİBRİT SKOR BİRLEŞTİRME")
    print(f"   (Ağırlıklar - Statik: {static_weight}, LLM: {llm_weight})")
    print(f"{'='*60}\n")
    
    from module.advanced_judge import AdvancedCodeJudge
    judge = AdvancedCodeJudge(metric_weights=metric_weights)
    
    if iteration == 0:
        # İLK TUR: 3 modelin hybrid skorlarını hesapla
        static_results = state["static_analysis_result"]
        llm_results = state["llm_evaluation_result"]
        
        hybrid_scores = {}
        full_analysis = {}
        
        for model in static_results.keys():
            static_analysis = static_results[model]
            llm_evaluation = llm_results[model]
            
            # Hybrid skor hesapla
            hybrid_result = judge.get_hybrid_score(static_analysis, llm_evaluation,
                                                  static_weight=static_weight,
                                                  llm_weight=llm_weight)
            hybrid_scores[model] = hybrid_result["hybrid_score"]
            full_analysis[model] = hybrid_result
            
            print(f"📊 {model} Hybrid Skor: {hybrid_result['hybrid_score']}/100 "
                  f"(Static: {hybrid_result['static_score']}/100, LLM: {hybrid_result['llm_score']}/100)")
        
        # Kazananı bul
        winner = max(hybrid_scores, key=hybrid_scores.get)
        
        # DÜZELTME: Kalite puanı olarak KAZANANIN skorunu kullan (ortalama değil!)
        # Eski: final_quality_score = sum(hybrid_scores.values()) / len(hybrid_scores)
        final_quality_score = hybrid_scores[winner]
        
        print(f"\n🏆 Kazanan: {winner} (Skor: {final_quality_score}/100)")
        
        # Kalite Profili Oluştur
        quality_parts = []
        for model, analysis in full_analysis.items():
            hybrid = analysis.get("hybrid_score", 0)
            static = analysis.get("static_score", 0)
            llm = analysis.get("llm_score", 0)
            reasoning = analysis.get("breakdown", {}).get("llm_evaluation", {}).get("reasoning", "")
            
            quality_parts.append(f"### {model}")
            quality_parts.append(f"- Hybrid Skor: {hybrid}/100 (Statik: {static}/100, LLM: {llm}/100)")
            quality_parts.append(f"- Değerlendirme: {reasoning}")
        
        quality_profile = "\n".join(quality_parts)
        
        # İLK TURDA SPESİFİK ÖNERİLER EKLE
        winner_analysis = full_analysis[winner]
        breakdown = winner_analysis.get("breakdown", {}).get("static_analysis", {}).get("breakdown", {})
        initial_suggestions = []
        
        if breakdown.get("ast_structure", {}).get("score", 0) < 15:
            initial_suggestions.append("- Kod yapısını iyileştir: Docstring ekle, class ve function kullan")
        if breakdown.get("complexity", {}).get("average_complexity", 0) > 10:
            initial_suggestions.append("- Karmaşıklığı azalt: Büyük fonksiyonları böl, nested if'leri azalt")
        if breakdown.get("security", {}).get("issues_count", 0) > 0:
            initial_suggestions.append("- Güvenlik açıklarını düzelt (injection, hardcoded credentials vb.)")
        if breakdown.get("style", {}).get("violations", 0) > 5:
            initial_suggestions.append("- PEP8 standartlarına uy (satır uzunluğu, boşluk kullanımı vb.)")
        
        if initial_suggestions:
            quality_profile += "\n\n## ÖNCELİKLİ İYİLEŞTİRMELER:\n" + "\n".join(initial_suggestions)
        
        print(f"\n📋 QUALITY PROFILE OLUŞTURULDU ({len(quality_profile)} karakter)\n")
        
        # 4_categories'i kazanandan al
        winner_4_categories = static_results[winner].get("4_categories", {})
        
        return {
            "round1_scores": full_analysis,
            "winner_model": winner,
            "winner_code": state["round1_codes"][winner],
            "current_code": state["round1_codes"][winner],
            "winner_score": hybrid_scores[winner],
            "final_quality_score": final_quality_score,
            "current_score": hybrid_scores[winner],
            "hybrid_score": hybrid_scores[winner],
            "quality_profile": quality_profile,
            "previous_categories": winner_4_categories,
            "previous_code_snapshot": state["round1_codes"][winner],
            "iteration_count": iteration + 1
        }
    else:
        # FEEDBACK TURU: İyileştirilen kodun hybrid skorunu hesapla
        previous_code = state.get("previous_code_snapshot", "")
        new_code = state["current_code"]
        previous_score = state["current_score"]
        previous_categories = state.get("previous_categories", {})
        
        static_analysis = state["static_analysis_result"]
        llm_evaluation = state["llm_evaluation_result"]
        
        # Hybrid skor hesapla
        hybrid_result = judge.get_hybrid_score(static_analysis, llm_evaluation,
                                              static_weight=static_weight,
                                              llm_weight=llm_weight)
        new_score = hybrid_result["hybrid_score"]
        new_categories = static_analysis.get("4_categories", {})
        
        print(f"📊 Hybrid Skor: {new_score}/100 "
              f"(Static: {hybrid_result['static_score']}/100, LLM: {hybrid_result['llm_score']}/100)")
        
        # Chain-of-Thought Feedback Agent ile dinamik öneriler üret
        print(f"\n🧠 CoT Feedback Agent çalışıyor...")
        from module.feedback_agent import generate_cot_feedback, format_suggestions_for_prompt
        
        cot_feedback = generate_cot_feedback(
            code=new_code,
            original_prompt=state["prompt"],
            static_analysis=static_analysis,
            llm_evaluation=llm_evaluation,
            previous_score=previous_score,
            current_score=new_score
        )
        
        suggestions = cot_feedback.get("suggestions", [])
        cot_summary = cot_feedback.get("summary", "")
        chain_of_thought = cot_feedback.get("chain_of_thought", "")
        
        # Debug output
        if suggestions:
            print(f"✅ {len(suggestions)} dinamik öneri üretildi")
            for s in suggestions[:3]:  # İlk 3'ü göster
                print(f"   [{s.get('priority', '?')}] {s.get('area', 'Genel')}: {s.get('action', '')[:50]}...")
        else:
            print("⚠️  Öneri üretilemedi, fallback kullanılıyor")
            suggestions = [{"priority": 2, "area": "Genel", "issue": "Kod kalitesi düşük", "action": "Docstring, type hints ve error handling ekle"}]
        
        # Metrik değişimlerini hesapla
        metric_changes = {
            "reliability": new_categories.get("reliability", 0) - previous_categories.get("reliability", 0),
            "maintainability": new_categories.get("maintainability", 0) - previous_categories.get("maintainability", 0),
            "duplications": new_categories.get("duplications", 0) - previous_categories.get("duplications", 0),
            "complexity": new_categories.get("complexity", 0) - previous_categories.get("complexity", 0)
        }
        
        # Feedback geçmişini güncelle
        feedback_iter = state.get("feedback_iterations", [])
        
        # Önceki kodu doğru şekilde al
        # İterasyon 1'de winner_code kullan, sonraki iterasyonlarda previous_code_snapshot
        if iteration == 1:
            previous_code_for_display = state.get("winner_code", "") or state.get("previous_code_snapshot", "")
        else:
            previous_code_for_display = previous_code if previous_code else state.get("previous_code_snapshot", "")
        
        feedback_iter.append({
            "iteration": iteration,
            "previous_code": previous_code_for_display,
            "new_code": new_code,
            "previous_score": previous_score,
            "new_score": new_score,
            "score_improvement": new_score - previous_score,
            "suggestions": suggestions,
            "reasoning": llm_evaluation.get("reasoning", ""),
            "chain_of_thought": chain_of_thought,
            "static_breakdown": static_analysis.get("breakdown", {}),
            "metric_changes": metric_changes,
            "previous_categories": previous_categories,
            "new_categories": new_categories
        })

        
        # Kalite profilini güncelle - DİNAMİK ÖNERİLER ile
        reasoning = llm_evaluation.get("reasoning", "")
        feedback_text = format_suggestions_for_prompt(suggestions)
        
        # ROLLBACK MEKANİZMASI: Skor düştüyse önceki kodu koru
        rollback_applied = False
        final_code = new_code
        final_score = new_score
        final_categories = new_categories
        
        if new_score < previous_score - 2:  # 2 puandan fazla düşüş varsa rollback
            print(f"⚠️  ROLLBACK: Skor {previous_score:.1f} → {new_score:.1f} düştü. Önceki kod korunuyor.")
            rollback_applied = True
            final_code = previous_code
            final_score = previous_score
            final_categories = previous_categories
        else:
            print(f"✅ İyileştirme: {previous_score:.1f} → {new_score:.1f}")
        
        new_quality_profile = f"""### İTERASYON {iteration} FEEDBACK (CoT)

**Mevcut Skor**: {previous_score}/100 → {new_score}/100 (Değişim: {new_score - previous_score:+.1f})
{f"**⚠️ ROLLBACK UYGULANDI** - Önceki kod korundu" if rollback_applied else ""}

**LLM Semantic Değerlendirmesi**:
{reasoning}

**🧠 Chain-of-Thought Dinamik Öneriler**:
{feedback_text}

{f"**Özet**: {cot_summary}" if cot_summary else ""}

**ÖNEMLİ**: Yukarıdaki ÖNCELİKLİ önerileri DİKKATLE uygula. Yüksek öncelikli olanları MUTLAKA düzelt."""
        
        print(f"\n📋 UPDATED QUALITY PROFILE ({len(new_quality_profile)} karakter):")
        print(new_quality_profile[:500] + "..." if len(new_quality_profile) > 500 else new_quality_profile)
        print()
        
        return {
            "current_code": final_code,  # Rollback varsa önceki, yoksa yeni kod
            "current_score": final_score,
            "final_quality_score": final_score,
            "hybrid_score": final_score,
            "feedback_iterations": feedback_iter,
            "quality_profile": new_quality_profile,
            "previous_categories": final_categories,
            "iteration_count": iteration + 1
        }


# --- Decision: Feedback gerekli mi? ---
def should_do_feedback(state: HybridState) -> str:
    """
    Kazananın skoru eşiğin altındaysa feedback'e git
    """
# --- Finalize Node ---
def finalize_node(state: HybridState) -> HybridState:
    """Süreci sonlandırır."""
    
    # Extract reasoning from the latest iteration or the winner
    if state.get("feedback_iterations"):
        reasoning = state["feedback_iterations"][-1].get("reasoning", "")
    else:
        # Getting reasoning from round 1 specific to the winner
        winner = state["winner_model"]
        reasoning = state["round1_scores"].get(winner, {}).get("breakdown", {}).get("llm_evaluation", {}).get("reasoning", "")
        
    return {
        "final_code": state["current_code"],
        "final_score": state["current_score"],
        "feedback_iterations": state.get("feedback_iterations", []),
        "status": "improved_via_feedback" if state["iteration_count"] > 1 else "direct_output",
        "judge_reasoning": reasoning
    }

# --- Decision Node: Devam edilsin mi? ---
def should_continue(state: HybridState) -> str:
    """Eşik kontrolü ve döngü kararı."""
    score = state["final_quality_score"]
    threshold = state.get("quality_threshold", 85.0)
    iteration = state.get("iteration_count", 0)
    
    print(f"\n⚖️  DÖNGÜ KONTROLÜ:")
    print(f"   Mevcut Kalite Puanı: {score:.2f}, Eşik: {threshold}, İterasyon: {iteration}")
    
    if score >= threshold:
        print("   ✅ Hedef sağlandı. Sonlandırılıyor...\n")
        return "finalize"
    elif iteration >= 10:
        print("   ⚠️  Maksimum iterasyon sayısına (10) ulaşıldı. Sonlandırılıyor...\n")
        return "finalize"
    else:
        print("   🔄 Kalite yetersiz. Feedback döngüsü devam ediyor...\n")
        return "generate"

# --- Graph Construction ---
workflow = StateGraph(HybridState)

# 4 ayrı node ekleniyor
workflow.add_node("generator", generator_node)
workflow.add_node("static_analyzer", static_analyzer_node)  # YENİ
workflow.add_node("llm_judge", llm_judge_node)              # YENİ
workflow.add_node("hybrid_scorer", hybrid_scorer_node)      # YENİ (eski judge yerine)
workflow.add_node("finalize", finalize_node)

workflow.set_entry_point("generator")

# Akış sırası: generator → static_analyzer → llm_judge → hybrid_scorer
workflow.add_edge("generator", "static_analyzer")
workflow.add_edge("static_analyzer", "llm_judge")
workflow.add_edge("llm_judge", "hybrid_scorer")

# Conditional: feedback veya finalize
workflow.add_conditional_edges(
    "hybrid_scorer",
    should_continue,
    {
        "generate": "generator",  # Feedback loop
        "finalize": "finalize"
    }
)

workflow.add_edge("finalize", END)

hybrid_graph = workflow.compile()


# --- Public Interface ---
def run_hybrid_workflow(prompt: str, 
                       quality_threshold: float = None, 
                       max_iterations: int = 10,
                       static_weight: float = 0.7,
                       llm_weight: float = 0.3,
                       metric_weights: Dict[str, int] = None) -> Dict[str, Any]:
    """
    Hybrid workflow çalıştır
    
    Args:
        prompt: Kullanıcı prompt'u
        quality_threshold: Kalite eşiği (None ise dinamik hesaplanır)
        max_iterations: Maksimum iterasyon sayısı
        static_weight: Statik analiz ağırlığı (default 0.7)
        llm_weight: LLM değerlendirme ağırlığı (default 0.3)
        metric_weights: Statik analiz metrik ağırlıkları (opsiyonel)
    """
    # Dinamik threshold hesapla veya verilen değeri kullan
    if quality_threshold is None:
        quality_threshold = calculate_dynamic_threshold(prompt)
    
    print(f"\n{'='*60}")
    print(f"🚀 HYBRID WORKFLOW BAŞLIYOR")
    print(f"{'='*60}")
    print(f"Prompt: {prompt[:100]}...")
    print(f"Kalite Eşiği: {quality_threshold}/100 {'(📊 Dinamik)' if quality_threshold != 85.0 else ''}")
    print(f"Max İterasyon: {max_iterations}")
    print(f"Ağırlıklar: Static={static_weight}, LLM={llm_weight}")
    if metric_weights:
        print(f"Özel Metrik Ağırlıkları: {metric_weights}")
    print(f"{'='*60}\n")
    
    initial_state = {
        "prompt": prompt,
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "quality_threshold": quality_threshold,
        "static_weight": static_weight,
        "llm_weight": llm_weight,
        "metric_weights": metric_weights,
        "round1_codes": {},
        "round1_scores": {},
        "current_code": "",
        "current_score": 0.0,
        "previous_code_snapshot": "",
        "previous_categories": {},
        "winner_model": "",
        "final_quality_score": 0.0,
        "static_analysis_result": {},   
        "llm_evaluation_result": {},    
        "hybrid_score": 0.0,             
        "quality_profile": "",
        "feedback_iterations": [],
        "final_code": "",
        "final_score": 0.0,
        "status": "",
        "judge_reasoning": "",
        "request_id": f"REQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    }
    
    result = hybrid_graph.invoke(
        initial_state,
        config={"recursion_limit": 50}
    )
    
    print(f"\n{'='*60}")
    print(f"✨ WORKFLOW TAMAMLANDI")
    print(f"{'='*60}")
    print(f"Durum: {result['status']}")
    print(f"Son Skor: {result['final_score']}/100")
    print(f"{'='*60}\n")
    
    # --- CSV Logging ---
    try:
        # Reuse the request_id already stored in state (same ID used by iteration logs)
        request_id = result.get("request_id", f"REQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}")
        
        # Extract model scores from round1_scores
        round1_scores = result.get("round1_scores", {})
        
        # Dinamik model isimlerini al
        model_names = get_model_names()
        
        # Get detailed scores for each model - static, llm, hybrid
        def _get_scores(model_key):
            data = round1_scores.get(model_names[model_key], {})
            return {
                "hybrid": data.get("hybrid_score", 0.0),
                "static": data.get("static_score", 0.0),
                "llm": data.get("llm_score", 0.0),
            }

        m1 = _get_scores("model_1")
        m2 = _get_scores("model_2")
        m3 = _get_scores("model_3")

        model_scores = {
            "model_1_static":  m1["static"],
            "model_1_llm":     m1["llm"],
            "model_1_hybrid":  m1["hybrid"],
            "model_2_static":  m2["static"],
            "model_2_llm":     m2["llm"],
            "model_2_hybrid":  m2["hybrid"],
            "model_3_static":  m3["static"],
            "model_3_llm":     m3["llm"],
            "model_3_hybrid":  m3["hybrid"],
        }
        
        # Determine status
        iteration_count = result.get("iteration_count", 0) - 1  # Subtract 1 because it's incremented at start
        if iteration_count < 0:
            iteration_count = 0
            
        status = "SUCCESS" if result.get("status") == "improved_via_feedback" or result.get("status") == "direct_output" else "MAX_ITER_REACHED"
        
        # If max iterations reached without success, update status
        if iteration_count >= max_iterations and result.get("final_score", 0) < quality_threshold:
            status = "MAX_ITER_REACHED"
            
        # Get Judge Model Name
        from module.llm_judge import LLMJudge
        judge_model = LLMJudge().get_model_name()
        
        # Log to CSV
        log_request_to_csv(
            request_id=request_id,
            user_prompt=prompt,
            model_names=model_names,
            judge_model=judge_model,
            static_weight=static_weight,
            llm_weight=llm_weight,
            model_scores=model_scores,
            initial_winner=result.get("winner_model", "Unknown"),
            iteration_count=iteration_count,
            final_score=result.get("final_score", 0.0),
            status=status,
            generated_code=result.get("final_code", ""),
            judge_reasoning=result.get("judge_reasoning", ""),
            feedback_iterations=result.get("feedback_iterations", [])
        )
        print(f"📝 Kapsamlı log kaydedildi: {request_id}")
        
        # Excel raporunu otomatik güncelle
        try:
            from module.excel_exporter import export_to_excel
            export_to_excel()
            print(f"📊 Excel raporu güncellendi: logs/workflow_report.xlsx")
        except Exception as excel_err:
            print(f"⚠️  Excel güncelleme hatası: {excel_err}")
            
    except Exception as e:
        print(f"❌ Loglama hatası: {e}")
        import traceback
        traceback.print_exc()
    
    # winner_score'u round1_scores'dan çıkar ve result'a ekle
    # (HybridState TypedDict'de tanımlı değil, LangGraph otomatik döndürmüyor)
    try:
        round1_scores = result.get("round1_scores", {})
        winner_model = result.get("winner_model", "")
        if winner_model and winner_model in round1_scores:
            result["winner_score"] = round1_scores[winner_model].get("hybrid_score", 0.0)
        else:
            result["winner_score"] = result.get("final_score", 0.0)
    except Exception:
        result["winner_score"] = 0.0

    return result

