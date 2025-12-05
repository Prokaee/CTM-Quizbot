"""
Formula Student Calculation Library
All formulas are hardcoded for deterministic, tested calculations.
Each formula includes rule references and version information.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class FormulaVersion(Enum):
    """Tracks which rule version each formula is from"""
    FS_RULES_2025_V1_1 = "FS Rules 2025 v1.1"
    FSA_HANDBOOK_2025_V1_3 = "FSA Handbook 2025 v1.3.0"


@dataclass
class FormulaResult:
    """Standard result format for all formulas"""
    score: float
    formula_name: str
    rule_reference: str
    parameters: Dict[str, Any]
    explanation: str
    version: FormulaVersion


# ============================================================================
# DYNAMIC EVENTS SCORING
# ============================================================================

def calculate_skidpad_score(
    t_team: float,
    t_max: float,
    p_max: float = 75.0
) -> FormulaResult:
    """
    Calculates Skidpad score according to FS Rules D 4.3.3

    Args:
        t_team: Team's corrected time in seconds
        t_max: Maximum time (slowest corrected time + 1.25 * difference)
        p_max: Maximum points available (default 75.0)

    Returns:
        FormulaResult with score and metadata

    Formula:
        If t_team > t_max: Score = 0.05 * p_max
        Else: Score = 0.95 * p_max * [(t_max/t_team)² - 1] / 0.5625 + 0.05 * p_max
    """
    if t_team <= 0:
        raise ValueError("Team time must be positive")

    if t_team > t_max:
        score = 0.05 * p_max
        explanation = f"Team exceeded max time ({t_team}s > {t_max}s), minimum score applied"
    else:
        term1 = (t_max / t_team) ** 2 - 1
        score = 0.95 * p_max * (term1 / 0.5625) + 0.05 * p_max
        explanation = (
            f"Score = 0.95 × {p_max} × [({t_max}/{t_team})² - 1] / 0.5625 + 0.05 × {p_max} "
            f"= {score:.2f} points"
        )

    return FormulaResult(
        score=round(score, 2),
        formula_name="skidpad_score",
        rule_reference="D 4.3.3",
        parameters={"t_team": t_team, "t_max": t_max, "p_max": p_max},
        explanation=explanation,
        version=FormulaVersion.FS_RULES_2025_V1_1
    )


def calculate_acceleration_score(
    t_team: float,
    t_max: float,
    p_max: float = 75.0
) -> FormulaResult:
    """
    Calculates Acceleration score according to FS Rules D 4.2.3

    Args:
        t_team: Team's corrected time in seconds
        t_max: Maximum time (slowest corrected time + 1.0s)
        p_max: Maximum points available (default 75.0)

    Returns:
        FormulaResult with score and metadata

    Formula:
        If t_team > t_max: Score = 0.05 * p_max
        Else: Score = 0.95 * p_max * [(t_max/t_team) - 1] / 0.3333 + 0.05 * p_max
    """
    if t_team <= 0:
        raise ValueError("Team time must be positive")

    if t_team > t_max:
        score = 0.05 * p_max
        explanation = f"Team exceeded max time ({t_team}s > {t_max}s), minimum score applied"
    else:
        term1 = (t_max / t_team) - 1
        score = 0.95 * p_max * (term1 / 0.3333) + 0.05 * p_max
        explanation = (
            f"Score = 0.95 × {p_max} × [({t_max}/{t_team}) - 1] / 0.3333 + 0.05 × {p_max} "
            f"= {score:.2f} points"
        )

    return FormulaResult(
        score=round(score, 2),
        formula_name="acceleration_score",
        rule_reference="D 4.2.3",
        parameters={"t_team": t_team, "t_max": t_max, "p_max": p_max},
        explanation=explanation,
        version=FormulaVersion.FS_RULES_2025_V1_1
    )


def calculate_autocross_score(
    t_team: float,
    t_min: float,
    p_max: float = 100.0
) -> FormulaResult:
    """
    Calculates Autocross score according to FS Rules D 5.1

    Args:
        t_team: Team's corrected time in seconds
        t_min: Minimum time (fastest corrected time)
        p_max: Maximum points available (default 100.0)

    Returns:
        FormulaResult with score and metadata

    Formula:
        Score = p_max * (t_min / t_team)
    """
    if t_team <= 0:
        raise ValueError("Team time must be positive")

    if t_min == 0:
        score = 0.0
        explanation = "No valid minimum time, score = 0"
    else:
        score = p_max * (t_min / t_team)
        explanation = (
            f"Score = {p_max} × ({t_min}/{t_team}) = {score:.2f} points"
        )

    return FormulaResult(
        score=round(score, 2),
        formula_name="autocross_score",
        rule_reference="D 5.1",
        parameters={"t_team": t_team, "t_min": t_min, "p_max": p_max},
        explanation=explanation,
        version=FormulaVersion.FS_RULES_2025_V1_1
    )


def calculate_endurance_score(
    t_team: float,
    t_min: float,
    p_max: float = 250.0
) -> FormulaResult:
    """
    Calculates Endurance score according to FS Rules D 6.3

    Args:
        t_team: Team's corrected time in seconds
        t_min: Minimum time (fastest corrected time)
        p_max: Maximum points available (default 250.0)

    Returns:
        FormulaResult with score and metadata

    Formula:
        Score = p_max * (t_min / t_team)
    """
    if t_team <= 0:
        raise ValueError("Team time must be positive")

    if t_min == 0:
        score = 0.0
        explanation = "No valid minimum time, score = 0"
    else:
        score = p_max * (t_min / t_team)
        explanation = (
            f"Score = {p_max} × ({t_min}/{t_team}) = {score:.2f} points"
        )

    return FormulaResult(
        score=round(score, 2),
        formula_name="endurance_score",
        rule_reference="D 6.3",
        parameters={"t_team": t_team, "t_min": t_min, "p_max": p_max},
        explanation=explanation,
        version=FormulaVersion.FS_RULES_2025_V1_1
    )


def calculate_efficiency_score(
    e_team: float,
    e_min: float,
    t_team_eff: float,
    t_min_eff: float,
    p_max: float = 100.0
) -> FormulaResult:
    """
    Calculates Efficiency score according to FS Rules D 7.1

    Args:
        e_team: Team's energy consumption
        e_min: Minimum energy consumption
        t_team_eff: Team's efficiency factor time
        t_min_eff: Minimum efficiency factor time
        p_max: Maximum points available (default 100.0)

    Returns:
        FormulaResult with score and metadata

    Formula:
        Efficiency Factor = (e_min / e_team) * (t_min_eff / t_team_eff)
        Score = p_max * min(Efficiency Factor, 1.0)
    """
    if e_team <= 0 or t_team_eff <= 0:
        score = 0.0
        explanation = "Invalid parameters (energy or time <= 0), score = 0"
    else:
        efficiency_factor = (e_min / e_team) * (t_min_eff / t_team_eff)
        capped_factor = min(efficiency_factor, 1.0)
        score = p_max * capped_factor
        explanation = (
            f"Efficiency Factor = ({e_min}/{e_team}) × ({t_min_eff}/{t_team_eff}) = {efficiency_factor:.4f}\n"
            f"Score = {p_max} × {capped_factor:.4f} = {score:.2f} points"
        )

    return FormulaResult(
        score=round(score, 2),
        formula_name="efficiency_score",
        rule_reference="D 7.1",
        parameters={
            "e_team": e_team,
            "e_min": e_min,
            "t_team_eff": t_team_eff,
            "t_min_eff": t_min_eff,
            "p_max": p_max
        },
        explanation=explanation,
        version=FormulaVersion.FS_RULES_2025_V1_1
    )


# ============================================================================
# STATIC EVENTS SCORING (Simplified - actual rules may have more complexity)
# ============================================================================

def calculate_cost_score(
    cost_real: float,
    cost_min: float,
    p_max: float = 100.0
) -> FormulaResult:
    """
    Calculates Cost Event score (simplified)

    Args:
        cost_real: Team's real cost
        cost_min: Minimum cost among all teams
        p_max: Maximum points available (default 100.0)

    Returns:
        FormulaResult with score and metadata
    """
    if cost_real <= 0:
        raise ValueError("Cost must be positive")

    if cost_min == 0:
        score = 0.0
        explanation = "No valid minimum cost, score = 0"
    else:
        # Simplified formula - actual Cost scoring is more complex
        score = p_max * (cost_min / cost_real)
        explanation = (
            f"Score = {p_max} × ({cost_min}/{cost_real}) = {score:.2f} points\n"
            f"Note: Actual cost scoring includes manufacturing scores and is more complex"
        )

    return FormulaResult(
        score=round(score, 2),
        formula_name="cost_score_simplified",
        rule_reference="D 3.1 (Simplified)",
        parameters={"cost_real": cost_real, "cost_min": cost_min, "p_max": p_max},
        explanation=explanation,
        version=FormulaVersion.FS_RULES_2025_V1_1
    )


# ============================================================================
# FORMULA REGISTRY
# ============================================================================

FORMULA_LIBRARY: Dict[str, callable] = {
    "skidpad_score": calculate_skidpad_score,
    "acceleration_score": calculate_acceleration_score,
    "autocross_score": calculate_autocross_score,
    "endurance_score": calculate_endurance_score,
    "efficiency_score": calculate_efficiency_score,
    "cost_score": calculate_cost_score,
}


def get_formula(formula_name: str) -> Optional[callable]:
    """
    Retrieves a formula function by name

    Args:
        formula_name: Name of the formula to retrieve

    Returns:
        Formula function or None if not found
    """
    return FORMULA_LIBRARY.get(formula_name)


def list_available_formulas() -> list[str]:
    """Returns list of all available formula names"""
    return list(FORMULA_LIBRARY.keys())


def get_formula_info(formula_name: str) -> Optional[Dict[str, str]]:
    """
    Gets metadata about a formula

    Args:
        formula_name: Name of the formula

    Returns:
        Dictionary with formula metadata or None
    """
    formula = get_formula(formula_name)
    if formula:
        return {
            "name": formula_name,
            "docstring": formula.__doc__ or "",
            "signature": str(formula.__annotations__)
        }
    return None
