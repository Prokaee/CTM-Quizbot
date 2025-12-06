"""
Agent Orchestrator

Main orchestrator that coordinates router, RAG, and reasoning agents
to answer Formula Student questions.
"""

from typing import Optional, Any
from dataclasses import dataclass

from .router import RouterAgent, QuestionType, RoutingDecision
from .reasoning_agent import ReasoningAgent, AgentResponse
from src.rag.retriever import Retriever


@dataclass
class OrchestratedResponse:
    """Complete response from the orchestrator"""
    answer: str
    question_type: QuestionType
    routing_decision: RoutingDecision
    agent_response: AgentResponse
    processing_time: Optional[float] = None


class AgentOrchestrator:
    """
    Main orchestrator for the Formula Student AI system.

    Coordinates:
    1. Router (Gemini 2.5 Flash) - Fast classification
    2. RAG (Vector Search) - Context retrieval
    3. Reasoning Agent (Gemini 3.0 Pro) - Answer generation
    """

    def __init__(self, retriever: Optional[Retriever] = None):
        """
        Initialize orchestrator.

        Args:
            retriever: RAG retriever instance
        """
        self.router = RouterAgent()
        self.reasoning_agent = ReasoningAgent(
            retriever=retriever,
            use_tools=True,
            use_rag=retriever is not None
        )
        self.retriever = retriever

    def process_question(
        self,
        question: str,
        image: Optional[Any] = None,
        skip_routing: bool = False
    ) -> OrchestratedResponse:
        """
        Process a question through the complete pipeline.

        Args:
            question: User's question
            image: Optional image (PIL.Image or path)
            skip_routing: Skip routing and go directly to reasoning

        Returns:
            OrchestratedResponse with complete result
        """
        import time
        start_time = time.time()

        # Step 1: Route the question
        if not skip_routing:
            routing_decision = self.router.route(
                question=question,
                has_image=image is not None
            )
            print(f"[ROUTE] Type: {routing_decision.question_type.value} (confidence: {routing_decision.confidence:.2f})")
        else:
            # Default to REASONING if skipping
            from .router import QuestionType, RoutingDecision
            routing_decision = RoutingDecision(
                question_type=QuestionType.REASONING,
                confidence=1.0,
                reasoning="Routing skipped"
            )

        # Step 2: Handle PHYSICS_MATH questions with pure reasoning
        from .router import QuestionType
        if routing_decision.question_type == QuestionType.PHYSICS_MATH:
            print("[AGENT] Using pure LLM reasoning for physics/math...")
            agent_response = self.reasoning_agent.answer_physics_math(question)
        else:
            # Step 3: Determine RAG usage
            use_rag = self.router.should_use_rag(routing_decision.question_type)

            # Step 4: Determine tool usage
            use_tools = self.router.should_use_tools(routing_decision.question_type)

            # Update reasoning agent configuration
            self.reasoning_agent.use_tools = use_tools

            # Step 5: Generate answer
            print(f"[AGENT] Generating answer (RAG: {use_rag}, Tools: {use_tools})...")

            agent_response = self.reasoning_agent.answer_question(
                question=question,
                image=image,
                top_k_retrieval=5 if use_rag else 0
            )

        # Step 6: Calculate processing time
        processing_time = time.time() - start_time

        print(f"[OK] Answer generated in {processing_time:.2f}s (confidence: {agent_response.confidence:.2f})")

        return OrchestratedResponse(
            answer=agent_response.answer,
            question_type=routing_decision.question_type,
            routing_decision=routing_decision,
            agent_response=agent_response,
            processing_time=processing_time
        )

    def answer(
        self,
        question: str,
        image: Optional[Any] = None,
        verbose: bool = True
    ) -> str:
        """
        Simple answer method (convenience).

        Args:
            question: User question
            image: Optional image
            verbose: Print processing steps

        Returns:
            Answer text
        """
        if not verbose:
            import sys
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

        try:
            response = self.process_question(question, image)
            return response.answer
        finally:
            if not verbose:
                sys.stdout = old_stdout

    def answer_with_metadata(
        self,
        question: str,
        image: Optional[Any] = None
    ) -> dict:
        """
        Answer with full metadata.

        Args:
            question: User question
            image: Optional image

        Returns:
            Dictionary with answer and metadata
        """
        response = self.process_question(question, image)

        return {
            "answer": response.answer,
            "question_type": response.question_type.value,
            "confidence": response.agent_response.confidence,
            "rule_references": response.agent_response.rule_references,
            "calculation_used": response.agent_response.calculation_used,
            "retrieval_used": response.agent_response.retrieval_used,
            "sources": response.agent_response.sources,
            "processing_time": response.processing_time
        }

    def interactive_mode(self):
        """
        Start interactive question-answering mode.
        """
        print("=" * 70)
        print("Formula Student AI Assistant - Interactive Mode")
        print("=" * 70)
        print("\nType your questions or commands:")
        print("  - 'quit' or 'exit' to quit")
        print("  - 'help' for help")
        print("  - 'stats' for retriever statistics")
        print("=" * 70)

        while True:
            try:
                question = input("\n[Q] Your question: ").strip()

                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n[EXIT] Goodbye!")
                    break

                if question.lower() == 'help':
                    self._print_help()
                    continue

                if question.lower() == 'stats':
                    self._print_stats()
                    continue

                if not question:
                    continue

                # Process question
                response = self.process_question(question)

                # Print answer
                print("\n" + "=" * 70)
                print("[ANSWER]:")
                print("=" * 70)
                print(response.answer)

                # Print metadata
                print("\n" + "-" * 70)
                print("[METADATA]:")
                print(f"  Type: {response.question_type.value}")
                print(f"  Confidence: {response.agent_response.confidence:.1%}")

                if response.agent_response.rule_references:
                    print(f"  Rule References: {', '.join(response.agent_response.rule_references)}")

                if response.agent_response.calculation_used:
                    print(f"  Calculation: {response.agent_response.calculation_used}")

                if response.agent_response.sources:
                    print(f"  Sources: {len(response.agent_response.sources)} chunks retrieved")

                print(f"  Processing Time: {response.processing_time:.2f}s")
                print("=" * 70)

            except KeyboardInterrupt:
                print("\n\n[EXIT] Goodbye!")
                break
            except Exception as e:
                print(f"\n[ERROR] Error: {e}")
                print("Please try again with a different question.")

    def _print_help(self):
        """Print help message"""
        print("\n" + "=" * 70)
        print("HELP - How to Use")
        print("=" * 70)
        print("""
This AI assistant answers questions about Formula Student rules.

Example questions:
  - "How many fire extinguishers are required?"
  - "Team got 4.5s in skidpad, max is 5.0s. What's their score?"
  - "What is the acceleration event scoring formula?"
  - "If FSA Handbook says X and FS Rules say Y, which wins?"

Commands:
  - help  : Show this help
  - stats : Show retriever statistics
  - quit  : Exit interactive mode

The system will:
  1. Route your question to the right handler
  2. Retrieve relevant rules (RAG)
  3. Use calculation tools if needed
  4. Generate an answer with rule references
        """)
        print("=" * 70)

    def _print_stats(self):
        """Print retriever statistics"""
        if self.retriever:
            stats = self.retriever.get_statistics()
            print("\n" + "=" * 70)
            print("RETRIEVER STATISTICS")
            print("=" * 70)
            print(f"Total chunks indexed: {stats['vector_store']['total_chunks']}")
            print(f"Document types: {stats['vector_store']['document_types']}")
            print(f"Embedding model: {stats['embedding_model']}")
            print(f"Default top-k: {stats['top_k_default']}")
            print("=" * 70)
        else:
            print("\n[WARN]  No retriever configured (RAG disabled)")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_orchestrator_from_config() -> AgentOrchestrator:
    """
    Create orchestrator with RAG from configuration.

    Returns:
        Configured AgentOrchestrator
    """
    from src.rag.retriever import create_retriever_from_config

    print("[INIT] Initializing Formula Student AI Assistant...")
    print("=" * 70)

    # Create retriever
    retriever = create_retriever_from_config()

    # Create orchestrator
    orchestrator = AgentOrchestrator(retriever=retriever)

    print("\n[OK] System ready!")
    print("=" * 70)

    return orchestrator


def quick_answer_with_orchestrator(question: str) -> str:
    """
    Quick answer using full orchestration (convenience).

    Args:
        question: Question to answer

    Returns:
        Answer text
    """
    orchestrator = create_orchestrator_from_config()
    return orchestrator.answer(question, verbose=False)
