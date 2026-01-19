"""
Hybrid Agentic Workflow
İlk tur: 3 model yarışması → Kazanan seçimi
İkinci tur: Kazanan < eşik ise feedback döngüsü
"""

from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

# Mevcut modüllerden import
from module.llm_clients import call_codellama, call_deepseek, call_gemini
from module.advanced_judge import AdvancedCodeJudge

# Env variables
load_dotenv()

# --- State Definition ---
class HybridState(TypedDict):
    """Hybrid workflow state"""
    prompt: str
    
    # İlk tur - 3 model kodları
    round1_codes: Dict[str, str]  # {"Llama 3.1 8B": code, "DeepSeek R1": code, "Gemini 1.5 Flash": code}
    round1_scores: Dict[str, float]  # Her modelin skoru
    
    # Kazanan
    winner_model: str
    winner_code: str
    winner_score: float
    
    # Feedback turu (opsiyonel)
    quality_threshold: float
    max_iterations: int
    feedback_iterations: List[Dict[str, Any]]  # Her feedback iterasyonunun detayları
    
    # Final
    final_code: str
    final_score: float
    status: str  # "direct_output" | "improved_via_feedback"


# --- Helper: HYBRID Analysis (Static + LLM) ---
def analyze_with_4_metrics(code: str, prompt: str = "") -> Dict[str, Any]:
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


# --- Node 1: Initial Round (3 Model Yarışması) ---
def initial_round_node(state: HybridState) -> HybridState:
    """
    3 farklı model ile kod üretir ve analiz eder
    """
    prompt = state["prompt"]
    
    print(f"\n{'='*60}")
    print(f"🏁 İLK TUR: 3 MODEL YARIŞMASI")
    print(f"{'='*60}\n")
    
    # 3 GÜÇLÜ model kod üret (CodeLlama 70B, DeepSeek V3, Gemini 2.0)
    codes = {
        "CodeLlama 70B": call_codellama(prompt),
        "DeepSeek V3": call_deepseek(prompt),
        "Gemini 2.0 Flash": call_gemini(prompt)
    }
    
    # Her kodu HYBRID analiz et (static + LLM)
    scores = {}
    full_analysis = {}
    for model, code in codes.items():
        print(f"📊 {model} analiz ediliyor...")
        print(f"   - Statik analiz çalışıyor...")
        print(f"   - LLM semantic evaluation çalışıyor...")
        
        # Prompt'u da geç (LLM judge için gerekli)
        analysis = analyze_with_4_metrics(code, prompt)
        
        hybrid_score = analysis.get("hybrid_score", 0)
        static_score = analysis.get("static_score", 0)
        llm_score = analysis.get("llm_score", 0)
        
        scores[model] = hybrid_score
        full_analysis[model] = analysis
        
        print(f"   ✅ Hybrid Skor: {hybrid_score}/100")
        print(f"      (Statik: {static_score}/100 [70%] + LLM: {llm_score}/100 [30%])\n")
    
    # Kazanan seç
    winner = max(scores, key=scores.get)
    winner_score = scores[winner]
    winner_code = codes[winner]
    
    print(f"\n🏆 KAZANAN: {winner} ({winner_score}/100)\n")
    
    return {
        "round1_codes": codes,
        "round1_scores": full_analysis,  # Now includes full breakdown
        "winner_model": winner,
        "winner_code": winner_code,
        "winner_score": winner_score
    }


# --- Decision: Feedback gerekli mi? ---
def should_do_feedback(state: HybridState) -> str:
    """
    Kazananın skoru eşiğin altındaysa feedback'e git
    """
    score = state["winner_score"]
    threshold = state.get("quality_threshold", 70.0)
    
    print(f"\n⚖️  EŞIK KONTROLÜ:")
    print(f"   Skor: {score}/100, Eşik: {threshold}")
    
    if score >= threshold:
        print("   ✅ Eşik sağlandı - Direkt çıktı!\n")
        return "finalize"
    else:
        print("   🔄 Eşik altında - Feedback döngüsüne giriyor...\n")
        return "feedback"


# --- Node 2: Feedback Loop ---
def feedback_loop_node(state: HybridState) -> HybridState:
    """
    Kazanan modeli feedback ile iyileştir
    """
    winner_model = state["winner_model"]
    current_code = state["winner_code"]
    current_score = state["winner_score"]
    max_iter = state.get("max_iterations", 3)
    threshold = state.get("quality_threshold", 70.0)
    
    print(f"\n{'='*60}")
    print(f"🔄 FEEDBACK DÖNGÜSÜ BAŞLIYOR")
    print(f"{'='*60}\n")
    
    feedback_iterations = []
    iteration = 0
    
    # Llama LLM for feedback generation
    llama_llm = ChatGroq(
        model_name="llama-3.1-8b-instant",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1
    )
    
    while iteration < max_iter and current_score < threshold:
        iteration += 1
        print(f"   İterasyon {iteration}/{max_iter}")
        
        # Önceki kodu sakla (before/after comparison için)
        previous_code = current_code
        previous_score = current_score
        
        # Feedback üret (basit heuristic)
        judge = AdvancedCodeJudge()
        analysis = judge.score_code(current_code)
        breakdown = analysis["breakdown"]
        previous_categories = analysis.get("4_categories", {})
        
        suggestions = []
        if breakdown["ast_structure"]["score"] < 15:
            suggestions.append({
                "area": "Kod Yapısı",
                "issue": f"AST skoru düşük ({breakdown['ast_structure']['score']}/20)",
                "action": "Docstring ekle, class ve function kullan"
            })
        if breakdown["complexity"].get("average_complexity", 0) > 10:
            suggestions.append({
                "area": "Karmaşıklık",
                "issue": f"Ortalama karmaşıklık yüksek ({breakdown['complexity'].get('average_complexity', 0)})",
                "action": "Büyük fonksiyonları böl, nested if'leri azalt"
            })
        if breakdown["security"]["issues_count"] > 0:
            suggestions.append({
                "area": "Güvenlik",
                "issue": f"{breakdown['security']['issues_count']} güvenlik açığı tespit edildi",
                "action": "Güvenlik açıklarını düzelt (injection, hardcoded credentials vb.)"
            })
        if breakdown["style"]["violations"] > 5:
            suggestions.append({
                "area": "Stil (PEP8)",
                "issue": f"{breakdown['style']['violations']} stil ihlali",
                "action": "PEP8 standartlarına uy (satır uzunluğu, boşluk kullanımı vb.)"
            })
        if breakdown["duplications"]["duplication_ratio"] > 0.2:
            suggestions.append({
                "area": "Kod Tekrarı",
                "issue": f"Yüksek tekrar oranı (%{breakdown['duplications']['duplication_ratio']*100:.1f})",
                "action": "Tekrarlanan kodları fonksiyonlara çıkar"
            })
        
        # Metinsel feedback oluştur
        feedback_text = "\n".join([f"- {s['area']}: {s['action']}" for s in suggestions]) if suggestions else "Kodun kalitesini artır"
        
        # Detaylı feedback prompt oluştur
        enhanced_prompt = f"""Orijinal İstek: {state['prompt']}

Mevcut Kod:
{current_code}

İyileştirme Önerileri:
{feedback_text}

Lütfen yukarıdaki önerileri dikkate alarak kodu iyileştir. SADECE Python kodu üret."""
        
        # Kazanan modelle yeniden üret
        if "CodeLlama" in winner_model or "Llama" in winner_model:
            new_code = call_codellama(enhanced_prompt)
        elif "DeepSeek" in winner_model:
            new_code = call_deepseek(enhanced_prompt)
        else:  # Gemini
            new_code = call_gemini(enhanced_prompt)
        
        # Yeni kodu analiz et
        new_analysis = analyze_with_4_metrics(new_code)
        new_score = new_analysis["total_score"]
        new_categories = new_analysis.get("4_categories", {})
        
        # Metrik değişimlerini hesapla
        metric_changes = {
            "reliability": (new_categories.get("reliability", 0) - previous_categories.get("reliability", 0)),
            "maintainability": (new_categories.get("maintainability", 0) - previous_categories.get("maintainability", 0)),
            "duplications": (new_categories.get("duplications", 0) - previous_categories.get("duplications", 0)),
            "complexity": (new_categories.get("complexity", 0) - previous_categories.get("complexity", 0))
        }
        
        print(f"   Yeni skor: {new_score}/100")
        
        # İterasyonu kaydet (detaylı)
        feedback_iterations.append({
            "iteration": iteration,
            "previous_code": previous_code,
            "new_code": new_code,
            "previous_score": previous_score,
            "new_score": new_score,
            "score_improvement": new_score - previous_score,
            "suggestions": suggestions,
            "feedback": feedback_text,
            "metric_changes": metric_changes,
            "previous_categories": previous_categories,
            "new_categories": new_categories
        })
        
        # Güncelle
        current_code = new_code
        current_score = new_score
        
        if current_score >= threshold:
            print(f"   ✅ Eşiğe ulaşıldı!\n")
            break
    
    if current_score < threshold:
        print(f"   ⚠️  Max iterasyona ulaşıldı ({max_iter})\n")
    
    return {
        "feedback_iterations": feedback_iterations,
        "final_code": current_code,
        "final_score": current_score,
        "status": "improved_via_feedback" if feedback_iterations else "direct_output"
    }


# --- Node 3: Finalize (direkt çıktı) ---
def finalize_node(state: HybridState) -> HybridState:
    """
    Eşik sağlandıysa kazanan kodu direkt final olarak işaretle
    """
    return {
        "final_code": state["winner_code"],
        "final_score": state["winner_score"],
        "status": "direct_output",
        "feedback_iterations": []
    }


# --- Graph Construction ---
workflow = StateGraph(HybridState)

# Node'ları ekle
workflow.add_node("initial_round", initial_round_node)
workflow.add_node("feedback_loop", feedback_loop_node)
workflow.add_node("finalize", finalize_node)

# Entry point
workflow.set_entry_point("initial_round")

# Conditional routing
workflow.add_conditional_edges(
    "initial_round",
    should_do_feedback,
    {
        "feedback": "feedback_loop",
        "finalize": "finalize"
    }
)

# Both feedback and finalize end
workflow.add_edge("feedback_loop", END)
workflow.add_edge("finalize", END)

# Compile
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
        "round1_codes": {},
        "round1_scores": {},
        "winner_model": "",
        "winner_code": "",
        "winner_score": 0.0,
        "quality_threshold": quality_threshold,
        "max_iterations": max_iterations,
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
    
    return result
