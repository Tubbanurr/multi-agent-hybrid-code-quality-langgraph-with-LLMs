// Main frontend logic

// State to store last results for analysis
let lastResults = {
    "CodeLlama": "",
    "DeepSeek-V3": "",
    "Gemini 2.5": ""
};

async function generateCode() {
    const prompt = document.getElementById("prompt").value;
    if (!prompt) return alert("Lütfen bir prompt girin!");

    const btn = document.getElementById("btn-generate");
    const loader = document.getElementById("loader-generate");

    // UI Loading State
    btn.disabled = true;
    loader.style.display = "inline-block";

    // Clear previous results
    document.querySelectorAll('code').forEach(el => el.textContent = 'Kod üretiliyor...');
    document.getElementById("winner-llm").style.display = "none";
    document.getElementById("winner-static").style.display = "none";

    try {
        const response = await fetch("/generate-code", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt })
        });

        if (!response.ok) throw new Error("API Hatası");

        const data = await response.json();
        lastResults = data.models;

        // Render Results
        renderCode("code-llama", data.models["CodeLlama"]);
        renderCode("code-deepseek", data.models["DeepSeek-V3"]);
        renderCode("code-gemini", data.models["Gemini 2.5"]);

        // Re-highlight using Prism
        Prism.highlightAll();

    } catch (error) {
        alert("Hata oluştu: " + error.message);
    } finally {
        btn.disabled = false;
        loader.style.display = "none";
    }
}

function renderCode(elementId, code) {
    const el = document.getElementById(elementId);
    // Escape HTML to prevent injection and render properly in <pre>
    el.textContent = code;
}

async function analyzeResults() {
    // Check if we have results
    if (!lastResults["CodeLlama"]) return alert("Önce kod üretmeniz lazım!");

    const btn = document.getElementById("btn-analyze");
    const loader = document.getElementById("loader-analyze");

    btn.disabled = true;
    loader.style.display = "inline-block";

    try {
        const payload = {
            llama: lastResults["CodeLlama"],
            deepseek: lastResults["DeepSeek-V3"],
            gemini: lastResults["Gemini 2.5"]
        };

        const response = await fetch("/analyze-results", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        // Visualize Scores in LLM panels
        renderScore("score-llama-llm", data.scores["CodeLlama"]);
        renderScore("score-deepseek-llm", data.scores["DeepSeek-V3"]);
        renderScore("score-gemini-llm", data.scores["Gemini 2.5"]);

        // Show Winner in LLM section
        const winnerDiv = document.getElementById("winner-llm");
        winnerDiv.innerHTML = `
            <div class="winner-title">🏆 Kazanan Model (LLM Hakem)</div>
            <h2 style="font-size:2rem; margin:0;">${data.winner}</h2>
            <p>Toplam Puan: <strong>${data.scores[data.winner].total}</strong></p>
            
            <div style="margin-top:20px; text-align:left; background:rgba(255,255,255,0.7); padding:15px; border-radius:8px;">
                <strong>💡 Yapay Zeka Hakem Görüşü:</strong>
                <p style="margin-top:5px; font-style:italic; font-size:1rem;">"${data.reasoning}"</p>
            </div>
        `;
        winnerDiv.style.display = "block";

    } catch (error) {
        alert("Analiz Hatası: " + error.message);
    } finally {
        btn.disabled = false;
        loader.style.display = "none";
    }
}

async function analyzeAdvanced() {
    //Check if we have results
    if (!lastResults["CodeLlama"]) return alert("Önce kod üretmeniz lazım!");

    const btn = document.getElementById("btn-analyze-advanced");
    const loader = document.getElementById("loader-analyze-advanced");

    btn.disabled = true;
    loader.style.display = "inline-block";

    try {
        const payload = {
            llama: lastResults["CodeLlama"],
            deepseek: lastResults["DeepSeek-V3"],
            gemini: lastResults["Gemini 2.5"]
        };

        const response = await fetch("/analyze-advanced", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        // Render advanced scores with detailed breakdown in Static panels
        renderAdvancedScore("score-llama-static", data.scores["CodeLlama"]);
        renderAdvancedScore("score-deepseek-static", data.scores["DeepSeek-V3"]);
        renderAdvancedScore("score-gemini-static", data.scores["Gemini 2.5"]);

        // Show Winner in Static section
        const winnerDiv = document.getElementById("winner-static");
        winnerDiv.innerHTML = `
            <div class="winner-title">🏆 Kazanan Model (Static Analysis)</div>
            <h2 style="font-size:2rem; margin:0;">${data.winner}</h2>
            <p>Toplam Puan: <strong>${data.scores[data.winner].total_score}/100</strong></p>
            
            <div style="margin-top:20px; text-align:left; background:rgba(255,255,255,0.7); padding:15px; border-radius:8px;">
                <strong>🔬 Objektif Analiz Raporu:</strong>
                <p style="margin-top:5px; font-style:italic; font-size:1rem;">"${data.reasoning}"</p>
                <p style="margin-top:10px; font-size:0.9rem; color:#666;">
                    <strong>Araçlar:</strong> AST, Pylint, Radon, Bandit, Flake8, Type Hints
                </p>
            </div>
        `;
        winnerDiv.style.display = "block";

    } catch (error) {
        alert("Gelişmiş Analiz Hatası: " + error.message);
    } finally {
        btn.disabled = false;
        loader.style.display = "none";
    }
}

function renderScore(containerId, scoreData) {
    const container = document.getElementById(containerId);

    // Helper to draw a bar
    const drawBar = (label, value, max = 20) => {
        const pct = (value / max) * 100;
        return `
            <div class="metric">
                <span style="width:80px;">${label}</span>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width:${pct}%; background-color: ${getColor(pct)};"></div>
                </div>
                <span style="width:30px; text-align:right;">${value}</span>
            </div>
        `;
    };

    container.innerHTML = `
        <div style="background:#28a745; color:white; padding:8px; font-weight:bold; text-align:center; border-radius:4px; margin-bottom:10px;">
            📊 LLM Analizi
        </div>
        ${drawBar("Syntax", scoreData.syntax)}
        ${drawBar("Clean", scoreData.cleanliness, 15)}
        ${drawBar("OOP", scoreData.oop)}
        ${drawBar("Complexity", scoreData.complexity)}
        <div class="total-score">Total: ${scoreData.total}</div>
        <div style="font-size:0.8rem; color:red; margin-top:5px;">${scoreData.error_msg || ''}</div>
    `;
}

function renderAdvancedScore(containerId, scoreData) {
    const container = document.getElementById(containerId);

    if (!scoreData || !scoreData.breakdown) {
        container.innerHTML = '<p style="color:red;">Error loading scores</p>';
        return;
    }

    const bd = scoreData.breakdown;

    container.innerHTML = `
        <div style="background:#6f42c1; color:white; padding:8px; font-weight:bold; text-align:center; border-radius:4px; margin-bottom:10px;">
            🔬 Static Analysis
        </div>
        <div style="background:#f8f9fa; padding:12px; border-radius:6px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <strong>1️⃣ AST Structure:</strong>
                <span>${bd.ast_structure.score}/20</span>
            </div>
            <div style="font-size:0.8rem; color:#666;">
                Classes: ${bd.ast_structure.classes}, Functions: ${bd.ast_structure.functions}, Docs: ${bd.ast_structure.docstrings}
            </div>
        </div>
        
        <div style="background:#f8f9fa; padding:12px; border-radius:6px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <strong>2️⃣ Pylint Quality:</strong>
                <span>${bd.pylint_quality.scaled_score}/25</span>
            </div>
            ${bd.pylint_quality.raw_score ? `<div style="font-size:0.8rem; color:#666;">Raw: ${bd.pylint_quality.raw_score.toFixed(1)}/10</div>` : ''}
        </div>
        
        <div style="background:#f8f9fa; padding:12px; border-radius:6px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <strong>3️⃣ Complexity:</strong>
                <span>${bd.complexity.score}/20</span>
            </div>
            ${bd.complexity.average_complexity ? `<div style="font-size:0.8rem; color:#666;">Avg: ${bd.complexity.average_complexity.toFixed(2)}</div>` : ''}
        </div>
        
        <div style="background:#f8f9fa; padding:12px; border-radius:6px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <strong>4️⃣ Security:</strong>
                <span>${bd.security.score}/15</span>
            </div>
            <div style="font-size:0.8rem; color:#666;">
                ${bd.security.severity_high > 0 ? `🔴 HIGH: ${bd.security.severity_high} ` : ''}
                ${bd.security.severity_medium > 0 ? `🟡 MED: ${bd.security.severity_medium} ` : ''}
                ${bd.security.issues_count === 0 ? '✅ No issues' : ''}
            </div>
        </div>
        
        <div style="background:#f8f9fa; padding:12px; border-radius:6px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <strong>5️⃣ Style (PEP8):</strong>
                <span>${bd.style.score}/10</span>
            </div>
            <div style="font-size:0.8rem; color:#666;">Violations: ${bd.style.violations}</div>
        </div>
        
        <div style="background:#f8f9fa; padding:12px; border-radius:6px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <strong>6️⃣ Type Hints:</strong>
                <span>${bd.type_hints.score}/10</span>
            </div>
            ${bd.type_hints.total_functions > 0 ? `<div style="font-size:0.8rem; color:#666;">Coverage: ${(bd.type_hints.coverage * 100).toFixed(0)}%</div>` : ''}
        </div>
        
        <div class="total-score" style="background:#004DB3; color:white; padding:10px; border-radius:6px;">
            Total: ${scoreData.total_score}/100
        </div>
    `;
}

function getColor(pct) {
    if (pct < 40) return '#dc3545';
    if (pct < 70) return '#ffc107';
    return '#28a745';
}
