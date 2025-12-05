"""
Tests for Formula Student calculation formulas
"""

import pytest
from src.core.formulas import (
    calculate_skidpad_score,
    calculate_acceleration_score,
    calculate_autocross_score,
    calculate_endurance_score,
    calculate_efficiency_score,
    get_formula,
    list_available_formulas,
)


class TestSkidpadScore:
    """Tests for Skidpad scoring formula (D 4.3.3)"""

    def test_normal_score(self):
        """Test normal scoring within max time"""
        result = calculate_skidpad_score(t_team=4.5, t_max=5.0)
        assert result.score == 33.46  # Calculated from formula
        assert result.rule_reference == "D 4.3.3"
        assert result.formula_name == "skidpad_score"

    def test_perfect_score(self):
        """Test maximum score (fastest time)"""
        result = calculate_skidpad_score(t_team=4.0, t_max=5.0)
        assert result.score > 33.46  # Better than normal
        assert result.score <= 75.0  # Never exceeds max

    def test_minimum_score(self):
        """Test minimum score when exceeding max time"""
        result = calculate_skidpad_score(t_team=6.0, t_max=5.0)
        assert result.score == 3.75  # 0.05 * 75.0
        assert "exceeded max time" in result.explanation.lower()

    def test_invalid_time(self):
        """Test that negative time raises error"""
        with pytest.raises(ValueError):
            calculate_skidpad_score(t_team=-1.0, t_max=5.0)


class TestAccelerationScore:
    """Tests for Acceleration scoring formula (D 4.2.3)"""

    def test_normal_score(self):
        """Test normal acceleration score"""
        result = calculate_acceleration_score(t_team=4.0, t_max=4.5)
        assert 0 < result.score <= 75.0
        assert result.rule_reference == "D 4.2.3"

    def test_minimum_score(self):
        """Test minimum score when exceeding max time"""
        result = calculate_acceleration_score(t_team=5.0, t_max=4.5)
        assert result.score == 3.75  # 0.05 * 75.0


class TestAutocrossScore:
    """Tests for Autocross scoring formula (D 5.1)"""

    def test_perfect_score(self):
        """Test perfect score (team == fastest)"""
        result = calculate_autocross_score(t_team=60.0, t_min=60.0)
        assert result.score == 100.0

    def test_normal_score(self):
        """Test normal score (team slower than fastest)"""
        result = calculate_autocross_score(t_team=65.0, t_min=60.0)
        assert 90 < result.score < 95  # Should be around 92.31
        assert result.score < 100.0

    def test_no_minimum_time(self):
        """Test when no valid minimum time exists"""
        result = calculate_autocross_score(t_team=60.0, t_min=0.0)
        assert result.score == 0.0


class TestEnduranceScore:
    """Tests for Endurance scoring formula (D 6.3)"""

    def test_perfect_score(self):
        """Test perfect score (team == fastest)"""
        result = calculate_endurance_score(t_team=1500.0, t_min=1500.0)
        assert result.score == 250.0

    def test_normal_score(self):
        """Test normal score"""
        result = calculate_endurance_score(t_team=1600.0, t_min=1500.0)
        assert 230 < result.score < 240
        assert result.score < 250.0


class TestEfficiencyScore:
    """Tests for Efficiency scoring formula (D 7.1)"""

    def test_perfect_efficiency(self):
        """Test perfect efficiency (minimum energy and time)"""
        result = calculate_efficiency_score(
            e_team=100.0,
            e_min=100.0,
            t_team_eff=1500.0,
            t_min_eff=1500.0
        )
        assert result.score == 100.0

    def test_normal_efficiency(self):
        """Test normal efficiency score"""
        result = calculate_efficiency_score(
            e_team=110.0,
            e_min=100.0,
            t_team_eff=1550.0,
            t_min_eff=1500.0
        )
        assert result.score < 100.0
        assert result.score > 0.0

    def test_efficiency_cap(self):
        """Test that efficiency factor is capped at 1.0"""
        # Impossible scenario: team uses less than minimum
        result = calculate_efficiency_score(
            e_team=90.0,
            e_min=100.0,
            t_team_eff=1400.0,
            t_min_eff=1500.0
        )
        # Should be capped at 100 points max
        assert result.score <= 100.0

    def test_zero_energy(self):
        """Test invalid input with zero energy"""
        result = calculate_efficiency_score(
            e_team=0.0,
            e_min=100.0,
            t_team_eff=1500.0,
            t_min_eff=1500.0
        )
        assert result.score == 0.0


class TestFormulaRegistry:
    """Tests for formula registration and retrieval"""

    def test_get_formula(self):
        """Test retrieving formula by name"""
        formula = get_formula("skidpad_score")
        assert formula is not None
        assert callable(formula)

    def test_get_nonexistent_formula(self):
        """Test retrieving non-existent formula"""
        formula = get_formula("nonexistent_formula")
        assert formula is None

    def test_list_formulas(self):
        """Test listing all available formulas"""
        formulas = list_available_formulas()
        assert "skidpad_score" in formulas
        assert "acceleration_score" in formulas
        assert "autocross_score" in formulas
        assert "endurance_score" in formulas
        assert "efficiency_score" in formulas
        assert len(formulas) >= 5


class TestFormulaResults:
    """Tests for FormulaResult dataclass"""

    def test_result_structure(self):
        """Test that result contains all required fields"""
        result = calculate_skidpad_score(t_team=4.5, t_max=5.0)
        assert hasattr(result, 'score')
        assert hasattr(result, 'formula_name')
        assert hasattr(result, 'rule_reference')
        assert hasattr(result, 'parameters')
        assert hasattr(result, 'explanation')
        assert hasattr(result, 'version')

    def test_result_parameters(self):
        """Test that parameters are stored correctly"""
        result = calculate_skidpad_score(t_team=4.5, t_max=5.0, p_max=75.0)
        assert result.parameters['t_team'] == 4.5
        assert result.parameters['t_max'] == 5.0
        assert result.parameters['p_max'] == 75.0
