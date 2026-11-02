# Havelsan-SUIT-AP
Kocaeli Üniversitesi AP

---

## HAVELSAN Hybrid Code Generator — Proje Özeti

### Ne Yapıyor?

Kullanıcıdan bir Python kodu isteği alıp, **3 yapay zeka modelini aynı anda çalıştırarak** en iyi kodu üretmeye ve iteratif olarak iyileştirmeye çalışan bir web uygulaması. Kocaeli Üniversitesi'nin HAVELSAN iş birliğiyle yürütülen bir araştırma/tez projesi.

---

### Sistemin Çalışma Mantığı (5 Adım)

```
Kullanıcı Promptu
       │
       ▼
[DÜĞÜM 1] Kod Üretimi ─── 3 model paralel çalışır
       │
       ▼
[DÜĞÜM 2] Statik Analiz ── Pylint, AST, Radon, Bandit, Flake8
       │
       ▼
[DÜĞÜM 3] LLM Yargıcı ─── Semantic değerlendirme (anlam, mantık)
       │
       ▼
[DÜĞÜM 4] Hibrit Skor ──── %70 Statik + %30 LLM → 100 puan
       │
       ├─ Skor ≥ Eşik? → [FİNAL] Direkt çıktı
       │
       └─ Skor < Eşik? → CoT Feedback → Düğüm 1'e geri dön (max 11 tur)
```

Grafı yöneten kütüphane: **LangGraph** (StateGraph yapısı)

---

### Kullanılan Yapay Zeka Modelleri

| Rol | Cloud Modu | Yerel (Ollama) Modu |
|---|---|---|
| **Kod Üretici 1** | Llama 3.3 70B (Groq) | Qwen2.5-Coder |
| **Kod Üretici 2** | DeepSeek V3 | DeepSeek-R1 |
| **Kod Üretici 3** | Gemini 2.0 Flash | Llama 3.2 |
| **LLM Yargıcı** | Llama 3.3 70B (Groq) | DeepSeek-R1 |
| **Feedback Ajanı** | Llama 3.3 70B (Groq) | DeepSeek-R1 |

---

### Puanlama Sistemi (100 Puan)

#### Statik Analiz Araçları (70 puan)
- **AST Analyzer** — Sözdizimi geçerliliği, type hints, hata yönetimi
- **Lint Analyzer** — Pylint skoru + Flake8 PEP8 uyumu
- **Complexity Analyzer** — Radon ile döngüsel karmaşıklık (cyclomatic complexity)
- **Security Analyzer** — Bandit ile güvenlik açığı tespiti
- **Coverage Analyzer** — Test kapsamı
- **Content Analyzer** — Yorum yoğunluğu, kod tekrarı (duplication)

#### LLM Semantik Değerlendirme (30 puan)
- Identifier Clarity (0–5): Değişken isimleri anlamlı mı?
- Prompt Adherence (0–10): İstek tam karşılandı mı?
- Naming Alignment (0–5): Alan terminolojisi doğru kullanıldı mı?
- Logic & Reliability (0–10): Mantık sağlam ve güvenilir mi?

#### 6 Final Kategorisi

| Kategori | Max Puan |
|---|---|
| 1. Kod Kalitesi | 20 |
| 2. Teknik Borç | 20 |
| 3. Test & Build | 15 |
| 4. Stil & Standart | 15 |
| 5. Semantic Alignment | 15 |
| 6. Robustness & Safety | 15 |

---

### Akıllı Özellikler

- **Dinamik Eşik (60–88):** Prompt ne kadar karmaşıksa ("binary search", "async", "OOP" gibi anahtar kelimeler) eşik o kadar yükselir. Basit prompt için düşük eşik yeterlidir.
- **Rollback Mekanizması:** Yeni iterasyonda skor düşerse sistem önceki daha iyi koda otomatik geri döner.
- **Chain-of-Thought Feedback:** Her başarısız iterasyondan sonra LLM, **neden** skor düşük olduğunu analiz edip kategoriye özgü somut öneriler üretir (JSON formatında).
- **Erken Durma:** Art arda 4 iterasyon iyileşme yoksa döngü sonlandırılır.

---

### Çıktılar ve Loglama

- **CSV Log** (`logs/workflow_log.csv`): Her isteğin tam geçmişi
- **Excel Raporu** (`logs/workflow_report.xlsx`): Formatlı, renkli tablo
- **Benchmark Runner** (`benchmark_runner.py`): Bir Excel dosyasındaki toplu promptları sırasıyla sisteme gönderip sonuçları karşılaştırmalı test eder — tez için performans değerlendirmesi yapılmaktadır.

---

### Teknoloji Yığını

`FastAPI` + `LangGraph` + `Groq/DeepSeek/Gemini API` + `Pylint` + `Radon` + `Bandit` + `Flake8` + `Pandas/OpenPyXL`
