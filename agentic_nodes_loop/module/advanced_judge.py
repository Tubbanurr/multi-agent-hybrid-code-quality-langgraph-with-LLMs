"""
Advanced Code Quality Judge using Multiple Static Analysis Tools
Combines: AST, Pylint, Radon, Bandit, Flake8, and Type Checking
"""

import ast
import re
import subprocess
import sys
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
        Returns score out of 10, scaled to 15 points.
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
                [sys.executable, '-m', 'pylint', temp_file, '--score=yes', '--disable=missing-docstring,missing-module-docstring,missing-function-docstring,invalid-name'],
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
                result["scaled_score"] = int((raw_score / 10) * 15)
            else:
                # If pylint fails to give a score because code is too short or weird,
                # give a neutral baseline (7.0/10) if no major errors exist
                if not proc.stderr or "error" not in proc.stderr.lower():
                    result["raw_score"] = 7.0
                    result["scaled_score"] = 10
            
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
        avg==0 artık ayırt ediliyor: radon fail mı, yoksa gerçekten basit mi?
        """
        result = {
            "average_complexity": 0,
            "max_complexity": 0,
            "score": 0,
            "error": None
        }
        
        # AST ile fonksiyon sayısını önceden belirle
        try:
            tree = ast.parse(code)
            fn_count = sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
        except SyntaxError:
            fn_count = 0
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            proc = subprocess.run(
                [sys.executable, '-m', 'radon', 'cc', temp_file, '-j'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            radon_found = False
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
                        radon_found = True
                except json.JSONDecodeError:
                    pass
            
            os.unlink(temp_file)
            
            avg = result["average_complexity"]
            
            if avg == 0:
                if not radon_found and fn_count > 0:
                    # Radon parse edemedi ama fonksiyon var → AST ile basit CC tahmini
                    # (if/for/while/and/or sayısı + 1 per function)
                    branches = sum(
                        1 for n in ast.walk(tree)
                        if isinstance(n, (ast.If, ast.For, ast.While,
                                         ast.ExceptHandler, ast.BoolOp))
                    )
                    estimated_avg = (branches / fn_count) + 1
                    result["average_complexity"] = round(estimated_avg, 1)
                    result["error"] = "Radon fallback: AST tahmini kullanıldı"
                    avg = estimated_avg
                elif fn_count == 0:
                    # Script tipi kod — fonksiyon yok, orta puan
                    result["score"] = 10
                    return result
                # else: radon found, CC gerçekten 0 (CC=1 basit fonksiyon) → 15

            # Puanlama
            if avg <= 5:
                result["score"] = 15
            elif avg <= 10:
                result["score"] = 12
            elif avg <= 15:
                result["score"] = 8
            else:
                result["score"] = 5
            
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
                [sys.executable, '-m', 'bandit', temp_file, '-f', 'json'],
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
        Score = (1 - violations / max_violations) * 10  [ister formülü]
        """
        MAX_VIOLATIONS = 20  # violations >= this → score = 0
        result = {
            "violations": 0,
            "score": 10,
            "error": None
        }
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            proc = subprocess.run(
                [sys.executable, '-m', 'flake8', temp_file, '--count'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if proc.stdout:
                lines = proc.stdout.strip().split('\n')
                if lines[-1].isdigit():
                    violations = int(lines[-1])
                    result["violations"] = violations
                    # İster formülü: 1 - violations/max_violations
                    ratio = min(violations / MAX_VIOLATIONS, 1.0)
                    result["score"] = round((1 - ratio) * 10)
            
            os.unlink(temp_file)
            
        except subprocess.TimeoutExpired:
            result["error"] = "Flake8 timeout"
        except FileNotFoundError:
            result["error"] = "Flake8 not installed"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def analyze_test_coverage(self, code: str) -> Dict[str, Any]:
        """
        Test Coverage: kodu geçici dosyaya yazıp coverage.py ile çalıştırır.
        Score = (coverage_percent / 100) * 10  [ister formülü]
        """
        result = {"coverage": 0.0, "score": 0, "error": None}
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            result["error"] = f"Syntax error: {e}"
            return result
        
        # Fonksiyon tanımlarını bul
        functions = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_')
        ]
        
        try:
            import sys
            import shutil
            tmp_dir = tempfile.mkdtemp()
            src_file = os.path.join(tmp_dir, 'src.py')
            test_file = os.path.join(tmp_dir, 'test_src.py')
            
            with open(src_file, 'w') as f:
                f.write(code)
            
            test_lines = [
                "import sys, os",
                f"sys.path.insert(0, r'{tmp_dir}')",
                "from src import *",
                ""
            ]
            for fn in functions:
                n_args = len(fn.args.args)
                args = ', '.join(['0'] * n_args)
                test_lines.append(f"def test_{fn.name}():")
                test_lines.append(f"    try: {fn.name}({args})")
                test_lines.append(f"    except: pass")
                test_lines.append("")
            
            if not functions:
                test_lines.append("def test_script():")
                test_lines.append("    pass")
            
            with open(test_file, 'w') as f:
                f.write('\n'.join(test_lines))
            
            # sys.executable kullan, --cov=src modül adıyla çağır
            proc = subprocess.run(
                [sys.executable, '-m', 'pytest', test_file,
                 '--cov=src', '--cov-report=term-missing', '-q', '--tb=no'],
                capture_output=True, text=True, timeout=30, cwd=tmp_dir
            )
            
            output = proc.stdout + proc.stderr
            # Önce "src.py   20   4   80%" satırını ara
            cov_match = re.search(r'src\.py\s+\d+\s+\d+\s+(\d+)%', output)
            if not cov_match:
                cov_match = re.search(r'\b(\d{1,3})%', output)
            
            if cov_match:
                pct = int(cov_match.group(1))
                result["coverage"] = pct / 100.0
                result["score"] = round(result["coverage"] * 10)
            
            shutil.rmtree(tmp_dir, ignore_errors=True)
            
        except subprocess.TimeoutExpired:
            result["error"] = "Coverage timeout"
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
        
        # Exclude completely empty lines from total lines to avoid skewed density
        valid_lines = [line for line in lines if line.strip()]
        result["total_lines"] = len(valid_lines)
        if result["total_lines"] == 0: return result

        comment_lines = 0
        in_multiline_string = False
        multiline_char = ""
        
        for line in valid_lines:
            stripped = line.strip()
            
            # Fast track single line comments
            if not in_multiline_string and stripped.startswith('#'):
                comment_lines += 1
                continue
                
            # Handle multiline strings (docstrings)
            quotes_3_double = stripped.count('"""')
            quotes_3_single = stripped.count("'''")
            
            if in_multiline_string:
                comment_lines += 1
                # Check if it ends on this line
                if (multiline_char == '"""' and quotes_3_double > 0) or \
                   (multiline_char == "'''" and quotes_3_single > 0):
                    in_multiline_string = False
            else:
                if quotes_3_double > 0 and quotes_3_double % 2 != 0:
                    in_multiline_string = True
                    multiline_char = '"""'
                    comment_lines += 1
                elif quotes_3_single > 0 and quotes_3_single % 2 != 0:
                    in_multiline_string = True
                    multiline_char = "'''"
                    comment_lines += 1
                elif (quotes_3_double > 0 and quotes_3_double % 2 == 0) or \
                     (quotes_3_single > 0 and quotes_3_single % 2 == 0):
                    # Single-line docstring like """Hello"""
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
        """Checks for consistent indentation, spacing, line length and common formatting issues."""
        result = {"score": 5, "issues": []}
        lines = code.splitlines()
        
        tab_space_mix = 0
        long_lines = 0        # Lines > 120 chars
        trailing_ws = 0       # Trailing whitespace
        consecutive_blanks = 0
        max_consecutive_blanks = 0
        prev_blank = False

        for i, line in enumerate(lines):
            # Tab + space mixing
            if line.strip() and '\t' in line and ' ' in line[:len(line) - len(line.lstrip())]:
                tab_space_mix += 1

            # Line too long (PEP8 allows up to 79, we allow up to 120 for lenience)
            if len(line) > 120:
                long_lines += 1

            # Trailing whitespace
            if line != line.rstrip():
                trailing_ws += 1

            # Consecutive blank lines (PEP8: max 2)
            if line.strip() == "":
                if prev_blank:
                    consecutive_blanks += 1
                    max_consecutive_blanks = max(max_consecutive_blanks, consecutive_blanks)
                else:
                    consecutive_blanks = 1
                prev_blank = True
            else:
                consecutive_blanks = 0
                prev_blank = False

        # Deduct points
        score = 5

        if tab_space_mix > 0:
            score -= 2
            result["issues"].append(f"Tab/space mixing ({tab_space_mix} lines)")

        if long_lines > 3:
            score -= 1
            result["issues"].append(f"Lines >120 chars ({long_lines} lines)")

        if trailing_ws > 3:
            score -= 1
            result["issues"].append(f"Trailing whitespace ({trailing_ws} lines)")

        if max_consecutive_blanks > 2:
            score -= 1
            result["issues"].append(f"Excessive blank lines (max {max_consecutive_blanks} in a row)")

        result["score"] = max(0, score)
        return result

    def _check_risk_level(self, tree: ast.AST) -> Dict[str, Any]:
        """Detect risky operations (I/O, Network, Parsing, Volatile) using AST."""
        high_risk_modules = {
            "requests": "network", "urllib": "network", "http": "network", "socket": "network",
            "sqlite3": "database", "sqlalchemy": "database"
        }
        low_risk_modules = {
            "json": "parsing", "pickle": "parsing", "yaml": "parsing", "xml": "parsing",
            "os": "system", "subprocess": "system", "shutil": "system", "glob": "system",
            "pathlib": "system", "pandas": "data_parsing", "csv": "data_parsing"
        }
        
        found_high_risks = set()
        found_low_risks = set()
        
        # Helper to recursively check if a node is inside a Try block or With block
        def is_protected(target_node, protection_type=ast.Try):
            for node in ast.walk(tree):
                if isinstance(node, protection_type):
                    for child in ast.walk(node):
                        if child is target_node:
                            return True
            return False

        for node in ast.walk(tree):
            found_risk_type = None
            risk_level = None
            
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base_module = alias.name.split('.')[0]
                    if base_module in high_risk_modules:
                        found_risk_type = high_risk_modules[base_module]
                        risk_level = 'high'
                    elif base_module in low_risk_modules:
                        found_risk_type = low_risk_modules[base_module]
                        risk_level = 'low'
            elif isinstance(node, ast.ImportFrom) and node.module:
                base_module = node.module.split('.')[0]
                if base_module in high_risk_modules:
                    found_risk_type = high_risk_modules[base_module]
                    risk_level = 'high'
                elif base_module in low_risk_modules:
                    found_risk_type = low_risk_modules[base_module]
                    risk_level = 'low'
            
            # Check built-in risky functions/calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["eval", "exec"]:
                        found_risk_type = "volatile"
                        risk_level = 'high'
                    elif node.func.id in ["open", "input"]:
                        found_risk_type = "io"
                        risk_level = 'low'
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["remove", "rmdir", "rmtree", "unlink"]:
                        found_risk_type = "destructive_io"
                        risk_level = 'high'

            # Potential zero division
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.Mod, ast.FloorDiv)):
                if not isinstance(node.right, ast.Constant):
                    found_risk_type = "potential_zero_division"
                    risk_level = 'low'
            
            if found_risk_type:
                # Check if the risk itself is protected
                protected_by_try = is_protected(node, ast.Try)
                protected_by_with = is_protected(node, ast.With)
                
                risk_data = (found_risk_type, protected_by_try, protected_by_with)
                if risk_level == 'high':
                    found_high_risks.add(risk_data)
                elif risk_level == 'low':
                    found_low_risks.add(risk_data)

        return {
            "has_high_risk": len(found_high_risks) > 0,
            "has_low_risk": len(found_low_risks) > 0,
            "high_risks": list(found_high_risks),
            "low_risks": list(found_low_risks)
        }

    def analyze_error_handling(self, code: str) -> int:
        """
        Check for error handling patterns with risk awareness.
        Simple, safe code gets a high baseline (10/10).
        Risky code without try-except is penalized based on severity.
        """
        try:
            tree = ast.parse(code)
            risk_info = self._check_risk_level(tree)
            
            has_try = False
            has_raise = False
            has_assert = False
            has_bare_except = False
            has_broad_exception = False
            has_specific_exception = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Try):
                    has_try = True
                    for handler in node.handlers:
                        if handler.type is None: # Bare except:
                            has_bare_except = True
                        elif isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                            has_broad_exception = True
                        else:
                            has_specific_exception = True
                if isinstance(node, ast.Raise):
                    has_raise = True
                if isinstance(node, ast.Assert):
                    has_assert = True
            
            # Start with a perfect score 
            score = 10
            
            # Penalize unprotected risks
            unprotected_high = sum(1 for r, p_try, p_with in risk_info["high_risks"] if not p_try)
            unprotected_low = sum(1 for r, p_try, p_with in risk_info["low_risks"] if not p_try and r != "io")
            unprotected_io = sum(1 for r, p_try, p_with in risk_info["low_risks"] if r == "io" and not p_try and not p_with)
            
            if unprotected_high > 0:
                score -= 4  # High risk without try/except loses 4 points
            elif unprotected_low > 0 or unprotected_io > 0:
                score -= 2  # Low risk or IO without try/with loses 2 points
                
            # If the code lacks try but has some manual checks (raise/assert), give back 1 point buffer
            if (unprotected_high > 0 or unprotected_low > 0) and not has_try and (has_raise or has_assert):
                score = min(10, score + 1)
                
            # Apply penalty for bad practices
            if has_bare_except:
                score -= 3 # Heavy penalty for bare except
            elif has_broad_exception and not has_specific_exception:
                score -= 1 # Minor penalty for catching Exception broadly without specific catches

            return max(0, min(score, 10))
            
        except Exception:
            # Fallback for syntax errors 
            score = 5
            if "try:" in code: score += 2
            if "except " in code: 
                score += 2
                if "Exception" in code: score -= 1
            if "except:" in code: score -= 3 # Bare except penalty 
            if "with open" in code: score += 2
            if "raise " in code or "assert " in code: score += 1
            return max(0, min(score, 10))
    
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
            
            BLOCK_SIZE = 3
            duplicate_indices = set()
            
            if result["total_lines"] >= BLOCK_SIZE:
                seen_blocks = set()
                for i in range(len(code_lines) - BLOCK_SIZE + 1):
                    block = tuple(code_lines[i:i+BLOCK_SIZE])
                    
                    # Filter out blocks that are just trivial combinations of brackets or generic statements
                    is_trivial = all(len(line) < 5 or line in ('continue', 'break', 'pass', 'return', 'else:') for line in block)
                    
                    if not is_trivial:
                        if block in seen_blocks:
                            for j in range(i, i+BLOCK_SIZE):
                                duplicate_indices.add(j)
                        else:
                            seen_blocks.add(block)
                            
            result["duplicate_lines"] = len(duplicate_indices)
            result["unique_lines"] = result["total_lines"] - result["duplicate_lines"]
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
        coverage_res = self.analyze_test_coverage(code)
        
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
            coverage_res["score"] = 0
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
                "coverage": coverage_res,
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
            min(5, static_data["breakdown"]["duplication"]["score"])
        )
        
        # 3. Test & Build (15 pts)
        # Compile Success (binary): syntax_valid → 0 veya 5 puan
        compile_pts = 5 if static_data["breakdown"]["syntax"]["syntax_valid"] else 0
        # Test Coverage: coverage/100 * 10 (ister formülü)
        coverage_pts = static_data["breakdown"]["coverage"]["score"]  # 0-10
        cat3 = compile_pts + coverage_pts
        # Korumasız runtime riski varsa -3 ceza
        if static_data["breakdown"]["error_handling"] <= 5:
            cat3 = max(0, cat3 - 3)
        
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
