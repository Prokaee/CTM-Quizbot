#!/usr/bin/env python3
"""
Formula Student AI Assistant - Main Entry Point

Simple CLI interface for the Formula Student quiz bot.
"""

import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings, validate_settings
from src.agents import create_orchestrator_from_config


def print_banner():
    """Print welcome banner"""
    print("""
======================================================================

        FORMULA STUDENT AI ASSISTANT

        Powered by Gemini 3.0 Pro + RAG + Formula Library

======================================================================
    """)


def main():
    """Main entry point"""

    print_banner()

    # Validate configuration
    print("[INIT] Validating configuration...")
    errors = validate_settings()

    if errors:
        print("\n[ERROR] Configuration errors found:")
        for error in errors:
            print(f"   - {error}")
        print("\n[INFO] Please check your .env file and ensure:")
        print("   1. GEMINI_API_KEY is set")
        print("   2. PDF files are in data/raw/")
        print("   3. Run 'python scripts/build_rag.py' to build the system")
        return 1

    print("[OK] Configuration valid\n")

    # Check if RAG is built
    embeddings_dir = settings.base_dir / "data" / "embeddings"
    handbook_embeddings = embeddings_dir / "fsa_handbook_embeddings.json"
    rules_embeddings = embeddings_dir / "fs_rules_embeddings.json"

    if not handbook_embeddings.exists() or not rules_embeddings.exists():
        print("[WARN] RAG system not built yet!")
        print("\n[INFO] To build the RAG system, run:")
        print("   python scripts/build_rag.py")
        print("\nThis will:")
        print("   - Process PDF documents")
        print("   - Create semantic chunks")
        print("   - Generate embeddings")
        print("   - Build vector store")
        print()

        choice = input("Continue without RAG? (answer quality will be lower) [y/N]: ").strip().lower()
        if choice not in ['y', 'yes']:
            print("\n[EXIT] Exiting. Please run build_rag.py first.")
            return 0

    # Create orchestrator
    print("\n[INIT] Initializing AI system...")
    print("=" * 70)

    try:
        orchestrator = create_orchestrator_from_config()
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize system: {e}")
        print("\n[INFO] Make sure you've run 'python scripts/build_rag.py' first")
        return 1

    print("\n[OK] System ready!")
    print("\n[INFO] Type 'help' for commands, 'quit' to exit")
    print("=" * 70)

    # Start interactive mode
    orchestrator.interactive_mode()

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[EXIT] Interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
