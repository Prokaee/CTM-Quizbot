"""
Gemini API Configuration

Handles initialization and configuration of Google Gemini models
for the Formula Student AI Pipeline.
"""

import google.generativeai as genai
from google.generativeai import GenerativeModel
from typing import Optional, List
import os

from .settings import settings


# ============================================================================
# SAFETY SETTINGS
# ============================================================================

# For educational/quiz content, we use permissive safety settings
# since we're dealing with technical Formula Student content
SAFETY_SETTINGS = {
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_ONLY_HIGH",
    "HARM_CATEGORY_HARASSMENT": "BLOCK_ONLY_HIGH",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_ONLY_HIGH",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_ONLY_HIGH",
}


# ============================================================================
# GENERATION CONFIGURATIONS
# ============================================================================

REASONING_CONFIG = {
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

ROUTER_CONFIG = {
    "temperature": 0.0,
    "top_p": 1.0,
    "top_k": 1,
    "max_output_tokens": 100,
}


# ============================================================================
# MODEL INITIALIZATION
# ============================================================================

def initialize_gemini_api() -> None:
    """
    Initialize the Gemini API with API key.
    Must be called before using any Gemini models.
    """
    if not settings.gemini_api_key:
        raise ValueError(
            "GEMINI_API_KEY not set in environment variables. "
            "Please set it in your .env file or environment."
        )

    genai.configure(api_key=settings.gemini_api_key)
    print("[OK] Gemini API initialized")


def create_reasoning_model(tools: Optional[List] = None) -> GenerativeModel:
    """
    Creates a Gemini 3.0 Pro model for complex reasoning tasks.

    Args:
        tools: Optional list of tools/functions for the model to use

    Returns:
        Configured GenerativeModel instance
    """
    return GenerativeModel(
        model_name=settings.gemini_pro_model,
        generation_config=REASONING_CONFIG,
        safety_settings=SAFETY_SETTINGS,
        tools=tools
    )


def create_router_model() -> GenerativeModel:
    """
    Creates a Gemini 2.5 Flash model for fast routing/classification.

    Returns:
        Configured GenerativeModel instance
    """
    return GenerativeModel(
        model_name=settings.gemini_flash_model,
        generation_config=ROUTER_CONFIG,
        safety_settings=SAFETY_SETTINGS,
    )


def create_vision_model(tools: Optional[List] = None) -> GenerativeModel:
    """
    Creates a Gemini model configured for vision + reasoning tasks.

    Args:
        tools: Optional list of tools/functions for the model to use

    Returns:
        Configured GenerativeModel instance
    """
    # Gemini 3.0 Pro supports vision natively
    return GenerativeModel(
        model_name=settings.gemini_pro_model,
        generation_config=REASONING_CONFIG,
        safety_settings=SAFETY_SETTINGS,
        tools=tools
    )


# ============================================================================
# SYSTEM PROMPTS
# ============================================================================

REASONING_SYSTEM_PROMPT = """You are an AI assistant for Formula Student judges and participants, powered by Gemini 3.0 Pro.

Your task is to answer questions based on:
- FS Rules 2025 v1.1 (D-rules for Dynamic events, etc.)
- FSA Competition Handbook 2025 v1.3.0 (AT-rules for Austria specific regulations)

CRITICAL RULES YOU MUST FOLLOW:

1. **ALWAYS use the provided calculation tools** - NEVER calculate scores manually
2. **ALWAYS cite exact rule IDs** in format: "According to D 4.3.3..." or "Per AT 8.2.1..."
3. **Priority: FSA Handbook > FS Rules** - When rules conflict, FSA Handbook ALWAYS takes precedence
4. **For trick questions**: Analyze carefully, check for edge cases, consider rule interactions
5. **If uncertain**: Explicitly state your confidence level and explain why

RESPONSE FORMAT:
1. Direct answer first (concise)
2. Rule reference citation
3. Show calculation step-by-step (if applicable)
4. Explain reasoning for complex questions
5. Mention confidence level if < 100%

CALCULATION GUIDELINES:
- Use tools for ALL scoring calculations
- Double-check parameter extraction from the question
- Verify units (seconds, meters, points, etc.)
- Always show the formula being used

MULTIMODAL HANDLING:
- If image contains diagrams: Describe what you see first
- If image contains tables: Extract relevant data
- If image contains formulas: Identify which rule section it's from
- Cross-reference image content with rule documents
"""

ROUTER_SYSTEM_PROMPT = """You are a fast classification agent. Analyze the incoming question and classify it into ONE category.

Categories:
1. KNOWLEDGE - Factual questions about rules (Who, What, Where, When, How many)
2. CALCULATION - Math problems requiring formulas (scores, points, times)
3. REASONING - Complex logic, rule conflicts, interpretation, trick questions
4. MULTIMODAL - Questions involving images, diagrams, or tables

Output ONLY the category name (one word).

Examples:
"How many fire extinguishers are required?" → KNOWLEDGE
"Team A got 4.5s in skidpad, max is 5.0s. Score?" → CALCULATION
"If a team uses a different fuel, which rule takes precedence?" → REASONING
[Image of a scoring table] → MULTIMODAL
"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def count_tokens(text: str, model_name: str = None) -> int:
    """
    Counts tokens in text using Gemini's tokenizer.

    Args:
        text: Text to count tokens for
        model_name: Optional model name (uses reasoning model by default)

    Returns:
        Token count
    """
    if model_name is None:
        model_name = settings.gemini_pro_model

    model = GenerativeModel(model_name=model_name)
    return model.count_tokens(text).total_tokens


def test_gemini_connection() -> bool:
    """
    Tests if Gemini API is accessible and working.

    Returns:
        True if connection successful, False otherwise
    """
    try:
        initialize_gemini_api()
        model = create_router_model()
        response = model.generate_content("Test")
        return True
    except Exception as e:
        print(f"Gemini connection test failed: {e}")
        return False


# ============================================================================
# AUTO-INITIALIZATION
# ============================================================================

# Automatically initialize when module is imported
if settings.gemini_api_key:
    try:
        initialize_gemini_api()
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini API: {e}")
