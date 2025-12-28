import ast
import re

class CodeQualityAnalyzer:

    def score(self, code: str) -> dict:
        score = {
            "syntax": 0,
            "cleanliness": 0,
            "oop": 0,
            "comments": 0,
            "exceptions": 0,
            "complexity": 0,
            "total": 0
        }

        # 1) Syntax Kontrolü
        try:
            ast.parse(code)
            score["syntax"] = 20
        except:
            score["syntax"] = 0

        # 2) Temizlik / okunabilirlik
        if len(code.split("\n")) < 300:  
            score["cleanliness"] = 15
        else:
            score["cleanliness"] = 8

        # 3) OOP Yapısı kontrol
        classes = len(re.findall(r"class\s+\w+", code))
        if classes >= 3: score["oop"] = 20
        elif classes == 2: score["oop"] = 15
        else: score["oop"] = 5

        # 4) Yorum satırı oranı
        comment_ratio = len(re.findall(r"#", code)) / (len(code.split("\n")) + 1)
        if comment_ratio > 0.10:
            score["comments"] = 10
        else:
            score["comments"] = 5

        # 5) Exception kullanımı
        if "raise" in code:
            score["exceptions"] = 15
        else:
            score["exceptions"] = 5

        # 6) Basit karmaşıklık ölçümü
        functions = len(re.findall(r"def\s+\w+", code))
        if functions >= 5:
            score["complexity"] = 20
        else:
            score["complexity"] = 10

        # Total
        score["total"] = (
            score["syntax"]
            + score["cleanliness"]
            + score["oop"]
            + score["comments"]
            + score["exceptions"]
            + score["complexity"]
        )

        return score


def compare_models(code_llama: str, deepseek: str, gemini: str):
    analyzer = CodeQualityAnalyzer()

    results = {
        "LLaMA3": analyzer.score(code_llama),
        "DeepSeek": analyzer.score(deepseek),
        "Gemini": analyzer.score(gemini)
    }

    # kazanan modeli bul
    winner = max(results, key=lambda k: results[k]["total"])

    return {
        "scores": results,
        "winner": winner
    }