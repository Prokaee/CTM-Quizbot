"""
Gemini Function Declarations (Tools) for Formula Student Calculations

This module defines the function calling interface for Gemini to use our
hardcoded formula library. Gemini will analyze questions, select the right
formula, extract parameters, and call these functions.
"""

from typing import List, Dict, Any
from google.generativeai.types import FunctionDeclaration, Tool
from .formulas import (
    calculate_skidpad_score,
    calculate_acceleration_score,
    calculate_autocross_score,
    calculate_endurance_score,
    calculate_efficiency_score,
    calculate_cost_score,
    FORMULA_LIBRARY
)


# ============================================================================
# FUNCTION DECLARATIONS FOR GEMINI
# ============================================================================

skidpad_declaration = FunctionDeclaration(
    name="calculate_skidpad_score",
    description="""
    Calculates the Skidpad score according to FS Rules D 4.3.3.

    Use this when the question involves:
    - Skidpad event scoring
    - Corrected times for skidpad
    - Figure-8 maneuverability test

    The formula accounts for team time vs. maximum allowed time.
    """,
    parameters={
        "type": "object",
        "properties": {
            "t_team": {
                "type": "number",
                "description": "Team's corrected time in seconds for the skidpad event"
            },
            "t_max": {
                "type": "number",
                "description": "Maximum time threshold (slowest corrected time + 1.25 * difference)"
            },
            "p_max": {
                "type": "number",
                "description": "Maximum points available (default: 75.0)"
            }
        },
        "required": ["t_team", "t_max"]
    }
)

acceleration_declaration = FunctionDeclaration(
    name="calculate_acceleration_score",
    description="""
    Calculates the Acceleration score according to FS Rules D 4.2.3.

    Use this when the question involves:
    - Acceleration event (75m straight line)
    - 0-75m sprint times
    - Acceleration performance scoring

    The formula accounts for team time vs. maximum allowed time.
    """,
    parameters={
        "type": "object",
        "properties": {
            "t_team": {
                "type": "number",
                "description": "Team's corrected time in seconds for the acceleration event"
            },
            "t_max": {
                "type": "number",
                "description": "Maximum time threshold (slowest corrected time + 1.0s)"
            },
            "p_max": {
                "type": "number",
                "description": "Maximum points available (default: 75.0)"
            }
        },
        "required": ["t_team", "t_max"]
    }
)

autocross_declaration = FunctionDeclaration(
    name="calculate_autocross_score",
    description="""
    Calculates the Autocross score according to FS Rules D 5.1.

    Use this when the question involves:
    - Autocross event scoring
    - Single lap time trial
    - Handling course performance

    Score is proportional to fastest time divided by team time.
    """,
    parameters={
        "type": "object",
        "properties": {
            "t_team": {
                "type": "number",
                "description": "Team's corrected time in seconds"
            },
            "t_min": {
                "type": "number",
                "description": "Fastest corrected time among all teams"
            },
            "p_max": {
                "type": "number",
                "description": "Maximum points available (default: 100.0)"
            }
        },
        "required": ["t_team", "t_min"]
    }
)

endurance_declaration = FunctionDeclaration(
    name="calculate_endurance_score",
    description="""
    Calculates the Endurance score according to FS Rules D 6.3.

    Use this when the question involves:
    - Endurance event (22km race)
    - Long distance performance
    - Multi-lap endurance scoring

    Score is proportional to fastest time divided by team time.
    """,
    parameters={
        "type": "object",
        "properties": {
            "t_team": {
                "type": "number",
                "description": "Team's corrected total time in seconds"
            },
            "t_min": {
                "type": "number",
                "description": "Fastest corrected time among all teams"
            },
            "p_max": {
                "type": "number",
                "description": "Maximum points available (default: 250.0)"
            }
        },
        "required": ["t_team", "t_min"]
    }
)

efficiency_declaration = FunctionDeclaration(
    name="calculate_efficiency_score",
    description="""
    Calculates the Efficiency score according to FS Rules D 7.1.

    Use this when the question involves:
    - Energy efficiency scoring
    - Fuel/battery consumption
    - CO2 emissions or energy usage

    Accounts for both energy consumption and time performance.
    """,
    parameters={
        "type": "object",
        "properties": {
            "e_team": {
                "type": "number",
                "description": "Team's energy consumption (in appropriate units)"
            },
            "e_min": {
                "type": "number",
                "description": "Minimum energy consumption among all teams"
            },
            "t_team_eff": {
                "type": "number",
                "description": "Team's efficiency factor time"
            },
            "t_min_eff": {
                "type": "number",
                "description": "Minimum efficiency factor time"
            },
            "p_max": {
                "type": "number",
                "description": "Maximum points available (default: 100.0)"
            }
        },
        "required": ["e_team", "e_min", "t_team_eff", "t_min_eff"]
    }
)

cost_declaration = FunctionDeclaration(
    name="calculate_cost_score",
    description="""
    Calculates a simplified Cost Event score.

    Use this when the question involves:
    - Cost event scoring
    - Real cost analysis
    - Manufacturing cost evaluation

    Note: This is a simplified version. Actual cost scoring includes
    manufacturing scores and additional complexity.
    """,
    parameters={
        "type": "object",
        "properties": {
            "cost_real": {
                "type": "number",
                "description": "Team's real manufacturing cost"
            },
            "cost_min": {
                "type": "number",
                "description": "Minimum cost among all teams"
            },
            "p_max": {
                "type": "number",
                "description": "Maximum points available (default: 100.0)"
            }
        },
        "required": ["cost_real", "cost_min"]
    }
)


# ============================================================================
# TOOL CREATION
# ============================================================================

def create_formula_tools() -> Tool:
    """
    Creates a Gemini Tool containing all Formula Student calculation functions.

    Returns:
        Tool object with all function declarations
    """
    return Tool(
        function_declarations=[
            skidpad_declaration,
            acceleration_declaration,
            autocross_declaration,
            endurance_declaration,
            efficiency_declaration,
            cost_declaration,
        ]
    )


# ============================================================================
# FUNCTION EXECUTION MAPPER
# ============================================================================

FUNCTION_MAP: Dict[str, callable] = {
    "calculate_skidpad_score": calculate_skidpad_score,
    "calculate_acceleration_score": calculate_acceleration_score,
    "calculate_autocross_score": calculate_autocross_score,
    "calculate_endurance_score": calculate_endurance_score,
    "calculate_efficiency_score": calculate_efficiency_score,
    "calculate_cost_score": calculate_cost_score,
}


def execute_function_call(function_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Executes a function call from Gemini with the provided arguments.

    Args:
        function_name: Name of the function to call
        arguments: Dictionary of arguments to pass to the function

    Returns:
        FormulaResult object from the calculation

    Raises:
        ValueError: If function name is not recognized
    """
    if function_name not in FUNCTION_MAP:
        raise ValueError(f"Unknown function: {function_name}")

    func = FUNCTION_MAP[function_name]
    result = func(**arguments)

    return result


def format_function_result_for_gemini(result) -> str:
    """
    Formats a FormulaResult for inclusion in Gemini's context.

    Args:
        result: FormulaResult object

    Returns:
        Formatted string for Gemini to use in its response
    """
    return f"""
Calculation Result:
- Score: {result.score} points
- Formula: {result.formula_name}
- Rule Reference: {result.rule_reference}
- Parameters: {result.parameters}
- Explanation: {result.explanation}
- Version: {result.version.value}
"""


# ============================================================================
# TOOL METADATA
# ============================================================================

def get_tools_info() -> List[Dict[str, Any]]:
    """
    Returns metadata about all available tools.

    Returns:
        List of dictionaries with tool information
    """
    return [
        {
            "name": "calculate_skidpad_score",
            "event": "Skidpad",
            "rule_reference": "D 4.3.3",
            "max_points": 75.0
        },
        {
            "name": "calculate_acceleration_score",
            "event": "Acceleration",
            "rule_reference": "D 4.2.3",
            "max_points": 75.0
        },
        {
            "name": "calculate_autocross_score",
            "event": "Autocross",
            "rule_reference": "D 5.1",
            "max_points": 100.0
        },
        {
            "name": "calculate_endurance_score",
            "event": "Endurance",
            "rule_reference": "D 6.3",
            "max_points": 250.0
        },
        {
            "name": "calculate_efficiency_score",
            "event": "Efficiency",
            "rule_reference": "D 7.1",
            "max_points": 100.0
        },
        {
            "name": "calculate_cost_score",
            "event": "Cost",
            "rule_reference": "D 3.1",
            "max_points": 100.0
        }
    ]
