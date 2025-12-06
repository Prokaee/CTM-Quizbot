#!/usr/bin/env python3
"""
Quick Demo Test - Formula Student AI
Tests the system with a few example questions
"""

import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents import create_orchestrator_from_config

def main():
    print("=" * 70)
    print("FORMULA STUDENT AI - QUICK DEMO")
    print("=" * 70)

    # Create orchestrator
    print("\n[INIT] Loading system...")
    orchestrator = create_orchestrator_from_config()
    print("[OK] System ready!\n")

    # Test questions
    test_questions = [
        "What is the minimum track width requirement?",
        "How many fire extinguishers are required?",
        "What are the skidpad event rules?"
    ]

    print("=" * 70)
    print("RUNNING TEST QUESTIONS")
    print("=" * 70)

    for i, question in enumerate(test_questions, 1):
        print(f"\n[TEST {i}/3] Question: {question}")
        print("-" * 70)

        try:
            response = orchestrator.process_question(question)

            print(f"\n[ANSWER]:")
            print(response.answer[:500] + "..." if len(response.answer) > 500 else response.answer)

            print(f"\n[INFO]:")
            print(f"  - Type: {response.question_type.value}")
            print(f"  - Confidence: {response.agent_response.confidence:.1%}")
            print(f"  - Sources: {len(response.agent_response.sources)} chunks")
            print(f"  - Time: {response.processing_time:.2f}s")

        except Exception as e:
            print(f"[ERROR] {e}")

        print("=" * 70)

    print("\n[OK] Demo complete!")
    print("\nTo use the interactive CLI, run: python main.py")
    print("=" * 70)

if __name__ == "__main__":
    main()
