"""
Agent System for Formula Student AI

Exports:
- RouterAgent: Fast question classification
- ReasoningAgent: Main reasoning with RAG + tools
- AgentOrchestrator: Complete orchestration
"""

from .router import RouterAgent, QuestionType, RoutingDecision, route_question
from .reasoning_agent import (
    ReasoningAgent,
    AgentResponse,
    create_reasoning_agent_with_rag,
    quick_answer
)
from .orchestrator import (
    AgentOrchestrator,
    OrchestratedResponse,
    create_orchestrator_from_config,
    quick_answer_with_orchestrator
)

__all__ = [
    # Router
    "RouterAgent",
    "QuestionType",
    "RoutingDecision",
    "route_question",

    # Reasoning Agent
    "ReasoningAgent",
    "AgentResponse",
    "create_reasoning_agent_with_rag",
    "quick_answer",

    # Orchestrator
    "AgentOrchestrator",
    "OrchestratedResponse",
    "create_orchestrator_from_config",
    "quick_answer_with_orchestrator",
]
