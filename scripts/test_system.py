"""
Test the Complete Formula Student AI System

This script tests the entire pipeline:
1. Router classification
2. RAG retrieval
3. Reasoning agent
4. Tool usage (calculations)

Run after building the RAG system with build_rag.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings, validate_settings
from src.agents.orchestrator import AgentOrchestrator, create_orchestrator_from_config


def test_basic_questions():
    """Test with basic questions"""

    print("\n" + "=" * 80)
    print("TEST 1: Basic Knowledge Questions")
    print("=" * 80)

    orchestrator = create_orchestrator_from_config()

    questions = [
        "How many fire extinguishers are required?",
        "What is the minimum weight of the vehicle?",
        "What are the skidpad event rules?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'=' * 80}")
        print(f"Question {i}: {question}")
        print('=' * 80)

        try:
            response = orchestrator.process_question(question)

            print(f"\n📝 Answer:")
            print(response.answer)

            print(f"\n📊 Metadata:")
            print(f"  - Type: {response.question_type.value}")
            print(f"  - Confidence: {response.agent_response.confidence:.1%}")
            print(f"  - Time: {response.processing_time:.2f}s")

            if response.agent_response.rule_references:
                print(f"  - Rules: {', '.join(response.agent_response.rule_references[:5])}")

        except Exception as e:
            print(f"\n❌ Error: {e}")


def test_calculation_questions():
    """Test calculation questions with tools"""

    print("\n" + "=" * 80)
    print("TEST 2: Calculation Questions (Tool Usage)")
    print("=" * 80)

    orchestrator = create_orchestrator_from_config()

    questions = [
        "Team got 4.5 seconds in skidpad, max time is 5.0 seconds. What's their score?",
        "In acceleration, team time is 4.0s and max is 4.5s. Calculate the score.",
        "Team finished autocross in 65 seconds, fastest was 60 seconds. What points?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'=' * 80}")
        print(f"Question {i}: {question}")
        print('=' * 80)

        try:
            response = orchestrator.process_question(question)

            print(f"\n📝 Answer:")
            print(response.answer)

            print(f"\n📊 Metadata:")
            print(f"  - Type: {response.question_type.value}")
            print(f"  - Calculation Used: {response.agent_response.calculation_used or 'None'}")
            print(f"  - Confidence: {response.agent_response.confidence:.1%}")
            print(f"  - Time: {response.processing_time:.2f}s")

        except Exception as e:
            print(f"\n❌ Error: {e}")


def test_complex_questions():
    """Test complex reasoning questions"""

    print("\n" + "=" * 80)
    print("TEST 3: Complex Reasoning Questions")
    print("=" * 80)

    orchestrator = create_orchestrator_from_config()

    questions = [
        "If FSA Handbook and FS Rules conflict, which takes precedence?",
        "Can a team get efficiency points if they got a cone penalty in endurance?",
        "What happens if a team exceeds the maximum time in skidpad?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'=' * 80}")
        print(f"Question {i}: {question}")
        print('=' * 80)

        try:
            response = orchestrator.process_question(question)

            print(f"\n📝 Answer:")
            print(response.answer)

            print(f"\n📊 Metadata:")
            print(f"  - Type: {response.question_type.value}")
            print(f"  - Confidence: {response.agent_response.confidence:.1%}")
            print(f"  - Sources: {len(response.agent_response.sources) if response.agent_response.sources else 0} chunks")
            print(f"  - Time: {response.processing_time:.2f}s")

        except Exception as e:
            print(f"\n❌ Error: {e}")


def test_interactive_mode():
    """Start interactive mode"""

    print("\n" + "=" * 80)
    print("INTERACTIVE MODE")
    print("=" * 80)

    orchestrator = create_orchestrator_from_config()
    orchestrator.interactive_mode()


def main():
    """Main test function"""

    print("=" * 80)
    print(" FORMULA STUDENT AI SYSTEM - COMPREHENSIVE TEST")
    print("=" * 80)

    # Validate configuration
    print("\n📋 Validating configuration...")
    errors = validate_settings()

    if errors:
        print("\n❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease fix configuration and retry.")
        return 1

    print("✅ Configuration valid")

    # Check if embeddings exist
    embeddings_dir = settings.base_dir / "data" / "embeddings"
    handbook_embeddings = embeddings_dir / "fsa_handbook_embeddings.json"
    rules_embeddings = embeddings_dir / "fs_rules_embeddings.json"

    if not handbook_embeddings.exists() or not rules_embeddings.exists():
        print("\n⚠️  WARNING: Embeddings not found!")
        print("Please run 'python scripts/build_rag.py' first to build the RAG system.")
        print("\nContinuing anyway (some tests may fail)...")

    # Run tests
    print("\n" + "=" * 80)
    print("Starting Tests...")
    print("=" * 80)

    choice = input("\nSelect test mode:\n  1. Basic questions\n  2. Calculation questions\n  3. Complex reasoning\n  4. All tests\n  5. Interactive mode\n\nChoice (1-5): ").strip()

    if choice == "1":
        test_basic_questions()
    elif choice == "2":
        test_calculation_questions()
    elif choice == "3":
        test_complex_questions()
    elif choice == "4":
        test_basic_questions()
        test_calculation_questions()
        test_complex_questions()
    elif choice == "5":
        test_interactive_mode()
    else:
        print("Invalid choice. Exiting.")
        return 1

    print("\n" + "=" * 80)
    print(" TESTS COMPLETE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit(main())
