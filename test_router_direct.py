#!/usr/bin/env python3
"""Test Router Classification Directly"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents.router import RouterAgent

def main():
    router = RouterAgent()

    questions = [
        "Calculate acceleration time for 75m with 4 m/s² acceleration",
        "Calculate pipe resonance frequency for 780 Hz",
        "What is the minimum track width in Formula Student?",
        "Calculate skidpad score for team time 4.5s and max time 5.0s",
        "Organ pipe calculations with frequency 820 Hz"
    ]

    print("=" * 70)
    print("ROUTER CLASSIFICATION TEST")
    print("=" * 70)

    for q in questions:
        decision = router.route(q)
        print(f"\nQ: {q}")
        print(f"   -> {decision.question_type.value} (confidence: {decision.confidence:.2f})")
        print(f"   Reasoning: {decision.reasoning}")

if __name__ == "__main__":
    main()
