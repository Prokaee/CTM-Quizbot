"""
Router Agent

Fast question classification using Gemini 2.5 Flash.
Routes questions to appropriate handlers (knowledge, calculation, reasoning).
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

from config.gemini_config import create_router_model
from config.prompts import ROUTER_PROMPT


class QuestionType(Enum):
    """Types of questions the system can handle"""
    KNOWLEDGE = "KNOWLEDGE"
    CALCULATION = "CALCULATION"
    REASONING = "REASONING"
    MULTIMODAL = "MULTIMODAL"
    PHYSICS_MATH = "PHYSICS_MATH"  # General physics/math not in rules


@dataclass
class RoutingDecision:
    """Result of routing decision"""
    question_type: QuestionType
    confidence: float
    reasoning: str


class RouterAgent:
    """Fast classification agent using Gemini 2.5 Flash"""

    def __init__(self):
        """Initialize router with Gemini 2.5 Flash"""
        self.model = create_router_model()
        self.system_prompt = ROUTER_PROMPT

    def route(
        self,
        question: str,
        has_image: bool = False
    ) -> RoutingDecision:
        """
        Route a question to the appropriate handler.

        Args:
            question: Question text
            has_image: Whether the question includes an image

        Returns:
            RoutingDecision with classification
        """
        # If has image, automatically classify as MULTIMODAL
        if has_image:
            return RoutingDecision(
                question_type=QuestionType.MULTIMODAL,
                confidence=1.0,
                reasoning="Question includes image/screenshot"
            )

        # Create prompt
        prompt = f"{self.system_prompt}\n\nQuestion: {question}\n\nClassification:"

        # Get classification from Gemini Flash
        try:
            response = self.model.generate_content(prompt)
            classification = response.text.strip().upper()

            # Parse classification
            if "PHYSICS_MATH" in classification or "PHYSICS" in classification or "MATH" in classification:
                question_type = QuestionType.PHYSICS_MATH
            elif "KNOWLEDGE" in classification:
                question_type = QuestionType.KNOWLEDGE
            elif "CALCULATION" in classification:
                question_type = QuestionType.CALCULATION
            elif "REASONING" in classification:
                question_type = QuestionType.REASONING
            elif "MULTIMODAL" in classification:
                question_type = QuestionType.MULTIMODAL
            else:
                # Default to REASONING for safety (most capable handler)
                question_type = QuestionType.REASONING

            return RoutingDecision(
                question_type=question_type,
                confidence=0.9,  # Gemini Flash is very reliable
                reasoning=f"Classified as {question_type.value} based on question pattern"
            )

        except Exception as e:
            print(f"Router error: {e}")
            # Fallback to REASONING
            return RoutingDecision(
                question_type=QuestionType.REASONING,
                confidence=0.5,
                reasoning=f"Error in classification, defaulting to REASONING: {e}"
            )

    def should_use_rag(self, question_type: QuestionType) -> bool:
        """
        Determine if RAG retrieval is needed for this question type.

        Args:
            question_type: Type of question

        Returns:
            True if RAG should be used
        """
        # Physics/math questions don't need RAG (not in rules)
        # All other types benefit from RAG
        return question_type != QuestionType.PHYSICS_MATH

    def should_use_tools(self, question_type: QuestionType) -> bool:
        """
        Determine if calculation tools are needed.

        Args:
            question_type: Type of question

        Returns:
            True if tools should be available
        """
        # Tools needed for Formula Student scoring calculations only
        # Physics/math questions use pure LLM reasoning
        return question_type in [QuestionType.CALCULATION, QuestionType.REASONING, QuestionType.MULTIMODAL]


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def route_question(question: str, has_image: bool = False) -> RoutingDecision:
    """
    Route a question (convenience function).

    Args:
        question: Question text
        has_image: Whether question has image

    Returns:
        RoutingDecision
    """
    router = RouterAgent()
    return router.route(question, has_image)
