"""
Reasoning Agent

Main agent using Gemini 3.0 Pro for complex reasoning and question answering.
Integrates RAG, calculation tools, and multimodal capabilities.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import google.generativeai as genai

from config.gemini_config import create_reasoning_model, create_vision_model
from config.prompts import REASONING_AGENT_PROMPT, create_question_prompt
from src.core.tools import create_formula_tools, execute_function_call, format_function_result_for_gemini
from src.rag.retriever import Retriever, RetrievalResult


@dataclass
class AgentResponse:
    """Response from the reasoning agent"""
    answer: str
    rule_references: List[str]
    confidence: float
    calculation_used: Optional[str] = None
    retrieval_used: bool = False
    sources: Optional[List[Dict]] = None
    raw_response: Optional[Any] = None


class ReasoningAgent:
    """Main reasoning agent powered by Gemini 3.0 Pro"""

    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        use_tools: bool = True,
        use_rag: bool = True
    ):
        """
        Initialize reasoning agent.

        Args:
            retriever: RAG retriever instance (optional)
            use_tools: Whether to use calculation tools
            use_rag: Whether to use RAG retrieval
        """
        self.use_rag = use_rag and retriever is not None
        self.retriever = retriever
        self.use_tools = use_tools

        # Create model with or without tools
        if use_tools:
            tools = create_formula_tools()
            self.model = create_reasoning_model(tools=[tools])
        else:
            self.model = create_reasoning_model()

        self.system_prompt = REASONING_AGENT_PROMPT
        self.chat_session = None

    def answer_question(
        self,
        question: str,
        image: Optional[Any] = None,
        top_k_retrieval: int = 5
    ) -> AgentResponse:
        """
        Answer a question using RAG + reasoning + tools.

        Args:
            question: User's question
            image: Optional image (PIL.Image or file path)
            top_k_retrieval: Number of chunks to retrieve

        Returns:
            AgentResponse with answer and metadata
        """
        # Step 1: Retrieve relevant context (if RAG enabled)
        retrieval_result = None
        context = None

        if self.use_rag:
            retrieval_result = self.retriever.retrieve_with_priority_boost(
                query=question,
                top_k=top_k_retrieval
            )
            context = self.retriever.format_context_for_llm(retrieval_result)

        # Step 2: Create prompt
        full_prompt = self._create_prompt(question, context, image)

        # Step 3: Generate response
        if image:
            response = self._generate_with_image(full_prompt, image)
        else:
            response = self._generate_text_only(full_prompt)

        # Step 4: Parse response and extract metadata
        return self._parse_response(response, retrieval_result)

    def _create_prompt(
        self,
        question: str,
        context: Optional[str] = None,
        image: Optional[Any] = None
    ) -> str:
        """
        Create the complete prompt for the model.

        Args:
            question: User question
            context: Retrieved context from RAG
            image: Optional image

        Returns:
            Complete prompt string
        """
        prompt_parts = [self.system_prompt, "\n\n"]

        if context:
            prompt_parts.append(context)
            prompt_parts.append("\n\n")

        if image:
            prompt_parts.append("**Image Provided:** Please analyze the image along with the question.\n\n")

        prompt_parts.append(f"**Question:**\n{question}\n\n")
        prompt_parts.append("**Your Answer:**\n")

        return "".join(prompt_parts)

    def _generate_text_only(self, prompt: str) -> Any:
        """
        Generate response for text-only question.

        Args:
            prompt: Complete prompt

        Returns:
            Model response
        """
        try:
            response = self.model.generate_content(prompt)

            # Handle function calls
            while response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]

                # Check if it's a function call
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    function_name = function_call.name
                    function_args = dict(function_call.args)

                    # Execute the function
                    result = execute_function_call(function_name, function_args)
                    result_text = format_function_result_for_gemini(result)

                    # Send result back to model
                    response = self.model.generate_content([
                        prompt,
                        response.candidates[0].content,
                        genai.protos.Content(parts=[
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=function_name,
                                    response={"result": result_text}
                                )
                            )
                        ])
                    ])
                else:
                    break

            return response

        except Exception as e:
            raise RuntimeError(f"Error generating response: {e}")

    def _generate_with_image(self, prompt: str, image: Any) -> Any:
        """
        Generate response for question with image.

        Args:
            prompt: Complete prompt
            image: Image (PIL.Image or path)

        Returns:
            Model response
        """
        # Use vision model
        vision_model = create_vision_model(
            tools=[create_formula_tools()] if self.use_tools else None
        )

        try:
            # Handle different image types
            from PIL import Image
            if isinstance(image, str):
                img = Image.open(image)
            else:
                img = image

            response = vision_model.generate_content([prompt, img])

            # Handle function calls (similar to text-only)
            while response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]

                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    function_name = function_call.name
                    function_args = dict(function_call.args)

                    result = execute_function_call(function_name, function_args)
                    result_text = format_function_result_for_gemini(result)

                    response = vision_model.generate_content([
                        prompt,
                        img,
                        response.candidates[0].content,
                        genai.protos.Content(parts=[
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=function_name,
                                    response={"result": result_text}
                                )
                            )
                        ])
                    ])
                else:
                    break

            return response

        except Exception as e:
            raise RuntimeError(f"Error generating response with image: {e}")

    def _parse_response(
        self,
        response: Any,
        retrieval_result: Optional[RetrievalResult] = None
    ) -> AgentResponse:
        """
        Parse model response into AgentResponse.

        Args:
            response: Raw model response
            retrieval_result: RAG retrieval result (if used)

        Returns:
            Structured AgentResponse
        """
        answer_text = response.text if hasattr(response, 'text') else str(response)

        # Extract rule references (basic regex)
        import re
        rule_pattern = r'([DATB])\s*(\d+(?:\.\d+)*)'
        rule_matches = re.findall(rule_pattern, answer_text)
        rule_references = [f"{match[0]} {match[1]}" for match in rule_matches]

        # Check if calculation was used
        calculation_used = None
        if hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    calculation_used = part.function_call.name
                    break

        # Build sources from retrieval
        sources = None
        if retrieval_result:
            sources = [
                {
                    "document": chunk.metadata.get('document_type', 'Unknown'),
                    "pages": chunk.metadata.get('page_range', 'Unknown'),
                    "score": chunk.score
                }
                for chunk in retrieval_result.chunks[:3]
            ]

        # Estimate confidence (simple heuristic)
        confidence = self._estimate_confidence(
            answer_text,
            rule_references,
            calculation_used,
            retrieval_result
        )

        return AgentResponse(
            answer=answer_text,
            rule_references=list(set(rule_references)),
            confidence=confidence,
            calculation_used=calculation_used,
            retrieval_used=retrieval_result is not None,
            sources=sources,
            raw_response=response
        )

    def _estimate_confidence(
        self,
        answer: str,
        rule_refs: List[str],
        calculation_used: Optional[str],
        retrieval_result: Optional[RetrievalResult]
    ) -> float:
        """
        Estimate confidence in the answer.

        Args:
            answer: Answer text
            rule_refs: Extracted rule references
            calculation_used: Whether calculation was used
            retrieval_result: RAG result

        Returns:
            Confidence score (0-1)
        """
        confidence = 0.5  # Base confidence

        # Boost if rule references found
        if rule_refs:
            confidence += 0.2

        # Boost if calculation tool was used (deterministic)
        if calculation_used:
            confidence += 0.2

        # Boost if RAG found good matches
        if retrieval_result and retrieval_result.chunks:
            avg_score = sum(c.score for c in retrieval_result.chunks) / len(retrieval_result.chunks)
            confidence += 0.1 * min(avg_score, 1.0)

        # Check for uncertainty phrases
        uncertainty_phrases = [
            "not certain", "not sure", "might be", "could be",
            "possibly", "uncertain", "unclear"
        ]
        if any(phrase in answer.lower() for phrase in uncertainty_phrases):
            confidence *= 0.8

        return min(confidence, 1.0)

    def start_conversation(self) -> None:
        """Start a multi-turn conversation session"""
        self.chat_session = self.model.start_chat(history=[])

    def continue_conversation(self, message: str) -> AgentResponse:
        """
        Continue a multi-turn conversation.

        Args:
            message: User message

        Returns:
            AgentResponse
        """
        if self.chat_session is None:
            self.start_conversation()

        # In conversation mode, we may want to retrieve context
        retrieval_result = None
        if self.use_rag:
            retrieval_result = self.retriever.retrieve_with_priority_boost(
                query=message,
                top_k=3  # Fewer for conversation
            )
            context = self.retriever.format_context_for_llm(retrieval_result)
            message_with_context = f"{context}\n\n{message}"
        else:
            message_with_context = message

        response = self.chat_session.send_message(message_with_context)
        return self._parse_response(response, retrieval_result)

    def clear_conversation(self) -> None:
        """Clear conversation history"""
        self.chat_session = None


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_reasoning_agent_with_rag(retriever: Retriever) -> ReasoningAgent:
    """
    Create a fully-configured reasoning agent with RAG.

    Args:
        retriever: RAG retriever instance

    Returns:
        ReasoningAgent ready to use
    """
    return ReasoningAgent(
        retriever=retriever,
        use_tools=True,
        use_rag=True
    )


def quick_answer(question: str, retriever: Optional[Retriever] = None) -> str:
    """
    Quick answer to a question (convenience function).

    Args:
        question: Question to answer
        retriever: Optional retriever

    Returns:
        Answer text
    """
    agent = ReasoningAgent(retriever=retriever, use_tools=True, use_rag=retriever is not None)
    response = agent.answer_question(question)
    return response.answer
