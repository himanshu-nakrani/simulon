"""Property-based tests for the Simulation Engine — scenario generation.

Property 1: Scenario probability sum invariant
Validates: Requirements 3.2, 3.3

For any valid structured_input with N options and any risk_tolerance in [0.0, 1.0],
generate_scenarios must return exactly N option groups where:
- each group has 2–3 scenarios
- the scenario probabilities within each group sum to exactly 1.0
"""

import math

from hypothesis import given, settings
from hypothesis import strategies as st

from backend.app.simulation import generate_scenarios


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Non-empty option strings (printable, at least 1 char)
option_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
    min_size=1,
    max_size=30,
).filter(lambda s: s.strip())

# structured_input dict with at least 2 options
structured_input_strategy = st.fixed_dictionaries(
    {
        "options": st.lists(option_strategy, min_size=2, max_size=5, unique=True),
        "factors": st.just(["factor_1"]),
    }
)

risk_tolerance_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


# ---------------------------------------------------------------------------
# Property 1: Scenario probability sum invariant
# Validates: Requirements 3.2, 3.3
# ---------------------------------------------------------------------------


@given(structured_input=structured_input_strategy, risk_tolerance=risk_tolerance_strategy)
@settings(max_examples=100)
def test_scenario_probability_sum_invariant(structured_input, risk_tolerance):
    """**Validates: Requirements 3.2, 3.3**

    For any valid structured_input and risk_tolerance in [0.0, 1.0]:
    - generate_scenarios returns exactly one group per option
    - each group has 2–3 scenarios
    - probabilities within each group sum to exactly 1.0
    """
    result = generate_scenarios(structured_input, risk_tolerance)

    # One group per option (Requirement 3.1)
    assert len(result) == len(structured_input["options"])

    for group in result:
        scenarios = group["scenarios"]

        # Each group has 2–3 scenarios (Requirement 3.2)
        assert 2 <= len(scenarios) <= 3, (
            f"Expected 2–3 scenarios per option, got {len(scenarios)} "
            f"for option '{group['option']}'"
        )

        # Probabilities sum to exactly 1.0 (Requirement 3.3)
        total = sum(s["probability"] for s in scenarios)
        assert math.isclose(total, 1.0, abs_tol=1e-4), (
            f"Probabilities for option '{group['option']}' sum to {total}, expected 1.0"
        )


# ---------------------------------------------------------------------------
# Strategies for run_simulation tests
# ---------------------------------------------------------------------------

from backend.app.simulation import run_simulation

# Scenario name strategies for semantic salary range testing
HIGH_GROWTH_KEYWORDS = ["high growth", "promotion", "success"]
STRESSFUL_KEYWORDS = ["stressful", "risk", "struggle"]

high_growth_name_strategy = st.sampled_from(HIGH_GROWTH_KEYWORDS).flatmap(
    lambda kw: st.just(kw)
    | st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Zs")), min_size=0, max_size=10).map(
        lambda prefix: f"{prefix} {kw}".strip()
    )
)

stressful_name_strategy = st.sampled_from(STRESSFUL_KEYWORDS).flatmap(
    lambda kw: st.just(kw)
    | st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Zs")), min_size=0, max_size=10).map(
        lambda prefix: f"{prefix} {kw}".strip()
    )
)

# Neutral names: must not contain any high-growth or stressful keywords
_ALL_KEYWORDS = HIGH_GROWTH_KEYWORDS + STRESSFUL_KEYWORDS

neutral_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Zs")),
    min_size=3,
    max_size=20,
).filter(
    lambda s: s.strip()
    and not any(kw in s.lower() for kw in _ALL_KEYWORDS)
)


def make_scenario_list(scenario_name: str, probability: float = 1.0) -> list[dict]:
    """Build a minimal valid scenario list with a single option and single scenario."""
    return [{"option": "test_option", "scenarios": [{"name": scenario_name, "probability": probability}]}]


# Valid scenario list strategy for general simulation tests
scenario_entry_strategy = st.fixed_dictionaries(
    {
        "name": st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Zs")),
            min_size=1,
            max_size=30,
        ).filter(lambda s: s.strip()),
        "probability": st.just(1.0),
    }
)

scenario_list_strategy = st.lists(
    st.fixed_dictionaries(
        {
            "option": st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
                min_size=1,
                max_size=20,
            ).filter(lambda s: s.strip()),
            "scenarios": st.lists(scenario_entry_strategy, min_size=1, max_size=3),
        }
    ),
    min_size=1,
    max_size=3,
)

time_horizon_strategy = st.integers(min_value=1, max_value=30)


# ---------------------------------------------------------------------------
# Property 7: Simulation output value invariants
# Validates: Requirements 4.2, 4.3, 4.4
# ---------------------------------------------------------------------------


@given(scenarios=scenario_list_strategy, time_horizon=time_horizon_strategy)
@settings(max_examples=100)
def test_simulation_output_value_invariants(scenarios, time_horizon):
    """**Validates: Requirements 4.2, 4.3, 4.4**

    For any valid scenario list and time_horizon >= 1:
    - every result has salary > 0
    - every result has risk_score in [0.0, 1.0]
    - every result has happiness in [0.0, 1.0]
    """
    results = run_simulation(scenarios, time_horizon)

    for r in results:
        assert r["salary"] > 0, f"Expected salary > 0, got {r['salary']}"
        assert 0.0 <= r["risk_score"] <= 1.0, f"Expected risk_score in [0,1], got {r['risk_score']}"
        assert 0.0 <= r["happiness"] <= 1.0, f"Expected happiness in [0,1], got {r['happiness']}"


# ---------------------------------------------------------------------------
# Property 9: Simulation determinism
# Validates: Requirements 4.1
# ---------------------------------------------------------------------------


@given(scenarios=scenario_list_strategy, time_horizon=time_horizon_strategy)
@settings(max_examples=50)
def test_simulation_determinism(scenarios, time_horizon):
    """**Validates: Requirements 4.1**

    Calling run_simulation twice with identical inputs must produce identical results
    because np.random.seed(42) is set inside run_simulation.
    """
    results_1 = run_simulation(scenarios, time_horizon)
    results_2 = run_simulation(scenarios, time_horizon)

    assert results_1 == results_2, (
        f"run_simulation is not deterministic: first call returned {results_1}, "
        f"second call returned {results_2}"
    )


# ---------------------------------------------------------------------------
# Property 8: Semantic salary ranges
# Validates: Requirements 4.5, 4.6, 4.7
# ---------------------------------------------------------------------------


@given(scenario_name=high_growth_name_strategy, time_horizon=time_horizon_strategy)
@settings(max_examples=100)
def test_semantic_salary_range_high_growth(scenario_name, time_horizon):
    """**Validates: Requirements 4.5**

    For scenario names containing high-growth keywords, salary must fall in
    [base * 1.3 * (1 + 0.05*t), base * 2.0 * (1 + 0.05*t)] where base in [40000, 80000].
    """
    results = run_simulation(make_scenario_list(scenario_name), time_horizon)
    assert len(results) == 1
    salary = results[0]["salary"]

    growth_factor = 1 + 0.05 * time_horizon
    min_salary = 40000 * 1.3 * growth_factor
    max_salary = 80000 * 2.0 * growth_factor

    assert min_salary <= salary <= max_salary, (
        f"High-growth scenario '{scenario_name}' salary {salary} not in "
        f"[{min_salary:.2f}, {max_salary:.2f}] for time_horizon={time_horizon}"
    )


@given(scenario_name=stressful_name_strategy, time_horizon=time_horizon_strategy)
@settings(max_examples=100)
def test_semantic_salary_range_stressful(scenario_name, time_horizon):
    """**Validates: Requirements 4.6**

    For scenario names containing stressful keywords, salary must fall in
    [base * 0.8 * (1 + 0.05*t), base * 1.1 * (1 + 0.05*t)] where base in [40000, 80000].
    """
    results = run_simulation(make_scenario_list(scenario_name), time_horizon)
    assert len(results) == 1
    salary = results[0]["salary"]

    growth_factor = 1 + 0.05 * time_horizon
    min_salary = 40000 * 0.8 * growth_factor
    max_salary = 80000 * 1.1 * growth_factor

    assert min_salary <= salary <= max_salary, (
        f"Stressful scenario '{scenario_name}' salary {salary} not in "
        f"[{min_salary:.2f}, {max_salary:.2f}] for time_horizon={time_horizon}"
    )


@given(scenario_name=neutral_name_strategy, time_horizon=time_horizon_strategy)
@settings(max_examples=100)
def test_semantic_salary_range_neutral(scenario_name, time_horizon):
    """**Validates: Requirements 4.7**

    For neutral scenario names (no high-growth or stressful keywords), salary must fall in
    [base * 1.0 * (1 + 0.05*t), base * 1.4 * (1 + 0.05*t)] where base in [40000, 80000].
    """
    results = run_simulation(make_scenario_list(scenario_name), time_horizon)
    assert len(results) == 1
    salary = results[0]["salary"]

    growth_factor = 1 + 0.05 * time_horizon
    min_salary = 40000 * 1.0 * growth_factor
    max_salary = 80000 * 1.4 * growth_factor

    assert min_salary <= salary <= max_salary, (
        f"Neutral scenario '{scenario_name}' salary {salary} not in "
        f"[{min_salary:.2f}, {max_salary:.2f}] for time_horizon={time_horizon}"
    )
