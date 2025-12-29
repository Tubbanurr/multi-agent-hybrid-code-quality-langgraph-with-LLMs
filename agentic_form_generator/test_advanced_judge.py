"""
Test script for the Advanced Code Judge in agentic_form_generator
Demonstrates multi-tool static analysis system
"""

from module.advanced_judge import advanced_judge

# Test codes - different quality levels

code_excellent = '''
from typing import List, Optional

class FibonacciCalculator:
    """
    A calculator for Fibonacci numbers with memoization.
    
    This class provides efficient Fibonacci calculation using
    dynamic programming with memoization technique.
    """
    
    def __init__(self):
        """Initialize the calculator with an empty cache."""
        self.cache: dict = {}
    
    def calculate(self, n: int) -> int:
        """
        Calculate the nth Fibonacci number.
        
        Args:
            n: The position in Fibonacci sequence (0-indexed)
            
        Returns:
            The nth Fibonacci number
            
        Raises:
            ValueError: If n is negative
        """
        if n < 0:
            raise ValueError("n must be non-negative")
        
        if n in self.cache:
            return self.cache[n]
        
        if n <= 1:
            return n
        
        result = self.calculate(n - 1) + self.calculate(n - 2)
        self.cache[n] = result
        return result
    
    def get_sequence(self, count: int) -> List[int]:
        """
        Generate a Fibonacci sequence.
        
        Args:
            count: Number of Fibonacci numbers to generate
            
        Returns:
            List of Fibonacci numbers
        """
        return [self.calculate(i) for i in range(count)]
'''

code_medium = '''
def fibonacci(n):
    """Calculate fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def get_fib_sequence(count):
    result = []
    for i in range(count):
        result.append(fibonacci(i))
    return result

class Calculator:
    def __init__(self):
        self.values = []
    
    def add(self, x, y):
        return x + y
'''

code_poor = '''
def f(x):
    if x==0 or x==1:return x
    return f(x-1)+f(x-2)

password="admin123"
api_key = "sk-1234567890abcdef"

def run_code(code):
    eval(code)  # Security risk!

import os,sys,json
'''

# Run advanced judge
print("🔬 Advanced Code Judge - Test Run")
print("=" * 70)
print()

result = advanced_judge(
    code_llama=code_excellent,
    code_deepseek=code_medium,
    code_gemini=code_poor
)

print(f"🏆 WINNER: {result['winner']}")
print()
print(f"💬 REASONING:")
print(f"   {result['reasoning']}")
print()
print("=" * 70)
print()

for model_name, data in result['scores'].items():
    print(f"📊 {model_name}: {data['total_score']}/100")
    print("-" * 70)
    
    breakdown = data['breakdown']
    
    # AST Structure
    ast_data = breakdown['ast_structure']
    print(f"  1️⃣  AST Structure: {ast_data['score']}/20")
    print(f"      ✓ Syntax Valid: {ast_data['syntax_valid']}")
    print(f"      ✓ Classes: {ast_data['classes']}")
    print(f"      ✓ Functions: {ast_data['functions']}")
    print(f"      ✓ Docstrings: {ast_data['docstrings']}")
    if ast_data['error']:
        print(f"      ⚠ Error: {ast_data['error']}")
    
    # Pylint Quality
    pylint_data = breakdown['pylint_quality']
    print(f"\n  2️⃣  Pylint Quality: {pylint_data['scaled_score']}/25")
    if pylint_data['raw_score']:
        print(f"      ✓ Raw Score: {pylint_data['raw_score']:.2f}/10")
    if pylint_data['error']:
        print(f"      ⚠ {pylint_data['error']}")
    
    # Complexity
    complexity_data = breakdown['complexity']
    print(f"\n  3️⃣  Complexity: {complexity_data['score']}/20")
    if complexity_data['average_complexity']:
        print(f"      ✓ Avg Complexity: {complexity_data['average_complexity']:.2f}")
        print(f"      ✓ Max Complexity: {complexity_data['max_complexity']}")
    if complexity_data['error']:
        print(f"      ⚠ {complexity_data['error']}")
    
    # Security
    security_data = breakdown['security']
    print(f"\n  4️⃣  Security: {security_data['score']}/15")
    print(f"      ✓ Total Issues: {security_data['issues_count']}")
    if security_data['severity_high'] > 0:
        print(f"      🔴 HIGH Severity: {security_data['severity_high']}")
    if security_data['severity_medium'] > 0:
        print(f"      🟡 MEDIUM Severity: {security_data['severity_medium']}")
    if security_data['severity_low'] > 0:
        print(f"      🟢 LOW Severity: {security_data['severity_low']}")
    if security_data['error']:
        print(f"      ⚠ {security_data['error']}")
    
    # Style
    style_data = breakdown['style']
    print(f"\n  5️⃣  Style (PEP8): {style_data['score']}/10")
    print(f"      ✓ Violations: {style_data['violations']}")
    if style_data['error']:
        print(f"      ⚠ {style_data['error']}")
    
    # Type Hints
    type_data = breakdown['type_hints']
    print(f"\n  6️⃣  Type Hints: {type_data['score']}/10")
    if type_data['total_functions'] > 0:
        coverage_pct = type_data['coverage'] * 100
        print(f"      ✓ Coverage: {coverage_pct:.0f}% ({type_data['functions_with_hints']}/{type_data['total_functions']} functions)")
    else:
        print(f"      - No functions detected")
    if type_data['error']:
        print(f"      ⚠ {type_data['error']}")
    
    print()
    print("=" * 70)
    print()

print("✅ Test completed!")
print()
print("💡 TIP: Install all tools for full analysis:")
print("   pip install -r requirements.txt")
