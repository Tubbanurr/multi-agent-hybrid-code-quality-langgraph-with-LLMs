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
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Mevcut modüllerden import
from module.llm_clients import call_codellama, call_deepseek, call_gemini
from module.advanced_judge import AdvancedCodeJudge

# Env variables
load_dotenv()

# --- CSV Logging Utility ---
def log_request_to_csv(
    request_id: str,
    user_prompt: str,
    model_llama_score: float,
    model_deepseek_score: float,
    model_gemini_score: float,
    initial_winner: str,
    iteration_count: int,
    final_score: float,
    status: str,
    log_file: str = "logs/workflow_log.csv"
):
    """
    Append workflow summary to CSV file.
    
    Args:
        request_id: Unique identifier for this request
        user_prompt: User's original prompt
        model_llama_score: CodeLlama's initial hybrid score
        model_deepseek_score: DeepSeek's initial hybrid score
        model_gemini_score: Gemini's initial hybrid score
        initial_winner: Model that won in round 1
        iteration_count: Number of feedback iterations
        final_score: Final quality score after iterations
        status: SUCCESS or MAX_ITER_REACHED
        log_file: Path to CSV log file
    """
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Check if file exists to determine if we need to write headers
    file_exists = os.path.isfile(log_file)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    with open(log_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header if file is new
        if not file_exists:
            writer.writerow([
                "Request_ID",
                "User_Prompt",
                "Model_Llama_Score",
                "Model_DeepSeek_Score",
                "Model_Gemini_Score",
                "Initial_Winner",
                "Iteration_Count",
                "Final_Score",
                "Status",
                "Timestamp"
            ])
        
        # Write data row
        writer.writerow([
            request_id,
            user_prompt[:100],  # Truncate long prompts
            f"{model_llama_score:.1f}",
            f"{model_deepseek_score:.1f}",
            f"{model_gemini_score:.1f}",
            initial_winner,
            iteration_count,
            f"{final_score:.1f}",
            status,
            timestamp
        ])

# --- State Definition ---
class HybridState(TypedDict):
    """Hybrid workflow state"""
    prompt: str
    iteration_count: int
    max_iterations: int
    quality_threshold: float
    
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


# --- Helper: HYBRID Analysis (Static + LLM) ---
def analyze_with_4_metrics(code: str, prompt: str = "") -> Dict[str, Any]:
    """Perform static + LLM analysis and return hybrid result including LLM reasoning."""
    """
    HYBRID ANALYSIS: Static (70%) + LLM Semantic (30%)
    
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
            "weights": {"static": 0.7, "llm": 0.3},
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
    judge = AdvancedCodeJudge()
    static_analysis = judge.score_code(code)
    
    # 2. LLM Semantic Evaluation (new)
    llm_judge = LLMJudge()
    llm_evaluation = llm_judge.evaluate_code(code, prompt)
    
    # 3. Combine into Hybrid Score
    hybrid_result = judge.get_hybrid_score(static_analysis, llm_evaluation)
    
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
        
        codes = {
            "CodeLlama 70B": call_codellama(prompt),
            "DeepSeek V3": call_deepseek(prompt),
            "Gemini 2.0 Flash": call_gemini(prompt)
        }
        return {"round1_codes": codes}
    else:
        print(f"\n{'='*60}")
        print(f"🔄 DÜĞÜM 1: KOD İYİLEŞTİRME (İterasyon {iteration})")
        print(f"{'='*60}\n")
        
        # Geliştirilmiş prompt oluştur (Düğüm 2'den gelen kalite profili ile)
        enhanced_prompt = f"""Orijinal İstek: {prompt}

QUALITY PROFILE (Ajanların değerlendirmeleri):
{state['quality_profile']}

Mevcut Kod:
{state['current_code']}

Lütfen yukarıdaki profil ve önerileri dikkate alarak kodu iyileştir. SADECE kod üret."""
        
        winner_model = state["winner_model"]
        if "CodeLlama" in winner_model:
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
    
    print(f"\n{'='*60}")
    print(f"🔍 DÜĞÜM 2: STATİK ANALİZ")
    print(f"{'='*60}\n")
    
    from module.advanced_judge import AdvancedCodeJudge
    judge = AdvancedCodeJudge()
    
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
    
    print(f"\n{'='*60}")
    print(f"⚖️  DÜĞÜM 4: HİBRİT SKOR BİRLEŞTİRME")
    print(f"{'='*60}\n")
    
    from module.advanced_judge import AdvancedCodeJudge
    judge = AdvancedCodeJudge()
    
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
            hybrid_result = judge.get_hybrid_score(static_analysis, llm_evaluation)
            hybrid_scores[model] = hybrid_result["hybrid_score"]
            full_analysis[model] = hybrid_result
            
            print(f"📊 {model} Hybrid Skor: {hybrid_result['hybrid_score']}/100 "
                  f"(Static: {hybrid_result['static_score']}/100, LLM: {hybrid_result['llm_score']}/100)")
        
        # Kazananı bul
        winner = max(hybrid_scores, key=hybrid_scores.get)
        
        # Ağırlıklı Ortalama (Nihai Kalite Puanı)
        final_quality_score = sum(hybrid_scores.values()) / len(hybrid_scores)
        
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
        hybrid_result = judge.get_hybrid_score(static_analysis, llm_evaluation)
        new_score = hybrid_result["hybrid_score"]
        new_categories = static_analysis.get("4_categories", {})
        
        print(f"📊 Hybrid Skor: {new_score}/100 "
              f"(Static: {hybrid_result['static_score']}/100, LLM: {hybrid_result['llm_score']}/100)")
        
        # Heuristic-based suggestions
        breakdown = static_analysis.get("breakdown", {})
        suggestions = []
        if breakdown.get("ast_structure", {}).get("score", 0) < 15:
            suggestions.append({"area": "Kod Yapısı", "action": "Docstring ekle, class ve function kullan"})
        if breakdown.get("complexity", {}).get("average_complexity", 0) > 10:
            suggestions.append({"area": "Karmaşıklık", "action": "Büyük fonksiyonları böl, nested if'leri azalt"})
        if breakdown.get("security", {}).get("issues_count", 0) > 0:
            suggestions.append({"area": "Güvenlik", "action": "Güvenlik açıklarını düzelt"})
        if breakdown.get("style", {}).get("violations", 0) > 5:
            suggestions.append({"area": "Stil (PEP8)", "action": "PEP8 standartlarına uy"})
        
        # Metrik değişimlerini hesapla
        metric_changes = {
            "reliability": new_categories.get("reliability", 0) - previous_categories.get("reliability", 0),
            "maintainability": new_categories.get("maintainability", 0) - previous_categories.get("maintainability", 0),
            "duplications": new_categories.get("duplications", 0) - previous_categories.get("duplications", 0),
            "complexity": new_categories.get("complexity", 0) - previous_categories.get("complexity", 0)
        }
        
        # Feedback geçmişini güncelle
        feedback_iter = state.get("feedback_iterations", [])
        
        if iteration == 1:
            previous_code = state.get("winner_code", "")
        
        feedback_iter.append({
            "iteration": iteration,
            "previous_code": previous_code,
            "new_code": new_code,
            "previous_score": previous_score,
            "new_score": new_score,
            "score_improvement": new_score - previous_score,
            "suggestions": suggestions,
            "reasoning": llm_evaluation.get("reasoning", ""),
            "static_breakdown": breakdown,
            "metric_changes": metric_changes,
            "previous_categories": previous_categories,
            "new_categories": new_categories
        })
        
        # Kalite profilini güncelle
        reasoning = llm_evaluation.get("reasoning", "")
        feedback_text = "\n".join([f"- {s['area']}: {s['action']}" for s in suggestions]) if suggestions else "Kodun kalitesini artır"
        
        new_quality_profile = f"""### İTERASYON {iteration} FEEDBACK

**Mevcut Skor**: {previous_score}/100 → {new_score}/100 (Değişim: {new_score - previous_score:+.1f})

**LLM Semantic Değerlendirmesi**:
{reasoning}

**Tespit Edilen Sorunlar ve Öneriler**:
{feedback_text}

**ÖNEMLİ**: Yukarıdaki önerileri DİKKATLE uygula. Her bir sorunu FİZİKSEL OLARAK düzelt."""
        
        print(f"\n📋 UPDATED QUALITY PROFILE ({len(new_quality_profile)} karakter):")
        print(new_quality_profile[:500] + "..." if len(new_quality_profile) > 500 else new_quality_profile)
        print()
        
        return {
            "current_score": new_score,
            "final_quality_score": new_score,
            "hybrid_score": new_score,
            "feedback_iterations": feedback_iter,
            "quality_profile": new_quality_profile,
            "previous_categories": new_categories,
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
    return {
        "final_code": state["current_code"],
        "final_score": state["current_score"],
        "feedback_iterations": state.get("feedback_iterations", []),
        "status": "improved_via_feedback" if state["iteration_count"] > 1 else "direct_output"
    }

# --- Decision Node: Devam edilsin mi? ---
def should_continue(state: HybridState) -> str:
    """Eşik kontrolü ve döngü kararı."""
    score = state["final_quality_score"]
    threshold = state.get("quality_threshold", 70.0)
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
def run_hybrid_workflow(prompt: str, quality_threshold: float = 70.0, max_iterations: int = 3) -> Dict[str, Any]:
    """
    Hybrid workflow çalıştır
    
    Returns:
        {
            "round1_codes": {...},
            "round1_scores": {...},
            "winner_model": str,
            "winner_score": float,
            "feedback_iterations": [...] (boş olabilir),
            "final_code": str,
            "final_score": float,
            "status": "direct_output" | "improved_via_feedback"
        }
    """
    print(f"\n{'='*60}")
    print(f"🚀 HYBRID WORKFLOW BAŞLIYOR")
    print(f"{'='*60}")
    print(f"Prompt: {prompt[:100]}...")
    print(f"Kalite Eşiği: {quality_threshold}/100")
    print(f"Max İterasyon: {max_iterations}")
    print(f"{'='*60}\n")
    
    initial_state = {
        "prompt": prompt,
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "quality_threshold": quality_threshold,
        "round1_codes": {},
        "round1_scores": {},
        "current_code": "",
        "current_score": 0.0,
        "previous_code_snapshot": "",
        "previous_categories": {},
        "winner_model": "",
        "final_quality_score": 0.0,
        "static_analysis_result": {},   # ← YENİ ALAN
        "llm_evaluation_result": {},    # ← YENİ ALAN
        "hybrid_score": 0.0,             # ← YENİ ALAN
        "quality_profile": "",
        "feedback_iterations": [],
        "final_code": "",
        "final_score": 0.0,
        "status": ""
    }
    
    result = hybrid_graph.invoke(initial_state)
    
    print(f"\n{'='*60}")
    print(f"✨ WORKFLOW TAMAMLANDI")
    print(f"{'='*60}")
    print(f"Durum: {result['status']}")
    print(f"Son Skor: {result['final_score']}/100")
    print(f"{'='*60}\n")
    
    # --- CSV Logging ---
    try:
        # Generate unique request ID
        request_id = f"REQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Extract model scores from round1_scores
        round1_scores = result.get("round1_scores", {})
        
        # Get hybrid scores for each model
        llama_score = round1_scores.get("CodeLlama 70B", {}).get("hybrid_score", 0.0)
        deepseek_score = round1_scores.get("DeepSeek V3", {}).get("hybrid_score", 0.0)
        gemini_score = round1_scores.get("Gemini 2.0 Flash", {}).get("hybrid_score", 0.0)
        
        # Determine status
        iteration_count = result.get("iteration_count", 0) - 1  # Subtract 1 because it's incremented at start
        if iteration_count < 0:
            iteration_count = 0
            
        status = "SUCCESS" if result.get("status") == "improved_via_feedback" or result.get("status") == "direct_output" else "MAX_ITER_REACHED"
        
        # If max iterations reached without success, update status
        if iteration_count >= max_iterations and result.get("final_score", 0) < quality_threshold:
            status = "MAX_ITER_REACHED"
        
        # Log to CSV
        log_request_to_csv(
            request_id=request_id,
            user_prompt=prompt,
            model_llama_score=llama_score,
            model_deepseek_score=deepseek_score,
            model_gemini_score=gemini_score,
            initial_winner=result.get("winner_model", "Unknown"),
            iteration_count=iteration_count,
            final_score=result.get("final_score", 0.0),
            status=status
        )
        print(f"📝 Log kaydedildi: {request_id}")
    except Exception as e:
        print(f"⚠️  CSV logging hatası: {e}")
    
    return result

