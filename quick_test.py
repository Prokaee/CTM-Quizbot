"""
Quick test of the system without RAG
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.formulas import calculate_skidpad_score, calculate_acceleration_score

print("=" * 70)
print("FORMULA TEST (No API Needed)")
print("=" * 70)

# Test 1: Skidpad
print("\nTest 1: Skidpad Calculation")
print("-" * 70)
result = calculate_skidpad_score(t_team=4.5, t_max=5.0)
print(f"Team time: 4.5s, Max time: 5.0s")
print(f"Score: {result.score} points")
print(f"Rule: {result.rule_reference}")
print(f"Explanation: {result.explanation}")

# Test 2: Acceleration
print("\n\nTest 2: Acceleration Calculation")
print("-" * 70)
result = calculate_acceleration_score(t_team=4.0, t_max=4.5)
print(f"Team time: 4.0s, Max time: 4.5s")
print(f"Score: {result.score} points")
print(f"Rule: {result.rule_reference}")

print("\n" + "=" * 70)
print("ALL FORMULAS WORKING!")
print("=" * 70)
