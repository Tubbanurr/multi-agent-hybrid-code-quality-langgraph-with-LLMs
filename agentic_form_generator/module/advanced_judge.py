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
    
    def __init__(self):
        self.weights = {
            "ast_structure": 20,
            "pylint_score": 25,
            "complexity": 20,
            "security": 15,
            "style": 10,
            "type_hints": 10
        }
    
    def clean_code(self, text: str) -> str:
        """Extract pure Python code from markdown or mixed content."""
        pattern = r"```(?:python)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return max(matches, key=len).strip()
        return text.strip()
    
    def analyze_ast(self, code: str) -> Dict[str, Any]:
        """
        AST-based structural analysis
        Returns: syntax validity, classes count, functions count, imports count
        """
        result = {
            "syntax_valid": False,
            "classes": 0,
            "functions": 0,
            "imports": 0,
            "docstrings": 0,
            "score": 0,
            "error": None
        }
        
        try:
            tree = ast.parse(code)
            result["syntax_valid"] = True
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    result["classes"] += 1
                    if ast.get_docstring(node):
                        result["docstrings"] += 1
                        
                elif isinstance(node, ast.FunctionDef):
                    result["functions"] += 1
                    if ast.get_docstring(node):
                        result["docstrings"] += 1
                        
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    result["imports"] += 1
            
            # Scoring logic
            score = 0
            if result["syntax_valid"]:
                score += 10
            
            # Reward OOP structure
            if result["classes"] >= 2:
                score += 5
            elif result["classes"] == 1:
                score += 3
            
            # Reward functions
            if result["functions"] >= 3:
                score += 3
            elif result["functions"] >= 1:
                score += 2
            
            # Reward documentation
            if result["docstrings"] >= 2:
                score += 2
            
            result["score"] = min(score, 20)  # Max 20 points
            
        except SyntaxError as e:
            result["error"] = f"Syntax Error: {e.msg} at line {e.lineno}"
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
            
            # Run pylint
            proc = subprocess.run(
                ['pylint', temp_file, '--output-format=json', '--score=yes'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse output
            if proc.stdout:
                try:
                    data = json.loads(proc.stdout)
                    result["issues"] = data if isinstance(data, list) else []
                except json.JSONDecodeError:
                    pass
            
            # Extract score from stderr (pylint puts score there)
            score_match = re.search(r'Your code has been rated at ([\d\.]+)/10', proc.stderr)
            if score_match:
                raw_score = float(score_match.group(1))
                result["raw_score"] = raw_score
                result["scaled_score"] = int((raw_score / 10) * 25)  # Scale to 25 points
            
            # Cleanup
            os.unlink(temp_file)
            
        except subprocess.TimeoutExpired:
            result["error"] = "Pylint timeout"
        except FileNotFoundError:
            result["error"] = "Pylint not installed"
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
            
            # Run radon cc (cyclomatic complexity)
            proc = subprocess.run(
                ['radon', 'cc', temp_file, '-j'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if proc.stdout:
                try:
                    data = json.loads(proc.stdout)
                    complexities = []
                    
                    for file_data in data.values():
                        for item in file_data:
                            complexities.append(item.get('complexity', 0))
                    
                    if complexities:
                        result["average_complexity"] = sum(complexities) / len(complexities)
                        result["max_complexity"] = max(complexities)
                    
                    # Scoring: lower complexity is better
                    avg = result["average_complexity"]
                    if avg <= 5:
                        result["score"] = 20
                    elif avg <= 10:
                        result["score"] = 15
                    elif avg <= 15:
                        result["score"] = 10
                    else:
                        result["score"] = 5
                        
                except json.JSONDecodeError:
                    pass
            
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
            
            # Run bandit
            proc = subprocess.run(
                ['bandit', temp_file, '-f', 'json'],
                capture_output=True,
                text=True,
                timeout=10
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
            
            # Run flake8
            proc = subprocess.run(
                ['flake8', temp_file, '--count'],
                capture_output=True,
                text=True,
                timeout=10
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
        (MyPy would be too complex for quick analysis)
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
                    
                    # Check if function has type hints
                    has_hints = (
                        node.returns is not None or
                        any(arg.annotation is not None for arg in node.args.args)
                    )
                    
                    if has_hints:
                        result["functions_with_hints"] += 1
            
            if result["total_functions"] > 0:
                result["coverage"] = result["functions_with_hints"] / result["total_functions"]
                result["score"] = int(result["coverage"] * 10)  # Max 10 points
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def score_code(self, raw_code: str) -> Dict[str, Any]:
        """
        Main scoring function that combines all analysis methods.
        """
        code = self.clean_code(raw_code)
        
        # Run all analyzers
        ast_result = self.analyze_ast(code)
        pylint_result = self.analyze_pylint(code)
        complexity_result = self.analyze_complexity(code)
        security_result = self.analyze_security(code)
        style_result = self.analyze_style(code)
        type_hints_result = self.analyze_type_hints(code)
        
        # Calculate total score
        total_score = (
            ast_result["score"] +
            pylint_result["scaled_score"] +
            complexity_result["score"] +
            security_result["score"] +
            style_result["score"] +
            type_hints_result["score"]
        )
        
        return {
            "total_score": total_score,
            "breakdown": {
                "ast_structure": ast_result,
                "pylint_quality": pylint_result,
                "complexity": complexity_result,
                "security": security_result,
                "style": style_result,
                "type_hints": type_hints_result
            },
            "max_score": 100
        }


def advanced_judge(code_llama: str, code_deepseek: str, code_gemini: str) -> Dict[str, Any]:
    """
    Compare three code snippets using advanced static analysis.
    """
    judge = AdvancedCodeJudge()
    
    results = {
        "CodeLlama": judge.score_code(code_llama),
        "DeepSeek-V3": judge.score_code(code_deepseek),
        "Gemini 2.5": judge.score_code(code_gemini)
    }
    
    # Find winner
    winner = max(results.keys(), key=lambda k: results[k]["total_score"])
    
    # Generate reasoning
    winner_score = results[winner]["total_score"]
    reasoning_parts = [f"{winner} kazandı ({winner_score}/100 puan) çünkü:"]
    
    breakdown = results[winner]["breakdown"]
    if breakdown["ast_structure"]["score"] >= 15:
        reasoning_parts.append("- Mükemmel kod yapısı ve syntax")
    if breakdown["pylint_quality"]["scaled_score"] >= 20:
        reasoning_parts.append("- Yüksek kod kalitesi (Pylint)")
    if breakdown["complexity"]["score"] >= 15:
        reasoning_parts.append("- Düşük karmaşıklık (maintainable)")
    if breakdown["security"]["score"] >= 12:
        reasoning_parts.append("- Güvenlik açığı yok")
    
    reasoning = " ".join(reasoning_parts)
    
    return {
        "winner": winner,
        "reasoning": reasoning,
        "scores": results
    }
