# Havelsan-SUIT-AP

## 📋 Proje Özeti

Bu proje, **LLM (Large Language Model) tabanlı bir kod üretici ve değerlendirme platformu**dur. Kullanıcıdan bir prompt alır, üç farklı AI modeli (CodeLlama, DeepSeek-V3, Gemini) ile kod üretir ve bu kodları **iki farklı hakem sistemi** ile kalite açısından karşılaştırarak en iyisini seçer.

## 🆕 Yeni Özellikler

### 🔬 Gelişmiş Hakem Sistemi (Static Analysis)
- **6 katmanlı objektif kod analizi**: AST, Pylint, Radon, Bandit, Flake8, Type Hints
- **API key gerektirmez** - Tamamen ücretsiz ve offline çalışır
- **Detaylı metrikler**: 100 puan üzerinden 6 farklı kategoride analiz
- **Hızlı**: <1 saniyede sonuç
- Detaylı kılavuz: [`ADVANCED_JUDGE_GUIDE.md`](./ADVANCED_JUDGE_GUIDE.md)

### � Türkçe Dil Desteği
- LLM hakem artık **Türkçe açıklama** yapıyor
- Kullanıcı arayüzü Türkçe
- Hata mesajları Türkçe

### 🎨 Yeni Arayüz
- **3 buton sistemi**: Kod üret, LLM analiz, Static analiz
- Mor renkli "Gelişmiş Analiz" butonu
- Detaylı skor breakdown'ları

---

## �🏗️ Proje Mimarisi

### **Ana Bileşenler:**

1. **Backend (FastAPI)** - API sunucusu
2. **Frontend (HTML/CSS/JS)** - Kullanıcı arayüzü
3. **LLM Modülleri** - Kod üretme ve değerlendirme mantığı
4. **Static Analysis Modülü** - Objektif kod kalitesi analizi

---

## 📂 Dosya Yapısı ve Bağlantılar

### **1. Ana Giriş Noktası: `main.py`**
- **Rol:** FastAPI web sunucusu
- **Bağlantılar:**
  - `module/llm_clients.py` → `call_codellama()`, `call_deepseek()`, `call_gemini()` fonksiyonlarını import eder
  - `module/agent_graph.py` → `run_agent()` fonksiyonunu import eder
  - `module/advanced_judge.py` → `advanced_judge()` fonksiyonunu import eder **[YENİ!]**
  - `templates/index.html` → Root endpoint'te HTML dosyasını serve eder
  - `static/` klasörü → CSS ve JS dosyalarını static olarak sunar

- **API Endpoints:**
  - `GET /` → Frontend'i gösterir
  - `POST /generate-code` → 3 modelden kod üretir
  - `POST /analyze-results` → Üretilen kodları LLM hakem ile analiz eder (LangGraph)
  - `POST /analyze-advanced` → **YENİ!** Static analysis araçları ile objektif değerlendirme (Pylint + Radon + Bandit + Flake8)

---

### **2. LLM İstemci Modülü: `module/llm_clients.py`**
- **Rol:** Farklı LLM API'larına istek gönderir
- **Fonksiyonlar:**
  - `call_codellama()` → Groq API üzerinden Llama 3.3 (70B) modelini çağırır
  - `call_deepseek()` → OpenRouter API üzerinden DeepSeek V3 modelini çağırır
  - `call_gemini()` → Google AI REST API üzerinden Gemini 2.0 Flash modelini çağırır

- **Bağımlılıklar:**
  - `.env` dosyasından API anahtarları okur (GROQ_API_KEY, DEEPSEEK_API_KEY, GEMINI_API_KEY)
  - `groq` paketi, `requests` paketi kullanır

- **Kullanım:**
  - `main.py` tarafından `/generate-code` endpoint'inde kullanılır
  - `agent_graph.py` tarafından `generate_competitors` node'unda kullanılır

---

### **3. Agentic Graph (LangGraph): `module/agent_graph.py`**
- **Rol:** LangGraph kullanarak kod üretimi ve değerlendirme sürecini yönetir
- **Yapı:**
  ```
  generate_competitors → judge_solutions → END
  ```

- **Node'lar:**
  1. **`generate_competitors`**: 3 modelden kod üretir (opsiyonel, zaten üretilmişse atlanır)
  2. **`judge_solutions`**: Llama 3 modelini **Türkçe konuşan hakem** olarak kullanıp kodları değerlendirir **[GÜNCELLENMIŞ!]**

- **State (AgentState):**
  ```python
  {
    "prompt": str,           # Kullanıcı isteği
    "code_llama": str,       # Llama'nın ürettiği kod
    "code_deepseek": str,    # DeepSeek'in ürettiği kod
    "code_gemini": str,      # Gemini'nin ürettiği kod
    "judge_result": dict     # Hakem sonucu (winner, reasoning(TÜRKÇE), scores)
  }
  ```

- **Hakem Kriterleri:**
  - ✅ Doğruluk (Kullanıcı isteğini çözüyor mu?)
  - ✅ Verimlilik (Big O karmaşıklığı, kaynak kullanımı)
  - ✅ Stil (Temizlik, yorumlar, isimlendirme)
  - ✅ Güvenlik (Güvenlik açığı yok mu?)

- **Bağlantılar:**
  - `llm_clients.py` → `call_deepseek()` kullanır
  - `langchain-groq`, `langchain-google-genai` paketlerini kullanır
  - `main.py` tarafından `/analyze-results` endpoint'inde çağrılır

---

### **4. Kod Kalite Analizi (Eski Yöntem): `module/code_quality.py`**
- **Rol:** Regex tabanlı basit kod kalite analizi (şu an aktif olarak kullanılmıyor)
- **Fonksiyonlar:**
  - `clean_code()`: Markdown formatındaki koddan saf Python kodu çıkarır
  - `CodeQualityAnalyzer.score()`: AST ve regex ile kod kalitesini puanlar
  - `compare_models()`: 3 modelin skorlarını karşılaştırır

- **Not:** 
  - `main.py`'de yorum satırına alınmış
  - Şu an yerine `agent_graph.py` (LLM hakem) veya `advanced_judge.py` (Static analysis) kullanılıyor

---

### **4b. 🆕 Gelişmiş Kod Kalite Analizi: `module/advanced_judge.py`**
- **Rol:** **AST + Pylint + Radon + Bandit + Flake8** araçları ile objektif kod değerlendirmesi
- **Araçlar:**
  - **AST** (Python built-in) → Kod yapısı analizi
  - **Pylint** → Kapsamlı kod kalitesi skorlama (0-10 → 25 puan)
  - **Radon** → Cyclomatic complexity ölçümü
  - **Bandit** → Güvenlik açığı taraması
  - **Flake8** → PEP8 stil kontrolü
  - **Type Hints** (AST) → Type annotation coverage

- **Puanlama Sistemi:** 100 puan üzerinden 6 katmanlı analiz
  ```
  1. AST Structure:    20 puan (syntax, classes, functions, docstrings)
  2. Pylint Quality:   25 puan (kod kalitesi 0-10 skala)
  3. Complexity:       20 puan (cyclomatic complexity)
  4. Security:         15 puan (güvenlik açıkları)
  5. Style (PEP8):     10 puan (stil ihlalleri)
  6. Type Hints:       10 puan (annotation coverage)
  ────────────────────────────
  TOPLAM:             100 puan
  ```

- **Avantajları:**
  - ⚡ Çok hızlı (<1 saniye)
  - 💰 Tamamen ücretsiz (API key gerektirmez)
  - ✅ %100 objektif ve deterministik
  - 🔒 Detaylı güvenlik taraması
  - 📊 6 katmanlı analiz

- **Kullanım:**
  - `main.py` → `/analyze-advanced` endpoint'inde kullanılır
  - Detaylı kılavuz: [`ADVANCED_JUDGE_GUIDE.md`](./ADVANCED_JUDGE_GUIDE.md)

---

### **5. Frontend: `templates/index.html`**
- **Rol:** Kullanıcı arayüzü
- **Bağlantılar:**
  - `static/css/style.css` → Stil dosyası
  - `static/js/script.js` → JavaScript mantığı
  - PrismJS CDN → Kod syntax highlighting

- **Bileşenler:**
  - Prompt giriş alanı
  - **🚀 "Modelleri Çalıştır"** butonu (Mavi) → `generateCode()` fonksiyonu
  - **📊 "Kalite Analizi (LLM)"** butonu (Yeşil) → `analyzeResults()` fonksiyonu
  - **🔬 "Gelişmiş Analiz (Static Tools)"** butonu (Mor) → `analyzeAdvanced()` fonksiyonu **[YENİ!]**
  - 3 adet model kartı (Llama, DeepSeek, Gemini)
  - Kazanan gösterge paneli (Türkçe açıklama ile)

---

### **6. Frontend Stili: `static/css/style.css`**
- **Rol:** Havelsan mavi teması ile modern UI tasarımı
- **Özellikler:**
  - Gradient header
  - Card-based layout
  - Progress bar animasyonları
  - Responsive design (3 kolon → 1 kolon mobilde)
  - **YENİ:** `.btn-advanced` mor buton stili

---

### **7. Frontend Mantığı: `static/js/script.js`**
- **Rol:** API çağrıları ve UI güncellemeleri
- **Fonksiyonlar:**
  - `generateCode()`: `/generate-code` endpoint'ini çağırır, sonuçları gösterir
  - `analyzeResults()`: `/analyze-results` endpoint'ini çağırır, LLM hakem skorları ve **Türkçe reasoning** gösterir
  - `analyzeAdvanced()`: **YENİ!** `/analyze-advanced` endpoint'ini çağırır, detaylı static analysis sonuçlarını gösterir
  - `renderCode()`: Kod snippet'lerini DOM'a ekler
  - `renderScore()`: LLM hakem skorlarını çizer
  - `renderAdvancedScore()`: **YENİ!** 6 katmanlı static analysis skorlarını detaylı gösterir

- **State Yönetimi:**
  - `lastResults` değişkeninde son üretilen kodları tutar

---

## 🔄 Veri Akışı

### **Senaryo 1: Kod Üretme**
```
Kullanıcı Prompt Girer
    ↓
script.js → generateCode()
    ↓
POST /generate-code
    ↓
main.py → call_codellama(), call_deepseek(), call_gemini()
    ↓
llm_clients.py → API çağrıları yapar
    ↓
JSON Response {models: {CodeLlama: "...", DeepSeek-V3: "...", Gemini 2.5: "..."}}
    ↓
script.js → Kodları ekrana render eder (Prism ile syntax highlighting)
```

### **Senaryo 2a: LLM Tabanlı Analiz (Türkçe)**
```
Kullanıcı "📊 Kalite Analizi (LLM)" butonuna basar
    ↓
script.js → analyzeResults()
    ↓
POST /analyze-results {llama: "...", deepseek: "...", gemini: "..."}
    ↓
main.py → run_agent()
    ↓
agent_graph.py → LangGraph workflow çalışır
    ├─ generate_competitors (atlanır, zaten kodlar var)
    └─ judge_solutions (Llama 3'ü TÜRKÇE konuşan hakem olarak kullanır)
        ↓
    Llama 3 → 3 kodu TÜRKÇE değerlendirir, JSON döner
        {winner: "...", reasoning: "TÜRKÇE açıklama...", scores: {...}}
    ↓
script.js → Skorları ve TÜRKÇE kazanan açıklamasını ekrana gösterir
```

### **Senaryo 2b: Static Analysis Tabanlı Analiz (Objektif)**
```
Kullanıcı "🔬 Gelişmiş Analiz (Static Tools)" butonuna basar
    ↓
script.js → analyzeAdvanced()
    ↓
POST /analyze-advanced {llama: "...", deepseek: "...", gemini: "..."}
    ↓
main.py → advanced_judge()
    ↓
advanced_judge.py → 6 katmanlı statik analiz
    ├─ AST Structure (syntax, classes, functions, docstrings)
    ├─ Pylint Quality (kod kalitesi 0-10)
    ├─ Radon Complexity (cyclomatic complexity)
    ├─ Bandit Security (güvenlik açıkları)
    ├─ Flake8 Style (PEP8 ihlalleri)
    └─ Type Hints (annotation coverage)
        ↓
    JSON Response {winner: "...", reasoning: "...", scores: {breakdown: {...}}}
    ↓
script.js → 6 katmanlı detaylı skorları ekrana gösterir
```

---

## 🔑 Önemli Bağımlılıklar

### `requirements.txt` (Temel Bağımlılıklar)

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **groq**: Llama API client
- **langgraph**: AI agent orchestration
- **langchain-groq**, **langchain-google-genai**, **langchain-core**: LLM integrations
- **requests**: HTTP istekleri (DeepSeek, Gemini)
- **python-dotenv**: Environment variables

### Static Analysis Araçları (Zaten `requirements.txt`'e eklendi)

- **pylint≥3.0.0**: Comprehensive code quality checker
- **radon≥6.0.0**: Cyclomatic complexity analyzer
- **bandit≥1.7.0**: Security vulnerability scanner
- **flake8≥7.0.0**: PEP8 style checker
- **mypy≥1.8.0**: Static type checker (optional)

---

## 🆚 İki Hakem Sistemi Karşılaştırması

| Özellik | LLM Hakem | Static Analysis Hakem |
|---------|-----------|----------------------|
| **Endpoint** | `/analyze-results` | `/analyze-advanced` |
| **Dosya** | `agent_graph.py` | `advanced_judge.py` |
| **Hakem** | Llama 3.3 (70B) | Pylint + Radon + Bandit + Flake8 |
| **Dil** | 🇹🇷 Türkçe açıklama | 📊 Sayısal metrikler |
| **Hız** | 🐌 3-5 saniye | ⚡ <1 saniye |
| **Maliyet** | 💸 API maliyeti | 💰 Ücretsiz |
| **API Key** | ✅ Gerekli | ❌ Gereksiz |
| **Objektiflik** | ⚠️ Subjektif | ✅ %100 Objektif |
| **Bağlam** | ✅ Anlıyor | ❌ Anlamıyor |
| **Güvenlik** | ⚠️ Genel | ✅ Detaylı (Bandit) |
| **Metrik Sayısı** | 6 metrik | 6 katman, 20+ metrik |
| **Tutarlılık** | ⚠️ Değişken | ✅ Deterministik |

**Öneri:** Her ikisini birlikte kullan!
- Hızlı ön değerlendirme: `/analyze-advanced`
- Derinlemesine inceleme: `/analyze-results`

---

## 🚀 Kurulum ve Çalıştırma

### 1. **Bağımlılıkları yükleyin:**
```bash
cd agentic_form_generator
pip install -r requirements.txt
```

### 2. **API anahtarlarınızı `.env` dosyasına ekleyin:**
```env
GROQ_API_KEY=gsk_your_groq_key
DEEPSEEK_API_KEY=sk_your_deepseek_key  # OpenRouter için
GEMINI_API_KEY=AIza_your_gemini_key
```

### 3. **Uygulamayı çalıştırın:**
```bash
uvicorn main:app --reload
```

### 4. **Tarayıcıda açın:**
```
http://localhost:8000
```

---

## 🎯 Kullanım Senaryoları

### **Senaryo 1: Hızlı Objektif Analiz**
1. Prompt gir: "Fibonacci hesaplayan fonksiyon yaz"
2. **🚀 Modelleri Çalıştır**
3. **🔬 Gelişmiş Analiz (Static Tools)** ← Hızlı, ücretsiz, objektif
4. Detaylı 6 katmanlı sonuçları incele

### **Senaryo 2: Derinlemesine İnceleme**
1. Prompt gir: "REST API endpoint yaz"
2. **🚀 Modelleri Çalıştır**
3. **📊 Kalite Analizi (LLM)** ← Türkçe açıklama, bağlam anlıyor
4. Hakem görüşünü oku

### **Senaryo 3: İkisini Karşılaştır**
1. Kod üret
2. Önce **🔬 Static analiz** yap → Objektif skorları gör
3. Sonra **📊 LLM analiz** yap → Açıklamayı oku
4. İki sonucu karşılaştır

---

## 📝 Test

### **Otomatik Test:**
```bash
python test_advanced_judge.py
```

Bu test 3 farklı kalitede kod örneğini analiz eder ve detaylı sonuçları gösterir.

---

## 📚 Ek Dokümantasyon

- **Gelişmiş Hakem Kılavuzu:** [`ADVANCED_JUDGE_GUIDE.md`](./ADVANCED_JUDGE_GUIDE.md)
  - Kurulum adımları
  - Puanlama kriterleri detayları
  - Örnek kullanımlar
  - API endpoint açıklamaları
  - Sorun giderme

---

## 📊 Özet Bağlantı Şeması

```
main.py (API Sunucusu)
├── module/llm_clients.py (LLM API çağrıları)
│   ├── call_codellama() → Groq API (Llama 3.3 70B)
│   ├── call_deepseek() → OpenRouter API (DeepSeek V3)
│   └── call_gemini() → Google AI API (Gemini 2.0 Flash)
│
├── module/agent_graph.py (LangGraph workflow - LLM Hakem)
│   ├── generate_competitors (node)
│   │   └── llm_clients kullanır
│   └── judge_solutions (node)
│       └── Llama 3 Türkçe hakem olarak kullanır
│
├── module/advanced_judge.py [YENİ!] (Static Analysis Hakem)
│   ├── AST analizi
│   ├── Pylint (kod kalitesi)
│   ├── Radon (complexity)
│   ├── Bandit (güvenlik)
│   ├── Flake8 (PEP8)
│   └── Type Hints (annotation)
│
├── templates/index.html (Frontend)
│   ├── static/css/style.css (Stil + mor buton)
│   └── static/js/script.js (Mantık + analyzeAdvanced)
│       ├── /generate-code endpoint'ini çağırır
│       ├── /analyze-results endpoint'ini çağırır (LLM)
│       └── /analyze-advanced endpoint'ini çağırır (Static) [YENİ!]
│
└── module/code_quality.py (Kullanılmıyor - eski regex tabanlı analiz)
```

---

## 🎉 Yenilikler Özeti

✅ **Gelişmiş Static Analysis Hakem Sistemi** (6 araç, 100 puan)  
✅ **Türkçe Dil Desteği** (Hakem açıklamaları Türkçe)  
✅ **Üç Butonlu Arayüz** (Mavi-Yeşil-Mor)  
✅ **Detaylı Metrikler** (20+ farklı metrik)  
✅ **API-free Seçenek** (Static analysis ücretsiz)  
✅ **Hızlı Analiz** (<1 saniye)  
✅ **Objektif Değerlendirme** (Deterministik sonuçlar)  

---

## 📝 Lisans

Bu proje HAVELSAN için geliştirilmiştir.

