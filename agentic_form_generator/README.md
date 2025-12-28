# Havelsan-SUIT-AP

## 📋 Proje Özeti

Bu proje, **LLM (Large Language Model) tabanlı bir kod üretici ve değerlendirme platformu**dur. Kullanıcıdan bir prompt alır, üç farklı AI modeli (CodeLlama, DeepSeek-V3, Gemini) ile kod üretir ve bu kodları kalite açısından karşılaştırarak en iyisini seçer.

## 🏗️ Proje Mimarisi

### **Ana Bileşenler:**

1. **Backend (FastAPI)** - API sunucusu
2. **Frontend (HTML/CSS/JS)** - Kullanıcı arayüzü
3. **LLM Modülleri** - Kod üretme ve değerlendirme mantığı

---

## 📂 Dosya Yapısı ve Bağlantılar

### **1. Ana Giriş Noktası: `main.py`**
- **Rol:** FastAPI web sunucusu
- **Bağlantılar:**
  - `module/llm_clients.py` → `call_codellama()`, `call_deepseek()`, `call_gemini()` fonksiyonlarını import eder
  - `module/agent_graph.py` → `run_agent()` fonksiyonunu import eder
  - `templates/index.html` → Root endpoint'te HTML dosyasını serve eder
  - `static/` klasörü → CSS ve JS dosyalarını static olarak sunar

- **API Endpoints:**
  - `GET /` → Frontend'i gösterir
  - `POST /generate-code` → 3 modelden kod üretir
  - `POST /analyze-results` → Üretilen kodları analiz eder (LangGraph agenti kullanarak)

---

### **2. LLM İstemci Modülü: `module/llm_clients.py`**
- **Rol:** Farklı LLM API'larına istek gönderir
- **Fonksiyonlar:**
  - `call_codellama()` → Groq API üzerinden Llama 3 modelini çağırır
  - `call_deepseek()` → OpenRouter API üzerinden DeepSeek modelini çağırır
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
  2. **`judge_solutions`**: Llama 3 modelini hakem olarak kullanıp kodları değerlendirir

- **State (AgentState):**
  ```python
  {
    "prompt": str,           # Kullanıcı isteği
    "code_llama": str,       # Llama'nın ürettiği kod
    "code_deepseek": str,    # DeepSeek'in ürettiği kod
    "code_gemini": str,      # Gemini'nin ürettiği kod
    "judge_result": dict     # Hakem sonucu (winner, reasoning, scores)
  }
  ```

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
  - `main.py`'de yorum satırına alınmış (`# from module.code_quality import compare_models`)
  - Şu an yerine `agent_graph.py`'deki LLM-based hakem sistemi kullanılıyor

---

### **5. Frontend: `templates/index.html`**
- **Rol:** Kullanıcı arayüzü
- **Bağlantılar:**
  - `static/css/style.css` → Stil dosyası
  - `static/js/script.js` → JavaScript mantığı
  - PrismJS CDN → Kod syntax highlighting

- **Bileşenler:**
  - Prompt giriş alanı
  - "Modelleri Çalıştır" butonu → `generateCode()` fonksiyonu
  - "Kalite Analizi Yap" butonu → `analyzeResults()` fonksiyonu
  - 3 adet model kartı (Llama, DeepSeek, Gemini)

---

### **6. Frontend Stili: `static/css/style.css`**
- **Rol:** Havelsan mavi teması ile modern UI tasarımı
- **Özellikler:**
  - Gradient header
  - Card-based layout
  - Progress bar animasyonları
  - Responsive design (3 kolon → 1 kolon mobilde)

---

### **7. Frontend Mantığı: `static/js/script.js`**
- **Rol:** API çağrıları ve UI güncellemeleri
- **Fonksiyonlar:**
  - `generateCode()`: `/generate-code` endpoint'ini çağırır, sonuçları gösterir
  - `analyzeResults()`: `/analyze-results` endpoint'ini çağırır, skorları ve kazananı gösterir
  - `renderCode()`: Kod snippet'lerini DOM'a ekler
  - `renderScore()`: Skor çubuklarını çizer

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

### **Senaryo 2: Analiz**
```
Kullanıcı "Kalite Analizi Yap" butonuna basar
    ↓
script.js → analyzeResults()
    ↓
POST /analyze-results {llama: "...", deepseek: "...", gemini: "..."}
    ↓
main.py → run_agent()
    ↓
agent_graph.py → LangGraph workflow çalışır
    ├─ generate_competitors (atlanır, zaten kodlar var)
    └─ judge_solutions (Llama 3'ü hakem olarak kullanır)
        ↓
    Llama 3 → 3 kodu değerlendirir, JSON döner
        {winner: "...", reasoning: "...", scores: {...}}
    ↓
script.js → Skorları ve kazananı ekrana gösterir
```

---

## 🔑 Önemli Bağımlılıklar (`requirements.txt`)

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **groq**: Llama API client
- **langgraph**: AI agent orchestration
- **langchain-groq**, **langchain-google-genai**, **langchain-core**: LLM integrations
- **requests**: HTTP istekleri (DeepSeek, Gemini)
- **python-dotenv**: Environment variables

---

## 📊 Özet Bağlantı Şeması

```
main.py (API Sunucusu)
├── module/llm_clients.py (LLM API çağrıları)
│   ├── call_codellama() → Groq API
│   ├── call_deepseek() → OpenRouter API
│   └── call_gemini() → Google AI API
│
├── module/agent_graph.py (LangGraph workflow)
│   ├── generate_competitors (node)
│   │   └── llm_clients.call_deepseek() kullanır
│   └── judge_solutions (node)
│       └── Llama 3 (Groq) hakem olarak kullanır
│
├── templates/index.html (Frontend)
│   ├── static/css/style.css (Stil)
│   └── static/js/script.js (Mantık)
│       ├── /generate-code endpoint'ini çağırır
│       └── /analyze-results endpoint'ini çağırır
│
└── module/code_quality.py (Kullanılmıyor - eski regex tabanlı analiz)
```

---

## 🚀 Kurulum ve Çalıştırma

1. **Bağımlılıkları yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

2. **API anahtarlarınızı `.env` dosyasına ekleyin:**
   ```
   GROQ_API_KEY=your_groq_key
   DEEPSEEK_API_KEY=your_deepseek_key
   GEMINI_API_KEY=your_gemini_key
   ```

3. **Uygulamayı çalıştırın:**
   ```bash
   uvicorn main:app --reload
   ```

4. **Tarayıcıda açın:**
   ```
   http://localhost:8000
   ```

---

## 📝 Lisans

Bu proje HAVELSAN için geliştirilmiştir.
