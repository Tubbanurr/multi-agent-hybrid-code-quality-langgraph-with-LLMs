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
    document.getElementById("winner-display").style.display = "none";

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

        // Visualize Scores
        renderScore("score-llama", data.scores["CodeLlama"]);
        renderScore("score-deepseek", data.scores["DeepSeek-V3"]);
        renderScore("score-gemini", data.scores["Gemini 2.5"]);

        // Show Winner
        const winnerDiv = document.getElementById("winner-display");
        winnerDiv.innerHTML = `
            <div class="winner-title">🏆 Kazanan Model</div>
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
        ${drawBar("Syntax", scoreData.syntax)}
        ${drawBar("Clean", scoreData.cleanliness, 15)}
        ${drawBar("OOP", scoreData.oop)}
        ${drawBar("Complexity", scoreData.complexity)}
        <div class="total-score">Total: ${scoreData.total}</div>
        <div style="font-size:0.8rem; color:red; margin-top:5px;">${scoreData.error_msg || ''}</div>
    `;
}

function getColor(pct) {
    if (pct < 40) return '#dc3545';
    if (pct < 70) return '#ffc107';
    return '#28a745';
}
