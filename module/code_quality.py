import ast
import re

def clean_code(text: str) -> str:
    """
    Extracts pure Python code from a potential Markdown string.
    Finds content between ```python ... ``` or just ``` ... ```.
    """
    # Pattern to find code blocks
    pattern = r"```(?:python)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        # Return the longest (most likely main) code block
        return max(matches, key=len).strip()
    
    # If no markdown blocks, usually the whole text is code (or just text)
    # But some models might return "Here is code:\n<code>"
    # For now, we assume if no backticks, treat whole as code if it looks like it?
    # Or just return raw and let ast try to parse.
    return text.strip()

class CodeQualityAnalyzer:

    def score(self, raw_text: str) -> dict:
        code = clean_code(raw_text)
        
        score = {
            "syntax": 0,
            "cleanliness": 0,
            "oop": 0,
            "comments": 0,
            "exceptions": 0,
            "complexity": 0,
            "total": 0,
            "error_msg": None # To feedback why syntax failed
        }

        # 1) Syntax Kontrolü
        try:
            ast.parse(code)
            score["syntax"] = 20
        except SyntaxError as e:
            score["syntax"] = 0
            score["error_msg"] = f"Syntax Error: {e.msg} line {e.lineno}"
        except Exception:
            score["syntax"] = 0

        # If syntax is dead, usually code value is low, but we check other strings
        
        lines = code.split("\n")
        
        # 2) Temizlik / okunabilirlik (Length check logical?)
        # Too short might be trival, too long might be messy.
        if 5 < len(lines) < 300:  
            score["cleanliness"] = 15
        else:
            score["cleanliness"] = 5

        # 3) OOP Yapısı kontrol
        classes = len(re.findall(r"class\s+\w+", code))
        if classes >= 2: score["oop"] = 20
        elif classes == 1: score["oop"] = 15
        else: score["oop"] = 5

        # 4) Yorum satırı oranı
        # Count actual code lines vs comments
        comment_lines = len(re.findall(r"^\s*#", code, re.MULTILINE))
        total_lines = len(lines)
        if total_lines > 0:
            ratio = comment_lines / total_lines
            if ratio > 0.05: score["comments"] = 10
            elif ratio > 0: score["comments"] = 5
            else: score["comments"] = 0

        # 5) Exception kullanımı
        if "try:" in code and "except" in code:
            score["exceptions"] = 15
        else:
            score["exceptions"] = 5

        # 6) Basit karmaşıklık ölçümü (Functions)
        functions = len(re.findall(r"def\s+\w+", code))
        if functions >= 3:
            score["complexity"] = 20
        elif functions >= 1:
            score["complexity"] = 15
        else:
            score["complexity"] = 5

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