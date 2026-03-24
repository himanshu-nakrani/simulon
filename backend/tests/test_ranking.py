"""Property-based tests for the Simulation Engine — outcome ranking.

Property 2: Ranking non-increasing order
Property 3: Risk weight derivation
Property 4: Dynamic salary normalization
Property 5: Probability-weighted option aggregation

Validates: Requirements 5.1, 5.2, 5.3, 5.5, 5.6, 5.7
"""

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backend.app.simulation import rank_outcomes

# ---------------------------------------------------------------------------
# Standard weights used across all tests
# ---------------------------------------------------------------------------

WEIGHTS = {"salary_w": 0.4, "happiness_w": 0.4}

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

option_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
    min_size=1,
    max_size=20,
).filter(lambda s: s.strip())

risk_tolerance_strategy = st.floats(
    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
)

# A single result entry for a given option name and probability
def result_entry_strategy(option: str, probability: float):
    return st.fixed_dictionaries(
        {
            "option": st.just(option),
            "scenario": st.just("some scenario"),
            "probability": st.just(probability),
            "salary": st.floats(min_value=10000.0, max_value=200000.0, allow_nan=False, allow_infinity=False),
            "risk_score": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            "happiness": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        }
    )


# Strategy: list of results where each option has exactly one scenario (probability=1.0)
# This keeps aggregation simple while still testing ranking.
multi_option_results_strategy = st.lists(
    option_name_strategy, min_size=1, max_size=5, unique=True
).flatmap(
    lambda options: st.tuples(
        *[result_entry_strategy(opt, 1.0) for opt in options]
    ).map(list)
)


# ---------------------------------------------------------------------------
# Property 2: Ranking non-increasing order
# Validates: Requirements 5.6, 5.7
# ---------------------------------------------------------------------------


@given(results=multi_option_results_strategy, risk_tolerance=risk_tolerance_strategy)
@settings(max_examples=100)
def test_ranking_non_increasing_order(results, risk_tolerance):
    """**Validates: Requirements 5.6, 5.7**

    For any non-empty results list and valid weights/risk_tolerance:
    - ranked list is sorted in non-increasing order of aggregate score
    - best_option equals ranked[0]["option"]
    """
    output = rank_outcomes(results, WEIGHTS, risk_tolerance)
    ranked = output["ranked"]
    best_option = output["best_option"]

    # ranked[0].score >= ranked[i].score for all i > 0
    for i in range(1, len(ranked)):
        assert ranked[0]["score"] >= ranked[i]["score"], (
            f"ranked[0].score={ranked[0]['score']} < ranked[{i}].score={ranked[i]['score']}"
        )

    # best_option == ranked[0]["option"]
    assert best_option == ranked[0]["option"], (
        f"best_option={best_option!r} != ranked[0]['option']={ranked[0]['option']!r}"
    )


# ---------------------------------------------------------------------------
# Property 3: Risk weight derivation
# Validates: Requirements 5.1
# ---------------------------------------------------------------------------


@given(risk_tolerance=risk_tolerance_strategy)
@settings(max_examples=200)
def test_risk_weight_derivation(risk_tolerance):
    """**Validates: Requirements 5.1**

    For any risk_tolerance in [0.0, 1.0], rank_outcomes must compute
    risk_w as exactly 1.0 - risk_tolerance.

    Tested indirectly: two results with identical salaries and happiness but
    different risk_scores. When risk_tolerance is low (risk_w is high), the
    option with lower risk_score must receive a higher score.
    """
    # Build two single-scenario options with identical salary and happiness
    # but different risk_scores: option_a has low risk, option_b has high risk.
    results = [
        {
            "option": "option_a",
            "scenario": "baseline",
            "probability": 1.0,
            "salary": 50000.0,
            "risk_score": 0.2,
            "happiness": 0.5,
        },
        {
            "option": "option_b",
            "scenario": "baseline",
            "probability": 1.0,
            "salary": 50000.0,
            "risk_score": 0.8,
            "happiness": 0.5,
        },
    ]

    output = rank_outcomes(results, WEIGHTS, risk_tolerance)
    ranked = output["ranked"]

    # Derive expected risk_w
    risk_w = 1.0 - risk_tolerance

    # Compute expected scores manually (salaries are equal → norm_salary = 0.0 for both)
    # score = salary_w * 0.0 + happiness_w * 0.5 - risk_w * risk_score
    score_a = WEIGHTS["happiness_w"] * 0.5 - risk_w * 0.2
    score_b = WEIGHTS["happiness_w"] * 0.5 - risk_w * 0.8

    # Verify the ranking matches the expected ordering
    ranked_options = {r["option"]: r["score"] for r in ranked}

    assert math.isclose(ranked_options["option_a"], score_a, rel_tol=1e-6, abs_tol=1e-9), (
        f"option_a score mismatch: got {ranked_options['option_a']}, expected {score_a}"
    )
    assert math.isclose(ranked_options["option_b"], score_b, rel_tol=1e-6, abs_tol=1e-9), (
        f"option_b score mismatch: got {ranked_options['option_b']}, expected {score_b}"
    )

    # When risk_w > 0 (risk_tolerance < 1.0), option_a (lower risk) should rank higher
    if risk_tolerance < 1.0:
        assert ranked[0]["option"] == "option_a", (
            f"With risk_tolerance={risk_tolerance} (risk_w={risk_w:.4f}), "
            f"option_a (risk=0.2) should beat option_b (risk=0.8), "
            f"but best_option={output['best_option']!r}"
        )


# ---------------------------------------------------------------------------
# Property 4: Dynamic salary normalization
# Validates: Requirements 5.2, 5.3
# ---------------------------------------------------------------------------


def test_salary_normalization_uses_list_bounds():
    """**Validates: Requirements 5.2, 5.3**

    With salaries [10000, 20000]:
    - norm_salary for 10000 must be 0.0
    - norm_salary for 20000 must be 1.0
    """
    results = [
        {
            "option": "option_low",
            "scenario": "baseline",
            "probability": 1.0,
            "salary": 10000.0,
            "risk_score": 0.5,
            "happiness": 0.5,
        },
        {
            "option": "option_high",
            "scenario": "baseline",
            "probability": 1.0,
            "salary": 20000.0,
            "risk_score": 0.5,
            "happiness": 0.5,
        },
    ]

    output = rank_outcomes(results, WEIGHTS, risk_tolerance=0.5)
    scenario_results = output["scenario_results"]

    scores_by_option = {r["option"]: r["score"] for r in scenario_results}

    # With equal risk_score and happiness, the score difference is purely from norm_salary.
    # option_high (norm=1.0): score = 0.4*1.0 + 0.4*0.5 - 0.5*0.5 = 0.4 + 0.2 - 0.25 = 0.35
    # option_low  (norm=0.0): score = 0.4*0.0 + 0.4*0.5 - 0.5*0.5 = 0.0 + 0.2 - 0.25 = -0.05
    expected_high = 0.4 * 1.0 + 0.4 * 0.5 - 0.5 * 0.5
    expected_low = 0.4 * 0.0 + 0.4 * 0.5 - 0.5 * 0.5

    assert math.isclose(scores_by_option["option_high"], expected_high, rel_tol=1e-6), (
        f"option_high score={scores_by_option['option_high']}, expected {expected_high}"
    )
    assert math.isclose(scores_by_option["option_low"], expected_low, rel_tol=1e-6), (
        f"option_low score={scores_by_option['option_low']}, expected {expected_low}"
    )


def test_salary_normalization_equal_salaries_no_division_by_zero():
    """**Validates: Requirements 5.3**

    When all salaries are equal, salary_range is set to 1 (not 0),
    so norm_salary = 0.0 for all entries and no ZeroDivisionError is raised.
    """
    results = [
        {
            "option": "option_a",
            "scenario": "baseline",
            "probability": 1.0,
            "salary": 50000.0,
            "risk_score": 0.3,
            "happiness": 0.7,
        },
        {
            "option": "option_b",
            "scenario": "baseline",
            "probability": 1.0,
            "salary": 50000.0,
            "risk_score": 0.3,
            "happiness": 0.7,
        },
    ]

    # Should not raise
    output = rank_outcomes(results, WEIGHTS, risk_tolerance=0.5)

    # All norm_salary = 0.0 → scores are identical
    for r in output["scenario_results"]:
        expected_score = WEIGHTS["happiness_w"] * 0.7 - 0.5 * 0.3
        assert math.isclose(r["score"], expected_score, rel_tol=1e-6), (
            f"score={r['score']}, expected {expected_score}"
        )


@given(
    salary=st.floats(min_value=10000.0, max_value=200000.0, allow_nan=False, allow_infinity=False),
    risk_tolerance=risk_tolerance_strategy,
)
@settings(max_examples=100)
def test_salary_normalization_dynamic_bounds(salary, risk_tolerance):
    """**Validates: Requirements 5.2, 5.3**

    For any results list, normalization must use the min/max of that specific list.
    The minimum salary always normalizes to 0.0 and the maximum to 1.0
    (when they differ), regardless of absolute values.
    """
    low = salary
    high = salary * 2.0  # guaranteed different

    results = [
        {
            "option": "option_low",
            "scenario": "baseline",
            "probability": 1.0,
            "salary": low,
            "risk_score": 0.5,
            "happiness": 0.5,
        },
        {
            "option": "option_high",
            "scenario": "baseline",
            "probability": 1.0,
            "salary": high,
            "risk_score": 0.5,
            "happiness": 0.5,
        },
    ]

    output = rank_outcomes(results, WEIGHTS, risk_tolerance)
    scenario_results = {r["option"]: r for r in output["scenario_results"]}

    risk_w = 1.0 - risk_tolerance
    expected_low_score = WEIGHTS["salary_w"] * 0.0 + WEIGHTS["happiness_w"] * 0.5 - risk_w * 0.5
    expected_high_score = WEIGHTS["salary_w"] * 1.0 + WEIGHTS["happiness_w"] * 0.5 - risk_w * 0.5

    assert math.isclose(scenario_results["option_low"]["score"], expected_low_score, rel_tol=1e-6, abs_tol=1e-9), (
        f"option_low score={scenario_results['option_low']['score']}, expected {expected_low_score}"
    )
    assert math.isclose(scenario_results["option_high"]["score"], expected_high_score, rel_tol=1e-6, abs_tol=1e-9), (
        f"option_high score={scenario_results['option_high']['score']}, expected {expected_high_score}"
    )


# ---------------------------------------------------------------------------
# Property 5: Probability-weighted option aggregation
# Validates: Requirements 5.5
# ---------------------------------------------------------------------------


@given(
    prob_a=st.floats(min_value=0.01, max_value=0.99, allow_nan=False),
    salary_1=st.floats(min_value=10000.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
    salary_2=st.floats(min_value=10000.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
    risk_tolerance=risk_tolerance_strategy,
)
@settings(max_examples=100)
def test_probability_weighted_option_aggregation(prob_a, salary_1, salary_2, risk_tolerance):
    """**Validates: Requirements 5.5**

    For any results with multiple scenarios per option, each option's aggregate
    score must equal sum(scenario_score * scenario_probability) for its scenarios.
    """
    prob_b = round(1.0 - prob_a, 10)  # complement so they sum to 1.0

    results = [
        {
            "option": "option_x",
            "scenario": "scenario_1",
            "probability": prob_a,
            "salary": salary_1,
            "risk_score": 0.3,
            "happiness": 0.6,
        },
        {
            "option": "option_x",
            "scenario": "scenario_2",
            "probability": prob_b,
            "salary": salary_2,
            "risk_score": 0.5,
            "happiness": 0.4,
        },
    ]

    output = rank_outcomes(results, WEIGHTS, risk_tolerance)
    ranked = output["ranked"]
    scenario_results = output["scenario_results"]

    # Compute expected scores manually using the same normalization logic
    all_salaries = [salary_1, salary_2]
    min_s = min(all_salaries)
    max_s = max(all_salaries)
    salary_range = max_s - min_s if max_s != min_s else 1.0
    risk_w = 1.0 - risk_tolerance

    def expected_score(salary, risk_score, happiness):
        norm = (salary - min_s) / salary_range
        return WEIGHTS["salary_w"] * norm + WEIGHTS["happiness_w"] * happiness - risk_w * risk_score

    score_1 = expected_score(salary_1, 0.3, 0.6)
    score_2 = expected_score(salary_2, 0.5, 0.4)
    expected_aggregate = score_1 * prob_a + score_2 * prob_b

    # Find option_x in ranked
    option_x_ranked = next(r for r in ranked if r["option"] == "option_x")

    assert math.isclose(option_x_ranked["score"], expected_aggregate, rel_tol=1e-6, abs_tol=1e-9), (
        f"option_x aggregate score={option_x_ranked['score']}, expected {expected_aggregate}"
    )
