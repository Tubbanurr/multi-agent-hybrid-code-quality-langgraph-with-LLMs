// Global Functions (attached to window for direct HTML access)
window.copyCode = function(elementId) {
    const codeElement = document.getElementById(elementId);
    if (!codeElement) {
        console.error("Copy failed: Element not found", elementId);
        return;
    }

    const text = codeElement.innerText || codeElement.textContent || "";
    if (!text) return;

    const triggerFeedback = () => {
        const container = codeElement.closest('.code-container') || codeElement.closest('.comparison-col');
        const btn = container ? container.querySelector('.copy-btn') : null;
        if (btn) {
            const originalText = btn.textContent;
            btn.textContent = "Copied!";
            btn.classList.add("copied");
            setTimeout(() => {
                btn.textContent = originalText;
                btn.classList.remove("copied");
            }, 2000);
        }
    };

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text)
            .then(() => triggerFeedback())
            .catch(err => {
                console.warn("Modern copy failed, trying fallback...", err);
                if (window.fallbackCopyTextToClipboard(text)) triggerFeedback();
            });
    } else {
        if (window.fallbackCopyTextToClipboard(text)) triggerFeedback();
    }
};

window.fallbackCopyTextToClipboard = function(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-9999px";
    textArea.style.top = "0";
    textArea.style.opacity = "0";
    textArea.setAttribute("readonly", "");
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    textArea.setSelectionRange(0, 999999);

    let successful = false;
    try {
        successful = document.execCommand('copy');
    } catch (err) {
        console.error('Fallback copy failed:', err);
    }
    document.body.removeChild(textArea);
    return successful;
};

// Error Handler
window.onerror = function(message, source, lineno, colno, error) {
    console.error(`JS HATA: ${message} @ ${source}:${lineno}:${colno}`);
    return false;
};

async function generate() {
    const prompt = document.getElementById("prompt").value;
    if (!prompt) return alert("Lütfen bir prompt girin");

    const btn = document.getElementById("btn-generate");
    const loader = document.getElementById("loader");

    // UI Loading
    btn.disabled = true;
    loader.style.display = "inline-block";

    // Hide sections
    document.getElementById("round1-section").style.display = "none";
    document.getElementById("winner-section").style.display = "none";

    try {
        const response = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt })
        });

        if (!response.ok) throw new Error("API Hatası");

        const data = await response.json();
        console.log("Sonuç:", data);

        // Round 1: 3 model kodları göster (HYBRID SCORES)
        showRound1(data.round1_codes, data.round1_scores);

        // Kazanan ve feedback
        showWinner(data);

    } catch (error) {
        alert("Hata: " + error.message);
    } finally {
        btn.disabled = false;
        loader.style.display = "none";
    }
}

function showRound1(codes, scoresData) {
    document.getElementById("round1-section").style.display = "block";

    // Dinamik model isimleri - backend'den gelen isimleri kullan
    const modelKeys = Object.keys(codes);
    const modelSlots = ["model-1", "model-2", "model-3"];

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
        if (!scorePanel) {
            console.error(`Missing element: score-${slotId}`);
            return;
        }

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

        const hybridScore = scoreData.total_score || 0;
        const staticScore = scoreData.static_total || 0;
        const llmScore = scoreData.llm_total || 0;

        const categories = scoreData.categories || {};
        const staticAnalysis = scoreData.static_analysis || {};
        const llmEvaluation = scoreData.llm_evaluation || {};
        const staticBreakdown = staticAnalysis.breakdown || {};
        const llmBreakdown = llmEvaluation.breakdown || {};

        scorePanel.innerHTML = `
            <!-- Hybrid Score Badge -->
            <div class="score-total">
                <div class="hybrid-badge">
                    <div class="score-total-value">Hybrid: ${hybridScore}/100</div>
                </div>
                <div class="score-breakdown">
                    Statik: ${(staticScore / 70 * 100).toFixed(1)}/100 (70%) | LLM: ${(llmScore / 30 * 100).toFixed(1)}/100 (30%)
                </div>
            </div>
            
            <!-- 6 Hybrid Categories -->
            <div class="categories-container">
                <div class="categories-title">Kod Kalite Metrikleri (6 Kategori)</div>
                
                <div class="category-item">
                    <div class="category-header">
                        <span class="category-label">1. Kod Kalitesi</span>
                        <span class="category-value">${categories["1_Kod_Kalitesi"] || 0}/25</span>
                    </div>
                    <div class="progress-bars-container" style="display: flex; gap: 2px;">
                        <div class="progress-bar" style="flex: 1;"><div class="progress-fill" style="width: ${(categories["1_Kod_Kalitesi"] || 0) / 25 * 100}%; background: #3b82f6;"></div></div>
                    </div>
                </div>
                
                <div class="category-item">
                    <div class="category-header">
                        <span class="category-label">2. Teknik Borç</span>
                        <span class="category-value">${categories["2_Teknik_Borc"] || 0}/20</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${(categories["2_Teknik_Borc"] || 0) / 20 * 100}%; background: #f59e0b;"></div>
                    </div>
                </div>
                
                <div class="category-item">
                    <div class="category-header">
                        <span class="category-label">3. Test & Build</span>
                        <span class="category-value">${categories["3_Test_Build"] || 0}/15</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${(categories["3_Test_Build"] || 0) / 15 * 100}%; background: #10b981;"></div>
                    </div>
                </div>
                
                <div class="category-item">
                    <div class="category-header">
                        <span class="category-label">4. Stil & Standart</span>
                        <span class="category-value">${categories["4_Stil_Standart"] || 0}/15</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${(categories["4_Stil_Standart"] || 0) / 15 * 100}%; background: #6366f1;"></div>
                    </div>
                </div>

                <div class="category-item">
                    <div class="category-header">
                        <span class="category-label">5. Semantic Alignment</span>
                        <span class="category-value">${categories["5_Semantic_Alignment"] || 0}/15</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${(categories["5_Semantic_Alignment"] || 0) / 15 * 100}%; background: #ec4899;"></div>
                    </div>
                </div>

                <div class="category-item">
                    <div class="category-header">
                        <span class="category-label">6. Robustness & Safety</span>
                        <span class="category-value">${categories["6_Robustness_Safety"] || 0}/10</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${(categories["6_Robustness_Safety"] || 0) / 10 * 100}%; background: #ef4444;"></div>
                    </div>
                </div>
            </div>
            
            <!-- LLM Semantic Evaluation -->
            <div class="llm-evaluation">
                <div class="llm-title">LLM Semantic Değerlendirme</div>
                <div class="llm-breakdown">
                    <div class="llm-metric-row">
                        <span>Identifier Clarity:</span>
                        <span class="llm-score-value">${llmBreakdown.identifier_clarity || 0}/5</span>
                    </div>
                    <div class="llm-metric-row">
                        <span>Prompt Adherence:</span>
                        <span class="llm-score-value">${llmBreakdown.prompt_adherence || 0}/10</span>
                    </div>
                    <div class="llm-metric-row">
                        <span>Naming Alignment:</span>
                        <span class="llm-score-value">${llmBreakdown.naming_alignment || 0}/5</span>
                    </div>
                    <div class="llm-metric-row">
                        <span>Logic & Reliability:</span>
                        <span class="llm-score-value">${llmBreakdown.test_reliability || 0}/10</span>
                    </div>
                </div>
                ${llmEvaluation.chain_of_thought ? `
                    <details class="cot-thinking" style="margin-top: 0.75rem; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 8px; padding: 0.5rem;">
                        <summary style="cursor: pointer; font-weight: 600; color: #a78bfa; display: flex; align-items: center; gap: 0.5rem;">
                            <span style="animation: pulse 2s infinite;">🧠</span> CoT (Düşünce Süreci)
                        </summary>
                        <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #94a3b8; line-height: 1.6; font-family: monospace; white-space: pre-wrap; max-height: 200px; overflow-y: auto; padding: 0.5rem; background: rgba(0,0,0,0.3); border-radius: 4px;">
                            ${llmEvaluation.chain_of_thought}
                        </div>
                    </details>
                ` : ''}
                ${llmEvaluation.reasoning ? `
                    <details style="margin-top: 0.75rem;">
                        <summary style="cursor: pointer; font-weight: 600; color: var(--gray-700);">💬 LLM Reasoning</summary>
                        <p style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--gray-600); line-height: 1.6;">
                            ${llmEvaluation.reasoning}
                        </p>
                    </details>
                ` : ''}
            </div>
            
            <!-- Detaylı Statik Analiz -->
            <details>
                <summary>Detaylı Statik Metrikler</summary>
                <div class="details-content">
                    <div><strong>Syntax/AST:</strong> ${staticBreakdown.syntax?.score || 0}/5</div>
                    <div><strong>Pylint:</strong> ${staticBreakdown.pylint?.scaled_score || 0}/15 (Raw: ${staticBreakdown.pylint?.raw_score?.toFixed(2) || 0}/10)</div>
                    <div><strong>Karmaşıklık:</strong> ${staticBreakdown.complexity?.score || 0}/15 (Max: ${staticBreakdown.complexity?.max_complexity || 0})</div>
                    <div><strong>Stil (PEP8):</strong> ${staticBreakdown.style?.score || 0}/10 (İhlal: ${staticBreakdown.style?.violations || 0})</div>
                    <div><strong>Yorum Yoğunluğu:</strong> ${staticBreakdown.comments?.score || 0}/5 (%${((staticBreakdown.comments?.density || 0) * 100).toFixed(1)})</div>
                    <div><strong>Kod Tekrarı:</strong> ${staticBreakdown.duplication?.score || 0}/5 (%${((staticBreakdown.duplication?.duplication_ratio || 0) * 100).toFixed(1)})</div>
                    <div><strong>Hata Yönetimi:</strong> ${staticBreakdown.error_handling || 0}/10</div>
                </div>
            </details>
        `;
    });

    Prism.highlightAll();
}

function showWinner(data) {
    document.getElementById("winner-section").style.display = "block";

    const winnerInfo = document.getElementById("winner-info");
    if (!winnerInfo) {
        console.error("Missing element: winner-info");
        return;
    }
    const statusText = data.status === "direct_output"
        ? "Eşik sağlandı - Direkt çıktı"
        : "Feedback döngüsü ile iyileştirildi";

    const hybridScore = data.final_score || 0;
    const initialScore = data.winner_score || 0;

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
    if (!container) {
        console.error("Missing element: feedback-iterations");
        return;
    }
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
                        <div class="code-container" style="height: auto; max-height: 400px;">
                            <button class="copy-btn" onclick="copyCode('prev-code-${index}')">Copy</button>
                            <pre><code id="prev-code-${index}" class="language-python">${iter.previous_code || 'N/A'}</code></pre>
                        </div>
                    </div>
                    <div class="comparison-col">
                        <div class="comparison-label">İyileştirilmiş Kod (${iter.new_score}/100)</div>
                        <div class="code-container" style="height: auto; max-height: 400px;">
                            <button class="copy-btn" onclick="copyCode('new-code-${index}')">Copy</button>
                            <pre><code id="new-code-${index}" class="language-python">${iter.new_code || 'N/A'}</code></pre>
                        </div>
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

// Initial load
document.addEventListener("DOMContentLoaded", () => {
    updateModelHeaders();
});

async function updateModelHeaders() {
    try {
        const response = await fetch("/models");
        const models = await response.json();

        document.getElementById("header-model-1").textContent = models.model_1 || "Model 1";
        document.getElementById("header-model-2").textContent = models.model_2 || "Model 2";
        document.getElementById("header-model-3").textContent = models.model_3 || "Model 3";
    } catch (err) {
        console.error("Modeller yüklenemedi:", err);
    }
}

function getMetricLabel(metric) {
    const labels = {
        '1_Kod_Kalitesi': 'Kod Kalitesi',
        '2_Teknik_Borc': 'Teknik Borç',
        '3_Test_Build': 'Test & Build',
        '4_Stil_Standart': 'Stil & Standart',
        '5_Semantic_Alignment': 'Semantic Alignment',
        '6_Robustness_Safety': 'Robustness & Safety',
        'reliability': 'Güvenilirlik',
        'maintainability': 'Sürdürülebilirlik',
        'duplications': 'Kod Tekrarı',
        'complexity': 'Karmaşıklık'
    };
    return labels[metric] || metric;
}


// End of Script
