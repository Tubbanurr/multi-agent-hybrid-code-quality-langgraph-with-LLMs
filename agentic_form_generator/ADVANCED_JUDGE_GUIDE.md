# 🔬 Gelişmiş Hakem Sistemi - Kullanım Kılavuzu

## 📋 Genel Bakış

Bu sistem, **Regex + AST + Static Analysis araçları** kullanarak objektif kod kalitesi değerlendirmesi yapar.

---

## 🏗️ 6 Katmanlı Analiz Sistemi

```
┌──────────────────────────────────────────┐
│  1. AST Structure      → 20 puan        │
│  2. Pylint Quality     → 25 puan        │
│  3. Complexity (Radon) → 20 puan        │
│  4. Security (Bandit)  → 15 puan        │
│  5. Style (Flake8)     → 10 puan        │
│  6. Type Hints         → 10 puan        │
├──────────────────────────────────────────┤
│  TOPLAM:                 100 puan        │
└──────────────────────────────────────────┘
```

---

## 🚀 Kurulum

### 1. Bağımlılıkları Yükle

```bash
cd agentic_form_generator
pip install -r requirements.txt
```

### 2. Araçları Doğrula

```bash
pylint --version
radon --version
bandit --version
flake8 --version
```

---

## 💻 Kullanım Şekilleri

### Yöntem 1: Test Script ile

```bash
python test_advanced_judge.py
```

### Yöntem 2: API Endpoint ile

**LLM-based hakem (subjektif):**
```bash
curl -X POST http://localhost:8000/analyze-results \
  -H "Content-Type: application/json" \
  -d '{
    "llama": "def hello(): print(\"hi\")",
    "deepseek": "def greet(): return \"hello\"",
    "gemini": "print(\"test\")",
    "prompt": "Greeting function"
  }'
```

**Static Analysis hakem (objektif):**
```bash
curl -X POST http://localhost:8000/analyze-advanced \
  -H "Content-Type: application/json" \
  -d '{
    "llama": "def hello(): print(\"hi\")",
    "deepseek": "def greet(): return \"hello\"",
    "gemini": "print(\"test\")",
    "prompt": ""
  }'
```

### Yöntem 3: Python'dan Direct Import

```python
from module.advanced_judge import advanced_judge

code1 = """
def fibonacci(n: int) -> int:
    '''Calculate Fibonacci number'''
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

code2 = "def fib(x): return x if x<2 else fib(x-1)+fib(x-2)"
code3 = "f=lambda n:n if n<2 else f(n-1)+f(n-2)"

result = advanced_judge(code1, code2, code3)
print(f"Winner: {result['winner']}")
print(f"Score: {result['scores'][result['winner']]['total_score']}/100")
```

---

## 📊 Detaylı Puanlama

### 1️⃣ AST Structure (20 puan)

| Kriter | Puan |
|--------|------|
| Syntax valid | +10 |
| 2+ classes | +5 |
| 1 class | +3 |
| 3+ functions | +3 |
| 1-2 functions | +2 |
| 2+ docstrings | +2 |

**Örnek:**
```python
class Calculator:  # +3
    """Doc"""      # +1
    def add(self, x, y):  # +2
        """Add"""         # +1
        return x + y
    
# Toplam: 10 (syntax) + 3 (1 class) + 2 (1+ func) + 2 (2 doc) = 17/20
```

### 2️⃣ Pylint Quality (25 puan)

Pylint'in 0-10 skoru 25 puana çevrilir:
- 10/10 → 25 puan
- 8/10 → 20 puan
- 5/10 → 12.5 puan

**Kontrol edilen:**
- Code quality
- Naming conventions
- Unused variables
- Code duplication
- Refactoring opportunities

### 3️⃣ Complexity (20 puan)

Radon cyclomatic complexity:

| Avg Complexity | Puan | Kalite |
|----------------|------|--------|
| ≤ 5 | 20 | Simple |
| 6-10 | 15 | Moderate |
| 11-15 | 10 | Complex |
| > 15 | 5 | Very Complex |

**Örnek:**
```python
# Complexity = 1 (simple)
def add(x, y):
    return x + y

# Complexity = 3 (moderate)
def fibonacci(n):
    if n <= 1:      # +1
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Complexity = 8 (high)
def complex_func(x):
    if x > 10:      # +1
        for i in range(x):  # +2
            if i % 2 == 0:  # +3
                ...
```

### 4️⃣ Security (15 puan)

Bandit ile güvenlik taraması. 15'ten başla, sorun başına düş:

| Severity | Kesinti |
|----------|---------|
| HIGH | -5 puan |
| MEDIUM | -3 puan |
| LOW | -1 puan |

**Yaygın güvenlik sorunları:**
```python
# HIGH severity (-5)
password = "admin123"  # Hardcoded password
eval(user_input)       # Code injection risk

# MEDIUM severity (-3)
import subprocess
subprocess.call(user_input, shell=True)  # Shell injection

# LOW severity (-1)
import pickle
pickle.loads(data)  # Insecure deserialization
```

### 5️⃣ Style (PEP8) - 10 puan

Flake8 violations:

| Violations | Puan |
|-----------|------|
| 0 | 10 |
| 1-5 | 7 |
| 6-10 | 5 |
| 10+ | 2 |

**PEP8 kuralları:**
- Line length max 79 chars
- 2 blank lines between top-level functions
- Proper whitespace around operators
- Import organization

### 6️⃣ Type Hints (10 puan)

```
Score = (Annotated Functions / Total Functions) × 10
```

**Örnek:**
```python
# 10/10 puan - %100 coverage
def add(x: int, y: int) -> int:
    return x + y

def multiply(a: int, b: int) -> int:
    return a * b

# 5/10 puan - %50 coverage
def add(x: int, y: int) -> int:  # Annotated
    return x + y

def subtract(a, b):  # NOT annotated
    return a - b
```

---

## 📈 Response Format

```json
{
  "winner": "CodeLlama",
  "reasoning": "CodeLlama kazandı (85/100 puan) çünkü: - Mükemmel kod yapısı ve syntax - Yüksek kod kalitesi (Pylint) - Düşük karmaşıklık (maintainable) - Güvenlik açığı yok",
  "scores": {
    "CodeLlama": {
      "total_score": 85,
      "breakdown": {
        "ast_structure": {
          "score": 18,
          "syntax_valid": true,
          "classes": 1,
          "functions": 3,
          "docstrings": 3
        },
        "pylint_quality": {
          "scaled_score": 22,
          "raw_score": 8.8
        },
        "complexity": {
          "score": 18,
          "average_complexity": 4.2,
          "max_complexity": 7
        },
        "security": {
          "score": 15,
          "issues_count": 0
        },
        "style": {
          "score": 8,
          "violations": 3
        },
        "type_hints": {
          "score": 4,
          "coverage": 0.4
        }
      }
    },
    "DeepSeek-V3": {...},
    "Gemini 2.5": {...}
  }
}
```

---

## 🆚 Karşılaştırma

| Özellik | LLM Hakem | Static Analysis |
|---------|-----------|-----------------|
| Hız | 🐌 3-5 sn | ⚡ <1 sn |
| Maliyet | 💸 API | 💰 Ücretsiz |
| Objektiflik | ⚠️ Subjektif | ✅ Objektif |
| Tutarlılık | ⚠️ Değişken | ✅ Deterministik |
| Bağlam anlama | ✅ Mükemmel | ❌ Sınırlı |
| Güvenlik | ⚠️ Genel | ✅ Detaylı |

**Öneri:** Her ikisini birlikte kullan!
- Hızlı değerlendirme: `/analyze-advanced`
- Derinlemesine analiz: `/analyze-results`

---

## 🐛 Sorun Giderme

### Araç Kurulu Değil

```
Error: Pylint not installed
```

**Çözüm:**
```bash
pip install pylint radon bandit flake8
```

### Timeout Hataları

Büyük dosyalarda timeout artırın:

`module/advanced_judge.py` içinde `timeout=10` → `timeout=30`

---

## 🎯 Başarı Kriterleri

| Skor | Kalite Seviyesi |
|------|----------------|
| 90-100 | 🌟 Mükemmel |
| 75-89 | ✅ İyi |
| 60-74 | ⚠️ Orta |
| 40-59 | ❌ Zayıf |
| 0-39 | 🔴 Çok Kötü |

---

## 📝 Örnek Kullanım

```bash
# 1. Sunucuyu başlat
uvicorn main:app --reload

# 2. Kod üret
curl -X POST http://localhost:8000/generate-code \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Fibonacci calculator with memoization"}'

# 3. Gelişmiş analiz yap
curl -X POST http://localhost:8000/analyze-advanced \
  -H "Content-Type: application/json" \
  -d @response.json
```

---

Artık objektif ve güvenilir kod değerlendirmesi yapabilirsiniz! 🎉
