"""
Advanced Code Quality Judge using Multiple Static Analysis Tools
Combines: AST, Pylint, Radon, Bandit, Flake8, and Type Checking
"""

import ast
import re
import subprocess
import tempfile
import os
from typing import Dict, Any
import json


class AdvancedCodeJudge:
    """
    Multi-layered code quality analyzer using industry-standard tools.
    """
    
    def __init__(self, metric_weights: Dict[str, int] = None):
        # Default weights per 100-point 6-category system
        self.weights = {
            "cyclomatic_complexity": 15,
            "comment_density": 5,
            "identifier_clarity": 5,
            "code_smells": 15,
            "duplication": 5,
            "test_coverage": 10,
            "compile_success": 5,
            "static_lint": 10,
            "formatting": 5,
            "prompt_adherence": 10,
            "naming_alignment": 5,
            "error_handling": 10
        }
        
        # Override if provided
        if metric_weights:
            self.weights.update(metric_weights)

    def clean_code(self, text: str) -> str:
        """Extract pure Python code from markdown or mixed content."""
        pattern = r"```(?:python)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return max(matches, key=len).strip()
        return text.strip()
    
    def analyze_ast(self, code: str) -> Dict[str, Any]:
        """Check for syntax errors using AST."""
        result = {
            "syntax_valid": False,
            "score": 0, # Max 5 points in this system
            "error": None
        }
        
        if not code.strip():
            return result
            
        try:
            ast.parse(code)
            result["syntax_valid"] = True
            result["score"] = 5
        except SyntaxError as e:
            result["error"] = f"Syntax Error at line {e.lineno}: {e.msg}"
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    def analyze_pylint(self, code: str) -> Dict[str, Any]:
        """
        Run Pylint for comprehensive code quality check.
        Returns score out of 10, scaled to 25 points.
        """
        result = {
            "raw_score": 0.0,
            "scaled_score": 0,
            "issues": [],
            "error": None
        }
        
        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run pylint - we need the text output to get the 'rated at' line easily
            proc = subprocess.run(
                ['python3', '-m', 'pylint', temp_file, '--score=yes'],
                capture_output=True,
                text=True,
                timeout=15,
                env={**os.environ, "PAGER": "cat"}
            )
            
            # Combined stdout and stderr to find the score
            full_output = proc.stdout + proc.stderr
            score_match = re.search(r'Your code has been rated at ([\d\.]+)/10', full_output)
            if score_match:
                raw_score = float(score_match.group(1))
                result["raw_score"] = raw_score
                result["scaled_score"] = int((raw_score / 10) * 25)
            else:
                # If pylint fails to give a score because code is too short or weird,
                # give a neutral baseline (7.0/10) if no major errors exist
                if not proc.stderr or "error" not in proc.stderr.lower():
                    result["raw_score"] = 7.0
                    result["scaled_score"] = 17
            
            # Cleanup
            os.unlink(temp_file)
            
        except subprocess.TimeoutExpired:
            result["error"] = "Pylint timeout"
        except FileNotFoundError:
            result["error"] = "Pylint not installed"
            result["raw_score"] = 10.0 # Default to max score if tool is missing to avoid penalizing environment issues
            result["scaled_score"] = 25
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def analyze_complexity(self, code: str) -> Dict[str, Any]:
        """
        Use Radon to calculate cyclomatic complexity.
        Lower complexity = better score.
        """
        result = {
            "average_complexity": 0,
            "max_complexity": 0,
            "score": 0,
            "error": None
        }
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run radon cc (cyclomatic complexity) with python -m
            proc = subprocess.run(
                ['python3', '-m', 'radon', 'cc', temp_file, '-j'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if proc.stdout:
                try:
                    data = json.loads(proc.stdout)
                    complexities = []
                    
                    for key, file_data in data.items():
                        items = file_data if isinstance(file_data, list) else [file_data]
                        for item in items:
                            if isinstance(item, dict):
                                complexities.append(item.get('complexity', 0))
                    
                    if complexities:
                        result["average_complexity"] = sum(complexities) / len(complexities)
                        result["max_complexity"] = max(complexities)
                except json.JSONDecodeError:
                    pass
            
            # Scoring logic - Max 15 points
            avg = result["average_complexity"]
            if avg == 0: 
                result["score"] = 15
            elif avg <= 5:
                result["score"] = 15
            elif avg <= 10:
                result["score"] = 12
            elif avg <= 15:
                result["score"] = 8
            else:
                result["score"] = 5
            
            os.unlink(temp_file)
            
        except subprocess.TimeoutExpired:
            result["error"] = "Radon timeout"
        except FileNotFoundError:
            result["error"] = "Radon not installed"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def analyze_security(self, code: str) -> Dict[str, Any]:
        """
        Use Bandit to detect security issues.
        """
        result = {
            "issues_count": 0,
            "severity_high": 0,
            "severity_medium": 0,
            "severity_low": 0,
            "score": 15,  # Start with full points, deduct for issues
            "error": None
        }
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run bandit with python -m
            proc = subprocess.run(
                ['python3', '-m', 'bandit', temp_file, '-f', 'json'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if proc.stdout:
                try:
                    data = json.loads(proc.stdout)
                    results = data.get('results', [])
                    result["issues_count"] = len(results)
                    
                    for issue in results:
                        severity = issue.get('issue_severity', 'LOW')
                        if severity == 'HIGH':
                            result["severity_high"] += 1
                            result["score"] -= 5
                        elif severity == 'MEDIUM':
                            result["severity_medium"] += 1
                            result["score"] -= 3
                        else:
                            result["severity_low"] += 1
                            result["score"] -= 1
                    
                    result["score"] = max(0, result["score"])  # Don't go negative
                    
                except json.JSONDecodeError:
                    pass
            
            os.unlink(temp_file)
            
        except subprocess.TimeoutExpired:
            result["error"] = "Bandit timeout"
        except FileNotFoundError:
            result["error"] = "Bandit not installed"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def analyze_style(self, code: str) -> Dict[str, Any]:
        """
        Use Flake8 for PEP8 compliance.
        """
        result = {
            "violations": 0,
            "score": 10,
            "error": None
        }
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run flake8 with python -m
            proc = subprocess.run(
                ['python3', '-m', 'flake8', temp_file, '--count'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # Count violations from output
            if proc.stdout:
                lines = proc.stdout.strip().split('\n')
                # Last line usually contains count
                if lines[-1].isdigit():
                    result["violations"] = int(lines[-1])
                    
                    # Deduct points for violations
                    if result["violations"] == 0:
                        result["score"] = 10
                    elif result["violations"] <= 5:
                        result["score"] = 7
                    elif result["violations"] <= 10:
                        result["score"] = 5
                    else:
                        result["score"] = 2
            
            os.unlink(temp_file)
            
        except subprocess.TimeoutExpired:
            result["error"] = "Flake8 timeout"
        except FileNotFoundError:
            result["error"] = "Flake8 not installed"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def analyze_type_hints(self, code: str) -> Dict[str, Any]:
        """
        Check for type hints using simple AST analysis.
        """
        result = {
            "functions_with_hints": 0,
            "total_functions": 0,
            "coverage": 0.0,
            "score": 0,
            "error": None
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    result["total_functions"] += 1
                    
                    has_hints = (
                        node.returns is not None or
                        any(arg.annotation is not None for arg in node.args.args)
                    )
                    
                    if has_hints:
                        result["functions_with_hints"] += 1
            
            if result["total_functions"] > 0:
                result["coverage"] = result["functions_with_hints"] / result["total_functions"]
                result["score"] = int(result["coverage"] * 5)  # Scale to 5 points (part of Maintainability)
            
        except Exception as e:
            result["error"] = str(e)
        
        return result

    def analyze_comments(self, code: str) -> Dict[str, Any]:
        """Calculate comment density: (comment_lines / total_lines)."""
        result = {"density": 0.0, "score": 0, "total_lines": 0, "comment_lines": 0}
        lines = code.splitlines()
        result["total_lines"] = len(lines)
        if result["total_lines"] == 0: return result

        comment_lines = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#') or (stripped.startswith('"""') or stripped.startswith("'''")):
                comment_lines += 1
        
        result["comment_lines"] = comment_lines
        result["density"] = comment_lines / result["total_lines"]
        
        # Scoring: Ideal density 10-30%
        # More lenient: for very short files (< 10 lines), don't penalize missing comments 
        if result["total_lines"] < 10 and result["comment_lines"] == 0:
            result["score"] = 5 # Give full points to short scripts without noise
        elif 0.05 <= result["density"] <= 0.4: # Lowened threshold to 5%
            result["score"] = 5
        elif result["density"] > 0:
            result["score"] = 3
        else:
            result["score"] = 0
        return result

    def analyze_formatting(self, code: str) -> Dict[str, Any]:
        """Checks for consistent indentation and spacing."""
        result = {"score": 5, "issues": []}
        lines = code.splitlines()
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith((' ', '\t', '#')):
                # Check for mixing tabs and spaces
                if '\t' in line and ' ' in line[:line.find(line.strip())]:
                    result["score"] = max(0, result["score"] - 1)
        return result

    def analyze_error_handling(self, code: str) -> int:
        """Check for try-except, assert, and Optional patterns."""
        score = 0
        try:
            tree = ast.parse(code)
            has_try = False
            has_assert = False
            for node in ast.walk(tree):
                if isinstance(node, ast.Try):
                    has_try = True
                if isinstance(node, ast.Assert):
                    has_assert = True
            
            if has_try: score += 6
            if has_assert: score += 4
        except:
            pass
        return min(score, 10)
    
    def analyze_duplications(self, code: str) -> Dict[str, Any]:
        """
        Detect code duplications (repeated lines/blocks).
        """
        result = {
            "total_lines": 0,
            "unique_lines": 0,
            "duplicate_lines": 0,
            "duplication_ratio": 0.0,
            "score": 5,
            "error": None
        }
        
        try:
            lines = code.strip().split('\n')
            code_lines = [
                line.strip() for line in lines 
                if line.strip() and not line.strip().startswith('#')
            ]
            
            result["total_lines"] = len(code_lines)
            if result["total_lines"] == 0:
                return result
            
            unique = set(code_lines)
            result["unique_lines"] = len(unique)
            result["duplicate_lines"] = result["total_lines"] - result["unique_lines"]
            result["duplication_ratio"] = result["duplicate_lines"] / result["total_lines"]
            
            if result["duplication_ratio"] == 0:
                result["score"] = 5
            elif result["duplication_ratio"] < 0.1:
                result["score"] = 4
            elif result["duplication_ratio"] < 0.2:
                result["score"] = 3
            elif result["duplication_ratio"] < 0.3:
                result["score"] = 2
            else:
                result["score"] = 1
            
        except Exception as e:
            result["error"] = str(e)
        
        return result

    def score_code(self, raw_code: str) -> Dict[str, Any]:
        """
        Main scoring function that combines all analysis methods.
        Categorized as per the 6-category requirement.
        """
        code = self.clean_code(raw_code)
        
        # Substantial check: Detect garbage/one-word hallucinations or explanatory paragraphs
        substance = False
        clean_stripped = code.strip()
        
        # A valid script MUST have at least one of these major structural markers
        # to be considered "code" rather than just a paragraph of text.
        major_markers = ["def ", "import ", " = ", "class ", "print("]
        has_major = any(m in clean_stripped for m in major_markers)
        
        # If the output is longer than 40 chars and has NO major markers, it's likely a paragraph/hallucination.
        if len(clean_stripped) > 40:
            if has_major:
                substance = True
            else:
                substance = False
        # For very short strings, we look for any major marker or at least a minimal structure
        elif len(clean_stripped) > 5 and has_major:
            substance = True
        elif len(clean_stripped) > 0 and has_major: # e.g. "a = 1"
            substance = True
        
        # 1. Kod Kalitesi (0-25)
        complexity_res = self.analyze_complexity(code)
        # If complexity is literally 0 AND it's not a substantial script, it's suspect
        if complexity_res["average_complexity"] == 0 and not substance:
            complexity_res["score"] = 0
        comment_res = self.analyze_comments(code)
        
        # 2. Teknik Borç (0-20)
        pylint_res = self.analyze_pylint(code)
        duplication_res = self.analyze_duplications(code)
        
        # 3. Test & Build (0-15)
        ast_res = self.analyze_ast(code)
        
        # 4. Stil & Standart (0-15)
        style_res = self.analyze_style(code)
        format_res = self.analyze_formatting(code)
        
        # 6. Güvenlik & Hata Yönetimi (0-10)
        error_res = self.analyze_error_handling(code)
        
        if not substance:
            # Penalize everything drastically for garbage content
            complexity_res["score"] = 0
            comment_res["score"] = 0
            pylint_res["scaled_score"] = 0
            pylint_res["raw_score"] = 0
            duplication_res["score"] = 0
            style_res["score"] = 0
            format_res["score"] = 0
            error_res = 0
            # Ensure syntax also fails
            ast_res["syntax_valid"] = False
        
        # Static Total - Precise sum based on weights:
        # 15(Complexity)+5(Comments)+15(Pylint)+5(Duplication)+5(Syntax)+10(Style)+5(Format)+10(Error) = 70 total
        static_raw = (
            complexity_res["score"] +    # 15
            comment_res["score"] +       # 5
            pylint_res["scaled_score"] + # 15
            duplication_res["score"] +    # 5
            ast_res["score"] +            # 5
            style_res["score"] +         # 10
            format_res["score"] +        # 5
            error_res                    # 10
        )
        
        return {
            "static_total": static_raw,
            "breakdown": {
                "complexity": complexity_res,
                "comments": comment_res,
                "pylint": pylint_res,
                "duplication": duplication_res,
                "syntax": ast_res,
                "style": style_res,
                "format": format_res,
                "error_handling": error_res,
                "security": self.analyze_security(code),
                "type_hints": self.analyze_type_hints(code)
            }
        }

    def get_hybrid_score(self, static_data: Dict[str, Any], llm_eval: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combines static and LLM results into the exact 6-category 100-point scale.
        """
        # 1. Kod Kalitesi (25 pts)
        cat1 = (
            min(15, static_data["breakdown"]["complexity"]["score"]) + 
            static_data["breakdown"]["comments"]["score"] + 
            llm_eval["breakdown"].get("identifier_clarity", 0)
        )
        
        # 2. Teknik Borç (20 pts)
        cat2 = (
            min(15, int(static_data["breakdown"]["pylint"]["raw_score"] * 1.5)) + 
            min(5, static_data["breakdown"]["duplication"]["score"] / 2)
        )
        
        # 3. Test & Build (15 pts)
        cat3 = (5 if static_data["breakdown"]["syntax"]["syntax_valid"] else 0)
        cat3 += llm_eval["breakdown"].get("test_reliability", 8)
        
        # 4. Stil & Standart (15 pts)
        cat4 = min(10, static_data["breakdown"]["style"]["score"]) + static_data["breakdown"]["format"]["score"]
        
        # 5. Semantic Alignment (15 pts)
        cat5 = llm_eval["breakdown"].get("prompt_adherence", 0) + llm_eval["breakdown"].get("naming_alignment", 0)
        
        # 6. Robustness & Safety (10 pts)
        cat6 = static_data["breakdown"]["error_handling"]
        
        total_score = cat1 + cat2 + cat3 + cat4 + cat5 + cat6
        
        return {
            "total_score": int(total_score),
            "static_total": static_data["static_total"],
            "llm_total": llm_eval["semantic_score"],
            "categories": {
                "1_Kod_Kalitesi": cat1,
                "2_Teknik_Borc": cat2,
                "3_Test_Build": cat3,
                "4_Stil_Standart": cat4,
                "5_Semantic_Alignment": cat5,
                "6_Robustness_Safety": cat6
            },
            "static_analysis": static_data,
            "llm_evaluation": llm_eval,
            "reasoning": llm_eval.get("reasoning", ""),
            "chain_of_thought": llm_eval.get("chain_of_thought", "")
        }

def advanced_judge(code_1: str, code_2: str, code_3: str, prompt: str) -> Dict[str, Any]:
    """
    Compare three code snippets using the new 100-point metric set.
    """
    judge = AdvancedCodeJudge()
    from module.llm_judge import LLMJudge
    llm_judge = LLMJudge()
    
    from module.llm_clients import get_model_names
    model_names = get_model_names()
    
    all_results = {}
    for i, code in enumerate([code_1, code_2, code_3], 1):
        name = model_names.get(f"model_{i}", f"Model {i}")
        static = judge.score_code(code)
        llm_eval = llm_judge.evaluate_code(code, prompt)
        all_results[name] = judge.get_hybrid_score(static, llm_eval)
    
    winner = max(all_results.keys(), key=lambda k: all_results[k]["total_score"])
    
    return {
        "winner": winner,
        "results": all_results,
        "reasoning": all_results[winner]["reasoning"]
    }
