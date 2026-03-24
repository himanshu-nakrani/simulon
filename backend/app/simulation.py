import random

import numpy as np


# Scenario templates keyed by semantic category
_TEMPLATES = {
    "high_growth": [
        "High growth trajectory",
        "Rapid promotion",
        "Success and expansion",
        "Breakthrough performance",
    ],
    "stressful": [
        "Stressful transition period",
        "High-risk environment",
        "Struggle and adaptation",
        "Turbulent adjustment",
    ],
    "neutral": [
        "Stable baseline",
        "Moderate progress",
        "Steady continuation",
        "Gradual improvement",
    ],
}


def _get_templates(option: str, risk_tolerance: float) -> list[str]:
    """
    Return 2 or 3 scenario template names for a given option.
    Higher risk_tolerance → include a high-growth scenario; lower → lean neutral/stressful.
    """
    option_lower = option.lower()

    # Pick one template from each semantic bucket, varied by option text
    high_idx = hash(option_lower + "high") % len(_TEMPLATES["high_growth"])
    stress_idx = hash(option_lower + "stress") % len(_TEMPLATES["stressful"])
    neutral_idx = hash(option_lower + "neutral") % len(_TEMPLATES["neutral"])

    high = _TEMPLATES["high_growth"][high_idx]
    stressful = _TEMPLATES["stressful"][stress_idx]
    neutral = _TEMPLATES["neutral"][neutral_idx]

    if risk_tolerance >= 0.6:
        # High risk tolerance: high-growth, stressful, neutral (3 scenarios)
        return [high, stressful, neutral]
    elif risk_tolerance >= 0.3:
        # Medium risk tolerance: high-growth, neutral (2 scenarios)
        return [high, neutral]
    else:
        # Low risk tolerance: neutral, stressful (2 scenarios)
        return [neutral, stressful]


def _sample_probability(risk_tolerance: float, remaining_prob: float) -> float:
    """
    Sample a probability for a non-last scenario.
    Higher risk_tolerance → higher variance (more extreme splits).
    """
    # Base split: lean toward even distribution, then skew by risk_tolerance
    # Low risk_tolerance → probabilities closer to even split
    # High risk_tolerance → wider variance, can assign more to one scenario
    low = max(0.1, remaining_prob * (0.2 + 0.3 * (1.0 - risk_tolerance)))
    high = min(remaining_prob - 0.05, remaining_prob * (0.6 + 0.3 * risk_tolerance))

    if low >= high:
        # Fallback: assign roughly half of remaining
        return round(remaining_prob * 0.5, 2)

    return round(random.uniform(low, high), 2)


def generate_scenarios(structured_input: dict, risk_tolerance: float) -> list[dict]:
    """
    Returns 2-3 scenarios per option with assigned probabilities.

    For each option:
    - Generates 2-3 scenario templates based on the option and risk_tolerance
    - Assigns probabilities to all but the last scenario (rounded to 2 dp)
    - Last scenario probability = round(1.0 - sum(assigned_probs), 4)
      to guarantee exact sum of 1.0 without independent rounding error

    Args:
        structured_input: dict with key "options" (list of str)
        risk_tolerance: float in [0.0, 1.0]

    Returns:
        list of {"option": str, "scenarios": [{"name": str, "probability": float}]}
    """
    scenario_list = []

    for option in structured_input["options"]:
        templates = _get_templates(option, risk_tolerance)
        scenarios = []
        assigned_probs = []
        remaining_prob = 1.0

        # Assign probabilities to all scenarios except the last
        for template in templates[:-1]:
            prob = _sample_probability(risk_tolerance, remaining_prob)
            scenarios.append({"name": template, "probability": prob})
            assigned_probs.append(prob)
            remaining_prob -= prob

        # Last scenario: exact remainder — do NOT round independently
        last_prob = round(1.0 - sum(assigned_probs), 4)
        scenarios.append({"name": templates[-1], "probability": last_prob})

        scenario_list.append({"option": option, "scenarios": scenarios})

    return scenario_list


def run_simulation(scenarios: list[dict], time_horizon: int) -> list[dict]:
    """
    For each scenario, simulate salary, risk_score, happiness using numpy random.
    Sets np.random.seed(42) for deterministic output.

    Args:
        scenarios: list of {"option": str, "scenarios": [{"name": str, "probability": float}]}
        time_horizon: positive integer (years)

    Returns:
        list of {"option", "scenario", "probability", "salary", "risk_score", "happiness"}
    """
    np.random.seed(42)
    results = []

    for option_block in scenarios:
        for scenario in option_block["scenarios"]:
            name_lower = scenario["name"].lower()

            # Determine salary multiplier and risk/happiness ranges by keyword
            if any(kw in name_lower for kw in ("high growth", "promotion", "success")):
                salary_multiplier = np.random.uniform(1.3, 2.0)
                risk_score = np.random.uniform(0.4, 0.8)
                happiness = np.random.uniform(0.6, 1.0)
            elif any(kw in name_lower for kw in ("stressful", "risk", "struggle")):
                salary_multiplier = np.random.uniform(0.8, 1.1)
                risk_score = np.random.uniform(0.6, 1.0)
                happiness = np.random.uniform(0.2, 0.6)
            else:
                salary_multiplier = np.random.uniform(1.0, 1.4)
                risk_score = np.random.uniform(0.2, 0.6)
                happiness = np.random.uniform(0.4, 0.8)

            base_salary = np.random.uniform(40000, 80000)
            salary = base_salary * salary_multiplier * (1 + 0.05 * time_horizon)

            results.append({
                "option": option_block["option"],
                "scenario": scenario["name"],
                "probability": scenario["probability"],
                "salary": round(salary, 2),
                "risk_score": round(risk_score, 2),
                "happiness": round(happiness, 2),
            })

    return results


def rank_outcomes(results: list[dict], weights: dict, risk_tolerance: float) -> dict:
    """
    Aggregates scores at the option level using probability-weighted scenario scores.
    risk_weight is derived as (1 - risk_tolerance) — user preference drives penalty.
    Salary is normalized dynamically using min/max of actual simulated salaries.
    option_score = sum(scenario_score * scenario_probability) for all scenarios of that option.
    Returns {"best_option": str, "ranked": [sorted option-level aggregates], "scenario_results": results}
    """
    risk_w = 1.0 - risk_tolerance

    # Dynamic salary normalization using actual result bounds
    all_salaries = [r["salary"] for r in results]
    min_salary = min(all_salaries)
    max_salary = max(all_salaries)
    salary_range = max_salary - min_salary
    if salary_range == 0:
        salary_range = 1

    # Score each scenario
    for result in results:
        norm_salary = (result["salary"] - min_salary) / salary_range
        result["score"] = (
            weights["salary_w"] * norm_salary
            + weights["happiness_w"] * result["happiness"]
            - risk_w * result["risk_score"]
        )

    # Aggregate to option level via probability-weighted scores
    option_scores: dict[str, float] = {}
    for result in results:
        option = result["option"]
        if option not in option_scores:
            option_scores[option] = 0.0
        option_scores[option] += result["score"] * result["probability"]

    # Sort options by aggregate score descending
    ranked = sorted(
        [{"option": opt, "score": score} for opt, score in option_scores.items()],
        key=lambda x: x["score"],
        reverse=True,
    )

    best_option = ranked[0]["option"]

    # Scenario-level results sorted by score descending (for UI display)
    scenario_results = sorted(results, key=lambda r: r["score"], reverse=True)

    return {
        "best_option": best_option,
        "ranked": ranked,
        "scenario_results": scenario_results,
    }
