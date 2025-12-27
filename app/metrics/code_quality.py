import ast
import re


class CodeQualityAnalyzer:
    """
    Basit ama genişletilebilir bir kod kalite analizcisi.
    Amaç: Farklı LLM'lerin ürettiği kodları karşılaştırmalı puanlamak.
    """

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

        # -------------------------------------------------
        # 1) Syntax kontrolü (AST parse)
        # -------------------------------------------------
        try:
            ast.parse(code)
            score["syntax"] = 20
        except Exception:
            score["syntax"] = 0

        # -------------------------------------------------
        # 2) Temizlik / okunabilirlik (satır sayısı)
        # -------------------------------------------------
        lines = code.split("\n")
        if len(lines) <= 300:
            score["cleanliness"] = 15
        else:
            score["cleanliness"] = 8

        # -------------------------------------------------
        # 3) OOP kullanımı (class sayısı)
        # -------------------------------------------------
        classes = len(re.findall(r"\bclass\s+\w+", code))
        if classes >= 3:
            score["oop"] = 20
        elif classes == 2:
            score["oop"] = 15
        else:
            score["oop"] = 5

        # -------------------------------------------------
        # 4) Yorum oranı
        # -------------------------------------------------
        comment_count = len(re.findall(r"#", code))
        comment_ratio = comment_count / (len(lines) + 1)

        if comment_ratio >= 0.10:
            score["comments"] = 10
        else:
            score["comments"] = 5

        # -------------------------------------------------
        # 5) Exception / hata yönetimi
        # -------------------------------------------------
        if "try" in code and "except" in code:
            score["exceptions"] = 15
        elif "raise" in code:
            score["exceptions"] = 10
        else:
            score["exceptions"] = 5

        # -------------------------------------------------
        # 6) Basit karmaşıklık (fonksiyon sayısı)
        # -------------------------------------------------
        functions = len(re.findall(r"\bdef\s+\w+", code))
        if functions >= 5:
            score["complexity"] = 20
        else:
            score["complexity"] = 10

        # -------------------------------------------------
        # TOTAL SCORE
        # -------------------------------------------------
        score["total"] = sum(score.values())

        return score


def compare_models(code_llama: str, code_deepseek: str, code_gemini: str) -> dict:
    """
    Üç farklı LLM çıktısını karşılaştırır ve kazananı döner.
    """

    analyzer = CodeQualityAnalyzer()

    results = {
        "LLaMA3": analyzer.score(code_llama),
        "DeepSeek": analyzer.score(code_deepseek),
        "Gemini": analyzer.score(code_gemini)
    }

    winner = max(results, key=lambda model: results[model]["total"])

    return {
        "scores": results,
        "winner": winner
    }