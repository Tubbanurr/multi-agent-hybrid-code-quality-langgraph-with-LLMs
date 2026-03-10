// Hybrid Workflow Frontend Logic - Turkish & Detailed Feedback
// NOW WITH HYBRID SCORING (Static + LLM)
// Updated for Ollama support with dynamic model names

// --- Canlı bekleme durumu ---
let statusInterval = null;
const statusMessages = [
    "⏳ Modeller koda hazırlanıyor...",
    "🤖 Ollama yerel modeller çalışıyor...",
    "📝 Kod üretimi devam ediyor...",
    "🔍 Statik analiz yürütülüyor...",
    "🧠 LLM değerlendirmesi yapılıyor...",
    "🏆 En iyi kod seçiliyor...",
    "🔄 Feedback döngüsü işleniyor...",
    "⚙️  Kalite eşiği kontrol ediliyor...",
    "✨ Sonuçlar hazırlanıyor...",
];

function startStatusTicker() {
    const statusEl = document.getElementById("status-message");
    if (!statusEl) return;
    statusEl.style.display = "block";
    let i = 0;
    statusEl.textContent = statusMessages[0];
    statusInterval = setInterval(() => {
        i = (i + 1) % statusMessages.length;
        statusEl.textContent = statusMessages[i];
    }, 3000);
}

function stopStatusTicker() {
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }
    const statusEl = document.getElementById("status-message");
    if (statusEl) statusEl.style.display = "none";
}

function showError(message) {
    let errEl = document.getElementById("error-banner");
    if (!errEl) {
        errEl = document.createElement("div");
        errEl.id = "error-banner";
        errEl.style.cssText = `
            background: #fee2e2;
            border: 2px solid #ef4444;
            border-radius: 10px;
            padding: 1rem 1.5rem;
            margin-top: 1rem;
            color: #b91c1c;
            font-weight: 600;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        `;
        document.querySelector(".input-section").appendChild(errEl);
    }
    errEl.innerHTML = `<span style="font-size:1.4rem">⚠️</span> ${message}`;
    errEl.style.display = "flex";
}

function clearError() {
    const errEl = document.getElementById("error-banner");
    if (errEl) errEl.style.display = "none";
}

async function generate() {
    const prompt = document.getElementById("prompt").value;
    if (!prompt) return alert("Lütfen bir prompt girin");

    const btn = document.getElementById("btn-generate");
    const loader = document.getElementById("loader");

    // UI Loading
    btn.disabled = true;
    loader.style.display = "inline-block";
    clearError();

    // Sonuç bölümlerini gizle
    document.getElementById("round1-section").style.display = "none";
    document.getElementById("winner-section").style.display = "none";

    // Canlı durum mesajını başlat
    startStatusTicker();

    try {
        // 1. Job'ı başlat — sunucu ANINDA job_id döndürür
        const response = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt })
        });

        if (!response.ok) throw new Error(`Sunucu hatası: HTTP ${response.status}`);

        const { job_id } = await response.json();
        console.log("Job başlatıldı:", job_id);

        // 2. Polling — sonuç gelene kadar her 3sn'de sorgula
        await pollStatus(job_id);

    } catch (error) {
        showError("Hata: " + error.message);
        stopStatusTicker();
        btn.disabled = false;
        loader.style.display = "none";
    }
}

async function pollStatus(job_id) {
    const btn = document.getElementById("btn-generate");
    const loader = document.getElementById("loader");

    const poll = async () => {
        try {
            const res = await fetch(`/status/${job_id}`);

            // 404: sunucu restart olmuş, job bellekten silindi
            if (res.status === 404) {
                stopStatusTicker();
                btn.disabled = false;
                loader.style.display = "none";
                showError("Sunucu yeniden başlatıldı, işlem kayboldu. Lütfen tekrar gönderin.");
                return;
            }

            if (!res.ok) throw new Error(`Status sorgu hatası: HTTP ${res.status}`);


            const data = await res.json();

            if (data.status === "done") {
                // İşlem tamamlandı
                stopStatusTicker();
                btn.disabled = false;
                loader.style.display = "none";

                const result = data.result;
                console.log("Sonuç:", result);

                // Null güvenlik kontrolü
                if (!result || !result.round1_codes || !result.round1_scores) {
                    showError("Sonuç verisi eksik veya hatalı. Terminali kontrol edin.");
                    return;
                }

                showRound1(result.round1_codes, result.round1_scores);
                showWinner(result);


            } else if (data.status === "error") {
                // Hata oluştu
                stopStatusTicker();
                btn.disabled = false;
                loader.style.display = "none";
                showError("İşlem hatası: " + (data.error || "Bilinmeyen hata"));

            } else {
                // Hâlâ çalışıyor (pending / running) — 3sn sonra tekrar sor
                setTimeout(poll, 3000);
            }

        } catch (err) {
            stopStatusTicker();
            btn.disabled = false;
            loader.style.display = "none";
            showError("Polling hatası: " + err.message);
        }
    };

    // İlk sorguyu 2sn sonra yap (workflow'un başlamasına zaman ver)
    setTimeout(poll, 2000);
}


function showRound1(codes, scoresData) {
    if (!codes || !scoresData) return;  // null guard
    document.getElementById("round1-section").style.display = "block";


    // Dinamik model isimleri - backend'den gelen isimleri kullan
    const modelKeys = Object.keys(codes);
    const modelSlots = ["llama", "deepseek", "gemini"];

    modelKeys.forEach((modelName, index) => {
        const slotId = modelSlots[index] || `model-${index}`;
        const code = codes[modelName] || "Kod üretilemedi";
        const scoreData = scoresData[modelName];

        // Update model header with dynamic name
        const headerElement = document.getElementById(`header-${slotId}`);
        if (headerElement) headerElement.textContent = modelName;

        // Display code
        const codeElement = document.getElementById(`code-${slotId}`);
        if (codeElement) codeElement.textContent = code;

        // Display HYBRID score with breakdown
        const scorePanel = document.getElementById(`score-${slotId}`);

        if (!scoreData || scoreData.is_error) {
            // API HATASI - ÖZEL GÖSTER
            scorePanel.innerHTML = `
                <div style="background: #fee; padding: 1rem; border-radius: 8px; border: 2px solid #f00; text-align: center;">
                    <div style="font-weight: bold; color: #d00; font-size: 1.2rem;">API HATASI</div>
                    <div style="margin-top: 0.5rem; color: #666; font-size: 0.9rem;">Model kod üretemedi</div>
                    <div style="margin-top: 0.5rem; font-weight: bold;">Skor: 0/100</div>
                </div>
            `;
            return;
        }

        const hybridScore = scoreData.hybrid_score || scoreData.total_score || 0;
        const staticScore = scoreData.static_score || 0;
        const llmScore = scoreData.llm_score || 0;

        // Get breakdowns from correct paths
        const staticAnalysis = scoreData.breakdown?.static_analysis || scoreData;
        const llmEvaluation = scoreData.breakdown?.llm_evaluation || {};
        const staticBreakdown = staticAnalysis.breakdown || {};
        const llmBreakdown = llmEvaluation.breakdown || {};

        // 4_categories is inside static_analysis, not at root level
        const categories = staticAnalysis["4_categories"] || scoreData["4_categories"] || {};

        scorePanel.innerHTML = `
            <!-- Hybrid Score Badge -->
            <div class="score-total">
                <div class="hybrid-badge">
                    <div class="score-total-value">Hybrid: ${hybridScore}/100</div>
                </div>
                <div class="score-breakdown">
                    Statik: ${staticScore}/100 (70%) | LLM: ${llmScore}/100 (30%)
                </div>
            </div>
            
            <!-- Static Analysis Categories -->
            <div class="categories-container">
                <div class="categories-title">Statik Analiz Metrikleri</div>
                
                <div class="category-item">
                    <div class="category-header">
                        <span class="category-label">Güvenilirlik</span>
                        <span class="category-value">${categories.reliability || 0}/35</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill reliability" style="width: ${(categories.reliability || 0) / 35 * 100}%"></div>
                    </div>
                </div>
                
                <div class="category-item">
                    <div class="category-header">
                        <span class="category-label">Sürdürülebilirlik</span>
                        <span class="category-value">${categories.maintainability || 0}/45</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill maintainability" style="width: ${(categories.maintainability || 0) / 45 * 100}%"></div>
                    </div>
                </div>
                
                <div class="category-item">
                    <div class="category-header">
                        <span class="category-label">Kod Tekrarı</span>
                        <span class="category-value">${categories.duplications || 0}/10</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill duplications" style="width: ${(categories.duplications || 0) / 10 * 100}%"></div>
                    </div>
                </div>
                
                <div class="category-item">
                    <div class="category-header">
                        <span class="category-label">Karmaşıklık</span>
                        <span class="category-value">${categories.complexity || 0}/20</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill complexity" style="width: ${(categories.complexity || 0) / 20 * 100}%"></div>
                    </div>
                </div>
            </div>
            
            <!-- LLM Semantic Evaluation (NEW!) -->
            <div class="llm-evaluation">
                <div class="llm-title">LLM Semantic Değerlendirme</div>
                <div class="llm-breakdown">
                    <div>
                        <span>Algorithm Correctness:</span>
                        <span class="llm-score-value">${llmBreakdown.algorithm_correctness || 0}/25</span>
                    </div>
                    <div>
                        <span>Code Logic:</span>
                        <span class="llm-score-value">${llmBreakdown.code_logic || 0}/25</span>
                    </div>
                    <div>
                        <span>Best Practices:</span>
                        <span class="llm-score-value">${llmBreakdown.best_practices || 0}/25</span>
                    </div>
                    <div>
                        <span>Readability:</span>
                        <span class="llm-score-value">${llmBreakdown.readability || 0}/25</span>
                    </div>
                </div>
                ${llmEvaluation.chain_of_thought ? `
                    <details class="cot-thinking" style="margin-top: 0.75rem; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 8px; padding: 0.5rem;">
                        <summary style="cursor: pointer; font-weight: 600; color: #a78bfa; display: flex; align-items: center; gap: 0.5rem;">
                            <span style="animation: pulse 2s infinite;">🧠</span> Chain-of-Thought (Düşünce Süreci)
                        </summary>
                        <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #94a3b8; line-height: 1.6; font-family: monospace; white-space: pre-wrap; max-height: 200px; overflow-y: auto; padding: 0.5rem; background: rgba(0,0,0,0.3); border-radius: 4px;">
                            ${llmEvaluation.chain_of_thought}
                        </div>
                    </details>
                ` : ''}
                ${llmEvaluation.reasoning ? `
                    <details style="margin-top: 0.75rem;">
                        <summary style="cursor: pointer; font-weight: 600; color: var(--gray-700);">💬 LLM Reasoning (Sonuç)</summary>
                        <p style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--gray-600); line-height: 1.6;">
                            ${llmEvaluation.reasoning}
                        </p>
                    </details>
                ` : ''}
            </div>
            
            <!-- Detaylı Analiz (Collapsible) -->
            <details>
                <summary>Detaylı Statik Analiz</summary>
                <div class="details-content">
                    <div><strong>AST Yapısı:</strong> ${staticBreakdown.ast_structure?.score || 0}/20</div>
                    <div><strong>Pylint Kalitesi:</strong> ${staticBreakdown.pylint_quality?.scaled_score || 0}/25</div>
                    <div><strong>Güvenlik:</strong> ${staticBreakdown.security?.score || 0}/15 ${staticBreakdown.security?.issues_count > 0 ? '(' + staticBreakdown.security.issues_count + ' açık)' : '(Temiz)'}</div>
                    <div><strong>Stil (PEP8):</strong> ${staticBreakdown.style?.score || 0}/10 (${staticBreakdown.style?.violations || 0} ihlal)</div>
                    <div><strong>Type Hints:</strong> ${staticBreakdown.type_hints?.score || 0}/10</div>
                    <div><strong>Kod Tekrarı:</strong> ${staticBreakdown.duplications?.score || 0}/10 (%${((staticBreakdown.duplications?.duplication_ratio || 0) * 100).toFixed(1)} tekrar)</div>
                </div>
            </details>
        `;
    });

    Prism.highlightAll();
}

function showWinner(data) {
    document.getElementById("winner-section").style.display = "block";

    const winnerInfo = document.getElementById("winner-info");
    const statusText = data.status === "direct_output"
        ? "Eşik sağlandı - Direkt çıktı"
        : "Feedback döngüsü ile iyileştirildi";

    const hybridScore = data.final_score || 0;

    // Başlangıç skoru: backend'den gelen winner_score (round1 hybrid skoru)
    // Fallback: round1_scores içinden kazananın skorunu bul
    let initialScore = data.winner_score;
    if (!initialScore && data.round1_scores && data.winner_model) {
        const winnerData = data.round1_scores[data.winner_model];
        initialScore = winnerData?.hybrid_score || winnerData?.total_score || 0;
    }
    initialScore = initialScore || 0;

    winnerInfo.innerHTML = `
        <div class="winner-title">Kazanan Model</div>
        <h2 class="winner-model">${data.winner_model}</h2>
        <div class="winner-stats">
            <strong>Başlangıç Skoru:</strong> ${initialScore}/100 &rarr; 
            <strong>Final Skor:</strong> ${hybridScore}/100
            <span style="color: ${hybridScore > initialScore ? '#10b981' : '#ef4444'}; font-weight: bold; margin-left: 10px;">
                (${hybridScore > initialScore ? '+' : ''}${(hybridScore - initialScore).toFixed(1)} puan)
            </span>
        </div>
        <div class="winner-status">
            <strong>Durum:</strong> ${statusText}
        </div>
    `;

    // Feedback iterationslarını göster (detaylı)
    if (data.feedback_iterations && data.feedback_iterations.length > 0) {
        document.getElementById("feedback-section").style.display = "block";
        showDetailedFeedback(data.feedback_iterations);
    } else {
        document.getElementById("feedback-section").style.display = "none";
    }

    // Final kodu göster
    document.getElementById("final-code").textContent = data.final_code;
    Prism.highlightElement(document.getElementById("final-code"));
}

function showDetailedFeedback(iterations) {
    const container = document.getElementById("feedback-iterations");
    container.innerHTML = "";

    iterations.forEach((iter, index) => {
        const improvement = iter.score_improvement || 0;
        const improvementClass = improvement > 0 ? 'positive' : (improvement < 0 ? 'negative' : 'neutral');

        const iterDiv = document.createElement("div");
        iterDiv.className = "feedback-iteration-detailed";
        iterDiv.innerHTML = `
            <div class="iteration-header">
                <h4>İterasyon ${iter.iteration}</h4>
                <div class="iteration-scores">
                    <span class="score-badge prev">${iter.previous_score}/100</span>
                    <span class="arrow">→</span>
                    <span class="score-badge new ${improvementClass}">${iter.new_score}/100</span>
                    <span class="improvement ${improvementClass}">
                        (${improvement > 0 ? '+' : ''}${improvement.toFixed(1)})
                    </span>
                </div>
            </div>
            
            <!-- Chain-of-Thought Thinking -->
            ${iter.chain_of_thought ? `
            <details class="cot-thinking" style="margin-bottom: 1rem; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 8px; padding: 0.75rem;">
                <summary style="cursor: pointer; font-weight: 600; color: #a78bfa; display: flex; align-items: center; gap: 0.5rem;">
                    <span style="animation: pulse 2s infinite;">🧠</span> CoT Düşünce Süreci
                </summary>
                <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #94a3b8; line-height: 1.6; font-family: monospace; white-space: pre-wrap; max-height: 150px; overflow-y: auto; padding: 0.5rem; background: rgba(0,0,0,0.3); border-radius: 4px;">
                    ${iter.chain_of_thought}
                </div>
            </details>
            ` : ''}
            
            <!-- İyileştirme Önerileri -->
            <div class="suggestions-box">
                <div class="suggestions-title">🎯 Dinamik Öneriler:</div>
                ${iter.suggestions && iter.suggestions.length > 0 ?
                iter.suggestions.map(s => `
                        <div class="suggestion-item" style="border-left: 3px solid ${s.priority === 1 ? '#ef4444' : s.priority === 2 ? '#f59e0b' : '#22c55e'}; padding-left: 0.5rem; margin-bottom: 0.5rem;">
                            <div class="suggestion-area" style="font-weight: 600; color: ${s.priority === 1 ? '#ef4444' : s.priority === 2 ? '#f59e0b' : '#22c55e'};">[${s.priority === 1 ? 'KRİTİK' : s.priority === 2 ? 'ÖNEMLİ' : 'DÜŞÜK'}] ${s.area}</div>
                            <div class="suggestion-issue" style="font-size: 0.85rem;">Sorun: ${s.issue || ''}</div>
                            <div class="suggestion-action" style="font-size: 0.85rem; font-weight: 500;">Aksiyon: ${s.action || ''}</div>
                        </div>
                    `).join('')
                : '<div style="color: #999;">Genel iyileştirmeler</div>'
            }
            </div>
            
            <!-- Metrik Değişimleri -->
            <div class="metric-changes">
                <div class="metric-changes-title">Metrik Değişimleri:</div>
                <div class="metric-changes-grid">
                    ${Object.entries(iter.metric_changes || {}).map(([metric, change]) => {
                const changeClass = change > 0 ? 'positive' : (change < 0 ? 'negative' : 'neutral');
                return `
                            <div class="metric-change-item">
                                <span class="metric-name">${getMetricLabel(metric)}:</span>
                                <span class="metric-change ${changeClass}">
                                    ${change > 0 ? '+' : ''}${change}
                                </span>
                            </div>
                        `;
            }).join('')}
                </div>
            </div>
            
            <!-- Kod Karşılaştırması -->
            <details class="code-comparison">
                <summary>Kod Değişimini Gör (Öncesi vs Sonrası)</summary>
                <div class="comparison-grid">
                    <div class="comparison-col">
                        <div class="comparison-label">Önceki Kod (${iter.previous_score}/100)</div>
                        <pre><code class="language-python">${iter.previous_code || 'N/A'}</code></pre>
                    </div>
                    <div class="comparison-col">
                        <div class="comparison-label">İyileştirilmiş Kod (${iter.new_score}/100)</div>
                        <pre><code class="language-python">${iter.new_code || 'N/A'}</code></pre>
                    </div>
                </div>
            </details>
        `;
        container.appendChild(iterDiv);
    });

    // Re-highlight kod blokları
    container.querySelectorAll('pre code').forEach(block => {
        Prism.highlightElement(block);
    });
}

function getMetricLabel(metric) {
    const labels = {
        'reliability': 'Güvenilirlik',
        'maintainability': 'Sürdürülebilirlik',
        'duplications': 'Kod Tekrarı',
        'complexity': 'Karmaşıklık'
    };
    return labels[metric] || metric;
}
