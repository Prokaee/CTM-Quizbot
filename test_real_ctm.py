#!/usr/bin/env python3
"""Test Real CTM Quiz Questions"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents import create_orchestrator_from_config

def main():
    print("=" * 70)
    print("REAL CTM QUIZ TEST")
    print("=" * 70)

    orchestrator = create_orchestrator_from_config()
    print("\n[OK] System ready!\n")

    # Real CTM Questions
    questions = [
        {
            "id": 868,
            "q": "Simple question to get started: Frad the FSG Racing Alpaca tries his hand at the acceleration event. As hopefully everyone knows, alpacas have a maximum speed of 56km/h and an acceleration of 4 m/s². Ignore grip, air resistance and downforce. What time does Frad set? Round to two decimal places. Answer in seconds. Example answer: 1.23",
            "correct": "6.77"
        },
        {
            "id": 885,
            "q": "Does the: Engine for the CV need to be off, TS for the EV need to be deactivated, when the vehicle is standing still, as the last point of the VSV sequence?",
            "correct": "Yes"
        },
        {
            "id": 872,
            "q": "Which of the following statements describes the requirements for ASSI placement on a vehicle? C) One ASSI must be placed on each side behind the driver's compartment, 160 mm below the top of the main hoop and 600 mm above the ground. A third ASSI must be at the rear, on the centerline, 160 mm below the top of the main hoop and 100 mm above the brake light.",
            "correct": "C (see T14.9.2)"
        }
    ]

    for test in questions:
        print(f"\n{'='*70}")
        print(f"ID: {test['id']} | Expected: {test['correct']}")
        print(f"{'='*70}")
        print(f"Q: {test['q'][:150]}...")
        print(f"{'-'*70}")

        try:
            response = orchestrator.process_question(test['q'])

            print(f"\n[TYPE] {response.question_type.value}")
            print(f"[CONF] {response.agent_response.confidence:.1%}")
            print(f"[TIME] {response.processing_time:.2f}s")

            # Extract just the answer (first line or short version)
            answer_lines = response.answer.strip().split('\n')
            short_answer = answer_lines[0][:100]

            print(f"\n[ANSWER]: {short_answer}")
            print(f"[FULL ANSWER]:\n{response.answer[:400]}...")

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*70}")
    print("[DONE] All tests complete!")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
