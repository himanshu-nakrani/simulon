"""Property-based tests for FastAPI request validation.

Property 10: Request validation rejects out-of-range inputs
Validates: Requirements 1.1, 1.2, 1.3

The `transformers` stub is installed in conftest.py. The module-level `llm`
singleton in main.py is patched via unittest.mock so no real model is loaded.
"""

from unittest.mock import MagicMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis import HealthCheck
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Strategies for invalid inputs
# ---------------------------------------------------------------------------

# risk values strictly outside [0.0, 1.0]
out_of_range_risk = st.one_of(
    st.floats(max_value=-0.0001, allow_nan=False, allow_infinity=False),
    st.floats(min_value=1.0001, allow_nan=False, allow_infinity=False),
)

# time_horizon values less than 1 (0 or negative)
invalid_time_horizon = st.integers(max_value=0)

# empty or whitespace-only decision_text
empty_decision_text = st.one_of(
    st.just(""),
    st.text(alphabet=st.characters(whitelist_categories=("Zs",)), min_size=1),
    st.just("   "),
    st.just("\t\n"),
)


# ---------------------------------------------------------------------------
# Module-level TestClient (created once to avoid per-example cold-start cost)
# ---------------------------------------------------------------------------

_mock_llm = MagicMock()
_mock_llm.structure_input.return_value = {
    "decision": "test",
    "options": ["proceed", "do not proceed"],
    "factors": ["risk"],
}
_mock_llm.generate_explanation.return_value = "test explanation"

with patch("backend.app.main.llm", _mock_llm):
    from backend.app.main import app

_client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Property 10: Request validation rejects out-of-range inputs
# Validates: Requirements 1.1, 1.2, 1.3
# ---------------------------------------------------------------------------

@given(risk=out_of_range_risk)
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_out_of_range_risk_returns_422(risk):
    """**Validates: Requirements 1.2**

    For any risk value outside [0.0, 1.0], the API must return HTTP 422.
    """
    response = _client.post(
        "/simulate",
        json={"decision_text": "Should I switch jobs?", "risk": risk, "time_horizon": 3},
    )
    assert response.status_code == 422, (
        f"Expected 422 for risk={risk}, got {response.status_code}"
    )


@given(time_horizon=invalid_time_horizon)
@settings(max_examples=50, deadline=None)
def test_invalid_time_horizon_returns_422(time_horizon):
    """**Validates: Requirements 1.3**

    For any time_horizon < 1, the API must return HTTP 422.
    """
    response = _client.post(
        "/simulate",
        json={"decision_text": "Should I switch jobs?", "risk": 0.5, "time_horizon": time_horizon},
    )
    assert response.status_code == 422, (
        f"Expected 422 for time_horizon={time_horizon}, got {response.status_code}"
    )


@given(decision_text=empty_decision_text)
@settings(max_examples=50, deadline=None)
def test_empty_decision_text_returns_422(decision_text):
    """**Validates: Requirements 1.1**

    For any empty or whitespace-only decision_text, the API must return HTTP 422.
    """
    response = _client.post(
        "/simulate",
        json={"decision_text": decision_text, "risk": 0.5, "time_horizon": 3},
    )
    assert response.status_code == 422, (
        f"Expected 422 for decision_text={repr(decision_text)}, got {response.status_code}"
    )
