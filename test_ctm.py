#!/usr/bin/env python3
"""Test CTM Quiz Questions"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents import create_orchestrator_from_config

def main():
    print("=" * 70)
    print("CTM QUIZ TEST - Hybrid System")
    print("=" * 70)

    # Create orchestrator
    print("\n[INIT] Loading system...")
    orchestrator = create_orchestrator_from_config()
    print("[OK] System ready!\n")

    # CTM Quiz Questions
    ctm_questions = [
        {
            "q": "Frad the FSG Racing Alpaca tries his hand at the acceleration event. Alpacas have a maximum speed of 56km/h and an acceleration of 4 m/s². Ignore grip, air resistance and downforce. What time does Frad set for 75m? Round to two decimal places. Answer in seconds.",
            "expected_type": "PHYSICS_MATH"
        },
        {
            "q": "What is the minimum track width requirement for Formula Student?",
            "expected_type": "KNOWLEDGE"
        }
    ]

    for i, test in enumerate(ctm_questions, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {test['expected_type']} Question")
        print(f"{'='*70}")
        print(f"Q: {test['q'][:80]}...")
        print(f"{'-'*70}")

        try:
            response = orchestrator.process_question(test['q'])

            print(f"\n[ROUTE] Classified as: {response.question_type.value}")
            print(f"[CONFIDENCE] {response.agent_response.confidence:.1%}")
            print(f"[TIME] {response.processing_time:.2f}s")
            print(f"\n[ANSWER]:\n{response.answer[:300]}...")

        except Exception as e:
            print(f"[ERROR] {e}")

    print(f"\n{'='*70}")
    print("[OK] Test complete!")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
